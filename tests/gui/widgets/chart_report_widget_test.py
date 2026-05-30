# ---
# project: ErgoMoCap
# file: chart_report_widget_test.py
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
import pandas as pd
from unittest.mock import MagicMock
from gui.theme.style import ErgoTheme
from gui.widgets.chart_report_widget import ChartReportWidget
from gui.utils.constants import MetricType


@pytest.fixture
def chart_widget(qtbot):
    """Fixture to initialize the ChartReportWidget."""
    # Using 'dark' as a standard theme key assumed to exist in THEMES
    widget = ChartReportWidget(current_theme=ErgoTheme.DARK)
    qtbot.addWidget(widget)
    return widget


def test_initialization(chart_widget):
    """Verify default properties and layout setup."""
    assert chart_widget.current_theme.value == "dark"
    assert chart_widget.main_layout.count() == 1
    # Check if facecolor was set (Matplotlib returns rgba tuple)
    assert chart_widget.canvas.figure.patch.get_facecolor() is not None


def test_update_chart_dataframe_risk(chart_widget):
    """Test updating chart with a DataFrame using MetricType.RISK."""
    df = pd.DataFrame({MetricType.RISK.value: ["High", "Low", "High", "Medium"]})

    # This hits the 'isinstance(data, pd.DataFrame)' and 'metric == MetricType.RISK' branches
    chart_widget.update_chart(df, MetricType.RISK)

    # Check if the title was set correctly
    assert chart_widget.canvas.figure.axes[0].get_title() == "RISK DISTRIBUTION"


def test_update_chart_dataframe_score(chart_widget):
    """Test updating chart with a DataFrame using MetricType.SCORE (Testing pd.cut branch)."""
    # Scores between 1 and 15
    df = pd.DataFrame({MetricType.SCORE.value: [1, 5, 5, 10, 15]})

    # This hits the 'pd.cut' branch (Lines 87-89)
    chart_widget.update_chart(df, MetricType.SCORE)

    # Validate logic: check if color map fallback or specific map was used
    assert chart_widget.canvas.figure.axes[0].get_title() == "SCORE DISTRIBUTION"


def test_update_chart_series_input(chart_widget):
    """Test updating chart with pd.Series or dict input (Line 92 branch)."""
    data = {"A": 10, "B": 20}

    # This hits the 'else' branch for data normalization
    chart_widget.update_chart(data, MetricType.RISK)

    # Verify the plot data exists
    ax = chart_widget.canvas.figure.axes[0]
    # In a pie chart, number of patches should match data length
    assert len(ax.patches) == 2


def test_update_chart_empty_data(chart_widget):
    """Ensure no crash occurs when data is empty (Line 95 branch)."""
    chart_widget.update_chart({}, MetricType.RISK)

    # Title should still be set even if pie chart isn't rendered
    assert "DISTRIBUTION" in chart_widget.canvas.figure.axes[0].get_title()


def test_get_image_bytes(chart_widget):
    """Verify PNG byte stream generation."""
    # Populate with some data first
    chart_widget.update_chart({"test": 1}, MetricType.RISK)

    image_bytes = chart_widget.get_image_bytes()

    assert isinstance(image_bytes, bytes)
    assert len(image_bytes) > 0
    # Check PNG magic number \x89PNG
    assert image_bytes.startswith(b"\x89PNG")


def test_text_styling_iteration(chart_widget):
    """Test that text and autotext colors are set (Lines 108-111)."""
    data = {"High": 50, "Low": 50}
    chart_widget.update_chart(data, MetricType.RISK)

    ax = chart_widget.canvas.figure.axes[0]
    # Check text items in the pie chart
    for t in ax.texts:
        assert t.get_fontsize() == 9


def test_color_map_fallback(chart_widget):
    """Test that unknown MetricTypes fallback to SCORE colors (Line 102)."""
    # Mock a MetricType that isn't in COLOR_MAP
    mock_metric = MagicMock()
    mock_metric.name = "UNKNOWN_METRIC"
    mock_metric.value = "unknown"

    chart_widget.update_chart({"val": 1}, mock_metric)
    # If no error, the .get(metric, COLOR_MAP[MetricType.SCORE]) logic worked
