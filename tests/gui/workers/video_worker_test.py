# ---
# project: ErgoMoCap
# file: video_worker_test.py
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
from unittest.mock import MagicMock, patch
import pytest
import numpy as np
import cv2

from PySide6.QtCore import QTimer
from gui.workers.video_worker import VideoWorker
from gui.utils.models import (
    FrameData,
    FramesExportResult,
    VideoCommand,
    VideoControl,
    VideoLoadRequest,
    RiskLevel,  # Added to satisfy the explicit Enum type constraint
)
from gui.core.analysis_engine import AnalysisEngine


@pytest.fixture
def mock_video_capture():
    """Mock standard cv2.VideoCapture behaviors for deterministic unit testing."""
    with patch("gui.workers.video_worker.cv2.VideoCapture") as mock_cap_class:
        mock_instance = MagicMock()
        mock_cap_class.return_value = mock_instance

        # Default mock settings: 10 frames total, 30 FPS, successfully opens
        mock_instance.isOpened.return_value = True

        def mock_get(prop):
            if prop == cv2.CAP_PROP_FRAME_COUNT:
                return 10.0
            if prop == cv2.CAP_PROP_FPS:
                return 30.0
            if prop == cv2.CAP_PROP_FRAME_WIDTH:
                return 640.0
            if prop == cv2.CAP_PROP_FRAME_HEIGHT:
                return 480.0
            return 0.0

        mock_instance.get.side_effect = mock_get
        # Returns True and a dummy black frame layout matrix
        mock_instance.read.return_value = (
            True,
            np.zeros((480, 640, 3), dtype=np.uint8),
        )
        yield mock_instance


@pytest.fixture
def worker(qtbot, request):
    """Instantiate the VideoWorker and register its cleanup lifecycle."""
    video_worker = VideoWorker()

    # Use request.addfinalizer to cleanly schedule deleteLater on the Qt main loop
    request.addfinalizer(video_worker.deleteLater)

    return video_worker


@pytest.fixture
def sample_request():
    """Provides a valid, populated VideoLoadRequest dataclass configuration payload."""
    return VideoLoadRequest(
        path=Path("dummy_video.mp4"),
        scores=[2, 4, 6, 8, 3, 5, 7, 9, 1, 4],
        thresholds=[(3, RiskLevel.LOW), (6, RiskLevel.MEDIUM), (9, RiskLevel.HIGH)],
    )


# ==============================================================================
# INITIALIZATION & LIFECYCLE TESTS
# ==============================================================================


def test_init_timer(worker):
    """Verify that init_timer sets up a valid QTimer with proper signal connections."""
    assert worker.playback_timer is None

    worker.init_timer()

    assert isinstance(worker.playback_timer, QTimer)
    assert worker.playback_timer.parent() is worker


def test_initialize_video_creates_timer_if_missing(
    worker, mock_video_capture, sample_request
):
    """Verify initialize_video lazy-initializes a timer instance safely if not present."""
    assert worker.playback_timer is None

    worker.initialize_video(sample_request)

    assert worker.playback_timer is not None
    assert worker.video_path == "dummy_video.mp4"
    assert worker.total_frames == 10
    assert worker.playback_interval_ms == 33  # 1000 / 30 fps


def test_initialize_video_stops_existing_timer_and_releases_capture(
    worker, mock_video_capture, sample_request
):
    """Verify video re-initialization clears historical components and frames counters cleanly."""
    worker.init_timer()

    # Pre-populate historical mock states
    mock_old_cap = MagicMock()
    worker.cap = mock_old_cap
    worker.playback_timer.start(100)
    worker.current_frame_idx = 5

    worker.initialize_video(sample_request)

    mock_old_cap.release.assert_called_once()
    assert not worker.playback_timer.isActive()
    assert worker.current_frame_idx == 0


def test_initialize_video_handles_zero_fps_fallback(
    worker, mock_video_capture, sample_request
):
    """Verify the calculation safeguards against divide-by-zero errors if video FPS reports 0."""
    mock_video_capture.get.side_effect = lambda prop: (
        0.0 if prop == cv2.CAP_PROP_FPS else 10.0
    )

    worker.initialize_video(sample_request)
    assert worker.playback_interval_ms == 33  # Fallback 30.0 FPS applied (1000 // 30)


def test_cleanup(worker, mock_video_capture):
    """Verify complete release of open file handles and timeline interval scheduling rules."""
    worker.init_timer()
    worker.cap = mock_video_capture
    worker.playback_timer.start(50)

    worker.cleanup()

    assert not worker.playback_timer.isActive()
    mock_video_capture.release.assert_called_once()


# ==============================================================================
# PLAYBACK PLAY / PAUSE LOGIC TESTS
# ==============================================================================


def test_toggle_playback_fails_without_open_capture_or_timer(worker):
    """Verify playback configuration returns False if assets are uninitialized."""
    # Scenario A: Completely uninitialized
    assert worker.toggle_playback() is False

    # Scenario B: Captured but lacks timer context
    worker.cap = MagicMock()
    worker.cap.isOpened.return_value = True
    assert worker.toggle_playback() is False


