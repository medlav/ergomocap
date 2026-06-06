# ---
# project: ErgoMoCap
# file: calculators_adapter.py
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
ErgoMoCap: Calculators Adapter
------------------------------
Standardized Interface for Multi-Method Ergonomic Assessments.

This module implements the [BaseErgoAdapter][gui.core.calculators_adapter.BaseErgoAdapter]
pattern, providing a unified pipeline for converting raw FreeMoCap motion data into
standardized ergonomic scores. It acts as a structural bridge between disparate
biomechanical calculation functions and the ErgoMoCap [gui](reference.md#gui) system.

The adapters handle the coordination between data mapping, frame-by-frame
calculation, and statistical aggregation for several international standards
including REBA, RULA, NIOSH, OCRA, EWAS, and Snook & Ciriello.

Key Features:
    * Abstract interface for unified execution across different assessment methods.
    * Integration with [freemocap_adapter][calculators.adapters.freemocap_adapter] for kinematics mapping.
    * Automated frequency distribution (stats) calculation for risk level bucketing.
    * Standardized output format using [MetricType][gui.utils.constants.MetricType] and [RiskLevel][gui.utils.constants.RiskLevel].
"""

from typing import Any, Callable

import numpy as np
import pandas as pd
from abc import ABC, abstractmethod


# CENTRALIZED IMPORTS
from calculators.adapters.freemocap_adapter import (
    map_fmc_joint_angles_to_ergo_degs,
    map_fmc_kinematics_to_niosh_vars,  # TODO all niosh_calculator/ code and relative adapter/ is to be done
    map_fmc_kinematics_to_ocra_vars,  # TODO all ocra_calculator/ code and relative adapter/ is to be done
    map_fmc_kinematics_to_ewas_vars,  # TODO all ewas_calculator/ code and relative adapter/ is to be done
    map_fmc_kinematics_to_snook_vars,  # TODO all snook_calculator/ code and relative adapter/ is to be done
)

from calculators.calculators import (
    calculate_frame_reba_from_degs,
    calculate_frame_rula_from_degs,
    calculate_frame_niosh_li,  # TODO all niosh_calculator/ code and relative adapter/ is to be done
    calculate_frame_ocra_index,  # TODO all ocra_calculator/ code and relative adapter/ is to be done
    calculate_frame_ewas_score,  # TODO all ewas_calculator/ code and relative adapter/ is to be done
    calculate_frame_snook_index,  # TODO all snook_calculator/ code and relative adapter/ is to be done
)

# CENTRALIZED CONSTANTS & ENUMS
from gui.utils.logger import logger
from gui.utils.constants import RiskLevel, MetricType


# ---------------------------------------------------------
# BASE ADAPTER
# ---------------------------------------------------------

# TODO ADD ALL DOCS


class BaseErgoAdapter(ABC):
    """
    Abstract Base Class for ergonomic assessment adapters.

    This class handles the standard pipeline of converting raw motion data
    (DataFrame rows) into ergonomic scores and statistical distributions.

    Methods:
        get_thresholds: Returns a list of (upper_limit, RiskLevel) tuples for risk bucketing.
        get_relay_tools: Returns the specific mapping and calculation functions for the method.
        run_on_dataframe: Iterates through a DataFrame to calculate scores for every frame.
        process: Converts raw score dictionaries into a processed pandas DataFrame.
        get_stats: Calculates the frequency distribution of scores across risk levels.
    """

    INTERNAL_SCORE_KEY: str = MetricType.SCORE.value

    @staticmethod
    @abstractmethod
    def get_thresholds() -> list[tuple[int, RiskLevel]]:
        """Returns a list of (upper_limit, RiskLevel) tuples for risk bucketing.

        Returns:
            list[tuple[int, RiskLevel]]: Thresholds ordered by limit ascending.
        """
        pass

    @staticmethod
    @abstractmethod
    def get_relay_tools() -> tuple[Callable, Callable]:
        """Returns the specific mapping and calculation functions for the method.

        Returns:
            tuple[Callable, Callable]: (mapping_function, calculation_function)
        """
        pass

    # @classmethod TODO unused dead code implement it or remove it
    # def run_on_dataframe(cls, df: pd.DataFrame) -> list[dict[str, Any]]:
    #     """Iterates through a DataFrame to calculate scores for every frame.

    #     Args:
    #         df: Input motion data where each row represents one time frame.

    #     Returns:
    #         list[dict[str, Any]]: A list of score dictionaries (one per frame).
    #     """
    #     mapper, calculator = cls.get_relay_tools()
    #     results: list[dict[str, Any]] = []

    #     for _, row in df.iterrows():
    #         input_data = mapper(row)
    #         scores, _ = calculator(input_data)
    #         results.append(scores)
    #     return results

    @classmethod
    def process(
        cls,
        results_list: list[dict[str, Any]],
        risk_callback: Callable[[int], RiskLevel],
    ) -> pd.DataFrame:
        """Converts raw score dictionaries into a processed pandas DataFrame.

        Args:
            results_list: The raw output from run_on_dataframe.
            risk_callback: A function to map numerical scores to RiskLevel Enums.

        Returns:
            pd.DataFrame: A DataFrame with standardized score and risk columns.
        """
        df = pd.DataFrame(results_list)
        if df.empty:
            return df

        heuristic_score_col = [
            col for col in df.columns if "FINAL_SCORE" in col.upper()
        ][0]

        internal_key = getattr(cls, "INTERNAL_SCORE_KEY", heuristic_score_col)

        if internal_key not in df.columns:
            logger.error(
                f"Key '{internal_key}' not found in results. Available: {list(df.columns)}"
            )
            raise KeyError("No Score Column in the Dataframe")

        df[MetricType.SCORE.value] = df[internal_key]

        df[MetricType.RISK.value] = [
            risk_callback(int(score)).value for score in df[MetricType.SCORE.value]
        ]

        return df

    @classmethod
    def get_stats(cls, scores_list: list[int]) -> dict[str, int]:
        """Calculates the frequency distribution of scores across risk levels.

        Args:
            scores_list: A list of numerical scores.

        Returns:
            dict[RiskLevel, int]: Mapping of RiskLevel members to frame counts.
        """
        scores = np.array(scores_list)
        stats: dict[str, int] = {}
        thresholds: list[tuple[int, RiskLevel]] = cls.get_thresholds()

        prev_limit = -np.inf
        for limit, level in thresholds:
            count = np.sum((scores > prev_limit) & (scores <= limit))
            stats[level.value] = int(count)
            prev_limit = limit

        return stats


# ---------------------------------------------------------
# SPECIFIC METHOD ADAPTERS
# ---------------------------------------------------------


class REBAAdapter(BaseErgoAdapter):
    """Adapter for Rapid Entire Body Assessment (REBA)."""

    INTERNAL_SCORE_KEY = "Final_Score_REBA"

    @staticmethod
    def get_relay_tools() -> tuple[Callable, Callable]:
        """Returns tools for REBA mapping and calculation."""
        return map_fmc_joint_angles_to_ergo_degs, calculate_frame_reba_from_degs

    @staticmethod
    def get_thresholds() -> list[tuple[int, RiskLevel]]:
        """Returns standardized REBA risk thresholds."""
        return [
            (1, RiskLevel.NEGLIGIBLE),
            (3, RiskLevel.LOW),
            (7, RiskLevel.MEDIUM),
            (10, RiskLevel.HIGH),
            (11, RiskLevel.VERY_HIGH),
        ]


class RULAAdapter(BaseErgoAdapter):
    """Adapter for Rapid Upper Limb Assessment (RULA)."""

    INTERNAL_SCORE_KEY = "Final_Score_RULA"

    @staticmethod
    def get_relay_tools() -> tuple[Callable, Callable]:
        """Returns tools for RULA mapping and calculation."""
        return map_fmc_joint_angles_to_ergo_degs, calculate_frame_rula_from_degs

    @staticmethod
    def get_thresholds() -> list[tuple[int, RiskLevel]]:
        """Returns standardized RULA risk thresholds."""
        return [
            (1, RiskLevel.NEGLIGIBLE),
            (3, RiskLevel.LOW),
            (5, RiskLevel.MEDIUM),
            (7, RiskLevel.HIGH),
        ]


class NIOSHAdapter(BaseErgoAdapter):
    """Adapter for NIOSH Lifting Equation."""

    @staticmethod
    def get_relay_tools() -> tuple[Callable, Callable]:
        """Returns tools for NIOSH mapping and calculation."""
        # TODO all niosh_calculator/ code and relative adapter/ is to be done
        return map_fmc_kinematics_to_niosh_vars, calculate_frame_niosh_li

    @staticmethod
    def get_thresholds() -> list[tuple[int, RiskLevel]]:
        """Returns standardized NIOSH lifting index risk thresholds."""
        return [
            (1, RiskLevel.LOW),
            (3, RiskLevel.MEDIUM),
            (4, RiskLevel.HIGH),
        ]


class OCRAAdapter(BaseErgoAdapter):
    """Adapter for Occupational Repetitive Actions (OCRA) Index."""

    @staticmethod
    def get_relay_tools() -> tuple[Callable, Callable]:
        """Returns tools for OCRA mapping and calculation.

        Returns:
            tuple[Callable, Callable]: (mapper, calculator) functions.
        """
        # TODO all ocra_calculator/ code and relative adapter/ is to be done
        return map_fmc_kinematics_to_ocra_vars, calculate_frame_ocra_index

    @staticmethod
    def get_thresholds() -> list[tuple[int, RiskLevel]]:
        """Returns OCRA index risk thresholds mapped to RiskLevel Enums.

        Returns:
            list[tuple[int, RiskLevel]]: Threshold limits and levels.
        """
        return [
            (7, RiskLevel.NEGLIGIBLE),
            (11, RiskLevel.LOW),
            (14, RiskLevel.MEDIUM),
            (22, RiskLevel.HIGH),
            (23, RiskLevel.VERY_HIGH),
        ]


class EWASAdapter(BaseErgoAdapter):
    """Adapter for Ergo-Work Assessment System (EWAS)."""

    @staticmethod
    def get_relay_tools() -> tuple[Callable, Callable]:
        """Returns tools for EWAS mapping and calculation.

        Returns:
            tuple[Callable, Callable]: (mapper, calculator) functions.
        """
        # TODO all ewas_calculator/ code and relative adapter/ is to be done
        return map_fmc_kinematics_to_ewas_vars, calculate_frame_ewas_score

    @staticmethod
    def get_thresholds() -> list[tuple[int, RiskLevel]]:
        """Returns EWAS score risk thresholds mapped to RiskLevel Enums.

        Returns:
            list[tuple[int, RiskLevel]]: Threshold limits and levels.
        """
        return [
            (25, RiskLevel.LOW),
            (50, RiskLevel.MEDIUM),
            (51, RiskLevel.HIGH),
        ]


class SNOOKAdapter(BaseErgoAdapter):
    """Adapter for Snook & Ciriello Tables (Lifting/Lowering/Pushing)."""

    @staticmethod
    def get_relay_tools() -> tuple[Callable, Callable]:
        """Returns tools for SNOOK mapping and calculation.

        Returns:
            tuple[Callable, Callable]: (mapper, calculator) functions.
        """
        # TODO all snook_calculator/ code and relative adapter/ is to be done
        return map_fmc_kinematics_to_snook_vars, calculate_frame_snook_index

    @staticmethod
    def get_thresholds() -> list[tuple[int, RiskLevel]]:
        """Returns SNOOK ratio risk thresholds mapped to RiskLevel Enums.

        Returns:
            list[tuple[int, RiskLevel]]: Threshold limits and levels.
        """
        return [
            (1, RiskLevel.LOW),
            (2, RiskLevel.HIGH),
        ]
