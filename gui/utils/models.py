# ---
# project: ErgoMoCap
# file: models.py
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
ErgoMoCap: GUI - Backend Communication Models
---------------------------------------------
Typed Data Contracts and Structural Communication Interfaces.

This module provides immutably frozen, memory-optimized (`__slots__`) data models
to standardize communications between asynchronous backend processes, workers,
and user interface threads.

By enforcing strict type boundaries across signals and slots, this architecture
prevents thread-boundary race mutations and standardizes API contracts across
the application lifecycle.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Sequence
import numpy as np
import pandas as pd

# Import existing enums for strict typing
from gui.utils.constants import AssessmentMethod, MetricType, RiskLevel


class PlaybackState(Enum):
    """
    Tracks whether the video engine ticker is active or paused.

    Attributes:
        PLAYING (bool): The background worker processing timer tick loop is enabled.
        PAUSED (bool): The background worker parsing pipeline is halted.
    """

    PLAYING = True
    PAUSED = False


@dataclass(frozen=True, slots=True)
class FrameData:
    """
    Typed contract for sequential video frame emission pipelines.

    Encapsulates raw frame visual matrix blocks alongside contextual calculations
    and skeletal landmark parameters processed during asynchronous visual workers ticks.

    Attributes:
        image (np.ndarray): The raw multi-channel image matrix array matching OpenCV formats (BGR).
        frame_idx (int): The absolute temporal timeline sequential element integer frame index identifier.
        landmarks (list): Collection array structure holding multi-dimensional coordinate mapping elements. Defaults to empty list.
        score (int | None): The specific calculated ergonomic evaluation integer score, or None if skipped. Defaults to None.
        risk (RiskLevel | None): The qualitative risk ranking assignment context enum classification tracking value. Defaults to None.
    """

    image: np.ndarray
    frame_idx: int
    landmarks: list = field(default_factory=list)
    score: int | None = None
    risk: RiskLevel | None = None

    def to_dict(self) -> dict:
        """
        Helper for backward compatibility with dict-based consumer tracking slots.

        Flattens the structured fields data layouts directly into primitive structural
        lookup dictionaries for legacy tracking elements components.

        Returns:
            dict (dict): Composed metric values keys structure mapping frame information configurations.
        """
        return {
            "frame_idx": self.frame_idx,
            MetricType.SCORE.value: self.score if self.score else None,
            MetricType.RISK.value: self.risk.value if self.risk else None,
        }


@dataclass(frozen=True, slots=True)
class AnalysisRequest:
    """
    Typed command container parameters payload requested to run ergonomic calculations.

    Attributes:
        method (AssessmentMethod): Target metric evaluation system mapping layout configuration selection.
        export_frames (bool): Flag determining whether single annotated frame matrices are generated to disk. Defaults to False.
        data_ref (np.ndarray | Path | None): File tracking pointer reference indicating where tracking elements reside. Defaults to None.
    """

    method: AssessmentMethod
    export_frames: bool = False
    data_ref: np.ndarray | Path | None = None


@dataclass(frozen=True, slots=True)
class AnalysisResult:
    """
    Typed compilation results structural receipt dispatched back by the calculation engines.

    Attributes:
        success (bool): Operational completion assertion status flag tracking validation success.
        message (str): Explanatory execution text trace reporting diagnostics details logs metadata.
        output_path (Path | None): Systemic disk tracking target pointer path containing CSV sheets, or None. Defaults to None.
        scores (Sequence[int]): Sequential collection of the frame-by-frame computed results score integers array. Defaults to empty list.
        stats (dict[str, int]): Evaluative qualitative summary frequency grouping metadata calculation table. Defaults to empty dict.
    """

    success: bool
    message: str
    output_path: Path | None = None
    scores: Sequence[int] = field(default_factory=list)
    stats: dict[str, int] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ReportData:
    """
    Data payload model for generating standalone visual report templates sheets.

    Attributes:
        df (pd.DataFrame): Dataframe container compiling synchronized evaluation data layers parameters metrics.
        file_path (Path): System absolute path target pinpointing localized assets configurations metrics logs.
        total_frames (int): Length magnitude configuration metrics representing overall timeline size scope counts.
        average_score (float): Computed cumulative global standard score tracking mean floating-point calculations.
        summary_dict (dict): Consolidated diagnostic lookup grouping keys defining assessment distribution metadata profiles.
    """

    df: pd.DataFrame
    file_path: Path
    total_frames: int
    average_score: float
    summary_dict: dict


