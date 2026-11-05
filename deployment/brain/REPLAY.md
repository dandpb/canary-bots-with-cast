# Replay and gameplay benchmarks

The worker can record a selected bot's observed life and replay it without a running game or model access. The local player compares up to four runs by elapsed time or first observed level gain. It shows sampled floor-aware coordinates, XP, health, decisions, native results, interventions, settled cost and unresolved reservations. The default map is a coordinate grid; no proprietary map/client artwork is bundled.

## Start with an offline demonstration

Use the existing brain Python environment in Linux/WSL, with the updated package installed. Choose a fresh recording filename; demo refuses to overwrite a completed run.

```sh
canary-brain replay demo --recording /tmp/replay-demo.sqlite3
canary-brain replay serve --recording /tmp/replay-demo.sqlite3 --port 8092
```

Open `http://127.0.0.1:8092/replay`. Both demonstration runs are explicitly synthetic. They verify the viewer, not model skill, actual character progress or real provider prices. Select the second run, jump to a level milestone, play at a different speed and inspect a recorded event. The standalone viewer has no game-command endpoint and makes no model requests.

## Record an existing bot

Recording is disabled unless `recording` is present in the worker configuration. It also works with the existing direct OpenAI configuration; gateway migration is a separate explicit deployment change.

```json
"recording": {
  "path": "/var/lib/canary-brain/recording.sqlite3",
  "namespace": "grizzle-wsl",
  "sample_ms": 1000,
  "queue_size": 2048,
  "max_bytes": 536870912
}
```

Keep the recording database separate from the mutable state and shared budget database. For an existing bot the lifetime run identity is `namespace:BOT_ID:life`; reuse the namespace and database across worker restarts. A deliberate character reset needs a new namespace/lineage. The recorder preserves session boundaries, generation changes and observation gaps. It cannot recover life before recording began.

The worker writes through a bounded background queue. Queue loss, write failures and the storage limit produce visible evidence gaps; native gameplay is not blocked. At the default 512 MiB limit recording stops accepting ordinary events and retains an explicit storage-limit marker. There is no silent automatic deletion or diagnostic-history pruning of replay records. Export/back up and choose a new recording segment before reaching the limit. Retention is bounded, not a promise of unlimited disk storage.

Movement is sampled at the configured cadence, with additional samples on floor, life-state, objective-generation and level changes. Viewer downsampling is distinct from missing observations. Decision inspection retains the offered options, proposal, policy-adjusted choice, emitted intent, native acceptance and terminal outcome. A model explanation is not invented during replay.

The updated native library emits cumulative per-world death counters and lifecycle/ownership telemetry. Older servers can supply observation replays, but death/ownership metrics are unavailable. Controlled live experiments require the new bridge capabilities and `keep_awake: true`; the native baseline uses shadow mode with the same awake policy.

The supervision console exposes `/replay` when recording is enabled. The separate `replay serve` command binds only to loopback and remains read-only. Its APIs paginate events; time seeks use indexed sample checkpoints. The primary endpoints are `/api/replays`, `/api/replay`, `/api/replay/seek`, `/api/replay/events`, `/api/replay/track`, `/api/replay/timeline` and `/api/replay/summary`.

## Configure LiteLLM

The private proxy uses LiteLLM **1.108.0**, with the tested dependency set in `gateway/requirements.lock`. Build and run the dedicated optional deployment:

```sh
cd deployment/brain/gateway
umask 077
mkdir -p runtime
cp gateway.example.yaml runtime/gateway.yaml
# Prepare the private provider.env and worker.env described below.
docker compose build
docker compose up -d --wait
sha256sum runtime/gateway.yaml
```

`runtime/provider.env` contains the configured upstream provider credentials and a strong, separately generated `LITELLM_MASTER_KEY`. `runtime/worker.env` contains a different `LITELLM_WORKER_KEY`. Give the worker a separate private file containing the same worker-key value as `LITELLM_API_KEY=...`. The worker does not receive the master or provider keys. Never place actual keys in a model configuration, experiment manifest, report or Git.

The custom worker authentication permits only inference for declared aliases, checks the gateway version, exact configuration SHA-256 and expected upstream mapping, and rejects administration and per-request routing overrides. Configure one explicit deployment per alias, zero retries at both gateway layers, no fallback/order failover, no response cache and `drop_params: false`. The gateway also refuses a configuration changed after startup. Its host publication is loopback-only. The application remains the authoritative ledger for the shared USD 50 monthly limit; gateway estimates do not settle or replace application reservations.

