# M5 free qualification — 2026-11-05

Two controlled real-game windows completed within the declared ±5-second
recording tolerance, with positive persisted XP and no recorded death, gap or
inference request. A separate low-stock run proved an actual NPC purchase and
explicit return to the temple. **This is not paid-pilot admission**: independent
review, historical database identity, model protocol/account access and spending
gates remain below.

## Results and retained attempts

| Attempt | Recorded seconds | Supervisor seconds | XP gained | Result |
|---|---:|---:|---:|---|
| B / native | 1,636.838 | 1,637.274 | 2,316 | Failed: real 600 s stagnation stop after native cooldown |
| D / native | 1,800.586 | 1,800.931 | 7,647 | Six timed evidence checks passed |
| D / fake | 1,799.963 | 1,800.324 | 4,365 | Six timed evidence checks passed under the declared tolerance |
| E / fake, low stock | 300.190 | 300.288 | 617 | Failed supply goal: purchase occurred, explicit return was not requested |
| F / fake, low stock | 54.993 | 55.811 | 0 | Eight purchase/return evidence checks passed |
| Canonical runner / native smoke C | 10.349 | See supervised-stop.json | Not a progression test | Real revised runner completed its 10 s horizon |

All five archived gameplay attempts had **0 observed deaths, 0 recorded gaps and
0 inference ledger requests**. Native D saved XP `106447`; fake D saved XP
`103165`, both from `98800`, matching their final recorded samples. The fake is
a declared scripted policy, not an AI model, and these one-off nondeterministic
world runs do not establish a provider ranking or statistical performance claim.

The [machine-readable index](index.json) links each attempt's `analysis.json`,
manifest, source-blob verification, hashes, audit/status/supervisor logs and
`run.replay.zip`. Archives retain both failed and successful attempts. No database
environment, provider credential, world map, native executable or database volume
is published. Initial invalid calibration A is documented in
[the harness guide](../../../../../tests/fixture/M5_QUALIFICATION.md): startup
funding and a mismatched status healthcheck invalidated it before qualification.
Unused derivative C was prepared but never executed and is not a result.

## Frozen identity and controls

Long-window driver revision:
`c03a32257a66d7bf9fb5e779b22dd7c498b0d6c4`. Its three driver blobs are verified
against Git and their manifest hashes by `m5_archive.py`, even after later driver
changes. Shared SQL/authored/map fixture SHA256:
`42467745d544801e44e32deecf99f5f6d1e1aa869e2bf227734daf95ae42e5be`.
Both D participants used game image ID
`sha256:885acba76a8cb98d1dfe5d098a98f009194739a2844cdb7cf7d5a34d4d9a5bc3`.
World SHA256 is
`a80de1dda6a9aca3956a9d5b7fb2e0caebb451570d26853fc21beb40d5f31da2`
(`184776037` bytes). The per-attempt manifest records individual authored files,
level-20 equipment, GUID65001, HP365, mana95, skills50, initial bank10000 and
20 health + 20 mana potions.

Only authored hunts77/399 are enabled; hunt77's vocation mask is adapted for the
knight. Hunt weight100, other ambient weights0, hunt clock600s, short dwell,
no ambient roam and re-hunt chance100% are equal across D participants. This
reduces idle-only windows and enables bounded hunt-cycle inspection. It is a
controlled benchmark fixture, not an unrestricted-world playtest. Market/funding
scripts are disabled only in the derived QA image. Natural world monsters and
combat are unchanged; no timed-run teleports, heals, monster injection or human
gameplay rescue occurred. The passive observer issues read-only status commands
every10s after540 observed seconds. These inspection operations are preserved.

The image ID is the historical build authority. A separate read-only
`docker run --rm --network none --entrypoint sha256sum IMAGE ...` verified inside
the pinned D image that `/canary/canary` and `/canary/libbot_engine.so` match the
manifest hashes `c2a0ababa5f69d074703c60b488ed88d852f3f3c437a756364ddb804c223c150`
and `9088c8142cab7b554c30f4f0c2dad971f773b9fd8609d997fee9efe64909bdb4`.
Those artifacts reuse the #22 native base `33c6a578` with private timing
instrumentation; no bot-core source difference through preparation main
`a2bbf1c0` was found. This is not a newly deployed production build.

**Database identity limit:** long D Compose files used `mariadb:11.4`. Fake D's
running database was inspected before teardown and had image ID
`sha256:a794d9eb009e20de605858a11f32f63b4075cbd197c650436f0e3b457e4caed7`.
Native D's actual database image was not captured before removal; its digest is
left null in the attestation. The current tag is not retrospective proof. E/F
and the canonical runner smoke pin that content ID before startup. Any subsequent
scored paired campaign must pin and attest the database for every participant.
This limitation prevents treating historical D as a fully attested scored pair.

Current preparation was exercised again in fresh directory G, before any run.
Its [manifest](preparation-only-g/manifest.json) freezes the database and verifies
both native binary hashes inside its own pinned game image. SQL/authored/map
identity remains the same, while the newly built image has its own ID
`sha256:a0cebf352f4750e7d20a13df82beaca79fa21025b8a335b5bc8b4fc39c2aa96c`.
G is preparation validation only, with no gameplay result or pooled D evidence.

## Hunt and supply cycle evidence

Native D's passive status trace shows hunt77 PATROLLING → LEAVING at610.269s →
RESUPPLYING at710.522s → a second preparation/travel/patrol, then LEAVING at
1341.332s → RESUPPLYING at1441.477s → preparation/travel/patrol of hunt399.
Its bank and potions stayed10000/40: those phase names do **not** prove a purchase.
Fake D recorded terminal `hunt_progress` macro objectives; these five-minute
native contracts are distinct from completing an entire authored patrol lap.

