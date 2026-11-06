# Canonical runner startup and explicit fake qualification

An isolated 10-second real-game smoke ended before the first observation:
TCP health preceded map/bot loading, while the campaign watchdog stopped after
`min(15, seconds/2)` seconds. The worker already allowed 240 seconds for startup.
The campaign now uses that startup grace and starts the scored horizon from
the existing first-observation clock. Premature completion still fails.

The same canonical runner can now declare `kind: fake`, using the existing
runtime's local FakeProvider. Its manifest records provider=fake rather than
pretending native control. This supports free fixture qualification without
a separate timing/supervision implementation. It does not qualify provider
skill or permit an implicit paid fallback.

Source-equivalent changes were first exercised at
`c9e447c500d1c245e7ea3736934eacfda0b5d445` in an isolated worktree:

- Eight directed virtual-clock cases: native/fake, first observation 2/20 s,
  normal/premature completion. Independent benchmark/horizon/worker check:
  37 tests passed, without game/provider execution by the reviewer.
- Real native 10 s smoke: 11.145 seconds observed; fake 10 s: 10.286 seconds;
  canonical supervision, no gaps/inference, final saved XP consistent.
- Real native 1800 s: 1800.493 seconds sampled, +8349 XP, no deaths/gaps/inference,
  saved XP matches, owned containers/networks cleaned.
- Real fake 1800 s attempt remains **failed**: supervisor stopped stalled after
  1508.244 seconds sampled, +1993 XP, no deaths/gaps/inference. Its route/recovery
  failure remains under diagnosis. This bug fix does not accept PR25/M5.

Combined local integration of main after #39, these changes and reviewed wrapper #38
passed 344 Python tests in 124.84 seconds, using temporary test data in shared
memory. That validation does not turn the failed real-game qualification green.
No production runtime, existing character, provider key or canonical ledger was
changed by these runner changes. The initial guide now documents fake as an
explicit free participant, while retaining the fixture and paid admission gates.
