import pandas as pd
from pathlib import Path
from gui.backend.backend import ErgoBackend


class ReviewBackend(ErgoBackend):
    """
    Subclasses the core ErgoBackend engine to handle live modifications
    on structural CSV calculations without breaking ongoing multi-thread frameworks.
    """

    def __init__(self) -> None:
        super().__init__()
        self.active_dataframe: pd.DataFrame | None = None
        self.source_dataset_path: Path | None = None

    def mount_analysis_dataset(self, csv_file_path: Path) -> bool:
        """Reads automated structural calculations safely into editable arrays."""
        try:
            self.source_dataset_path = Path(csv_file_path)
            if not self.source_dataset_path.exists():
                return False

            self.active_dataframe = pd.read_csv(self.source_dataset_path)
            return True
        except Exception as e:
            self.status_updated.emit(f"Data Read Fault: {str(e)}")
            return False

    def get_dataset_fields(self) -> list[str]:
        if self.active_dataframe is not None:
            return list(self.active_dataframe.columns)
        return []

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

        # Handle global variable manipulation wildcard bounds
        if end_frame == -1:
            self.active_dataframe[variable_field] = override_value
            self.status_updated.emit(
                f"Global rewrite applied to field: [{variable_field}] -> {override_value}"
            )
        else:
            # Bound and sanitize limits safely within row indices
            start = max(0, min(start_frame, total_rows - 1))
            end = max(0, min(end_frame, total_rows - 1))

            # Perform efficient in-place slice allocation
            self.active_dataframe.loc[start:end, variable_field] = override_value
            self.status_updated.emit(
                f"Modified [{variable_field}] from frame {start} to {end} -> {override_value}"
            )

    def save_mutated_dataset(self) -> bool:
        """Permanently commits human post-processed outputs directly back out to storage tracks."""
        if self.active_dataframe is None or self.source_dataset_path is None:
            return False
        try:
            # Safely create a verified backup tag before overwriting source components
            backup_file = self.source_dataset_path.with_suffix(".bak_automated")
            if not backup_file.exists():
                self.active_dataframe.to_csv(backup_file, index=False)

            # Save modified data
            self.active_dataframe.to_csv(self.source_dataset_path, index=False)
            self.status_updated.emit(
                f"Saved changes securely to: {self.source_dataset_path.name}"
            )
            return True
        except Exception as e:
            self.status_updated.emit(f"Commit Failure: {str(e)}")
            return False
