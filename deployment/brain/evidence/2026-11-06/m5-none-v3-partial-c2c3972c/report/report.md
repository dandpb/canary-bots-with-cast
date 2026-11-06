# M5 evidence report: m5-none-v3-20261106-c2c3972c

Ready for review: False. Verdict: descriptive pilot, no winner.
Financial totals complete: True; if false, displayed values are only known valid amounts, not a complete cost/passive total.
Financial final: False. Confirmed usage-priced spend: USD 0.001981700; unknown liability retained: USD 0.005245675. Unknown liability is not confirmed spend or a zero-cost attempt.

| Run | Status/reason | Observed seconds | XP | Deaths | Interventions | Settled USD | Unknown USD |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| m5-none-v3-20261106-c2c3972c:native:0 | failed/recording_gap | 220.803 | 0 | 0 | 0 | 0.000000000 | 0.000000000 |

## Findings

- recording_incomplete (m5-none-v3-20261106-c2c3972c:native:0): Critical gaps/incomplete recording cannot pass qualification
- stop_status_mismatch (m5-none-v3-20261106-c2c3972c:native:0): Unexpected/missing stop classification; retain interrupted/infrastructure attempts
- stop_evidence_mismatch (m5-none-v3-20261106-c2c3972c:native:0): Need exactly one matching durable supervisor stop
- character_evidence_missing (m5-none-v3-20261106-c2c3972c:native:0): Need restored initial and final saved character evidence plus samples
- missing_attempt_evidence (m5-none-v3-20261106-c2c3972c:openai:0): Every predeclared attempt needs a recording and trial record
- missing_attempt_evidence (m5-none-v3-20261106-c2c3972c:gemini:0): Every predeclared attempt needs a recording and trial record
- missing_attempt_evidence (m5-none-v3-20261106-c2c3972c:native:1): Every predeclared attempt needs a recording and trial record
- missing_attempt_evidence (m5-none-v3-20261106-c2c3972c:openai:1): Every predeclared attempt needs a recording and trial record
- missing_attempt_evidence (m5-none-v3-20261106-c2c3972c:gemini:1): Every predeclared attempt needs a recording and trial record
- missing_attempt_evidence (m5-none-v3-20261106-c2c3972c:native:2): Every predeclared attempt needs a recording and trial record
- missing_attempt_evidence (m5-none-v3-20261106-c2c3972c:openai:2): Every predeclared attempt needs a recording and trial record
- missing_attempt_evidence (m5-none-v3-20261106-c2c3972c:gemini:2): Every predeclared attempt needs a recording and trial record

## Interpretation

- The independent run is the sample unit; repeated frames are not extra samples.
- Completed-response latency is deadline-censored; inspect failures by deadline.
- Generic RuntimeError fallback is not an exact backoff count; instrumented ProviderBackoff is reported separately. TTL attribution requires additional identity.
- Usage-priced costs are not provider invoice reconciliation.
- This checker does not establish fixture hunt/resupply acceptance or human/AFK safety.

Per-request usage, TTL/deadline slices, classified timeouts and distributions are in report.json.
