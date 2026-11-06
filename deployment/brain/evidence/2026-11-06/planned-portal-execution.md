# Planned portal execution after a skipped approach

## Native build and captured diagnostics

The isolated build of `667631ba7637c8021e1070a9f0237387080ebb68` passed
155 native unit tests and produced zero GNU UNIQUE symbols. Its audit is
`/home/daniel/canary-maintenance/planner-build-20261106T115452Z/result.json`.

| Artifact | SHA-256 |
| --- | --- |
| Source archive | `c0e70465f66b3880e34bb1186ae04e3cdfe9ac4661e6d3743a2efb673a4960b4` |
| Canary executable | `678a45f6390869b41c9feeaa893f0f38a513bbf19b19068963a786a97863cc9d` |
| Bot library | `492a3e6a7d899cfa5e58f828c1127b1714f602c3f53139aeb4b2b8453a7b5fec` |
| Derived game image | `52fbd02e79d3323818f78092a7ef37dc2b1c41e9fd60a4ba67b73aa6aa3827b3` |

The new approach-progress clock removed the captured 28-second failure in
diagnostic C (`/tmp/m5ret-diag-20261106c`): it recorded 60.338 seconds and
45 distinct positions, ending at `(32425,32159,7)` with retreat still running.
This proved continued movement, not arrival.

Diagnostic D (`/tmp/m5ret-diag-20261106d`) kept the native deadlines unchanged
and observed the same checkpoint for 240.745 seconds without rescue. It ended
at `(32425,32165,7)`, with 48 distinct positions and no arrival. The executor
cycled between approaching and verifying the floor change. Full logs and
replays were preserved before the isolated containers and networks were removed.

The target portal is `(32427,32170,7)`, ground 433 with `FC_DOWN`; its landing
has dirt 352 and ladder 1948 at z=8. This is a walk-on hole and ladder return,
not evidence of a missing rope or shovel.

## Confirmed execution defects

D skipped its terminal waypoint after the existing 15-second near-portal
allowance. The floor-change consumer treated `idx >= size` as an action having
fired, although timeout/path skips also consume the cursor. It entered
verification without reaching the portal. An earlier door arrival must not
validate a later skipped terminal either.

D also blacklisted the portal at 12:06:22 and reused it at 12:06:23 through the
cached hop, without a new route search. Reset cleared the active floor-change
plan while retaining that cached hop.

The focused correction records the exact last waypoint reached by arrival or
action. The portal executor verifies only an actual terminal acknowledgement
or an observed floor change. A skipped terminal enters the existing bounded
approach-failure path. Reset invalidates the hop cache, and cache consumption
checks whether quarantine changed since the fresh route decision. A deliberate
fallback records the observed expiry and can reuse that decision until it changes.

Two additional contracts were reproduced by compiling the actual helper and
consumer code with controlled state: the first bounded retry was being reset
by its caller, erasing its retry counter; and a refused floor-change start after
five failures was nevertheless reported as a successful handoff. The caller
now retains the helper's retry state and propagates refusal as a failed walk.
These controlled-state failures were not claimed to have occurred in D.

No timeout, route budget or portal-selection policy changes. A fresh route
search may still use the existing, explicitly logged blacklist-recovery policy;
cache invalidation is not a promise that a fresh search never selects that portal.

## Regressions and remaining gates

`python3 tools/bot_brain/test_planned_portal.py` exercises the real terminal
consumer, cached-hop gate, retry helper, reset, floor-change start and handoff.
The previous code failed terminal skip, earlier-arrival plus terminal skip,
bounded retries, refused handoff and cached quarantine cases at runtime.

The direct route diagnostics and their BFS/cache/floor-boundary tests are
separate commits. They compare the same search algorithms without changing
their decisions, and must be used to distinguish a budget-exhausted BFS from a
genuinely unavailable direct leg on the real map.

A fresh isolated build and retreat without rescue remain required. Neither
the timeout correction nor this execution correction establishes arrival,
fixture qualification or permission to start paid trials.

The initial hunt stall remains a separate investigation. Diagnostic E
(`m5hunt-restart-diag-20261106e`) restarted hunt399 at `(32374,32092,7)` and
entered patrol, but only after skipping its entry waypoint at 36 seconds. The
brain's authored-route limit and macro restart were not changed here; three
five-minute `hunt_progress` outcomes are progress windows, not complete cycles.
