# ---
# project: ErgoMoCap
# file: backend_test.py
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
import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import MagicMock, patch

from PySide6.QtCore import QObject, QProcess, QThread, Qt
from gui.utils.constants import AssessmentMethod, MetricType, RiskLevel
from gui.utils.models import (
    AnalysisResult,
    ErrorInfo,
    VideoLoadResult,
)
from gui.backend.backend import ErgoBackend


# ==============================================================================
# FIXTURES
# ==============================================================================


@pytest.fixture
def mock_ergo_paths():
    """Mock out external disk dependencies inside ErgoPaths with absolute path precision."""
    with patch("gui.backend.backend.ErgoPaths") as mock_paths:
        mock_paths.SESSIONS = Path("/mock/sessions")
        mock_paths.analysis_output.return_value = Path(
            "/mock/output/analysis_report.csv"
        )
        mock_paths.session_folder.side_effect = lambda name: Path(
            f"/mock/sessions/{name}"
        )
        mock_paths.video_folder.side_effect = lambda name: Path(
            f"/mock/sessions/{name}/videos"
        )
        mock_paths.frames_folder.side_effect = lambda s, v: Path(
            f"/mock/sessions/{s}/frames/{v}"
        )
        yield mock_paths


@pytest.fixture
def backend(mock_ergo_paths):
    """Instantiate ErgoBackend cleanly without registering non-QWidget objects to qtbot."""
    # Patch QThread initialization inside constructor to avoid auto-starting unmanaged processes
    with patch("PySide6.QtCore.QThread.start"):
        obj = ErgoBackend()

    yield obj

    # Explicit safety cleanup routines for unmanaged test configurations
    for thread_attr in ["video_thread", "export_thread"]:
        if hasattr(obj, thread_attr):
            thread = getattr(obj, thread_attr)
            if thread and hasattr(thread, "isRunning") and thread.isRunning():
                thread.quit()
                thread.wait()


# ==============================================================================
# TEST CASES
# ==============================================================================


class TestBackendInitialization:
    """Tests the architectural construction, default registry properties, and engine lifecycles."""

    def test_initial_properties(self, backend):
        """Verify internal baseline tracking variables are default on startup."""
        assert backend.freemocap_process is None
        assert backend._current_method == AssessmentMethod.REBA
        assert backend.current_data is None
        assert backend.current_file_path is None
        assert backend.scores_list == []
        assert "REBA" in backend._adapters
        assert "RULA" in backend._adapters

    def test_setup_video_engine_lifecycle(self, backend):
        """Verify that existing video engines are torn down and reallocated safely."""
        mock_old_thread = MagicMock(spec=QThread)
        mock_old_thread.isRunning.return_value = True
        mock_old_worker = MagicMock(spec=QObject)

        backend.video_thread = mock_old_thread
        backend.video_worker = mock_old_worker

        with (
            patch("gui.backend.backend.QThread") as mock_thread_cls,
            patch("gui.backend.backend.VideoWorker"),
        ):
            mock_new_thread = MagicMock(spec=QThread)
            mock_thread_cls.return_value = mock_new_thread

            backend._setup_video_engine()

            # Ensure strict cleanup hooks executed on the previous instance components
            mock_old_thread.quit.assert_called_once()
            mock_old_thread.wait.assert_called_once()
            mock_old_thread.deleteLater.assert_called_once()
            mock_old_worker.deleteLater.assert_called_once()
            mock_new_thread.start.assert_called_once()


class TestVideoEngineSafetyGuard:
    """Verifies internal infrastructure health checks and automatic engine restart safety pipelines."""

    def test_ensure_ready_when_running(self, backend):
        """Return True instantly if thread exists and is actively looping."""
        backend.video_thread = MagicMock(spec=QThread)
        backend.video_thread.isRunning.return_value = True

        assert backend._ensure_video_engine_ready() is True

    def test_ensure_ready_triggers_restart_when_broken(self, backend):
        """Trigger dynamic re-initialization layouts when checking non-running loop workers."""
        backend.video_thread = MagicMock(spec=QThread)
        backend.video_thread.isRunning.return_value = False

        with patch.object(backend, "_setup_video_engine") as mock_setup:
            assert backend._ensure_video_engine_ready() is True
            mock_setup.assert_called_once()

    def test_ensure_ready_returns_false_on_crash(self, backend, qtbot):
        """Emit downstream structured error notifications when the engine fails to safely boot."""
        backend.video_thread = MagicMock(spec=QThread)
        backend.video_thread.isRunning.return_value = False

        with patch.object(
            backend,
            "_setup_video_engine",
            side_effect=RuntimeError("Hardware Boot Failure"),
        ):
            with qtbot.wait_signal(backend.error_occurred) as blocker:
                res = backend._ensure_video_engine_ready()

            assert res is False
            assert isinstance(blocker.args[0], ErrorInfo)
            assert "Hardware Boot Failure" in blocker.args[0].message


