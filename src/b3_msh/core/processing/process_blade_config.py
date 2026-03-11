import logging
import os

import numpy as np
import pyvista as pv

from ...utils.logger import get_logger
from .blade_load_config import blade_load_config
from .blade_process_sections import blade_process_sections
from .blade_save_vtp import blade_save_vtp
from .blade_save_vtm import blade_save_vtm

def process_blade_config(config_path, output_format="vtp", verbose=False):
    """Process blade from YAML config."""
    logger = get_logger("processing")
    if verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    logger.info(f"Processing blade from {config_path}")

    config_data = blade_load_config(config_path)
    config_dir = os.path.dirname(os.path.abspath(config_path))
    workdir = os.path.join(config_dir, config_data["workdir"])
    mesh_config = config_data["mesh"]
    chordwise_mesh = mesh_config["chordwise"]
    webs_config = config_data["structure"]["webs"]

    input_path = os.path.join(workdir, "b3_geo", "lm1_mesh.vtp")
    logger.info(f"Loading pre-processed mesh from {input_path}")
    mesh = pv.read(input_path)

    z_sections = np.unique(mesh.points[:, 2])
    z_sections = np.sort(z_sections)
    logger.info(f"Found {len(z_sections)} z sections: {np.round(z_sections, 2).tolist()}")

    sections = blade_process_sections(logger, mesh, z_sections, chordwise_mesh, webs_config)

    if output_format == "vtm":
        output_path = os.path.join(workdir, "b3_msh", "lm2.vtm")
        blade_save_vtm(logger, sections, output_path)
    else:
        output_path = os.path.join(workdir, "b3_msh", "lm2.vtp")
        blade_save_vtp(logger, sections, output_path)

    logger.info(f"Saved remeshed blade mesh to {output_path}")