The separate supply fixture SHA256 is
`1d6e3ca67ee5dd36ff8566395a35701255c2622ee2d9f244ce63fb84634a9b6d`.
It changes only the two potion stacks from20 to1 each. F's frozen driver is
`6818b1e46f8f5db0082903fd0d63276de42a0711`; the manifest identifies the parent.
The fake chooses an eligible `resupply`, waits for authoritative `supplies_bought`
with `supply_delta=38`, then chooses an eligible `retreat`. Native outcome
`party_rejoined` confirms completion of that solo temple-return action. The
worker stops on that explicit combined goal, not on the timed-window horizon.
It uses no operator endpoint or injected movement order.

F persisted **2→40 potions**, **10000→7986 bank gp** and position
`(32371,32238,7)`, within three tiles of initial temple `(32369,32241,7)`.
Purchase, return, stop reason, stock, bank debit, saved position, no gaps and no
inference all pass programmatic checks. In solo mode, the resupply action itself
finishes at purchase; return is a second explicit decision. E preserved the
failed assumption that the party-specific combined outcome would appear solo.
F is a derivative proof of the adapter path, not a purchase inserted into D's
equivalent-start windows or a human party acceptance test.

## Supervisor and actual runner

The original B failure exercises the real ten-minute no-observed-progress stop.
Separate private datagram tests cover native/fake death limit, generation change,
observation loss, the real30s blocked-proposal window, a scaled stall interval,
and early runtime exit. Twelve policy methods, six real-worker test methods
(ten scenarios), and seven finalizer subcases passed. Finalization now treats
saved/closed infrastructure separately from qualification: every evidence check
must pass, otherwise metadata is failed and the command exits1. An early worker
return is explicitly `runtime_ended`. Later driver changes do not alter which
revision produced the archived long runs.

The canonical runner fixes are in [PR26](https://github.com/dandpb/canary-bots-with-cast/pull/26),
head `ea70dd40d36c5cd6aafd64075b5b99c7faee47ec`: **182 tests**, Ruff and strict
mypy passed. Shutdown races found by independent review received directed
regressions. It still requires independent re-review. Its stricter completion
rule requires actual observation coverage and recorded sample span ≥ the exact
horizon. Historical fake D is37ms short of1800s and passed its earlier ±5s
criterion; it is not evidence that the revised exact-horizon rule ran for30min.

The [runner smoke C](runner-smoke/m5run-20261105c/smoke-result.json) executes the
actual revised campaign/worker, game, MariaDB, recorder, classification and
teardown, using the same D game image and fixture. Only Compose preparation adds
the pinned DB, private internal network and the QA audit mount. It does not mock
worker observations or game outcomes. The native-only10s trial recorded10.349s,
completed without gaps and made0 inference requests. The exact smoke driver is
archived with its hash and exported replay. An initial launch refused WSL's
CRLF-only dirty report before starting a stack; the driver checks canonical Git
content with the matching checkout normalization. A first successful11.172s smoke
is retained locally; C is the published repeat with its exact driver preserved.

## Reproduction and remaining gates

Use a fresh output identity; no directory is recycled. External world/native
prerequisites and all fixture controls are explained in the harness guide.

```sh
export PYTHONPATH="$PWD/deployment/brain/src"
export CANARY_M5_QA=/tmp/m5q-UNUSED-ID
python tests/fixture/m5_qa.py prepare
python tests/fixture/m5_qa.py native
python tests/fixture/m5_qa.py fake
# Current driver automatically invokes the fail-closed finalizer after teardown.
python tests/fixture/m5_archive.py "$CANARY_M5_QA/native"
python tests/fixture/m5_archive.py "$CANARY_M5_QA/fake"

python tests/fixture/m5_lowstock.py "$CANARY_M5_QA" /tmp/m5q-UNUSED-SUPPLY
python tests/fixture/m5_freeze_supply.py /tmp/m5q-UNUSED-SUPPLY
CANARY_M5_QA=/tmp/m5q-UNUSED-SUPPLY python tests/fixture/m5_qa.py fake
python tests/fixture/m5_archive.py /tmp/m5q-UNUSED-SUPPLY/fake

python -m unittest discover -s tests/fixture -p 'test_m5_*.py'
# Canonical runner smoke: PYTHONPATH must point at the reviewed PR26 source.
PYTHONPATH=/path/to/clean-PR26-source/deployment/brain/src \
  python tests/fixture/m5_runner_smoke.py /path/to/clean-PR26-source \
  /tmp/m5q-DECLARED-FIXTURE /tmp/m5run-UNUSED-ID
```

No disposable QA containers remained after the runs. Only newly created QA
projects/volumes were controlled; production services were inspected read-only.
No production deploy, provider/account credential read or paid call occurred.
Temporary zero-inference ledgers are fixtures, not a new US$50 allowance.

Before any paid opt-in: independently review PR26 and this evidence, choose a
fully pinned scored fixture/campaign, resolve the Haiku native `strict:true`
wire gate documented in [PR27](https://github.com/dandpb/canary-bots-with-cast/pull/27),
then review real account access, sourced prices and the existing monthly ledger
under the separately authorized admission procedure. The reviewed US$7 proposal
and US$50 monthly ceiling remain unchanged. No human playtest or AFK safety
acceptance is established here.