@dataclass(frozen=True, slots=True)
class SessionData:
    """
    Typed session parsing and directory mapping validation meta context tracking model.

    Attributes:
        name (str): Label string identifying unique target folder recording session items profiles.
        success (bool): Operational status assertion flag verifying disk structure lookup results mappings.
        message (str): Log tracing diagnostic notification description text parameters.
        csv_path (Path | None): Absolute system folder mapping target identifying joint coordinate files, or None. Defaults to None.
        video_paths (list[str]): Sequential listing array containing absolute string links paths pointing to media files. Defaults to empty list.
        loaded (bool): Initialization evaluation track status monitoring flag component. Defaults to False.
    """

    name: str
    success: bool
    message: str
    csv_path: Path | None = None
    video_paths: list[str] = field(default_factory=list)
    loaded: bool = False

    @property
    def is_ready(self) -> bool:
        """
        Convenience checking query interface supporting transactional interface interactive states enablement.

        Returns:
            bool (bool): True if session paths resolution criteria parameters components matches healthy targets.
        """
        return self.loaded and self.csv_path is not None


@dataclass(frozen=True, slots=True)
class VideoLoadRequest:
    """
    Typed parameter targets initialization packet dispatched to establish background video engine playback context.

    Attributes:
        path (Path): Absolute system directory file target locator tracking media recording structures source assets.
        scores (list[int]): Sequential array indices carrying calculated timeline point score information markers. Defaults to empty list.
        thresholds (list[tuple[int, RiskLevel]]): Structural intervals matrix tracking score-to-level translation limits. Defaults to empty list.
    """

    path: Path
    scores: list[int] = field(default_factory=list)
    thresholds: list[tuple[int, RiskLevel]] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class VideoLoadResult:
    """
    Typed structural verification feedback payload reporting media worker initialization context success parameters.

    Attributes:
        success (bool): Verification parameter monitoring success of media asset loading pipelines.
        message (str): Logging trace update text string specifying context setup diagnostics parameters.
        video_paths (list[str]): Discovered system target files paths listings array tracks structure. Defaults to empty list.
        loaded (bool): State indicator monitoring internal setup verification completeness metrics. Defaults to False.
    """

    success: bool
    message: str
    video_paths: list[str] = field(default_factory=list)
    loaded: bool = False


@dataclass(frozen=True, slots=True)
class VideoPosition:
    """
    Typed real-time positional coordinate update tracking payload enabling cross-thread synchronization widgets interfaces.

    Attributes:
        current_frame (int): Absolute playback timeline frame positional index pointer integer position.
        total_frames (int): Total bounded capacity layout limit tracking metric representing files stream dimension length.
    """

    current_frame: int
    total_frames: int


class VideoCommand(Enum):
    """
    Transport action command primitive indicators navigating background worker media rendering buffers indices.

    Attributes:
        TOGGLE (auto): Reverses running execution playback state metrics tracking switches.
        STEP_FORWARD (auto): Shifts background rendering arrays pointers ahead by exactly one index unit frame.
        STEP_BACKWARD (auto): Regresses active frame buffers lookups markers back by exactly one frame iteration unit.
        SEEK (auto): Forces operational media decoders directly onto target localized coordinate position bounds.
    """

    TOGGLE = auto()
    STEP_FORWARD = auto()
    STEP_BACKWARD = auto()
    SEEK = auto()


@dataclass(frozen=True, slots=True)
class VideoControl:
    """
    Unified execution envelope routing atomic layout command structures directly down into background transport streams.

    Attributes:
        command (VideoCommand): Action type designation key identifier tracking intent options mappings.
        target_frame (int | None): Direct specific sequence coordinate framework positional index location parameters, or None. Defaults to None.
    """

    command: VideoCommand
    target_frame: int | None = None


@dataclass(frozen=True, slots=True)
class FramesExportResult:
    """
    Typed tracking receipt mapping operational metrics recording asynchronous batch frame processing operations.

    Attributes:
        success (bool): Execution tracking parameters completion validation monitoring status flag.
        message (str): Text specification string details log tracing diagnostic parameters notes outputs.
        frames_paths (str): Absolute file target path string tracking localized assembly folders directories layouts. Defaults to empty string.
    """

    success: bool
    message: str
    frames_paths: str = field(default_factory=str)


@dataclass(frozen=True, slots=True)
class ReportExportRequest:
    """
    Unified command request container compiling raw visualization elements to generate printable document formats.

    Attributes:
        save_path (Path): Absolute system destination output file locator target route specifications tracking.
        chart_data (bytes): Byte array buffer container streams processing embedded static graphics layouts parameters.
    """

    save_path: Path
    chart_data: bytes


@dataclass(frozen=True, slots=True)
class ReportExportResult:
    """
    Typed tracking response envelope returning results from background document generation sub-workers.

    Attributes:
        success (bool): Transaction completion state verification parameters flag tracking status indicator.
        message (str): Technical context text trace layout providing detailed internal log strings configurations.
        report_path (str): Final target localized storage path string tracking generated report elements on disk. Defaults to empty string.
    """

    success: bool
    message: str
    report_path: str = field(default_factory=str)


@dataclass(frozen=True, slots=True)
class ErrorInfo:
    """
    Simplified structured telemetry error container packet optimized for cross-thread exception warning widgets deployment.

    Attributes:
        title (str): Bold notification dialogue header summary label classification metric context text string.
        message (str): Core execution stack exceptions context message descriptive explanation logs parameters.
    """

    title: str
    message: str
