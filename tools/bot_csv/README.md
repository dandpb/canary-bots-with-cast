# Bot Authored CSV Tooling (`tools/bot_csv`)

## Overview
Provides the canonical RFC-4180 CSV writer (`csv_common.py`), offline schema and cross-file validator (`validate.py`), and MySQL scratch/rollback importer (`import_to_mysql.py`) for the `data/bot/authored/` bot dataset.

## Interface
- `[csv_common.py:AUTHORED_DIR]` — Target directory resolved from `$BOT_AUTHORED_DIR` or default `"data/bot/authored"`.
- `[csv_common.py:announce_authored_dir]` — `announce_authored_dir(tool_name)` prints the overridden `AUTHORED_DIR` when `$BOT_AUTHORED_DIR` is set.
- `[csv_common.py:csv_field]`, `[csv_common.py:csv_row]`, `[csv_common.py:write_csv]` — `write_csv(path, header, rows, banners=None)` writes UTF-8 LF CSV files atomically with quoting matching `botCsvField()` in `src/creatures/players/bot/bot_csv.cpp`.
- `[validate.py:WAYPOINT_TYPES]`, `[validate.py:PHASES]`, `[validate.py:POI_TYPES]` — Allowed enum sets and canonical phase order (`["travel_to", "hunt_patrol", "travel_from"]`).
- `[validate.py:CsvError]`, `[validate.py:lex]`, `[validate.py:Table]`, `[validate.py:validate]`, `[validate.py:main]` — Offline CSV lexer, typed table parser (`raw`, `line`, `num`, `num_or`, `enum`), and cross-file validator.
- `[import_to_mysql.py:SCHEMA]`, `[import_to_mysql.py:ORDER]` — MySQL DDL and dependency order for `bot_hunt_scripts`, `bot_hunt_waypoints`, `bot_hunt_targets`, `bot_city_routes`, `bot_city_route_waypoints`, `bot_city_pois`, `bot_equipment`, `travel_positions`, and `bot_town_mapping`.
- `[import_to_mysql.py:load_all]`, `[import_to_mysql.py:main]` — Loads authored CSVs into MySQL (`--host`, `--user`, `--password`, `--db`, `--create`, `--i-mean-it`).

## Invariants
- `[csv_common.py:csv_field]` quotes a field (doubling internal `"`) iff it contains `,`, `"`, `\r`, or `\n`, has leading/trailing space or tab, or begins with `#`.
- `[validate.py:lex]` and `[validate.py:Table]` reject empty files, `;`- or `\t`-delimited headers, duplicate or unrecognized columns (unless prefixed with `_`), missing required columns, mismatched row field counts, and out-of-range integers or enums.
- `[validate.py:validate]` enforces that `meta.csv` defines `format_version` and `next_script_id`, every `hunt_scripts.csv` `id < next_script_id` has a 1-to-1 `hunt_waypoints/<id>.csv` file with contiguous phases in canonical order (`travel_to` -> `hunt_patrol` -> `travel_from`), every `hunt_targets.csv` `script_id` exists in `hunt_scripts.csv`, every `city_route_waypoints/town_<id>.csv` group matches a `(town_id, source_name)` row in `city_routes.csv` with contiguous `source_name` blocks, and `(town_id, name)` in `city_pois.csv`, `(level, vocation)` in `equipment.csv`, and `lower(source_name)` in `town_mapping.csv` are unique.
- `[import_to_mysql.py:main]` refuses to write to `--db canary` (exiting with status `2`) unless `--i-mean-it` is explicitly supplied, and wraps all table deletes and inserts in a single transaction that rolls back on `CsvError` or `mysql.connector.Error`.

## Side Effects
- `[csv_common.py:write_csv]` creates parent directories (`os.makedirs`), writes `<path>.tmp`, and atomically replaces `<path>` via `os.replace`.
- `[validate.py:validate]` reads all CSV files under `AUTHORED_DIR` (`meta.csv`, `hunt_scripts.csv`, `hunt_waypoints/*.csv`, `hunt_targets.csv`, `city_routes.csv`, `city_route_waypoints/*.csv`, `city_pois.csv`, `equipment.csv`, `town_mapping.csv`, `travel_positions.csv`).
- `[import_to_mysql.py:main]` connects to MySQL, optionally executes `CREATE TABLE IF NOT EXISTS` (`--create`), deletes existing rows from the 9 tables in `ORDER`, and bulk-inserts rows parsed from `AUTHORED_DIR`.

## Verification
- Run: `ctest --test-dir build --output-on-failure`
