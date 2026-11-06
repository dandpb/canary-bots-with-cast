# R2 final qualification report: NO-GO before games

The single canonical R2 invocation `m5-og-r2-20261106-27120d96`, source `4c5bb9bf4b93fb11abffd7bd3020e6381296fd6d`, ended with **qualification rejected**. OpenAI's technical/unreconciled-evidence gate did not pass. **Gemini R2 was not evaluated, no native/game trial started, and no nine-run provider comparison or gameplay XP result exists.** This is the final report of this qualification attempt, not completion of the comparative M5 pilot.

The historical GO receipt SHA256 is `944a94de02ca12cd6a3a99ced89e9d902d2bf2a033e071d518d61c648b3b1f9c`. The invocation ran from 18:15:58.549112 to 18:16:10.673949 UTC on 2026-11-06 and exited 1. `campaign` remains null. The predeclared gate stopped execution before `run_attested_campaign`; there is no generated game output to relabel or fabricate.

## What actually ran

The OpenAI probe is **real inference on synthetic decision fixtures**, not live gameplay or a counterfactual XP/survival experiment. One replay preserves 18 events and three canonically reserved application attempts. Its original manifest retains `synthetic=true`, `source_revision=unknown` and configuration hash null. Source 4c attribution is supplied separately by the captured execution inputs and GO/source receipts; the archived manifest was not retroactively edited.

| Case | Observed result | Elapsed ms | Accounting/selection scope |
| --- | --- | ---: | --- |
| Long 1 | Post-request `ValueError`; no `model_proposed` event | 4093 | Finished response; 170900 nanodollars settled |
| Long 2 | Valid `hunt:399`; one recorded proposal | 4217 | Finished response; 114900 settled |
| Singleton | Local `resupply` | 0 | No model request/reservation |
| Short | Recorded `TimeoutError` | 1018 |942250 reserved unknown |
| Next short cases | Two local `ProviderBackoff` skips | 0 each | No extra HTTP reservation |

The original qualification reports `valid=2` (one model selection plus local resupply), `late=1`, `technical_invalid=3`, `accepted_for_game=false`, `evidence_reconciled=false`, policy `short_deadline_performance_recovery_v2`, and rejection `technical_or_unreconciled_evidence`. Preserve this original aggregate, but do not call it three upstream/model failures: it includes the first ValueError and two local backoff results. The timeout/backoff counts retain their deadline context; no latency ranking is inferred from them.

Three **distinct stages** remain visible: first decision `ValueError` after a finished request; later evidence-reconciliation `ValueError` at `m5.probe_evidence`; outer rejection at `m5.probe_ledger.openai`. None is renamed as a SQL error, identity failure or provider truncation without evidence. The timeout's unknown liability is not zero and does not prove completed upstream inference.

## Diagnostic finding and its limits

The safe copy analysis confirms the first request's alias/effective-model/deployment identity matches the expected `canary-openai`/`gpt-6-luna` route. It records reserved→finished, zero request-failed events for that request, and zero model proposals. The ValueError occurred after `_request` in action selection, with no exact branch retained.

Usage was input 429/output 256/reasoning 256/total 685, priced at 170900 nanodollars. The frozen stack's configured output budget is 256; all reported output tokens were reasoning tokens. This is **compatible with exhausting the output budget before an actionable choice**, but status, `incomplete_details`, raw output and tool-call count were **not persisted**. Do not assert `status=incomplete`, truncation, a specific guard branch or a provider defect as proven.

The second response had input 429/output 144/reasoning 121/total 573, cost 114900 and a recorded `hunt:399` proposal. A proposal event is not a persisted tool-call count. The public diagnostic is derived from source SHA256 `0941f9c56933f269d714f9aa6adb54d66d4d4caa8f17c52aacaaa84bb870e4b4`: only its private `copy_database` path was replaced with a label. Usage, identities, events and limitations remain intact; the transformation is recorded separately.

## Financial report: known spend and unknown liability

The executor successfully wrote its selected ten-row `ledger.json` at **18:16:10.203764 UTC**, without `ledger_export_error`. Finance independently reconciled those 10 rows and the seven prior IDs at **18:21:10.457077 UTC**. `finance-1821` contains the approved public receipt byte-for-byte, SHA256 `8750cf48751b7958a68078e6cd3179cc097d3115e2ed74b68c75bd7b58a08be8`.

