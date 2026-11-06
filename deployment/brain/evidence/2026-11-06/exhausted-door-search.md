# Exhausted door search must not discard a direct route

## Captured real-map proof

Diagnostic G used source `3f829b6b8c4f793ecf613c7c78e7c9936248d4e9`,
game image `sha256:34365530c377ad3e974ed99f961e7b617561c601dd8bd63b36855c076c7e5f3c`
and the current QA application `dbf72473`. Its isolated native build passed
155 unit tests with zero GNU UNIQUE symbols. Raw evidence is preserved at
`/tmp/m5ret-diag-20261106g`, including `diagnostic-commands.jsonl` and the replay.

Before the retreat, these commands traced explicit source coordinates without
moving the actor, whose observed position remained `(32372,32103,7)`:

```text
route 32372,32103,7 32369,32241,7 direct
route 32425,32165,7 32427,32170,7 direct
```

The first query targets the Thais temple. Its door BFS exhausted its existing
20,000-cell budget: 20,002 visited, 19,829 expanded. The existing bounded A*
could nevertheless reach the destination:

| Profile | Arrival radius | Result | Path tiles | Created / closed nodes |
| --- | --- | --- | --- | --- |
| Stock, radius 50 / 512 nodes | 0 | Budget exhausted | 0 | 512 / 441 |
| Stock, radius 50 / 512 nodes | 2 | Budget exhausted | 0 | 512 / 441 |
| Wide, radius 200 / 4,096 nodes | 0 | Reached | 166 | 541 / 299 |
| Wide, radius 200 / 4,096 nodes | 2 | Reached | 164 | 535 / 297 |

The second query traces the later stuck checkpoint to the selected hole. Both
stock and wide A* exhausted their node budgets, including at arrival radius two.
That proves failure under those limits, not mathematical disconnection of the
portal. This explicit-source trace is not a claim that the actor was already
at the later checkpoint when the query ran.

G's retreat `33b01eaf9fb24fadae78661f9fd01b5b` eventually failed with
`return_route_unavailable` after 209.286 seconds. The recording spans 240.618
seconds and never samples arrival. Its isolated resources were removed. The
setup used explicit operator pause/retreat, so it is diagnostic evidence, not
an accepted scored run. The later hunt77 was an ordinary policy choice after
that failure and is not a successful return.

## Focused routing correction

The boolean door-search result remains unchanged for existing callers. A new
optional exhaustion output records whether a false result came from the node
budget, and the cache retains that cause alongside the boolean. Cache hits,
forced refreshes and floor mismatches initialize or restore the cause explicitly.

When the same-floor search exhausted its budget, the scoped planner first tries
the existing `goToWide` helper. A successful bounded direct path ends planning
before portal selection. Failure or cooldown preserves the previous graph
fallback, without also executing the ungated direct-search step a second time.
An exhausted frontier continues to the existing graph path directly.

The helper's 4,096-node limit, radius 200 and existing 15-second failed-search
cooldown are unchanged. Success clears its cooldown as before. The door BFS
budget/radius, cache lifetime, bypass behavior, ordinary walker and portal
selection policies are unchanged. The observational `route ... direct` command
still uses its separate uncached search wrapper.

## Regression and remaining acceptance

`python3 tools/bot_brain/test_exhausted_planner.py` compiles the real scoped
planner consumer, door cache and wide-search helper. The previous consumer
and cache failed the unknown-budget rescue, cached cause, failed-wide cooldown,
forced refresh, cause-output and floor-output cases at runtime.

The regression covers fresh and cached budget exhaustion, frontier failures,
the legacy boolean API, refresh, floor mismatch, existing clear/door routes,
successful preemption of the graph and bounded failure/cooldown behavior.

A new exact build and an isolated retreat without rescue must confirm physical
arrival. This captured route proof and code regression do not themselves qualify
the fixture or complete the comparative benchmark. The authored hunt-entry
timeout observed in diagnostic E remains a separate issue.
