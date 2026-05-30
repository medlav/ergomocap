# ---
# project: ErgoMoCap
# file: rula_body_parts_test.py
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
from calculators.rula_calculator.rula_body_parts import (
    upper_arm_rula_score,
    lower_arm_rula_score,
    wrist_rula_score,
    wrist_twist_rula_score,
    neck_rula_score,
    trunk_rula_score,
)

# --- UPPER ARM TESTS ---


@pytest.mark.parametrize(
    "flex, abd, rise, supp, expected",
    [
        (95.0, 0.0, 0.0, False, 4),  # Flex > 90
        (60.0, 0.0, 0.0, False, 3),  # 45 < Flex <= 90
        (30.0, 0.0, 0.0, False, 2),  # 20 < Flex <= 45
        (-25.0, 0.0, 0.0, False, 2),  # Flex < -20
        (10.0, 0.0, 0.0, False, 1),  # Else (Neutral)
        (95.0, 25.0, 15.0, False, 6),  # 4 + 1 (Abd) + 1 (Rise) = 6
        (95.0, 0.0, 0.0, True, 3),  # 4 - 1 (Supported) = 3
        (0.0, 0.0, 0.0, True, 1),  # 1 - 1 = 0 -> capped at 1
        (100.0, 30.0, 30.0, False, 6),  # 4 + 1 + 1 = 6 -> capped at 6
    ],
)
def test_upper_arm_rula_logic(flex, abd, rise, supp, expected):
    assert upper_arm_rula_score(flex, abd, rise, supp) == expected


# --- LOWER ARM TESTS ---


@pytest.mark.parametrize(
    "flexion, expected",
    [
        (70.0, 1),  # Within 60-100
        (60.0, 1),  # Boundary low
        (100.0, 1),  # Boundary high
        (59.0, 2),  # Outside low
        (101.0, 2),  # Outside high
    ],
)
def test_lower_arm_rula_logic(flexion, expected):
    assert lower_arm_rula_score(flexion) == expected


# --- WRIST TESTS ---


@pytest.mark.parametrize(
    "flex_ex, side, expected",
    [
        (0.0, 0.0, 1),  # Exactly 0
        (10.0, 0.0, 2),  # -15 <= x <= 15
        (-15.0, 0.0, 2),  # Boundary
        (20.0, 0.0, 3),  # Outside range
        (0.0, 15.0, 2),  # 1 (Base) + 1 (Side > 10)
        (20.0, 15.0, 4),  # 3 (Base) + 1 (Side) = 4
        (30.0, 20.0, 4),  # 3 + 1 = 4 -> capped at 4
    ],
)
def test_wrist_rula_logic(flex_ex, side, expected):
    assert wrist_rula_score(flex_ex, side) == expected


def test_wrist_twist_rula_logic():
    assert wrist_twist_rula_score(30.0) == 1
    assert wrist_twist_rula_score(-45.0) == 2  # abs > 40
    assert wrist_twist_rula_score(40.0) == 1  # Boundary


# --- NECK TESTS ---


@pytest.mark.parametrize(
    "flex, side, twist, expected",
    [
        (-5.0, 0.0, 0.0, 4),  # Flex < 0 (Extension) -> Base 4
        (25.0, 0.0, 0.0, 3),  # Flex > 20 -> Base 3
        (15.0, 0.0, 0.0, 2),  # 10 < Flex <= 20 -> Base 2
        (5.0, 0.0, 0.0, 1),  # Else -> Base 1
        (25.0, 15.0, 15.0, 5),  # 3 + 1 (Side) + 1 (Twist) = 5
        (-5.0, 15.0, 15.0, 6),  # 4 (Extension) + 1 (Side) + 1 (Twist) = 6
    ],
)
def test_neck_rula_logic(flex, side, twist, expected):
    assert neck_rula_score(flex, side, twist) == expected


# --- TRUNK TESTS ---


@pytest.mark.parametrize(
    "flex, side, torsion, expected",
    [
        (65.0, 0.0, 0.0, 4),  # Flex > 60
        (30.0, 0.0, 0.0, 3),  # 20 < Flex <= 60
        (10.0, 0.0, 0.0, 2),  # 0 < Flex <= 20
        (0.0, 0.0, 0.0, 1),  # Else
        (65.0, 15.0, 15.0, 6),  # 4 + 1 + 1 = 6
        (10.0, 15.0, 15.0, 4),  # 2 + 1 + 1 = 4
    ],
)
def test_trunk_rula_logic(flex, side, torsion, expected):
    assert trunk_rula_score(flex, side, torsion) == expected
