# tests/gui/workers/analysis_worker_test.py
import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
import pandas as pd

from gui.utils.constants import AssessmentMethod, RiskLevel, MetricType
from gui.utils.models import AnalysisResult
from gui.workers.analysis_worker import AnalysisWorker


class TestAnalysisWorkerPipeline:
    """Validates computation matrix tracking logic inside the isolated thread worker."""

    @pytest.fixture
    def worker(self):
        """Provides an isolated AnalysisWorker instance with mocked signal emitters."""
        worker = AnalysisWorker()
        worker.finished = MagicMock()
        return worker

    def test_worker_run_success(self, worker):
        """Verify dynamic metrics aggregation and output CSV writing inside worker runtime."""
        # Setup input states onto pending attributes
        worker._pending_data = pd.DataFrame({"joint_angle_data": [15, 30]})
        worker._pending_method = AssessmentMethod.REBA

        # Properly mock the adapter and its tools unpacking structure
        mock_adapter = MagicMock()
        mock_mapper = MagicMock()
        mock_calculator = MagicMock()
        mock_adapter.get_relay_tools.return_value = (mock_mapper, mock_calculator)
        mock_adapter.get_thresholds.return_value = [1, 3, 5]

        # Ensure the processed DataFrame includes the exact metric column expected
        mock_df = pd.DataFrame({MetricType.SCORE.value: [2, 5]})
        mock_adapter.process.return_value = mock_df
        worker._pending_adapter = mock_adapter

        # Mock core engine calculation returns
        mock_engine = MagicMock()
        mock_engine.run_calculation.return_value = [
            {"calculated": True},
            {"calculated": True},
        ]
        mock_engine.get_risk_level_enum.return_value = RiskLevel.LOW

        mock_output_path = Path("/mock/target/output.csv")

        # Patch dependencies where they are imported or called
        with (
            patch("pandas.DataFrame.to_csv") as mock_to_csv,
            patch.object(worker, "engine", mock_engine),
            patch(
                "gui.workers.analysis_worker.ErgoPaths.analysis_output",
                return_value=mock_output_path,
            ),
        ):
            worker.run()

            # Verify processing and side effects
            assert mock_adapter.process.call_count == 1
            mock_to_csv.assert_called_once_with(mock_output_path, index=False)

            # Assert completion signal emitted safe tracking results
            worker.finished.emit.assert_called_once()
            result = worker.finished.emit.call_args[0][0]

            assert isinstance(result, AnalysisResult)
            assert result.success is True
            assert result.output_path == mock_output_path
            assert result.scores == [2, 5]
            assert result.stats == {"2": 1, "5": 1}

    def test_worker_run_empty_blocks_failure(self, worker):
        """Ensure completion signal transmits failure context if calculation engine returns empty frames."""
        worker._pending_data = pd.DataFrame({"joint_1": [0.5]})
        worker._pending_method = AssessmentMethod.RULA

        mock_adapter = MagicMock()
        mock_adapter.get_relay_tools.return_value = (MagicMock(), MagicMock())
        worker._pending_adapter = mock_adapter

        mock_engine = MagicMock()
        mock_engine.run_calculation.return_value = None  # Failure trigger

        with patch.object(worker, "engine", mock_engine):
            worker.run()

            worker.finished.emit.assert_called_once()
            result = worker.finished.emit.call_args[0][0]
            assert result.success is False
            assert "No results generated" in result.message

    def test_worker_run_generic_exception_catch(self, worker):
        """Ensure execution crashes inside worker threads are intercepted cleanly and signaled down."""
        worker._pending_data = pd.DataFrame({"raw_metrics": [1]})
        worker._pending_method = AssessmentMethod.REBA

        # Prevent unpacking error by setting up get_relay_tools correctly first
        mock_adapter = MagicMock()
        mock_adapter.get_relay_tools.return_value = (MagicMock(), MagicMock())

        # Trigger your intentional error on the actual downstream calculation process step
        mock_adapter.process.side_effect = ValueError("Internal Parser Crash")
        worker._pending_adapter = mock_adapter

        # Mock the engine so it passes the calculation runner step safely
        mock_engine = MagicMock()
        mock_engine.run_calculation.return_value = [{"frame": 1}]

        with patch.object(worker, "engine", mock_engine):
            worker.run()

            worker.finished.emit.assert_called_once()
            result = worker.finished.emit.call_args[0][0]
            assert result.success is False
            assert "Internal Parser Crash" in result.message
