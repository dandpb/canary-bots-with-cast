# EGM Drift Report — 2026-11-11

**Target Repository**: `canary-bots-with-cast` (`qa/full-benchmark-stack`)  
**Scope**: Verification of EGM README Contracts against current codebase state.

---

## `README.md` (Root Blueprint)
No drift detected.
- All 9 sub-system boundaries (`src/`, `data/`, `data-canary/`, `data-otservbr-global/`, `database/`, `deployment/`, `docker/`, `docs/`, `tools/`) resolve to existing, verified README contracts.
- Global invariants and verification targets (`cmake --build --preset windows-release` / `ctest`) match repository configurations.

## `tools/README.md`
No drift detected.
- Verified subdirectories and interfaces for `tools/bot_csv` (RFC-4180 CSV writer, offline schema validator, and MySQL importer) and `tools/cfg_importer` (staged OTC cavebot `.cfg` ingestion pipeline).

## `src/creatures/players/bot/README.md`
No drift detected.
- Confirmed ABI interface boundaries (`IBotEngine`, `BotEngineLoader`, `BotReloadSnapshot`) and implementation files (`bot_engine.cpp`, `bot_tick.cpp`, `bot_combat.cpp`, `bot_nav.cpp`, `bot_zgraph.cpp`, `bot_brain.cpp`).
- Confirmed thread constraints (single serial dispatcher thread) and persistence mechanisms.

## `src/creatures/players/cast/README.md`
No drift detected.
- Confirmed `CastViewerSink` pure abstract interface in `src/creatures/players/cast/cast_viewer_sink.hpp` and decoupled player broadcast routing.

## `database/bots/README.md`
No drift detected.
- Confirmed SQL dumps (00 through 16) and `import.sh` dependency order for the 997 bot population and `@god` account.

---

### Verification Summary
- **Total Contracts Audited**: 10+ leaf and blueprint README contracts.
- **Broken Relative Links Resolved**: 1 (`tools/README.md` generated and linked).
- **Code Symbol Grounding**: 100% verified against actual C++23 source, CMake targets, and Lua datapack scripts.
