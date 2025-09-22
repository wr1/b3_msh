import numpy as np
from afmesh.core.airfoil import Airfoil
from afmesh.core.shear_web import ShearWeb

# Load NACA0018 from file
af = Airfoil.from_xfoil("examples/naca0018.dat")

# Add shear web with refinement
sw = ShearWeb({"type": "plane", "origin": (0.5, 0, 0), "normal": (1, 0, 0)})
af.add_shear_web(sw, refinement_factor=2.0)

# Add trailing edge shear web
sw_te = ShearWeb({"type": "trailing_edge"})
af.add_shear_web(sw_te)

# Add shear web with n_elements
sw_mesh = ShearWeb({"type": "plane", "origin": (0.3, 0.05, 0), "normal": (0, 1, 0)})
af.add_shear_web(sw_mesh, n_elements=10)

# Remesh with total points, using shear web refinement
af.remesh(total_n_points=100)

# Plot
af.plot(show_hard_points=True, save_path="airfoil.png")

# Export to PyVista
mesh = af.to_pyvista()
print(f"Mesh has {mesh.n_points} points and {mesh.n_cells} cells")

# Write to VTP
mesh.save("output.vtp")

# Example with NACA0018 from file and hard points at t=0.3 and t=0.7
af_naca = Airfoil.from_xfoil("examples/naca0018.dat")
af_naca.add_hard_point(0.3)
af_naca.add_hard_point(0.7)
af_naca.remesh(total_n_points=50)
af_naca.plot(show_hard_points=True, save_path="airfoil_naca.png")

# Example with meshed shear webs
print("Shear webs are included in the mesh and plot above.")

# Second example: Multiple airfoils with shared shear web
import copy

# Load base airfoil
base_af = Airfoil.from_xfoil("examples/naca0018.dat")

# Create three copies with different positions, chords, and twists
af1 = copy.deepcopy(base_af)
af1.chord = 1.5
af1.position = np.array([0, 0, 0])
af1.rotation = 0
af1.current_points = af1.get_points(af1.current_t)  # Update points

af2 = copy.deepcopy(base_af)
af2.chord = 1.2
af2.position = np.array([0, 0, 2])
af2.rotation = 5
af2.current_points = af2.get_points(af2.current_t)

af3 = copy.deepcopy(base_af)
af3.chord = 1.0
af3.position = np.array([0, 0, 4])
af3.rotation = 10
af3.current_points = af3.get_points(af3.current_t)

# Add the same planar shear web to all airfoils (goes through all)
sw_shared = ShearWeb({"type": "plane", "origin": (0.5, 0, 0), "normal": (1, 0, 0)})
for af in [af1, af2, af3]:
    af.add_shear_web(sw_shared, n_elements=5)
    af.remesh(total_n_points=100)

# Plot all airfoils in the same plot
plt.figure()
for i, af in enumerate([af1, af2, af3]):
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
plt.title("Multiple Airfoils with Shared Shear Web")
plt.legend()
plt.grid(True)
plt.savefig("airfoils_multi.png")

# Export each to PyVista
for i, af in enumerate([af1, af2, af3], 1):
    mesh = af.to_pyvista()
    mesh.save(f"output_multi_{i}.vtp")
    print(f"Mesh {i} has {mesh.n_points} points and {mesh.n_cells} cells")

print("Multiple airfoils with shared shear web created.")
