# ---
# project: ErgoMoCap
# file: utils.py
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
ErgoMoCap: Utility Module
---------------------------------------
Helper functions for session data management and report generation. (as of now)

This module provides utility functions to support the ergonomic analysis workflow,
specifically focusing on the transformation of raw session data into actionable
insights. It includes logic for:

- **Report Generation**: Creating Markdown-formatted summaries of assessment sessions.
- **Metric Aggregation**: Calculating dynamic averages from `pandas.DataFrame`
  objects to identify postural trends.
- **Naming Standardization**: Constructing consistent column identifiers based
  on anatomical parts, metric types, and assessment methods (RULA/REBA).

These utilities ensure a unified data schema between the backend processing
logic and the frontend reporting interface.
"""

from pathlib import Path
from typing import Any

import pandas as pd

from gui.utils.constants import AssessmentMethod, BodyPart, MetricType


def generate_markdown_report(
    report_path: str | Path, all_data_records: list[dict[str, Any]]
) -> None:
    """
    Generates a Markdown report summarizing the assessment session.

    Args:
        report_path (str | Path): Destination path for the `.md` file.
        all_data_records (list[dict[str, Any]]): A `list` of all frame dictionaries collected during the session.

    Returns:
        None (None): Writes the report to the file system.
    """
    # TODO generate a table with the averages or remove this from backend
    pass


def get_dynamic_metrics(
    df: pd.DataFrame, metric_type: MetricType, method: AssessmentMethod
) -> list[tuple[str, str]]:
    """
    Calculates session averages using standardized column naming.

    Scans the `pandas.DataFrame` for columns ending in the standard score/method suffix
    and calculates their mean values to provide an overview of postural trends.

    Args:
        df (pandas.DataFrame): The full session data loaded into a `pandas.DataFrame`.
        metric_type (MetricType): The [MetricType][gui.utils.constants.MetricType] to filter by.
        method (AssessmentMethod): The [AssessmentMethod][gui.utils.constants.AssessmentMethod] used (e.g., RULA/REBA).

    Returns:
        list[tuple[str, str]]: A `list` of (`str`, `str`) tuples containing (District_Name, Average_Score).
    """
    rows: list[tuple[str, str]] = []

    cleaned_df = df.drop(columns=[MetricType.RISK.value, MetricType.SCORE.value])

    for col in cleaned_df.columns:
        # display_name = col.replace("_", " ").title() TODO review this
        display_name = str(col)
        avg_value = df[col].mean()
        rows.append((display_name, f"{avg_value:.2f}"))

    # print(df.columns, df.head(2), f"GET DYNAMIC METRICS ROWS {rows}", "\n") TODO print_reactivate
    # print(df.columns, "SCORE COLS\n") TODO print_reactivate
    return rows


def resolve_column_name(
    part: BodyPart, metric: MetricType, method: AssessmentMethod
) -> str:
    """
    Constructs a standardized database/CSV column name.

    Args:
        part (BodyPart): The anatomical [BodyPart][gui.utils.constants.BodyPart] Enum.
        metric (MetricType): The [MetricType][gui.utils.constants.MetricType] Enum (e.g., angle, score).
        method (AssessmentMethod): The [AssessmentMethod][gui.utils.constants.AssessmentMethod] Enum (e.g., reba).

    Returns:
        str (str): A `lower_snake_case` string in the format `[part]_[metric]_[method]`.
    """
    return f"{part.value}_{metric.value}_{method.value}"
