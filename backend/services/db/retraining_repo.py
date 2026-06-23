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

class SupabaseRetrainingRepository:
    """Production implementation using Supabase Postgres."""
    def __init__(self, client):
        self.client = client

    def start_run(self) -> str:
        # INSERT into retraining_runs, status='running'
        response = self.client.table("retraining_runs").insert({"status": "running"}).execute()
        if not response.data:
            raise RuntimeError("Failed to insert retraining_runs row")
        return response.data[0]["id"]

    def complete_run(self, run_id: str, model_id: str, metrics: Dict[str, Any], rows_used: int) -> None:
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).isoformat()
        self.client.table("retraining_runs").update({
            "status": "completed",
            "model_id": model_id,
            "metrics": metrics,
            "rows_used": rows_used,
            "completed_at": now
        }).eq("id", run_id).execute()

    def fail_run(self, run_id: str, error_message: str) -> None:
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).isoformat()
        self.client.table("retraining_runs").update({
            "status": "failed",
            "error_message": error_message,
            "completed_at": now
        }).eq("id", run_id).execute()
