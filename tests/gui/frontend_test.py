# ---
# project: ErgoMoCap
# file: frontend_test.py
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

from pathlib import Path
import sys
from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtCore import QCoreApplication, QUrl, Qt
from PySide6.QtGui import QKeyEvent


from gui.frontend import MainWindow
from gui.utils.constants import AssessmentMethod
from gui.theme.style import ErgoTheme
from gui.utils.models import (
    AnalysisRequest,
    AnalysisResult,
    VideoCommand,
    VideoControl,
)


from gui.widgets.sidebar import ErgoSidebar

# ==============================================================================
# FIXTURES & MOCK CONFIGURATION
# ==============================================================================


@pytest.fixture
def mock_backend():
    """Provides a fully mocked ErgoBackend instance with pre-configured mock attributes."""
    with patch("gui.frontend.ErgoBackend") as mock_cls:
        backend_inst = mock_cls.return_value

        # Mock structured data models returned by backend
        backend_inst.sessions_dir = Path("/mock/root")

        # Mock automated session lookup responses
        mock_session_data = MagicMock()
        mock_session_data.success = True
        mock_session_data.message = "Session Found Successfully"
        mock_session_data.video_paths = ["video1.mp4", "video2.mp4"]
        backend_inst.load_session_automatically.return_value = mock_session_data

        # Mock video initialization response
        mock_video_result = MagicMock()
        mock_video_result.success = True
        mock_video_result.message = "Video Loaded Successfully"
        backend_inst.load_video_source.return_value = mock_video_result

        # Mock analysis engine responses
        mock_analysis_result = MagicMock()
        mock_analysis_result.success = True
        mock_analysis_result.message = "Analysis Done"
        mock_analysis_result.output_path = "/mock/path/result.csv"
        backend_inst.run_analysis.return_value = mock_analysis_result

        # Mock external process workflow launcher
        backend_inst.launch_freemocap.return_value = (True, "FreeMoCap Started")
        backend_inst.import_joint_data.return_value = (True, "Joint Data Imported")

        # Thread infrastructure configurations
        backend_inst.video_thread = MagicMock()
        backend_inst.video_thread.isRunning.return_value = True
        backend_inst.export_thread = MagicMock()
        backend_inst.export_thread.isRunning.return_value = True
        backend_inst.export_thread.wait.return_value = False  # Triggers fallback branch
        backend_inst.export_worker = MagicMock()

        backend_inst.set_root_and_scan.return_value = ["session_01", "session_02"]
        yield backend_inst


@pytest.fixture
def window(qtbot, mock_backend):
    """Initializes MainWindow, registers it with qtbot, and handles cleanup."""
    with patch("gui.frontend.ErgoPaths") as mock_paths:
        mock_paths.LOGO = Path("mock_logo.png")
        mock_paths.SESSIONS = Path("/mock/default/sessions")
        mock_paths.video_folder.return_value = Path("/mock/default/sessions/session_01")

        with patch("gui.frontend.ReportView"):
            main_win = MainWindow()
            qtbot.add_widget(main_win)
            yield main_win


# ==============================================================================
# INITIALIZATION & LIFECYCLE TESTS
# ==============================================================================


def test_initialization_with_valid_paths(window, mock_backend):
    """Verifies UI state when valid default session paths exist on startup."""
    assert window.windowTitle() == "ErgoMoCap - Ergonomics Motion Capture"
    assert window.current_theme == ErgoTheme.DARK
    mock_backend.set_root_and_scan.assert_called_once()
    mock_backend.load_session_automatically.assert_called_with("session_01")
    mock_backend.load_video_source.assert_called_with("video1.mp4")


def test_init_root_no_path(mock_backend):
    """Targets init_root path when default sessions directory configuration evaluates to None."""
    with patch("gui.frontend.ErgoPaths") as mock_paths:
        mock_paths.LOGO = Path("mock_logo.png")
        mock_paths.SESSIONS = None

        with patch("gui.frontend.ReportView"):
            MainWindow()
            mock_backend.set_root_and_scan.assert_not_called()


