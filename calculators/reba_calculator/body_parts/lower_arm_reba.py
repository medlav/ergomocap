# ---
# project: ErgoMoCap
# file: lower_arm_reba.py
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
ErgoMoCap: REBA Lower Arm Calculator
------------------------------------
Lower arm postural assessment for the Rapid Entire Body Assessment (REBA).

This module calculates the scoring for the lower arm component of the REBA method.
It evaluates elbow flexion and extension angles to determine the postural risk score
for the upper limbs, specifically focusing on identifying the most strained arm
to ensure a conservative (worst-case) ergonomic assessment.

The calculator utilizes `numpy.ndarray` for input/output to maintain compatibility
with the project's high-performance data processing pipelines and is designed
for future `numba` optimization.
"""

import numpy as np
from numpy.typing import NDArray
from numba import int16


# @njit(int16[:](float64[:])) TODO test numba and activate
def lower_arm_reba_score(lower_arm_degrees: NDArray[np.float64]) -> NDArray[np.int16]:
    """
    Calculates the REBA (Rapid Entire Body Assessment) score for the lower arms.

    The function evaluates both arms and selects the score based on the arm with
    the higher degree of flexion, following standard REBA threshold intervals.

    Args:
        lower_arm_degrees (NDArray[np.float64]): A 1D NumPy array containing
            [RIGHT_ELBOW_EXTENSION_FLEXION, LEFT_ELBOW_EXTENSION_FLEXION].
            Expected unit: Degrees.

    Returns:
        NDArray[np.int16]: A 1D NumPy array containing the final
            REBA lower arm score [score]. Values are typically 1 or 2.
    """

    # freemocap_adapter.py mapping TODO remove or implement this chekc if works with numba
    # 5. Lower Arm [14:16] -> [right_elbow, left_elbow]
    # degs[14] = row["right_elbow_extension_flexion"]
    # degs[15] = row["left_elbow_extension_flexion"]

    right_degree = lower_arm_degrees[0]
    left_degree = lower_arm_degrees[1]
    lower_arm_reba_score = 1  # Initialized as int

    if (
        right_degree >= left_degree
    ):  # TODO important test for the degrees as this are calculated from a saggital perspective and the sign can be inconsistent based on the direction of movement or sensor placement.
        # We want to ensure we are correctly identifying the arm with the greater degree of flexion for accurate scoring.
        if 0.0 <= right_degree < 60.0:
            lower_arm_reba_score = 2
        if 60.0 <= right_degree < 100.0:
            lower_arm_reba_score = 1
        if 100.0 <= right_degree:
            lower_arm_reba_score = 2
    else:
        if 0.0 <= left_degree < 60.0:
            lower_arm_reba_score = 2
        if 60.0 <= left_degree < 100.0:
            lower_arm_reba_score = 1
        if 100.0 <= left_degree:
            lower_arm_reba_score = 2

    return np.array([int16(lower_arm_reba_score)], dtype=np.int16)
