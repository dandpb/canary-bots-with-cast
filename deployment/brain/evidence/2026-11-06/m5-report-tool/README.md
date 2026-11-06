# Offline final-evidence review

`tools/m5_report.py` reads closed replay SQLite files or portable `.replay.zip`
archives, the public experiment export, normalized trial metadata and a redacted
canonical-ledger export. It makes no provider/Docker calls, never opens the
financial database and writes only a new report directory. Archive imports use
temporary recording databases, not a new financial ledger.

## Inputs

Keep `experiment.json` from the runner, including `configuration_sha256`, `plan`
and `preflight.character`. Preserve its exact fingerprint: it includes private
path identities in the runner, so hashing only the redacted plan is different.
The tool compares the recorded manifest fingerprint rather than regenerating it.

The required plan fields are `name`, `participants` (name/kind, and gateway for
real models), `repetitions`, `seconds`, `expected_initial_sha256`, `memory_mode`,
`source_revision`, `game_image`, `database_image`, `run_cap_nanousd` and
`campaign_cap_nanousd`. Kinds `native`, `fake` and `litellm` can be reported;
this does not add fake support to any runner. Normally IDs are
`name:participant:repetition`; a custom QA export can add `plan.expected_runs`
with explicit `{run_id,participant,repetition}` entries, without rewriting the
original files/identities.

For normalized `trials.json`, supply:

```json
{
  "trials": [{
    "run_id": "pilot:native:0",
    "reason": "completed",
    "elapsed_seconds": 1800.5,
    "observed_seconds": 1800.3,
    "initial_character": {"id": 7, "level": 20, "experience": 98800},
    "saved_character": {"id": 7, "level": 21, "experience": 106800},
    "game_image": "sha256:FULL_GAME_IMAGE_ID",
    "database_image": "mariadb@sha256:FULL_DATABASE_DIGEST",
    "images_verified": true,
    "resources_cleaned": true
  }]
}
```

The flags must refer to actual image inspections and exact resource removal,
not merely an expected Compose declaration. Saved character evidence comes from
the actual isolated database. Do not manufacture values/flags to pass a gate.

Alternatively `--trials-root /path/to/campaign --attestation /path/to/attestation.json`
copies `participant-repetition/worker.sqlite3` plus any WAL into a private
temporary directory, then reads that copy with `mode=ro` for
`records(kind=run_stop,key=end)` and the adjacent `saved-character.json`.
Initial character comes from `experiment.preflight.character`. The attestation
supplies the four image/cleanup fields above, either at its top level or per run
under `trials[RUN_ID]`. Missing attestations remain findings, never defaults.

Supply `ledger.json` exported by a separate read-only query of the existing
monthly authority. Its request set can include other runs; only declared campaign
and additional probe identities enter this report:

```json
{
  "authority": "canary-bots-wsl_brain-state:/state.sqlite3",
  "snapshot_utc": "2026-11-06T00:00:00Z",
  "budget": {"cap": 50000000000, "spent": 14, "reserved": 0, "available": 49999999986},
  "requests": [{"id": "REQUEST_ID", "run_id": "pilot:openai:0", "month": "2026-11", "reserved": 1000, "spent": 14}]
}
```

All money is integer nanodollars; unknown usage has `spent:null` and retains
`reserved`. Export only request IDs/run IDs/month/reserved/spent, not whole
learning records, credentials or the complete live SQLite file. The snapshot
retains liabilities from other runs/months. The checker cannot establish the
canonical origin of an arbitrary JSON; retain query/source provenance.

For previously billed probes add audit-envelope fields
`additional_cost_run_ids` and `total_cap_nanousd` alongside `plan` in a derived
experiment review copy. Preserve the original runner file and fingerprint.
Additional probes enter total spent/unknown liability without becoming scored
gameplay samples. Declare the ceiling including probes (for example USD7), not
just the USD6 ceiling of six model game runs. Do not reuse old probe identities.
Every declared probe must appear in the ledger export. Invalid amounts or
missing probe rows reject review and set `financial_totals_complete:false`;
the tool never labels the remaining valid subtotal as a complete cost.

## Run

From `deployment/brain`, using the installed Python environment:

```bash
PYTHONPATH=src python tools/m5_report.py \
  --recording /path/to/campaign/recording.sqlite3 \
  --experiment /path/to/campaign/experiment.json \
  --trials /path/to/trials.json --ledger /path/to/ledger.json \
  --output /path/to/new-final-report
```

Repeat `--recording` for multiple files or archived runs. Use
`--require-completed` for free qualification; every attempt then needs positive
saved XP and `reason=completed`. Without it, predeclared gameplay stops such as
`deaths_limit`, `stalled`, `proposal_timeout` and `budget_stop` remain measured
failed/budget outcomes. They are not discarded or relabeled successful.

