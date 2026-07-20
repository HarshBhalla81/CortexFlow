import os
import time
from collections import Counter

DATA_FILE = "data/agentic_events.csv"

def analyze_metrics():
    print("=" * 60)
    print("  CORTEXFLOW - PATHWAY AGENTIC GATEWAY METRICS REPORT")
    print("=" * 60)
    
    if not os.path.exists(DATA_FILE):
        print(f"\n[ERROR] Data file '{DATA_FILE}' not found.")
        print("Run the stress tester first to generate event data.")
        # Try alternate location
        alt = "data/tool_events_watchdog.csv"
        if os.path.exists(alt):
            print(f"[INFO] Found alternate file: {alt}")
        return
        
    with open(DATA_FILE, "r") as f:
        lines = f.readlines()
        
    if not lines:
        print("\nNo events recorded yet.")
        return
    
    # Parse events
    events = []
    event_types = Counter()
    sessions = set()
    
    for line in lines:
        parts = line.strip().split(',')
        if len(parts) >= 5 and parts[0] != "session_id":
            event = {
                "session_id": parts[0],
                "task_id": parts[1],
                "event_type": parts[2],
                "payload": ",".join(parts[3:-1]) if len(parts) > 5 else parts[3],
                "timestamp": parts[-1]
            }
            events.append(event)
            event_types[parts[2]] += 1
            sessions.add(parts[0])
    
    print(f"\n{'─' * 40}")
    print(f"  OVERVIEW")
    print(f"{'─' * 40}")
    print(f"  Total Events Processed : {len(events)}")
    print(f"  Unique Sessions        : {len(sessions)}")
    
    # Timestamp range
    try:
        timestamps = [float(e["timestamp"]) for e in events if e["timestamp"]]
        if timestamps:
            duration = max(timestamps) - min(timestamps)
            print(f"  Time Window            : {duration:.2f} seconds")
            if duration > 0:
                print(f"  Avg Events/Second      : {len(events) / duration:.2f}")
    except (ValueError, TypeError):
        pass
    
    print(f"\n{'─' * 40}")
    print(f"  EVENT TYPE BREAKDOWN")
    print(f"{'─' * 40}")
    for etype, count in event_types.most_common():
        pct = (count / len(events)) * 100
        bar = "█" * int(pct / 3) + "░" * (33 - int(pct / 3))
        print(f"  {etype:<22} {count:>5}  {bar} {pct:.1f}%")
    
    # Error analysis
    failures = event_types.get("TASK_FAILED", 0)
    completions = event_types.get("TASK_COMPLETED", 0)
    total_tasks = failures + completions
    
    print(f"\n{'─' * 40}")
    print(f"  RELIABILITY METRICS")
    print(f"{'─' * 40}")
    if total_tasks > 0:
        success_rate = (completions / total_tasks) * 100
        failure_rate = (failures / total_tasks) * 100
        print(f"  Tasks Completed   : {completions}")
        print(f"  Tasks Failed      : {failures}")
        print(f"  Success Rate      : {success_rate:.1f}%")
        print(f"  Failure Rate      : {failure_rate:.1f}%")
    else:
        print(f"  No TASK_COMPLETED or TASK_FAILED events found.")
        print(f"  (Agent worker may not be processing tasks)")
    
    retries = event_types.get("RETRY_TRIGGERED", 0)
    print(f"  Retries Triggered : {retries}")
    
    # Agent activity
    agent_events = event_types.get("AGENT_COMPLETED", 0)
    tool_events = event_types.get("tool_call", 0)
    
    print(f"\n{'─' * 40}")
    print(f"  AGENT ACTIVITY")
    print(f"{'─' * 40}")
    print(f"  Agent Completions : {agent_events}")
    print(f"  Tool Calls        : {tool_events}")
    print(f"  User Prompts      : {event_types.get('user_prompt', 0)}")
    
    # Check for anomaly patterns
    print(f"\n{'─' * 40}")
    print(f"  ANOMALY INDICATORS")
    print(f"{'─' * 40}")
    
    # Check for sessions with many failures
    session_failures = Counter()
    for e in events:
        if e["event_type"] == "TASK_FAILED":
            session_failures[e["session_id"]] += 1
    
    hot_sessions = [(s, c) for s, c in session_failures.most_common(5) if c > 1]
    if hot_sessions:
        print(f"  ⚠️  Sessions with repeated failures:")
        for session, count in hot_sessions:
            print(f"     {session}: {count} failures")
    else:
        print(f"  ✅ No repeated failure patterns detected")
    
    # Check for potential loops (same session with many AGENT_COMPLETED)
    session_agents = Counter()
    for e in events:
        if e["event_type"] == "AGENT_COMPLETED":
            session_agents[e["session_id"]] += 1
    
    loops = [(s, c) for s, c in session_agents.most_common(5) if c > 3]
    if loops:
        print(f"  ⚠️  Potential reasoning loops:")
        for session, count in loops:
            print(f"     {session}: {count} agent cycles")
    else:
        print(f"  ✅ No reasoning loops detected")
    
    print(f"\n{'=' * 60}")
    print(f"  END OF REPORT")
    print(f"{'=' * 60}")

if __name__ == "__main__":
    analyze_metrics()
