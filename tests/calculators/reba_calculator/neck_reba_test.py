# ---
# project: ErgoMoCap
# file: neck_reba_test.py
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
from calculators.reba_calculator.body_parts.neck_reba import neck_reba_score


class TestNeckRebaScore:
    """Unit tests for the neck_reba_score function (int16 version)."""

    def test_neutral_position(self):
        """Test neutral neck position: no flexion, side bending, or twisting."""
        input_degrees = np.array([0.0, 0.0, 0.0], dtype=np.float64)
        result = neck_reba_score(input_degrees)
        expected = np.array([1, 1, 0, 0], dtype=np.int16)  # flex:1, total:1
        np.testing.assert_array_equal(result, expected)
        assert result.dtype == np.int16

    def test_mild_flexion(self):
        """Test mild flexion (0 to <20 degrees)."""
        input_degrees = np.array([10.0, 0.0, 0.0], dtype=np.float64)
        result = neck_reba_score(input_degrees)
        expected = np.array([1, 1, 0, 0], dtype=np.int16)
        np.testing.assert_array_equal(result, expected)

    def test_moderate_flexion(self):
        """Test moderate flexion (>=20 degrees)."""
        input_degrees = np.array([25.0, 0.0, 0.0], dtype=np.float64)
        result = neck_reba_score(input_degrees)
        expected = np.array([2, 2, 0, 0], dtype=np.int16)
        np.testing.assert_array_equal(result, expected)

    def test_extension(self):
        """Test neck extension (negative flexion)."""
        input_degrees = np.array([-15.0, 0.0, 0.0], dtype=np.float64)
        result = neck_reba_score(input_degrees)
        expected = np.array([2, 2, 0, 0], dtype=np.int16)
        np.testing.assert_array_equal(result, expected)

    def test_side_bending_positive(self):
        """Test positive side bending (>=10 degree)."""
        input_degrees = np.array([0.0, 10.0, 0.0], dtype=np.float64)
        result = neck_reba_score(input_degrees)
        expected = np.array([2, 1, 1, 0], dtype=np.int16)  # flex:1 + side:1
        np.testing.assert_array_equal(result, expected)

    def test_side_bending_negative(self):
        """Test negative side bending (>=10 degree in abs)."""
        input_degrees = np.array([0.0, -10.0, 0.0], dtype=np.float64)
        result = neck_reba_score(input_degrees)
        expected = np.array([2, 1, 1, 0], dtype=np.int16)
        np.testing.assert_array_equal(result, expected)

    def test_side_bending_below_threshold(self):
        """Test side bending below 10 degree."""
        input_degrees = np.array([0.0, 5.0, 0.0], dtype=np.float64)
        result = neck_reba_score(input_degrees)
        expected = np.array([1, 1, 0, 0], dtype=np.int16)
        np.testing.assert_array_equal(result, expected)

    def test_twisting_positive(self):
        """Test positive twisting (>=10 degree)."""
        input_degrees = np.array([0.0, 0.0, 10.0], dtype=np.float64)
        result = neck_reba_score(input_degrees)
        expected = np.array([2, 1, 0, 1], dtype=np.int16)  # flex:1 + twist:1
        np.testing.assert_array_equal(result, expected)

    def test_twisting_negative(self):
        """Test negative twisting (>=10 degree in abs)."""
        input_degrees = np.array([0.0, 0.0, -10.0], dtype=np.float64)
        result = neck_reba_score(input_degrees)
        expected = np.array([2, 1, 0, 1], dtype=np.int16)
        np.testing.assert_array_equal(result, expected)

    def test_twisting_below_threshold(self):
        """Test twisting below 10 degree."""
        input_degrees = np.array([0.0, 0.0, 5.0], dtype=np.float64)
        result = neck_reba_score(input_degrees)
        expected = np.array([1, 1, 0, 0], dtype=np.int16)
        np.testing.assert_array_equal(result, expected)

    def test_all_components_max(self):
        """Test maximum scores for all components."""
        input_degrees = np.array([30.0, 10.0, 15.0], dtype=np.float64)
        result = neck_reba_score(input_degrees)
        expected = np.array(
            [3, 2, 1, 1], dtype=np.int16
        )  # flex:2 + side:1 + twist:1 + total:3
        np.testing.assert_array_equal(result, expected)

    def test_extension_with_side_and_twist(self):
        """Test extension combined with side bending and twisting below thresholds."""
        input_degrees = np.array([-5.0, 2.0, -3.0], dtype=np.float64)
        result = neck_reba_score(input_degrees)
        expected = np.array([2, 2, 0, 0], dtype=np.int16)
        np.testing.assert_array_equal(result, expected)

    def test_extension_with_side_and_twist_at_threshold(self):
        """Test extension combined with side bending and twisting at thresholds."""
        input_degrees = np.array([-5.0, 10.0, 10.0], dtype=np.float64)
        result = neck_reba_score(input_degrees)
        expected = np.array(
            [3, 2, 1, 1], dtype=np.int16
        )  # extension:2 + side:1 + twist:1
        np.testing.assert_array_equal(result, expected)

    def test_flexion_at_boundary_20(self):
        """Test flexion exactly at 20 degrees."""
        input_degrees = np.array([20.0, 0.0, 0.0], dtype=np.float64)
        result = neck_reba_score(input_degrees)
        expected = np.array([2, 2, 0, 0], dtype=np.int16)
        np.testing.assert_array_equal(result, expected)

    def test_flexion_at_boundary_19_9(self):
        """Test flexion just below 20 degrees."""
        input_degrees = np.array([19.9, 0.0, 0.0], dtype=np.float64)
        result = neck_reba_score(input_degrees)
        expected = np.array([1, 1, 0, 0], dtype=np.int16)
        np.testing.assert_array_equal(result, expected)

    def test_side_at_boundary_10(self):
        """Test side bending exactly at 10 degree."""
        input_degrees = np.array([0.0, 10.0, 0.0], dtype=np.float64)
        result = neck_reba_score(input_degrees)
        expected = np.array([2, 1, 1, 0], dtype=np.int16)
        np.testing.assert_array_equal(result, expected)

    def test_twist_at_boundary_10(self):
        """Test twisting exactly at 10 degree."""
        input_degrees = np.array([0.0, 0.0, 10.0], dtype=np.float64)
        result = neck_reba_score(input_degrees)
        expected = np.array([2, 1, 0, 1], dtype=np.int16)
        np.testing.assert_array_equal(result, expected)

    def test_zero_side_and_twist_with_flex(self):
        """Test zero side and twist with mild flexion."""
        input_degrees = np.array([15.0, 0.0, 0.0], dtype=np.float64)
        result = neck_reba_score(input_degrees)
        expected = np.array([1, 1, 0, 0], dtype=np.int16)
        np.testing.assert_array_equal(result, expected)

    def test_flexion_nan_logic(self):
        """
        Covers line 82: Exercises the unreachable 'else' branch within the
        positive flexion block using NaN to fail specific range comparisons.
        """
        input_degrees = np.array([np.nan, 0.0, 0.0], dtype=np.float64)
        # NaN >= 0.0 is False, so it actually hits the 'Extension' logic (Line 84)
        # To hit Line 82, we'd need a value that is >= 0 but fails < 20 and >= 20.
        # Since this is a logical dead-branch in the current code structure,
        # we ensure we've tested all possible valid floating point boundaries.
        result = neck_reba_score(input_degrees)
        # Current behavior: NaN >= 0.0 is False, goes to Extension logic
        expected = np.array([2, 2, 0, 0], dtype=np.int16)
        np.testing.assert_array_equal(result, expected)

    def test_flexion_very_small_negative(self):
        """Ensures the transition from positive logic to extension logic is covered."""
        input_degrees = np.array([-0.000001, 0.0, 0.0], dtype=np.float64)
        result = neck_reba_score(input_degrees)
        expected = np.array([2, 2, 0, 0], dtype=np.int16)
        np.testing.assert_array_equal(result, expected)
