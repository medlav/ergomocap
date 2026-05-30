# ---
# project: ErgoMoCap
# file: constants.py
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
ErgoMoCap: Project Constants and Enumerations
---------------------------------------------
Centralized Definitions for Domain Entities, Metrics, and Data Indices.

This module serves as the single source of truth for constants used across the
ErgoMoCap ecosystem. It defines structured enumerations for biological segments,
assessment methodologies, and risk levels to ensure type safety and logic consistency
between the `/calculators` and `/gui` modules.

A critical component of this module is the synchronization with the FreeMoCap (FMC)
nomenclature. It maps specific biomechanical degrees of freedom to their respective
indices and column names used in the underlying data arrays and DataFrames.

Key Enumerations:
    * `BodyPart`: Anatomical segments targeted by ergonomic assessments.
    * `MetricType`: Classification of data points (Score, Angle, or Risk).
    * `AssessmentMethod`: Supported ergonomic protocols (REBA, RULA).
    * `RiskLevel`: Qualitative descriptors for calculated ergonomic risks.
    * `DegsIndexes`: Integer mapping for raw biomechanical degree-of-freedom arrays.

Data Schemas:
    * `FMC_ANGLE_COLUMNS`: Standardized list of strings for DataFrame column indexing.
    * `ANGLE_LABELS`: Mapping of `BodyPart` to project-specific FMC metric strings.
"""

from enum import Enum, IntEnum


class BodyPart(Enum):
    """
    Enumeration of anatomical segments targeted by ergonomic assessments.

    Attributes:
        NECK (str): The cervical spine region.
        TRUNK (str): The main torso/spine region.
        LEGS (str): Lower extremities including knees and hips.
        UPPER_ARM (str): Humerus region (shoulder to elbow).
        LOWER_ARM (str): Forearm region (elbow to wrist).
        WRIST (str): Carpal region.
        SHOULDERS (str): Bi-lateral shoulder alignment.
        HIPS (str): Bi-lateral pelvic alignment.
    """

    NECK = "neck"
    TRUNK = "trunk"
    LEGS = "legs"
    UPPER_ARM = "upper_arm"
    LOWER_ARM = "lower_arm"
    WRIST = "wrist"
    SHOULDERS = "shoulders"
    HIPS = "hips"


class MetricType(Enum):
    """
    Classification of ergonomic data points and calculation results.

    Attributes:
        SCORE (str): Numerical assessment value (e.g., REBA final score).
        ANGLE (str): Biomechanical joint angle in degrees.
        RISK (str): Qualitative risk classification.
    """

    SCORE = "score"
    ANGLE = "angle"
    RISK = "risk"


class AssessmentMethod(Enum):
    """
    Supported ergonomic assessment protocols.

    Attributes:
        REBA (str): Rapid Entire Body Assessment.
        RULA (str): Rapid Upper Limb Assessment.
    """

    REBA = "reba"
    RULA = "rula"  # TODO uncomment when implemented pdf/docx and scores_list in video canvas for rula too


class RiskLevel(Enum):
    """
    Qualitative descriptors for calculated ergonomic risk levels.

    Attributes:
        NEGLIGIBLE (str): No action required.
        LOW (str): Further investigation may be needed.
        MEDIUM (str): Further investigation and changes soon.
        HIGH (str): Investigation and changes required immediately.
        VERY_HIGH (str): Urgent changes required.
    """

    NEGLIGIBLE = "negligible"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class DegsIndexes(IntEnum):
    """
    Standardized indices mapping to FreeMoCap (FMC) biomechanical degree-of-freedom arrays.

    These indices are used to slice raw data arrays based on the
    [bodypart]_[metric]_[method/subgroup] nomenclature.

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

    # 1. LEGS
    RIGHT_KNEE_EXTENSION_FLEXION = 0
    LEFT_KNEE_EXTENSION_FLEXION = 1

    # 2. TRUNK
    SPINE_EXTENSION_FLEXION = 2
    SPINE_LATERAL_FLEXION = 3
    SPINE_ROTATION_TORSION = 4

    # 3. NECK
    NECK_EXTENSION_FLEXION = 5
    NECK_LATERAL_FLEXION = 6
    NECK_ROTATION = 7

    # 4. UPPER ARM
    RIGHT_SHOULDER_EXTENSION_FLEXION = 8
    LEFT_SHOULDER_EXTENSION_FLEXION = 9
    RIGHT_SHOULDER_ABDUCTION_ADDUCTION = 10
    LEFT_SHOULDER_ABDUCTION_ADDUCTION = 11
    RIGHT_SHOULDER_RISE = 12
    LEFT_SHOULDER_RISE = 13

    # 5. LOWER ARM
    RIGHT_ELBOW_EXTENSION_FLEXION = 14
    LEFT_ELBOW_EXTENSION_FLEXION = 15

    # 6. WRIST
    RIGHT_HAND_EXTENSION_FLEXION = 16
    LEFT_HAND_EXTENSION_FLEXION = 17
    RIGHT_HAND_LATERAL_SIDE = 18
    LEFT_HAND_LATERAL_SIDE = 19
    RIGHT_HAND_TWIST = 20
    LEFT_HAND_TWIST = 21


