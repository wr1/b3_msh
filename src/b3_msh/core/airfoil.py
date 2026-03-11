"""Represents an airfoil with spline interpolation, hard points, panels, and shear webs."""

from .airfoil_core import AirfoilCore
from .airfoil_mesh import AirfoilMesh
from .airfoil_plot import AirfoilPlot
from .airfoil_viz import AirfoilViz


class Airfoil(AirfoilCore, AirfoilMesh, AirfoilPlot, AirfoilViz):
    """Represents an airfoil with spline interpolation, hard points, panels, and shear webs."""

    pass
