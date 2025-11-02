import numpy as np
from unittest.mock import Mock
from b3_msh.core.blade_processing import process_section_from_mesh
from b3_msh.core.airfoil import Airfoil
from b3_msh.utils.logger import get_logger


def test_process_section_from_mesh_basic():
    """Test basic section processing from mesh."""
    # Create a mock mesh with points at z=0 and z=1
    points = np.array(
        [
            [0, 0, 0],
            [0.5, 0.1, 0],
            [1, 0, 0],  # z=0
            [0, 0, 1],
            [0.5, 0.1, 1],
            [1, 0, 1],  # z=1
        ]
    )
    t_values = np.array([0, 0.5, 1, 0, 0.5, 1])
    mock_mesh = Mock()
    mock_mesh.points = points
    mock_mesh.point_data = {"t": t_values}

    logger = get_logger(__name__)
    chordwise_mesh = {"default": {"n_elem": 10}}
    webs_config = []

    af = process_section_from_mesh(mock_mesh, 0.0, chordwise_mesh, webs_config, logger)
    assert isinstance(af, Airfoil)
    assert af.position[2] == 0.0  # z position
    assert len(af.current_points) == 11  # n_elem + 1


def test_process_section_from_mesh_with_webs():
    """Test section processing with shear webs."""
    points = np.array(
        [
            [0, 0, 0],
            [0.5, 0.1, 0],
            [1, 0, 0],  # z=0
            [0, 0, 1],
            [0.5, 0.1, 1],
            [1, 0, 1],  # z=1
        ]
    )
    t_values = np.array([0, 0.5, 1, 0, 0.5, 1])
    mock_mesh = Mock()
    mock_mesh.points = points
    mock_mesh.point_data = {"t": t_values}

    logger = get_logger(__name__)
    chordwise_mesh = {"default": {"n_elem": 10}}
    webs_config = [
        {
            "name": "test_web",
            "type": "plane",
            "origin": [0.5, 0.05, 0],
            "orientation": [0, 1, 0],
            "z_range": [-1, 1],
            "mesh": True,
        }
    ]

    af = process_section_from_mesh(mock_mesh, 0.0, chordwise_mesh, webs_config, logger)
    assert len(af.shear_webs) == 2  # One from config + trailing edge
    assert af.shear_webs[0].name == "test_web"
    assert af.shear_webs[1].name == "trailing_edge"


def test_process_section_from_mesh_z_out_of_range():
    """Test that webs are not added if z is out of range."""
    points = np.array(
        [
            [0, 0, 0],
            [0.5, 0.1, 0],
            [1, 0, 0],  # z=0
            [0, 0, 1],
            [0.5, 0.1, 1],
            [1, 0, 1],  # z=1
        ]
    )
    t_values = np.array([0, 0.5, 1, 0, 0.5, 1])
    mock_mesh = Mock()
    mock_mesh.points = points
    mock_mesh.point_data = {"t": t_values}

    logger = get_logger(__name__)
    chordwise_mesh = {"default": {"n_elem": 10}}
    webs_config = [
        {
            "name": "test_web",
            "type": "plane",
            "origin": [0.5, 0.05, 0],
            "orientation": [0, 1, 0],
            "z_range": [0.5, 1.5],  # z=0 is not in range
            "mesh": True,
        }
    ]

    af = process_section_from_mesh(mock_mesh, 0.0, chordwise_mesh, webs_config, logger)
    assert len(af.shear_webs) == 1  # Only trailing edge
    assert af.shear_webs[0].name == "trailing_edge"


def test_process_section_from_mesh_no_mesh_flag():
    """Test that webs are not added if mesh flag is False."""
    points = np.array(
        [
            [0, 0, 0],
            [0.5, 0.1, 0],
            [1, 0, 0],  # z=0
            [0, 0, 1],
            [0.5, 0.1, 1],
            [1, 0, 1],  # z=1
        ]
    )
    t_values = np.array([0, 0.5, 1, 0, 0.5, 1])
    mock_mesh = Mock()
    mock_mesh.points = points
    mock_mesh.point_data = {"t": t_values}

    logger = get_logger(__name__)
    chordwise_mesh = {"default": {"n_elem": 10}}
    webs_config = [
        {
            "name": "test_web",
            "type": "plane",
            "origin": [0.5, 0.05, 0],
            "orientation": [0, 1, 0],
            "z_range": [-1, 1],
            "mesh": False,  # Not to mesh
        }
    ]

    af = process_section_from_mesh(mock_mesh, 0.0, chordwise_mesh, webs_config, logger)
    assert len(af.shear_webs) == 1  # Only trailing edge
    assert af.shear_webs[0].name == "trailing_edge"
