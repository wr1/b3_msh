import numpy as np
from scipy.interpolate import PchipInterpolator
import pyvista as pv
import matplotlib.pyplot as plt


class Airfoil:
    """Represents an airfoil with spline interpolation, hard points, panels, and shear webs."""

    def __init__(
        self, points, is_normalized=True, chord=1.0, position=(0, 0, 0), rotation=0
    ):
        """Initialize an Airfoil."""
        self.original_points = np.array(points)
        if self.original_points.shape[1] == 2:
            self.original_points = np.column_stack(
                [self.original_points, np.zeros(len(self.original_points))]
            )
        self.is_normalized = is_normalized
        self.chord = chord
        self.position = np.array(position)
        self.rotation = rotation  # degrees, around z-axis
        self.hard_points = [0.0, 1.0]  # Default hard points at ends
        self.shear_webs = []  # List of ShearWeb instances
        self.shear_web_refinements = {}  # Dict of shear_web to refinement_factor
        self.shear_web_n_elements = {}  # Dict of shear_web to n_elements
        self.current_t = np.linspace(0, 1, 100)  # Default t distribution
        self.current_points = None
        self._build_spline()
        self.remesh(self.current_t)  # Initial mesh

    def _build_spline(self):
        """Build PCHIP splines for x, y, z from original points."""
        # Compute parametric t based on cumulative arc length
        diffs = np.diff(self.original_points, axis=0)
        dist = np.sqrt(np.sum(diffs**2, axis=1))
        cum_dist = np.cumsum(dist)
        cum_dist = np.insert(cum_dist, 0, 0)
        t_orig = cum_dist / cum_dist[-1]
        self.spline_x = PchipInterpolator(t_orig, self.original_points[:, 0])
        self.spline_y = PchipInterpolator(t_orig, self.original_points[:, 1])
        self.spline_z = PchipInterpolator(t_orig, self.original_points[:, 2])

    def _apply_transformations(self, points):
        """Apply scaling, rotation, and translation."""
        # Scale by chord
        points *= self.chord
        # Rotate around z-axis
        rot_rad = np.radians(self.rotation)
        rot_matrix = np.array(
            [
                [np.cos(rot_rad), -np.sin(rot_rad), 0],
                [np.sin(rot_rad), np.cos(rot_rad), 0],
                [0, 0, 1],
            ]
        )
        points = points @ rot_matrix.T
        # Translate
        points += self.position
        return points

    def get_points(self, t_values):
        """Get interpolated points at given t values, with transformations applied."""
        x = self.spline_x(t_values)
        y = self.spline_y(t_values)
        z = self.spline_z(t_values)
        points = np.column_stack([x, y, z])
        return self._apply_transformations(points)

    @classmethod
    def from_xfoil(cls, filename, **kwargs):
        """Load airfoil from XFOIL format file."""
        with open(filename, "r") as f:
            lines = f.readlines()
        data = np.loadtxt(lines[1:])  # Skip name line
        return cls(data, **kwargs)

    @classmethod
    def from_array(cls, points, **kwargs):
        """Create airfoil from numpy array."""
        return cls(points, **kwargs)

    def add_hard_point(self, t):
        """Add a hard point at parametric t."""
        if 0 <= t <= 1 and t not in self.hard_points:
            self.hard_points.append(t)
            self.hard_points.sort()
            self.remesh()  # Update mesh to include new hard points

    def add_shear_web(self, shear_web, refinement_factor=1.0, n_elements=None):
        """Add a shear web, which adds hard points at intersections."""
        self.shear_webs.append(shear_web)
        self.shear_web_refinements[shear_web] = refinement_factor
        self.shear_web_n_elements[shear_web] = (
            n_elements if n_elements is not None else 1
        )
        t1, t2 = shear_web.compute_intersections(self)
        self.add_hard_point(t1)
        self.add_hard_point(t2)
        self.remesh()  # Update mesh to include new hard points

    def rotate(self, angle):
        """Rotate the airfoil by angle degrees around z-axis."""
        self.rotation += angle
        self.current_points = self.get_points(self.current_t)

    def translate(self, x, y, z):
        """Translate the airfoil by (x, y, z)."""
        self.position += np.array([x, y, z])
        self.current_points = self.get_points(self.current_t)

    def get_panels(self):
        """Get list of panels as (t_start, t_end) tuples."""
        panels = []
        sorted_hp = sorted(self.hard_points)
        for i in range(len(sorted_hp) - 1):
            panels.append((sorted_hp[i], sorted_hp[i + 1]))
        return panels

    def remesh(
        self,
        t_distribution=None,
        total_n_points=None,
        element_length=None,
        relative_refinement=None,
    ):
        """Remesh the airfoil."""
        if relative_refinement is None and self.shear_web_refinements:
            relative_refinement = {}
            panels = self.get_panels()
            for sw, factor in self.shear_web_refinements.items():
                t1, t2 = sw.compute_intersections(self)
                for p_idx, (ts, te) in enumerate(panels):
                    if ts <= t1 < te or ts < t2 <= te or (t1 <= ts and te <= t2):
                        relative_refinement[p_idx] = max(
                            relative_refinement.get(p_idx, 1.0), factor
                        )
        if t_distribution is not None:
            t_vals = np.array(t_distribution)
        elif total_n_points is not None:
            panels = self.get_panels()
            total_segments = total_n_points - 1
            t_vals = []
            for t_start, t_end in panels:
                length = t_end - t_start
                segments = round(length * total_segments)
                n_points_panel = segments + 1
                t_panel = np.linspace(t_start, t_end, n_points_panel)
                t_vals.extend(t_panel)
            t_vals = np.array(t_vals)
        elif element_length is not None:
            # Approximate based on arc length
            total_length = self._arc_length(0, 1)
            n = int(total_length / element_length)
            t_vals = np.linspace(0, 1, n)
        elif relative_refinement is not None:
            # Refine relative to current
            panels = self.get_panels()
            t_vals = []
            for i, (t_start, t_end) in enumerate(panels):
                factor = relative_refinement.get(i, 1.0)
                n_panel = max(10, int(len(self.current_t) * factor / len(panels)))
                t_panel = np.linspace(t_start, t_end, n_panel)
                t_vals.extend(t_panel)
            t_vals = np.array(t_vals)
        else:
            t_vals = self.current_t  # Default

        # Ensure hard points are included
        all_t = np.sort(np.concatenate([t_vals, self.hard_points]))
        self.current_t = all_t
        self.current_points = self.get_points(all_t)

    def _arc_length(self, t1, t2, n_samples=1000):
        """Approximate arc length between t1 and t2."""
        t_samples = np.linspace(t1, t2, n_samples)
        points = self.get_points(t_samples)
        diffs = np.diff(points, axis=0)
        return np.sum(np.sqrt(np.sum(diffs**2, axis=1)))

    def to_pyvista(self):
        """Export to PyVista PolyData (line mesh)."""
        airfoil_points = self.current_points
        web_points = []
        web_info = []  # list of (sw, start_idx, n_points_web)
        current_web_idx = len(airfoil_points)
        for sw in self.shear_webs:
            t1, t2 = sw.compute_intersections(self)
            p1 = self.get_points([t1])[0]
            p2 = self.get_points([t2])[0]
            n_elements = self.shear_web_n_elements[sw]
            n_points_web = n_elements + 1
            web_points.append(np.linspace(p1, p2, n_points_web))
            web_info.append((sw, current_web_idx, n_points_web))
            current_web_idx += n_points_web
        if web_points:
            web_points = np.vstack(web_points)
            all_points = np.vstack([airfoil_points, web_points])
        else:
            all_points = airfoil_points
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
        # Add distances from hard points
        for i, hp in enumerate(sorted(self.hard_points)):
            hp_pos = self.get_points([hp])[0]
            abs_distances = np.linalg.norm(airfoil_points - hp_pos, axis=1)
            poly.point_data[f"abs_dist_hp_{i}"] = np.concatenate(
                [abs_distances, np.zeros(len(all_points) - len(airfoil_points))]
            )
            rel_distances = np.abs(self.current_t - hp)
            poly.point_data[f"rel_dist_hp_{i}"] = np.concatenate(
                [rel_distances, np.zeros(len(all_points) - len(airfoil_points))]
            )
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
        return poly

    def plot(self, show_hard_points=False, save_path=None, show=True):
        """Plot the airfoil using Matplotlib."""
        plt.figure()  # Create a new figure to avoid overlapping
        points = self.current_points
        plt.plot(points[:, 0], points[:, 1], "b-", alpha=0.5)
        # Plot shear webs
        for sw in self.shear_webs:
            t1, t2 = sw.compute_intersections(self)
            p1 = self.get_points([t1])[0]
            p2 = self.get_points([t2])[0]
            plt.plot([p1[0], p2[0]], [p1[1], p2[1]], "g--", linewidth=2)
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
            plt.xticks(
                hard_points_pos[:, 0], labels=[f"t={t:.2f}" for t in self.hard_points]
            )
        if save_path:
            plt.savefig(save_path)
        if show and save_path is None:
            plt.show()
