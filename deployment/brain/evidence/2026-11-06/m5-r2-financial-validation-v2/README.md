# R2 financial validator V2 supplement

This later supplement fixes two omissions in the original offline validator from [PR #66](https://github.com/dandpb/canary-bots-with-cast/pull/66). The published R2 amounts were correct. After recomputing checksums on a copy, V1 could nevertheless accept an incorrect known/unknown partition in the summary or a swap of the two settled amounts between request IDs. The tests here reproduce both V1 passes and require V2 to reject them.

The original 22 files, V1 checker, replay and checksum index remain unchanged in [the R2 appendix](../m5-r2-negative-qualification-27120d96/README.md). `supplement-manifest.json` identifies that publication and its producer. It does not replace the original index or present the additional checks as a historical V1 result.

V2 runs the original checker from its pinned published code, then checks:

- Exact integer request amounts, aggregate amounts and financial counts, rejecting equal-valued floats, strings and booleans. Each monthly header is checked at its own historical cutoff; their differences are not attributed to M5.
- Each new request's ID, run ID, original reservation, terminal event, settled amount or retained unknown liability across the executor ledger, Finance's 18:21 public receipt and the decision replay.
- Settled spend recalculated from recorded input/cache/write/output token counts and the captured price version. Reasoning tokens are included in output tokens and are not billed twice.
- New, prior and cumulative known/unknown amounts and liabilities against both the summary and Finance receipt; the seven prior rows are not repriced using R2's prices.
- Local backoff skips remain outside ledger reservations, and the consumed claim remains one non-billable claim.

Run from the repository root with Python's standard library:

```sh
python3 -B deployment/brain/evidence/2026-11-06/m5-r2-financial-validation-v2/verify_financial_v2.py
python3 -B deployment/brain/evidence/2026-11-06/m5-r2-financial-validation-v2/test_verify_financial_v2.py
```

`--parent PATH` validates a file copy of the original public appendix; it never executes code from that supplied path. Tests mutate only temporary copies, update their indexes, and confirm that the published parent's bytes remain unchanged. No SQLite database, service, provider or credential is opened. Checksums identify published bytes; they are not a signature against coordinated replacement of all evidence and trusted code.

The checked facts remain **285800** known plus **942250** unknown nanodollars for the three new attempts, and **863500** known plus **4299300** unknown cumulatively: liability **5162800** nanodollars. Financial reconciliation does not change `financial_final=false`, the rejected qualification, Gemini R2's unevaluated status or the absence of games. XP, deaths and interventions remain unobserved (`null`). This supplement authorizes no retry or paid execution.
