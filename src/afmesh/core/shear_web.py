import numpy as np
from scipy.optimize import brentq
from ..utils.logger import get_logger


class ShearWeb:
    """Represents a shear web defined by a plane, line, or trailing edge, computing intersections with the airfoil."""

    def __init__(self, definition):
        """Initialize a ShearWeb."""
        self.logger = get_logger(self.__class__.__name__)
        self.logger.info("Initializing ShearWeb")
        self.definition = definition
        self.name = None  # Set in add_shear_web
        self.logger.debug(f"ShearWeb definition: {definition}")

    def compute_intersections(self, airfoil):
        """Compute t values where the shear web intersects the airfoil spline."""
        self.logger.info("Computing intersections")
        if self.definition["type"] == "plane":
            result = self._intersect_plane(airfoil)
        elif self.definition["type"] == "line":
            result = self._intersect_line(airfoil)
        elif self.definition["type"] == "trailing_edge":
            result = 0.0, 1.0
        else:
            self.logger.error(f"Unsupported shear web type: {self.definition['type']}")
            raise ValueError("Unsupported shear web type")
        self.logger.debug(f"Intersections: {result}")
        return result

    def _intersect_plane(self, airfoil):
        """Find t where spline intersects plane using root-finding."""
        self.logger.debug("Intersecting with plane")
        origin = np.array(self.definition["origin"])
        normal = np.array(self.definition["normal"])

        def f(t):
            point = airfoil.get_points([t])[0]
            return np.dot(point - origin, normal)

        # Assume two intersections; find roots in [0,0.5] and [0.5,1]
        try:
            t1 = brentq(f, 0, 0.5)
            t2 = brentq(f, 0.5, 1)
            return t1, t2
        except ValueError:
            self.logger.error("Plane does not intersect airfoil at two points")
            raise ValueError("Plane does not intersect airfoil at two points")

    def _intersect_line(self, airfoil):
        """Find t where spline is closest to line (approximate intersection)."""
        self.logger.debug("Intersecting with line")
        # For simplicity, minimize distance; assumes 2D or 3D line
        point = np.array(self.definition["point"])
        direction = np.array(self.definition["direction"])

        def dist(t):
            spline_pt = airfoil.get_points([t])[0]
            vec = spline_pt - point
            proj = np.dot(vec, direction) / np.dot(direction, direction)
            return np.linalg.norm(vec - proj * direction)

        # Find two minima (rough approximation for two intersections)
        from scipy.optimize import minimize_scalar

        res1 = minimize_scalar(dist, bounds=(0, 0.5), method="bounded")
        res2 = minimize_scalar(dist, bounds=(0.5, 1), method="bounded")
        return res1.x, res2.x