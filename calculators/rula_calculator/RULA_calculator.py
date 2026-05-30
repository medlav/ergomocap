# ---
# project: ErgoMoCap
# file: RULA_calculator.py
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
ErgoMoCap: RULA Assessment Calculator
-------------------------------------
Implementation of the Rapid Upper Limb Assessment (RULA) ergonomic method.

This module provides the computational logic to determine postural risk scores
based on the RULA standard. It uses a series of lookup tables (Table A, B, and C)
to aggregate individual joint scores into a final ergonomic risk value.

The calculator processes 3D skeletal data (angles) to evaluate:
- **Group A**: Upper arms, lower arms, wrists, and wrist twist.
- **Group B**: Neck, trunk, and legs.

Final scores indicate the level of intervention required, ranging from 1 (negligible
risk) to 7+ (immediate change required).
"""

# from numba import njit TODO test numba and activate
from typing import Any

import numpy as np
from numpy.typing import NDArray

from calculators.adapters.freemocap_adapter import DegsIndexes as DI

# --- SCORING MATRICES ---
from calculators.rula_calculator.rula_body_parts import (
    lower_arm_rula_score,
    neck_rula_score,
    trunk_rula_score,
    upper_arm_rula_score,
    wrist_rula_score,
    wrist_twist_rula_score,
)
from calculators.rula_calculator.rula_score_tables import (
    _TABLE_A_DATA,
    _TABLE_B_DATA,
    _TABLE_C_DATA,
)

# --- MASTER PIPELINE ---


def calculate_frame_rula_from_degs(
    degs: NDArray[np.float64],
    muscle_score: int = 0,
    force_score: int = 0,
    is_arm_supported: bool = False,
    are_legs_unsupported: bool = False,
) -> tuple[dict[str, int], dict[str, Any]]:
    """
    Standardized RULA Entry Point using DegsIndexes Enum.

    Calculates the complete RULA assessment for a single frame of data by
    performing lookups in Table A (Upper Limb), Table B (Neck/Trunk/Legs),
    and Table C (Grand Score).

    Args:
        degs (numpy.ndarray): A 1D `numpy.ndarray` containing 22 joint angle values.
        muscle_score (int): Static posture or repetition penalty (typically 0 or 1).
        force_score (int): Load or force penalty (0, 1, 2, or 3).
        is_arm_supported (bool): Whether the upper arm is supported.
        are_legs_unsupported (bool): Whether the legs and feet are poorly supported.

    Raises:
        IndexError: If the `degs` array does not contain exactly 22 values.

    Returns:
        tuple[dict[str, int], dict[str, Any]]: A tuple containing:
            - `final_scores`: A `dict` with specific RULA keys (Upper_Arm_Score_RULA, etc.).
            - `metadata`: An empty `dict` for future compatibility.
    """

    if len(degs) != 22:
        raise IndexError(f"Expected 22 degree values, got {len(degs)}")

    # --- Group A: Arms & Wrist ---
    # Slicing from DI for clarity, but passing specific indices to RULA sub-functions
    upper_arm_score = upper_arm_rula_score(
        degs[DI.RIGHT_SHOULDER_EXTENSION_FLEXION],
        degs[DI.RIGHT_SHOULDER_ABDUCTION_ADDUCTION],
        degs[DI.RIGHT_SHOULDER_RISE],
        is_arm_supported,
    )

    lower_arm_score = lower_arm_rula_score(degs[DI.RIGHT_ELBOW_EXTENSION_FLEXION])

    wrist_score = wrist_rula_score(
        degs[DI.RIGHT_HAND_EXTENSION_FLEXION], degs[DI.RIGHT_HAND_LATERAL_SIDE]
    )

    # Wrist Twist: Penalty if rotation exceeds 40 degrees
    wrist_twist_score = wrist_twist_rula_score(
        degs[DI.RIGHT_HAND_TWIST],
    )  # TODO here only uses RIGHT Side and even before, address this

    # Score A Table Lookup
    score_a_raw = _TABLE_A_DATA[
        int(upper_arm_score) - 1,
        int(lower_arm_score) - 1,
        int(wrist_score) - 1,
        int(wrist_twist_score) - 1,
    ]
    grand_score_a = int(max(1, min(score_a_raw + muscle_score + force_score, 8)))

    # --- Group B: Neck, Trunk, Legs ---
    neck_score = neck_rula_score(
        degs[DI.NECK_EXTENSION_FLEXION],
        degs[DI.NECK_LATERAL_FLEXION],
        degs[DI.NECK_ROTATION],
    )

    trunk_score = trunk_rula_score(
        degs[DI.SPINE_EXTENSION_FLEXION],
        degs[DI.SPINE_LATERAL_FLEXION],
        degs[DI.SPINE_ROTATION_TORSION],
    )

    legs_score = 2 if are_legs_unsupported else 1

    # Score B Table Lookup
    score_b_raw = _TABLE_B_DATA[
        int(neck_score) - 1, int(trunk_score) - 1, int(legs_score) - 1
    ]
    grand_score_b = int(max(1, min(score_b_raw + muscle_score + force_score, 7)))

    # Final Synthesis (Table C)
    final_rula = _TABLE_C_DATA[grand_score_a - 1, grand_score_b - 1]

    # DO NOT CHANGE THESE NAMES
    final_scores = {
        "Upper_Arm_Score_RULA": upper_arm_score,
        "Lower_Arm_Score_RULA": lower_arm_score,
        "Trunk_Score_RULA": trunk_score,
        "Neck_Score_RULA": neck_score,
        "Wrist_Score_RULA": wrist_score,
        "Score_A_RULA": grand_score_a,
        "Score_B_RULA": grand_score_b,
        "Final_Score_RULA": int(final_rula),
    }

    return final_scores, {}
