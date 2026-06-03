import math
from typing import Any
import pandas as pd
from pathlib import Path
from PySide6.QtCore import QObject, Signal, QThread, Qt

from gui.utils.app_paths import ErgoPaths
from gui.utils.constants import AssessmentMethod, RiskLevel
from gui.utils.models import FrameReviewData, AnalysisResult, SessionData
from gui.utils.logger import logger
from gui.workers.analysis_worker import AnalysisWorker


class ReviewBackend(QObject):
    """
    An independent backend controller managing sandboxed, human-in-the-loop
    ergonomic re-analyses without interfering with raw session logs.
    """

    # Signals required by the UI
    status_updated = Signal(str)
    analysis_finished = Signal(AnalysisResult)
    frame_review_ready = Signal(FrameReviewData)

    def __init__(self) -> None:
        super().__init__()
        # Memory Sandboxes
        self.active_dataframe: pd.DataFrame | None = None
        self.joint_angles_dataframe: pd.DataFrame | None = None
        self.current_ergo_analysis_path: Path | None = None
        self.current_joint_analysis_path: Path | None = None
        self.checkpoint_file_path: Path | None = None

        # Thread & Worker Management attributes
        self._analysis_thread: QThread | None = None
        self._analysis_worker: AnalysisWorker | None = None

    def load_review_session(self, session_data: SessionData) -> tuple[bool, str]:
        """
        Loads the existing analysis data, provisions an in-memory copy,
        and establishes an on-disk safety checkpoint instantly.
        """
        try:
            self.current_ergo_analysis_path = ErgoPaths.analysis_output()
            if not self.current_ergo_analysis_path.exists():
                return (
                    False,
                    f"Target file does not exist: {self.current_ergo_analysis_path.name}",
                )

            self.current_joint_analysis_path = session_data.joint_angles_csv_path

            if not self.current_joint_analysis_path:
                print("\n\n", session_data, "\n\n")
                raise ValueError(
                    "No joint angles file path in ReviewBackend load_review_session"
                )

            # 1. Read Data directly into Memory (Copy #1: The In-Memory Sandbox)
            self.active_dataframe = pd.read_csv(self.current_ergo_analysis_path)
            self.joint_angles_dataframe = pd.read_csv(self.current_joint_analysis_path)

            # 2. Generate a local disk checkpoint (Copy #2: The I/O Safety Net)
            self.checkpoint_file_path = self.current_ergo_analysis_path.with_suffix(
                ".bak_review"
            )
            self.active_dataframe.to_csv(self.checkpoint_file_path, index=False)

            return (
                True,
                f"Successfully sandboxed: {self.current_ergo_analysis_path.name}",
            )
        except Exception as e:
            logger.error(f"Failed to initialize review sandbox: {e}", exc_info=True)
            return False, f"Sandbox initialization failure: {str(e)}"

    def get_dataset_fields(self) -> list[str]:
        """Returns columns from the active dataframe for UI selectors."""
        if self.active_dataframe is not None:
            return list(self.active_dataframe.columns)
        return []

    def run_review_analysis(
        self, method: AssessmentMethod = AssessmentMethod.REBA
    ) -> None:
        """
        Executes a targeted analysis run using the modified in-memory dataframe state.
        Allows consecutive executions without affecting the original source files.
        """
        if self.active_dataframe is None:
            logger.warning("Review analysis attempted with no sandboxed data loaded.")
            self.analysis_finished.emit(
                AnalysisResult(
                    success=False,
                    message="No active dataframe loaded.",
                    output_path=None,
                )
            )
            return

        try:
            # Clean up existing thread safely before spinning up a new processing pass
            self._terminate_active_worker()

            # Initialize fresh threading infrastructure
            self._analysis_thread = QThread()
            self._analysis_worker = AnalysisWorker()

            self._analysis_worker._pending_data = self.active_dataframe
            self._analysis_worker._pending_method = method

            self._analysis_worker.moveToThread(self._analysis_thread)

            # Connect Pipelines (QueuedConnections are vital for cross-thread messaging)
            self._analysis_worker.finished.connect(
                self._handle_review_worker_finished,
                type=Qt.ConnectionType.QueuedConnection,
            )
            self._analysis_worker.finished.connect(self._analysis_thread.quit)
            self._analysis_worker.finished.connect(self._analysis_worker.deleteLater)
            self._analysis_thread.finished.connect(self._analysis_thread.deleteLater)

            self._analysis_thread.started.connect(
                self._analysis_worker.run,
                type=Qt.ConnectionType.QueuedConnection,
            )

            self.status_updated.emit(
                f"Recalculating {method.value} engine matrix layers..."
            )
            self._analysis_thread.start()

        except Exception as e:
            logger.error(f"Review engine execution failure: {e}", exc_info=True)
            self.analysis_finished.emit(
                AnalysisResult(
                    success=False, message=f"Re-run failed: {str(e)}", output_path=None
                )
            )

    def _handle_review_worker_finished(self, result: AnalysisResult) -> None:
        """Interceptors worker output to update our memory layer and soft-checkpoint."""
        if result.success:
            if self.checkpoint_file_path and self.active_dataframe is not None:
                self.active_dataframe.to_csv(self.checkpoint_file_path, index=False)

            self.status_updated.emit("Review pass updated. Soft checkpoint saved.")

        # Forward results up to the UI layers (ReviewView or MainWindow?)
        self.analysis_finished.emit(result)

    def mutate_records(
        self,
        start_frame: int,
        end_frame: int,
        variable_field: str,
        override_value: float,
    ) -> None:
        """Modifies selected rows in memory based on instructions received from the UI."""
        if self.active_dataframe is None:
            self.status_updated.emit("Data modification rejected: No dataset mounted.")
            return

        if variable_field not in self.active_dataframe.columns:
            self.active_dataframe[variable_field] = 0.0

        total_rows = len(self.active_dataframe)

        if end_frame == -1:
            self.active_dataframe[variable_field] = override_value
            self.status_updated.emit(
                f"Global rewrite applied to field: [{variable_field}] -> {override_value}"
            )
        else:
            start = max(0, min(start_frame, total_rows - 1))
            end = max(0, min(end_frame, total_rows - 1))

            self.active_dataframe.loc[start:end, variable_field] = override_value
            self.status_updated.emit(
                f"Modified [{variable_field}] from frame {start} to {end} -> {override_value}"
            )

    def commit_final_review(self) -> bool:
        """
        The Double-Confirmation Trigger. Hard-saves the actively modified
        memory dataset into a discrete 'ergomocap_review.csv' file.
        """
        if self.active_dataframe is None or self.current_ergo_analysis_path is None:
            self.status_updated.emit("Commit blocked: No active dataset found.")
            return False
        try:
            final_output_path = (
                self.current_ergo_analysis_path.parent / "ergomocap_review.csv"
            )
            self.active_dataframe.to_csv(final_output_path, index=False)
            self.status_updated.emit(
                f"Review session committed to: {final_output_path.name}"
            )

            if self.checkpoint_file_path and self.checkpoint_file_path.exists():
                self.checkpoint_file_path.unlink()

            return True
        except Exception as e:
            logger.error(f"Failed to commit final review track: {e}")
            self.status_updated.emit(f"Final Write Failure: {str(e)}")
            return False

    def _terminate_active_worker(self) -> None:
        """Safely breaks down running threads before spinning up successive runs."""
        if hasattr(self, "_analysis_thread") and self._analysis_thread is not None:
            try:
                if self._analysis_thread.isRunning():
                    self._analysis_thread.quit()
                    if not self._analysis_thread.wait(1000):
                        self._analysis_thread.terminate()
                        self._analysis_thread.wait()
                self._analysis_thread.deleteLater()
            except RuntimeError:
                pass
            finally:
                self._analysis_thread = None

        if hasattr(self, "_analysis_worker") and self._analysis_worker is not None:
            try:
                self._analysis_worker.deleteLater()
            except RuntimeError:
                pass
            finally:
                self._analysis_worker = None

    def emit_frame_review_data(self, current_frame_idx: int) -> None:
        """
        Extracts frame properties dynamically from separate score and kinematic
        data sources using structural parsing, ensuring strict validation safety.
        """
        # Strict state validation
        if self.active_dataframe is None:
            raise ValueError(
                "Review calculation blocked: Active score dataframe is not initialized."
            )
        if self.joint_angles_dataframe is None:
            self.joint_angles_dataframe

            raise ValueError(
                "Review calculation blocked: Joint angles dataframe is not initialized."
            )

        total_rows = len(self.active_dataframe)
        if current_frame_idx < 0 or current_frame_idx >= total_rows:
            raise IndexError(
                f"Requested frame index {current_frame_idx} is out of bounds (0-{total_rows - 1})."
            )

        if current_frame_idx >= len(self.joint_angles_dataframe):
            raise IndexError(
                f"Requested frame index {current_frame_idx} exceeds available joint angles row data."
            )

        # 1. Pull independent raw rows as dictionaries
        score_row = self.active_dataframe.iloc[current_frame_idx].to_dict()
        angle_row = self.joint_angles_dataframe.iloc[current_frame_idx].to_dict()

        method_suffix = str(score_row.get("Method", "REBA")).upper()

        # 2. Extract completely dynamic metric payloads
        scores_payload = {str(key): value for key, value in score_row.items()}
        print(scores_payload, "\n\nHERE\n\n")

        angles_payload = self._parse_pure_row_metrics(angle_row, is_score_file=False)

        # 3. Resolve global summary metadata with none-safety checks
        unified_score = self._resolve_unified_score(score_row, method_suffix)
        resolved_risk = self._resolve_risk_level(score_row)

        # 4. Construct package and dispatch downstream
        review_packet = FrameReviewData(
            frame_idx=current_frame_idx,
            total_frames=total_rows,
            landmarks=[],
            score=unified_score,
            risk=resolved_risk,
            joint_angles=angles_payload,
            scores_dict=scores_payload,
        )
        self.frame_review_ready.emit(review_packet)

    def _parse_pure_row_metrics(
        self, row_dict: dict, is_score_file: bool, method_suffix: str = ""
    ) -> dict[str, Any]:
        """
        Iterates over all columns present inside a file row without text keyword tracking.
        Converts column keys to clean labels and raises exceptions on null/corrupted fields.
        """
        ignored_fields = {"METHOD", "FRAME", "INDEX", "FRAME_IDX", "SCORE", "RISK"}
        payload = {}

        for col_name, col_value in row_dict.items():
            col_upper = str(col_name).upper()

            # Skip common administrative tracking metadata blocks
            if (
                col_upper in ignored_fields
                or col_upper == f"FINAL_SCORE_{method_suffix}"
            ):
                continue

            # Strict None / NaN Safety validation
            if col_value is None or (
                isinstance(col_value, float) and math.isnan(col_value)
            ):
                raise ValueError(
                    f"Strict Check Failure: Corrupt or missing value encountered in column '{col_name}'."
                )

            # Format raw key into clean, title-cased presentation string
            # TODO is better to delegate all this to one interface /Strategy Pattern Class
            clean_name = col_name
            if (
                is_score_file
                and method_suffix
                and clean_name.upper().endswith(f"_{method_suffix}")
            ):
                clean_name = clean_name[: -len(f"_{method_suffix}")]

            if is_score_file and clean_name.upper().endswith("_SCORE"):
                clean_name = clean_name[:-6]

            clean_name = clean_name.replace("_", " ").strip().title()

            # Sanitize numeric formats cleanly
            try:
                val_float = float(col_value)
                payload[clean_name] = (
                    int(val_float) if val_float.is_integer() else val_float
                )
            except (ValueError, TypeError):
                payload[clean_name] = col_value

        return payload

    def _resolve_unified_score(self, row_data: dict, method_suffix: str) -> int:
        """Dynamically isolates the dominant global summary calculation value."""
        possible_keys = {"SCORE", f"FINAL_SCORE_{method_suffix}", "FINAL_SCORE"}

        for col_name, col_value in row_data.items():
            if str(col_name).upper() in possible_keys:
                if col_value is None or (
                    isinstance(col_value, float) and math.isnan(col_value)
                ):
                    raise ValueError(
                        f"Strict Check Failure: Base score entry '{col_name}' cannot be empty."
                    )
                try:
                    return int(float(col_value))
                except (ValueError, TypeError) as e:
                    raise ValueError(
                        f"Strict Check Failure: Uncastable summary score '{col_value}'"
                    ) from e

        raise ValueError(
            "Strict Check Failure: No valid summary assessment score column discovered in file layout."
        )

    def _resolve_risk_level(self, row_data: dict) -> RiskLevel:
        """Maps target string values safely into designated structural Enum types."""

        risk_key = next((k for k in row_data.keys() if "RISK" in str(k).upper()), None)
        if not risk_key:
            raise ValueError(
                "Strict Check Failure: Missing mandatory descriptive 'risk' indicator entry column."
            )

        raw_risk = str(row_data[risk_key]).strip().lower()

        if not raw_risk or raw_risk in ("nan", "none", ""):
            raise ValueError(
                f"Strict Check Failure: Risk tracking column '{risk_key}' contains a null or empty value."
            )

        try:
            return RiskLevel(raw_risk)
        except ValueError as e:
            valid_options = [e.value for e in RiskLevel]
            raise ValueError(
                f"Strict Check Failure: Value '{raw_risk}' is not a registered classification type of RiskLevel. "
                f"Valid options are: {valid_options}."
            ) from e
