import numpy as np
from scipy.interpolate import PchipInterpolator


class AirfoilCore:
    """Core functionality for Airfoil initialization, spline building, and transformations."""

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
        self.hard_point_names = {0.0: 'leading_edge', 1.0: 'trailing_edge'}
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

    def rotate(self, angle):
        """Rotate the airfoil by angle degrees around z-axis."""
        self.rotation += angle
        self.current_points = self.get_points(self.current_t)

    def translate(self, x, y, z):
        """Translate the airfoil by (x, y, z)."""
        self.position += np.array([x, y, z])
        self.current_points = self.get_points(self.current_t)