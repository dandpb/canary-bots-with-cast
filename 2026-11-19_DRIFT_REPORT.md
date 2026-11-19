# EGM Drift Report — 2026-11-19 (Post-Fix Verification)

- **HEAD audited:** `7348aa678` (`main`)
- **Comparison baseline:** EGM bootstrap commit `28d459899` + `docs/design/*.md`
- **Status:** All 29 drifted `README.md` contracts were reconciled against `7348aa678`, 8 unbootstrapped code directories received new EGM `README.md` contracts, and automated checks verified `0` broken relative links, `0` non-UTF-8 files, and `0` stale symbols/defaults across all `README.md` files.

---

## docs/design/fixture-persistence-witness.md

- Historical design note pinned to `c8b3878d` (intentionally preserved verbatim): line-number citations (`src/server/signals.cpp:65-101`, `src/game/game.cpp:634-704`, `src/game/scheduling/save_manager.cpp:47-108`, `src/io/iologindata.cpp:194`, `src/game/game.cpp:8552`) predate the `f870e22ad` final-save retry flow (`Game::finishNormalShutdown`, `SaveManager::beginFinalSave`/`saveFinal`, and `SIGTERM`/`SIGINT` retry dispatch).

## docs/design/native-admission-stage.md

- Historical stage design note pinned to `#72` / `ba3e00a8` (intentionally preserved verbatim): `"Nothing under tests/fixture ... was changed"` predates subsequent offline capture/trace additions under `tests/fixture/` and `canary_brain` gateway/supervision enhancements.

## docs/design/native-admission-validation.md

- Historical stage validation receipt pinned to `stage/72-native-admission` / `3431b404` / `e3657489` (intentionally preserved verbatim): recorded test counts (`65 Python tests`, `35 admission/metadata tests`) predate later test additions in `deployment/brain/tests/` and `tests/fixture/`.

## docs/design/native-supervised-harness-interface.md

- No drift detected.

## README.md

- No drift detected.

## cmake/modules/README.md

- No drift detected.

## data/README.md

- No drift detected.

## data/scripts/globalevents/README.md

- No drift detected.

## database/bots/README.md

- No drift detected.

## deployment/brain/README.md

- No drift detected.

## deployment/brain/gateway/README.md

- No drift detected.

## deployment/brain/src/canary_brain/README.md

- No drift detected.

## deployment/brain/tools/README.md

- No drift detected.

## deployment/core-qa/README.md

- No drift detected.

## deployment/core-qa/b1/README.md

- No drift detected.

## deployment/web/README.md

- No drift detected.

## deployment/web/voxel-explorer/README.md

- No drift detected.

## deployment/web/voxel-explorer/src/README.md

- No drift detected.

## deployment/web/voxel-explorer/scripts/README.md

- No drift detected.

## deployment/wsl/README.md

- No drift detected.

## docker/README.md

- No drift detected.

## docker/data/README.md

- No drift detected.

## docs/README.md

- No drift detected.

## src/account/README.md

- No drift detected.

## src/creatures/players/README.md

- No drift detected.

## src/creatures/players/bot/README.md

- No drift detected.

## src/creatures/players/cast/README.md

- No drift detected.

## src/creatures/players/components/README.md

- No drift detected.

## src/database/README.md

- No drift detected.

## src/game/README.md

- No drift detected.

## src/game/scheduling/README.md

- No drift detected.

## src/io/README.md

- No drift detected.

## src/items/containers/README.md

- No drift detected.

## src/map/README.md

- No drift detected.

## src/server/README.md

- No drift detected.

## src/server/network/protocol/README.md

- No drift detected.

## tests/README.md

- No drift detected.

## tests/fixture/README.md

- No drift detected.

## tests/integration/README.md

- No drift detected.

## tests/lua/README.md

- No drift detected.

## tools/bot_brain/README.md

- No drift detected.
