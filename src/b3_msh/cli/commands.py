"""CLI command implementations."""
import logging
import numpy as np
import os
import yaml
import pyvista as pv
from ..core.airfoil import Airfoil
from ..core.shear_web import ShearWeb
from ..utils.logger import get_logger
from ..core.blade_processing import process_section_from_mesh


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


def blade(config: str, verbose: bool = False):
    """Process blade from YAML config."""
    logger = get_logger("CLI")
    if verbose:
        logger.setLevel(logging.DEBUG)
        logger.info("Verbose logging enabled")
    else:
        logger.setLevel(logging.INFO)
    logger.info(f"Processing blade from {config}")
    
    # Load config
    with open(config, "r") as f:
        config_data = yaml.safe_load(f)
    
    config_dir = os.path.dirname(os.path.abspath(config))
    workdir = os.path.join(config_dir, config_data["workdir"])
    mesh_config = config_data["mesh"]
    chordwise_mesh = mesh_config["chordwise"]
    webs_config = config_data["structure"]["webs"]
    
    # Load the pre-processed mesh
    input_path = os.path.join(workdir, "b3_geo", "lm1_mesh.vtp")
    logger.info(f"Loading pre-processed mesh from {input_path}")
    mesh = pv.read(input_path)
    
    # Get z sections from mesh
    z_sections = np.unique(mesh.points[:, 2])
    z_sections = np.sort(z_sections)
    logger.info(f"Found {len(z_sections)} z sections: {np.round(z_sections, 2).tolist()}")
    
    logger.info("Processing sections")
    # Process each section
    sections = []
    for z in z_sections:
        af = process_section_from_mesh(mesh, z, chordwise_mesh, webs_config, logger)
        sections.append(af)
    
    logger.info("Creating new MultiBlock mesh")
    # Create new MultiBlock
    new_multi_block = pv.MultiBlock()
    for i, af in enumerate(sections):
        mesh_out = af.to_pyvista()
        new_multi_block.append(mesh_out, f"Section_{i}")
    
    # Save to VTM (MultiBlock format)
    output_path = os.path.join(workdir, "b3_msh", "lm2.vtm")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    logger.info(f"Saving mesh to {output_path}")
    new_multi_block.save(output_path)
    logger.info(f"Saved remeshed blade mesh to {output_path}")
