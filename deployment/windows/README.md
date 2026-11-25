# Windows WSL Deployment Status Tool (`deployment/windows`)

## Overview
Provides a read-only Windows host status check (`canary-status.py`) and its unit test suite (`test_canary_status.py`) for inspecting the `canary-bots-wsl` Docker Compose stack via Docker CLI, native TSQP status port (`7173`), HTTP endpoints, and the latest S1 digest artifact.

## Interface
- `collect_services()`, `native_status(host, timeout)`, `http_probe(url, timeout)`, `health_from_status(status)` (`[canary-status.py:collect_services]`, `[canary-status.py:native_status]`): Read-only probes querying Docker container states (`com.docker.compose.project=canary-bots-wsl`), sending the binary TSQP `info` frame to port `7173`, and checking HTTP endpoints.
- CLI modes (`[canary-status.py]`): Supports default terminal panel output, `--json`, and `--open` (opens the world map in a browser).

## Invariants
- Strictly read-only: performs no writes, restarts, or bot commands (`[canary-status.py]`).
- Deterministic exit-code contract: `0` (`GREEN`), `1` (`AMBER`), `2` (`RED`), where historical S1 digest verdicts (`deployment/wsl/runtime/digests`) are displayed without overriding live health (`[canary-status.py:EXIT_CODES]`).

## Side Effects
- Executes `docker ps -a`, opens TCP/HTTP client connections to localhost-forwarded WSL ports, reads digest markdown files under `deployment/wsl/runtime/digests`, and optionally opens a browser URL with `--open` (`[canary-status.py]`).

## Verification
- Run: `python -m unittest deployment/windows/test_canary_status.py`
