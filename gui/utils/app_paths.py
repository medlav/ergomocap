# ---
# project: ErgoMoCap
# file: app_paths.py
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
ErgoMoCap: Application Path Management
--------------------------------------
Centralized Path Resolution for Internal Assets and External Data.

This module provides the `ErgoPaths` class and supporting utility functions to
standardize how the application accesses the file system. It specifically
addresses the challenges of path resolution in "frozen" environments (e.g.,
executables bundled with PyInstaller) versus standard development environments.

By centralizing all "magic strings" related to directory names and file locations,
this module ensures that changes to the project structure only need to be
reflected in a single location.
"""

from PySide6.QtCore import QUrl
from pathlib import Path
import sys


def get_internal_root() -> Path:
    """
    Resolves the root directory for internal assets.

    Handles the path shift that occurs when the application is bundled using
    PyInstaller (`_MEIPASS`) versus running as a raw script. This is used for
    read-only assets like icons, templates, and core application code.
    `Path`

    Returns:
        Path (Path): The absolute path to the bundled internal assets or
            the project source root.
    """
    if hasattr(sys, "_MEIPASS"):
        # Running as internal bundle
        internal_root = Path(sys._MEIPASS)  # type: ignore
    else:
        # Running as normal script
        internal_root = Path(__file__).resolve().parent.parent.parent

    return internal_root


def get_external_root() -> Path:
    """
    Resolves the root directory for external user data.

    Ensures that output files (videos, CSVs) are saved relative to the user's
    executable environment in a 'frozen' state, preventing data from being
    written to temporary system folders.

    Returns:
        Path (Path): The absolute path to the persistent external
            application environment.
    """
    if getattr(sys, "frozen", False):
        external_root = Path(sys.executable).resolve().parent.parent.parent
    else:
        external_root = Path(__file__).resolve().parent.parent.parent

    return external_root


class ErgoPaths:
    """
    Centralized registry for all folder names and file locations in ErgoMoCap.

    This class serves as the single source of truth for the project's file system
    hierarchy. It differentiates between internal read-only application layers (`APP_CODE`)
    and external writeable structures (`USER_DATA`).

    Attributes:
        USER_DATA (Path): Root path for persistent user data and tracking sessions.
        SESSIONS (Path): Directory containing recording session data folders.
        APP_CODE (Path): Root path for the core application source and asset resources.
        ASSETS (Path): Directory containing UI images, icons, and static graphics.
        TEMPLATES (Path): Directory containing Jinja2/HTML visual report templates.
        OUTPUT_FOLDER (Path): Standardized directory for generated ergonomic analysis results.
        DATA_FOLDER_NAME (str): Static directory string identifying subfolders holding raw metric data.
        VIDEO_FOLDER_NAME (str): Static directory string identifying subfolders holding annotated video streams.
        LOCAL_SITE (str): Static directory string pointing to local web assets or report packages.
        LOGO (Path): Absolute filesystem locator path to the primary application logo graphic.

    Methods:
        update_user_root: Updates the USER_DATA path and all constant paths at a class level.
        session_folder: Constructs the absolute path to a specific recording session directory.
        data_folder: Constructs the absolute path to the data subfolder of a session.
        video_folder: Constructs the absolute path to the video subfolder of a session.
        frames_folder: Constructs the absolute path to the video frames subfolder of a video, creating it if needed.
        output_folder: Resolves the global output directory, ensuring its safe creation on disk.
        analysis_output: Returns the standardized target path for the primary analysis CSV export sheet.
        get_local_site_url: Converts an absolute systemic path string into a valid QUrl resource location.
    """

    # --- The Big Roots ---
    # Where user data lives (External)
    SESSIONS_FOLDER_NAME = "recording_sessions"
    USER_DATA = get_external_root() / "freemocap_data"
    SESSIONS = USER_DATA / SESSIONS_FOLDER_NAME

    # Where the app code/assets live (Internal)
    APP_CODE = get_internal_root()
    ASSETS = APP_CODE / "assets"
    TEMPLATES = APP_CODE / "gui" / "templates"

    OUTPUT_FOLDER = APP_CODE / "ergomocap_data"

    # --- Specific Folder Names ---
    # These are the "Magic Strings" we are killing
    DATA_FOLDER_NAME = "output_data"
    VIDEO_FOLDER_NAME = "annotated_videos"
    LOCAL_SITE = "site"

    # --- Common Files ---
    LOGO = ASSETS / "ergomocap_logo_dark.png"

    @classmethod
    def update_user_root(cls, new_root: Path) -> None:
        """
        Dynamically updates the base path location when a user selects
        a custom root folder from the interface.


        Args:
            new_root (Path): The unique identifier/folder name of the session.

        Returns:
            None (None): Simply Updated the class.
        """
        if new_root.name == cls.SESSIONS_FOLDER_NAME:
            # If they picked 'recording_sessions', go one step up to find freemocap_data
            cls.USER_DATA = new_root.parent
            cls.SESSIONS = new_root
        elif (
            new_root / cls.SESSIONS_FOLDER_NAME
        ).exists() or new_root.name == "freemocap_data":
            # If they picked 'freemocap_data' or a directory containing 'recording_sessions'
            cls.USER_DATA = new_root
            cls.SESSIONS = new_root / cls.SESSIONS_FOLDER_NAME
        else:
            # Fallback treat whatever they picked as the directory containing session folders
            cls.USER_DATA = new_root.parent
            cls.SESSIONS = new_root

    @staticmethod
    def session_folder(session_name: str) -> Path:
        """
        Constructs the absolute path to a specific recording session.

        Args:
            session_name (str): The unique identifier/folder name of the session.

        Returns:
            Path (Path): Absolute path to the session directory.
        """
        return ErgoPaths.SESSIONS / session_name

    @staticmethod
    def data_folder(session_name: str) -> Path:
        """
        Constructs the absolute path to the data subfolder of a session.

        Args:
            session_name (str): The name of the target session.

        Returns:
            Path (Path): Path to the session's 'output_data' directory.
        """
        return ErgoPaths.session_folder(session_name) / ErgoPaths.DATA_FOLDER_NAME

    @staticmethod
    def video_folder(session_name: str) -> Path:
        """
        Constructs the absolute path to the video subfolder of a session.

        Args:
            session_name (str): The name of the target session.

        Returns:
            Path (Path): Path to the session's 'annotated_videos' directory.
        """
        return ErgoPaths.session_folder(session_name) / ErgoPaths.VIDEO_FOLDER_NAME

    @staticmethod
    def frames_folder(session_name: str, video_name: str) -> Path:
        """
        Constructs the absolute path to the video frames subfolder of a video.

        Args:
            session_name (str): The name of the target session.

        Returns:
            Path (Path): Path to the video's 'frames' directory.
        """

        frames_dir = ErgoPaths.output_folder() / session_name / video_name / "frames"
        frames_dir.mkdir(parents=True, exist_ok=True)
        return frames_dir

    @staticmethod
    def output_folder() -> Path:
        """
        Resolves the global output folder, creating it if it does not exist.

        Returns:
            Path (Path): The verified directory for ergonomic data output.
        """
        ErgoPaths.OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)
        return ErgoPaths.OUTPUT_FOLDER

    @staticmethod
    def analysis_output() -> Path:
        """
        Returns the standardized path for the primary analysis CSV.

        Ensures that analysis results are consistently stored in the recognized
        output directory.

        Returns:
            Path (Path): Absolute path to 'ergo_analysis.csv'.
        """
        # TODO do something better like return ErgoPaths.output_folder() / f"{method.lower()}_analysis.csv"
        return ErgoPaths.output_folder() / "ergo_analysis.csv"

    @staticmethod
    def get_local_site_url(page_name: str) -> QUrl:
        """
        Helper method to construct a safe local file URL.

        Resolves internal application page assets into validated uniform resource locator
        structures compatible with PySide6 web engine components.

        Args:
            page_name (str): Relative filename string pointing to the targeted web asset or page.

        Returns:
            QUrl (QUrl): A validated local file system pointer scheme (`file:///...`) targeting the component.

        Raises:
            ValueError (ValueError): If the target file resource does not exist at the resolved location path.
        """

        local_path = ErgoPaths.APP_CODE / ErgoPaths.LOCAL_SITE / page_name

        if not local_path.exists():
            raise ValueError("Url not found")

        # Convert the absolute system path into a valid QUrl (file:///...)
        return QUrl.fromLocalFile(local_path)
