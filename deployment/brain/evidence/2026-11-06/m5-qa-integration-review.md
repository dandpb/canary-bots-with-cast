# Combined QA guards after interrupted final attempts

This follow-up combines PR25 evidence head `2a52504fb` with main
`b33e1602fa03120e5c9e37e6e2b19679f2d7ed12` and QA branch `47adddc40`.
The single guide conflict was resolved by preserving both imported-source
attestation and explicit stable command directories. The timed driver keeps
observed-window XP checks from `26d2e9667` and now supervises its status observer.
No frozen attempt, producer code snapshot, fixture, database bind or original
receipt was modified. No new live qualification or paid request was started.

## Standards

Independent review found zero documented violations and no new actionable code
smell in this integration. Command directories remain explicit, and one named
helper owns bounded native status polling. The earlier possible duplication of
image attestation is outside this delta and was not refactored.

## Spec

Review found one P2: twenty empty status polls silently produced an empty row,
so a prior valid phase cycle could hide the later loss of status. The correction
raises `TimeoutError` after those polls and rejects invalid command identities
or malformed processed native responses. The supervising wrapper records
`observer-error.json`, requests stop, awaits the worker's flush and propagates
failure. Final acceptance checks that persisted observer diagnostic even when
the earlier cycle is valid.

Five new regression subcases failed before the correction. After correction,
the independent Spec reviewer reran all seven observer tests successfully and
reported the P2 resolved with no new blocker. The source-import and observed-XP
guards remain intact. Totals: Standards zero new findings; Spec one P2 found and
resolved, zero remaining findings in the reviewed delta.

## Validation

- All 48 directed QA tests passed, including a real POSIX signal/cleanup check,
  an invalid inherited-directory regression using a fake Docker executable,
  malformed status, exhausted polls and lost status after a valid cycle.
- Ruff lint and format checks passed on all seven QA Python files.
- Full runtime pytest execution: 391 passed; six setup tests failed because the
  sparse worktree omitted `deployment/wsl`. After adding that tracked directory
  to this worktree's sparse paths, all six failed setup tests passed on rerun.
  This is not described as one full execution with 397 successes.
- The interrupted-attempt verifier still checks all 48 checksums and both replay
  archives with `accepted=false` and `paid_pilot_admitted=false`.
- `git diff --check` passed. Earlier evidence remains unchanged.

```sh
PYTHONPATH=deployment/brain/src:tests/fixture python -m unittest \
  test_m5_qualification_gates test_m5_current_source \
  test_m5_current_lowstock test_m5_observer -v
PYTHONPATH=deployment/brain:deployment/brain/src python -m pytest \
  deployment/brain/tests -q
PYTHONPATH=deployment/brain:deployment/brain/src python -m pytest \
  deployment/brain/tests/test_gateway_setup.py -q
python deployment/brain/evidence/2026-11-06/m5-final-interrupted-attempts/verify_bundle.py
```

The native/fake attempts remain interrupted at 1,338.798/1,338.790 sampled
seconds. Their five-row partial phase logs do not prove a full cycle. Cleanup
exception preservation is the separate coordinator-owned PR51; current private
Redis/gateway policy mounts and runtime coordination still need attestation.
Neither unit tests nor this integration admit the paid pilot or establish human
party acceptance. A new live attempt requires coordination after these gates.
