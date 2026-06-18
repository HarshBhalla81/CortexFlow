# Implementation Plan: Gateway-to-Pathway Bridge

This document outlines the proposed changes to the FastAPI gateway in `gateway/main.py` to establish an asynchronous, non-blocking bridge to the Pathway ingestion endpoint at `http://localhost:8080/`.

---

## 1. Context & Objectives

*   **FastAPI Gateway**: Running on `localhost:8000` (defined in `services/gateway/main.py`), acting as the primary entry point.
*   **Pathway Ingestion Endpoint**: Running on `localhost:8080`, performing real-time stream processing and event analytics.
*   **Missing File Notice**: Although `poc/pathway_stream.py` was referenced as defining the Pathway stream engine, it was not found in the workspace directory. For the purposes of this bridge, we assume the Pathway engine exposes an HTTP server at `http://localhost:8080/` (typically using `pw.io.http.rest_connector` or similar).

### Core Goals
1.  **Asynchronous Forwarding**: Forward the payload of the `/process` route in `gateway/main.py` using `httpx.AsyncClient` to `http://localhost:8080/`.
2.  **Non-Blocking Behavior**: Ensure that requests to the gateway are processed without blocking the FastAPI event loop.
3.  **Resilience**: Gracefully handle connection issues, timeouts, or downtime of the Pathway engine without crashing the gateway.
4.  **Efficiency**: Utilize a shared, persistent connection pool instead of instantiating `httpx.AsyncClient` on every request.

---

## 2. Analysis of Current Implementation

The current local modifications in `services/gateway/main.py` use an ad-hoc client instantiation inside the request handler:

```python
@app.post("/process")
async def process_event(payload: dict = Body(...)):
    try:
        async with httpx.AsyncClient() as client:
            await client.post("http://localhost:8080/", json=payload)
    except Exception:
        pass
    return {"status": "success"}
```

### Limitations of Current Approach:
*   **Connection Overhead**: Opening and closing a client on every request defeats the benefits of connection pooling (TCP connection re-use), which degrades performance under high throughput.
*   **Awaited HTTP Request**: Awaiting `client.post` directly in the endpoint handler holds the client's request connection open until Pathway responds. If Pathway is slow, the FastAPI gateway responses will be delayed.

---

## 3. Proposed Enhancements

### A. Shared Lifespan Client (Recommended)
We will manage the lifespan of the `httpx.AsyncClient` using FastAPI's `lifespan` event handler. This opens the connection pool when FastAPI starts and closes it gracefully on shutdown.

```python
from contextlib import asynccontextmanager
import httpx
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize shared HTTP client
    app.state.http_client = httpx.AsyncClient(timeout=5.0)
    yield
    # Shutdown: Close client session
    await app.state.http_client.aclose()

app = FastAPI(lifespan=lifespan)
```

### B. Configuration Management
Instead of hardcoding `"http://localhost:8080/"`, we will read the Pathway endpoint URL from environment variables, defaulting to `http://localhost:8080/`.

```python
import os

PATHWAY_URL = os.getenv("PATHWAY_URL", "http://localhost:8080/")
```

### C. Background Event Forwarding (Optional/Resilient)
To make the route fully non-blocking for callers, we can use FastAPI's `BackgroundTasks`. The gateway will respond immediately with HTTP 202 (Accepted) or 200 (OK), and forward the request to Pathway in the background.

```python
from fastapi import BackgroundTasks

async def forward_to_pathway(client: httpx.AsyncClient, payload: dict):
    try:
        response = await client.post(PATHWAY_URL, json=payload)
        response.raise_for_status()
    except httpx.HTTPError as e:
        # Log error or send to dead-letter queue (DLQ)
        pass

@app.post("/process")
async def process_event(
    payload: dict = Body(...),
    background_tasks: BackgroundTasks = None
):
    # Get client from request state or dependency injection
    client = app.state.http_client
    background_tasks.add_task(forward_to_pathway, client, payload)
    return {"status": "success"}
```

---

## 4. Concrete Steps for Implementation

1.  **Introduce Lifespan Context Manager**: Modify `services/gateway/main.py` to add `lifespan` control and bind `httpx.AsyncClient` to `app.state.http_client`.
2.  **Define Configuration**: Pull `PATHWAY_URL` from the environment.
3.  **Update `/process` Endpoint**:
    *   Inject `Request` to access the stateful `http_client`.
    *   Perform async post using the shared client.
    *   Add robust exception logging for `httpx.RequestError` and timeout handling.
4.  **Validate via Tests**: Run the existing test suite (`tests/test_bridge.py`) to verify functionality.

---

## 5. Verification Plan

### Automated Tests
Run python tests using `pytest` inside the virtual environment:
```bash
# Locate active python/pytest in virtual environment
# Run test suite
python -m pytest tests/test_bridge.py
```

### Manual Verification
1.  Start the FastAPI Gateway on port `8000`.
2.  Send a test POST request to `http://localhost:8000/process` using `curl` or Postman.
3.  Observe response codes and console logs.
