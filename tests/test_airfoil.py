import numpy as np
from afmesh.core.airfoil import Airfoil
from afmesh.utils.utils import process_airfoils_parallel


def dummy_func(af):
    """Dummy function for parallel processing test."""
    return len(af.current_points)


def test_airfoil_init():
    """Test Airfoil initialization."""
    points = np.array([[0, 0], [0.5, 0.1], [1, 0]])
    af = Airfoil(points)
    assert af.current_points.shape[1] == 3  # Includes z


def test_airfoil_init_3d():
    """Test Airfoil initialization with 3D points."""
    points = np.array([[0, 0, 0], [0.5, 0.1, 0.1], [1, 0, 0]])
    af = Airfoil(points)
    assert af.current_points.shape[1] == 3


def test_remesh():
    """Test remeshing."""
    points = np.array([[0, 0], [0.5, 0.1], [1, 0]])
    af = Airfoil(points)
    af.remesh(total_n_points=50)
    assert len(af.current_points) >= 50


def test_remesh_element_length():
    """Test remeshing with element length."""
    points = np.array([[0, 0], [0.5, 0.1], [1, 0]])
    af = Airfoil(points)
    af.remesh(element_length=0.1)
    assert len(af.current_points) > 3


def test_remesh_relative_refinement():
    """Test remeshing with relative refinement."""
    points = np.array([[0, 0], [0.5, 0.1], [1, 0]])
    af = Airfoil(points)
    af.add_hard_point(0.5)
    af.remesh(relative_refinement={0: 2.0})
    assert len(af.current_points) > 100  # Should be more refined


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
    assert "panel_id" in mesh.cell_data
    assert len(mesh.cell_data["panel_id"]) == mesh.n_cells
    assert "abs_dist_hp_0" in mesh.point_data
    assert "rel_dist_hp_0" in mesh.point_data
    assert "Normals" in mesh.point_data


def test_plot_show_hard_points():
    """Test plotting with hard points shown."""
    points = np.array([[0, 0], [0.5, 0.1], [1, 0]])
    af = Airfoil(points)
    af.add_hard_point(0.5)
    # Just call plot, assume it works without error
    af.plot(show_hard_points=True, show=False)


def test_process_parallel():
    """Test parallel processing of airfoils."""
    points = np.array([[0, 0], [0.5, 0.1], [1, 0]])
    af1 = Airfoil(points)
    af2 = Airfoil(points)
    airfoils = [af1, af2]
    results = process_airfoils_parallel(airfoils, dummy_func)
    assert len(results) == 2
    assert all(isinstance(r, int) for r in results)
