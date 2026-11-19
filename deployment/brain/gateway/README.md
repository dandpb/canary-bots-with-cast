# LiteLLM & Gemini Decisions Gateway (`deployment/brain/gateway`)

## Overview
Provides container images, Compose definitions, and route policy templates for running the LiteLLM proxy alongside Canary Brain—including the standard UI/benchmark gateways and the dedicated Gemini Decision 1 Decisions gateway (`Dockerfile.decisions`, `gateway.decisions.example.json`).

## Interface
- `[Dockerfile.decisions]` / `[gateway.decisions.example.json]` — Non-root (`10001:10001`) LiteLLM `1.111.0rc1` proxy image and Decisions-mode config template routing alias `canary-gemini-decision-1` to `gemini/gemini-decision-1` with `custom_auth: "gateway_policy.authenticate"`.
- `[Dockerfile]` / `[Dockerfile.benchmark]` / `[Dockerfile.ui]` / `[requirements.lock]` — Base, benchmark-isolated, and UI-enabled LiteLLM container builds with pinned Python dependencies.
- `[compose.yaml]` / `[compose.benchmark.yaml]` — Standalone and benchmark-isolated Docker Compose gateway stacks.
- `[gateway.example.yaml]` / `[gateway.named-credentials.example.json]` — Route templates for OpenAI/Gemini aliases (`canary-openai`, `canary-gemini`) and named UI credentials.

## Invariants
- The dedicated Decisions template disables retries, fallbacks, response caching, telemetry, and spend logs. The worker accounts for its paid attempts in the canonical SQLite ledger. See the [setup guide](../SETUP.pt-BR.md) for the UI gateway's usage reporting.
- `Dockerfile.decisions` runs as unprivileged user `10001:10001` with `CANARY_BENCHMARK_GATEWAY_ONLY=1`. The [WSL Compose service](../../wsl/compose.yaml) mounts the readable policy at `/app/gateway.yaml` as read-only.

## Side Effects
- Builds Docker images and serves HTTP inference endpoints on container port `4000`, forwarding authenticated requests to upstream OpenAI or Gemini APIs.

## Verification
- With the [development dependencies installed](../README.md#verification), run `cd deployment/brain` and `python -m pytest tests/test_gateway.py tests/test_gateway_setup.py` from the repository root.
