import os
import subprocess
import sys

import pytest

# List of example scripts to test
examples = [
    "examples/process_blade.py",
    "examples/example_usage.py",
    "examples/multi_airfoil_example.py",
    "examples/explicit_n_elements_example.py",
    "examples/run_blade_with_ribbon.py",
    "examples/run_surface_example.py",
    "examples/run_blade_example.py",
    "examples/debug_3d_web_intersection.py",
    "examples/process_surface.py",
]


@pytest.mark.parametrize("example", examples)
def test_example_runs(example):
    """Test that each example script runs without error."""
    # Run from the project root directory
    project_root = os.path.dirname(os.path.dirname(__file__))
    os.chdir(project_root)
    result = subprocess.run([sys.executable, example], capture_output=True, text=True)
    assert result.returncode == 0, (
        f"{example} failed with stdout: {result.stdout}, stderr: {result.stderr}"
    )
