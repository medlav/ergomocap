# ---
# project: ErgoMoCap
# file: conversion_utils_test.py
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
from calculators.calculators_utils.conversion_utils import (
    convert_length,
    convert_mass,
    convert_temp,
    convert_volume,
    LENGTH_FACTORS,
    MASS_FACTORS,
    VOLUME_FACTORS,
)

# --- LENGTH CONVERSION TESTS ---


@pytest.mark.parametrize(
    "value, pre, post, expected",
    [
        (1, "m", "cm", 100.0),
        (100, "cm", "m", 1.0),
        (1, "inch", "cm", 2.54),
        (1, "foot", "inch", 12.0),
        (1, "yard", "foot", 3.0),
        (10, "mm", "cm", 1.0),
        (0, "m", "inch", 0.0),
    ],
)
def test_convert_length_success(value, pre, post, expected):
    """Test standard length conversions and rounding."""
    assert convert_length(value, pre, post) == expected


def test_convert_length_invalid_unit():
    """Test that unsupported length units raise ValueError (Lines 55-57)."""
    with pytest.raises(ValueError, match="Unsupported length unit"):
        convert_length(10, "lightyear", "m")
    with pytest.raises(ValueError, match="Unsupported length unit"):
        convert_length(10, "m", "pixel")


# --- MASS CONVERSION TESTS ---


@pytest.mark.parametrize(
    "value, pre, post, expected",
    [
        (1, "kg", "g", 1000.0),
        (1000, "g", "kg", 1.0),
        (1, "lb", "kg", 0.4536),  # Rounded to 4 places
        (16, "oz", "lb", 1.0),
        (2.20462, "lb", "kg", 1.0),
    ],
)
def test_convert_mass_success(value, pre, post, expected):
    """Test standard mass conversions and rounding."""
    assert convert_mass(value, pre, post) == expected


def test_convert_mass_invalid_unit():
    """Test that unsupported mass units raise ValueError (Lines 83-85)."""
    with pytest.raises(ValueError, match="Unsupported mass unit"):
        convert_mass(10, "stone", "kg")


# --- TEMPERATURE CONVERSION TESTS ---


@pytest.mark.parametrize(
    "value, pre, post, expected",
    [
        # Celsius to others
        (0, "c", "c", 0.0),
        (0, "c", "f", 32.0),
        (0, "c", "k", 273.15),
        # Fahrenheit to others
        (32, "f", "c", 0.0),
        (212, "f", "c", 100.0),
        (32, "f", "k", 273.15),
        # Kelvin to others
        (273.15, "k", "c", 0.0),
        (0, "k", "c", -273.15),
        (300, "k", "f", 80.33),
    ],
)
def test_convert_temp_success(value, pre, post, expected):
    """Test all temperature scales and branches (Lines 111-125)."""
    assert convert_temp(value, pre, post) == expected


def test_convert_temp_invalid_unit():
    """Test invalid temperature unit handling (Line 119)."""
    # Using type ignore or casting because Literal would usually catch this in IDEs
    with pytest.raises(ValueError, match="Unit must be 'c', 'f', or 'k'"):
        convert_temp(100, "rankine", "c")  # type: ignore


def test_convert_temp_post_unit_fallback():
    """Ensure code handles the final return if no post_unit matches (Line 127)."""
    # This covers the edge case if logic somehow bypasses the if/elif for post_unit
    assert convert_temp(10, "c", "unknown") == 10.0  # type: ignore


# --- VOLUME CONVERSION TESTS ---


@pytest.mark.parametrize(
    "value, pre, post, expected",
    [
        (1, "l", "ml", 1000.0),
        (1, "gal", "l", 3.7854),
        (4, "qt", "gal", 1.0),
        (500, "ml", "l", 0.5),
    ],
)
def test_convert_volume_success(value, pre, post, expected):
    """Test standard volume conversions and rounding."""
    assert convert_volume(value, pre, post) == expected


def test_convert_volume_invalid_unit():
    """Test that unsupported volume units raise ValueError (Lines 149-151)."""
    with pytest.raises(ValueError, match="Unsupported volume unit"):
        convert_volume(1, "pint", "l")


# --- DATA INTEGRITY TESTS ---


def test_factors_dictionaries_not_empty():
    """Ensure the registry dictionaries are populated."""
    assert len(LENGTH_FACTORS) > 0
    assert len(MASS_FACTORS) > 0
    assert len(VOLUME_FACTORS) > 0
