"""Run all example scripts in sequence."""

import subprocess
import sys
import os

# List of example scripts to run
examples = [
    "process_blade.py",
    "example_usage.py",
    "multi_airfoil_example.py",
    "explicit_n_elements_example.py",
]

# Run from the project root directory
project_root = os.path.dirname(os.path.dirname(__file__))
os.chdir(project_root)

for ex in examples:
    ex_path = os.path.join("examples", ex)
    print(f"Running {ex_path}...")
    result = subprocess.run([sys.executable, ex_path])
    if result.returncode != 0:
        print(f"Failed to run {ex_path} with return code {result.returncode}")
        sys.exit(1)
    print(f"{ex_path} completed successfully.\n")

print("All examples ran successfully!")