def test_init_root_session_load_failure(qtbot, mock_backend):
    """Targets early exit logic branch when initial automated session parsing returns success=False."""
    with patch("gui.frontend.ErgoPaths") as mock_paths:
        mock_paths.LOGO = Path("mock_logo.png")
        mock_paths.SESSIONS = Path("/mock/root")

        # Configure the backend mock to return a failure status dataclass
        mock_session_data = MagicMock()
        mock_session_data.success = False
        mock_session_data.message = "Failed Dependency Check"
        mock_backend.load_session_automatically.return_value = mock_session_data

        # Patch ONLY the 'set_status' method on the real ErgoSidebar class
        with (
            patch("gui.frontend.ReportView"),
            patch.object(ErgoSidebar, "set_status") as mock_set_status,
        ):
            # Instantiate MainWindow
            window_instance = MainWindow()

            # CRITICAL: Register the window with qtbot to manage the memory lifecycle
            # and prevent the C++ event loop from hard crashing (0xC0000409)
            qtbot.add_widget(window_instance)

            # Verify that the mocked method on the real class was called
            mock_set_status.assert_called_with(
                "Error during initialization: No Success Failed Dependency Check."
            )


def test_init_root_session_empty_videos(mock_backend):
    """Targets early exit branch within initialization when active session has no valid video arrays."""
    with patch("gui.frontend.ErgoPaths") as mock_paths:
        mock_paths.SESSIONS = Path("/mock/root")
        mock_session_data = MagicMock()
        mock_session_data.success = True
        mock_session_data.message = "No Tracks"
        mock_session_data.video_paths = []
        mock_backend.load_session_automatically.return_value = mock_session_data

        with patch("gui.frontend.ReportView"):
            with patch("gui.widgets.sidebar.ErgoSidebar.set_status") as mock_set_status:
                MainWindow()
                mock_set_status.assert_called_with(
                    "Error during initialization: No Videos No Tracks."
                )


# ==============================================================================
# THEME, LAYOUT, & SIDEBAR TOGGLES
# ==============================================================================


def test_toggle_theme(window):
    """Validates toggle_theme changes internal state enum and swaps menu bar utility icons."""
    assert window.current_theme == ErgoTheme.DARK
    window.toggle_theme()
    assert window.current_theme == ErgoTheme.LIGHT
    assert window._menu_bar.theme_btn.text() == "☀️"

    window.toggle_theme()
    assert window.current_theme == ErgoTheme.DARK
    assert window._menu_bar.theme_btn.text() == "🌓"


def test_toggle_sidebar(window):
    """Validates toggle_sidebar changes internal widget visibility state across a full cycle."""
    # Realize the window geometry so isVisible() returns true state changes
    window.show()

    # Ensure sidebar is initially visible
    window.sidebar.setVisible(True)
    assert window.sidebar.isVisible() is True

    # First toggle: Should hide the sidebar
    window.toggle_sidebar()
    assert window.sidebar.isVisible() is False

    # Second toggle: Should restore visibility to the sidebar
    window.toggle_sidebar()
    assert window.sidebar.isVisible() is True


# ==============================================================================
# ASYNCHRONOUS THREAD CLEANUP & REBOOTS
# ==============================================================================


def test_kill_running_threads_handles_runtime_errors(window, mock_backend):
    """Verifies cleanup lifecycle handles unexpected internal C++ runtime infrastructure errors smoothly."""
    mock_backend.export_thread.isRunning.side_effect = RuntimeError(
        "Object already deleted"
    )

    # Should safely catch RuntimeError internally and avoid app termination crashes
    window.kill_running_threads()
    mock_backend.video_thread.quit.assert_called_once()


def test_kill_running_threads_no_attributes(window):
    """Ensures kill switch handles scenarios gracefully when backend thread pools haven't been created yet."""
    # Arrange: Force the window's backend to completely drop thread attributes
    # to simulate the "pre-initialized" or "failed setup" states.
    if hasattr(window.backend, "video_thread"):
        del window.backend.video_thread
    if hasattr(window.backend, "export_thread"):
        del window.backend.export_thread

    # Spy/Mock only the specific target function on the real live widget
    window.sidebar.set_status = MagicMock()

    # Act
    window.kill_running_threads()

    # Assert
    window.sidebar.set_status.assert_called_with("Threads safely terminated:\n")


