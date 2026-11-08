# OTC Cavebot Config Importer (`tools/cfg_importer`)

## Overview
Converts OTClient cavebot 1.3 `.cfg` hunt files and `cfg_manifest.csv` metadata into the authored CSV dataset (`data/bot/authored/`) using a staged validation pipeline.

## Interface
- `[convert_cfg.py:parse_cfg]` — `parse_cfg(filepath: Path)` parses `.cfg` directives (`label:level`, `label:monsters`, `label:TELEPORT`, phase labels, `goto:`, `use:`, `usewith:`, `npc:`, `TELEPORT:`, `function:`) into `(min_level, monsters, steps, stand_hints)`.
- `[convert_cfg.py:to_waypoints]` — `to_waypoints(steps, stand_hints=None)` converts raw steps into phase-tagged waypoints (`travel_to`, `hunt_patrol`, `travel_from`), deduplicates consecutive identical steps, promotes large Chebyshev gaps (`> TELEPORT_GAP_THRESHOLD`) to `teleport`, and promotes pre-interaction/floor-change nodes to `stand`.
- `[convert_cfg.py:classify_cfg]` — `classify_cfg(path)` classifies a `.cfg` file as `'hunt'`, `'city_route'`, or `'poi'`.
- `[convert_cfg.py:AuthoredTree]` — In-memory loader and writer for `hunt_scripts.csv`, `hunt_targets.csv`, `hunt_waypoints/<id>.csv`, and `meta.csv`.
- `[convert_cfg.py:load_manifest]`, `[convert_cfg.py:save_manifest]`, `[convert_cfg.py:manifest_defaults]` — Readers/writers for `tools/cfg_importer/cfg_manifest.csv`.
- `[convert_cfg.py:load_anchor_pois]`, `[convert_cfg.py:infer_town]` — Infers `town_id` by finding the nearest enabled anchor POI (`temple`, `depot`, `depot_outside`, `boat`) in `city_pois.csv`.
- `[convert_cfg.py:check_waypoints]`, `[convert_cfg.py:check_row_coherence]`, `[convert_cfg.py:run_validator]`, `[convert_cfg.py:ingest]`, `[convert_cfg.py:write_tree]`, `[convert_cfg.py:main]` — Staged ingestion pipeline and CLI entry point (`cfgs`, `--cfg-dir`, `--only`, `--regenerate`, `--dry-run`).
- `[convert_cfg.py:IngestError]` — Exception raised on fatal `.cfg` classification, town anchor distance, level label, or coherence violations.

## Invariants
- `[convert_cfg.py:classify_cfg]` and `[convert_cfg.py:ingest]` reject any `.cfg` that is not classified as `'hunt'` (`city_route` or `poi` configs are refused before copying or writing).
- `[convert_cfg.py:infer_town]` and `[convert_cfg.py:ingest]` require inferred town anchors for new scripts to be within `TOWN_ANCHOR_MAX_DIST` (`150` tiles Chebyshev distance) of the starting waypoint, and `[convert_cfg.py:has_level_label]` requires an explicit `label:level:` directive so new scripts never default to `min_level=1` uncapped.
- `[convert_cfg.py:check_waypoints]` enforces that all waypoint types belong to `WAYPOINT_TYPES` (16 valid types) and that `hunt`/`quest` scripts have at least one `hunt_patrol` waypoint (`traveling` scripts must have `travel_to` waypoints).
- `[convert_cfg.py:check_row_coherence]` enforces `(script_category == "quest") == (is_quest == "1")` and uniqueness of `lower(name)` across all scripts in `hunt_scripts.csv`.
- `[convert_cfg.py:write_tree]` stages all modifications in a temporary copy of `data/bot/authored/` and runs `tools/bot_csv/validate.py` in a subprocess (`BOT_AUTHORED_DIR`); no live CSV files or `cfg_manifest.csv` are modified unless validation passes.
- Scripts with `skip_reimport == "1"` in `cfg_manifest.csv` sync metadata rows in `hunt_scripts.csv` while keeping their on-disk `hunt_waypoints/<id>.csv` frozen (`[convert_cfg.py:ingest]`).

## Side Effects
- `[convert_cfg.py:write_tree]` creates and cleans up a temporary staging directory (`tempfile.mkdtemp(prefix="botcsv_")`), spawns `tools/bot_csv/validate.py`, and copies changed `.csv` files into `data/bot/authored/` (`hunt_scripts.csv`, `hunt_targets.csv`, `meta.csv`, `hunt_waypoints/<id>.csv`).
- `[convert_cfg.py:save_manifest]` rewrites `tools/cfg_importer/cfg_manifest.csv` via `csv_common.write_csv`.
- `[convert_cfg.py:main]` copies newly dropped `.cfg` files into `tools/cfg_importer/cfg/` after a successful non-dry-run import.

## Verification
- Run: `ctest --test-dir build --output-on-failure`
