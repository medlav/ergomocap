# ---
# project: ErgoMoCap
# file: wrist_reba_test.py
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
from calculators.reba_calculator.body_parts.wrist_reba import wrist_reba_score


def test_wrist_neutral_position():
    """Test both wrists in neutral position (0 degrees)."""
    # [R_flex, L_flex, R_side, L_side, R_twist, L_twist]
    input_data = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0], dtype=np.float64)
    result = wrist_reba_score(input_data)
    assert result[0] == 1  # Total
    assert result[1] == 1  # Flex
    assert result[2] == 0  # Side
    assert result[3] == 0  # Torsion


def test_wrist_flexion_right_greater_than_left():
    """
    Force the first 'if' branch: right_flex > left_flex.
    Covers lines 86-89.
    """
    # Right is 15 (Score 2), Left is 10. 15 > 10 triggers the first block.
    input_data = np.array([15.0, 10.0, 0.0, 0.0, 0.0, 0.0], dtype=np.float64)
    result = wrist_reba_score(input_data)
    assert result[1] == 2


def test_wrist_flexion_left_greater_than_right():
    """
    Force the 'else' branch: left_flex >= right_flex.
    Covers lines 91-94.
    """
    # Left is 15 (Score 2), Right is 10. 15 > 10 triggers else block.
    input_data = np.array([10.0, 15.0, 0.0, 0.0, 0.0, 0.0], dtype=np.float64)
    result = wrist_reba_score(input_data)
    assert result[1] == 2


def test_wrist_extension_negative_boundary_right():
    """Force Score 2 via the negative boundary on the right side."""
    # To enter Right block, Right must be > Left.
    # -15.1 (Right) > -20.0 (Left)
    input_data = np.array([-15.1, -20.0, 0.0, 0.0, 0.0, 0.0], dtype=np.float64)
    result = wrist_reba_score(input_data)
    assert result[1] == 2


def test_wrist_extension_negative_boundary_left():
    """
    Force Score 2 via the negative boundary on the left side.
    To enter the Else (Left) block, right_flex > left_flex must be False.
    To get score 2, left_flex must be < -15.0.
    """
    # -20.0 > -16.0 is False, so the Else block (Left wrist) is used.
    # -16.0 is < -15.0, which sets wrist_flex_score to 2.
    input_data = np.array([-20.0, -16.0, 0.0, 0.0, 0.0, 0.0], dtype=np.float64)
    result = wrist_reba_score(input_data)
    assert result[1] == 2


def test_side_bending_penalty_right():
    """Trigger side bend penalty via right side."""
    input_data = np.array([0.0, 0.0, 1.0, 0.0, 0.0, 0.0], dtype=np.float64)
    result = wrist_reba_score(input_data)
    assert result[2] == 1


def test_side_bending_penalty_left():
    """Trigger side bend penalty via left side."""
    input_data = np.array([0.0, 0.0, 0.0, 1.0, 0.0, 0.0], dtype=np.float64)
    result = wrist_reba_score(input_data)
    assert result[2] == 1


def test_torsion_penalty_right():
    """Trigger torsion penalty via right twist."""
    input_data = np.array([0.0, 0.0, 0.0, 0.0, 1.0, 0.0], dtype=np.float64)
    result = wrist_reba_score(input_data)
    assert result[3] == 1


def test_torsion_penalty_left():
    """Trigger torsion penalty via left twist."""
    input_data = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 1.0], dtype=np.float64)
    result = wrist_reba_score(input_data)
    assert result[3] == 1


def test_total_score_cap():
    """Verify the min(total, 3) logic on line 111."""
    # Flex(2) + Side(1) + Twist(1) = 4. Cap should result in 3.
    input_data = np.array([15.0, 0.0, 1.0, 0.0, 1.0, 0.0], dtype=np.float64)
    result = wrist_reba_score(input_data)
    assert result[0] == 3


@pytest.mark.parametrize(
    "r_f, l_f, expected",
    [
        (14.9, 0.0, 1),  # Right > Left, Right in range
        (15.0, 0.0, 2),  # Right > Left, Right boundary
        (0.0, 14.9, 1),  # Left >= Right, Left in range
        (0.0, 15.0, 2),  # Left >= Right, Left boundary
        (-14.9, -15.0, 1),  # Right > Left, Right in range
        (-15.1, -20.0, 2),  # Right > Left, Right out of range
    ],
)
def test_exhaustive_flexion_logic(r_f, l_f, expected):
    """Hits all branch combinations for flexion logic in lines 85-97."""
    input_data = np.array([r_f, l_f, 0.0, 0.0, 0.0, 0.0], dtype=np.float64)
    result = wrist_reba_score(input_data)
    assert result[1] == expected
