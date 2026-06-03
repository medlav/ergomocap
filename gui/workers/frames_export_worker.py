# ---
# project: ErgoMoCap
# file: frames_export_worker.py
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
ErgoMoCap: Frames Export Worker
-------------------------------
Headless frame serialization and data synchronization utilities.

This module provides multithreaded and headless components designed to extract
individual frame buffers from video recording files, write them to disk, and synchronize
them with calculated ergonomic metrics into manageable data frames.
"""

import cv2
import pandas as pd
from pathlib import Path


from PySide6.QtCore import Signal, QObject

from gui.utils.logger import logger
from gui.utils.models import VideoPosition


class FramesExportWorker(QObject):
    """
    Asynchronous worker for executing frame extraction operations inside a background thread.

    Manages the operational state lifecycle of a headless extraction run, providing cooperative
    cancellation hooks and proxying progress telemetry via Qt Signals to avoid blocking the
    primary user interface thread.

    Attributes:
        finished (Signal): Signal emitted when the frame extraction sequence completes.
        progress (Signal): Signal emitted every 5 frames containing a [VideoPosition][gui.utils.models.VideoPosition] state telemetry capsule.
        video_path (Path | str): File system path referencing the source video capture file.
        frames_dir (Path): Destination folder path where image frames will be written.
        scores_list (list[int]): Ordered sequence of calculated ergonomic risk scores.
        _is_running (bool): Internal control flag indicating active thread processing state.

    Methods:
        __init__: Initialize the worker instance with data paths and scores.
        stop: Request a cooperative cancellation of the running extraction routine.
        run: Execute the headless frame extraction loop and serialize synchronized telemetry.
    """

    finished = Signal()

    progress = Signal(VideoPosition)

    def __init__(self, video_path, frames_dir, scores_list):
        """
        Initialize the worker instance with data paths and scores.

        Args:
            video_path (Path | str): File system path referencing the source video capture file.
            frames_dir (Path): Destination folder path where image frames will be written.
            scores_list (list[int]): Ordered sequence of calculated ergonomic risk scores.

        Returns:
            None (None): Initializer return.
        """
        super().__init__()
        self.video_path = video_path
        self.frames_dir = frames_dir
        self.scores_list = scores_list

        self._is_running = False

    def stop(self):
        """
        Request a cooperative cancellation of the running extraction routine.

        Sets the internal execution flags to false, prompting the underlying headless processor
        loop to break operations at the next evaluation interval.

        Returns:
            None (None): Updates the internal running state.
        """
        self._is_running = False

    def run(self):
        """
        Execute the headless frame extraction loop and serialize synchronized telemetry.

        Launches the core engine runner, tracks progress metrics via signal emitters,
        and upon valid completion writes out a structured mapping index file using
        [pandas.DataFrame.to_csv][pandas.DataFrame.to_csv].

        Returns:
            None (None): Dispatches lifecycle termination signals to the main listener thread.
        """
        self._is_running = True
        # We pass self.progress.emit directly as the callback
        df = export_frames_headless(
            video_path=self.video_path,
            output_folder=self.frames_dir,
            scores_list=self.scores_list,
            progress_callback=self.progress.emit,
            should_stop=lambda: not self._is_running,
        )

        if df is not None and not df.empty:
            df.to_csv(self.frames_dir / "synchronized_data.csv", index=False)

        self.finished.emit()


def export_frames_headless(
    video_path, output_folder, scores_list=[], progress_callback=None, should_stop=None
) -> pd.DataFrame:
    """
    Headless pipeline to extract frames sequentially and compile an indexed telemetry dataset.

    Parses raw video frames using `cv2.VideoCapture`, serializes compressed jpeg imagery
    directly to disk, and returns a cumulative `pandas.DataFrame` correlating index positions
    to associated risk profiles.

    Args:
        video_path (Path | str): File system path referencing the source video capture file.
        output_folder (Path | str): Target filesystem directory where frame slices should reside.
        scores_list (list[int]): Optional ordered array containing specific ergonomic scores per frame index. Defaults to `[]`.
        progress_callback (Callable[[VideoPosition], None] | None): Callback function invoked with [VideoPosition][gui.utils.models.VideoPosition] elements every 5 processed loops. Defaults to `None`.
        should_stop (Callable[[], bool] | None): Lambda function evaluated at loop cycle boundaries to handle execution abort requests. Defaults to `None`.

    Returns:
        pandas.DataFrame (`pandas.DataFrame`): Master index log mapping specific frame indices, generated file paths, and metadata metrics.
    """
    cap = cv2.VideoCapture(str(video_path))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_idx = 0
    exported_data = []

    while True:
        if should_stop and should_stop():
            logger.warning("Export stopped by user.")
            break
        ret, frame = cap.read()
        if not ret:
            break

        file_name = f"frame_{frame_idx:06d}.jpg"
        cv2.imwrite(str(Path(output_folder) / file_name), frame)

        row = {"frame_idx": frame_idx, "filename": file_name}
        if scores_list and frame_idx < len(scores_list):
            row.update({"reba_score": scores_list[frame_idx]})

        exported_data.append(row)
        frame_idx += 1

        # Emit current and total
        if progress_callback and frame_idx % 5 == 0:
            progress_callback(
                VideoPosition(
                    current_frame=frame_idx,
                    total_frames=total_frames,
                )
            )

    cap.release()
    return pd.DataFrame(exported_data)