def test_toggle_playback_starts_and_stops_timer(
    worker, mock_video_capture, sample_request
):
    """Verify toggle framework alters timer loop parameters statefully."""
    worker.initialize_video(sample_request)
    assert not worker.playback_timer.isActive()

    # Toggle on
    started = worker.toggle_playback()
    assert started is True
    assert worker.playback_timer.isActive()
    assert worker.playback_timer.interval() == worker.playback_interval_ms

    # Toggle off
    stopped = worker.toggle_playback()
    assert stopped is False
    assert not worker.playback_timer.isActive()


# ==============================================================================
# SEEKING & STEPPING OPERATIONS
# ==============================================================================


def test_seek_to_index_out_of_bounds_clamping(
    worker, mock_video_capture, sample_request
):
    """Verify target indices clamp safely inside absolute frame boundary limits."""
    worker.initialize_video(sample_request)

    # Lower bound clamping verification
    worker._seek_to_index(-50)
    assert worker.current_frame_idx == 0

    # Upper bound clamping verification
    worker._seek_to_index(500)
    assert worker.current_frame_idx == 9  # total_frames (10) - 1


def test_seek_does_nothing_if_capture_is_not_open(worker):
    """Verify seeking exits immediately without crashing if capture stream is closed."""
    worker.cap = MagicMock()
    worker.cap.isOpened.return_value = False

    worker.seek(3)
    assert worker.current_frame_idx == 0  # Unchanged


@patch.object(AnalysisEngine, "get_risk_level_enum", return_value=RiskLevel.LOW)
def test_seek_emits_payload_and_re_seeks(
    mock_get_risk, worker, qtbot, mock_video_capture, sample_request
):
    """Verify seeking positions hardware capture pointers and flashes snapshot data payloads."""
    worker.initialize_video(sample_request)

    # Initialization calls set() twice (one for initial preview frame, one to re-seek back).
    # Clear mock history here so we can cleanly assert on just the .seek() action.
    mock_video_capture.set.reset_mock()

    with qtbot.wait_signals([worker.frame_ready, worker.position_changed], timeout=500):
        worker.seek(4)

    assert worker.current_frame_idx == 4
    # Frame seeking triggers set mapping calls twice within _seek_to_index
    assert mock_video_capture.set.call_count == 2
    mock_video_capture.set.assert_any_call(cv2.CAP_PROP_POS_FRAMES, 4)


def test_step_frame_forward_and_backward(worker, mock_video_capture, sample_request):
    """Verify single step movements accurately calculate step coordinate values."""
    worker.initialize_video(sample_request)
    worker.current_frame_idx = 4

    with patch.object(worker, "_seek_to_index") as mock_seek:
        worker.step_frame(forward=True)
        mock_seek.assert_called_with(5)

        worker.step_frame(forward=False)
        mock_seek.assert_called_with(3)


# ==============================================================================
# VIDEO CONTROL INTERFACE ROUTING
# ==============================================================================


def test_handle_video_control_toggle(worker):
    """Verify control dispatch intercepts and routes toggle commands cleanly."""
    with patch.object(worker, "toggle_playback") as mock_toggle:
        control = VideoControl(command=VideoCommand.TOGGLE, target_frame=None)
        worker.handle_video_control(control)
        mock_toggle.assert_called_once()


def test_handle_video_control_seek(worker, mock_video_capture, sample_request):
    """Verify control dispatch extracts target values and filters inputs safely."""
    worker.initialize_video(sample_request)

    with patch.object(worker, "_seek_to_index") as mock_seek:
        # Seek targeting active index
        worker.handle_video_control(
            VideoControl(command=VideoCommand.SEEK, target_frame=5)
        )
        mock_seek.assert_called_once_with(frame_idx=5)

        # Seek missing explicit parameter frame target (ignored safely)
        mock_seek.reset_mock()
        worker.handle_video_control(
            VideoControl(command=VideoCommand.SEEK, target_frame=None)
        )
        mock_seek.assert_not_called()


def test_handle_video_control_stepping(worker, mock_video_capture, sample_request):
    """Verify control interfaces enforce forward/backward boundary rules during processing."""
    worker.initialize_video(sample_request)

    with patch.object(worker, "step_frame") as mock_step:
        # Step Forward
        worker.current_frame_idx = 0
        worker.handle_video_control(VideoControl(command=VideoCommand.STEP_FORWARD))

        mock_step.assert_called_once_with(forward=True)

        # Step Backward
        mock_step.reset_mock()
        worker.handle_video_control(
            VideoControl(command=VideoCommand.STEP_BACKWARD, target_frame=None)
        )
        assert worker.current_frame_idx == 0
        mock_step.assert_called_once_with(forward=False)


# ==============================================================================
# BACKGROUND TIMER FRAME PROCESSING
# ==============================================================================


