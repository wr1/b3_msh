"""Test statesman integration."""

import pytest
import pyvista as pv
import numpy as np
from pathlib import Path
from b3_msh.core.mesh_model import Config
from b3_msh.step.mesh_sections import B3MshSectionStep
from b3_msh.step.mesh_line import B3MshLineStep


@pytest.fixture
def sample_config(tmp_path):
    """Sample config for testing."""
    config_path = tmp_path / "test_config.yml"
    config_data = {
        "workdir": str(tmp_path),
        "geometry": {
            "planform": {
                "npchord": 200,
                "dx": [[0.0]],
                "dy": [[0.0]],
                "z": [[0.0]],
                "chord": [[1.0]],
                "thickness": [[0.1]],
                "twist": [[0.0]]
            }
        },
        "airfoils": [],
        "structure": {"webs": []},
        "mesh": {
            "meshes": [
                {
                    "name": "test_line",
                    "type": "line",
                    "z": [{"type": "plain", "values": [10.0, 20.0]}],
                    "chordwise": {"default": {"n_elem": 20}}
                }
            ]
        }
    }
    
    # Create minimal input mesh
    input_mesh_path = tmp_path / "b3_geo" / "lm1_mesh.vtp"
    input_mesh_path.parent.mkdir(parents=True)
    
    # Create dummy input mesh
    points = np.array([
        [0.0, 0.0, 10.0], [0.5, 0.1, 10.0], [1.0, 0.0, 10.0],
        [0.0, 0.0, 20.0], [0.5, 0.1, 20.0], [1.0, 0.0, 20.0]
    ])
    lines = np.array([3, 0, 1, 2, 3, 3, 4, 5])
    poly = pv.PolyData(points, lines=lines)
    poly["t"] = [0.0, 0.5, 1.0, 0.0, 0.5, 1.0]
    poly["rel_span"] = [0.1, 0.1, 0.1, 0.2, 0.2, 0.2]
    poly.save(str(input_mesh_path))
    
    return config_path, config_data


def test_b3msh_multistep(sample_config):
    """Test B3MshMultiStep execution."""
    config_path, config_data = sample_config
    
    # Write config
    import yaml
    with open(config_path, "w") as f:
        yaml.safe_dump(config_data, f)
    
    # Run section step first
    section_step = B3MshSectionStep(config_path=str(config_path))
    section_step._execute()
    
    # Run line step
    step = B3MshLineStep(config_path=str(config_path))
    step._execute()
    
    # Check outputs
    workdir = Path(config_data["workdir"])
    outputs = list(workdir.glob("b3_msh/lm2_test_line_*"))
    assert len(outputs) >= 2, f"Expected 2+ output files, found {len(outputs)}: {outputs}"
    
    # Check line mesh loaded correctly
    vtp_file = workdir / "b3_msh" / "lm2_test_line_line.vtp"
    assert vtp_file.exists()
    
    mesh = pv.read(str(vtp_file))
    assert mesh.n_points > 0
    assert "panel_id" in mesh.cell_data
    assert "t" in mesh.point_data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
