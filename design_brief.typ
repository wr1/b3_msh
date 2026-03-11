#set page(margin: 1in)
#set text(font: "New Computer Modern", size: 12pt)

= b3_msh

// Author: wr1 <8971152+wr1@users.noreply.github.com>
// Consolidated & updated design brief (March 2026)
// Merges original functionality with architectural decisions for 2D/3D separation

b3_msh is a Python library for handling line meshes representing airfoils (and full blade sections) with internal structure such as shear webs. It supports both 2D airfoil processing and 3D surface meshing within a single, logically cohesive codebase.

The base of every airfoil is an XFOIL-style point list (x-y and optional z coordinates). Internally, this list is interpolated with a spline using a parametric coordinate #emph[t ∈ [0, 1]] (LE = 0, TE = 1). All subsequent operations (remeshing, hard-point insertion, shear-web definition) operate on this spline to prevent drift.

== Architectural Overview

b3_msh is deliberately structured as a unified meshing library while maintaining strict separation of concerns between 2D and 3D workflows. This prevents feature creep, simplifies testing, and keeps the codebase maintainable.

- *2D Meshing (Airfoil/Blade Section Processing)*:  
  Handled by the `Airfoil` family of classes (in `core/`) and the `B3MshStep` pipeline (in `step/blade_mesh_step.py`).  
  Focus: individual airfoil remeshing, hard points, panels, shear webs, and line-mesh generation in the local x-y plane.  
  Output: line meshes (VTU/VTP) suitable for 2D analysis or as input to 3D steps.

- *3D Meshing (Surface Processing)*:  
  Handled by the dedicated `B3MshSurfaceStep` (in `step/surface_mesh_step.py`).  
  Focus: stacking multiple airfoil sections, propagating chordwise/spanwise coordinates (TE distance, chordwise arc length, spanwise position, etc.), and generating full 3D surface meshes.  
  Operates in true 3D space and builds directly on 2D `Airfoil` objects.

- *Shared Core*:  
  `AirfoilCore`, `ShearWeb`, `RibbonWeb`, and utilities in `core/` and `utils/`.  
  Shared components are minimal and explicitly tested for both pipelines; 2D changes never leak into 3D (and vice versa).

=== Step/State Objects (b3_state integration)

- `B3MshStep`: processes pre-computed 2D sections, inserts shear webs/hard points, and writes a merged VTP line mesh.  
- `B3MshSurfaceStep`: consumes the 2D line meshes, performs 3D surface generation, and propagates all required coordinates.  

The two steps have completely separate input/output manifests and dependency graphs; combining them would harm testability and state management. They remain together in one library because *meshing* is the single domain responsibility of b3_msh.

== Functionality

=== Input
- Normalised (chord = 1) XFOIL files or raw NumPy arrays.  
- Full-scale 3D airfoils (x, y, z already supplied).  
- Automatic scaling, rotation, and translation to target position.

=== Remeshing
- Regenerates the mesh from the *original* input spline (never from a previously remeshed result).  
- Supports:
  - Local refinement relative to current distribution  
  - Fixed number of points per panel  
  - Absolute or relative target element length  
  - Arbitrary t-distribution (including hard-point forcing)

=== Hard Points & Panels
- Hard points are nodes that survive any remeshing (default: LE t=0 and TE t=1).  
- Can be specified by parametric t, by name, or by geometric construction (see shear webs).  
- A *panel* is the segment between two consecutive hard points.  
- Adding a shear web at t=0.3 and t=0.7 automatically creates three panels (0–0.3, 0.3–0.7, 0.7–1).

=== Shear Webs

==== 2D / Basic 3D
- Defined by:
  - Plane (origin + normal)  
  - Straight line in the 2D plane  
- Intersection with the airfoil spline yields two hard points.  
- Named webs (default `web0`, `web1`, …) automatically attach coordinate arrays to the output mesh (absolute/relative distance from each web endpoint along the surface).

==== Ribbon Webs (3D-only)
- New `Ribbon` class.  
- Defined relative to a *reference web* plus a list of key points `[[z, offset], …]`.  
- Offset is interpolated with PCHIP for any intermediate spanwise location, enabling swept/angled ribbon webs that follow the blade twist and sweep.

== Tech Stack
- Core interpolation: SciPy PCHIP univariate spline  
- Array handling: NumPy (fully vectorised)  
- Output & visualisation: PyVista (VTU/VTP, line and surface meshes)  
- Configuration: Pydantic models  
- Testing: pytest + coverage  
- Plotting: Matplotlib  
- Parallelism: multiprocessing at the airfoil/section level (full blades processed in parallel)  

== Testing Strategy
- Separate test suites:
  - `tests/test_airfoil.py`, `tests/test_shear_web.py` (2D)  
  - `tests/test_surface_mesh.py` (3D)  
- Shared components tested in both contexts.  
- PyVista output format is explicitly verified after every third-party change.

== Key Design Principles
- *Single responsibility*: each module/file owns exactly one concern.  
- *Strict separation of 2D/3D*: no cross-contamination.  
- *Immutable original spline*: all remeshing derives from the input data only.  
- *Extensibility*: new web types, mesh specs, or output formats can be added via new Pydantic models or step classes.  
- *Performance-first*: vectorised NumPy + multiprocessing wherever possible.

== Maintenance Notes
- When touching `AirfoilCore` or any shared utility, run the full 2D *and* 3D test suites.  
- New meshing features belong in 2D, 3D, or shared—prefer separation unless the feature is truly common.  
- Keep this document up-to-date when new steps or web types are introduced.  
- PyVista compatibility must be re-validated after library upgrades (recent line-format fixes affected both pipelines).

This design keeps b3_msh focused, testable, and future-proof while delivering a clean, powerful interface for both 2D airfoil work and full 3D blade surface meshing.