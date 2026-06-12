import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QHeaderView, QAbstractItemView

from gui.utils.models import FrameReviewData, RiskLevel
from gui.widgets.review_metrics_table import ReviewMetricsTable


# ==============================================================================
# FIXTURES
# ==============================================================================


@pytest.fixture
def metrics_table(qtbot):
    """Instantiates the ReviewMetricsTable component under clean qtbot lifecycle control."""
    table = ReviewMetricsTable()
    qtbot.add_widget(table)
    return table


# ==============================================================================
# INITIALIZATION & PROPERTIES
# ==============================================================================


def test_initial_table_properties(metrics_table):
    """Verifies layout constraints, visual modes, selection rules, and structural scaling configurations."""
    assert metrics_table.columnCount() == 2
    assert metrics_table.horizontalHeaderItem(0).text() == "Parameter"
    assert metrics_table.horizontalHeaderItem(1).text() == "Value"

    # Header Resize Modes
    assert (
        metrics_table.horizontalHeader().sectionResizeMode(0)
        == QHeaderView.ResizeMode.Stretch
    )
    assert (
        metrics_table.horizontalHeader().sectionResizeMode(1)
        == QHeaderView.ResizeMode.ResizeToContents
    )

    # Visibility and Row Alternate Configurations
    assert not metrics_table.verticalHeader().isVisible()
    assert metrics_table.alternatingRowColors() is True

    # Interaction Triggers
    assert metrics_table.editTriggers() == QAbstractItemView.EditTrigger.NoEditTriggers
    assert metrics_table.selectionMode() == QAbstractItemView.SelectionMode.NoSelection


# ==============================================================================
# DATA SYNCHRONIZATION PIPELINES
# ==============================================================================


def test_sync_frame_review_data_minimal(metrics_table):
    """Validates row rendering pipeline metrics when provided minimal structural tracking inputs."""
    packet = FrameReviewData(
        frame_idx=10,
        total_frames=500,
        landmarks=[],
        score=None,
        risk=None,
        joint_angles={},
        scores_dict={},
    )

    metrics_table.sync_frame_review_data(packet)

    # Total profile metadata items = 3 (Index, Score, Risk Level)
    assert metrics_table.rowCount() == 3

    assert metrics_table.item(0, 0).text() == "Timeline Frame Index"
    assert metrics_table.item(0, 1).text() == "10 / 500"

    assert metrics_table.item(1, 0).text() == "Unified Evaluation Score"
    assert metrics_table.item(1, 1).text() == "0"

    assert metrics_table.item(2, 0).text() == "Qualitative Risk Assignment"
    assert metrics_table.item(2, 1).text() == "NEGLIGIBLE"


def test_sync_frame_review_data_comprehensive(metrics_table):
    """Validates full layout matrix generations including breakdown slices and dynamic metrics labels."""
    scores = {"Trunk Score": 4, "Neck Score": 2}
    angles = {"Left Knee": 45.223, "Right Knee": "Unreliable_Data"}

    packet = FrameReviewData(
        frame_idx=120,
        total_frames=200,
        landmarks=[],
        score=7,
        risk=RiskLevel.MEDIUM,
        joint_angles=angles,
        scores_dict=scores,
    )

    metrics_table.sync_frame_review_data(packet)

    # Total row distribution check:
    # 3 (Base Specs) + 1 (Header Score Segment) + 2 (Scores) + 1 (Header Kinematics Segment) + 2 (Angles) = 9 Rows
    assert metrics_table.rowCount() == 9

    # Verify Global Profiles
    assert metrics_table.item(1, 1).text() == "7"
    assert metrics_table.item(2, 1).text() == "medium"

    # Verify Structural Score Breakdown Header Row
    assert metrics_table.item(3, 0).text() == "--- Score Components Breakdown ---"
    assert metrics_table.item(3, 0).background() == QColor("#2d3f50")
    assert metrics_table.item(3, 0).foreground() == QColor("#ffffff")
    assert (
        metrics_table.item(3, 1) is None
    )  # Row is split / combined as a single structural span

    # Verify Internal Mapped Elements
    assert metrics_table.item(4, 0).text() == "Trunk Score"
    assert metrics_table.item(4, 1).text() == "4"
    assert metrics_table.item(4, 1).textAlignment() == Qt.AlignmentFlag.AlignCenter

    # Verify Measured Kinematic Variables Section Headers
    assert metrics_table.item(6, 0).text() == "--- Measured Kinematic Variables ---"

    # Verify Mathematical Float Angle Conversions
    assert metrics_table.item(7, 0).text() == "Left Knee"
    assert metrics_table.item(7, 1).text() == "45.22°"

    # Verify Resilient Fallback for Uncastable String Angle Values
    assert metrics_table.item(8, 0).text() == "Right Knee"
    assert metrics_table.item(8, 1).text() == "Unreliable_Data"


# ==============================================================================
# SUBSECTION HELPER METHODS
# ==============================================================================


def test_add_header_row_span_constraints(metrics_table):
    """Confirms visual section breaker rows create proper two-column widget layout spans."""
    metrics_table.setRowCount(0)
    metrics_table._add_header_row("Test Header Block")

    assert metrics_table.rowCount() == 1
    # Check column spanning across both available matrix indexes
    # metrics_table.rowSpan(row, column)
    assert metrics_table.rowSpan(0, 0) == 1
    assert metrics_table.columnSpan(0, 0) == 2
