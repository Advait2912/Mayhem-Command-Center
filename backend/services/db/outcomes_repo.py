from typing import Protocol, List, Dict, Any

class OutcomesRepository(Protocol):
    def list_outcomes(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Retrieve a list of outcome records, ordered by creation date descending."""
        ...
 
    def insert_outcome(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Insert a new outcome record into the store."""
        ...
 
    def count_unused_outcomes(self) -> int:
        """Returns the number of outcomes that have not yet been marked used_for_training."""
        ...
 
    def mark_used_for_training(self) -> None:
        """Marks all currently unused outcomes as used_for_training."""
        ...



# Fields an officer fills in after the fact -- the ground-truth labels used
# for retraining. Kept in one place since both repo implementations and
# retrain.py need the same split between "outcome" and "payload" fields.
OUTCOME_FIELDS = {
    "actual_officers_used", "actual_duration_hrs",
    "actual_required_closure", "actual_priority", "notes",
}
PAYLOAD_FIELDS = {
    "source_event_id", "event_cause", "zone",
    "predicted_officers", "predicted_closure_probability",
    "predicted_cascade_risk_score",
}


def flatten_outcome_row(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Normalizes a raw repo row -- either a flat CSV row or a nested
    Supabase row (event_payload/actual_outcome jsonb) -- into the flat
    shape the OutcomeRecord schema and retrain.py both expect."""
    if "actual_outcome" in raw:
        payload = raw.get("event_payload") or {}
        actuals = raw.get("actual_outcome") or {}
        return {
            "logged_at": raw.get("created_at"),
            "source_event_id": payload.get("source_event_id"),
            "event_cause": payload.get("event_cause"),
            "zone": payload.get("zone"),
            "predicted_officers": payload.get("predicted_officers"),
            "predicted_closure_probability": payload.get("predicted_closure_probability"),
            "predicted_cascade_risk_score": payload.get("predicted_cascade_risk_score"),
            "actual_officers_used": actuals.get("actual_officers_used"),
            "actual_duration_hrs": actuals.get("actual_duration_hrs"),
            "actual_required_closure": actuals.get("actual_required_closure"),
            "actual_priority": actuals.get("actual_priority"),
            "notes": actuals.get("notes"),
            "used_for_training": raw.get("used_for_training", False),
        }
    return raw


class CsvOutcomesRepository:
    """Local development implementation using outcomes_log.csv."""
    def __init__(self, log_path):
        self.log_path = log_path

    def list_outcomes(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        import pandas as pd
        if not self.log_path.exists() or self.log_path.stat().st_size < 10:
            return []

        df = pd.read_csv(self.log_path, dtype=str)
        # Sort descending by logged_at
        df = df.sort_values("logged_at", ascending=False)

        # Apply offset and limit
        df = df.iloc[offset : offset + limit]

        # Convert to dicts
        results = []
        for _, row in df.iterrows():
            results.append(row.to_dict())
        return results

    def insert_outcome(self, record: Dict[str, Any]) -> Dict[str, Any]:
        import pandas as pd
        file_exists = self.log_path.exists() and self.log_path.stat().st_size >= 10
 
        if not file_exists:
            pd.DataFrame([record]).to_csv(self.log_path, mode="w", header=True, index=False)
            return record
 
        # Schema-safe append: if this record introduces columns the file's
        # header doesn't have yet (e.g. a newly added outcome field), widen
        # the existing file first instead of writing a row with a different
        # column count -- a mismatched column count silently misaligns every
        # row read back afterwards.
        existing_columns = pd.read_csv(self.log_path, nrows=0).columns.tolist()
        new_columns = [c for c in record.keys() if c not in existing_columns]
        if new_columns:
            full_df = pd.read_csv(self.log_path, dtype=str)
            for c in new_columns:
                full_df[c] = None
            full_df.to_csv(self.log_path, mode="w", header=True, index=False)
            existing_columns = existing_columns + new_columns
 
        row_df = pd.DataFrame([record]).reindex(columns=existing_columns)
        row_df.to_csv(self.log_path, mode="a", header=False, index=False)
        return record
 
    def count_unused_outcomes(self) -> int:
        import pandas as pd
        if not self.log_path.exists() or self.log_path.stat().st_size < 10:
            return 0
        df = pd.read_csv(self.log_path, dtype=str)
        # Local CSV mode is simple; we just return total count.
        return len(df)
 
    def mark_used_for_training(self) -> None:
        # No-op for CSV mode.
        pass


class SupabaseOutcomesRepository:
    """Production implementation using Supabase Postgres."""
    def __init__(self, client):
        self.client = client

    def list_outcomes(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        # Supabase handles sorting via .order()
        # we map the DB fields to match the expected CSV-like record if needed,
        # but ideally the API layer handles the final mapping to the Pydantic model.
        response = self.client.table("outcomes")\
            .select("*")\
            .order("created_at", desc=True)\
            .range(offset, offset + limit - 1)\
            .execute()
        return response.data

    def insert_outcome(self, record: Dict[str, Any]) -> Dict[str, Any]:
        # The record passed here is a flat dict from the API layer.
        # We need to split it into the DB columns: event_payload and actual_outcome.
        # However, to keep the Protocol clean and the CSV repo simple,
        # we'll let the Supabase repo handle the mapping based on the schema.
        event_payload = {k: v for k, v in record.items() if k in PAYLOAD_FIELDS}
        actual_outcome = {k: v for k, v in record.items() if k in OUTCOME_FIELDS}

        db_row = {
            "model_version": record.get("model_version", "v1"),
            "source": "live",
            "event_payload": event_payload,
            "actual_outcome": actual_outcome,
            "used_for_training": False
        }

        response = self.client.table("outcomes").insert(db_row).execute()
        return response.data[0] if response.data else {}

    def count_unused_outcomes(self) -> int:
        response = self.client.table("outcomes").select("id", count="exact").eq("used_for_training", False).execute()
        return response.count if response.count is not None else 0

    def mark_used_for_training(self) -> None:
        self.client.table("outcomes").update({"used_for_training": True}).eq("used_for_training", False).execute()
