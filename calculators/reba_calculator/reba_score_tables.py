# ---
# project: ErgoMoCap
# file: reba_score_tables.py
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
ErgoMoCap - Biomechanical Scoring Tables
-------------------------------------------
This module contains the matrix representations of the REBA (Rapid Entire Body
Assessment) lookup tables. These tables are used to consolidate partial joint
scores into composite risk indices (Score A and Score B), which finally
determine the Grand Score (Score C).

The implementation uses NumPy arrays for O(1) lookups. Because the REBA
standard uses 1-based indexing for scores, all retrieval functions in this
project adjust these values to 0-based indexing for internal array access.
"""

import numpy as np

# Table A: Trunk (1-5), Neck (1-3), Legs (1-4)
# Note: REBA scores are 1-indexed, so we add a padding row/col at index 0
# or subtract 1 from the input scores. We'll subtract 1 for efficiency.

_TABLE_A_DATA = np.array(
    [
        # Trunk score 1
        [[1, 2, 3, 4], [2, 3, 4, 5], [2, 4, 5, 6]],
        # Trunk score 2
        [[2, 3, 4, 5], [3, 4, 5, 6], [4, 5, 6, 7]],
        # Trunk score 3
        [[2, 4, 5, 6], [4, 5, 6, 7], [5, 6, 7, 8]],
        # Trunk score 4
        [[3, 5, 6, 7], [5, 6, 7, 8], [6, 7, 8, 9]],
        # Trunk score 5
        [[4, 6, 7, 8], [7, 8, 9, 9], [7, 8, 9, 9]],
    ],
    dtype=np.int16,
)

# Table B: Upper Arm (1-6), Lower Arm (1-2), Wrist (1-3)
_TABLE_B_DATA = np.array(
    [
        # Upper Arm 1
        [[1, 2, 2], [1, 2, 3]],
        # Upper Arm 2
        [[1, 2, 3], [2, 3, 4]],
        # Upper Arm 3
        [[3, 4, 5], [4, 5, 5]],
        # Upper Arm 4
        [[4, 5, 5], [5, 6, 7]],
        # Upper Arm 5
        [[6, 7, 8], [7, 8, 8]],
        # Upper Arm 6
        [[7, 8, 8], [8, 9, 9]],
    ],
    dtype=np.int16,
)

# Table C: Score A (1-12) x Score B (1-12)
_TABLE_C_DATA = np.array(
    [
        [1, 1, 1, 2, 3, 3, 4, 5, 6, 7, 7, 7],
        [1, 2, 2, 3, 4, 4, 5, 6, 6, 7, 7, 8],
        [2, 3, 3, 3, 4, 5, 6, 7, 7, 8, 8, 8],
        [3, 4, 4, 4, 5, 6, 7, 8, 8, 9, 9, 9],
        [4, 4, 4, 5, 6, 7, 8, 8, 9, 9, 9, 9],
        [6, 6, 6, 7, 8, 8, 9, 9, 10, 10, 10, 10],
        [7, 7, 7, 8, 9, 9, 9, 10, 10, 11, 11, 11],
        [8, 8, 8, 9, 10, 10, 10, 10, 10, 11, 11, 11],
        [9, 9, 9, 10, 10, 10, 11, 11, 11, 12, 12, 12],
        [10, 10, 10, 11, 11, 11, 11, 12, 12, 12, 12, 12],
        [11, 11, 11, 11, 12, 12, 12, 12, 12, 12, 12, 12],
        [12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12],
    ],
    dtype=np.int16,
)
