# ---
# project: ErgoMoCap
# file: force_adapter_test.py
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
import numpy as np
from calculators.adapters.force_adapter import ForceDataAdapter


@pytest.fixture
def mock_mocap_df():
    """Provides a basic MoCap DataFrame with 10 frames."""
    return pd.DataFrame({"frame": np.arange(10), "data": np.random.rand(10)})


@pytest.fixture
def mock_force_csv_data(tmp_path):
    """Creates a temporary CSV file to simulate force sensor output."""
    csv_path = tmp_path / "force_data.csv"
    df = pd.DataFrame(
        {
            "timestamp": [0.0, 0.5, 1.0, 1.5, 2.0],
            "force_n": [0.0, 20.0, 25.0, 5.0, 30.0],
        }
    )
    df.to_csv(csv_path, index=False)
    return str(csv_path)


def test_initialization(mock_mocap_df, mock_force_csv_data):
    """Test that the adapter loads CSV data correctly on init."""
    adapter = ForceDataAdapter(mock_mocap_df, mock_force_csv_data, fps=30)
    assert isinstance(adapter.force_raw, pd.DataFrame)
    assert adapter.fps == 30
    assert "force_n" in adapter.force_raw.columns


def test_interpolate_force_with_timestamps(mock_mocap_df, mock_force_csv_data):
    """Exercises the 'timestamp' in columns branch (Line 42)."""
    # Add explicit timestamps to mocap
    mock_mocap_df["timestamp"] = np.linspace(0, 2.0, 10)
    adapter = ForceDataAdapter(mock_mocap_df, mock_force_csv_data)

    synced = adapter._interpolate_force()
    assert len(synced) == 10
    assert isinstance(synced, np.ndarray)
    assert synced.dtype == np.float64


def test_interpolate_force_no_timestamps(mock_mocap_df, mock_force_csv_data):
    """Exercises the FPS-based timestamp calculation branch (Line 45)."""
    # mocap_df has no 'timestamp' column
    adapter = ForceDataAdapter(mock_mocap_df, mock_force_csv_data, fps=10)

    synced = adapter._interpolate_force()
    # 10 frames at 10 fps = timestamps [0.0, 0.1, ... 0.9]
    assert len(synced) == 10


def test_identify_pulses_standard(mock_mocap_df, mock_force_csv_data):
    """Tests pulse labeling logic with clear starts and ends (Lines 64-69)."""
    adapter = ForceDataAdapter(mock_mocap_df, mock_force_csv_data)
    # 2 pulses: indices 1-2 and index 4
    force_array = np.array([0.0, 15.0, 15.0, 0.0, 20.0, 0.0])

    action_ids = adapter._identify_pulses(force_array, threshold=10.0)

    expected = np.array([0, 1, 1, 0, 2, 0])
    np.testing.assert_array_equal(action_ids, expected)


def test_identify_pulses_hanging_edge_case(mock_mocap_df, mock_force_csv_data):
    """Exercises the edge case where a pulse never ends (Lines 72-74)."""
    adapter = ForceDataAdapter(mock_mocap_df, mock_force_csv_data)
    # Pulse starts at index 2 and continues to the end
    force_array = np.array([0.0, 0.0, 50.0, 50.0, 50.0])

    action_ids = adapter._identify_pulses(force_array, threshold=10.0)

    expected = np.array([0, 0, 1, 1, 1])
    np.testing.assert_array_equal(action_ids, expected)


def test_identify_pulses_no_activity(mock_mocap_df, mock_force_csv_data):
    """Tests behavior when no force exceeds threshold."""
    adapter = ForceDataAdapter(mock_mocap_df, mock_force_csv_data)
    force_array = np.array([1.0, 2.0, 1.0])

    action_ids = adapter._identify_pulses(force_array, threshold=10.0)

    assert np.all(action_ids == 0)


def test_sync_and_tag_integration(mock_mocap_df, mock_force_csv_data):
    """Tests the full public pipeline (Lines 22-33)."""
    adapter = ForceDataAdapter(mock_mocap_df, mock_force_csv_data, fps=5)

    result_df = adapter.sync_and_tag()

    assert "force_n" in result_df.columns
    assert "action_id" in result_df.columns
    assert len(result_df) == len(mock_mocap_df)
    # Ensure action_id is populated (based on mock_force_csv_data having values > 10)
    assert result_df["action_id"].max() > 0


def test_identify_pulses_at_threshold(mock_mocap_df, mock_force_csv_data):
    """Boundary test: exactly at threshold should not be active."""
    adapter = ForceDataAdapter(mock_mocap_df, mock_force_csv_data)
    force_array = np.array([10.0, 10.0001])

    action_ids = adapter._identify_pulses(force_array, threshold=10.0)

    assert action_ids[0] == 0
    assert action_ids[1] == 1
