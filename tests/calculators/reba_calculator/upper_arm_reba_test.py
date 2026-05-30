# ---
# project: ErgoMoCap
# file: upper_arm_reba_test.py
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

import numpy as np
from calculators.reba_calculator.body_parts.upper_arm_reba import upper_arm_reba_score


class TestUpperArmRebaScore:
    """Unit tests for the upper_arm_reba_score function (int16 version)."""

    def test_neutral_position(self):
        """Test neutral position: both arms at 0, no side, no rise."""
        input_data = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0], dtype=np.float64)
        result = upper_arm_reba_score(input_data)
        expected = np.array([1, 1, 0, 0], dtype=np.int16)
        np.testing.assert_array_equal(result, expected)
        assert result.dtype == np.int16

    def test_right_arm_flexion_20_to_45(self):
        """Test right arm flexion between 20 and 45 degrees."""
        input_data = np.array([30.0, 10.0, 0.0, 0.0, 0.0, 0.0], dtype=np.float64)
        result = upper_arm_reba_score(input_data)
        expected = np.array([2, 2, 0, 0], dtype=np.int16)
        np.testing.assert_array_equal(result, expected)

    def test_left_arm_flexion_45_to_90(self):
        """Test left arm flexion between 45 and 90 degrees, higher than right."""
        input_data = np.array([10.0, 60.0, 0.0, 0.0, 0.0, 0.0], dtype=np.float64)
        result = upper_arm_reba_score(input_data)
        expected = np.array([3, 3, 0, 0], dtype=np.int16)
        np.testing.assert_array_equal(result, expected)

    def test_right_arm_extension_beyond_20(self):
        """Test right arm extension beyond -20 degrees."""
        input_data = np.array([-30.0, 10.0, 0.0, 0.0, 0.0, 0.0], dtype=np.float64)
        result = upper_arm_reba_score(input_data)
        expected = np.array([2, 2, 0, 0], dtype=np.int16)
        np.testing.assert_array_equal(result, expected)

    def test_left_arm_flexion_over_90(self):
        """Test left arm flexion over 90 degrees."""
        input_data = np.array([10.0, 100.0, 0.0, 0.0, 0.0, 0.0], dtype=np.float64)
        result = upper_arm_reba_score(input_data)
        expected = np.array([4, 4, 0, 0], dtype=np.int16)
        np.testing.assert_array_equal(result, expected)

    def test_side_abduction_penalty_right(self):
        """Test side abduction penalty for right arm (>20 degrees)."""
        input_data = np.array([0.0, 0.0, 25.0, 0.0, 0.0, 0.0], dtype=np.float64)
        result = upper_arm_reba_score(input_data)
        expected = np.array([2, 1, 1, 0], dtype=np.int16)
        np.testing.assert_array_equal(result, expected)

    def test_side_abduction_penalty_left(self):
        """Test side abduction penalty for left arm (>20 degrees)."""
        input_data = np.array([0.0, 0.0, 0.0, -25.0, 0.0, 0.0], dtype=np.float64)
        result = upper_arm_reba_score(input_data)
        expected = np.array([2, 1, 1, 0], dtype=np.int16)
        np.testing.assert_array_equal(result, expected)

    def test_shoulder_rise_penalty_right(self):
        """Test shoulder rise penalty for right arm."""
        input_data = np.array([0.0, 0.0, 0.0, 0.0, 100.0, 0.0], dtype=np.float64)
        result = upper_arm_reba_score(input_data)
        expected = np.array([2, 1, 0, 1], dtype=np.int16)
        np.testing.assert_array_equal(result, expected)

    def test_shoulder_rise_penalty_left(self):
        """Test shoulder rise penalty for left arm."""
        input_data = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 95.0], dtype=np.float64)
        result = upper_arm_reba_score(input_data)
        expected = np.array([2, 1, 0, 1], dtype=np.int16)
        np.testing.assert_array_equal(result, expected)

    def test_combined_penalties(self):
        """Test combined side and shoulder rise penalties."""
        input_data = np.array([30.0, 10.0, 25.0, 0.0, 100.0, 0.0], dtype=np.float64)
        result = upper_arm_reba_score(input_data)
        expected = np.array([4, 2, 1, 1], dtype=np.int16)
        np.testing.assert_array_equal(result, expected)

    def test_edge_case_flexion_equal(self):
        """Test when right and left flexion are equal, chooses right."""
        input_data = np.array([45.0, 45.0, 0.0, 0.0, 0.0, 0.0], dtype=np.float64)
        result = upper_arm_reba_score(input_data)
        expected = np.array([3, 3, 0, 0], dtype=np.int16)
        np.testing.assert_array_equal(result, expected)

    def test_no_penalty_thresholds(self):
        """Test just below penalty thresholds."""
        input_data = np.array([0.0, 0.0, 2.0, -2.0, 90.0, 90.0], dtype=np.float64)
        result = upper_arm_reba_score(input_data)
        expected = np.array([1, 1, 0, 0], dtype=np.int16)
        np.testing.assert_array_equal(result, expected)

    def test_side_abduction_boundary_20(self):
        """Test side abduction exactly at 20 degrees (no penalty)."""
        input_data = np.array([0.0, 0.0, 20.0, 0.0, 0.0, 0.0], dtype=np.float64)
        result = upper_arm_reba_score(input_data)
        expected = np.array([1, 1, 0, 0], dtype=np.int16)
        np.testing.assert_array_equal(result, expected)

    def test_side_abduction_boundary_20_1(self):
        """Test side abduction at 20.1 degrees (penalty triggered)."""
        input_data = np.array([0.0, 0.0, 20.1, 0.0, 0.0, 0.0], dtype=np.float64)
        result = upper_arm_reba_score(input_data)
        expected = np.array([2, 1, 1, 0], dtype=np.int16)
        np.testing.assert_array_equal(result, expected)

    def test_shoulder_rise_boundary_90(self):
        """Test shoulder rise exactly at 90 degrees (no penalty)."""
        input_data = np.array([0.0, 0.0, 0.0, 0.0, 90.0, 0.0], dtype=np.float64)
        result = upper_arm_reba_score(input_data)
        expected = np.array([1, 1, 0, 0], dtype=np.int16)
        np.testing.assert_array_equal(result, expected)

    def test_left_arm_extension_penalty(self):
        """Covers line 104: Left arm is primary, extension < -20."""
        input_data = np.array([5.0, -25.0, 0.0, 0.0, 0.0, 0.0], dtype=np.float64)
        result = upper_arm_reba_score(input_data)
        expected = np.array([2, 2, 0, 0], dtype=np.int16)
        np.testing.assert_array_equal(result, expected)

    def test_left_arm_flexion_20_to_45(self):
        """Covers line 106: Left arm is primary, flexion [20, 45)."""
        input_data = np.array([0.0, 30.0, 0.0, 0.0, 0.0, 0.0], dtype=np.float64)
        result = upper_arm_reba_score(input_data)
        expected = np.array([2, 2, 0, 0], dtype=np.int16)
        np.testing.assert_array_equal(result, expected)

    def test_score_logic_clamping_and_total(self):
        """Covers line 131: Exercises the total calculation and int16 conversion."""
        # Max flexion (4) + side penalty (1) + shoulder rise (1) = 6
        input_data = np.array([0.0, 110.0, 25.0, 0.0, 0.0, 95.0], dtype=np.float64)
        result = upper_arm_reba_score(input_data)
        expected = np.array([6, 4, 1, 1], dtype=np.int16)
        np.testing.assert_array_equal(result, expected)

    def test_left_arm_flexion_neutral_range(self):
        """Covers line 101: Left arm is primary (|L| > |R|), in neutral range [-20, 20)."""
        # Left (10) magnitude is greater than Right (5)
        input_data = np.array([5.0, 10.0, 0.0, 0.0, 0.0, 0.0], dtype=np.float64)
        result = upper_arm_reba_score(input_data)
        expected = np.array([1, 1, 0, 0], dtype=np.int16)
        np.testing.assert_array_equal(result, expected)

    def test_left_arm_flexion_45_to_90_primary(self):
        """Covers line 108: Left arm is primary and in the 45-90 degree range."""
        # Left (60) magnitude is greater than Right (10)
        input_data = np.array([10.0, 60.0, 0.0, 0.0, 0.0, 0.0], dtype=np.float64)
        result = upper_arm_reba_score(input_data)
        expected = np.array([3, 3, 0, 0], dtype=np.int16)
        np.testing.assert_array_equal(result, expected)

    def test_final_score_clamping_max(self):
        """Covers line 131: Ensures total score caps at 6 and conversion to int16."""
        # flex(4) + side(1) + rise(1) + support(0) = 6
        input_data = np.array([0.0, 100.0, 25.0, 0.0, 0.0, 95.0], dtype=np.float64)
        result = upper_arm_reba_score(input_data)
        expected = np.array([6, 4, 1, 1], dtype=np.int16)
        np.testing.assert_array_equal(result, expected)
        assert result.dtype == np.int16

    def test_final_score_clamping_min(self):
        """Covers line 131: Ensures total score does not drop below 1."""
        # Even if penalties were negative, score must be at least 1
        input_data = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0], dtype=np.float64)
        result = upper_arm_reba_score(input_data)
        # flex_score is 1 for 0 degrees, side 0, rise 0 -> total 1
        expected = np.array([1, 1, 0, 0], dtype=np.int16)
        np.testing.assert_array_equal(result, expected)
