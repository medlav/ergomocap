# ---
# project: ErgoMoCap
# file: conversion_utils.py
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
ErgoMoCap: Measurement Conversion Utilities
-------------------------------------------
Unit normalization and conversion engine for anthropometric and environmental data.

This module provides a robust set of utilities for converting measurements between
metric and imperial systems. It uses a base-unit normalization strategy (cm for
length, kg for mass, and L for volume) to ensure precision and simplify the
internal conversion logic. These utilities are essential for processing
user-provided physical attributes and environmental parameters within the
ergonomic analysis pipeline.

Key conversion categories:
- **Length**: Supports metric (m, cm, mm) and imperial (inch, foot, yard) units.
- **Mass**: Supports metric (kg, g) and imperial (lb, oz) units.
- **Volume**: Supports metric (L, ml) and imperial (gal, qt) units.
- **Temperature**: Provides precision scaling between Celsius, Fahrenheit, and Kelvin.
"""

from typing import Literal

# --- UNIT DATA (Normalized to Metric base units: cm, kg, L) ---
# Length: Base is cm
LENGTH_FACTORS = {
    "m": 100.0,
    "cm": 1.0,
    "mm": 0.1,
    "inch": 2.54,
    "foot": 30.48,
    "yard": 91.44,
}

# Mass: Base is kg
MASS_FACTORS = {"kg": 1.0, "g": 0.001, "lb": 0.45359237, "oz": 0.0283495}

# Volume: Base is L
VOLUME_FACTORS = {"l": 1.0, "ml": 0.001, "gal": 3.78541, "qt": 0.946353}


def convert_length(value: float, pre_unit: str, post_unit: str) -> float:
    """
    Converts a length value from one unit to another using a metric base-cm scale.

    Args:
        value (float): The numeric value to be converted.
        pre_unit (str): The current unit of the value (e.g., 'm', 'cm', 'inch', 'foot').
        post_unit (str): The target unit for the conversion (e.g., 'mm', 'yard', 'cm').

    Returns:
        float: The converted value, rounded to 4 decimal places.

    Raises:
        ValueError: If either pre_unit or post_unit is not found in the LENGTH_FACTORS registry.
    """
    if pre_unit not in LENGTH_FACTORS or post_unit not in LENGTH_FACTORS:
        raise ValueError(
            f"Unsupported length unit. Supported: {list(LENGTH_FACTORS.keys())}"
        )

    # Convert input to cm, then cm to post_unit
    value_in_cm = value * LENGTH_FACTORS[pre_unit]
    result = value_in_cm / LENGTH_FACTORS[post_unit]
    return round(result, 4)


def convert_mass(value: float, pre_unit: str, post_unit: str) -> float:
    """
    Converts a mass/weight value from one unit to another using a metric base-kg scale.

    Args:
        value (float): The numeric value to be converted.
        pre_unit (str): The current unit of the value (e.g., 'kg', 'lb', 'oz').
        post_unit (str): The target unit for the conversion (e.g., 'g', 'kg', 'lb').

    Returns:
        float: The converted value, rounded to 4 decimal places.

    Raises:
        ValueError: If either pre_unit or post_unit is not found in the MASS_FACTORS registry.
    """
    if pre_unit not in MASS_FACTORS or post_unit not in MASS_FACTORS:
        raise ValueError(
            f"Unsupported mass unit. Supported: {list(MASS_FACTORS.keys())}"
        )

    value_in_kg = value * MASS_FACTORS[pre_unit]
    result = value_in_kg / MASS_FACTORS[post_unit]
    return round(result, 4)


def convert_temp(
    value: float, pre_unit: Literal["c", "f", "k"], post_unit: Literal["c", "f", "k"]
) -> float:
    """
    Converts a temperature value between Celsius, Fahrenheit, and Kelvin scales.

    Args:
        value (float): The numeric temperature to be converted.
        pre_unit (Literal['c', 'f', 'k']): The source scale ('c' for Celsius, 'f' for Fahrenheit, 'k' for Kelvin).
        post_unit (Literal['c', 'f', 'k']): The target scale for the conversion.

    Returns:
        float: The converted temperature, rounded to 2 decimal places.

    Raises:
        ValueError: If an unsupported scale is provided.
    """
    # 1. Normalize to Celsius
    if pre_unit == "c":
        temp_c = value
    elif pre_unit == "f":
        temp_c = (value - 32) * 5 / 9
    elif pre_unit == "k":
        temp_c = value - 273.15
    else:
        raise ValueError("Unit must be 'c', 'f', or 'k'")

    # 2. Convert Celsius to target
    if post_unit == "c":
        return round(temp_c, 2)
    if post_unit == "f":
        return round((temp_c * 9 / 5) + 32, 2)
    if post_unit == "k":
        return round(temp_c + 273.15, 2)

    return round(temp_c, 2)


def convert_volume(value: float, pre_unit: str, post_unit: str) -> float:
    """
    Converts a volume value from one unit to another using a metric base-L scale.

    Args:
        value (float): The numeric volume to be converted.
        pre_unit (str): The current unit of the value (e.g., 'l', 'ml', 'gal').
        post_unit (str): The target unit for the conversion (e.g., 'qt', 'l', 'ml').

    Returns:
        float: The converted value, rounded to 4 decimal places.

    Raises:
        ValueError: If either pre_unit or post_unit is not found in the VOLUME_FACTORS registry.
    """
    if pre_unit not in VOLUME_FACTORS or post_unit not in VOLUME_FACTORS:
        raise ValueError(
            f"Unsupported volume unit. Supported: {list(VOLUME_FACTORS.keys())}"
        )

    value_in_l = value * VOLUME_FACTORS[pre_unit]
    result = value_in_l / VOLUME_FACTORS[post_unit]
    return round(result, 4)
