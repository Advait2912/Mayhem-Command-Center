from typing import Protocol, Dict, Any

class RetrainingRepository(Protocol):
    def start_run(self) -> str:
        """Initializes a retraining run and returns the run_id."""
        ...

    def complete_run(self, run_id: str, model_id: str, metrics: Dict[str, Any], rows_used: int) -> None:
        """Marks a run as completed and links the resulting model."""
        ...

    def fail_run(self, run_id: str, error_message: str) -> None:
        """Marks a run as failed with an error message."""
        ...

class NoopRetrainingRepository:
    """Local development implementation that logs to console without persisting."""
    def start_run(self) -> str:
        print("[RetrainingRepo] Starting run (local noop)")
        return "local-run-0"

    def complete_run(self, run_id: str, model_id: str, metrics: Dict[str, Any], rows_used: int) -> None:
        print(f"[RetrainingRepo] Run {run_id} completed successfully. Model: {model_id}, Rows: {rows_used}")

    def fail_run(self, run_id: str, error_message: str) -> None:
        print(f"[RetrainingRepo] Run {run_id} failed: {error_message}")
