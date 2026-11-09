# M5 evidence report: m5-current-fake-d6226a4777

Ready for review: False. Verdict: descriptive pilot, no winner.
Financial totals complete: True; if false, displayed values are only known valid amounts, not a complete cost/passive total.

| Run | Status/reason | Observed seconds | XP | Deaths | Interventions | Settled USD | Unknown USD |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| m5-current-fake-d6226a4777:fake:0 | failed/stalled | 1508.244 | 1993 | 0 | 0 | 0.000000000 | 0.000000000 |

## Findings

- qualification_not_completed (m5-current-fake-d6226a4777:fake:0): Free qualification requires reason=completed

## Interpretation

- The independent run is the sample unit; repeated frames are not extra samples.
- Completed-response latency is deadline-censored; inspect failures by deadline.
- Generic RuntimeError fallback is not an exact backoff count; instrumented ProviderBackoff is reported separately. TTL attribution requires additional identity.
- Usage-priced costs are not provider invoice reconciliation.
- This checker does not establish fixture hunt/resupply acceptance or human/AFK safety.

Per-request usage, TTL/deadline slices, classified timeouts and distributions are in report.json.