Use `worker-replay.example.json` as the migration template, supplying the actual configuration hash, private gateway credential path, exact effective/upstream model and reviewed versioned prices. The loopback gateway address works for a worker running on the host. A containerized worker needs the gateway on its private Docker network and `http://litellm:4000/v1`; its container's loopback is not the host.

All providers use the same LiteLLM-facing application adapter. Additional models require an explicit `model_list` entry and participant configuration, not another provider SDK adapter. The common decision path uses a constrained Responses function call with a reserved output-token limit. `decision_api: "decisions"` is rejected when output tokens have a nonzero price: that endpoint has no enforced output-token bound in this adapter. Input-only/free-output configurations remain opt-in and must pass conformance for the pinned gateway/model. Unsupported tools, reasoning parameters or endpoints fail rather than silently changing the task.

The experiment's common decision timeout defaults to ten seconds for macro objectives and is capped further by the shortest offered server deadline. Native combat/healing continues independently; slow planning has a separate concurrency lane. Frozen runs disable policy updates, policy overrides and autonomous reflection/strategy-memory updates. Independent runs start from the same seed records and learn separately. The timed horizon begins with the worker's first valid observation, not database/container provisioning.

LiteLLM may return the configured alias in the response's model field. The recorder distinguishes that observation from an upstream model name and resolves the configured upstream through the exact policy hash and deployment ID. A mutable upstream alias is not proof of an immutable provider model revision.

Offline gateway conformance uses the real pinned proxy and a local fake upstream, inside a Docker container with external networking disabled:

```sh
python deployment/brain/tools/gateway_smoke.py
```

This checks a successful accounted request and an upstream failure: exactly one upstream call per attempt, no fallback, and retained unresolved liability after failure. No real model credential is used.

## Prepare an isolated experiment

The live runner uses a new `canary-bench-*` Compose project for each attempt, private bind directories, no host game/database ports and no production volumes. It starts the worker socket before starting the game. Each trial restores the same declared fixture. Native control uses no inference; frozen-policy and independent-learning runs are separate modes.

Prepare a local fixture directory containing:

- `database.sql`: a complete, sanitized, compatible isolated database fixture. It must register the selected pilot under the one-bot population configuration; a production dump containing a different selected population is not interchangeable.
- `character.json`: the exact saved `id`, `level`, `experience`, `posx`, `posy`, `posz` integers checked before the game starts.
- Optional `authored/`: the exact routes for the trial, copied into each isolated runtime.
- Optional `worker-state.json`: initial learning records with `kind`, `key`, `data`; only policy, recency, guidance and strategy records are accepted. Do not seed accounting or pending intents.

The map is referenced separately, read-only, and included in the initial hash. A restored database is not a deterministic whole-world simulator: live RNG, scheduling and later encounters can diverge. No production character is reset by these commands.

```sh
canary-brain benchmark hash --fixture /home/daniel/benchmark-fixture \
  --world-map /home/daniel/maps/otservbr.otbm
canary-brain benchmark preflight --config /home/daniel/benchmark.json
canary-brain benchmark run --config /home/daniel/benchmark.json --live
```

Use `experiment.example.json` as the template. Replace all fixture/configuration hashes and model mappings, select reviewed prices and use the existing shared budget path. Keep output paths short enough for Unix sockets. Build the game image with this implementation before running: an older bridge is rejected before model decisions are applied. The optional `--live` flag is required for game/provider execution. The shipped configuration is a template, not an authorization to spend or evidence of a completed trial.

All declared run caps must fit the campaign cap. On resume, only attempts without a recorded identity add future liability against the remaining shared monthly allowance; settled and unknown charges already remain in that ledger. Every inference attempt reserves against both run and monthly limits in the same transaction. Unknown charges survive failure, restart and month rollover. Zero-cost baselines do not get an infinite XP-per-dollar score.

An attempt is persisted before provisioning. Failed, budget-stopped and interrupted trials remain in the results; rerunning the same campaign skips their identities instead of replacing them with successes. Changed campaign configuration requires a new campaign identity. A kernel-held campaign lease prevents a second orchestrator from treating an active trial as an orphan. After a crash, the next invocation first tears down the exact deterministic Compose project, preserving its bind data, then marks the open attempt interrupted. Failed cleanup stops the resume and leaves it retryable. Saved final character evidence stays in the trial's private runtime directory. Live campaigns require Linux/WSL.

