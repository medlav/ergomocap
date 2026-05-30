# ---
# project: ErgoMoCap
# file: sidebar_test.py
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

import pytest
from unittest.mock import MagicMock
from PySide6.QtWidgets import QScrollArea, QWidget
from gui.widgets.sidebar import ErgoSidebar
from gui.utils.constants import AssessmentMethod
from gui.utils.models import AnalysisRequest


@pytest.fixture
def sidebar(qtbot):
    """Fixture to initialize the ErgoSidebar and register it safely with qtbot."""
    widget = ErgoSidebar()
    qtbot.addWidget(widget)
    return widget


def test_sidebar_initial_state(sidebar):
    """Verify initial UI state, default labels, and asset constraints."""
    assert sidebar.objectName() == "Sidebar"
    assert sidebar.width() == 320
    assert "READY" in sidebar.status_label.text()
    assert sidebar.combo_method.count() > 0
    assert not sidebar.btn_play_video.isEnabled()
    assert not sidebar.btn_prev_frame.isEnabled()
    assert not sidebar.btn_next_frame.isEnabled()


def test_update_sessions_logic(sidebar):
    """Test session list updates, status text changes, and explicit signal blocking verification."""
    spy = MagicMock()
    sidebar.session_changed.connect(spy)

    sessions = ["Session_A", "Session_B"]
    sidebar.update_sessions(sessions)

    # Verify UI state update
    assert sidebar.combo_sessions.count() == 2
    assert "Found 2 sessions." in sidebar.status_label.text()

    # Statement Coverage: Verify signals were successfully blocked during list updates
    spy.assert_not_called()


def test_update_videos_logic(sidebar):
    """Test video list updates and frame step modifier visibility states."""
    # Test layout enablement path
    sidebar.update_videos(["vid1.mp4"])
    assert sidebar.btn_play_video.isEnabled()
    assert sidebar.btn_prev_frame.isEnabled()
    assert sidebar.btn_next_frame.isEnabled()

    # Test disabling flow (Branch coverage for empty arrays)
    sidebar.update_videos([])
    assert not sidebar.btn_play_video.isEnabled()


def test_getters_and_setters(sidebar):
    """Verify public unified structural API for modifying and retrieving visual interface states."""
    sidebar.update_sessions(["S1", "S2"])
    sidebar.combo_sessions.setCurrentIndex(1)

    sidebar.update_videos(["V1"])
    sidebar.combo_videos.setCurrentIndex(0)

    # Fix: Reflect the modified items array schema present in sidebar.py layout ("RULA (Unstable)")
    sidebar.combo_method.setCurrentText("RULA (Unstable)")

    assert sidebar.get_current_session() == "S2"
    assert sidebar.get_current_video() == "V1"
    assert sidebar.get_selected_method() == "RULA (Unstable)"

    sidebar.set_status("Running Framework pipeline...")
    assert "STATUS: Running Framework pipeline..." in sidebar.status_label.text()


def test_signal_emissions(sidebar, qtbot):
    """Verify that simulated user interactions trigger custom unified architecture signals."""

    # 1. Root Folder Selection Request
    with qtbot.waitSignal(sidebar.root_selection_requested, timeout=500):
        sidebar.btn_select_root.click()

    # 2. Dropdown Session Selection Changes
    sidebar.update_sessions(["A", "B"])
    with qtbot.waitSignal(sidebar.session_changed, timeout=500) as blocker:
        sidebar.combo_sessions.setCurrentIndex(1)
    assert blocker.args == ["B"]

    # 3. Dropdown Video Feed Selection Changes
    sidebar.update_videos(["V1", "V2"])
    with qtbot.waitSignal(sidebar.video_changed, timeout=500) as blocker:
        sidebar.combo_videos.setCurrentIndex(1)
    assert blocker.args == ["V2"]

    # 4. Run Analysis Flow Execution (With packed structured payload verification)
    sidebar.combo_method.setCurrentText("REBA")
    sidebar.export_frames_checkbox.setChecked(True)

    with qtbot.waitSignal(sidebar.run_analysis_clicked, timeout=500) as blocker:
        sidebar.btn_analysis.click()

    # Assert signature updates map accurately to the AnalysisRequest model
    payload = blocker.args[0]
    assert isinstance(payload, AnalysisRequest)
    assert payload.method == AssessmentMethod.REBA
    assert payload.export_frames is True


def test_signals_blocked_sanity_fix(sidebar):
    """Ensure signals activate normally when matching discrete manual interaction states."""
    spy = MagicMock()
    sidebar.session_changed.connect(spy)

    # Update list updates layout silently
    sidebar.update_sessions(["New_1", "New_2"])
    spy.assert_not_called()

    # Manual structural text alteration path
    sidebar.combo_sessions.setCurrentText("New_2")
    assert spy.call_count == 1


def test_ui_structure_coverage(sidebar):
    """Ensure complete layout tree generation elements compile safely."""
    assert isinstance(sidebar.main_container, QWidget)
    assert isinstance(sidebar.scroll_area, QScrollArea)
    assert sidebar.scroll_area.widget() == sidebar.container
    assert sidebar.btn_fmc.objectName() == "FMCBtn"
    assert sidebar.btn_analysis.objectName() == "AnalyzeBtn"
    assert sidebar.btn_report.objectName() == "ReportBtn"


def test_unimplemented_method_branch_coverage(sidebar):
    """
    Branch Coverage: Verifies that handling an unsupported analysis method
    gracefully updates the terminal footer status view using a KeyError fallback.
    """
    # Force state machine to select a planned/unsupported text target string block
    sidebar.combo_method.setCurrentText("OCRA (Planned)")

    # Trigger the submission execution handler loop
    sidebar.btn_analysis.click()

    # Assert fallback loop captures standard error message strings accurately
    assert "OCRA (PLANNED) is not implemented." in sidebar.status_label.text()
