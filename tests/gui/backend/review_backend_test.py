import pytest
import pandas as pd
from unittest.mock import MagicMock, patch

from gui.utils.app_paths import ErgoPaths
from gui.utils.constants import AssessmentMethod, RiskLevel
from gui.utils.models import FrameReviewData, AnalysisResult, SessionData
from gui.workers.analysis_worker import AnalysisWorker
from gui.backend.review_backend import ReviewBackend


# ==============================================================================
# FIXTURES
# ==============================================================================


@pytest.fixture
def review_backend():
    """
    Instantiates the ReviewBackend instance.(QObject)
    """
    backend = ReviewBackend()
    return backend


@pytest.fixture
def sample_session_data(tmp_path):
    """Creates a mock SessionData pointing to temporary data assets."""
    joint_path = tmp_path / "joint_angles.csv"
    df = pd.DataFrame(
        {
            "Frame": [0, 1, 2],
            "Left_Elbow": [45.0, 50.0, 55.5],
            "Right_Elbow": [30.0, 32.0, 31.0],
        }
    )
    df.to_csv(joint_path, index=False)

    session = MagicMock(spec=SessionData)
    session.joint_angles_csv_path = joint_path
    return session


@pytest.fixture
def sample_ergo_data(tmp_path):
    """Generates standard sandboxed csv data contents for test execution loops."""
    ergo_path = tmp_path / "ergo_output.csv"
    df = pd.DataFrame(
        {
            "Frame": [0, 1, 2],
            "Method": ["REBA", "REBA", "REBA"],
            "Trunk_Score": [2, 3, 2],
            "Final_Score_REBA": [4, 6, 5],
            "Risk_Level": ["low", "medium", "low"],
        }
    )
    df.to_csv(ergo_path, index=False)
    return ergo_path


# ==============================================================================
# UNMUTED SUCCESS & FAILURE PATH RUNS
# ==============================================================================


def test_load_review_session_success(
    review_backend, sample_session_data, sample_ergo_data
):
    """Verifies happy path dataset initialization and copy isolation behavior."""
    with patch.object(
        ErgoPaths, "get_analysis_data_file_path", return_value=sample_ergo_data
    ):
        success, message = review_backend.load_review_session(sample_session_data)

        assert success is True
        assert "Successfully sandboxed" in message
        assert review_backend.active_dataframe is not None
        assert review_backend.joint_angles_dataframe is not None
        assert review_backend.checkpoint_file_path.exists()
        assert review_backend.checkpoint_file_path.suffix == ".bak_review"


def test_load_review_session_missing_ergo_file(
    review_backend, sample_session_data, tmp_path
):
    """Verifies clean failure propagation if target calculation file is absent."""
    non_existent = tmp_path / "does_not_exist.csv"
    with patch.object(
        ErgoPaths, "get_analysis_data_file_path", return_value=non_existent
    ):
        success, message = review_backend.load_review_session(sample_session_data)

        assert success is False
        assert "Target file does not exist" in message


def test_load_review_session_missing_joint_path(review_backend, sample_ergo_data):
    """Checks handling of malformed tracking configs lacking structural kinematic records."""
    invalid_session = MagicMock(spec=SessionData)
    invalid_session.joint_angles_csv_path = None

    with patch.object(
        ErgoPaths, "get_analysis_data_file_path", return_value=sample_ergo_data
    ):
        success, message = review_backend.load_review_session(invalid_session)

        assert success is False
        assert "Sandbox initialization failure" in message


def test_get_dataset_fields(review_backend):
    """Validates dataframe schema field visibility selectors across unallocated states."""
    assert review_backend.get_dataset_fields() == []

    review_backend.active_dataframe = pd.DataFrame(columns=["Alpha", "Beta", "Gamma"])
    assert review_backend.get_dataset_fields() == ["Alpha", "Beta", "Gamma"]


# ==============================================================================
# STATE MUTATION MODES
# ==============================================================================


