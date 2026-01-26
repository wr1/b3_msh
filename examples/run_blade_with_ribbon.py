"""Run blade processing example with ribbon web."""

import os
import subprocess
import sys

# Run the blade command with the ribbon config
config_path = "examples/blade_test_ribbon.yml"
if not os.path.exists(config_path):
    sys.exit(1)

# Note: Assumes input mesh exists; generate or provide lm1_mesh.vtp
result = subprocess.run([sys.executable, "-m", "b3_msh.cli.cli", "blade", config_path])
if result.returncode != 0:
    pass
else:
    pass
