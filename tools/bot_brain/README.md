# Bot Brain QA & Lifecycle Harness (`tools/bot_brain`)

## Overview
Provides a disposable Docker-isolated Canary + MariaDB stack (`lifecycle_qa.py`) and accompanying regression suites for testing bot brain lifecycle behavior, `/cavebot reload` state preservation, route tracing, planner exhaustion, and persistence contracts without mutating external or production environments.

## Interface
- `[lifecycle_qa.py:PREFIX]` — Container/network naming prefix constant (`"canary-lifecycle-qa"`).
- `[lifecycle_qa.py:docker]` — `docker(*args, input=None, check=True)` subprocess wrapper for executing `docker` CLI commands.
- `[lifecycle_qa.py:verify]` — `verify(name)` guard asserting container name starts with `PREFIX` and carries label `canary.qa=lifecycle`.
- `[lifecycle_qa.py:seed_human]` — `seed_human()` seeds disposable human QA account/character `64999` (`Lifecycle Human`) in `canary-lifecycle-qa-db` during `create()`.
- `[lifecycle_qa.py:command]` — `command(action, **values)` writes `qa-command.lua` into `canary-lifecycle-qa-game` and polls `/canary/qa-result.json` (up to 60s) for command completion.
- `[lifecycle_qa.py:create]` — `create(world, build)` provisions the internal Docker network (`canary-lifecycle-qa`), disposable MariaDB 11.4 container (`canary-lifecycle-qa-db`), and game container (`canary-lifecycle-qa-game`) from a QA build container.
- CLI flags (`[lifecycle_qa.py:__main__]`): `--create`, `--world`, `--build` (default `"canary-state-qa-build"`), `--action`, `--values` (JSON string).
- Regression suites: `test_accepted_navigation_reset.py`, `test_cast_lifecycle.py`, `test_checkpoint_deadlock_db.py`, `test_checkpoint_overlap.py`, `test_checkpoint_retry.py`, `test_direct_trace.py`, `test_door_search.py`, `test_engine_loader.py`, `test_exhausted_planner.py`, `test_floor_guard.py`, `test_lifecycle_import_safety.py`, `test_movement.py`, `test_navigation_objective.py`, `test_online_time.cpp`, `test_planned_portal.py`, `test_planner_progress.py`, `test_player_commands.lua`, `test_reload*.lua`, `test_reload_progress.py`, `test_reload_quests.py`, `test_startup_batches.lua`, `test_stateful_reload.py`, and `test_telemetry_delivery.py`.
- Related reference documentation: [`./README.reload.md`](./README.reload.md), [`./README.route-direct.md`](./README.route-direct.md).

## Invariants
- `[lifecycle_qa.py:verify]` refuses to mutate or exec into any container whose name does not start with `canary-lifecycle-qa` or whose `canary.qa` Docker label is not `"lifecycle"`.
- `[lifecycle_qa.py:create]` requires `build` container name to start with `"canary-state-qa"`, `"canary-reload-"`, or `"canary-cast-"`, and `--create` requires `--world` to point to an existing `.otbm` file (`[lifecycle_qa.py:__main__]`).
- `[lifecycle_qa.py:command]` requires all command payload values to be `str`, `int`, or `bool` before serializing the Lua table (`qa-command.lua`), and asserts `canary-lifecycle-qa-game` remains running while awaiting `/canary/qa-result.json`.
- `[lifecycle_qa.py:create]` decodes `database/bots/02_players.sql` as `latin1` to preserve raw binary player attributes when extracting seed rows for player GUIDs `65001`, `65003`, and `65004`.

## Side Effects
- `[lifecycle_qa.py:create]` writes temporary initialization SQL and entrypoint scripts under `/tmp/canary-lifecycle-qa` (`initdb/000_schema.sql` through `004_players.sql`, `entry.py`, `adapter.lua`) and copies `canary` and `libbot_engine.so` from the build container.
- `[lifecycle_qa.py:create]` creates an internal Docker network (`canary-lifecycle-qa`) and launches containers `canary-lifecycle-qa-db` (`mariadb:11.4`) and `canary-lifecycle-qa-game` (`canary-bots-wsl-game:local`).
- `[lifecycle_qa.py:command]` atomically writes `qa-command.tmp` and renames it to `qa-command.lua` inside the `canary-lifecycle-qa-game` container, triggering `GlobalEvent("CanaryLifecycleQA")` to write `qa-result.json`.

## Verification
- Run the [standalone Lua startup tests](../../tests/lua/README.md#verification)
  and the [Brain worker checks](../../deployment/brain/README.md#verification).
