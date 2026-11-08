# Farmine

## Overview
Component package under `raids/farmine` containing 5 files (`beetles.xml`..`zulazza_the_corruptor.xml`).

## Interface
- `<announce>` raid broadcast tags (2 messages) [beetles.xml:announce]
- `<areaspawn>` monster `Lancer Beetle` (amount=10) [beetles.xml:areaspawn]
- `<announce>` raid broadcast tags (1 messages) [draptor.xml:announce]
- `<singlespawn name="Draptor">` boss/creature spawn [draptor.xml:singlespawn]
- `<singlespawn name="Grand Mother Foulscale">` boss/creature spawn [draptor.xml:singlespawn]
- `<areaspawn>` monster `Dragon` (amount=70) [draptor.xml:areaspawn]
- `<areaspawn>` monster `Dragon` (amount=40) [draptor.xml:areaspawn]
- `<announce>` raid broadcast tags (3 messages) [gnarlhounds.xml:announce]
- `<areaspawn>` monster `Gnarlhound` (amount=20) [gnarlhounds.xml:areaspawn]
- `<announce>` raid broadcast tags (1 messages) [zevelon_duskbringer.xml:announce]
- `<singlespawn name="Zevelon Duskbringer">` boss/creature spawn [zevelon_duskbringer.xml:singlespawn]
- `<announce>` raid broadcast tags (5 messages) [zulazza_the_corruptor.xml:announce]
- `<singlespawn name="Zulazza the Corruptor">` boss/creature spawn [zulazza_the_corruptor.xml:singlespawn]
- `<singlespawn name="Chizzoron the Distorter">` boss/creature spawn [zulazza_the_corruptor.xml:singlespawn]

## Invariants
- Spawn coordinates (`x`, `y`, `z` / `fromx`..`toz`) and `delay` timestamps must correspond to valid map tiles and monster names [beetles.xml:raid]
- Spawn coordinates (`x`, `y`, `z` / `fromx`..`toz`) and `delay` timestamps must correspond to valid map tiles and monster names [draptor.xml:raid]
- Spawn coordinates (`x`, `y`, `z` / `fromx`..`toz`) and `delay` timestamps must correspond to valid map tiles and monster names [gnarlhounds.xml:raid]
- Spawn coordinates (`x`, `y`, `z` / `fromx`..`toz`) and `delay` timestamps must correspond to valid map tiles and monster names [zevelon_duskbringer.xml:raid]
- Spawn coordinates (`x`, `y`, `z` / `fromx`..`toz`) and `delay` timestamps must correspond to valid map tiles and monster names [zulazza_the_corruptor.xml:raid]

## Side Effects
- Broadcasts server-wide raid messages and spawns configured monsters when the raid executes [beetles.xml:raid]
- Broadcasts server-wide raid messages and spawns configured monsters when the raid executes [draptor.xml:raid]
- Broadcasts server-wide raid messages and spawns configured monsters when the raid executes [gnarlhounds.xml:raid]
- Broadcasts server-wide raid messages and spawns configured monsters when the raid executes [zevelon_duskbringer.xml:raid]
- Broadcasts server-wide raid messages and spawns configured monsters when the raid executes [zulazza_the_corruptor.xml:raid]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
