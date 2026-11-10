# Native status capture arbiter (offline component)

`m5_status_capture.py` is an opt-in component. It is not wired to the 1800-second
qualification runner and does not change the `hunt_cycle` gate. The caller must
provide a real `submit(bot_name) -> command_id` transport, a
`fetch(command_id) -> processed status` transport, and a durable event sink.
This change does not execute SQL or claim game↔worker compatibility.

Periodic requests and matching `[HUNT:PHASE]` hints enter one FIFO queue.
`capture_next()` serializes all callers and dispatches one command total at a
time. Queue overflow, expiry, command failure, evidence failure, cancellation,
epoch change, and timeout halt the attempt. The queue bound (4), queue age (2 s)
and command timeout (3 s) are provisional admission values, not measured game
latencies. A caller must test them before a long run and reject any loss; it
must not extend the phase or silently drop samples to obtain a pass.

A timeout does **not** cancel the underlying submit/fetch task. The pending
command ID, if known, is recorded. A late reply remains attached to the same
request and external epoch, is marked unaccepted, and never reopens dispatch.
If the insert times out before returning an ID, the identity is recorded as
unknown until the task resolves; that state also halts dispatch. Shutdown and
task cancellation, including cancellation while waiting for the arbiter,
record the pending identity without assuming SQL stopped. A cancelled waiter
fences the entire attempt; the active command's eventual reply is late and
unaccepted, and no queued request can dispatch.

The caller supplies run, world hash, container ID, StartedAt, bot GUID/name,
and script ID as external bindings. These do not prove a native hunt instance
or absence of reload; every output says `internal_epoch=not_demonstrated` and
has no `hunt_instance_id`. A hint is only a request trigger. Its phase is never
copied into a status observation; only a reply from the matching command ID
can provide a status phase. A trace logger can omit transitions, so even an
apparently contiguous sequence is diagnostic only. This component cannot by
itself prove the existing same-hunt acceptance contract.

The separate runner adapter must provide a durable sink and establish how it
receives trace events, authenticates the external bindings, and handles source
loss before it is eligible for a frozen 1800-second run. A dispatcher fallback
for phases shorter than status latency remains a separate design decision.
