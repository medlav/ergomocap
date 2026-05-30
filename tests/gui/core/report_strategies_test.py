# ---
# project: ErgoMoCap
# file: report_strategies_test.py
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

from gui.core.report_strategies import (
    ResultRow,
    RulaStrategy,
    RebaStrategy,
)


class TestReportStrategies:
    """
    Test suite for ErgoMoCap report strategies.
    Ensures data mapping accuracy and visual hierarchy logic.
    """

    def test_result_row_defaults(self):
        """Verifies dataclass default values for UI flags."""
        row = ResultRow(label="Test", value=10)
        assert row.label == "Test"
        assert row.value == 10
        assert row.is_header is False
        assert row.is_critical is False
        assert row.is_angle is False

    def test_rula_strategy_formatting(self):
        """Covers RULA key mapping and header/critical flag assignment."""
        strategy = RulaStrategy()
        data = {
            "Upper_Arm_Score_RULA": "3",
            "Wrist_Score_RULA": "2",
            "Score_A_RULA": "4",
            "Neck_Score_RULA": "2",
            "Trunk_Score_RULA": "3",
            "Final_Score_RULA": "7",
        }

        rows = strategy.format(data)

        assert strategy.name == "RULA"
        assert len(rows) == 8

        # Check Header
        assert rows[0].label == "Group A (Upper Limbs)"
        assert rows[0].is_header is True

        # Check Value Mapping
        assert rows[1].label == "Upper Arm"
        assert rows[1].value == "3"

        # Check Critical Score
        assert rows[-1].label == "FINAL RULA"
        assert rows[-1].value == "7"
        assert rows[-1].is_critical is True

    def test_reba_strategy_formatting(self):
        """Covers REBA key mapping and visual structure."""
        strategy = RebaStrategy()
        data = {
            "Neck_Score_REBA": "2",
            "Trunk_Score_REBA": "4",
            "Legs_Score_REBA": "1",
            "Upper_Arm_Score_REBA": "3",
            "Lower_Arm_Score_REBA": "2",
            "Wrist_Score_REBA": "2",
            "Final_Score_REBA": "11",
        }

        rows = strategy.format(data)

        assert strategy.name == "REBA"
        assert len(rows) == 9

        # Check Headers
        headers = [r for r in rows if r.is_header]
        assert len(headers) == 2
        assert headers[0].label == "Group A (Neck, Trunk, legs)"

        # Check Fallback for missing keys
        empty_rows = strategy.format({})
        assert empty_rows[1].value == "-"  # Neck score should fallback to "-"

    def test_strategy_protocol_compliance(self):
        """
        Structural test to ensure concrete strategies follow the ReportStrategy Protocol.
        """
        # This is a type-checking test; if they didn't comply,
        # static analysis would fail, but we check presence of members here.
        strategies = [RulaStrategy(), RebaStrategy()]
        for s in strategies:
            assert hasattr(s, "name")
            assert hasattr(s, "format")
            assert callable(s.format)

    def test_niosh_ocra_stubs(self):
        """
        Simply verifies the existence of upcoming strategy stubs
        to ensure they aren't accidentally removed.
        """
        from gui.core.report_strategies import NIOSHStrategy, OCRAStrategy

        # Since these are currently Ellipsis (...), we just check they exist
        assert NIOSHStrategy is not None
        assert OCRAStrategy is not None
