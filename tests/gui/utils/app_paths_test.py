# ---
# project: ErgoMoCap
# file: app_paths_test.py
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

import sys
from pathlib import Path
from gui.utils.app_paths import get_internal_root, get_external_root, ErgoPaths


class TestAppPathResolution:
    """
    Test suite to ensure path resolution works correctly across
    frozen (PyInstaller) and development environments.
    """

    def test_get_internal_root_frozen(self, monkeypatch):
        """Test internal root resolution when running as a bundled executable."""
        mock_path = "/mock/meipass/dir"
        # Simulate PyInstaller environment (_MEIPASS is a string in reality)
        monkeypatch.setattr(sys, "_MEIPASS", mock_path, raising=False)

        root = get_internal_root()
        assert isinstance(root, Path)
        # Standardizing separators for comparison
        assert str(root).replace("\\", "/") == mock_path

    def test_get_internal_root_script(self, monkeypatch):
        """Test internal root resolution when running as a standard script."""
        # Ensure _MEIPASS is NOT present to trigger the 'else' branch
        if hasattr(sys, "_MEIPASS"):
            monkeypatch.delattr(sys, "_MEIPASS")

        root = get_internal_root()
        # Should resolve to the project root
        assert root.exists()
        assert (root / "gui").exists()

    def test_get_external_root_frozen(self, monkeypatch):
        """
        Test external root resolution when frozen.
        The path logic is: sys.executable -> bin -> project -> root
        So .parent.parent.parent should land on the root.
        """
        # Mock sys.frozen and sys.executable
        # Path: C:/test_root/project_dir/bin/app.exe
        mock_exec = Path("C:/test_root/project_dir/bin/app.exe")
        monkeypatch.setattr(sys, "frozen", True, raising=False)
        monkeypatch.setattr(sys, "executable", str(mock_exec))

        root = get_external_root()

        # 1. /bin (parent 1)
        # 2. /project_dir (parent 2)
        # 3. /test_root (parent 3) -> This is what get_external_root returns
        assert root.parts[-1] == "test_root"

    def test_get_external_root_script(self, monkeypatch):
        """Test external root resolution when running as a script."""
        monkeypatch.setattr(sys, "frozen", False, raising=False)

        root = get_external_root()
        assert root.exists()


class TestErgoPaths:
    """Tests the centralized registry and path construction logic."""

    def test_static_paths_initialization(self):
        """Verify the main root paths are initialized as Path objects."""
        assert isinstance(ErgoPaths.USER_DATA, Path)
        assert isinstance(ErgoPaths.APP_CODE, Path)
        assert ErgoPaths.DATA_FOLDER_NAME == "output_data"

    def test_session_folder_construction(self):
        """Verify session folder naming logic."""
        session_name = "test_session_001"
        expected = ErgoPaths.SESSIONS / session_name
        assert ErgoPaths.session_folder(session_name) == expected

    def test_data_and_video_folders(self):
        """Verify subfolder pathing for data and videos."""
        session = "session_A"
        data_path = ErgoPaths.data_folder(session)
        video_path = ErgoPaths.video_folder(session)

        assert data_path.name == ErgoPaths.DATA_FOLDER_NAME
        assert video_path.name == ErgoPaths.VIDEO_FOLDER_NAME
        assert data_path.parent.name == session

    def test_output_folder_creation(self, tmp_path, monkeypatch):
        """Verify output_folder creates the directory if it doesn't exist."""
        mock_output = tmp_path / "fake_output"
        # We patch the attribute on the class
        monkeypatch.setattr(ErgoPaths, "OUTPUT_FOLDER", mock_output)

        assert not mock_output.exists()
        resolved_path = ErgoPaths.output_folder()
        assert resolved_path.exists()
        assert resolved_path == mock_output

    def test_analysis_output_path(self, tmp_path, monkeypatch):
        """Verify the final CSV output pathing."""
        mock_output = tmp_path / "fake_output"
        monkeypatch.setattr(ErgoPaths, "OUTPUT_FOLDER", mock_output)

        csv_path = ErgoPaths.analysis_output()
        assert csv_path.name == "ergo_analysis.csv"
        assert csv_path.parent == mock_output
