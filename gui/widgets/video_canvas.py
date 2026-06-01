# ---
# project: ErgoMoCap
# file: video_canvas.py
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
ErgoMoCap: Video Canvas
-----------------------
Visual rendering components for motion capture and ergonomic feedback.

This module provides the `VideoCanvas` class, a specialized `QLabel` designed to
render synchronized video streams and skeletal overlays. It handles the
real-time conversion of `OpenCV` frames to `PySide6` graphics, applies dynamic
scaling while maintaining aspect ratios, and overlays coordinate-based landmarks
color-coded by ergonomic risk levels.

TODO refractor this code, it's still trying to paint while the annotation is done with freemocap!
"""

from typing import Any

from PySide6.QtCore import QRect, QSize, Qt, QPointF, Slot, Signal
from PySide6.QtGui import (
    QImage,
    QPaintEvent,
    QPainter,
    QPen,
    QColor,
    QPixmap,
    QMouseEvent,
)
from PySide6.QtWidgets import (
    QLabel,
)
from cv2.typing import MatLike

import cv2

from gui.utils.constants import RiskLevel
from gui.utils.models import FrameData, VideoPosition


class Landmark:
    """
    Mock class defining the structure of a pose landmark.

    This class serves as a lightweight data structure to represent spatial
    coordinates and detection confidence without requiring the full MediaPipe
    dependency.

    Attributes:
        x (float): Normalized horizontal coordinate (0.0 to 1.0).
        y (float): Normalized vertical coordinate (0.0 to 1.0).
        z (float): Normalized depth coordinate.
        visibility (float): Confidence score of the landmark detection.
    """

    x: float
    y: float
    z: float
    visibility: float


class VideoCanvas(QLabel):
    """
    A custom QLabel widget for rendering video frames and overlaying motion capture data.

    This class handles the conversion of `numpy.ndarray` (OpenCV frames) to `QPixmap`,
    calculates centered scaling for display, and paints skeletal landmarks with
    dynamic color-coding based on [RiskLevel][gui.utils.constants.RiskLevel].

    Attributes:
        seek_requested (Signal): Emits the target frame index (`int`).
        toggle_requested (Signal): Emits a request to play/pause.
        final_pixmap (QPixmap | None): The processed and scaled image ready for painting.
        landmarks (list[Any]): A `list` of detected pose landmarks for the current frame.
        frame_num (int): Current frame index for the overlay display.
        total_frames (int): Total frame count for scroller synchronization.
        risk_color (QColor): The color assigned to landmarks based on the ergonomic risk level.
        risk_text (str): String representation of the current risk level.
        show_frame_overlay (bool): Toggle for displaying frame metadata on screen.
        color_map (dict[RiskLevel, str]): Mapping of risk levels to hexadecimal color codes.

    Methods:
        __init__: Initializes the VideoCanvas with default dimensions and styling.
        set_frame_overlay: Toggle the visibility of the on-screen frame and risk metadata.
        update_position: Update the internal frame counters for seeker rendering.
        mousePressEvent: Handle mouse clicks for video seeking and playback toggling.
        update_frame: Update the canvas with a new video frame and associated metadata.
        paintEvent: Handles the rendering of the frame and the skeletal overlays.
        _draw_seeker: Draw the interactive seeker bar at the bottom of the video.
        _draw_overlay: Draw technical metadata onto the video surface.
    """

    seek_requested: Signal = Signal(
        int
    )  # Don't delete, connects to frontend -> backend -> video_worker
    toggle_requested: Signal = (
        Signal()
    )  # Don't delete, connects to frontend -> backend -> video_worker

    def __init__(self) -> None:
        """
        Initializes the VideoCanvas with default dimensions and styling.

        Returns:
            None (None): Initializer return.
        """
        super().__init__()
        self.setMinimumSize(854, 480)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setObjectName("VideoCanvas")

        self.final_pixmap: QPixmap | None = None
        self.landmarks: list[Any] = []
        self.frame_num: int = 0
        self.total_frames: int = 0
        self.risk_color: QColor = QColor("#9ece6a")
        self.risk_text: str = ""
        self.show_frame_overlay: bool = True

        self.color_map: dict[RiskLevel, str] = {
            RiskLevel.VERY_HIGH: "#f7768e",  # Red
            RiskLevel.HIGH: "#ff9e64",  # Orange
            RiskLevel.MEDIUM: "#e0af68",  # Yellow/Gold
            RiskLevel.LOW: "#9ece6a",  # Green
            RiskLevel.NEGLIGIBLE: "#73daca",  # Cyan/Teal
        }

    def set_frame_overlay(self, show_frame_overlay: bool) -> None:
        """
        Toggle the visibility of the on-screen frame and risk metadata.

        Args:
            show_frame_overlay (bool): Whether to render the metadata text.

        Returns:
            None (None): Updates the overlay state.
        """
        self.show_frame_overlay = show_frame_overlay

    @Slot(VideoPosition)
    def update_position(self, video_position: VideoPosition) -> None:
        """
        Update the internal frame counters for seeker rendering.

        Args:
            video_position (VideoPosition): Structured data model containing indices
                mapped via [VideoPosition][gui.utils.models.VideoPosition].

        Returns:
            None (None): Updates internal state.
        """
        self.frame_num = video_position.current_frame
        self.total_frames = video_position.total_frames

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """
        Handle mouse clicks for video seeking and playback toggling.

        Detects if a click lands within the bottom seeker boundary to dispatch frame skips
        via `seek_requested`, or hits the focal display canvas to toggle media playback.

        Args:
            event (QMouseEvent): Mouse event containing click coordinates.

        Returns:
            None (None): Emits control signals.
        """
        if not self.final_pixmap:
            return

        rect = self.contentsRect()
        # Video area dimensions
        vw, vh = self.final_pixmap.width(), self.final_pixmap.height()
        vx = rect.left() + (rect.width() - vw) // 2
        vy = rect.top() + (rect.height() - vh) // 2

        # Check if click is in the bottom seeker area (last 20px of video)
        if vy + vh - 20 <= event.position().y() <= vy + vh:
            relative_x = event.position().x() - vx
            if 0 <= relative_x <= vw:
                target_frame = int((relative_x / vw) * self.total_frames)
                self.seek_requested.emit(target_frame)
        else:
            self.toggle_requested.emit()

    @Slot(FrameData)
    def update_frame(self, frame_data: FrameData) -> None:
        """
        Update the canvas with a new video frame and associated metadata.

        Converts the raw image data to a scaled `QPixmap`, determines the
        visual color for landmarks based on the ergonomic risk level, and
        triggers a repaint.

        Args:
            frame_data (FrameData): Frame data capsule defined by
                [FrameData][gui.utils.models.FrameData], containing the underlying
                `numpy.ndarray` matrix image buffer and landmark listings.

        Returns:
            None (None): Emits an internal update request to trigger `paintEvent`.
        """
        if frame_data.image is None or frame_data.image.size == 0:
            return

        h, w, ch = frame_data.image.shape
        rgb_frame: MatLike = cv2.cvtColor(frame_data.image, cv2.COLOR_BGR2RGB)
        q_img: QImage = QImage(
            rgb_frame.data, w, h, ch * w, QImage.Format.Format_RGB888
        ).copy()
        pix: QPixmap = QPixmap.fromImage(q_img)

        safe_size: QSize = self.contentsRect().size()

        self.final_pixmap = pix.scaled(
            safe_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.landmarks = frame_data.landmarks

        risk_value = frame_data.risk if frame_data.risk else RiskLevel.NEGLIGIBLE
        risk_score = frame_data.score if frame_data.score else 0

        if isinstance(risk_value, str):
            self.risk_text = risk_value + " " + str(risk_score)
            self.risk_color = QColor(
                next(
                    (c for r, c in self.color_map.items() if r.value == risk_value),
                    "#73daca",
                )
            )
        else:
            self.risk_text = risk_value.value + " " + str(risk_score)
            self.risk_color = QColor(self.color_map.get(risk_value, "#73daca"))

        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        """
        Handles the rendering of the frame and the skeletal overlays.

        Calculates the centered position of the scaled pixmap within the widget's
        available space and draws landmarks as ellipses if they meet the
        visibility threshold.

        Args:
            event (QPaintEvent): The paint event triggered by the system or `update()`.

        Returns:
            None (None): Draws directly to the widget's surface.
        """
        if not self.final_pixmap:
            super().paintEvent(event)
            return
        painter: QPainter = QPainter(self)

        rect: QRect = self.contentsRect()

        x: int = rect.left() + (rect.width() - self.final_pixmap.width()) // 2
        y: int = rect.top() + (rect.height() - self.final_pixmap.height()) // 2

        painter.drawPixmap(x, y, self.final_pixmap)

        if self.landmarks:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(QPen(self.risk_color, 3))
            for lm in self.landmarks:
                if hasattr(lm, "visibility") and lm.visibility > 0.5:
                    px = x + (lm.x * self.final_pixmap.width())
                    py = y + (lm.y * self.final_pixmap.height())
                    painter.drawEllipse(QPointF(px, py), 4, 4)

        if self.show_frame_overlay:
            self._draw_overlay(painter, x, y)

        self._draw_seeker(
            painter, x, y, self.final_pixmap.width(), self.final_pixmap.height()
        )

    def _draw_seeker(self, painter: QPainter, x: int, y: int, w: int, h: int) -> None:
        """
        Draw the interactive seeker bar at the bottom of the video.

        Args:
            painter (QPainter): The active painting object.
            x (int): Video horizontal offset.
            y (int): Video vertical offset.
            w (int): Video width.
            h (int): Video height.

        Returns:
            None (None): Draws seeker bar.
        """
        if self.total_frames <= 0:
            return

        seeker_y = y + h - 10
        painter.setPen(Qt.PenStyle.NoPen)

        # Background bar
        painter.setBrush(QColor(100, 100, 100, 150))
        painter.drawRect(x, seeker_y, w, 5)

        # Progress bar
        progress_w = int((self.frame_num / self.total_frames) * w)
        painter.setBrush(self.risk_color)
        painter.drawRect(x, seeker_y, progress_w, 5)

    def _draw_overlay(self, painter: QPainter, x: int, y: int):
        """
        Draw technical metadata onto the video surface.

        Args:
            painter (QPainter): The active painting object.
            x (int): Horizontal offset of the scaled video.
            y (int): Vertical offset of the scaled video.

        Returns:
            None (None): Renders text using the active painter.
        """
        painter.setPen(QColor("#ff0000ff"))
        painter.setFont(self.font())
        painter.drawText(x + 10, y + 20, f"FRAME: #{self.frame_num:05d}")
        painter.setPen(QPen(self.risk_color, 2))
        painter.drawText(x + 10, y + 35, f"RISK: {self.risk_text.upper()}")
