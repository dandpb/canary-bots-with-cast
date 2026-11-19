# Voxel Explorer Frontend Source (`deployment/web/voxel-explorer/src`)

## Overview
Implements the client-side Thais Voxel Explorer application: district tile/POI data loading (`thais.json`), procedural voxel geometry construction (`architecture.js`, `voxel-kit.js`), Three.js WebGL and Canvas 2D fallback rendering (`main.js`, `software-renderer.js`), camera/walk navigation (`navigation.js`), and place integrity validation (`place.js`, `place-validation.js`).

## Interface
- `[main.js]` — Application entrypoint wiring URL parameters (`?andar=`, `?render=software`), UI controls (Passeio, Diorama, Caminhar, Andar, Mapa), and render loop.
- `[district.js:tiles]`, `[district.js:width]`, `[district.js:scale]`, `[district.js:local]`, `[district.js:indexOf]`, `[district.js:read]`, `[district.js:walkable]`, `[district.js:palette]`, `[district.js:random]`, `[district.js:strips]` — Coordinate projection and walkability/tile helpers over `[thais.json]`.
- `[architecture.js:buildDistrict]` / `[voxel-kit.js:createVoxelKit]` — Procedural voxel geometry and material builders for Thais buildings, streets, depot, and temple.
- `[place.js:createPlace]` / `[place-validation.js:validatePlace]` — Place definition factory and structural/coordinate validator.
- `[navigation.js:createNavigation]` — Guided tour, diorama orbit, and first-person walk controller.
- `[software-renderer.js:SoftwareRenderer]` — Canvas 2D software renderer fallback reproducing the same district geometry without WebGL.
- `[style.css]` / `[atlas.css]` / `fonts/` — UI styles and bundled `DM Sans` / `Gloock` WOFF2 typography.

## Invariants
- `validatePlace` verifies floor bounds (`0..15`), coordinate mapping (`X 32329..32408`, `Y 32201..32280`), and POI alignment against `thais.json` (`[place-validation.js:validatePlace]`).
- `SoftwareRenderer` consumes the same scene geometry and camera coordinates as the WebGL path (`[software-renderer.js:SoftwareRenderer]`).

## Side Effects
- Mutates browser DOM, WebGL/2D canvas contexts, and URL query/history state during interactive exploration (`[main.js]`).

## Verification
- Run: `npm --prefix deployment/web/voxel-explorer run check`
