"""Save blade mesh as VTM (one function)."""

import os
import pyvista as pv


def blade_save_vtm(logger, sections, output_path):
    """Save as VTM."""
    logger.info("Creating new MultiBlock mesh")
    new_multi_block = pv.MultiBlock()
    for i, af in enumerate(sections):
        mesh_out = af.to_pyvista()
        new_multi_block.append(mesh_out, f"Section_{i}")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    logger.info(f"Saving mesh to {output_path}")
    new_multi_block.save(output_path)
