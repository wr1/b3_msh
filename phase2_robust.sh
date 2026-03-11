#!/bin/bash
# Phase 2 - SUPER ROBUST (Multiline 2D → 2d/ + critical fixes from Phase 1)
# Fixes the broken __init__.py import, moves all blade processing, renames step, creates façade
# Safe to run multiple times. Handles missing files gracefully.

set -e

root="src/b3_msh"

echo "=== SUPER ROBUST Phase 2 Helper started ==="

# 0. Critical fix: update main package __init__.py (was still pointing to old core/airfoil)
cat > "$root"/__init__.py << 'EOT'
"""b3_msh package initialization."""

from .meshing.airfoil import Airfoil
from .meshing.webs import ShearWeb
from .utils.parallel_utils import process_airfoils_parallel

__all__ = ["Airfoil", "ShearWeb", "process_airfoils_parallel"]
EOT

echo "✅ Fixed main __init__.py import"

# 1. Create directories
mkdir -p "$root"/2d/{processing,step} "$root"/3d/{processing,step} "$root"/step

# 2. Safe move function
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

# Move blade (multiline) processing files
move_safe "$root"/core/processing/blade_load_config.py "$root"/2d/processing/blade_load_config.py
move_safe "$root"/core/processing/blade_save_vtp.py "$root"/2d/processing/blade_save_vtp.py
move_safe "$root"/core/processing/blade_merge_meshes.py "$root"/2d/processing/blade_merge_meshes.py
move_safe "$root"/core/processing/blade_save_vtm.py "$root"/2d/processing/blade_save_vtm.py
move_safe "$root"/core/processing/blade_process_sections.py "$root"/2d/processing/blade_process_sections.py
move_safe "$root"/core/processing/process_blade_config.py "$root"/2d/processing/process_blade_config.py

# Move blade step and rename class later via sed
move_safe "$root"/step/blade_mesh_step.py "$root"/2d/step/B3MshLineStep.py

# Move surface processing files to 3d/ (needed for consistency)
move_safe "$root"/core/processing/process_surface_config.py "$root"/3d/processing/process_surface_config.py
move_safe "$root"/core/processing/surface_load_config.py "$root"/3d/processing/surface_load_config.py
move_safe "$root"/core/processing/surface_process_sections.py "$root"/3d/processing/surface_process_sections.py
move_safe "$root"/core/processing/surface_build_faces.py "$root"/3d/processing/surface_build_faces.py
move_safe "$root"/core/processing/surface_build_point_data.py "$root"/3d/processing/surface_build_point_data.py
move_safe "$root"/core/processing/surface_collect_section_data.py "$root"/3d/processing/surface_collect_section_data.py
move_safe "$root"/core/processing/surface_build_cell_data.py "$root"/3d/processing/surface_build_cell_data.py

# Move surface step
move_safe "$root"/step/surface_mesh_step.py "$root"/3d/step/B3MshSurfaceStep.py

# 3. Update imports in moved files (fix old core/processing paths)
for file in "$root"/2d/**/*.py "$root"/3d/**/*.py "$root"/2d/step/B3MshLineStep.py "$root"/3d/step/B3MshSurfaceStep.py; do
  if [[ -f "$file" ]]; then
    sed -i 's|from \.\.core.processing|from ....2d.processing|g' "$file"
    sed -i 's|from \.\.core.processing|from ....3d.processing|g' "$file"
    sed -i 's|from \.\.step.blade_mesh_step|from ....2d.step.B3MshLineStep|g' "$file"
    sed -i 's|from \.\.step.surface_mesh_step|from ....3d.step.B3MshSurfaceStep|g' "$file"
    sed -i 's|from \.\.meshing.airfoil|from ....meshing.airfoil|g' "$file"
  fi
done

# 4. Rename class inside B3MshLineStep.py (was still B3MshStep)
sed -i 's/class B3MshStep/class B3MshLineStep/g' "$root"/2d/step/B3MshLineStep.py
sed -i 's/B3MshStep/B3MshLineStep/g' "$root"/2d/step/B3MshLineStep.py

# 5. Create step façade (public for b3_state)
cat > "$root"/step/line.py << 'EOT'
"""Public re-export for B3MshLineStep."""
from ..2d.step.B3MshLineStep import B3MshLineStep

__all__ = ["B3MshLineStep"]
EOT

cat > "$root"/step/surface.py << 'EOT'
"""Public re-export for B3MshSurfaceStep."""
from ..3d.step.B3MshSurfaceStep import B3MshSurfaceStep

__all__ = ["B3MshSurfaceStep"]
EOT

cat > "$root"/step/__init__.py << 'EOT'
"""Public step façade for b3_state workflows."""
from .line import B3MshLineStep
from .surface import B3MshSurfaceStep

__all__ = ["B3MshLineStep", "B3MshSurfaceStep"]
EOT

# 6. Create 2d/ and 3d/ __init__.py
cat > "$root"/2d/__init__.py << 'EOT'
"""Multiline (2D multi-section blade) package."""
from .step.B3MshLineStep import B3MshLineStep

__all__ = ["B3MshLineStep"]
EOT

cat > "$root"/3d/__init__.py << 'EOT'
"""Surface (3D quad mesh) package."""
from .step.B3MshSurfaceStep import B3MshSurfaceStep

__all__ = ["B3MshSurfaceStep"]
EOT

# 7. Clean up old core/processing if empty
if [[ -d "$root/core/processing" ]] && [[ -z "$(ls -A "$root/core/processing" 2>/dev/null)" ]]; then
  rmdir "$root/core/processing"
fi
if [[ -d "$root/core" ]] && [[ -z "$(ls -A "$root/core" 2>/dev/null)" ]]; then
  rmdir "$root/core"
fi

# 8. Git commits
git add "$root"/2d/ "$root"/3d/ "$root"/step/ "$root"/__init__.py
git commit -m 'refactor: complete Phase 2 - multiline moved to 2d/, surface to 3d/, façade created' || true

git add phase2_robust.sh
# git commit phase2_robust.sh -m 'chore: add super robust Phase 2 helper' || true

echo "=== SUPER ROBUST Phase 2 COMPLETED ==="
echo ""
echo "Verification:"
echo "  ruff format . && ruff check . --fix"
echo "  uv run pytest -q"
echo "  ls src/b3_msh/"
echo ""
echo "When green, say 'start phase 3' for CLI/examples/tests cleanup."