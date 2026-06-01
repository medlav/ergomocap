# ---
# project: ErgoMoCap
# file: video_worker.py
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
ErgoMoCap: Video Engine Worker
------------------------------
Stateful Video I/O and Telemetry Synchronization Engine.

This module implements the `VideoWorker`, a specialized background execution component
designed to run within a dedicated worker thread. It isolates heavy file system operations,
frame decoding using `OpenCV`, and unthrottled media encoding workflows from the primary
user interface thread.

By utilizing a non-blocking `QTimer` lifecycle architecture rather than blocking loops,
the worker delivers fluid playback frame buffers synchronized frame-by-frame with
precalculated ergonomic risk metrics and categorical data payloads.
"""

from typing import Any, Optional
from pathlib import Path
import cv2
import numpy as np
from PySide6.QtCore import QObject, Signal, Slot, QTimer

from gui.utils.models import (
    FrameData,
    FramesExportResult,
    VideoCommand,
    VideoControl,
    VideoLoadRequest,
    VideoPosition,
)


from gui.core.analysis_engine import AnalysisEngine


class VideoWorker(QObject):
    """
    Stateful worker managing video I/O, scoring overlays, and frame exporting.

    This component runs inside its own dedicated worker thread managed by the application backend.
    It uses a non-blocking `QTimer` lifecycle architecture to decode media frames sequentially,
    synchronize them with risk metadata matrices, and emit rendering capsules to the GUI layer.

    Attributes:
        frame_ready (Signal): Signal emitted when a new frame is decoded and processed ([FrameData][gui.utils.models.FrameData]).
        position_changed (Signal): Signal emitted on playback updates containing timeline values ([VideoPosition][gui.utils.models.VideoPosition]).
        export_progress (Signal): Signal emitted to track frame write cycles ([VideoPosition][gui.utils.models.VideoPosition]).
        frames_export_finished (Signal): Signal emitted on export completion ([FramesExportResult][gui.utils.models.FramesExportResult]).
        cap (cv2.VideoCapture | None): The open file stream capture decoder wrapper instance.
        video_path (str): File system path pointing to the active media asset.
        scores_list (list[int]): Array sequence tracking calculated analytical scores matching frame indices.
        thresholds (list[tuple[int, Any]]): Boundary score structures used to determine qualitative classification steps.
        total_frames (int): Total frame count value assigned by the video header stream analyzer.
        current_frame_idx (int): Current frame playback pointer index counter.
        playback_timer (QTimer | None): Internal non-blocking loop scheduler driving periodic frame steps.

    Methods:
        init_timer: Create and initialize the internal timer inside the worker thread space.
        initialize_video: Configures the current video asset context safely.
        cleanup: Shuts down any active playback intervals and releases open media stream file handles.
        handle_video_control: Processes video commands safely inside the worker thread.
        toggle_playback: Starts or stops the frame ticker timer.
        seek: Public slot accepting external target navigation frames.
        step_frame: Steps sequentially up or down one tick.
        _seek_to_index: Updates internal stream pointers and reads video matrix segments.
        _process_playback_frame: Handles cyclic timer ticks to read, increment, and emit media data frames.
        _emit_current_frame_payload: Bundles spatial features and risk labels into metadata packets.
        execute_frames_export: Runs an unthrottled loop to combine frame saving and rendering into a single worker script.
    """

    frame_ready: Signal = Signal(FrameData)
    position_changed: Signal = Signal(VideoPosition)
    export_progress: Signal = Signal(VideoPosition)  # current, total
    frames_export_finished: Signal = Signal(FramesExportResult)

    def __init__(self) -> None:

        super().__init__()
        self.cap: Optional[cv2.VideoCapture] = None
        self.video_path: str = ""
        self.scores_list: list[int] = []
        self.thresholds: list[tuple[int, Any]] = []

        self.total_frames: int = 0
        self.current_frame_idx: int = 0

        # Drive playback via a Qt Timer rather than blocking loops
        self.playback_timer: Optional[QTimer] = None

    @Slot()
    def init_timer(self) -> None:
        """
        Create and initialize the internal timer inside the worker thread space.

        Instantiates the `QTimer` framework container directly inside the executing thread context
        to maintain thread-safe affinity boundaries and hooks up the loop timeout callback.

        Returns:
            None (None): Modifies the object state in-place.
        """
        self.playback_timer = QTimer(self)
        self.playback_timer.timeout.connect(self._process_playback_frame)

    @Slot(VideoLoadRequest)
    def initialize_video(
        self,
        video_load_request: VideoLoadRequest,
    ) -> None:
        """
        Configures the current video asset context safely.

        Resets ongoing playback loops, releases any pre-allocated system video capture handles,
        parses technical properties from the target file configuration payload, and renders
        the initial frame slice.

        Args:
            video_load_request (VideoLoadRequest): Configuration descriptor mapping paths, scores,
                and boundaries via [VideoLoadRequest][gui.utils.models.VideoLoadRequest].

        Returns:
            None (None): Dispatches a preview frame or reinitializes structural attributes.
        """

        if not self.playback_timer:
            self.init_timer()

        if not self.playback_timer:
            return
        self.playback_timer.stop()
        if self.cap:
            self.cap.release()

        self.video_path = str(video_load_request.path)
        self.scores_list = list(video_load_request.scores)
        self.thresholds = video_load_request.thresholds

        self.cap = cv2.VideoCapture(self.video_path)
        fps = self.cap.get(cv2.CAP_PROP_FPS) or 30.0
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.current_frame_idx = 0

        # Calculate dynamic frame timing interval in milliseconds

        self.playback_interval_ms = int(1000 / fps)

        # Render the initial preview frame
        self._seek_to_index(0)

    @Slot()
    def cleanup(self) -> None:
        """
        Shuts down any active playback intervals and releases open media stream file handles.

        Returns:
            None (None): In-place cleanup execution wrapper.
        """
        if self.playback_timer:
            self.playback_timer.stop()
        if self.cap:
            self.cap.release()

    @Slot(VideoControl)
    def handle_video_control(self, action: VideoControl) -> None:
        """
        Processes video commands safely inside the worker thread.

        Parses incoming action commands to adjust playback states, perform hard index skips,
        or step through sequential frames frame-by-frame.

        Args:
            action (VideoControl): Message bundle specifying state commands mapped by
                [VideoControl][gui.utils.models.VideoControl].

        Returns:
            None (None): Performs state routing and state updates.
        """
        if action.command == VideoCommand.TOGGLE:
            self.toggle_playback()  # Starts/stops your QTimer safely here!

        elif action.command == VideoCommand.SEEK:
            if action.target_frame is not None:
                self.current_frame_idx = max(
                    0, min(action.target_frame, self.total_frames - 1)
                )
                self.seek(frame_idx=self.current_frame_idx)

        elif action.command == VideoCommand.STEP_FORWARD:
            self.current_frame_idx = min(
                self.current_frame_idx + 1, self.total_frames - 1
            )
            self.step_frame(forward=True)

        elif action.command == VideoCommand.STEP_BACKWARD:
            self.current_frame_idx = max(0, self.current_frame_idx - 1)
            self.step_frame(forward=False)

    @Slot()
    def toggle_playback(self) -> bool:
        """
        Starts or stops the frame ticker timer.

        Evaluates operational flags, state loops, and active timers to cleanly toggle
        periodic media processing routines.

        Returns:
            bool (`bool`): True if a timer sequence successfully started, False if it was paused or failed.
        """
        if not self.cap or not self.cap.isOpened():
            return False

        if not self.playback_timer:
            return False

        if self.playback_timer.isActive():
            self.playback_timer.stop()
            return False
        else:
            self.playback_timer.start(self.playback_interval_ms)
            return True

    @Slot(int)
    def seek(self, frame_idx: int) -> None:
        """
        Public slot accepting external target navigation frames.

        Args:
            frame_idx (int): Absolute destination index path targeting targeted index segments.

        Returns:
            None (None): Dispatches internal seek handlers.
        """
        self._seek_to_index(frame_idx)

    @Slot(bool)
    def step_frame(self, forward: bool) -> None:
        """
        Steps sequentially up or down one tick.

        Args:
            forward (bool): Set to True to increment the timeline frame index, False to decrement.

        Returns:
            None (None): Dispatches updated coordinate mappings.
        """
        target = self.current_frame_idx + 1 if forward else self.current_frame_idx - 1
        self._seek_to_index(target)

    def _seek_to_index(self, frame_idx: int) -> None:
        """
        Updates internal stream pointers and reads video matrix segments.

        Handles hardware pointer relocations inside `cv2.VideoCapture` wrappers and invokes
        the payload packager instantly to prevent rendering lag.

        Args:
            frame_idx (int): Clean target bounding parameter mapping specific file indexes.

        Returns:
            None (None): Restores layout tracking bounds.
        """
        if not self.cap or not self.cap.isOpened():
            return

        target = max(0, min(frame_idx, self.total_frames - 1))
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, target)
        self.current_frame_idx = target

        # Instantly render the target frame context
        ret, frame = self.cap.read()
        if ret:
            self._emit_current_frame_payload(frame)
            # Re-seek back to catch the frame for future regular playback ticks
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, target)

    def _process_playback_frame(self) -> None:
        """
        Handles cyclic timer ticks to read, increment, and emit media data frames.

        Monitors frame index bounds and terminates timer execution loops automatically
        if end-of-file flags or validation faults occur during extraction.

        Returns:
            None (None): Advances timeline state metrics or halts active timers.
        """
        if not self.playback_timer:
            return

        if not self.cap or not self.cap.isOpened():
            self.playback_timer.stop()
            return

        ret, frame = self.cap.read()
        if not ret or self.current_frame_idx >= self.total_frames:
            self.playback_timer.stop()
            return

        self._emit_current_frame_payload(frame)
        self.current_frame_idx += 1

    def _emit_current_frame_payload(self, frame: np.ndarray) -> None:
        """
        Bundles spatial features and risk labels into metadata packets.

        Evaluates index points against calculated assessment tables, extracts structural enum items
        via [AnalysisEngine.get_risk_level_enum][gui.core.analysis_engine.AnalysisEngine.get_risk_level_enum],
        and emits telemetry packages.

        Args:
            frame (numpy.ndarray): Multi-dimensional matrix array tracking pixel layouts.

        Returns:
            None (None): Dispatches tracking telemetry signals out to attached subscribers.
        """

        score = None
        risk = None

        if self.scores_list and self.current_frame_idx < len(self.scores_list):
            score = self.scores_list[self.current_frame_idx]

            if self.thresholds:
                risk = AnalysisEngine.get_risk_level_enum(score, self.thresholds)

        self.frame_ready.emit(
            FrameData(
                image=frame,
                frame_idx=self.current_frame_idx,
                landmarks=[],
                score=score,
                risk=risk,
            )
        )
        self.position_changed.emit(
            VideoPosition(
                current_frame=self.current_frame_idx,
                total_frames=self.total_frames,
            )
        )

    @Slot(str)
    def execute_frames_export(self, output_path: str) -> None:
        """
        Runs an unthrottled loop to combine frame saving and rendering into a single worker script.

        Freezes interactive timeline cycles, sets file structures up via `cv2.VideoWriter`, and loops
        sequentially through every frames slice to serialize an overlay-ready raw output file.

        Args:
            output_path (str): Intended file system path string destination where the generated media output should reside.

        Returns:
            None (None): Emits asynchronous progress telemetry bundles during processing.
        """
        if not self.playback_timer:
            return

        self.playback_timer.stop()
        if not self.cap or not self.cap.isOpened():
            self.frames_export_finished.emit(
                FramesExportResult(
                    success=False, message="No video stream initialized."
                ),
            )
            return

        try:
            # Re-verify layout specifications
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = self.cap.get(cv2.CAP_PROP_FPS) or 30.0

            fourcc = cv2.VideoWriter.fourcc(*"mp4v")
            writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

            for idx in range(self.total_frames):
                ret, frame = self.cap.read()
                if not ret:
                    break

                # Apply overlays directly here if baked exports are needed
                writer.write(frame)

                if idx % 5 == 0:
                    self.export_progress.emit(
                        VideoPosition(
                            current_frame=idx,
                            total_frames=self.total_frames,
                        )
                    )

            writer.release()
            self.frames_export_finished.emit(
                FramesExportResult(
                    success=True,
                    message=f"Export successful: {Path(output_path).name}",
                )
            )

            # Reset timeline layout preview
            self._seek_to_index(0)
        except Exception as e:
            self.frames_export_finished.emit(
                FramesExportResult(
                    success=False,
                    message=str(e),
                )
            )
