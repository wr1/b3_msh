from unittest.mock import Mock, patch

import numpy as np

from b3_msh.multiline.step.B3MshLineStep import B3MshLineStep


def test_b3msh_step_attributes():
    """Test B3MshLineStep class attributes."""
    assert B3MshLineStep.workdir_key == "workdir"
    assert len(B3MshLineStep.input_files) == 1
    assert B3MshLineStep.input_files[0].name == "b3_geo/lm1_mesh.vtp"
    assert B3MshLineStep.input_files[0].non_empty
    assert B3MshLineStep.output_files == ["b3_msh/lm2.vtp"]
    assert set(B3MshLineStep.dependent_sections) == {
        "geometry",
        "airfoils",
        "structure",
        "mesh",
    }


def test_b3msh_step_execute():
    """Test B3MshLineStep _execute method with mocked dependencies."""
    step = object.__new__(B3MshLineStep)
    step.config_path = "/tmp/config.yml"
    # Mock config
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
    }
    step.config = mock_config
    # Mock logger
    step.logger = Mock()
    # Mock mesh
    mock_mesh = Mock()
    mock_mesh.points = np.array(
        [[0, 0, 0], [1, 0, 0], [0.5, 0.1, 0], [0, 0, 1], [1, 0, 1], [0.5, 0.1, 1]]
    )
    mock_mesh.point_data = {"t": np.array([0, 0.5, 1, 0, 0.5, 1])}
    mock_mesh.cell_data = {}
    mock_mesh.lines = np.array([], dtype=int)
    mock_mesh.point_data_to_cell_data = Mock(return_value=mock_mesh)
    mock_mesh.save = Mock()
    mock_af = Mock()
    mock_af.to_pyvista = Mock(return_value=mock_mesh)
    step.process_section_from_mesh = Mock(return_value=mock_af)
    # Mock pv.read
    with (
        patch("b3_msh.multiline.step.B3MshLineStep.pv.read", return_value=mock_mesh) as mock_read,
        patch("b3_msh.multiline.step.B3MshLineStep.pv.MultiBlock") as mock_multiblock,
        patch("pathlib.Path.exists", return_value=True),
        patch("b3_msh.multiline.step.B3MshLineStep.pv.merge", return_value=mock_mesh) as mock_merge,
        patch("b3_msh.multiline.step.B3MshLineStep.pv.PolyData.save", Mock()) as mock_poly_save,
    ):
        mock_mb_instance = Mock()
        mock_multiblock.return_value = mock_mb_instance
        # Call _execute
        step._execute()
        # Check that read was called
        mock_read.assert_called_once()
        # Check that merge was called
        mock_merge.assert_called_once()
        # Check that poly save was called
        mock_poly_save.assert_called_once()


def test_merge_meshes_with_missing_arrays():
    """Test that _merge_and_save_mesh adds missing cell arrays with zeros."""
    step = object.__new__(B3MshLineStep)
    step.logger = Mock()
    # Create mock meshes
    mesh1 = Mock()
    mesh1.n_cells = 5
    mesh1.cell_data = {
        "panel_id": np.array([0, 0, 1, 1, -1], dtype=int),
        "other_field": np.array([1.0] * 5, dtype=float),
    }
    mesh1.point_data = {}
    mesh1.lines = np.array([])
    mesh1.points = np.array([[0, 0, 0]] * 5)
    mesh1.point_data_to_cell_data = Mock(return_value=mesh1)

    mesh2 = Mock()
    mesh2.n_cells = 3
    mesh2.cell_data = {"panel_id": np.array([0, 1, -10], dtype=int)}  # Missing 'other_field'
    mesh2.point_data = {}
    mesh2.lines = np.array([])
    mesh2.points = np.array([[0, 0, 0]] * 3)
    mesh2.point_data_to_cell_data = Mock(return_value=mesh2)

    sections = [Mock(), Mock()]  # Two sections
    sections[0].to_pyvista = Mock(return_value=mesh1)
    sections[1].to_pyvista = Mock(return_value=mesh2)

    # Mock pv.merge and PolyData
    merged_mesh = Mock()
    merged_mesh.points = np.array([])
    merged_mesh.lines = np.array([])
    merged_mesh.cell_data = {}
    merged_mesh.point_data = {}
    with (
        patch("b3_msh.multiline.step.B3MshLineStep.pv.merge", return_value=merged_mesh) as mock_merge,
        patch("b3_msh.multiline.step.B3MshLineStep.pv.PolyData") as mock_poly_class,
        patch("pathlib.Path") as mock_path,
    ):
        mock_poly = Mock()
        mock_poly_class.return_value = mock_poly
        mock_path_instance = Mock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.parent.mkdir = Mock()
        mock_poly.save = Mock()

        # Call the method
        output_path = Mock()
        step._merge_and_save_mesh(sections, output_path)

        # Check that mesh2 now has 'other_field' added
        assert "other_field" in mesh2.cell_data
        assert np.array_equal(mesh2.cell_data["other_field"], np.zeros(3, dtype=float))
        # Check that merge was called
        mock_merge.assert_called_once()
