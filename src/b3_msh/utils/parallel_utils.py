"""Process a list of Airfoil instances in parallel."""

from multiprocessing import Pool


def process_airfoils_parallel(airfoils, func, n_processes=None):
    """Process a list of Airfoil instances in parallel."""
    with Pool(processes=n_processes) as pool:
        results = pool.map(func, airfoils)
    return results
