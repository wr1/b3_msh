import os
import numpy as np
import pyvista as pv
import yaml
from pathlib import Path
from b3_msh.core.mesh_model import Config
from b3_msh.step.mesh_base import MeshBaseStep
from b3_msh.utils.logger import get_logger


def load_yaml_config(config_path):
    """Load and validate YAML configuration file."""
    with open(config_path) as f:
        config_dict = yaml.safe_load(f)
    config = Config.model_validate(config_dict)
    return config


def main():
    logger = get_logger(__name__)
    logger.info("Starting blade surface remeshing")

    config_path = "examples/blade_test_ribbon.yml"
    logger.info(f"Loading config from {config_path}")
    config = load_yaml_config(config_path)
    logger.info(f"Loaded config with workdir: {config.workdir}, {len(config.mesh)} meshes")

    config_dir = os.path.dirname(os.path.abspath(config_path))
    workdir = os.path.join(config_dir, config.workdir)
    workdir_path = Path(workdir)
    
    # Find surface mesh config
    mesh_config = next((m for m in config.mesh if m.type == "surface"), None)
    if not mesh_config:
        logger.error("No surface mesh config found")
        return
    
    input_path = workdir_path / "b3_geo" / f"lm1_{mesh_config.name}.vtp"
    
    logger.info(f"Loading pre-processed mesh from {input_path}")
    if not input_path.exists():
        raise FileNotFoundError(f"{input_path} not found")
    
    mesh = pv.read(str(input_path))
    logger.info(f"Loaded mesh: {mesh.n_points} points, {mesh.n_cells} cells")
    logger.info(f"Point data keys: {list(mesh.point_data.keys())}")
    logger.info(f"Cell data keys: {list(mesh.cell_data.keys())}")
    
    logger.info(f"\n--- Processing mesh '{mesh_config.name}' ({mesh_config.type}) ---")
    
    # Expand z-locations
    z_values = []
    for z_spec in mesh_config.z:
        if z_spec["type"] == "plain":
            z_values.extend(z_spec["values"])
        elif z_spec["type"] == "linspace":
            z_values.extend(
                np.linspace(
                    z_spec["values"][0], z_spec["values"][1], z_spec["num"]
                )
            )
    z_values = sorted(list(set(z_values)))
    logger.info(f"  z-sections: {len(z_values)} locations")
    
    chordwise_mesh = mesh_config.chordwise.model_dump()
    webs_config_dict = [web.model_dump() for web in config.structure.webs]

    # Process sections
    logger.info(f"  Processing {len(z_values)} sections")
    sections = []
    for z in z_values:
        af = MeshBaseStep.process_section_from_mesh(
            mesh, z, chordwise_mesh, webs_config_dict, logger
        )
        sections.append(af)

    # Surface mesh
    from b3_msh.core.surface_mesh import generate_surface_mesh
    surface_mesh = generate_surface_mesh(sections)
    output_dir = workdir_path / "b3_msh"
    output_dir.mkdir(parents=True, exist_ok=True)
    vtp_path = output_dir / f"lm2_{mesh_config.name}_surface.vtp"
    surface_mesh.save(str(vtp_path))
    logger.info(f"  Saved surface mesh: {vtp_path} ({surface_mesh.n_cells:,} cells)")

    logger.info("Surface mesh processing complete")


if __name__ == "__main__":
    main()