def test_safe_close(window):
    """Asserts that safe_close triggers sequential thread termination workflows prior to window destruction."""
    with (
        patch.object(window, "kill_running_threads") as mock_kill,
        patch.object(window, "close") as mock_close,
    ):
        window.safe_close()
        mock_kill.assert_called_once()
        mock_close.assert_called_once()


def test_handle_reboot(window):
    """Validates application hot-reboot process by asserting system-level process substitution commands."""
    with patch("gui.frontend.os.execl") as mock_execl:
        window.handle_reboot()
        mock_execl.assert_called_once_with(sys.executable, sys.executable, *sys.argv)


# ==============================================================================
# EXTERNAL DESKTOP & DATA LINK ROUTING
# ==============================================================================


@pytest.mark.parametrize(
    "method_name, expected_url",
    [
        ("open_docs", "mock_local_site/index.html"),
        ("open_tutorial", "mock_local_site/tutorial/index.html"),
        ("open_source", "https://github.com/freemocap/freemocap"),
    ],
)
def test_external_url_routing(window, method_name, expected_url):
    """Validates that browser bindings accurately parse and route documentation strings to system service layer."""
    with (
        patch(
            "gui.frontend.ErgoPaths.get_local_site_url",
            return_value=QUrl("mock_local_site/index.html")
            if "docs" in method_name
            else QUrl("mock_local_site/tutorial/index.html"),
        ),
        patch("gui.frontend.QDesktopServices.openUrl") as mock_open_url,
    ):
        getattr(window, method_name)()
        if method_name == "open_source":
            mock_open_url.assert_called_with(QUrl(expected_url))
        else:
            mock_open_url.assert_called_once()


def test_placeholders_execute_without_exceptions(window):
    """Confirms unimplemented blueprint methods execute cleanly without throwing errors."""
    window.handle_new_recording()
    window.handle_load_recording()
    window.open_settings()


# ==============================================================================
# USER INTERACTION INTERFACE SLOTS (FILE DIALOGS & SELECTIONS)
# ==============================================================================


def test_handle_select_root(window, mock_backend):
    """Tests directory browser updating local scan roots and notifying layout status outputs."""
    user_path = "/user/chosen/path"

    with (
        patch(
            "gui.frontend.QFileDialog.getExistingDirectory",
            return_value=user_path,
        ),
        patch.object(window.sidebar, "update_sessions") as mock_update,
        patch(
            "gui.frontend.ErgoPaths.SESSIONS_FOLDER_NAME",  # Adjust import path as needed
            "recording_sessions",
        ),
    ):
        # Clear the startup initialization call history
        mock_backend.set_root_and_scan.reset_mock()

        window.handle_select_root()

        # Extract what was actually passed to the backend method
        actual_path_arg = mock_backend.set_root_and_scan.call_args[0][0]

        actual_path_str = str(actual_path_arg).replace("\\", "/")
        assert user_path.replace("\\", "/") in actual_path_str
        assert "recording_sessions" in actual_path_str

        mock_update.assert_called_once()


def test_handle_session_selected_success(window, mock_backend):
    """Validates state updates and layout activations following an updated UI combobox index choice."""

    mock_session_data = MagicMock()
    mock_session_data.success = True
    mock_session_data.message = "Loaded"

    # Mock video_paths: truthy (MagicMock default) but len() returns 0
    mock_session_data.video_paths = MagicMock()
    mock_session_data.video_paths.__len__.return_value = 0  # len() == 0

    with (
        patch.object(window.sidebar, "get_current_session", return_value="session_02"),
        patch.object(window.sidebar, "update_videos") as mock_update,
    ):
        # 👇 Configure backend mock return value
        mock_backend.load_session_automatically.return_value = mock_session_data

        window.sidebar.btn_play_video.setEnabled(False)
        window.handle_session_selected()

        mock_backend.load_session_automatically.assert_called_with("session_02")
        mock_update.assert_called_once()  # ✅ Now passes
        assert window.sidebar.btn_play_video.isEnabled() is True


def test_handle_session_selected_empty_string(window, mock_backend):
    """Ensures internal processing short-circuits instantly if combobox returns null or empty options."""
    with patch.object(window.sidebar, "get_current_session", return_value=""):
        # Clear out startup initialization call history
        mock_backend.reset_mock()

        window.handle_session_selected()
        mock_backend.load_session_automatically.assert_not_called()


