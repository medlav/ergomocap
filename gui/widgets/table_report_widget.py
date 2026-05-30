# ---
# project: ErgoMoCap
# file: table_report_widget.py
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
ErgoMoCap: Table Report Widget
------------------------------
Standardized Tabular Visualization Component for Ergonomic Assessment Metrics.

This module provides the `TableReportWidget`, a high-level UI component used to display
complex calculation results in a clean, professional table format. It leverages a
Strategy-based architecture to handle different assessment protocols (RULA, REBA, etc.)
while maintaining a consistent look and feel.

The widget is designed to integrate with a custom CSS framework by utilizing specific
`ObjectNames` and `UserRole` data roles for dynamic styling.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


from gui.core.report_strategies import ReportStrategy, ResultRow


class TableReportWidget(QWidget):
    """
    A professional UI component that renders data based on the provided strategy.

    This widget provides a standardized interface for displaying ergonomic assessment
    results (such as RULA or REBA) within the ErgoMoCap GUI. It utilizes a strategy
    pattern to transform raw calculation data into formatted table rows and applies
    styling via `ObjectNames` for integration with the 'VOLKS-TYPO' CSS framework.

    Attributes:
        strategy (ReportStrategy): The active reporting protocol implementation.
        title (str): The title string used for the header label.
        main_layout (QVBoxLayout): The primary layout container.
        title_lbl (QLabel): The label displaying the assessment method name.
        table (QTableWidget): The internal table used to render metrics and values.

    Methods:
        update_results: Execute the current strategy and update the UI table with new data.
        update_strategy: Swap the current reporting strategy used by the widget.
        _insert_row: Insert and format a new row in the internal QTableWidget based on ResultRow properties.
    """

    def __init__(
        self, title: str, strategy: ReportStrategy, parent: QWidget | None = None
    ):
        """
        Initialize the analysis report widget.

        [ReportStrategy][gui.core.report_strategies.ReportStrategy]

        Args:
            title (str): The title string displayed in the header.
            strategy (ReportStrategy): An object implementing the strategy protocol.
            parent (QWidget | None): Optional parent widget. Defaults to `None`.

        Returns:
            None (None): Initializer return.
        """
        super().__init__(parent)
        self.strategy: ReportStrategy = strategy
        self.title: str = title

        self.main_layout: QVBoxLayout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        # Title with ObjectName for H3 styling
        self.title_lbl: QLabel = QLabel(f"// {title.upper()}")
        self.title_lbl.setObjectName("h3")
        self.main_layout.addWidget(self.title_lbl)

        # Table Setup
        self.table: QTableWidget = QTableWidget(0, 2)
        self.table.setObjectName("InfoTable")
        self.table.setHorizontalHeaderLabels(["METRIC", "VALUE"])
        self.table.verticalHeader().setVisible(False)
        # self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        header: QHeaderView = self.table.horizontalHeader()
        if header:
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
            self.table.setColumnWidth(1, 100)

        self.main_layout.addWidget(self.table)

    def update_results(
        self,
        summary_data: dict[str, str],
    ) -> None:
        """
        Execute the current strategy and update the UI table with new data.

        Args:
            summary_data (dict[str, str]): A `dict` containing the raw metric keys and values
                retrieved from the calculators.

        Returns:
            None (None): Clears the existing rows and repopulates the table in-place.
        """

        self.title_lbl.setText(self.strategy.name)

        self.table.setRowCount(0)

        formatted_rows = self.strategy.format(summary_data)

        for row_data in formatted_rows:
            self._insert_row(row_data)

    def _insert_row(self, row_data: ResultRow) -> None:
        """
        Insert and format a new row in the internal `QTableWidget`.

        Handles logic for spans (headers), alignment, and conditional formatting based on the
        properties of the provided `ResultRow`.

        [ResultRow][gui.core.report_strategies.ResultRow]

        Args:
            row_data (ResultRow): The data object containing values and formatting flags.

        Returns:
            None (None): Modifies the internal `table` state by appending a formatted row.
        """
        row_idx: int = self.table.rowCount()
        self.table.insertRow(row_idx)

        # Label Item
        label_text: str = f"  {row_data.label}"
        label_item = QTableWidgetItem(label_text)

        # Value Item
        display_val = row_data.value
        if row_data.is_angle and isinstance(display_val, (int, float)):
            display_val = f"{display_val:.1f}°"
        value_item: QTableWidgetItem = QTableWidgetItem(str(display_val))
        value_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        # Apply Visual Logic via Data Roles (Safe for CSS)
        if row_data.is_header:
            label_item.setData(Qt.ItemDataRole.UserRole, "header")
            value_item.setData(Qt.ItemDataRole.UserRole, "header")
            self.table.setSpan(row_idx, 0, 1, 2)

        # if row_data.is_critical:
        #     value_item.setData(Qt.ItemDataRole.UserRole, "critical")
        #     # Inline highlight for total clarity
        #     value_item.setBackground(QColor("#ff3c00")) TODO delete this

        self.table.setItem(row_idx, 0, label_item)
        self.table.setItem(row_idx, 1, value_item)

    def update_strategy(self, strategy: ReportStrategy) -> None:
        """
        Swap the current reporting strategy used by the widget.

        [ReportStrategy][gui.core.report_strategies.ReportStrategy]

        Args:
            strategy (ReportStrategy): The new strategy to apply for future updates.

        Returns:
            None (None): Updates the internal reference and triggers a widget redraw.
        """
        self.strategy: ReportStrategy = strategy
        self.update()
