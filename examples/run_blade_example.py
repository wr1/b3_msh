"""Run blade processing example with the config."""

import subprocess
import sys
import os

# Run the blade command with the config
config_path = "examples/blade_test.yml"
if not os.path.exists(config_path):
    print(f"Config file {config_path} not found. Please ensure airfoil files are present.")
    sys.exit(1)

# Note: This assumes the input mesh exists; in practice, generate or provide lm1_mesh.vtp
print(f"Running blade processing with config {config_path}...")
result = subprocess.run([sys.executable, "-m", "b3_msh.cli.cli", "blade", config_path])
if result.returncode != 0:
    print(f"Failed with exit code {result.returncode}")
else:
    print("Blade processing completed successfully.")
