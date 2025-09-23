import numpy as np
from b3_msh.core.airfoil import Airfoil
from b3_msh.core.shear_web import ShearWeb


def test_shear_web_plane():
    """Test shear web plane intersection."""
    points = np.array([[0, 0], [0.5, 0.1], [1, 0]])
    af = Airfoil(points)
    sw = ShearWeb({"type": "plane", "origin": (0.5, 0.05, 0), "normal": (0, 1, 0)})
    af.add_shear_web(sw)
    assert len(af.hard_points) > 2  # Should add points


def test_shear_web_line():
    """Test shear web line intersection."""
    points = np.array([[0, 0], [0.5, 0.1], [1, 0]])
    af = Airfoil(points)
    sw = ShearWeb({"type": "line", "point": (0.5, 0, 0), "direction": (0, 1, 0)})
    af.add_shear_web(sw)
    assert len(af.hard_points) > 2


def test_shear_web_trailing_edge():
    """Test shear web trailing edge."""
    points = np.array([[0, 0], [0.5, 0.1], [1, 0]])
    af = Airfoil(points)
    sw = ShearWeb({"type": "trailing_edge"})
    t1, t2 = sw.compute_intersections(af)
    assert t1 == 0.0
    assert t2 == 1.0


def test_shear_web_meshing():
    """Test shear web meshing in PyVista."""
    points = np.array([[0, 0], [0.5, 0.1], [1, 0]])
    af = Airfoil(points)
    sw = ShearWeb({"type": "plane", "origin": (0.5, 0.05, 0), "normal": (0, 1, 0)})
    af.add_shear_web(sw)
    af.remesh(total_n_points=50)
    mesh = af.to_pyvista()
    # Airfoil cells + shear web cells
    expected_cells = (len(af.current_points) - 1) + len(af.shear_webs)
    assert mesh.n_cells == expected_cells


def test_shear_web_n_elements():
    """Test shear web with n_elements."""
    points = np.array([[0, 0], [0.5, 0.1], [1, 0]])
    af = Airfoil(points)
    sw = ShearWeb({"type": "plane", "origin": (0.5, 0.05, 0), "normal": (0, 1, 0)})
    af.add_shear_web(sw, n_elements=3)
    mesh = af.to_pyvista()
    # Airfoil cells + 3 web cells
    expected_cells = (len(af.current_points) - 1) + 3
    assert mesh.n_cells == expected_cells


def test_shear_web_5_elements():
    """Test shear web with 5 elements."""
    points = np.array([[0, 0], [0.5, 0.1], [1, 0]])
    af = Airfoil(points)
    sw = ShearWeb({"type": "plane", "origin": (0.5, 0.05, 0), "normal": (0, 1, 0)})
    af.add_shear_web(sw, n_elements=5)
    mesh = af.to_pyvista()
    # Airfoil cells + 5 web cells
    expected_cells = (len(af.current_points) - 1) + 5
    assert mesh.n_cells == expected_cells


def test_shear_web_named():
    """Test shear web with name."""
    points = np.array([[0, 0], [0.5, 0.1], [1, 0]])
    af = Airfoil(points)
    sw = ShearWeb(
        {
            "type": "plane",
            "origin": (0.5, 0.05, 0),
            "normal": (0, 1, 0),
            "name": "test_web",
        }
    )
    af.add_shear_web(sw)
    mesh = af.to_pyvista()
    assert "abs_dist_test_web_hp0" in mesh.point_data
    assert "abs_dist_test_web_hp1" in mesh.point_data
