"""Build surface faces (one function)."""

import numpy as np


def surface_build_faces(section_data, sections):
    """Build all_points and all_faces."""
    all_points = []
    all_faces = []
    point_offset = 0
    for i in range(len(sections) - 1):
        sec1 = section_data[i]
        sec2 = section_data[i + 1]
        airfoil_lines1 = sec1["lines"][sec1["panel_ids"] >= 0]
        airfoil_lines2 = sec2["lines"][sec2["panel_ids"] >= 0]
        if len(airfoil_lines1) != len(airfoil_lines2):
            continue
        for j in range(len(airfoil_lines1)):
            p1 = airfoil_lines1[j][0] + point_offset
            p2 = airfoil_lines1[j][1] + point_offset
            p3 = airfoil_lines2[j][1] + point_offset + sec1["n_points"]
            p4 = airfoil_lines2[j][0] + point_offset + sec1["n_points"]
            all_faces.append([4, p1, p2, p3, p4])
        unique_panels = np.unique(sec1["panel_ids"])
        for panel_id in unique_panels:
            if panel_id < 0:
                lines1 = sec1["lines"][sec1["panel_ids"] == panel_id]
                lines2 = sec2["lines"][sec2["panel_ids"] == panel_id]
                if len(lines1) != len(lines2):
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
    return np.array(all_points), np.array(all_faces)
