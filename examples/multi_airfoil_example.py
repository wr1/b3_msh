import numpy as np
import copy
from afmesh.core.airfoil import Airfoil
from afmesh.core.shear_web import ShearWeb
from afmesh.utils.utils import process_airfoils_parallel
import pyvista as pv


# Function to process each airfoil: add shear web and remesh
def process_airfoil(af):
    """Process an airfoil by adding shear web and remeshing."""
    sw_shared = ShearWeb({"type": "plane", "origin": (0.5, 0, 0), "normal": (1, 0, 0)})
    af.add_shear_web(sw_shared, n_elements=5)
    # Example: set 20 elements in first panel, 30 in second, etc.
    # Assuming 3 panels after adding shear web
    af.remesh(n_elements_per_panel=[20, 30, 25])
    return af


# Load base airfoil
base_af = Airfoil.from_xfoil("examples/naca0018.dat")

# Define the three base airfoils
base_airfoils = [
    {"chord": 1.5, "position": np.array([0, 0, 0]), "rotation": 0},
    {"chord": 1.2, "position": np.array([0, 0, 2]), "rotation": 5},
    {"chord": 1.0, "position": np.array([0, 0, 4]), "rotation": 10},
]

# Interpolate to 30 sections (31 airfoils for 30 intervals)
n_sections = 30
n_airfoils = n_sections + 1
airfoils = []
for i in range(n_airfoils):
    t = i / n_sections  # 0 to 1
    # Linear interpolation between the three
    if t <= 0.5:
        t_local = t * 2  # 0 to 1 between first and second
        chord = base_airfoils[0]["chord"] + t_local * (
            base_airfoils[1]["chord"] - base_airfoils[0]["chord"]
        )
        position = base_airfoils[0]["position"] + t_local * (
            base_airfoils[1]["position"] - base_airfoils[0]["position"]
        )
        rotation = base_airfoils[0]["rotation"] + t_local * (
            base_airfoils[1]["rotation"] - base_airfoils[0]["rotation"]
        )
    else:
        t_local = (t - 0.5) * 2  # 0 to 1 between second and third
        chord = base_airfoils[1]["chord"] + t_local * (
            base_airfoils[2]["chord"] - base_airfoils[1]["chord"]
        )
        position = base_airfoils[1]["position"] + t_local * (
            base_airfoils[2]["position"] - base_airfoils[1]["position"]
        )
        rotation = base_airfoils[1]["rotation"] + t_local * (
            base_airfoils[2]["rotation"] - base_airfoils[1]["rotation"]
        )
    af = copy.deepcopy(base_af)
    af.chord = chord
    af.position = position
    af.rotation = rotation
    airfoils.append(af)

# Process airfoils in parallel
processed_airfoils = process_airfoils_parallel(airfoils, process_airfoil)

# Create MultiBlock for all meshes
multi_block = pv.MultiBlock()
for i, af in enumerate(processed_airfoils):
    mesh = af.to_pyvista()
    multi_block.append(mesh, f"Section_{i}")

# Save all to a single VTM file
multi_block.save("airfoils_30_sections.vtm")
print(f"Saved {len(processed_airfoils)} airfoil meshes to airfoils_30_sections.vtm")

print("30 interpolated airfoils with shared shear web processed in parallel.")
