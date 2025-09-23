import numpy as np
from ..utils.logger import get_logger


class AirfoilMesh:
    """Meshing functionality for Airfoil, including hard points, panels, and remeshing."""

    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)

    def add_hard_point(self, t, name=None):
        """Add a hard point at parametric t."""
        self.logger.debug(f"Adding hard point at t={t}")
        if 0 <= t <= 1 and t not in self.hard_points:
            self.hard_points.append(t)
            self.hard_points.sort()
            if name is None:
                name = f'hp{len(self.hard_point_names)}'
            self.hard_point_names[t] = name
            self.remesh()  # Update mesh to include new hard points
            self.logger.debug(f"Hard point added: {name} at t={t}")
        else:
            self.logger.warning(f"Hard point at t={t} not added: invalid or duplicate")

    def add_shear_web(self, shear_web, refinement_factor=1.0, n_elements=None):
        """Add a shear web, which adds hard points at intersections."""
        self.logger.debug(f"Adding shear web: {shear_web.definition}")
        shear_web.name = shear_web.definition.get('name', f'web{len(self.shear_webs)}')
        self.shear_webs.append(shear_web)
        self.shear_web_refinements[shear_web] = refinement_factor
        self.shear_web_n_elements[shear_web] = (
            n_elements if n_elements is not None else 1
        )
        t1, t2 = shear_web.compute_intersections(self)
        self.add_hard_point(t1, name=f'{shear_web.name}_hp0')
        self.add_hard_point(t2, name=f'{shear_web.name}_hp1')
        self.remesh()  # Update mesh to include new hard points
        self.logger.debug(f"Shear web added with intersections at t={t1}, t={t2}")

    def get_panels(self):
        """Get list of panels as (t_start, t_end) tuples."""
        self.logger.debug("Getting panels")
        panels = []
        sorted_hp = sorted(self.hard_points)
        for i in range(len(sorted_hp) - 1):
            panels.append((sorted_hp[i], sorted_hp[i + 1]))
        self.logger.debug(f"Panels: {panels}")
        return panels

    def remesh(
        self,
        t_distribution=None,
        total_n_points=None,
        element_length=None,
        relative_refinement=None,
        n_elements_per_panel=None,
    ):
        """Remesh the airfoil."""
        self.logger.debug("Remeshing airfoil")
        if n_elements_per_panel is not None:
            self.logger.debug("Remeshing with n_elements_per_panel")
            panels = self.get_panels()
            t_vals = []
            for p_idx, (t_start, t_end) in enumerate(panels):
                if isinstance(n_elements_per_panel, dict):
                    n_elem = n_elements_per_panel.get(p_idx, 1)
                else:
                    n_elem = n_elements_per_panel[p_idx]
                t_panel = np.linspace(t_start, t_end, n_elem + 1)
                t_vals.extend(t_panel)
            t_vals = np.sort(np.unique(t_vals))
            self.current_t = t_vals
            self.current_points = self.get_points(t_vals)
            self.logger.debug(f"Remeshed to {len(t_vals)} points")
            return
        elif relative_refinement is None and self.shear_web_refinements:
            relative_refinement = {}
            panels = self.get_panels()
            for sw, factor in self.shear_web_refinements.items():
                t1, t2 = sw.compute_intersections(self)
                for p_idx, (ts, te) in enumerate(panels):
                    if ts <= t1 < te or ts < t2 <= te or (t1 <= ts and te <= t2):
                        relative_refinement[p_idx] = max(
                            relative_refinement.get(p_idx, 1.0), factor
                        )
        if t_distribution is not None:
            self.logger.debug("Using provided t_distribution")
            t_vals = np.array(t_distribution)
        elif total_n_points is not None:
            self.logger.debug(f"Remeshing to total {total_n_points} points")
            panels = self.get_panels()
            total_segments = total_n_points - 1
            t_vals = []
            for t_start, t_end in panels:
                length = t_end - t_start
                segments = round(length * total_segments)
                n_points_panel = segments + 1
                t_panel = np.linspace(t_start, t_end, n_points_panel)
                t_vals.extend(t_panel)
            t_vals = np.array(t_vals)
        elif element_length is not None:
            self.logger.debug(f"Remeshing with element length {element_length}")
            # Approximate based on arc length
            total_length = self._arc_length(0, 1)
            n = int(total_length / element_length)
            t_vals = np.linspace(0, 1, n)
        elif relative_refinement is not None:
            self.logger.debug("Remeshing with relative refinement")
            # Refine relative to current
            panels = self.get_panels()
            t_vals = []
            for i, (t_start, t_end) in enumerate(panels):
                factor = relative_refinement.get(i, 1.0)
                n_panel = max(10, int(len(self.current_t) * factor / len(panels)))
                t_panel = np.linspace(t_start, t_end, n_panel)
                t_vals.extend(t_panel)
            t_vals = np.array(t_vals)
        else:
            self.logger.debug("Using default t_distribution")
            t_vals = self.current_t  # Default

        # Ensure hard points are included
        all_t = np.sort(np.unique(np.concatenate([t_vals, self.hard_points])))
        self.current_t = all_t
        self.current_points = self.get_points(all_t)
        self.logger.info(f"Remeshing complete: {len(all_t)} points")

    def _arc_length(self, t1, t2, n_samples=1000):
        """Approximate arc length between t1 and t2."""
        self.logger.debug(f"Calculating arc length from {t1} to {t2}")
        t_samples = np.linspace(t1, t2, n_samples)
        points = self.get_points(t_samples)
        diffs = np.diff(points, axis=0)
        length = np.sum(np.sqrt(np.sum(diffs**2, axis=1)))
        self.logger.debug(f"Arc length: {length}")
        return length