Run summaries report confirmed net XP, wall/observed-active time, deaths when available, human interventions, native ownership time, confirmed objective results, request failures, latency and money. Native ownership is not a claim that a provider remained continuously available. Stalled duration requires observed working-state evidence and is unavailable when that evidence is insufficient. Aggregate summaries use independent runs, report all attempts and do not automatically declare a winner.

## Export and verify

Recorded decision fixtures can also be evaluated without executing any game action:

```sh
canary-brain benchmark decisions --fixtures /path/to/decision-fixtures.json
# Explicit real inference, charged to the same ledger with an explicit run cap:
canary-brain benchmark decisions --fixtures /path/to/decision-fixtures.json \
  --worker-config /path/to/evaluation-worker.json --live
```

The JSON file contains up to 100 entries with `observation`, optional identical `memory`, and optional expected candidate `expected`. Without `--live` this uses the explicit fake provider. Real evaluation requires a LiteLLM worker configuration, recording, a shared budget file and a per-run cap. It records request attribution and reports validity, expected-choice agreement and elapsed time. It never assigns hypothetical XP or survival to unexecuted choices.

```sh
canary-brain replay list --recording /path/to/recording.sqlite3
canary-brain replay summary --recording /path/to/recording.sqlite3 --run RUN_ID
canary-brain replay export --recording /path/to/recording.sqlite3 --run RUN_ID --output /tmp/bot.replay.zip
canary-brain replay import --recording /tmp/imported.sqlite3 --archive /tmp/bot.replay.zip
canary-brain replay report --recording /path/to/recording.sqlite3 --run RUN_A --run RUN_B --output /tmp/comparison.html
```

ZIP archives contain bounded event segments, metadata and SHA-256 checksums. ZIP and HTML exports pin one read-only SQLite snapshot, including concurrent live recording. Import validates every member before creating the destination; it never extracts arbitrary paths. It imports the complete new run in one transaction and rejects any existing run identity, including an otherwise identical lifetime manifest; choose a new destination to keep histories separate. SQL failure rolls back the entire imported run. HTML reports contain the player, styles and data and work offline. HTML exports are limited to four runs and 20,000 events; use the full ZIP and local viewer for larger histories. Neither archive nor report contains credentials or a game-control token. Replay never makes billable requests.

## Offline video / timelapse

```sh
canary-brain replay video --recording /path/to/recording.sqlite3 --run RUN_ID \
  --output /tmp/bot-life.mp4 --speed 60 --fps 24
# Export a chapter rather than the entire recorded life:
canary-brain replay video --recording /path/to/recording.sqlite3 --run RUN_ID \
  --output /tmp/chapter.mp4 --start-ms 600000 --end-ms 1800000 --speed 30
```

The renderer uses only recorded coordinates, floor, XP, health, mana, supplies,
settled/reserved cost and event phases. It first copies a consistent read-only
SQLite snapshot to a private temporary database, with a ten-second copy deadline.
The live source is closed before frame rendering or ffmpeg/ffprobe begins, so a
long video export does not pin the recorder's WAL. It streams the private copy;
no game, provider, browser, tile service or credentials are needed. It requires
local `ffmpeg` with `librsvg`/`libx264`, plus `ffprobe`. It draws a sparse coordinate
map, not the original client's terrain, sprites or attack animation. The video
always labels that distinction, and synthetic recordings remain visibly labelled.
No coordinates are interpolated across gaps/floor changes. Stale displays retain
the last known state with a gap label until another actual sample arrives.

MP4 is 1280×720. Export is bounded to 14,400 frames/600 seconds; increase speed or
select chapters for longer histories. A JSON sidecar records the source manifest,
snapshot hash, time window, requested/effective speed, actual frame count/duration
and MP4 hash. The encoded artifact is checked with ffprobe before publication.
`source_events_sha256` covers the chronological event prefix through `end_ms`;
`source_snapshot_sha256` covers that digest, its ending time and the captured
`source_metadata`, including the manifest, status and incomplete flag. It is an
export-evidence hash, not a checksum of unused events or SQLite file bytes.
Output and sidecar paths must be new; existing artifacts are not overwritten.
The renderer streams history and bounds its displayed trail to recent samples.

Validate changes with the existing pytest, ruff and strict mypy commands, plus the gateway smoke tool and native library build. Browser checks cover the initial page, comparing two runs, seeking, floor changes, playback, milestone alignment, console health and a narrow viewport. Real model rankings require a separately selected, budgeted pilot with multiple independent runs. Native client capture/clips can later be attached separately to these sampled-map videos.