| Scope | Known settled nanodollars | Unknown reserved | Complete liability |
| --- | ---: | ---: | ---: |
| Prior 7: bounded smoke + failed e65 |577700 |3357050 |3934750 |
| New R2 OpenAI 3 |285800 |942250 |1228050 |
| **Cumulative** |**863500** |**4299300** |**5162800** |

One dollar is 1,000,000,000 nanodollars. Cumulative known spend is **US$0.000863500**, unknown reserved liability **US$0.004299300**, and complete liability **US$0.005162800**. **`financial_final=false`**. Reservations remain held; they are not confirmed final spend, free calls or evidence of transmission/completion. Claim `COUNT=1` is retained and consumed, with its data field unread; it is **not an eleventh billable request** and was not mutated by Finance or this collector.

The 18:21 monthly account header is newer than the executor's 18:16 export: cap 50000000000, settled 558192525, reserved 75456550, available 49366350925 nanodollars. It includes production/shared-account activity. Do not attribute all header changes to M5 or substitute the older header as current. Prior 7 preservation and new3 reconciliation are explicit in the Finance receipt. Gemini's zero **new R2** attempts does not erase its older e65 liabilities and is not a result about Gemini's performance.

## Closure, preservation and source chronology

Owner custody receipt SHA256 `40824d0f69adb7f892c00d3d27be1612c72033a1edb5c5a8981a7d9106d27191` preserved 19 files before any SQLite reader, including DB/WAL/SHM, seven captured inputs and the root/preflight/outcome receipts. This collector copied that custody into a private workspace and used a further temporary DB+WAL copy for export/reimport. The supplied copies' hashes/sizes/mtimes/modes/owners remained unchanged. No primary f6/f7, canonical DB, credential or production service was opened by this collector.

Closure SHA256 `2bfc66a66a8cbee73d6568afe249987b70f84214071dfc274a008c5c7e09ef69` retains one invocation and zero reinvocations. The **full harness CID was not retained**. Its exact actual name was retained, later inspected absent, and no harness service remained. The historical Docker event window returned no records; that emptiness is explicitly **not proof of no game creation**. No-game evidence comes from the gate stopping before campaign execution, null campaign, absent game output and absence checks of all nine exact owned projects. Do not manufacture a historical destroy event or missing CID.

The temporary private gateway was separately closed at 18:27:18 UTC after diagnosis. Its owner exited, cleanup phase is `cleaned`, lease is free and logs were preserved by the operator. The safe cleanup projection references receipt SHA256 `45f8cb31876a2dce4bb5e81cfa938088c202c2cda3590063413112df6c853b7b`. Ten permanent containers remain running; nine have healthy Docker checks and the brain has no Docker healthcheck. This collector made no cleanup command, call, reservation release or claim change.

The producer remains 4c. Later main `a2f4d799` adds onboarding documentation; it is not relabelled as R2's source. Captured code validation 587 tests/67 subtests, setup 54 and Redis 50 are separate integration scopes, not additive model/game samples and not comparative M5 acceptance. The successful [free-B qualification in PR25](https://github.com/dandpb/canary-bots-with-cast/pull/25), [failed e65 attempt in PR60](https://github.com/dandpb/canary-bots-with-cast/pull/60) and [single-use recovery control in PR63](https://github.com/dandpb/canary-bots-with-cast/pull/63) retain their own sources, outcomes and limits. None is overwritten by R2.

## Offline verification and remaining work

```bash
python -B verify_bundle.py
```

The stdlib-only checker validates hashes, the 18-event synthetic archive, three new request IDs and 10-row accounting, rejected qualification, unevaluated Gemini/no-games scope and retained claim. It writes nothing and accesses no original path, provider, Docker service or ledger. Root checksums cover actual public bytes, including nested Finance checksums; source hashes identify the private pre-projection receipts.

No `game/experiment.json`, nine-run score table, new Gemini archive, gameplay timelapse, XP/h comparison or winner is fabricated. Paid nine-run comparison remains **unexecuted and blocked by this qualification outcome**. Any new effort/diagnostic controls, authorization and run identity require a separate reviewed process; this historical GO cannot resume R2 and its consumed claim must not be cleared.

Append to [#10](https://github.com/dandpb/canary-bots-with-cast/issues/10) and [#14](https://github.com/dandpb/canary-bots-with-cast/issues/14). Issue #10 was already closed as a planning artifact; this report does not close it again or infer M5 completion from its status.
