# ---
# project: ErgoMoCap
# file: rula_calculator_test.py
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
from calculators.adapters.freemocap_adapter import DegsIndexes as DI
from calculators.rula_calculator.RULA_calculator import (
    upper_arm_rula_score,
    lower_arm_rula_score,
    wrist_rula_score,
    wrist_twist_rula_score,
    neck_rula_score,
    trunk_rula_score,
    calculate_frame_rula_from_degs,
)


class TestRulaIndividualScores:
    """Tests the logic for individual body part scoring."""

    def test_upper_arm_rula_logic(self):
        # Flexion 0-20 -> 1
        assert upper_arm_rula_score(10.0, 0.0, 0.0, False) == 1
        # Flexion > 90 -> 4
        assert upper_arm_rula_score(100.0, 0.0, 0.0, False) == 4
        # Extension > 20 -> 2
        assert upper_arm_rula_score(-30.0, 0.0, 0.0, False) == 2
        # Penalties: Abduction + Rise (1 + 1 + 1) -> 3
        assert upper_arm_rula_score(10.0, 25.0, 15.0, False) == 3
        # Supported adjustment (-1)
        assert upper_arm_rula_score(30.0, 0.0, 0.0, True) == 1  # 2 - 1

    def test_lower_arm_rula_logic(self):
        # Neutral 60-100 -> 1
        assert lower_arm_rula_score(80.0) == 1
        # Outside range -> 2
        assert lower_arm_rula_score(30.0) == 2
        assert lower_arm_rula_score(110.0) == 2

    def test_wrist_rula_logic(self):
        # Neutral 0 -> 1
        assert wrist_rula_score(0.0, 0.0) == 1
        # Flex/Ext 0-15 -> 2
        assert wrist_rula_score(10.0, 0.0) == 2
        # Deviation penalty
        assert wrist_rula_score(0.0, 15.0) == 2  # 1 + 1

    def test_wrist_twist_rula_logic(self):
        assert wrist_twist_rula_score(20.0) == 1
        assert wrist_twist_rula_score(45.0) == 2

    def test_neck_rula_logic(self):
        # Flexion > 20 -> 3
        assert neck_rula_score(25.0, 0.0, 0.0) == 3
        # Extension -> 4
        assert neck_rula_score(-5.0, 0.0, 0.0) == 4
        # Twist + Side bend penalties
        assert neck_rula_score(5.0, 15.0, 15.0) == 3  # 1 + 1 + 1

    def test_trunk_rula_logic(self):
        # Neutral 0 -> 1
        assert trunk_rula_score(0.0, 0.0, 0.0) == 1
        # Flexion 20-60 -> 3
        assert trunk_rula_score(30.0, 0.0, 0.0) == 3
        # Penalties
        assert trunk_rula_score(10.0, 15.0, 15.0) == 4  # 2 + 1 + 1


class TestRulaMasterPipeline:
    """Tests the full calculation pipeline and table lookups."""

    @pytest.fixture
    def neutral_degs(self):
        """Returns a 22-element zero array."""
        return np.zeros(22, dtype=np.float64)

    def test_rula_pipeline_neutral(self, neutral_degs):
        # All neutral should result in low scores
        scores, _ = calculate_frame_rula_from_degs(neutral_degs)

        assert scores["Upper_Arm_Score_RULA"] == 1
        assert scores["Lower_Arm_Score_RULA"] == 2  # Penalization for lower arm at 0°
        assert scores["Trunk_Score_RULA"] == 1
        assert scores["Neck_Score_RULA"] == 1
        assert scores["Wrist_Score_RULA"] == 1
        assert scores["Final_Score_RULA"] == 2

        # Lookup at _TABLE_A_DATA[0, 1, 0, 0]
        # Lookup at _TABLE_B_DATA[0, 0, 0]
        # Score A = 2, Score B = 1
        # Lookup at _TABLE_C_DATA[1, 0]
        # Final Score = 2

    def test_rula_pipeline_extreme_posture(self, neutral_degs):
        # Set extreme values for Group A
        degs = neutral_degs.copy()
        degs[DI.RIGHT_SHOULDER_EXTENSION_FLEXION] = 100.0  # Upper Arm -> 4
        degs[DI.RIGHT_ELBOW_EXTENSION_FLEXION] = 30.0  # Lower Arm -> 2
        degs[DI.RIGHT_HAND_EXTENSION_FLEXION] = 20.0  # Wrist -> 3
        degs[DI.RIGHT_HAND_TWIST] = 50.0  # Twist -> 2

        # Set extreme values for Group B
        degs[DI.NECK_EXTENSION_FLEXION] = -10.0  # Neck -> 4
        degs[DI.SPINE_EXTENSION_FLEXION] = 70.0  # Trunk -> 4

        scores, _ = calculate_frame_rula_from_degs(degs, are_legs_unsupported=True)

        # Assertions corrected to match the code's math
        assert scores["Upper_Arm_Score_RULA"] == 4
        assert scores["Lower_Arm_Score_RULA"] == 2  # Changed from 4 to 2 (0-60 range)
        assert scores["Neck_Score_RULA"] == 4  # Corrected to match input -10.0
        assert scores["Trunk_Score_RULA"] == 4  # Corrected to match input 70.0
        assert scores["Wrist_Score_RULA"] == 3
        assert scores["Score_A_RULA"] == 5  # Verified via Table A [3, 1, 2, 1]
        assert scores["Score_B_RULA"] == 7  # Verified via Table B [3, 3, 1]
        assert scores["Final_Score_RULA"] == 7  # Table C [4, 6]

    def test_muscle_and_force_penalties(self, neutral_degs):
        # Neutral body but high force/muscle
        scores, _ = calculate_frame_rula_from_degs(
            neutral_degs, muscle_score=1, force_score=1
        )

        # Raw A is 2. +1 muscle +1 force = 3
        assert scores["Score_A_RULA"] == 4
        # Raw B is 1. +1 muscle +1 force = 3
        assert scores["Score_B_RULA"] == 3
        # Table C [4,3] is 3
        assert scores["Final_Score_RULA"] == 3

    def test_invalid_input_length(self):
        with pytest.raises(IndexError):
            calculate_frame_rula_from_degs(np.array([1.0, 2.0]))

    def test_output_types(self, neutral_degs):
        scores, extra = calculate_frame_rula_from_degs(neutral_degs)
        assert isinstance(scores, dict)
        assert isinstance(extra, dict)
        assert isinstance(scores["Final_Score_RULA"], int)
