import logging
import numpy as np
from ..core.airfoil import Airfoil
from ..core.shear_web import ShearWeb
from ..utils.logger import get_logger
from treeparse import cli, command, argument, option


def plot(
    file: str,
    chord: float = 1.0,
    px=0,
    py=0,
    pz=0,
    rotation: float = 0,
    verbose: bool = False,
):
    """Plot an airfoil from file."""
    logger = get_logger("CLI")
    if verbose:
        logger.setLevel(logging.DEBUG)
        logger.info("Verbose logging enabled")
    else:
        logger.setLevel(logging.WARNING)
    logger.info(f"Plotting airfoil from {file}")
    af = Airfoil.from_xfoil(
        file,
        chord=chord,
        position=(px, py, pz),
        rotation=rotation,
    )
    af.plot()
    logger.debug("Plot command completed")


def remesh(
    file: str,
    output: str,
    n_points: int = 100,
    verbose: bool = False,
):
    """Remesh an airfoil and save."""
    logger = get_logger("CLI")
    if verbose:
        logger.setLevel(logging.DEBUG)
        logger.info("Verbose logging enabled")
    else:
        logger.setLevel(logging.WARNING)
    logger.info(f"Remeshing airfoil from {file}")
    af = Airfoil.from_xfoil(file)
    af.remesh(n_points=n_points)
    np.savetxt(output, af.current_points[:, :2], header="x y", comments="")
    logger.info(f"Remeshed points saved to {output}")
    logger.debug("Remesh command completed")


def process_section_from_mesh(mesh, z, chordwise_mesh, webs_config, logger):
    """Process a single section mesh by remeshing with uniform t distribution."""
    logger.debug(f"Processing section at z={z}")

    # Extract points at this z
    mask = np.isclose(mesh.points[:, 2], z)
    section_points = mesh.points[mask]
    # Sort by associated t pointdata
    t_values = mesh.point_data["t"][mask]
    sorted_indices = np.argsort(t_values)
    sorted_points = section_points[sorted_indices]
    points_2d = sorted_points[:, :2]  # Take x,y

    # Create Airfoil from points
    af = Airfoil(points_2d, is_normalized=False, position=(0, 0, z))  # Position at z

    # Add shear webs if applicable
    for web in webs_config:
        if web.get("mesh", False):
            z_range = web["z_range"]
            if z_range[0] <= z <= z_range[1]:
                sw_def = {
                    "type": web["type"],
                    "origin": [web["origin"][0], web["origin"][1], z],
                    "normal": web["orientation"],
                    "name": web["name"],
                }
                sw = ShearWeb(sw_def)
                af.add_shear_web(sw, n_elements=10)  # Default n_elements
                logger.debug(f"Added shear web {web['name']} at z={z}")

    # Add trailing edge shear web
    sw_te = ShearWeb({"type": "trailing_edge", "name": "trailing_edge"})
    af.add_shear_web(sw_te, n_elements=5)
    logger.debug(f"Added trailing edge shear web at z={z}")

    # Remesh with uniform t distribution
    n_elem = chordwise_mesh["default"]["n_elem"]
    logger.debug(f"Remeshing with {n_elem} elements")
    af.remesh(total_n_points=n_elem + 1)

    return af


