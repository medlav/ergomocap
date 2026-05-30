# ---
# project: ErgoMoCap
# file: leg_reba.py
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
ErgoMoCap: REBA Leg Calculator
------------------------------
Lower limb stability and postural assessment for REBA.

This module provides the logic to evaluate leg support and knee flexion as part of
the REBA scoring system. It assesses whether the weight is distributed evenly
between both legs and if the degree of knee flexion indicates an unstable or
high-strain posture.

The scores generated here contribute to the Group A postural score within the
overall REBA methodology.
"""

import numpy as np
from numpy.typing import NDArray
from numba import int16


# @njit(int16[:](float64[:])) TODO test numba and activate
def leg_reba_score(leg_degrees: NDArray[np.float64]) -> NDArray[np.int16]:
    """
    Calculates the REBA (Rapid Entire Body Assessment) score for legs.

    The function selects the leg with the highest absolute flexion/degree
    and applies a score based on specific threshold ranges (30° and 60°).

    Args:
        leg_degrees (NDArray[np.float64]): A 1D NumPy array containing
            [RIGHT_KNEE_EXTENSION_FLEXION, LEFT_KNEE_EXTENSION_FLEXION].
            Expected unit: Degrees as float64.

    Returns:
        NDArray[np.int16]: A 1D NumPy array containing the final
            REBA leg score [score]. Values are typically 1 or 2.
    """

    # freemocap_adapter.py mapping
    # 1. Legs [0:2] -> [right_knee, left_knee]
    # degs[0] = row["right_knee_extension_flexion"]
    # degs[1] = row["left_knee_extension_flexion"]

    right_leg_degree = leg_degrees[0]
    left_leg_degree = leg_degrees[1]
    leg_reba_score = 1
    leg_flexion_score = 0
    balance_score = 1  # Default to balanced TODO remove with REBA FIX #1

    unbalanced = False  # TODO implement a way to chek legs balance

    if right_leg_degree < 30.0 or left_leg_degree < 30.0:
        leg_flexion_score = 0
    elif 30.0 <= right_leg_degree < 60.0 or 30.0 <= left_leg_degree < 60.0:
        leg_flexion_score = 1
    elif 60.0 <= right_leg_degree or 60.0 <= right_leg_degree:
        leg_flexion_score = 2

    if unbalanced:
        balance_score = 2

    total: float = leg_flexion_score + balance_score
    leg_reba_score = min(total, 4)  # Capped at 4 for legs (as per REBA guidelines)

    return np.array([int16(leg_reba_score)], dtype=np.int16)


def check_leg_balance(args) -> bool:
    # TODO REBA FIX #1 implement logic here for leg score Balanced/Unbalanced!
    return False
