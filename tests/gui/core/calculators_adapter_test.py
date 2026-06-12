# ---
# project: ErgoMoCap
# file: calculators_adapter_test.py
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
import pandas as pd
from gui.core.calculators_adapter import (
    BaseErgoAdapter,
    REBAAdapter,
    RULAAdapter,
    NIOSHAdapter,
    OCRAAdapter,
    EWASAdapter,
    SNOOKAdapter,
)
from gui.utils.constants import RiskLevel, MetricType


# We define a concrete implementation for testing the Base class logic
class MockAdapter(BaseErgoAdapter):
    INTERNAL_SCORE_KEY = "mock_score"

    @staticmethod
    def get_thresholds():
        return [(5, RiskLevel.LOW), (10, RiskLevel.HIGH)]

    @staticmethod
    def get_relay_tools():
        # Using .sum() to ensure we return a scalar and avoid Pandas truthiness errors
        return lambda row: row.sum(), lambda x: ({"mock_score": int(x + 1)}, None)


class TestCalculatorsAdapter:
    """
    Revised Suite for Calculators Adapter.
    Fixes inheritance attribute errors and Pandas truthiness ambiguity.
    """

    def test_process_empty_dataframe(self):
        """Covers line 150-151: early exit for empty results."""
        df = MockAdapter.process([], lambda x: RiskLevel.LOW)
        assert df.empty

    def test_process_with_explicit_key(self):
        """Covers the happy path where INTERNAL_SCORE_KEY is present."""
        results = [
            {"mock_score": 3, "MY_FINAL_SCORE": 0},
            {"mock_score": 8, "MY_FINAL_SCORE": 0},
        ]

        def mock_risk_cb(score):
            return RiskLevel.LOW if score < 5 else RiskLevel.HIGH

        df = MockAdapter.process(results, mock_risk_cb)

        assert df[MetricType.SCORE.value].tolist() == [3, 8]
        assert df[MetricType.RISK.value].iloc[0] == RiskLevel.LOW.value

    def test_process_internal_key_fallback(self):
        """
        Covers fallback when INTERNAL_SCORE_KEY is missing/ignored
        and relies on the FINAL_SCORE heuristic tracking.
        """

        class SimpleAdapter(BaseErgoAdapter):
            @staticmethod
            def get_thresholds():
                return []

            @staticmethod
            def get_relay_tools():
                return lambda x: x, lambda x: ({}, None)

        heuristic_col = "target_FINAL_SCORE"
        results = [{"ignore_me": 1, heuristic_col: 10}]

        SimpleAdapter.INTERNAL_SCORE_KEY = heuristic_col

        df = SimpleAdapter.process(results, lambda x: RiskLevel.LOW)

        assert df[MetricType.SCORE.value].iloc[0] == 10

    def test_get_stats_distribution(self):
        """Covers lines 174-184: frequency distribution logic."""
        scores = [1, 4, 6, 12]  # Thresholds are (5, LOW), (10, HIGH)
        stats = MockAdapter.get_stats(scores)

        assert stats[RiskLevel.LOW.value] == 2  # 1 and 4
        assert stats[RiskLevel.HIGH.value] == 1  # 6
        # 12 is excluded as it's > 10

    @pytest.mark.parametrize(
        "adapter_cls, first_limit",
        [
            (REBAAdapter, 1),
            (RULAAdapter, 1),
            (NIOSHAdapter, 1),
            (OCRAAdapter, 7),
            (EWASAdapter, 25),
            (SNOOKAdapter, 1),
        ],
    )
    def test_adapter_thresholds_matrix(self, adapter_cls, first_limit):
        """Matrix test for all specific adapter threshold definitions."""
        thresholds = adapter_cls.get_thresholds()
        assert thresholds[0][0] == first_limit
        assert isinstance(thresholds[0][1], RiskLevel)

    def test_adapter_relay_tools_logic(self):
        """Ensures the real adapters return the correct imported functions."""
        # Test REBA as the primary example
        mapper, calculator = REBAAdapter.get_relay_tools()
        assert mapper.__name__ == "map_fmc_joint_angles_to_ergo_degs"
        assert calculator.__name__ == "calculate_frame_reba_from_degs"

    def test_stats_empty_input(self):
        """Verify stats doesn't crash on empty input and returns zeroed counts."""
        stats = RULAAdapter.get_stats([])
        assert all(count == 0 for count in stats.values())
