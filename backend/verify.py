import time
import requests
import subprocess
import sys
import os

print("Starting server...")
env = os.environ.copy()
proc = subprocess.Popen(["python3", "-m", "uvicorn", "backend.main:app", "--port", "8000"], cwd="/mnt/f/dev/python/gridlock_web", env=env)

try:
    print("Waiting for server to start (and load artifacts, ~15-25s)...")
    for _ in range(60):
        try:
            r = requests.get("http://localhost:8000/")
            if r.status_code == 200:
                print("Server is up!")
                break
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(1)
    else:
        print("Server failed to start in time.")
        sys.exit(1)

    print("\n--- Testing GET /api/meta ---")
    resp = requests.get("http://localhost:8000/api/meta")
    resp.raise_for_status()
    print("Meta OK. Event count:", resp.json()["event_count"])
    
    print("\n--- Testing GET /api/events?limit=5 ---")
    resp = requests.get("http://localhost:8000/api/events?limit=5")
    resp.raise_for_status()
    events = resp.json()["events"]
    print(f"Events OK. Returned {len(events)} events.")
    
    if events:
        event_id = events[0]["id"]
        print(f"\n--- Testing GET /api/events/{event_id}/advisory ---")
        resp = requests.get(f"http://localhost:8000/api/events/{event_id}/advisory")
        resp.raise_for_status()
        print("Advisory OK. Cascade risk score:", resp.json()["cascade_risk_score"])
    
    print("\n--- Testing POST /api/predict ---")
    payload = {
        "event_cause": "vehicle_breakdown",
        "zone_filled": "West Zone 2",
        "latitude": 12.9716,
        "longitude": 77.5946,
        "start_datetime": "2024-03-15T14:32:00",
        "description": "Truck broken down",
        "veh_type": "truck"
    }
    resp = requests.post("http://localhost:8000/api/predict", json=payload)
    resp.raise_for_status()
    print("Predict OK. Closure probability:", resp.json()["closure_probability"])
    
    print("\n--- Testing GET /api/outcomes ---")
    resp = requests.get("http://localhost:8000/api/outcomes")
    resp.raise_for_status()
    initial_count = resp.json()["count"]
    print("Outcomes GET OK. Current count:", initial_count)
    
    print("\n--- Testing POST /api/outcomes ---")
    outcome_payload = {
        "event_cause": "vehicle_breakdown",
        "zone": "West Zone 2",
        "predicted_officers": 3,
        "predicted_closure_probability": 0.234
    }
    resp = requests.post("http://localhost:8000/api/outcomes", json=outcome_payload)
    resp.raise_for_status()
    print("Outcomes POST OK. Status:", resp.json()["status"])
    
    print("\n--- Testing GET /api/outcomes (after POST) ---")
    resp = requests.get("http://localhost:8000/api/outcomes")
    resp.raise_for_status()
    new_count = resp.json()["count"]
    print("Outcomes GET OK. New count:", new_count)
    assert new_count == initial_count + 1, "Count did not increment"
    
    print("\nALL TESTS PASSED SUCCESSFULLY!")
finally:
    print("Terminating server...")
    proc.terminate()
    proc.wait()
