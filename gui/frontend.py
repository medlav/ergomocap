# ---
# project: ErgoMoCap
# file: frontend.py
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
ErgoMoCap Main Application Window
---------------------------------
Primary user interface controller and orchestration layer for ErgoMoCap.

This module implements the `MainWindow`, which coordinates interactions between the
ergonomic configuration sidebar, the video rendering canvas, and the background execution
engine (`ErgoBackend`). It manages the top-level window lifecycle, application-wide themes,
asynchronous thread cleanup, and shortcuts.
"""

import os
from pathlib import Path
import sys
import time

from PySide6.QtCore import QCoreApplication, QUrl, Qt, Slot
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QLabel,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFileDialog,
)
from PySide6.QtGui import QDesktopServices, QIcon

from gui.backend.backend import ErgoBackend
from gui.utils.constants import AssessmentMethod
from gui.theme.style import get_stylesheet, ErgoTheme
from gui.utils.app_paths import ErgoPaths
from gui.utils.models import AnalysisRequest, AnalysisResult, VideoCommand, VideoControl
from gui.views.report_view import ReportView
from gui.views.review_view import ReviewView
from gui.widgets.menu_actions import MenuActions
from gui.widgets.menu_bar import MenuBar

# from gui.widgets.navbar import Navbar
from gui.widgets.sidebar import ErgoSidebar
from gui.widgets.video_canvas import VideoCanvas
from gui.utils.logger import logger


class MainWindow(QMainWindow):
    """
    The primary application window for the ErgoMoCap GUI.

    This class manages the user interface, handles interactions between the
    sidebar controls and the video canvas, and coordinates with the ErgoBackend
    for data processing and analysis.

    Attributes:
        backend (ErgoBackend): The core logic handler for data and video processing.
        current_theme (ErgoTheme): Tracks the active UI theme ('dark' or 'light').
        report_window (ReportView): A persistent window instance for displaying results.
        canvas (VideoCanvas): The central widget for video rendering.
        menu_actions (MenuActions): Logic handler for menu bar commands.
        sidebar (ErgoSidebar): The left-hand control panel for user input.
        _menu_bar (MenuBar): The top-level application menu bar.

    Methods:
        setup_ui: Constructs the main layout and widget hierarchy.
        handle_reboot: Restarts the application process.
        kill_running_threads: Safely terminates active backend threads.
        safe_close: Safely terminates running threads and closes the main window.
        handle_new_recording: Placeholder for starting a new capture session.
        handle_load_recording: Placeholder for loading existing recordings.
        open_settings: Placeholder for the settings configuration window.
        open_docs: Opens the locally shipped documentation homepage.
        open_tutorial: Opens the locally shipped tutorial page.
        open_source: Opens the live GitHub repository on the web.
        connect_signals: Establishes connections between UI signals and handlers.
        toggle_theme: Switches the UI between dark and light stylesheets.
        toggle_sidebar: Shows or hides the ergonomic sidebar.
        init_root: Sets up the initial data directory and scans for sessions.
        handle_select_root: Slot to update the data root directory.
        handle_session_selected: Slot to load data for a specific session.
        handle_video_selection_changed: Slot to switch the active video source.
        handle_load_video: Slot to manually browse for a video file.
        _reconnect_video_signals: Internal helper to manage frame stream connections.
        step_video: Sends a relative step request to the backend safely across threads.
        keyPressEvent: Overrides keyboard interaction to trigger shortcuts.
        _handle_canvas_seek: Handles the seek request from the video canvas overlay.
        handle_toggle_video: Slot to play or pause video playback.
        handle_run_fmc: Slot to trigger external FreeMoCap processing.
        handle_import_joint_data: Slot to manually import joint data files.
        show_review: Displays the live review window.
        show_report: Displays the analysis reporting window.
        run_analysis: Triggers the ergonomic calculation engine.
        _update_export_status: Unified status formatter for background processing.
        handle_headless_export: Delegates frame export processing to the backend.
    """

    def __init__(self) -> None:
        """
        Initializes the MainWindow, sets up the backend, and triggers UI construction.

        Returns:
            None (None): Initializes the instance state.
        """
        super().__init__()
        self.backend: ErgoBackend = ErgoBackend()
        self.current_theme: ErgoTheme = ErgoTheme.DARK

        self.setWindowTitle(self.tr("ErgoMoCap - Ergonomics Motion Capture"))

        icon_path = ErgoPaths.LOGO

        self.setWindowIcon(QIcon(str(icon_path)))
        self.setMinimumSize(1200, 800)

        # Initialize your Report Window as a persistent separate window
        self.report_window: ReportView = ReportView(self)

        # Initialize your Review Window as a persistent separate window
        self.review_window: ReviewView = ReviewView(self)

        self.setup_ui()
        self.connect_signals()
        self.init_root()

    def setup_ui(self) -> None:
        """
        Constructs the main layout, widgets, and signal-slot connections.

        This method initializes the central widget, the `VideoCanvas`, the
        `ErgoSidebar`, and the application `MenuBar`.

        Returns:
            None (None): Modifies the `MainWindow` state.
        """
        central: QWidget = QWidget()
        self.setCentralWidget(central)

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        master_layout: QVBoxLayout = QVBoxLayout(central)
        master_layout.setContentsMargins(0, 0, 0, 0)
        master_layout.setSpacing(0)

        # 2. CONTENT AREA
        content_area: QWidget = QWidget()
        content_layout: QHBoxLayout = QHBoxLayout(content_area)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # --- VIDEO AREA ---
        self.canvas: VideoCanvas = VideoCanvas()
        content_layout.addWidget(self.canvas, 1)

        # Add Content Area to Master Layout
        master_layout.addWidget(content_area)

        # 1. Plug in the menu from the other file
        self.menu_actions = MenuActions(self)

        self._menu_bar = MenuBar(actions=self.menu_actions, parent=self)
        self.setMenuBar(self._menu_bar)

        self.sidebar = ErgoSidebar(self)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.sidebar)

    # --- Methods for Actions ---
    def handle_reboot(self) -> None:
        """
        Restarts the application by executing a new Python process.

        Returns:
            None (None): Terminates the current process.
        """
        python = sys.executable  # nosec B606 TODO replace if possible
        os.execl(python, python, *sys.argv)  # nosec B606 TODO replace if possible

    def kill_running_threads(self) -> None:
        """
        Safely terminates active backend threads to prevent memory leaks or crashes.

        Returns:
            None (None): Stops background threads.
        """
        killed_threads: str = ""

        # 1. Safely stop video playback thread using native QThread methods
        if hasattr(self.backend, "video_thread") and self.backend.video_thread:
            if self.backend.video_thread.isRunning():
                self.backend.video_thread.quit()
                self.backend.video_thread.wait()
                killed_threads += "- video_thread\n"

        # 2. Safely clean up the background frame exporter thread if it's currently processing
        if hasattr(self.backend, "export_thread") and self.backend.export_thread:
            try:
                if self.backend.export_thread.isRunning():
                    # 1. Break internal cv2 worker loop safely
                    if (
                        hasattr(self.backend, "export_worker")
                        and self.backend.export_worker
                    ):
                        self.backend.export_worker.stop()

                    # 2. Tear down thread infrastructure
                    self.backend.export_thread.quit()

                    if not self.backend.export_thread.wait(2000):
                        self.backend.export_thread.terminate()
                        self.backend.export_thread.wait()

                    killed_threads += "- export_thread\n"
            except RuntimeError:
                # Catch and dismiss cases where C++ lifecycle already ended
                pass

        self.sidebar.set_status(f"Threads safely terminated:\n{killed_threads}")

        # TODO implement a better kill switch for all threads and processes of the app in particular freemocap

    def safe_close(self) -> None:
        """
        Safely terminates running backend threads and closes the application window.

        Returns:
            None (None): Closes the window hierarchy.
        """
        # TODO add docsrings and include this function in MainWindow Docstringas
        self.kill_running_threads()
        self.close()

    def handle_new_recording(self) -> None:
        """
        Placeholder for starting a new motion capture recording session.

        Returns:
            None (None): Not yet implemented.
        """
        pass

    def handle_load_recording(self) -> None:
        """
        Placeholder for loading an existing historical recording session.

        Returns:
            None (None): Not yet implemented.
        """
        pass

    def open_settings(self) -> None:
        """
        Placeholder for configuring application preferences and window paths.

        Returns:
            None (None): Not yet implemented.
        """
        # TODO make setting view and open as secondary window
        pass

    def open_docs(self) -> None:
        """
        Opens the locally shipped documentation homepage.

        Returns:
            None (None): Launches system default desktop browser.
        """
        url = ErgoPaths.get_local_site_url(page_name="index.html")
        QDesktopServices.openUrl(url)

    def open_tutorial(self) -> None:
        """
        Opens the locally shipped tutorial page.

        Returns:
            None (None): Launches system default desktop browser.
        """
        url = ErgoPaths.get_local_site_url(page_name="tutorial.html")
        QDesktopServices.openUrl(url)

    def open_source(self) -> None:
        """
        Opens the live GitHub repository on the web.

        Returns:
            None (None): Launches system default desktop browser.
        """
        url = QUrl("https://github.com/freemocap/freemocap")
        QDesktopServices.openUrl(url)

    def connect_signals(self) -> None:
        """
        Wiring the Sidebar Public API to the existing MainWindow handlers.

        Returns:
            None (None): Establishes Qt signal-slot connections.
        """
        s = self.sidebar

        # Connect internal sidebar signals to MainWindow handlers
        s.btn_fmc.clicked.connect(self.handle_run_fmc)
        s.btn_select_root.clicked.connect(self.handle_select_root)
        s.combo_sessions.currentIndexChanged.connect(self.handle_session_selected)
        s.run_analysis_clicked.connect(self.run_analysis)
        s.btn_review.clicked.connect(self.show_review)
        s.btn_report.clicked.connect(self.show_report)
        s.btn_load_video.clicked.connect(self.handle_load_video)
        s.btn_play_video.clicked.connect(self.handle_toggle_video)
        s.combo_videos.currentIndexChanged.connect(self.handle_video_selection_changed)

        # --- NEW CANVAS INTERACTION CONNECTIONS ---
        c = self.canvas
        # When you click the seeker bar on the video
        c.seek_requested.connect(self._handle_canvas_seek)
        # When you click the video (not the bar) to play/pause
        c.toggle_requested.connect(self.handle_toggle_video)

        # New Button Connections
        s.btn_prev_frame.clicked.connect(self._on_prev_clicked)
        s.btn_next_frame.clicked.connect(self._on_next_clicked)

        self.backend.status_updated.connect(self.sidebar.set_status)

        self.backend.analysis_finished.connect(
            self._handle_analysis_finished,
            type=Qt.ConnectionType.QueuedConnection,  # ← CRITICAL: UI updates must run on main thread
        )

        self.backend.session_loaded.connect(self.review_window.update_session_data)

    def toggle_theme(self) -> None:
        """
        Switches the application stylesheet between dark and light modes.

        Returns:
            None (None): Updates the `QApplication` stylesheet and theme icons.
        """

        self.current_theme = (
            ErgoTheme.LIGHT if self.current_theme == ErgoTheme.DARK else ErgoTheme.DARK
        )
        app = QApplication.instance()
        if isinstance(app, QApplication):
            app.setStyleSheet(get_stylesheet(self.current_theme))
            icon: str = "☀️" if self.current_theme == ErgoTheme.LIGHT else "🌓"
            self._menu_bar.theme_btn.setText(icon)

    def toggle_sidebar(self) -> None:
        """
        Toggle the visibility of the sidebar.

        Returns:
            None (None): Updates the visibility state of the `sidebar` widget.
        """
        self.sidebar.setVisible(not self.sidebar.isVisible())

    def init_root(self) -> None:
        """
        Initializes the data root from the backend configuration on startup.

        Scans the default directory for sessions and attempts to load assets
        (CSV data and video) for the first found session.

        Returns:
            None (None): Populates UI widgets with initial data.
        """
        root_path: Path | None = ErgoPaths.SESSIONS
        if not root_path:
            return

        sessions: list[str] = self.backend.set_root_and_scan(root_path)

        if not sessions:
            logger.warning(
                "No Session Data Found. Check if the root folder is the correct 'freemocap_data' folder."
            )
            self.sidebar.set_status(
                self.tr(
                    "No Session Data Found. Check if the root folder is the correct one."
                )
            )
            return

        # Update UI with available sessions
        self.sidebar.update_sessions(sessions)

        # Attempt to automatically load the first session
        session_data = self.backend.load_session_automatically(sessions[0])

        if not session_data:
            logger.warning(
                "No Session Data Found. Check if the root folder is the correct 'freemocap_data' folder."
            )
            return

        if not session_data.success:
            self.sidebar.set_status(
                self.tr("Error during initialization: No Success {}.").format(
                    session_data.message
                )
            )
            return

        if not session_data.video_paths or len(session_data.video_paths) == 0:
            self.sidebar.set_status(
                self.tr("Error during initialization: No Videos {}.").format(
                    session_data.message
                )
            )
            return

        # Populates UI with videos found
        self.sidebar.update_videos(session_data.video_paths)

        # Safe to extract target video now that length check has passed
        target_video = session_data.video_paths[0]
        video_result = self.backend.load_video_source(target_video)

        # Check video loading outcome
        if video_result.success:
            self.handle_video_selection_changed()
            # Set the final successful status message here so it doesn't get overwritten unexpectedly
            self.sidebar.set_status(
                self.tr("Found {} sessions. Loaded {} videos").format(
                    len(sessions), len(session_data.video_paths)
                )
            )
        else:
            self.sidebar.set_status(
                self.tr("Video Load Error: {}").format(video_result.message)
            )

    @Slot()
    def handle_select_root(self) -> None:
        """
        Updates the backend root and refreshes the session list.

        Opens a `QFileDialog` for the user to select a new directory.

        Returns:
            None (None): Updates the [ErgoSidebar][gui.widgets.sidebar.ErgoSidebar].
        """
        root_path: str | None = QFileDialog.getExistingDirectory(
            self, self.tr("Select FreeMoCap Data Folder")
        )
        if root_path:
            chosen_path = Path(root_path)
            ErgoPaths.update_user_root(chosen_path)  # resets constant class paths

            sessions_folder: Path = Path(root_path) / ErgoPaths.SESSIONS_FOLDER_NAME
            sessions: list[str] = self.backend.set_root_and_scan(sessions_folder)
            self.sidebar.update_sessions(sessions)
            self.sidebar.set_status(self.tr("Found {} sessions.").format(len(sessions)))

    @Slot()
    def handle_session_selected(self) -> None:
        """
        Loads metadata and populates videos for the selected session.

        Returns:
            None (None): Updates backend state and UI enabled/disabled statuses.
        """
        session_name: str = self.sidebar.get_current_session()
        if not session_name or session_name == "":
            return

        # Clear previous state to avoid analyzing old data if new load fails
        self.sidebar.set_status(self.tr("Loading session data..."))

        session_data = self.backend.load_session_automatically(session_name)

        if session_data.success:
            videos_num: int = len(session_data.video_paths)
            if session_data.video_paths and videos_num > 0:
                self.sidebar.update_videos(session_data.video_paths)
                self.handle_video_selection_changed()

            self.sidebar.btn_play_video.setEnabled(True)
            self.sidebar.btn_next_frame.setEnabled(True)
            self.sidebar.btn_prev_frame.setEnabled(True)
            self.sidebar.btn_analysis.setEnabled(True)  # Ensure this is enabled
            self.sidebar.set_status(
                self.tr("Session Loaded: {}. Found {} videos").format(
                    session_name, videos_num
                )
            )

            self.review_window.update_session_data(session_data)

        else:
            # This is likely where your error is happening
            self.sidebar.set_status(self.tr("ERROR: {}").format(session_data.message))
            self.sidebar.btn_analysis.setEnabled(False)

    @Slot()
    def handle_video_selection_changed(self) -> None:
        """
        Loads a specific video file into the backend based on sidebar selection.

        Returns:
            None (None): Updates the video source in [ErgoBackend][gui.backend.backend.ErgoBackend].
        """
        video_name: str = self.sidebar.get_current_video()
        session_name: str = self.sidebar.get_current_session()

        if not video_name or not session_name:
            return

        video_path: Path = ErgoPaths.video_folder(session_name) / video_name

        if not video_path.exists():
            self.sidebar.set_status(f"ERROR: Video not found at {video_path.name}")
            return

        # Safety: Reconnect frame signals
        self._reconnect_video_signals()

        video_result = self.backend.load_video_source(str(video_path))
        if video_result.success:
            self.sidebar.btn_play_video.setEnabled(True)
            self.sidebar.set_status(self.tr("Loaded {}").format(video_name))

    @Slot()
    def handle_load_video(self) -> None:
        """
        Opens a file dialog to manually browse and select a video file.

        Returns:
            None (None): Updates the backend video source and UI status.
        """
        session_name = self.sidebar.get_current_session()
        initial_path: str = (
            str(ErgoPaths.video_folder(session_name))
            if session_name
            else str(ErgoPaths.SESSIONS)
        )

        path, _ = QFileDialog.getOpenFileName(
            self,
            self.tr("Select Video"),
            initial_path,
            self.tr("Videos (*.mp4 *.avi *.mov *.mkv)"),
        )
        if path:
            video_result = self.backend.load_video_source(path)

            self.sidebar.set_status(self.tr("{}").format(video_result.message))
            if video_result.success:
                self._reconnect_video_signals()
                self.sidebar.btn_play_video.setEnabled(True)
                self.sidebar.btn_next_frame.setEnabled(True)
                self.sidebar.btn_prev_frame.setEnabled(True)

    def _reconnect_video_signals(self) -> None:
        """
        Helper to safely handle frame connections.

        Ensures that the `frame_ready` signal from the backend is correctly
        routed to the [VideoCanvas][gui.widgets.video_canvas.VideoCanvas].

        Returns:
            None (None): Re-establishes signal connections.
        """
        try:
            self.backend.frame_ready.disconnect()
            self.backend.position_changed.disconnect()
        except (RuntimeError, TypeError):
            pass

        # Connect the image to the canvas
        self.backend.frame_ready.connect(self.canvas.update_frame)

        # Connect the seeker data (current/total frames) to the canvas
        # This makes the progress bar actually move!
        self.backend.position_changed.connect(self.canvas.update_position)
        self.backend.position_changed.connect(self.review_window.sync_video_position)

    # Define these helper slots in your view class:
    @Slot()
    def _on_prev_clicked(self) -> None:
        self.step_video(-1)

    @Slot()
    def _on_next_clicked(self) -> None:
        self.step_video(1)

    def step_video(self, delta: int) -> None:
        """
        Sends a relative step request to the backend safely across threads.

        Args:
            delta (int): The number of frames to step (positive for forward, negative for backward).

        Returns:
            None (None): Emits cross-thread signaling.
        """
        command = VideoCommand.STEP_FORWARD if delta > 0 else VideoCommand.STEP_BACKWARD

        # Emitting a copy-safe dataclass across threads is 100% thread-safe!
        self.backend.video_control_requested.emit(VideoControl(command=command))
        self.sidebar.set_status(f"Stepped {command.name}")

    def keyPressEvent(self, event) -> None:
        """
        Overrides standard key presses to handle shortcut bindings.

        Maps arrow keys to frame stepping and spacebar to video toggle commands.

        Args:
            event (QKeyEvent): The incoming key keyboard event configuration.

        Returns:
            None (None): Accepts or passes the incoming key event structure.
        """

        # Ensure we have a video thread running before trying to step
        if not hasattr(self, "backend") or not self.backend.video_worker:
            super().keyPressEvent(event)
            return

        key = event.key()

        if key == Qt.Key.Key_Left:
            self.step_video(-1)
            event.accept()
        elif key == Qt.Key.Key_Right:
            self.step_video(1)
            event.accept()
        elif key == Qt.Key.Key_Space:
            self.handle_toggle_video()
            event.accept()
        else:
            super().keyPressEvent(event)

    @Slot(int)
    def _handle_canvas_seek(self, frame_idx: int) -> None:
        """
        Handles the seek request from the video canvas overlay.

        Args:
            frame_idx (int): Target frame absolute indexing point.

        Returns:
            None (None): Dispatches a structured `VideoControl` request.
        """
        self.backend.video_control_requested.emit(
            VideoControl(
                command=VideoCommand.SEEK,
                target_frame=frame_idx,
            ),
        )
        self.sidebar.set_status(f"Seeking to frame: {frame_idx}")

    @Slot()
    def handle_toggle_video(self) -> None:
        """
        Toggles Play/Pause state of the video playback.

        Returns:
            None (None): Updates the UI status label and backend playback state.
        """
        self.backend.video_control_requested.emit(
            VideoControl(
                command=VideoCommand.TOGGLE,
            )
        )

    @Slot()
    def handle_run_fmc(self) -> None:
        """Triggers FreeMoCap processing with a forced 2-second visual delay.

        Returns:
            None
        """
        self.wait_dialog = QDialog(parent=self)
        self.wait_dialog.setWindowModality(Qt.WindowModality.WindowModal)

        layout = QVBoxLayout()
        layout.addWidget(
            QLabel(
                self.tr("Initializing FreeMoCap... Please wait until it opens."),
                self.wait_dialog,
            )
        )

        self.wait_dialog.setLayout(layout)
        self.wait_dialog.show()
        QCoreApplication.processEvents()

        start_time = time.time()
        success, msg = self.backend.launch_freemocap()
        self.sidebar.set_status(self.tr("{}").format(msg))

        elapsed = time.time() - start_time
        if elapsed < 3.0:
            time.sleep(3.0 - elapsed)

        self.wait_dialog.accept()
        self.wait_dialog.deleteLater()

    @Slot()
    def handle_import_joint_data(self) -> None:
        """
        Opens a file dialog to manually import joint coordinate data.

        Returns:
            None (None): Updates the backend data buffer.
        """
        path, _ = QFileDialog.getOpenFileName(
            self, self.tr("Select Data"), "", self.tr("Data (*.csv *.xlsx *.npy)")
        )
        if path:
            success, msg = self.backend.import_joint_data(path)
            self.sidebar.set_status(self.tr("{}").format(msg))

    @Slot()
    def show_review(self) -> None:
        """
        Displays the Review window and updates it with the current method.

        Returns:
            None (None): Shows or raises the `review_window`.
        """

        self.handle_session_selected()
        self.review_window.update()
        if self.review_window.isHidden():
            self.review_window.show()
        else:
            self.review_window.raise_()
            self.review_window.activateWindow()

    @Slot()
    def show_report(self) -> None:
        """
        Displays the ReportView window and updates it with the current method.

        Returns:
            None (None): Shows or raises the `report_window`.
        """
        selected_method: str = self.sidebar.get_selected_method().upper()
        method: AssessmentMethod = AssessmentMethod[selected_method]
        self.report_window.set_method(method)
        self.report_window.update_current_strategy()

        if self.report_window.isHidden():
            self.report_window.show()
        else:
            self.report_window.raise_()
            self.report_window.activateWindow()

    @Slot(AnalysisRequest)
    def run_analysis(self, analysis_request: AnalysisRequest) -> None:
        """Executes the ergonomic assessment and opens the results.

        Calculates scores based on the selected method (RULA/REBA) and loads
        the resulting data into the [`ReportView`][gui.views.report_view.ReportView].

        Args:
            analysis_request (AnalysisRequest): Parameters configuring the method and frame export triggers.
        """
        self._pending_analysis_request = analysis_request
        self.report_window.set_method(analysis_request.method)

        self.sidebar.btn_analysis.setEnabled(False)
        self.sidebar.set_status(
            self.tr("Starting {} analysis...").format(analysis_request.method.value)
        )

        self.backend.run_analysis(method=analysis_request.method)

    @Slot(AnalysisResult)
    def _handle_analysis_finished(self, result: AnalysisResult) -> None:
        """Handles the `analysis_finished` signal from the backend.

        Processes the [`AnalysisResult`][gui.utils.models.AnalysisResult] emitted by the
        backend after the asynchronous calculation completes. It updates the UI state,
        triggers frame exports if requested, and displays the report window. This slot
        always executes on the main UI thread via a queued connection.

        Args:
            result (AnalysisResult): The analysis result containing the success status,
                message, output path, and optional scores or stats.
        """
        import threading

        logger.debug(
            f"Frontend: _handle_analysis_finished on thread: {threading.current_thread().name}"
        )

        self.sidebar.btn_analysis.setEnabled(True)

        msg = result.message if result.message else "Analysis completed"
        self.sidebar.set_status(self.tr(msg))

        if result.success and result.output_path:
            if (
                hasattr(self, "_pending_analysis_request")
                and self._pending_analysis_request
            ):
                if self._pending_analysis_request.export_frames:
                    self.handle_headless_export()
                self._pending_analysis_request = None

            self.report_window.backend.load_data_and_run(file_path=result.output_path)
            self.handle_session_selected()

            if self.report_window.isHidden():
                self.report_window.show()
            else:
                self.report_window.raise_()
                self.report_window.activateWindow()
        else:
            logger.warning(f"Analysis failed: {result.message}")

    def _update_export_status(self, current: int, total: int) -> None:
        """
        Unified status formatter for processing progress indicators. (1/10 or 10%)

        Args:
            current (int): Current frame index processed.
            total (int): Comprehensive index total.

        Returns:
            None (None): Textually reformats the application sidebar status bar.
        """
        percent = (current / total) * 100 if total > 0 else 0
        status_msg = f"⏳ Exporting Frames: {current}/{total} frames ({percent:.1f}%)"
        self.sidebar.set_status(status_msg)

    def handle_headless_export(self) -> None:
        """
        Gathers UI state parameters and delegates frame export processing to the backend.

        Returns:
            None (None): Launches asynchronous background calculations.
        """
        video_name: str = self.sidebar.get_current_video()
        session_name: str = self.sidebar.get_current_session()

        # Delegate core tracking work down to the backend controller
        self.backend.export_headless_frames(
            session_name=session_name, video_name=video_name
        )
