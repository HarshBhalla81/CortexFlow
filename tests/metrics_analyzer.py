import os
import time

DATA_FILE = "data/agentic_events.csv"

def analyze_metrics():
    print("--- Pathway Agentic Gateway Metrics ---")
    
    if not os.path.exists(DATA_FILE):
        print(f"Data file {DATA_FILE} not found. Run the stress tester first.")
        return
        
    with open(DATA_FILE, "r") as f:
        lines = f.readlines()
        
    if not lines:
        print("No events recorded yet.")
        return
        
    events = []
    for line in lines:
        parts = line.strip().split(',')
        if len(parts) >= 5 and parts[0] != "session_id":
            events.append({
                "session_id": parts[0],
                "task_id": parts[1],
                "event_type": parts[2],
                "timestamp": parts[4]
            })
            
    print(f"Total Events Processed: {len(events)}")
    
    # Calculate Latency / TTFT heuristics
    # (In a real scenario, you'd parse ISO timestamps and compare to injection time)
    # This serves as a placeholder for empirical optimization tracking.
    
    # Count error rates
    errors = sum(1 for e in events if "error" in str(e).lower())
    print(f"Total Errors Detected: {errors}")
    print(f"Success Rate: {((len(events) - errors) / len(events) * 100) if len(events) > 0 else 0:.2f}%")

if __name__ == "__main__":
    analyze_metrics()
