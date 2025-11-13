import numpy as np
from pathlib import Path
from statesman import Statesman
from statesman.core.base import ManagedFile
from ..utils.logger import get_logger
from ..core.airfoil import Airfoil
from ..core.shear_web import ShearWeb
import pyvista as pv
from pydantic import BaseModel
from typing import List, Dict, Any


class Planform(BaseModel):
    npchord: int
    npspan: int
    pre_rotation: float
    dx: List[List[float]]
    dy: List[List[float]]
    z: List[List[float]]
    chord: List[List[float]]
    thickness: List[List[float]]
    twist: List[List[float]]


class Geometry(BaseModel):
    planform: Planform


class AirfoilItem(BaseModel):
    path: str
    name: str
    thickness: float


class Web(BaseModel):
    name: str
    type: str
    origin: List[float]
    orientation: List[float]
    z_range: List[float]
    element_size: float
    mesh: bool


class Structure(BaseModel):
    webs: List[Web]


class Chordwise(BaseModel):
    default: Dict[str, Any]
    panels: List[Dict[str, Any]]


class Mesh(BaseModel):
    z: List[float]
    chordwise: Chordwise


class Config(BaseModel):
    workdir: str
    geometry: Geometry
    airfoils: List[AirfoilItem]
    structure: Structure
    mesh: Mesh


class B3MshStep(Statesman):
    """Statesman step for running b3_msh blade processing."""

    workdir_key = "workdir"
    input_files = [
        ManagedFile(name="b3_geo/lm1_mesh.vtp", non_empty=True),
    ]
    output_files = ["b3_msh/lm2.vtp"]
    dependent_sections = ["geometry", "airfoils", "structure", "mesh"]

    def _expand_mesh_z(self):
        """Expand mesh.z from specs to list of floats."""
        mesh_z = []
        for z_spec in self.config['mesh']['z']:
            if z_spec["type"] == "plain":
                mesh_z.extend(z_spec["values"])
            elif z_spec["type"] == "linspace":
                mesh_z.extend(np.linspace(z_spec["values"][0], z_spec["values"][1], z_spec["num"]))
        self.config['mesh']['z'] = sorted(list(set(mesh_z)))

    def _load_and_validate_config(self):
        """Load and validate config."""
        config_model = Config(**self.config)
        return config_model

    def _load_mesh(self, input_path):
        """Load the pre-processed mesh."""
        logger = get_logger(__name__)
        logger.info(f"Loading pre-processed mesh from {input_path}")
        if not input_path.exists():
            raise FileNotFoundError(
                f"Input file {input_path} does not exist. "
                "Ensure previous steps have run."
            )
        mesh = pv.read(str(input_path))
        return mesh

    def _process_sections(self, mesh, z_sections, chordwise_mesh, webs_config):
        """Process each section."""
        logger = get_logger(__name__)
        logger.info("Processing sections")
        sections = []
        for z in z_sections:
            af = self.process_section_from_mesh(
                mesh, z, chordwise_mesh.model_dump(), webs_config, logger
            )
            sections.append(af)
        return sections

    def _merge_and_save_mesh(self, sections, output_path):
        """Merge meshes and save."""
        logger = get_logger(__name__)
        logger.info("Merging meshes into single PolyData")
        # Create meshes
        meshes = [af.to_pyvista() for af in sections]
        rmeshes = []
        # Translate point arrays to cell arrays before merging
        for mesh in meshes:
            rmeshes.append(
                mesh.point_data_to_cell_data(progress_bar=False, pass_point_data=True)
            )
            for key in ["Normals", "z"]:
                if key in mesh.cell_data:
                    del mesh.cell_data[key]
        # Merge into single UnstructuredGrid
        merged_mesh = pv.merge(rmeshes)
        # Manually concatenate constant fields if present
        for field in mesh.point_data.keys():
            if rmeshes and field in rmeshes[0].cell_data:
                merged_values = np.concatenate(
                    [rmesh.cell_data[field] for rmesh in rmeshes]
                )
                merged_mesh.cell_data[field] = merged_values

        # Convert to PolyData for VTP
        poly = pv.PolyData()
        poly.points = merged_mesh.points
        poly.lines = merged_mesh.lines
        for key, value in merged_mesh.cell_data.items():
            poly.cell_data[key] = value
        for key, value in merged_mesh.point_data.items():
            poly.point_data[key] = value

        # Save to VTP
        output_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"Saving merged mesh to {output_path}")
        poly.save(str(output_path))
        logger.info(f"Saved remeshed blade mesh to {output_path}")

    def _execute(self):
        """Execute the step."""
        self.logger.info("Executing B3MshStep: Processing blade mesh.")
        self._expand_mesh_z()
        config_model = self._load_and_validate_config()
        get_logger(__name__)

        config_dir = Path(self.config_path).parent
        workdir = config_dir / config_model.workdir
        mesh_config = config_model.mesh
        z_sections = mesh_config.z
        chordwise_mesh = mesh_config.chordwise
        webs_config = config_model.structure.webs

        input_path = workdir / "b3_geo" / "lm1_mesh.vtp"
        mesh = self._load_mesh(input_path)

        sections = self._process_sections(mesh, z_sections, chordwise_mesh, webs_config)
        output_path = workdir / "b3_msh" / "lm2.vtp"
        self._merge_and_save_mesh(sections, output_path)

    def process_section_from_mesh(self, mesh, z, chordwise_mesh, webs_config, logger):
        """Process a single section mesh by remeshing with uniform t distribution."""
        logger.debug(f"Processing section at z={z}")

        # Extract points at this z
        mask = np.isclose(mesh.points[:, 2], z)
        section_points = mesh.points[mask]
        # Sort by associated t pointdata
        t_values = mesh.point_data["t"][mask]
        sorted_indices = np.argsort(t_values)
        sorted_points = section_points[sorted_indices]
        points_2d = sorted_points[:, :2]  # Take x,y

        # Create Airfoil from points
        af = Airfoil(points_2d, is_normalized=False, position=(0, 0, z))  # Position at z

        # Add constant fields from input mesh
        af.constant_fields = {}
        for field in mesh.point_data.keys():
            values = mesh.point_data[field][mask]
            if np.allclose(values, values[0]):
                af.constant_fields[field] = values[0]

        # Add shear webs if applicable
        for web in webs_config:
            if web.mesh:
                z_range = web.z_range
                if z_range[0] <= z <= z_range[1]:
                    sw_def = {
                        "type": web.type,
                        "origin": [web.origin[0], web.origin[1], z],
                        "normal": web.orientation,
                        "name": web.name,
                    }
                    sw = ShearWeb(sw_def)
                    af.add_shear_web(sw, n_elements=10)  # Default n_elements
                    logger.debug(f"Added shear web {web.name} at z={z}")

        # Add trailing edge shear web
        sw_te = ShearWeb({"type": "trailing_edge", "name": "trailing_edge"})
        af.add_shear_web(sw_te, n_elements=5)
        logger.debug(f"Added trailing edge shear web at z={z}")

        # Remesh with uniform t distribution
        n_elem = chordwise_mesh["default"]["n_elem"]
        logger.debug(f"Remeshing with {n_elem} elements")
        af.remesh(total_n_points=n_elem + 1)

        return af
