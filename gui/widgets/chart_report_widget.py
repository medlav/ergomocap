# ---
# project: ErgoMoCap
# file: chart_report_widget.py
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
ErgoMoCap: Chart Report Widget
------------------------------
Specialized Visualization Component for Ergonomic Analytics.

This module provides the `ChartReportWidget`, which encapsulates Matplotlib
functionality within the PySide6 ecosystem. It is designed to handle the
automated preprocessing and rendering of ergonomic risk and score distributions.

The widget integrates with the [THEMES][gui.theme.style] configuration
to ensure visual consistency across the ErgoMoCap dashboard.
"""

from io import BytesIO
import pandas as pd
from typing import Union
from PySide6.QtWidgets import QWidget, QVBoxLayout
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from gui.theme.style import THEMES, ErgoTheme
from gui.utils.constants import MetricType

# Strategic color constants
COLOR_MAP = {
    MetricType.RISK: ["#9d001d", "#fc002e", "#f99602", "#f5db5a", "#9ece6a"],
    MetricType.SCORE: [
        "#ff0e3a",
        "#ff5d4b",
        "#fd9c0b",
        "#e0af68",
        "#f5ed4d",
        "#9ece6a",
        "#4dd6ee",
        "#0eebff",
    ],
}


class ChartReportWidget(QWidget):
    """
    Encapsulated Matplotlib widget for ErgoMoCap.

    Handles rendering of ergonomic distributions and provides utility methods for
    capturing figure states as raw byte streams for document generation.

    Attributes:
        current_theme (ErgoTheme): The active UI theme name (e.g., "dark", "light").
        canvas (FigureCanvasQTAgg): The Qt-compatible drawing surface for Matplotlib figures.
        main_layout (QVBoxLayout): The primary layout container.

    Methods:
        update_chart: Hyper-abstracted update method for data visualization (preprocesses and renders pie charts).
        get_image_bytes: Captures the current figure as a PNG-formatted byte stream for PDF/DOCX export.
    """

    def __init__(self, current_theme: ErgoTheme, parent=None):
        """
        Initialize the Chart Report Widget.

        Args:
            current_theme (ErgoTheme): The initial theme identifier used for styling.
            parent (QWidget | None): The parent widget. Defaults to `None`.

        Returns:
            None (None): Initializer return.
        """
        super().__init__(parent)
        self.current_theme = current_theme
        self.canvas = FigureCanvasQTAgg(Figure(figsize=(4, 4), dpi=100))
        self.canvas.figure.patch.set_facecolor(THEMES[self.current_theme]["background"])

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(self.canvas)

    def update_chart(
        self, data: Union[pd.DataFrame, pd.Series, dict], metric: MetricType
    ):
        """
        Hyper-abstracted update method for data visualization.

        This method handles DataFrame preprocessing, value counting, and binning
        automatically based on the provided [MetricType][gui.utils.constants.MetricType].
        It renders the results as a pie chart styled according to the project's color maps.

        [Figure][matplotlib.figure.Figure]

        Args:
            data (pd.DataFrame | pd.Series | dict): The source data to visualize.
                Can be a full project `DataFrame` or pre-summarized data.
            metric (MetricType): The type of ergonomic metric being plotted.

        Returns:
            None (None): Clears and redraws the `canvas`.
        """
        self.canvas.figure.clear()
        ax = self.canvas.figure.add_subplot(111)
        theme: dict[str, str] = THEMES[self.current_theme]
        bg_color: str = theme["background"]
        self.canvas.figure.patch.set_facecolor(bg_color)
        ax.set_facecolor(bg_color)
        # 1. Data Normalization
        if isinstance(data, pd.DataFrame):
            raw = data[metric.value]
            plot_data = (
                raw.value_counts()
                if metric == MetricType.RISK
                else pd.cut(
                    raw, bins=range(32), labels=[str(i) for i in range(1, 32)]
                ).value_counts()
            )
        else:
            plot_data = pd.Series(data)

        plot_data = plot_data[plot_data > 0]
        # 2. Rendering Logic
        if not plot_data.empty:
            # Unpack safely using a single variable to satisfy Pylance's Union type
            results = ax.pie(
                plot_data,
                labels=[str(i) for i in plot_data.index],
                autopct="%1.1f%%",
                colors=COLOR_MAP.get(metric, COLOR_MAP[MetricType.SCORE]),
                startangle=140,
                pctdistance=0.8,
            )

            # The type is tuple[list, list] | tuple[list, list, list]
            # We only iterate over what exists
            for text_list in results[1:]:  # Captures both 'texts' and 'autotexts'
                for t in text_list:
                    t.set_color(theme["text_primary"])
                    t.set_fontsize(9)

        # 3. Dynamic Metadata
        title = self.tr(f"{metric.name.replace('_', ' ')} DISTRIBUTION")
        ax.set_title(title, color=theme["accent"], fontweight="bold", pad=20)

        self.canvas.figure.tight_layout()

        self.canvas.draw()

    def get_image_bytes(self) -> bytes:
        """
        Captures the current figure for PDF/DOCX export.

        [Figure.savefig][matplotlib.figure.Figure.savefig]

        Returns:
            bytes (bytes): A PNG-formatted byte stream of the current Matplotlib figure.
        """
        buf = BytesIO()
        self.canvas.figure.savefig(buf, format="png")
        return buf.getvalue()
