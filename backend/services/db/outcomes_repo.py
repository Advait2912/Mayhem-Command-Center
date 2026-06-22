from typing import Protocol, List, Dict, Any

class OutcomesRepository(Protocol):
    def list_outcomes(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Retrieve a list of outcome records, ordered by creation date descending."""
        ...

    def insert_outcome(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Insert a new outcome record into the store."""
        ...

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
        # we expect record to match the CSV columns
        row_df = pd.DataFrame([record])
        write_header = (not self.log_path.exists()) or self.log_path.stat().st_size < 10
        row_df.to_csv(self.log_path, mode="a", header=write_header, index=False)
        return record

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
        
        # Extract the payload and outcome parts from the flat record
        # This assumes the record is passed as a flat dict (like the CSV one)
        # We split by keys defined in the database_schema.sql
        
        outcome_fields = {
            "actual_officers_used", "actual_duration_hrs", 
            "actual_required_closure", "notes"
        }
        payload_fields = {
            "source_event_id", "event_cause", "zone", 
            "predicted_officers", "predicted_closure_probability", 
            "predicted_cascade_risk_score"
        }
        
        event_payload = {k: v for k, v in record.items() if k in payload_fields}
        actual_outcome = {k: v for k, v in record.items() if k in outcome_fields}
        
        db_row = {
            "model_version": record.get("model_version", "v1"),
            "source": "live",
            "event_payload": event_payload,
            "actual_outcome": actual_outcome,
            "used_for_training": False
        }
        
        response = self.client.table("outcomes").insert(db_row).execute()
        return response.data[0] if response.data else {}
