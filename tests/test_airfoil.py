import numpy as np
import pytest
from afmesh.core.airfoil import Airfoil


def test_airfoil_init():
    """Test Airfoil initialization."""
    points = np.array([[0, 0], [0.5, 0.1], [1, 0]])
    af = Airfoil(points)
    assert af.current_points.shape[1] == 3  # Includes z


def test_remesh():
    """Test remeshing."""
    points = np.array([[0, 0], [0.5, 0.1], [1, 0]])
    af = Airfoil(points)
    af.remesh(total_n_points=50)
    assert len(af.current_points) >= 50


def test_hard_points():
    """Test adding hard points."""
    points = np.array([[0, 0], [0.5, 0.1], [1, 0]])
    af = Airfoil(points)
    af.add_hard_point(0.5)
    assert 0.5 in af.hard_points


def test_panels():
    """Test getting panels."""
    points = np.array([[0, 0], [0.5, 0.1], [1, 0]])
    af = Airfoil(points)
    af.add_hard_point(0.5)
    panels = af.get_panels()
    assert len(panels) == 2


def test_to_pyvista():
    """Test PyVista export."""
    points = np.array([[0, 0], [0.5, 0.1], [1, 0]])
    af = Airfoil(points)
    mesh = af.to_pyvista()
    assert mesh.n_points == len(af.current_points)
    assert 'panel_id' in mesh.cell_data
    assert len(mesh.cell_data['panel_id']) == mesh.n_cells
    assert 'abs_dist_hp_0' in mesh.point_data
    assert 'rel_dist_hp_0' in mesh.point_data