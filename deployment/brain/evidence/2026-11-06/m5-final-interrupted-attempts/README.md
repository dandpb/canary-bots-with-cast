# Final free attempts — interrupted, not accepted

Both attempts preserve `interrupted` / `operator_stop`, not completion. They do
not qualify the requested1,800-second horizon, and **paid pilot admission remains
false**. Cancellation origin is unresolved: that stop label alone is not proof
that an operator sent a signal.

| Mode | Recorded first→last samples | Observed XP | DB XP, postmortem copy |
|---|---:|---:|---:|
| Native | 1,338.798 s | +2,420 | 101,220 |
| Explicit scripted fake | 1,338.790 s | +2,812 | 101,612 |

No recorded deaths, gaps, human interventions, automatic recovery requests or
inference requests occurred. This is a controlled fixture, not a model ranking.
The free runs were parallel functional checks, not latency comparisons.

## Producer, evaluator and frozen identities

The producer application is `1e25dc174b6a50af276983697df2ca4a5764f255`, containing
the canonical worker from main `92e0084db43b6df2f49614ec56a823a64370e104` plus
the frozen QA driver. Exact native build is
`d43050147bc13d8024bdc66b641b127c31253b7c` (PR47). Game image:
`sha256:9bd6213c4d37fa9acdb46c4149d4f3427c3af1d6e1ed6b8b6599c37244185b99`.
MariaDB image:
`sha256:a794d9eb009e20de605858a11f32f63b4075cbd197c650436f0e3b457e4caed7`.
These identities were inspected at runtime; executable/library hashes and the
native build attestation are retained per mode. The shared fixture is
`42467745d544801e44e32deecf99f5f6d1e1aa869e2bf227734daf95ae42e5be`.
Only controlled hunts77/399, their declared mask, timing and weights apply.

The later acceptance evaluator is
`26d2e9667a36059a66635335f667c6deb2717728`. It adds an observed-window XP gate
and binds future driver imports to the driver checkout. Both recorded runs show
positive observed XP, but their timing/completion/cycle acceptance is false.
The new import guard did not execute inside the old producer. Its recorded
launcher explicitly pinned the frozen source, clean revision and code hashes.
The original qualification JSON and canonical saved-character export are absent
because execution raised before that postprocessing. No replacement was written
into the original output. `reviewed-qualification.json` is explicitly a later
assessment using separately labelled postmortem state.

## Failure and evidence limits

Each replay includes an `orchestrator-failure` event with category
`CancelledError`. Launcher PIDs, original command metadata, start times and exit
codes1/1 are retained in the labelled launcher copies. The producer stdout ends
with `RuntimeError` from `harness.close`; both command logs contain
`getwd: no such file or directory` and Compose validation failure.
The cleanup exception can mask an earlier cancellation, so it does not establish
the cancellation's source or who removed resources.

The original `producer-resources-cleaned.json` reports **false**, with container
and network identities. A later exact-label inspection found those resources
absent and is retained separately. Neither report was rewritten and no removal
actor is inferred. The original service-log files say log capture was unavailable;
they are not full native logs. Each status-inspector file contains five rows,
ending around582s. No missing phase or full hunt cycle is invented from positions
or from a later textual checkpoint.

## Postmortem database method

Canonical `saved-character.json` files were not produced. Instead, each closed
private QA database bind was mounted read-only into a self-removing offline
helper and copied to a new private directory. A temporary MariaDB of the same
pinned image opened only that copy, with `--network none`, no host ports, and no
game process. It read character65001's named fields. The original349 files in
each source database had equal hashes before copying and after the copied DB
query. Source database binds, env files, original cleanup reports and replays
were not rewritten. No game, map, binary, database or env file is published.

The first native forensic cleanup check raced asynchronous container removal and
reported false. Its original receipt is preserved; the later source-integrity
receipt confirms removal. The fake forensic receipt and both later inspections
confirm no temporary forensic DB remains. These copies are forensic observations,
not new qualification attempts, canonical exports, resets or resupply proofs.

## Offline verification and preservation

`public-provenance.json` links public copies to the original file hashes. JSON
and log copies replace private prefixes with path labels; compressed logs have
their own hashes. The two replay archives retain original logical events and
were reimported successfully. `checksums.json` addresses the actual public bytes.

```sh
python deployment/brain/evidence/2026-11-06/m5-final-interrupted-attempts/verify_bundle.py
```

Historical Nov5 evidence and the previously published Nov6 failed/diagnostic
attempts remain separate. `previous-evidence-preservation.json` records their
unchanged Git trees and all89 historical checksums. No free failure was relabelled
as completion. No paid request or new qualification was started by this review.
The Redis/current-gateway gate remains a separate coordinator-owned false gate.
