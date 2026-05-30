# ---
# project: ErgoMoCap
# file: report_backend_test.py
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

from pathlib import Path
import pytest
import pandas as pd
from unittest.mock import MagicMock, patch

from gui.backend.report_backend import ReportBackend
from gui.utils.constants import AssessmentMethod, MetricType
from gui.utils.models import (
    ErrorInfo,
    ReportData,
    ReportExportRequest,
)


@pytest.fixture(autouse=True)
def mock_ergo_paths(tmp_path):
    """Automatically patch ErgoPaths to prevent reliance on system folders."""
    with patch("gui.backend.report_backend.ErgoPaths") as mock_paths:
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir(parents=True, exist_ok=True)
        mock_paths.TEMPLATES = templates_dir
        yield mock_paths


@pytest.fixture
def sample_df():
    """Create a fully compliant ergonomic dataframe matching strict naming structures."""
    return pd.DataFrame(
        {
            MetricType.SCORE.value: [3, 4, 3, 5],
            MetricType.RISK.value: ["Medium", "High", "Medium", "High"],
            "final_score_reba": [3, 4, 3, 5],
            "risk": ["Medium", "High", "Medium", "High"],
            "Trunk_Score_REBA": [1.0, 2.0, 1.0, 2.0],
            "Neck_Score_REBA": [1.0, 1.0, 1.0, 1.0],
            "Legs_Score_REBA": [1.0, 1.0, 1.0, 1.0],
            "Upper_Arm_Score_REBA": [2.0, 2.0, 2.0, 2.0],
            "Lower_Arm_Score_REBA": [1.0, 1.0, 1.0, 1.0],
            "Wrist_Score_REBA": [1.0, 1.0, 1.0, 1.0],
            "Score_A_REBA": [2.0, 3.0, 2.0, 3.0],
            "Score_B_REBA": [2.0, 2.0, 2.0, 2.0],
            "Score_C_REBA": [3.0, 4.0, 3.0, 4.0],
        }
    )


# ==========================================
# Data Loading & Parsing Tests
# ==========================================


def test_load_data_csv_success(qtbot, sample_df, tmp_path):
    """Test successful CSV parsing along with metric collection via signals."""
    backend = ReportBackend()
    csv_path = tmp_path / "test_data.csv"
    sample_df.to_csv(csv_path, index=False)

    mock_metrics = [("Final_Score_REBA", "4.0"), ("Trunk_Score_REBA", "1.5")]
    with patch(
        "gui.backend.report_backend.get_dynamic_metrics", return_value=mock_metrics
    ):
        with qtbot.waitSignal(backend.data_processed, timeout=1000) as blocker:
            backend.load_data_and_run(csv_path)

    report_data = blocker.args[0]
    assert isinstance(report_data, ReportData)
    assert report_data.total_frames == 4
    assert report_data.average_score == 3.75
    assert report_data.summary_dict == {
        "Final_Score_REBA": "4.0",
        "Trunk_Score_REBA": "1.5",
    }
    assert report_data.file_path == csv_path


def test_load_data_excel_success(qtbot, sample_df, tmp_path):
    """Test successful processing branch for Excel spreadsheets (.xlsx)."""
    backend = ReportBackend()
    xlsx_path = tmp_path / "test_data.xlsx"

    with patch(
        "gui.backend.report_backend.pd.read_excel", return_value=sample_df
    ) as mock_read_excel:
        with patch("gui.backend.report_backend.get_dynamic_metrics", return_value=[]):
            with qtbot.waitSignal(backend.data_processed, timeout=1000):
                backend.load_data_and_run(xlsx_path)

    mock_read_excel.assert_called_once_with(xlsx_path)


