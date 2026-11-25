# Isolated QA & Qualification Fixtures (`tests/fixture`)

## Overview
Contains offline and Docker-isolated test harnesses for M5 comparative pilot qualification, party acceptance and combat performance probes, lifecycle/persistence contracts, hunt-phase tracing, and overlapping `PlayerStorage` acknowledgement verification.

## Interface
- M5 qualification & status runners: `m5_qa.py`, `m5_current_qualification.py`, `m5_current_lowstock.py`, `m5_lowstock.py`, `m5_qualification_gates.py`, `m5_status_capture.py`, `m5_status_runner_adapter.py`, `m5_probe.py`, `m5_worker.py`, `m5_stop.py`, `m5_finalize.py`, `m5_supply_finalize.py`, `m5_archive.py`, `m5_runner_archive.py`, `m5_runner_smoke.py`, `m5_evidence_manifest.py`, `m5_evidence_index.py`, `m5_verify_published.py`, `m5_cycle_report.py`, `m5_report.py`, `m5_read_state.py`, `m5_freeze_supply.py`, `m5_persistence_adapter.py`, `m5_persistence.lua`.
- Party acceptance & performance harnesses: `party_qa.py`, `party_acceptance.cpp`, `party_build.py`, `party_combat_perf.py`, `party_perf.py`, `party_policy.py`, `party_population.py`, `party_scenarios.py`, `party_scenarios.lua`, `party_worker.py`, `party_metadata.py`, `party_report.py`.
- Offline trace & storage fixtures: `hunt_phase_trace.py`, `player_storage_ack_offline.py`, `bot_database_tasks_offline.py`, `lifecycle_bridge.cpp`, `bot_engine_loader_main.cpp`, `injection_fixture.hpp`, `test_injection.hpp`, `test_items.hpp`.
- Test suites: `test_m5_*.py` (including `test_m5_docker_ownership.py`), `test_hunt_phase_trace.py`, `test_party_run.py`.
- Reference documentation: [`M5_CURRENT_QA.md`](./M5_CURRENT_QA.md), [`M5_QUALIFICATION.md`](./M5_QUALIFICATION.md), [`M5_SUPERVISED_QA.md`](./M5_SUPERVISED_QA.md), [`PARTY_ACCEPTANCE.md`](./PARTY_ACCEPTANCE.md), [`STATUS_CAPTURE_OFFLINE.md`](./STATUS_CAPTURE_OFFLINE.md), [`STATUS_RUNNER_ADAPTER_OFFLINE.md`](./STATUS_RUNNER_ADAPTER_OFFLINE.md).

## Invariants
- Offline status capture (`m5_status_capture.py`, `m5_status_runner_adapter.py`) and hunt-phase tracing (`hunt_phase_trace.py`) validate telemetry and logs passively without injecting synthetic status responses.
- Qualification harnesses never mutate production volumes or canonical ledgers outside explicitly configured evidence directories.

## Side Effects
- Spawns isolated Docker containers/subprocesses during live fixture runs and writes JSON/Markdown evidence bundles and archive manifests to caller-specified output paths.

## Verification

Use Linux or WSL with Python 3.11 or newer and `luajit` on `PATH`. From the
repository root, install the locked Brain development dependencies and the
worker in editable mode so the harness resolves it from the source checkout.
The full suite includes `test_m5_persistence_contract.py`, which needs an ARM64
Linux LuaJIT process with `libcrypto.so.3`. Use an ARM64 host or run that process
under ARM64 emulation. On AMD64 with native LuaJIT, run the other fixture tests
with `--ignore=tests/fixture/test_m5_persistence_contract.py`.

```sh
python3 -m venv .venv
.venv/bin/pip install -r deployment/brain/requirements-dev.lock
.venv/bin/pip install --no-deps -e deployment/brain
.venv/bin/python -m pytest tests/fixture
```
