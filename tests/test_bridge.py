import os
import httpx

PATHWAY_URL = os.getenv("PATHWAY_URL", "http://localhost:8080/")

def test_connection():
    payload = {
        "task_id": "verify-123",
        "event_type": "VERIFY_CONNECTION",
        "payload": "Verify bridge connection",
        "timestamp": 12345.0
    }
    response = httpx.post(PATHWAY_URL, json=payload, timeout=5.0)
    response.raise_for_status()
    print("Bridge Verified")

if __name__ == "__main__":
    try:
        test_connection()
    except Exception as e:
        print(f"Error: {e}")