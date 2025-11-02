"""Visualization functionality for Airfoil, including plotting and PyVista export."""

import numpy as np
import pyvista as pv
import matplotlib.pyplot as plt
from ..utils.logger import get_logger


class AirfoilViz:
    """Visualization functionality for Airfoil, including plotting and PyVista export."""

    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)

    def to_pyvista(self):
        """Export to PyVista PolyData (line mesh)."""
        self.logger.debug("Exporting to PyVista")
        airfoil_points = self.current_points
        web_points = []
        web_w = []
        web_info = []  # list of (sw, start_idx, n_points_web)
        current_web_idx = len(airfoil_points)
        for sw in self.shear_webs:
            t1, t2 = sw.compute_intersections(self)
            p1 = self.get_points([t1])[0]
            p2 = self.get_points([t2])[0]
            n_elements = self.shear_web_n_elements[sw]
            n_points_web = n_elements + 1
            web_points.append(np.linspace(p1, p2, n_points_web))
            web_w.append(np.linspace(0, 1, n_points_web))
            web_info.append((sw, current_web_idx, n_points_web))
            current_web_idx += n_points_web
        if web_points:
            web_points = np.vstack(web_points)
            web_w = np.concatenate(web_w)
            all_points = np.vstack([airfoil_points, web_points])
        else:
            all_points = airfoil_points
            web_w = np.array([])
        n_points = len(all_points)
        lines = []
        # Airfoil lines
        for i in range(len(airfoil_points) - 1):
            lines.extend([2, i, i + 1])
        # Shear web lines
        for sw, start_idx, n_points_web in web_info:
            for i in range(n_points_web - 1):
                lines.extend([2, start_idx + i, start_idx + i + 1])
        lines = np.array(lines)
        poly = pv.PolyData(all_points, lines=lines)
        # Add panel id to cells
        panels = self.get_panels()
        n_airfoil_cells = len(airfoil_points) - 1
        total_cells = n_airfoil_cells
        for sw in self.shear_webs:
            n = self.shear_web_n_elements[sw]
            total_cells += n
        cell_data = np.zeros(total_cells, dtype=int)
        sorted_hp = sorted(self.hard_points)
        hp_indices = [
            np.where(np.isclose(self.current_t, hp))[0][0] for hp in sorted_hp
        ]
        for p_idx in range(len(hp_indices) - 1):
            start_idx = hp_indices[p_idx]
            end_idx = hp_indices[p_idx + 1]
            cell_data[start_idx:end_idx] = p_idx
        # Shear webs have panel_id = - (i + 1) for i in range(len(self.shear_webs))
        cell_start = n_airfoil_cells
        for i, sw in enumerate(self.shear_webs):
            panel_id_web = -(i + 1)
            n_cells_web = self.shear_web_n_elements[sw]
            cell_data[cell_start : cell_start + n_cells_web] = panel_id_web
            cell_start += n_cells_web
        poly.cell_data["panel_id"] = cell_data
        # Compute cumulative arc lengths
        diffs = np.diff(airfoil_points, axis=0)
        arc_lengths = np.sqrt(np.sum(diffs**2, axis=1))
        cum_arc = np.cumsum(arc_lengths)
        cum_arc = np.insert(cum_arc, 0, 0)
        # Add distances from hard points
        for hp in sorted(self.hard_points):
            name = self.hard_point_names[hp]
            hp_idx = np.where(np.isclose(self.current_t, hp))[0][0]
            abs_distances = np.abs(cum_arc - cum_arc[hp_idx])
            poly.point_data[f"abs_dist_{name}"] = np.concatenate(
                [abs_distances, np.zeros(len(all_points) - len(airfoil_points))]
            )
            rel_distances = np.abs(self.current_t - hp)
            poly.point_data[f"rel_dist_{name}"] = np.concatenate(
                [rel_distances, np.zeros(len(all_points) - len(airfoil_points))]
            )
        # Add t values
        poly.point_data["t"] = np.concatenate(
            [self.current_t, np.full(len(all_points) - len(airfoil_points), np.nan)]
        )
        # Add w values for webs
        poly.point_data["w"] = np.concatenate(
            [np.full(len(airfoil_points), np.nan), web_w]
        )
        # Add z values
        poly.point_data["z"] = all_points[:, 2]
        # Compute normal vectors for points
        normals_point = []
        for i in range(len(all_points)):
            if i < len(airfoil_points):
                # Airfoil point
                t = self.current_t[i]
                dx = self.spline_x.derivative()(t)
                dy = self.spline_y.derivative()(t)
                dz = self.spline_z.derivative()(t)
                tangent = np.array([dx, dy, dz])
                # Normal in xy plane
                normal = np.array([-tangent[1], tangent[0], 0])
                normal = (
                    normal / np.linalg.norm(normal)
                    if np.linalg.norm(normal) > 0
                    else np.array([0, 0, 1])
                )
                normals_point.append(normal)
            else:
                # Web point - compute normal in plane of mesh
                # Find which web this point belongs to
                web_idx = 0
                point_idx_in_web = i - len(airfoil_points)
                for sw_idx, (sw, start_idx, n_points_web) in enumerate(web_info):
                    if start_idx <= i < start_idx + n_points_web:
                        web_idx = sw_idx
                        break
                sw = self.shear_webs[web_idx]
                t1, t2 = sw.compute_intersections(self)
                p1 = self.get_points([t1])[0]
                p2 = self.get_points([t2])[0]
                direction = p2 - p1
                dx, dy, dz = direction
                normal = np.array([-dy, dx, 0])
                norm = np.linalg.norm(normal)
                if norm > 0:
                    normal /= norm
                else:
                    normal = np.array([0, 0, 1])
                normals_point.append(normal)
        poly.point_data["Normals"] = np.array(normals_point)
        self.logger.debug(
            f"PyVista mesh created with {poly.n_points} points and {poly.n_cells} cells"
        )
        return poly

    def plot(self, show_hard_points=False, save_path=None, show=True):
        """Plot the airfoil using Matplotlib."""
        self.logger.debug("Plotting airfoil")
        plt.figure()  # Create a new figure to avoid overlapping
        points = self.current_points
        plt.plot(points[:, 0], points[:, 1], "b-", alpha=0.5)
        # Plot shear webs
        for sw in self.shear_webs:
            t1, t2 = sw.compute_intersections(self)
            p1 = self.get_points([t1])[0]
            p2 = self.get_points([t2])[0]
            n_elements = self.shear_web_n_elements[sw]
            n_points_web = n_elements + 1
            web_points = np.linspace(p1, p2, n_points_web)
            plt.plot(web_points[:, 0], web_points[:, 1], "g-", alpha=0.5, linewidth=2)
            plt.plot(web_points[:, 0], web_points[:, 1], "g.", markersize=4)
        # Plot non-hard points with .
        non_hard_mask = ~np.isin(self.current_t, self.hard_points)
        plt.plot(points[non_hard_mask, 0], points[non_hard_mask, 1], "k.", markersize=2)
        plt.axis("equal")
        plt.xlabel("x")
        plt.ylabel("y")
        plt.title("Airfoil Mesh")
        plt.grid(True)
        if show_hard_points:
            hard_points_pos = self.get_points(self.hard_points)
            plt.plot(hard_points_pos[:, 0], hard_points_pos[:, 1], "ro", markersize=8)
            for i, (x, y, _) in enumerate(hard_points_pos):
                plt.text(
                    x,
                    y + 0.01,
                    f"t={self.hard_points[i]:.2f}",
                    fontsize=8,
                    ha="center",
                    va="bottom",
                )
        if save_path:
            plt.savefig(save_path)
            self.logger.info(f"Plot saved to {save_path}")
        if show and save_path is None:
            plt.show()
        self.logger.debug("Plotting complete")
