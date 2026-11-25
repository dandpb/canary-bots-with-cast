# Canary Brain Python Package (`canary_brain`)

## Overview
Implements the external autonomous-companion and party-pilot worker (`canary_brain`), communicating with the C++ `libbot_engine.so` over a non-blocking `AF_UNIX` datagram socket. Provides protocol serialization, SQLite WAL state and monthly USD-cap accounting, OpenAI & LiteLLM/Gemini Decisions providers, contextual bandit learning, live HTTP operator supervision (including reward-aware hunt hiatus), native admission & persistence witness verification, benchmark Docker fixture orchestration, replay/timelapse export, and visual packet replay packaging/rendering.

## Interface
- `[cli.py:main]` — Top-level CLI entrypoint (`canary-brain`) exposing `serve`, `status`, `inspect`, `checkpoint`, `rollback`, `forget`, `record-cost`, `replay`, and `benchmark` subcommands.
- `[runtime.py:Configuration]`, `[runtime.py:DatagramProtocol]`, `[runtime.py:read_credential]`, `[runtime.py:recording_failure]`, `[runtime.py:run]` — Worker configuration model (including split `gateway` / `responses_gateway` routing), Unix datagram I/O loop, and process lifecycle.
- `[protocol.py:Packet]`, `[protocol.py:Candidate]`, `[protocol.py:Bot]`, `[protocol.py:MemberState]`, `[protocol.py:Party]`, `[protocol.py:Message]`, `[protocol.py:Observation]`, `[protocol.py:Intent]`, `[protocol.py:intent_for]` — Protocol v1 observation/intent schemas and validation helpers.
- `[controller.py:Model]`, `[controller.py:Controller]` — Decision/response orchestration, multi-step objective planning, cooldowns, and action lease tracking.
- `[intent_routing.py:route_probability]`, `[intent_routing.py:clarification_question]`, `[intent_routing.py:confirm_action_reply]`, `[intent_routing.py:format_factual_outcome]` — Calibrated decision probability routing (`act`, `clarify`, `abstain`), clarification prompts, and factual outcome formatting.
- `[provider.py:Prices]`, `[provider.py:Proposal]`, `[provider.py:UnpricedCacheWrite]`, `[provider.py:ProviderBackoff]`, `[provider.py:Provider]`, `[provider.py:tactical_choice]` — Direct OpenAI Responses/Decisions client with nanodollar cost reservation, tactical choice filtering, and backoff.
- `[gateway.py:GatewayConfiguration]`, `[gateway.py:GatewayProvider]` — LiteLLM gateway provider supporting explicit `decision_api` (`"decisions"` | `"responses"`), `reasoning` effort control, pinned model deployment IDs, and Gemini Decisions routing.
- `[gateway_policy.py:DispatchPin]`, `[gateway_policy.py:validate_dispatch]`, `[gateway_policy.py:validate_native_tools]`, `[gateway_policy.py:validate_policy]`, `[gateway_policy.py:authenticate]` — Proxy-side LiteLLM authentication and routing-immutability enforcement.
- `[learning.py:Selection]`, `[learning.py:Policy]`, `[learning.py:episode_reward]` — Persistent contextual bandit selection, exploration, repetition caps, and terminal-outcome reward updates.
- `[supervision.py:Supervisor]` — Operator supervision state machine (pause/resume/recover/avoid/notes) and escalating reward-aware hunt hiatus (`Supervisor.reward_hiatus`, `REWARD_HIATUS_MIN_SAMPLES = 8`, `REWARD_HIATUS_LOW_MEAN = 0.25`, `REWARD_HIATUS_RECOVERY_MEAN = 0.5`, `REWARD_HIATUS_BASE_SECONDS = 1800`, `REWARD_HIATUS_MAX_SECONDS = 7200`).
- `[operator_http.py:OperatorServer]` — Loopback HTTP operator console (`/api/state`, `/api/command`) enforcing `Host`, `Origin`, and per-process `X-Operator-Token`.
- `[store.py:Store]`, `[store.py:BudgetExceeded]`, `[store.py:month_now]`, `[sqlite_files.py:prepare_database]` — Private SQLite WAL state/ledger persistence with integer nanodollar reservations and monthly `America/Sao_Paulo` caps.
- `[native_admission.py:Admission]`, `[native_admission.py:Qualification]`, `[supervised_native.py:SupervisedNative]`, `[persistence_witness.py:publish_request]` — Supervised native admission handshake, correlated `telemetry_fence` cutoff, and terminal persistence witness validation.
- `[benchmark.py:Participant]`, `[benchmark.py:Experiment]`, `[benchmark.py:DockerFixture]`, `[benchmark.py:ComposeOwnershipInvalid]`, `[benchmark.py:LegacyCleanupRequired]`, `[benchmark.py:preflight]`, `[benchmark.py:run_campaign]`, `[benchmark_stops.py:TelemetryTail]`, `[benchmark_stops.py:Stops]` — Isolated Docker Compose campaign runner with strict Compose ownership record validation and stop-policy monitors.
- `[recording.py:Manifest]`, `[recording.py:RecordingConfiguration]`, `[recording.py:RecordingStore]`, `[recording.py:ReplayReader]`, `[recording.py:Recorder]`, `[replay.py:ArchivedEvent]`, `[replay.py:ArchivedRun]`, `[replay.py:export_archive]`, `[replay.py:import_archive]`, `[timelapse.py:Projection]`, `[tracing.py:Capture]` — Deterministic event recording, replay archival, atomic timelapse publication, and structured tracing.
- `[replay_cli.py:configure]`, `[replay_cli.py:execute]`, `[replay_cli.py:serve]`, `[replay_cli.py:decision_fixtures]` — Replay & visual-replay CLI commands (`visual-pack`, `visual-stage`, `visual-video`, archive/report/serve).
- `[visual_replay.py:pack_visual]`, `[visual_replay.py:stage_visual_client]`, `[visual_replay.py:export_visual_video]`, `[visual_replay.py:capture_info]`, `[visual_replay.py:select_events]`, `[visual_capture.lua]` — Server-side visual packet tape packaging, OTClient visual playback staging, and FFmpeg video export.
- `[testing.py:FakeProvider]` — Offline zero-cost deterministic provider fixture.
- Subdirectory [`./dashboard/README.md`](./dashboard/README.md) — Static frontend assets for the operator console and replay viewer.

