# Raids

## Overview
Provides 1 direct files (`raids.xml`..`raids.xml`) and 17 subdirectories under `raids`.

## Interface
- `<raid name="Badger" file="abdendriel/badger.xml">` entry [raids.xml:raid]
- `<raid name="WarWolf" file="abdendriel/warwolf.xml">` entry [raids.xml:raid]
- `<raid name="WaspBear" file="abdendriel/wasp_bear.xml">` entry [raids.xml:raid]
- `<raid name="Dragons" file="abdendriel/dragons.xml">` entry [raids.xml:raid]
- `<raid name="Bonebeast" file="ankrahmun/bone_beast.xml">` entry [raids.xml:raid]
- `<raid name="Cobra" file="ankrahmun/cobra.xml">` entry [raids.xml:raid]
- `<raid name="Gargoyle" file="ankrahmun/gargoyle.xml">` entry [raids.xml:raid]
- `<raid name="Nomad" file="ankrahmun/nomad.xml">` entry [raids.xml:raid]
- `<raid name="Scarab" file="ankrahmun/scarab.xml">` entry [raids.xml:raid]
- `<raid name="Terramite" file="ankrahmun/terramite.xml">` entry [raids.xml:raid]
- `<raid name="OrcWoods" file="carlin/orc.xml">` entry [raids.xml:raid]
- `<raid name="Chayenne" file="chayenne/chayenne.xml">` entry [raids.xml:raid]
- `<raid name="Lions" file="darashia/lions.xml">` entry [raids.xml:raid]
- `<raid name="Minos" file="darashia/minotaurs.xml">` entry [raids.xml:raid]
- `<raid name="Necropharus" file="darashia/necropharus.xml">` entry [raids.xml:raid]
- Total of 64 `<raid>` definitions in `<raids>` manifest [raids.xml:raids]
- [abdendriel](./abdendriel/README.md) - Component package under `raids/abdendriel` containing 4 files (`badger.xml`..`wasp_bear.xml`).
- [ankrahmun](./ankrahmun/README.md) - Component package under `raids/ankrahmun` containing 6 files (`bone_beast.xml`..`terramite.xml`).
- [carlin](./carlin/README.md) - Component package under `raids/carlin` containing 2 files (`orc.xml`..`yeti.xml`).
- [chayenne](./chayenne/README.md) - Component package under `raids/chayenne` containing 1 files (`chayenne.xml`..`chayenne.xml`).
- [darashia](./darashia/README.md) - Component package under `raids/darashia` containing 9 files (`arachir_the_ancient_one.xml`..`white_pale.xml`).
- [edron](./edron/README.md) - Component package under `raids/edron` containing 8 files (`feroxa.xml`..`weakened_shlorg.xml`).
- [farmine](./farmine/README.md) - Component package under `raids/farmine` containing 5 files (`beetles.xml`..`zulazza_the_corruptor.xml`).
- [fury_gate](./fury_gate/README.md) - Component package under `raids/fury_gate` containing 1 files (`furyosa.xml`..`furyosa.xml`).
- [kazordoon](./kazordoon/README.md) - Component package under `raids/kazordoon` containing 2 files (`goblins.xml`..`horned.xml`).
- [liberty_bay](./liberty_bay/README.md) - Component package under `raids/liberty_bay` containing 10 files (`crustacea_gigantica_1.xml`..`undead_cavebear.xml`).
- [oramond](./oramond/README.md) - Component package under `raids/oramond` containing 2 files (`crustacea_gigantica_4.xml`..`crustacea_gigantica_5.xml`).
- [port_hope](./port_hope/README.md) - Component package under `raids/port_hope` containing 8 files (`kongras.xml`..`the_welter.xml`).
- [rookgaard](./rookgaard/README.md) - Component package under `raids/rookgaard` containing 6 files (`munster.xml`..`teleskor.xml`).
- [roshamuul](./roshamuul/README.md) - Component package under `raids/roshamuul` containing 2 files (`gaz_haragoth.xml`..`omrafir.xml`).
- [svargrond](./svargrond/README.md) - Component package under `raids/svargrond` containing 8 files (`barba_bittermor.xml`..`zushuka.xml`).
- [thais](./thais/README.md) - Component package under `raids/thais` containing 4 files (`cyclops.xml`..`wild_horses.xml`).
- [venore](./venore/README.md) - Component package under `raids/venore` containing 9 files (`dharalion.xml`..`water_buffalo.xml`).

## Invariants
- Each `<raid>` entry in `raids.xml` must reference a valid relative XML raid file path and define `interval2` and `margin` attributes [raids.xml:raid]

## Side Effects
- Registers raid schedule definitions loaded by the server raid manager [raids.xml:raids]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
