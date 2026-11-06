# Prospective M5 short-deadline policy

This is an optional admission contract, defined before inference. It does not
authorize paid execution or describe a completed model trial. The comparison is
between `configured_controller_stacks`; native decoder guarantees remain unequal.

## Admission and execution

Root must freeze `probe_outcome_policy:"short_deadline_performance_v1"` in the
admission document, together with the source and input hashes already required
by `m5_pilot.py`. Its authorization must declare the exact total ceiling of
6,980,214,600 nanodollars (USD6.9802146). This covers the original 214,600
nanodollars of settled historical smoke, two probe blocks of at most USD0.49,
and six paid game trials of at most USD1. Declared additional prior costs remain
liabilities; they cannot silently expand that envelope. The monthly USD50
authority and existing USD12 admission headroom are unchanged.

The frozen six observations must contain two model-choice opportunities with
an effective 5,000ms deadline, three with effective deadlines 1,000/1,000/1,500ms,
and one local single-candidate choice. Effective deadline remains the minimum
of worker timeout and every offered action's TTL. The policy changes neither
the candidate TTLs nor the provider timeout calculation.

There is one canonical invocation. Each provider's fixture block runs once;
both blocks must pass this policy before the existing attested campaign starts.
The canonical rotation, nine trial identities, one monthly ledger, kernel lease,
immutable output, input snapshots, private gateway and cleanup hooks are retained.
There is no resume flag, second scheduler, fresh ledger, retry or replacement
attempt. The evaluator's existing sequential timing and backoff remain intact.

## Positive evidence and negative performance

Both 5-second choices must be valid. Their replay evidence must identify the
frozen observation, decision, one request, settled ledger amount, effective
model and deployment. Every returned short-deadline response must pass the same
validation. An authentication, route, schema, usage, cache-price or other observed
technical error blocks the game, including one occurring at a short deadline.
Each positive summary must match its one recorded `model_proposed` choice;
negative summaries must remain false and contain neither a choice nor a recorded
proposal. Requested observations and memory must match the frozen inputs.
Positive responses also require integer elapsed evidence within the candidate
deadline in both the total decision summary and the terminal request event;
the total cannot be shorter than its request. A synchronous stall can prevent
an asyncio timer from firing before a late result returns. Such a purported
success blocks with `positive_timing_unqualified`, for long and short cases
alike, even when usage is known. It is never credited as successful performance.

A short `TimeoutError` is allowed only when the real request recorder also
reports `failed/TimeoutError`, with `unsettled:true`, a matching ledger request
whose `spent` remains null, and the complete original reservation intact. An
error label alone is insufficient. Missing usage is a technical error, not a
deadline exception. No timeout reservation is released or settled as zero.
The total decision elapsed time must be an integer reaching that deadline;
the terminal request elapsed time must be an integer between zero and the total.
The request clock starts after reservation SQL, so it need not itself reach
the full TTL. An immediate transport `TimeoutError` is not deadline performance.

The next short opportunity may be skipped by the existing controller backoff.
It is allowed only after a reconciled timeout, with a recorded `skipped/backoff`
event, zero reservation and no ledger request. A successful later response resets
this causal state just as the provider resets backoff. The policy never waits
for cooldown, clears backoff or repeats an opportunity to obtain a nicer result.

The complete run/request/decision evidence must reconcile: no missing or repeated
decisions, gaps, unrelated ledger attempts or unaccounted reservations. Each
probe's `sum(COALESCE(spent,reserved))` must stay within USD0.49. The existing
Store continues enforcing the canonical monthly and run caps during execution.

## Reporting

Timeouts and causal skips keep `valid:false`; their outcomes are
`deadline_negative_unknown_charge` and `causal_backoff_negative`. Reports expose
five model-choice **opportunities** separately from actual ledger attempts.
For example, two successful 5-second choices followed by a 1-second timeout and
two causal skips produce three requests, not five.

`accepted_for_game:true` means the prospective admission contract passed. It
does not mean every probe passed or every cost is known. `financial_final:false`
identifies retained unknown charges; `short_contract_coverage_complete:false`
identifies short cases whose response contract was not observed. Known spend
and reserved liabilities must remain separate. This policy does not qualify
game duration, XP, survival, party play or the final pilot by itself.

## Offline regression scope

Tests enter the real pilot executor and canonical decision evaluator using the
real GatewayProvider, recorder and temporary Store. Only the SDK boundary and
game execution boundary are simulated. They cover timeout/backoff continuation
once, all five successful responses, observed technical failures, failed long
conformance, misleading error labels, replay gaps, unrelated unknown requests,
actual spend above the probe cap, prospective bounds and strict-policy behavior.
No real inference, credentials, canonical ledger SQL or production mutation is
needed for these checks.

Verification on the prospective patch: the new continuation test first failed
on the unchanged executor's `conformance failed` gate, then passed with this
policy. The combined pilot, report, attestation, gateway and budget suite passed
131 tests (45 pilot tests, including the original strict-mode regressions).
Ruff lint/format, mypy for both tools and `git diff --check` passed. These are
offline application-boundary checks, not evidence of a real provider's latency,
cost or gameplay performance.

Independent review also reproduced two inconsistent summaries on the first
prospective patch: a skip labeled valid and a settled schema failure relabeled
as a valid offered choice without a recorded proposal. Both new regressions
failed by reaching the simulated game before the fix, then passed with the
proposal/negative-state reconciliation above.
The temporal review also reproduced synchronous SDK stalls beyond the long
and short deadlines while the canonical evaluator still returned valid choices.
Both regressions reached the simulated game before the elapsed-time guard and
were blocked afterward, without changing the provider or scheduler.
An immediate SDK `TimeoutError` also reached the simulated game before the
negative elapsed-time check. Its regression now blocks, while a control with
120ms reservation overhead accepts a genuine outer deadline whose request
clock legitimately measures less than the TTL.
