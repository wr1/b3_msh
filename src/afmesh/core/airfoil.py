import numpy as np
from scipy.interpolate import PchipInterpolator
from scipy.optimize import brentq
import pyvista as pv
import matplotlib.pyplot as plt


class Airfoil:
    """Represents an airfoil with spline interpolation, hard points, panels, and shear webs."""

    def __init__(self, points, is_normalized=True, chord=1.0, position=(0, 0, 0), rotation=0):
        """Initialize an Airfoil."""
        self.original_points = np.array(points)
        if self.original_points.shape[1] == 2:
            self.original_points = np.column_stack([self.original_points, np.zeros(len(self.original_points))])
        self.is_normalized = is_normalized
        self.chord = chord
        self.position = np.array(position)
        self.rotation = rotation  # degrees, around z-axis
        self.hard_points = [0.0, 1.0]  # Default hard points at ends
        self.shear_webs = []  # List of ShearWeb instances
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
        """Apply scaling, rotation, and translation if not normalized."""
        if not self.is_normalized:
            # Scale by chord
            points *= self.chord
            # Rotate around z-axis
            rot_rad = np.radians(self.rotation)
            rot_matrix = np.array([
                [np.cos(rot_rad), -np.sin(rot_rad), 0],
                [np.sin(rot_rad), np.cos(rot_rad), 0],
                [0, 0, 1]
            ])
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
        with open(filename, 'r') as f:
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

    def add_shear_web(self, shear_web):
        """Add a shear web, which adds hard points at intersections."""
        self.shear_webs.append(shear_web)
        t1, t2 = shear_web.compute_intersections(self)
        self.add_hard_point(t1)
        self.add_hard_point(t2)

    def get_panels(self):
        """Get list of panels as (t_start, t_end) tuples."""
        panels = []
        sorted_hp = sorted(self.hard_points)
        for i in range(len(sorted_hp) - 1):
            panels.append((sorted_hp[i], sorted_hp[i+1]))
        return panels

    def remesh(self, t_distribution=None, total_n_points=None, element_length=None, relative_refinement=None):
        """Remesh the airfoil."""
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
        points = self.current_points
        n_points = len(points)
        lines = []
        # Airfoil lines
        for i in range(n_points-1):
            lines.extend([2, i, i+1])
        # Shear web lines
        for sw in self.shear_webs:
            t1, t2 = sw.compute_intersections(self)
            idx1 = np.where(np.isclose(self.current_t, t1))[0][0]
            idx2 = np.where(np.isclose(self.current_t, t2))[0][0]
            lines.extend([2, idx1, idx2])
        lines = np.array(lines)
        poly = pv.PolyData(points, lines=lines)
        # Add panel id to cells
        panels = self.get_panels()
        n_airfoil_cells = n_points - 1
        n_shear_cells = len(self.shear_webs)
        cell_data = np.zeros(n_airfoil_cells + n_shear_cells, dtype=int)
        sorted_hp = sorted(self.hard_points)
        hp_indices = [np.where(np.isclose(self.current_t, hp))[0][0] for hp in sorted_hp]
        for p_idx in range(len(hp_indices)-1):
            start_idx = hp_indices[p_idx]
            end_idx = hp_indices[p_idx+1]
            cell_data[start_idx:end_idx] = p_idx
        # Shear webs have panel_id = len(panels)
        cell_data[n_airfoil_cells:] = len(panels)
        poly.cell_data['panel_id'] = cell_data
        # Add distances from hard points
        for i, hp in enumerate(sorted(self.hard_points)):
            hp_pos = self.get_points([hp])[0]
            abs_distances = np.linalg.norm(self.current_points - hp_pos, axis=1)
            poly.point_data[f'abs_dist_hp_{i}'] = abs_distances
            rel_distances = np.abs(self.current_t - hp)
            poly.point_data[f'rel_dist_hp_{i}'] = rel_distances
        return poly

    def plot(self, show_hard_points=False):
        """Plot the airfoil using Matplotlib."""
        points = self.current_points
        plt.plot(points[:, 0], points[:, 1], 'b-', alpha=0.5)
        # Plot shear webs
        for sw in self.shear_webs:
            t1, t2 = sw.compute_intersections(self)
            p1 = self.get_points([t1])[0]
            p2 = self.get_points([t2])[0]
            plt.plot([p1[0], p2[0]], [p1[1], p2[1]], 'g--', linewidth=2)
        # Plot non-hard points with .
        non_hard_mask = ~np.isin(self.current_t, self.hard_points)
        plt.plot(points[non_hard_mask, 0], points[non_hard_mask, 1], 'k.', markersize=2)
        plt.axis('equal')
        plt.title('Airfoil Mesh')
        plt.grid(True)
        if show_hard_points:
            hard_points_pos = self.get_points(self.hard_points)
            plt.plot(hard_points_pos[:, 0], hard_points_pos[:, 1], 'ro', markersize=8)
            plt.xticks(hard_points_pos[:, 0], labels=[f"t={t:.2f}" for t in self.hard_points])
        plt.show()