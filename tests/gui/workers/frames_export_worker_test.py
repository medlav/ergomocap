# ---
# project: ErgoMoCap
# file: frames_export_worker_test.py
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

from unittest.mock import MagicMock, patch
import pytest
import pandas as pd
import numpy as np

from gui.workers.frames_export_worker import FramesExportWorker, export_frames_headless


@pytest.fixture
def mock_cv2_pipeline():
    """Mock standard cv2 behaviors for video processing and frame saving."""
    with (
        patch("gui.workers.frames_export_worker.cv2.VideoCapture") as mock_cap_class,
        patch("gui.workers.frames_export_worker.cv2.imwrite") as mock_imwrite,
    ):
        mock_instance = MagicMock()
        mock_cap_class.return_value = mock_instance

        # Configure default video with 12 frames total
        mock_instance.get.return_value = 12.0

        # Simulate sequential reads: 12 valid frames, then EOF (ret=False)
        frame_sequence = [
            (True, np.zeros((480, 640, 3), dtype=np.uint8)) for _ in range(12)
        ]
        frame_sequence.append((False, None))  # type: ignore
        mock_instance.read.side_effect = frame_sequence

        yield {"capture_instance": mock_instance, "imwrite": mock_imwrite}


@pytest.fixture
def sample_setup(tmp_path):
    """Provides valid configuration parameters using temporary testing directories."""
    return {
        "video_path": tmp_path / "test_video.mp4",
        "frames_dir": tmp_path / "extracted_frames",
        "scores_list": [
            1,
            2,
            3,
            2,
            1,
            4,
            5,
            4,
            3,
            2,
            1,
            5,
        ],  # Length matching 12 frames
    }


# ==============================================================================
# STANDALONE HEADLESS ENGINE PIPELINE TESTS
# ==============================================================================


def test_export_frames_headless_success(mock_cv2_pipeline, sample_setup):
    """Verify clean sequential frame slicing, score tracking, and progress emissions."""
    progress_calls = []

    def progress_sink(pos):
        progress_calls.append(pos)

    # Ensure destination path exists
    sample_setup["frames_dir"].mkdir(parents=True, exist_ok=True)

    df = export_frames_headless(
        video_path=sample_setup["video_path"],
        output_folder=sample_setup["frames_dir"],
        scores_list=sample_setup["scores_list"],
        progress_callback=progress_sink,
        should_stop=None,
    )

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 12
    assert "reba_score" in df.columns
    assert list(df["reba_score"]) == sample_setup["scores_list"]

    # Progress signals are emitted every 5 frames (idx 5 and idx 10 out of 12)
    assert len(progress_calls) == 2
    assert progress_calls[0].current_frame == 5
    assert progress_calls[0].total_frames == 12
    assert progress_calls[1].current_frame == 10

    # Ensure cv2 pipeline was cleaned up properly
    mock_cv2_pipeline["capture_instance"].release.assert_called_once()
    assert mock_cv2_pipeline["imwrite"].call_count == 12


def test_export_frames_headless_cooperative_cancellation(
    mock_cv2_pipeline, sample_setup
):
    """Verify the execution loop stops instantly when the cancellation lambda evaluates to True."""
    # Force cancellation on the 3rd index frame
    stop_evaluator = MagicMock(side_effect=[False, False, True])

    df = export_frames_headless(
        video_path=sample_setup["video_path"],
        output_folder=sample_setup["frames_dir"],
        scores_list=sample_setup["scores_list"],
        progress_callback=None,
        should_stop=stop_evaluator,
    )

    # Processed exactly 2 loops before breaking on the 3rd evaluation boundary
    assert len(df) == 2
    assert mock_cv2_pipeline["imwrite"].call_count == 2
    mock_cv2_pipeline["capture_instance"].release.assert_called_once()


