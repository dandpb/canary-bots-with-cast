# Planner waypoint progress during autonomous retreat

## Captured failure

The current-runner fake qualification at `/tmp/m5cur-f1800-20261106a`
stopped with `reason=stalled`, after 1,508.716 seconds (1,508.565 seconds
recorded). It gained 1,993 XP through three completed `hunt:399` objectives,
then stopped moving at `(32372,32103,7)`. This is failed qualification evidence.

The frozen runner/source is `c9e447c500d1c245e7ea3736934eacfda0b5d445`;
the relevant native files match native base `33c6a578`. The game image is
`sha256:a0cebf352f4750e7d20a13df82beaca79fa21025b8a335b5bc8b4fc39c2aa96c`.
The original files and recordings were preserved without modification.

Diagnostic B used a new directory `/tmp/m5ret-diag-20261106b` and isolated
Compose project `canary-bench-680ae8cd376ce7963926`. The same map and image
started the character at the stalled position. Explicit operator pause and
retreat passed through the ordinary Supervisor/intent path. No provider was
called. Its logs and commands were captured before all diagnostic containers
and the project network were removed.

The retreat chose a hole at `(32427,32170,7)` while returning to the Thais
temple `(32369,32241,7)`. The latter position was verified in the mounted
OTBM Town node, and in the session's `home` field. It did not use the authored
`travel_from` path of either hunt.

| Recorded time | Position during retreat |
| --- | --- |
| 23.702 s | `(32372,32103,7)` |
| 29.748 s | `(32376,32111,7)` |
| 35.773 s | `(32378,32122,7)` |
| 41.783 s | `(32384,32129,7)` |
| 47.806 s | `(32391,32134,7)` |

Despite this movement, action `b2e41b84cf4d4950b4a215c7063e2e93` failed with
`return_route_unavailable` after 28.213 seconds. The native log reported
`ZLEG: Skipping stuck hole ... (28s elapsed)`.

The per-waypoint elapsed time started at approach initialization, while its
limit was recalculated from the remaining distance every tick. The initial
67-tile distance allowed 41.8 seconds; at `(32395,32138,7)` it allowed only
27.8 seconds. A moving character therefore crossed the contracting threshold.

## Focused change

Only the three scoped planner approach configurations opt into movement
progress tracking. Their per-waypoint clock updates when the character reaches
a new best Chebyshev distance to that waypoint, including while a walk queue
is active. A changed waypoint index or target initializes its clock; oscillation
between previously reached distances does not renew it. Replanning the same
waypoint retains its progress history.

Authored hunt, city and quest followers retain their existing behavior by
default. The existing global timers remain unchanged: they measure time
without waypoint-index advancement, with 60 seconds for the portal approach
and 120 seconds for a same-floor planner leg. Existing leg reconstruction and
other existing reset sites still apply. These are not new absolute journey caps.

No door-search, A*, portal selection, route data or fixture change is included.
The separate possibility that a bounded door BFS reports an exhausted search
as unreachable remains a hypothesis to investigate only if the next captured
failure requires it.

## Regression and remaining acceptance

`python3 tools/bot_brain/test_planner_progress.py` compiles the actual global
and per-waypoint timeout gates with a fake clock. The recorded 28-second
approach failed its runtime assertion before the change. The regression covers
movement, movement with a queued walk, a stationary timeout, oscillation,
retargeting the same index, the legacy default and the unchanged global timeout.
`python3 tools/bot_brain/test_movement.py` also passes.

These tests exercise the timeout consumer without loading a map. A rebuilt
isolated game must repeat diagnostic B without rescue and record actual arrival
or the next failure. Passing these tests alone does not establish successful
navigation, a complete resupply cycle or readiness for paid benchmarking.
