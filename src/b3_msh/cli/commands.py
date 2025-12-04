import logging
import numpy as np
import os
import yaml
import pyvista as pv
from ..core.airfoil import Airfoil
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


def _load_config(config_path):
    """Load YAML config."""
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def _process_sections(logger, mesh, z_sections, chordwise_mesh, webs_config):
    """Process sections from mesh."""
    logger.info("Processing sections")
    sections = []
    for z in z_sections:
        af = process_section_from_mesh(mesh, z, chordwise_mesh, webs_config, logger)
        sections.append(af)
    return sections


def _save_as_vtm(logger, sections, output_path):
    """Save as VTM."""
    logger.info("Creating new MultiBlock mesh")
    new_multi_block = pv.MultiBlock()
    for i, af in enumerate(sections):
        mesh_out = af.to_pyvista()
        new_multi_block.append(mesh_out, f"Section_{i}")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    logger.info(f"Saving mesh to {output_path}")
    new_multi_block.save(output_path)


def _save_as_vtp(logger, sections, output_path):
    """Save as VTP."""
    logger.info("Merging meshes into single PolyData")
    meshes = [af.to_pyvista() for af in sections]
    rmeshes = []
    for mesh in meshes:
        rmeshes.append(
            mesh.point_data_to_cell_data(progress_bar=False, pass_point_data=True)
        )
        for key in ["Normals", "z"]:
            if key in mesh.cell_data:
                del mesh.cell_data[key]
    merged_mesh = pv.merge(rmeshes)
    for field in mesh.point_data.keys():
        if rmeshes and field in rmeshes[0].cell_data:
            merged_values = np.concatenate(
                [rmesh.cell_data[field] for rmesh in rmeshes]
            )
            merged_mesh.cell_data[field] = merged_values
    poly = pv.PolyData()
    poly.points = merged_mesh.points
    poly.lines = merged_mesh.lines
    for key, value in merged_mesh.cell_data.items():
        poly.cell_data[key] = value
    for key, value in merged_mesh.point_data.items():
        poly.point_data[key] = value
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    logger.info(f"Saving merged mesh to {output_path}")
    poly.save(output_path)


def blade(config: str, output_format: str = "vtp", verbose: bool = False):
    """Process blade from YAML config."""
    logger = get_logger("CLI")
    if verbose:
        logger.setLevel(logging.DEBUG)
        logger.info("Verbose logging enabled")
    else:
        logger.setLevel(logging.INFO)
    logger.info(f"Processing blade from {config}")

    config_data = _load_config(config)
    config_dir = os.path.dirname(os.path.abspath(config))
    workdir = os.path.join(config_dir, config_data["workdir"])
    mesh_config = config_data["mesh"]
    chordwise_mesh = mesh_config["chordwise"]
    webs_config = config_data["structure"]["webs"]

    input_path = os.path.join(workdir, "b3_geo", "lm1_mesh.vtp")
    logger.info(f"Loading pre-processed mesh from {input_path}")
    mesh = pv.read(input_path)

    z_sections = np.unique(mesh.points[:, 2])
    z_sections = np.sort(z_sections)
    logger.info(
        f"Found {len(z_sections)} z sections: {np.round(z_sections, 2).tolist()}"
    )

    sections = _process_sections(logger, mesh, z_sections, chordwise_mesh, webs_config)

    if output_format == "vtm":
        output_path = os.path.join(workdir, "b3_msh", "lm2.vtm")
        _save_as_vtm(logger, sections, output_path)
    else:
        output_path = os.path.join(workdir, "b3_msh", "lm2.vtp")
        _save_as_vtp(logger, sections, output_path)

    logger.info(f"Saved remeshed blade mesh to {output_path}")
