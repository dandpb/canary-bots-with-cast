# Existing runtime schema and ARM64 deployment

The native engine already reads/writes `bot_state_persistence`,
`bot_startup_config` and `bot_nav_events`, but the shipped bot schema omits their
definitions. `database/bots/16_runtime_compatibility.sql` backfills those existing
contracts. It also widens charm totals to the engine's unsigned 32-bit fields and
online time beyond signed INT. It introduces no new runtime persistence feature.

From the repository root, apply the repair after the ordinary schema/import and
before starting the game. Existing installations can apply it again; rows are
retained. Apply it while the game is stopped because ALTER TABLE acquires locks.
The normal `database/bots/import.sh` also includes the repair for fresh installs.

```sh
mariadb --defaults-extra-file=/protected/database.cnf canary < database/bots/16_runtime_compatibility.sql
```

Fresh schema definitions and migration 50 use the same charm widths, so migration
does not narrow seeded high-level bot totals back to SMALLINT. The compatibility
script remains necessary for existing runtime tables and already-created databases.

`compose.arm64.example.yml` mirrors the deployed topology: native MariaDB and the
matching AMD64 game/engine release under QEMU. Prepare the release binary and its
runtime files in the repository root, install/enable the host's AMD64 binfmt
handler, and configure `config.lua` with database host `database`, database/user
`canary`, and the password from your protected environment file. That file supplies
`MARIADB_ROOT_PASSWORD` and `MARIADB_PASSWORD`; it is not part of the repository.

```sh
CANARY_DATABASE_ENV_FILE=/protected/database.env docker compose -f deployment/compose.arm64.example.yml config --quiet
CANARY_DATABASE_ENV_FILE=/protected/database.env docker compose -f deployment/compose.arm64.example.yml up -d
```

Ports bind to loopback by default; configure `CANARY_BIND_IP` for an intended
interface. Configure the advertised game address separately in `config.lua`.
This example does not build the server or establish native ARM64 compatibility.

Opt-in regression against an existing disposable MariaDB container:

```sh
python3 tests/bot_installation_test.py --container your-mariadb-test-container
```

The test creates a uniquely named database, reproduces the original overflows,
applies the repair twice, verifies stored runtime rows and removes its database.
It never selects the production database.
