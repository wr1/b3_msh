#!/bin/bash

files="
pyproject.toml
README.md
src/b3_msh/statesman_step.py
src/b3_msh/__init__.py
src/b3_msh/cli/commands.py
src/b3_msh/cli/cli.py
src/b3_msh/core/airfoil_viz.py
src/b3_msh/core/airfoil_core.py
src/b3_msh/core/airfoil.py
src/b3_msh/core/blade_processing.py
src/b3_msh/core/airfoil_mesh.py
src/b3_msh/core/shear_web.py
src/b3_msh/utils/logger.py
src/b3_msh/utils/utils.py
examples/process_blade.py
examples/example_usage.py
examples/multi_airfoil_example.py
examples/explicit_n_elements_example.py
examples/run_all_examples.py
tests/test_airfoil.py
tests/test_statesman.py
tests/test_shear_web.py
tests/test_blade_processing.py
"

ruff format
ruff check --fix > out.txt
uv run pytest -v >> out.txt

for file in $files; do
    git add $file
    git commit $file -m "summary of edits for $file"
done
