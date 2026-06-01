# ---
# project: ErgoMoCap
# file: force_adapter.py
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
TODO make docstring
"""

import pandas as pd
import numpy as np


class ForceDataAdapter:
    """
    Adapter to synchronize high-frequency force sensor data with MoCap frames.

    This implementation resolves Pylance 'reportArgumentType' by enforcing
    explicit NumPy float64 casting for the interpolation engine. It ensures that
    disparate sampling rates between force sensors and motion capture systems
    are aligned onto a unified temporal grid.

    Attributes:
        mocap_df (pandas.DataFrame): The primary motion capture data container.
        force_raw (pandas.DataFrame): Raw force data loaded from the provided CSV path.
        fps (int): Frames per second of the motion capture data, used for timeline generation.

    Methods:
        sync_and_tag: Main entry point to align force data with MoCap timestamps.
        _interpolate_force: Performs linear interpolation using explicitly casted NumPy arrays.
        _identify_pulses: Groups continuous exertions into unique Action IDs.
    """

    def __init__(self, mocap_df: pd.DataFrame, force_csv_path: str, fps: int = 30):
        """
        Initialize the adapter with MoCap data and force sensor file path.

        Args:
            mocap_df (pandas.DataFrame): The source motion capture data.
            force_csv_path (str): Local system path to the force sensor CSV file.
            fps (int): Sampling rate of the MoCap system. Defaults to 30.

        Returns:
            None (None): Initializes the instance attributes.
        """
        self.mocap_df = mocap_df
        # Load force data immediately into a DataFrame
        self.force_raw = pd.read_csv(force_csv_path)
        self.fps = fps

    def sync_and_tag(self) -> pd.DataFrame:
        """
        Main entry point to align force data with MoCap timestamps.

        This method orchestrates the temporal interpolation of force values and
        the subsequent identification of discrete physical actions based on
        force thresholds.

        Returns:
            mocap_df (pandas.DataFrame): The modified DataFrame containing "force_n" and "action_id" columns.
        """
        # 1. Temporal Synchronization
        synced_force = self._interpolate_force()

        # 2. Add to MoCap DataFrame
        self.mocap_df["force_n"] = synced_force
        self.mocap_df["action_id"] = self._identify_pulses(synced_force)

        return self.mocap_df

    def _interpolate_force(self) -> np.ndarray:
        """
        Performs linear interpolation using explicitly casted NumPy arrays.

        Resolves: reportArgumentType and reportCallIssue by ensuring all inputs
        to `numpy.interp` are `numpy.float64`. It maps the high-frequency sensor
        time series onto the MoCap timeline.

        Returns:
            interp_values (numpy.ndarray): The force values interpolated to match MoCap frame timestamps.
        """
        # Define target timestamps (X axis for interpolation)
        if "timestamp" in self.mocap_df.columns:
            target_times = self.mocap_df["timestamp"].to_numpy(dtype=np.float64)
        else:
            target_times = np.arange(len(self.mocap_df), dtype=np.float64) / self.fps

        # Define source timestamps and values (XP and FP axes)
        # We use .to_numpy() instead of .values to guarantee the correct array protocol
        sensor_times = self.force_raw["timestamp"].to_numpy(dtype=np.float64)
        sensor_values = self.force_raw["force_n"].to_numpy(dtype=np.float64)

        # np.interp(x, xp, fp) -> maps target_times onto the sensor's timeline
        return np.interp(target_times, sensor_times, sensor_values)

    def _identify_pulses(
        self, force_array: np.ndarray, threshold: float = 10.0
    ) -> np.ndarray:
        """
        Groups continuous exertions into unique Action IDs for Section 2.

        Identifies segments where force exceeds a specific threshold and assigns
        a unique integer ID to each contiguous block (pulse). This allows for
        per-action ergonomic analysis.

        Args:
            force_array (numpy.ndarray): Array of synchronized force values in Newtons.
            threshold (float): Force value above which an action is considered "active". Defaults to 10.0.

        Returns:
            action_ids (numpy.ndarray): An array of `int32` IDs where 0 is idle and N is the action index.
        """
        is_active = (force_array > threshold).astype(np.int32)

        # Use prepend=0 to keep the resulting diff array the same length as force_array
        changes = np.diff(is_active, prepend=0)

        starts = np.where(changes == 1)[0]
        ends = np.where(changes == -1)[0]

        action_ids = np.zeros(len(force_array), dtype=np.int32)

        # Zip pulse start/end pairs to label action windows
        for i, (start, end) in enumerate(zip(starts, ends), start=1):
            action_ids[start:end] = i

        # Edge Case: Pulse starts at the very end of the recording and never drops
        if len(starts) > len(ends):
            action_ids[starts[-1] :] = len(starts)

        return action_ids
