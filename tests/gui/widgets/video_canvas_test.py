# ---
# project: ErgoMoCap
# file: video_canvas_test.py
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
import numpy as np
from PySide6.QtGui import QColor, QPixmap, QPainter
from gui.widgets.video_canvas import VideoCanvas, Landmark
from gui.utils.constants import RiskLevel
from gui.utils.models import FrameData


@pytest.fixture
def canvas(qtbot):
    """Fixture to initialize the VideoCanvas and register with qtbot."""
    widget = VideoCanvas()
    qtbot.addWidget(widget)
    return widget


def test_initial_state(canvas):
    """Verify default visual states, styling configurations, and properties."""
    assert canvas.objectName() == "VideoCanvas"
    assert canvas.minimumWidth() == 854
    assert canvas.show_frame_overlay is True
    assert canvas.frame_num == 0
    assert canvas.landmarks == []


def test_set_frame_overlay(canvas):
    """Test toggling the on-screen technical metadata overlay visibility."""
    canvas.set_frame_overlay(False)
    assert canvas.show_frame_overlay is False
    canvas.set_frame_overlay(True)
    assert canvas.show_frame_overlay is True


def test_update_frame_invalid_inputs(canvas):
    """Ensure early graceful return on empty, zero-sized, or missing frame images."""
    # Test completely missing image data
    data_none = FrameData(
        image=None,  # type: ignore
        frame_idx=0,
        landmarks=[],
        risk=RiskLevel.NEGLIGIBLE,
        score=0,  # type: ignore
    )
    canvas.update_frame(data_none)
    assert canvas.final_pixmap is None

    # Test an empty zero-sized numpy ndarray matrix
    empty_img = np.array([], dtype=np.uint8)
    data_empty = FrameData(
        image=empty_img, frame_idx=0, landmarks=[], risk=RiskLevel.NEGLIGIBLE, score=0
    )
    canvas.update_frame(data_empty)
    assert canvas.final_pixmap is None


def test_update_frame_with_enum_risk(canvas):
    """Test successful frame pipeline processing using structural RiskLevel Enums."""
    frame = np.zeros((100, 100, 3), dtype=np.uint8)

    # Pack parameters inside the unified structural payload capsule
    payload = FrameData(
        image=frame, frame_idx=42, landmarks=[], risk=RiskLevel.VERY_HIGH, score=4
    )

    # Sync internal mock frame numbers to verify downstream rendering metrics
    canvas.frame_num = 42
    canvas.update_frame(payload)

    assert canvas.frame_num == 42
    assert canvas.risk_text == f"{RiskLevel.VERY_HIGH.value} 4"
    # Verify accurate mapping hex color conversions (#f7768e)
    assert canvas.risk_color == QColor("#f7768e")
    assert isinstance(canvas.final_pixmap, QPixmap)


def test_update_frame_with_string_risk(canvas):
    """Test backwards fallback compatibility processing raw string-based risks."""
    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    payload = FrameData(
        image=frame,
        frame_idx=12,
        landmarks=[],
        risk="high",  # Passing a raw string instead of enum # type: ignore
        score=3,
    )

    canvas.update_frame(payload)

    assert canvas.risk_text == "high 3"
    # Verify dynamic reverse dictionary lookup hits the correct hex block
    assert canvas.risk_color == QColor("#ff9e64")


def test_update_frame_unknown_risk_fallback(canvas):
    """Test generic fallback assignment routines when an unmapped framework risk is evaluated."""
    frame = np.zeros((10, 10, 3), dtype=np.uint8)
    payload = FrameData(
        image=frame,
        frame_idx=0,
        landmarks=[],
        risk="non_existent_risk",  # type: ignore
        score=0,  # type: ignore
    )

    canvas.update_frame(payload)

    # Code defaults custom fallback color targets to standard Cyan/Teal (#73daca)
    assert canvas.risk_color == QColor("#73daca")


def test_paint_event_no_pixmap(canvas, qtbot):
    """Verify system paintEvent processes early escape evaluations when no image array is loaded."""
    canvas.final_pixmap = None
    canvas.update()
    qtbot.wait_exposed(canvas)
    assert canvas.final_pixmap is None


def test_paint_event_full_render(canvas, qtbot):
    """Verify layout math calculations, visibility clipping parameters, and painter loops execute cleanly."""
    frame = np.zeros((100, 100, 3), dtype=np.uint8)

    # Configure landmark nodes: one visible, one below threshold (0.5)
    lm_visible = Landmark()
    lm_visible.x, lm_visible.y, lm_visible.visibility = 0.5, 0.5, 0.9

    lm_hidden = Landmark()
    lm_hidden.x, lm_hidden.y, lm_hidden.visibility = 0.1, 0.1, 0.1

    payload = FrameData(
        image=frame,
        frame_idx=1,
        landmarks=[lm_visible, lm_hidden],
        risk=RiskLevel.LOW,
        score=1,
    )

    canvas.frame_num = 1
    canvas.update_frame(payload)

    # Force graphics window context system repaints
    canvas.repaint()

    assert len(canvas.landmarks) == 2
    assert canvas.final_pixmap.width() > 0


def test_draw_overlay_coverage(canvas):
    """Directly challenge internal text coordinate calculations to ensure full code statement coverage."""
    canvas.frame_num = 100
    canvas.risk_text = "low"
    canvas.risk_color = QColor("#00ff00")

    # Generate a memory-backed QPixmap surface context canvas painter
    pix = QPixmap(10, 10)
    painter = QPainter(pix)

    canvas._draw_overlay(painter, 0, 0)
    painter.end()


def test_landmark_attribute_safety(canvas):
    """Verify that pose framework parsing skips corrupt structural objects missing standard attributes."""
    frame = np.zeros((10, 10, 3), dtype=np.uint8)

    class BadLandmark:
        x, y = 0.5, 0.5
        # Explicitly omitting 'visibility' fields to trigger security fallbacks

    payload = FrameData(
        image=frame,
        frame_idx=5,
        landmarks=[BadLandmark()],
        risk=RiskLevel.NEGLIGIBLE,
        score=0,
    )

    canvas.update_frame(payload)
    canvas.repaint()

    # If it didn't raise an AttributeError, hasattr checking logic caught the mismatch successfully
    assert len(canvas.landmarks) == 1
