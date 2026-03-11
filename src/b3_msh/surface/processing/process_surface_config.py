import logging
import os

import numpy as np
import pyvista as pv

from b3_msh.utils.logger import get_logger
from .surface_build_faces import surface_build_faces
from .surface_build_point_data import surface_build_point_data
from .surface_collect_section_data import surface_collect_section_data
from .surface_load_config import surface_load_config
from .surface_process_sections import surface_process_sections


def process_surface_config(config_path, verbose=False):
    """Process surface mesh from YAML config."""
    logger = get_logger("processing")
    if verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    logger.info(f"Processing surface mesh from {config_path}")

    config = surface_load_config(config_path)
    if config is None:
        return
    workdir, chordwise_mesh, webs_config = config

    input_path = os.path.join(workdir, "b3_geo", "lm1_mesh3d.vtp")
    logger.info(f"Loading pre-processed mesh from {input_path}")
    mesh = pv.read(input_path)

    z_sections = np.unique(mesh.points[:, 2])
    z_sections = np.sort(z_sections)
    logger.info(f"Found {len(z_sections)} z sections: {np.round(z_sections, 2).tolist()}")

    sections = surface_process_sections(logger, mesh, z_sections, chordwise_mesh, webs_config)

    section_data = surface_collect_section_data(sections)
    all_points, all_faces = surface_build_faces(section_data, sections)
    point_data_global = surface_build_point_data(section_data, sections)

    surface_mesh = pv.PolyData(all_points, faces=all_faces)
    for key, arr in point_data_global.items():
        surface_mesh.point_data[key] = arr

    output_path = os.path.join(workdir, "b3_msh", "lm2_surface_mesh.vtp")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    logger.info(
        f"Surface mesh created with {surface_mesh.n_points} points, {surface_mesh.n_cells} cells"
    )
    logger.info(f"Saving surface mesh to {output_path}")
    surface_mesh.save(output_path)
    logger.info(f"Saved surface mesh to {output_path}")
