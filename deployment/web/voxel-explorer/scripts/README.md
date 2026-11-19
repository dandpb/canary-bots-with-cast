# Voxel Explorer Build & Map Scripts (`deployment/web/voxel-explorer/scripts`)

## Overview
Provides offline map-extraction and place-validation CLI scripts used to regenerate the 16-floor Thais voxel map slice and verify scene/data integrity during builds.

## Interface
- `[check-place.mjs]` — Node.js validation script (`npm run check`) invoking `validatePlace` against `src/thais.json` and place definitions.
- `[crop-thais.py]` — Python/Pillow utility extracting the `80x80` Thais tile bounding box (`X 32329..32408`, `Y 32201..32280`) across all 16 World Map floor PNGs and recording source file hashes into `src/thais.json`.

## Invariants
- `check-place.mjs` exits non-zero if any floor slice, POI anchor, or coordinate constraint fails validation (`[check-place.mjs]`).
- `crop-thais.py` preserves exact 1 px = 1 tile alignment across all 16 floors (`0..15`) (`[crop-thais.py]`).

## Side Effects
- `crop-thais.py` writes cropped PNG slices into `public/data/` and updates `src/thais.json`.

## Verification
- Run: `node deployment/web/voxel-explorer/scripts/check-place.mjs`
