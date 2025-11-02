"""Get a configured logger for the given name."""

import logging
from rich.logging import RichHandler


def get_logger(name):
    """Get a configured logger for the given name."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = RichHandler(rich_tracebacks=True, markup=True, show_time=False)
        logger.setLevel(logging.INFO)  # Default level changed to INFO for output
        logger.addHandler(handler)
    return logger
