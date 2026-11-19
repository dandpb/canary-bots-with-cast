# Core-QA B1 Playtest Fixture Assets (`deployment/core-qa/b1`)

## Overview
Stores the SQL seeds, brain server configuration, and Lua market no-op overrides consumed by `deployment/core-qa/b1_fixture.py` when provisioning the isolated `canary-qa-b1` companion playtest stack (`CORE_QA_PROFILE=b1`).

## Interface
- `[server.json]` — Canary Brain server config selecting pilot bots `[65001, 65004, 65003]` in `active` mode with `autonomous_bot: 0` (party-only) and socket directory `/var/lib/canary-human-qa-stage2/socket`.
- `[seed-companions.sql]` — Deterministic seed state for the three companion pilots (`65001`, `65004`, `65003`).
- `[leader-prep.sql.template]` — Parameterized SQL template preparing the human party leader character for B1 playtests.
- `[slice.sql]` — Read-only database snapshot query used by `b1_fixture.py` to hash and verify fixture state.
- `[bot_market.lua]` / `[bot_market_funding.lua]` — No-op Lua globalevent overrides mounted during B1 runs to suppress background market mutations.

## Invariants
- `server.json` keeps `autonomous_bot: 0` so companions accept party objectives without running autonomous solo exploration (`[server.json]`).
- Assets in this directory are strictly isolated to `CORE_QA_PROFILE=b1` (`canary-qa-b1`) and never mutate `canary-core-qa` stage-1 baselines (`[../b1_fixture.py:require_b1]`).

## Side Effects
- Mounted or copied into `runtime/b1/initdb/` and container script overlays by `deployment/core-qa/b1_fixture.py` during B1 stack setup.

## Verification
- Run: `pytest deployment/core-qa/test_b1_fixture.py deployment/core-qa/test_b1_profile.py`
