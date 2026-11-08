# Kilmaresh

## Overview
Component package under `monster/quests/kilmaresh` containing 15 files (`a_shielded_astral_glyph.lua`..`xogixath.lua`).

## Interface
- `Game.createMonsterType("A Shielded Astral Glyph")` and `mType:register(monster)` [a_shielded_astral_glyph.lua:Game.createMonsterType]
- `Game.createMonsterType("Amenef the Burning")` and `mType:register(monster)` [amenef_the_burning.lua:Game.createMonsterType]
- `Game.createMonsterType("An Astral Glyph")` and `mType:register(monster)` [an_astral_glyph.lua:Game.createMonsterType]
- `Game.createMonsterType("Bragrumol")` and `mType:register(monster)` [bragrumol.lua:Game.createMonsterType]
- `Game.createMonsterType("Earworm")` and `mType:register(monster)` [earworm.lua:Game.createMonsterType]
- `Game.createMonsterType("Mozradek")` and `mType:register(monster)` [mozradek.lua:Game.createMonsterType]
- `Game.createMonsterType("Neferi the Spy")` and `mType:register(monster)` [neferi_the_spy.lua:Game.createMonsterType]
- `Game.createMonsterType("Sister Hetai")` and `mType:register(monster)` [sister_hetai.lua:Game.createMonsterType]
- `Game.createMonsterType("Sun-Marked Goanna")` and `mType:register(monster)` [sun-marked_goanna.lua:Game.createMonsterType]
- `Game.createMonsterType("Urmahlullu the Immaculate")` and `mType:register(monster)` [urmahlullu_the_immaculate.lua:Game.createMonsterType]
- `Game.createMonsterType("Urmahlullu the Tamed")` and `mType:register(monster)` [urmahlullu_the_tamed.lua:Game.createMonsterType]
- `Game.createMonsterType("Urmahlullu the Weakened")` and `mType:register(monster)` [urmahlullu_the_weakened.lua:Game.createMonsterType]
- `Game.createMonsterType("Wildness of Urmahlullu")` and `mType:register(monster)` [wildness_of_urmahlullu.lua:Game.createMonsterType]
- `Game.createMonsterType("Wisdom of Urmahlullu")` and `mType:register(monster)` [wisdom_of_urmahlullu.lua:Game.createMonsterType]
- `Game.createMonsterType("Xogixath")` and `mType:register(monster)` [xogixath.lua:Game.createMonsterType]

## Invariants
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [a_shielded_astral_glyph.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [amenef_the_burning.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [an_astral_glyph.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [bragrumol.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [earworm.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [mozradek.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [neferi_the_spy.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [sister_hetai.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [sun-marked_goanna.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [urmahlullu_the_immaculate.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [urmahlullu_the_tamed.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [urmahlullu_the_weakened.lua:monster.flags]

## Side Effects
- Registers monster type `A Shielded Astral Glyph` into the global `Game` engine registry via `mType:register(monster)` [a_shielded_astral_glyph.lua:mType:register]
- Registers monster type `Amenef the Burning` into the global `Game` engine registry via `mType:register(monster)` [amenef_the_burning.lua:mType:register]
- Registers monster type `An Astral Glyph` into the global `Game` engine registry via `mType:register(monster)` [an_astral_glyph.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [an_astral_glyph.lua:monster.events]
- Registers monster type `Bragrumol` into the global `Game` engine registry via `mType:register(monster)` [bragrumol.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [bragrumol.lua:monster.events]
- Registers monster type `Earworm` into the global `Game` engine registry via `mType:register(monster)` [earworm.lua:mType:register]
- Registers monster type `Mozradek` into the global `Game` engine registry via `mType:register(monster)` [mozradek.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [mozradek.lua:monster.events]
- Registers monster type `Neferi the Spy` into the global `Game` engine registry via `mType:register(monster)` [neferi_the_spy.lua:mType:register]
- Registers monster type `Sister Hetai` into the global `Game` engine registry via `mType:register(monster)` [sister_hetai.lua:mType:register]
- Registers monster type `Sun-Marked Goanna` into the global `Game` engine registry via `mType:register(monster)` [sun-marked_goanna.lua:mType:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
