# M5 recovery v2 — prospective budget contract

Status: prospective contract implemented after the reviewed SQLite lifetime fix.
This document does not authorize provider calls; reviewed source, frozen inputs
and a new root GO remain required.

## Identity and preserved history

The new literal policy is `short_deadline_performance_recovery_v2`. The existing
`short_deadline_performance_v1` retains its exact USD6.9802146 authorization and
behavior. The original strict policy also retains its current behavior.

This recovery refers to the single failed invocation under namespace
`m5-og-20261106-dae4b84b`. Its OpenAI qualification and incomplete Gemini block
remain a separate failed infrastructure attempt with their actual financial
liabilities; neither becomes zero, disappears, or is retroactively qualified.

The authorization must retain these two historical request IDs and amounts:

| Historical request | Settled nanodollars |
| --- | ---: |
| `8e32e915ca5e4407a3ec55ab501bd99a` | 52800 |
| `57f0becd17ab47a2ad3638987ca2f6ef` | 161800 |

`additional_cost_run_ids` must contain these two actual prior probe IDs exactly
once, including the Gemini block whose result/export was interrupted:

- `decisions:e9b235a5fcd24566b020fc332cd44e0d:65001`
- `decisions:3f5394354a1a43ef8072c99256c4cbb3:65001`

Both runs must exist in the canonical request table. A missing run is an
admission failure, not an assumed zero. All requests belonging to the two runs
are counted; a missing recording terminal does not exclude a reservation.

## Complete envelope

The new envelope must declare `max_total_nanousd: 7000000000` and the existing
canonical monthly cap of USD50. Compute `L` from one canonical read-only SQL
snapshot: the two historical settled amounts plus `SUM(COALESCE(spent,reserved))`
for the mandatory prior runs, excluding the two historical request IDs from
that latter sum. Do not add the global monthly balance to `L` or count a request
twice. The global monthly balance still independently enforces the USD50 cap
and the existing USD12 admission headroom.

At the verified 17:08:42 UTC cut:

| Component | Known spend | Unknown reservation | Complete liability |
| --- | ---: | ---: | ---: |
| Original smoke | 214600 | 0 | 214600 |
| Failed OpenAI probe | 187300 | 942250 | 1129550 |
| Failed Gemini probe | 175800 | 2414800 | 2590600 |
| `L` | 577700 | 3357050 | 3934750 |

Admission requires `L + 2 * 490000000 + 6 * 1000000000 <= 7000000000`.
With the observed values this is `6983934750`, or USD6.98393475, leaving
16065250 nanodollars under the unchanged USD7 user ceiling. Re-read `L` at
preflight; do not substitute this observed constant for live accounting.

Every unknown charge keeps its full canonical reservation. A lower `L` can
only reflect a real canonical settlement supported by trustworthy usage and
pricing evidence; no assumed refund, zero settlement, release, manual edit,
fresh ledger, or second authority is permitted.

## One new prospective invocation

Use a fresh namespace different from the failed namespace, a fresh immutable
output, the reviewed fixed source, and newly hash-bound admission inputs.
Before inference, freeze the same model/deployment mappings, prices, gateway
policy, fixture/seed, candidate TTLs, controller behavior and trial rotation.
The source/output/namespace identities change; the comparison conditions do not.

Run at most one complete qualification block per provider under this recovery
invocation. Do not reuse the partial Gemini block or substitute the old OpenAI
result, and do not add hidden retries, replacement trials or continuation calls.
Both new blocks must pass the existing two-5s-response/short-deadline contract
before scored games begin. Each new block retains its USD0.49 run cap and each
of the six model game runs retains its USD1 cap. The failed invocation created
no scored run, so no scored trial is being replaced.

Retain the existing kernel lease, canonical Store enforcement, recorder,
request/decision reconciliation, genuine timeout provenance, cleanup and stop
conditions. `financial_final=false` remains mandatory while any included
charge is unknown. Budget acceptance is separate from model conformance,
observed horizons and eventual pilot qualification.

The canonical ledger holds a permanent single-use recovery claim in `records`.
Read-only preflight refuses an existing claim. Under the M5 lease and before any
provider call, execution takes an immediate SQL transaction, rechecks the exact
historical rows, both prior runs, USD7 envelope and USD12 monthly headroom, then
inserts the claim with the namespace and admitted input hashes. A failed or
interrupted execution never releases it; another namespace cannot omit the
first recovery's charges and start a second recovery.

## Proposed minimal source delta

1. Add the recovery literal and the two required prior-run IDs. Recognize it as
   the same performance-contract family while retaining its actual policy label
   in successful and failed qualification summaries.
2. In recovery preflight only, require the exact historical IDs/amounts, the two
   prior runs without duplicates, a new namespace, and the USD7 envelope.
3. Extend `ledger_snapshot` with an optional recovery-only required-run check.
   In its existing explicit read transaction, calculate the additional liability
   and presence of both runs. Preserve the SQL lifetime/closing fix supplied by
   the prerequisite branch. Keep its ordinary return fields unchanged.
4. Reuse the existing USD7 `L + new_worst_case` comparison for recovery; retain
   the tighter v1 comparison unchanged. The configured run caps and Store stay
   unchanged. This changes admission, not billing or settlement.
5. Add focused temporary-SQLite regressions: exact recovery accepts; either
   prior run omitted/duplicated/missing fails (including missing Gemini summary);
   unknowns count in full; exact USD7 boundary accepts and +1 nanodollar fails;
   prior costs are not double counted; old namespace fails; v1 exact ceiling
   and legacy behavior remain unchanged. No canonical SQL or real provider call.
6. Persist and recheck the single-use recovery claim in the canonical ledger
   before inference. This prevents a second fresh namespace from replaying the
   same historical envelope after the first recovery has spent money.

Root reviews the precise patch, an independent reviewer checks this budget v2,
and a new explicit root GO is required after the SQLite fix and all admission
gates pass. This proposal does not resume or retry the failed execution.
