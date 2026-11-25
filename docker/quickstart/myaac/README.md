# Quickstart MyAAC Container (`docker/quickstart/myaac`)

## Overview
Builds and initializes the standalone MyAAC (`slawkens/myaac` `2.x`) website/admin container for the Docker quickstart stack (`docker/compose.quickstart.yml`), keeping website/admin concerns separated from the `login-server` client login path.

## Interface
- `Dockerfile`: Two-stage `php:8.3-apache` image that downloads `slawkens/myaac` (`MYAAC_REF=2.x`), installs Composer/npm assets, removes `login.php` (forcing client logins through `login-server` instead of MyAAC), and installs `myaac-entrypoint` and `myaac-bootstrap.php` (`[Dockerfile]`).
- `entrypoint.sh` (`[entrypoint.sh:escape_lua]`, `[entrypoint.sh:require_uint]`): Validates numeric `CANARY_*` ports/timeouts, renders `/canary/config.lua`, `/canary/data/XML/vocations.xml`, and `/canary/data/XML/groups.xml`, invokes `php /usr/local/bin/myaac-bootstrap.php`, and launches Apache (`exec "$@"`).
- `bootstrap.php` (`[bootstrap.php:wait_for_database]`, `[bootstrap.php:wait_for_canary_schema]`): Waits up to 90 attempts for MariaDB and Canary's `accounts`/`players` tables, ensures required schema columns exist, and configures `config.local.php`.

## Invariants
- `Dockerfile` explicitly deletes `login.php` (`rm -f login.php`) so MyAAC remains website/admin-only while clients authenticate through `login-server` (`[Dockerfile]`).
- `entrypoint.sh` validates `CANARY_DB_PORT`, `CANARY_LOGIN_PORT`, `CANARY_GAME_PORT`, `CANARY_STATUS_PORT`, and `CANARY_STATUS_TIMEOUT` as unsigned integers and escapes Lua string literals (`[entrypoint.sh:require_uint]`, `[entrypoint.sh:escape_lua]`).

## Side Effects
- Downloads upstream MyAAC archives during image build, writes `/canary/config.lua` and XML stub files at container start, and alters/seeds MyAAC database tables and `/var/www/html/config.local.php` (`[Dockerfile]`, `[entrypoint.sh]`, `[bootstrap.php]`).

## Verification
- See [`../../DOCKER.md`](../../DOCKER.md#validate-the-compose-file) for Compose validation and quickstart checks.
