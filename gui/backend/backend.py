# ---
# project: ErgoMoCap
# file: backend.py
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
ErgoMoCap: Backend Controller
------------------------------
Central Orchestration and Application Logic Module.

This module implements the `ErgoBackend` class, which serves as the primary
controller for the ErgoMoCap project. It coordinates asynchronous operations
between the [SessionManager][gui.core.session_manager.SessionManager], the
[AnalysisEngine][gui.core.analysis_engine.AnalysisEngine], and the
[VideoWorker][gui.workers.video_worker.VideoWorker].

The backend manages the lifecycle of ergonomic assessments, from launching
external FreeMoCap processes to executing multi-method calculations and
managing synchronized video playback.

Key Features:
    * Centralized registry for ergonomic assessment adapters (RULA, REBA, etc.).
    * Subprocess management for external FreeMoCap integration.
    * Automated session asset resolution and data importation.
    * Signal-based communication for real-time GUI updates and error handling.
"""

import subprocess
import sys

from pathlib import Path
from PySide6.QtCore import QObject, Qt, Signal, QThread, Slot
import pandas as pd

from gui.utils.app_paths import ErgoPaths
from gui.utils.constants import AssessmentMethod, MetricType, RiskLevel

from gui.core.analysis_engine import AnalysisEngine
from gui.core.session_manager import SessionManager
from gui.utils.models import (
    AnalysisResult,
    ErrorInfo,
    FrameData,
    PlaybackState,
    SessionData,
    VideoControl,
    VideoLoadRequest,
    VideoLoadResult,
    VideoPosition,
)
from gui.workers.analysis_worker import AnalysisWorker
from gui.workers.frames_export_worker import FramesExportWorker
from gui.workers.video_worker import VideoWorker
from gui.core.calculators_adapter import (
    BaseErgoAdapter,
    REBAAdapter,
    RULAAdapter,
    NIOSHAdapter,
    OCRAAdapter,
    EWASAdapter,
    SNOOKAdapter,
)

from gui.utils.logger import logger


class ErgoBackend(QObject):
    """
    The central controller for the ErgoMoCap application.

    Coordinates data loading via [SessionManager][gui.core.session_manager.SessionManager],
    triggers ergonomic calculations via the [AnalysisEngine][gui.core.analysis_engine.AnalysisEngine]
    using specialized adapters, and manages the [VideoWorker][gui.workers.video_worker.VideoWorker].

    Attributes:
        frame_ready (Signal): Signal emitted with a [FrameData][gui.utils.models.FrameData] object containing rendering matrices and calculations metadata.
        position_changed (Signal): Signal emitted with a [VideoPosition][gui.utils.models.VideoPosition] object tracking playback counters.
        session_loaded (Signal): Signal emitted with a [SessionData][gui.utils.models.SessionData] object providing resolved session context.
        error_occurred (Signal): Signal emitted with an [ErrorInfo][gui.utils.models.ErrorInfo] object when processing crashes.
        status_updated (Signal): Signal emitted with a `str` displaying application progress strings in the visual status bar.
        playback_state_changed (Signal): Signal emitted with a `bool` representing whether a video ticker is active.
        video_load_requested (Signal): Signal emitted with a [VideoLoadRequest][gui.utils.models.VideoLoadRequest] to initialize a resource context.
        video_control_requested (Signal): Signal emitted with a [VideoControl][gui.utils.models.VideoControl] object altering video worker tickers.
        analysis_finished (Signal): Signal Emitted with an [AnalysisResult][gui.utils.models.AnalysisResult] object with ergonomic analysis results.
        freemocap_process (QProcess | None): Running instance handler for the external subprocess, or `None` if inactive.
        engine (AnalysisEngine): The core computation engine instance [AnalysisEngine][gui.core.analysis_engine.AnalysisEngine].
        session_manager (SessionManager): The asset parsing and disk lookup entity [SessionManager][gui.core.session_manager.SessionManager].
        video_thread (QThread): Dedicated tracking execution runtime loop processing video file buffers.
        video_worker (VideoWorker): Background operational worker parsing video stream indices.
        current_data (pandas.DataFrame | None): The currently active dataset metrics container, or `None` if completely empty.
        current_file_path (Path | None): Absolute filesystem location reference path to the loaded matrix data asset.
        scores_list (list[int]): Sequential array structure holding processed single frame evaluation integers.

    Methods:
        _setup_video_engine: Initialize or re-initialize the video worker thread infrastructure.
        _ensure_video_engine_ready: Ensure the video thread is running; restart if needed.
        set_current_method: Set the internal assessment protocol target selection configuration.
        launch_freemocap: Launches the external FreeMoCap GUI as a subprocess.
        get_adapter: Retrieves the adapter class for a specific ergonomic method.
        get_summary_statistics: Calculates frequency distribution of risk levels for the current scores.
        run_analysis: The main dispatching logic for ergonomic analysis.
        get_score_list_from_video_source: Retrieves synchronized scores matching the specific video context.
        load_video_source: Initializes a new video thread context for the given file path.
        import_joint_data: Loads CSV or NPY joint data into the backend via the session manager.
        set_root_and_scan: Scans a custom directory for session folders.
        get_initial_sessions: Scan the default sessions directory for available session folders.
        load_session_automatically: Locates and loads all assets for a session (Data + Video).
        export_headless_frames: Triggers background worker execution frames assembly writing out files.
    """

    frame_ready = Signal(FrameData)

    position_changed = Signal(VideoPosition)

    session_loaded = Signal(SessionData)

    error_occurred = Signal(ErrorInfo)

    status_updated = Signal(str)

    playback_state_changed = Signal(bool)

    video_load_requested = Signal(VideoLoadRequest)
    video_control_requested = Signal(VideoControl)

    analysis_finished = Signal(AnalysisResult)

    def __init__(self) -> None:
        """
        Initializes the `ErgoBackend` controller and its core components.

        Sets up the internal project structure paths, instantiates the [AnalysisEngine][gui.core.analysis_engine.AnalysisEngine]
        and [SessionManager][gui.core.session_manager.SessionManager], and registers the mapping
        of ergonomic assessment methods to their respective adapter classes.

        The constructor establishes the default sessions directory at `freemocap_data/recording_sessions`
        relative to the application root.

        Returns:
            None: The return value is always None.
        """
        super().__init__()
        self.freemocap_process = None
        self._current_method: AssessmentMethod = AssessmentMethod.REBA
        self.current_data = None
        self.current_file_path = None
        self.scores_list = []

        self.engine = AnalysisEngine()
        self.session_manager = SessionManager(ErgoPaths.SESSIONS)

        self._adapters = {
            "REBA": REBAAdapter,
            "RULA": RULAAdapter,
            "OCRA": OCRAAdapter,
            "EWAS": EWASAdapter,
            "NIOSH": NIOSHAdapter,
            "SNOOK": SNOOKAdapter,
        }

        self._setup_video_engine()

    def _setup_video_engine(self) -> None:
        """
        Initialize or re-initialize the video worker thread infrastructure.

        Safely handles the lifecycle deletion of pre-existing execution context pipelines,
        creates isolated instances, links cross-thread execution hooks, and binds worker signals.

        Returns:
            None (None): Reconstructs internal thread contexts.
        """

        if hasattr(self, "video_thread") and self.video_thread:
            if self.video_thread.isRunning():
                self.video_thread.quit()
                self.video_thread.wait()
            self.video_thread.deleteLater()

        if hasattr(self, "video_worker") and self.video_worker:
            self.video_worker.deleteLater()

        # Create fresh instances
        self.video_thread = QThread()
        self.video_worker = VideoWorker()
        self.video_worker.moveToThread(self.video_thread)

        # Re-establish signal/slot connections
        self.video_thread.started.connect(self.video_worker.init_timer)

        self.video_load_requested.connect(
            self.video_worker.initialize_video, type=Qt.ConnectionType.QueuedConnection
        )

        self.video_control_requested.connect(self.video_worker.handle_video_control)

        # Proxy worker signals to backend
        self.video_worker.frame_ready.connect(self.frame_ready)
        self.video_worker.position_changed.connect(self.position_changed)
        self.video_thread.finished.connect(self.video_worker.cleanup)

        # Start the thread
        self.video_thread.start()
        logger.debug("Video engine thread started")

    def _ensure_video_engine_ready(self) -> bool:
        """
        Ensure the video thread is running; restart if needed.

        Returns:
            bool (bool): `True` if active or successfully restarted, `False` if thread boot failed.
        """
        if not hasattr(self, "video_thread") or not self.video_thread.isRunning():
            logger.warning("Video thread not running. Re-initializing")
            try:
                self._setup_video_engine()
                return True
            except Exception as e:
                logger.error(f"Failed to restart video engine: {e}")
                self.error_occurred.emit(
                    ErrorInfo(title="Video engine restart failed:", message=f"{e}")
                )
                return False
        return True

    def set_current_method(self, new_method: AssessmentMethod) -> None:
        """
        Set the internal assessment protocol target selection configuration.

        Args:
            new_method (AssessmentMethod): The targeting enumeration choice selection parameter.

        Returns:
            None (None): Updates the internal monitoring option property field.
        """
        self._current_method = new_method

    def launch_freemocap(self) -> tuple[bool, str]:
        """Launches the external FreeMoCap GUI as an isolated subprocess,
        by redispatching the execution path back to the primary compiled executable.

        Returns:
            tuple[bool, str]: A tuple containing (success_status, status_message).
        """
        if (
            hasattr(self, "freemocap_process")
            and self.freemocap_process
            and self.freemocap_process.poll() is None
        ):
            return False, self.tr("FreeMoCap is already running.")

        try:
            if getattr(sys, "frozen", False):
                # --- PYINSTALLER EXE MODE ---
                # Call your own ErgoMoCap.exe with a custom routing switch
                args = [sys.executable, "--run-freemocap-gui"]
            else:
                # --- VS CODE DEVELOPMENT MODE ---
                args = [sys.executable, "-m", "freemocap"]

            creation_flags = 0
            if sys.platform == "win32":
                creation_flags = subprocess.CREATE_NO_WINDOW

            # Fire the subprocess using the self-contained interpreter context
            self.freemocap_process = subprocess.Popen(
                args, creationflags=creation_flags
            )

            return True, self.tr(
                "FreeMoCap is starting successfully. Please wait until it opens."
            )

        except Exception as e:
            return False, str(e)

    def get_adapter(self, method: AssessmentMethod) -> BaseErgoAdapter:
        """
        Retrieves the adapter class for a specific ergonomic method.

        Args:
            method (AssessmentMethod): The key string of the assessment method (e.g., 'REBA', 'RULA').

        Returns:
            BaseErgoAdapter: The corresponding [BaseErgoAdapter][gui.core.calculators_adapter.BaseErgoAdapter] subclass.

        Raises:
            NotImplementedError: If the requested method key is not found in the registry.
        """
        adapter = self._adapters.get(method.value.upper())
        if not adapter:
            raise NotImplementedError(f"{method} integration in progress.")
        return adapter

    def get_summary_statistics(
        self, method: AssessmentMethod = AssessmentMethod.REBA
    ) -> dict[str, int]:
        """
        Calculates frequency distribution of risk levels for the current scores.

        Args:
            method (AssessmentMethod): Threshold protocol mapping definitions engine choice. Defaults to [AssessmentMethod.REBA][gui.utils.constants.AssessmentMethod].

        Returns:
            dict[str, int] (dict): A frequency counts dictionary lookup mapping text evaluation string tags to numerical frame integers.
        """
        if (
            not self.scores_list
        ):  # TODO do better handling here and signal error to frontend
            return {}
        try:
            adapter = self.get_adapter(method)
            return adapter.get_stats(self.scores_list)
        except NotImplementedError:
            return {}

    def run_analysis(self, method: AssessmentMethod = AssessmentMethod.REBA) -> None:
        """Dispatches the ergonomic analysis process.

        Selects the appropriate adapter, routes motion capture data through the calculation
        sequence, and delegates the heavy computation to a background worker thread to
        keep the UI responsive.

        Args:
            method (AssessmentMethod): The assessment method to execute. Defaults to
                [`AssessmentMethod.REBA`][gui.utils.constants.AssessmentMethod].
        """
        if self.current_data is None:
            logger.warning("Analysis attempted with no data loaded.")
            self.analysis_finished.emit(
                AnalysisResult(
                    success=False, message=self.tr("NO_DATA_LOADED"), output_path=None
                )
            )
            return

        try:
            adapter = self.get_adapter(method)

            if hasattr(self, "_analysis_thread") and self._analysis_thread is not None:
                try:
                    if self._analysis_thread.isRunning():
                        self._analysis_thread.quit()
                        if not self._analysis_thread.wait(1000):
                            self._analysis_thread.terminate()
                            self._analysis_thread.wait()
                    self._analysis_thread.deleteLater()
                except RuntimeError:
                    pass
                finally:
                    self._analysis_thread = None

            if hasattr(self, "_analysis_worker") and self._analysis_worker is not None:
                try:
                    self._analysis_worker.deleteLater()
                except RuntimeError:
                    pass
                finally:
                    self._analysis_worker = None

            analysis_thread = QThread()
            analysis_worker = AnalysisWorker()

            # Store data as attributes before moving to thread to avoid Qt serialization issues
            analysis_worker._pending_data = self.current_data
            analysis_worker._pending_adapter = adapter
            analysis_worker._pending_method = method

            analysis_worker.moveToThread(analysis_thread)

            analysis_worker.finished.connect(
                self.analysis_finished,
                type=Qt.ConnectionType.QueuedConnection,
            )

            analysis_worker.finished.connect(analysis_thread.quit)
            analysis_worker.finished.connect(analysis_worker.deleteLater)
            analysis_thread.finished.connect(analysis_thread.deleteLater)

            self._analysis_thread = analysis_thread
            self._analysis_worker = analysis_worker

            analysis_thread.started.connect(
                analysis_worker.run,
                type=Qt.ConnectionType.QueuedConnection,
            )

            self.status_updated.emit(
                self.tr("Running {} analysis...").format(method.value)
            )
            analysis_thread.start()

        except NotImplementedError as e:
            self.analysis_finished.emit(
                AnalysisResult(success=False, message=self.tr(str(e)), output_path=None)
            )
        except Exception as e:
            logger.error(f"Analysis setup failed: {e}", exc_info=True)
            self.analysis_finished.emit(
                AnalysisResult(
                    success=False,
                    message=self.tr("Analysis failed: {}").format(str(e)),
                    output_path=None,
                )
            )

    def get_score_list_from_video_source(
        self, video_path: str, method: AssessmentMethod = AssessmentMethod.REBA
    ) -> tuple[list[int], list[tuple[int, RiskLevel]]]:
        """
        Retrieves synchronized scores matching the specific video context.

        Parses targeted source contexts dynamically to match parameters and builds safe
        fallbacks to universal processing summaries when file checks are missing.

        Args:
            video_path (str): The local system filepath target locating visual recording footage streams.
            method (AssessmentMethod): Structural targeting calculation metric layout definition. Defaults to [AssessmentMethod.REBA][gui.utils.constants.AssessmentMethod].

        Returns: TODO change return type to custom model
            tuple[list[int], list[tuple[int, RiskLevel]]] (tuple): Composed array elements holding:
                * score_list (`list`): List of per-frame calculated ergonomic evaluation score integers.
                * threshold_mapping (`list`): Risk interval parameters definition array associated with the method.
        """
        adapter = self.get_adapter(method)
        current_thresholds = adapter.get_thresholds()

        # Isolate video file base stem safely (e.g., "cam_1.mp4" -> "cam_1")
        video_stem = Path(video_path).stem
        analysis_filename = f"{video_stem}_{method.value.lower()}_metrics.csv"
        analysis_path = ErgoPaths.analysis_output() / analysis_filename

        # Fallback to shared general configuration file if contextual analytics don't exist
        if not analysis_path.exists():
            analysis_path = ErgoPaths.analysis_output()

        if not analysis_path.exists():
            # If no tracking data sheets are found, run analysis generation directly
            self.run_analysis(method=method)
            analysis_path = ErgoPaths.analysis_output()

        if not analysis_path.exists():
            return [], current_thresholds

        try:
            analysis_df = pd.read_csv(analysis_path)
            self.scores_list = analysis_df[MetricType.SCORE.value].tolist()
            return self.scores_list, current_thresholds
        except Exception as e:
            logger.error(f"Failed parsing analytics matrix: {e}")
            return [], current_thresholds

    def load_video_source(
        self, path: str, scores_list: list[int] | None = None
    ) -> VideoLoadResult:
        """
        Initializes a new video thread context for the given file path.

        Halts ongoing loop cycles safely, binds evaluation scores targets array inputs
        parameters, and triggers background tracking setup updates.

        Args:
            path (str): Absolute systemic locator string indicating local video data targets.
            scores_list (list[int] | None): Sequential score array updates parameter overlay data. Defaults to `None`.

        Returns:
            VideoLoadResult (VideoLoadResult): Structured model detailing file preparation success parameters.
        """
        try:
            if not self._ensure_video_engine_ready():
                return VideoLoadResult(
                    success=False, message=self.tr("Video engine unavailable")
                )

            fresh_score_list, thresholds = self.get_score_list_from_video_source(
                path, method=self._current_method
            )
            self.scores_list = fresh_score_list

            if scores_list is not None:
                self.scores_list = scores_list

            # Push asset target changes down to the video_worker via queued slots across threads
            video_load_request = VideoLoadRequest(
                path=Path(path), scores=self.scores_list, thresholds=thresholds
            )
            #
            self.video_load_requested.emit(video_load_request)

            self.playback_state_changed.emit(
                PlaybackState.PAUSED
            )  # Load state naturally starts paused
            return VideoLoadResult(
                success=True, message=self.tr("Video loaded and ready.")
            )

        except Exception as e:
            return VideoLoadResult(
                success=False, message=self.tr("Video error: {}").format(str(e))
            )

    def import_joint_data(self, file_path: str | Path) -> tuple[bool, str]:
        """
        Loads CSV or NPY joint data into the backend via the session manager.

        Args:
            file_path (str | Path): Path targeting metric information structures asset data files.

        Returns:
            tuple[bool, str] (tuple): A sequence collection tracking:
                * success_status (`bool`): Operational status index verification tracking flag.
                * status_message (`str`): Detail message tracking diagnostic logs strings output context.
        """
        try:
            logger.debug(f"Attempting to import joint data from: {file_path}")
            # session_manager returns (data, path_object)
            self.current_data, self.current_file_path = (
                self.session_manager.load_file_data(file_path)
            )
            return True, self.tr("Successfully loaded: {}").format(
                self.current_file_path.name if self.current_file_path else "Data"
            )
        except Exception as e:
            return False, self.tr("Failed to load data: {}").format(str(e))

    def set_root_and_scan(self, path: str | Path) -> list[str]:
        """
        Scans a custom directory for session folders.

        Args:
            path (str | Path): The directory path to scan.

        Returns:
            list[str]: A list of session directory names found.
        """
        return self.session_manager.scan_custom_path(path)

    def get_initial_sessions(self) -> list[str]:
        """
        Scan the default sessions directory for available session folders.

        Returns:
            list[str]: A list of session directory names found via the session manager.
        """
        return self.session_manager.get_initial_sessions()

    def load_session_automatically(self, session_name: str) -> SessionData:
        """
        Locates and loads all assets for a session (Data + Video).

        Automatically identifies joint movement metrics records sheets data sets and selects the core video
        capture file corresponding to the requested tracking string indicator key parameters.

        Args:
            session_name (str): Label identifier key targeting target recordings assets directory groupings.

        Returns:
            SessionData (SessionData): Unified tracking model layout storing data configuration resolution success variables.
        """
        logger.info(f"Loading session: {session_name}")

        # 1. Ask ErgoPaths for the address
        session_path = ErgoPaths.session_folder(session_name)

        if not session_path.exists():
            logger.error(
                f"Session folder with name {session_name} not found at: {session_path}"
            )
            return SessionData(
                name=session_name,
                success=False,
                message=self.tr("Session folder not found at: {}").format(session_path),
            )

        # 2. Let SessionManager handle the deep dive
        target_csv, target_video, video_files = (
            self.session_manager.resolve_session_assets(session_name)
        )

        if not target_csv:
            return SessionData(
                name=session_name,
                success=False,
                message=self.tr("No 'joint_angles' CSV found."),
            )

        # 3. Load Data
        success, msg = self.import_joint_data(target_csv)

        if not success or self.current_data is None:
            logger.error(f"Data Load Failed: {msg}")
            self.error_occurred.emit(
                ErrorInfo(title="Failed to load session", message=msg)
            )
            return SessionData(
                name=session_name,
                success=False,
                message=msg,
            )

        # 4. Load Video using ErgoPaths for the full path construction
        if target_video:
            video_full_path = ErgoPaths.video_folder(session_name) / target_video
            video_result = self.load_video_source(str(video_full_path))
            # TODO check this and test it
            if not video_result.success:
                logger.error(f"Video Load Failed: {video_result.message}")
                return SessionData(
                    name=session_name,
                    success=False,
                    message=video_result.message,
                )

        session_data = SessionData(
            name=session_name,
            success=True,
            message=self.tr("Loaded Session: {}").format(session_name),
            video_paths=video_files,
        )
        self.session_loaded.emit(session_data)
        return session_data

    def export_headless_frames(self, video_name: str, session_name: str) -> bool:
        """
        Triggers background worker execution frames assembly writing out files.

        Kicks off an asynchronous background processing tracking routine extracting matrix overlays
        and saving raw frame images sequentially into standalone target directories without lockups.

        Args:
            video_name (str): String file name indicator targeting video selection asset files.
            session_name (str): Recording grouping label index indicator parameter.

        Returns:
            bool (bool): Thread kickoff invocation execution verification tracking parameter indicator status.
        """
        if not video_name or not session_name:
            return False

        video_path = ErgoPaths.video_folder(session_name) / video_name

        frames_dir = ErgoPaths.frames_folder(session_name, video_name)

        # 2. Clean up existing export thread assets if running
        if hasattr(self, "export_thread") and self.export_thread:
            try:
                if self.export_thread.isRunning():
                    logger.info(
                        "Stopping active export thread before starting new one..."
                    )
                    if hasattr(self, "export_worker") and self.export_worker:
                        self.export_worker.stop()
                    self.export_thread.quit()
                    self.export_thread.wait()
            except RuntimeError:
                pass  # C++ object was already garbage collected

        # --- Threading Setup ---
        self.export_thread = QThread()
        self.export_worker = FramesExportWorker(
            video_path, frames_dir, self.scores_list
        )
        self.export_worker.moveToThread(self.export_thread)

        # 4. Connect Cross-Thread Signals
        # Forward the worker's progress straight out through backend proxy boundary
        @Slot(VideoPosition)
        def format_progress_message(video_position: VideoPosition):
            """
            Interceptor callback translating raw positions inputs sequences parameters into output logging strings messages.

            Args:
                video_position (VideoPosition): Data model recording frame metrics update indexes parameters.

            Returns:
                None (None): Dispatches a modified tracking state string directly to listener objects via UI slots.
            """
            message = f"⏳ Exporting Frames: {video_position.current_frame} / {video_position.total_frames}"
            self.status_updated.emit(message)

        self.export_worker.progress.connect(format_progress_message)

        self.export_thread.started.connect(self.export_worker.run)
        # Clean up strategies when finished
        self.export_worker.finished.connect(self.export_thread.quit)
        self.export_worker.finished.connect(
            lambda: self.status_updated.emit("✅ Export Complete")
        )

        # Safe C++ deletions
        self.export_worker.finished.connect(self.export_worker.deleteLater)
        self.export_thread.finished.connect(self.export_thread.deleteLater)

        # 5. Kick off background execution
        self.export_thread.start()
        self.status_updated.emit("⏳ Exporting Frames (Headless Mode)...")
        return True
