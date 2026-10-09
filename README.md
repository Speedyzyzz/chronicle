# Chronicle: Deterministic Record-and-Replay Runtime for Coding Agents

A time-travel execution runtime that records every causal event, tool invocation, environment read, and content-addressed filesystem delta—allowing engineers to reproduce, diff, and bisect an agent run with zero cloud LLM API calls.

## Architecture

- **`sdk/`**: Python (`chronicle_sdk`) and TypeScript SDKs for intercepting tools, model calls, subprocesses, filesystem deltas, and Lamport/vector clock sequencing.
- **`backend/app/ledger/`**: Append-only event-sourced causal execution ledger. Content-addressed filesystem deltas hashed via BLAKE3.
- **`backend/app/replay/`**: Replay Coordinator supporting Pure Replay (0 model calls, inputs re-hydrated from ledger), Verified Replay, and First-Divergence Localization.
- **`backend/app/llm/`**: Dual-Engine LLM architecture supporting live adapters (OpenAI, Anthropic, Gemini) and a deterministic offline test engine with fault injection.
- **`frontend/`**: Next.js 15 App Router control plane with React 19, time-travel playback slider, and causality graph.
- **`benchmark/`**: `ChronicleBench` 40-task benchmark proving 95%+ exact replay convergence and divergence localization within $\pm 0$ events.

## Quick Start (Offline Verification)

```bash
# 1. Run all unit & integration tests (100% offline)
pytest backend/tests -v

# 2. Run the 40-task ChronicleBench
python3 benchmark/chronicle_bench.py
```

## Running the Full Stack

```bash
# Start backend API (FastAPI)
cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000

# Start frontend (Next.js 15)
cd frontend && npm install && npm run dev
```
