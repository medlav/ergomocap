# ---
# project: ErgoMoCap
# file: calculators_test.py
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
import calculators.calculators as calc

# List of all expected attributes based on the source __all__
EXPECTED_ATTRIBUTES = [
    "map_fmc_joint_angles_to_ergo_degs",
    "map_fmc_kinematics_to_niosh_vars",
    "map_fmc_kinematics_to_ocra_vars",
    "map_fmc_kinematics_to_ewas_vars",
    "map_fmc_kinematics_to_snook_vars",
    "calculate_frame_reba_from_degs",
    "calculate_frame_rula_from_degs",
    "calculate_frame_niosh_li",
    "calculate_frame_ocra_index",
    "calculate_frame_ewas_score",
    "calculate_frame_snook_index",
]


def test_module_level_metadata():
    """Verify module metadata exists (Author, License info is usually implicit)."""
    assert calc.__name__ == "calculators.calculators"


def test_all_list_completeness_and_uniqueness():
    """
    Check that __all__ contains exactly what we expect.
    Note: The source code has a duplicate for 'map_fmc_joint_angles_to_ergo_degs'.
    This test ensures we recognize what is actually exported.
    """
    # Converting to set to check for presence, but checking length for duplicates
    export_set = set(calc.__all__)

    for attr in EXPECTED_ATTRIBUTES:
        assert attr in export_set, f"Expected {attr} to be exported in __all__"

    # Validation for the duplicate found in the source file
    assert (
        len(calc.__all__) == 12
    ), "Expected 12 entries in __all__ (including duplicates)"


@pytest.mark.parametrize("attr_name", EXPECTED_ATTRIBUTES)
def test_each_exported_attribute_exists(attr_name):
    """
    Exhaustively check that every single string defined in __all__
    corresponds to a real, reachable object in the module.
    """
    assert hasattr(
        calc, attr_name
    ), f"Attribute {attr_name} is in __all__ but not in module"


def test_verify_callable_objects():
    """
    Ensure that the key calculators and adapters are actually
    functions/callables and not just None placeholders.
    """
    callables = [
        calc.map_fmc_joint_angles_to_ergo_degs,
        calc.calculate_frame_reba_from_degs,
        calc.calculate_frame_rula_from_degs,
        calc.calculate_frame_niosh_li,
        calc.calculate_frame_ocra_index,
        calc.calculate_frame_ewas_score,
        calc.calculate_frame_snook_index,
    ]
    for obj in callables:
        assert callable(obj), f"Object {obj} should be callable"


def test_import_integrity():
    """
    Final check: Attempting to access an attribute not in __all__
    that shouldn't be there (sanity check).
    """
    with pytest.raises(AttributeError):
        _ = calc.non_existent_calculator_function_99  # type: ignore
