"""Base functionality for mesh processing steps."""

import numpy as np
from pathlib import Path
from statesman import Statesman
from statesman.core.base import ManagedFile
from ..core.airfoil import Airfoil
from ..core.shear_web import ShearWeb
from ..core.mesh_model import Config
from ..utils.logger import get_logger


class MeshBaseStep(Statesman):
    """Base class for mesh processing steps with shared utilities."""

    workdir_key = "workdir"
    input_files = [
        ManagedFile(name="b3_geo/lm1_mesh.vtp", non_empty=True),
    ]

    def __init__(self, config_path):
        super().__init__(config_path)
        self.logger = get_logger(self.__class__.__name__)

    def _expand_z_locations(self, z_specs):
        """Expand z specs to flat list of z-locations."""
        mesh_z = []
        for z_spec in z_specs:
            if z_spec["type"] == "plain":
                mesh_z.extend(z_spec["values"])
            elif z_spec["type"] == "linspace":
                mesh_z.extend(np.linspace(z_spec["values"][0], z_spec["values"][1], z_spec["num"]))
        return sorted(list(set(mesh_z)))

    def _load_and_validate_config(self):
        """Load and validate config."""
        config_model = Config(**self.config)
        return config_model

    def _load_mesh(self, input_path):
        """Load the pre-processed mesh."""
        self.logger.info(f"Loading pre-processed mesh from {input_path}")
        if not input_path.exists():
            raise FileNotFoundError(
                f"Input file {input_path} does not exist. Ensure previous steps have run."
            )
        import pyvista as pv

        mesh = pv.read(str(input_path))
        return mesh

    @staticmethod
    def process_section_from_mesh(mesh, z, chordwise_mesh, webs_config, logger):
        """Process a single section mesh by remeshing with uniform t distribution."""
        logger.debug(f"Processing section at z={z}")

        logger.info(f"  Extracting section at z={mesh.points}")

        # Extract points at this z
        mask = np.isclose(mesh.points[:, 2], z, atol=1e-6)

        section_points = mesh.points[mask]

        logger.info(f"  Found {section_points.shape[0]} points at z={z}")

        # Sort by associated t pointdata
        t_values = mesh.point_data["t"][mask]
        sorted_indices = np.argsort(t_values)
        sorted_points = section_points[sorted_indices]
        points_2d = sorted_points[:, :2]  # Take x,y

        # Get rel_span from mesh
        rel_span_values = mesh.point_data["rel_span"][mask]
        rel_span = float(rel_span_values[0])  # All same

        # Create Airfoil
        af = Airfoil(points_2d, is_normalized=False, position=(0, 0, z))
        af.rel_span = rel_span

        # Copy constant fields
        af.constant_fields = {}
        for field in mesh.point_data.keys():
            values = mesh.point_data[field][mask]
            if np.allclose(values, values[0]):
                af.constant_fields[field] = float(values[0])

        # Add shear webs
        for web in webs_config:
            if web["mesh"]:
                z_range = web.get("z_range", [-np.inf, np.inf])
                if z_range[0] <= z <= z_range[1]:
                    if web["type"] == "ribbon":
                        ref_web_name = web["reference_web"]
                        ref_web = next(w for w in webs_config if w["name"] == ref_web_name)

                        z_vals = np.array([p[0] for p in web["offsets"]])
                        offset_vals = np.array([p[1] for p in web["offsets"]])
                        sort_idx = np.argsort(z_vals)
                        z_vals, offset_vals = z_vals[sort_idx], offset_vals[sort_idx]

                        interp_method = web.get("interp_method", "pchip")
                        if interp_method == "pchip":
                            from scipy.interpolate import PchipInterpolator

                            offset_interp = PchipInterpolator(z_vals, offset_vals)
                        else:  # linear
                            from scipy.interpolate import interp1d

                            offset_interp = interp1d(
                                z_vals,
                                offset_vals,
                                kind="linear",
                                bounds_error=False,
                                fill_value="extrapolate",
                            )

                        offset = float(offset_interp(z))
                        ref_origin = np.array(ref_web["origin"])
                        ref_normal = np.array(ref_web.get("normal", ref_web.get("orientation")))
                        normal_unit = ref_normal / np.linalg.norm(ref_normal)
                        new_origin = ref_origin + offset * normal_unit

                        sw_def = {
                            "type": "plane",
                            "origin": new_origin.tolist(),
                            "normal": ref_normal.tolist(),
                            "name": web["name"],
                        }
                    else:
                        sw_def = {
                            "type": web["type"],
                            "origin": web["origin"],
                            "normal": web.get("normal", web.get("orientation")),
                            "name": web["name"],
                        }

                    sw = ShearWeb(sw_def)
                    n_elements = web.get("n_elem", 10)
                    af.add_shear_web(sw, n_elements=n_elements)
                    logger.debug(f"  Added {web['type']} web '{web['name']}' ({n_elements} elems)")

        # Trailing edge web
        sw_te = ShearWeb({"type": "trailing_edge", "name": "trailing_edge"})
        af.add_shear_web(sw_te, n_elements=5)

        # Remesh
        n_elem = chordwise_mesh["default"]["n_elem"]
        af.remesh(total_n_points=n_elem + 1)
        logger.debug(f"  Remeshed: {len(af.current_t)} points")

        return af
