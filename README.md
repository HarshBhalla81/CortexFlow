<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/FastAPI-0.100%2B-009688?logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Pathway-Streaming-4ade80?logo=data:image/svg+xml;base64,..." alt="Pathway" />
  <img src="https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white" alt="Docker" />
  <img src="https://img.shields.io/badge/License-MIT-yellow" alt="License" />
</p>

# 🧠 CortexFlow — Fault-Tolerant Agentic Gateway with Real-Time Stream Processing

> A containerized, multi-service gateway for orchestrating autonomous AI agents with Pathway-powered real-time streaming, a Neural Watchdog for anomaly detection & reasoning-loop termination, and a live telemetry dashboard — built for high-throughput, zero-leaked-state execution.

---

## 📑 Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [System Architecture](#system-architecture)
- [Service Topology](#service-topology)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [API Reference](#api-reference)
- [Neural Watchdog (BDH)](#neural-watchdog-bdh)
- [Provider-Agnostic LLM Adapter Layer](#provider-agnostic-llm-adapter-layer)
- [Live Telemetry Dashboard](#live-telemetry-dashboard)
- [Stress Testing & Chaos Engineering](#stress-testing--chaos-engineering)
- [Testing](#testing)
- [Configuration](#configuration)
- [Demonstration Scenario: Dynamic Support Tiering](#demonstration-scenario-dynamic-support-tiering)

---

## Overview

**CortexFlow** is a production-grade, containerized multi-service gateway designed for orchestrating autonomous AI agent workflows. It ingests, normalizes, and routes agentic events (user prompts, model thoughts, tool calls, task completions) through a **Pathway real-time streaming backbone**, enabling live observability, anomaly detection, and fault-tolerant execution.

The system is purpose-built to address critical challenges in agentic AI infrastructure:

- **Reasoning Loops** — Autonomous agents can enter infinite cycles (e.g., Planner → Researcher → Critic → Planner). CortexFlow detects and terminates these via directed-graph cycle detection (DFS).
- **State Leakage** — Events are immutably streamed through Pathway with zero mutable shared state between services.
- **Provider Lock-In** — A decoupled adapter layer abstracts away LLM provider differences (OpenAI, Anthropic, vLLM, Groq, OpenRouter).
- **Throughput Bottlenecks** — Asynchronous, non-blocking forwarding with connection pooling and exponential backoff retry handles high-concurrency loads.

---

## Key Features

| Category | Feature |
|---|---|
| **Streaming** | Pathway-powered real-time event ingestion via `pw.io.http.rest_connector` with CSV output sinks |
| **Fault Tolerance** | Exponential backoff retry (3 attempts), shared `httpx.AsyncClient` with connection pooling (100 max connections) |
| **Anomaly Detection** | Isolation Forest (scikit-learn) trained online on 8-dimensional feature vectors extracted from live event streams |
| **Cycle Detection** | Markov-based reasoning loop detection on directed task graphs, catching infinite agent handoff cycles |
| **LLM Abstraction** | Provider-agnostic adapter pattern supporting OpenAI, Anthropic, vLLM, Groq, and OpenRouter |
| **Tool Validation** | Pydantic `ToolDispatchSchema` normalizes heterogeneous LLM function-calling formats before streaming |
| **Vector Store** | FAISS-based similarity search with persistent index storage for context retrieval |
| **Live Dashboard** | WebSocket-driven telemetry dashboard with real-time throughput (EPS), latency (TTFT), and watchdog alert counters |
| **Stress Testing** | Configurable load generator (1000 requests, 50 concurrent) with anomaly injection (poison pill at request #500) |
| **Containerization** | Full Docker Compose orchestration with 6 services, Nginx reverse proxy, and isolated `cortex-net` bridge network |

---

## System Architecture

```
                    ┌─────────────────────────────────────────────┐
                    │              Nginx Reverse Proxy (:80)      │
                    │          /  → Frontend   /api/ → Gateway    │
                    └────────────┬────────────────┬───────────────┘
                                 │                │
              ┌──────────────────▼──┐    ┌────────▼──────────────┐
              │   Frontend (:3000)  │    │   Gateway (:8000)     │
              │   - Live Dashboard  │◄──►│   - FastAPI           │
              │   - WebSocket       │ WS │   - /process          │
              │   - Stress Trigger  │    │   - /request          │
              └─────────────────────┘    │   - /ws/telemetry     │
                                         │   - /health, /metrics │
                                         └────────┬──────────────┘
                                                   │ async POST
                                                   │ (httpx + retry)
                                         ┌─────────▼──────────────┐
                                         │ Pathway Engine (:8080)  │
                                         │ - REST Connector        │
                                         │ - AgenticEventSchema    │
                                         │ - CSV Sink (dual)       │
                                         └──┬──────────────┬───────┘
                                            │              │
                              ┌─────────────▼──┐    ┌──────▼──────────┐
                              │  Agent Worker   │    │  BDH Watchdog   │
                              │  - CSV Tailer   │    │  - CSV Tailer   │
                              │  - LLM Adapter  │    │  - Feature Ext. │
                              │  - Tool Calls   │    │  - Markov Trans    │
                              │  - Dispatch Loop│    │  - Isolation     │
                              └────────────────┘     │    Forest       │
                                                     │  - Alert Mgr    │
                                                     └─────────────────┘
```

### Data Flow

1. **Ingestion** — Client sends an event to the Gateway (`POST /process` or `POST /request`)
2. **Normalization** — Gateway normalizes the payload to Pathway's `AgenticEventSchema`
3. **Forwarding** — Async HTTP POST with exponential backoff retry to the Pathway Engine
4. **Stream Processing** — Pathway ingests the event, writes to dual CSV sinks (`agentic_events.csv` and `tool_events_watchdog.csv`)
5. **Agent Processing** — Agent Worker tails `agentic_events.csv`, processes `user_prompt` events through the LLM adapter, and dispatches tool calls back through the Gateway
6. **Watchdog Monitoring** — BDH Watchdog tails `tool_events_watchdog.csv`, extracts features, runs anomaly scoring, and performs cycle detection
7. **Telemetry** — Gateway streams live metrics to the Frontend via WebSocket

---

## Service Topology

| Service | Container Name | Port | Description |
|---|---|---|---|
| **Gateway** | `gateway` | `8000` | FastAPI entry point; normalizes and forwards events to Pathway |
| **Pathway Engine** | `pathway_engine` | `8080` | Real-time stream processor; HTTP REST ingestion → CSV output |
| **Agent Worker** | `cortex_agent_worker` | — | Async CSV tailer; dispatches user prompts to LLM adapters |
| **BDH Watchdog** | `cortex_watchdog` | — | Neural anomaly detector; Isolation Forest + Markov anomaly detection |
| **Frontend** | `cortex_frontend` | `3000` | Live telemetry dashboard with WebSocket connectivity |
| **Nginx** | `cortex_proxy` | `80` | Reverse proxy routing `/` → Frontend, `/api/` → Gateway |

All services communicate over an isolated Docker bridge network (`cortex-net`).

---

## Tech Stack

| Layer | Technology |
|---|---|
| **API Gateway** | FastAPI, Uvicorn, httpx (async client with connection pooling) |
| **Stream Processing** | Pathway (`pw.io.http.rest_connector`, `pw.io.csv.write`) |
| **Machine Learning** | scikit-learn (Isolation Forest), NumPy, FAISS (vector search) |
| **LLM Providers** | OpenAI, Anthropic, vLLM, Groq, OpenRouter |
| **Data Validation** | Pydantic (BaseModel, ToolDispatchSchema) |
| **NLP** | Sentence-Transformers (`all-MiniLM-L6-v2`), LangChain Text Splitters |
| **Frontend** | Vanilla HTML/CSS/JS, WebSocket API, Inter font |
| **Infrastructure** | Docker, Docker Compose, Nginx (Alpine) |
| **Testing** | pytest, httpx (integration), custom stress tester |

---

## Project Structure

```
CortexFlow/
├── docker-compose.yml              # Multi-service orchestration (6 containers)
├── .env                            # API keys (GROQ, OpenRouter, OpenAI)
├── nginx/
│   └── nginx.conf                  # Reverse proxy routing rules
│
├── services/
│   ├── gateway/                    # FastAPI Gateway Service
│   │   ├── Dockerfile
│   │   ├── main.py                 # Lifespan-managed httpx client, CORS, WebSocket telemetry
│   │   ├── utils.py                # PATHWAY_URL config, _forward_with_retry (exponential backoff)
│   │   ├── requirements.txt
│   │   └── routing/
│   │       ├── task.py             # POST /request — Task ingestion with Pydantic validation
│   │       ├── results.py          # GET /result/{task_id} — Result retrieval stub
│   │       └── health.py           # GET /health — Service health check
│   │
│   ├── pathway_engine/             # Pathway Streaming Engine
│   │   ├── Dockerfile
│   │   ├── main.py                 # AgenticEventSchema, REST connector, dual CSV sinks
│   │   └── requirements.txt
│   │
│   ├── orchestrator/               # Agent Worker + BDH Watchdog
│   │   ├── Dockerfile
│   │   ├── agent_worker.py         # Async CSV tailer, LLM dispatch, tool call routing
│   │   ├── watchdog_runner.py      # Watchdog bootstrap entry point
│   │   ├── requirements.txt
│   │   ├── llm_adapters/           # Provider-Agnostic LLM Layer
│   │   │   ├── base.py             # Abstract BaseLLMAdapter (ABC)
│   │   │   ├── factory.py          # LLMAdapterFactory — runtime provider selection
│   │   │   ├── openai_adapter.py   # OpenAI GPT-4o-mini adapter
│   │   │   ├── anthropic_adapter.py# Anthropic Claude adapter (tool format conversion)
│   │   │   └── vllm_adapter.py     # Local vLLM adapter (OpenAI-compatible)
│   │   ├── watchdog/               # Neural BDH Watchdog Pipeline
│   │   │   ├── watchdog.py         # Main pipeline orchestrator
│   │   │   ├── feature_extractor.py# 8-dimensional feature vector builder (sliding window)
│   │   │   ├── graph_analyzer.py   # Directed graph builder + Markov anomaly detection
│   │   │   ├── anomaly_detector.py # Isolation Forest (online training, scoring)
│   │   │   ├── alert_manager.py    # Alert publishing (REASONING_LOOP, ANOMALY)
│   │   │   └── models.py           # EventFeatures dataclass
│   │   ├── schemas/
│   │   │   └── tool_contract.py    # Pydantic ToolDispatchSchema + validation
│   │   ├── vectorstore/
│   │   │   ├── faiss_store.py      # FAISS IndexFlatL2 with persistence
│   │   │   └── store.py            # Store interface
│   │   └── tools/
│   │       ├── base_tool.py        # BaseTool abstract class
│   │       ├── groq_tool.py        # Groq LLaMA-3.3-70B tool
│   │       └── openrouter_tool.py  # OpenRouter DeepSeek tool
│   │
│   └── tools/
│       └── support_tools.py        # Mock tool microservice (process_refund, escalate_to_human)
│
├── frontend/                       # Live Telemetry Dashboard
│   ├── Dockerfile
│   ├── index.html                  # Dashboard UI (metrics cards, log streams)
│   ├── app.js                      # WebSocket client, stress test trigger, log management
│   └── style.css                   # Glassmorphism design, dark theme, animations
│
├── shared/                         # Cross-Service Shared Models
│   ├── models/
│   │   ├── event.py                # Event Pydantic model
│   │   ├── task.py                 # Task Pydantic model
│   │   └── result.py               # TaskResult Pydantic model
│   ├── document.py                 # Document model
│   └── logging_config.py           # Centralized logging configuration
│
├── data/                           # Pathway CSV Output Sinks
│   ├── agentic_events.csv          # Full event log (Agent Worker reads)
│   └── tool_events_watchdog.csv    # Watchdog event log (BDH Watchdog reads)
│
├── tests/                          # Test Suite
│   ├── stress_tester.py            # Async load generator (1000 req, 50 concurrency, anomaly injection)
│   ├── test_bridge.py              # Gateway ↔ Pathway connectivity verification
│   ├── test_pathway_stream.py      # End-to-end Pathway ingestion + CSV output test
│   ├── test_events.py              # Normal workflow + reasoning loop test fixtures
│   ├── watchdog_test_cases.py      # Graph cycle detection unit tests
│   └── metrics_analyzer.py         # Post-test CSV metrics analysis
│
└── docs/                           # Technical Documentation
    ├── bridge_plan.md              # Gateway-to-Pathway bridge implementation plan
    └── design.md                   # Bridge design specification
```

---

## Getting Started

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) & [Docker Compose](https://docs.docker.com/compose/install/)
- API keys for at least one LLM provider (OpenAI, Groq, or OpenRouter)

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/CortexFlow.git
cd CortexFlow
```

### 2. Configure Environment Variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

### 3. Build and Launch All Services

```bash
docker-compose up --build
```

This spins up **6 containers** on an isolated Docker bridge network:

| Container | URL |
|---|---|
| Dashboard | [http://localhost:80](http://localhost:80) |
| Gateway API | [http://localhost:8000](http://localhost:8000) |
| Pathway Engine | [http://localhost:8080](http://localhost:8080) |
| Frontend (direct) | [http://localhost:3000](http://localhost:3000) |

### 4. Verify Health

```bash
curl http://localhost:8000/health
# {"status": "healthy", "message": "Pathway Agentic Gateway is running"}
```

### 5. Send a Test Event

```bash
curl -X POST http://localhost:8000/process \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "demo-001",
    "task_id": "demo-001",
    "event_type": "user_prompt",
    "payload": "{\"message\": \"I need a refund for order #12345\"}",
    "timestamp": 1718700000.0
  }'
```

---

## API Reference

### Gateway Service (`:8000`)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Root status check |
| `GET` | `/health` | Service health check |
| `GET` | `/metrics` | System metrics (throughput, active agents) |
| `POST` | `/process` | Ingest raw event → normalize → forward to Pathway |
| `POST` | `/request` | Ingest typed Task (Pydantic validated) → forward to Pathway |
| `GET` | `/result/{task_id}` | Query task result (stub — Pathway writes directly to CSV) |
| `WS` | `/ws/telemetry` | Live WebSocket telemetry stream |

### Pathway Engine (`:8080`)

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/` | Ingest event matching `AgenticEventSchema` |

#### `AgenticEventSchema`

```json
{
  "session_id": "string",
  "task_id": "string",
  "event_type": "string",
  "payload": "string",
  "timestamp": 0.0
}
```

---

## Neural Watchdog (BDH)

The **Behavioral Drift & Hallucination (BDH) Watchdog** is an asynchronous, non-blocking monitoring pipeline that performs real-time anomaly detection on the agentic event stream.

### Pipeline Stages

```
Event Stream (CSV) → Feature Extraction → Graph Analysis → Anomaly Scoring → Alert Publishing
```

### 1. Feature Extraction (`feature_extractor.py`)

Extracts an **8-dimensional feature vector** from a sliding window of the last 500 events:

| Feature | Description |
|---|---|
| `failure_rate` | Ratio of `TASK_FAILED` events to total events |
| `retry_rate` | Ratio of `RETRY_TRIGGERED` events to total events |
| `avg_latency` | Mean time between `TASK_STARTED` and `TASK_COMPLETED` |
| `queue_depth` | Number of queued items (currently reserved) |
| `throughput` | Ratio of `TASK_COMPLETED` events to total events |
| `active_tasks` | Count of currently in-progress tasks |
| `agent_failure_rate` | Agent-level failure rate |
| `worker_failure_rate` | Worker-level failure rate |

### 2. Graph Cycle Detection (`graph_analyzer.py`)

Builds a **directed graph** of component handoffs per task (e.g., `PlannerAgent → ResearchAgent → CriticAgent`) and uses **DFS with a recursion stack** to detect reasoning loops:

```
If CriticAgent → PlannerAgent (cycle!) → REASONING_LOOP alert triggered
```

### 3. Anomaly Scoring (`anomaly_detector.py`)

- **Algorithm**: Isolation Forest (`sklearn.ensemble.IsolationForest`)
- **Contamination**: 5%
- **Training**: Online — model trains after 20 samples, retrains every 100 samples
- **Scoring**: `decision_function()` returns anomaly score; `predict() == -1` → anomaly

### 4. Alert Manager (`alert_manager.py`)

Publishes structured alerts with severity levels:

| Alert Type | Severity | Trigger |
|---|---|---|
| `REASONING_LOOP` | HIGH | DFS detects a cycle in the task's component graph |
| `ANOMALY` | MEDIUM | Isolation Forest prediction returns `-1` |

Alerts are forwarded back to the Gateway (`POST /process`) for streaming to the telemetry dashboard.

---

## Provider-Agnostic LLM Adapter Layer

CortexFlow abstracts LLM provider differences through a **Factory + Adapter pattern**:

```
BaseLLMAdapter (ABC)
├── OpenAIAdapter      → GPT-4o-mini (native tool calling)
├── AnthropicAdapter   → Claude 3 Haiku (tool format conversion)
├── VLLMAdapter        → Local models (OpenAI-compatible API)
├── GroqTool           → LLaMA-3.3-70B (Groq inference)
└── OpenRouterTool     → DeepSeek Chat v3 (OpenRouter routing)
```

### Key Design Decisions

- **Standardized Output**: All adapters return `{"content": str, "tool_calls": []}` regardless of provider
- **Tool Dispatch Validation**: Every tool call is validated against `ToolDispatchSchema` (Pydantic) before entering the Pathway stream
- **Runtime Selection**: `LLMAdapterFactory.get_adapter(provider)` resolves the adapter at runtime via `LLM_PROVIDER` environment variable

---

## Live Telemetry Dashboard

The frontend is a **real-time telemetry dashboard** connected to the Gateway via WebSocket:

### Metrics Panel
- **Throughput** — Events per second (EPS) from the Pathway stream
- **Latency (TTFT)** — Time to first token / processing latency
- **Watchdog Alerts** — Running count of anomaly and reasoning loop alerts

### Live Streams
- **Live Support Tickets** — Real-time feed of incoming user prompts
- **Agent Invocations & Tools** — Tool dispatches, LLM thoughts, and watchdog alerts

### Built-in Stress Test
One-click "Launch Stress Test" button fires **50 sequential requests** (100ms gap) from the browser, populating the live streams in real-time.

### Design
- Glassmorphism card UI with `backdrop-filter: blur(12px)`
- Dark theme with radial gradient backgrounds
- Slide-in animations for log entries
- Pulsing connection indicator orb
- Auto-scrolling, 50-entry capped log windows

---

## Stress Testing & Chaos Engineering

### Automated Stress Tester (`tests/stress_tester.py`)

```bash
python tests/stress_tester.py
```

| Parameter | Value |
|---|---|
| Total Requests | 1,000 |
| Concurrency Limit | 50 (semaphore-bounded) |
| Anomaly Injection | Poison pill at request #500 |
| Event Type Diversity | 8 event types (`user_prompt`, `TASK_STARTED`, `TASK_FAILED`, etc.) |
| Component Diversity | 5 agent components (for graph cycle testing) |

### Anomaly Injection (Chaos Engineering)

At request #500, the stress tester injects a **poison pill**:

1. **Reasoning Loop** — Sends 4 events cycling through `PlannerAgent → ResearchAgent → CriticAgent → PlannerAgent` on a single task
2. **Failure Spike** — Injects 5 rapid `TASK_FAILED` events to spike the failure rate

This validates that the BDH Watchdog correctly detects:
- ✅ The Markov anomaly detection triggers `REASONING_LOOP` alert
- ✅ The Isolation Forest flags the anomalous failure spike

### Post-Test Metrics Analysis

```bash
python tests/metrics_analyzer.py
```

Outputs total events processed, error count, and success rate from the Pathway CSV.

---

## Testing

### Unit Tests

```bash
# Graph cycle detection (normal workflow + reasoning loop)
python tests/watchdog_test_cases.py

# Gateway ↔ Pathway bridge connectivity
python tests/test_bridge.py
```

### Integration Tests

```bash
# Full Pathway stream ingestion → CSV output pipeline
python -m pytest tests/test_pathway_stream.py -v
```

### Stress Test

```bash
# 1000 requests with anomaly injection
python tests/stress_tester.py
```

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| `PATHWAY_URL` | `http://localhost:8080/` | Pathway Engine endpoint |
| `GATEWAY_URL` | `http://gateway:8000/request` | Gateway endpoint (for inter-service calls) |
| `LLM_PROVIDER` | `openai` | LLM adapter selection (`openai`, `anthropic`, `vllm`) |
| `OPENAI_API_KEY` | — | OpenAI API key |
| `GROQ_API_KEY` | — | Groq API key |
| `OPENROUTER_API_KEY` | — | OpenRouter API key |
| `ANTHROPIC_API_KEY` | — | Anthropic API key |
| `VLLM_BASE_URL` | `http://localhost:8000/v1` | Local vLLM server URL |

### Gateway Connection Tuning

| Parameter | Value | Location |
|---|---|---|
| `max_connections` | 100 | `gateway/main.py` (lifespan) |
| `max_keepalive_connections` | 20 | `gateway/main.py` (lifespan) |
| `timeout` | 30.0s | `gateway/main.py` (lifespan) |
| `max_retries` | 3 | `gateway/utils.py` |
| `backoff_factor` | 0.5 | `gateway/utils.py` |

### Watchdog Hyperparameters

| Parameter | Value | Location |
|---|---|---|
| `contamination` | 0.05 | `anomaly_detector.py` |
| `min_training_samples` | 20 | `anomaly_detector.py` |
| `retrain_interval` | 100 samples | `anomaly_detector.py` |
| `training_buffer_size` | 1,000 | `anomaly_detector.py` |
| `events_window_size` | 500 | `feature_extractor.py` |
| `csv_poll_interval` | 0.5s | `watchdog.py` |

---

## Demonstration Scenario: Dynamic Support Tiering

CortexFlow ships with a **Dynamic Support Tiering** demonstration that simulates a production customer support workflow:

1. **Inbound Ticket** → User submits a support request (refund, escalation)
2. **Gateway Ingestion** → Event is normalized and streamed to Pathway
3. **Agent Processing** → Agent Worker picks up `user_prompt`, invokes LLM with tool schemas
4. **Tool Dispatch** → LLM decides to call `process_refund` or `escalate_to_human`
5. **Watchdog Monitoring** → BDH Watchdog detects if the agent enters a reasoning loop
6. **Live Dashboard** → All events, tool calls, and alerts stream to the frontend in real-time
7. **Stress Test** → Launch 1000 concurrent requests to validate throughput and fault tolerance

### Available Tools

| Tool | Description |
|---|---|
| `process_refund(ticket_id, amount)` | Issue a refund for a support ticket |
| `escalate_to_human(ticket_id, reason)` | Escalate ticket to Tier 2 human support |

---

## Evaluation Criteria Alignment

| Dimension | Weight | How CortexFlow Addresses It |
|---|---|---|
| **Implementation** | 30% | Containerized multi-service gateway with shared lifespan httpx client, exponential backoff retry, connection pooling, and Pathway-based zero-leaked-state streaming |
| **Architecture** | 25% | Pathway streaming backbone with `rest_connector`, async non-blocking BDH Watchdog (CSV tailing), decoupled LLM adapter factory pattern, Pydantic tool contract validation |
| **Product Implementation** | 20% | Fully functional client proxy dashboard with WebSocket telemetry, live throughput/latency/alert metrics, built-in stress test trigger, and real-time log streams |
| **Documentation** | 15% | This comprehensive README, technical bridge plan (`docs/bridge_plan.md`), design specification (`docs/design.md`), inline docstrings, and API schema documentation |
| **Ideation & Novelty** | 10% | Stress tester with poison pill anomaly injection for chaos engineering, Markov-based reasoning loop detection, online Isolation Forest retraining, and 8-dimensional feature vector behavioral analysis |

---

## License

This project is licensed under the MIT License.
