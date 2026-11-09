# NONEV3 — partial campaign evidence (2026-11-06)

The nine-run campaign stopped during `native:0` with `recording_gap`. No run completed. The campaign owner's closure records confirm that the remaining eight runs never started; OpenAI and Gemini therefore have **zero gameplay runs** in this campaign. Both current provider probes were accepted, which establishes probe acceptance only.

The frozen application source is `7f2904e5827edc67997d309d453fa1d7371523cc`. Owner-supplied receipts retain these identities:

| Receipt | SHA-256 |
| --- | --- |
| GO | `2e172d89be1046279d128bbd9e56796c0713b3685853bb0ca95e78c87c6f7c9a` |
| Final Finance | `3b956b89a2b93a53c0d8f483df140b56faad9687904cb5235cb5f5758b7397dd` |
| Custody | `fac42f7a9b711ac9b258ea16cee81db0c8f8ef8cbb55eb5d979b3d93603f13f3` |
| Campaign closure | `c3bba75e9181f4a8605591a0c5727f5f1e955f203a869dc23b8c9bce254aa5ec` |
| Gap projection | `ba7e2f3185c7dcd7155d42249a11d58f9fa0b97b80c3e6c20c0601f1d38baa18` |

## Observed fragment

| Planned | Partial | Not started | Completed |
| ---: | ---: | ---: | ---: |
| 9 | 1 | 8 | 0 |

`native:0` contains 183 samples spanning **220.803 seconds**, against the planned 1,800-second horizon, and one recording gap. Recorded XP delta, deaths and human interventions are each zero **within this incomplete fragment**. There is no final SQL `saved-character` evidence. These values do not establish whole-run survival, saved progression or a completed hunt/resupply cycle. Gameplay metrics for the eight unstarted attempts are unavailable, not zero.

The unmodified reporter output retains `expected_attempts=9`, `recorded_attempts=1`, `reviewed_attempts=1`, all **12 findings**, and `ready_for_review=false`; exit code 2 is expected. Keep `failed/recording_gap` and the stop-classification/evidence findings intact. The gap's cause remains under investigation in [issue #72](https://github.com/dandpb/canary-bots-with-cast/issues/72); this append does not assign an underlying transport cause or retrospectively apply a later fix.

Sample span is distinct from the 239.689-second recorded envelope and the worker clocks (221.788 seconds observed, 221.872 seconds elapsed). `recording_gap` is outside this reporter's accepted stop-reason whitelist; that explains its status finding without implying corrupted status. Two durable stop events retain the original stop and after-flush validation, not two executions. The recorded `observation_sequence_jump` explicitly does not prove packet loss; it is distinct from the critical `native_telemetry_loss` gap.

## Provider qualifications and replay scope

The new OpenAI profile explicitly used effort `none`; Gemini kept its default. Both probes passed the admitted `openai_none_performance_v3` policy, with two valid long-deadline model choices each. OpenAI retains one genuine short timeout and two causal local backoff skips; Gemini has five finished model requests plus one local choice. Local choices/skips are not extra paid attempts. This is probe evidence, without comparative gameplay XP or survival.

Only [three replay ZIPs](replay-verification.json) exist here: the partial native game (411 events), OpenAI synthetic decision probe (19) and Gemini synthetic decision probe (24). OpenAI's archive remains `failed` because its negative timeout is preserved; acceptance under the explicit performance policy does not relabel recorder status. Probe manifests retain their original `source_revision:"unknown"` and null configuration; captured receipts supply external provenance. No eight nonexistent game archives were created.

The native partial [video sidecar](video/native-partial-60x.mp4.json) describes a sampled map replay generated after closure: 96 frames, 24 fps, speed60, 4.0 seconds for the 239.689-second envelope. [Verification](video/verification-receipt.json) includes ffprobe and first/middle/final visual checks. The MP4 is a separate local deliverable; it is not a client capture, AI gameplay or a full 30-minute run. No video frames are statistical samples.

## Financial scope

| Confirmed usage-priced spend | Unknown liability retained | Combined liability |
| ---: | ---: | ---: |
| US$ 0.001981700 | US$ 0.005245675 | US$ 0.007227375 |

These totals reconcile **18 accounting rows**: 10 prior rows, three new OpenAI rows and five new Gemini rows. Four unresolved reservations remain held. The scope includes prior costs and current probes; it must not be attributed to the native fragment or to AI gameplay. `financial_totals_complete=true` means the selected accounting envelope is complete; `financial_final=false` preserves unresolved costs. Usage-priced spend is not provider invoice reconciliation. The reporter's input snapshot is `2026-11-06T19:54:19.625985Z`; the separate final Finance receipt is dated `2026-11-06T20:00:07.949234Z`.

## Relationship to earlier evidence

The R1 evidence in [PR #60](https://github.com/dandpb/canary-bots-with-cast/pull/60) and R2 evidence in [PR #66](https://github.com/dandpb/canary-bots-with-cast/pull/66) plus [PR #68](https://github.com/dandpb/canary-bots-with-cast/pull/68) remain immutable. This appendix adds a separate partial campaign. FreeB qualification in [PR #25](https://github.com/dandpb/canary-bots-with-cast/pull/25) belongs to its separate controlled scenario and does not qualify NONEV3.

This evidence supports no provider ranking, equivalent provider workloads, completed comparative pilot or closure of issue #10. Publication remains subject to independent review of the assembled bundle.

Native/provider randomness was not seeded as a controlled paired trial. Alias/deployment/model strings identify configured controller stacks and gateway routes, not immutable model weights; native decoder guarantees differ and the shared account also serves production. No causal LLM-only XP or human/AFK safety acceptance is inferred.

## Offline checks

From this directory, run `python3 -B verify_bundle.py` and `python3 -B test_verify_bundle.py`. The standard-library checker verifies public hashes, available replay integrity, partial scope and per-request financial/usage reconciliation; it opens no SQLite database or external service. [Raw custody hashes](raw-custody-hashes.json) keep DB-main, WAL and SHM identities separate. Fresh replay imports were compared logically, without claiming physical SQLite equality. The canonical reporter's findings remain unmodified.
