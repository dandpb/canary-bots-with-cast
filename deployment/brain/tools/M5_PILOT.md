# Admitted M5 wrapper

`m5_pilot.py` is an operator entry point for the declared fixture-G pilot.
It calls the existing `decision_fixtures` evaluator and a single canonical
`run_campaign` (native/OpenAI/Gemini, three repetitions of three 30-minute trials).
Canonical execution
already rotates ABC/BCA/CAB; the wrapper does not implement another scheduler.
It does not perform provider SDK translation or own a second financial ledger.
For initial gateway/worker configuration, start with the
[Portuguese setup guide](../SETUP.pt-BR.md#7-preparar-o-benchmark-e-autorizar-a-execução-paga).
These tools being integrated does not authorize the paid pilot.
For a reproducible private-gateway build/serve/cleanup using tracked files,
follow [gateway provisioning](../SETUP.pt-BR.md#4-cadastrar-credenciais-e-associar-modelos).
The launcher refuses an existing `gateway` alias and never sends inference.

Use a frozen source export and the admitted common worker image. Mount that
source directory at the same absolute path inside the harness, and set
`PYTHONPATH=<source_path>/deployment/brain/src`. The source manifest must hash
all exported Python modules and `deployment/brain/tools/m5_pilot.py` itself.
Keep source, inputs and outputs on the host WSL Linux filesystem, not a Windows
drive under `/mnt/*`. Start the host launcher from `/`, use absolute paths and
set the harness `working_dir` to `/`. Docker subprocesses explicitly use `/`
so an inherited checkout cwd cannot break inspection, final save or teardown.
Before admission, attest host `findmnt` and actual read-only source/input binds;
source hashes/path checks alone do not establish filesystem or mount permissions.

```sh
python /absolute/source/deployment/brain/tools/m5_pilot.py --plan /absolute/pilot.plan.json --preflight
# Only after root has accepted the actual free/gateway evidence:
python /absolute/source/deployment/brain/tools/m5_pilot.py --plan /absolute/pilot.plan.json --execute
```

Plan JSON keys: `output`, `campaign`, `admission`, `authorization`,
`source_manifest`, `decision_fixtures`, `probe_workers` (`openai`/`gemini` paths),
`worker_image`, `canonical_ledger_file`, `canonical_volume`. Paths are absolute.
The output may be a freshly created empty Docker bind directory; attempts use
an exclusive execution marker and cannot be rerun or replaced automatically.
A kernel lease on the canonical volume also excludes another M5 orchestrator
with a different output path. Its lock file is retained to avoid inode races;
the kernel releases ownership on close/process death.

The root admission must have `approved:true`, `read_only_preparation:false`,
all six named free/gateway gates true, the exact `source_revision`, and
`approved_inputs_sha256`: hashes of every input except admission itself
(`campaign`, `authorization`, `source_manifest`, `decision_fixtures`, `openai`,
`gemini`). Worker-image/Python/OpenAI/Pydantic identities must match
admission. Candidate documents with false gates are deliberately rejected.
The two provenance/schema gates are `conformance_input_provenance_frozen` and
`same_candidate_schema_and_application_validation`. Admission/results declare
`comparison_scope:"configured_controller_stacks"` and
`native_decoding_guarantees_equal:false`: Google ANY and OpenAI strict do not
promise identical native decoder guarantees.

The wrapper captures bytes/hashes before validation, checks for concurrent
edits, then passes the same admitted in-memory JSON to the canonical evaluator
(`read_text`/`stat` interface) and a validated Experiment to the campaign runner.
Audit snapshots preserve those exact bytes; execution never reopens mutable
original configuration paths or uses the audit copies as new authority.

`--preflight` makes no Store, schema, reservation, provider or game changes.
It reads input hashes and SQLite in read-only mode and inspects only the current
harness's image/mount metadata. The canonical existing volume must be mounted
directly RW as `canary-bots-wsl_brain-state`; bind copies are rejected. This
profile fixes the ledger identity to `/var/lib/canary-brain/state.sqlite3`;
another SQLite file in that same volume is not an accepted authority. The
profile requires existing ledger headroom of USD12 and a global monthly cap of USD50.

The paid bounds are USD0.49 per model's conformance block (one recorded bot,
at most six observations) and six scored runs at USD1 each. Historical settled
probes and declared additional prior costs also consume the USD7 envelope.
Single-candidate observations select locally and are counted as zero model
attempts. Other observations must each produce exactly one ledger request.

Each scored participant receives the same isolated internal game/DB network,
`<trial-directory>:/m5` audit mount and passive status query cadence
(after 540 s, every 10 s). The observer is qualified for fixture-G Grizzle 65001;
it issues only status queries, not gameplay orders. The canonical runner owns
service teardown; observer tasks are cancelled/joined and patched hooks restored.

Before game start, the wrapper creates the game container without starting it
and inspects actual game/database IDs, image content IDs, selected Compose
labels, host ports, bind mounts and the single internal project network. The
already-running database must have the owned NetworkID and an endpoint before
game start; mounts must match canonical trial/world paths, not mutable Compose
declarations. A failed
check prevents the first game observation/model request. `start --wait` uses the
created container; a second inspection rejects replacement IDs or unexpected
running/network state. Docker queries use cwd `/` and bounded timeouts. No full
inspect, `Config.Env` or authentication header is requested or exported.

Each trial writes mode0600 `trial-attestation.json`; the campaign also writes
`trial-attestations.json`, a `trials` map keyed by canonical run ID. These contain
observed identities and error types, not exception messages. After the canonical
project-scoped `down` runs once, inspection lists containers/networks bearing the
exact trial project label. A leftover, inspection error or close failure keeps
`resources_cleaned:false` and propagates; the wrapper never broadens teardown or
deletes a leftover again. Observer errors retain their error file and an
attestation failure entry. Compose declarations cannot set `images_verified`.

A deadline is a negative performance result, distinct from protocol/identity/
usage failures. Probe output records valid, late and unknown counts separately.
Mixed deadline/technical failures are labeled `mixed`, retaining both counts.
Any failed conformance or unresolved charge stops before game runs and requires
root review; the wrapper never increases TTLs, retries or qualifies itself.

`execution-result.json` preserves stage outputs/errors. `ledger.json` exports
only relevant rows (historical IDs, probe recordings/returned IDs, declared extra
run IDs and every campaign-namespace SQL row), while its balance header includes
all production charges/unknown reservations. Header and rows come from one SQL
read transaction with an aware UTC timestamp. No full SQLite or key is exported.
An export failure is recorded and prevents a successful completion claim.
The most specific Docker mount covering the ledger/lease paths must be the
canonical volume; an extra file/directory bind shadowing it is rejected.
Passive observer errors stop the worker, mark incomplete evidence and propagate
through canonical teardown instead of silently qualifying a completed run.

Offline tests cover admission/source binding, missing/copied ledger rejection,
shared caps, no replacement, hook restoration, deadline liability retention,
actual image/scope/mount rejection, retained foreign/active leftovers, close/query
failure, metadata redaction and combined observer/attestation failure.
The tests do not qualify a live Docker deployment, account or paid campaign.

## Review the pilot offline

Use `m5_report.py` in the brain Python environment on Linux/WSL after preserving
a stable evidence snapshot. Docker is not required for this offline report;
`SOURCE` below is the frozen export directory. It performs no game/provider calls.
`--experiment` expects the generated campaign document
(`game/experiment.json`, containing `plan`, `configuration_sha256` and
`preflight.character`), not the flat input campaign. Prepare a reviewed report
copy preserving that identity and declaring all prior/current probe
`additional_cost_run_ids` plus `total_cap_nanousd` for the complete USD7 envelope.
Do not omit probes because they are outside the nine scored runs.

`--ledger` is the wrapper's scoped `ledger.json`, not a SQLite copy or LiteLLM's
cost estimate. Its global monthly header, month and aware UTC snapshot timestamp
come from the same transaction as its selected request rows. Unknown charges
remain liabilities. Use the wrapper's automatic `game/trial-attestations.json`.
The reporter also accepts reviewed external image/cleanup attestations: either a
`trials` map keyed by run ID or global `game_image`, `database_image`,
`images_verified` and `resources_cleaned` fields. Do not fill these from intent.

```sh
PYTHONPATH="$SOURCE/deployment/brain/src" python "$SOURCE/deployment/brain/tools/m5_report.py" \
  --recording /absolute/pilot/game/recording.sqlite3 \
  --experiment /absolute/report-experiment.json \
  --trials-root /absolute/pilot/game \
  --attestation /absolute/pilot/game/trial-attestations.json \
  --ledger /absolute/pilot/ledger.json --output /absolute/new-report
```

`--trials-root` reads each `<participant>-<repetition>/worker.sqlite3` and
`saved-character.json`; alternatively `--trials` accepts `{"trials":[...]}`.
Repeat `--recording` for scored evidence split across files, not for probe
recordings outside that grid. Keep probe recordings as separate evidence.
The destination must not exist. The tool writes `report.json`, `report.md` and
`acceptance.json`; exit 2 means evidence findings require review. Failed,
budget-stopped and interrupted attempts remain outcomes, not replacements.
Use `--require-completed` only when the reviewed acceptance requires every run
to finish its full horizon. A report ready for review neither declares a winner
nor closes the issue. Inspect the [visual replay/export](../REPLAY.md#export-and-verify)
separately, then preserve evidence and verify temporary-container cleanup.
