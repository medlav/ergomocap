# ---
# project: ErgoMoCap
# file: session_manager_test.py
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

from unittest.mock import patch

import pytest
import numpy as np
import pandas as pd
from pathlib import Path
from gui.core.session_manager import SessionManager


class TestSessionManager:
    """
    Test suite for SessionManager.
    Covers directory scanning, asset resolution, and multi-format data loading.
    """

    @pytest.fixture
    def mock_sessions_dir(self, tmp_path):
        """Creates a mock directory structure for session testing."""
        sessions = tmp_path / "sessions"
        sessions.mkdir()
        (sessions / "session_01").mkdir()
        (sessions / "session_02").mkdir()
        (sessions / ".hidden_dir").mkdir()
        (sessions / "not_a_dir.txt").write_text("hello")
        return sessions

    def test_init_behavior(self):
        """Tests initialization with custom path and fallback logic."""
        # Custom path
        custom_path = Path("/tmp/ergo")
        sm = SessionManager(custom_path)
        assert sm.sessions_dir == custom_path

        # Fallback to ErgoPaths (Mocked)
        with patch("gui.core.session_manager.ErgoPaths") as mock_paths:
            mock_paths.SESSIONS = Path("/default/sessions")
            sm_fallback = SessionManager(mock_paths.SESSIONS)
            assert sm_fallback.sessions_dir == Path("/default/sessions")

    def test_get_initial_sessions(self, mock_sessions_dir):
        """Verifies scanning and filtering of session directories."""
        sm = SessionManager(mock_sessions_dir)
        sessions = sm.get_initial_sessions()

        assert len(sessions) == 2
        assert "session_01" in sessions
        assert "session_02" in sessions
        assert ".hidden_dir" not in sessions
        assert "not_a_dir.txt" not in sessions

    def test_get_initial_sessions_invalid_path(self):
        """Tests behavior when the sessions directory does not exist."""
        sm = SessionManager("/non/existent/path")
        assert sm.get_initial_sessions() == []

    def test_scan_custom_path(self, tmp_path):
        """Verifies scanning of an arbitrary external path."""
        external = tmp_path / "external"
        external.mkdir()
        (external / "ext_session").mkdir()

        sm = SessionManager(tmp_path)
        results = sm.scan_custom_path(external)
        assert results == ["ext_session"]

        # Test invalid path
        assert sm.scan_custom_path(tmp_path / "void") == []

    @patch("gui.core.session_manager.ErgoPaths")
    def test_resolve_session_assets(self, mock_paths, tmp_path):
        """Covers the heuristic-based resolution of CSV and Video assets."""
        # Setup mock paths for specific session
        data_dir = tmp_path / "data"
        video_dir = tmp_path / "video"
        data_dir.mkdir()
        video_dir.mkdir()

        mock_paths.data_folder.return_value = data_dir
        mock_paths.video_folder.return_value = video_dir

        # Create files
        csv_file = data_dir / "recording_joint_angles.csv"
        csv_file.write_text("header,data")
        (data_dir / "random.csv").write_text("ignore me")

        vid_file = video_dir / "annotated_view.mp4"
        vid_file.write_text("video_binary")

        sm = SessionManager(tmp_path)
        target_csv, target_video, video_files = sm.resolve_session_assets(
            "test_session"
        )

        assert target_csv == csv_file
        assert target_video == "annotated_view.mp4"
        assert "annotated_view.mp4" in video_files

    @patch("gui.core.session_manager.ErgoPaths")
    def test_resolve_session_assets_missing(self, mock_paths, tmp_path):
        """Verifies asset resolution returns None when folders are missing."""
        mock_paths.data_folder.return_value = tmp_path / "void_data"
        mock_paths.video_folder.return_value = tmp_path / "void_video"

        sm = SessionManager(tmp_path)
        csv, vid, vids = sm.resolve_session_assets("ghost_session")
        assert csv is None
        assert vid is None
        assert vids == []

    def test_load_joint_angles_file_csv(self, tmp_path):
        """Verifies loading of CSV files into DataFrames."""
        csv_path = tmp_path / "data.csv"
        df_orig = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
        df_orig.to_csv(csv_path, index=False)

        sm = SessionManager(tmp_path)
        data, path = sm.load_joint_angles_file(csv_path)

        assert isinstance(data, pd.DataFrame)
        assert data.shape == (2, 2)
        assert path == csv_path

    def test_load_joint_angles_file_npy(self, tmp_path):
        """Verifies loading of NPY files into NumPy arrays."""
        npy_path = tmp_path / "data.npy"
        arr_orig = np.array([1, 2, 3])
        np.save(npy_path, arr_orig)

        sm = SessionManager(tmp_path)
        data, path = sm.load_joint_angles_file(npy_path)

        assert isinstance(data, np.ndarray)
        assert np.array_equal(data, arr_orig)

    def test_load_joint_angles_file_errors(self, tmp_path):
        """Covers error raising for missing files and unsupported formats."""
        sm = SessionManager(tmp_path)

        # FileNotFoundError
        with pytest.raises(FileNotFoundError):
            sm.load_joint_angles_file(tmp_path / "missing.csv")

        # ValueError (Unsupported Format)
        bad_file = tmp_path / "data.txt"
        bad_file.write_text("oops")
        with pytest.raises(ValueError, match="Unsupported file format"):
            sm.load_joint_angles_file(bad_file)
