"""Build global point data (one function - fixes length mismatch)."""

import numpy as np

def surface_build_point_data(section_data, sections):
    """Build point_data_global (robust to web points)."""
    all_point_data_keys = set()
    point_dtype = {}
    for sec_data in section_data:
        for k in sec_data["point_data"]:
            all_point_data_keys.add(k)
            if k not in point_dtype:
                point_dtype[k] = sec_data["point_data"][k].dtype
    new_keys = ["dist_from_te", "chordwise_coord", "spanwise_coord"]
    for key in new_keys:
        all_point_data_keys.add(key)
        point_dtype[key] = float
    all_z = [af.position[2] for af in sections]
    min_z = min(all_z)
    max_z = max(all_z)
    span_range = max_z - min_z if max_z > min_z else 1.0
    point_data_global = {}
    for key in all_point_data_keys:
        arrays = []
        for i, sec_data in enumerate(section_data):
            af = sections[i]
            n_airfoil = sec_data["n_airfoil"]
            n_total = sec_data["n_points"]
            if key in sec_data["point_data"]:
                arrays.append(sec_data["point_data"][key])
            elif key == "dist_from_te":
                diffs = np.diff(af.current_points, axis=0)
                arc_lengths = np.sqrt(np.sum(diffs**2, axis=1))
                cum_arc = np.cumsum(arc_lengths)
                cum_arc = np.insert(cum_arc, 0, 0)
                total_arc = cum_arc[-1]
                dist_from_te = total_arc - cum_arc
                pad = np.full(n_total - n_airfoil, np.nan)
                arrays.append(np.concatenate([dist_from_te, pad]))
            elif key == "chordwise_coord":
                chordwise = af.current_t
                pad = np.full(n_total - n_airfoil, np.nan)
                arrays.append(np.concatenate([chordwise, pad]))
            elif key == "spanwise_coord":
                z_val = af.position[2]
                spanwise = (z_val - min_z) / span_range
                arrays.append(np.full(n_total, spanwise))
            else:
                pad = np.full(n_total, np.nan, dtype=point_dtype[key])
                arrays.append(pad)
        point_data_global[key] = np.concatenate(arrays)
    return point_data_global
