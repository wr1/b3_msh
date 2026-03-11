"""Save blade mesh as VTP (one function)."""

import os


def blade_save_vtp(logger, sections, output_path):
    """Save as VTP."""
    from .blade_merge_meshes import blade_merge_meshes

    poly = blade_merge_meshes(logger, sections)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    logger.info(f"Saving merged mesh to {output_path}")
    poly.save(output_path)