def test_export_frames_headless_missing_or_short_scores(
    mock_cv2_pipeline, sample_setup
):
    """Verify column synchronization safety when scores list is absent or shorter than total frames."""
    # Scenario: 12 frames found, but scores tracking array contains only 2 elements
    short_scores = [9, 8]

    df = export_frames_headless(
        video_path=sample_setup["video_path"],
        output_folder=sample_setup["frames_dir"],
        scores_list=short_scores,
        progress_callback=None,
        should_stop=None,
    )

    assert len(df) == 12
    # Ensure scores map for the first two items and cleanly default to NaN/None for others
    assert df.loc[0, "reba_score"] == 9
    assert df.loc[1, "reba_score"] == 8
    assert pd.isna(df.loc[2, "reba_score"])


# ==============================================================================
# ASYNCHRONOUS WORKER OPERATIONS & LIFECYCLE TESTS
# ==============================================================================


def test_worker_initialization_state(sample_setup):
    """Verify initialization variables map smoothly onto worker properties on instantiation."""
    worker = FramesExportWorker(
        video_path=sample_setup["video_path"],
        frames_dir=sample_setup["frames_dir"],
        scores_list=sample_setup["scores_list"],
    )

    assert worker.video_path == sample_setup["video_path"]
    assert worker.frames_dir == sample_setup["frames_dir"]
    assert worker.scores_list == sample_setup["scores_list"]
    assert worker._is_running is False


def test_worker_stop_action(sample_setup):
    """Verify cooperative cancellation trigger updates active internal running flags."""
    worker = FramesExportWorker(
        video_path=sample_setup["video_path"],
        frames_dir=sample_setup["frames_dir"],
        scores_list=sample_setup["scores_list"],
    )
    worker._is_running = True

    worker.stop()
    assert worker._is_running is False


def test_worker_run_workflow_with_csv_serialization(
    qtbot, mock_cv2_pipeline, sample_setup, request
):
    """Verify operational loops complete, update runtime state, and save dataframes to disk."""
    sample_setup["frames_dir"].mkdir(parents=True, exist_ok=True)

    worker = FramesExportWorker(
        video_path=sample_setup["video_path"],
        frames_dir=sample_setup["frames_dir"],
        scores_list=sample_setup["scores_list"],
    )
    # Correct QObject memory teardown mechanism via finalizer
    request.addfinalizer(worker.deleteLater)

    progress_signals = []
    worker.progress.connect(progress_signals.append)

    # Run background processing workflow while observing finished lifecycle signals
    with qtbot.wait_signal(worker.finished, timeout=500):
        worker.run()

    # Verify that a telemetry dataframe CSV file was exported inside the frames directory
    expected_csv = sample_setup["frames_dir"] / "synchronized_data.csv"
    assert expected_csv.is_file()

    # Re-verify structured data elements from written artifact
    saved_df = pd.read_csv(expected_csv)
    assert len(saved_df) == 12
    assert list(saved_df["reba_score"]) == sample_setup["scores_list"]
    assert len(progress_signals) == 2


def test_worker_run_empty_or_canceled_skips_csv_generation(
    qtbot, mock_cv2_pipeline, sample_setup, request
):
    """Verify CSV generation is bypassed cleanly if the operation returns empty or no telemetry."""
    worker = FramesExportWorker(
        video_path=sample_setup["video_path"],
        frames_dir=sample_setup["frames_dir"],
        scores_list=sample_setup["scores_list"],
    )
    request.addfinalizer(worker.deleteLater)

    # Inject an immediate stop hook execution step inside the pipeline mock loop execution space
    with patch(
        "gui.workers.frames_export_worker.export_frames_headless",
        return_value=pd.DataFrame(),
    ) as mock_pipeline:
        with qtbot.wait_signal(worker.finished, timeout=500):
            worker.run()

        mock_pipeline.assert_called_once()
        expected_csv = sample_setup["frames_dir"] / "synchronized_data.csv"
        # Ensure file generation didn't process due to empty operational frame bounds
        assert not expected_csv.exists()
