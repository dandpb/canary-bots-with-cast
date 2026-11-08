# Canary Brain Operational, Smoke & M5 Qualification Tools (`tools`)

## Overview

Command-line tools, smoke harnesses, and M5 comparative pilot wrappers (`m5_pilot.py`, `m5_report.py`, `benchmark_gateway.py`, `evaluate.py`, `probe.py`, and gateway/deadline smoke runners) for offline bandit evaluation, LiteLLM gateway boundary qualification, and attested M5 campaign execution. See [`M5_PILOT.md`](./M5_PILOT.md) for M5 operator workflow details.

## Interface

- `[m5_pilot.py:main]` / `[m5_pilot.py:preflight]` / `[m5_pilot.py:execute]` / `[m5_pilot.py:execute_admitted]` — M5 admission wrapper CLI (`--plan`, `--preflight` | `--execute`) enforcing the 6 admission gates (`[m5_pilot.py:GATES]`), short-deadline qualification (`[m5_pilot.py:qualify_short_deadlines]`, `[m5_pilot.py:probe_deadlines]`), single-use SQLite claims (`[m5_pilot.py:claim_recovery]`, `[m5_pilot.py:claim_none_profile]`), and attested trial execution (`[m5_pilot.py:run_attested_campaign]`, `[m5_pilot.py:TrialAttestation]`, `[m5_pilot.py:Plan]`).
- `[m5_pilot.py:ledger_snapshot]` / `[m5_pilot.py:ledger_export]` / `[m5_pilot.py:admitted_budget]` / `[m5_pilot.py:validate_none_configuration]` / `[m5_pilot.py:validate_none_envelope]` / `[m5_pilot.py:validate_recovery_envelope]` / `[m5_pilot.py:source_files]` / `[m5_pilot.py:assert_frozen_imports]` — Read-only SQLite ledger verification, frozen source manifest validation, and profile configuration comparators against `[m5_openai_none_reference.v2.json:schema_version]`.
- `[m5_report.py:main]` / `[m5_report.py:review]` / `[m5_report.py:window_persistence]` / `[m5_report.py:latency_metrics]` / `[m5_report.py:priced_usage]` / `[m5_report.py:markdown]` — Offline M5 evidence verifier CLI (`--recording`, `--experiment`, `--trials` | `--trials-root`, `--attestation`, `--ledger`, `--output`, `--require-completed`) generating `report.json`, `acceptance.json`, and `report.md`.
- `[benchmark_gateway.py:main]` / `[benchmark_gateway.py:serve]` / `[benchmark_gateway.py:cleanup]` / `[benchmark_gateway.py:environment]` — Private benchmark LiteLLM gateway lifecycle manager (`--runtime`, `--policy`, `--image`, `--revision`, `--check` | `--serve`) with crash-safe mutation journaling (`[benchmark_gateway.py:journal]`) and flock leasing (`[benchmark_gateway.py:lease]`).
- `[evaluate.py:main]` / `[evaluate.py:evaluate]` — Deterministic held-out synthetic contextual bandit evaluation CLI (`--output`).
- `[probe.py:probe]` — Live OpenAI contract probe CLI (`[probe.py:--live]`, `[probe.py:--credential]`, `[probe.py:--state]`, `[probe.py:--output]`, `[probe.py:--samples]`, `[probe.py:--max-effort]`, `[probe.py:--tool-result]`).
- `[deadline_smoke.py:main]` / `[deadline_smoke.py:exercise]` — End-to-end deadline enforcement and reservation retention smoke suite across candidate TTL profiles (`[deadline_smoke.py:PROFILES]`) and upstream delays (`[deadline_smoke.py:DELAYS_MS]`).
- `[gateway_smoke.py:main]` / `[gateway_routing_smoke.py:main]` / `[gateway_usage_smoke.py:main]` / `[gateway_flat_import_smoke.py:main]` / `[gateway_admin_routing_smoke.py:main]` / `[run_gateway_admin_routing_smoke.py:main]` / `[gemini_gateway_smoke.py:main]` / `[haiku_gateway_smoke.py:main]` — Offline and containerized LiteLLM proxy boundary, routing immutability, usage accounting, and provider wire-schema smoke tests.
- `[recording_benchmark.py:main]` — Synthetic 1,000-event burst benchmark over `Recorder` across 3 bots.

