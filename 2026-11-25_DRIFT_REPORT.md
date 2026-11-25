# EGM Drift Report — 2026-11-25 (Post-Fix Verification)

- **HEAD audited:** `934256f21` (`main`)
- **Comparison baseline:** EGM reconciliation commit `ecc74f039` (2026-11-19) + `docs/design/*.md`
- **Status:** Reconciled `52` drifted `README.md` contracts against `934256f21`, created `13` new EGM `README.md` contracts (`12` untracked + `tools/link-audit/README.md` matched by `.gitignore:427`), and removed `5` orphaned empty-directory `README.md` files left by upstream 15.25 moves (`data-otservbr-global/npc/blue_valley/README.md`, `data/scripts/spells/attack/monk/README.md`, `data/scripts/spells/familiar/monk/README.md`, `data/scripts/spells/healing/monk/README.md`, `data/scripts/spells/support/monk/README.md`). Automated verification across all `599` `README.md` files on disk confirmed `0` non-UTF-8 files, `0` broken relative links, `0` orphaned empty-directory READMEs, `0` missing immediate child `README.md` links, `0` deleted-file mentions, `0` stale local `[file:sym]` references, and `0` undocumented newly added code files.

---

## docs/design/bot-guia-de-thais.md

- Unimplemented draft proposal (`Estado: Rascunho para playtest local`): `/party guia` and `/party guia cancelar` subcommands, session/reservation logic, and the proposed dedicated guide GUID configuration key in `src/config/bot_config_keys.hpp` and `config.lua.dist` are absent from `data/scripts/talkactions/player/bot_party.lua`, `src/creatures/players/bot/`, `src/config/bot_config_keys.hpp`, and `config.lua.dist`.

## docs/design/fixture-persistence-witness.md

- Historical design note pinned to `c8b3878d` (intentionally preserved verbatim): cited line numbers predate subsequent refactoring on `main` (current positions at `934256f21`: `Game::finishNormalShutdown` at `src/game/game.cpp:9689`, `SaveManager::saveFinal` at `src/game/scheduling/save_manager.cpp:163`, `IOLoginData::capturePlayerSave` at `src/io/iologindata.cpp:201`).

## docs/design/native-admission-stage.md

- Historical stage design note pinned to `#72` / `ba3e00a8` (intentionally preserved verbatim): `"Nothing under tests/fixture ... was changed"` predates subsequent offline capture/trace and fixture additions under `tests/fixture/` and `deployment/brain/src/canary_brain/`.

## docs/design/native-admission-validation.md

- Historical stage validation receipt pinned to `stage/72-native-admission` / `3431b404` / `e3657489` (intentionally preserved verbatim): recorded test counts (`65 Python tests`, `35 admission/metadata tests`, `220` distinct Python cases) predate subsequent test additions in `deployment/brain/tests/` and `tests/fixture/`.

## docs/design/native-supervised-harness-interface.md

- No drift detected.

## README.md

- No drift detected.

## cmake/README.md

- No drift detected.

## data-canary/README.md

- No drift detected.

## data-canary/migrations/README.md

- No drift detected.

## data-otservbr-global/README.md

- No drift detected.

## data-otservbr-global/migrations/README.md

- No drift detected.

## data-otservbr-global/npc/README.md

- No drift detected.

## data-otservbr-global/scripts/actions/README.md

- No drift detected.

## data-otservbr-global/scripts/actions/object/README.md

- No drift detected.

## data/libs/gamestore/README.md

- No drift detected.

## data/modules/scripts/README.md

- No drift detected.

## data/modules/scripts/npc/README.md

- No drift detected.

## data/modules/scripts/taskboard/README.md

- No drift detected.

## data/scripts/creaturescripts/bot/README.md

- No drift detected.

## data/scripts/eventcallbacks/README.md

- No drift detected.

## data/scripts/eventcallbacks/creature/README.md

- No drift detected.

## data/scripts/eventcallbacks/player/README.md

- No drift detected.

## data/scripts/lib/README.md

- No drift detected.

## data/scripts/spells/attack/README.md

- No drift detected.

## data/scripts/spells/familiar/README.md

- No drift detected.

## data/scripts/spells/healing/README.md

- No drift detected.

## data/scripts/spells/house/README.md

- No drift detected.

## data/scripts/spells/support/README.md

- No drift detected.

## data/scripts/talkactions/god/README.md

- No drift detected.

## data/scripts/talkactions/player/README.md

- No drift detected.

## database/bots/README.md

- No drift detected.

## deployment/README.md

- No drift detected.

## deployment/brain/README.md

- No drift detected.

## deployment/brain/src/canary_brain/README.md

- No drift detected.

## deployment/web/README.md

- No drift detected.

## deployment/windows/README.md

- No drift detected.

## docker/README.md

- No drift detected.

## docker/quickstart/myaac/README.md

- No drift detected.

## docs/README.md

- No drift detected.

## otclient/README.md

- No drift detected.

## otclient/modules/game_botcontrol/README.md

- No drift detected.

## src/config/README.md

- No drift detected.

## src/creatures/monsters/README.md

- No drift detected.

## src/creatures/players/README.md

- No drift detected.

## src/creatures/players/bot/README.md

- No drift detected.

## src/creatures/players/components/README.md

- No drift detected.

## src/creatures/players/components/pvp/README.md

- No drift detected.

## src/creatures/players/livestream/README.md

- No drift detected.

## src/enums/README.md

- No drift detected.

## src/game/README.md

- No drift detected.

## src/game/bank/README.md

- No drift detected.

## src/game/scheduling/README.md

- No drift detected.

## src/io/README.md

- No drift detected.

## src/lua/README.md

- No drift detected.

## src/lua/docgen/README.md

- No drift detected.

## src/lua/functions/core/game/README.md

- No drift detected.

## src/lua/functions/creatures/player/README.md

- No drift detected.

## src/map/README.md

- No drift detected.

## src/security/README.md

- No drift detected.

## src/server/network/protocol/README.md

- No drift detected.

## src/utils/README.md

- No drift detected.

## tests/fixture/README.md

- No drift detected.

## tests/integration/README.md

- No drift detected.

## tests/lua/README.md

- No drift detected.

## tools/README.md

- No drift detected.

## tools/botctl/README.md

- No drift detected.

## tools/bottest/README.md

- No drift detected.

## tools/bottest/otc_mod/harness_ctl/README.md

- No drift detected.

## tools/canary_audit/README.md

- No drift detected.

## tools/link-audit/README.md

- No drift detected.