def test_load_data_csv_unicode_fallback(qtbot, sample_df, tmp_path):
    """Test automatic fallback handling to latin-1 encoding on decode failures."""
    backend = ReportBackend()
    csv_path = tmp_path / "test_data.csv"

    def dynamic_csv_read(*args, **kwargs):
        if kwargs.get("encoding") == "latin-1":
            return sample_df
        raise UnicodeDecodeError("utf-8", b"", 0, 1, "invalid start byte")

    with patch(
        "gui.backend.report_backend.pd.read_csv", side_effect=dynamic_csv_read
    ) as mock_read_csv:
        with patch("gui.backend.report_backend.get_dynamic_metrics", return_value=[]):
            with qtbot.waitSignal(backend.data_processed, timeout=1000):
                backend.load_data_and_run(csv_path)

    assert mock_read_csv.call_count == 2


def test_load_data_empty_file(qtbot, tmp_path):
    """Test that loading an empty file correctly propagates a structured ErrorInfo signal."""
    backend = ReportBackend()
    csv_path = tmp_path / "empty.csv"
    empty_df = pd.DataFrame()

    with patch("gui.backend.report_backend.pd.read_csv", return_value=empty_df):
        with qtbot.waitSignal(backend.error_occurred, timeout=1000) as blocker:
            backend.load_data_and_run(csv_path)

    error_info = blocker.args[0]
    assert isinstance(error_info, ErrorInfo)
    assert error_info.title == "Load Error"
    assert "no data" in error_info.message.lower()


def test_load_data_general_exception(qtbot, tmp_path):
    """Test that arbitrary parsing file execution exceptions are securely caught and emitted."""
    backend = ReportBackend()
    csv_path = tmp_path / "corrupt.csv"

    with patch(
        "gui.backend.report_backend.pd.read_csv",
        side_effect=RuntimeError("File system locked"),
    ):
        with qtbot.waitSignal(backend.error_occurred, timeout=1000) as blocker:
            backend.load_data_and_run(csv_path)

    error_info = blocker.args[0]
    assert error_info.title == "Load Error"
    assert "File system locked" in error_info.message


def test_load_data_csv_empty_after_dropna(qtbot, tmp_path):
    """Test edge case where file contains rows but all target metric columns are dropped."""
    backend = ReportBackend()
    csv_path = tmp_path / "all_nan.csv"
    nan_df = pd.DataFrame(
        {MetricType.SCORE.value: [None, None], MetricType.RISK.value: [None, None]}
    )
    nan_df.to_csv(csv_path, index=False)

    with patch("gui.backend.report_backend.get_dynamic_metrics", return_value=[]):
        with qtbot.waitSignal(backend.data_processed, timeout=1000) as blocker:
            backend.load_data_and_run(csv_path)

    report_data = blocker.args[0]
    assert report_data.total_frames == 0
    assert report_data.average_score == 0.0


# ==========================================
# HTML / PDF Export Tests
# ==========================================


def test_prepare_pdf_export_no_active_file(qtbot):
    """Test error branch tracking if pdf compilation requests trigger before loading active data."""
    backend = ReportBackend()
    backend.current_file = None

    req = MagicMock(spec=ReportExportRequest)
    req.save_path = Path("save.pdf")
    req.chart_data = b"raw_bytes"

    with qtbot.waitSignal(backend.error_occurred, timeout=1000) as blocker:
        backend.prepare_pdf_export(req)

    error_info = blocker.args[0]
    assert error_info.title == "Export Error"
    assert "No active data" in error_info.message


