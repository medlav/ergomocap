import pytest
from unittest.mock import MagicMock, patch
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox

from gui.utils.models import SessionData, VideoPosition, FrameReviewData, RiskLevel
from gui.views.review_view import ReviewView


# ==============================================================================
# FIXTURES
# ==============================================================================


@pytest.fixture
def review_view(qtbot):
    """Instantiates the ReviewView component under clean qtbot control."""
    view = ReviewView()
    qtbot.add_widget(view)
    return view


# ==============================================================================
# INITIALIZATION & UI STATE TESTS
# ==============================================================================


def test_initial_window_properties(review_view):
    """Verifies floating configuration, layout dimensions, and title bounds."""
    flags = review_view.windowFlags()
    assert flags & Qt.WindowType.Window
    assert flags & Qt.WindowType.WindowStaysOnTopHint
    assert review_view.windowTitle() == "Video Review Suite"
    assert review_view.status_label.toPlainText() == "REVIEW SUITE: INITIALIZED"


def test_scope_changed_toggles_spinboxes(review_view):
    """Checks if changing scope indices activates or deactivates frame ranges correctly."""
    # Start at Index 1 (Custom) so spinboxes become enabled first
    review_view.combo_scope.setCurrentIndex(1)
    assert review_view.spin_start.isEnabled()
    assert review_view.spin_end.isEnabled()

    # Index 0: Current Frame Only -> Spinboxes disabled
    review_view.combo_scope.setCurrentIndex(0)
    assert not review_view.spin_start.isEnabled()
    assert not review_view.spin_end.isEnabled()

    # Index 2: Entire Recording Timeline -> Spinboxes disabled
    review_view.combo_scope.setCurrentIndex(2)
    assert not review_view.spin_start.isEnabled()
    assert not review_view.spin_end.isEnabled()


def test_notes_text_changed_emits_signal(review_view, qtbot):
    """Ensures modifications inside observations trigger corresponding text events."""
    with qtbot.wait_signal(review_view.note_added) as blocker:
        review_view.txt_notes.setPlainText("Test observation payload.")

    assert blocker.args[0] == "Test observation payload."


# ==============================================================================
# DATA SYNCHRONIZATION PIPELINES
# ==============================================================================


def test_sync_frame_review_data_populates_combos(review_view):
    """Validates real-time adjustment updates matching frame indexing metrics."""
    scores = {"Trunk": 2, "Neck": 1, "Legs": 3}
    packet = FrameReviewData(
        frame_idx=42,
        total_frames=100,
        landmarks=[],
        score=4,
        risk=RiskLevel.LOW,
        joint_angles={},
        scores_dict=scores,
    )

    with patch.object(
        review_view.metrics_table, "sync_frame_review_data"
    ) as mock_table_sync:
        review_view.sync_frame_review_data(packet)

        assert review_view.scores_dict == scores
        assert review_view.current_idx == 42
        assert [
            review_view.combo_fields.itemText(i)
            for i in range(review_view.combo_fields.count())
        ] == ["Trunk", "Neck", "Legs"]
        mock_table_sync.assert_called_once_with(packet)


def test_handle_combo_field_changed_updates_label(review_view):
    """Verifies label presentation changes cleanly when switching field selections."""
    review_view.scores_dict = {"Trunk": 3, "Neck": 2}

    review_view.combo_fields.blockSignals(True)
    review_view.combo_fields.addItems(["Trunk", "Neck"])
    review_view.combo_fields.blockSignals(False)

    review_view.combo_fields.setCurrentText("Neck")
    assert review_view.lbl_field_value.text() == "Current Field Value is: 2"


def test_handle_combo_field_changed_raises_on_empty_scores(review_view):
    """Ensures exceptions are raised if field switches occur before data mounting."""
    review_view.scores_dict = None

    # Call the target slot explicitly to let pytest capture the expected ValueError.
    review_view.combo_fields.blockSignals(True)
    review_view.combo_fields.addItem("Orphan_Field")
    review_view.combo_fields.setCurrentText("Orphan_Field")
    review_view.combo_fields.blockSignals(False)

    with pytest.raises(ValueError, match="No scores_dict"):
        review_view._handle_combo_field_changed()


def test_sync_video_position_routes_to_backend(review_view):
    """Verifies timeline frame updates step backend calculation calls cleanly."""
    review_view.review_backend.current_joint_analysis_path = "mock_path.csv"
    pos = VideoPosition(current_frame=15, total_frames=100)

    with patch.object(
        review_view.review_backend, "emit_frame_review_data"
    ) as mock_emit:
        review_view.sync_video_position(pos)
        mock_emit.assert_called_once_with(current_frame_idx=15)


def test_sync_video_position_early_return_unallocated(review_view):
    """Guards against frame processing when backend tracks are unallocated."""
    review_view.review_backend.current_joint_analysis_path = None
    pos = VideoPosition(current_frame=15, total_frames=100)

    with patch.object(
        review_view.review_backend, "emit_frame_review_data"
    ) as mock_emit:
        review_view.sync_video_position(pos)
        mock_emit.assert_not_called()


