# Party technical acceptance — #1

Native base: `33c6a57878e58ef1241d287d26bd5aa489b5cc50`. Work used the isolated
`qa/1-party-technical-acceptance` clone and `canary-party-qa` game/MariaDB/internal
network/named volume. No host ports, production writes or paid calls. All three QA
containers were stopped with exit code zero; the volume and artifacts remain for
review. This report supplies technical observations for #1; human acceptance
remains open.

## Fixture and measurement

The three companions are Grizzle Alyronia (65001, knight), Sever Heartspear
(65003, paladin), and Galdon Whitehoof (65004, druid), with two ordinary account
Players used as simulated leaders. Level 20, 98,800 starting XP and generous
500 HP/mana are fixture resources. The native module calls ordinary login,
invitation, leadership and connection-close paths; it bypasses authentication and
supplies pong/idle scaffolding. Simulated leaders follow through the native
Creature adapter. These are not human-operated clients.

The runtime matched all **531 source Lua scripts and 291 authored CSVs**, with
one extra private QA command adapter. Xodet, Wolf, item definitions and vocations
matched the main Git blobs after CRLF normalization. Executable/library hashes
and runtime image identity are in [environment](party-environment.json) and the
source comparison files. The private build adds a steady-clock scope around the
whole native tick and its `tickBrain()` call. Repository product sources and ABI
are unchanged. Samples are bounded and drained outside the measured tick; the
disabled return path is timed as well.

These are execution-wall scopes. Waiting in the dispatcher between scheduled
ticks and real provider inference latency are separate measurements.

There are **27 measured windows and 8,556 raw ticks**: three repetitions of
disabled/shadow/active fake for follow, combat with three registered bots, and
combat with 997 registered/active bots. The larger population had **7–8 awake
and 989–990 hibernated**, rather than 997 simultaneously rendered combatants.
The 994 background characters come from the repository's public seed, imported
only into the private database. Native background activity continued; its state
and world RNG were not reset between modes. The mode order rotates each round.

Each final window lasts approximately 30 seconds. Combat introduces three waves
of four ordinary full-health wolves. XP, basic potions, health/mana and placement
are reset before each combat window; surviving fixture wolves are removed after
measurement and recorded separately. The fixture performs no heal, teleport or
artificial monster damage during a measured combat window. Normal native healing
and combat remain active. These resets make the windows independent technical
probes; this dataset does not represent one continuous bot life.

Intervention accounting covers fixture commands. The retained raw
`setup_teleports: 5` field is an upper bound for five avatar placements; an avatar
already on its target skips that teleport. The reusable harness now labels that
field `setup_teleport_upper_bound`. Native automatic rescue teleports and
background-character mortality were not exhaustively classified.

Percentiles use nearest rank. The table gives the range of the three per-window
p95 values; [summary.json](summary.json) also includes pooled p95/p99, maxima,
threshold crossings, CPU and observed queues. CPU is approximate cgroup usage
for game, worker and probes, expressed as percent of one logical core; MariaDB
runs in its own cgroup. This is an x86-64 WSL host with 16 logical CPUs shared
with existing services. The final timed cohorts ran without auxiliary builds or
test suites alongside them.

## Performance

| Population / scenario | Mode | Native ticks | Bridge p95 range, ms | Whole tick p95 range, ms | CPU range, % of one core |
|---|---|---:|---:|---:|---:|
| 3 / follow | disabled | 967 | 0.001–0.001 | 0.203–0.216 | 3.297–3.518 |
| 3 / follow | shadow | 988 | 0.352–0.371 | 0.510–0.540 | 6.165–6.457 |
| 3 / follow | active fake | 994 | 0.359–0.390 | 0.548–0.559 | 6.382–6.566 |
| 3 / combat | disabled | 942 | 0.001–0.001 | 0.384–0.485 | 7.547–8.445 |
| 3 / combat | shadow | 933 | 0.407–0.426 | 0.695–0.797 | 10.054–10.252 |
| 3 / combat | active fake | 931 | 0.389–0.477 | 0.724–0.812 | 9.848–11.181 |
| 997 / combat | disabled | 936 | 0.001–0.001 | 1.070–5.723 | 11.002–12.333 |
| 997 / combat | shadow | 931 | 0.414–0.449 | 1.466–6.189 | 12.917–16.956 |
| 997 / combat | active fake | 934 | 0.431–0.446 | 1.473–5.785 | 13.038–15.527 |

All enabled-bridge window p95 values met the initial **2 ms bridge target**.
In the 997 cohort the largest measured active bridge call was 0.773 ms and none
exceeded 2 ms; the active whole-tick maximum was 10.721 ms. Whole-tick cost grows
with native background work and must be assessed separately. The historical
2.999781 ms bridge sample in `EVALUATION.md` used an amd64 game on an ARM64 host;
the load state, scenario and timing window also differ. These observations do
not establish a causal performance improvement over that historical sample.

The maximum observed companion walk queue was three entries in the three-bot
combat cohort and two in the larger cohort. Worker arbiter tasks peaked at one
in flight. The functional worker's durable pending table was empty after crash,
restart and disconnect. Kernel datagram backlog and every dispatcher/SQL queue
were not instrumented, so these are scoped queue observations. Three repetitions
give a descriptive comparison, without a confidence claim about production tails.

## Native scenarios

