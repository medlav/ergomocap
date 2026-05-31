# ---
# project: ErgoMoCap
# file: constants.py
# author: medlav
# created: 2026-05-31
# license: AGPL-3.0
# ---
# Copyright (C) 2026 medlav
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the representation of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
ErgoMoCap: GUI Logging Service
----------------------------
Centralized logging configuration for the ErgoMoCap application.

This module implements a robust logging infrastructure using a rotating file
handler. It ensures that application events are captured at the `DEBUG` level
in a persistent local file, while providing cleaner, filtered `INFO` level
feedback to the console. This setup facilitates both production monitoring
and granular development debugging.
"""

import logging

import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from gui.utils.app_paths import get_external_root

#######################
# ---    LOGGER   --- #
#######################


def setup_logger(name: str = "ergomocap_gui") -> logging.Logger:
    """
    Configures a global logger with console and file handlers.

    Args:
        name (str): The name identifier for the logger (default: "ergomocap_gui").

    Returns:
        `logging.Logger` (logging.Logger): A configured logger instance with rotating file and console handlers.
    """
    # 1. Create logs directory if it doesn't exist
    root = get_external_root()

    log_dir = root / Path("logs")
    log_dir.mkdir(exist_ok=True)

    log_file = log_dir / "ergomocap_gui.log"

    logger = logging.getLogger(name)

    # Prevent duplicate handlers if setup_logger is called multiple times
    if logger.hasHandlers():
        return logger

    logger.setLevel(logging.DEBUG)

    # 2. Formatters
    # Console is cleaner; File includes timestamps and line numbers
    console_format = logging.Formatter("%(levelname)s: %(message)s")
    file_format = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
    )

    # 3. Console Handler (Standard Output)
    c_handler = logging.StreamHandler(sys.stdout)
    c_handler.setLevel(logging.INFO)  # Usually only want INFO+ in console
    c_handler.setFormatter(console_format)

    # 4. File Handler (Rotating: 5MB per file, keeps 5 backups)
    f_handler = RotatingFileHandler(
        log_file, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    f_handler.setLevel(logging.DEBUG)  # Always log everything to the file
    f_handler.setFormatter(file_format)

    # Add handlers to the logger
    logger.addHandler(c_handler)
    logger.addHandler(f_handler)

    return logger


# Initialize once
logger = setup_logger()
