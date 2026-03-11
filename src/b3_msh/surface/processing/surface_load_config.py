import os

from b3_msh.utils.logger import get_logger

from .blade_load_config import blade_load_config


def surface_load_config(config_path):
    """Load config for surface processing."""
    config_data = blade_load_config(config_path)
    config_dir = os.path.dirname(os.path.abspath(config_path))
    workdir = os.path.join(config_dir, config_data["workdir"])
    mesh3d_config = config_data.get("mesh3d")
    if not mesh3d_config:
        logger = get_logger("processing")
        logger.error("mesh3d section required for surface meshing")
        return None
    chordwise_mesh = mesh3d_config["chordwise"]
    webs_config = config_data["structure"]["webs"]
    return workdir, chordwise_mesh, webs_config
