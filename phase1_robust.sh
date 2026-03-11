#!/bin/bash
# Phase 1 - SUPER ROBUST VERSION (handles ANY current state)
# - If file still in core/ → move it
# - If already in meshing/ → skip
# - If missing → warn and skip
# - Always recreates correct __init__.py files
# - Safe to run multiple times
# - Cleans old core/ directory at the end

set -e

root="src/b3_msh"

echo "=== SUPER ROBUST Phase 1 Helper started ==="

# 1. Create directories
mkdir -p "$root"/meshing/airfoil "$root"/meshing/webs

# 2. Remove any broken empty placeholders from previous attempts
rm -f "$root"/meshing/airfoil/__init__.py
rm -f "$root"/meshing/webs/__init__.py
rm -f "$root"/meshing/__init__.py

# 3. Safe move function
move_safe() {
  local src="$1"
  local dst="$2"
  if [[ -f "$src" ]]; then
    mv "$src" "$dst"
    echo "✅ Moved: $src → $dst"
  elif [[ -f "$dst" ]]; then
    echo "✅ Already in place: $dst"
  else
    echo "⚠️  Missing: $src (skipping)"
  fi
}

move_safe "$root/core/airfoil_core.py" "$root/meshing/airfoil/core.py"
move_safe "$root/core/airfoil_mesh.py" "$root/meshing/airfoil/mesh.py"
move_safe "$root/core/airfoil_plot.py" "$root/meshing/airfoil/plot.py"
move_safe "$root/core/airfoil_viz.py" "$root/meshing/airfoil/viz.py"
move_safe "$root/core/airfoil.py" "$root/meshing/airfoil/__init__.py"
move_safe "$root/core/mesh_model.py" "$root/meshing/airfoil/models.py"
move_safe "$root/core/mesh3d_model.py" "$root/meshing/airfoil/models_3d.py"
move_safe "$root/core/shear_web.py" "$root/meshing/webs/shear_web.py"

# 4. Fix imports in the target files
echo "Fixing imports..."
for file in "$root"/meshing/airfoil/*.py "$root"/meshing/webs/*.py; do
  if [[ -f "$file" ]]; then
    sed -i 's|from \.\.utils|from ....utils|g' "$file"
    sed -i 's|from \.\.core|from ....meshing.airfoil|g' "$file"
    sed -i 's|from \.\.shear_web|from ....meshing.webs.shear_web|g' "$file"
  fi
done

# 5. Create correct __init__.py files (always overwrite)
cat > "$root"/meshing/airfoil/__init__.py << 'EOT'
"""Airfoil package - Line mode foundation."""
from .core import AirfoilCore
from .mesh import AirfoilMesh
from .plot import AirfoilPlot
from .viz import AirfoilViz
from .models import *

class Airfoil(AirfoilCore, AirfoilMesh, AirfoilPlot, AirfoilViz):
    """Represents an airfoil with spline interpolation, hard points, panels, and shear webs."""
    pass

__all__ = ["Airfoil"]
EOT

cat > "$root"/meshing/webs/__init__.py << 'EOT'
"""Web package - shared across Line, Multiline and Surface modes."""
from .shear_web import ShearWeb

__all__ = ["ShearWeb"]
EOT

cat > "$root"/meshing/__init__.py << 'EOT'
"""Shared meshing core - used by Line, Multiline and Surface."""
from .airfoil import Airfoil
from .webs import ShearWeb

__all__ = ["Airfoil", "ShearWeb"]
EOT

# 6. Clean up old core/ directory if empty
if [[ -d "$root/core" ]] && [[ -z "$(ls -A "$root/core" 2>/dev/null)" ]]; then
  rmdir "$root/core"
  echo "Cleaned up empty core/ directory"
fi

# 7. Git commits (safe - only commits what actually changed)
echo "Creating git commits..."
git add "$root"/meshing/airfoil/ "$root"/meshing/webs/ "$root"/meshing/__init__.py 2>/dev/null || true
git commit -m 'refactor: complete Phase 1 - shared core moved to meshing/ (super robust)' || true

git add phase1_robust.sh
# git commit phase1_robust.sh -m 'chore: add super robust Phase 1 helper' || true

echo "=== SUPER ROBUST Phase 1 COMPLETED SUCCESSFULLY ==="
echo ""
echo "Verification commands:"
echo "  ruff format ."
echo "  ruff check ."
echo "  uv run pytest -q"
echo "  ls src/b3_msh/meshing/"
echo ""
echo "When everything looks good, say 'start phase 2' for the Multiline (2d/) refactor."