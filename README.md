# b3_msh

A Python library for handling line meshes representing airfoils with internal structure (like shear webs).

## Features

- Load airfoils from XFOIL format files or numpy arrays
- Apply transformations: scaling, rotation, translation
- Add hard points and shear webs for internal structure
- Remesh airfoils with various refinement options
- Export to PyVista for visualization and further processing
- Parallel processing support for multiple airfoils
- Named hard points and shear webs for organized data output

## Installation

Install from source:

```bash
git clone https://github.com/yourusername/b3_msh.git
cd b3_msh
pip install .
```

Or using uv:

```bash
uv pip install .
```

## Quick Start

```python
from b3_msh.core.airfoil import Airfoil
from b3_msh.core.shear_web import ShearWeb

# Load an airfoil
af = Airfoil.from_xfoil("examples/naca0018.dat")

# Add a shear web
sw = ShearWeb({"type": "plane", "origin": (0.5, 0, 0), "normal": (1, 0, 0), "name": "spar"})
af.add_shear_web(sw, refinement_factor=2.0)

# Remesh
af.remesh(total_n_points=100)

# Plot
af.plot(show_hard_points=True)

# Export to PyVista
mesh = af.to_pyvista()
mesh.save("airfoil.vtp")
```

## Examples

See the `examples/` directory for detailed usage:

- `example_usage.py`: Basic airfoil loading, shear web addition, and meshing
- `multi_airfoil_example.py`: Parallel processing of multiple airfoils
- `explicit_n_elements_example.py`: Explicit element counts per panel

## API Reference

### Airfoil

- `Airfoil(points, **kwargs)`: Initialize from points
- `Airfoil.from_xfoil(filename, **kwargs)`: Load from XFOIL file
- `add_hard_point(t, name=None)`: Add a hard point at parametric t
- `add_shear_web(shear_web, **kwargs)`: Add a shear web
- `remesh(**options)`: Remesh the airfoil
- `to_pyvista()`: Export to PyVista PolyData
- `plot(**kwargs)`: Plot the airfoil

### ShearWeb

- `ShearWeb(definition)`: Initialize with definition dict (plane, line, trailing_edge)

### Utilities

- `process_airfoils_parallel(airfoils, func)`: Process airfoils in parallel

## Testing

Run tests with pytest:

```bash
pytest
```

Or with coverage:

```bash
pytest --cov=b3_msh
```

## CLI

Use the command-line interface:

```bash
b3_msh plot -f airfoil.dat -c 1.0
```

## Contributing

Contributions are welcome! Please open issues or pull requests on GitHub.

## License

MIT License
