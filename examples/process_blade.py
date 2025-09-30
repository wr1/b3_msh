import os
import yaml
import numpy as np
import pyvista as pv
import logging
from b3_msh.core.airfoil import Airfoil
from b3_msh.core.shear_web import ShearWeb
from b3_msh.utils.logger import get_logger

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def load_yaml_config(config_path):
    """Load YAML configuration file."""
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    return config


def process_section_from_mesh(mesh, z, chordwise_mesh, webs_config, logger):
    """Process a single section mesh by remeshing with uniform t distribution."""
    logger.info(f"Processing section at z={z}")

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
                logger.info(f"Added shear web {web['name']} at z={z}")

    # Add trailing edge shear web
    sw_te = ShearWeb({"type": "trailing_edge", "name": "trailing_edge"})
    af.add_shear_web(sw_te, n_elements=5)
    logger.info(f"Added trailing edge shear web at z={z}")

    # Remesh with uniform t distribution
    n_elem = chordwise_mesh["default"]["n_elem"]
    logger.info(f"Remeshing with {n_elem} elements")
    af.remesh(total_n_points=n_elem + 1)

    return af


def main():
    logger = get_logger(__name__)
    logger.info("Starting blade remeshing")

    config_path = "config/data/blade_test.yml"
    logger.info(f"Loading config from {config_path}")
    config = load_yaml_config(config_path)

    print(config_path)

    workdir = config["workdir"]
    mesh_config = config["mesh"]
    z_specs = mesh_config["z"]
    z_values = []
    for z_spec in z_specs:
        if z_spec["type"] == "plain":
            z_values.extend(z_spec["values"])
        elif z_spec["type"] == "linspace":
            z_values.extend(np.linspace(z_spec["values"][0], z_spec["values"][1], z_spec["num"]))
    chordwise_mesh = mesh_config["chordwise"]
    webs_config = config["structure"]["webs"]

    # Load the pre-processed mesh
    input_path = os.path.join("examples", workdir, "b3_geo", "lm1_mesh.vtp")
    logger.info(f"Loading pre-processed mesh from {input_path}")
    mesh = pv.read(input_path)

    logger.info("Processing sections")
    # Process each section
    sections = []
    for z in z_values:
        af = process_section_from_mesh(mesh, z, chordwise_mesh, webs_config, logger)
        sections.append(af)

    logger.info("Creating new MultiBlock mesh")
    # Create new MultiBlock
    new_multi_block = pv.MultiBlock()
    for i, af in enumerate(sections):
        mesh_out = af.to_pyvista()
        new_multi_block.append(mesh_out, f"Section_{i}")

    # Save to VTM (MultiBlock format)
    output_path = os.path.join("examples", workdir, "b3_msh", "lm2.vtm")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    logger.info(f"Saving mesh to {output_path}")
    new_multi_block.save(output_path)
    logger.info(f"Saved remeshed blade mesh to {output_path}")


if __name__ == "__main__":
    main()