def test_process_playback_frame_aborts_without_timer_or_open_capture(worker):
    """Verify background frame processing safely terminates execution if contexts drop."""
    # Case A: Missing timer instance context
    assert worker.playback_timer is None
    worker._process_playback_frame()  # Exits silently without issues

    # Case B: Captured stream disconnects while processing ticks
    worker.init_timer()
    worker.playback_timer.start(100)
    worker.cap = MagicMock()
    worker.cap.isOpened.return_value = False

    worker._process_playback_frame()
    assert not worker.playback_timer.isActive()


def test_process_playback_frame_stops_at_eof(
    worker, mock_video_capture, sample_request
):
    """Verify playback automatically turns off when the end of the file is reached."""
    worker.initialize_video(sample_request)
    worker.playback_timer.start(100)

    # Force read simulation failure to mimic an EOF condition
    mock_video_capture.read.return_value = (False, None)

    worker._process_playback_frame()
    assert not worker.playback_timer.isActive()


def test_process_playback_frame_increments_and_emits(
    worker, qtbot, mock_video_capture, sample_request
):
    """Verify valid sequential frames accurately advance loop indices and dispatch data packages."""
    worker.initialize_video(sample_request)
    worker.init_timer()
    worker.current_frame_idx = 2

    with qtbot.wait_signals([worker.frame_ready, worker.position_changed], timeout=500):
        worker._process_playback_frame()

    assert worker.current_frame_idx == 3


# ==============================================================================
# FRAME TELEMETRY PAYLOAD EMISSION
# ==============================================================================


def test_emit_current_frame_payload_safeguards(worker, qtbot):
    """Verify tracking emissions execute reliably even if index lists or risk targets are missing."""
    dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    worker.scores_list = []  # No structural telemetry data
    worker.current_frame_idx = 0
    worker.total_frames = 100

    # Should evaluate with default fallback values cleanly
    with qtbot.wait_signal(worker.frame_ready) as blocker:
        worker._emit_current_frame_payload(dummy_frame)

    payload = blocker.args[0]
    assert isinstance(payload, FrameData)
    assert payload.score is None
    assert payload.risk is None


# ==============================================================================
# BULK FRAMES EXPORT WORKFLOW TESTS
# ==============================================================================


def test_execute_frames_export_aborts_if_uninitialized(worker):
    """Verify bulk export operations terminate safely if internal timers are missing."""
    assert worker.playback_timer is None
    worker.execute_frames_export("output.mp4")  # Exits silently without exceptions


def test_execute_frames_export_fails_if_capture_closed(worker, qtbot):
    """Verify export failures emit clear failure notifications to monitoring layers."""
    worker.init_timer()
    worker.cap = MagicMock()
    worker.cap.isOpened.return_value = False

    with qtbot.wait_signal(worker.frames_export_finished) as blocker:
        worker.execute_frames_export("output.mp4")

    result = blocker.args[0]
    assert isinstance(result, FramesExportResult)
    assert result.success is False
    assert "No video stream initialized" in result.message


@patch("gui.workers.video_worker.cv2.VideoWriter")
def test_execute_frames_export_success(
    mock_writer_class, worker, qtbot, mock_video_capture, sample_request
):
    """Verify successful frame-by-frame background conversion loops and progress signal scaling."""
    worker.initialize_video(sample_request)
    mock_writer = MagicMock()
    mock_writer_class.return_value = mock_writer

    # Ensure read behaves accurately as a sequence loop over 10 iterations
    mock_video_capture.read.side_effect = [
        (True, np.zeros((480, 640, 3), dtype=np.uint8)) for _ in range(10)
    ] + [(False, None)]

    # Track export progress calls
    progress_signals = []
    worker.export_progress.connect(progress_signals.append)

    with qtbot.wait_signal(worker.frames_export_finished) as blocker:
        worker.execute_frames_export("output_folder/export.mp4")

    result = blocker.args[0]
    assert result.success is True
    assert "Export successful" in result.message

    # 10 frames total / updates triggered every 5th item (idx 0 and idx 5)
    assert len(progress_signals) == 2
    assert progress_signals[0].current_frame == 0
    assert progress_signals[1].current_frame == 5

    mock_writer.write.assert_called()
    mock_writer.release.assert_called_once()


@patch("gui.workers.video_worker.cv2.VideoWriter")
def test_execute_frames_export_exception_handling(
    mock_writer_class, worker, qtbot, mock_video_capture, sample_request
):
    """Verify internal conversion exceptions are caught gracefully and wrapped inside status results."""
    worker.initialize_video(sample_request)

    # Force system write failures during execution cycles
    mock_writer_class.side_effect = RuntimeError("Disk IO Error writing components")

    with qtbot.wait_signal(worker.frames_export_finished) as blocker:
        worker.execute_frames_export("broken_path/export.mp4")

    result = blocker.args[0]
    assert result.success is False
    assert "Disk IO Error" in result.message
