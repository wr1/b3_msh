"""Plotting functionality for Airfoil."""

import matplotlib.pyplot as plt

from ..utils.logger import get_logger
import numpy as np


class AirfoilPlot:
    """Plotting functionality for Airfoil."""

    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)

    def plot(self, show_hard_points=False, save_path=None, show=True):
        """Plot the airfoil using Matplotlib."""
        self.logger.debug("Plotting airfoil")
        plt.figure()  # Create a new figure to avoid overlapping
        points = self.current_points
        plt.plot(points[:, 0], points[:, 1], "b-", alpha=0.5)
        # Plot shear webs
        for sw in self.shear_webs:
            t1, t2 = sw.compute_intersections(self)
            p1 = self.get_points([t1])[0]
            p2 = self.get_points([t2])[0]
            n_elements = self.shear_web_n_elements[sw]
            n_points_web = n_elements + 1
            web_points = np.linspace(p1, p2, n_points_web)
            plt.plot(web_points[:, 0], web_points[:, 1], "g-", alpha=0.5, linewidth=2)
            plt.plot(web_points[:, 0], web_points[:, 1], "g.", markersize=4)
        # Plot non-hard points with .
        non_hard_mask = ~np.isin(self.current_t, self.hard_points)
        plt.plot(points[non_hard_mask, 0], points[non_hard_mask, 1], "k.", markersize=2)
        plt.axis("equal")
        plt.xlabel("x")
        plt.ylabel("y")
        plt.title("Airfoil Mesh")
        plt.grid(True)
        if show_hard_points:
            hard_points_pos = self.get_points(self.hard_points)
            plt.plot(hard_points_pos[:, 0], hard_points_pos[:, 1], "ro", markersize=8)
            for i, (x, y, _) in enumerate(hard_points_pos):
                plt.text(
                    x,
                    y + 0.01,
                    f"t={self.hard_points[i]:.2f}",
                    fontsize=8,
                    ha="center",
                    va="bottom",
                )
        if save_path:
            plt.savefig(save_path)
            self.logger.info(f"Plot saved to {save_path}")
        if show and save_path is None:
            plt.show()
        self.logger.debug("Plotting complete")
