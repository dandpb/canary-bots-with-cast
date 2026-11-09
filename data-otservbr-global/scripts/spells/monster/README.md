# Monster

## Overview
Component package under `scripts/spells/monster` containing 591 files (`abyssador_paralyze.lua`..`zushuka_paralyze.lua`).

## Interface
- Defines 591 script/configuration files (`abyssador_paralyze.lua` through `zushuka_paralyze.lua`) [abyssador_paralyze.lua]
- `spell.onCastSpell(creature, var)` [abyssador_paralyze.lua:spell.onCastSpell]
- `Spell("instant")` assigned to `spell` [abyssador_paralyze.lua:spell]
- `Spell("instant")` registration [abyssador_paralyze.lua:Spell]
- `spell.onCastSpell(creature, var)` [abyssador_poison_wave.lua:spell.onCastSpell]
- `Spell("instant")` assigned to `spell` [abyssador_poison_wave.lua:spell]
- `Spell("instant")` registration [abyssador_poison_wave.lua:Spell]
- `spell.onCastSpell(creature, var)` [abyssador_skill_reducer_1.lua:spell.onCastSpell]
- `Spell("instant")` assigned to `spell` [abyssador_skill_reducer_1.lua:spell]
- `Spell("instant")` registration [abyssador_skill_reducer_1.lua:Spell]
- `spell.onCastSpell(creature, var)` [abyssador_skill_reducer_2.lua:spell.onCastSpell]
- `Spell("instant")` assigned to `spell` [abyssador_skill_reducer_2.lua:spell]
- `Spell("instant")` registration [abyssador_skill_reducer_2.lua:Spell]
- `spell.onCastSpell(creature, var)` [aftershock_wave.lua:spell.onCastSpell]
- `Spell("instant")` assigned to `spell` [aftershock_wave.lua:spell]
- `Spell("instant")` registration [aftershock_wave.lua:Spell]
- `onTargetTile(cid, pos)` [aggresive_lava_wave.lua:onTargetTile]
- `spell.onCastSpell(creature, var)` [aggresive_lava_wave.lua:spell.onCastSpell]
- `Spell("instant")` assigned to `spell` [aggresive_lava_wave.lua:spell]
- `Spell("instant")` registration [aggresive_lava_wave.lua:Spell]
- `spell.onCastSpell(creature, var)` [alptramun_summon.lua:spell.onCastSpell]
- `Spell("instant")` assigned to `spell` [alptramun_summon.lua:spell]
- `Spell("instant")` registration [alptramun_summon.lua:Spell]
- `spell.onCastSpell(creature, var)` [ancient_scarab_paralyze.lua:spell.onCastSpell]
- `Spell("instant")` assigned to `spell` [ancient_scarab_paralyze.lua:spell]

## Invariants
- Combat parameters and area matrices (`combat:setParameter`, `combat:setArea`) constrain spell/attack target resolution [abyssador_paralyze.lua:combat]
- Combat parameters and area matrices (`combat:setParameter`, `combat:setArea`) constrain spell/attack target resolution [abyssador_poison_wave.lua:combat]
- Combat parameters and area matrices (`combat:setParameter`, `combat:setArea`) constrain spell/attack target resolution [aftershock_wave.lua:combat]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [aggresive_lava_wave.lua:Tile]
- Combat parameters and area matrices (`combat:setParameter`, `combat:setArea`) constrain spell/attack target resolution [aggresive_lava_wave.lua:combat]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [alptramun_summon.lua:getStorageValue]
- Combat parameters and area matrices (`combat:setParameter`, `combat:setArea`) constrain spell/attack target resolution [alptramun_summon.lua:combat]
- Combat parameters and area matrices (`combat:setParameter`, `combat:setArea`) constrain spell/attack target resolution [ancient_scarab_paralyze.lua:combat]
- Combat parameters and area matrices (`combat:setParameter`, `combat:setArea`) constrain spell/attack target resolution [annihilon_paralyze.lua:combat]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [anomaly_break.lua:Tile]
- Combat parameters and area matrices (`combat:setParameter`, `combat:setArea`) constrain spell/attack target resolution [anomaly_wave.lua:combat]
- Combat parameters and area matrices (`combat:setParameter`, `combat:setArea`) constrain spell/attack target resolution [apprentice_sheng_summon.lua:combat]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [abyssador_paralyze.lua:register]
- Executes combat damage, healing, or condition effects on targets via `combat:execute(creature, var)` [abyssador_paralyze.lua:combat:execute]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [abyssador_poison_wave.lua:register]
- Executes combat damage, healing, or condition effects on targets via `combat:execute(creature, var)` [abyssador_poison_wave.lua:combat:execute]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [abyssador_skill_reducer_1.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [abyssador_skill_reducer_2.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [aftershock_wave.lua:register]
- Executes combat damage, healing, or condition effects on targets via `combat:execute(creature, var)` [aftershock_wave.lua:combat:execute]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [aggresive_lava_wave.lua:register]
- Executes combat damage, healing, or condition effects on targets via `combat:execute(creature, var)` [aggresive_lava_wave.lua:combat:execute]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [alptramun_summon.lua:register]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [alptramun_summon.lua:Game]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
