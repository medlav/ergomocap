# ---
# project: ErgoMoCap
# file: report_view_test.py
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
from pathlib import Path
from unittest.mock import patch

from PySide6.QtWidgets import QLabel

from gui.views.report_view import ReportView
from gui.utils.constants import AssessmentMethod
from gui.core.report_strategies import RebaStrategy
from gui.utils.models import (
    ReportData,
    ReportExportResult,
    ErrorInfo,
    ReportExportRequest,
)


@pytest.fixture
def report_view(qtbot):
    """Initialize ReportView with mocked backend to avoid heavy background processing."""
    with patch("gui.views.report_view.ReportBackend") as MockBackend:
        mock_backend_inst = MockBackend.return_value
        view = ReportView(parent=None, initial_csv=None)
        qtbot.addWidget(view)
        view.backend = mock_backend_inst  # Ensure we use the active mock instance
        return view


def test_initialization_defaults(report_view):
    """Verify window setup and default enumeration states."""
    assert report_view.windowTitle() == "ErgoMoCap Reports"
    assert report_view.current_method == AssessmentMethod.REBA
    assert isinstance(report_view.current_strategy, RebaStrategy)
    assert report_view.btn_pdf.isEnabled() is False
    assert report_view.btn_docx.isEnabled() is False


def test_initialization_with_file(qtbot):
    """Verify auto-loading logic when initial_csv is provided on creation."""
    test_path = "test_data.csv"
    with patch("gui.views.report_view.ReportBackend") as MockBackend:
        mock_backend_inst = MockBackend.return_value
        view = ReportView(parent=None, initial_csv=test_path)
        qtbot.addWidget(view)
        mock_backend_inst.load_data_and_run.assert_called_with(Path(test_path))


def test_set_method_logic(report_view):
    """Test switching assessment methods using the AssessmentMethod Enum."""
    # Test shifting to RULA member updates the enumeration property
    report_view.set_method(AssessmentMethod.RULA)
    assert report_view.current_method == AssessmentMethod.RULA

    # Test redundant protection execution path returns early
    report_view.set_method(AssessmentMethod.RULA)

    # Test shifting back to REBA member updates properties
    report_view.set_method(AssessmentMethod.REBA)
    assert report_view.current_method == AssessmentMethod.REBA


def test_on_data_ready_updates_ui(report_view):
    """Verify UI components update properly when wrapped ReportData payload is processed."""
    df = pd.DataFrame({"risk": [1, 2], "score": [5, 10]})
    path = Path("/mock/path.csv")
    summary = {"Metric": "Value"}

    # Wrap inside the updated dataclass layout
    report_data = ReportData(
        df=df, file_path=path, total_frames=100, average_score=5.5, summary_dict=summary
    )

    # Trigger the slot
    report_view._on_data_ready(report_data)

    # Check stat cards
    total_lbl = report_view.card_total.findChild(QLabel, "total_val")
    avg_lbl = report_view.card_avg.findChild(QLabel, "avg_val")

    assert total_lbl.text() == "100"
    assert avg_lbl.text() == "5.50"
    assert report_view.btn_pdf.isEnabled() is True
    assert report_view.btn_docx.isEnabled() is True
    assert "path.csv" in report_view.file_info.toPlainText()


def test_handle_import_dialog(report_view):
    """Simulate user selecting a file path within the import dialog wrapper."""
    with patch("PySide6.QtWidgets.QFileDialog.getOpenFileName") as mock_dialog:
        mock_dialog.return_value = ("/path/to/data.csv", "Data Files (*.csv)")

        report_view._handle_import_dialog()
        report_view.backend.load_data_and_run.assert_called_with(
            Path("/path/to/data.csv")
        )


def test_handle_pdf_request(report_view):
    """Test PDF generation pipeline triggers backend conversion with standard image buffers."""
    report_view._handle_pdf_request()
    report_view.backend.prepare_pdf_export.assert_called_once()

    # Assert it was called passing the ReportExportRequest parameter container
    args, _ = report_view.backend.prepare_pdf_export.call_args
    assert isinstance(args[0], ReportExportRequest)


def test_handle_docx_request_success(report_view):
    """Test DOCX export triggers backend engine when path selection is accepted."""
    with patch("PySide6.QtWidgets.QFileDialog.getSaveFileName") as mock_save:
        mock_save.return_value = ("/path/save.docx", "Word (*.docx)")

        report_view._handle_docx_request()
        report_view.backend.export_to_docx.assert_called_once()

        args, _ = report_view.backend.export_to_docx.call_args
        assert isinstance(args[0], ReportExportRequest)
        assert args[0].save_path == Path("/path/save.docx")


