# ---
# project: ErgoMoCap
# file: freemocap_adapter.py
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
ErgoMoCap: FreeMoCap Adapter
----------------------------
Kinematic Mapping and Biomechanical Variable Extraction.

This module acts as the primary translation layer between raw FreeMoCap
output formats and the specific input requirements of various ergonomic
assessment engines (RULA, REBA, NIOSH, OCRA, EAWS, and Snook).

It provides:
- **Index Mapping**: A standardized enumeration (`DegsIndexes`) for internal
  kinematic arrays.
- **Coordinate Transformation**: Calculation of spatial variables like
  asymmetry angles relative to the mid-sagittal plane.
- **Task Specific Extraction**: Specialized mappers that isolate relevant
  joint angles and 3D landmarks for different ergonomic standards.

All functions are optimized for use within `pandas.DataFrame` application
pipelines and maintain strict adherence to biomechanical coordinate
conventions.
"""

from typing import Any
from enum import IntEnum

import numpy as np
from numpy.typing import NDArray
import pandas as pd


FMC_ANGLE_COLUMNS = [
    "left_elbow_extension_flexion",
    "left_shoulder_extension_flexion",
    "left_shoulder_abduction_adduction",
    "right_elbow_extension_flexion",
    "right_shoulder_extension_flexion",
    "right_shoulder_abduction_adduction",
    "left_knee_extension_flexion",
    "left_hip_extension_flexion",
    "left_hip_abduction_adduction",
    "right_knee_extension_flexion",
    "right_hip_extension_flexion",
    "right_hip_abduction_adduction",
    "neck_extension_flexion",
    "neck_lateral_flexion",
    "neck_rotation",
    "left_ankle_dorsiflexion_plantarflexion",
    "left_ankle_inversion_eversion",
    "right_ankle_dorsiflexion_plantarflexion",
    "right_ankle_inversion_eversion",
    "spine_extension_flexion",
    "spine_lateral_flexion",
    "left_hand_extension_flexion",
    "right_hand_extension_flexion",
]


class DegsIndexes(IntEnum):
    """
    Standardized indices using EXACT FreeMoCap column nomenclature in CAPSLOCK.

    This enumeration provides a semantic mapping for the flat kinematic arrays
    used throughout the ErgoMoCap project. It ensures that indices for legs,
    trunk, neck, and upper/lower limbs are consistent across different
    ergonomic calculators (RULA, REBA, EAWS).

    Attributes:
        RIGHT_KNEE_EXTENSION_FLEXION (int): Index 0.
        LEFT_KNEE_EXTENSION_FLEXION (int): Index 1.
        SPINE_EXTENSION_FLEXION (int): Index 2.
        SPINE_LATERAL_FLEXION (int): Index 3.
        SPINE_ROTATION_TORSION (int): Index 4.
        NECK_EXTENSION_FLEXION (int): Index 5.
        NECK_LATERAL_FLEXION (int): Index 6.
        NECK_ROTATION (int): Index 7.
        RIGHT_SHOULDER_EXTENSION_FLEXION (int): Index 8.
        LEFT_SHOULDER_EXTENSION_FLEXION (int): Index 9.
        RIGHT_SHOULDER_ABDUCTION_ADDUCTION (int): Index 10.
        LEFT_SHOULDER_ABDUCTION_ADDUCTION (int): Index 11.
        RIGHT_SHOULDER_RISE (int): Index 12.
        LEFT_SHOULDER_RISE (int): Index 13.
        RIGHT_ELBOW_EXTENSION_FLEXION (int): Index 14.
        LEFT_ELBOW_EXTENSION_FLEXION (int): Index 15.
        RIGHT_HAND_EXTENSION_FLEXION (int): Index 16.
        LEFT_HAND_EXTENSION_FLEXION (int): Index 17.
        RIGHT_HAND_LATERAL_SIDE (int): Index 18.
        LEFT_HAND_LATERAL_SIDE (int): Index 19.
        RIGHT_HAND_TWIST (int): Index 20.
        LEFT_HAND_TWIST (int): Index 21.
    """

    # 1. LEGS [0:2]
    RIGHT_KNEE_EXTENSION_FLEXION = 0
    LEFT_KNEE_EXTENSION_FLEXION = 1

    # 2. TRUNK [2:5]
    SPINE_EXTENSION_FLEXION = 2
    SPINE_LATERAL_FLEXION = 3
    SPINE_ROTATION_TORSION = 4  # Explicitly mapped for future-proofing

    # 3. NECK [5:8]
    NECK_EXTENSION_FLEXION = 5
    NECK_LATERAL_FLEXION = 6
    NECK_ROTATION = 7

    # 4. UPPER ARM [8:14]
    RIGHT_SHOULDER_EXTENSION_FLEXION = 8
    LEFT_SHOULDER_EXTENSION_FLEXION = 9
    RIGHT_SHOULDER_ABDUCTION_ADDUCTION = 10
    LEFT_SHOULDER_ABDUCTION_ADDUCTION = 11
    RIGHT_SHOULDER_RISE = 12
    LEFT_SHOULDER_RISE = 13

    # 5. LOWER ARM [14:16]
    RIGHT_ELBOW_EXTENSION_FLEXION = 14
    LEFT_ELBOW_EXTENSION_FLEXION = 15

    # 6. WRIST [16:22]
    RIGHT_HAND_EXTENSION_FLEXION = 16
    LEFT_HAND_EXTENSION_FLEXION = 17
    RIGHT_HAND_LATERAL_SIDE = 18
    LEFT_HAND_LATERAL_SIDE = 19
    RIGHT_HAND_TWIST = 20
    LEFT_HAND_TWIST = 21


DI = DegsIndexes


def map_fmc_joint_angles_to_ergo_degs(row: pd.Series) -> np.ndarray:
    """
    Maps FreeMoCap CSV columns to the flat array expected by REBA_calculator.

    This function extracts specific joint angles from a DataFrame row and
    organizes them into a structured `numpy.ndarray` according to the
    DegsIndexes schema.

    Args:
        row (pandas.Series): A single row from a FreeMoCap joint angles DataFrame.

    Returns:
        degs (numpy.ndarray): A 22-element `numpy.float64` array of joint angles.
    """
    # Initialize array of 22 zeros (matching your degs[16:22] logic)
    degs = np.zeros(22, dtype=np.float64)

    # 1. Legs [0:2] -> [right_knee, left_knee]
    degs[DI.RIGHT_KNEE_EXTENSION_FLEXION] = row["right_knee_extension_flexion"]
    degs[DI.LEFT_KNEE_EXTENSION_FLEXION] = row["left_knee_extension_flexion"]

    # 2. Trunk [2:5] -> [flexion, side_bending, torsion]
    degs[DI.SPINE_EXTENSION_FLEXION] = row["spine_extension_flexion"]
    degs[DI.SPINE_LATERAL_FLEXION] = row["spine_lateral_flexion"]
    degs[DI.SPINE_ROTATION_TORSION] = (
        0  # FreeMoCap spine rotation isn't always in base CSV, default to 0
    )

    # 3. Neck [5:8] -> [flexion, side_bend, twist]
    degs[DI.NECK_EXTENSION_FLEXION] = row["neck_extension_flexion"]
    degs[DI.NECK_LATERAL_FLEXION] = row["neck_lateral_flexion"]
    degs[DI.NECK_ROTATION] = row["neck_rotation"]

    # 4. Upper Arm [8:14] -> [R_flex, L_flex, R_side, L_side, R_rise, L_rise]
    degs[DI.RIGHT_SHOULDER_EXTENSION_FLEXION] = row["right_shoulder_extension_flexion"]
    degs[DI.LEFT_SHOULDER_EXTENSION_FLEXION] = row["left_shoulder_extension_flexion"]
    degs[DI.RIGHT_SHOULDER_ABDUCTION_ADDUCTION] = row[
        "right_shoulder_abduction_adduction"
    ]
    degs[DI.LEFT_SHOULDER_ABDUCTION_ADDUCTION] = row[
        "left_shoulder_abduction_adduction"
    ]
    # R/L Shoulder rise usually mapped from abduction or separate landmarks
    degs[DI.RIGHT_SHOULDER_RISE] = 0
    degs[DI.LEFT_SHOULDER_RISE] = 0

    # 5. Lower Arm [14:16] -> [right_elbow, left_elbow]
    degs[DI.RIGHT_ELBOW_EXTENSION_FLEXION] = row["right_elbow_extension_flexion"]
    degs[DI.LEFT_ELBOW_EXTENSION_FLEXION] = row["left_elbow_extension_flexion"]

    # 6. Wrist [16:22] -> [R_flex, L_flex, R_side, L_side, R_twist, L_twist]
    degs[DI.RIGHT_HAND_EXTENSION_FLEXION] = row["right_hand_extension_flexion"]
    degs[DI.LEFT_HAND_EXTENSION_FLEXION] = row["left_hand_extension_flexion"]

    # Side/Twist for wrist often 0 unless using high-fidelity FMC gloves/configs
    degs[DI.RIGHT_HAND_LATERAL_SIDE] = 0
    degs[DI.LEFT_HAND_LATERAL_SIDE] = 0
    degs[DI.RIGHT_HAND_TWIST] = 0
    degs[DI.LEFT_HAND_TWIST] = 0

    return degs


def calculate_asymmetry_angle_from_sagittal_plane(
    body_kinematic_row: pd.Series,
) -> float:
    """
    Calculates the angular displacement of the load relative to the mid-sagittal plane.

    The calculation projects the body's forward orientation and the load position
    onto the horizontal XZ floor plane. The angle is determined by the displacement
    of the mid-wrist point relative to the forward vector originating from the
    mid-ankle point.

    Args:
        body_kinematic_row (pandas.Series): Frame data containing 'x' and 'z' 3D coordinates.

    Returns:
        asymmetry_angle_in_degrees (float): The calculated angle in degrees (0 to 180).

    NOTE:
        USED for NIOSH (TODO maybe put it in the NIOSH folder)
    """

    # 1. DEFINE BODY ORIENTATION VECTOR (XZ PLANE)
    # We extract the 2D coordinates for the hips to establish the lateral axis
    left_pelvic_hip_joint_xz_coordinates = np.array(
        [
            float(body_kinematic_row["left_hip_x"]),
            float(body_kinematic_row["left_hip_z"]),
        ]
    )
    right_pelvic_hip_joint_xz_coordinates = np.array(
        [
            float(body_kinematic_row["right_hip_x"]),
            float(body_kinematic_row["right_hip_z"]),
        ]
    )

    # Calculate the vector representing the line between both hips
    hip_to_hip_lateral_axis_vector = (
        right_pelvic_hip_joint_xz_coordinates - left_pelvic_hip_joint_xz_coordinates
    )

    # The forward-facing orientation (sagittal plane) is defined as the
    # orthogonal vector to the lateral hip-to-hip line.
    # Rotation transformation: (dx, dz) -> (-dz, dx)
    body_forward_facing_sagittal_vector = np.array(
        [-hip_to_hip_lateral_axis_vector[1], hip_to_hip_lateral_axis_vector[0]]
    )

    # 2. DEFINE LOAD POSITION VECTOR (ORIGIN AT ANKLE MIDPOINT)
    # We establish the base of the user (mid-point between ankles)
    left_ankle_joint_xz_coordinates = np.array(
        [
            float(body_kinematic_row["left_ankle_x"]),
            float(body_kinematic_row["left_ankle_z"]),
        ]
    )
    right_ankle_joint_xz_coordinates = np.array(
        [
            float(body_kinematic_row["right_ankle_x"]),
            float(body_kinematic_row["right_ankle_z"]),
        ]
    )
    midpoint_origin_between_ankles = (
        left_ankle_joint_xz_coordinates + right_ankle_joint_xz_coordinates
    ) / 2.0

    # We establish the position of the load (mid-point between wrists)
    left_wrist_joint_xz_coordinates = np.array(
        [
            float(body_kinematic_row["left_wrist_x"]),
            float(body_kinematic_row["left_wrist_z"]),
        ]
    )
    right_wrist_joint_xz_coordinates = np.array(
        [
            float(body_kinematic_row["right_wrist_x"]),
            float(body_kinematic_row["right_wrist_z"]),
        ]
    )
    midpoint_load_position_between_wrists = (
        left_wrist_joint_xz_coordinates + right_wrist_joint_xz_coordinates
    ) / 2.0

    # The load vector represents the direction from the feet to the hands
    vector_pointing_towards_load_center = (
        midpoint_load_position_between_wrists - midpoint_origin_between_ankles
    )

    # 3. CALCULATE ANGULAR DISPLACEMENT (DOT PRODUCT METHOD)
    magnitude_of_forward_facing_vector = np.linalg.norm(
        body_forward_facing_sagittal_vector
    )
    magnitude_of_load_direction_vector = np.linalg.norm(
        vector_pointing_towards_load_center
    )

    # Handle division by zero for stationary or overlapping coordinates
    if (
        magnitude_of_forward_facing_vector == 0
        or magnitude_of_load_direction_vector == 0
    ):
        return 0.0

    # Calculate normalized dot product to find the cosine of the angle
    normalized_dot_product_of_vectors = np.dot(
        body_forward_facing_sagittal_vector, vector_pointing_towards_load_center
    ) / (magnitude_of_forward_facing_vector * magnitude_of_load_direction_vector)

    # Clip values to handle floating point precision errors outside the [-1, 1] range
    clamped_cosine_value = np.clip(normalized_dot_product_of_vectors, -1.0, 1.0)

    # Convert arc-cosine result from radians to degrees
    asymmetry_angle_in_degrees = np.degrees(np.arccos(clamped_cosine_value))

    return float(asymmetry_angle_in_degrees)


def map_fmc_kinematics_to_niosh_vars(
    body_row: pd.Series, load_weight: float = 5.0
) -> dict[str, float]:
    """
    Maps FreeMoCap 3D trajectory data to NIOSH Lifting Equation variables.

    This function extracts the geometric spatial relationships between the
    worker's ankles, hips, and wrists to compute the horizontal, vertical,
    and asymmetric components of a lift.

    Args:
        body_row (pd.Series): A single frame from 'mediapipe_body_3d_xyz.csv'.
        load_weight (float): The weight of the object in kg. Defaults to 5.0.

    Returns:
        niosh_vars (dict[str, float]): dictionary containing:
            - 'load': Actual mass (kg)
            - 'H': Horizontal distance (cm/units)
            - 'V': Vertical height (cm/units)
            - 'A': Asymmetry angle (degrees)
            - 'D': Vertical travel (default 0.0 for frame-based)
    """
    # 1. Origin (Mid-Ankle) and Load (Mid-Wrist) positions
    l_ank_xz = np.array(
        [float(body_row["left_ankle_x"]), float(body_row["left_ankle_z"])]
    )
    r_ank_xz = np.array(
        [float(body_row["right_ankle_x"]), float(body_row["right_ankle_z"])]
    )
    mid_ankle_xz = (l_ank_xz + r_ank_xz) / 2.0

    l_wri_xz = np.array(
        [float(body_row["left_wrist_x"]), float(body_row["left_wrist_z"])]
    )
    r_wri_xz = np.array(
        [float(body_row["right_wrist_x"]), float(body_row["right_wrist_z"])]
    )
    mid_hand_xz = (l_wri_xz + r_wri_xz) / 2.0

    # 2. Compute H (Horizontal Distance)
    h_dist = float(np.linalg.norm(mid_hand_xz - mid_ankle_xz))

    # 3. Compute V (Vertical Height)
    ankle_y = (float(body_row["left_ankle_y"]) + float(body_row["right_ankle_y"])) / 2.0
    hand_y = (float(body_row["left_wrist_y"]) + float(body_row["right_wrist_y"])) / 2.0
    v_dist = abs(hand_y - ankle_y)

    # 4. Compute A (Asymmetry Angle)
    asymmetry_angle = calculate_asymmetry_angle_from_sagittal_plane(body_row)

    return {
        "load": float(load_weight),
        "H": h_dist,
        "V": v_dist,
        "A": asymmetry_angle,
        "D": 0.0,  # Displacement requires temporal start/end frames
    }


def map_fmc_kinematics_to_ocra_vars(degs: NDArray[np.float64]) -> dict[str, Any]:
    """
    Translates FreeMoCap kinematic slices into OCRA-specific risk variables.

    This mapper isolates upper-limb kinematics and categorizes them into
    postural 'Technical Actions' based on ISO 11228-3 thresholds. It
    evaluates both limbs and returns the highest risk found.

    Args:
        degs (NDArray[np.float64]): A 1D array containing 22 kinematic values.
            Expected slices:
            - [8:10]   Upper Arm Flexion: [Right, Left]
            - [10:12]  Upper Arm Abduction: [Right, Left]
            - [14:16]  Lower Arm Flexion: [Right, Left]
            - [16:18]  Wrist Flexion/Extension: [Right, Left]
            - [18:20]  Wrist Deviation: [Right, Left]

    Returns:
        ocra_flags (dict[str, any]): Boolean risk flags for the scoring engine:
            - 'shoulder_extreme': True if Flex/Abd > 80°.
            - 'shoulder_heavy': True if Flex/Abd > 40°.
            - 'elbow_extreme': True if Flex < 40° or Flex > 150°.
            - 'wrist_extreme': True if Flex/Ext > 45° or Deviation > 15°.
    """
    if len(degs) != 22:
        raise IndexError(f"OCRA Mapper expected 22 values, received {len(degs)}")

    # Evaluate both sides to find the worst-case posture
    # Indices: 8/9 (Flexion), 10/11 (Abduction), 14/15 (Elbow), 16/17 (Wrist Flex), 18/19 (Wrist Dev)
    r_shoulder = max(degs[8], degs[10])
    l_shoulder = max(degs[9], degs[11])
    max_shoulder = max(r_shoulder, l_shoulder)

    max_elbow_flex = max(degs[14], degs[15])
    min_elbow_flex = min(degs[14], degs[15])

    max_wrist_flex = max(abs(degs[16]), abs(degs[17]))
    max_wrist_dev = max(abs(degs[18]), abs(degs[19]))

    return {
        "shoulder_extreme": bool(max_shoulder > 80.0),
        "shoulder_heavy": bool(max_shoulder > 40.0),
        "elbow_extreme": bool(min_elbow_flex < 40.0 or max_elbow_flex > 150.0),
        "wrist_extreme": bool(max_wrist_flex > 45.0 or max_wrist_dev > 15.0),
    }


def map_fmc_kinematics_to_ewas_vars(body_row: pd.Series) -> dict[str, float]:
    """
    Maps FreeMoCap joint angles to the variables required for EAWS Section 1.

    This adapter extracts trunk and neck angles, ensuring they are narrowed
    to float types to satisfy static type checkers.

    Args:
        body_row (pd.Series): A single frame of joint angle data.

    Returns:
        eaws_vars (dict[str, float]): Cleaned kinematic variables for EAWS calculation.
            - 'trunk_flexion': Degrees of forward bend.
            - 'trunk_lateral': Degrees of side bending.
            - 'neck_flexion': Degrees of neck bend.
    """
    return {
        "trunk_flexion": float(body_row.get("spine_extension_flexion", 0.0)),
        "trunk_lateral": float(body_row.get("spine_lateral_flexion", 0.0)),
        "neck_flexion": float(body_row.get("neck_extension_flexion", 0.0)),
        "trunk_rotation": float(body_row.get("spine_rotation", 0.0)),
    }


def map_fmc_kinematics_to_snook_vars(
    body_3d_xyz: np.ndarray, event_frames: tuple[int, int]
) -> dict[str, float]:
    """
    Extracts Snook/Liberty Mutual spatial variables from an FMC event segment.

    Processes a temporal slice of 3D data to determine vertical travel and average
    horizontal reach during a specific lifting or lowering event.

    Args:
        body_3d_xyz (numpy.ndarray): A [Frames, Joints, 3] `numpy.ndarray` of coordinates.
        event_frames (tuple[int, int]): A `tuple` containing (start_frame, end_frame).

    Returns:
        snook_vars (dict[str, float]): Dictionary with 'v_start_cm', 'v_end_cm', 'v_travel_cm', and 'h_dist_cm'.
    """
    start_idx, end_idx = event_frames

    # 1. Vertical Heights (V) at start and end
    # Using Mid-Wrist (Average of 15, 16)
    wrists_y = (body_3d_xyz[:, 15, 1] + body_3d_xyz[:, 16, 1]) / 2.0
    v_start = wrists_y[start_idx]
    v_end = wrists_y[end_idx]
    v_travel = abs(v_end - v_start)

    # 2. Horizontal Distance (H)
    # Measured from Mid-Hip (23) to Mid-Wrist (15/16)
    hips_xz = (body_3d_xyz[:, 23, 0], body_3d_xyz[:, 23, 2])
    wrists_xz = (
        (body_3d_xyz[:, 15, 0] + body_3d_xyz[:, 16, 0]) / 2.0,
        (body_3d_xyz[:, 15, 2] + body_3d_xyz[:, 16, 2]) / 2.0,
    )

    # Calculate H for all frames in the event and take the mean
    h_dist = np.mean(
        np.sqrt((wrists_xz[0] - hips_xz[0]) ** 2 + (wrists_xz[1] - hips_xz[1]) ** 2)
    )

    # Snook adjustment: Subtract ~20cm for body depth (Abdomen origin)
    h_snook = float(max(h_dist - 20.0, 0.0))

    return {
        "v_start_cm": v_start,
        "v_end_cm": v_end,
        "v_travel_cm": v_travel,
        "h_dist_cm": h_snook,
    }
