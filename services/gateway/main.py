import os
import logging
import asyncio
from contextlib import asynccontextmanager
import httpx
from fastapi import FastAPI, Body, Request, WebSocket, WebSocketDisconnect

from routing.health import router as health_router
from routing.task import router as task_router
from routing.results import router as result_router
from shared.metrics import metrics
from utils import PATHWAY_URL, _forward_with_retry

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize shared HTTP client
    app.state.http_client = httpx.AsyncClient(timeout=5.0)
    yield
    # Shutdown: Close client session
    await app.state.http_client.aclose()

app = FastAPI(lifespan=lifespan)

app.include_router(task_router)
app.include_router(result_router)
app.include_router(health_router)

@app.get("/")
async def root():
    return {"message": "Gateway Running"}

@app.get("/metrics")
def get_metrics():
    return metrics.get_metrics()

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



@app.post("/process")
async def process_event(request: Request, payload: dict = Body(...)):
    client = getattr(request.app.state, "http_client", None)
    if client is not None:
        await _forward_with_retry(client, PATHWAY_URL, payload)
    else:
        # Fallback if lifespan client is not initialized (e.g. in some TestClient scenarios)
        try:
            async with httpx.AsyncClient(timeout=5.0) as fallback_client:
                await _forward_with_retry(fallback_client, PATHWAY_URL, payload)
        except Exception as e:
            logger.error(f"Unexpected error in fallback client: {e}")
            
    return {"status": "success"}