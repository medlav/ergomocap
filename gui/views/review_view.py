"""
ErgoMoCap: Video Review Suite View
----------------------------------
Unified Orchestration & Correction View for Human-in-the-Loop Video Reviews.

This module implements the `ReviewView`, a specialized floating `QWidget` that serves
as an interactive control center for review, inspection, and manual verification of
computer-vision tracking and algorithmic outputs. It integrates diagnostic telemetry
data streams with contextual timeline-targeted data manipulation tools.

The interface adheres to a strict model-view-controller separation by wrapping
data-layer synchronization and persistence operations inside a dedicated
`ReviewBackend` component while piping presentation structures directly
to responsive PySide6 components.
"""

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import (
    QWidget,
    QFrame,
    QHBoxLayout,
    QVBoxLayout,
    QGroupBox,
    QPushButton,
    QLabel,
    QComboBox,
    QScrollArea,
    QSpinBox,
    QDoubleSpinBox,
    QTextEdit,
    QSizePolicy,
    QMessageBox,
)

from gui.utils.logger import logger
from gui.utils.models import SessionData, VideoPosition, FrameReviewData
from gui.backend.review_backend import ReviewBackend
from gui.widgets.review_metrics_table import ReviewMetricsTable


class ReviewView(QWidget):
    """
    Unified Orchestration & Correction View for Human-in-the-Loop video reviews.

    Combines the sidebar options and view window management into a single class.
    Stays floating on top of the main workspace canvas.

    Attributes:
        apply_override_requested (Signal): Signal emitted when an override correction is requested.
        save_session_requested (Signal): Signal emitted when saving the session dataset is requested.
        note_added (Signal): Signal emitted when the operator modifies the text notes area.
        review_backend (ReviewBackend): The underlying execution engine managing the current review session data state.
        landmarks (Any): Storage slot for human-in-the-loop tracking coordinate data.
        scores_dict (dict): Dictionary mapping metric fields to their extracted or calculated ergonomic scores.
        current_idx (int): The currently focused individual video timeline frame tracking index.
        scroll_area (QScrollArea): Inner viewport scroll framing area widget.
        container (QWidget): Central structural block layout containing panel elements.
        metrics_table (ReviewMetricsTable): Embedded spreadsheet viewport tracking multi-variable data outputs.
        lbl_scope (QLabel): Descriptive range text marker layout element.
        combo_scope (QComboBox): Range constraint drop-down target selection object.
        spin_start (QSpinBox): Lower framework timeline margin selection slider layout piece.
        spin_end (QSpinBox): Upper framework timeline margin selection slider layout piece.
        lbl_field (QLabel): Descriptive drop-down variable listing text marker layout element.
        combo_fields (QComboBox): Active column tracking field context selection drop-down selector.
        lbl_field_value (QLabel): Real-time numeric variable value view update tracker wrapper text label.
        lbl_value (QLabel): Manual entry field descriptor string line element widget.
        spin_value (QDoubleSpinBox): Numeric user entry point viewport tracking configuration container element.
        btn_apply (QPushButton): Control click workflow mutation request emitter action component.
        txt_notes (QTextEdit): Text logging viewport canvas component panel region interface box.
        btn_save (QPushButton): Local workspace text format commit layout operator command interface button.
        status_label (QTextEdit): Visual debugging data pipeline readout status screen pane block.

    Methods:
        sync_frame_review_data: Intercepts frame packets to populate fields before routing to the metrics table.
        sync_video_position: Updates the backend state with the currently active video player layout position frame index.
        update_session_data: Loads a newly updated ergonomic analysis folder data packet layer onto the UI layout.
        set_status: Updates the visual text message console stream box widget inside the view.
        _setup_ui: Instantiates, structures, and configures the graphical view widgets layout chain.
        _connect_signals: Attaches view action events and incoming back-end notification slots to event paths.
        _handle_scope_changed: Updates numeric boundary limits view component edit availability state selections.
        _handle_combo_field_changed: Refreshes real-time numeric variables content metadata context displays.
        _handle_apply_clicked: Formulates multi-frame timeline mutation processing arguments to apply variable value modifications.
        _on_save_session: Confirms data commits with interactive platform graphical alert window diagnostics boxes.
    """

    apply_override_requested = Signal(int, int, str, float)
    save_session_requested = Signal()
    note_added = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        # 1. Floating Windows Configuration
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowTitle("Video Review Suite")
        self.resize(420, 850)

        # Initialize Data Layer
        self.review_backend = ReviewBackend()
        self.landmarks = None
        self.scores_dict = None
        self.current_idx = None

        # Build UI
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """
        Instantiates, structures, and configures the graphical view widgets layout chain.

        Returns:
            None (None): Creates the layout configuration internally.
        """
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)

        # Scroll Engine Wrapper
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        self.container = QWidget()
        self.container.setFixedWidth(390)
        self.container.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding
        )
        self.scroll_area.setWidget(self.container)

        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        # --- SESSION TERMINAL MONITOR ---
        self.session_label = QTextEdit()
        self.session_label.setReadOnly(True)
        self.session_label.setPlainText(self.tr("CURRENT SESSION: None"))
        self.session_label.setFrameShape(QFrame.Shape.NoFrame)
        self.session_label.viewport().setAutoFillBackground(False)
        self.session_label.setFixedHeight(30)
        self.session_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        layout.addWidget(self.session_label)

        # --- FRAME DATA MONITOR ---
        data_group = QGroupBox(self.tr("FRAME DATA SPECS"))
        data_lay = QVBoxLayout(data_group)

        self.metrics_table = ReviewMetricsTable(self)
        self.metrics_table.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.metrics_table.setMinimumHeight(380)

        data_lay.addWidget(self.metrics_table)
        layout.addWidget(data_group)

        # --- TARGET RANGE SELECTION ---
        scope_group = QGroupBox(self.tr("1. SCOPE TARGET"))
        scope_lay = QVBoxLayout(scope_group)

        self.lbl_scope = QLabel(self.tr("Apply Correction To:"))
        self.combo_scope = QComboBox()
        self.combo_scope.addItems(
            [
                self.tr("Current Frame Only"),
                self.tr("Custom Frame Range"),
                self.tr("Entire Recording Timeline"),
            ]
        )
        scope_lay.addWidget(self.lbl_scope)
        scope_lay.addWidget(self.combo_scope)

        range_ctrl_lay = QHBoxLayout()
        self.spin_start = QSpinBox()
        self.spin_start.setRange(0, 999999)
        self.spin_end = QSpinBox()
        self.spin_end.setRange(0, 999999)

        range_ctrl_lay.addWidget(QLabel("From:"))
        range_ctrl_lay.addWidget(self.spin_start)
        range_ctrl_lay.addWidget(QLabel("To:"))
        range_ctrl_lay.addWidget(self.spin_end)
        scope_lay.addLayout(range_ctrl_lay)
        layout.addWidget(scope_group)

        # --- SCORE & VARIABLE OVERRIDES ---
        override_group = QGroupBox(self.tr("2. ERGONOMIC ADJUSTMENTS"))
        override_lay = QVBoxLayout(override_group)

        self.lbl_field = QLabel(self.tr("Select Variable:"))
        self.combo_fields = QComboBox()

        self.lbl_field_value = QLabel(self.tr("No Variable Selected"))
        self.lbl_field_value.setFixedHeight(40)

        self.lbl_value = QLabel(self.tr("Enter Value Overrides:"))
        self.spin_value = QDoubleSpinBox()
        self.spin_value.setRange(0.0, 100.0)
        self.spin_value.setSingleStep(1.0)

        self.btn_apply = QPushButton(self.tr("⚡ APPLY CORRECTION"))
        self.btn_apply.setObjectName("ApplyBtn")
        self.btn_apply.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        override_lay.addWidget(self.lbl_field)
        override_lay.addWidget(self.combo_fields)
        override_lay.addWidget(self.lbl_field_value)
        override_lay.addWidget(self.lbl_value)
        override_lay.addWidget(self.spin_value)
        override_lay.addWidget(self.btn_apply)
        layout.addWidget(override_group)

        # --- OPERATOR NOTES & LOGGING ---
        notes_group = QGroupBox(self.tr("3. OPERATOR OBSERVATIONS"))
        notes_lay = QVBoxLayout(notes_group)
        self.txt_notes = QTextEdit()
        self.txt_notes.setPlaceholderText(
            self.tr(
                "Document any specific human adjustments, tracking failures, or workspace anomalies here..."
            )
        )
        self.txt_notes.setMinimumHeight(200)
        notes_lay.addWidget(self.txt_notes)
        layout.addWidget(notes_group)

        # --- PERSISTENCE OPERATIONS ---
        save_group = QGroupBox(self.tr("4. DATA EXPORT"))
        save_lay = QVBoxLayout(save_group)
        self.btn_save = QPushButton(self.tr("💾 COMMIT REVISIONS"))
        self.btn_save.setObjectName("SaveBtn")
        self.btn_save.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        save_lay.addWidget(self.btn_save)
        layout.addWidget(save_group)

        # --- STATUS TERMINAL MONITOR ---
        self.status_label = QTextEdit()
        self.status_label.setReadOnly(True)
        self.status_label.setPlainText(self.tr("REVIEW SUITE: INITIALIZED"))
        self.status_label.setFrameShape(QFrame.Shape.NoFrame)
        self.status_label.viewport().setAutoFillBackground(False)
        self.status_label.setFixedHeight(60)
        self.status_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        layout.addWidget(self.status_label)

        layout.addStretch()
        main_layout.addWidget(self.scroll_area)

    def _connect_signals(self) -> None:
        """
        Connects UI signals to their respective slots and handlers.

        Returns:
            None (None): Binds signals internally.
        """
        self.btn_apply.clicked.connect(self._handle_apply_clicked)
        self.btn_save.clicked.connect(self._on_save_session)
        self.txt_notes.textChanged.connect(
            lambda: self.note_added.emit(self.txt_notes.toPlainText())
        )
        self.combo_scope.currentIndexChanged.connect(self._handle_scope_changed)
        self.combo_fields.currentIndexChanged.connect(self._handle_combo_field_changed)

        # We route packets cleanly directly through our structured class slot
        self.review_backend.frame_review_ready.connect(self.sync_frame_review_data)
        self.review_backend.status_updated.connect(self.set_status)

    @Slot(FrameReviewData)
    def sync_frame_review_data(self, review_data: FrameReviewData) -> None:
        """
        Intercepts frame packets to populate fields before routing to the metrics table.

        Args:
            review_data (FrameReviewData): Structural incoming data frame tracking updates tracking container payload.

        Returns:
            None (None): Updates child variables cache tables and calls inner layouts updates functions.
        """
        if self.combo_fields.count() == 0 and review_data.scores_dict:
            self.combo_fields.blockSignals(True)
            self.combo_fields.addItems(list(review_data.scores_dict.keys()))
            self.combo_fields.blockSignals(False)
        if review_data.scores_dict:
            self.scores_dict = review_data.scores_dict
        # Pass the update downward to the table UI
        self.metrics_table.sync_frame_review_data(review_data)
        self.current_idx = review_data.frame_idx

    def _handle_scope_changed(self, index: int) -> None:
        """
        Updates numeric boundary limits view component edit availability state selections.

        Args:
            index (int): Dropdown tracking layout options position choice reference index value.

        Returns:
            None (None): Modifies visual visibility constraints states internally.
        """
        is_range = index == 1
        self.spin_start.setEnabled(is_range)
        self.spin_end.setEnabled(is_range)

    def _handle_combo_field_changed(self):
        """
        Refreshes real-time numeric variables content metadata context displays.

        Raises:
            ValueError: If internal `scores_dict` state object reference mapping tracks as empty.

        Returns:
            None (None): Updates the label text representation value layout fields directly.
        """
        selected_field = self.combo_fields.currentText()
        # If the combobox was cleared or is empty, return early gracefully
        if not selected_field:
            return

        if self.scores_dict is None:
            raise ValueError("No scores_dict")

        if selected_field not in self.scores_dict:
            return

        field_value = self.scores_dict[selected_field]
        lbl_field_value_text = f"Current Field Value is: {field_value}"
        self.lbl_field_value.setText(str(lbl_field_value_text))

    def _handle_apply_clicked(self) -> None:
        """
        Formulates multi-frame timeline mutation processing arguments to apply variable value modifications.

        Returns:
            None (None): Directs state variables values manipulation calls payload routing actions downward.
        """
        scope = self.combo_scope.currentIndex()
        field = self.combo_fields.currentText()
        val = self.spin_value.value()

        start, end = None, None

        if scope == 0:
            if self.current_idx is not None:
                start = end = self.current_idx
            else:
                return
        elif scope == 1:
            start, end = self.spin_start.value(), self.spin_end.value()
        elif scope == 2:
            start, end = 0, -1
        else:
            start, end = self.spin_start.value(), self.spin_end.value()

        self.review_backend.mutate_records(
            start_frame=start, end_frame=end, variable_field=field, override_value=val
        )

    @Slot(VideoPosition)
    def sync_video_position(self, video_position: VideoPosition):
        """
        Updates the backend state with the currently active video player layout position frame index.

        Args:
            video_position (VideoPosition): Data model payload container indicating frame index layout metrics positions.

        Returns:
            None (None): Commands data queries across active back-end data storage arrays.
        """
        # TODO NEED TO ADD CHECKING HERE..
        if not self.review_backend.current_joint_analysis_path:
            return
        self.review_backend.emit_frame_review_data(
            current_frame_idx=video_position.current_frame
        )

    @Slot(SessionData)
    def update_session_data(self, session_data: SessionData):
        """
        Loads a newly updated ergonomic analysis folder data packet layer onto the UI layout.

        Args:
            session_data (SessionData): Structural session properties directory context tracking info definition wrapper.

        Returns:
            None (None): Clears layout caches and repopulates visual selections data controls tracking targets lists.
        """
        success, message = self.review_backend.load_review_session(session_data)
        if success:
            fields = self.review_backend.get_dataset_fields()

            self.combo_fields.blockSignals(True)
            self.combo_fields.clear()
            self.combo_fields.addItems(fields)
            # TODO UPDATE THE SCORES DICT TOO , check twice but the get_score_list_from_video_source should be doing this already
            self.combo_fields.blockSignals(False)
            self.set_status(message)
            self.session_label.setPlainText(f"CURRENT SESSION: {session_data.name}")

            # Auto-populate table with frame 0 data when a session initializes
            self.review_backend.emit_frame_review_data(0)

            self.update()
        else:
            logger.error(f"Error: {message}")
            self.set_status(f"Error: {message}")

    @Slot()
    def _on_save_session(self) -> None:
        """
        Confirms data commits with interactive platform graphical alert window diagnostics boxes.

        Returns:
            None (None): Spawns operating system native desktop alert information dialogs blocks views.
        """
        if self.review_backend.commit_final_review():
            QMessageBox.information(
                self,
                self.tr("Success"),
                self.tr(
                    "Human corrections committed safely to disk as 'ergomocap_review.csv'."
                ),
            )
        else:
            QMessageBox.critical(
                self,
                self.tr("Error"),
                self.tr("Failed to finalize changes into review log."),
            )

    def set_status(self, text: str) -> None:
        """
        Updates the visual text message console stream box widget inside the view.

        Args:
            text (str): Raw tracking console information logging output display text lines string.

        Returns:
            None (None): Sets formatting content blocks values onto the interface window views directly.
        """
        self.status_label.setText(f"REVIEW STATUS: {text}")