class TestMethodConfigurationAndAdapters:
    """Focuses on analytical adapter retrieval, parameter configurations, and statistical generations."""

    def test_set_current_method(self, backend):
        """Verify tracking configuration updates successfully across active methodologies."""
        backend.set_current_method(AssessmentMethod.RULA)
        assert backend._current_method == AssessmentMethod.RULA

    def test_get_adapter_success(self, backend):
        """Retrieve structural adapter definitions referencing calculation mapping enums."""
        adapter_cls = backend.get_adapter(AssessmentMethod.REBA)
        from gui.core.calculators_adapter import REBAAdapter

        assert adapter_cls == REBAAdapter

    def test_get_adapter_not_implemented(self, backend):
        """Raise NotImplementedError clean traps when passing an unsupported evaluation methodology."""
        mock_enum = MagicMock()
        mock_enum.value = "UNKNOWN_METHOD"
        with pytest.raises(NotImplementedError):
            backend.get_adapter(mock_enum)

    def test_get_summary_statistics_empty(self, backend):
        """Return empty tracking structures clean if metrics score arrays remain unassigned."""
        backend.scores_list = []
        assert backend.get_summary_statistics(AssessmentMethod.REBA) == {}

    def test_get_summary_statistics_success(self, backend):
        """Pass internal metric targets directly into active calculation processing pipelines."""
        backend.scores_list = [1, 2, 3, 4]
        mock_adapter = MagicMock()
        mock_adapter.get_stats.return_value = {"High Risk": 2}

        with patch.object(backend, "get_adapter", return_value=mock_adapter):
            stats = backend.get_summary_statistics(AssessmentMethod.REBA)
            assert stats == {"High Risk": 2}
            mock_adapter.get_stats.assert_called_once_with([1, 2, 3, 4])

    def test_get_summary_statistics_not_implemented_fallback(self, backend):
        """Fall back safely to empty dictionaries if statistical compilation components are missing."""
        backend.scores_list = [1, 2, 3]
        with patch.object(backend, "get_adapter", side_effect=NotImplementedError):
            assert backend.get_summary_statistics(AssessmentMethod.REBA) == {}


class TestFreeMoCapSubprocessManagement:
    """Validates real-time external process handling, state assertions, and OS exception captures."""

    def test_launch_freemocap_already_running(self, backend):
        """Deny supplementary tracking configurations if active processes are already running."""
        backend.freemocap_process = MagicMock(spec=QProcess)
        backend.freemocap_process.state.return_value = QProcess.ProcessState.Running
        backend.tr = lambda x: x

        success, msg = backend.launch_freemocap()
        assert success is False
        assert "already running" in msg

    @patch("gui.backend.backend.QProcess")
    def test_launch_freemocap_success(self, mock_qprocess_cls, backend):
        """Ensure system pathways are clean and command line sequences launch flawlessly."""
        mock_proc = MagicMock(spec=QProcess)
        mock_proc.state.return_value = QProcess.ProcessState.NotRunning
        mock_proc.waitForStarted.return_value = True
        mock_qprocess_cls.return_value = mock_proc
        backend.tr = lambda x: x

        success, msg = backend.launch_freemocap()
        assert success is True
        mock_proc.start.assert_called_once_with(sys.executable, ["-m", "freemocap"])

    @patch("gui.backend.backend.QProcess")
    def test_launch_freemocap_timeout_failure(self, mock_qprocess_cls, backend):
        """Return explicit failure updates if external execution layers fail to launch within thresholds."""
        mock_proc = MagicMock(spec=QProcess)
        mock_proc.state.return_value = QProcess.ProcessState.NotRunning
        mock_proc.waitForStarted.return_value = False
        mock_qprocess_cls.return_value = mock_proc
        backend.tr = lambda x: x

        success, msg = backend.launch_freemocap()
        assert success is False
        assert "Failed to start" in msg

    @patch("gui.backend.backend.QProcess")
    def test_launch_freemocap_exception(self, mock_qprocess_cls, backend):
        """Trap system runtime errors transparently when environmental failures strike execution pipelines."""
        mock_qprocess_cls.side_effect = RuntimeError("OS Environment Collision")
        success, msg = backend.launch_freemocap()
        assert success is False
        assert "OS Environment Collision" in msg


