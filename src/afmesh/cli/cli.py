import logging
import numpy as np
from ..core.airfoil import Airfoil
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
        logging.getLogger().setLevel(logging.DEBUG)
        logger.info("Verbose logging enabled")
    else:
        logging.getLogger().setLevel(logging.WARNING)
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
        logging.getLogger().setLevel(logging.DEBUG)
        logger.info("Verbose logging enabled")
    else:
        logging.getLogger().setLevel(logging.WARNING)
    logger.info(f"Remeshing airfoil from {file}")
    af = Airfoil.from_xfoil(file)
    af.remesh(n_points=n_points)
    np.savetxt(output, af.current_points[:, :2], header="x y", comments="")
    print(f"Remeshed points saved to {output}")
    logger.debug("Remesh command completed")


app = cli(
    name="afmesh",
    help="Command-line interface for afmesh airfoil processing.",
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
        argument(name="file", arg_type=str, help="Path to XFOIL format file.", sort_key=0),
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
        argument(name="file", arg_type=str, help="Path to XFOIL format file.", sort_key=0),
        argument(name="output", arg_type=str, help="Output file for remeshed points.", sort_key=1),
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


def main():
    """Entry point for the CLI."""
    app.run()


if __name__ == "__main__":
    main()