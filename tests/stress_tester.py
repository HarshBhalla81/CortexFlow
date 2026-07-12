import asyncio
import httpx
import time
import json
import random

GATEWAY_URL = "http://localhost:8000/process"
TOTAL_REQUESTS = 20
CONCURRENCY_LIMIT = 5

# Mock anomaly (infinite loop) injection parameters
INJECT_ANOMALY = True
ANOMALY_INDEX = 10  # Inject poison pill at the 10th request

# Diverse event types that the watchdog's FeatureExtractor understands
EVENT_TYPES = [
    "user_prompt",
    "TASK_STARTED",
    "TASK_COMPLETED",
    "TASK_FAILED",
    "RETRY_TRIGGERED",
    "tool_call",
    "AGENT_COMPLETED",
    "WORKER_COMPLETED",
]

# Component names for graph cycle detection
COMPONENTS = [
    "PlannerAgent",
    "ResearchAgent",
    "CriticAgent",
    "SummarizationAgent",
    "QAAgent",
]


async def send_request(client: httpx.AsyncClient, index: int):
    # ----- Anomaly Injection: reasoning loop (same task, cycling components) -----
    if INJECT_ANOMALY and index == ANOMALY_INDEX:
        session_id = f"anomaly_session_{index}"
        print(f"[STRESS TEST] Injecting Poison Pill for session: {session_id}")

        # Simulate a reasoning loop: Planner -> Research -> Critic -> Planner
        loop_components = ["PlannerAgent", "ResearchAgent", "CriticAgent", "PlannerAgent"]
        for comp in loop_components:
            payload = {
                "session_id": session_id,
                "task_id": session_id,
                "event_type": "AGENT_COMPLETED",
                "payload": json.dumps({"component": comp, "tool_name": "process_refund"}),
                "timestamp": time.time()
            }
            await client.post(GATEWAY_URL, json=payload)

        # Also inject rapid TASK_FAILED events to spike failure_rate
        for _ in range(5):
            payload = {
                "session_id": session_id,
                "task_id": f"fail_{session_id}_{_}",
                "event_type": "TASK_FAILED",
                "payload": json.dumps({"error": "Simulated crash for anomaly injection"}),
                "timestamp": time.time()
            }
            await client.post(GATEWAY_URL, json=payload)
        return

    # ----- Normal traffic: force user prompts with diverse tasks -----
    session_id = f"test_ticket_{index}"
    event_type = "user_prompt"
    
    prompts = [
        "I need a refund for my last order.",
        "I'm locked out of my account, please reset my password.",
        "How do I track my shipment?",
        "I need to speak to a human manager immediately!",
        "My billing address is incorrect, how do I change it?"
    ]

    payload = {
        "session_id": session_id,
        "task_id": session_id,
        "event_type": event_type,
        "payload": json.dumps({
            "message": random.choice(prompts)
        }),
        "timestamp": time.time()
    }

    start_time = time.time()
    try:
        response = await client.post(GATEWAY_URL, json=payload)
        response.raise_for_status()
    except Exception as e:
        print(f"[STRESS TEST] Request {index} failed: {e}")


async def main():
    print(f"Starting Stress Test: {TOTAL_REQUESTS} requests at {CONCURRENCY_LIMIT} concurrency.")
    print(f"Event types: {EVENT_TYPES}")
    print(f"Anomaly injection at request #{ANOMALY_INDEX}")

    semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)

    async with httpx.AsyncClient(timeout=30.0) as client:
        async def bounded_request(index):
            async with semaphore:
                await send_request(client, index)

        tasks = [bounded_request(i) for i in range(TOTAL_REQUESTS)]

        start = time.time()
        await asyncio.gather(*tasks)
        end = time.time()

    duration = end - start
    print(f"\n--- Stress Test Completed ---")
    print(f"Total Time: {duration:.2f} seconds")
    print(f"Throughput: {TOTAL_REQUESTS / duration:.2f} requests/second")


if __name__ == "__main__":
    asyncio.run(main())