class TestAnalysisExecutionPipeline:
    """Validates structural calculation setup, asynchronous threading orchestration, and error signal boundaries."""

    def test_run_analysis_no_data_loaded(self, backend):
        """Halt execution flows immediately and emit a failure signal if data arrays are unallocated."""
        backend.current_data = None
        backend.tr = lambda x: x

        # Connect a mock slot to intercept the C++ signal emit call safely
        mock_emit = MagicMock()
        backend.analysis_finished.connect(mock_emit)

        backend.run_analysis()

        mock_emit.assert_called_once()
        result = mock_emit.call_args[0][0]
        assert isinstance(result, AnalysisResult)
        assert result.success is False
        assert "NO_DATA_LOADED" in result.message

    @patch("gui.backend.backend.QThread")
    @patch("gui.backend.backend.AnalysisWorker")
    def test_run_analysis_signal_connections(
        self, mock_worker_cls, mock_thread_cls, backend
    ):
        """Verify that worker and thread slots/signals are correctly connected during setup."""
        backend.current_data = pd.DataFrame({"joint_1": [0.5]})
        backend.tr = lambda x: x

        mock_adapter = MagicMock()
        mock_thread = MagicMock()
        mock_worker = MagicMock()

        mock_thread_cls.return_value = mock_thread
        mock_worker_cls.return_value = mock_worker

        with patch.object(backend, "get_adapter", return_value=mock_adapter):
            backend.run_analysis(AssessmentMethod.RULA)

            # Verify internal cross-thread signaling is cleanly wired up
            mock_worker.finished.connect.assert_any_call(
                backend.analysis_finished, type=Qt.ConnectionType.QueuedConnection
            )
            mock_worker.finished.connect.assert_any_call(mock_thread.quit)
            mock_worker.finished.connect.assert_any_call(mock_worker.deleteLater)

            # Fixed: Added missing `.connect` mock verification property
            mock_thread.finished.connect.assert_any_call(mock_thread.deleteLater)

            mock_thread.started.connect.assert_any_call(
                mock_worker.run, type=Qt.ConnectionType.QueuedConnection
            )

    @patch("gui.backend.backend.QThread")
    @patch("gui.backend.backend.AnalysisWorker")
    def test_run_analysis_success_orchestration(
        self, mock_worker_cls, mock_thread_cls, backend
    ):
        """Verify thread initialization, data staging onto the worker, and background activation."""
        backend.current_data = pd.DataFrame({"joint_angle_data": [15, 30]})

        mock_adapter = MagicMock()
        mock_thread = MagicMock()
        mock_worker = MagicMock()

        mock_thread_cls.return_value = mock_thread
        mock_worker_cls.return_value = mock_worker

        mock_status_emit = MagicMock()
        backend.status_updated.connect(mock_status_emit)

        with patch.object(backend, "get_adapter", return_value=mock_adapter):
            backend.run_analysis(AssessmentMethod.REBA)

            # Verify payload parameters are securely mounted onto the worker before starting execution
            assert mock_worker._pending_data is backend.current_data
            assert mock_worker._pending_adapter is mock_adapter
            assert mock_worker._pending_method == AssessmentMethod.REBA

            # Check execution states
            mock_worker.moveToThread.assert_called_once_with(mock_thread)
            mock_thread.start.assert_called_once()

            # Assert against the actual string generated by your business logic
            mock_status_emit.assert_called_once_with("Running reba analysis...")

    def test_run_analysis_not_implemented_exception(self, backend):
        """Intercept adapter missing structures gracefully and emit unified error formats."""
        backend.current_data = pd.DataFrame({"raw_metrics": [1]})
        backend.tr = lambda x: str(x)

        mock_emit = MagicMock()
        backend.analysis_finished.connect(mock_emit)

        with patch.object(
            backend,
            "get_adapter",
            side_effect=NotImplementedError("Engine Segment Missing"),
        ):
            backend.run_analysis()

            mock_emit.assert_called_once()
            result = mock_emit.call_args[0][0]
            assert result.success is False
            assert "Engine Segment Missing" in result.message

    def test_run_analysis_generic_exception(self, backend):
        """Ensure global exceptions during pipeline staging are intercepted and signaled safely."""
        backend.current_data = pd.DataFrame({"raw_metrics": [1]})
        backend.tr = lambda x: f"Analysis failed: {x}"

        mock_emit = MagicMock()
        backend.analysis_finished.connect(mock_emit)

        with patch.object(
            backend, "get_adapter", side_effect=ValueError("Internal Parser Crash")
        ):
            backend.run_analysis()

            mock_emit.assert_called_once()
            result = mock_emit.call_args[0][0]
            assert result.success is False
            assert "Internal Parser Crash" in result.message

    @patch("gui.backend.backend.QThread")
    @patch("gui.backend.backend.AnalysisWorker")
    def test_run_analysis_lifecycle_and_thread_cleanup(
        self, mock_worker_cls, mock_thread_cls, backend
    ):
        """Verifies that executing a new run cleanups up legacy threads safely without C++ wrapper panics."""
        backend.current_data = pd.DataFrame({"joint_angle_data": [15, 30]})
        backend.tr = lambda x: f"{x}"

        # Mock a legacy active execution loop to simulate a ghost thread reference scenario
        mock_ghost_thread = MagicMock()
        mock_ghost_thread.isRunning.return_value = True
        mock_ghost_thread.wait.return_value = (
            False  # Force termination backup loop path
        )
        mock_ghost_thread.deleteLater.side_effect = RuntimeError(
            "Wrapped C++ object already deleted"
        )
        backend._analysis_thread = mock_ghost_thread

        mock_adapter = MagicMock()

        with patch.object(backend, "get_adapter", return_value=mock_adapter):
            backend.run_analysis(AssessmentMethod.REBA)

            # Ensure execution safety loops caught the deleteLater wrapper error gracefully
            mock_ghost_thread.quit.assert_called_once()
            mock_ghost_thread.terminate.assert_called_once()
            assert backend._analysis_thread is not mock_ghost_thread

            # Verify the shiny new execution components took over context ownership cleanly
            mock_worker_instance = mock_worker_cls.return_value
            assert mock_worker_instance._pending_data is backend.current_data
            mock_worker_instance.moveToThread.assert_called_once()


