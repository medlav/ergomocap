# ---
# project: ErgoMoCap
# file: rula_score_tables.py
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

import numpy as np

# --- SCORING MATRICES ---

# Table A: [Upper Arm (1-6), Lower Arm (1-3), Wrist Score (1-4) ,Wrist Twist(1-2)]
_TABLE_A_DATA = np.array(
    [
        # Upper Arm 1
        [
            [[1, 2], [2, 2], [2, 3], [3, 3]],  # Lower Arm 1
            [[2, 2], [2, 2], [3, 3], [3, 3]],  # Lower Arm 2
            [[2, 3], [3, 3], [3, 3], [4, 4]],  # Lower Arm 3
        ],
        # Upper Arm 2
        [
            [[2, 3], [3, 3], [3, 4], [4, 4]],  # Lower Arm 1
            [[3, 3], [3, 3], [3, 4], [4, 4]],  # Lower Arm 2
            [[3, 4], [4, 4], [4, 4], [5, 5]],  # Lower Arm 3
        ],
        # Upper Arm 3
        [
            [[3, 3], [4, 4], [4, 4], [5, 5]],  # Lower Arm 1
            [[3, 4], [4, 4], [4, 4], [5, 5]],  # Lower Arm 2
            [[4, 4], [4, 4], [4, 5], [5, 5]],  # Lower Arm 3
        ],
        # Upper Arm 4
        [
            [[4, 4], [4, 5], [4, 5], [5, 6]],  # Lower Arm 1
            [[4, 4], [4, 4], [4, 5], [5, 5]],  # Lower Arm 2
            [[4, 4], [4, 5], [5, 5], [6, 6]],  # Lower Arm 3
        ],
        # Upper Arm 5
        [
            [[5, 5], [5, 5], [5, 6], [6, 7]],  # Lower Arm 1
            [[5, 6], [6, 6], [6, 7], [7, 7]],  # Lower Arm 2
            [[6, 6], [6, 7], [7, 7], [7, 8]],  # Lower Arm 3
        ],
        # Upper Arm 6
        [
            [[7, 7], [7, 7], [7, 8], [8, 9]],  # Lower Arm 1
            [[8, 8], [8, 8], [8, 9], [9, 9]],  # Lower Arm 2
            [[9, 9], [9, 9], [9, 9], [9, 9]],  # Lower Arm 3
        ],
    ],
    dtype=np.int32,
)

# Table B: [Neck (1-6), Trunk (1-6), Legs (1-2)]
_TABLE_B_DATA = np.array(
    [
        # Neck 1
        [[1, 3], [2, 3], [3, 4], [5, 5], [6, 6], [7, 7]],
        # Neck 2
        [[2, 3], [2, 3], [4, 5], [5, 5], [6, 7], [7, 7]],
        # Neck 3
        [[3, 3], [3, 4], [4, 5], [5, 6], [6, 7], [7, 7]],
        # Neck 4
        [[5, 5], [5, 6], [6, 7], [7, 7], [7, 7], [8, 8]],
        # Neck 5
        [[7, 7], [7, 7], [7, 8], [8, 8], [8, 8], [8, 8]],
        # Neck 6
        [[8, 8], [8, 8], [8, 8], [8, 9], [9, 9], [9, 9]],
    ],
    dtype=np.int32,
)

# Table C: [Score A (1-8+), Score B (1-7+)]
_TABLE_C_DATA = np.array(
    [
        [1, 2, 3, 3, 4, 5, 5],
        [2, 2, 3, 4, 4, 5, 5],
        [3, 3, 3, 4, 4, 5, 6],
        [3, 3, 3, 4, 5, 6, 6],
        [4, 4, 4, 5, 6, 7, 7],
        [4, 4, 5, 6, 6, 7, 7],
        [5, 5, 6, 6, 7, 7, 7],
        [5, 5, 6, 7, 7, 7, 7],
    ],
    dtype=np.int32,
)
