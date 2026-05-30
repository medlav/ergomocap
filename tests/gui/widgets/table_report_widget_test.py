# ---
# project: ErgoMoCap
# file: table_report_widget_test.py
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

import pytest
from unittest.mock import MagicMock
from PySide6.QtCore import Qt
from gui.widgets.table_report_widget import TableReportWidget
from gui.core.report_strategies import ReportStrategy, ResultRow


@pytest.fixture
def mock_strategy():
    """Create a mock strategy that returns a variety of row types."""
    strategy = MagicMock(spec=ReportStrategy)
    strategy.name = "TEST_STRATEGY"

    # Define a set of rows that covers all conditional branches in _insert_row
    strategy.format.return_value = [
        ResultRow(label="Header Section", value="", is_header=True),
        ResultRow(label="Normal Metric", value="Value"),
        ResultRow(label="Angle Metric", value=45.23, is_angle=True),
        ResultRow(label="Critical Metric", value="HIGH", is_critical=True),
    ]
    return strategy


@pytest.fixture
def table_report(qtbot, mock_strategy):
    """Fixture to initialize the TableReportWidget."""
    widget = TableReportWidget("Initial Title", mock_strategy)
    qtbot.addWidget(widget)
    return widget


def test_initialization(table_report):
    """Verify the widget sets up UI components correctly."""
    assert table_report.title_lbl.text() == "// INITIAL TITLE"
    assert table_report.table.columnCount() == 2
    assert table_report.table.horizontalHeaderItem(0).text() == "METRIC"
    assert table_report.table.horizontalHeaderItem(1).text() == "VALUE"


def test_update_results_execution(table_report, mock_strategy):
    """Test that update_results populates the table and clears old data."""
    data = {"dummy": "data"}

    # Run update
    table_report.update_results(data)

    # Verify strategy was called
    mock_strategy.format.assert_called_once_with(data)

    # Verify row count (4 rows defined in mock_strategy fixture)
    assert table_report.table.rowCount() == 4
    # Verify title updated to strategy name
    assert table_report.title_lbl.text() == "TEST_STRATEGY"


def test_insert_row_header_logic(table_report):
    """Test branch where is_header is True (Span and UserRole)."""
    row_data = ResultRow(label="Section", value="", is_header=True)
    table_report.table.setRowCount(0)
    table_report._insert_row(row_data)

    # Check UserRole data
    item = table_report.table.item(0, 0)
    assert item.data(Qt.ItemDataRole.UserRole) == "header"

    # Check Span (Column 0 spans 2 columns)
    assert table_report.table.columnSpan(0, 0) == 2


def test_insert_row_angle_formatting(table_report):
    """Test branch where is_angle is True and value is numeric."""
    row_data = ResultRow(label="Elbow", value=90, is_angle=True)
    table_report.table.setRowCount(0)
    table_report._insert_row(row_data)

    # Verify degree symbol and rounding
    assert table_report.table.item(0, 1).text() == "90.0°"


# def test_insert_row_critical_styling(table_report):
#     """Test branch where is_critical is True (Color and UserRole)."""
#     row_data = ResultRow(label="Risk", value="CRITICAL", is_critical=True)
#     table_report.table.setRowCount(0)
#     table_report._insert_row(row_data)
#  # TODO uncomment if you implement the crtical style, as of now is commented also in the code
#     value_item = table_report.table.item(0, 1)
#     assert value_item.data(Qt.ItemDataRole.UserRole) == "critical"
#     # Verify explicit color (Tokyo Night Orange)
#     assert value_item.foreground().color().name() == "#ff9e64"


def test_update_strategy(table_report):
    """Test swapping strategies."""
    new_strategy = MagicMock(spec=ReportStrategy)
    new_strategy.name = "NEW_STRAT"

    table_report.update_strategy(new_strategy)
    assert table_report.strategy == new_strategy

    # Verify text updates upon next result push
    new_strategy.format.return_value = []
    table_report.update_results({})
    assert table_report.title_lbl.text() == "NEW_STRAT"


def test_header_resize_modes(table_report):
    """Ensure the header sections are configured as requested (Coverage for init)."""
    header = table_report.table.horizontalHeader()
    assert header.sectionResizeMode(0) == header.ResizeMode.Stretch
    assert header.sectionResizeMode(1) == header.ResizeMode.Fixed
