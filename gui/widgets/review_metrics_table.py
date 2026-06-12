"""
ErgoMoCap: Review Metrics Table View
------------------------------------
Tabular Telemetry Display Widget for Ergonomic Data Presentation.

This module implements the `ReviewMetricsTable`, a specialized `QTableWidget` sub-component
designed to render real-time ergonomic telemetry outputs. It parses dynamic sub-scores
and physical joint kinematic angle values from incoming frame packets, organizing them
into clear, user-scannable categorical groups.

The table serves as a pure structural visualizer within the human-in-the-loop
review workflow, offloading all raw calculation logic to the underlying back-end data engines.
"""

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

    Methods:
        sync_frame_review_data: Re-populates layout data rows inside the data grid directly from the data structural properties of our FrameReviewData contract.
        _initialize_table_properties: Configures the aesthetic layout framework variables for the data spreadsheet view.
        _add_row_metric: Appends a standard key-value string row data layout element.
        _add_header_row: Appends a spanning structural subsection label divider.
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._initialize_table_properties()

    def _initialize_table_properties(self) -> None:
        """
        Configures the aesthetic layout framework variables for the data spreadsheet view.

        Returns:
            None (None): Modifies row, column, header, and selection properties internally.
        """
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
        Re-populates layout data rows inside the data grid directly from the data structural properties of our FrameReviewData contract.

        Args:
            review_data (FrameReviewData): Structural frame packet payload container housing evaluated ergonomic scores, risk designations, and angular telemetry.

        Returns:
            None (None): Disables UI paint triggers, flushes existing rows, maps clean strings data collections, and re-enables layout paint updates.
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
        """
        Appends a standard key-value string row data layout element.

        Args:
            name_label (str): Text tag string describing the target parameter column label row entry.
            value_label (str): Numeric evaluation rating or geometric calculation scale text label value string.

        Returns:
            None (None): Mutates table matrix elements structural entries states.
        """
        row: int = self.rowCount()
        self.insertRow(row)

        name_item = QTableWidgetItem(name_label)
        value_item = QTableWidgetItem(value_label)
        value_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        self.setItem(row, 0, name_item)
        self.setItem(row, 1, value_item)

    def _add_header_row(self, group_title: str) -> None:
        """
        Appends a spanning structural subsection label divider.

        Args:
            group_title (str): Grouping subsection text label identifier sequence content.

        Returns:
            None (None): Inserts styled background structural division elements across active columns pathways.
        """
        row: int = self.rowCount()
        self.insertRow(row)

        header_item = QTableWidgetItem(group_title)
        header_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
        header_item.setBackground(QColor("#2d3f50"))
        header_item.setForeground(QColor("#ffffff"))

        self.setItem(row, 0, header_item)
        self.setSpan(row, 0, 1, 2)
