"""Merge meshes into single PolyData (one function)."""

import numpy as np
import pyvista as pv

def blade_merge_meshes(logger, sections):
    """Merge meshes into single PolyData."""
    logger.info("Merging meshes into single PolyData")
    meshes = [af.to_pyvista() for af in sections]
    rmeshes = []
    for mesh in meshes:
        rmeshes.append(mesh.point_data_to_cell_data(progress_bar=False, pass_point_data=True))
        for key in ["Normals", "z"]:
            if key in mesh.cell_data:
                del mesh.cell_data[key]
    all_keys = set()
    dtype_dict = {}
    for mesh in rmeshes:
        for key in mesh.cell_data.keys():
            all_keys.add(key)
            if key not in dtype_dict:
                dtype_dict[key] = mesh.cell_data[key].dtype
    for mesh in rmeshes:
        for key in all_keys:
            if key not in mesh.cell_data:
                mesh.cell_data[key] = np.zeros(mesh.n_cells, dtype=dtype_dict[key])
    merged_mesh = pv.merge(rmeshes)
    poly = pv.PolyData()
    poly.points = merged_mesh.points
    poly.lines = merged_mesh.lines
    for key, value in merged_mesh.cell_data.items():
        poly.cell_data[key] = value
    for key, value in merged_mesh.point_data.items():
        poly.point_data[key] = value
    return poly
