# Design: Gateway-to-Pathway Bridge
## Goal
Forward incoming task requests from the FastAPI gateway to the Pathway ingestion endpoint.

## Scope
- Modify: `gateway/main.py`
- Target: `http://localhost:8080/`
- Method: `POST` (Async)

## Success Criteria
1. FastAPI successfully receives a POST request.
2. The payload is forwarded to Pathway without blocking the FastAPI event loop.
3. No change to existing Redis functionality (for now).