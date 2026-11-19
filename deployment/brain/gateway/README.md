# LiteLLM & Gemini Decisions Gateway (`deployment/brain/gateway`)

## Overview
Provides container images, Compose definitions, and route policy templates for running the LiteLLM proxy alongside Canary Brain—including the standard UI/benchmark gateways and the dedicated Gemini Decision 1 Decisions gateway (`Dockerfile.decisions`, `gateway.decisions.example.json`).

## Interface
- `[Dockerfile.decisions]` / `[gateway.decisions.example.json]` — Non-root (`10001:10001`) LiteLLM `1.111.0rc1` proxy image and Decisions-mode config template routing alias `canary-gemini-decision-1` to `gemini/gemini-decision-1` with `custom_auth: "gateway_policy.authenticate"`.
- `[Dockerfile]` / `[Dockerfile.benchmark]` / `[Dockerfile.ui]` / `[requirements.lock]` — Base, benchmark-isolated, and UI-enabled LiteLLM container builds with pinned Python dependencies.
- `[compose.yaml]` / `[compose.benchmark.yaml]` — Standalone and benchmark-isolated Docker Compose gateway stacks.
- `[gateway.example.yaml]` / `[gateway.named-credentials.example.json]` — Route templates for OpenAI/Gemini aliases (`canary-openai`, `canary-gemini`) and named UI credentials.

## Invariants
- All gateway templates disable automatic retries (`num_retries: 0`), fallbacks (`fallbacks: []`, `max_fallbacks: 0`), response caching (`cache: false`, `cache_responses: false`), and telemetry/spend logging (`telemetry: false`, `disable_spend_logs: true`, `turn_off_message_logging: true`) so every billable attempt is accounted for solely by Canary Brain's SQLite ledger (`[gateway.decisions.example.json]`).
- `Dockerfile.decisions` runs as unprivileged user `10001:10001` with `CANARY_BENCHMARK_GATEWAY_ONLY=1` and mounts `/app/gateway.yaml` read-only (`[Dockerfile.decisions]`).

## Side Effects
- Builds Docker images and serves HTTP inference endpoints on container port `4000`, forwarding authenticated requests to upstream OpenAI or Gemini APIs.

## Verification
- Run: `pytest deployment/brain/tests/test_gateway.py`
