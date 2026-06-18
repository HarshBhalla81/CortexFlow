import os
import json
import time
import logging
import asyncio
from contextlib import asynccontextmanager
import httpx
from fastapi import FastAPI, Body, Request, WebSocket, WebSocketDisconnect

from routing.health import router as health_router
from routing.task import router as task_router
from routing.results import router as result_router

from utils import PATHWAY_URL, _forward_with_retry

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize shared HTTP client with higher timeout and connection limits for stress testing
    limits = httpx.Limits(max_connections=100, max_keepalive_connections=20)
    app.state.http_client = httpx.AsyncClient(timeout=30.0, limits=limits)
    yield
    # Shutdown: Close client session
    await app.state.http_client.aclose()

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(task_router)
app.include_router(result_router)
app.include_router(health_router)

@app.get("/")
async def root():
    return {"message": "Gateway Running"}

@app.get("/metrics")
def get_metrics():
    return {
        "status": "in-memory-stub",
        "active_agents": 3,
        "events_per_sec": 5.2
    }

@app.websocket("/ws/telemetry")
async def telemetry_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # Stream live telemetry metrics
            await asyncio.sleep(2)
            # In a real scenario, this reads from Pathway's live telemetry or Redis
            await websocket.send_json({"status": "live", "metrics": {"events_per_sec": 5.2, "active_agents": 3}})
    except WebSocketDisconnect:
        logger.info("Telemetry client disconnected")



def _normalize_payload(payload: dict) -> dict:
    """Transform any incoming payload format into Pathway's AgenticEventSchema."""
    normalized = {}
    normalized["session_id"] = payload.get("session_id") or payload.get("task_id", f"auto-{int(time.time()*1000)}")
    normalized["task_id"] = payload.get("task_id", normalized["session_id"])
    normalized["event_type"] = payload.get("event_type") or payload.get("task_type", "user_prompt")
    
    raw_payload = payload.get("payload", "")
    if isinstance(raw_payload, dict):
        normalized["payload"] = json.dumps(raw_payload)
    else:
        normalized["payload"] = str(raw_payload)
    
    normalized["timestamp"] = payload.get("timestamp", time.time())
    return normalized


@app.post("/process")
async def process_event(request: Request, payload: dict = Body(...)):
    normalized = _normalize_payload(payload)
    client = getattr(request.app.state, "http_client", None)
    if client is not None:
        await _forward_with_retry(client, PATHWAY_URL, normalized)
    else:
        # Fallback if lifespan client is not initialized (e.g. in some TestClient scenarios)
        try:
            limits = httpx.Limits(max_connections=100, max_keepalive_connections=20)
            async with httpx.AsyncClient(timeout=30.0, limits=limits) as fallback_client:
                await _forward_with_retry(fallback_client, PATHWAY_URL, normalized)
        except Exception as e:
            logger.error(f"Unexpected error in fallback client: {e}")
            
    return {"status": "success"}