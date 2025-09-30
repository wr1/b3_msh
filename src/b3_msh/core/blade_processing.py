"""Core functionality for processing blade sections."""
import numpy as np
from .airfoil import Airfoil
from .shear_web import ShearWeb
from ..utils.logger import get_logger


def process_section_from_mesh(mesh, z, chordwise_mesh, webs_config, logger):
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
        if web.get("mesh", False):
            z_range = web["z_range"]
            if z_range[0] <= z <= z_range[1]:
                sw_def = {
                    "type": web["type"],
                    "origin": [web["origin"][0], web["origin"][1], z],
                    "normal": web["orientation"],
                    "name": web["name"],
                }
                sw = ShearWeb(sw_def)
                af.add_shear_web(sw, n_elements=10)  # Default n_elements
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
