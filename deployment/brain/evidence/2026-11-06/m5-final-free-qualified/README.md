# Free-B functional qualification passed

The closed native and scripted-fake B attempts each passed **16/16 gates**, including the recorded/observed horizon, positive saved XP, cycle evidence, healthy observer, pinned runtime images and cleanup. This is free functional qualification. **It does not admit a paid campaign or establish a model ranking, human party acceptance or AFK safety.**

| Participant | Requested s | Sampled span s | Supervisor observed / elapsed s | XP gain | Saved XP | Completed hunt macros / confirmed defeats |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Native | 1800 | 1800.387 | 1800.374013 / 1800.404031 | +3891 | 102691 | Native phase evidence below |
| Scripted fake | 1800 | 1801.000 | 1800.946146 / 1801.009709 | +4142 | 102942 | 5 / 108 |

Both started at XP 98800 and recorded zero deaths, gaps, operator interventions, automatic recovery requests and inference requests. Replay cost fields are zero; no canonical paid-ledger authority is asserted here. The fake's `model_decisions`/`valid_proposals` count scripted evaluations, not LLM calls. One run per participant is descriptive; it cannot establish a winner.

## Cycles and persistence limits

The native status observer records script 399 through PATROLLING → LEAVING → RESUPPLYING → PATROLLING (last transition around observer elapsed 1327 s). These are hunt phases, **not proof of an NPC purchase**. The fake has linked, XP-positive `hunt_progress` completions followed by new accepted hunts; these are hunt macro cycles, **not proof of a return or purchase**.

Canonical `saved-character.json` proves SQL-persisted **XP, level and position only**. `character-live.jsonl.gz` retains HP, potions and other observations **in memory**; it is not a post-save SQL inventory/HP export. Do not broaden the persistence claim. The separate [supply-B derivative](../m5-supply-return-proof/README.md) proves purchase, persisted stock/bank and solo return under its own controlled mask0 fixture, source and short duration.

## Source and equivalent starting fixture

Both B producers are frozen revision `47adddc40ad866e75450d317622dada6b7592687`; their exact driver SHA256 is `6f3c8fc550b24511fbd0d30c2ebe7611a1e977a7006fcbcae39343ed791c1336`, included byte-for-byte. The QA driver and dependencies are available at that Git revision under `tests/fixture`; its stable-cwd/observer checks were validated separately. Later evaluator improvements remain later source, not attributed retroactively to B.

Both use native `d43050147bc13d8024bdc66b641b127c31253b7c`, game image `sha256:9bd6213c4d37fa9acdb46c4149d4f3427c3af1d6e1ed6b8b6599c37244185b99` and DB image `sha256:a794d9eb009e20de605858a11f32f63b4075cbd197c650436f0e3b457e4caed7`.

Fixture G SHA256 is `42467745d544801e44e32deecf99f5f6d1e1aa869e2bf227734daf95ae42e5be`; map SHA256 is `a80de1dda6a9aca3956a9d5b7fb2e0caebb451570d26853fc21beb40d5f31da2`. `frozen-fixture-receipt.json` records selected starting stats, equipment, authored hunts 77/399, vocation mask, timers and activity weights. These are a **controlled scenario**, not default-world behaviour. Source/map/fixture identities match across participants. They ran isolated stacks concurrently, so this is not a controlled latency/CPU benchmark.

The PR also integrates main `1f025f0ea` (including cleanup #51 and trial attestations #53). Those later changes, and the [Redis operational receipt](../m5-redis-qualification/README.md), are not relabelled as B producer source. Runtime pins and paid integration keep their own acceptance review.

## Offline evidence and preservation

```bash
python verify_bundle.py
```

Run from this directory. The stdlib-only verifier checks published bytes, archive identities and horizons, saved XP, outcomes and the explicit free/pilot distinction. It writes no files or requests. The two archives contain native 3296 and fake 5750 events, exported from temporary closed SQLite+WAL copies and freshly imported. Original hashes were checked before/after and against the final post-run audit. Original source hashes identify pre-label bytes; `checksums.json` identifies these published copies.

Pass `--repository /path/to/checkout` to also verify the 326 pre-existing evidence files against their recorded working-byte hashes and Git blobs at the previous PR25 head and current HEAD. The original 89 historical checksums are included in that preserved history; none of the prior bundles was rewritten.

Each participant retains its canonical qualification, exact producer driver, phase status, compressed live observations, runtime/cleanup metadata, original source hashes and independent post-run audit projection. No DB, worker state, env, credential, map, native binary or full service log is published.

All prior evidence remains chronological and unchanged: the earlier stalled fake, [interrupted A](../m5-final-interrupted-attempts/README.md), its [infrastructure follow-up](../m5-infrastructure-A-followup/README.md), supply and navigation diagnostics. Passing B does not erase their failures or turn auxiliary/postmortem data into canonical artifacts.
