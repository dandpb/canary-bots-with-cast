# #72 supervised native admission and completion

Integration base: `3431b4046602875b161216ddb7be464eb4842f1a` (includes #82 and
#84). Draft #83 head `ba3e00a8c518f74171e0e98f66b9d275b3accc18` was rebased
first as `dde8b9f3`; its recorder/runtime/replay diff against this main was empty.
The standalone boundary's B/t0/D0/O0, immutable retry reply and bounded #75 FIFO
remain intact. Nothing under tests/fixture or historical evidence was changed.

## Admission

Supervised Configuration requires a 40-character native source commit pin,
explicitly or from its manifest; pins must agree. Campaign configuration supplies
the experiment source revision. Default worker manifests also carry the pin.
A clean native build must report that exact commit. The build metadata identifies
source state; it does not replace external binary/image attestation.

The private AF_UNIX callback accepts the configured server pathname and pins its
socket device/inode/owner. Rebinding it or a socket error invalidates the attempt.
World and bot identities remain fixed. The supervised gate serializes callbacks,
requires lifecycle_telemetry/telemetry_delivery/telemetry_admission/telemetry_fence
and keep_awake, and retries one admission nonce. No observation, model task,
reflection, reconciliation intent or run clock can open through this gate early.

The native dispatcher captures O0/t0/D0 once, allocates B once, and enqueues the
run_nonce-tagged boundary through the existing FIFO. The worker validates the
reply, writes admission and O0 into the recorder, flushes within a bound and
checks the committed admission, then persists the full private admission in its
state database. Recorder coverage is seeded at B-1, never first receipt. B itself
must arrive and validate before O0 is released to the controller. Traffic while
the reply/B are delayed is buffered within a fixed limit. Retry cannot replace
the cut, and an already admitted/restarted recording cannot silently resume.

## Native window and terminal proof

The completion horizon is max(run_seconds, 1800) measured as native captured_ms
after t0. Receipt time remains the watchdog clock. The first actual observation
at or beyond that horizon is frozen synchronously before another controller task
can launch. Samples/levels/outcomes after it remain diagnostic. Deaths use D0;
delayed deaths captured within the window still count, while later deaths do not
inflate the scored window. Ordinary death retains the session and FIFO; native
unavailability, removal, hibernation, reload or peer loss fails the attempt.

At cutoff, model/reflection and intent admission close permanently. Existing model
tasks are cancelled and given a bounded 0.5-second wait; unconfirmed shutdown is
failure, with existing request-accounting/cancellation behavior retained.

The gate sends telemetry_fence with a fresh terminal nonce and the admission
nonce. Only a correlated native reply can certify the tail; a periodic/cached
status cannot. Native checks the session and bot availability, flushes within the
same FIFO attempt budget, and returns allocated/accepted/pending/loss counters.
Removal emits unavailable through the FIFO and also faults the fence. Retries
may return newer counters; the worker freezes the first complete eligible fence.
The drain deadline is three seconds from the first horizon observation, including
model cancellation. Every telemetry frame from B through that watermark must
validate contiguously, with no faults. Schema, identity and producer faults remain
sticky even before the horizon, and conflicting retransmissions fail.

After bounded recorder close (#82), final validation checks committed admission,
O0, exact horizon sample, correlated fence and every native key AND payload in
[B, terminal]. A missing frame cannot be replaced by a high in-memory watermark.
The state and replay carry native_finalizing until this succeeds. Only then is a
completed stop appended and published in worker state. A crash before final
validation therefore has no completed receipt. Operator/budget stops, recording
failures and world changes retain precedence over completion. Late traffic is
still validated; it cannot reopen model admission or move the scoring cutoff.

Bounds: 32 callback tasks, 256 buffered pre-admission/pre-B packets, 8192 telemetry
frames and 8192 observation fingerprints; overflow is explicit failure. Startup
retains the 240-second watchdog, even for a reply whose B never arrives. Admission
recorder work has a 1.5-second await bound; final committed proof has a one-second
await bound. Python cannot terminate a thread blocked inside filesystem/kernel
I/O: timeout rejects qualification, while resource release may require process
exit, as with #82's recorder writer limitation.

## Remaining qualification gates — #72 stays open

- Full server/engine compilation and loader/reload integration. Local offline
  configuration is blocked by missing CURLConfig.cmake; focused native admission,
  FIFO and fence tests compile and pass independently.
- Real game pressure, death/removal/rebind/reload and process-crash tests against
  the built, clean, externally attested native artifact. Current worker tests use
  real local sockets but synthetic native capture values and peers.
- Harness/source/image attestation and the free isolated native 30-minute run,
  with replay/XP/deaths/gaps, resource and final-save checks. No synthetic time
  jump or unit-test pass substitutes for this run.
- Independent integration review before readiness/merge. Neither #72 closure nor
  deployment, provider access, spending or reuse of historical claims is implied.

See [validation notes](native-admission-validation.md) for RED/GREEN receipts and
known environmental test constraints. No live services or canonical ledgers were
accessed during this stage.
