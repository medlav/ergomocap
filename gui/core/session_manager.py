# ---
# project: ErgoMoCap
# file: session_manager.py
# author: medlav
# created: 2026-05-19
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
ErgoMoCap: Session Management
------------------------------
Filesystem Operations and Data Asset Resolution Module.

This module implements the [SessionManager][gui.core.session_manager.SessionManager] class,
which provides a high-level API for interacting with the ErgoMoCap and FreeMoCap
data structures. It handles the discovery of recording sessions, resolution of
associated video and CSV assets, and provides standardized loading mechanisms
for analysis data.

The manager integrates with [ErgoPaths][gui.utils.app_paths.ErgoPaths] to ensure
cross-platform path resolution and compatibility with frozen environments
(e.g., PyInstaller).

Key Features:
    * Automatic discovery of session directories within defined root paths.
    * Heuristic-based resolution of joint angle CSVs and annotated MP4 videos.
    * Unified data loading interface for `numpy.ndarray` and `pandas.DataFrame` formats.
    * Support for arbitrary external path scanning for portable session review.
"""

import numpy as np
import pandas as pd
from pathlib import Path
from typing import Any, Union

from gui.utils.app_paths import ErgoPaths


class SessionManager:
    """
    Handles filesystem operations related to ErgoMoCap recording sessions.

    This manager abstracts the directory structure of the data storage,
    providing methods to scan for sessions, resolve specific assets (CSV/Video),
    and load data files into memory.

    Attributes:
        sessions_dir (Path): The base directory where session folders are stored.

    Methods:
        get_initial_sessions: Scans the sessions_dir for valid session directories.
        scan_custom_path: Scans an arbitrary external path for session folders.
        resolve_session_assets: Locates primary data and video assets within a specific session.
        load_file_data: Loads session data from the disk based on file extension.
    """

    def __init__(self, sessions_dir: Union[str, Path]) -> None:
        """Initializes the SessionManager with a root data directory.

        Args:
            sessions_dir: Path to the directory containing ergonomic sessions.

        Returns:
            None (None): Initializer does not return a value.

        NOTE:
        Uses get_external_root() as a fallback to ensure PyInstaller
        compatibility (Centralized Path Management).
        """
        self.sessions_dir = Path(sessions_dir) if sessions_dir else ErgoPaths.SESSIONS

    def get_initial_sessions(self) -> list[str]:
        """Scans the sessions_dir for valid session directories.

        Filters out hidden directories and non-directory files to identify
        potential FreeMoCap session folders.

        Returns:
            list[str]: A list of session directory names found at the root.
        """
        if not self.sessions_dir.exists() or not self.sessions_dir.is_dir():
            return []

        return [
            d.name
            for d in self.sessions_dir.iterdir()
            if d.is_dir() and not d.name.startswith(".")
        ]

    def scan_custom_path(self, path: Union[str, Path]) -> list[str]:
        """
        Scans an arbitrary external path for session folders.

        Args:
            path (str | Path): The directory path to scan.

        Returns:
            list[str]: A list of subdirectories found at the given path.
        """
        root: Path = Path(path)
        if not root.exists() or not root.is_dir():
            return []
        return [
            d.name for d in root.iterdir() if d.is_dir() and not d.name.startswith(".")
        ]

    def resolve_session_assets(
        self, session_name: str
    ) -> tuple[Path | None, str | None, list[str]]:
        """
        Locates primary data and video assets within a specific session.

        This method follows the FreeMoCap output convention, searching for
        joint angle CSVs in the data folder and MP4s in the video folder as
        defined by [ErgoPaths][gui.utils.app_paths.ErgoPaths].

        Args:
            session_name (str): The name of the session folder to inspect.

        Returns:
            tuple[Path | None, str | None, list[str]]: A tuple containing (target_csv, target_video, video_files).
        """
        # Resolve CSV Data (Searching for joint angles output)
        csv_dir = ErgoPaths.data_folder(session_name)
        video_dir = ErgoPaths.video_folder(session_name)

        # 1. Look for the CSV
        target_csv = None
        if csv_dir.exists():
            csv_files = list(csv_dir.rglob("*.csv"))
            target_csv = next(
                (f for f in csv_files if "joint_angles" in f.name.lower()), None
            )

        # 2. Look for the Videos
        video_files = []
        if video_dir.exists():
            video_files = [f.name for f in video_dir.rglob("*.mp4")]

        target_video = video_files[0] if video_files else None

        # print(target_csv, target_video, video_files) TODO print_reactivate

        return target_csv, target_video, video_files

    def load_file_data(self, file_path: Union[str, Path]) -> tuple[Any, Path]:
        """
        Loads session data from the disk based on file extension.

        Supports NumPy (`.npy`) for raw landmark data and Pandas (`.csv`) for
        calculated angles or scores.

        Args:
            file_path (str | Path): The path to the file to load.

        Returns:
            tuple[Any, Path]: A tuple containing the loaded object (`numpy.ndarray` or `pandas.DataFrame`) and its confirmed `Path` object.

        Raises:
            ValueError (ValueError): If the file format is not supported (`.npy` or `.csv` only).
            FileNotFoundError (FileNotFoundError): If the provided path does not exist.
        """
        path: Path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"Session data file not found: {path}")

        if path.suffix == ".npy":
            return np.load(path), path
        elif path.suffix == ".csv":
            return pd.read_csv(path), path

        raise ValueError(
            f"Unsupported file format: {path.suffix}. Expected .npy or .csv"
        )
