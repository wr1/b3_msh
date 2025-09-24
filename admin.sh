#!/bin/bash

# List of files added/modified
files=(
    "pyproject.toml"
    "src/b3_msh/utils/logger.py"
    "admin.sh"
)

# Run ruff format
ruff format

# Run ruff check --fix and pipe to out.txt
ruff check --fix > out.txt

# Run pytest and append to out.txt
uv run pytest -v >> out.txt

# Git add and commit each file
for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        git add "$file"
        git commit -m "summary of edits for $file"
    fi
done