def test_handle_docx_cancel(report_view):
    """Test canceling the DOCX save dialog returns early without hitting backend pipelines."""
    with patch("PySide6.QtWidgets.QFileDialog.getSaveFileName") as mock_save:
        mock_save.return_value = ("", "")

        report_view._handle_docx_request()
        report_view.backend.export_to_docx.assert_not_called()


def test_print_pdf_success(report_view):
    mock_filename = "/mock/path/to/report.pdf"

    with (
        patch(
            "PySide6.QtWidgets.QFileDialog.getSaveFileName",
            return_value=(mock_filename, "PDF Files (*.pdf)"),
        ) as mock_dialog,
        patch("gui.views.report_view.QPrinter") as MockPrinter,
        patch("PySide6.QtGui.QTextDocument.print_") as mock_print_call,
        patch("PySide6.QtWidgets.QMessageBox.information") as mock_info,
    ):
        # Configure our QPrinter mock instance to mimic a successful internal state
        mock_printer_instance = MockPrinter.return_value
        mock_printer_instance.outputFileName.return_value = mock_filename

        # Execute target method
        report_view._print_pdf("<html><body>Report Content</body></html>")

        # 1. Verify dialog and constructor execution
        mock_dialog.assert_called_once()
        MockPrinter.assert_called_once()

        mock_printer_instance.setOutputFileName.assert_called_once_with(mock_filename)

        # 3. Verify final processing engine and message popups executed successfully
        mock_print_call.assert_called_once_with(mock_printer_instance)
        mock_info.assert_called_once()


def test_print_pdf_cancel(report_view):
    """Test that cancelling the file dialog exits the process gracefully without GUI."""
    with (
        # 1. Return empty string to simulate hitting 'Cancel' inside the native file dialog
        patch(
            "PySide6.QtWidgets.QFileDialog.getSaveFileName", return_value=("", "")
        ) as mock_dialog,
        patch("PySide6.QtPrintSupport.QPrinter") as MockPrinter,
        patch("PySide6.QtGui.QTextDocument.print_") as mock_print_call,
        patch("PySide6.QtWidgets.QMessageBox.information") as mock_info,
    ):
        # Execute target method
        report_view._print_pdf("<html><body>Report Content</body></html>")

        # ASSERTIONS
        mock_dialog.assert_called_once()  # Proves dialog initialization was reached

        # Because filename was empty, everything inside the 'if filename:' block should be completely skipped
        MockPrinter.assert_not_called()
        mock_print_call.assert_not_called()
        mock_info.assert_not_called()


def test_print_pdf_error(report_view):
    """Test exception tracking catch block during active document conversion loops."""
    mock_filename = "/mock/path/to/report.pdf"

    with (
        patch(
            "PySide6.QtWidgets.QFileDialog.getSaveFileName",
            return_value=(mock_filename, "PDF Files (*.pdf)"),
        ),
        # Force setHtml to crash out completely to test your try/except recovery loop
        patch(
            "PySide6.QtGui.QTextDocument.setHtml",
            side_effect=Exception("Print Engine Failure"),
        ),
        patch("PySide6.QtWidgets.QMessageBox.critical") as mock_crit,
    ):
        report_view._print_pdf("<html></html>")

        # Verifies the exception was successfully trapped and displayed cleanly to the user
        mock_crit.assert_called_once()


def test_handle_backend_messages(report_view):
    """Test execution notifications mapping success and exception wrappers downstream."""
    # Test Success Wrapper
    with patch("PySide6.QtWidgets.QMessageBox.information") as mock_info:
        success_result = ReportExportResult(
            success=True, message="File Saved successfully."
        )
        report_view._handle_export_success(success_result)
        mock_info.assert_called_once_with(
            report_view, "Success", "File Saved successfully."
        )

    # Test Error Info Dialog Wrapper
    with patch("PySide6.QtWidgets.QMessageBox.critical") as mock_crit:
        error_payload = ErrorInfo(
            title="Export Error", message="Write permission denied."
        )
        report_view._handle_error(error_payload)
        mock_crit.assert_called_once_with(
            report_view, "Export Error", "Write permission denied."
        )
