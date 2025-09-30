"""Command-line interface for b3_msh."""
from treeparse import cli, command, argument, option
from .commands import plot, remesh, blade

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
