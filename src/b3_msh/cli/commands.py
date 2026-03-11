import logging

import numpy as np

from b3_msh.meshing.airfoil import Airfoil
from b3_msh.multiline.processing.process_blade_config import process_blade_config
from b3_msh.surface.processing.process_surface_config import process_surface_config
from b3_msh.utils.logger import get_logger


def plot(
    file: str,
    chord: float = 1.0,
    px=0,
    py=0,
    pz=0,
    rotation: float = 0,
    verbose: bool = False,
):
    """Plot an airfoil from file."""
    logger = get_logger("CLI")
    if verbose:
        logger.setLevel(logging.DEBUG)
        logger.info("Verbose logging enabled")
    else:
        logger.setLevel(logging.WARNING)
    logger.info(f"Plotting airfoil from {file}")
    af = Airfoil.from_xfoil(
        file,
        chord=chord,
        position=(px, py, pz),
        rotation=rotation,
    )
    af.plot()
    logger.debug("Plot command completed")


def remesh(
    file: str,
    output: str,
    n_points: int = 100,
    verbose: bool = False,
):
    """Remesh an airfoil and save."""
    logger = get_logger("CLI")
    if verbose:
        logger.setLevel(logging.DEBUG)
        logger.info("Verbose logging enabled")
    else:
        logger.setLevel(logging.WARNING)
    logger.info(f"Remeshing airfoil from {file}")
    af = Airfoil.from_xfoil(file)
    af.remesh(n_points=n_points)
    np.savetxt(output, af.current_points[:, :2], header="x y", comments="")
    logger.info(f"Remeshed points saved to {output}")
    logger.debug("Remesh command completed")


def blade(config: str, output_format: str = "vtp", verbose: bool = False):
    """Process blade from YAML config."""
    process_blade_config(config, output_format, verbose)


def surface(config: str, verbose: bool = False):
    """Process surface mesh from YAML config."""
    process_surface_config(config, verbose)
