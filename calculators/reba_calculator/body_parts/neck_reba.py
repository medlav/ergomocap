# ---
# project: ErgoMoCap
# file: neck_reba.py
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
ErgoMoCap: REBA Neck Calculator
-------------------------------
Cervical spine postural assessment for the Rapid Entire Body Assessment (REBA).

This module implements the scoring logic for the neck region. It processes three-dimensional
angular data including flexion, extension, lateral side-bending, and axial rotation.
The final score is a composite value that penalizes non-neutral postures and
excessive torsion or lateral deviation.

Key calculations:
- **Flexion/Extension**: Base score determined by the sagittal angle.
- **Lateral Bending**: Penalty score for side-leaning exceeding threshold.
- **Torsion**: Penalty score for axial rotation exceeding threshold.
"""

import numpy as np
from numpy.typing import NDArray
from numba import int16


# @njit(int16[:](float64[:])) TODO test numba and activate
def neck_reba_score(neck_degrees: NDArray[np.float64]) -> NDArray[np.int16]:
    """
    Calculates the REBA (Rapid Entire Body Assessment) score for the neck.

    Evaluates flexion/extension, side bending, and twisting to provide a
    composite score and individual component scores.

    Args:
        neck_degrees (NDArray[np.float64]): A 1D NumPy array containing
            [NECK_EXTENSION_FLEXION, NECK_LATERAL_FLEXION, NECK_ROTATION].
            Note: Negative flexion values are treated as neck extension.

    Returns:
        NDArray[np.int16]: A 1D NumPy array containing:
            [total_neck_score, flex_score, side_score, torsion_score].
    """

    # freemocap_adapter.py mapping
    # 1. Legs [0:2] -> [right_knee, left_knee]
    # degs[0] = row["right_knee_extension_flexion"]
    # degs[1] = row["left_knee_extension_flexion"]

    neck_flex_degree = neck_degrees[0]
    neck_side_bending_degree = neck_degrees[1]
    neck_twist_degree = neck_degrees[2]

    neck_reba_score = 1  # Updated to int
    neck_flex_score = 0
    neck_side_score = 0
    neck_torsion_score = 0

    # Flexion / Extension Logic (determines base score)
    if neck_flex_degree >= 0.0:
        if 0.0 <= neck_flex_degree < 20.0:
            neck_flex_score = 1
        elif 20.0 <= neck_flex_degree:
            neck_flex_score = 2
        else:
            neck_flex_score = 1
    else:  # Extension Logic (negative values treated as extension)
        neck_flex_score = 2

    # Side Bending Logic
    if abs(neck_side_bending_degree) >= 10.0:
        neck_side_score = 1

    # Twisting Logic
    if abs(neck_twist_degree) >= 10.0:
        neck_torsion_score = 1

    total: int = neck_flex_score + neck_side_score + neck_torsion_score
    neck_reba_score = min(total, 3)  # Cap the neck score at 3 (as per REBA guidelines)

    return np.array(
        [
            int16(neck_reba_score),
            int16(neck_flex_score),
            int16(neck_side_score),
            int16(neck_torsion_score),
        ],
        dtype=np.int16,
    )
