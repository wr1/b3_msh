from unittest.mock import Mock, patch

import numpy as np
import pytest

from b3_msh.surface.step.b3_msh_surface_step import b3_msh_surface_step


def test_surface_step_attributes():
    """Test b3_msh_surface_step class attributes."""
    assert b3_msh_surface_step.workdir_key == "workdir"
    assert len(b3_msh_surface_step.input_files) == 1
    assert b3_msh_surface_step.input_files[0].name == "b3_geo/lm1_mesh3d.vtp"
    assert b3_msh_surface_step.input_files[0].non_empty
    assert b3_msh_surface_step.output_files == ["b3_msh/lm2_surface_mesh.vtp"]
    assert set(b3_msh_surface_step.dependent_sections) == {
        "geometry",
        "airfoils",
        "structure",
        "mesh3d",
    }


def test_surface_step_execute():
    """Test b3_msh_surface_step _execute method with mocked dependencies."""
    step = object.__new__(b3_msh_surface_step)
    step.config_path = "/tmp/config.yml"
    # Mock config with mesh3d
    mock_config = {
        "workdir": "/tmp/test",
        "geometry": {
            "planform": {
                "npchord": 10,
                "dx": [],
                "dy": [],
                "z": [],
                "chord": [],
                "thickness": [],
                "twist": [],
            }
        },
        "airfoils": [],
        "structure": {"webs": []},
        "mesh": {
            "z": [{"type": "plain", "values": [0.0, 1.0]}],
            "chordwise": {"default": {"n_elem": 10}, "panels": []},
        },
        "mesh3d": {
            "z": [{"type": "plain", "values": [0.0, 1.0]}],
            "chordwise": {"default": {"n_elem": 10}, "panels": []},
        },
    }
    step.config = mock_config
    # Mock logger
    step.logger = Mock()
    # Mock mesh
    mock_mesh = Mock()
    mock_mesh.points = np.array(
        [[0, 0, 0], [1, 0, 0], [0.5, 0.1, 0], [0, 0, 1], [1, 0, 1], [0.5, 0.1, 1]]
    )
    mock_mesh.point_data = {
        "t": np.array([0, 0.5, 1, 0, 0.5, 1]),
        "rel_span": np.array([0, 0, 0, 1, 1, 1]),
    }
    mock_mesh.cell_data = {"panel_id": np.array([0, 1, -1])}  # Add panel_id
    mock_mesh.lines = np.array([2, 0, 1, 2, 1, 2, 2, 2, 3])  # Mock lines
    mock_af = Mock()
    mock_af.position = [0, 0, 0]
    mock_af.current_points = np.array([[0, 0, 0], [1, 0, 0], [0.5, 0.1, 0]])
    mock_af.current_t = np.array([0, 0.5, 1])
    mock_af.to_pyvista = Mock(return_value=mock_mesh)
    step.process_section_from_mesh = Mock(return_value=mock_af)
    # Mock pv.read and PolyData
    with (
        patch("b3_msh.surface.step.b3_msh_surface_step.pv.read", return_value=mock_mesh) as mock_read,
        patch("pyvista.PolyData") as mock_poly_class,
        patch("pathlib.Path.exists", return_value=True),
    ):
        mock_poly = Mock()
        mock_poly_class.return_value = mock_poly
        mock_poly.save = Mock()
        mock_poly.n_points = 6
        mock_poly.n_cells = 2
        mock_poly.point_data = {
            "t": np.array([0, 0.5, 1] * 2),
            "rel_span": np.array([0] * 3 + [1] * 3),
        }
        # Call _execute
        step._execute()
        # Check that read was called
        mock_read.assert_called_once()
        # Check that poly was created and saved
        mock_poly_class.assert_called_once()
        mock_poly.save.assert_called_once()


def test_surface_step_no_mesh3d():
    """Test that surface step fails without mesh3d."""
    step = object.__new__(b3_msh_surface_step)
    step.config = {
        "workdir": "/tmp/test",
        "geometry": {
            "planform": {
                "npchord": 10,
                "dx": [],
                "dy": [],
                "z": [],
                "chord": [],
                "thickness": [],
                "twist": [],
            }
        },
        "airfoils": [],
        "structure": {"webs": []},
        "mesh": {
            "z": [{"type": "plain", "values": [0.0]}],
            "chordwise": {"default": {"n_elem": 10}},
        },
        # No mesh3d
    }
    with pytest.raises(ValueError, match="mesh3d section required"):
        step._load_and_validate_config()


def test_point_data_propagation():
    """Test point data propagation in surface mesh."""
    # Mock two sections with point_data
    mock_pv1 = Mock()
    mock_pv1.points = np.zeros((3, 3))
    mock_pv1.point_data = {"t": np.array([0.0, 0.5, 1.0]), "Normals": np.ones((3, 3))}
    mock_pv1.lines = np.array([2, 0, 1, 2, 1, 2])
    mock_pv1.cell_data = {"panel_id": np.array([0, 1])}

    mock_pv2 = Mock()
    mock_pv2.points = np.ones((3, 3))
    mock_pv2.point_data = {"t": np.array([0.1, 0.6, 1.1]), "z": np.array([1, 2, 3])}
    mock_pv2.lines = np.array([2, 0, 1, 2, 1, 2])
    mock_pv2.cell_data = {"panel_id": np.array([0, 1])}

    sections = [Mock(), Mock()]
    sections[0].to_pyvista = Mock(return_value=mock_pv1)
    sections[1].to_pyvista = Mock(return_value=mock_pv2)
    sections[0].position = [0, 0, 0]
    sections[1].position = [0, 0, 1]
    sections[0].current_points = np.zeros((3, 3))
    sections[1].current_points = np.ones((3, 3))
    sections[0].current_t = np.array([0.0, 0.5, 1.0])
    sections[1].current_t = np.array([0.1, 0.6, 1.1])

    step = object.__new__(b3_msh_surface_step)
    step.logger = Mock()
    output_path = Mock()

    # Mock pv.PolyData to capture point_data assignment
    with patch("b3_msh.surface.step.b3_msh_surface_step.pv.PolyData") as mock_poly_class:
        mock_poly = Mock()
        mock_poly_class.return_value = mock_poly
        mock_poly.n_points = 6
        mock_poly.n_cells = 2
        mock_poly.point_data = {}

        # Call the method
        step._create_surface_mesh(sections, output_path)

        # Assert that point_data keys include propagated ones
        expected_keys = {"t", "Normals", "z", "dist_from_te", "chordwise_coord", "spanwise_coord"}
        actual_keys = set(mock_poly.point_data.keys())
        assert expected_keys.issubset(actual_keys), f"Missing keys: {expected_keys - actual_keys}"

        # Assert logger was called with point data keys message
        step.logger.info.assert_any_call(f"Point data keys: {list(mock_poly.point_data.keys())}")
