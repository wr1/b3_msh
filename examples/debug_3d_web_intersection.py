"""Debug example to demonstrate true 3D web plane intersection.

With airfoil at z=40 and web origin at z=0, z-normal affects intersections.
"""

import numpy as np

from b3_msh.core.airfoil import Airfoil
from b3_msh.core.shear_web import ShearWeb
from b3_msh.utils.logger import get_logger

logger = get_logger(__name__)

# Load a sample airfoil and position it at z=40
af = Airfoil.from_xfoil("examples/naca0018.dat", position=(0, 0, 40))

# Define web origin at z=0 (different from airfoil z=40)
origin = (0.5, 0, 0)  # z=0
normal_with_z = (1, 0, 0.001)  # Has z-component
normal_without_z = (1, 0, 0)  # No z-component

sw1 = ShearWeb({"type": "plane", "origin": origin, "normal": normal_with_z, "name": "web_with_z"})
sw2 = ShearWeb(
    {
        "type": "plane",
        "origin": origin,
        "normal": normal_without_z,
        "name": "web_without_z",
    }
)

# Compute intersections
t1_z, t2_z = sw1.compute_intersections(af)
t1_no_z, t2_no_z = sw2.compute_intersections(af)

logger.info("Airfoil at z=40, web origin at z=0")
logger.info(f"Intersections with z-normal {normal_with_z}: t1={t1_z:.4f}, t2={t2_z:.4f}")
logger.info(f"Without z-normal {normal_without_z}: t1={t1_no_z:.4f}, t2={t2_no_z:.4f}")

# With true 3D, they should differ due to z-offset
tol = 1e-6
differ = not np.allclose([t1_z, t2_z], [t1_no_z, t2_no_z], atol=tol)
logger.info(f"Intersections differ (z-component affects in 3D)? {differ}")

if differ:
    logger.info("True 3D intersection demonstrated: z-component shifts intersections.")
else:
    logger.warning("No difference detected; check setup.")

# Plot for visualization (add webs and remesh)
af.add_shear_web(sw1)
af.add_shear_web(sw2)
af.remesh(total_n_points=100)
af.plot(show_hard_points=True, save_path="debug_3d_web_intersection_3d.png")

logger.info("Debug plot saved to debug_3d_web_intersection_3d.png")
