# ---
# project: ErgoMoCap
# file: upper_arm_reba.py
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
ErgoMoCap: REBA Upper Arm Calculator
------------------------------------
Shoulder and upper arm postural assessment for the Rapid Entire Body Assessment (REBA).

This module evaluates the ergonomic risk of the upper limbs by analyzing shoulder
flexion/extension, abduction/adduction, and shoulder girdle elevation (rise).
It employs a "worst-case" selection logic, prioritizing the arm with the greatest
deviation from the neutral position to ensure conservative risk estimation.

Calculations include:
- **Flexion/Extension**: Range-based scoring for the humerus.
- **Abduction**: Penalty for arms moving away from the midline of the body.
- **Shoulder Rise**: Penalty for elevated shoulder postures.
- **Static Support**: Adjustments for supported arm postures or leaning.
"""

import numpy as np
from numpy.typing import NDArray
from numba import int16


# @njit(int16[:](float64[:])) TODO test numba and activate
def upper_arm_reba_score(upper_arm_degrees: NDArray[np.float64]) -> NDArray[np.int16]:
    """
    Calculates the REBA (Rapid Entire Body Assessment) score for the upper arms.

    Evaluates flexion/extension for both arms (choosing the maximum),
    and checks for side abduction and shoulder elevation penalties.

    NOTE: upper_arm_degrees input MUST comply with degrees API from freemocap_adapter.py

    Args:
        upper_arm_degrees (NDArray[np.float64]): A 1D NumPy array containing
            [RIGHT_SHOULDER_EXTENSION_FLEXION, LEFT_SHOULDER_EXTENSION_FLEXION,
             RIGHT_SHOULDER_ABDUCTION_ADDUCTION, LEFT_SHOULDER_ABDUCTION_ADDUCTION,
             RIGHT_SHOULDER_RISE, LEFT_SHOULDER_RISE].

    Returns:
        NDArray[np.int16]: A 1D NumPy array containing:
            [total_score, flex_score, side_score, shoulder_rise_score].
    """
    # freemocap_adapter.py mapping TODO remove or implement!
    # 4. Upper Arm [8:14] -> [R_flex, L_flex, R_side, L_side, R_rise, L_rise]
    # degs[8] = row["right_shoulder_extension_flexion"]
    # degs[9] = row["left_shoulder_extension_flexion"]
    # degs[10] = row["right_shoulder_abduction_adduction"]
    # degs[11] = row["left_shoulder_abduction_adduction"]
    # R/L Shoulder rise usually mapped from abduction or separate landmarks
    # degs[12] = 0
    # degs[13] = 0

    right_flexion = upper_arm_degrees[0]
    left_flexion = upper_arm_degrees[1]
    right_side = upper_arm_degrees[2]
    left_side = upper_arm_degrees[3]
    right_shoulder_rise = upper_arm_degrees[
        4
    ]  # TODO EFFECTIVELY ALWAYS 0 !! MUST IMPLEMENT IN FMC ADAPTER TO GET REAL VALUES
    left_shoulder_rise = upper_arm_degrees[
        5
    ]  # TODO EFFECTIVELY ALWAYS 0 !! MUST IMPLEMENT IN FMC ADAPTER TO GET REAL VALUES

    upper_arm_reba_score = 1
    upper_arm_flex_score = 0
    upper_arm_side_score = 0
    upper_arm_shoulder_rise = 0
    support_leaning_score = 0

    # Flexion Logic (Choosing the arm in worse ergonomic position - furthest from neutral)
    # TODO this is almost all WRONG! should check the degrees, now it consider normal position at 0
    if abs(right_flexion) >= abs(left_flexion):
        if -20.0 <= right_flexion < 20.0:
            upper_arm_flex_score = 1
        if 20.0 <= right_flexion < 45.0:
            upper_arm_flex_score = 2
        if right_flexion < -20.0:
            upper_arm_flex_score = 2
        if 45.0 <= right_flexion < 90.0:
            upper_arm_flex_score = 3
        if 90.0 <= right_flexion:
            upper_arm_flex_score = 4
    else:
        if -20.0 <= left_flexion < 20.0:
            upper_arm_flex_score = 1
        if left_flexion < -20.0:
            upper_arm_flex_score = 2
        if 20.0 <= left_flexion < 45.0:
            upper_arm_flex_score = 2
        if 45.0 <= left_flexion < 90.0:
            upper_arm_flex_score = 3
        if 90.0 <= left_flexion:
            upper_arm_flex_score = 4

    # Side Bending / Abduction Penalty
    if (
        abs(right_side) > 20.0 or abs(left_side) > 20.0
    ):  # put at 20° to avoid penalizing small deviations
        upper_arm_side_score = 1

    # Shoulder Rise Penalty
    if right_shoulder_rise > 90.0 or left_shoulder_rise > 90.0:
        # TODO EFFECTIVELY ALWAYS 0 !! MUST IMPLEMENT IN FMC ADAPTER TO GET REAL VALUES
        upper_arm_shoulder_rise = 1

    arm_supported: bool = False  # TODO EFFECTIVELY ALWAYS FALSE !! MUST IMPLEMENT IN FMC ADAPTER TO GET REAL VALUES
    person_leaning: bool = False  # TODO EFFECTIVELY ALWAYS FALSE !! MUST IMPLEMENT IN FMC ADAPTER TO GET REAL VALUES

    # Arm Supported/ Leaning Penalty
    if arm_supported or person_leaning:
        # TODO EFFECTIVELY ALWAYS 0 !! MUST IMPLEMENT IN FMC ADAPTER TO GET REAL VALUES
        support_leaning_score = -1

    total: int = (
        upper_arm_flex_score
        + upper_arm_side_score
        + upper_arm_shoulder_rise
        + support_leaning_score
    )

    # Use max(1, ...) to ensure the negative penalty doesn't drop score below the REBA minimum
    upper_arm_reba_score = int16(max(1, min(total, 6)))

    return np.array(
        [
            upper_arm_reba_score,
            int16(upper_arm_flex_score),
            int16(upper_arm_side_score),
            int16(upper_arm_shoulder_rise),
        ],
        dtype=np.int16,
    )


# TODO REBA FIX #3 FIX ALL THIS FILE IS A MESS OF COURSE IS THE ONE CAUSING THE MOST PORBLEMS IN MY CALCULATOR!!
