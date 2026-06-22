from supabase import create_client
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

def main():
    # 1. Setup and Connectivity
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not url or not key:
        print("❌ Error: SUPABASE_URL or SUPABASE_SERVICE_KEY not set in environment.")
        exit(1)

    supabase = create_client(url, key)
    
    # 2. Refuse to run if models table is already populated
    existing_models = supabase.table("models").select("*").execute().data
    if len(existing_models) > 0:
        print(f"❌ Aborting: The 'models' table already contains {len(existing_models)} rows.")
        print("Bootstrap should only be run once to seed v1. Manual cleanup required.")
        exit(1)

    # 3. Identify artifacts to upload
    # Based on backend/services/inference.py, we need the triage models and their calibrators.
    # We'll upload EVERYTHING in backend/models to be safe and ensure a complete v1 snapshot.
    models_dir = Path("backend/models")
    artifacts = list(models_dir.glob("*"))
    
    if not artifacts:
        print("❌ Error: No artifacts found in backend/models/")
        exit(1)
        
    print(f"Found {len(artifacts)} artifacts to upload to v1/...")

    # 4. Upload to Storage
    for art_path in artifacts:
        storage_path = f"v1/{art_path.name}"
        print(f"Uploading {art_path.name} -> {storage_path}...", end=" ")
        try:
            with open(art_path, "rb") as f:
                supabase.storage.from_("models").upload(storage_path, f)
            print("✅")
        except Exception as e:
            print(f"❌ Failed: {e}")
            exit(1)

    # 5. Seed the Database
    # We set the closure model as the primary 'active' artifact_path 
    # since that's the one the ModelManager will be focused on in Phase 4.
    primary_artifact = "v1/triage_model_closure.cbm"
    
    print(f"Seeding v1 as active model with path {primary_artifact}...")
    try:
        insert_res = supabase.table("models").insert({
            "version": "v1",
            "artifact_path": primary_artifact,
            "status": "active",
            "metrics": {"note": "Initial bootstrap from git repository"},
        }).execute()
        
        if not insert_res.data:
            print("❌ Error: Failed to insert v1 record into models table.")
            exit(1)
        print("✅ v1 seeded successfully.")
    except Exception as e:
        print(f"❌ Database insert failed: {e}")
        exit(1)

    print("\n🚀 Bootstrap complete! v1 is now live in Supabase.")

if __name__ == "__main__":
    main()
