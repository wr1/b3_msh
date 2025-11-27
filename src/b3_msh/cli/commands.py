import logging
import numpy as np
import os
import yaml
import pyvista as pv
from ..utils.logger import get_logger
from ..core.blade_processing import process_section_from_mesh


def _load_config_and_mesh(config_path):
    """Load config and mesh."""
    with open(config_path, "r") as f:
        config_data = yaml.safe_load(f)
    config_dir = os.path.dirname(os.path.abspath(config_path))
    workdir = os.path.join(config_dir, config_data["workdir"])
    mesh_config = config_data["mesh"]
    chordwise_mesh = mesh_config["chordwise"]
    webs_config = config_data["structure"]["webs"]
    input_path = os.path.join(workdir, "b3_geo", "lm1_mesh.vtp")
    mesh = pv.read(input_path)
    return mesh, chordwise_mesh, webs_config


def _get_z_sections(mesh):
    """Get unique z sections from mesh."""
    z_sections = np.unique(mesh.points[:, 2])
    z_sections = np.sort(z_sections)
    return z_sections


def _process_sections(mesh, z_sections, chordwise_mesh, webs_config, logger):
    """Process each section."""
    sections = []
    for z in z_sections:
        af = process_section_from_mesh(mesh, z, chordwise_mesh, webs_config, logger)
        sections.append(af)
    return sections


def _save_as_vtm(sections, output_path):
    """Save as MultiBlock VTM."""
    new_multi_block = pv.MultiBlock()
    for i, af in enumerate(sections):
        mesh_out = af.to_pyvista()
        new_multi_block.append(mesh_out, f"Section_{i}")
    new_multi_block.save(output_path)


def _save_as_vtp(sections, output_path):
    """Save as merged PolyData VTP."""
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

    mesh, chordwise_mesh, webs_config = _load_config_and_mesh(config)
    z_sections = _get_z_sections(mesh)
    logger.info(f"Found {len(z_sections)} z sections")

    sections = _process_sections(mesh, z_sections, chordwise_mesh, webs_config, logger)

    config_dir = os.path.dirname(os.path.abspath(config))
    workdir = os.path.join(config_dir, config_data["workdir"])
    if output_format == "vtm":
        output_path = os.path.join(workdir, "b3_msh", "lm2.vtm")
        _save_as_vtm(sections, output_path)
    else:
        output_path = os.path.join(workdir, "b3_msh", "lm2.vtp")
        _save_as_vtp(sections, output_path)

    logger.info(f"Saved remeshed blade mesh to {output_path}")
