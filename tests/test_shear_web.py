import numpy as np
from afmesh.core.airfoil import Airfoil
from afmesh.core.shear_web import ShearWeb


def test_shear_web_plane():
    """Test shear web plane intersection."""
    points = np.array([[0, 0], [0.5, 0.1], [1, 0]])
    af = Airfoil(points)
    sw = ShearWeb({'type': 'plane', 'origin': (0.5, 0.05, 0), 'normal': (0, 1, 0)})
    af.add_shear_web(sw)
    assert len(af.hard_points) > 2  # Should add points


def test_shear_web_meshing():
    """Test shear web meshing in PyVista."""
    points = np.array([[0, 0], [0.5, 0.1], [1, 0]])
    af = Airfoil(points)
    sw = ShearWeb({'type': 'plane', 'origin': (0.5, 0.05, 0), 'normal': (0, 1, 0)})
    af.add_shear_web(sw)
    af.remesh(total_n_points=50)
    mesh = af.to_pyvista()
    # Airfoil cells + shear web cells
    expected_cells = (len(af.current_points) - 1) + len(af.shear_webs)
    assert mesh.n_cells == expected_cells