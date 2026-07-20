"""
Watchdog Diagnostic Test
Sends a crafted sequence of events designed to trigger the watchdog's anomaly detection.
"""
import asyncio
import httpx
import time
import json

GATEWAY_URL = "http://gateway:8000/process"

async def main():
    print("--- Watchdog Diagnostic Test ---")
    print("Sending crafted events to trigger anomaly detection...\n")

    async with httpx.AsyncClient(timeout=30.0) as client:

        # Phase 1: Send normal baseline events
        print("[Phase 1] Sending 5 normal user_prompt events...")
        for i in range(5):
            payload = {
                "session_id": f"watchdog_test_{i}",
                "task_id": f"watchdog_test_{i}",
                "event_type": "user_prompt",
                "payload": json.dumps({"message": f"Normal support request #{i}"}),
                "timestamp": time.time()
            }
            try:
                await client.post(GATEWAY_URL, json=payload)
                print(f"  Sent normal event #{i}")
            except Exception as e:
                print(f"  Failed to send event #{i}: {e}")
        
        await asyncio.sleep(1)

        # Phase 2: Trigger a reasoning loop (graph cycle)
        print("\n[Phase 2] Injecting reasoning loop (graph cycle)...")
        session_id = "watchdog_loop_test"
        loop_components = ["PlannerAgent", "ResearchAgent", "CriticAgent", "PlannerAgent", "ResearchAgent", "CriticAgent"]
        for comp in loop_components:
            payload = {
                "session_id": session_id,
                "task_id": session_id,
                "event_type": "AGENT_COMPLETED",
                "payload": json.dumps({"component": comp, "tool_name": "analyze"}),
                "timestamp": time.time()
            }
            try:
                await client.post(GATEWAY_URL, json=payload)
                print(f"  Sent loop event: {comp}")
            except Exception as e:
                print(f"  Failed: {e}")

        await asyncio.sleep(1)

        # Phase 3: Trigger rapid failures (spike failure_rate)
        print("\n[Phase 3] Injecting rapid TASK_FAILED events...")
        for i in range(10):
            payload = {
                "session_id": f"fail_test_{i}",
                "task_id": f"fail_test_{i}",
                "event_type": "TASK_FAILED",
                "payload": json.dumps({"error": f"Simulated failure #{i}"}),
                "timestamp": time.time()
            }
            try:
                await client.post(GATEWAY_URL, json=payload)
                print(f"  Sent failure event #{i}")
            except Exception as e:
                print(f"  Failed: {e}")

        await asyncio.sleep(1)

        # Phase 4: Trigger tool repetition loop
        print("\n[Phase 4] Injecting repeated identical tool calls...")
        for i in range(6):
            payload = {
                "session_id": "tool_loop_test",
                "task_id": "tool_loop_test",
                "event_type": "tool_call",
                "payload": json.dumps({"tool_name": "process_refund", "arguments": {"order_id": "12345"}}),
                "timestamp": time.time()
            }
            try:
                await client.post(GATEWAY_URL, json=payload)
                print(f"  Sent repeated tool_call #{i}")
            except Exception as e:
                print(f"  Failed: {e}")

    print("\n--- Watchdog Diagnostic Test Complete ---")
    print("Check the frontend UI for anomaly alerts in the Watchdog Alerts counter and Agent Invocations panel.")

if __name__ == "__main__":
    asyncio.run(main())
