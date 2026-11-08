# World Map MyAAC Page (`pages`)

## Overview

MyAAC Community page controller (`worldmap.php`) serving both the interactive World Map HTML view (`/index.php/worldmap`) and the cached JSON marker feed (`/index.php/worldmap?data=1`) of online character coordinates.

## Interface

- `[worldmap.php:$_GET['data']]` — `GET /index.php/worldmap?data=1`: JSON endpoint returning `{"t": <timestamp>, "markers": [[name, level, vocation, posx, posy, posz], ...]}` or HTTP 500 `{"t": <timestamp>, "error": "query failed", "markers": []}`.
- `[worldmap.php:$title]` — MyAAC page view `'World Map'` rendering `#worldmap-wrap` HTML and injecting `window.WORLDMAP_CFG` (`dataUrl`, `assets`, `pollMs`, `defaultFloor`, `defaultLayer`, `hasOverview`, `overviewImage`, `layers`, `bounds`, `vocations`).

## Invariants

- `[worldmap.php:MYAAC]` — Requires constant `MYAAC` to be defined or terminates execution with `'Direct access not allowed!'`.
- `[worldmap.php:$wmAccountId]` — Casts `$wmCfg['account_id']` to `int` when non-null before SQL interpolation.
- `[worldmap.php:$markers]` — Marker tuples maintain fixed element order `[name (string), level (int), vocation (int), posx (int), posy (int), posz (int)]` matching `BOT_*` indices in `worldmap.js`.
- `[worldmap.php:$defaultLayer]` — Falls back to `'floors'` when the configured overview image file does not exist under `PLUGINS . 'worldmap/static/'`.

## Side Effects

- `[worldmap.php:ob_end_clean]` — Clears active PHP output buffers and sends `Content-Type: application/json` and `Cache-Control: no-store` headers when `$_GET['data']` is set.
- `[worldmap.php:$cacheFile]` — Reads cached JSON from `CACHE . 'worldmap_data.json'` if age `< $ttl`, and writes fresh JSON payload to `CACHE . 'worldmap_data.json'` with `LOCK_EX` when `$ttl > 0`.
- `[worldmap.php:$db->query]` — Queries `players_online` joined with `players` (optionally filtered by `account_id`) via the global MyAAC `$db` PDO instance.
- `[worldmap.php:setting]` — Reads `'core.vocations'` configuration via MyAAC `setting()` helper and sets global `$title`.

## Verification

- Run: `ctest --test-dir build --output-on-failure`
