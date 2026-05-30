# ---
# project: ErgoMoCap
# file: report_strategies.py
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
ErgoMoCap: Report Strategies
----------------------------
Strategy Pattern Implementation for Multi-Method Ergonomic Reporting.

This module defines the architectural contract and concrete implementations for
transforming raw calculation data into display-ready structures. It utilizes the
Strategy design pattern to decouple the [TableReportWidget][gui.widgets.table_report_widget.TableReportWidget]
from specific assessment logic (RULA, REBA, etc.).

Each strategy is responsible for mapping internal dictionary keys to human-readable
labels and defining the visual hierarchy of the generated report tables.

Key Components:
    * `ResultRow`: The atomic data structure representing a table entry.
    * `ReportStrategy`: The `Protocol` defining the required interface for all calculators.
    * `RulaStrategy`: Formatting logic for Rapid Upper Limb Assessment.
    * `RebaStrategy`: Formatting logic for Rapid Entire Body Assessment.
"""

from typing import Any, Protocol
from dataclasses import dataclass


# --- 1. The Strategy Interface ---


@dataclass
class ResultRow:
    """
    Standardized data structure for a report row within the ErgoMoCap project.

    This dataclass encapsulates the visual and structural properties of a single row in
    the analysis report tables located in the [gui](reference.md#gui) module.

    Attributes:
        label (str): The display name of the ergonomic metric.
        value (Any): The actual measurement or score associated with the metric.
        is_header (bool): Whether the row acts as a category separator. Defaults to `False`.
        is_critical (bool): Whether the value represents a final risk score requiring highlighting. Defaults to `False`.
        is_angle (bool): Whether the value should be formatted with a degree symbol. Defaults to `False`.
    """

    label: str
    value: Any
    is_header: bool = False
    is_critical: bool = False
    is_angle: bool = False


class ReportStrategy(Protocol):
    """
    Protocol defining how to transform raw data into report rows.

    Any concrete strategy implemented in [calculators](reference.md#calculators) must adhere to
    this interface to ensure compatibility with [TableReportWidget][gui.widgets.table_report_widget.TableReportWidget].

    Attributes:
        name (str): The display name of the ergonomic assessment method (e.g., "RULA").

    Methods:
        format: Transform raw data into a list of report rows.
    """

    name: str

    def format(self, data: dict[str, Any]) -> list[ResultRow]:
        """
        Transform raw data into a list of report rows.

        Args:
            data (dict[str, Any]): Dictionary containing raw calculation results.

        Returns:
            list[ResultRow] (list[ResultRow]): A list of formatted rows for table rendering.
        """
        ...


# --- 2. Concrete Strategies ---


class RulaStrategy:
    """
    Transform raw ergonomic data into a list of formatted RULA report rows.

    This strategy maps keys specific to the Rapid Upper Limb Assessment (RULA)
    protocol into a structured visual format.

    Attributes:
        name (str): The identifier "RULA".

    Methods:
        format: Format RULA specific data into table rows.
    """

    name = "RULA"

    def format(self, data: dict[str, str]) -> list[ResultRow]:
        """
        Format RULA specific data into table rows.

        Args:
            data (dict[str, str]): A dictionary containing RULA specific keys such as
                `Upper_Arm_Score_RULA` and `Final_Score_RULA`.

        Returns:
            list[ResultRow] (list[ResultRow]): A `list` of [ResultRow][gui.core.report_strategies.ResultRow]
                objects structured for the RULA table layout.
        """

        rows = [
            ResultRow("Group A (Upper Limbs)", "---", is_header=True),
            ResultRow("Upper Arm", data.get("Upper_Arm_Score_RULA", "-")),
            ResultRow("Wrist", data.get("Wrist_Score_RULA", "-")),
            ResultRow("Raw Score A", data.get("Score_A_RULA", "-")),
            ResultRow("Group B (Neck/Trunk)", "---", is_header=True),
            ResultRow("Neck", data.get("Neck_Score_RULA", "-")),
            ResultRow("Trunk", data.get("Trunk_Score_RULA", "-")),
            ResultRow(
                "FINAL RULA", data.get("Final_Score_RULA", "-"), is_critical=True
            ),
        ]
        return rows


class RebaStrategy:
    """
    Transform raw ergonomic data into a list of formatted REBA report rows.

    This strategy maps keys specific to the Rapid Entire Body Assessment (REBA)
    protocol into a structured visual format.

    Attributes:
        name (str): The identifier "REBA".

    Methods:
        format: Format RULA specific data into table rows.
    """

    name = "REBA"

    def format(self, data: dict[str, str]) -> list[ResultRow]:
        """
        Format REBA specific data into table rows.

        Args:
            data (dict[str, str]): A dictionary containing REBA specific keys such as
                `Neck_Score_REBA` and `Final_Score_REBA`.

        Returns:
            list[ResultRow] (list[ResultRow]): A `list` of [ResultRow][gui.core.report_strategies.ResultRow]
                objects structured for the REBA table layout.
        """
        rows = [
            ResultRow("Group A (Neck, Trunk, legs)", "---", is_header=True),
            ResultRow("Neck", data.get("Neck_Score_REBA", "-")),
            ResultRow("Trunk", data.get("Trunk_Score_REBA", "-")),
            ResultRow("Legs", data.get("Legs_Score_REBA", "-")),
            ResultRow("Group B (Upper Limbs)", "---", is_header=True),
            ResultRow("Upper Arm", data.get("Upper_Arm_Score_REBA", "-")),
            ResultRow("Lower Arm", data.get("Lower_Arm_Score_REBA", "-")),
            ResultRow("Wrist", data.get("Wrist_Score_REBA", "-")),
            ResultRow(
                "FINAL REBA", data.get("Final_Score_REBA", "-"), is_critical=True
            ),
        ]

        return rows


class NIOSHStrategy: ...  # TODO Next Calculator


class OCRAStrategy: ...  # TODO Next Calculator
