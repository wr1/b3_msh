"""Run surface meshing example with the config."""

import os
import subprocess
import sys

# Run the surface command with the config
config_path = "examples/blade_test_surface.yml"
if not os.path.exists(config_path):
    sys.exit(1)

# Note: Assumes input mesh exists; generate or provide lm1_mesh.vtp
result = subprocess.run([sys.executable, "-m", "b3_msh.cli.cli", "surface", config_path])
if result.returncode != 0:
    pass
else:
    pass
