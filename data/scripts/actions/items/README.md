# items

## Overview
Package implementation for `data/scripts/actions/items`, providing component logic and data interfaces for items.

## Interface
- `anniversaryBalloons.onUse` (`[anniversary_balloons.lua:anniversaryBalloons.onUse]`)
- `rewardBox.onUse` (`[anniversary_reward_boxes.lua:rewardBox.onUse]`)
- `bananaChocolateShake.onUse` (`[banana_chocolate_shake.lua:bananaChocolateShake.onUse]`)
- `bedModificationKits.onUse` (`[bed_modification_kits.lua:bedModificationKits.onUse]`)
- `bladesparkFigurine.onUse` (`[bladespark_figurine.lua:bladesparkFigurine.onUse]`)
- `blessedSteak.onUse` (`[blessed_steak.lua:blessedSteak.onUse]`)
- `blessingCharms.onUse` (`[blessing_charms.lua:blessingCharms.onUse]`)
- `blueberryBush.onUse` (`[blueberry_bush.lua:blueberryBush.onUse]`)
- `blueberryCupcake.onUse` (`[blueberry_cupcake.lua:blueberryCupcake.onUse]`)
- `carrotCake.onUse` (`[carrot_cake.lua:carrotCake.onUse]`)

## Invariants
- None

## Side Effects
- Schedules timed tasks or dispatcher callbacks (`[exercise_training_weapons.lua]`)
- Schedules timed tasks or dispatcher callbacks (`[magic_gold_converter.lua]`)

## Verification
- Run: `ctest --test-dir build --output-on-failure`
