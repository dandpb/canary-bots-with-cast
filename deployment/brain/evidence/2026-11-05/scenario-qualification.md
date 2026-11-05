# Native scenario qualification — 2026-11-05

Two additional, independently restored native-only trials tested whether the
fixture offers useful work before spending on model comparisons. They used the
final immutable-checkpoint game build (`81ac51592`), a frozen observer worker
(`235459ec6`), separate Compose/database/socket directories, no published ports,
no model calls and zero AI spending. These are scenario checks, not provider ranks.

The exact game image for both successful trials was
`sha256:d564b249e91ff36b6850de472c77f6201a71292c4c78ededb1f926b6a4bcf6ea`.
A preceding packaging attempt lacked the executable bit on the copied game binary.
Its failed identity/logs remain recorded. Explicit image COPY modes fixed that
packaging error; the attempt was not overwritten or converted into a success.

## Observations

| Fixture | Requested window | Initial hash | Distinct sampled positions | Offered action types | XP delta / deaths |
|---|---:|---|---:|---|---|
| Dawnport Tutorial | 300 s | `7c512b093ef63870410326d38fd64ec152e2001d37d0ad9e288c4fa9c916d73b` | 1 | continue, hold | 0 / 0 |
| Thais | 180 s | `3b8a877d248f707dee076cf4beb322e101b4f764bfd0768e2df713df94cdf670` | 128 | continue, hold, resupply, retreat, target | 0 / 0 |

Both trials completed without recorded gaps or interventions, with 100% minimum
observed health. Dawnport stayed at `(32069,31901,6)` in DWELLING state and did not
offer hunt/resupply during the window. It remains a valid recorder/runner fixture;
these observations do not establish an informative progression benchmark there.

Thais moved from `(32369,32241,7)` to `(32494,32131,7)` and entered native HUNTING.
Its observed catalog offered a shop/resupply path and native target opportunities.
Initial stock was two potions, below the model hunt-offer gate of ten. This does
not prove that a model completed resupply, a hunt, or earned XP. Validate those
behaviors and use longer repeated windows before a real performance comparison.

These trials have different initial hashes and durations. Do not pool them into
one comparative experiment, treat positions as independent repetitions, or infer
a better model from them. See [raw evidence](native-scenario-qualification.json).

## Preparing the declared Thais fixture

The new fixture was copied from the disposable public-seed QA snapshot, preserving
all non-location character fields and inventory. It did not use a production dump.
Its database seed appends:

```sql
UPDATE players
SET town_id=8,posx=32369,posy=32241,posz=7
WHERE id=65001;
```

Its `character.json` declares ID 65001, level 8, experience 4200 and that position.
Town 8 and its temple/shops are defined in the pinned authored `city_pois.csv`.
Recompute `benchmark hash` for the full seed and world map; never reuse Dawnport's
hash for this fixture. Each model and its native control must independently
restore this same declared fixture and use the same pinned image/awake policy.

## Clock correctness and reanalysis

The recorded calendar and monotonic elapsed clocks differed during the trials:
295395 / 315204 ms in Dawnport and 177826 / 189725 ms in Thais, respectively for
recorded elapsed / calendar elapsed between the first and last samples. No cause
for the host clock discrepancy is asserted.

The prior XP/hour denominator used calendar timestamps. Regression tests with
forward/backward clock corrections showed 10 seconds becoming 3610 seconds or
zero. Metric version 2 uses the recorded elapsed timeline, retains signed calendar
elapsed separately and preserves recorded restart-gap estimates. Three regression
tests failed before the fix and passed afterward. Full Python suite: **98 passed**;
Ruff and strict mypy (18 source modules) passed.

The raw JSON linked above explicitly identifies analysis revision `9aade71b1` and
metric version 2. Original recordings and original on-disk campaign summaries are
preserved. Historical unversioned reports must be reanalyzed with the same metric
version before comparison; they are not silently rewritten as original evidence.

An offline MP4 from the real native Thais recording verified 230 frames, 24 fps,
9.583333 s, 1280×720, requested speed 20×. Video SHA-256:
`ff3a6a5a7c501295f9d56df8165cb8f8973555066ec87acc1396f3006e0a0055`.
It shows sampled native movement on a coordinate grid, without model inference,
invented interpolation or OTClient footage. This remains separate from paid M5.
