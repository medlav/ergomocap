# ---
# project: ErgoMoCap
# file: wrist_reba.py
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
ErgoMoCap: REBA Wrist Calculator
--------------------------------
Distal upper limb postural assessment for the Rapid Entire Body Assessment (REBA).

This module calculates the scoring for the wrist joint, focusing on deviations
from the neutral plane. It evaluates flexion, extension, radial/ulnar deviation
(side bending), and forearm pronation/supination (torsion). This score is a
critical component of the REBA Group B assessment for fine-motor or manual
handling tasks.

Key features:
- **Flexion/Extension**: Binary scoring threshold at 15 degrees.
- **Deviation/Torsion**: Individual penalty increments for non-neutral alignments.
- **Input Compatibility**: Processes data typically derived from high-fidelity
  motion capture or specialized hand-tracking sensors.
"""

import numpy as np
from numpy.typing import NDArray
from numba import int16


# @njit(int16[:](float64[:])) TODO test numba and activate
def wrist_reba_score(wrist_degrees: NDArray[np.float64]) -> NDArray[np.int16]:
    """
    Calculates the REBA (Rapid Entire Body Assessment) score for the wrists.

    Evaluates flexion/extension by selecting the wrist with the maximum deviation,
    and applies penalties for side bending (radial/ulnar deviation) or torsion.

    NOTE: wrist_degrees input MUST comply with degrees API from freemocap_adapter.py

    Args:
        wrist_degrees (NDArray[np.float64]): A 1D NumPy array containing
            [RIGHT_HAND_EXTENSION_FLEXION, LEFT_HAND_EXTENSION_FLEXION,
             RIGHT_HAND_LATERAL_SIDE, LEFT_HAND_LATERAL_SIDE,
             RIGHT_HAND_TWIST, LEFT_HAND_TWIST].

    Returns:
        NDArray[np.int16]: A 1D NumPy array containing:
            [total_wrist_score, flex_score, side_bend_score, torsion_score].
    """
    # freemocap_adapter.py mapping TODO REMOVE OR IMPLEMENT!!
    # 6. Wrist [16:22] -> [R_flex, L_flex, R_side, L_side, R_twist, L_twist]
    # degs[16] = row["right_hand_extension_flexion"]
    # degs[17] = row["left_hand_extension_flexion"]
    # # Side/Twist for wrist often 0 unless using high-fidelity FMC gloves/configs
    # degs[18:22] = 0

    right_flex = wrist_degrees[0]
    left_flex = wrist_degrees[1]
    right_side = wrist_degrees[
        2
    ]  # TODO EFFECTIVELY ALWAYS 0 !! MUST IMPLEMENT IN FMC ADAPTER TO GET REAL VALUES
    left_side = wrist_degrees[
        3
    ]  # TODO EFFECTIVELY ALWAYS 0 !! MUST IMPLEMENT IN FMC ADAPTER TO GET REAL VALUES
    right_twist = wrist_degrees[
        4
    ]  # TODO EFFECTIVELY ALWAYS 0 !! MUST IMPLEMENT IN FMC ADAPTER TO GET REAL VALUES
    left_twist = wrist_degrees[
        5
    ]  # TODO EFFECTIVELY ALWAYS 0 !! MUST IMPLEMENT IN FMC ADAPTER TO GET REAL VALUES

    wrist_reba_score = 1
    wrist_flex_score = 0
    wrist_side_bend_score = 0
    wrist_torsion_score = 0

    # Flexion / Extension Logic (Choosing the wrist with higher deviation)
    if right_flex > left_flex:
        if -15.0 <= right_flex < 15.0:
            wrist_flex_score = 1
        if 15.0 <= right_flex or right_flex < -15.0:
            wrist_flex_score = 2
    else:
        if -15.0 <= left_flex < 15.0:
            wrist_flex_score = 1
        if 15.0 <= left_flex or left_flex < -15.0:
            wrist_flex_score = 2

    # Side Bending (Deviation) Penalty
    if (
        right_side != 0.0 or left_side != 0.0
    ):  # TODO EFFECTIVELY ALWAYS 0 !! MUST IMPLEMENT IN FMC ADAPTER TO GET REAL VALUES
        wrist_side_bend_score = 1

    # Torsion (Twist) Penalty
    if (
        right_twist != 0.0 or left_twist != 0.0
    ):  # TODO EFFECTIVELY ALWAYS 0 !! MUST IMPLEMENT IN FMC ADAPTER TO GET REAL VALUES
        wrist_torsion_score = 1

    total: int = wrist_flex_score + wrist_side_bend_score + wrist_torsion_score
    wrist_reba_score = min(total, 3)  # Capped at 3 for wrist (as per REBA guidelines)

    return np.array(
        [
            int16(wrist_reba_score),
            int16(wrist_flex_score),
            int16(wrist_side_bend_score),
            int16(wrist_torsion_score),
        ],
        dtype=np.int16,
    )


# TODO SHOULD NOTIFY THE USER THAT IS NOT GREATAT WRIST ANGLE CALCULATION.. BUT IT SHOULD
# BE SIMPLER TO IJMPL;EMNT USING THE HOLISITC MODELS:.
