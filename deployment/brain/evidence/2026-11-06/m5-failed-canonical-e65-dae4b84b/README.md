# Closed e65 invocation failed before any game

This appendix preserves **one failed canonical invocation**, namespace `m5-og-20261106-dae4b84b`, on source `e65e8913becc6e5766e1fa050cbf82183e7ee69e`. It ran from 16:53:11.482973 to 16:53:22.701064 UTC on 2026-11-06 and exited 1 with `OperationalError`; the wrapper's automatic ledger export also reported `OperationalError`. The original message, traceback and SQLite errno were not retained. **No scored campaign, native trial, gameplay XP result or nine-run comparison exists.**

The closure receipt reports one execute invocation, zero reinvocations, no game-child events in its captured window, `game_campaign_created=false`, and the temporary harness absent. Its original SHA256 is `ff01dbaaa9c282b8bee1b47a5a7b62f04796567dd1e980e034a0e8ea06534551`. The collector performed no cleanup command and did not open the canonical ledger. This does not claim that an entire provider/gateway service was stopped.

## Decision probes are synthetic fixtures, not gameplay

Both archives retain `synthetic=true`, scenario `recorded-decisions-real-inference`, and their original recording status `failed`. Recorded observations may contain bot/XP fields, but those are **decision fixtures**, not live progress, counterfactual XP or scored game evidence. The manifest source revision was `unknown` and configuration hash null; these are preserved. The external e65 source/policy attribution comes from the captured inputs, actual preflight, source export and closure/GO receipts, not a retroactively edited replay manifest.

| Probe | Application attempts with canonical reservations | Finished | Recorded timeout failure | Local backoff skips | Missing request terminal | Original result JSON |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| OpenAI / `gpt-6-luna` | 3 | 2 | 1 | 2 | 0 | Present; narrow probe policy accepted it for game |
| Gemini / `gemini-3.5-flash-lite` | 2 | 1 | 0 | 3 | 1 | Absent after local wrapper failure |

OpenAI has two valid long-deadline responses and a one-second timeout. Its original `valid=3` also counts a local single-candidate selection; it does not mean three successful provider responses. Two subsequent backoff skips are local, not additional HTTP attempts or SQL reservations. Probe-policy acceptance did not start a game.

Gemini has one valid long-deadline response. Its second reserved request has no recorded finished/failed terminal, followed by three local backoff skips. Do not infer a second valid response, a timeout, a zero charge or a completed Gemini probe from the missing terminal/result. The later Finance KV observation was absent; absence is not a cause diagnosis or proof of no upstream work.

The two archives contain 19 and 16 events and were exported from temporary copies of the closed recording DB+WAL, then freshly imported. Original DB/WAL/SHM content hashes, sizes, mtimes, modes and owners were unchanged. No original SQLite was opened by the replay reader and no credential, raw DB, worker state or full canonical ledger is published.

The f6 recording DBs and the closure snapshots used by Finance have **different physical DB hashes**. `recording-representation-equivalence.json` preserves both identities: full run metadata and every event compared equal in private copies. Finance's `recording_sha256` means its closure snapshot DB-main file hash, not the raw f6 DB or a composite DB+WAL hash. WAL hashes are retained separately in `originals-preservation.json`. No physical equality or corruption is inferred from the different representation hashes.

## Financial liability remains attached to this failed attempt

The public Finance projections are copied **byte-for-byte** in separate directories. Their timestamps are not merged into a fabricated snapshot:

- `finance-1702-prices-kv`: financial cut at 17:02, prices from hash-matched captured inputs, and a separately timed KV observation around 17:05.
- `finance-1708-integrity`: final financial cut at 17:08, `integrity_check=ok`, and comparison against the 17:02 baseline.

| Scope | Known settled nanodollars | Unknown reserved nanodollars | Known + unknown liability |
| --- | ---: | ---: | ---: |
| OpenAI probe | 187300 | 942250 | 1129550 |
| Gemini probe | 175800 | 2414800 | 2590600 |
| This invocation | **363100** | **3357050** | **3720150** |
| Prior bounded smoke | 214600 | 0 | 214600 |
| Including that history | **577700** | **3357050** | **3934750** |

One dollar is 1,000,000,000 nanodollars. This invocation has US$0.000363100 settled and US$0.003357050 reserved unknown; its liability is US$0.003720150, or US$0.003934750 including history. **`financial_final=false`**. Reservations are liabilities, not measured final spend, and were not released or settled by this collection. All five current request IDs match between the probe evidence and Finance projection. Scored-game ledger requests are zero.

The application recorded five attempts carrying canonical reservations: three responses finished, one recorded a timeout and one has no terminal. Upstream transmission for the second Gemini request is unconfirmed by the preserved public evidence; its full unknown liability remains. Zero calls performed by the financial audit/collector is a different scope and must not be described as zero paid activity for the attempt. Public monthly account totals include production and are not attributed to this failed invocation.

The stronger preserved ledger baseline starts at **17:02**, after the execution: 10126→10211 rows, no missing baseline rows, 10034 known and 92 unknown IDs/values preserved, and seven prior selected requests unchanged. Do not invent an all-known baseline before 17:02 or assign all later rows causally to this attempt. These receipts are accounting/integrity evidence, not provider invoice reconciliation.

Only the original error class is known. Later helpers' `CANTOPEN` errors and synthetic POSIX/SQLite reproductions are separate experiments; they do not establish this invocation's exact original cause. No actual canonical-ledger corruption is observed in the published final integrity receipt. Gemini's null cache-write price remains unqualified for positive cache-write usage.

## Source, approved inputs and historical GO

The reviewed ROOT_FINAL e65 package SHA256 is `2ff5b9375cef99c46efa0ffdb51fa5054e2c64b738313851cf5d0454ebf445f8`; the historical one-invocation GO receipt SHA256 is `40bd05b7c4f507768cce92831f3325886aa92e0f99aa89e7ecf34b3bae34add3`. Its actual preflight receipt hash and exact captured admission hash are retained in the projections.

There are **six approved payload hashes** (campaign, authorization, source manifest, decision fixtures, OpenAI and Gemini), excluding admission's self-reference. Admission is captured separately, giving **seven captured JSON artifacts**. The actual captured hashes match the execution-started preflight. The earlier ROOT_FINAL admission projection and the final captured admission remain distinct; preparation approval/pending flags are not silently rewritten into runtime history.

`source-and-policy-provenance.json` records the 41-file frozen e65 source manifest, checked file hashes, policy/routing pins and selected model/price profiles. `validation-provenance.json` retains current e65 **534 tests / 59 subtests** with durable raw-log hashes verified. The historical 531-test `/tmp` raw logs were lost after the restart; none was recreated or presented as retained. Existing source-validation success is not proof that this invocation succeeded.

A later recovery must have a separate namespace and authorization after the SQL fix/review. It cannot resume this invocation, erase its cost, replace missing terminals or retroactively qualify it. This appendix changes no future pilot source/configuration and makes no production or provider request.

## Offline verification

```bash
python -B verify_bundle.py
```

The stdlib-only verifier checks the public inventory, both replay member hashes/identities, five request IDs, missing terminal, six-plus-one input roles, closure and financial arithmetic. It writes nothing and does not access any original path, API, Docker service or ledger. `originals-preservation.json` retains private-original artifact hashes and metadata using relative labels; root `checksums.json` covers the actual public bytes, including the two nested Finance checksum files.

Refs #10/#14. Issue #10 was already closed as a planning artifact; this failed pre-game attempt neither completes M5 nor closes that issue again. No model ranking, human playtest, AFK safety or nine-trial acceptance is claimed.