# ==============================================================================
# MUTATION AND DATA EXECUTION CONTROLS
# ==============================================================================


@pytest.mark.parametrize(
    "scope_idx, current_idx, spin_start, spin_end, expected_range",
    [
        (0, 45, 0, 0, (45, 45)),
        (1, 45, 10, 20, (10, 20)),
        (2, 45, 0, 0, (0, -1)),
        (3, 45, 30, 40, (30, 40)),
    ],
)
def test_handle_apply_clicked_scopes(
    review_view, scope_idx, current_idx, spin_start, spin_end, expected_range
):
    """Verifies that frame scope selection maps to appropriate frame range boundaries."""
    review_view.scores_dict = {"Trunk_Score": 4.5}
    review_view.combo_fields.blockSignals(True)
    review_view.combo_fields.addItem("Trunk_Score")
    review_view.combo_fields.setCurrentText("Trunk_Score")
    review_view.combo_fields.blockSignals(False)

    review_view.combo_scope.setCurrentIndex(scope_idx)
    review_view.current_idx = current_idx
    review_view.spin_start.setValue(spin_start)
    review_view.spin_end.setValue(spin_end)
    review_view.spin_value.setValue(4.5)

    with patch.object(review_view.review_backend, "mutate_records") as mock_mutate:
        review_view._handle_apply_clicked()

        mock_mutate.assert_called_once_with(
            start_frame=expected_range[0],
            end_frame=expected_range[1],
            variable_field="Trunk_Score",
            override_value=4.5,
        )


def test_handle_apply_clicked_current_frame_skipped_if_none(review_view):
    """Ensures mutate_records is not invoked if current frame context is missing under frame scope."""
    review_view.scores_dict = {"Trunk_Score": 0.0}
    review_view.combo_fields.blockSignals(True)
    review_view.combo_fields.addItem("Trunk_Score")
    review_view.combo_fields.blockSignals(False)

    review_view.combo_scope.setCurrentIndex(0)
    review_view.current_idx = None

    with patch.object(review_view.review_backend, "mutate_records") as mock_mutate:
        review_view._handle_apply_clicked()
        mock_mutate.assert_not_called()


# ==============================================================================
# LIFECYCLE & PERSISTENCE MANAGEMENT
# ==============================================================================


def test_update_session_data_success(review_view):
    """Verifies UI component reloads and first-frame loading on successful session updates."""
    mock_session = MagicMock(spec=SessionData)
    fields = ["Neck", "Trunk", "Legs"]

    with (
        patch.object(
            review_view.review_backend,
            "load_review_session",
            return_value=(True, "Sandbox Loaded"),
        ),
        patch.object(
            review_view.review_backend, "get_dataset_fields", return_value=fields
        ),
        patch.object(review_view.review_backend, "emit_frame_review_data") as mock_emit,
    ):
        review_view.update_session_data(mock_session)

        assert review_view.status_label.toPlainText() == "REVIEW STATUS: Sandbox Loaded"
        assert [
            review_view.combo_fields.itemText(i)
            for i in range(review_view.combo_fields.count())
        ] == fields
        mock_emit.assert_called_once_with(0)


def test_update_session_data_failure(review_view):
    """Ensures system logs errors and updates tracking labels appropriately when backend load fails."""
    mock_session = MagicMock(spec=SessionData)

    with (
        patch.object(
            review_view.review_backend,
            "load_review_session",
            return_value=(False, "Missing Permissions"),
        ),
        patch("gui.views.review_view.logger.error") as mock_logger,
    ):
        review_view.update_session_data(mock_session)

        mock_logger.assert_called_once_with("Error: Missing Permissions")
        assert (
            review_view.status_label.toPlainText()
            == "REVIEW STATUS: Error: Missing Permissions"
        )


def test_on_save_session_success(review_view):
    """Confirms information boxes trigger correctly when revisions are successfully written out."""
    with (
        patch.object(
            review_view.review_backend, "commit_final_review", return_value=True
        ),
        patch.object(QMessageBox, "information") as mock_box,
    ):
        review_view._on_save_session()
        mock_box.assert_called_once_with(
            review_view,
            review_view.tr("Success"),
            review_view.tr(
                "Human corrections committed safely to disk as 'ergomocap_review.csv'."
            ),
        )


def test_on_save_session_failure(review_view):
    """Confirms critical error notifications trigger correctly if backend commit fails."""
    with (
        patch.object(
            review_view.review_backend, "commit_final_review", return_value=False
        ),
        patch.object(QMessageBox, "critical") as mock_box,
    ):
        review_view._on_save_session()
        mock_box.assert_called_once_with(
            review_view,
            review_view.tr("Error"),
            review_view.tr("Failed to finalize changes into review log."),
        )
