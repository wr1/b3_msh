from pathlib import Path

import numpy as np
import pyvista as pv
from scipy.interpolate import PchipInterpolator, interp1d
from statesman import Statesman
from statesman.core.base import ManagedFile

from ..core.airfoil import Airfoil
from ..core.shear_web import ShearWeb


class B3MshSurfaceStep(Statesman):
    """Statesman step for running b3_msh surface meshing."""

    workdir_key = "workdir"
    input_files = [
        ManagedFile(name="b3_geo/lm1_mesh3d.vtp", non_empty=True),
    ]
    output_files = ["b3_msh/lm2_surface_mesh.vtp"]
    dependent_sections = ["geometry", "airfoils", "structure", "mesh3d"]

    def _expand_mesh_z(self):
        """Expand mesh3d.z from specs to list of floats."""
        mesh_z = []
        for z_spec in self.config_model.mesh3d.z:
            if z_spec.type == "plain":
                mesh_z.extend(z_spec.values)
            elif z_spec.type == "linspace":
                mesh_z.extend(np.linspace(z_spec.values[0], z_spec.values[1], z_spec.num))
        self.config_model.mesh3d.z = sorted(set(mesh_z))

    def _load_and_validate_config(self):
        """Load and validate config."""
        from ..core.mesh_model import Config

        config_model = Config(**self.config)
        if config_model.mesh3d is None:
            raise ValueError("mesh3d section required for surface meshing")
        self.config_model = config_model
        return config_model

    def _load_mesh(self, input_path):
        """Load the pre-processed mesh."""
        self.logger.info(f"Loading pre-processed mesh from {input_path}")
        if not input_path.exists():
            raise FileNotFoundError(
                f"Input file {input_path} does not exist. Ensure previous steps have run."
            )
        mesh = pv.read(str(input_path))
        return mesh

    def _process_sections(self, mesh, z_sections, chordwise_mesh, webs_config):
        """Process each section for surface meshing."""
        self.logger.info("Processing sections for surface mesh")
        sections = []
        webs_config_dict = [web.model_dump() for web in webs_config]
        for z in z_sections:
            af = self.process_section_from_mesh(
                mesh, z, chordwise_mesh.model_dump(), webs_config_dict, self.logger
            )
            sections.append(af)
        return sections

    def _create_surface_mesh(self, sections, output_path):
        """Create surface mesh by connecting line meshes into quads."""
        self.logger.info("Creating surface mesh")
        # Sort sections by z position
        sections.sort(key=lambda af: af.position[2])
        all_points = []
        all_faces = []
        point_offset = 0

        # Collect points and faces for each section
        section_data = []
        for i, af in enumerate(sections):
            pv_mesh = af.to_pyvista()
            points = pv_mesh.points
            lines = pv_mesh.lines.reshape(-1, 3)[:, 1:]  # Get line connectivity
            panel_ids = pv_mesh.cell_data["panel_id"]
            airfoil_lines = lines[panel_ids >= 0]
            shear_web_lines = {}
            unique_panels = np.unique(panel_ids)
            for panel_id in unique_panels:
                if panel_id < 0:
                    shear_web_lines[panel_id] = lines[panel_ids == panel_id]
            section_data.append(
                {
                    "points": points,
                    "lines": lines,
                    "panel_ids": panel_ids,
                    "n_points": len(points),
                    "n_airfoil_lines": len(airfoil_lines),
                    "shear_web_lines": shear_web_lines,
                }
            )
            self.logger.info(
                f"Section {i} (z={af.position[2]:.2f}): {len(points)} points, {len(airfoil_lines)} airfoil lines, shear webs: { {k: len(v) for k, v in shear_web_lines.items()} }"
            )

        # Assume sections have consistent line elements for panel_id >= 0
        for i in range(len(sections) - 1):
            sec1 = section_data[i]
            sec2 = section_data[i + 1]

            # For airfoil panels (panel_id >= 0)
            airfoil_lines1 = sec1["lines"][sec1["panel_ids"] >= 0]
            airfoil_lines2 = sec2["lines"][sec2["panel_ids"] >= 0]

            if len(airfoil_lines1) != len(airfoil_lines2):
                self.logger.warning(
                    f"Inconsistent number of airfoil line elements between sections {i} ({len(airfoil_lines1)}) and {i + 1} ({len(airfoil_lines2)}), skipping airfoil quads for this pair"
                )
                continue

            for j in range(len(airfoil_lines1)):
                p1 = airfoil_lines1[j][0] + point_offset
                p2 = airfoil_lines1[j][1] + point_offset
                p3 = airfoil_lines2[j][1] + point_offset + sec1["n_points"]
                p4 = airfoil_lines2[j][0] + point_offset + sec1["n_points"]
                all_faces.append([4, p1, p2, p3, p4])  # Quad face

            # For each shear web panel_id < 0
            unique_panels = np.unique(sec1["panel_ids"])
            for panel_id in unique_panels:
                if panel_id < 0:
                    lines1 = sec1["lines"][sec1["panel_ids"] == panel_id]
                    lines2 = sec2["lines"][sec2["panel_ids"] == panel_id]
                    if len(lines1) != len(lines2):
                        self.logger.warning(
                            f"Inconsistent shear web elements for panel {panel_id} between sections {i} ({len(lines1)}) and {i + 1} ({len(lines2)}), skipping"
                        )
                        continue
                    for j in range(len(lines1)):
                        p1 = lines1[j][0] + point_offset
                        p2 = lines1[j][1] + point_offset
                        p3 = lines2[j][1] + point_offset + sec1["n_points"]
                        p4 = lines2[j][0] + point_offset + sec1["n_points"]
                        all_faces.append([4, p1, p2, p3, p4])

            all_points.extend(sec1["points"])
            point_offset += sec1["n_points"]

        # Add last section points
        all_points.extend(section_data[-1]["points"])

        # Create PyVista mesh
        surface_mesh = pv.PolyData(np.array(all_points), faces=np.array(all_faces))

        # Save
        output_path.parent.mkdir(parents=True, exist_ok=True)
        self.logger.info(f"Saving surface mesh to {output_path}")
        surface_mesh.save(str(output_path))
        self.logger.info(f"Saved surface mesh to {output_path}")

    @staticmethod
    def process_section_from_mesh(mesh, z, chordwise_mesh, webs_config, logger):
        """Process a single section mesh by remeshing with uniform t distribution."""
        # Extract points at this z
        mask = np.isclose(mesh.points[:, 2], z)

        section_points = mesh.points[mask]
        # Sort by associated t pointdata
        t_values = mesh.point_data["t"][mask]
        sorted_indices = np.argsort(t_values)
        sorted_points = section_points[sorted_indices]
        points_2d = sorted_points[:, :2]  # Take x,y

        # Get rel_span from mesh
        rel_span_values = mesh.point_data["rel_span"][mask]
        rel_span = rel_span_values[0]  # All points at same z have same rel_span

        # Create Airfoil from points
        af = Airfoil(points_2d, is_normalized=False, position=(0, 0, z))  # Position at z
        af.rel_span = rel_span

        # Add constant fields from input mesh
        af.constant_fields = {}
        for field in mesh.point_data.keys():
            values = mesh.point_data[field][mask]
            if np.allclose(values, values[0]):
                af.constant_fields[field] = values[0]

        # Add shear webs if applicable
        for web in webs_config:
            if web["mesh"]:
                z_range = web["z_range"]
                if z_range[0] <= z <= z_range[1]:
                    if web["type"] == "ribbon":
                        # Handle ribbon web
                        ref_web_name = web["reference_web"]
                        ref_web = next(w for w in webs_config if w["name"] == ref_web_name)
                        z_vals = np.array([p[0] for p in web["offsets"]])
                        offset_vals = np.array([p[1] for p in web["offsets"]])
                        sort_idx = np.argsort(z_vals)
                        z_vals = z_vals[sort_idx]
                        offset_vals = offset_vals[sort_idx]
                        interp_method = web.get("interp_method", "pchip")
                        if interp_method == "pchip":
                            offset_interp = PchipInterpolator(z_vals, offset_vals)
                        elif interp_method == "linear":
                            offset_interp = interp1d(
                                z_vals,
                                offset_vals,
                                kind="linear",
                                bounds_error=False,
                                fill_value="extrapolate",
                            )
                        else:
                            logger.error(
                                f"Unsupported interp_method '{interp_method}' for ribbon web {web['name']}"
                            )
                            raise ValueError(f"Unsupported interp_method: {interp_method}")
                        offset = float(offset_interp(z))
                        ref_origin = np.array(ref_web["origin"])
                        ref_normal = np.array(ref_web["orientation"])
                        normal_unit = ref_normal / np.linalg.norm(ref_normal)
                        new_origin = ref_origin + offset * normal_unit
                        sw_def = {
                            "type": "plane",
                            "origin": new_origin.tolist(),
                            "normal": ref_normal.tolist(),
                            "name": web["name"],
                        }
                        sw = ShearWeb(sw_def)
                        af.add_shear_web(sw, n_elements=web.get("n_elem", 10))
                        logger.debug(f"Added ribbon shear web {web['name']} at z={z}")
                    else:
                        sw_def = {
                            "type": web["type"],
                            "origin": [
                                web["origin"][0],
                                web["origin"][1],
                                web["origin"][2],
                            ],
                            "normal": web["orientation"],
                            "name": web["name"],
                        }
                        sw = ShearWeb(sw_def)
                        af.add_shear_web(sw, n_elements=web.get("n_elem", 10))
                        logger.debug(f"Added shear web {web['name']} at z={z}")

        # Add trailing edge shear web
        sw_te = ShearWeb({"type": "trailing_edge", "name": "trailing_edge"})
        af.add_shear_web(sw_te, n_elements=5)
        logger.debug(f"Added trailing edge shear web at z={z}")

        # Remesh with uniform t distribution
        n_elem = chordwise_mesh["default"]["n_elem"]
        logger.debug(f"Remeshing with {n_elem} elements")
        af.remesh(total_n_points=n_elem + 1)

        return af

    def _execute(self):
        """Execute the step."""
        self.logger.info("Executing B3MshSurfaceStep: Processing surface mesh.")
        config_model = self._load_and_validate_config()
        self._expand_mesh_z()

        config_dir = Path(self.config_path).parent
        workdir = config_dir / config_model.workdir
        z_sections = config_model.mesh3d.z
        chordwise_mesh = config_model.mesh3d.chordwise
        webs_config = config_model.structure.webs

        input_path = workdir / "b3_geo" / "lm1_mesh3d.vtp"
        mesh = self._load_mesh(input_path)

        sections = self._process_sections(mesh, z_sections, chordwise_mesh, webs_config)
        output_path = workdir / "b3_msh" / "lm2_surface_mesh.vtp"
        self._create_surface_mesh(sections, output_path)