Every `completed` attempt, with or without `--require-completed`, must have its
observed sample span and both worker clocks within
`[plan.seconds, plan.seconds + horizon_tolerance_seconds]`. The default upper
tolerance is five seconds: a1800-second run must cover1800–1805 seconds, and a
10-second smoke10–15 seconds. A stricter tolerance can be predeclared alongside
`plan` in the review envelope as `horizon_tolerance_seconds` in the range0–5.
A larger value is rejected so an overrunning run cannot gain extra XP/time and
still pass as the intended horizon. Failed/budget outcomes remain visible and
are not subjected to completed-run acceptance.

Exit0 means evidence consistency passed, exit2 means review findings. Missing
attempts, mismatched fingerprints, gaps, short completed horizons, saved XP/level
differences, image/cleanup gaps, inconsistent costs and cap excesses produce
findings. Input file/WAL hashes are checked for changes during review and included
in the report. Use closed evidence snapshots. Existing output is refused so an
interrupted rerun cannot mix old and new artifacts.
SQLite may create empty WAL/SHM files even for a read-only open. The checker
therefore opens private copies, preserving the original filenames and bytes.

## Output and interpretation

- `report.json`: per attempt, v2 XP/death/intervention/native-ownership metrics,
  ledger charges/unknown liabilities, request correlations and latency by
  effective `deadline_ms`, including offered TTL/action classes when recorded.
- `report.md`: compact comparison, stop causes, money and interpretation.
- `acceptance.json`: machine-readable consistency findings and review status.

Cost calculations are independently recomputed from recorded usage and the
participant's versioned prices, then compared with canonical request rows.
Actual settled/unknown ledger amounts remain in totals even if a recording is
missing or inconsistent. A zero-cost native baseline has no infinite XP/dollar.
An unknown cache-write price may be null only when the observed write count is
zero; positive writes cannot be independently priced with that value. The
instrumented worker retains such requests as `UnpricedCacheWrite` liabilities.

The p50/p95 here uses completed responses and is explicitly deadline-censored.
Timeouts/cancellation/other failures are separate by effective deadline.
The legacy lifecycle generic `RuntimeError` cannot prove an exact backoff skip
or its TTL. A source instrumented with a specific `ProviderBackoff` class can
declare `instrumentation:{provider_backoff_classification:"ProviderBackoff"}`
beside `plan` in the review envelope. Then that type is counted exactly,
including a meaningful zero; without the declaration the exact count remains
unavailable. Confirm the declaration against the pinned source. The generic
RuntimeError count stays separate. When the source also records request
`phase:"skipped",reason:"backoff",deadline_ms,reserved_nanousd:0`, add
`instrumentation.request_backoff_events:true`. These skips are then counted by
deadline/TTL without requiring a SQL request or incrementing the denominator of
reserved HTTP attempts. They never create a charge. This evidence path takes
precedence over lifecycle counts so one skip is not counted twice. Without the
request instrumentation, per-TTL backoff remains unavailable. Do not call the
total model latency distribution from the successful-response p95.

Distributions use independent attempts, showing raw XP/hour values, median and
range. The verdict is always a descriptive pilot without an inferred winner.
Hunt/resupply topology, provider invoices, human acceptance and AFK safety still
need their own evidence; `ready_for_review` does not close #10 automatically.

Pure regressions cover exact-horizon rejection (including the old37 ms short
case), canonical cost/unknown-liability conservation, identity collisions,
saved XP, mutable-image mismatch, unverified cleanup, unavailable native deaths,
unclassified backoff, extra probe costs and read-only archive/CLI reruns.

## Validation on2026-11-06

Twenty-four pure tests, Ruff lint/format and strict mypy passed. Independent
review reproduced and then rechecked corrections for omitted attempt-grid
entries, inconsistent initial characters, missing/malformed probe liabilities,
plan changes between read/hash and trial files appearing during review. Tests
also distinguish reserved HTTP attempts from zero-liability backoff skips and
nullable unknown cache-write rates.
After updating the review branch to main `cd021c806`, the combined report,
backoff-observability and unknown-cache-write subset passed29 tests.

The checker was exercised read-only on the closed native10-second current-runner
smoke at `/tmp/m5cur-n10-20261106b`. It read11.145 recorded seconds, zero request
cost/unknown liability and eight input hashes. It correctly refused acceptance
because that input attestation did not explicitly supply `images_verified` or
`resources_cleaned`; those flags were not invented to make it pass. Private
review artifacts: `/home/daniel/canary-maintenance/m5-report-smoke-20261106T104425Z`.
No game database, live provider or monthly ledger was opened by the report tool.

An independent PR review then reproduced an overlong `completed` attempt being
accepted: only the lower horizon bound had been checked. The follow-up fixes
the upper bound for both default and free-qualification modes, including the
sample span and each clock independently.42 reporter regressions and47 combined
report/backoff/cache tests passed, along with Ruff and strict mypy. The3600-second
case now fails against a1800-second plan;1805 seconds passes and1805.001 fails.