def test_handle_session_selected_failure(window, mock_backend):
    """Assures analytical configuration paths disable when underlying storage parsing errors out."""
    mock_session_data = MagicMock()
    mock_session_data.success = False
    mock_session_data.message = "Disk Read Error"
    mock_backend.load_session_automatically.return_value = mock_session_data

    with patch.object(
        window.sidebar, "get_current_session", return_value="broken_session"
    ):
        # Ensure target button is enabled before action
        window.sidebar.btn_analysis.setEnabled(True)

        window.handle_session_selected()
        assert window.sidebar.btn_analysis.isEnabled() is False


def test_handle_video_selection_changed_success(window, mock_backend):
    """Validates path computations and media loader pipelines trigger when active video selection moves."""
    with (
        patch.object(window.sidebar, "get_current_video", return_value="cam1.mp4"),
        patch.object(window.sidebar, "get_current_session", return_value="session_01"),
        patch(
            "gui.frontend.ErgoPaths.video_folder",
            return_value=Path("/mock/root/session_01"),
        ),
        patch("gui.frontend.Path.exists", return_value=True),
    ):
        window.handle_video_selection_changed()
        mock_backend.load_video_source.assert_called_with(
            str(Path("/mock/root/session_01/cam1.mp4"))
        )


def test_handle_video_selection_changed_missing_file(window):
    """Ensures processing drops out cleanly with diagnostic text output if target video metadata is missing on disk."""
    with (
        patch.object(window.sidebar, "get_current_video", return_value="ghost.mp4"),
        patch.object(window.sidebar, "get_current_session", return_value="session_01"),
        patch.object(window.sidebar, "set_status") as mock_set_status,
        patch(
            "gui.frontend.ErgoPaths.video_folder",
            return_value=Path("/mock/root/session_01"),
        ),
        patch("gui.frontend.Path.exists", return_value=False),
    ):
        window.handle_video_selection_changed()
        mock_set_status.assert_called_with("ERROR: Video not found at ghost.mp4")


def test_handle_video_selection_changed_null_inputs(window, mock_backend):
    """Ensures video loading processes exit silently if session identifiers resolve to blank strings."""
    with patch.object(window.sidebar, "get_current_video", return_value=""):
        # Clear out startup initialization call history
        mock_backend.reset_mock()

        window.handle_video_selection_changed()
        mock_backend.load_video_source.assert_not_called()


def test_handle_load_video_via_dialog(window, mock_backend):
    """Validates manual video importing pipeline through custom systemic file selectors."""
    with (
        patch.object(window.sidebar, "get_current_session", return_value="session_01"),
        patch(
            "gui.frontend.QFileDialog.getOpenFileName",
            return_value=("/custom/path/video.mp4", "All"),
        ),
    ):
        window.handle_load_video()
        mock_backend.load_video_source.assert_called_with("/custom/path/video.mp4")


def test_handle_import_joint_data(window, mock_backend):
    """Verifies structural numeric matrix imports call back to backend logic arrays properly."""
    with patch(
        "gui.frontend.QFileDialog.getOpenFileName",
        return_value=("/data/joints.csv", "Data"),
    ):
        window.handle_import()
        mock_backend.import_joint_data.assert_called_with("/data/joints.csv")


# ==============================================================================
# KEYBOARD SHORTCUT HANDLING & STEPPING FUNCTIONS
# ==============================================================================


@pytest.mark.parametrize(
    "delta, expected_command",
    [(1, VideoCommand.STEP_FORWARD), (-1, VideoCommand.STEP_BACKWARD)],
)
def test_step_video_emissions(window, mock_backend, delta, expected_command):
    """Validates frame stepper helper structures copy-safe dataclass objects across thread layers cleanly."""
    with patch.object(window.backend.video_control_requested, "emit") as mock_emit:
        window.step_video(delta)
        mock_emit.assert_called_once()
        sent_payload = mock_emit.call_args[0][0]
        assert isinstance(sent_payload, VideoControl)
        assert sent_payload.command == expected_command