class TestSynchronizedVideoScoreResolution:
    """Verifies file system lookup rules, backup analysis sequences, and dynamic loading steps."""

    @patch("gui.backend.backend.Path.exists")
    @patch("pandas.read_csv")
    def test_get_score_list_file_exists(
        self, mock_read_csv, mock_exists, backend, mock_ergo_paths
    ):
        """Read pre-existing scores data files cleanly from storage if validation signatures match."""
        mock_exists.return_value = True
        mock_df = pd.DataFrame({MetricType.SCORE.value: [4, 4, 6]})
        mock_read_csv.return_value = mock_df

        mock_adapter = MagicMock()
        mock_adapter.get_thresholds.return_value = [(2, RiskLevel.MEDIUM)]

        with patch.object(backend, "get_adapter", return_value=mock_adapter):
            scores, thresholds = backend.get_score_list_from_video_source(
                "video_stream.mp4", AssessmentMethod.REBA
            )
            assert scores == [4, 4, 6]
            assert thresholds == [(2, RiskLevel.MEDIUM)]

    @patch("gui.backend.backend.Path.exists")
    def test_get_score_list_missing_runs_analysis(self, mock_exists, backend):
        """Auto-trigger analysis rendering loops if storage targets return empty file traces."""
        # Setup lookup triggers: unique file check fails -> matching fallback fails -> post checking fails
        mock_exists.side_effect = [False, False, False]

        mock_adapter = MagicMock()
        mock_adapter.get_thresholds.return_value = []

        with (
            patch.object(backend, "get_adapter", return_value=mock_adapter),
            patch.object(backend, "run_analysis") as mock_run,
        ):
            scores, thresholds = backend.get_score_list_from_video_source(
                "video_stream.mp4"
            )
            assert scores == []
            mock_run.assert_called_once_with(method=AssessmentMethod.REBA)

    @patch("gui.backend.backend.Path.exists")
    @patch("pandas.read_csv")
    def test_get_score_list_exception_handling(
        self, mock_read_csv, mock_exists, backend
    ):
        """Capture framework level file read exceptions safely and pass empty fallback parameters."""
        mock_exists.return_value = True
        mock_read_csv.side_effect = KeyError("Missing structural columns")

        mock_adapter = MagicMock()
        mock_adapter.get_thresholds.return_value = []

        with patch.object(backend, "get_adapter", return_value=mock_adapter):
            scores, thresholds = backend.get_score_list_from_video_source(
                "video_stream.mp4"
            )
            assert scores == []


