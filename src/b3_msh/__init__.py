"""b3_msh package initialization."""

from .meshing.airfoil import Airfoil
from .meshing.webs import ShearWeb
from .utils.parallel_utils import process_airfoils_parallel

__all__ = ["Airfoil", "ShearWeb", "process_airfoils_parallel"]