The bounded guided hunt selected authored script **399**, recorded **37 distinct
guide positions**, dealt damage through all three companions and confirmed
**16 ordinary wolf deaths**. Native XP deltas were **246 / 150 / 243** for
65001 / 65003 / 65004. Both simulated leaders followed the guide. The fixture
ended this approximately two-minute window by an ordinary retreat order; it
records **zero completed 15-minute hunts**.

All three companions subsequently walked from the Thais rendezvous to an ordinary
potion vendor, bought stock and returned to the leader:

| Companion | Stock before → after | Funds spent | Native elapsed | Terminal outcome |
|---|---:|---:|---:|---|
| Grizzle / 65001 | 2 → 40 | 2,014 gp | 75.282 s | supplies_bought_and_party_rejoined |
| Sever / 65003 | 2 → 40 | 2,014 gp | 65.329 s | supplies_bought_and_party_rejoined |
| Galdon / 65004 | 2 → 40 | 2,014 gp | 55.707 s | supplies_bought_and_party_rejoined |

The transfer moved all companion authorities from 64999 to 64998 and cancelled
the old goals with `authority_changed`. A subsequent hunt order from the former
leader did not start a hunt. These goals used follow; the previous PM/hold
demonstration is not the principal acceptance case.

For worker loss, one hunt and two secondary long-lived hold goals were active
before **SIGKILL**. All three goals were released. The observer bracketed fallback
between **3.794 and 6.268 seconds** after the stop request; its approximately
two-second cadence does not provide an exact five-second-deadline measurement.
An ordinary wolf was confirmed defeated after the worker stopped, through native
combat. Restarting the same state recovered the cancelled outcomes and left no
resurrected goals or durable pending entries.

Closing leader B's real loopback transport transferred authority to A. Closing
A's transport left all companion leaders at zero and no retained human party.
No deaths of the five fixture avatars were observed across the recorded cases.
The 18 timed combat windows confirmed **101/108** wolves in the three-bot cohort
and **102/108** in the 997 cohort; the remaining wolves were recorded as post-window
removals, without counting them as defeats.

## Variety, cost and remaining human work

The existing policy ran **20 seeds × three identities × 100 selections = 6,000**
synthetic selections among five equivalent eligible hunts. Every case visited all
five, with at most three consecutive equal selections. These are synthetic policy
updates, not 6,000 live completed hunts; the live bounded guide used one hunt.

[Financial and pending checks](financial-and-pending.json) found **zero requests,
zero reserved nanodollars and zero settled nanodollars** in all 35 private fake
state files. The functional run retained nine episode records and zero durable
pending entries. No gateway/provider credentials were supplied.

Human usefulness, ambiguous natural requests, a complete multi-floor party hunt,
long-run mortality, the original three-session human rubric and learned-selection
promotion remain open. Generous fixture health, scripted following and a fake
provider cannot establish safe AFK operation or improved real-model decisions.
The paid #10/M5 pilot still needs its models, scenario and budget defined and
authorized separately.

## Reproduction and retained evidence

See [fixture instructions](../../../../../tests/fixture/PARTY_ACCEPTANCE.md).
The commands actually used for the final cohorts were:

```sh
# Isolated /review checkout, /source build cache, /build output, /out QA artifacts:
python3 /review/tests/fixture/party_build.py
python3 tests/fixture/party_qa.py create
python3 tests/fixture/party_qa.py setup
python3 tests/fixture/party_metadata.py
python3 tests/fixture/party_perf.py --seconds 30
python3 tests/fixture/party_combat_perf.py
python3 tests/fixture/party_scenarios.py
python3 tests/fixture/party_scenarios.py --resume-after-hunt
PYTHONPATH=deployment/brain/src python3 tests/fixture/party_policy.py
python3 tests/fixture/party_metadata.py
python3 tests/fixture/party_report.py
python3 tests/fixture/party_population.py
python3 tests/fixture/party_combat_perf.py --population 997 --output party-population-perf-raw.json
python3 tests/fixture/party_metadata.py
python3 tests/fixture/party_qa.py stop
python3 tests/fixture/party_report.py
```

The initial calibration image had four older Lua files; those data were excluded
and both timing cohorts were repeated after matching main. Before resupply, the
fixture's global NPC-name lookup selected an underground duplicate Xodet; the
fixture now starts at the declared Thais rendezvous and lets the production shop
adapter select its vendor. Lua command serialization was also corrected to carry
UTF-8 rather than unsupported JSON `\u` escapes. The completed hunt evidence was
retained and subsequent scenarios resumed; these repairs change QA scaffolding.

Build validation: **155/155 native unit tests** from `/source`; **21/21 targeted
Python tests** for controller/protocol/learning/recovery/provider faults/frozen
policy. Raw tick arrays, native observations, kills, damage sources, setup resets,
outcomes and policy choices are retained in the `*.json.gz` files. Decode with
Python's `gzip.open(path, 'rt')`; no game map, private database or compiled binary
is committed. [teardown.json](teardown.json) records stopped QA containers and exit
codes. The original checkout and its work were preserved; no deployment occurred.

The metadata capture is implemented in `party_metadata.py` and was exercised
against the private stack. The command adapter also passed UTF-8 round trip,
malformed-Lua failure reporting and subsequent-command recovery; see
[fixture-command-regression.json](fixture-command-regression.json). Ruff checks
and formatting passed for ten Python fixture files. Clang-format 18.1.8 passed;
recompiling the formatted native adapter produced the exact binary hash exercised
by the game, recorded in [format-and-compile.json](format-and-compile.json).
