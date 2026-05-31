# ---
# project: ErgoMoCap
# file: report_view.py
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
ErgoMoCap: Report View
----------------------
Analytics Dashboard and Visualization Module for Ergonomic Assessment.

This module implements the `ReportView` class, the primary user interface for
post-analysis data review. It integrates Matplotlib for data visualization,
Pandas for dataset manipulation, and a Strategy-based reporting widget to
display multi-method results (RULA/REBA).

The view supports professional document generation (PDF/DOCX) by communicating
with the [ReportBackend][gui.backend.report_backend.ReportBackend].

Key Features:
    * Data visualization using Matplotlib pie charts.
    * Dynamic metric calculation via Pandas.
    * Professional reporting in PDF (via Jinja2/QtPrintSupport) and DOCX (via DocxTemplate).
"""

from io import BytesIO
import pandas as pd
from pathlib import Path
from PySide6.QtWidgets import (
    QMainWindow,
    QTextEdit,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QPushButton,
    QFileDialog,
    QMessageBox,
)
from PySide6.QtCore import Slot
from PySide6.QtPrintSupport import QPrinter
from PySide6.QtGui import QTextDocument, QIcon, Qt

from gui.theme.style import ErgoTheme
from gui.utils.app_paths import ErgoPaths
from gui.utils.constants import AssessmentMethod, MetricType
from gui.backend.report_backend import ReportBackend
# from gui.widgets.menu_bar import menu_bar

# Add these to your imports at the top
from gui.utils.models import (
    ErrorInfo,
    ReportData,
    ReportExportRequest,
    ReportExportResult,
)
from gui.widgets.chart_report_widget import ChartReportWidget
from gui.core.report_strategies import RebaStrategy, RulaStrategy
from gui.widgets.table_report_widget import TableReportWidget


# from gui.utils.logger import logger TODO implement logger


class ReportView(QMainWindow):
    """
    The main dashboard window for ergonomic report generation and visualization.

    This class provides a comprehensive interface to load analysis datasets,
    visualize risk distributions through interactive charts, and export data
    into medical-grade reports.

    Attributes:
        current_theme (ErgoTheme): The active UI theme configuration.
        current_method (AssessmentMethod): The active assessment protocol (e.g., REBA, RULA).
        current_strategy (RebaStrategy | RulaStrategy): The active evaluation strategy logic.
        backend (gui.backend.report_backend.ReportBackend): The processing engine for data and exports.
        current_file (Path | None): File path to the active dataset.
        sidebar (QFrame): The navigation and control sidebar widget.
        btn_import (QPushButton): Button to trigger data loading.
        btn_pdf (QPushButton): Button to trigger PDF report export.
        btn_docx (QPushButton): Button to trigger Word document export.
        file_info (QTextEdit): Text area displaying information about the loaded file.
        card_total (QFrame): Dashboard card displaying total frames processed.
        card_avg (QFrame): Dashboard card displaying average risk score.
        chart_risk (gui.widgets.chart_report_widget.ChartReportWidget): Matplotlib canvas for risk level distribution.
        chart_score (gui.widgets.chart_report_widget.ChartReportWidget): Matplotlib canvas for total score frequency.
        report_widget (gui.widgets.table_report_widget.TableReportWidget): The dynamic table display for metrics.

    Methods:
        __init__: Initialize the Report View dashboard.
        _setup_ui: Initializes the graphical user interface layout and components.
        _create_stat_card: Factory method to create a stylized 'Stat Card' for the dashboard.
        _connect_signals: Connects UI signals to their respective backend slots and handlers.
        _handle_export_success: Slot to handle the UI notification after a successful file export.
        _handle_error: Slot to handle and display error messages from the backend.
        _on_data_ready: Internal slot triggered when the backend finishes processing data.
        _handle_import_dialog: Triggers a QFileDialog to allow users to select a new data source.
        _handle_pdf_request: GUI-side handling of PDF printing requests.
        _print_pdf: Renders the generated HTML report to a PDF file using Qt's print system.
        _handle_docx_request: Trigger backend export with a screenshot of the current chart.
        _update_charts: Logic outsourced to specialized chart widgets for Matplotlib rendering.
        set_method: Update the active ergonomic assessment method.
        update_current_strategy: Synchronize the UI strategy with the currently selected assessment method.
    """

    #############################################
    # --- Start of Initialization Functions --- #

    def __init__(
        self,
        parent,
        initial_csv: str | None = None,
        current_theme=ErgoTheme.DARK,
        current_method=AssessmentMethod.REBA,
    ) -> None:
        """
        Initialize the Report View dashboard.

        Args:
            parent (QWidget | None): The parent widget of this window.
            initial_csv (str | None): Optional path to a CSV file to load on startup.
            current_theme (ErgoTheme): The initial theme identifier. Defaults to "dark".
            current_method (AssessmentMethod): The initial assessment method. Defaults to AssessmentMethod.REBA.

        Returns:
            None (None): Initializer return.
        """
        super().__init__(parent)

        self.setWindowFlags(Qt.WindowType.Window)

        self.current_theme: ErgoTheme = current_theme
        self.current_method: AssessmentMethod = current_method
        self.current_strategy = RebaStrategy()
        self.backend = ReportBackend()
        self.current_file: Path | None = Path(initial_csv) if initial_csv else None

        self.setWindowTitle(self.tr("ErgoMoCap Reports"))
        self.resize(1280, 720)
        icon_path: Path = ErgoPaths.LOGO
        self.setWindowIcon(QIcon(str(icon_path)))

        self._setup_ui()
        self._connect_signals()
        self.update_current_strategy()

        if self.current_file:
            self.backend.load_data_and_run(self.current_file)

    def _setup_ui(self) -> None:
        """
        Initializes the graphical user interface layout and components.

        This method constructs a hierarchical nested layout consisting of:
        1. A top-level vertical layout to host the global menu_bar.
        2. A horizontal content area containing a Sidebar and a Dashboard.
        3. Stylized stat cards, Matplotlib canvases, and a reporting table.

        References internal components like [TableReportWidget][gui.widgets.table_report_widget.TableReportWidget].

        Returns:
            None (None): Modifies the window state in-place.

        Note:
            Requires the following instance attributes to be pre-initialized:
            - `THEMES`: A `dict` containing color hex codes.
            - `current_theme`: A `str` ("light" or "dark") for theme selection.
        """

        central_widget: QWidget = QWidget()
        self.setCentralWidget(central_widget)

        # ROOT LAYOUT (Vertical)
        root_layout: QVBoxLayout = QVBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # CONTENT AREA (Horizontal)
        content_layout: QHBoxLayout = QHBoxLayout()
        content_layout.setSpacing(0)
        root_layout.addLayout(content_layout)

        # --- SIDEBAR ---
        self.sidebar: QFrame = QFrame()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(260)
        side_layout: QVBoxLayout = QVBoxLayout(self.sidebar)

        lbl_menu: QLabel = QLabel(self.tr("REPORT CONTROLS"))
        lbl_menu.setProperty("class", "h2")

        self.btn_import: QPushButton = QPushButton(self.tr("📁 LOAD DATA"))

        self.btn_pdf: QPushButton = QPushButton(self.tr("📜 EXPORT TO PDF"))
        self.btn_pdf.setEnabled(False)

        self.btn_docx: QPushButton = QPushButton(self.tr("📄 EXPORT TO DOCX"))
        self.btn_docx.setEnabled(False)

        side_layout.addWidget(lbl_menu)
        side_layout.addSpacing(20)
        side_layout.addWidget(self.btn_import)
        side_layout.addSpacing(10)
        side_layout.addWidget(self.btn_pdf)
        side_layout.addWidget(self.btn_docx)
        side_layout.addStretch()

        # Create a QTextEdit instead of a QLabel
        self.file_info: QTextEdit = QTextEdit()
        self.file_info.setReadOnly(True)
        self.file_info.setText(self.tr("No file loaded"))

        # Styling it to look like a label
        self.file_info.setFrameStyle(QFrame.Shape.NoFrame)
        self.file_info.viewport().setAutoFillBackground(False)
        self.file_info.setFixedHeight(150)

        side_layout.addWidget(self.file_info)

        # --- DASHBOARD ---
        dashboard = QWidget()
        dash_lay = QVBoxLayout(dashboard)

        # Stats
        stats_row = QHBoxLayout()
        self.card_total = self._create_stat_card(
            self.tr("TOTAL FRAMES"), "0", "total_val"
        )
        self.card_avg = self._create_stat_card(
            self.tr("AVERAGE SCORE"), "0.0", "avg_val"
        )
        stats_row.addWidget(self.card_total)
        stats_row.addWidget(self.card_avg)
        dash_lay.addLayout(stats_row)

        # Charts (Utilizing specialized ChartReportWidget)
        chart_row = QHBoxLayout()
        self.chart_risk = ChartReportWidget(self.current_theme)
        self.chart_score = ChartReportWidget(self.current_theme)
        chart_row.addWidget(self.chart_risk)
        chart_row.addWidget(self.chart_score)
        dash_lay.addLayout(chart_row)

        # Table
        self.report_widget = TableReportWidget(
            title=self.current_method.name, strategy=self.current_strategy
        )
        dash_lay.addWidget(self.report_widget)

        content_layout.addWidget(self.sidebar)
        content_layout.addWidget(dashboard)

    def _create_stat_card(self, title: str, value: str, internal_name: str) -> QFrame:
        """
        Factory method to create a stylized 'Stat Card' for the dashboard.

        Args:
            title (str): The label for the metric (e.g., "AVG REBA SCORE").
            value (str): The initial value to display.
            internal_name (str): The unique ID used to update the label text later.

        Returns:
            QFrame (QFrame): A stylized frame containing the metric labels.
        """
        card: QFrame = QFrame()
        card.setObjectName("blockquote")

        lay: QVBoxLayout = QVBoxLayout(card)

        v_lbl: QLabel = QLabel(value)
        v_lbl.setObjectName(internal_name)
        v_lbl.setProperty("class", "h3")

        t_lbl: QLabel = QLabel(title)
        t_lbl.setProperty("class", "text-muted")

        lay.addWidget(t_lbl)
        lay.addWidget(v_lbl)

        return card

    def _connect_signals(self) -> None:
        """
        Connects UI signals to their respective backend slots and handlers.

        Returns:
            None (None): Establishes signal-slot connections.
        """
        self.btn_import.clicked.connect(self._handle_import_dialog)
        self.btn_pdf.clicked.connect(self._handle_pdf_request)
        self.btn_docx.clicked.connect(self._handle_docx_request)
        self.backend.data_processed.connect(self._on_data_ready)
        self.backend.pdf_html_ready.connect(self._print_pdf)
        self.backend.report_export_finished.connect(self._handle_export_success)
        self.backend.error_occurred.connect(self._handle_error)

    # --- End of Initialization Functions --- #
    ###########################################

    #############################################
    # --- Slots for Backend Comunication
    #############################################

    @Slot(ReportExportResult)
    def _handle_export_success(self, report_export_result: ReportExportResult):
        """
        Slot to handle the UI notification after a successful file export.

        Args:
            report_export_result (ReportExportResult): Data class object containing details of the export result.

        Returns:
            None (None): Triggers a `QMessageBox`.
        """
        if report_export_result.success:
            QMessageBox.information(
                self, self.tr("Success"), report_export_result.message
            )

    @Slot(ErrorInfo)
    def _handle_error(self, error_info):
        """
        Slot to handle and display error messages from the backend.

        Args:
            error_info (ErrorInfo): Data class object containing the error title and descriptive message.

        Returns:
            None (None): Triggers a critical `QMessageBox`.
        """
        QMessageBox.critical(self, error_info.title, error_info.message)

    @Slot(ReportData)
    def _on_data_ready(self, report_data: ReportData) -> None:
        """
        Internal slot triggered when the backend finishes processing data.

        Args:
            report_data (ReportData): ReportData from report backend
        Returns:
            None (None): Populates the dashboard UI with live data.
        """
        # Pylance-safe casting for finding children in the themed cards
        total_lbl = self.card_total.findChild(QLabel, "total_val")
        if isinstance(total_lbl, QLabel):
            total_lbl.setText(str(report_data.total_frames))

        avg_lbl = self.card_avg.findChild(QLabel, "avg_val")
        if isinstance(avg_lbl, QLabel):
            avg_lbl.setText(f"{report_data.average_score:.2f}")

        # print(summary) TODO print_reactivate

        self.update_current_strategy()
        self.report_widget.update_results(report_data.summary_dict)
        self._update_charts(report_data.df)
        self.btn_pdf.setEnabled(True)
        self.btn_docx.setEnabled(True)
        self.file_info.setPlainText(
            f"Analysis Run on data from:\n{report_data.file_path}"
        )

    #############################################
    # --- Handle Import Requests (Import Buttons)
    #############################################

    def _handle_import_dialog(self) -> None:  # TODO fix not working
        """
        Triggers a QFileDialog to allow users to select a new data source.

        Supports .csv and .xlsx extensions. If a path is selected, it triggers
        the `load_data_and_run` method in the [ReportBackend][gui.backend.report_backend.ReportBackend].

        Returns:
            None (None): Updates the report backend with the new file path.
        """
        path: str | None = None
        path, _ = QFileDialog.getOpenFileName(
            self, self.tr("Open Data"), "", self.tr("Data Files (*.csv *.xlsx)")
        )
        if path:
            self.backend.load_data_and_run(Path(path))

    #############################################
    # --- Handle Export Requests (Export Buttons)
    #############################################

    def _handle_pdf_request(self) -> None:
        """
        GUI-side handling of PDF printing (requires access to Printer/Canvas).

        Captures the current Matplotlib buffer as `bytes` and passes it to the
        [ReportBackend][gui.backend.report_backend.ReportBackend] for template rendering.

        Returns:
            None (None): Triggers the PDF generation sequence.
        """

        # Capture chart as bytes to send to backend (thread-safe way to handle images)
        buf = BytesIO()
        self.chart_score.canvas.figure.savefig(
            buf, format="png"
        )  # using only chart_score score distribution (instead of risk dostribution)
        chart_bytes = buf.getvalue()

        self.backend.prepare_pdf_export(
            ReportExportRequest(save_path=Path(""), chart_data=chart_bytes)
        )

    def _print_pdf(self, html: str) -> None:
        """
        Renders the generated HTML report to a PDF file using Qt's print system.

        Args:
            html (str): The rendered HTML content from the Jinja2 template.

        Returns:
            None (None): Generates the physical PDF file.

        Raises:
            Exception (Exception): If the printer or document fails to write to the path.
        """

        try:
            filename, _ = QFileDialog.getSaveFileName(
                self, self.tr("Save PDF"), "", self.tr("PDF Files (*.pdf)")
            )
            if filename:
                doc: QTextDocument = QTextDocument()
                doc.setHtml(html)

                printer: QPrinter = QPrinter(QPrinter.PrinterMode.HighResolution)
                printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
                printer.setOutputFileName(filename)

                doc.print_(printer)

                if (
                    printer.outputFileName() == filename
                ):  # Checks if user confirmed the save, pass if cancelled the save in file dialog
                    QMessageBox.information(
                        self, self.tr("Success"), self.tr("PDF Generated.")
                    )
                else:
                    pass
        except Exception as e:
            QMessageBox.critical(self, self.tr("Export Error"), str(e))

    def _handle_docx_request(self) -> None:
        """
        Trigger backend export with a screenshot of the current chart.

        Converts the `chart_risk` canvas into a `bytes` buffer for insertion into a
        DOCX template via the [ReportBackend][gui.backend.report_backend.ReportBackend].

        Returns:
            None (None): Initiates the Word document generation.
        """
        save_path, _ = QFileDialog.getSaveFileName(
            self, self.tr("Save Word"), "", "Word (*.docx)"
        )
        if not save_path:
            return

        # Capture chart as bytes to send to backend (thread-safe way to handle images)
        buf = BytesIO()
        self.chart_risk.canvas.figure.savefig(buf, format="png")
        chart_bytes = buf.getvalue()

        self.backend.export_to_docx(
            ReportExportRequest(save_path=Path(save_path), chart_data=chart_bytes)
        )

    #############################################
    # --- Charts Rendering with matplotlib
    #############################################

    def _update_charts(self, df: pd.DataFrame) -> None:
        """
        Logic outsourced to specialized chart widgets.

        Updates both the risk distribution and score frequency visualizations using
        the provided dataset.

        Args:
            df (pandas.DataFrame): The dataset containing ergonomic metrics.

        Returns:
            None (None): Redraws the Matplotlib canvases via the chart widgets.
        """
        self.chart_risk.update_chart(
            df,
            MetricType.RISK,
        )
        self.chart_score.update_chart(
            df,
            MetricType.SCORE,
        )

    #############################################
    # --- Public API to implement User Inputs ()
    #############################################

    def set_method(self, method: AssessmentMethod) -> None:
        """
        Update the active ergonomic assessment method.

        Args:
            method (AssessmentMethod): The name of the method to apply (e.g., AssessmentMethod.RULA, AssessmentMethod.REBA).

        Returns:
            None: Updates internal state and clears previous strategy if necessary.
        """
        if hasattr(self, "current_method") and self.current_method == method:
            return  # Don't recreate the strategy if it's the same
        if hasattr(self, "strategy"):
            self.strategy = None

        self.current_method = method

    def update_current_strategy(self):
        """
        Synchronize the UI strategy with the currently selected assessment method.

        Returns:
            None (None): Updates the `report_widget` with the correct
                [ReportStrategy][gui.core.report_strategies.ReportStrategy].
        """
        match self.current_method:
            case "REBA":
                self.current_strategy = RebaStrategy()

            case "RULA":
                self.current_strategy = RulaStrategy()

        self.report_widget.update_strategy(self.current_strategy)
        self.update()
