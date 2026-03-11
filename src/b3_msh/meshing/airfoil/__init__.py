"""Airfoil package - Line mode foundation."""
from .core import AirfoilCore
from .mesh import AirfoilMesh
from .plot import AirfoilPlot
from .viz import AirfoilViz
from .models import *

class Airfoil(AirfoilCore, AirfoilMesh, AirfoilPlot, AirfoilViz):
    """Represents an airfoil with spline interpolation, hard points, panels, and shear webs."""
    pass

__all__ = ["Airfoil"]