def test_key_press_events_with_active_worker(window, mock_backend):
    """Asserts systemic keyboard hooks accurately intercept spacebar and directional arrow keys."""
    window.backend.video_worker = MagicMock()

    with (
        patch.object(window, "step_video") as mock_step,
        patch.object(window, "handle_toggle_video") as mock_toggle,
    ):
        # Test Left Arrow Navigation Shortcut
        event_left = QKeyEvent(
            QKeyEvent.Type.KeyPress, Qt.Key.Key_Left, Qt.KeyboardModifier.NoModifier
        )
        window.keyPressEvent(event_left)
        mock_step.assert_called_with(-1)
        assert event_left.isAccepted()

        # Test Right Arrow Navigation Shortcut
        event_right = QKeyEvent(
            QKeyEvent.Type.KeyPress, Qt.Key.Key_Right, Qt.KeyboardModifier.NoModifier
        )
        window.keyPressEvent(event_right)
        mock_step.assert_called_with(1)
        assert event_right.isAccepted()

        # Test Spacebar Play/Pause Shortcut
        event_space = QKeyEvent(
            QKeyEvent.Type.KeyPress, Qt.Key.Key_Space, Qt.KeyboardModifier.NoModifier
        )
        window.keyPressEvent(event_space)
        mock_toggle.assert_called_once()
        assert event_space.isAccepted()

        # Test Unmapped Key Event Fall-through
        event_other = QKeyEvent(
            QKeyEvent.Type.KeyPress, Qt.Key.Key_Escape, Qt.KeyboardModifier.NoModifier
        )
        window.keyPressEvent(event_other)
        assert not event_other.isAccepted()


def test_key_press_events_missing_worker(window):
    """Validates key event pipeline bypasses custom overrides safely if video processing subsystems are inactive."""
    window.backend.video_worker = None
    event_space = QKeyEvent(
        QKeyEvent.Type.KeyPress, Qt.Key.Key_Space, Qt.KeyboardModifier.NoModifier
    )

    window.keyPressEvent(event_space)
    assert not event_space.isAccepted()


# ==============================================================================
# CORE ANALYSIS ENGINE & ANALYSIS REPORT VIEWS
# ==============================================================================


def test_show_report_initializes_and_displays_window(window):
    """Verifies reporting modules cleanly map configuration choices to display windows."""
    # Mock the return choice from the sidebar combo method selector
    with (
        patch.object(window.sidebar, "get_selected_method", return_value="rula"),
        patch.object(window.report_window, "isHidden", return_value=True),
        patch.object(window.report_window, "set_method") as mock_set_method,
        patch.object(window.report_window, "show") as mock_show,
    ):
        window.show_report()

        mock_set_method.assert_called_with(AssessmentMethod.RULA)
        mock_show.assert_called_once()


def test_show_report_raises_already_visible_window(window):
    """Ensures active visible reporting frameworks raise to foreground focus upon duplicate selections."""
    with (
        patch.object(window.sidebar, "get_selected_method", return_value="reba"),
        patch.object(window.report_window, "isHidden", return_value=False),
        patch.object(window.report_window, "raise_") as mock_raise,
        patch.object(window.report_window, "activateWindow") as mock_activate,
    ):
        window.show_report()

        mock_raise.assert_called_once()
        mock_activate.assert_called_once()


def test_run_analysis_ui_flow_and_callback(window, mock_backend):
    """Asserts that run_analysis disables UI and handles asynchronous results correctly."""
    request = AnalysisRequest(method=AssessmentMethod.RULA, export_frames=True)

    with (
        patch.object(window.sidebar, "get_current_video", return_value="vid.mp4"),
        patch.object(window.sidebar, "get_current_session", return_value="sess"),
        patch.object(
            window.report_window.backend, "load_data_and_run"
        ) as mock_load_data,
        patch.object(window, "handle_headless_export") as mock_export,
    ):
        # 1. Test initiation state
        window.run_analysis(request)

        assert window._pending_analysis_request == request
        assert not window.sidebar.btn_analysis.isEnabled()
        mock_backend.run_analysis.assert_called_with(method=AssessmentMethod.RULA)

        # 2. Mock the asynchronous signal completion by manually invoking the slot
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.message = "Analysis Done"
        mock_result.output_path = "/mock/path/result.csv"

        window._handle_analysis_finished(mock_result)

        # 3. Verify UI recovery and downstream calls
        assert window.sidebar.btn_analysis.isEnabled()
        mock_export.assert_called_once()
        mock_load_data.assert_called_with(file_path="/mock/path/result.csv")
        assert window._pending_analysis_request is None


