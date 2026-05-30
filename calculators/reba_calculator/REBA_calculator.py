# ---
# project: ErgoMoCap
# file: REBA_calculator.py
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
ErgoMoCap: Biomechanical Scoring Engine (REBA)
---------------------------------------------
Master orchestrator for the Rapid Entire Body Assessment (REBA) pipeline.

This module implements the full REBA calculation logic, transforming 3D skeletal
angles into ergonomic risk scores. It organizes the assessment into:
- **Group A**: Trunk, Neck, and Legs.
- **Group B**: Upper Arm, Lower Arm, and Wrist.

The engine utilizes optimized lookup tables and support for Numba-accelerated
numerical operations to ensure high-performance processing of MoCap data.
"""

from typing import Any

import numpy as np

from numpy.typing import NDArray
from calculators.reba_calculator.body_parts.leg_reba import leg_reba_score
from calculators.reba_calculator.body_parts.lower_arm_reba import (
    lower_arm_reba_score,
)
from calculators.reba_calculator.body_parts.neck_reba import neck_reba_score
from calculators.reba_calculator.body_parts.trunk_reba import trunk_reba_score
from calculators.reba_calculator.body_parts.upper_arm_reba import (
    upper_arm_reba_score,
)
from calculators.reba_calculator.body_parts.wrist_reba import wrist_reba_score
from calculators.reba_calculator.reba_score_tables import (
    _TABLE_A_DATA,
    _TABLE_B_DATA,
    _TABLE_C_DATA,
)

from calculators.adapters.freemocap_adapter import DegsIndexes as DI


# @njit(int16[:](int16[:, :], int16[:, :]))
def calculate_frame_reba_from_degs(
    degs: NDArray[np.float64],
) -> tuple[dict[str, int], dict[str, Any]]:
    """
    Modular REBA Scoring Entry Point (Vectorized Input).

    This function processes pre-calculated biomechanical angles directly, bypassing
    the kinematic transformation stage. It maps a flat 1D array of degrees to
    specific body districts, calculates individual penalty scores, and synthesizes
    the final REBA Risk Index using Numba-accelerated lookup tables (A, B, and C).

    Args:
        degs (NDArray[np.float64]): A 1D array containing exactly 22 kinematic
            values in the following sequence:
            - [0:2]   Legs: [RIGHT_KNEE_EXTENSION_FLEXION, LEFT_KNEE_EXTENSION_FLEXION]
            - [2:5]   Trunk: [SPINE_EXTENSION_FLEXION, SPINE_LATERAL_FLEXION, SPINE_ROTATION_TORSION]
            - [5:8]   Neck: [NECK_EXTENSION_FLEXION, NECK_LATERAL_FLEXION, NECK_ROTATION]
            - [8:14]  Upper Arm: [RIGHT_SHOULDER_EXTENSION_FLEXION, LEFT_SHOULDER_EXTENSION_FLEXION,
                                  RIGHT_SHOULDER_ABDUCTION_ADDUCTION, LEFT_SHOULDER_ABDUCTION_ADDUCTION,
                                  RIGHT_SHOULDER_RISE, LEFT_SHOULDER_RISE]
            - [14:16] Lower Arm: [RIGHT_ELBOW_EXTENSION_FLEXION, LEFT_ELBOW_EXTENSION_FLEXION]
            - [16:22] Wrist: [RIGHT_HAND_EXTENSION_FLEXION, LEFT_HAND_EXTENSION_FLEXION,
                              RIGHT_HAND_LATERAL_SIDE, LEFT_HAND_LATERAL_SIDE,
                              RIGHT_HAND_TWIST, LEFT_HAND_TWIST]

    Returns:
        tuple[dict[str, int], dict[str, Any]]:
            - final_scores: dictionary containing integer penalty scores for
              each district plus the "Final_REBA_Score".
            - degrees_map: Empty dictionary (reserved for API consistency).

    Note:
        This method is preferred for processing high-frequency offline data
        where joint angles have already been solved (e.g., FreeMoCap post-processing).
    """
    if len(degs) != 22:
        raise IndexError(f"Expected exactly 22 degree values, got {len(degs)}")

    # 2. Calculate District Scores using Verbose Constant Slices
    # Slicing logic: [START : END + 1] to ensure the last index is included
    # IMPORTANT! Single body parts return an array so you must pop the first value [0] to get the score

    legs_score = leg_reba_score(
        degs[DI.RIGHT_KNEE_EXTENSION_FLEXION : DI.LEFT_KNEE_EXTENSION_FLEXION + 1]
    )[0]

    trunk_score = trunk_reba_score(
        degs[DI.SPINE_EXTENSION_FLEXION : DI.SPINE_ROTATION_TORSION + 1]
    )[0]

    neck_score = neck_reba_score(
        degs[DI.NECK_EXTENSION_FLEXION : DI.NECK_ROTATION + 1]
    )[0]

    upper_arm_score = upper_arm_reba_score(
        degs[DI.RIGHT_SHOULDER_EXTENSION_FLEXION : DI.LEFT_SHOULDER_RISE + 1]
    )[0]

    lower_arm_score = lower_arm_reba_score(
        degs[DI.RIGHT_ELBOW_EXTENSION_FLEXION : DI.LEFT_ELBOW_EXTENSION_FLEXION + 1]
    )[0]

    wrist_score = wrist_reba_score(
        degs[DI.RIGHT_HAND_EXTENSION_FLEXION : DI.LEFT_HAND_TWIST + 1]
    )[0]

    # Calculate Score A, B, and Final
    score_a = get_score_a(trunk_score, neck_score, legs_score)

    # TODO adjust for load score
    # If load < 11 lbs. : +0
    # If load 11 to 22 lbs. : +1
    # If load > 22 lbs.: +2
    # Adjust: If shock or rapid build up of force: add +1
    load_score = (
        0  # Placeholder for load score (to be integrated with actual load data)
    )
    adjusted_score_a = score_a + load_score

    score_b = get_score_b(
        upper_arm_score,
        lower_arm_score,
        wrist_score,
    )

    # TODO adjust for coupling/activity score
    # Coupling/Activity Score Adjustments (to be added to Score B):
    # Well fitting Handle and mid rang power grip, good: +0
    # Acceptable but not ideal hand hold or coupling
    # acceptable with another body part, fair: +1
    # Hand hold not acceptable but possible, poor: +2
    # No handles, awkward, unsafe with any body part,
    # Unacceptable: +3
    coupling_score = 0  # Placeholder for coupling/activity score (to be integrated with actual task data)
    adjusted_score_b = score_b + coupling_score

    final_reba_val = get_final_reba(adjusted_score_a, adjusted_score_b)

    final_scores = {  # TODO this dict is also hardcoded, should be a class if numba is unused
        "Legs_Score_REBA": int(legs_score),
        "Trunk_Score_REBA": int(trunk_score),
        "Neck_Score_REBA": int(neck_score),
        "Upper_Arm_Score_REBA": int(upper_arm_score),
        "Lower_Arm_Score_REBA": int(lower_arm_score),
        "Wrist_Score_REBA": int(wrist_score),
        "Final_Score_REBA": int(final_reba_val),
        "Score_A_REBA": int(adjusted_score_a),
        "Score_B_REBA": int(adjusted_score_b),
        "Score_C_REBA": int(final_reba_val),
    }

    return final_scores, {}


# @njit TODO test numba and activate
def get_score_a(trunk: int, neck: int, legs: int) -> int:
    """
    Performs Table A lookup for Group A (Trunk, Neck, Legs).

    Args:
        trunk (int): The calculated score for the trunk district.
        neck (int): The calculated score for the neck district.
        legs (int): The calculated score for the legs district.

    Returns:
        int (int): The composite Score A from the REBA matrix.
    """
    # Use floor/int conversion because MoCap data often comes in as floats
    tr = int(max(1, min(trunk, 5))) - 1
    ne = int(max(1, min(neck, 3))) - 1
    le = int(max(1, min(legs, 4))) - 1
    return _TABLE_A_DATA[tr, ne, le]


# @njit TODO test numba and activate
def get_score_b(upper_arm: int, lower_arm: int, wrist: int) -> int:
    """
    Performs Table B lookup for Group B (Arms, Wrists).

    Args:
        upper_arm (int): The calculated score for the upper arm.
        lower_arm (int): The calculated score for the lower arm.
        wrist (int): The calculated score for the wrist.

    Returns:
        int (int): The composite Score B from the REBA matrix.
    """
    ua = int(max(1, min(upper_arm, 6))) - 1
    la = int(max(1, min(lower_arm, 2))) - 1
    wr = int(max(1, min(wrist, 3))) - 1
    return _TABLE_B_DATA[ua, la, wr]


# @njit TODO test numba and activate
def get_final_reba(score_a: int, score_b: int, load: int = 0, activity: int = 0) -> int:
    """
    Calculates the final REBA score by combining Score A and Score B via Table C.

    Args:
        score_a (int): The total score from Group A (including load/force).
        score_b (int): The total score from Group B (including coupling).
        load (int): Penalty score for load/force (default: 0).
        activity (int): Penalty score for activity/postural instability (default: 0).

    Returns:
        int (int): The final REBA Risk Index.
    """
    # Add external load to Score A
    a_total = max(1, min(score_a + load, 12)) - 1
    # Add coupling/activity to Score B
    b_total = max(1, min(score_b, 12)) - 1

    score_c = _TABLE_C_DATA[a_total, b_total]

    # Final Result = Score C + Activity Score
    return score_c + activity