@pytest.mark.parametrize(
    "risk_column_variant", ["risk_level", "rischio_level", "no_matching_column"]
)
def test_prepare_pdf_export_success(qtbot, sample_df, tmp_path, risk_column_variant):
    """Test contextual mapping and template rendering logic for automated PDF exports."""
    backend = ReportBackend()
    csv_path = tmp_path / "active.csv"
    backend.current_file = csv_path
    backend.current_method = AssessmentMethod.REBA

    df = sample_df.copy()
    if risk_column_variant != "no_matching_column":
        df[risk_column_variant] = ["High"] * len(df)
    else:
        # Erase risk indicators completely to test baseline default fallback branches
        risk_cols = [
            c for c in df.columns if "RISK" in c.upper() or "RISCHIO" in c.upper()
        ]
        df = df.drop(columns=risk_cols)

    req = MagicMock(spec=ReportExportRequest)
    req.save_path = tmp_path / "save.pdf"
    req.chart_data = b"fake_chart_bytes"

    mock_metrics = [
        ("Trunk_Score_REBA", "2.0"),
        ("Neck_Score_REBA", "1.0"),
        ("Final_Score_REBA", "4.0"),
    ]

    mock_template = MagicMock()
    mock_template.render.return_value = "<html>Rendered Blueprint Content</html>"

    with (
        patch("gui.backend.report_backend.pd.read_csv", return_value=df),
        patch(
            "gui.backend.report_backend.get_dynamic_metrics", return_value=mock_metrics
        ),
        patch.object(
            backend.jinja_env, "get_template", return_value=mock_template
        ) as mock_get_template,
    ):
        with qtbot.waitSignal(backend.pdf_html_ready, timeout=1000) as blocker:
            backend.prepare_pdf_export(req)

    mock_get_template.assert_called_once_with("REBA_report.j2")
    assert blocker.args[0] == "<html>Rendered Blueprint Content</html>"


def test_prepare_pdf_export_exception(qtbot, tmp_path):
    """Test exceptions within template processing are translated to explicit ErrorInfo signals."""
    backend = ReportBackend()
    backend.current_file = tmp_path / "active.csv"

    req = MagicMock(spec=ReportExportRequest)
    req.save_path = Path("save.pdf")
    req.chart_data = b"bytes"

    with patch(
        "gui.backend.report_backend.pd.read_csv",
        side_effect=Exception("Jinja2 Environment Broken"),
    ):
        with qtbot.waitSignal(backend.error_occurred, timeout=1000) as blocker:
            backend.prepare_pdf_export(req)

    error_info = blocker.args[0]
    assert error_info.title == "PDF Preparation Error"
    assert "Jinja2 Environment Broken" in error_info.message


# ==========================================
# DOCX Generation Tests
# ==========================================


def test_export_to_docx_no_active_file(qtbot):
    """Test that early termination operates silently if no runtime data tracks are set up."""
    backend = ReportBackend()
    backend.current_file = None

    req = MagicMock(spec=ReportExportRequest)

    with (
        qtbot.assertNotEmitted(backend.report_export_finished),
        qtbot.assertNotEmitted(backend.error_occurred),
    ):
        backend.export_to_docx(req)


@pytest.mark.parametrize("risk_column_variant", ["risk", "rischio", "missing"])
def test_export_to_docx_success(qtbot, sample_df, tmp_path, risk_column_variant):
    """Test valid end-to-end processing pipeline for generating standard Word documents."""
    backend = ReportBackend()
    csv_path = tmp_path / "active.csv"
    backend.current_file = csv_path
    backend.current_method = AssessmentMethod.REBA

    df = sample_df.copy()
    if risk_column_variant == "rischio":
        df["rischio_custom"] = ["Low"] * len(df)
    elif risk_column_variant == "missing":
        risk_cols = [
            c for c in df.columns if "RISK" in c.upper() or "RISCHIO" in c.upper()
        ]
        df = df.drop(columns=risk_cols)

    save_path = tmp_path / "final_report.docx"
    req = MagicMock(spec=ReportExportRequest)
    req.save_path = save_path
    req.chart_data = b"matplotlib_binary_stream"

    mock_metrics = [("Final_Score_REBA", "5.0")]

    with (
        patch("gui.backend.report_backend.pd.read_csv", return_value=df),
        patch(
            "gui.backend.report_backend.get_dynamic_metrics", return_value=mock_metrics
        ),
        patch("gui.backend.report_backend.DocxTemplate") as mock_docx_cls,
        patch("gui.backend.report_backend.InlineImage"),
    ):
        mock_doc_instance = MagicMock()
        mock_docx_cls.return_value = mock_doc_instance

        with qtbot.waitSignal(backend.report_export_finished, timeout=1000) as blocker:
            backend.export_to_docx(req)

        mock_doc_instance.render.assert_called_once()
        mock_doc_instance.save.assert_called_once_with(save_path)

        result = blocker.args[0]
        assert result.success is True
        assert "Word Document Generated successfully" in result.message


