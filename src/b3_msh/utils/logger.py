import logging
import sys


def get_logger(name):
    """Get a configured logger for the given name."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.setLevel(logging.INFO)  # Default level changed to INFO for output
        logger.addHandler(handler)
    return logger
