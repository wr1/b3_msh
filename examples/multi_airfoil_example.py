import numpy as np
import matplotlib.pyplot as plt
import copy
from afmesh.core.airfoil import Airfoil
from afmesh.core.shear_web import ShearWeb
from afmesh.utils.utils import process_airfoils_parallel

# Function to process each airfoil: add shear web and remesh
def process_airfoil(af):
    """Process an airfoil by adding shear web and remeshing."""
    sw_shared = ShearWeb({"type": "plane", "origin": (0.5, 0, 0), "normal": (1, 0, 0)})
    af.add_shear_web(sw_shared, n_elements=5)
    af.remesh(total_n_points=100)
    return af

# Load base airfoil
base_af = Airfoil.from_xfoil("examples/naca0018.dat")

# Create three copies with different positions, chords, and twists
af1 = copy.deepcopy(base_af)
af1.chord = 1.5
af1.position = np.array([0, 0, 0])
af1.rotation = 0

af2 = copy.deepcopy(base_af)
af2.chord = 1.2
af2.position = np.array([0, 0, 2])
af2.rotation = 5

af3 = copy.deepcopy(base_af)
af3.chord = 1.0
af3.position = np.array([0, 0, 4])
af3.rotation = 10

airfoils = [af1, af2, af3]

# Process airfoils in parallel
processed_airfoils = process_airfoils_parallel(airfoils, process_airfoil)

# Plot all airfoils in the same plot
plt.figure()
for i, af in enumerate(processed_airfoils):
    points = af.current_points
    plt.plot(
        points[:, 0],
        points[:, 1],
        label=f"z={af.position[2]:.1f}, chord={af.chord}, twist={af.rotation}°",
    )
    # Plot shear webs
    for sw in af.shear_webs:
        t1, t2 = sw.compute_intersections(af)
        p1 = af.get_points([t1])[0]
        p2 = af.get_points([t2])[0]
        plt.plot([p1[0], p2[0]], [p1[1], p2[1]], "g--", linewidth=2)
plt.axis("equal")
plt.xlabel("x")
plt.ylabel("y")
plt.title("Multiple Airfoils with Shared Shear Web (Processed in Parallel)")
plt.legend()
plt.grid(True)
plt.savefig("airfoils_multi.png")

# Export each to PyVista
for i, af in enumerate(processed_airfoils, 1):
    mesh = af.to_pyvista()
    mesh.save(f"output_multi_{i}.vtp")
    print(f"Mesh {i} has {mesh.n_points} points and {mesh.n_cells} cells")

print("Multiple airfoils with shared shear web processed in parallel.")
