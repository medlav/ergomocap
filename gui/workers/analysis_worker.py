# ---
# project: ErgoMoCap
# file: analysis_worker.py
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
ErgoMoCap: Analysis Engine Worker
---------------------------------
Asynchronous Processing Core Wrapper for Ergonomic Calculations.

This module implements the `AnalysisWorker`, a specialized background execution
component designed to run within a dedicated worker thread. It decouples long-running
frame processing loops, adapter transformations, and system file I/O operations
from the primary user interface layer.

By encapsulating the synchronous [AnalysisEngine][gui.core.analysis_engine.AnalysisEngine],
the worker handles dispatch requests gracefully using Qt's cross-thread signal slot matrix
and dispatches typed structural analysis receipts upon operation boundaries.
"""

from pathlib import Path
from typing import Union
import numpy as np
import pandas as pd

from PySide6.QtCore import QObject, Signal, Slot

# Internal Imports
from gui.core.analysis_engine import AnalysisEngine
from gui.core.calculators_adapter import BaseErgoAdapter
from gui.utils.app_paths import ErgoPaths
from gui.utils.constants import AssessmentMethod, MetricType, RiskLevel
from gui.utils.models import AnalysisResult

from gui.utils.logger import logger


class AnalysisWorker(QObject):
    """
    Stateful worker managing background ergonomic calculations and file serialization.

    This component runs inside its own dedicated worker thread managed by the application backend.
    It provisions an internal `AnalysisEngine` instance, extracts programmatic tools via
    external methodology adapters, and updates application state domains via asynchronous signals.

    Attributes:
        finished (Signal): Signal emitted on calculation cycle completions tracking structural receipts ([AnalysisResult][gui.utils.models.AnalysisResult]).
        engine (AnalysisEngine): Core non-blocking calculation engine execution instance.
        _pending_data (pandas.DataFrame | numpy.ndarray | None): Temporary storage buffer for input metrics queued before thread execution.
        _pending_adapter (BaseErgoAdapter | None): Temporary storage buffer for the methodology adapter queued before thread execution.
        _pending_method (AssessmentMethod | None): Temporary storage buffer for the assessment protocol queued before thread execution.

    Methods:
        run: Parameterless entry point for queued execution on the worker thread.
        start_analysis: Thread-safe public entry execution slot accepting runtime processing parameters.
    """

    finished = Signal(AnalysisResult)

    def __init__(self) -> None:
        """
        Initializes the `AnalysisWorker` component.

        Sets up the base QObject infrastructure, allocates the structural computational core logic engine,
        and prepares internal storage buffers for asynchronous parameter queuing.

        Returns:
            None (None): The return value is always None.
        """
        super().__init__()
        self.engine: AnalysisEngine = AnalysisEngine()

        # Pending data for async execution (bypasses Qt meta-type serialization)
        self._pending_data: Union[pd.DataFrame, np.ndarray, None] = None
        self._pending_adapter: Union[BaseErgoAdapter, None] = None
        self._pending_method: Union[AssessmentMethod, None] = None

    def run(self) -> None:
        """
        Parameterless entry point for queued execution on the worker thread.

        Extracts runtime parameters from internal staging buffers, clears references to free memory,
        and delegates execution to the core analysis routine. This design bypasses Qt's meta-type
        serialization constraints for complex objects like pandas DataFrames.

        Returns:
            None (None): Delegates to `start_analysis` for background processing.
        """
        # Extract pending data
        data = self._pending_data
        adapter = self._pending_adapter
        method = self._pending_method

        # Clear refs to free memory and prevent leaks
        self._pending_data = None
        self._pending_adapter = None
        self._pending_method = None

        # Execute analysis
        self.start_analysis(data, adapter, method)

    @Slot(object, BaseErgoAdapter, AssessmentMethod)
    def start_analysis(
        self,
        current_data: Union[pd.DataFrame, np.ndarray],
        adapter: BaseErgoAdapter,
        method: AssessmentMethod = AssessmentMethod.REBA,
    ) -> None:
        """
        Executes the main dispatching background routine for ergonomic processing.

        Routes raw metrics through data mapping functions, loops frames asynchronously,
        compiles structured analysis tracking matrices, and posts unified diagnostic receipts.

        Args:
            current_data (pandas.DataFrame | numpy.ndarray): The raw matrix or sheet data tracking biomechanical data elements.
            adapter (BaseErgoAdapter): The methodology adapter class mapping scoring routines and criteria.
            method (AssessmentMethod): Structural framework metric enumeration settings tracking computation variants. Defaults to REBA.

        Returns:
            None (None): Dispatches output results directly back upstream using the `finished` signal pipeline.
        """

        import threading

        logger.debug(
            f"🔹 Worker: start_analysis running on thread: {threading.current_thread().name}"
        )

        if current_data is None:
            logger.warning("Background analysis attempted with no data payload.")
            self.finished.emit(
                AnalysisResult(
                    success=False,
                    message="NO_DATA_LOADED",
                    output_path=None,
                )
            )
            return

        try:
            mapper, calculator = adapter.get_relay_tools()

            raw_results = self.engine.run_calculation(current_data, mapper, calculator)

            if not raw_results:
                self.finished.emit(
                    AnalysisResult(
                        success=False,
                        message="No results generated.",
                        output_path=None,
                    )
                )
                return

            current_thresholds = adapter.get_thresholds()

            def risk_callback(score: int) -> RiskLevel:
                """
                Nested routing handler providing adapter-level enum metrics transformations.

                Args:
                    score (int): Frame index structural calculation metrics points score tracking index.

                Returns:
                    RiskLevel: Categorical qualitative priority enumeration classifications.
                """
                return self.engine.get_risk_level_enum(
                    score,
                    current_thresholds,
                )

            analysis_df = adapter.process(raw_results, risk_callback)

            scores_list = analysis_df[MetricType.SCORE.value].tolist()

            stats_dict = analysis_df[MetricType.SCORE.value].value_counts().to_dict()
            stats = {str(k): int(v) for k, v in stats_dict.items()}

            output_path: Path = ErgoPaths.analysis_output()
            analysis_df.to_csv(output_path, index=False)

            msg: str = f"Analysis Complete.\n{method.name} executed on {len(raw_results)} frames"

            # 7. Dispatch structural analytics result capsule back upstream to tracking receivers
            self.finished.emit(
                AnalysisResult(
                    success=True,
                    message=msg,
                    output_path=output_path,
                    scores=scores_list,
                    stats=stats,
                )
            )

        except NotImplementedError as e:
            self.finished.emit(
                AnalysisResult(
                    success=False,
                    message=str(e),
                    output_path=None,
                )
            )
        except Exception as e:
            self.finished.emit(
                AnalysisResult(
                    success=False,
                    message=f"Analysis failed: {str(e)}",
                    output_path=None,
                )
            )
