# ---
# project: ErgoMoCap
# file: conftest.py
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

import os


from unittest.mock import MagicMock, patch
import numpy as np
import pandas as pd
import pytest
from PySide6.QtWidgets import QWidget

# Local Frontend Imports
from gui.frontend import MainWindow

os.environ["QT_API"] = "pyside6"
# os.environ["QT_QPA_PLATFORM"] = "offscreen"


@pytest.fixture
def neutral_body_frame():
    """Provides a standardized 'neutral' frame for all calculators."""
    return {
        "trunk_angle": 0.0,
        "neck_angle": 0.0,
        "upper_arm_angle": 0.0,
        "lower_arm_angle": 90.0,
        "wrist_angle": 0.0,
        "legs_supported": True,
        "force_load": 0.0,
    }


@pytest.fixture
def dummy_mocap_df():
    """Provides a small 10-frame DataFrame for integration testing."""
    data = {
        "trunk_angle": np.linspace(0, 45, 10),  # Gradual bending
        "neck_angle": [0] * 10,
        "upper_arm_angle": [10] * 10,
        "lower_arm_angle": [90] * 10,
        "wrist_angle": [0] * 10,
    }
    return pd.DataFrame(data)


@pytest.fixture
def main_window(qtbot):
    """Initialize the MainWindow with cleanly mocked components."""

    class MockSidebar(QWidget):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.btn_fmc = MagicMock()
            self.btn_select_root = MagicMock()
            self.combo_sessions = MagicMock()
            self.btn_analysis = MagicMock()
            self.btn_report = MagicMock()
            self.btn_load_video = MagicMock()
            self.btn_play_video = MagicMock()
            self.combo_videos = MagicMock()

        def update_sessions(self, sessions):
            pass

        def update_videos(self, videos):
            pass

        def set_status(self, msg):
            pass

        def get_current_session(self):
            return "mock_session"

        def get_current_video(self):
            return "mock_video.mp4"

        def get_selected_method(self):
            return "RULA"

        def isVisible(self):
            return True

    class MockCanvas(QWidget):
        def __init__(self, parent=None):
            super().__init__(parent)

        def update_frame(self, frame):
            pass

    with (
        patch("gui.frontend.ErgoBackend"),
        patch("gui.frontend.ReportView"),
        patch("gui.frontend.MenuActions"),
        patch("gui.frontend.MenuBar"),
        patch("gui.frontend.ErgoSidebar", side_effect=MockSidebar),
        patch("gui.frontend.VideoCanvas", side_effect=MockCanvas),
    ):
        with patch.object(MainWindow, "init_root"):
            window = MainWindow()
            qtbot.addWidget(window)
            return window
