from PySide6.QtWidgets import (
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
)
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt
from gui.utils.models import FrameReviewData


class ReviewMetricsTable(QTableWidget):
    """
    Tabular display component rendering detailed ergonomic sub-scores and joint angle degrees.

    This specialized view widget organizes key-value telemetry payloads into categorized,
    user-scannable data grids without maintaining local heavy logic calculations.
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._initialize_table_properties()

    def _initialize_table_properties(self) -> None:
        """Configures the aesthetic layout framework variables for the data spreadsheet view."""
        self.setColumnCount(2)
        self.setHorizontalHeaderLabels(["Parameter", "Value"])
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.verticalHeader().setVisible(False)
        self.setAlternatingRowColors(True)

    def sync_frame_review_data(self, review_data: FrameReviewData) -> None:
        """
        Re-populates layout data rows inside the data grid directly from
        the data structural properties of our FrameReviewData contract.
        """
        self.setUpdatesEnabled(False)
        self.setRowCount(0)

        # --- 1. GLOBAL PROFILE METADATA SEGMENTS ---
        self._add_row_metric(
            "Timeline Frame Index",
            f"{review_data.frame_idx} / {review_data.total_frames}",
        )

        risk_label = review_data.risk.value if review_data.risk else "NEGLIGIBLE"
        score_label = str(review_data.score) if review_data.score is not None else "0"

        self._add_row_metric("Unified Evaluation Score", score_label)
        self._add_row_metric("Qualitative Risk Assignment", risk_label)

        # --- 2. DYNAMIC COMPONENT BREAKDOWNS (SCORES_DICT) ---
        if review_data.scores_dict:
            self._add_header_row("--- Score Components Breakdown ---")
            for body_part, localized_score in review_data.scores_dict.items():
                self._add_row_metric(str(body_part), str(localized_score))

        # --- 3. DYNAMIC KINEMATIC VARIABLES (JOINT_ANGLES) ---
        if review_data.joint_angles:
            self._add_header_row("--- Measured Kinematic Variables ---")
            for joint_name, kinematic_angle in review_data.joint_angles.items():
                try:
                    self._add_row_metric(
                        str(joint_name), f"{float(kinematic_angle):.2f}°"
                    )
                except (ValueError, TypeError):
                    self._add_row_metric(str(joint_name), str(kinematic_angle))

        self.setUpdatesEnabled(True)

    def _add_row_metric(self, name_label: str, value_label: str) -> None:
        """Appends a standard key-value string row data layout element."""
        row: int = self.rowCount()
        self.insertRow(row)

        name_item = QTableWidgetItem(name_label)
        value_item = QTableWidgetItem(value_label)
        value_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        self.setItem(row, 0, name_item)
        self.setItem(row, 1, value_item)

    def _add_header_row(self, group_title: str) -> None:
        """Appends a spanning structural subsection label divider."""
        row: int = self.rowCount()
        self.insertRow(row)

        header_item = QTableWidgetItem(group_title)
        header_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
        header_item.setBackground(QColor("#2d3f50"))
        header_item.setForeground(QColor("#ffffff"))

        self.setItem(row, 0, header_item)
        self.setSpan(row, 0, 1, 2)
