#!/bin/bash

# List of files added/modified
pyproject.toml
README.md
src/b3_msh/__init__.py
src/b3_msh/cli/cli.py
src/b3_msh/core/airfoil.py
src/b3_msh/core/airfoil_core.py
src/b3_msh/core/airfoil_mesh.py
src/b3_msh/core/airfoil_viz.py
src/b3_msh/core/shear_web.py
src/b3_msh/statesman_step.py
src/b3_msh/utils/logger.py
src/b3_msh/utils/utils.py
examples/process_blade.py
examples/example_usage.py
examples/multi_airfoil_example.py
examples/explicit_n_elements_example.py
tests/test_airfoil.py
tests/test_statesman.py
tests/test_shear_web.py

ruff format
ruff check --fix > out.txt
uv run pytest -v >> out.txt

git add pyproject.toml
git commit pyproject.toml -m 'Update pyproject.toml with CLI script'
git add README.md
git commit README.md -m 'Update README.md'
git add src/b3_msh/__init__.py
git commit src/b3_msh/__init__.py -m 'Refactor __init__.py'
git add src/b3_msh/cli/cli.py
git commit src/b3_msh/cli/cli.py -m 'Add one-character CLI options'
git add src/b3_msh/core/airfoil.py
git commit src/b3_msh/core/airfoil.py -m 'Refactor Airfoil class'
git add src/b3_msh/core/airfoil_core.py
git commit src/b3_msh/core/airfoil_core.py -m 'Refactor AirfoilCore'
git add src/b3_msh/core/airfoil_mesh.py
git commit src/b3_msh/core/airfoil_mesh.py -m 'Refactor AirfoilMesh'
git add src/b3_msh/core/airfoil_viz.py
git commit src/b3_msh/core/airfoil_viz.py -m 'Refactor AirfoilViz'
git add src/b3_msh/core/shear_web.py
git commit src/b3_msh/core/shear_web.py -m 'Refactor ShearWeb'
git add src/b3_msh/statesman_step.py
git commit src/b3_msh/statesman_step.py -m 'Refactor StatesmanStep'
git add src/b3_msh/utils/logger.py
git commit src/b3_msh/utils/logger.py -m 'Refactor logger'
git add src/b3_msh/utils/utils.py
git commit src/b3_msh/utils/utils.py -m 'Refactor utils'
git add examples/process_blade.py
git commit examples/process_blade.py -m 'Update config path in process_blade.py'
git add examples/example_usage.py
git commit examples/example_usage.py -m 'Update example_usage.py'
git add examples/multi_airfoil_example.py
git commit examples/multi_airfoil_example.py -m 'Update multi_airfoil_example.py'
git add examples/explicit_n_elements_example.py
git commit examples/explicit_n_elements_example.py -m 'Update explicit_n_elements_example.py'
git add tests/test_airfoil.py
git commit tests/test_airfoil.py -m 'Update tests'
git add tests/test_statesman.py
git commit tests/test_statesman.py -m 'Update statesman tests'
git add tests/test_shear_web.py
git commit tests/test_shear_web.py -m 'Update shear web tests'