# Navigation diagnostics — qualification remains blocked

These six controlled, real-game diagnostics retain the attempts that preceded a successful solo return. They use explicit operator setup, scripted choices and different native builds. They are **not scored M5 rounds**, do not compare AI models and do not admit the paid pilot. The earlier 30-minute fake failure remains unchanged in `../m5-current-free-attempts`.

| Case | Requested / sampled seconds | Linked action outcome | What the evidence establishes |
| --- | ---: | --- | --- |
| B | 60 / 60.608 | Retreat failed after 28.213 s: `return_route_unavailable` | The short recording completed, but the return failed. |
| C | 60 / 60.338 | No terminal return outcome | Movement reached a different checkpoint; arrival was not proved. |
| D | 240 / 240.745 | No terminal return outcome | Longer observation still did not prove arrival. |
| E | 120 / 121.111 | `hunt:399` accepted, no terminal hunt outcome | `travel_to[0]` was skipped after 36 s and patrol progressed to cursor 7. This is partial progress, not a completed hunt or a reproduction of the original immobility. |
| G | 240 / 240.618 | Retreat failed after 209.286 s: `return_route_unavailable` | The earlier cache build still failed this return; bounded portal search and uncached path diagnostics are retained. |
| H | 240 / 94.179 | Retreat completed after 71.501 s: `party_rejoined` | Native outcome plus postmortem DB-copy B proves arrival within three tiles. The requested horizon and canonical export did not complete. |

All six have zero observed deaths, recording gaps and inference requests. These diagnostics include operator setup: two recorded interventions in B/C/D/G/H and one in E. Automatic recovery requests were zero. Generic short-window clock checks reported `accepted` on some originals; `matrix.json` preserves that as `author_generic_clock_gate_accepted`, while **qualification_accepted=false / paid_pilot_admitted=false** remains explicit throughout this appendix.

## H: arrival evidence and export limitation

The linked action `0d61f013af5f4b24bab7baf88f349281` records `completed` at replay t=108829 ms with native action elapsed time 71.501 s. The last replay sample is `(32369,32237,7)`, four tiles from the temple `(32369,32241,7)`. A separate postmortem **copy B** records `(32369,32238,7)`, distance 3, HP 365 and XP 100793. `party_rejoined` is the native completion reason for this solo temple return; it is not a human party playtest.

The diagnostic was externally stopped after that native completion. Its recording status is `interrupted`, the sampled span is 94.179 s of the requested 240 s, and `CancelledError` prevented the canonical `qualification.json` and `saved-character.json` export. Both remain absent in the original. The selected cancellation evidence and `H/postmortem-db-copy-receipt.json` make this distinction explicit; postmortem data is never relabeled as a canonical export.

Copy B's receipt says the closed original DB was mounted read-only for copying; 345 original files had identical before/after tree hash `96d5cc58d7c69600c6dd0e8e78f53b3ae3ccfa57432ec693499f0ec5ff269aa0`. The receipt includes the exact character SELECT and hash of the private source-hash manifest. The original DB, copy, and file tree are excluded from publication. This receipt references the prior controlled extraction; this consolidation did not start MariaDB or query a game DB.

## Build and trace identities

Each case has `identity.json`, including application revision, native revision when separately attested, images, binary hashes, fixture, map and driver hashes. B's original attestation does not identify a separate native source revision; that field remains null. C/D/E use native `667631ba`; G uses `3f829b6b`; H uses `29867133`. These are kept separate from the evolving main branch.

G's native cache receipt identifies `sha256:b0aa91ee0398c9fde82f66b8b265c831af9f69f09beacb98f1d582e99fd9612e`; H identifies `sha256:2493a8b501445c2fbaf5f4cce8ceb6e76f7427b7ac9bfe478d6790e2da30f045`. These are build cache image identities, not gameplay runtime images. H's runtime game image is `sha256:16b69a22965756ccca1328aa4ae50e955776b59702dc4d13ac5430432543efef`.

G's selected portal trace preserves bounded BFS exhaustion (`visited=20002`, budget 20000) and an uncached wide A* path of 164 tiles for the original checkpoint with arrival 2. The same trace also retains failed searches at the later stalled checkpoint. A path found in a diagnostic search does not imply the live return completed; G's linked terminal failure remains in the replay.

`selected-native-trace.json` documents its line selection and source log hash. `diagnostic-commands.json` retains only allowed debug command/result fields. Full service logs remain private. Every replay is exported from a temporary copy of closed SQLite + WAL files and freshly imported for validation; original SQLite hashes were checked before and after. `source-sha256.json` names original artifacts relative to their diagnostic identity, while `checksums.json` verifies the published bytes. Private path prefixes in derived JSON are replaced with labels; the original hashes identify pre-label source bytes, not the derived copies.

## Offline verification

From this directory, run:

```bash
python verify_bundle.py
```

The stdlib-only verifier checks the published inventory, archive integrity, event/sample identities, linked action outcomes and the explicit blocked verdict. It writes no files and contacts no provider, container or database. Source hashes are provenance references: verifying the public bundle does not grant access to, or independently reproduce, the private DB extraction.

The adjacent [gateway receipt](../m5-gateway-qualification/README.md) covers operational readiness and cleanup at a recorded instant, with zero inference. New long rounds, paid OpenAI/Gemini comparisons, NPC purchase/return acceptance and human playtesting retain their own gates.
