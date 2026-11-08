# party

## Overview
Package implementation for `data/scripts/eventcallbacks/party`, providing component logic and data interfaces for party.

## Interface
- `callback.partyOnDisband` (`[on_disband.lua:callback.partyOnDisband]`)

## Invariants
- None

## Side Effects
- Schedules timed tasks or dispatcher callbacks (`[on_disband.lua]`)

## Verification
- Run: `ctest --test-dir build --output-on-failure`
