# Admitted M5 wrapper

`m5_pilot.py` is an operator entry point for the declared fixture-G pilot.
It calls the existing `decision_fixtures` evaluator and a single canonical
`run_campaign` (native/OpenAI/Gemini, three30-minute blocks). Canonical execution
already rotates ABC/BCA/CAB; the wrapper does not implement another scheduler.
It does not perform provider SDK translation or own a second financial ledger.

Use a frozen source export and the admitted common worker image. Mount that
source directory at the same absolute path inside the harness, and set
`PYTHONPATH=<source_path>/deployment/brain/src`. The source manifest must hash
all exported Python modules and `deployment/brain/tools/m5_pilot.py` itself.

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
profile requires existing ledger headroom ofUSD12 and a global monthly cap50.

The paid bounds areUSD0.49 per model's conformance block (one recorded bot,
at most six observations) and six scored runs atUSD1 each. Historical settled
probes and declared additional prior costs also consume theUSD7 envelope.
Single-candidate observations select locally and are counted as zero model
attempts. Other observations must each produce exactly one ledger request.

Each scored participant receives the same isolated internal game/DB network,
`<trial-directory>:/m5` audit mount and passive status query cadence
(after540s, every10s). The observer is qualified for fixture-G Grizzle65001;
it issues only status queries, not gameplay orders. The canonical runner owns
service teardown; observer tasks are cancelled/joined and patched hooks restored.

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
shared caps, no replacement, hook restoration and deadline liability retention.
The tests do not qualify a live Docker deployment, account or paid campaign.
