"""Collect section data for surface (one function)."""

def surface_collect_section_data(sections):
    """Collect section data."""
    section_data = []
    for af in sections:
        pv_mesh = af.to_pyvista()
        points = pv_mesh.points
        lines = pv_mesh.lines.reshape(-1, 3)[:, 1:]
        panel_ids = pv_mesh.cell_data["panel_id"]
        n_airfoil = len(af.current_points)
        section_data.append(
            {
                "points": points,
                "lines": lines,
                "panel_ids": panel_ids,
                "n_points": len(points),
                "n_airfoil": n_airfoil,
                "point_data": {k: v.copy() for k, v in pv_mesh.point_data.items()},
            }
        )
    return section_data
