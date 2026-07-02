"""
Centralized logging configuration.

Logs go both to the console (INFO+) and to a rotating log file (DEBUG+)
so that every API request, response, and error is captured for the
deliverable log files required by the task.
"""

import logging
import os
from logging.handlers import RotatingFileHandler

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
LOG_FILE = os.path.join(LOG_DIR, "trading_bot.log")


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """
    Configure and return the application logger.

    Creates a `logs/` directory next to the project root (if missing),
    attaches a rotating file handler (5 MB x 3 backups) and a console
    handler, and returns a named logger for the bot.

    Args:
        log_level: Root console log level, e.g. "DEBUG", "INFO", "WARNING".

    Returns:
        Configured `logging.Logger` instance named "trading_bot".
    """
    os.makedirs(LOG_DIR, exist_ok=True)

    logger = logging.getLogger("trading_bot")
    logger.setLevel(logging.DEBUG)  # capture everything; handlers filter output

    # Avoid duplicate handlers if setup_logging() is called more than once
    if logger.handlers:
        return logger

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # File handler: always DEBUG level so requests/responses are fully logged
    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(fmt)

    # Console handler: configurable level, keeps terminal output readable
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    console_handler.setFormatter(fmt)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
