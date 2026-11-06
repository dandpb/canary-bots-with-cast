# Separate supply purchase and solo return proof

The controlled supply-B attempt completed its two declared goals: buy supplies through the normal action path, persist the result, then return near the temple. **It is not a 30-minute qualification, an equivalent-start scored round, a human party test, or a model comparison.** It does not replace the earlier failed fake run or the H navigation diagnostic.

| Evidence | Result |
| --- | --- |
| Run | `m5-supply-7f445fec33:supply` |
| Sampled span / full recording envelope | 82.749 s / 99.351 s |
| Purchase action | `supplies_bought`, completed in 44.647 s, supply delta +38 |
| Persisted stock / bank | Potions 2 → 40; bank 10000 → 7986 (2014 gp) |
| Return action | `party_rejoined`, completed in 38.205 s; native party size 1 |
| Persisted position | `(32371,32238,7)`, Chebyshev distance 3 from temple `(32369,32241,7)` |
| XP | 98800 before and after; this proof targets supplies/return |
| Observed deaths / gaps / operator interventions / automatic recovery requests / inference requests | 0 / 0 / 0 / 0 / 0 |

`goal-proof.json` preserves all **14 goal checks** and `goal_accepted=true`. The separate `summary.json` explicitly keeps **qualification_accepted=false / paid_pilot_admitted=false**. The zero cost fields are replay observability with zero inference requests, not an assertion about a paid canonical ledger.

The inherited `model_decisions` and `valid_proposals` metrics count scripted fake evaluations here; they are not LLM or billed API calls.

`private-cost-receipt.json` retains the original read-only, single-transaction request aggregate from this proof's private worker state: zero requests/spent/reserved and `canonical_ledger_accessed=false`. It has no monthly budget header and supplies no claim about canonical paid spend or available budget.

## Controlled fixture and source

The supply-only derivative starts with one health potion and one mana potion and an empty hunt mask (`mask=0`). It allows the scripted provider to choose resupply below ten potions, then retreat after confirmed purchase. An empty hunt mask changes the available actions and helps the normal solo retreat survive the healthy-idle filter. This is an intentional fixture variation, not a scored equivalent start.

Parent fixture SHA256: `42467745d544801e44e32deecf99f5f6d1e1aa869e2bf227734daf95ae42e5be`.
Derivative SHA256: `a98765bba6267216cdb517673761c29823b32259361e1583b5e67efc02ffb930`.

The application revision is `390b8c8920d4e42e8d2eaca056c2076798d1edf7`, native revision `d43050147bc13d8024bdc66b641b127c31253b7c`, and game image `sha256:9bd6213c4d37fa9acdb46c4149d4f3427c3af1d6e1ed6b8b6599c37244185b99`. These identities remain distinct from H's native `29867133` and image `16b69a22`. Runtime image/binary metadata and a cleanup receipt are included.

`party_rejoined` is the native terminal reason for this **solo** return; it does not establish a human party playtest. The selected goal proof contains character/stock values already extracted by the original harness. No game DB is included or queried by this consolidation.

## Offline verification

```bash
python verify_bundle.py
```

Run from this directory. The stdlib-only verifier checks public hashes, replay integrity, the two linked outcomes and the narrow goal checks. It writes no files and starts no provider, container or database.

The replay contains 207 events and was exported from a temporary copy of the closed recording SQLite and WAL, then freshly imported. Source hashes were unchanged before/after. `source-sha256.json` references original files; `checksums.json` covers published bytes. The public plan omits private build paths and runtime identity labels. Raw DBs, worker state, env files, credentials, map, native binaries and full logs remain excluded.

The long free-run qualification and any paid OpenAI/Gemini pilot require their own recorded horizons, equivalent fixture, accounting and acceptance gates.

An earlier supply-A preflight rejected a literal placeholder image ID before fixture, DB or game creation. `preflight-A-receipt.json` retains that separate failure; it is not a real run or part of supply B's goal result.
