# ---
# project: ErgoMoCap
# file: freemocap_adapter_test.py
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

import pytest
import numpy as np
import pandas as pd
from calculators.adapters.freemocap_adapter import (
    DegsIndexes,
    map_fmc_joint_angles_to_ergo_degs,
    calculate_asymmetry_angle_from_sagittal_plane,
    map_fmc_kinematics_to_niosh_vars,
    map_fmc_kinematics_to_ocra_vars,
    map_fmc_kinematics_to_ewas_vars,
    map_fmc_kinematics_to_snook_vars,
)


@pytest.fixture
def sample_joint_row():
    """Returns a pd.Series simulating one frame of FMC joint angle data."""
    data = {
        "right_knee_extension_flexion": 10.0,
        "left_knee_extension_flexion": 15.0,
        "spine_extension_flexion": 5.0,
        "spine_lateral_flexion": 2.0,
        "neck_extension_flexion": 1.0,
        "neck_lateral_flexion": 0.0,
        "neck_rotation": 3.0,
        "right_shoulder_extension_flexion": 45.0,
        "left_shoulder_extension_flexion": 40.0,
        "right_shoulder_abduction_adduction": 20.0,
        "left_shoulder_abduction_adduction": 25.0,
        "right_elbow_extension_flexion": 90.0,
        "left_elbow_extension_flexion": 85.0,
        "right_hand_extension_flexion": 10.0,
        "left_hand_extension_flexion": -5.0,
        "spine_rotation": 4.0,
    }
    return pd.Series(data)


@pytest.fixture
def sample_kinematic_row():
    """Returns a pd.Series simulating 3D coordinates (x, y, z) for one frame."""
    return pd.Series(
        {
            "left_hip_x": 0.0,
            "left_hip_z": 0.0,
            "right_hip_x": 10.0,
            "right_hip_z": 0.0,
            "left_ankle_x": 0.0,
            "left_ankle_z": 10.0,
            "left_ankle_y": 0.0,
            "right_ankle_x": 10.0,
            "right_ankle_z": 10.0,
            "right_ankle_y": 0.0,
            "left_wrist_x": 2.0,
            "left_wrist_z": 20.0,
            "left_wrist_y": 50.0,
            "right_wrist_x": 8.0,
            "right_wrist_z": 20.0,
            "right_wrist_y": 50.0,
        }
    )


# --- REBA / JOINT ANGLE MAPPING TESTS ---


def test_map_fmc_joint_angles_to_ergo_degs(sample_joint_row):
    """Verifies that the 22-element degs array is populated correctly (Lines 105-150)."""
    degs = map_fmc_joint_angles_to_ergo_degs(sample_joint_row)
    assert len(degs) == 22
    assert degs[DegsIndexes.RIGHT_KNEE_EXTENSION_FLEXION] == 10.0
    assert degs[DegsIndexes.SPINE_ROTATION_TORSION] == 0  # Fixed default
    assert degs[DegsIndexes.RIGHT_HAND_TWIST] == 0  # Fixed default


# --- NIOSH / VECTOR MATH TESTS ---


def test_calculate_asymmetry_angle_standard(sample_kinematic_row):
    """Tests normal angular calculation logic (Lines 164-255)."""
    angle = calculate_asymmetry_angle_from_sagittal_plane(sample_kinematic_row)
    assert isinstance(angle, float)
    assert 0 <= angle <= 180


def test_calculate_asymmetry_angle_zero_division():
    """Tests the guard for overlapping coordinates (Line 245)."""
    # Create row where hips are at the same spot (magnitude 0)
    zero_row = pd.Series(
        {
            k: 0.0
            for k in [
                "left_hip_x",
                "left_hip_z",
                "right_hip_x",
                "right_hip_z",
                "left_ankle_x",
                "left_ankle_z",
                "right_ankle_x",
                "right_ankle_z",
                "left_wrist_x",
                "left_wrist_z",
                "right_wrist_x",
                "right_wrist_z",
            ]
        }
    )
    angle = calculate_asymmetry_angle_from_sagittal_plane(zero_row)
    assert angle == 0.0


def test_map_fmc_kinematics_to_niosh_vars(sample_kinematic_row):
    """Tests mapping of H, V, A, D variables for NIOSH (Lines 267-308)."""
    vars = map_fmc_kinematics_to_niosh_vars(sample_kinematic_row, load_weight=10.0)
    assert vars["load"] == 10.0
    assert vars["V"] == 50.0  # hand_y(50) - ankle_y(0)
    assert vars["H"] > 0
    assert vars["D"] == 0.0


# --- OCRA MAPPING TESTS ---


def test_map_fmc_kinematics_to_ocra_vars_success():
    """Tests OCRA risk logic thresholds (Lines 341-356)."""
    degs = np.zeros(22)
    # Trigger extreme shoulder (>80) and heavy (>40)
    degs[8] = 85.0
    # Trigger extreme elbow (<40 or >150)
    degs[14] = 30.0
    # Trigger extreme wrist (>45)
    degs[16] = 50.0

    risk = map_fmc_kinematics_to_ocra_vars(degs)
    assert risk["shoulder_extreme"] is True
    assert risk["shoulder_heavy"] is True
    assert risk["elbow_extreme"] is True
    assert risk["wrist_extreme"] is True


def test_map_fmc_kinematics_to_ocra_invalid_length():
    """Exercises the IndexError guard (Line 342)."""
    with pytest.raises(IndexError, match="OCRA Mapper expected 22 values"):
        map_fmc_kinematics_to_ocra_vars(np.array([1, 2, 3]))


# --- EAWS MAPPING TESTS ---


def test_map_fmc_kinematics_to_ewas_vars(sample_joint_row):
    """Tests the EAWS Section 1 mapping (Lines 380-398)."""
    vars = map_fmc_kinematics_to_ewas_vars(sample_joint_row)
    assert vars["trunk_flexion"] == 5.0
    assert vars["trunk_rotation"] == 4.0

    # Test default fallback
    empty_row = pd.Series({})
    vars_default = map_fmc_kinematics_to_ewas_vars(empty_row)
    assert vars_default["trunk_flexion"] == 0.0


# --- SNOOK MAPPING TESTS ---


def test_map_fmc_kinematics_to_snook_vars():
    """Tests 3D array slicing and mean distance for Snook (Lines 398-423)."""
    # Create 3 frames, 25 joints, 3 coordinates (x, y, z)
    body_data = np.zeros((3, 25, 3))
    # Joints: 15/16 (Wrists), 23 (Mid-Hip)
    # Set wrist Y (height)
    body_data[0, 15:17, 1] = 100.0  # Start height
    body_data[2, 15:17, 1] = 150.0  # End height
    # Set horizontal positions
    body_data[:, 23, 0] = 0.0  # Hip X
    body_data[:, 15:17, 0] = 50.0  # Wrist X (H-dist should be ~50)

    vars = map_fmc_kinematics_to_snook_vars(body_data, (0, 2))
    assert vars["v_start_cm"] == 100.0
    assert vars["v_end_cm"] == 150.0
    assert vars["v_travel_cm"] == 50.0
    # H = 50 - 20 (snook adjustment) = 30
    assert vars["h_dist_cm"] == 30.0


def test_map_fmc_kinematics_to_snook_negative_h_floor():
    """Verifies that H distance never goes below zero after Snook adjustment."""
    body_data = np.zeros((2, 25, 3))
    # wrists and hips at same XZ -> H = 0. H_snook = 0 - 20 -> should floor to 0.
    vars = map_fmc_kinematics_to_snook_vars(body_data, (0, 1))
    assert vars["h_dist_cm"] == 0.0
