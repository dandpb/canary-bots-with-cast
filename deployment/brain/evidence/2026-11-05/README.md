# Disposable replay/benchmark acceptance — 2026-11-05

These are development measurements on x86_64 WSL/Docker, with an internal private
network and separate MariaDB data. No production deployment or paid inference was
performed. Native game observations are real; `fake` responses are explicitly
simulated. The measurements do not establish a winning model or human usefulness.

## Independent native baseline

The actual Compose runner completed four independent trials: two native labels,
two repetitions, order A0/B0/B1/A1, 30-second requested windows. Each trial started
its own game/database/worker from the same fixture and destroyed its stack. All
four initial hashes were
`7c512b093ef63870410326d38fd64ec152e2001d37d0ad9e288c4fa9c916d73b`.
The runtime image was pinned to
`sha256:1a5876fe13c2b6da2d1b8d2d3e6de984970eabb509418134182c21ed99baf0b0`;
game source was `3748d691e6740ae119de9f4be649d92b6f57a0c7`, worker/runner
source `0da3501a0cd93ad83dd547c0b3ed69e7600902a5`.

[Machine-readable summaries](native-baseline-summary.json) retain the full manifest,
status, sampled timing and metric availability for every trial. All completed,
with zero XP gain, observed deaths, interventions, model calls or AI cost in these
short fixtures. The verdict is `descriptive_only`; two labels running the same
native controller are a runner/attribution check, not an AI comparison. Recording
duration also includes lifecycle boundaries outside the observed active window.

The first real runner attempt exposed MariaDB UID 999 being unable to read the
fixture mount. Its failure remains recorded. The fix makes only the readonly
initdb subtree traversable/readable; its private parent remains mode 0700.
Teardown retains redacted service logs before removal, even after a startup error.
An actual orchestrator was subsequently SIGKILLed after game events arrived.
Restart cleaned its deterministic Compose resources and retained that attempt as
`interrupted`; it did not silently replace it with a successful retry.

## Recorder/viewer cost

Each row used a separate 40-second worker lifetime, with CPU measured during a
30-second window after five seconds of warmup. Native bots were paused at a safe
temple; one or three bots were observed, with other bots hibernated in the one-bot
case. Provider was fake and memory frozen. Tick p95 covers the latest 256 bridge
ticks, not the whole dispatcher or combat latency. A development C++ build ran
concurrently during part of the sequence, so these are bounded smoke measurements,
not statistically controlled speed comparisons.

| Observed bots | Recording | Replay HTTP reads | Worker CPU-seconds / 30 s | Max sampled RSS MiB | Bridge p95 µs | Final recording KiB / events |
|---|---|---|---:|---:|---:|---:|
| 1 | off | none | 0.28 | 67.63 | 194.557 | — |
| 1 | on | none | 0.34 | 67.93 | 156.769 | 76 / 81 |
| 3 | off | none | 0.69 | 68.02 | 356.049 | — |
| 3 | on | none | 0.79 | 68.36 | 290.846 | 160 / 235 |
| 3 | on | 145 requests / 30 s | 1.19 | 68.93 | 332.036 | 168 / 241 |

The viewer alternated list, seek, track and summary GET requests against the real
local OperatorServer, with zero HTTP errors. Real cast spectators stayed zero,
runtime identities stayed unchanged, and no bot was awakened by replay reads.
The three recorded fixtures contained zero gap events. This is not a queue peak
measurement or a disk-full claim; separate automated fault tests cover overflow,
write errors, retention and recovery. Final SQLite size is not a linear storage
rate because it includes schema/pages and excludes transient WAL reuse.
See [raw condensed measurements](recording-overhead.json).

## Native party and video

An ordinary native Player fixture invited all three bots through the real invitation
path. All three sessions recognized human GUID 64999. A Portuguese PM hold order
went through native observation, fake provider, validator and native adapter; its
episode completed as `hold_finished` after 30.004 seconds, party size four, progress
one, XP delta zero and deaths zero. Subsequent test-client ping timeout removed
party authority from all three sessions. It does not replace a human hunt/resupply,
leadership-transfer or usefulness/survival playtest.

M6 exported the actual sampled party recording to an offline MP4: 213 frames,
24 fps, 8.875 seconds, 1280×720, from an 88.365-second source interval. ffprobe and
rendered-frame inspection verified the artifact. It is a coordinate replay with
simulated inference, not captured OTClient footage or a real-model benchmark.
Its SHA-256 was
`817d6bc77470b6c7a4981ecf8f8e445368f3cc222e3a274099f0db8bb2f2d53a`.
The synthetic demo separately verified 480 frames / 20 seconds at 24 fps.

## Automated checks and remaining gates

The full Python suite passed 86 tests; Ruff passed; strict mypy passed 18 modules.
Before the later immutable-checkpoint revision, the complete integrated native
build passed 30 selected native tests, four loader/reload CTests and 16 startup
Lua tests. Lifecycle acceptance and subsequent concurrency validation are tracked
in `tests/lua/LIFECYCLE_ACCEPTANCE.md` rather than attributed to these earlier runs.

M1–M4 and M6 have implementation and offline/disposable evidence in PRs #15/#21.
M5 still needs explicit real providers/models, scenario, duration, repetitions,
criteria, caps and paid opt-in under the shared USD 50 monthly ledger. No production
provider was changed. Human acceptance for #1 remains a separate gate. All PRs
remain reviewable drafts; these measurements do not authorize merge or deployment.
