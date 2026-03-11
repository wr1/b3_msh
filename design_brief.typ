#set page(margin: 1in)
#set text(font: "New Computer Modern", size: 12pt)

= b3_msh – Architecture & Development Guide

// Author: wr1 + LLM Maintainers
// Date: March 2026
// Status: Authoritative reference for all future development

b3_msh is a focused Python library for creating high-quality line and surface meshes of airfoils and wind turbine blades, with full support for internal structures (shear webs).

The library deliberately maintains a clean separation between shared meshing logic, multiline (2D multi-section blade line meshes), and surface (3D quad mesh) workflows.

== Canonical Project Structure

All code *must* follow this exact layout (valid Python package names only):

```plain
src/b3_msh/
├── cli/                    # Command-line interface (one function per file)
├── meshing/                # Shared core meshing logic (single source of truth)
│   ├── airfoil/            # AirfoilCore, Mesh, Plot, Viz, remeshing
│   ├── webs/               # ShearWeb, RibbonWeb, intersection logic
│   ├── sections.py         # Shared section extraction
│   └── __init__.py
├── multiline/              # Multiline (2D multi-section blade line meshes)
│   ├── processing/         # Blade-specific config & merging
│   └── step/               # B3MshLineStep
├── surface/                # Surface (3D quad mesh)
│   ├── processing/         # Surface-specific face building & data propagation
│   └── step/               # B3MshSurfaceStep
├── step/                   # Public façade for b3_state
│   ├── __init__.py         # re-exports LineStep and SurfaceStep
│   ├── line.py
│   └── surface.py
├── utils/                  # Logger, parallel processing, helpers
└── __init__.py
```

This structure is mandatory. Do not create new top-level directories without first updating this document.

== Meshing Modes

The library explicitly supports three distinct modes:

- *Line* (pure 2D single section):  
  Handled directly by the `Airfoil` class in `meshing/airfoil/`.  
  Used by CLI commands `plot` and `remesh`.  
  Produces a single 2D line mesh (with optional shear webs).

- *Multiline* (2D multi-section blade):  
  Handled in `multiline/`.  
  Stacks multiple line meshes into VTP or VTM output.  
  Uses shared `meshing/` components for consistent section processing.

- *Surface* (3D quad mesh):  
  Handled in `surface/`.  
  Connects multiline sections into full 3D surface quads.  
  Propagates chordwise / spanwise coordinates and panel IDs.

== Layer Responsibilities

- *meshing/ *: All fundamental geometry, spline interpolation, hard points, panels, and web intersection logic. This is the heart of the library and is used by *all three modes*.
- *multiline/ *: Responsible for multiline (multi-section line-mesh) blade processing and VTP/VTM combination.
- *surface/ *: Responsible for surface (3D quad) meshing by connecting adjacent sections.
- *cli/ *: Thin command layer. Must remain one public function per file.
- *step/ *: Thin re-exports so `b3_state` workflows can import `B3MshLineStep` and `B3MshSurfaceStep` cleanly.

== Core Concepts

- Parametric coordinate *t ∈ [0, 1]* (LE = 0, TE = 1). All remeshing derives from the original spline.
- Hard points define panel boundaries and survive remeshing.
- Shear webs (plane, line, trailing_edge, ribbon) automatically insert hard points.
- Ribbon webs support spanwise-varying offsets via PCHIP interpolation.

== Design Principles

- Single responsibility per file and per module.
- Strict separation of line / multiline / surface logic — no cross-contamination.
- `meshing/` is the only place for core geometry algorithms.
- One public function or class per `.py` file where practical.
- All changes must be accompanied by updated tests in the matching test directory.
- Prefer explicit over implicit. Favor readability for both humans and LLMs.
- Never delete or rename files outside the current working directory.

== Examples

The `examples/` directory contains runnable Python scripts that demonstrate *all three modes* programmatically:

- `example_usage.py` and `explicit_n_elements_example.py` → Line (single section)
- `process_blade.py` and `run_blade_example.py` → Multiline (blade)
- `process_surface.py` and `run_surface_example.py` → Surface (with ribbon webs)

These examples serve as living documentation and must continue to run after any change.

== Tech Stack

- Core: NumPy (vectorised), SciPy PCHIP
- Meshing & I/O: PyVista
- Configuration: Pydantic
- CLI: treeparse
- State management: b3_state
- Formatting: ruff
- Testing: pytest

== Testing Strategy

- `tests/meshing/` — core airfoil and web logic (used by all modes)
- `tests/multiline/` — multiline pipeline
- `tests/surface/`   — surface pipeline
- All examples must continue to run after any change.

== Maintenance Rules (Mandatory for LLMs)

1. Before editing anything in `meshing/`, run the full test suite (line + multiline + surface).
2. When adding new functionality, decide first: shared (`meshing/`), line-only, multiline (`multiline/`), or surface-only (`surface/`).
3. Keep this `design_brief.typ` up to date when the architecture changes.
4. Use high-level one-line docstrings and clear function names.
5. Directory tree must always accurately reflect current responsibilities.

This document is the single source of truth for the architecture of b3_msh. All future development must align with it.