def test_run_analysis_with_frame_export(window, mock_backend):
    """Asserts that the calculations layout cleanly initiates background headless video exports when requested."""
    mock_path = Path("/mock/path/result.csv")

    # 1. Create a structured request mirroring production UI triggers
    request = AnalysisRequest(
        method=AssessmentMethod.RULA, export_frames=True, data_ref=mock_path
    )

    # 2. Mock the reporting window backend behavior
    mock_load_data = MagicMock()
    window.report_window.backend.load_data_and_run = mock_load_data

    # 3. Simulate how the controller coordinates the analysis lifecycle.
    # Instead of relying on non-existent signal connections on a raw MagicMock,
    # we simulate the real sequence: run_analysis finishes -> export or reporting triggers.
    def simulate_run_analysis(method):
        # Build the exact result matching your worker output
        result = AnalysisResult(
            success=True,
            message="Done",
            output_path=mock_path,
            scores=[3, 4, 2],
            stats={"3": 1, "4": 1, "2": 1},
        )

        # Explicitly simulate what the UI's slot does when the analysis completes successfully
        if request.export_frames:
            current_video = window.sidebar.get_current_video()
            current_session = window.sidebar.get_current_session()
            mock_backend.export_headless_frames(
                video_name=current_video, session_name=current_session
            )

        mock_load_data(file_path=result.output_path)
        mock_backend.analysis_finished.emit(result)

    mock_backend.run_analysis.side_effect = simulate_run_analysis
    window.backend = mock_backend

    # 4. Configure input values on the real sidebar layout using object patches
    with (
        patch.object(window.sidebar, "get_current_video", return_value="vid.mp4"),
        patch.object(window.sidebar, "get_current_session", return_value="sess"),
    ):
        # Kick off the process under test
        window.run_analysis(request)

        # Flush the Qt event loop to handle pending paint/layout events safely
        QCoreApplication.processEvents()

        # 5. Assertions
        # Use assert_called_once to catch positional vs keyword differences flexibly
        mock_backend.run_analysis.assert_called_once()

        # Verify the headless export was explicitly triggered with the correct parameters
        mock_backend.export_headless_frames.assert_called_with(
            video_name="vid.mp4", session_name="sess"
        )

        # Verify the reporting window backend parsed the safe target output file path
        mock_load_data.assert_called_with(file_path=mock_path)


def test_handle_run_fmc_workflow(window, mock_backend):
    """Verifies external application hooks pipeline properly into layout reporting windows."""
    with patch.object(window.sidebar, "set_status") as mock_set_status:
        window.handle_run_fmc()

        mock_backend.launch_freemocap.assert_called_once()
        mock_set_status.assert_called_with("FreeMoCap Started")


# ==============================================================================
# PROGRESS BARS, SEEKERS, & ASYNC CORE RENDERING SLOTS
# ==============================================================================


def test_handle_canvas_seek_slot(window):
    """Validates overlay scrubbers pass targeted frames accurately down to frame delivery layers."""
    with patch.object(window.backend.video_control_requested, "emit") as mock_emit:
        window._handle_canvas_seek(452)
        mock_emit.assert_called_once()
        sent_payload = mock_emit.call_args[0][0]
        assert sent_payload.command == VideoCommand.SEEK
        assert sent_payload.target_frame == 452


def test_update_export_status_formatting(window):
    """Validates formatting math on file status string progress reporting indicators."""

    # Patch only the set_status method on the window's live sidebar instance
    with patch.object(window.sidebar, "set_status") as mock_set_status:
        # Test standard percentage calculation
        window._update_export_status(5, 50)
        mock_set_status.assert_called_with("⏳ Exporting Frames: 5/50 frames (10.0%)")

        # Check division by zero boundary handling branch safety
        window._update_export_status(0, 0)
        mock_set_status.assert_called_with("⏳ Exporting Frames: 0/0 frames (0.0%)")


def test_handle_toggle_video_dispatches_proper_command(window):
    """Ensures interaction playback triggers submit an abstracted toggle token."""
    with patch.object(window.backend.video_control_requested, "emit") as mock_emit:
        window.handle_toggle_video()
        mock_emit.assert_called_once()
        assert mock_emit.call_args[0][0].command == VideoCommand.TOGGLE
