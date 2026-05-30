# ---
# project: ErgoMoCap
# file: trunk_reba.py
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
ErgoMoCap: REBA Trunk Calculator
--------------------------------
Thoracic and lumbar postural assessment for the Rapid Entire Body Assessment (REBA).

This module implements the scoring logic for the trunk/spine region. It processes
multi-axial angular data including flexion, extension, lateral side-bending, and
axial torsion. The final score is a composite value that identifies postural strain
in the spine, which serves as a foundational component for the REBA Group A score.

Key calculations:
- **Flexion/Extension**: Categorical scoring based on forward or backward deviation.
- **Lateral Bending**: Binary penalty for any significant lateral deviation.
- **Torsion**: Binary penalty for spinal twisting.
"""

import numpy as np
from numpy.typing import NDArray
from numba import int16


# @njit(int16[:](float64[:])) TODO test numba and activate
def trunk_reba_score(trunk_degrees: NDArray[np.float64]) -> NDArray[np.int16]:
    """
    Calculates the REBA (Rapid Entire Body Assessment) score for the trunk.

    Evaluates trunk flexion, extension, side bending, and torsion to provide
    a total trunk score and its individual components.

    NOTE: trunk_degrees input MUST comply with degrees API from freemocap_adapter.py

    Args:
        trunk_degrees (NDArray[np.float64]): A 1D NumPy array containing
            [SPINE_EXTENSION_FLEXION, SPINE_LATERAL_FLEXION, SPINE_ROTATION_TORSION].
            Note: Positive flexion is forward bending; negative is extension.

    Returns:
        NDArray[np.int16]: A 1D NumPy array containing:
            [total_trunk_score, flex_score, side_score, torsion_score].
    """

    trunk_flex_degree = trunk_degrees[0]
    trunk_side_bending_degree = trunk_degrees[1]
    trunk_torsion_degree = trunk_degrees[
        2
    ]  # TODO EFFECTIVELY ALWAYS 0 !! MUST IMPLEMENT IN FMC ADAPTER TO GET REAL VALUES

    trunk_reba_score = 1
    trunk_flex_score = 0
    trunk_side_score = 0
    trunk_torsion_score = 0  # TODO EFFECTIVELY ALWAYS 0 !! MUST IMPLEMENT IN FMC ADAPTER TO GET REAL VALUES

    # Trunk Flexion / Extension Logic
    if trunk_flex_degree >= 0.0:
        # Forward Flexion
        if 0.0 <= trunk_flex_degree < 5.0:
            trunk_flex_score = 1
        elif 5.0 <= trunk_flex_degree < 20.0:
            trunk_flex_score = 2
        elif 20.0 <= trunk_flex_degree < 60.0:
            trunk_flex_score = 3
        elif 60.0 <= trunk_flex_degree:
            trunk_flex_score = 4
    else:
        # Trunk Extension
        trunk_flex_score = 2

    # Side Bending Logic
    if abs(trunk_side_bending_degree) >= 1.0:
        trunk_side_score = 1

    # Torsion (Twisting) Logic
    if abs(trunk_torsion_degree) >= 1.0:
        # TODO EFFECTIVELY ALWAYS 0 !! MUST IMPLEMENT IN FMC ADAPTER TO GET REAL VALUES
        trunk_torsion_score = 1

    total: int = trunk_flex_score + trunk_side_score + trunk_torsion_score
    trunk_reba_score = min(total, 5)  # Capped at 5 for trunk (as per REBA guidelines)

    return np.array(
        [
            int16(trunk_reba_score),
            int16(trunk_flex_score),
            int16(trunk_side_score),
            int16(trunk_torsion_score),
        ],
        dtype=np.int16,
    )


# TODO REBA FIX #2 Find a way to calculate the trunk_torsion_degree or ALERT USER ABOUT THIS..
