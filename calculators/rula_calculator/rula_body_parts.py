# ---
# project: ErgoMoCap
# file: rula_body_parts.py
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


def upper_arm_rula_score(
    flexion: float, abduction: float, shoulder_rise: float, is_supported: bool
) -> int:
    """
    Calculates the RULA score for the upper arm based on flexion and posture.

    Args:
        flexion (float): The flexion/extension angle in degrees.
        abduction (float): The abduction/adduction angle in degrees.
        shoulder_rise (float): The vertical shoulder elevation in degrees.
        is_supported (bool): Whether the arm is supported or the person is leaning.

    Returns:
        int (int): A score between 1 and 6.
    """
    # Base Score
    if flexion > 90.0:
        score = 4
    elif 45.0 < flexion <= 90.0:
        score = 3
    elif 20.0 < flexion <= 45.0 or flexion < -20.0:
        score = 2
    else:
        score = 1
    # Adjustments
    if shoulder_rise > 10.0:
        score += 1
    if abduction > 20.0:
        score += 1
    if is_supported:
        score -= 1
    return int(max(1, min(score, 6)))


def lower_arm_rula_score(flexion: float) -> int:
    """
    Calculates the RULA score for the lower arm based on flexion.

    Args:
        flexion (float): The elbow flexion/extension angle in degrees.

    Returns:
        int (int): A score of 1 (60-100°) or 2 (outside range).
    """
    # Logic for 'working across midline' is usually a manual observation (+1).
    if 60.0 <= flexion <= 100.0:
        return 1
    return 2


def wrist_rula_score(flexion_extension: float, side_deviation: float) -> int:
    """
    Calculates the RULA score for the wrist based on flexion and deviation.

    Args:
        flexion_extension (float): The wrist flexion/extension angle in degrees.
        side_deviation (float): The wrist radial/ulnar deviation angle in degrees.

    Returns:
        int (int): A score between 1 and 4.
    """

    if flexion_extension == 0:
        score = 1
    elif -15.0 <= flexion_extension <= 15.0:
        score = 2
    else:
        score = 3
    if abs(side_deviation) > 10.0:
        score += 1
    return int(max(1, min(score, 4)))


def wrist_twist_rula_score(twist_degree: float) -> int:
    """
    Calculates the RULA score for the wrist based on flexion and deviation.

    Args:
        twist_degree (float): The wrist twist angle in degrees.

    Returns:
        int (int): A score of either 1 or 2.
    """
    return 2 if abs(twist_degree) > 40.0 else 1


def neck_rula_score(flexion: float, side_bend: float, twist: float) -> int:
    """
    Calculates the RULA score for the neck.

    Args:
        flexion (float): The neck flexion/extension angle in degrees.
        side_bend (float): The neck lateral flexion angle in degrees.
        twist (float): The neck rotation angle in degrees.

    Returns:
        int (int): A score between 1 and 6.
    """

    if flexion < 0:
        score = 4
    elif flexion > 20.0:
        score = 3
    elif 10.0 < flexion <= 20.0:
        score = 2
    else:
        score = 1
    if abs(twist) > 10.0:
        score += 1
    if abs(side_bend) > 10.0:
        score += 1
    return int(max(1, min(score, 6)))


def trunk_rula_score(flexion: float, side_bending: float, torsion: float) -> int:
    """
    Calculates the RULA score for the trunk.

    Args:
        flexion (float): The trunk flexion/extension angle in degrees.
        side_bending (float): The trunk lateral flexion angle in degrees.
        torsion (float): The trunk rotation/torsion angle in degrees.

    Returns:
        int (int): A score between 1 and 6.
    """

    if flexion > 60.0:
        score = 4
    elif 20.0 < flexion <= 60.0:
        score = 3
    elif 0.0 < flexion <= 20.0:
        score = 2
    else:
        score = 1
    if abs(torsion) > 10.0:
        score += 1
    if abs(side_bending) > 10.0:
        score += 1
    return int(max(1, min(score, 6)))
