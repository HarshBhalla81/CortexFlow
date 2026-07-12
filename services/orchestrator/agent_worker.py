import os
import time
import json
import asyncio
import httpx
from datetime import datetime

from llm_adapters.factory import LLMAdapterFactory

DATA_FILE = "/app/data/agentic_events.csv"
GATEWAY_URL = os.getenv("GATEWAY_URL", "http://gateway:8000/request")

# Mock tools schema for Dynamic Support Tiering
SUPPORT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "process_refund",
            "description": "Issue a refund for a given support ticket.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticket_id": {"type": "string"},
                    "amount": {"type": "number"}
                },
                "required": ["ticket_id", "amount"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "escalate_to_human",
            "description": "Escalate the ticket to a human agent.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticket_id": {"type": "string"},
                    "reason": {"type": "string"}
                },
                "required": ["ticket_id", "reason"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "reset_password",
            "description": "Send a password reset link to the user.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_email": {"type": "string"}
                },
                "required": ["user_email"]
            }
        }
    }
]

async def dispatch_to_gateway(client: httpx.AsyncClient, session_id: str, event_type: str, payload: dict):
    # Sends an event back to the Gateway, which forwards it to Pathway
    task_payload = {
        "task_id": session_id,
        "task_type": event_type,
        "payload": payload,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    try:
        response = await client.post(GATEWAY_URL, json=task_payload)
        response.raise_for_status()
    except Exception as e:
        print(f"[AGENT WORKER] Failed to send to Gateway: {e}")

async def process_user_prompt(session_id: str, payload_str: str, adapter):
    try:
        # payload_str might be JSON encoded string
        payload = json.loads(payload_str)
        user_message = payload.get("message", payload_str)
    except:
        user_message = payload_str

    messages = [
        {"role": "system", "content": "You are a customer support agent. Resolve the user's issue using available tools."},
        {"role": "user", "content": f"Ticket ID: {session_id}\nIssue: {user_message}"}
    ]

    print(f"[AGENT WORKER] Processing session {session_id} with LLM...")
    response = await adapter.generate_response(messages, tools=SUPPORT_TOOLS)
    
    async with httpx.AsyncClient() as client:
        # Send thoughts back to stream
        if response.get("content"):
            await dispatch_to_gateway(
                client, 
                session_id, 
                "model_thought", 
                {"thought": response["content"]}
            )
        
        # Send tool calls back to stream
        for tc in response.get("tool_calls", []):
            await dispatch_to_gateway(
                client,
                session_id,
                "tool_call",
                {"tool_name": tc.get("name"), "arguments": tc.get("arguments")}
            )

async def main():
    print("[AGENT WORKER] Starting up...")
    
    provider = os.getenv("LLM_PROVIDER", "openai")
    adapter = LLMAdapterFactory.get_adapter(provider)
    
    last_pos = 0
    while True:
        if not os.path.exists(DATA_FILE):
            await asyncio.sleep(1)
            continue
            
        with open(DATA_FILE, 'r') as f:
            f.seek(last_pos)
            lines = f.readlines()
            last_pos = f.tell()
            
            if not lines:
                await asyncio.sleep(1)
                continue
                
            for line in lines:
                parts = line.strip().split(',')
                if len(parts) >= 5 and parts[0] != "session_id":
                    session_id = parts[0]
                    event_type = parts[2]
                    payload_str = parts[3]
                    
                    if event_type == "user_prompt":
                        # Fire and forget processing
                        asyncio.create_task(process_user_prompt(session_id, payload_str, adapter))

if __name__ == "__main__":
    asyncio.run(main())
