# Direct route diagnostics

`route x1,y1,z1 x2,y2,z2 direct` bypasses the portal graph. It reports:

- A fresh call to the planner's existing door-permissive BFS, including visited
  and expanded cells, its budget/radius and whether its frontier or budget ended.
- The existing stock and wide A* profiles, each with exact arrival and a two-tile
  arrival radius. Results include created/closed nodes and the termination reason.

No search budget, route decision or movement command is changed. Ordinary
`route` and `route ... wide` keep tracing the graph's chosen legs. A failed
bounded BFS is not proof that the entire map has no route.

For the captured Thais retreat, compare these read-only commands on an isolated
diagnostic game, using an awake bot as the movement permission context:

```text
route 32372,32103,7 32369,32241,7 direct
route 32425,32165,7 32427,32170,7 direct
tileinfo 32427,32170,7
tileinfo 32427,32170,8
```

The second trace distinguishes the stock/wide profiles at the floor-change
handoff. Exact arrival retains the existing walk-on floor-change whitelist.

Run the real BFS-prefix regression without a game, database or provider:

```sh
python3 tools/bot_brain/test_door_search.py
```

The open-grid case demonstrates that a reachable 138-tile target can exhaust
the 20,000-cell BFS budget; it does not establish the outcome on the Tibia map.
