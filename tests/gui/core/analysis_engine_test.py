# ---
# project: ErgoMoCap
# file: analysis_engine_test.py
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
from gui.core.analysis_engine import AnalysisEngine
from gui.utils.constants import RiskLevel


class TestAnalysisEngine:
    """
    Comprehensive test suite for the AnalysisEngine.
    Targets 100% coverage of mapping and calculation loops.
    """

    @pytest.fixture
    def engine(self):
        return AnalysisEngine()

    @pytest.fixture
    def thresholds(self):
        """Standardized thresholds for testing risk mapping."""
        return [
            (2, RiskLevel.NEGLIGIBLE),
            (4, RiskLevel.LOW),
            (7, RiskLevel.MEDIUM),
            (10, RiskLevel.HIGH),
        ]

    # --- Tests for get_risk_level_enum ---

    @pytest.mark.parametrize(
        "score, expected_level",
        [
            (1, RiskLevel.NEGLIGIBLE),  # Below first threshold
            (2, RiskLevel.NEGLIGIBLE),  # Exactly first threshold
            (3, RiskLevel.LOW),  # Middle threshold
            (7, RiskLevel.MEDIUM),  # Exactly middle threshold
            (11, RiskLevel.HIGH),  # Above all thresholds (fallback branch)
            (99, RiskLevel.HIGH),  # Extreme boundary
        ],
    )
    def test_get_risk_level_enum_mapping(self, score, expected_level, thresholds):
        """Covers all branches of the threshold loop and the fallback return."""
        result = AnalysisEngine.get_risk_level_enum(score, thresholds)
        assert result == expected_level

    # --- Tests for run_calculation ---

    def test_run_calculation_with_dataframe(self, engine):
        """Covers the pd.DataFrame branch of run_calculation (Lines 113-119)."""
        # Setup mock DataFrame
        df = pd.DataFrame({"angle": [10, 20, 30], "frame": [0, 1, 2]})

        # Mapper: Extracts 'angle' from row
        def mock_mapper(row):
            return row["angle"]

        # Calculator: Returns score as a dict and a dummy metadata tuple
        def mock_calculator(val):
            return {"score": val * 2}, "metadata"

        results = engine.run_calculation(df, mock_mapper, mock_calculator)

        assert len(results) == 3
        assert results[0] == {"score": 20}
        assert results[1] == {"score": 40}
        assert results[2] == {"score": 60}

    def test_run_calculation_with_numpy(self, engine):
        """Covers the np.ndarray branch of run_calculation (Lines 122-129)."""
        # Setup mock NumPy array (3 frames, 2 values each)
        arr = np.array([[1.0, 2.0], [3.0, 4.0]])

        # Mapper: Identity function (as mentioned in docstrings)
        def mock_mapper(data):
            return data

        # Calculator: Sums the array elements
        def mock_calculator(data):
            return {"sum": np.sum(data)}, None

        results = engine.run_calculation(arr, mock_mapper, mock_calculator)

        assert len(results) == 2
        assert results[0] == {"sum": 3.0}
        assert results[1] == {"sum": 7.0}

    def test_run_calculation_empty_inputs(self, engine):
        """Tests boundary conditions with empty data structures."""
        # Empty DataFrame
        df_empty = pd.DataFrame(columns=["a"])
        res_df = engine.run_calculation(df_empty, lambda x: x, lambda x: ({}, None))
        assert res_df == []

        # Empty Array
        arr_empty = np.array([])
        res_arr = engine.run_calculation(arr_empty, lambda x: x, lambda x: ({}, None))
        assert res_arr == []

    def test_run_calculation_unsupported_type(self, engine):
        """
        Ensures that if an unsupported type (like a list) is passed,
        it returns an empty list (implicit behavior of the current code).
        """
        results = engine.run_calculation([1, 2, 3], lambda x: x, lambda x: ({}, None))  # type: ignore
        assert results == []

    def test_calculation_complex_metadata_handling(self, engine):
        """
        Verifies that the metadata (the underscore variable in the loop)
        is correctly ignored by the engine but handled by the calculator.
        """
        arr = np.array([[10]])

        def complex_calculator(val):
            # Returning a complex dictionary and a structured metadata tuple
            return {"val": val[0]}, {"meta_info": "ignore_me"}

        results = engine.run_calculation(arr, lambda x: x, complex_calculator)
        assert results == [{"val": 10}]
