#!/bin/bash

# List of files added or modified
src/b3_msh/cli/commands.py
src/b3_msh/core/airfoil.py
src/b3_msh/core/airfoil_core.py
src/b3_msh/core/airfoil_mesh.py
src/b3_msh/core/airfoil_viz.py
src/b3_msh/core/shear_web.py

# Run ruff format
ruff format

# Run ruff check --fix and pipe to out.txt
ruff check --fix > out.txt

# Run pytest and append to out.txt
uv run pytest -v >> out.txt

# Git commit each file
git add src/b3_msh/cli/commands.py
git commit -m 'Refactor blade function to reduce complexity'

git add src/b3_msh/core/airfoil.py
git commit -m 'Fix long docstring lines'

git add src/b3_msh/core/airfoil_core.py
git commit -m 'Fix long docstring lines'

git add src/b3_msh/core/airfoil_mesh.py
git commit -m 'Fix long docstring line'

git add src/b3_msh/core/airfoil_viz.py
git commit -m 'Fix long docstring line'

git add src/b3_msh/core/shear_web.py
git commit -m 'Fix long docstring lines'

git add admin.sh
git commit -m 'Add admin.sh script for automation'