def blade(config: str, verbose: bool = False):
    """Process blade from YAML config."""
    import os
    import yaml
    import pyvista as pv
    logger = get_logger("CLI")
    if verbose:
        logger.setLevel(logging.DEBUG)
        logger.info("Verbose logging enabled")
    else:
        logger.setLevel(logging.INFO)
    logger.info(f"Processing blade from {config}")
    
    # Load config
    with open(config, "r") as f:
        config_data = yaml.safe_load(f)
    
    config_dir = os.path.dirname(os.path.abspath(config))
    workdir = os.path.join(config_dir, config_data["workdir"])
    mesh_config = config_data["mesh"]
    chordwise_mesh = mesh_config["chordwise"]
    webs_config = config_data["structure"]["webs"]
    
    # Load the pre-processed mesh
    input_path = os.path.join(workdir, "b3_geo", "lm1_mesh.vtp")
    logger.info(f"Loading pre-processed mesh from {input_path}")
    mesh = pv.read(input_path)
    
    # Get z sections from mesh
    z_sections = np.unique(mesh.points[:, 2])
    z_sections = np.sort(z_sections)
    logger.info(f"Found {len(z_sections)} z sections: {z_sections}")
    
    logger.info("Processing sections")
    # Process each section
    sections = []
    for z in z_sections:
        af = process_section_from_mesh(mesh, z, chordwise_mesh, webs_config, logger)
        sections.append(af)
    
    logger.info("Creating new MultiBlock mesh")
    # Create new MultiBlock
    new_multi_block = pv.MultiBlock()
    for i, af in enumerate(sections):
        mesh_out = af.to_pyvista()
        new_multi_block.append(mesh_out, f"Section_{i}")
    
    # Save to VTM (MultiBlock format)
    output_path = os.path.join(workdir, "b3_msh", "lm2.vtm")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    logger.info(f"Saving mesh to {output_path}")
    new_multi_block.save(output_path)
    logger.info(f"Saved remeshed blade mesh to {output_path}")


app = cli(
    name="b3_msh",
    help="Command-line interface for b3_msh airfoil processing.",
    max_width=120,
    show_types=True,
    show_defaults=True,
    line_connect=True,
    theme="monochrome",
)

plot_cmd = command(
    name="plot",
    help="Plot an airfoil from file.",
    callback=plot,
    arguments=[
        argument(
            name="file", arg_type=str, help="Path to XFOIL format file.", sort_key=0
        ),
    ],
    options=[
        option(
            flags=["--chord", "-c"],
            arg_type=float,
            default=1.0,
            help="Chord length.",
            sort_key=0,
        ),
        option(
            flags=["--px"],
            arg_type=float,
            default=0,
            help="Position x.",
            sort_key=1,
        ),
        option(
            flags=["--py"],
            arg_type=float,
            default=0,
            help="Position y.",
            sort_key=2,
        ),
        option(
            flags=["--pz"],
            arg_type=float,
            default=0,
            help="Position z.",
            sort_key=3,
        ),
        option(
            flags=["--rotation", "-r"],
            arg_type=float,
            default=0,
            help="Rotation in degrees.",
            sort_key=4,
        ),
        option(
            flags=["--verbose", "-v"],
            arg_type=bool,
            default=False,
            help="Enable verbose logging.",
            sort_key=5,
        ),
    ],
)
app.commands.append(plot_cmd)

remesh_cmd = command(
    name="remesh",
    help="Remesh an airfoil and save.",
    callback=remesh,
    arguments=[
        argument(
            name="file", arg_type=str, help="Path to XFOIL format file.", sort_key=0
        ),
        argument(
            name="output",
            arg_type=str,
            help="Output file for remeshed points.",
            sort_key=1,
        ),
    ],
    options=[
        option(
            flags=["--n_points", "-n"],
            arg_type=int,
            default=100,
            help="Number of points per panel.",
            sort_key=0,
        ),
        option(
            flags=["--verbose", "-v"],
            arg_type=bool,
            default=False,
            help="Enable verbose logging.",
            sort_key=1,
        ),
    ],
)
app.commands.append(remesh_cmd)

blade_cmd = command(
    name="blade",
    help="Process blade from YAML config.",
    callback=blade,
    arguments=[
        argument(
            name="config", arg_type=str, help="Path to YAML config file.", sort_key=0
        ),
    ],
    options=[
        option(
            flags=["--verbose", "-v"],
            arg_type=bool,
            default=False,
            help="Enable verbose logging.",
            sort_key=0,
        ),
    ],
)
app.commands.append(blade_cmd)


def main():
    """Entry point for the CLI."""
    app.run()


if __name__ == "__main__":
    main()