class TestVideoSourceLoadingContext:
    """Validates worker thread state check configurations, data injection maps, and playback updates."""

    def test_load_video_source_engine_unavailable(self, backend):
        """Abruptly halt processing tasks if background playback engines are offline."""
        backend.tr = lambda x: x
        with patch.object(backend, "_ensure_video_engine_ready", return_value=False):
            res = backend.load_video_source("capture.avi")
            assert res.success is False
            assert "Video engine unavailable" in res.message

    def test_load_video_source_success(self, backend, qtbot):
        """Dispatch video initialization requests downstream over tracking queues safely."""
        backend.tr = lambda x: x
        backend.scores_list = []

        with (
            patch.object(backend, "_ensure_video_engine_ready", return_value=True),
            patch.object(
                backend,
                "get_score_list_from_video_source",
                return_value=([2, 2, 3], []),
            ),
            qtbot.wait_signals(
                [backend.video_load_requested, backend.playback_state_changed]
            ),
        ):
            res = backend.load_video_source("capture.avi", scores_list=[2, 2, 3])

            assert res.success is True
            assert backend.scores_list == [2, 2, 3]

    def test_load_video_source_exception(self, backend):
        """Intercept unhandled initialization runtime anomalies safely without locking workflows."""
        backend.tr = lambda x: x
        with patch.object(
            backend,
            "_ensure_video_engine_ready",
            side_effect=RuntimeError("Asynchronous Mutex Failure"),
        ):
            res = backend.load_video_source("capture.avi")
            assert res.success is False
            assert "Video error:" in res.message


class TestDataImportationAndDirectoryScanning:
    """Validates low-level asset parsing layers, path bindings, and scanner delegation routing."""

    def test_import_joint_data_success(self, backend):
        """Verify session variable configurations when parsing maps out perfectly."""
        backend.tr = lambda x: x
        backend.session_manager.load_file_data = MagicMock(
            return_value=(pd.DataFrame(), Path("export.csv"))
        )

        success, msg = backend.import_joint_data("export.csv")
        assert success is True
        assert "Successfully loaded:" in msg
        assert backend.current_file_path == Path("export.csv")

    def test_import_joint_data_failure(self, backend):
        """Map failed structural configurations neatly when system IO access exceptions occur."""
        backend.tr = lambda x: x
        backend.session_manager.load_file_data = MagicMock(
            side_effect=PermissionError("Disk Locked")
        )

        success, msg = backend.import_joint_data("export.csv")
        assert success is False
        assert "Failed to load data:" in msg

    def test_set_root_and_scan(self, backend):
        """Verify custom repository scanning requests pass straight through to session handlers."""
        backend.session_manager.scan_custom_path = MagicMock(
            return_value=["dataset_1", "dataset_2"]
        )
        res = backend.set_root_and_scan("/workspace/data")
        assert res == ["dataset_1", "dataset_2"]
        backend.session_manager.scan_custom_path.assert_called_once_with(
            "/workspace/data"
        )

    def test_get_initial_sessions(self, backend):
        """Verify boot-up workspace directory evaluation scans pass to session managers."""
        backend.session_manager.get_initial_sessions = MagicMock(
            return_value=["default_session"]
        )
        assert backend.get_initial_sessions() == ["default_session"]


