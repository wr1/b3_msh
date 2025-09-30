import pytest
import numpy as np
from unittest.mock import Mock, patch
from b3_msh.statesman_step import B3MshStep


def test_b3msh_step_attributes():
    """Test B3MshStep class attributes."""
    assert B3MshStep.workdir_key == "workdir"
    assert len(B3MshStep.input_files) == 1
    assert B3MshStep.input_files[0].name == "b3_geo/lm1_mesh.vtp"
    assert B3MshStep.input_files[0].non_empty == True
    assert B3MshStep.output_files == ["b3_msh/lm2.vtm"]
    assert set(B3MshStep.dependent_sections) == {"geometry", "airfoils", "structure", "mesh"}


def test_b3msh_step_execute():
    """Test B3MshStep _execute method with mocked dependencies."""
    step = object.__new__(B3MshStep)
    # Mock config
    mock_config = {
        "workdir": "/tmp/test",
        "geometry": {
            "planform": {
                "npchord": 10,
                "npspan": 10,
                "pre_rotation": 0,
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
        "mesh": {"z": [0.0, 1.0], "chordwise": {"default": {"n_elem": 10}, "panels": []}},
    }
    step.config = mock_config
    # Mock logger
    step.logger = Mock()
    # Mock mesh
    mock_mesh = Mock()
    mock_mesh.points = np.array([[0, 0, 0], [1, 0, 0], [0.5, 0.1, 0], [0, 0, 1], [1, 0, 1], [0.5, 0.1, 1]])
    mock_mesh.point_data = {"t": np.array([0, 0.5, 1, 0, 0.5, 1])}
    # Mock pv.read
    with patch('b3_msh.statesman_step.pv.read', return_value=mock_mesh) as mock_read, \
         patch('b3_msh.statesman_step.pv.MultiBlock') as mock_multiblock, \
         patch('b3_msh.statesman_step.os.makedirs') as mock_makedirs:
        mock_mb_instance = Mock()
        mock_multiblock.return_value = mock_mb_instance
        # Call _execute
        step._execute()
        # Check that read was called
        mock_read.assert_called_once()
        # Check that MultiBlock was created and save called
        mock_multiblock.assert_called_once()
        mock_mb_instance.save.assert_called_once()
