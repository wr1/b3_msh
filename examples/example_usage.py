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
