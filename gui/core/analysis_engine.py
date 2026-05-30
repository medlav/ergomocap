# ---
# project: ErgoMoCap
# file: analysis_engine.py
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
ErgoMoCap: Analysis Engine
--------------------------
Core Computational Logic for Ergonomic Assessments.

This module implements the [AnalysisEngine][gui.core.analysis_engine.AnalysisEngine]
class, which serves as the high-performance processing core of the ErgoMoCap
project. It utilizes a "Relay" pattern to decouple data iteration from specific
ergonomic assessment logic (e.g., RULA, REBA, NIOSH).

By accepting arbitrary mapping and calculation functions, the engine can process
both structured `pandas.DataFrame` objects from CSV files and raw `numpy.ndarray`
landmark data exported directly from FreeMoCap.

Key Features:
    * Agnostic data processing loop for multiple biomechanical standards.
    * Real-time risk level categorization using standardized [RiskLevel][gui.utils.constants.RiskLevel] Enums.
    * Support for multi-format input handling (Pandas and NumPy).
    * Synchronized frame-by-frame metadata generation for analysis reporting.
"""

import numpy as np
import pandas as pd
from typing import Callable, Any, Union

# Internal Imports
from gui.utils.constants import RiskLevel


class AnalysisEngine:
    """
    Core computational engine for ergonomic assessments.

    This engine acts as a high-performance processor that executes mapping and
    calculation functions provided by external adapters. It handles data
    iteration across various formats (Pandas DataFrames or NumPy arrays)
    without internalizing the specific ergonomic logic.

    Methods:
        get_risk_level_enum: Maps a numerical score to a standardized [RiskLevel][gui.utils.constants.RiskLevel] Enum.
        run_calculation: Executes a frame-by-frame processing loop for postural analysis.
    """

    @staticmethod
    def get_risk_level_enum(
        score: int, thresholds: list[tuple[int, RiskLevel]]
    ) -> RiskLevel:
        """
        Maps a numerical score to a standardized RiskLevel Enum.

        This method performs a range-check against a list of thresholds.
        It returns an Enum rather than a string to ensure the UI can
        handle localization (translations) and styling (colors) consistently.

        Args:
            score (int): The calculated ergonomic value (e.g., REBA total index).
            thresholds (list[tuple[int, RiskLevel]]): A list of (upper_limit, RiskLevel) tuples, sorted in ascending order.

        Returns:
            RiskLevel: The corresponding standardized [RiskLevel][gui.utils.constants.RiskLevel] category.
        """
        # Iterate through limits. If score is below or equal to limit, return that level.
        for limit, level in thresholds:
            if score <= limit:
                return level

        # Fallback to the final category (usually VERY_HIGH)
        return thresholds[-1][1]

    def run_calculation(
        self,
        current_data: Union[pd.DataFrame, np.ndarray],
        mapper_func: Callable[[Any], Any],
        calculator_func: Callable[[Any], tuple[dict[str, Any], Any]],
    ) -> list[dict[str, Any]]:
        """
        Executes a frame-by-frame processing loop for postural analysis.

        Handles the "Relay" pattern:
        1. Iterates through the input source (DataFrame rows or Array elements).
        2. Passes raw data to a 'mapper' to prepare assessment-specific joint data.
        3. Passes the mapped data to a 'calculator' to compute ergonomic scores.

        Args:
            current_data (pandas.DataFrame | numpy.ndarray): The input source (DataFrame for CSV, ndarray for NPY).
            mapper_func (Callable[[Any], Any]): Function that transforms a row/frame into the calculator's expected input structure.
            calculator_func (Callable[[Any], tuple[dict[str, Any], Any]]): Function that computes scores and returns a tuple of (results_dict, metadata).

        Returns:
            list[dict[str, Any]]: A list of dictionaries, where each dict contains standardized keys for a single frame.
        """
        results_list: list[dict[str, Any]] = []

        # Logic for Pandas DataFrames (Structured CSV data)
        if isinstance(current_data, pd.DataFrame):
            for _, row in current_data.iterrows():
                # Mapper transforms the row into the calculator's input vars
                input_vars = mapper_func(row)
                # Calculator computes ergonomic indices
                scores, _ = calculator_func(input_vars)
                results_list.append(scores)

        # Logic for raw NumPy arrays (Direct FreeMoCap landmark exports)
        elif isinstance(current_data, np.ndarray):
            for frame_data in current_data:
                # Typically, mappers for raw arrays are identity functions
                # or handled within the calculator_func for performance.
                input_vars = mapper_func(frame_data)
                scores, _ = calculator_func(input_vars)
                results_list.append(scores)

        return results_list
