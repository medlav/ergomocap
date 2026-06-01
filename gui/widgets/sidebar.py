# ---
# project: ErgoMoCap
# file: sidebar.py
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
ErgoMoCap: Ergonomic Sidebar
----------------------------
Control Panel and Configuration Interface for the ErgoMoCap Application.

This module implements the `ErgoSidebar`, a specialized `QDockWidget` that serves
as the primary control hub for the user. It organizes recording source selection,
data management, analytics parameters, and video visualization controls into a
scrollable vertical interface.

The sidebar follows a "Deaf-Mute" component pattern, communicating exclusively
through Qt Signals to maintain strict decoupling from the project's backend
and processing logic.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QDockWidget,
    QFrame,
    QHBoxLayout,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QGroupBox,
    QPushButton,
    QLabel,
    QComboBox,
    QScrollArea,
    QWidget,
)

from gui.utils.constants import AssessmentMethod
from gui.utils.models import AnalysisRequest


class ErgoSidebar(QDockWidget):
    """
    A scrollable control panel for managing ergonomic analysis workflows.

    The sidebar is divided into logical sections:
    - **Capture Source**: Execute external processing via FreeMoCap.
    - **Data Management**: File system navigation and session selection.
    - **Analytics**: Method selection (RULA/REBA) and analysis execution.
    - **Reports**: Navigation to the dashboard.
    - **Video Visualizer**: Media control and playback selection.

    Attributes:
        session_changed (Signal): Signal emitted when a new recording session is selected (str).
        video_changed (Signal): Signal emitted when a new video file is selected (str).
        run_analysis_clicked (Signal): Signal emitted with the formatted payload (`AnalysisRequest`).
        root_selection_requested (Signal): Signal emitted when the user requests a directory change.
        main_container (QWidget): Central container hosting the main vertical layout structure.
        scroll_area (QScrollArea): Main viewport allowing scrolling layout behaviors for small screens.
        container (QWidget): Child container acting as the canvas within the scroll area.
        btn_fmc (QPushButton): Push button to execute the FreeMoCap runner application.
        btn_select_root (QPushButton): File explorer launcher button for selecting a root folder.
        lbl_session (QLabel): Label descriptive title for session combos.
        combo_sessions (QComboBox): Dropdown selection menu displaying discovered local capture sessions.
        lbl_method (QLabel): Label descriptive title for calculation method selection combo box.
        combo_method (QComboBox): Dropdown selection layout offering supported framework algorithms.
        export_frames_checkbox (QCheckBox): Checkbox indicating whether output frame buffers should persist.
        btn_analysis (QPushButton): Trigger execution wrapper to launch backend processing logic.
        btn_report (QPushButton): Navigation trigger shortcut to deploy dashboard analytics displays.
        lbl_video_select (QLabel): Title layout text label header for picking file streams.
        combo_videos (QComboBox): Dropdown selector populated with multi-camera recordings if existing.
        btn_load_video (QPushButton): Fallback local file system dialog trigger for arbitrary videos.
        btn_play_video (QPushButton): Playback action control toggle button interface.
        btn_prev_frame (QPushButton): Manual single frame step backward hotkey layout link button.
        btn_next_frame (QPushButton): Manual single frame step forward hotkey layout link button.
        status_label (QLabel): Message terminal line positioned near footer boundary blocks.

    Methods:
        __init__: Initialize the sidebar and its internal UI components.
        _setup_ui: Construct the visual layout of the sidebar.
        _connect_internal_signals: Establish signal-slot connections for internal child widgets.
        update_sessions: Refresh the session selection list.
        update_videos: Refresh the available video list and update playback controls.
        set_status: Update the status label text in the UI.
        get_current_session: Returns the currently selected session name.
        get_current_video: Returns the currently selected video name.
        get_selected_method: Returns the currently selected analysis method.
        handle_run_analysis: Map selected GUI configurations to structured downstream events.
    """

    # Custom signals: The Sidebar "talks" to the app without knowing the Backend
    session_changed = Signal(str)
    video_changed = Signal(str)
    run_analysis_clicked = Signal(
        AnalysisRequest
    )  # sends the method name (REBA for now)
    root_selection_requested = Signal()

    def __init__(self, parent=None) -> None:
        """
        Initialize the sidebar and its internal UI components.

        Args:
            parent (QWidget | None): The parent widget, typically
                [MainWindow][gui.frontend.MainWindow]. Defaults to `None`.

        Returns:
            None (None): Initializer return.
        """
        super().__init__(parent)
        self._setup_ui()
        self._connect_internal_signals()

    def _setup_ui(self) -> None:
        """
        Construct the visual layout of the sidebar.

        Creates the main container, scroll area, and group boxes for organized
        control placement. It also configures the widget as a non-closable,
        left-aligned dock.

        Returns:
            None (None): Modifies the widget state in-place.
        """
        self.setObjectName("Sidebar")
        self.setFixedWidth(320)

        # --- THE FIX: Create a central widget for the Dock ---
        self.main_container: QWidget = QWidget()
        self.setWidget(self.main_container)

        # All layouts now go inside 'self.main_container'
        main_layout: QVBoxLayout = QVBoxLayout(self.main_container)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 1. Create the Scroll Area
        self.scroll_area: QScrollArea = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        # 2. Create a Container Widget for the scroll area
        self.container: QWidget = QWidget()
        self.container.setFixedWidth(300)
        self.container.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding
        )

        self.scroll_area.setWidget(self.container)

        # 3. The actual layout for your buttons
        layout: QVBoxLayout = QVBoxLayout(self.container)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        # --- CAPTURE SECTION ---
        cap_group: QGroupBox = QGroupBox(self.tr("CAPTURE SOURCE"))
        cap_lay: QVBoxLayout = QVBoxLayout(cap_group)
        self.btn_fmc: QPushButton = QPushButton(self.tr("💀 RUN FREEMOCAP"))
        self.btn_fmc.setObjectName("FMCBtn")
        cap_lay.addWidget(self.btn_fmc)
        layout.addWidget(cap_group)

        # --- DATA MANAGEMENT ---
        data_group: QGroupBox = QGroupBox(self.tr("DATA MANAGEMENT"))
        data_lay: QVBoxLayout = QVBoxLayout(data_group)
        self.btn_select_root: QPushButton = QPushButton(
            self.tr("📂 SELECT FREEMOCAP ROOT")
        )
        self.btn_select_root.setToolTip(
            "Select the path of your 'freemocap_data' folder."
        )

        data_lay.addWidget(self.btn_select_root)
        self.lbl_session: QLabel = QLabel(self.tr("Select Recording Session:"))
        self.lbl_session.setObjectName("FieldLabel")
        data_lay.addWidget(self.lbl_session)
        self.combo_sessions: QComboBox = QComboBox()
        data_lay.addWidget(self.combo_sessions)
        layout.addWidget(data_group)

        # --- ANALYTICS ---
        analysis_group: QGroupBox = QGroupBox(self.tr("ANALYTICS"))
        analysis_lay: QVBoxLayout = QVBoxLayout(analysis_group)
        self.lbl_method: QLabel = QLabel(self.tr("Select Ergonomic Method:"))
        self.lbl_method.setObjectName("FieldLabel")
        analysis_lay.addWidget(self.lbl_method)
        self.combo_method: QComboBox = QComboBox()
        # self.combo_method.addItems(
        #     ["REBA", "RULA", "OCRA (Planned)", "NIOSH (Planned)"]
        # )
        self.combo_method.addItems(
            [
                self.tr("REBA"),
                self.tr("RULA (Unstable)"),
                self.tr("OCRA (Planned)"),
                self.tr("EWAS (Planned)"),
                self.tr("NIOSH (Planned)"),
                self.tr("SNOOK (Planned)"),
            ]
        )
        self.export_frames_checkbox = QCheckBox(text="Export Frames?")
        analysis_lay.addWidget(self.combo_method)
        analysis_lay.addWidget(self.export_frames_checkbox)
        self.btn_analysis: QPushButton = QPushButton(self.tr("🏃 RUN ANALYSIS"))
        self.btn_analysis.setObjectName("AnalyzeBtn")
        analysis_lay.addWidget(self.btn_analysis)
        layout.addWidget(analysis_group)

        # --- REPORTS ---
        report_group: QGroupBox = QGroupBox(self.tr("REPORTS"))
        report_lay: QVBoxLayout = QVBoxLayout(report_group)
        self.btn_report: QPushButton = QPushButton(self.tr("📊 OPEN REPORT DASHBOARD"))
        self.btn_report.setObjectName("ReportBtn")
        report_lay.addWidget(self.btn_report)
        layout.addWidget(report_group)

        # --- VIDEO VISUALIZER ---
        video_group: QGroupBox = QGroupBox(self.tr("VIDEO VISUALIZER"))
        video_lay: QVBoxLayout = QVBoxLayout(video_group)
        self.lbl_video_select: QLabel = QLabel(self.tr("Select Video:"))
        self.lbl_video_select.setObjectName("FieldLabel")
        video_lay.addWidget(self.lbl_video_select)

        self.combo_videos: QComboBox = QComboBox()
        video_lay.addWidget(self.combo_videos)

        self.btn_load_video: QPushButton = QPushButton(self.tr("🎞️ BROWSE OTHER VIDEO"))
        self.btn_play_video: QPushButton = QPushButton(self.tr("▶ PLAY / PAUSE"))
        self.btn_play_video.setEnabled(False)

        # New: Frame Control Layout
        frame_ctrl_lay = QHBoxLayout()
        self.btn_prev_frame = QPushButton("Back (←)")
        self.btn_next_frame = QPushButton("Fwd (→)")
        self.btn_prev_frame.setEnabled(False)
        self.btn_next_frame.setEnabled(False)

        frame_ctrl_lay.addWidget(self.btn_prev_frame)
        frame_ctrl_lay.addWidget(self.btn_next_frame)

        video_lay.addWidget(self.btn_load_video)
        video_lay.addWidget(self.btn_play_video)
        video_lay.addLayout(frame_ctrl_lay)

        layout.addWidget(video_group)

        layout.addStretch()

        # Inside ErgoSidebar._setup_ui, apply this to your buttons:
        self.btn_fmc.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_analysis.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_play_video.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_prev_frame.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_next_frame.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        # --- STATUS BOX ---
        self.status_label: QTextEdit = QTextEdit()
        self.status_label.setReadOnly(True)
        self.status_label.setPlainText(self.tr("STATUS: READY"))

        self.status_label.setFrameStyle(QFrame.Shape.NoFrame)
        self.status_label.viewport().setAutoFillBackground(False)
        self.status_label.setMinimumHeight(120)
        self.status_label.setMaximumWidth(300)
        self.status_label.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding
        )

        self.scroll_area.setWidget(self.container)
        self.status_label.setAlignment(
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft
        )
        layout.addWidget(self.status_label)

        # Remove the Docker default features
        self.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)

        # Optional: Prevents the user from accidentally dragging it out
        self.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea)

        # 4. Finalize by adding the scroll area to the Sidebar's main layout
        main_layout.addWidget(self.scroll_area)

    def _connect_internal_signals(self) -> None:
        """
        Establish signal-slot connections for internal child widgets.

        Connects button clicks and combo box changes to the sidebar's public
        signals, effectively proxying widget interactions to the application controller.

        Returns:
            None (None): Sets up signal connections.
        """
        self.btn_select_root.clicked.connect(self.root_selection_requested.emit)
        self.combo_sessions.currentTextChanged.connect(self.session_changed.emit)
        self.combo_videos.currentTextChanged.connect(self.video_changed.emit)
        self.btn_analysis.clicked.connect(self.handle_run_analysis)

    # --- PUBLIC API: Logic moved from MainWindow to here ---

    def update_sessions(self, sessions: list[str]) -> None:
        """
        Refresh the session selection list.

        Args:
            sessions (list[str]): A `list` of session folder names found in the root directory.

        Returns:
            None (None): Updates the `combo_sessions` widget.
        """
        self.combo_sessions.blockSignals(True)
        self.combo_sessions.clear()
        self.combo_sessions.addItems(sessions)
        self.combo_sessions.blockSignals(False)
        self.set_status(f"Found {len(sessions)} sessions.")

    def update_videos(self, videos: list[str]) -> None:
        """
        Refresh the available video list and update playback controls.

        Args:
            videos (list[str]): A `list` of video file names associated with the current session.

        Returns:
            None (None): Updates the `combo_videos` widget and enables/disables the play button.
        """

        self.combo_videos.blockSignals(True)
        self.combo_videos.clear()
        self.combo_videos.addItems(videos)
        self.combo_videos.blockSignals(False)
        self.btn_play_video.setEnabled(len(videos) > 0)
        self.btn_next_frame.setEnabled(True)
        self.btn_prev_frame.setEnabled(True)

    def set_status(self, text: str) -> None:
        """
        Update the status label text in the UI.

        Args:
            text (str): The status message to display.

        Returns:
            None (None): Updates the `status_label` widget text.
        """
        self.status_label.setText(f"STATUS: {text}")

    def get_current_session(self) -> str:
        """
        Returns the currently selected session name.

        Returns:
            str (str): The text content of the active session combo box.
        """
        return self.combo_sessions.currentText()

    def get_current_video(self) -> str:
        """
        Returns the currently selected video name.

        Returns:
            str (str): The text content of the active video combo box.
        """
        return self.combo_videos.currentText()

    def get_selected_method(self) -> str:
        """
        Returns the currently selected analysis method.

        Returns:
            str (str): The selected method name (e.g., "REBA", "RULA").
        """

        return self.combo_method.currentText()

    def handle_run_analysis(self):
        """
        Map selected GUI configurations to structured downstream events.

        Constructs an instance of [AnalysisRequest][gui.utils.models.AnalysisRequest]
        and triggers the `run_analysis_clicked` signal if parsing matches known
        [AssessmentMethod][gui.utils.constants.AssessmentMethod] mappings. This
        signal proxies the configuration payload directly to the application's
        frontend orchestrator slot [run_analysis][gui.frontend.MainWindow.run_analysis].

        Returns:
            None (None): Emits Qt signals or writes parsing faults to the local terminal view.
        """
        selected_method: str = self.get_selected_method().upper()
        try:
            selected_method: str = self.combo_method.currentText().upper()
            method: AssessmentMethod = AssessmentMethod[selected_method]
            self.run_analysis_clicked.emit(
                AnalysisRequest(
                    method=method,
                    export_frames=self.export_frames_checkbox.isChecked(),
                )
            )
        except KeyError:
            self.status_label.setText(f"{selected_method} is not implemented.")
