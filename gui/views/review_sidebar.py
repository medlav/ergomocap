# logic

# Simply Use of the Video Canvas + Custom Sidebar/Control Bar
# to add variables to the whole video, parts of it or even
# frame by frame, with the opportunity of changing any
# score part to remove errors, basically a human post-processing suite
# for the operator to review the analysis and integrate extra info
#
#
#
#
#


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

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
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
    QSpinBox,
    QDoubleSpinBox,
)


class ReviewSidebar(QDockWidget):
    """
    A scrollable correction engine designed for manual human interventions.

    Sections:
    - TARGET FRAME CONTROL: Focus on a specific frame or select a wider frame index range.
    - SCORE & VARIABLE OVERRIDES: Change automated calculation errors on the fly.
    - ANNOTATIONS & NOTES: Inject operator observations directly into the session logs.
    - SAVE & PERSISTENCE: Write overrides back to the underlying session dataset.
    """

    # Signals to safely communicate state updates up to the view orchestrator
    apply_override_requested = Signal(int, int, str, float)  # start, end, field, value
    save_session_requested = Signal()
    note_added = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._setup_ui()
        self._connect_internal_signals()

    def _setup_ui(self) -> None:
        self.setObjectName("HitlSidebar")
        self.setFixedWidth(400)

        # Main Dock Window central wrapper
        self.main_container = QWidget()
        self.setWidget(self.main_container)
        main_layout = QVBoxLayout(self.main_container)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 1. Viewport Scroll Area Setup
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        # 2. Strict UI Canvas Containment Sizing
        self.container = QWidget()
        self.container.setFixedWidth(300)
        self.container.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding
        )
        self.scroll_area.setWidget(self.container)

        # 3. Layout Grid Construction
        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

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

        # Range index entry bars
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

        self.lbl_field = QLabel(self.tr("Select Discovered Variable:"))
        self.combo_fields = QComboBox()
        # Populated dynamically by backend columns, defaults provided as fallbacks
        self.combo_fields.addItems(
            ["RULA_SCORE", "REBA_SCORE", "TRUNK_SCORE", "NECK_SCORE", "LEGS_SCORE"]
        )

        self.lbl_value = QLabel(self.tr("Enter Adjusted Value Overrides:"))
        self.spin_value = QDoubleSpinBox()
        self.spin_value.setRange(0.0, 100.0)
        self.spin_value.setSingleStep(1.0)

        self.btn_apply = QPushButton(self.tr("⚡ APPLY CORRECTION"))
        self.btn_apply.setObjectName("ApplyBtn")

        override_lay.addWidget(self.lbl_field)
        override_lay.addWidget(self.combo_fields)
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
        self.txt_notes.setMaximumHeight(80)
        notes_lay.addWidget(self.txt_notes)
        layout.addWidget(notes_group)

        # --- PERSISTENCE OPERATIONS ---
        save_group = QGroupBox(self.tr("4. DATA EXPORT"))
        save_lay = QVBoxLayout(save_group)
        self.btn_save = QPushButton(self.tr("💾 COMMIT REVISIONS"))
        self.btn_save.setObjectName("SaveBtn")
        save_lay.addWidget(self.btn_save)
        layout.addWidget(save_group)

        layout.addStretch()

        # --- KEYBOARD FOCUS SANITIZATION ---
        self.btn_apply.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_save.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        # --- STATUS TERMINAL MONITOR ---
        self.status_label = QTextEdit()
        self.status_label.setReadOnly(True)
        self.status_label.setPlainText(self.tr("HITL SUITE: INITIALIZED"))
        self.status_label.setFrameStyle(QFrame.Shape.NoFrame)
        self.status_label.viewport().setAutoFillBackground(False)
        self.status_label.setMinimumHeight(100)
        self.status_label.setMaximumWidth(300)
        self.status_label.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding
        )
        self.status_label.setAlignment(
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft
        )
        layout.addWidget(self.status_label)

        # Lock Dock constraints
        self.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        self.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea)
        main_layout.addWidget(self.scroll_area)

    def _connect_internal_signals(self) -> None:
        self.btn_apply.clicked.connect(self._handle_apply_clicked)
        self.btn_save.clicked.connect(self.save_session_requested.emit)
        self.txt_notes.textChanged.connect(
            lambda: self.note_added.emit(self.txt_notes.toPlainText())
        )
        self.combo_scope.currentIndexChanged.connect(self._handle_scope_changed)

    def _handle_scope_changed(self, index: int) -> None:
        # Toggle range fields contextually based on choice scope items
        is_range = index == 1
        self.spin_start.setEnabled(is_range)
        self.spin_end.setEnabled(is_range)

    def _handle_apply_clicked(self) -> None:
        scope = self.combo_scope.currentIndex()
        field = self.combo_fields.currentText()
        val = self.spin_value.value()

        if scope == 0:  # Current Frame Only
            start, end = self.spin_start.value(), self.spin_start.value()
        elif scope == 2:  # Whole recording duration wildcard flag
            start, end = 0, -1
        else:  # Multi-frame block target range
            start, end = self.spin_start.value(), self.spin_end.value()

        self.apply_override_requested.emit(start, end, field, val)

    def sync_timeline_frame(self, current_frame: int) -> None:
        """Keeps the target boundaries linked with your timeline playback scrubber loop."""
        if self.combo_scope.currentIndex() == 0:
            self.spin_start.blockSignals(True)
            self.spin_end.blockSignals(True)
            self.spin_start.setValue(current_frame)
            self.spin_end.setValue(current_frame)
            self.spin_start.blockSignals(False)
            self.spin_end.blockSignals(False)

    def update_variable_dropdown(self, columns: list[str]) -> None:
        self.combo_fields.blockSignals(True)
        self.combo_fields.clear()
        self.combo_fields.addItems(columns)
        self.combo_fields.blockSignals(False)

    def set_status(self, text: str) -> None:
        self.status_label.setText(f"REVIEW STATUS: {text}")
