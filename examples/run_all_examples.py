"""Run all example scripts in sequence."""

import os
import subprocess
import sys

# List of example scripts to run
examples = [
    "process_blade.py",
    "example_usage.py",
    "multi_airfoil_example.py",
    "explicit_n_elements_example.py",
    "run_blade_with_ribbon.py",
]

# Run from the project root directory
project_root = os.path.dirname(os.path.dirname(__file__))
os.chdir(project_root)

for ex in examples:
    ex_path = os.path.join("examples", ex)
    result = subprocess.run([sys.executable, ex_path])
    if result.returncode != 0:
        sys.exit(1)
