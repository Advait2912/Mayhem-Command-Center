import logging
from pathlib import Path

from backend.core.config import VERSIONED_MODELS_DIR

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

def upload_model_files(client, paths: list[Path]) -> str:
    """Upload specific files to Storage under a new version prefix."""
    version = _next_version(client)
    for path in paths:
        if not path.exists():
            raise RuntimeError(f"Artifact {path} does not exist for upload.")
        storage_path = f"{version}/{path.name}"
        with open(path, "rb") as f:
            client.storage.from_(STORAGE_BUCKET).upload(
                storage_path, f, file_options={"upsert": "true"}
            )
    return version

def promote_version_in_db(client, version: str, metrics: dict, representative_path_name: str) -> str:
    # 3. Insert Candidate: Create a row in the models table with status = 'candidate'
    representative_path = f"{version}/{representative_path_name}"
    
    insert_res = client.table("models").insert({
        "version": version,
        "artifact_path": representative_path,
        "metrics": metrics,
        "status": "candidate",
    }).execute()
    
    if not insert_res.data:
        raise RuntimeError(f"Failed to insert models row for {version}")
    
    model_id = insert_res.data[0]["id"]
    
    # 4. Promote: Call the existing promote_model(model_id) RPC.
    client.rpc("promote_model", {"target_id": model_id}).execute()
    logger.info(f"[ModelManager] {version} promoted to active.")
    return model_id

def download_version(client, version: str, dest_dir: Path = VERSIONED_MODELS_DIR) -> int:
    """Pulls every file under the version's Storage prefix down into dest_dir."""
    files = client.storage.from_(STORAGE_BUCKET).list(version)
    if not files:
        raise RuntimeError(f"No files found under Storage prefix '{version}/'")

    dest_dir.mkdir(parents=True, exist_ok=True)
    for f in files:
        name = f["name"]
        data = client.storage.from_(STORAGE_BUCKET).download(f"{version}/{name}")
        (dest_dir / name).write_bytes(data)

    return len(files)
