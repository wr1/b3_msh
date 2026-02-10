"""Core processing functions for blade and surface meshing, shared between CLI and API."""

import os

import numpy as np
import pyvista as pv
import yaml

from ..step.blade_mesh_step import B3MshStep
from ..utils.logger import get_logger


def _load_config(config_path):
    """Load YAML config."""
    with open(config_path) as f:
        return yaml.safe_load(f)


def _process_sections(logger, mesh, z_sections, chordwise_mesh, webs_config):
    """Process sections from mesh."""
    logger.info("Processing sections")
    sections = []
    for z in z_sections:
        af = B3MshStep.process_section_from_mesh(
            mesh, z, chordwise_mesh, webs_config, logger
        )
        sections.append(af)
    return sections


def _save_as_vtm(logger, sections, output_path):
    """Save as VTM."""
    logger.info("Creating new MultiBlock mesh")
    new_multi_block = pv.MultiBlock()
    for i, af in enumerate(sections):
        mesh_out = af.to_pyvista()
        logger.info(f"Section {i} arrays: point_data {list(mesh_out.point_data.keys())}, cell_data {list(mesh_out.cell_data.keys())}")
        new_multi_block.append(mesh_out, f"Section_{i}")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    logger.info(f"Saving mesh to {output_path}")
    new_multi_block.save(output_path)


def _save_as_vtp(logger, sections, output_path):
    """Save as VTP."""
    logger.info("Merging meshes into single PolyData")
    meshes = [af.to_pyvista() for af in sections]
    for i, mesh in enumerate(meshes):
        logger.info(f"Section {i} arrays: point_data {list(mesh.point_data.keys())}, cell_data {list(mesh.cell_data.keys())}")
    rmeshes = []
    for mesh in meshes:
        rmeshes.append(
            mesh.point_data_to_cell_data(progress_bar=False, pass_point_data=True)
        )
        for key in ["Normals", "z"]:
            if key in mesh.cell_data:
                del mesh.cell_data[key]
    # Collect all unique cell_data keys across all meshes
    all_keys = set()
    dtype_dict = {}
    for mesh in rmeshes:
        for key in mesh.cell_data.keys():
            all_keys.add(key)
            if key not in dtype_dict:
                dtype_dict[key] = mesh.cell_data[key].dtype
    # For each mesh, add missing keys with zero arrays
    for mesh in rmeshes:
        for key in all_keys:
            if key not in mesh.cell_data:
                mesh.cell_data[key] = np.zeros(mesh.n_cells, dtype=dtype_dict[key])
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


def process_blade_config(config_path, output_format="vtp", verbose=False):
    """Process blade from YAML config."""
    logger = get_logger("processing")
    if verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    logger.info(f"Processing blade from {config_path}")

    config_data = _load_config(config_path)
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


def process_surface_config(config_path, verbose=False):
    """Process surface mesh from YAML config."""
    logger = get_logger("processing")
    if verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    logger.info(f"Processing surface mesh from {config_path}")

    config_data = _load_config(config_path)
    config_dir = os.path.dirname(os.path.abspath(config_path))
    workdir = os.path.join(config_dir, config_data["workdir"])
    mesh3d_config = config_data.get("mesh3d")
    if not mesh3d_config:
        logger.error("mesh3d section required for surface meshing")
        return
    chordwise_mesh = mesh3d_config["chordwise"]
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

    # Create surface mesh
    all_points = []
    all_faces = []
    point_offset = 0

    section_data = []
    for af in sections:
        pv_mesh = af.to_pyvista()
        points = pv_mesh.points
        lines = pv_mesh.lines.reshape(-1, 3)[:, 1:]
        panel_ids = pv_mesh.cell_data["panel_id"]
        section_data.append({
            "points": points,
            "lines": lines,
            "panel_ids": panel_ids,
            "n_points": len(points)
        })

    for i in range(len(sections) - 1):
        sec1 = section_data[i]
        sec2 = section_data[i + 1]

        # Airfoil panels
        airfoil_lines1 = sec1["lines"][sec1["panel_ids"] >= 0]
        airfoil_lines2 = sec2["lines"][sec2["panel_ids"] >= 0]

        if len(airfoil_lines1) != len(airfoil_lines2):
            logger.error(f"Inconsistent airfoil elements between sections {i} and {i+1}")
            continue

        for j in range(len(airfoil_lines1)):
            p1 = airfoil_lines1[j][0] + point_offset
            p2 = airfoil_lines1[j][1] + point_offset
            p3 = airfoil_lines2[j][1] + point_offset + sec1["n_points"]
            p4 = airfoil_lines2[j][0] + point_offset + sec1["n_points"]
            all_faces.append([4, p1, p2, p3, p4])

        # Shear webs
        unique_panels = np.unique(sec1["panel_ids"])
        for panel_id in unique_panels:
            if panel_id < 0:
                lines1 = sec1["lines"][sec1["panel_ids"] == panel_id]
                lines2 = sec2["lines"][sec2["panel_ids"] == panel_id]
                if len(lines1) != len(lines2):
                    logger.warning(f"Inconsistent shear web elements for panel {panel_id}")
                    continue
                for j in range(len(lines1)):
                    p1 = lines1[j][0] + point_offset
                    p2 = lines1[j][1] + point_offset
                    p3 = lines2[j][1] + point_offset + sec1["n_points"]
                    p4 = lines2[j][0] + point_offset + sec1["n_points"]
                    all_faces.append([4, p1, p2, p3, p4])

        all_points.extend(sec1["points"])
        point_offset += sec1["n_points"]

    all_points.extend(section_data[-1]["points"])

    surface_mesh = pv.PolyData(np.array(all_points), faces=np.array(all_faces))
    output_path = os.path.join(workdir, "b3_msh", "lm2_surface_mesh.vtp")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    logger.info(f"Saving surface mesh to {output_path}")
    surface_mesh.save(output_path)
    logger.info(f"Saved surface mesh to {output_path}")
