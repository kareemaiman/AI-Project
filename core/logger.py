"""
Smart Rail Structured Logging & Diagnostic Error Handler.

Provides multi-handler rotating logging to smart_rail.log and console,
with traceback capture, exception isolation, and graceful recovery utilities.
"""

import logging
from logging.handlers import RotatingFileHandler
import os
import sys
from typing import Optional


_LOGGER: Optional[logging.Logger] = None


def setup_logger(
    log_file: str = "smart_rail.log",
    level: str = "INFO",
    max_bytes: int = 2 * 1024 * 1024,
    backup_count: int = 3
) -> logging.Logger:
    """
    Configures and initializes the centralized rotating file and console logger.

    Args:
        log_file: Target log file path.
        level: Minimum logging level ('DEBUG', 'INFO', 'WARNING', 'ERROR').
        max_bytes: Maximum size of log file before rotation.
        backup_count: Number of archived log files to retain.

    Returns:
        logging.Logger: Configured logger instance.
    """
    global _LOGGER
    if _LOGGER is not None:
        return _LOGGER

    logger = logging.getLogger("SmartRail")
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(numeric_level)
    logger.propagate = False

    # Clear existing handlers if re-initializing
    if logger.hasHandlers():
        logger.handlers.clear()

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 1. Console Stream Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 2. Rotating File Handler
    try:
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8"
        )
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        logger.warning(f"Could not create file log handler ({log_file}): {e}. Falling back to console only.")

    _LOGGER = logger
    _LOGGER.info("Smart Rail logging subsystem initialized successfully.")
    return _LOGGER


def get_logger() -> logging.Logger:
    """Returns the singleton logger instance, creating it with defaults if uninitialized."""
    global _LOGGER
    if _LOGGER is None:
        _LOGGER = setup_logger()
    return _LOGGER
