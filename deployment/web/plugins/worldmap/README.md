# World Map — MyAAC Plugin (`worldmap`)

## Overview

A live map of where every online character is, exposed as a MyAAC Community subpage (`/index.php/worldmap`). Modelled on AzerothCore's *playermap*: it plots the position columns the server **already persists**, so it adds no telemetry, no schema, and no load on the game server.

- **Overview** layer — the tibia.com library artwork, floor-agnostic: every character plotted by x/y alone.
- **Floors** layer — per-floor minimap renders with a `− 7 +` stepper (`PageUp`/`PageDown`), showing only the characters actually on that floor.

Tested at 500 markers: a full redraw takes ~3–5 ms (canvas renderer, so the poll never rebuilds 500 DOM nodes) and the JSON payload is ~20 KB.

## Interface

- `[config.php:account_id]` / `[config.php:poll_ms]` / `[config.php:cache_ttl]` / `[config.php:default_floor]` / `[config.php:overview_image]` / `[config.php:default_layer]` / `[config.php:layers]` / `[config.php:bounds]` — Plugin configuration array defining account filter (`65000` or `null`), polling interval (`30000` ms), JSON cache TTL (`5` s), default floor (`7`), overview artwork filename (`'map_big.jpg'`), pixel grid origins/dimensions (`'floors'` at `31744, 30976`, `'overview'` at `31616, 30720`), and world coordinate bounds.
- `[install.php:WORLDMAP_MENU_LINK]` / `[install.php:WORLDMAP_MENU_NAME]` / `[install.php:WORLDMAP_MENU_CATEGORY]` — MyAAC plugin installer constants registering the `'World Map'` link (`'worldmap'`) under Community category `3`.
- Subdirectories:
  - [`./pages/README.md`](./pages/README.md) — MyAAC page controller (`[pages/worldmap.php:$_GET['data']]` JSON endpoint `/index.php/worldmap?data=1` and `[pages/worldmap.php:$title]` HTML view).
  - [`./static/README.md`](./static/README.md) — Bundled Leaflet 1.9.4 (`[static/leaflet.js:window.L]`), canvas world map controller (`[static/worldmap.js:window.WORLDMAP_CFG]`, `[static/worldmap.js:window.WORLDMAP_DEBUG]`), and floor tile renders (`static/floors/`).

## Invariants

- `[config.php:MYAAC]` / `[install.php:MYAAC]` — Both `config.php` and `install.php` require constant `MYAAC` to be defined (`defined('MYAAC') or die('Direct access not allowed!')`).
- `[config.php:layers]` — Both `'floors'` and `'overview'` layers share a `1 px = 1 world tile` minimap pixel grid differing only by integer origin offsets (`(31744, 30976)` vs. `(31616, 30720)`).
- `[install.php:Menu::where]` — Installer is idempotent per template: skips insertion if a `MyAAC\Models\Menu` row with `template = $anchor->template` and `link = WORLDMAP_MENU_LINK` (`'worldmap'`) already exists.

## Side Effects

- `[install.php:Menu::increment]` / `[install.php:Menu::create]` — Increments `ordering` on existing `MyAAC\Models\Menu` rows in category `3` after the `'online'` link and inserts a new enabled `'World Map'` menu entry per template.
- `[install.php:warning]` / `[install.php:success]` / `[install.php:error]` — Emits MyAAC admin panel notifications summarizing installed/skipped menu rows or warning when `'online'` anchor or `static/map_big.jpg` is missing.

## Verification

- Run: `ctest --test-dir build --output-on-failure`

---

## Requirements

- MyAAC 1.2+, PHP 8.1+
- A server that persists character positions to `players.posx/posy/posz` while they are online. **This is the one real prerequisite** — stock TFS/Canary only writes those columns on logout and on the (usually hourly or daily) save interval, so on a stock server the dots will be stale by that much. This repository's bot engine persists bot positions every few minutes, which is what makes the page useful here.

