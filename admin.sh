ruff format
ruff check --fix > out.txt
uv run pytest -v >> out.txt
git add pyproject.toml
git commit pyproject.toml -m 'Rename project from afmesh to b3_msh in pyproject.toml'
git add README.md
git commit README.md -m 'Update README.md for b3_msh rename'
git add src/b3_msh/__init__.py
git commit src/b3_msh/__init__.py -m 'Update __init__.py imports for b3_msh'
git add src/b3_msh/cli/cli.py
git commit src/b3_msh/cli/cli.py -m 'Update CLI name and entry point for b3_msh'
git add examples/example_usage.py
git commit examples/example_usage.py -m 'Update imports in example_usage.py for b3_msh'
git add examples/multi_airfoil_example.py
git commit examples/multi_airfoil_example.py -m 'Update imports in multi_airfoil_example.py for b3_msh'
git add examples/explicit_n_elements_example.py
git commit examples/explicit_n_elements_example.py -m 'Update imports in explicit_n_elements_example.py for b3_msh'
git add tests/test_airfoil.py
git commit tests/test_airfoil.py -m 'Update imports in test_airfoil.py for b3_msh'
git add tests/test_shear_web.py
git commit tests/test_shear_web.py -m 'Update imports in test_shear_web.py for b3_msh'
git add admin.sh
git commit admin.sh -m 'Add admin.sh script for formatting, checking, and committing changes'