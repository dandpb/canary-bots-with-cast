# Current native/fake qualification

These drivers use the current canonical campaign runner and a private, disposable
Compose project per output identity. They never read provider credentials or call
an inference SDK. A clean committed application checkout, a new output directory,
and pinned game/database images are required. Keep historical outputs unchanged.
The timed driver verifies that its imported `runtime` and `benchmark` modules
resolve to that same application checkout before attesting the Git revision.
Setting `PYTHONPATH` to another source tree must fail rather than mislabel it.

The freeze directory contains `fixture/` and `manifest.json`. In addition to the
fixture/world hashes and image IDs, the manifest binds `native_build.source_revision`
and `native_build.archive_sha256` to SHA256 hashes of both `canary` and
`libbot_engine.so`. The build must compile/test the pair together; the drivers
verify those hashes in the pinned image. Application and native source revisions
are recorded separately. A native fix creates a new image and freeze, even if the
fixture's bytes remain equivalent.

From `deployment/brain`, with this checkout installed in the active Python
environment:

```sh
PYTHONPATH=src python ../../tests/fixture/m5_current_qualification.py \
  --fixture-root "$FREEZE" --output "$NEW_NATIVE_SMOKE" --mode native --seconds 10
PYTHONPATH=src python ../../tests/fixture/m5_current_qualification.py \
  --fixture-root "$FREEZE" --output "$NEW_FAKE_SMOKE" --mode fake --seconds 10
PYTHONPATH=src python ../../tests/fixture/m5_current_qualification.py \
  --fixture-root "$FREEZE" --output "$NEW_NATIVE_RUN" --mode native --seconds 1800 --require-progress
PYTHONPATH=src python ../../tests/fixture/m5_current_qualification.py \
  --fixture-root "$FREEZE" --output "$NEW_FAKE_RUN" --mode fake --seconds 1800 --require-progress
```

The long-run gate requires `completed`, exactly one supervisor stop with
`reason=completed`, recorded/observed/elapsed clocks in 1,800–1,805 seconds, no
recorded gaps or observed deaths, no operator intervention, zero inference
requests, positive XP between the first and last observed samples agreeing with
the replay summary, and positive XP persisted in the final database and matching
the last sample. XP gained only before the first observation cannot qualify the
window. At least two hunts must appear in the same native observation.
These progress checks are mandatory for every 1,800-second run, including when
`--require-progress` is omitted. That flag only adds progress requirements to a
short smoke; a smoke without it proves clocks and isolation, not gameplay progress.

Cycle evidence follows each execution mode's actual contract:

- Native: an ordered hunt phase cycle `PATROLLING → LEAVING → RESUPPLYING → PATROLLING`.
- Fake: a nonoperator hunt intent, matching native acceptance and positive
  `hunt_progress` completion, then a new hunt accepted in the same bot/world.
  This is a hunt macro restart, not proof of temple return or NPC purchase.

Runtime image IDs and scoped absence of containers/networks after cleanup are
additional mandatory checks. The existing image's passive audit expects its
private run directory mounted at `/m5`; the driver supplies this mount and records
read-only native status every ten seconds after second 540. Phase observations do
not change game state. Automatic recovery remains visible as a metric and cannot
supply the fake hunt restart evidence.

## Separate supply and return proof

`m5_current_lowstock.py` deliberately derives a supply-only fixture. It changes the
two potion stacks to one item each and disables all authored hunts **before**
startup. It preserves the parent fixture, world, HP, bank, equipment, spawn, native
code and normal offer/filter implementation. The effective CSV mask, variation
and resulting fixture hash are frozen in `proof-plan.json`.

This empty hunt mask is necessary because the ordinary healthy-idle policy removes
`retreat` when hunting work is available. After the normal NPC purchase reaches
40 potions, no resupply or hunt remains; the unchanged policy can select the
offered retreat. This derivative is not an equivalent-start scored trial or a
model decision quality result.

```sh
PYTHONPATH=src python ../../tests/fixture/m5_current_lowstock.py \
  --fixture-root "$FREEZE" --output "$NEW_SUPPLY_PROOF" \
  --game-image "$PINNED_GAME_IMAGE_ID" --source-revision "$NATIVE_BUILD_REVISION" \
  --maximum-seconds 300
```

The proof requires authoritative purchase and return outcomes, 38 newly purchased
potions, persisted stock of 40, bank debit of 2,014 gold, final position within
three tiles of the temple, no hunts offered, no deaths/gaps/provider requests, and
zero operator interventions or automatic recoveries. Automatic recovery is
disabled and persisted before the first observation. SIGINT/SIGTERM requests a
graceful stop so logs and Compose cleanup still run. The replay retains the
goal-triggered external stop; it is not rewritten into a 30-minute supervisor
completion. `goal-proof.json` additionally requires the pinned runtime binaries
and confirmed cleanup.

A completed timed run and this separate goal proof remain independent gates.
Neither permits provider spending or closes a failed qualification. New native
changes require new long runs and supply proof on the resulting pinned image.