## Invariants
- Every billable model attempt reserves its conservative nanodollar upper bound in `Store` before dispatch and retains unknown-cost reservations across restarts (`[store.py:Store]`, `[provider.py:Provider]`).
- `Supervisor.reward_hiatus` escalates exclusion duration from `1800s` up to `7200s` once a hunt accumulates `>= 8` samples with mean reward `<= 0.25`, and resets offense level once mean reward recovers to `>= 0.5` (`[supervision.py:Supervisor.reward_hiatus]`).
- `DockerFixture` validates Compose ownership record shapes (`ComposeOwnershipInvalid`, `LegacyCleanupRequired`) before cleanup or reuse (`[benchmark.py:DockerFixture]`).
- `SupervisedNative` enforces immutable `native_admission` commit before model/intent admission and correlated `telemetry_fence` validation at window cutoff (`[supervised_native.py:SupervisedNative]`, `[native_admission.py:Admission]`).

## Side Effects
- Binds private `AF_UNIX` datagram sockets and exchanges bounded observations/intents with the Canary C++ server (`[runtime.py:DatagramProtocol]`).
- Reads and writes SQLite WAL state/ledger/recording databases (`[store.py:Store]`, `[recording.py:RecordingStore]`).
- Issues HTTPS requests to OpenAI or configured LiteLLM gateways (`[provider.py:Provider]`, `[gateway.py:GatewayProvider]`).
- Serves local HTTP operator APIs (`[operator_http.py:OperatorServer]`), spawns Docker Compose containers during benchmark runs (`[benchmark.py:DockerFixture]`), and runs FFmpeg/client staging for visual replay exports (`[visual_replay.py:export_visual_video]`).

## Verification
- With the [development dependencies installed](../../README.md#verification), run `cd deployment/brain` and `python -m pytest` from the repository root.