## Invariants

- `[m5_pilot.py:preflight]` — Requires `plan.output` to be an unpopulated non-symlink absolute path; admission `approved=True`, `read_only_preparation=False`, all 6 `GATES` true, `bot_id == 65001`, 40-hex `source_revision` matching `source_manifest`, `seconds == 1800`, `repetitions == 3`, `memory_mode == 'frozen'`, `run_cap_nanousd == USD`, `campaign_cap_nanousd == 6 * USD`, `canonical_monthly_cap_nanousd == 50 * USD`, and `0o600` credential permissions (`st_mode & 0o077 == 0`).
- `[m5_pilot.py:admitted_budget]` / `[m5_pilot.py:_ledger_snapshot_in_transaction]` — Enforces total pilot liability `<= 7 * USD` (or `SHORT_DEADLINE_TOTAL_CAP = 6_980_214_600`), monthly available headroom `>= 12 * USD`, zero existing requests for `namespace + ':%'`, and single-use SQLite claims (`m5_recovery_v2`, `m5_openai_none_v3`).
- `[m5_pilot.py:TrialAttestation.verify_images]` — Each trial must have exactly 2 containers (`game` and `database`) with `oneoff == 'False'`, no host port bindings, pinned `sha256:...` image content IDs, and 1 internal bridge network (`<project>_default`); `cleanup()` requires zero remaining trial containers or networks.
- `[m5_report.py:review]` / `[m5_report.py:window_persistence]` — Verifies recording manifests, absence of `gap` or `incomplete` flags, terminal persistence receipts (`witness_event.wall <= game_stopped_wall <= sql_read_wall`), bijective replay-to-ledger request ID sets, exact per-request nanousd settlement or retained unknown liability, zero inference rows for `native`/`fake` participants, and sets `verdict = 'descriptive_pilot_no_winner'`.
- `[benchmark_gateway.py:ensure_no_unresolved]` / `[benchmark_gateway.py:cleanup]` — Refuses to start if any existing `benchmark-gateway-*.json` journal is not in phase `'cleaned'`, and preserves container logs before removing owned containers (retaining the container on log capture failure).
- `[gateway_routing_smoke.py:main]` / `[gateway_admin_routing_smoke.py:main]` / `[gemini_gateway_smoke.py:main]` — Post-auth or DB-backed deployment mutations (`model`, `id`, `api_base`, `credential-reference`, `retry`) must be rejected before reaching upstream and retain reserved liability in the ledger.

## Side Effects

- `[m5_pilot.py:execute]` / `[m5_pilot.py:execute_admitted]` — Acquires `m5-pilot.lock` next to the canonical SQLite ledger, records single-use claims in the canonical ledger (`records` table), creates `plan.output` (`0o700`), runs live `decision_fixtures` probes and Docker benchmark trials (`benchmark.run_campaign`), spawns `observe_status` (`docker exec` against MariaDB), and writes `execution-started.json`, `<name>-probe-result.json`, `trial-attestations.json`, `ledger.json`, and `execution-result.json`.
- `[m5_report.py:main]` — Copies SQLite recordings/states into temporary directories (`m5-report-import-*`, `m5-report-state-*`), creates `--output` (`0o700`), writes `report.json`, `acceptance.json`, and `report.md`, and exits with code `2` if `ready_for_review` is `False`.
- `[benchmark_gateway.py:serve]` / `[benchmark_gateway.py:cleanup]` — Acquires `<runtime>/.benchmark-gateway.lock`, writes `benchmark-gateway-<session>.json` journals and `.log` files, and creates/starts/stops/removes the `benchmark-gateway` Docker container.
- `[probe.py:probe]` — Issues live HTTPS requests to `https://api.openai.com/v1`, mutates the SQLite ledger at `--state`, and writes `--output` (`0o600`).
- `[deadline_smoke.py:main]` / `[gateway_smoke.py:main]` / `[run_gateway_admin_routing_smoke.py:main]` — Spawns local fake HTTP upstream servers, `litellm` proxy subprocesses, temporary SQLite ledgers, and disposable `--network none` Docker containers.

## Verification

- Run: `pytest`
