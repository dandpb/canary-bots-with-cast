# Tools Subsystem (`tools`)

## Overview
Groups offline developer tools, data pipeline scripts, build-cache/recompilation checks, fork-delta guards, Lua API quality/doc checks, OTClient bot test harnesses, and profile-aware content auditors.

## Interface
- `check_lua_api_binding_docs.py` (`[check_lua_api_binding_docs.py]`): Validates Lua API binding documentation coverage against `docs/lua-api/lua_api.json`.
- `check_lua_api_quality.py` (`[check_lua_api_quality.py]`): Enforces Lua API parameter/return quality metrics against `docs/lua-api/lua_api_quality_baseline.json`.
- `configure_shared_build_cache.ps1` / `configure_shared_solution_cache.ps1`: Windows PowerShell scripts configuring and auditing shared CMake/MSBuild vcpkg build caches.
- `fork_delta_check.sh`: Fork durability guard enforcing zero fork-owned files in `data-otservbr-global/migrations/` and complete `FORK_DELTA.md` coverage against upstream.
- `setup_vscode_lua_api.ps1`: Configures `.vscode/settings.json` and `.luarc.json` to point LuaLS at `docs/lua-api`.
- `test_recompile.py`: Exercises `recompile.sh` with temporary ELF fixtures without compiling Canary or restarting services.
- `test_shared_cache_identity.py`: Exercises `cmake/SharedBuildCache.cmake` and `vcproj/SharedVcpkgCache.targets` in read-only CMake script mode.

## Subdirectories & Boundaries
- `bot_brain`: [`./bot_brain/README.md`](./bot_brain/README.md) - Bot startup, navigation and lifecycle regression harnesses.
- `bot_csv`: [`./bot_csv/README.md`](./bot_csv/README.md) - Canonical RFC-4180 CSV writer, cross-file offline schema validator, and MySQL scratch importer for authored bot datasets.
- `bot_population_generator`: [`./bot_population_generator/README.md`](./bot_population_generator/README.md) - Population and seed-data generation.
- `botctl`: [`./botctl/README.md`](./botctl/README.md) - Synchronous CLI wrapper inserting and polling `/cavebot` commands via `bot_commands`.
- `bottest`: [`./bottest/README.md`](./bottest/README.md) - Headless OTClient player & `@cast` camera test harness, WebSocket hub, server audit merger, and perception parity suite.
- `canary_audit`: [`./canary_audit/README.md`](./canary_audit/README.md) - Profile-aware Canary content reference auditor and schema validator.
- `cfg_importer`: [`./cfg_importer/README.md`](./cfg_importer/README.md) - Staged ingestion pipeline converting OTClient cavebot 1.3 `.cfg` hunt configs and metadata into authored CSV datasets.
- `link-audit`: [`./link-audit/README.md`](./link-audit/README.md) - Windows PowerShell link-audit evidence extractor (`extract-link-audit-evidence.ps1`).

## Verification
- Use the verification commands in each tool's guide, or run `python tools/test_recompile.py` and `python tools/test_shared_cache_identity.py` from the repository root.
