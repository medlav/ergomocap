# ---
# project: ErgoMoCap
# file: trunk_reba_test.py
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
from calculators.reba_calculator.body_parts.trunk_reba import trunk_reba_score


class TestTrunkRebaScore:
    """Unit tests for the trunk_reba_score function (int16 version)."""

    def test_flexion_0_to_5(self):
        degrees = np.array([0.0, 0.0, 0.0], dtype=np.float64)
        result = trunk_reba_score(degrees)
        expected = np.array([1, 1, 0, 0], dtype=np.int16)
        np.testing.assert_array_equal(result, expected)
        assert result.dtype == np.int16

    def test_flexion_5_to_20(self):
        degrees = np.array([10.0, 0.0, 0.0], dtype=np.float64)
        result = trunk_reba_score(degrees)
        expected = np.array([2, 2, 0, 0], dtype=np.int16)
        np.testing.assert_array_equal(result, expected)

    def test_flexion_20_to_60(self):
        degrees = np.array([30.0, 0.0, 0.0], dtype=np.float64)
        result = trunk_reba_score(degrees)
        expected = np.array([3, 3, 0, 0], dtype=np.int16)
        np.testing.assert_array_equal(result, expected)

    def test_flexion_above_60(self):
        degrees = np.array([70.0, 0.0, 0.0], dtype=np.float64)
        result = trunk_reba_score(degrees)
        expected = np.array([4, 4, 0, 0], dtype=np.int16)
        np.testing.assert_array_equal(result, expected)

    def test_extension_0_to_5(self):
        degrees = np.array([-2.0, 0.0, 0.0], dtype=np.float64)
        result = trunk_reba_score(degrees)
        expected = np.array([2, 2, 0, 0], dtype=np.int16)  # extension always scores 2
        np.testing.assert_array_equal(result, expected)

    def test_extension_5_to_20(self):
        degrees = np.array([-10.0, 0.0, 0.0], dtype=np.float64)
        result = trunk_reba_score(degrees)
        expected = np.array([2, 2, 0, 0], dtype=np.int16)
        np.testing.assert_array_equal(result, expected)

    def test_extension_above_20(self):
        degrees = np.array([-30.0, 0.0, 0.0], dtype=np.float64)
        result = trunk_reba_score(degrees)
        expected = np.array([2, 2, 0, 0], dtype=np.int16)
        np.testing.assert_array_equal(result, expected)

    def test_side_bending_positive(self):
        degrees = np.array([0.0, 5.0, 0.0], dtype=np.float64)
        result = trunk_reba_score(degrees)
        expected = np.array([2, 1, 1, 0], dtype=np.int16)
        np.testing.assert_array_equal(result, expected)

    def test_side_bending_negative(self):
        degrees = np.array([0.0, -5.0, 0.0], dtype=np.float64)
        result = trunk_reba_score(degrees)
        expected = np.array([2, 1, 1, 0], dtype=np.int16)
        np.testing.assert_array_equal(result, expected)

    def test_side_bending_zero(self):
        degrees = np.array([0.0, 0.5, 0.0], dtype=np.float64)
        result = trunk_reba_score(degrees)
        expected = np.array([1, 1, 0, 0], dtype=np.int16)
        np.testing.assert_array_equal(result, expected)

    def test_torsion_positive(self):
        degrees = np.array([0.0, 0.0, 5.0], dtype=np.float64)
        result = trunk_reba_score(degrees)
        expected = np.array([2, 1, 0, 1], dtype=np.int16)
        np.testing.assert_array_equal(result, expected)

    def test_torsion_negative(self):
        degrees = np.array([0.0, 0.0, -5.0], dtype=np.float64)
        result = trunk_reba_score(degrees)
        expected = np.array([2, 1, 0, 1], dtype=np.int16)
        np.testing.assert_array_equal(result, expected)

    def test_torsion_zero(self):
        degrees = np.array([0.0, 0.0, 0.5], dtype=np.float64)
        result = trunk_reba_score(degrees)
        expected = np.array([1, 1, 0, 0], dtype=np.int16)
        np.testing.assert_array_equal(result, expected)

    def test_combined_flexion_and_side(self):
        degrees = np.array([25.0, 10.0, 0.0], dtype=np.float64)
        result = trunk_reba_score(degrees)
        expected = np.array([4, 3, 1, 0], dtype=np.int16)
        np.testing.assert_array_equal(result, expected)

    def test_combined_extension_and_torsion(self):
        degrees = np.array([-15.0, 0.0, -10.0], dtype=np.float64)
        result = trunk_reba_score(degrees)
        expected = np.array([3, 2, 0, 1], dtype=np.int16)
        np.testing.assert_array_equal(result, expected)

    def test_all_components(self):
        degrees = np.array([45.0, 15.0, 20.0], dtype=np.float64)
        result = trunk_reba_score(degrees)
        expected = np.array([5, 3, 1, 1], dtype=np.int16)
        np.testing.assert_array_equal(result, expected)

    def test_edge_case_flexion_5(self):
        degrees = np.array([5.0, 0.0, 0.0], dtype=np.float64)
        result = trunk_reba_score(degrees)
        expected = np.array([2, 2, 0, 0], dtype=np.int16)
        np.testing.assert_array_equal(result, expected)

    def test_edge_case_flexion_20(self):
        degrees = np.array([20.0, 0.0, 0.0], dtype=np.float64)
        result = trunk_reba_score(degrees)
        expected = np.array([3, 3, 0, 0], dtype=np.int16)
        np.testing.assert_array_equal(result, expected)

    def test_edge_case_flexion_60(self):
        degrees = np.array([60.0, 0.0, 0.0], dtype=np.float64)
        result = trunk_reba_score(degrees)
        expected = np.array([4, 4, 0, 0], dtype=np.int16)
        np.testing.assert_array_equal(result, expected)

    def test_edge_case_extension_5(self):
        degrees = np.array([-5.0, 0.0, 0.0], dtype=np.float64)
        result = trunk_reba_score(degrees)
        expected = np.array([2, 2, 0, 0], dtype=np.int16)
        np.testing.assert_array_equal(result, expected)

    def test_edge_case_extension_20(self):
        degrees = np.array([-20.0, 0.0, 0.0], dtype=np.float64)
        result = trunk_reba_score(degrees)
        expected = np.array([2, 2, 0, 0], dtype=np.int16)
        np.testing.assert_array_equal(result, expected)

    def test_side_bending_exactly_1(self):
        degrees = np.array([0.0, 1.0, 0.0], dtype=np.float64)
        result = trunk_reba_score(degrees)
        expected = np.array([2, 1, 1, 0], dtype=np.int16)
        np.testing.assert_array_equal(result, expected)

    def test_torsion_exactly_1(self):
        degrees = np.array([0.0, 0.0, 1.0], dtype=np.float64)
        result = trunk_reba_score(degrees)
        expected = np.array([2, 1, 0, 1], dtype=np.int16)
        np.testing.assert_array_equal(result, expected)
