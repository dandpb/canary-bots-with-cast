# Edron

## Overview
Component package under `raids/edron` containing 8 files (`feroxa.xml`..`weakened_shlorg.xml`).

## Interface
- `<announce>` raid broadcast tags (3 messages) [feroxa.xml:announce]
- `<singlespawn name="Feroxa">` boss/creature spawn [feroxa.xml:singlespawn]
- `<announce>` raid broadcast tags (1 messages) [goblins.xml:announce]
- `<areaspawn>` monster `Goblin` (amount=40) [goblins.xml:areaspawn]
- `<areaspawn>` monster `Goblin Scavenger` (amount=10) [goblins.xml:areaspawn]
- `<areaspawn>` monster `Goblin Assassin` (amount=15) [goblins.xml:areaspawn]
- `<singlespawn name="Mad Mage">` boss/creature spawn [mad_mage.xml:singlespawn]
- `<areaspawn>` monster `Golden Servant` (amount=7) [mad_mage.xml:areaspawn]
- `<areaspawn>` monster `Iron Servant` (amount=7) [mad_mage.xml:areaspawn]
- `<announce>` raid broadcast tags (2 messages) [orc.xml:announce]
- `<areaspawn>` monster `Orc` (amount=20) [orc.xml:areaspawn]
- `<areaspawn>` monster `Orc Rider` (amount=5) [orc.xml:areaspawn]
- `<areaspawn>` monster `Orc Spearman` (amount=15) [orc.xml:areaspawn]
- `<areaspawn>` monster `Orc Warrior` (amount=10) [orc.xml:areaspawn]
- `<announce>` raid broadcast tags (3 messages) [orshabaal.xml:announce]
- `<singlespawn name="Orshabaal">` boss/creature spawn [orshabaal.xml:singlespawn]
- `<announce>` raid broadcast tags (1 messages) [sir_valorcrest.xml:announce]
- `<singlespawn name="Sir Valorcrest">` boss/creature spawn [sir_valorcrest.xml:singlespawn]
- `<announce>` raid broadcast tags (3 messages) [warlock.xml:announce]
- `<areaspawn>` monster `Monk` (amount=6) [warlock.xml:areaspawn]
- `<areaspawn>` monster `Warlock` (amount=3) [warlock.xml:areaspawn]
- `<singlespawn name="Weakened Shlorg">` boss/creature spawn [weakened_shlorg.xml:singlespawn]

## Invariants
- Spawn coordinates (`x`, `y`, `z` / `fromx`..`toz`) and `delay` timestamps must correspond to valid map tiles and monster names [feroxa.xml:raid]
- Spawn coordinates (`x`, `y`, `z` / `fromx`..`toz`) and `delay` timestamps must correspond to valid map tiles and monster names [goblins.xml:raid]
- Spawn coordinates (`x`, `y`, `z` / `fromx`..`toz`) and `delay` timestamps must correspond to valid map tiles and monster names [mad_mage.xml:raid]
- Spawn coordinates (`x`, `y`, `z` / `fromx`..`toz`) and `delay` timestamps must correspond to valid map tiles and monster names [orc.xml:raid]
- Spawn coordinates (`x`, `y`, `z` / `fromx`..`toz`) and `delay` timestamps must correspond to valid map tiles and monster names [orshabaal.xml:raid]
- Spawn coordinates (`x`, `y`, `z` / `fromx`..`toz`) and `delay` timestamps must correspond to valid map tiles and monster names [sir_valorcrest.xml:raid]
- Spawn coordinates (`x`, `y`, `z` / `fromx`..`toz`) and `delay` timestamps must correspond to valid map tiles and monster names [warlock.xml:raid]
- Spawn coordinates (`x`, `y`, `z` / `fromx`..`toz`) and `delay` timestamps must correspond to valid map tiles and monster names [weakened_shlorg.xml:raid]

## Side Effects
- Broadcasts server-wide raid messages and spawns configured monsters when the raid executes [feroxa.xml:raid]
- Broadcasts server-wide raid messages and spawns configured monsters when the raid executes [goblins.xml:raid]
- Broadcasts server-wide raid messages and spawns configured monsters when the raid executes [mad_mage.xml:raid]
- Broadcasts server-wide raid messages and spawns configured monsters when the raid executes [orc.xml:raid]
- Broadcasts server-wide raid messages and spawns configured monsters when the raid executes [orshabaal.xml:raid]
- Broadcasts server-wide raid messages and spawns configured monsters when the raid executes [sir_valorcrest.xml:raid]
- Broadcasts server-wide raid messages and spawns configured monsters when the raid executes [warlock.xml:raid]
- Broadcasts server-wide raid messages and spawns configured monsters when the raid executes [weakened_shlorg.xml:raid]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
