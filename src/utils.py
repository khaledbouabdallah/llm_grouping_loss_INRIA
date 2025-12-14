"""
Logging configuration
"""

import logging
import sys
from pathlib import Path


def setup_logging(
    log_file: str = None,
    level: int = logging.INFO,
    format_string: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
):
    """
    Setup logging configuration

    Args:
        log_file: Optional file path to write logs
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        format_string: Log message format
    """
    handlers = [logging.StreamHandler(sys.stdout)]

    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_file))

    logging.basicConfig(level=level, format=format_string, handlers=handlers)

    # Set specific loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)

    logger = logging.getLogger(__name__)
    logger.info("Logging initialized")