def test_mutate_records_not_mounted(review_backend, qtbot):
    """Guards structural sanity across non-allocated datasets."""
    with qtbot.wait_signal(review_backend.status_updated) as blocker:
        review_backend.mutate_records(0, 10, "Trunk_Score", 5.0)
    assert "Data modification rejected: No dataset mounted." in blocker.args[0]


def test_mutate_records_global_rewrite(review_backend, qtbot):
    """Validates complete global record rewrites matching wild index targets (-1)."""
    review_backend.active_dataframe = pd.DataFrame({"Trunk_Score": [1.0, 2.0, 3.0]})

    with qtbot.wait_signal(review_backend.status_updated) as blocker:
        review_backend.mutate_records(0, -1, "Trunk_Score", 4.0)

    assert (review_backend.active_dataframe["Trunk_Score"] == 4.0).all()
    assert "Global rewrite applied to field: [Trunk_Score] -> 4.0" in blocker.args[0]


def test_mutate_records_bounded_slice(review_backend):
    """Ensures targeted block array splicing remains clamped to maximum matrix limits."""
    review_backend.active_dataframe = pd.DataFrame({"Neck_Score": [1.0, 1.0, 1.0, 1.0]})

    review_backend.mutate_records(1, 2, "Neck_Score", 9.0)
    expected = [1.0, 9.0, 9.0, 1.0]
    assert review_backend.active_dataframe["Neck_Score"].tolist() == expected


def test_mutate_records_new_field(review_backend):
    """Checks inline runtime structural extension for dynamically targeted novel tracking rows."""
    review_backend.active_dataframe = pd.DataFrame({"Existing": [1.0, 2.0]})
    review_backend.mutate_records(0, 1, "Dynamic_Field", 7.5)

    assert "Dynamic_Field" in review_backend.active_dataframe.columns
    assert review_backend.active_dataframe["Dynamic_Field"].tolist() == [7.5, 7.5]


# ==============================================================================
# COMMIT TRACK TIMELINES
# ==============================================================================


def test_commit_final_review_unallocated(review_backend):
    """Guards against writing out non-existent sessions."""
    assert review_backend.commit_final_review() is False


def test_commit_final_review_success(review_backend, tmp_path, qtbot):
    """Confirms persistent final export output file generations and checkpoint trace cleanups."""
    origin_file = tmp_path / "raw_session.csv"
    checkpoint = tmp_path / "raw_session.bak_review"
    checkpoint.touch()

    review_backend.current_ergomocap_analysis_path = origin_file
    review_backend.checkpoint_file_path = checkpoint
    review_backend.active_dataframe = pd.DataFrame({"Data": [42]})

    with qtbot.wait_signal(review_backend.status_updated) as blocker:
        res = review_backend.commit_final_review()

    assert res is True
    expected_out = tmp_path / "ergomocap_review.csv"
    assert expected_out.exists()
    assert not checkpoint.exists()
    assert "Review session committed to: ergomocap_review.csv" in blocker.args[0]


def test_commit_final_review_exception(review_backend, tmp_path):
    """Asserts tracking system failure handling path behavior across file systems exceptions."""
    review_backend.current_ergomocap_analysis_path = (
        tmp_path / "read_only_dir" / "file.csv"
    )
    review_backend.active_dataframe = pd.DataFrame({"Data": [42]})

    res = review_backend.commit_final_review()
    assert res is False


# ==============================================================================
# ASYNCHRONOUS ENGINE PROCESSING PASSES (BACKGROUND THREADING)
# ==============================================================================


def test_run_review_analysis_aborts_on_empty_data(review_backend, qtbot):
    """Guards against starting thread lifecycles without an active workspace."""
    review_backend.active_dataframe = None

    with qtbot.wait_signal(review_backend.analysis_finished) as blocker:
        review_backend.run_review_analysis(AssessmentMethod.REBA)

    result = blocker.args[0]
    assert result.success is False
    assert result.output_path is None
    assert "No active dataframe loaded" in result.message


