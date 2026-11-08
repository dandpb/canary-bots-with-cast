# objects

## Overview
Package implementation for `data/scripts/actions/objects`, providing component logic and data interfaces for objects.

## Interface
- `bathtubDrain.onUse` (`[bath_tub_drain.lua:bathtubDrain.onUse]`)
- `carpets.onUse` (`[carpets.lua:carpets.onUse]`)
- `dailyRewardShrine.onUse` (`[daily_reward_shrine.lua:dailyRewardShrine.onUse]`)
- `forge.onUse` (`[exaltation_forge.lua:forge.onUse]`)
- `hiveGates.onUse` (`[hive_gates.lua:hiveGates.onUse]`)
- `largeSeashell.onUse` (`[large_seashell.lua:largeSeashell.onUse]`)
- `market.onUse` (`[market.lua:market.onUse]`)
- `offlineTrainingBook.onUse` (`[offline_training_book.lua:offlineTrainingBook.onUse]`)
- `skillTrainer.onUse` (`[skill_trainer.lua:skillTrainer.onUse]`)
- `stash.onUse` (`[stash.lua:stash.onUse]`)

## Invariants
- None

## Side Effects
- None

## Verification
- Run: `ctest --test-dir build --output-on-failure`
