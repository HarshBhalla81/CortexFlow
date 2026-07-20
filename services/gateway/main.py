import os
import json
import time
import logging
import asyncio
from contextlib import asynccontextmanager
import httpx
from fastapi import FastAPI, Body, Request, WebSocket, WebSocketDisconnect
import redis.asyncio as redis

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
    # Initialize Redis client for live event publishing
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
    app.state.redis_client = redis.from_url(redis_url)
    yield
    # Shutdown: Close clients
    await app.state.http_client.aclose()
    await app.state.redis_client.aclose()

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
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
    redis_client = None
    pubsub = None
    try:
        redis_client = redis.from_url(redis_url)
        pubsub = redis_client.pubsub()
        await pubsub.subscribe("telemetry_stream")
        
        async for message in pubsub.listen():
            if message['type'] == 'message':
                data = json.loads(message['data'])
                await websocket.send_json(data)
    except WebSocketDisconnect:
        logger.info("Telemetry client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        try:
            if pubsub:
                await pubsub.unsubscribe("telemetry_stream")
            if redis_client:
                await redis_client.aclose()
        except:
            pass



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
    
    # Instantly publish to Redis for live frontend streaming
    redis_client = getattr(request.app.state, "redis_client", None)
    if redis_client:
        try:
            # Build the message the frontend expects
            event_type = normalized.get("event_type", "")
            msg = {
                "event_type": event_type,
                "session_id": normalized.get("session_id"),
                "task_id": normalized.get("task_id")
            }
            # Parse the payload string back to dict for the frontend
            try:
                parsed_payload = json.loads(normalized.get("payload", "{}"))
            except (json.JSONDecodeError, TypeError):
                parsed_payload = {}
            
            if event_type == "user_prompt":
                msg["payload"] = parsed_payload
            elif event_type == "tool_call":
                msg["tool_name"] = parsed_payload.get("tool_name", "unknown")
                msg["arguments"] = parsed_payload.get("arguments", {})
            elif event_type == "model_thought":
                msg["thought"] = parsed_payload.get("thought", "")
            else:
                msg["payload"] = parsed_payload
            
            await redis_client.publish("telemetry_stream", json.dumps(msg))
        except Exception as e:
            logger.error(f"Redis publish error: {e}")
    
    # Forward to Pathway for processing
    client = getattr(request.app.state, "http_client", None)
    if client is not None:
        await _forward_with_retry(client, PATHWAY_URL, normalized)
    else:
        try:
            limits = httpx.Limits(max_connections=100, max_keepalive_connections=20)
            async with httpx.AsyncClient(timeout=30.0, limits=limits) as fallback_client:
                await _forward_with_retry(fallback_client, PATHWAY_URL, normalized)
        except Exception as e:
            logger.error(f"Unexpected error in fallback client: {e}")
            
    return {"status": "success"}