def test_export_to_docx_exception(qtbot, tmp_path):
    """Test exceptions in the DOCX engine emit an error_occurred payload structure."""
    backend = ReportBackend()
    backend.current_file = tmp_path / "active.csv"

    req = MagicMock(spec=ReportExportRequest)
    req.save_path = tmp_path / "output.docx"
    req.chart_data = b"data"

    with patch(
        "gui.backend.report_backend.pd.read_csv",
        side_effect=RuntimeError("DocxTemplate corrupt"),
    ):
        with qtbot.waitSignal(backend.error_occurred, timeout=1000) as blocker:
            backend.export_to_docx(req)

    error_info = blocker.args[0]
    assert "Docx Export Error" in error_info.title
    assert "DocxTemplate corrupt" in error_info.message


# ==========================================
# Distribution & Binning Heuristic Tests
# ==========================================


def test_get_chart_distribution_data_empty():
    """Verify clean distribution fallback logic when receiving completely empty operational frames."""
    backend = ReportBackend()
    res = backend.get_chart_distribution_data(pd.DataFrame())
    assert res["risk_counts"].empty
    assert res["score_groups"].empty


def test_get_chart_distribution_data_strict(sample_df):
    """Verify distribution frequencies match exact targeting configuration setups."""
    backend = ReportBackend()
    backend.current_method = AssessmentMethod.REBA
    res = backend.get_chart_distribution_data(sample_df)

    assert "risk_counts" in res
    assert "score_groups" in res
    assert not res["score_groups"].empty
    assert res["risk_counts"]["High"] == 2


def test_get_chart_distribution_data_heuristic():
    """Verify fallback operation resolves metric columns when missing normalized structural keys."""
    backend = ReportBackend()
    backend.current_method = AssessmentMethod.REBA

    heuristic_df = pd.DataFrame(
        {
            "CALCULATED_FINAL_REBA_SCORE_VALUE": [2, 3, 4, 7],
            "risk_level_reba": ["Low", "Low", "Medium", "High"],
        }
    )
    res = backend.get_chart_distribution_data(heuristic_df)

    assert not res["score_groups"].empty
    assert "7" in res["score_groups"].index
    assert res["risk_counts"]["Low"] == 2


def test_get_chart_distribution_data_heuristic_no_risk_col():
    """Verify continuous binning operates successfully even when nominal columns are absent."""
    backend = ReportBackend()
    backend.current_method = AssessmentMethod.REBA

    heuristic_df = pd.DataFrame(
        {"final_score_reba": [1, 2, 2, 3], "unrelated_data_stream": [9, 8, 7, 6]}
    )
    res = backend.get_chart_distribution_data(heuristic_df)

    assert res["risk_counts"].empty
    assert not res["score_groups"].empty
    assert res["score_groups"]["2"] == 2


def test_get_chart_distribution_data_completely_missing_score():
    """Verify immediate structural failure handling if no valid score tracks match lookups."""
    backend = ReportBackend()
    backend.current_method = AssessmentMethod.REBA

    unrelated_df = pd.DataFrame(
        {"unrelated_col_1": [1, 2], "unrelated_col_2": ["A", "B"]}
    )
    res = backend.get_chart_distribution_data(unrelated_df)

    assert res["risk_counts"].empty
    assert res["score_groups"].empty
