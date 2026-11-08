# World Map Static Frontend Assets (`static`)

## Overview

Static frontend assets for the MyAAC World Map plugin, containing the bundled Leaflet 1.9.4 library (`leaflet.js`, `leaflet.css`), the canvas-based world map controller (`worldmap.js`, `worldmap.css`), and per-floor minimap tile renders (`floors/floor-00.png` through `floors/floor-15.png`).

## Interface

- `[leaflet.js:window.L]` — Leaflet 1.9.4 UMD library export exposing `L.Map`/`L.map`, `L.CRS.Simple`, `L.Canvas`/`L.canvas`, `L.LayerGroup`/`L.layerGroup`, `L.ImageOverlay`/`L.imageOverlay`, `L.CircleMarker`/`L.circleMarker`, `L.LatLngBounds`/`L.latLngBounds`, `L.Tooltip`/`L.tooltip`, and `L.Popup`/`L.popup`.
- `[worldmap.js:window.WORLDMAP_CFG]` — Consumed global configuration object injected by `pages/worldmap.php` (`assets`, `pollMs`, `vocations`, `bounds`, `hasOverview`, `overviewImage`, `layers`, `defaultLayer`, `defaultFloor`, `dataUrl`).
- `[worldmap.js:window.WORLDMAP_DEBUG]` — Conditionally exposed debug object `{ map, state, LAYERS, toLatLng }` when the URL query string matches `/[?&]calib=1/` (`[worldmap.js:CALIB]`).

## Invariants

- `[worldmap.js:BOT_NAME,BOT_LEVEL,BOT_VOC,BOT_X,BOT_Y,BOT_Z]` — Compact marker tuple indices are fixed as `0` (name), `1` (level), `2` (vocation ID), `3` (x), `4` (y), `5` (z), matching `worldmap.php`'s `$markers` payload order.
- `[worldmap.js:BOUNDS]` — World coordinate bounds default to `{ minx: 31744, maxx: 34303, miny: 30976, maxy: 33023 }`; markers outside `inWorld(wx, wy)` are excluded from rendering and counted in `state.counts.offMap`.
- `[worldmap.js:toLatLng]` — World coordinates `(wx, wy)` map to `L.CRS.Simple` `[lat, lng]` as `[-(wy - L_.oy), wx - L_.ox]` at `1 px = 1 world tile`.
- `[worldmap.js:setFloor]` — Floor number `state.floor` is clamped to the inclusive range `[0, 15]`, where `'up'` decreases `z` toward `0` and `'down'` increases `z`.
- `[worldmap.js:LAYERS]` — `LAYERS.overview.keep` returns `true` for all floors, whereas `LAYERS.floors.keep` requires `bot[BOT_Z] === floor`; bots failing `keep` are counted in `state.counts.otherFloor`.
- `[worldmap.js:fetchData]` — On fetch failure, `state.bots` is preserved on screen (`state.failed = true`) rather than clearing existing markers.

## Side Effects

- `[leaflet.js:window.L]` — Assigns `window.L` and registers DOM/window listeners when map instances are initialized.
- `[worldmap.js:map]` — Initializes a Leaflet map instance on `#worldmap` with canvas renderer (`L.canvas({ padding: 0.5 })`), marker/calibration layer groups, and image overlays.
- `[worldmap.js:el]` — Mutates DOM elements `#wm-status`, `#wm-floorbox`, `#wm-floor-label`, and `.wm-layer` buttons, and binds click/keydown (`PageUp`/`PageDown`) listeners.
- `[worldmap.js:fetchData]` — Performs immediate and periodic (`setInterval` every `POLL_MS`, default `30000` ms) HTTP `GET` requests to `CFG.dataUrl`, plus a `15000` ms relative-time status timer.
- `[worldmap.js:window.WORLDMAP_DEBUG]` — Renders 12 known temple calibration pins (`[worldmap.js:TEMPLES]`, `[worldmap.js:drawCalibration]`) and sets `window.WORLDMAP_DEBUG` when `?calib=1` is present.

## Verification

- Run: `ctest --test-dir build --output-on-failure`
