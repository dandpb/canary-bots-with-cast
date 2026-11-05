# Interrupted rerun isolation — PR #22 follow-up

Review: [6657401143](https://github.com/dandpb/canary-bots-with-cast/pull/22#issuecomment-6657401143).
The measured values were independently confirmed. This correction addresses the
protocol for later runs; the existing 27-window dataset is preserved unchanged.

## Reproduction

The initial regression copied the published valid inputs into a temporary work
directory, marked the three-bot inputs as one round and the optional 997-bot raw
as another, then called the real reporter. It also called the real `create` path
with retained partial raws, substituting Docker responses without contacting a
daemon. At `d9c507c75`, both assertions failed:

```text
python3 -m unittest -v test_party_run
AssertionError: FileExistsError not raised
AssertionError: ValueError not raised
Ran 2 tests in 0.326s — FAILED (failures=2)
```

The causes were permissive work-directory reuse and reporting by fixed filename
without provenance validation. A third path, blind producer restart, could
overwrite the initial cohorts while leaving a completed population file behind.

## Correction

- Build artifacts have a separate directory. `create` exclusively claims a new
  or empty work directory and writes an immutable UUID manifest before setup.
  Old/partial directories are rejected without deleting their contents.
- Producers reserve outputs, stamp raw rows/metadata with the manifest identity,
  and atomically update checkpoints. A restarted producer cannot overwrite an
  existing attempt. The explicit scenario resume validates identity first.
- Game/DB resource labels bind mutations to the same round. The reporter loads
  every required/optional input once, validates all identities before output,
  and exports into a per-round directory. It rejects untagged legacy inputs.
- Historical measurements receive no invented identity and remain intact.

## Validation

Eleven offline tests pass, including the two original reproductions, interrupted
checkpoint publication, producer restart, cross-round scenario resume, foreign
metadata/container rejection, coherent-report acceptance and separate exports
for a later three-bot-only round. The positive report case retains the original
8,556-tick totals. Test data identities are synthetic and exist only in temporary
directories; these tests are not new gameplay measurements.

```sh
cd tests/fixture
python3 -m unittest -v test_party_run
```

Ruff lint and formatting cover the eleven fixture/test Python files. No native
runtime source changed, no game server was started and no provider was called
for this follow-up. No debug instrumentation was added.
