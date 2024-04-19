"""
Utility to create logger instances.
"""

import logging

LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


def get_logger(name: str, level=logging.DEBUG) -> logging.Logger:
    """
    Instantiate a logger with a given level and name.

    Example:
        ```python
        logger = blockutils.logging.get_logger(__name__)
        # __name__ is the name of the file where the logger is instantiated.
        ```

    Args:
        name: A name for the logger - is included in all the logging messages.
        level: A logging level (i.e. logging.DEBUG).

    Returns:
        A logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    # create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(level)
    formatter = logging.Formatter(LOG_FORMAT)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    return logger
