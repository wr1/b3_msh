import argparse
import numpy as np
from ..core.airfoil import Airfoil


def main():
    """Command-line interface for afmesh."""
    parser = argparse.ArgumentParser(description="afmesh CLI for airfoil processing.")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Plot command
    plot_parser = subparsers.add_parser("plot", help="Plot an airfoil from file.")
    plot_parser.add_argument(
        "-f", "--file", required=True, help="Path to XFOIL format file."
    )
    plot_parser.add_argument(
        "-c", "--chord", type=float, default=1.0, help="Chord length."
    )
    plot_parser.add_argument(
        "-p",
        "--position",
        nargs=3,
        type=float,
        default=[0, 0, 0],
        help="Position (x y z).",
    )
    plot_parser.add_argument(
        "-r", "--rotation", type=float, default=0, help="Rotation in degrees."
    )

    # Remesh command
    remesh_parser = subparsers.add_parser("remesh", help="Remesh an airfoil and save.")
    remesh_parser.add_argument(
        "-f", "--file", required=True, help="Path to XFOIL format file."
    )
    remesh_parser.add_argument(
        "-n", "--n_points", type=int, default=100, help="Number of points per panel."
    )
    remesh_parser.add_argument(
        "-o", "--output", required=True, help="Output file for remeshed points."
    )

    args = parser.parse_args()

    if args.command == "plot":
        af = Airfoil.from_xfoil(
            args.file,
            chord=args.chord,
            position=tuple(args.position),
            rotation=args.rotation,
        )
        af.plot()
    elif args.command == "remesh":
        af = Airfoil.from_xfoil(args.file)
        af.remesh(n_points=args.n_points)
        np.savetxt(args.output, af.current_points[:, :2], header="x y", comments="")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()