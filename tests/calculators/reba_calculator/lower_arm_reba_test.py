# ---
# project: ErgoMoCap
# file: lower_arm_reba_test.py
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
from calculators.reba_calculator.body_parts.lower_arm_reba import lower_arm_reba_score


class TestLowerArmRebaScore:
    """Unit tests for the lower_arm_reba_score function (int16 version)."""

    def test_right_arm_less_than_60_higher_than_left(self):
        # Right arm < 60, left < 60, right > left -> score 2
        result = lower_arm_reba_score(np.array([30.0, 20.0], dtype=np.float64))
        np.testing.assert_array_equal(result, np.array([2], dtype=np.int16))

    def test_left_arm_less_than_60_higher_than_right(self):
        # Left arm < 60, right < 60, left > right -> score 2
        result = lower_arm_reba_score(np.array([20.0, 30.0], dtype=np.float64))
        np.testing.assert_array_equal(result, np.array([2], dtype=np.int16))

    def test_right_arm_60_to_100_higher_than_left(self):
        # Right arm 60-100, left < 60, right > left -> score 1
        result = lower_arm_reba_score(np.array([70.0, 20.0], dtype=np.float64))
        np.testing.assert_array_equal(result, np.array([1], dtype=np.int16))

    def test_right_arm_100_or_more_higher_than_left(self):
        # Right arm >=100, left < 60, right > left -> score 2
        result = lower_arm_reba_score(np.array([110.0, 20.0], dtype=np.float64))
        np.testing.assert_array_equal(result, np.array([2], dtype=np.int16))

    def test_left_arm_60_to_100_higher_than_right(self):
        # Left arm 60-100, right < 60, left > right -> score 1
        result = lower_arm_reba_score(np.array([20.0, 70.0], dtype=np.float64))
        np.testing.assert_array_equal(result, np.array([1], dtype=np.int16))

    def test_left_arm_100_or_more_higher_than_right(self):
        # Left arm >=100, right < 60, left > right -> score 2
        result = lower_arm_reba_score(np.array([20.0, 110.0], dtype=np.float64))
        np.testing.assert_array_equal(result, np.array([2], dtype=np.int16))

    def test_both_arms_equal_less_than_60(self):
        # Both < 60, equal -> score 2
        result = lower_arm_reba_score(np.array([30.0, 30.0], dtype=np.float64))
        np.testing.assert_array_equal(result, np.array([2], dtype=np.int16))

    def test_both_arms_equal_60_to_100(self):
        # Both 60-100, equal -> score 1
        result = lower_arm_reba_score(np.array([70.0, 70.0], dtype=np.float64))
        np.testing.assert_array_equal(result, np.array([1], dtype=np.int16))

    def test_both_arms_equal_100_or_more(self):
        # Both >=100, equal -> score 2
        result = lower_arm_reba_score(np.array([110.0, 110.0], dtype=np.float64))
        np.testing.assert_array_equal(result, np.array([2], dtype=np.int16))

    def test_edge_case_right_60(self):
        # Right = 60 -> score 1
        result = lower_arm_reba_score(np.array([60.0, 50.0], dtype=np.float64))
        np.testing.assert_array_equal(result, np.array([1], dtype=np.int16))

    def test_edge_case_right_100(self):
        # Right = 100 -> score 2
        result = lower_arm_reba_score(np.array([100.0, 50.0], dtype=np.float64))
        np.testing.assert_array_equal(result, np.array([2], dtype=np.int16))

    def test_edge_case_left_60(self):
        # Left = 60 -> score 1
        result = lower_arm_reba_score(np.array([50.0, 60.0], dtype=np.float64))
        np.testing.assert_array_equal(result, np.array([1], dtype=np.int16))

    def test_edge_case_left_100(self):
        # Left = 100 -> score 2
        result = lower_arm_reba_score(np.array([50.0, 100.0], dtype=np.float64))
        np.testing.assert_array_equal(result, np.array([2], dtype=np.int16))

    def test_right_arm_just_below_60(self):
        # Right = 59.9 -> score 2
        result = lower_arm_reba_score(np.array([59.9, 50.0], dtype=np.float64))
        np.testing.assert_array_equal(result, np.array([2], dtype=np.int16))

    def test_right_arm_just_below_100(self):
        # Right = 99.9 -> score 1
        result = lower_arm_reba_score(np.array([99.9, 50.0], dtype=np.float64))
        np.testing.assert_array_equal(result, np.array([1], dtype=np.int16))

    def test_left_arm_just_below_60(self):
        # Left = 59.9 -> score 2
        result = lower_arm_reba_score(np.array([50.0, 59.9], dtype=np.float64))
        np.testing.assert_array_equal(result, np.array([2], dtype=np.int16))

    def test_left_arm_just_below_100(self):
        # Left = 99.9 -> score 1
        result = lower_arm_reba_score(np.array([50.0, 99.9], dtype=np.float64))
        np.testing.assert_array_equal(result, np.array([1], dtype=np.int16))

    def test_return_type_and_shape(self):
        # Ensure return is NDArray[np.int16] with shape (1,)
        result = lower_arm_reba_score(np.array([30.0, 20.0], dtype=np.float64))
        assert isinstance(result, np.ndarray)
        assert result.dtype == np.int16
        assert result.shape == (1,)
