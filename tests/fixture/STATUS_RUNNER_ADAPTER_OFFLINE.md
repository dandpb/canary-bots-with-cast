# Opt-in native status transport (offline review)

`m5_current_qualification.py` keeps its original observer and `hunt_cycle`
qualifier unless `--status-capture-opt-in` is supplied. The opt-in branch writes
`status-capture-events.jsonl` separately; it does not feed those events into the
historical `phase-status.jsonl`. An unsealed opt-in capture rejects the run;
it does not relax any historical qualification check. No runtime or 1800-second
qualification has been exercised for this adapter.

The runner binds each diagnostic attempt to the frozen run ID, world SHA256,
Docker game container ID and StartedAt, fixture bot GUID/name, and a script ID
declared in the frozen fixture. The SQL transport submits `status` and requires
a single positive `LAST_INSERT_ID()`. Fetch uses exactly `WHERE id=<that ID> AND
processed=1`. Every dispatch and accepted reply rechecks the game identity and
world hash. The externally bound values do not prove a native hunt instance or
an internal epoch; the arbiter records `internal_epoch=not_demonstrated` and a
null `hunt_instance_id`.

The game container's timestamped Docker log stream supplies phase hints. The
same bounded arbiter accepts those hints and periodic requests; a hint triggers
a real command and never becomes a status observation itself. Unexpected log
EOF, oversized line, command/identity error, queue overflow, periodic deadline
miss, sink failure, cancellation or timeout make the attempt fail closed. The
JSONL sink is created exclusively with mode 0600 and fsyncs every event. On
timeout/shutdown, the SQL operation can continue; its command ID stays linked
to that attempt, and a late reply cannot be used by another request.
The event file is sealed with a separate fsynced digest only when no command
remains outstanding. An unresolved command leaves the file unsealed and the
result carries no event hash. A cleanup failure is recorded and rejects the
attempt even if the worker stopped at the same time.

The adapter's queue limit 4, age 35 s, command timeout 30 s and the runner's
540 s/10 s periodic cadence are prospective. This patch has not measured
latency, log loss, CPU overhead or the SQL transport against a native game.
Before any long run, review the trace source's behavior, resource cleanup when
SQL remains pending, and admission values. The passive phase trace remains
diagnostic and is not a replacement for the existing same-hunt gate.
