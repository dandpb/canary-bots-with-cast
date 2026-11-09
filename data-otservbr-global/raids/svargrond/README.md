# Svargrond

## Overview
Component package under `raids/svargrond` containing 8 files (`barba_bittermor.xml`..`zushuka.xml`).

## Interface
- `<announce>` raid broadcast tags (2 messages) [barba_bittermor.xml:announce]
- `<areaspawn>` monster `Barbarian Bloodwalker` (amount=5) [barba_bittermor.xml:areaspawn]
- `<areaspawn>` monster `Barbarian Brutetamer` (amount=3) [barba_bittermor.xml:areaspawn]
- `<areaspawn>` monster `Barbarian Headsplitter` (amount=5) [barba_bittermor.xml:areaspawn]
- `<areaspawn>` monster `Barbarian Skullhunter` (amount=10) [barba_bittermor.xml:areaspawn]
- `<announce>` raid broadcast tags (5 messages) [barba_svar.xml:announce]
- `<areaspawn>` monster `Barbarian Bloodwalker` (amount=5) [barba_svar.xml:areaspawn]
- `<areaspawn>` monster `Barbarian Brutetamer` (amount=5) [barba_svar.xml:areaspawn]
- `<areaspawn>` monster `Barbarian Headsplitter` (amount=5) [barba_svar.xml:areaspawn]
- `<areaspawn>` monster `Barbarian Skullhunter` (amount=5) [barba_svar.xml:areaspawn]
- `<announce>` raid broadcast tags (3 messages) [barbarian.xml:announce]
- `<areaspawn>` monster `Barbarian Bloodwalker` (amount=35) [barbarian.xml:areaspawn]
- `<areaspawn>` monster `Barbarian Brutetamer` (amount=22) [barbarian.xml:areaspawn]
- `<areaspawn>` monster `Barbarian Headsplitter` (amount=22) [barbarian.xml:areaspawn]
- `<areaspawn>` monster `Barbarian Skullhunter` (amount=28) [barbarian.xml:areaspawn]
- `<areaspawn>` monster `Ice Witch` (amount=15) [barbarian.xml:areaspawn]
- `<announce>` raid broadcast tags (3 messages) [ghazbaran.xml:announce]
- `<singlespawn name="Ghazbaran">` boss/creature spawn [ghazbaran.xml:singlespawn]
- `<areaspawn>` monster `Deathslicer` (amount=12) [ghazbaran.xml:areaspawn]
- `<areaspawn>` monster `Juggernaut` (amount=5) [ghazbaran.xml:areaspawn]
- `<areaspawn>` monster `Fury` (amount=8) [ghazbaran.xml:areaspawn]
- `<areaspawn>` monster `Demon` (amount=6) [ghazbaran.xml:areaspawn]
- `<singlespawn name="Hirintror">` boss/creature spawn [hirintror.xml:singlespawn]
- `<announce>` raid broadcast tags (2 messages) [ice_golems.xml:announce]
- `<areaspawn>` monster `Ice Golem` (amount=15) [ice_golems.xml:areaspawn]

## Invariants
- Spawn coordinates (`x`, `y`, `z` / `fromx`..`toz`) and `delay` timestamps must correspond to valid map tiles and monster names [barba_bittermor.xml:raid]
- Spawn coordinates (`x`, `y`, `z` / `fromx`..`toz`) and `delay` timestamps must correspond to valid map tiles and monster names [barba_svar.xml:raid]
- Spawn coordinates (`x`, `y`, `z` / `fromx`..`toz`) and `delay` timestamps must correspond to valid map tiles and monster names [barbarian.xml:raid]
- Spawn coordinates (`x`, `y`, `z` / `fromx`..`toz`) and `delay` timestamps must correspond to valid map tiles and monster names [ghazbaran.xml:raid]
- Spawn coordinates (`x`, `y`, `z` / `fromx`..`toz`) and `delay` timestamps must correspond to valid map tiles and monster names [hirintror.xml:raid]
- Spawn coordinates (`x`, `y`, `z` / `fromx`..`toz`) and `delay` timestamps must correspond to valid map tiles and monster names [ice_golems.xml:raid]
- Spawn coordinates (`x`, `y`, `z` / `fromx`..`toz`) and `delay` timestamps must correspond to valid map tiles and monster names [ocyakao.xml:raid]
- Spawn coordinates (`x`, `y`, `z` / `fromx`..`toz`) and `delay` timestamps must correspond to valid map tiles and monster names [zushuka.xml:raid]

## Side Effects
- Broadcasts server-wide raid messages and spawns configured monsters when the raid executes [barba_bittermor.xml:raid]
- Broadcasts server-wide raid messages and spawns configured monsters when the raid executes [barba_svar.xml:raid]
- Broadcasts server-wide raid messages and spawns configured monsters when the raid executes [barbarian.xml:raid]
- Broadcasts server-wide raid messages and spawns configured monsters when the raid executes [ghazbaran.xml:raid]
- Broadcasts server-wide raid messages and spawns configured monsters when the raid executes [hirintror.xml:raid]
- Broadcasts server-wide raid messages and spawns configured monsters when the raid executes [ice_golems.xml:raid]
- Broadcasts server-wide raid messages and spawns configured monsters when the raid executes [ocyakao.xml:raid]
- Broadcasts server-wide raid messages and spawns configured monsters when the raid executes [zushuka.xml:raid]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
