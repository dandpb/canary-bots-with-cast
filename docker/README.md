# Docker Configuration & Container Definitions (`docker`)

## Overview
Contains Dockerfiles (`Dockerfile.x86`, `Dockerfile.arm`, `Dockerfile.dev`), `docker-compose.yml`, the Lua configuration mutator script (`config.sh`), and container startup/seed scripts (`./data`).

## Interface
- `[config.sh:substitute_lua_variable]` — `substitute_lua_variable(variable_name, new_value)` rewrites `variable_name = ...` assignments in `$lua_file` (preserving unquoted booleans/integers and quoting strings).
- `[config.sh:get_named_arg]` — `get_named_arg(arg_name, "$@")` extracts `--file` (default `"config.lua"`) and `--env` (default `".env"`) CLI arguments.
- `[config.sh:verify_file]` — `verify_file(path, label)` verifies that the target `.env` and `.lua` files exist before processing.
- Environment key mappings (`[config.sh:59]`): maps `MYSQL_HOST` -> `mysqlHost`, `MYSQL_DBNAME` -> `mysqlDatabase`, `MYSQL_USER` -> `mysqlUser`, `MYSQL_PASS` -> `mysqlPass`, `SERVER_NAME` -> `serverName`, `SERVER_IP` -> `ip`, `SERVER_PORT` -> `gameProtocolPort`, and passes through any other non-comment key in `$env_file` or positional key/value pairs (`[config.sh:89]`).
- Subdirectories:
  - `data`: [`./data/README.md`](./data/README.md) — Container startup entrypoint (`start.sh`) and test account/player SQL seeds.
- Additional documentation: [`./DOCKER.md`](./DOCKER.md).

## Invariants
- `[config.sh:45]` exits with code `1` if either `$env_file` (default `.env`) or `$lua_file` (default `config.lua`) does not exist on disk.
- `[config.sh:89]` expects positional overrides as alternating `variable_name` `new_value` pairs.

## Side Effects
- `[config.sh:12]` writes `$lua_file.tmp` and overwrites `$lua_file` via `mv` for every variable read from `$env_file` and positional CLI arguments.

## Verification
- Run: `ctest --test-dir build --output-on-failure`
