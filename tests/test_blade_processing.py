import numpy as np
from unittest.mock import Mock
from b3_msh.core.blade_processing import process_section_from_mesh
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
    rel_span_values = np.array([0.0, 0.0, 0.0, 1.0, 1.0, 1.0])
    mock_mesh = Mock()
    mock_mesh.points = points
    mock_mesh.point_data = {"t": t_values, "rel_span": rel_span_values}

    logger = get_logger(__name__)
    chordwise_mesh = {"default": {"n_elem": 10}}
    webs_config = []

    af = process_section_from_mesh(mock_mesh, 0.0, chordwise_mesh, webs_config, logger)

    assert af.rel_span == 0.0
    assert len(af.current_points) == 11  # 10 elements + 1
    assert af.constant_fields == {"rel_span": 0.0}


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
    rel_span_values = np.array([0.0, 0.0, 0.0, 1.0, 1.0, 1.0])
    mock_mesh = Mock()
    mock_mesh.points = points
    mock_mesh.point_data = {"t": t_values, "rel_span": rel_span_values}

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

    assert af.rel_span == 0.0
    assert len(af.shear_webs) == 2  # trailing edge + test_web
    assert af.constant_fields == {"rel_span": 0.0}


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
    rel_span_values = np.array([0.0, 0.0, 0.0, 1.0, 1.0, 1.0])
    mock_mesh = Mock()
    mock_mesh.points = points
    mock_mesh.point_data = {"t": t_values, "rel_span": rel_span_values}

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

    assert af.rel_span == 0.0
    assert len(af.shear_webs) == 1  # only trailing edge
    assert af.constant_fields == {"rel_span": 0.0}


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
    rel_span_values = np.array([0.0, 0.0, 0.0, 1.0, 1.0, 1.0])
    mock_mesh = Mock()
    mock_mesh.points = points
    mock_mesh.point_data = {"t": t_values, "rel_span": rel_span_values}

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

    assert af.rel_span == 0.0
    assert len(af.shear_webs) == 1  # only trailing edge
    assert af.constant_fields == {"rel_span": 0.0}
