# ---
# project: ErgoMoCap
# file: constants_test.py
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
from gui.utils.constants import (
    BodyPart,
    MetricType,
    AssessmentMethod,
    RiskLevel,
    DegsIndexes,
    FMC_ANGLE_COLUMNS,
    ANGLE_LABELS,
)


class TestConstantsAndEnums:
    """
    Test suite to verify that all constants and enums are correctly defined
    and maintain structural integrity for the ErgoMoCap ecosystem.
    """

    @pytest.mark.parametrize(
        "enum_class, expected_members",
        [
            (
                BodyPart,
                [
                    "NECK",
                    "TRUNK",
                    "LEGS",
                    "UPPER_ARM",
                    "LOWER_ARM",
                    "WRIST",
                    "SHOULDERS",
                    "HIPS",
                ],
            ),
            (MetricType, ["SCORE", "ANGLE", "RISK"]),
            (AssessmentMethod, ["REBA", "RULA"]),
            (RiskLevel, ["NEGLIGIBLE", "LOW", "MEDIUM", "HIGH", "VERY_HIGH"]),
        ],
    )
    def test_enum_members_exist(self, enum_class, expected_members):
        """Ensure all required enum members are present and accessible."""
        for member in expected_members:
            assert hasattr(enum_class, member)
            assert isinstance(getattr(enum_class, member), enum_class)

    def test_body_part_values(self):
        """Verify string values for BodyPart (used in UI and Logic)."""
        assert BodyPart.NECK.value == "neck"
        assert BodyPart.UPPER_ARM.value == "upper_arm"
        assert BodyPart.WRIST.value == "wrist"

    def test_degs_indexes_values(self):
        """Verify the IntEnum mapping for biomechanical indices."""
        assert DegsIndexes.RIGHT_KNEE_EXTENSION_FLEXION == 0
        assert DegsIndexes.NECK_ROTATION == 7
        assert DegsIndexes.LEFT_HAND_TWIST == 21
        # Test that it behaves as an integer
        assert DegsIndexes.SPINE_EXTENSION_FLEXION + 1 == 3

    def test_fmc_angle_columns_schema(self):
        """Verify the integrity of the FMC_ANGLE_COLUMNS list."""
        assert isinstance(FMC_ANGLE_COLUMNS, list)
        assert "left_elbow_extension_flexion" in FMC_ANGLE_COLUMNS
        assert "right_hand_extension_flexion" in FMC_ANGLE_COLUMNS
        assert len(FMC_ANGLE_COLUMNS) == 23

    def test_angle_labels_mapping(self):
        """
        Verify that ANGLE_LABELS correctly maps BodyPart enums
        to their respective string identifiers.
        """
        assert isinstance(ANGLE_LABELS, dict)

        # Test specific mappings
        assert "neck_extension_flexion" in ANGLE_LABELS[BodyPart.NECK]
        assert "shoulder_rise_right" in ANGLE_LABELS[BodyPart.UPPER_ARM]
        assert "hand_twist_left" in ANGLE_LABELS[BodyPart.WRIST]

        # Ensure all core BodyParts used in calculations have labels
        expected_parts = {
            BodyPart.LEGS,
            BodyPart.TRUNK,
            BodyPart.NECK,
            BodyPart.UPPER_ARM,
            BodyPart.LOWER_ARM,
            BodyPart.WRIST,
        }
        for part in expected_parts:
            assert part in ANGLE_LABELS
            assert isinstance(ANGLE_LABELS[part], list)
            assert len(ANGLE_LABELS[part]) > 0

    def test_enum_iteration(self):
        """Ensure Enums are iterable (often used in GUI dropdowns)."""
        methods = [m for m in AssessmentMethod]
        assert AssessmentMethod.REBA in methods
        # assert AssessmentMethod.RULA in methods TODO uncomment when implemented pdf/docx and scores_list in video canvas for rula too
        assert len(methods) == 2

    def test_risk_level_order(self):
        """Verify RiskLevel values represent the correct string keys for styles."""
        assert RiskLevel.NEGLIGIBLE.value == "negligible"
        assert RiskLevel.VERY_HIGH.value == "very_high"
