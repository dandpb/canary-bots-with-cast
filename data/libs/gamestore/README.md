# gamestore

## Overview
Package implementation for `data/libs/gamestore`, providing component logic and data interfaces for gamestore.

## Interface
- `helpers.convertType` (`[helpers.lua:helpers.convertType]`)
- `helpers.useOfferConfigure` (`[helpers.lua:helpers.useOfferConfigure]`)

## Invariants
- None

## Side Effects
- Executes SQL queries against game database (`[parsers.lua]`)
- Executes SQL queries against game database (`[store.lua]`)

## Verification
- Run: `ctest --test-dir build --output-on-failure`
