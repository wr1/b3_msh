"""Statesman step for running b3_msh blade processing."""
import os
import numpy as np
import pyvista as pv
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from statesman.core.base import Statesman, ManagedFile
from .core.airfoil import Airfoil
from .core.shear_web import ShearWeb
from .utils.logger import get_logger


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
    output_files = ["b3_msh/lm2.vtm"]
    dependent_sections = ["geometry", "airfoils", "structure", "mesh"]

    def _execute(self):
        self.logger.info("Executing B3MshStep: Processing blade mesh.")
        # Validate config
        config_model = Config(**self.config)
        logger = get_logger(__name__)

        workdir = config_model.workdir
        mesh_config = config_model.mesh
        z_sections = mesh_config.z
        chordwise_mesh = mesh_config.chordwise
        webs_config = config_model.structure.webs

        # Load the pre-processed mesh
        input_path = os.path.join(workdir, "b3_geo", "lm1_mesh.vtp")
        logger.info(f"Loading pre-processed mesh from {input_path}")
        mesh = pv.read(input_path)

        logger.info("Processing sections")
        # Process each section
        sections = []
        for z in z_sections:
            af = self.process_section_from_mesh(mesh, z, chordwise_mesh.model_dump(), webs_config, logger)
            sections.append(af)

        logger.info("Creating new MultiBlock mesh")
        # Create new MultiBlock
        new_multi_block = pv.MultiBlock()
        for i, af in enumerate(sections):
            mesh_out = af.to_pyvista()
            new_multi_block.append(mesh_out, f"Section_{i}")

        # Save to VTM (MultiBlock format)
        output_path = os.path.join(workdir, "b3_msh", "lm2.vtm")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        logger.info(f"Saving mesh to {output_path}")
        new_multi_block.save(output_path)
        logger.info(f"Saved remeshed blade mesh to {output_path}")

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
