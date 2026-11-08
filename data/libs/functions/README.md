# functions

## Overview
Package implementation for `data/libs/functions`, providing component logic and data interfaces for functions.

## Interface
- `BIT:new` (`[bit.lua:BIT:new]`)
- `NewBit` (`[bit.lua:NewBit]`)
- `hasBitSet` (`[bit.lua:hasBitSet]`)
- `setFlag` (`[bit.lua:setFlag]`)
- `BIT:hasFlag` (`[bit.lua:BIT:hasFlag]`)
- `BIT:updateFlag` (`[bit.lua:BIT:updateFlag]`)
- `BIT:updateNumber` (`[bit.lua:BIT:updateNumber]`)
- `BIT:getNumber` (`[bit.lua:BIT:getNumber]`)
- `testFlag` (`[bitwise_flags.lua:testFlag]`)
- `setFlag` (`[bitwise_flags.lua:setFlag]`)

## Invariants
- None

## Side Effects
- Schedules timed tasks or dispatcher callbacks (`[boss_lever.lua]`)
- Schedules timed tasks or dispatcher callbacks (`[creature.lua]`)
- Executes SQL queries against game database (`[functions.lua]`)
- Schedules timed tasks or dispatcher callbacks (`[functions.lua]`)
- Executes SQL queries against game database (`[game.lua]`)
- Executes SQL queries against game database (`[player.lua]`)

## Verification
- Run: `ctest --test-dir build --output-on-failure`
