import os
import numpy as np
import pyvista as pv
import yaml
from pathlib import Path
from b3_msh.core.mesh_model import Config
from b3_msh.step.mesh_base import MeshBaseStep, process_section_from_mesh
from b3_msh.utils.logger import get_logger


def load_yaml_config(config_path):
    """Load and validate YAML configuration file."""
    with open(config_path) as f:
        config_dict = yaml.safe_load(f)
    config = Config.model_validate(config_dict)
    return config


def main():
    logger = get_logger(__name__)
    logger.info("Starting blade remeshing")

    config_path = "examples/blade_test.yml"
    config = load_yaml_config(config_path)
    logger.info(f"Loaded config with {len(config.mesh.meshes)} meshes")

    workdir_path = Path(config.workdir).resolve()
    input_path = workdir_path / "b3_geo" / "lm1_mesh.vtp"
    
    logger.info(f"Loading pre-processed mesh from {input_path}")
    if not input_path.exists():
        raise FileNotFoundError(f"{input_path} not found")
    
    mesh = pv.read(str(input_path))
    logger.info(f"Loaded mesh: {mesh.n_points} points, {mesh.n_cells} cells")

    # Process each mesh configuration
    for mesh_config in config.mesh.meshes:
        logger.info(f"\n--- Processing mesh '{mesh_config.name}' ({mesh_config.type}) ---")
        
        # Expand z-locations
        z_values = []
        for z_spec in mesh_config.z:
            if z_spec.type == "plain":
                z_values.extend(z_spec.values)
            elif z_spec.type == "linspace":
                z_values.extend(
                    np.linspace(z_spec.values[0], z_spec.values[1], z_spec.num)
                )
        z_values = sorted(list(set(z_values)))
        logger.info(f"  z-sections: {len(z_values)} locations")
        
        chordwise_mesh = mesh_config.chordwise.model_dump()
        webs_config_dict = [web.model_dump() for web in config.structure.webs]

        # Process sections
        sections = []
        for z in z_values:
            logger.info(f"  Processing section z={z:.1f}")
            af = process_section_from_mesh(
                mesh, z, chordwise_mesh, webs_config_dict, logger
            )
            sections.append(af)

        # Save outputs based on mesh type
        output_dir = workdir_path / "b3_msh"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        if mesh_config.type == "line":
            # Line mesh outputs
            vtp_path = output_dir / f"lm2_{mesh_config.name}_line.vtp"
            vtm_path = output_dir / f"lm2_{mesh_config.name}_line.vtm"
            
            # Save VTP (merged)
            from b3_msh.step.mesh_line import B3MshLineStep
            B3MshLineStep._merge_line_meshes(sections, vtp_path)  # Static method
            logger.info(f"  Saved merged line mesh: {vtp_path}")
            
            # Save VTM (MultiBlock)
            multi_block = pv.MultiBlock()
            for i, af in enumerate(sections):
                mesh_out = af.to_pyvista()
                multi_block.append(mesh_out, f"z_{z_values[i]:.1f}")
            multi_block.save(str(vtm_path))
            logger.info(f"  Saved MultiBlock: {vtm_path}")
            
        elif mesh_config.type == "surface":
            # Surface mesh (stub for now)
            from b3_msh.step.mesh_surface import B3MshSurfaceStep
            from b3_msh.core.surface_mesh import generate_surface_mesh
            surface_mesh = generate_surface_mesh(
                sections,
                spanwise_n_elem=mesh_config.spanwise_n_elem,
                closure=mesh_config.closure
            )
            vtp_path = output_dir / f"lm2_{mesh_config.name}_surface.vtp"
            surface_mesh.save(str(vtp_path))
            logger.info(f"  Saved surface mesh: {vtp_path} ({surface_mesh.n_cells:,} cells)")

        logger.info(f"  Mesh '{mesh_config.name}' complete")

    logger.info("All meshes processed successfully")


if __name__ == "__main__":
    main()