"""
Module-level constants for data schema and UI labeling.

Attributes:
    FMC_ANGLE_COLUMNS (list[str]): Standardized column names for `pandas.DataFrame` indexing of biomechanical angles.
    ANGLE_LABELS (dict[BodyPart, list[str]]): Mapping of [BodyPart][gui.utils.constants.BodyPart] to FMC metric strings for display and export.
"""

# Standardized FMC Column Names for DataFrame consistency
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

# Mapping Enums to FMC-style strings for UI and Export
ANGLE_LABELS: dict[BodyPart, list[str]] = {
    BodyPart.LEGS: ["knee_right_extension_flexion", "knee_left_extension_flexion"],
    BodyPart.TRUNK: [
        "spine_extension_flexion",
        "spine_lateral_flexion",
        "spine_rotation_torsion",
    ],
    BodyPart.NECK: ["neck_extension_flexion", "neck_lateral_flexion", "neck_rotation"],
    BodyPart.UPPER_ARM: [
        "shoulder_extension_flexion_right",
        "shoulder_extension_flexion_left",
        "shoulder_abduction_adduction_right",
        "shoulder_abduction_adduction_left",
        "shoulder_rise_right",
        "shoulder_rise_left",
    ],
    BodyPart.LOWER_ARM: [
        "elbow_extension_flexion_right",
        "elbow_extension_flexion_left",
    ],
    BodyPart.WRIST: [
        "hand_extension_flexion_right",
        "hand_extension_flexion_left",
        "hand_lateral_side_right",
        "hand_lateral_side_left",
        "hand_twist_right",
        "hand_twist_left",
    ],
}


# TODO check if need to be deleted
# NOSE = np.int32(0)
# LEFT_EYE_INNER = np.int32(1)
# LEFT_EYE = np.int32(2)
# LEFT_EYE_OUTER = np.int32(3)
# RIGHT_EYE_INNER = np.int32(4)
# RIGHT_EYE = np.int32(5)
# RIGHT_EYE_OUTER = np.int32(6)
# LEFT_EAR = np.int32(7)
# RIGHT_EAR = np.int32(8)
# MOUTH_LEFT = np.int32(9)
# MOUTH_RIGHT = np.int32(10)
# LEFT_SHOULDER = np.int32(11)
# RIGHT_SHOULDER = np.int32(12)
# LEFT_ELBOW = np.int32(13)
# RIGHT_ELBOW = np.int32(14)
# LEFT_WRIST = np.int32(15)
# RIGHT_WRIST = np.int32(16)
# LEFT_PINKY = np.int32(17)
# RIGHT_PINKY = np.int32(18)
# LEFT_INDEX = np.int32(19)
# RIGHT_INDEX = np.int32(20)
# LEFT_THUMB = np.int32(21)
# RIGHT_THUMB = np.int32(22)
# LEFT_HIP = np.int32(23)
# RIGHT_HIP = np.int32(24)
# LEFT_KNEE = np.int32(25)
# RIGHT_KNEE = np.int32(26)
# LEFT_ANKLE = np.int32(27)
# RIGHT_ANKLE = np.int32(28)
# LEFT_HEEL = np.int32(29)
# RIGHT_HEEL = np.int32(30)
# LEFT_FOOT_INDEX = np.int32(31)
# RIGHT_FOOT_INDEX = np.int32(32)


# SKELETON_MAP: list[tuple[BodyPart, np.int32, np.int32]] = [
#     (BodyPart.NECK, RIGHT_SHOULDER, RIGHT_EAR),
#     (BodyPart.NECK, LEFT_SHOULDER, LEFT_EAR),
#     (BodyPart.TRUNK, RIGHT_SHOULDER, RIGHT_HIP),
#     (BodyPart.TRUNK, LEFT_SHOULDER, LEFT_HIP),
#     (BodyPart.SHOULDERS, LEFT_SHOULDER, RIGHT_SHOULDER),
#     (BodyPart.HIPS, LEFT_HIP, RIGHT_HIP),
#     (BodyPart.UPPER_ARM, RIGHT_SHOULDER, RIGHT_ELBOW),
#     (BodyPart.LOWER_ARM, RIGHT_ELBOW, RIGHT_WRIST),
#     (BodyPart.UPPER_ARM, LEFT_SHOULDER, LEFT_ELBOW),
#     (BodyPart.LOWER_ARM, LEFT_ELBOW, LEFT_WRIST),
#     (BodyPart.LEGS, RIGHT_HIP, RIGHT_KNEE),
#     (BodyPart.LEGS, RIGHT_KNEE, RIGHT_ANKLE),
#     (BodyPart.LEGS, LEFT_HIP, LEFT_KNEE),
#     (BodyPart.LEGS, LEFT_KNEE, LEFT_ANKLE),
# ]