@patch("gui.backend.review_backend.AnalysisWorker")
def test_run_review_analysis_execution_flow(mock_worker_cls, review_backend, qtbot):
    """Verifies internal QThread wiring, worker setup, and cross-thread pipeline execution."""
    mock_worker = MagicMock(spec=AnalysisWorker)
    mock_worker_cls.return_value = mock_worker

    review_backend.active_dataframe = pd.DataFrame({"dummy": [1, 2]})

    # Trigger the processing pass
    with qtbot.wait_signal(review_backend.status_updated) as blocker:
        review_backend.run_review_analysis(AssessmentMethod.RULA)

    assert "recalculating rula engine matrix layers..." in blocker.args[0].lower()
    assert review_backend._analysis_thread is not None
    assert review_backend._analysis_thread.isRunning()

    # Assert worker configurations
    assert mock_worker._pending_method == AssessmentMethod.RULA
    mock_worker.moveToThread.assert_called_with(review_backend._analysis_thread)

    # Clean up the running thread infrastructure
    review_backend._terminate_active_worker()


def test_run_review_analysis_exception_boundary(review_backend, qtbot):
    """Ensures exceptions inside structural thread generation loops are intercepted safely."""
    review_backend.active_dataframe = pd.DataFrame({"dummy": [1]})

    # Force a runtime breakdown by patching QThread instantiation to throw
    with patch(
        "gui.backend.review_backend.QThread",
        side_effect=RuntimeError("Thread resource failure"),
    ):
        with qtbot.wait_signal(review_backend.analysis_finished) as blocker:
            review_backend.run_review_analysis(AssessmentMethod.REBA)

        result = blocker.args[0]
        assert result.success is False
        assert "Re-run failed: Thread resource failure" in result.message


def test_handle_review_worker_finished_updates_checkpoint(
    review_backend, tmp_path, qtbot
):
    """Verifies that successful analysis runs auto-flush current states into checkpoints."""
    checkpoint = tmp_path / "autosave.bak_review"
    review_backend.checkpoint_file_path = checkpoint
    review_backend.active_dataframe = pd.DataFrame({"Updated_Score": [8, 9]})

    mock_result = AnalysisResult(
        success=True, message="Engine completed", output_path=None
    )

    with qtbot.wait_signal(review_backend.status_updated) as blocker_status:
        with qtbot.wait_signal(review_backend.analysis_finished) as blocker_finished:
            review_backend._handle_review_worker_finished(mock_result)

    assert "Review pass updated. Soft checkpoint saved." in blocker_status.args[0]
    assert blocker_finished.args[0] == mock_result

    # Verify actual disk serialization occurred
    saved_df = pd.read_csv(checkpoint)
    assert saved_df["Updated_Score"].tolist() == [8, 9]


# ==============================================================================
# STRUCTURAL DYNAMIC PACKET PARSING & RIGID BOUNDARY VERIFICATION
# ==============================================================================


def test_emit_frame_review_data_success(review_backend, qtbot):
    """Verifies multi-source data compilation into a complete FrameReviewData package."""
    review_backend.active_dataframe = pd.DataFrame(
        {
            "Method": ["REBA"],
            "Final_Score_REBA": [4],
            "Risk_Level": ["low"],
            "Trunk_Score": [2],
        }
    )
    review_backend.joint_angles_dataframe = pd.DataFrame(
        {"Frame": [0], "Left_Knee": [15.5]}
    )

    with qtbot.wait_signal(review_backend.frame_review_ready) as blocker:
        review_backend.emit_frame_review_data(0)

    packet: FrameReviewData = blocker.args[0]
    assert packet.frame_idx == 0
    assert packet.total_frames == 1
    assert packet.score == 4
    assert packet.risk == RiskLevel.LOW
    assert packet.joint_angles == {"Left Knee": 15.5}
    assert packet.scores_dict["Trunk_Score"] == 2


@pytest.mark.parametrize(
    "setup_mode, expected_err",
    [
        ("missing_active", "Active score dataframe is not initialized"),
        ("missing_joint", "Joint angles dataframe is not initialized"),
    ],
)
def test_emit_frame_review_data_uninitialized_state(
    review_backend, setup_mode, expected_err
):
    """Guards strict pre-flight assertions targeting state mutations."""
    if setup_mode == "missing_active":
        review_backend.active_dataframe = None
    else:
        review_backend.active_dataframe = pd.DataFrame({"Data": [1]})
        review_backend.joint_angles_dataframe = None

    with pytest.raises(ValueError, match=expected_err):
        review_backend.emit_frame_review_data(0)


