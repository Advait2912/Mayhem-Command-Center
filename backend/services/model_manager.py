"""
services/model_manager.py — Versioned model artifact storage.

Every retrain writes its artifacts to backend/models/ as today, then -- if
Supabase is configured -- pushes the whole folder to Storage under the next
"v{N}" prefix and promotes it to active via the promote_model() RPC (see
trash/database_schema.sql for the schema this assumes: models table +
promote_model function + a "models" Storage bucket, already bootstrapped
by scripts/bootstrap_models.py as v1).

On the next process startup, load_artifacts() calls download_active_model()
first, which pulls whichever version is currently marked active in the
models table down into backend/models/ before anything else loads --
so a fresh session always serves the latest promoted model, not whatever
happened to be on disk.
"""

import logging
from pathlib import Path

from backend.core.config import MODELS_DIR

logger = logging.getLogger("gridlock")

STORAGE_BUCKET = "models"


def _next_version(client) -> str:
    rows = client.table("models").select("version").execute().data
    numbers = []
    for r in rows:
        v = r.get("version", "")
        if v.startswith("v") and v[1:].isdigit():
            numbers.append(int(v[1:]))
    return f"v{(max(numbers) + 1) if numbers else 1}"


def upload_new_version(client, metrics: dict, source_dir: Path = MODELS_DIR) -> str:
    """Uploads every file currently in source_dir to Storage under a new
    incrementing version prefix, registers it in the models table, and
    promotes it to active. Returns the new version string ('v3', ...).
    Raises on failure -- callers should catch and log, not let a failed
    cloud push take down a retrain that already succeeded locally."""
    version = _next_version(client)
    artifacts = [p for p in source_dir.glob("*") if p.is_file()]
    if not artifacts:
        raise RuntimeError(f"No artifacts found in {source_dir} to upload as {version}")

    for path in artifacts:
        storage_path = f"{version}/{path.name}"
        with open(path, "rb") as f:
            client.storage.from_(STORAGE_BUCKET).upload(
                storage_path, f, file_options={"upsert": "true"}
            )

    # Representative path -- mirrors the v1 bootstrap convention. The full
    # version is a folder; this column just needs *a* file inside it so the
    # row is traceable to a concrete upload.
    representative_path = f"{version}/{artifacts[0].name}"
    insert_res = client.table("models").insert({
        "version": version,
        "artifact_path": representative_path,
        "metrics": metrics,
        "status": "candidate",
    }).execute()
    if not insert_res.data:
        raise RuntimeError(f"Failed to insert models row for {version}")

    model_id = insert_res.data[0]["id"]
    client.rpc("promote_model", {"target_id": model_id}).execute()
    logger.info(f"[ModelManager] {version} uploaded and promoted to active "
                f"({len(artifacts)} files)")
    return version


def download_active_model(client, dest_dir: Path = MODELS_DIR) -> str:
    """Pulls every file under the currently-active version's Storage prefix
    down into dest_dir, overwriting whatever's there. Returns the version
    string that was pulled. Raises if there's no active row or the download
    fails -- callers decide whether that's fatal (production) or a fallback
    to local disk (dev)."""
    rows = client.table("models").select("version").eq("status", "active").execute().data
    if not rows:
        raise RuntimeError("No model row with status='active' in Supabase")
    version = rows[0]["version"]

    files = client.storage.from_(STORAGE_BUCKET).list(version)
    if not files:
        raise RuntimeError(f"No files found under Storage prefix '{version}/'")

    dest_dir.mkdir(parents=True, exist_ok=True)
    for f in files:
        name = f["name"]
        data = client.storage.from_(STORAGE_BUCKET).download(f"{version}/{name}")
        (dest_dir / name).write_bytes(data)

    logger.info(f"[ModelManager] Pulled active model {version} "
                f"({len(files)} files) into {dest_dir}")
    return version
