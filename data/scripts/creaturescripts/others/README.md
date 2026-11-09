# others

## Overview
Package implementation for `data/scripts/creaturescripts/others`, providing component logic and data interfaces for others.

## Interface
- `extendedOpcode.onExtendedOpcode` (`[#extended_opcode.lua:extendedOpcode.onExtendedOpcode]`)
- `creatureEvent.onModalWindow` (`[modal_window_helper.lua:creatureEvent.onModalWindow]`)
- `removeEmptyParcelsEvent.onLogin` (`[remove_empty_parcel.lua:removeEmptyParcelsEvent.onLogin]`)

## Invariants
- None

## Side Effects
- None

## Verification
- Run: `ctest --test-dir build --output-on-failure`
