import os
import yaml
import numpy as np
import pyvista as pv
from b3_msh.core.airfoil import Airfoil
from b3_msh.core.shear_web import ShearWeb
from b3_msh.utils.logger import get_logger
from b3_msh.core.blade_processing import process_section_from_mesh


def load_yaml_config(config_path):
    """Load YAML configuration file."""
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    return config


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
    logger.info(f"Found z sections: {np.round(z_values, 2).tolist()}")
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
