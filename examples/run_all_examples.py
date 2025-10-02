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

# Change to examples directory
examples_dir = os.path.dirname(__file__)
os.chdir(examples_dir)

for ex in examples:
    print(f"Running {ex}...")
    result = subprocess.run([sys.executable, ex])
    if result.returncode != 0:
        print(f"Failed to run {ex} with return code {result.returncode}")
        sys.exit(1)
    print(f"{ex} completed successfully.\n")

print("All examples ran successfully!")