## Install

1. Copy `worldmap.json` and the `worldmap/` directory into your MyAAC `plugins/` directory. The manifest basename **must** match the directory name (`worldmap.json` ↔ `worldmap/`) — MyAAC's page auto-discovery globs `plugins/<dir>/pages/*.php` using it.

2. Install it from **admin panel → Plugins**, which runs `install.php` and adds the "World Map" entry to the Community menu. If you copied the files by hand instead, run this once:

   ```sql
   INSERT INTO myaac_menu (template, name, link, blank, color, category, ordering, enabled)
   SELECT template, 'World Map', 'worldmap', blank, color, category, ordering + 1, 1
   FROM myaac_menu WHERE link = 'online' AND category = 3;
   ```

3. **Clear the cache — this is not optional and not just tidiness:**

   ```bash
   rm -rf /var/www/html/system/cache/*
   mkdir -p /var/www/html/system/cache/{persistent,plugins,signatures,twig}
   chown -R www-data:www-data /var/www/html/system/cache
   ```

   MyAAC freezes routes into a FastRoute `route.cache` (unless `env` is `dev`) **and** caches `Plugins::getRoutes()` separately under `plugins_routes`. Clearing only one leaves the page 404ing no matter what you copied.

4. If `cache_engine` is `auto`/`apcu`, the **menu** also lives in APCu, which the CLI cannot reach (`apc.enable_cli = Off`), so `php aac cache:clear` does **not** clear it — and in practice restarting php-fpm did not either. The reliable move is a one-shot file in the webroot, fetched over HTTP and then deleted:

   ```php
   <?php apcu_clear_cache(); opcache_reset(); echo 'ok';
   ```

## The Overview layer (optional)

`static/map_big.jpg` is **not included**: it is CipSoft artwork and is not ours to redistribute. Without it the plugin simply drops the Overview button and opens on Floors — nothing breaks.

To enable it, download `map_big.jpg` from the Tibia library in a **browser** (static.tibia.com sits behind a Cloudflare challenge, so `curl`/`wget` get a 403) and save it to `static/map_big.jpg`. It must be the **2784×2592** version. Hotlinking is not an option — the file is served with `Cross-Origin-Resource-Policy: same-origin`, so browsers refuse to render it cross-origin. Self-host it.

## Configuration

Everything tunable is in [`config.php`](./config.php): which account to plot (`account_id`, `null` = every online character), poll interval, response-cache TTL, default layer and floor, and the layer geometry.

## Geometry, and how to re-verify it

Both layers are the same minimap pixel grid at **1 px = 1 world tile**, differing only by an integer origin:

```
Floors   (tibiamaps floor-NN)  px = worldX - 31744 ,  py = worldY - 30976
Overview (map_big.jpg)         px = worldX - 31616 ,  py = worldY - 30720
```

The (128, 256) delta is `map_big`'s decorative border inset. That was measured, not assumed — registering the artwork against the tibiamaps floor-07 render put 8 temple anchors spread across the map on that offset to within 1 px.

Append **`?calib=1`** to the page URL to pin 12 known temple positions on whichever layer is active. Every pin must land on its town. If one does not, an origin in `config.php` is wrong — there is nothing else it could be. That mode also exposes `window.WORLDMAP_DEBUG` (`map`, `state`, `LAYERS`, `toLatLng`) for scripted checks.

If you swap in different imagery, re-derive the origin as `origin = worldCoordOfTopLeftContentPixel − borderInset` and confirm with `?calib=1`.

## Credits

- Floor imagery: [tibia-map-data](https://github.com/tibiamaps/tibia-map-data) (MIT) by the [tibiamaps.io](https://tibiamaps.io/) project — bundled.
- [Leaflet](https://leafletjs.com) 1.9.4 (BSD-2-Clause) — bundled, unmodified.
- `map_big.jpg`: CipSoft GmbH — **not** bundled.
