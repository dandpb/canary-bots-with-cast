# Offline party acceptance fixture (#1)

This fixture exercises the production native party/brain adapters and the Python
worker with its explicit `fake` provider. It uses a separate labelled game,
MariaDB volume and internal Docker network named `canary-party-qa`; no ports are
published. It never mounts provider credentials. It is not a human playtest or a
wire authentication/client acceptance test.

## Local prerequisites

Run from an isolated checkout of the revision under test. The local development
image `canary-bots-wsl-game:local` supplies the datapack and runtime dependencies.
An independently configured build cache supplies `/source`, `/build` and
`/opt/installed/x64-linux`; the fixture does not configure or mutate production.
The external world fixture is `/tmp/canary-lifecycle-qa-world.otbm` (read only).
Python 3.12 worker dependencies are supplied read only at
`/tmp/canary-replay-deps`. These assets are intentionally not committed.

Build `tests/fixture/party_build.py` in a disposable container with this checkout
mounted at `/review:ro` and `/tmp/canary-party-qa-build:/out`. Build outputs stay
separate from the run directory. It synchronizes the
current native source, configures/builds `canary`, `bot_engine` and `canary_ut`,
runs the native unit binary from `/source`, and compiles `party_acceptance.so`.
Only the private build copy of `bot_tick.cpp` receives a timing scope. The product
source and ABI are unchanged. The timing export drains bounded samples of
`[complete_tick_us, tickBrain_call_us]` from the dispatcher. The disabled call is
measured too; a disabled bridge has no published status samples.

The native module constructs connected loopback transports and calls normal
`ProtocolGame::login` for two ordinary account characters. The unread handshake
timer is cancelled explicitly; a QA loop calls the normal pong/idle-reset handlers
and drains outbound data. Explicit `Connection::close(true)` still exercises
production disconnect/release. None of this proves authentication, network client
behavior or human follow skill. Bot invitations and leadership transfer use real
`Game` entry points; targets and purchases use native gameplay adapters.

## Commands in WSL

```sh
export CANARY_PARTY_QA_BUILD=/tmp/canary-party-qa-build
# Choose an unused directory for every attempt, including an interrupted rerun.
export CANARY_PARTY_QA_WORK=/tmp/canary-party-run-20261105-a
python3 tests/fixture/party_qa.py create
python3 tests/fixture/party_qa.py setup
# Wait for all three bots to accept the invitations and enter the five-member party.
python3 tests/fixture/party_metadata.py
python3 tests/fixture/party_perf.py --seconds 30
python3 tests/fixture/party_combat_perf.py
python3 tests/fixture/party_scenarios.py
PYTHONPATH=deployment/brain/src python3 tests/fixture/party_policy.py
python3 tests/fixture/party_metadata.py
python3 tests/fixture/party_report.py
python3 tests/fixture/party_population.py
python3 tests/fixture/party_combat_perf.py --population 997 --output party-population-perf-raw.json
python3 tests/fixture/party_metadata.py
python3 tests/fixture/party_qa.py stop
python3 tests/fixture/party_report.py
```

Run command-based scenarios sequentially; the private command adapter has one
dispatcher command slot. `stop` verifies labels, network and absent host bindings
before stopping only this game and database, preserving the QA volume/artifacts.
After a failure, retain its output and inspect the private stack; stop it when the
investigation finishes. Reusing existing Docker names is intentionally rejected by
`create` rather than deleting another run's containers or volume.

## Run identity and interrupted attempts

`create` claims a new or empty directory with an exclusive `run.json` manifest.
It refuses any existing contents before calling Docker or writing fixtures, and
copies only the three build inputs from `CANARY_PARTY_QA_BUILD` into the new run.
The chosen directory remains claimed if initialization fails. Keep it for
inspection and select another unused directory; no old data is removed for you.
Existing QA Docker names still require explicit operator cleanup before another
creation. Changing the work directory does not bypass those resource guards.

Raw rows and metadata carry the manifest's `run_id`; game/database/container
checks also verify the matching label. Each measurement producer reserves its
output before beginning and refuses to overwrite an earlier attempt, including
an empty or partial checkpoint. Only `--resume-after-hunt` is an explicit resume
path, and it validates the saved identity and phase before touching the game.
Checkpoints are written atomically. Metadata can be refreshed within the same
round; foreign or untagged existing data cannot be relabelled by a writer.

The report snapshots and validates **all** selected inputs, including optional
997-bot data and metadata, before creating output. Missing/mixed identities fail
closed. Exports live under
`deployment/brain/evidence/2026-11-05/party-technical-acceptance/<run_id>/`, so a
new three-bot-only report cannot retain an older round's 997-bot archive.

The historical artifacts published by this PR predate the identity protocol.
They remain unchanged and were checked independently. The new reporter refuses
to ingest them directly; it does not invent provenance or provide a legacy
bypass. The offline regression suite uses copies in temporary directories to
exercise coherent/mixed-round cases:

```sh
cd tests/fixture
python3 -m unittest -v test_party_run
```

`party_perf.py` rotates modes over three repetitions, defaulting to 60 seconds
each; the retained acceptance evidence uses `--seconds 30`. `party_combat_perf.py`
uses the same rotation with 30-second native
combat windows and four full-health wolves per wave. Initial placement and
between-window XP, potion and health/mana resets are setup interventions, never
survival progress. Surviving fixture monsters are removed after measurement and
are counted separately from defeats.
No fixture teleport, heal or artificial monster damage is injected during a
measured combat window. All avatars start at level 20 with generous 500 HP/mana;
the setup deliberately does not represent survival with normal starting gear.

`party_scenarios.py` collects a bounded guided hunt, real NPC resupply/return for
each companion, authority transfer, stale-leader order, worker loss/restart and
both normal leaders disconnecting. A deliberately interrupted 15-minute hunt is
reported as a bounded window, not a completed hunt. The secondary hold goals in
the SIGKILL worker-loss case merely keep goals alive beyond the heartbeat deadline; the
previous PM/hold demonstration is not this fixture's principal delivery.

The global NPC name lookup can select a duplicate on another floor. Resupply
starts at the declared Thais rendezvous and lets the production shop selector and
route find the local vendor. QA commands preserve UTF-8; JSON `\u` escapes are not
valid Lua 5.1 source. `--resume-after-hunt` retains an already-recorded successful
hunt while retrying the later scenarios after a fixture repair.

Archive and validate the three-bot results before `party_population.py`. It imports
the remaining 994 public seed rows into the private database, restarts only this
QA game, re-forms the party and activates/hibernates background bots in batches.
The larger cohort records registered/active/awake/hibernated counts before and
after each window; it does not claim 997 simultaneous awake combatants.

`party_metadata.py` captures matching Lua/CSV counts, artifact/map hashes, pinned
scenario data identities and the fake ledgers. Its data identities are pinned to
the tested base revision. The original raw field `setup_teleports` describes a
maximum of five setup placements, because already-positioned avatars skip the
teleport call. New runs use the explicit `setup_teleport_upper_bound` name.
Native automatic rescue teleports are not exhaustively classified by this fixture.

Raw JSON is written under `/tmp/canary-party-qa`. The variety script records
synthetic policy selections; it does not create completed hunts in the server.
Results and their remaining acceptance limits belong in the linked evidence
report and issues #1/#14. Never infer safe AFK operation or human usefulness from
this fixture.