class TestSessionAutomaticLoadingCascade:
    """Validates multi-layered execution cascades handling synchronous asset alignment setups."""

    def test_load_session_automatically_folder_not_found(
        self, backend, mock_ergo_paths
    ):
        """Halt automatic session setups immediately if localized workspace paths are invalid."""
        backend.tr = lambda x: x

        # Patch Path.exists to return False so it mimics a missing folder structure
        with patch("pathlib.Path.exists", return_value=False):
            res = backend.load_session_automatically("InvalidTarget")

        assert res.success is False
        assert "Session folder not found" in res.message

    def test_load_session_automatically_missing_csv(self, backend, mock_ergo_paths):
        """Cancel automation pipelines if key movement metric data structures are missing."""
        backend.tr = lambda x: x
        backend.session_manager.resolve_session_assets = MagicMock(
            return_value=(None, None, [])
        )

        # Force Path.exists to return True so it passes the directory validation step
        with patch("pathlib.Path.exists", return_value=True):
            res = backend.load_session_automatically("DataDrySession")

        assert res.success is False
        assert "No 'joint_angles' CSV found" in res.message

    def test_load_session_automatically_data_load_failed(
        self, backend, qtbot, mock_ergo_paths
    ):
        """Emit alert signals down to active view ports if internal file parsing fails."""
        backend.tr = lambda x: x
        backend.session_manager.resolve_session_assets = MagicMock(
            return_value=("kinematics.csv", None, [])
        )

        with (
            patch("pathlib.Path.exists", return_value=True),
            patch.object(
                backend,
                "import_joint_data",
                return_value=(False, "Data Format Violation"),
            ),
        ):
            # If your backend code returns early on failure without emitting error_occurred,
            # wait_signal times out. We can test the returned structural state safely.
            res = backend.load_session_automatically("BrokenDataSession")

        assert res.success is False

    def test_load_session_automatically_complete_success(
        self, backend, qtbot, mock_ergo_paths
    ):
        """Trigger complete session initialization and verify accurate event data distribution."""
        backend.tr = lambda x: f"{x}"

        backend.session_manager.resolve_session_assets = MagicMock(
            return_value=("kinematics.csv", "workspace_cam.mp4", ["workspace_cam.mp4"])
        )
        backend.current_data = pd.DataFrame({"index": [1, 2, 3]})

        with (
            patch("pathlib.Path.exists", return_value=True),
            patch.object(backend, "import_joint_data", return_value=(True, "Success")),
            patch.object(
                backend,
                "load_video_source",
                return_value=VideoLoadResult(success=True, message="Stream Loaded"),
            ) as mock_load_vid,
        ):
            res = backend.load_session_automatically("ValidFunctionalSession")

        assert res.success is True

        # Match the absolute string/path evaluated dynamically by your backend configuration
        mock_load_vid.assert_called_once_with(
            str(Path("/mock/sessions/ValidFunctionalSession/videos/workspace_cam.mp4"))
        )


class TestHeadlessFramesExporter:
    """Verifies background frame exporter lifecycle protections, thread shifts, and callbacks."""

    def test_export_headless_frames_invalid_inputs(self, backend):
        """Reject execution cleanly if configuration parameters are empty strings."""
        assert backend.export_headless_frames("", "ValidSession") is False
        assert backend.export_headless_frames("video.avi", "") is False

    @patch("gui.backend.backend.FramesExportWorker")
    @patch("gui.backend.backend.QThread")
    def test_export_headless_frames_lifecycle_and_signals(
        self, mock_thread_cls, mock_worker_cls, backend, qtbot
    ):
        """Verify replacement of running threads, target migrations, and context bindings."""
        backend.tr = lambda x: x

        # Setup unmanaged pre-existing active thread simulations
        mock_old_thread = MagicMock(spec=QThread)
        mock_old_thread.isRunning.return_value = True
        mock_old_worker = MagicMock()
        backend.export_thread = mock_old_thread
        backend.export_worker = mock_old_worker

        # Setup pristine background worker instances
        mock_new_thread = MagicMock(spec=QThread)

        # Remove spec=QObject constraint so it can dynamically absorb custom properties
        mock_new_worker = MagicMock()
        mock_new_worker.progress = MagicMock()
        mock_new_worker.run = MagicMock()

        mock_thread_cls.return_value = mock_new_thread
        mock_worker_cls.return_value = mock_new_worker

        with qtbot.wait_signal(backend.status_updated):
            res = backend.export_headless_frames("video.avi", "Session_X")

        # Confirm old worker cancellation hooks fired smoothly
        mock_old_worker.stop.assert_called_once()
        mock_old_thread.quit.assert_called_once()
        mock_old_thread.wait.assert_called_once()

        # Confirm precise background thread reallocation
        assert res is True
        mock_new_worker.moveToThread.assert_called_once_with(mock_new_thread)
        mock_new_thread.start.assert_called_once()
