# gamestore

## Overview
Package implementation for `data/modules/scripts/gamestore`, providing component logic and data interfaces for gamestore.

## Interface
- `loader.registerOffer` (`[catalog_loader.lua:loader.registerOffer]`)
- `loader.registerCategory` (`[catalog_loader.lua:loader.registerCategory]`)
- `loader.getCategories` (`[catalog_loader.lua:loader.getCategories]`)
- `onRecvbyte` (`[init.lua:onRecvbyte]`)
- Subdirectory [`./catalog/README.md`](./catalog/README.md) - Sub-package for catalog

## Invariants
- None

## Side Effects
- None

## Verification
- Run: `ctest --test-dir build --output-on-failure`
