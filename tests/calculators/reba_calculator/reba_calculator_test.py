# ---
# project: ErgoMoCap
# file: reba_calculator_test.py
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
from unittest.mock import patch

from calculators.adapters.freemocap_adapter import DegsIndexes as DI

from calculators.reba_calculator.REBA_calculator import (
    calculate_frame_reba_from_degs,
    get_score_a,
    get_score_b,
    get_final_reba,
)


class TestGetScoreA:
    def test_get_score_a_min_values(self):
        assert get_score_a(1, 1, 1) == 1  # _TABLE_A_DATA[0,0,0] == 1

    def test_get_score_a_max_values(self):
        assert get_score_a(5, 3, 4) == 9  # _TABLE_A_DATA[4,2,3] == 9

    def test_get_score_a_clamped_values(self):
        assert get_score_a(0, 0, 0) == get_score_a(1, 1, 1)
        assert get_score_a(6, 4, 5) == get_score_a(5, 3, 4)


class TestGetScoreB:
    def test_get_score_b_min_values(self):
        assert get_score_b(1, 1, 1) == 1  # _TABLE_B_DATA[0,0,0] == 1

    def test_get_score_b_max_values(self):
        assert get_score_b(6, 2, 3) == 9  # _TABLE_B_DATA[5,1,2] == 9

    def test_get_score_b_clamped_values(self):
        assert get_score_b(0, 0, 0) == get_score_b(1, 1, 1)
        assert get_score_b(7, 3, 4) == get_score_b(6, 2, 3)


class TestGetFinalReba:
    def test_get_final_reba_basic(self):
        assert get_final_reba(1, 1) == 1  # _TABLE_C_DATA[0,0] == 1

    def test_get_final_reba_with_load(self):
        assert get_final_reba(1, 1, load=1) == 1  # _TABLE_C_DATA[1,0] == 1

    def test_get_final_reba_with_activity(self):
        assert get_final_reba(1, 1, activity=1) == 2  # _TABLE_C_DATA[0,0] == 1 + 1

    def test_get_final_reba_clamped(self):
        assert get_final_reba(15, 15) == get_final_reba(12, 12)  # Clamped to 12


class TestCalculateFrameRebaFromDegs:
    @patch("calculators.reba_calculator.REBA_calculator.leg_reba_score")
    @patch("calculators.reba_calculator.REBA_calculator.trunk_reba_score")
    @patch("calculators.reba_calculator.REBA_calculator.neck_reba_score")
    @patch("calculators.reba_calculator.REBA_calculator.upper_arm_reba_score")
    @patch("calculators.reba_calculator.REBA_calculator.lower_arm_reba_score")
    @patch("calculators.reba_calculator.REBA_calculator.wrist_reba_score")
    def test_calculate_frame_reba_from_degs(
        self, mock_wrist, mock_l_arm, mock_u_arm, mock_neck, mock_trunk, mock_leg
    ):
        # Mock returns: source code expects a tuple/iterable where index [0] is extracted
        mock_leg.return_value = (1,)
        mock_trunk.return_value = (2,)
        mock_neck.return_value = (1,)
        mock_u_arm.return_value = (3,)
        mock_l_arm.return_value = (1,)
        mock_wrist.return_value = (2,)

        # Create input array using the absolute real dimension limit from source code constraints
        degs = np.ones(22)
        scores, deg_map = calculate_frame_reba_from_degs(degs)

        # Expected output tracking actual dictionary structures returned by your module
        expected_scores = {
            "Legs_Score_REBA": 1,
            "Trunk_Score_REBA": 2,
            "Neck_Score_REBA": 1,
            "Upper_Arm_Score_REBA": 3,
            "Lower_Arm_Score_REBA": 1,
            "Wrist_Score_REBA": 2,
            "Final_Score_REBA": 3,
            "Score_A_REBA": 2,
            "Score_B_REBA": 4,
            "Score_C_REBA": 3,
        }

        assert scores == expected_scores
        assert deg_map == {}

        # Safely extract positional call arguments to bypass the mock framework array ambiguity bug
        called_leg_arg = mock_leg.call_args[0][0]
        called_trunk_arg = mock_trunk.call_args[0][0]
        called_neck_arg = mock_neck.call_args[0][0]
        called_u_arm_arg = mock_u_arm.call_args[0][0]
        called_l_arm_arg = mock_l_arm.call_args[0][0]
        called_wrist_arg = mock_wrist.call_args[0][0]

        # Verify array slicing alignments match source constraints exactly
        np.testing.assert_array_equal(
            called_leg_arg,
            degs[DI.RIGHT_KNEE_EXTENSION_FLEXION : DI.LEFT_KNEE_EXTENSION_FLEXION + 1],
        )
        np.testing.assert_array_equal(
            called_trunk_arg,
            degs[DI.SPINE_EXTENSION_FLEXION : DI.SPINE_ROTATION_TORSION + 1],
        )
        np.testing.assert_array_equal(
            called_neck_arg, degs[DI.NECK_EXTENSION_FLEXION : DI.NECK_ROTATION + 1]
        )
        np.testing.assert_array_equal(
            called_u_arm_arg,
            degs[DI.RIGHT_SHOULDER_EXTENSION_FLEXION : DI.LEFT_SHOULDER_RISE + 1],
        )
        np.testing.assert_array_equal(
            called_l_arm_arg,
            degs[
                DI.RIGHT_ELBOW_EXTENSION_FLEXION : DI.LEFT_ELBOW_EXTENSION_FLEXION + 1
            ],
        )
        np.testing.assert_array_equal(
            called_wrist_arg,
            degs[DI.RIGHT_HAND_EXTENSION_FLEXION : DI.LEFT_HAND_TWIST + 1],
        )

    def test_calculate_frame_reba_from_degs_invalid_length(self):
        # Explicit verification for the boundary condition on line 78
        with pytest.raises(IndexError, match="Expected exactly 22 degree values"):
            calculate_frame_reba_from_degs(np.ones(21))

        with pytest.raises(IndexError, match="Expected exactly 22 degree values"):
            calculate_frame_reba_from_degs(np.ones(23))
