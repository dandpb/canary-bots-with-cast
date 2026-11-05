# Free M5 qualification

This harness runs only `native` and a declared deterministic `fake` choice policy.
It uses a fresh public-seed database, one knight GUID 65001, an internal Docker
network, no published game/database ports, and no production volumes. The worker
refuses provider clients and credential reads. It never tests account entitlement,
real inference, human usefulness, or a winning model.

Run in Linux/WSL from an isolated checkout. External local prerequisites are the
matching `canary-party-qa:local` image/artifacts from the #22 native validation,
the compatible `/tmp/canary-lifecycle-qa-world.otbm` world, and the existing Python
environment `/tmp/canary-replay-venv`. The map and binaries are not redistributed.
The preparation manifest captures their hashes and the actual derived image ID.
The reused native artifacts have base revision `33c6a578`; the preparation check
found no bot-core source difference through main `a2bbf1c0`. Private timing
instrumentation from #22 remains in these QA binaries and is not a production
runtime change.

```sh
cd /path/to/isolated/repository
export PYTHONPATH="$PWD/deployment/brain/src"
export CANARY_M5_QA=/tmp/m5q-UNUSED-ID
python tests/fixture/m5_qa.py prepare
python tests/fixture/m5_qa.py native
# Run the passive status probe from another terminal while the run is active:
python tests/fixture/m5_probe.py "$CANARY_M5_QA/native"
python tests/fixture/m5_report.py "$CANARY_M5_QA/native"
# After the native stack has stopped, restore the same fixture independently:
python tests/fixture/m5_qa.py fake
python tests/fixture/m5_probe.py "$CANARY_M5_QA/fake"
python tests/fixture/m5_report.py "$CANARY_M5_QA/fake"
```

`prepare` refuses an existing directory. Each mode also claims a new attempt
directory; interrupted attempts are retained and cannot be silently overwritten.
Docker project names derive from the full attempt identity hash. The harness
always tears down its own project in `finally`, retaining bind-mounted evidence.
Do not manually delete directories/volumes to turn failures into reruns.

The first calibration `m5q-20261105a` was invalid: standard market funding changed
the bank to 100 billion gp and the stock status port did not match the healthcheck.
It was stopped and preserved. Candidate `m5q-20261105b` fixes both **only in its
private image**. Funding and market scripts are moved outside the loaded script
tree; production scripts are unchanged.

The deliberately controlled scenario differs from the unrestricted world:

- Knight 20 / 98,800 XP, normal 365 HP / 95 mana, skill50 and magic4,
  10,000gp bank, 20 health + 20 mana potions, level20 equipment from the pinned
  authored table. Standard startup may normalize item SIDs or provision an
  auxiliary item; preserve initial SQL and live/saved inventory evidence.
- Only hunt routes 77 and 399 enabled. Route77's vocation mask is adapted to
  knight. Other routes remain in the CSV but disabled. Both runs restore the same
  full authored directory and database seed.
- Native hunt clock is fixed at600s; hunting activity weight100, other ambient
  activity weights0; short idle dwell and no ambient roaming. Hunt termination
  still waits for a patrol lap, so600s is not proof of a completed cycle.
- Candidate B retained the default50% re-hunt chance and could finish a hunt with
  no activity available during its native cooldown. It stopped correctly for
  stagnation at1,637.274s and was not accepted as a full window. Candidate D sets
  `botResupplyRehuntPct=100` equally for native/fake. Its image digest is distinct;
  it must not be pooled with B just because the SQL/map hash is the same.
- Standard natural world spawns and combat remain intact. No monsters are spawned,
  damaged, or removed by the harness during a timed run. No human leaders or
  gameplay orders are injected. Keep-awake is enabled in both modes.
- Native is a shadow observer. Fake uses the production active controller with a
  fixture-only explicit preference for route399/77 and eligible resupply. Frozen
  memory prevents policy learning/reflection overrides. This is not inference.

The optional probe queues only the read-only `status` command, at most once per
10 observed seconds after540s, to inspect native hunt phase/kills/waypoint. It
does not issue movement, supplies, teleport, healing or stop commands. These
inspection operations and their start times remain in `phase-status.jsonl` and
the native logs; they are not silently counted as model choices or human rescue.

After the harness has stopped and saved its database, `m5_finalize.py RUN_DIR`
checks the recorded duration, XP persistence, gaps and zero inference before
updating recording metadata. It refuses an active run and writes a new analysis
file exclusively. A completed horizon is distinct from a completed supply cycle;
stock/bank and native outcome evidence must still establish a purchase.

The monotonic horizon begins at the first valid observation, not provisioning or
healthcheck completion. The supervisor stops at1800s, after three observed deaths,
five seconds without observations, ten minutes without observed position/XP/
supplies/defeat-counter progress, a generation change, recorder error, or more than
30s without a locally validated selection in an open model-choice opportunity.

A model-choice window starts with the controller's actual `requested` event with
multiple filtered options. Repeated requests do not restart it. A locally
validated `selected` event clears it; a mere `model_proposed` does not. Native
objective execution, death, candidate disappearance or a single-candidate decision
closes the window. Native baseline has no provider-proposal deadline. Local
validation is distinct from a later server acknowledgement; report rejections and
expired actions separately. Stagnation here is lack of observed change, not proof
that movement is useful or that circling is productive.

Policy and real-worker fault tests:

```sh
cd tests/fixture
python -m unittest -v test_m5_stop
python -m unittest -v test_m5_worker_stop
```

The IPC tests use a private synthetic datagram peer, not a game server. They cover
native/fake deaths, world change and observation loss, fake proposal blocking
with a real30s interval, and fake stall with a scaled1.2s threshold. No paid
request is permitted; process exits, socket cleanup and zero ledger rows are
asserted. The separate two real-game1800s windows validate the actual horizon.

Qualification requires1,795–1,805s between recorded first/last samples, authoritative
XP and saved DB agreement, observed hunt/return/supplies evidence, alternative
choices, no critical evidence gaps, and zero fake/native inference requests.
Do not label a running/incomplete recording complete just because1800 appeared in
the configuration. Production spending and real account probes remain separately
gated; these temporary no-inference ledgers are never a new paid allowance.
