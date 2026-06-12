# ---
# project: ErgoMoCap
# file: report_backend.py
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
ErgoMoCap: Report Backend
-------------------------
Logic and Data Processing for the ErgoMoCap Report System.

This module handles pure data manipulation (Pandas), metric calculations,
and template generation (Jinja2/DocxTemplate). It strictly avoids PySide6
GUI components (like QTextDocument or QPrinter) to ensure it can be safely
moved to a QThread for asynchronous execution without causing segfaults.

Key Features:
    * Asynchronous data parsing for CSV and Excel formats via `pandas.DataFrame`.
    * Thread-safe HTML report rendering using `jinja2` environments.
    * Synchronous DOCX generation with embedded Matplotlib visualizations.
    * Heuristic and strict column targeting for RULA/REBA assessment methods.
"""

import base64
from io import BytesIO
from pathlib import Path
from typing import Any

import pandas as pd
from docx.shared import Mm
from docxtpl import DocxTemplate, InlineImage
from jinja2 import Environment, FileSystemLoader, select_autoescape

from PySide6.QtCore import QObject, Signal, Slot

from gui.utils.logger import logger
from gui.utils.app_paths import ErgoPaths
from gui.utils.constants import AssessmentMethod, MetricType
from gui.utils.models import (
    ErrorInfo,
    ReportData,
    ReportExportRequest,
    ReportExportResult,
)
from gui.utils.utils import get_dynamic_metrics


class ReportBackend(QObject):
    """
    Data processing core for the Report module.

    This class serves as the backend controller for ergonomic report generation. It
    inherits from `QObject` to facilitate thread-safe communication via signals and
    slots, allowing data-intensive operations (like `pandas` parsing and `jinja2`
    rendering) to be offloaded to background threads. It handles file I/O,
    metric aggregation, and template preparation for both PDF and DOCX exports.

    Attributes:
        data_processed (Signal): Signal emitted with a [ReportData][gui.utils.models.ReportData] object when data is successfully loaded and processed.
        pdf_html_ready (Signal): Signal emitted with a `str` containing the fully rendered HTML markup ready for GUI-thread printing.
        report_export_finished (Signal): Signal emitted with a [ReportExportResult][gui.utils.models.ReportExportResult] instance upon completion of a document export.
        error_occurred (Signal): Signal emitted with an [ErrorInfo][gui.utils.models.ErrorInfo] object when an exception is caught during processing.
        current_file (Path | None): The absolute filesystem `Path` to the currently active data source, or `None` if no data is loaded.
        current_method (AssessmentMethod): The active assessment protocol configuration, defaults to [AssessmentMethod.REBA][gui.utils.constants.AssessmentMethod].
        template_dir (Path): The file system path locating the directory containing the Jinja2 and Word templates.
        jinja_env (Environment): The securely configured `jinja2.Environment` instance optimized with autoescaping for report compilation.

    Methods:
        load_data_and_run: Asynchronously loads and parses ergonomic data from a given CSV/Excel file.
        prepare_pdf_export: Compiles the HTML report context using Jinja2 and emits it.
        export_to_docx: Generates and saves a Word document report synchronously.
        get_chart_distribution_data: Calculates distributions using strict column targeting based on the active method.
    """

    # --- Signals ---

    data_processed = Signal(ReportData)

    # Emits: HTML string, target save path (Allows Frontend to handle GUI-printing)
    pdf_html_ready = Signal(str)

    # Emits: Success boolean, Status Message
    report_export_finished = Signal(ReportExportResult)

    # Emits: Error Title, Error Message
    error_occurred = Signal(ErrorInfo)

    def __init__(self) -> None:
        """
        Initializes the backend state and sets up secure template handling.

        Returns:
            None (None): Initializes the state attributes of the `ReportBackend` object.
        """
        super().__init__()
        self.current_file: Path | None = None
        self.current_method = AssessmentMethod.REBA

        # Bandit Security: Secure Jinja environment setup
        self.template_dir = ErgoPaths.TEMPLATES
        self.jinja_env = Environment(
            loader=FileSystemLoader(self.template_dir),
            autoescape=select_autoescape(["html", "xml", "j2"]),
        )

    @Slot(Path)
    def load_data_and_run(self, file_path: Path) -> None:
        """
        Asynchronously loads and parses ergonomic data from a given CSV/Excel file.

        This method performs heuristic column detection to find risk and score columns
        regardless of the assessment method. On success, it calculates primary metrics,
        structures them into a data container, and emits the `data_processed` signal.
        If the operation fails, an `error_occurred` signal containing structural error
        details is dispatched.

        Args:
            file_path (Path): Absolute filesystem path to the source data file (supports `.csv` and `.xlsx`).

        Returns:
            None (None): Results or errors are transmitted asynchronously via Qt Signals.

        Raises:
            ValueError (ValueError): Raised if the chosen file contains an empty dataset.
            KeyError (KeyError): Raised if critical score or risk tracking columns cannot be identified.
        """
        try:
            # Handle encoding and format fallbacks
            if file_path.suffix == ".xlsx":
                df: pd.DataFrame = pd.read_excel(file_path)
            else:
                try:
                    df: pd.DataFrame = pd.read_csv(file_path)
                except UnicodeDecodeError:
                    logger.error("pandas.read_csv Failed for an UnicodeError")
                    df: pd.DataFrame = pd.read_csv(file_path, encoding="latin-1")

            if df.empty:
                raise ValueError("The selected file contains no data.")

            score_col: str = MetricType.SCORE.value
            risk_col: str = MetricType.RISK.value

            df = df.dropna(subset=[score_col, risk_col])

            self.current_file = file_path

            # Calculate primary metrics
            total_frames: int = len(df)

            avg_score: float = df[score_col].mean() if total_frames > 0 else 0.0

            summary_rows: list[tuple[str, str]] = get_dynamic_metrics(
                df, MetricType.SCORE, self.current_method
            )

            # print(summary_rows, "SUMMARY ROWS", "\n") TODO print_reactivate

            summary: dict = dict(summary_rows)

            # print(summary, "SUMMARY ROWS", "\n") TODO print_reactivate

            # Transmit structured data to frontend
            processed_data = ReportData(
                df=df,
                file_path=file_path,
                total_frames=total_frames,
                average_score=avg_score,
                summary_dict=summary,
            )
            self.data_processed.emit(processed_data)

        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)
            self.error_occurred.emit(
                ErrorInfo(
                    title="Load Error",
                    message=f"Could not parse analysis data: {str(e)}",
                )
            )

    def update_method(self, method: AssessmentMethod) -> None:
        """
        Update the active ergonomic assessment method.

        Args:
            method (AssessmentMethod): The name of the method to apply (e.g., AssessmentMethod.RULA, AssessmentMethod.REBA).

        Returns:
            None (None): Updates internal state and clears previous strategy if necessary.
        """
        if hasattr(self, "current_method") and self.current_method == method:
            return  # Don't change if it's the same

        self.current_method = method

    def prepare_pdf_export(self, report_export_request: ReportExportRequest) -> None:
        """
        Compiles the HTML report context using Jinja2 and emits the generated markup.

        This method processes the active dataset file to map internal ergonomic metrics
        to template variables. It encodes the binary chart image bytes into a base64
        string representation suitable for direct HTML document embedding. The compiled
        HTML is transmitted via the `pdf_html_ready` signal, freeing the background thread
        from engaging in unsafe GUI-bound rendering calls.

        Args:
            report_export_request (ReportExportRequest): A structured data model instance containing the destination path and chart data.

        Returns:
            None (None): The structural HTML content string is emitted via signals.
        """
        if not self.current_file:
            self.error_occurred.emit(
                ErrorInfo(title="Export Error", message="No active data loaded.")
            )
            return

        try:
            # 1. Use existing dataframe or load securely
            # Note: If self.df is stored during load_data_and_run, use it here to avoid re-reading
            df = pd.read_csv(self.current_file)
            method_suffix = self.current_method.value.upper()  # "REBA" or "RULA"

            # 2. Get dynamic metrics (Calculates means and formats names)
            # Result is list[tuple("Trunk Score Rula", "3.45"), ...]
            metrics_list = get_dynamic_metrics(
                df, MetricType.SCORE, self.current_method
            )

            # Create a lookup map where keys are standardized title-case strings
            m_raw = {label: float(val) for label, val in metrics_list}

            # 3. Map to Jinja2 context (m)
            # We target the specific names generated by your utility: .replace("_", " ").title()
            context_metrics = {
                "n_frames": len(df),
                "confidenza": "90%",
                "durata": f"{len(df) / 30:.1f}s" if len(df) > 0 else "0.0s",
                "Trunk": m_raw.get(f"Trunk_Score_{method_suffix}", 0.0),
                "Neck": m_raw.get(f"Neck_Score_{method_suffix}", 0.0),
                "Legs": m_raw.get(f"Legs_Score_{method_suffix}", 0.0),
                "Upper_Arm": m_raw.get(f"Upper_Arm_Score_{method_suffix}", 0.0),
                "Lower_Arm": m_raw.get(f"Lower_Arm_Score_{method_suffix}", 0.0),
                "Wrist": m_raw.get(f"Wrist_Score_{method_suffix}", 0.0),
                # Scores A/B/C
                "Total_A": m_raw.get(f"Score_A_{method_suffix}", 0.0),
                "Total_B": m_raw.get(f"Score_B_{method_suffix}", 0.0),
                "Score_C": m_raw.get(f"Score_C_{method_suffix}", 0.0),
                # Final Score (Matches the "Final Score RULA" or "Final Score REBA" logic)
                "Final": m_raw.get(f"Final_Score_{method_suffix}", 0.0),
                "Method": method_suffix,
            }

            risk_col = next(
                (
                    c
                    for c in df.columns
                    if "RISK" in c.upper() or "RISCHIO" in c.upper()
                ),
                None,
            )
            risk_value = df[risk_col].mode()[0] if risk_col and not df.empty else "N/A"

            translated_risk = "N/A"

            match risk_value:
                case "negligible":
                    translated_risk = "trascurabile"
                case "low":
                    translated_risk = "basso"
                case "medium":
                    translated_risk = "medio"
                case "high":
                    translated_risk = "alto"
                case "very_high":
                    translated_risk = "altissimo"

            context_metrics["risk"] = translated_risk

            # Convert chart bytes to base64 for HTML embedding
            img_base64: str = base64.b64encode(report_export_request.chart_data).decode(
                "utf-8"
            )

            # Render Template securely
            template = self.jinja_env.get_template(f"{method_suffix}_report.j2")
            html: str = template.render(m=context_metrics, chart=img_base64)

            # Hand HTML back to main thread for printing
            self.pdf_html_ready.emit(html)

        except Exception as e:
            self.error_occurred.emit(
                ErrorInfo(title="PDF Preparation Error", message=str(e))
            )

    @Slot(ReportExportRequest)
    def export_to_docx(self, report_export_request: ReportExportRequest) -> None:
        """
        Generates and saves a Word document report synchronously.

        Utilizes `docxtpl` to inject calculated dynamic ergonomic metrics and an
        inline `matplotlib` chart layout directly into a pre-defined `.docx` template.
        This operation avoids direct GUI dependencies making it entirely safe for background
        thread execution. Completion status is dispatched via the `report_export_finished` signal.

        Args:
            report_export_request (ReportExportRequest): A data model instance containing the target file save path and raw chart image bytes.

        Returns:
            None (None): Operation results are outputted asynchronously via execution signals.
        """
        if not self.current_file:
            return

        try:
            df: pd.DataFrame = pd.read_csv(self.current_file)

            # print(df.columns)

            method_suffix = self.current_method.value.upper()

            metrics_list = get_dynamic_metrics(
                df, MetricType.SCORE, self.current_method
            )
            m_raw = {label: float(val) for label, val in metrics_list}

            # TODO make this programmatic, now is REBA centric

            context: dict[str, Any] = {
                "n_frames": len(df),
                "confidenza": "90%",
                "durata": f"{len(df) / 30:.1f}s" if len(df) > 0 else "0.0s",
                # Using the .title() format produced by your get_dynamic_metrics
                "tronco": m_raw.get(f"Trunk_Score_{method_suffix}", 0.0),
                "collo": m_raw.get(f"Neck_Score_{method_suffix}", 0.0),
                "gambe": m_raw.get(f"Legs_Score_{method_suffix}", 0.0),
                "braccio": m_raw.get(f"Upper_Arm_Score_{method_suffix}", 0.0),
                "avambraccio": m_raw.get(f"Lower_Arm_Score_{method_suffix}", 0.0),
                "polso": m_raw.get(f"Wrist_Score_{method_suffix}", 0.0),
                # Scores A/B/C and Final
                "tot_a": m_raw.get(f"Score_A_{method_suffix}", 0.0),
                "tot_b": m_raw.get(f"Score_B_{method_suffix}", 0.0),
                "score_c": m_raw.get(f"Score_C_{method_suffix}", 0.0),
                "score_finale": m_raw.get(f"Final_Score_{method_suffix}", 0.0),
            }

            risk_col = next(
                (
                    c
                    for c in df.columns
                    if "RISK" in c.upper() or "RISCHIO" in c.upper()
                ),
                None,
            )
            risk_value = df[risk_col].mode()[0] if risk_col and not df.empty else "N/A"
            translated_risk = "N/A"

            match risk_value:
                case "negligible":
                    translated_risk = "trascurabile"
                case "low":
                    translated_risk = "basso"
                case "medium":
                    translated_risk = "medio"
                case "high":
                    translated_risk = "alto"
                case "very_high":
                    translated_risk = "altissimo"

            context["rischio"] = translated_risk

            template_path: Path = (
                self.template_dir / f"{method_suffix}_report_template.docx"
            )
            doc = DocxTemplate(template_path)

            # Stream chart bytes directly into docx
            buf = BytesIO(report_export_request.chart_data)
            context["chart"] = InlineImage(doc, buf, width=Mm(140))

            doc.render(context)
            doc.save(report_export_request.save_path)

            self.report_export_finished.emit(
                ReportExportResult(
                    success=True,
                    message="Word Document Generated successfully.",
                    report_path=str(
                        report_export_request.save_path,
                    ),
                )
            )

        except Exception as e:
            self.error_occurred.emit(
                ErrorInfo(title="Docx Export Error:", message=str(e))
            )

    def get_chart_distribution_data(self, df: pd.DataFrame) -> dict[str, pd.Series]:
        """
        Calculates distributions using strict column targeting based on the active method.

        Processes the provided structural dataset to generate frequency counts for nominal risk levels
        and binned continuous integer score groups matching the target assessment rules (e.g., 1-7 for RULA)
        for presentation inside frontend graphical visualizations.

        Args:
            df (pandas.DataFrame): The active runtime dataset containing calculated joint metrics and risk assignments.

        Returns:
            dict[str, pandas.Series] (dict): A standard dictionary mapping containing two `pandas.Series` entries:
                * `"risk_counts"`: Frequencies of occurred categorical risk descriptions.
                * `"score_groups"`: Sorted index frequency tracking of continuous binned operational values.
        """
        if df.empty:
            return {"risk_counts": pd.Series(), "score_groups": pd.Series()}

        # 1. Target the exact columns based on your project's naming convention
        # Format: [part]_[metric]_[method] -> e.g., final_score_rula
        method_str = self.current_method.value.lower()

        # Target the 'Final' score column specifically
        score_col = f"final_score_{method_str}"

        # Target the 'risk' column (Standardized across your exports)
        # If your CSV uses "risk", look for that; otherwise, use the method suffix
        risk_col = "risk" if "risk" in df.columns else f"risk_level_{method_str}"

        # 2. Validation: Fallback to heuristic ONLY if strict naming fails
        if score_col not in df.columns:
            score_col = next(
                (
                    c
                    for c in df.columns
                    if "FINAL" in c.upper() and method_str.upper() in c.upper()
                ),
                None,
            )

        if not score_col or score_col not in df.columns:
            return {"risk_counts": pd.Series(), "score_groups": pd.Series()}

        # 3. Categorical Distribution (Risk)
        # Use value_counts but ensure we handle missing risk columns gracefully
        risk_counts = (
            df[risk_col].value_counts() if risk_col in df.columns else pd.Series()
        )

        # 4. Dynamic Binning (Score)
        # RULA/REBA scores are integers. We want bins for each possible score.
        # We use min/max from the actual data to define the range.
        actual_max = int(df[score_col].max())
        upper_bound = max(actual_max, 7)  # Ensure at least 1-7 for RULA

        # Create bins: [0.5, 1.5, 2.5 ...] so that integers fall in the middle
        bins = [i + 0.5 for i in range(upper_bound + 1)]
        bins.insert(0, -0.5)

        labels = [str(i) for i in range(upper_bound + 1)]

        score_groups = (
            pd.cut(df[score_col], bins=bins, labels=labels, include_lowest=True)  # type: ignore
            .value_counts()
            .sort_index()
        )

        return {"risk_counts": risk_counts, "score_groups": score_groups}
