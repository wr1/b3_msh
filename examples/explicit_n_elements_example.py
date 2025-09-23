import numpy as np
import matplotlib.pyplot as plt
from afmesh.core.airfoil import Airfoil
from afmesh.core.shear_web import ShearWeb

# Load NACA0018 airfoil
af = Airfoil.from_xfoil("examples/naca0018.dat")

# Add hard points to create panels
af.add_hard_point(0.3)
af.add_hard_point(0.7)

# Now there are 3 panels: 0-0.3, 0.3-0.7, 0.7-1.0
panels = af.get_panels()
print(f"Panels: {panels}")

# Remesh with explicit number of elements per panel using dict
# Key is panel_id (0-based index), value is n_elements
n_elements_dict = {0: 10, 1: 20, 2: 15}
af.remesh(n_elements_per_panel=n_elements_dict)

print(f"Total points after remesh: {len(af.current_points)}")

# Plot the airfoil with hard points
af.plot(show_hard_points=True, save_path="explicit_n_elements_airfoil.png")

# Export to PyVista
mesh = af.to_pyvista()
mesh.save("explicit_n_elements_output.vtp")
print(f"Mesh saved with {mesh.n_points} points and {mesh.n_cells} cells")
print(f"Point data keys: {list(mesh.point_data.keys())}")

# Optionally, add a shear web and remesh again
sw = ShearWeb({"type": "plane", "origin": (0.5, 0, 0), "normal": (1, 0, 0), "name": "additional_web"})
af.add_shear_web(sw, n_elements=5)

# Now panels are more: depending on intersections
panels_after = af.get_panels()
print(f"Panels after adding shear web: {panels_after}")

# Remesh with new explicit n_elements (adjust dict accordingly)
# Assuming 4 panels now, set n_elements
n_elements_dict_new = {0: 10, 1: 15, 2: 20, 3: 10}  # Example
if len(panels_after) == len(n_elements_dict_new):
    af.remesh(n_elements_per_panel=n_elements_dict_new)
    print(f"Remeshed with shear web, total points: {len(af.current_points)}")
    af.plot(show_hard_points=True, save_path="explicit_n_elements_with_web.png")
    mesh2 = af.to_pyvista()
    mesh2.save("explicit_n_elements_with_web.vtp")
else:
    print("Adjust n_elements_dict to match number of panels")