@pytest.mark.parametrize(
    "frame_idx, active_len, joint_len, expected_err",
    [
        (-1, 5, 5, "out of bounds"),
        (5, 5, 5, "out of bounds"),
        (2, 5, 1, "exceeds available joint angles row data"),
    ],
)
def test_emit_frame_review_data_out_of_bounds(
    review_backend, frame_idx, active_len, joint_len, expected_err
):
    """Guards sequence arrays parsing limitations via direct mathematical index testing."""
    review_backend.active_dataframe = pd.DataFrame({"Method": ["REBA"] * active_len})
    review_backend.joint_angles_dataframe = pd.DataFrame({"Frame": [0] * joint_len})

    with pytest.raises(IndexError, match=expected_err):
        review_backend.emit_frame_review_data(frame_idx)


def test_parse_pure_row_metrics_nan_protection(review_backend):
    """Ensures runtime execution aborts violently when encountering Corrupted/NaN dataset blocks."""
    corrupt_row = {"Shoulder_Flexion": float("nan")}
    with pytest.raises(
        ValueError, match="Strict Check Failure: Corrupt or missing value"
    ):
        review_backend._parse_pure_row_metrics(corrupt_row, is_score_file=False)


def test_parse_pure_row_metrics_clean_formatting(review_backend):
    """Validates systemic stripping of trailing scoring metadata tags from user presentation layers."""
    row_data = {
        "FRAME": 0,
        "ARM_SCORE_REBA": 3.0,
        "NECK_SCORE": 2.0,
        "WRIST_DEVIATION_ANGLE": 14.50,
    }

    res = review_backend._parse_pure_row_metrics(
        row_data, is_score_file=True, method_suffix="REBA"
    )

    assert "Arm" in res and res["Arm"] == 3
    assert "Neck" in res and res["Neck"] == 2
    assert "Wrist Deviation Angle" in res and res["Wrist Deviation Angle"] == 14.5
    assert "Frame" not in res  # Stripped via ignored_fields context filters


@pytest.mark.parametrize(
    "row, method, expected",
    [
        ({"SCORE": 5}, "REBA", 5),
        ({"FINAL_SCORE_RULA": "7.0"}, "RULA", 7),
        ({"FINAL_SCORE": 3.2}, "REBA", 3),
    ],
)
def test_resolve_unified_score_variants(review_backend, row, method, expected):
    """Verifies layout-agnostic score extraction and robust float-to-int parsing pipelines."""
    assert review_backend._resolve_unified_score(row, method) == expected


def test_resolve_unified_score_failures(review_backend):
    """Verifies parsing exceptions map cleanly into transparent UI error exceptions."""
    with pytest.raises(ValueError, match="cannot be empty"):
        review_backend._resolve_unified_score({"SCORE": None}, "REBA")

    with pytest.raises(ValueError, match="Uncastable summary score"):
        review_backend._resolve_unified_score({"SCORE": "corrupted_text"}, "REBA")

    with pytest.raises(
        ValueError, match="No valid summary assessment score column discovered"
    ):
        review_backend._resolve_unified_score({"Malformed_Layout": 12}, "REBA")


def test_resolve_risk_level_variants(review_backend):
    """Ensures rigid typing constraints map input fields precisely into static RiskLevel structures."""

    with pytest.raises(
        ValueError, match="Missing mandatory descriptive 'risk' indicator"
    ):
        review_backend._resolve_risk_level({"No_Column_Present": 0})

    with pytest.raises(ValueError, match="contains a null or empty value"):
        review_backend._resolve_risk_level({"RISK_LEVEL": "   "})

    with pytest.raises(
        ValueError, match="is not a registered classification type of RiskLevel"
    ):
        review_backend._resolve_risk_level({"MY_RISK": "catastrophic"})
