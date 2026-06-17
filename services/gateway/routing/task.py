import json
import httpx
from datetime import datetime

from fastapi import APIRouter, Request
from shared.models.task import Task
from utils import PATHWAY_URL, _forward_with_retry

router = APIRouter()

@router.post("/request")
async def process_request(request: Request, data: Task):

    payload = data.model_dump()
    task_id = payload["task_id"]
    
    # Map to AgenticEventSchema
    agentic_event = {
        "session_id": task_id,
        "task_id": task_id,
        "event_type": payload["task_type"],
        "payload": json.dumps(payload["payload"]),
        "timestamp": data.timestamp.timestamp()
    }
    
    # Forward directly to Pathway Engine
    client = getattr(request.app.state, "http_client", None)
    if client is not None:
        await _forward_with_retry(client, PATHWAY_URL, agentic_event)
    else:
        async with httpx.AsyncClient(timeout=5.0) as fallback_client:
            await _forward_with_retry(fallback_client, PATHWAY_URL, agentic_event)
            
    return {
        "status": "queued",
        "task_id": task_id,
    }