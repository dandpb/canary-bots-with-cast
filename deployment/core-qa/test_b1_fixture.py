"""Offline tests of the B1 companion fixture: its numbers against the source, its SQL scope and guards, the
canonical slice, the authored overlays and the B1-only apply path. No Docker, git, network or MariaDB.

The seed's guard, writes, checks and the slice are portable SELECT/UPDATE/INSERT text: they also run here on an
in-memory SQLite built from the parsed 02_players.sql and 03_player_storage.sql rows. What only MariaDB runs
(DELIMITER, BEGIN NOT ATOMIC, SIGNAL, information_schema, the transaction) is checked as text."""

import csv
import json
import os
import re
import sqlite3
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch

import b1_fixture as fx

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent.parent
BOT = SOURCE / "src/creatures/players/bot"
SEED = (HERE / "b1/seed-companions.sql").read_text()
LEADER = (HERE / "b1/leader-prep.sql.template").read_text()
SLICE = (HERE / "b1/slice.sql").read_text()
# Pinned: the slice of the fresh B1 database at S0 (fx.expected_s0) and the query that produces it.
S0_SLICE_SHA256 = "170a78f86420ab6abefaf0d837284a932f2c5867580ee3c466e5f506f90b8b05"
FORBIDDEN = {3366: "magic plate armor", 3388: "demon armor", 3363: "dragon scale legs"}
STARTER = {  # id: (items.xml name, armor or defense or level the starter claim rests on)
    3351: "steel helmet",
    3352: "chain helmet",
    3355: "leather helmet",
    3357: "plate armor",
    3359: "brass armor",
    3361: "leather armor",
    3557: "plate legs",
    3372: "brass legs",
    3362: "studded legs",
    3552: "leather boots",
    3264: "sword",
    3277: "spear",
    3066: "snakebite rod",
    3074: "wand of vortex",
    3409: "steel shield",
    3412: "wooden shield",
}


def seed_rows(name, pattern):
    text = (SOURCE / "database/bots" / name).read_bytes().decode("latin1")
    return text, re.findall(pattern, text)


def players_seed():
    """The 02_players.sql columns and the three pilot rows, as SQL literals."""
    text = (SOURCE / "database/bots/02_players.sql").read_bytes().decode("latin1")
    columns = (
        re.search(r"INSERT INTO `players` \((.*?)\) VALUES", text)
        .group(1)
        .replace("`", "")
        .split(", ")
    )
    rows = {}
    for guid in fx.PILOTS:
        row = re.search(rf"\({guid},'.*?\)(?=[,;])", text).group()
        values = re.findall(r"'(?:[^'\\]|\\.)*'|[^,]+", row[1:-1])
        assert len(values) == len(columns)
        rows[guid] = dict(zip(columns, values))
    return columns, rows


def storage_seed():
    text = (
        (SOURCE / "database/bots/03_player_storage.sql").read_bytes().decode("latin1")
    )
    rows = re.findall(r"\((\d+),(-?\d+),(-?\d+)\)", text)
    return [tuple(map(int, row)) for row in rows if int(row[0]) in fx.PILOTS]


def guard_part():
    return SEED[: SEED.index("END//") + len("END//")]


def conditions(text):
    """The `IF (SELECT ...) <> n THEN` checks that SQLite can evaluate."""
    found = re.findall(r"IF \((SELECT .*?)\) <> (\d+) THEN", text, re.DOTALL)
    return [
        (sql, int(n))
        for sql, n in found
        if "information_schema" not in sql and "DATABASE()" not in sql
    ]


def writes():
    body = SEED[SEED.index("START TRANSACTION;") : SEED.rindex("DELIMITER //")]
    return re.findall(r"^(?:INSERT|UPDATE|DELETE)[^;]*;", body, re.MULTILINE)


def fresh_db():
    """A SQLite database holding what a fresh B1 init holds for the pilots."""
    columns, rows = players_seed()
    db = sqlite3.connect(":memory:")
    db.execute(
        f"CREATE TABLE players ({', '.join(f'`{column}`' for column in columns)})"
    )
    for row in rows.values():
        db.execute(f"INSERT INTO players VALUES ({', '.join(row.values())})")
    db.executescript(
        "CREATE TABLE accounts (id); CREATE TABLE player_depotitems (player_id); CREATE TABLE player_inboxitems "
        "(player_id); CREATE TABLE players_online (player_id); CREATE TABLE player_storage (player_id, `key`, value, PRIMARY KEY (player_id, `key`));"
        "CREATE TABLE player_items (player_id, pid, sid, itemtype, `count`, attributes);"
        "CREATE TABLE player_deaths (player_id, time, level, killed_by, is_player, mostdamage_by, "
        "mostdamage_is_player); CREATE TABLE qa_b1_fixture (k PRIMARY KEY, v);"
        "INSERT INTO accounts VALUES (1), (65000);"
    )
    db.executemany("INSERT INTO player_storage VALUES (?, ?, ?)", storage_seed())
    return db


def failing(db, checks):
    return [sql for sql, n in checks if db.execute(sql).fetchone()[0] != n]


def apply_seed(db):
    for statement in writes():
        db.execute(statement)


def run_slice(db):
    statements = [s.strip() for s in SLICE.split(";")]
    lines = []
    for statement in statements:
        body = "\n".join(
            line for line in statement.splitlines() if not line.startswith("--")
        ).strip()
        if body.startswith("SELECT"):
            lines += ["\t".join(map(str, row)) for row in db.execute(body)]
    return lines


def gains():
    root = ET.parse(SOURCE / "data/XML/vocations.xml").getroot()
    return {
        int(v.get("id")): tuple(
            int(v.get(k)) for k in ("gainhp", "gainmana", "gaincap")
        )
        for v in root
    }


def item_xml(item):
    text = (SOURCE / "data/items/items.xml").read_text()
    start = text.index(f'<item id="{item}" ')
    return text[start : text.index("</item>", start)]


def b1_env(**extra):
    return patch.dict(os.environ, {"CORE_QA_PROFILE": "b1", **extra})


class SourceNumbersTests(unittest.TestCase):
    def test_level_20_experience_is_the_server_formula(self):
        text = (SOURCE / "src/creatures/players/player.cpp").read_text()
        self.assertIn(
            "return (((level - 6ULL) * level + 17ULL) * level - 12ULL) / 6ULL * 100ULL;",
            text,
        )
        self.assertEqual((((20 - 6) * 20 + 17) * 20 - 12) // 6 * 100, fx.EXPERIENCE)

    def test_hp_mana_cap_are_the_vocation_values_at_level_20(self):
        schema = (SOURCE / "schema.sql").read_text()
        self.assertIn("`health` int(11) NOT NULL DEFAULT '150'", schema)
        self.assertIn("`mana` int(11) NOT NULL DEFAULT '0'", schema)
        self.assertIn(
            "uint32_t capacity = 40000;",
            (SOURCE / "src/creatures/players/player.hpp").read_text(),
        )
        g = gains()
        for vocation, (hp, mana, cap) in fx.VOCATION.items():
            self.assertEqual(hp, 150 + 7 * g[0][0] + 12 * g[vocation][0])
            self.assertEqual(mana, 7 * g[0][1] + 12 * g[vocation][1])
            self.assertEqual(cap, 400 + 7 * g[0][2] + 12 * g[vocation][2])
        self.assertEqual(
            fx.VOCATION[4][:2], (365, 95)
        )  # tests/fixture/m5_qa.py knight anchor
        self.assertGreaterEqual(
            fx.VOCATION[2][1], 120
        )  # druid party heal needs mana >= 120

    def test_potions_are_the_level_20_types_twenty_each_and_buyable(self):
        potions = (BOT / "bot_potions.hpp").read_text()
        self.assertIn("{ 266, 0, true, false, VOC_ANY }", potions)
        self.assertIn("{ 268, 0, false, true, VOC_ANY }", potions)
        self.assertIn("{ 236, 50,", potions)
        self.assertIn("{ 237, 50,", potions)
        xodet = (SOURCE / "data-otservbr-global/npc/xodet.lua").read_text()
        self.assertIn("clientId = 266, buy = 50", xodet)
        self.assertIn("clientId = 268, buy = 56", xodet)
        for _name, _vocation, stock in fx.PILOTS.values():
            self.assertEqual(set(stock), {266, 268})
            self.assertEqual(sum(stock.values()), 20)
            self.assertTrue(all(count < 20 for count in stock.values()))
            self.assertLess((20 - stock[266]) * 50 + (20 - stock[268]) * 56, 10000)

    def test_budget_is_10000_gp_in_coins_with_bank_0(self):
        funding = (
            SOURCE / "data/scripts/globalevents/bot_market_funding.lua"
        ).read_text()
        self.assertIn("local FUND_AMOUNT = 100000000000", funding)
        self.assertIn(
            "UPDATE `players` SET `balance` = %d WHERE `account_id` = %d", funding
        )
        self.assertEqual(fx.SEED_BALANCE, 100000000000)
        self.assertEqual(players_seed()[1][65001]["balance"], str(fx.SEED_BALANCE))
        self.assertIn(
            '<item id="3035" article="a" name="platinum coin">', item_xml(3035) + ">"
        )
        self.assertIn(
            "ITEM_PLATINUM_COIN = 3035,",
            (SOURCE / "src/utils/utils_definitions.hpp").read_text(),
        )
        self.assertIn(
            "case ITEM_PLATINUM_COIN:\n\t\t\treturn count * 100;",
            (SOURCE / "src/items/item.cpp").read_text(),
        )
        item = (SOURCE / "src/items/item.cpp").read_text()
        for worth in fx.WORTH.values():
            self.assertIn(
                f"return count{' * ' + str(worth) if worth > 1 else ''};", item
            )
        self.assertEqual(sorted(fx.COINS), [3031, 3035, 3043])
        self.assertEqual(
            sum(fx.WORTH[coin] * count for coin, count in fx.COINS.items()), fx.BUDGET
        )
        self.assertEqual((fx.BUDGET, fx.PILOT_BALANCE), (10000, 0))
        for guid in fx.PILOTS:
            self.assertRegex(
                SEED, rf"`posz` = 7, `balance` = 0\n  WHERE `id` = {guid} AND"
            )
        self.assertIn("AND `mana` = `manamax` AND `balance` = 0\n", SEED)

    def test_npc_takes_the_coins_and_gives_change_without_the_bank(self):
        # The NPC charges with removeMoney(useBalance=true): inventory coins first, sorted by worth; a stack worth
        # more than the rest is split and the change added; the bank is touched only for what coins cannot pay.
        npc = (SOURCE / "src/lua/functions/creatures/npc/npc_functions.cpp").read_text()
        self.assertIn(
            "if (!g_game().removeMoney(player, itemCost + backpackCost, 0, true)) {",
            npc,
        )
        game = (SOURCE / "src/game/game.cpp").read_text()
        body = game[game.index("bool Game::removeMoney(") :]
        body = body[: body.index("\n}\n")]
        self.assertIn("std::multimap<uint32_t, std::shared_ptr<Item>> moneyMap;", body)
        self.assertIn("addMoney(cylinder, (worth * removeCount) - money, flags);", body)
        self.assertIn(
            "if (useBalance && player && player->getBankBalance() >= money) {", body
        )
        brain = (SOURCE / "src/creatures/players/bot/bot_brain.cpp").read_text()
        self.assertIn("getBankBalance()", brain)
        for _name, _vocation, stock in fx.PILOTS.values():
            cost = (20 - stock[266]) * 50 + (20 - stock[268]) * 56
            platinum = -(-cost // 100)  # what removeMoney takes from the 100-coin stack
            self.assertLessEqual(platinum, fx.COINS[3035])
            self.assertEqual(
                platinum * 100 - cost + (fx.BUDGET - platinum * 100), fx.BUDGET - cost
            )

    def test_thais_is_town_8(self):
        self.assertIn(
            "THAIS = 8,",
            (SOURCE / "data-otservbr-global/lib/tables/town.lua").read_text(),
        )

    def test_skills_and_magic_level_are_not_reset_by_the_engine(self):
        # The only Lua setter of bot skills (all 100) is BotSystem.activateBot, which nothing calls; the other
        # setters are Dawnport's vocation change. No bot C++ sets skills, magic level, level or experience.
        setters = []
        for root in (SOURCE / "data", SOURCE / "data-otservbr-global"):
            for path in root.rglob("*.lua"):
                for number, line in enumerate(
                    path.read_text(errors="replace").splitlines(), 1
                ):
                    found = re.search(
                        r":set(SkillLevel|MagicLevel)\(|BotSystem\.activateBot\b", line
                    )
                    if found and not line.lstrip().startswith("--"):
                        setters.append(f"{path.relative_to(SOURCE)}:{number}")
        system = "data/scripts/lib/bot_system.lua"
        self.assertEqual(
            setters,
            [
                f"{system}:2657",
                *(f"{system}:{n}" for n in range(2726, 2734)),
                "data-otservbr-global/lib/others/dawnport.lua:65",
                "data-otservbr-global/lib/others/dawnport.lua:83",
            ],
        )
        self.assertIn(
            "function BotSystem.activateBot(player)",
            (SOURCE / system).read_text().splitlines()[2656],
        )
        for path in BOT.glob("*.[ch]pp"):
            self.assertNotRegex(
                path.read_text(errors="replace"),
                r"set(SkillLevel|MagicLevel|Level)\(|addSkillAdvance|addExperience\(",
                path.name,
            )
        engine = (BOT / "bot_engine.cpp").read_text()
        body = engine[
            engine.index("bool BotEngine::activateBot(uint32_t guid) {") : engine.index(
                "bool BotEngine::deactivateBot(uint32_t guid) {"
            )
        ]
        self.assertNotRegex(body, r"[Ss]kill|[Mm]agLevel|[Mm]agicLevel|manaSpent")


class EquipmentOverlayTests(unittest.TestCase):
    def test_loadout_is_starter_gear_from_items_xml_never_the_banned_tier(self):
        used = {item for slots in fx.LOADOUT.values() for item in slots.values()}
        self.assertEqual(used, set(STARTER))
        for item, name in STARTER.items():
            block = item_xml(item)
            self.assertIn(f'name="{name}"', block)
            self.assertNotIn("golden", name)
            armor = re.search(r'key="armor" value="(\d+)"', block)
            defense = re.search(r'key="defense" value="(\d+)"', block)
            level = re.search(r'key="level" value="(\d+)"', block)
            if armor:
                self.assertLessEqual(int(armor.group(1)), 10, name)
            if defense and "shield" in name:
                self.assertLessEqual(int(defense.group(1)), 21, name)
            if level:
                self.assertLessEqual(int(level.group(1)), 6, name)
        self.assertFalse(used & set(FORBIDDEN))
        for item in FORBIDDEN:
            self.assertNotIn(str(item), LEADER)
            self.assertNotRegex(SEED, rf", {item}, 1, ''\)")

    def test_overlay_replaces_exactly_levels_20_29_with_the_loadout(self):
        source = (fx.AUTHORED / "equipment.csv").read_text()
        overlay = fx.equipment_overlay(source)
        old, new = (
            list(csv.DictReader(source.splitlines())),
            list(csv.DictReader(overlay.splitlines())),
        )
        self.assertEqual(len(old), len(new))
        self.assertEqual(overlay.count("\n"), source.count("\n"))
        changed = 0
        for before, after in zip(old, new):
            level, vocation = int(after["level"]), int(after["vocation"])
            if level in fx.OVERLAY_LEVELS and vocation in fx.LOADOUT:
                slots = fx.LOADOUT[vocation]
                self.assertEqual(
                    [
                        int(after[c])
                        for c in (
                            "slot_head",
                            "slot_armor",
                            "slot_left",
                            "slot_right",
                            "slot_legs",
                            "slot_feet",
                            "slot_backpack",
                        )
                    ],
                    [
                        slots[1],
                        slots[4],
                        slots[5],
                        slots[6],
                        slots[7],
                        slots[8],
                        fx.BACKPACK,
                    ],
                )
                changed += 1
            else:
                self.assertEqual(before, after)
        self.assertEqual(changed, len(fx.OVERLAY_LEVELS) * len(fx.LOADOUT))

    def test_the_engine_re_equips_the_overlay_row_on_activation(self):
        data = (BOT / "bot_data.cpp").read_text()
        engine = (BOT / "bot_engine.cpp").read_text()
        self.assertIn(
            'BotCsvTable::load(fmt::format("{}/equipment.csv", BOT_AUTHORED_DIR)', data
        )
        self.assertIn(
            'eq.weapon = static_cast<uint16_t>(t.getIntOr(i, "slot_right"', data
        )
        self.assertIn("uint32_t key = level * 10 + baseVoc;", data)
        self.assertIn('{CONST_SLOT_LEFT, eq.weapon, "weapon"}', data)
        self.assertIn('{CONST_SLOT_RIGHT, eq.shield, "shield"}', data)
        self.assertIn("\tequipBot(bot);", engine)
        self.assertIn(
            'BOT_AUTHORED_DIR = "data/bot/authored"',
            (BOT / "bot_engine_impl.hpp").read_text(),
        )
        self.assertIn(
            "      - authored-data:/canary/data/bot/authored\n",
            (HERE / "compose.yaml").read_text(),
        )
        self.assertEqual(fx.AUTHORED_TARGET, "/canary/data/bot/authored")

    def test_seed_items_are_the_overlay_level_20_row(self):
        overlay = {
            int(r["vocation"]): r
            for r in csv.DictReader(
                fx.equipment_overlay(
                    (fx.AUTHORED / "equipment.csv").read_text()
                ).splitlines()
            )
            if r["level"] == "20"
        }
        for guid, (_name, vocation, _stock) in fx.PILOTS.items():
            rows = re.findall(rf"\({guid}, (\d+), \d+, (\d+), \d+, ''\)", SEED)
            slots = {int(pid): int(item) for pid, item in rows if int(pid) <= 11}
            row = overlay[vocation]
            self.assertEqual(
                slots,
                {
                    1: int(row["slot_head"]),
                    3: int(row["slot_backpack"]),
                    4: int(row["slot_armor"]),
                    5: int(row["slot_left"]),
                    6: int(row["slot_right"]),
                    7: int(row["slot_legs"]),
                    8: int(row["slot_feet"]),
                },
            )

    def test_loadout_potions_and_coins_fit_the_capacity(self):
        weight = {
            item: int(re.search(r'key="weight" value="(\d+)"', item_xml(item)).group(1))
            for item in {*STARTER, 266, 268, *fx.COINS, fx.BACKPACK}
        }
        for _name, vocation, stock in fx.PILOTS.values():
            carried = (
                sum(weight[item] for item in fx.LOADOUT[vocation].values())
                + weight[fx.BACKPACK]
            )
            carried += sum(
                weight[item] * count for item, count in {**stock, **fx.COINS}.items()
            )
            self.assertLess(carried, fx.VOCATION[vocation][2] * 100)

    def test_hunt_overlay_enables_only_399(self):
        source = (fx.AUTHORED / "hunt_scripts.csv").read_text()
        overlay = fx.hunts_overlay(source)
        rows, original = (
            list(csv.DictReader(overlay.splitlines())),
            list(csv.DictReader(source.splitlines())),
        )
        self.assertEqual([r["id"] for r in rows if r["enabled"] == "1"], ["399"])
        for new, old in zip(rows, original, strict=True):
            self.assertEqual(
                {k: v for k, v in new.items() if k != "enabled"},
                {k: v for k, v in old.items() if k != "enabled"},
            )

    def test_render_overlays_writes_both_with_hashes_only_under_b1(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.multiple(
                fx, OVERLAY_DIR=root / "authored", EVIDENCE=root / "evidence"
            ):
                with (
                    patch.dict(os.environ, {"CORE_QA_PROFILE": "stage1"}),
                    self.assertRaisesRegex(RuntimeError, "refused"),
                ):
                    fx.render_overlays()
                with b1_env():
                    manifest = fx.render_overlays()
            self.assertEqual(
                sorted(manifest["files"]), ["equipment.csv", "hunt_scripts.csv"]
            )
            for name, hashes in manifest["files"].items():
                self.assertEqual(
                    fx.sha256((root / "authored" / name).read_bytes()),
                    hashes["overlay_sha256"],
                )
                self.assertEqual(
                    fx.sha256((fx.AUTHORED / name).read_bytes()),
                    hashes["source_sha256"],
                )
            self.assertEqual(
                json.loads((root / "evidence/overlay-manifest.json").read_text()),
                manifest,
            )
        self.assertEqual(manifest["loadout_scope"], fx.LOADOUT_SCOPE)
        self.assertIn("every B1 bot of level 20-29", fx.LOADOUT_SCOPE)
        bind = manifest["binds"][fx.FUNDING_TARGET]
        self.assertEqual(bind["source"], "b1/bot_market_funding.lua")
        self.assertEqual(bind["sha256"], fx.sha256(fx.FUNDING_NOOP.read_bytes()))
        self.assertEqual(
            bind["replaces_sha256"], fx.sha256(fx.FUNDING_SOURCE.read_bytes())
        )
        self.assertIn("not authored-data", bind["via"])

    def test_install_plan_targets_only_the_b1_volume_and_is_never_run(self):
        with b1_env():
            commands = fx.install_commands()
        self.assertEqual(len(commands), 2)
        self.assertIn(
            "docker compose -p canary-qa-b1 -f compose.yaml -f compose.brain-fake.yaml -f "
            "compose.b1.yaml -f compose.b1-brain.yaml --env-file .env create --no-build --pull never game",
            commands[0],
        )
        self.assertIn(
            "-v canary-qa-b1_authored-data:/canary/data/bot/authored", commands[1]
        )
        self.assertIn("canary-qa-b1-game:local", commands[1])
        for command in commands:
            self.assertNotIn("canary-core-qa", command)
        for project in ("canary-core-qa", "canary-core-qa-b1", "other"):
            with (
                self.subTest(project),
                b1_env(),
                self.assertRaisesRegex(RuntimeError, "refused"),
            ):
                fx.install_commands(project)
        with (
            patch.dict(os.environ, {"CORE_QA_PROFILE": "stage1"}),
            self.assertRaisesRegex(RuntimeError, "refused"),
        ):
            fx.install_commands()
        with b1_env():
            readiness = fx.readiness_commands()
        self.assertTrue(
            readiness[0].endswith(f"exec -T game sha256sum {fx.FUNDING_TARGET}")
        )
        self.assertIn("docker exec -i canary-qa-b1-database-1 mariadb", readiness[2])
        self.assertEqual(
            readiness[3],
            "python3 b1_fixture.py check ready runtime/b1/evidence/ready/db-slice.tsv",
        )
        for command in readiness:
            self.assertNotIn("canary-core-qa", command)
        with b1_env(), self.assertRaisesRegex(RuntimeError, "refused"):
            fx.readiness_commands("canary-core-qa")
        with (
            patch("subprocess.run") as run,
            patch("os.system") as system,
            b1_env(),
            patch("sys.stdout") as stdout,
        ):
            self.assertEqual(fx.main(["install-plan"]), 0)
        run.assert_not_called()
        system.assert_not_called()
        printed = json.loads(
            "".join(call.args[0] for call in stdout.write.call_args_list)
        )
        self.assertIs(printed["executed"], False)
        self.assertEqual(printed["loadout_scope"], fx.LOADOUT_SCOPE)
        self.assertEqual(printed["readiness"]["commands"], readiness)
        self.assertIn(fx.FUNDING_TARGET, printed["funding_bind"])


class SeedGuardTests(unittest.TestCase):
    def test_preimage_is_every_02_players_column_of_each_pilot(self):
        columns, rows = players_seed()
        guard = guard_part()
        for guid, row in rows.items():
            block = re.search(
                rf"WHERE\s+`id` = {guid} AND (.*?)\) <> 1 THEN", guard, re.DOTALL
            ).group(1)
            pairs = dict(
                re.findall(
                    r"`(\w+)` = ('(?:[^'\\]|\\.)*'|-?\d+)",
                    f"`id` = {guid} AND " + block,
                )
            )
            self.assertEqual(pairs, row)
            self.assertEqual(len(pairs), len(columns))

    def test_storage_counts_are_03_player_storage(self):
        counts = {
            guid: sum(1 for row in storage_seed() if int(row[0]) == guid)
            for guid in fx.PILOTS
        }
        for guid, count in counts.items():
            self.assertIn(
                f"FROM player_storage WHERE player_id = {guid}) <> {count} THEN",
                guard_part(),
            )

    def test_storage_rows_are_exactly_03_player_storage(self):
        # (player_id, key, value) of each pilot, as the guard lists them, equal 03_player_storage.sql, and the
        # schema's (player_id, key) primary key makes "N exact matches and N rows" set equality.
        listed = re.findall(
            r"SELECT (6500[134])(?: AS player_id)?, (-?\d+)(?: AS k)?, (-?\d+)(?: AS v)?",
            guard_part(),
        )
        self.assertEqual(
            sorted(tuple(map(int, row)) for row in listed), sorted(storage_seed())
        )
        self.assertEqual(len(listed), 299 + 133 + 300)
        self.assertIn(
            "CONSTRAINT `player_storage_pk` PRIMARY KEY (`player_id`, `key`),",
            (SOURCE / "schema.sql").read_text(),
        )
        for guid, count in ((65001, 299), (65003, 133), (65004, 300)):
            self.assertIn(
                f"s.`key` = e.k AND s.value = e.v) <> {count} THEN\n"
                f"    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'b1 seed: pilot {guid} storage rows",
                guard_part(),
            )

    def test_every_write_comes_after_the_whole_guard(self):
        end = SEED.index("END//")
        for pattern in (
            r"^CREATE TABLE",
            r"^INSERT INTO",
            r"^UPDATE",
            r"^DELETE",
            r"^START TRANSACTION",
        ):
            for match in re.finditer(pattern, SEED, re.MULTILINE):
                self.assertGreater(match.start(), end, pattern)
        self.assertIn("table_name = 'qa_b1_fixture') <> 0 THEN", guard_part())
        self.assertNotIn("IF NOT EXISTS", SEED)
        self.assertIn("reapplication refused", guard_part())

    def test_guard_passes_the_fresh_init_and_writes_reach_the_declared_state(self):
        db = fresh_db()
        self.assertEqual(failing(db, conditions(guard_part())), [])
        self.assertEqual(len(conditions(guard_part())), 3 + 2 + 5 + 3 + 3)
        apply_seed(db)
        post = conditions(SEED[SEED.rindex("DELIMITER //") :])
        self.assertEqual(len(post), 6)
        self.assertEqual(failing(db, post), [])
        self.assertEqual(run_slice(db), fx.expected_s0())
        self.assertEqual(fx.digest(run_slice(db)), S0_SLICE_SHA256)

    def test_a_bot_played_database_is_refused(self):
        checks = conditions(guard_part())
        for name, change in (
            (
                "experience",
                "UPDATE players SET experience = experience + 1 WHERE id = 65001",
            ),
            (
                "level",
                "UPDATE players SET level = 9, experience = 6400 WHERE id = 65003",
            ),
            ("balance", "UPDATE players SET balance = 5 WHERE id = 65004"),
            ("skills", "UPDATE players SET skill_sword = 101 WHERE id = 65001"),
            ("position", "UPDATE players SET posx = posx + 1 WHERE id = 65004"),
            ("items", "INSERT INTO player_items VALUES (65003, 3, 101, 2854, 1, '')"),
            ("depot", "INSERT INTO player_depotitems VALUES (65001)"),
            (
                "storage row deleted",
                "DELETE FROM player_storage WHERE player_id = 65004 AND `key` = 10001001",
            ),
            (  # same count: one value changed
                "storage value changed",
                "UPDATE player_storage SET value = value + 1 WHERE player_id = 65001 AND `key` = 10001001",
            ),
            (  # same count: one key replaced by another
                "storage key replaced",
                "UPDATE player_storage SET `key` = 99999999 WHERE player_id = 65003 AND `key` = 10001001",
            ),
            (
                "death",
                "INSERT INTO player_deaths VALUES (65001, 1, 8, 'a wolf', 0, 'a wolf', 0)",
            ),
            ("online", "INSERT INTO players_online VALUES (65003)"),
            ("human account", "INSERT INTO accounts VALUES (65001)"),
        ):
            with self.subTest(name):
                db = fresh_db()
                db.execute(change)
                self.assertTrue(failing(db, checks), name)

    def test_same_count_storage_mutations_pass_the_counts_but_not_the_rows(self):
        checks = conditions(guard_part())
        for change, guid in (
            (
                "UPDATE player_storage SET value = value + 1 WHERE player_id = 65001 AND `key` = 10001001",
                65001,
            ),
            (
                "UPDATE player_storage SET `key` = 99999999 WHERE player_id = 65003 AND `key` = 10001001",
                65003,
            ),
        ):
            with self.subTest(change):
                db = fresh_db()
                db.execute(change)
                self.assertEqual(
                    db.execute(
                        f"SELECT COUNT(*) FROM player_storage WHERE player_id = {guid}"
                    ).fetchone()[0],
                    {65001: 299, 65003: 133}[guid],
                )
                refused = failing(db, checks)
                self.assertEqual(len(refused), 1)
                self.assertIn(f"SELECT {guid} AS player_id", refused[0])

    def test_reapplication_is_refused(self):
        db = fresh_db()
        apply_seed(db)
        self.assertTrue(
            failing(db, conditions(guard_part()))
        )  # pilots no longer at the preimage
        self.assertIn(
            "IF (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = DATABASE() "
            "AND table_name = 'qa_b1_fixture') <> 0 THEN",
            SEED,
        )  # marker present (MariaDB only)

    def test_every_write_is_scoped_by_explicit_ids(self):
        statements = writes()
        self.assertEqual(len(statements), 5)
        for statement in statements:
            if statement.startswith(("UPDATE", "DELETE")):
                self.assertRegex(
                    statement,
                    r"WHERE `(id|player_id)` (= 6500[134]|IN \(65001, 65003, 65004\))",
                )
        self.assertEqual(
            re.findall(r"^INSERT INTO `(\w+)`", SEED, re.MULTILINE),
            ["qa_b1_fixture", "player_items"],
        )
        self.assertEqual(
            set(re.findall(r"\((\d+), \d+, \d+, \d+, \d+, ''\)", SEED)),
            {"65001", "65003", "65004"},
        )

    def test_no_account_password_or_human_character(self):
        for text in (SEED, LEADER, SLICE):
            text = "\n".join(
                line for line in text.splitlines() if not line.lstrip().startswith("--")
            )
            self.assertNotRegex(
                text.lower(), r"password|insert into `?accounts|insert into `?players\b"
            )
        self.assertNotRegex(LEADER, r"UPDATE `?accounts")


class LeaderTemplateTests(unittest.TestCase):
    def test_template_guards_ids_marker_and_online(self):
        for needle in (
            "qa_b1_fixture",
            "id >= 66100 AND account_id >= 65001",
            f"v = '{fx.MARKER}'",
            "id NOT IN (6, 65001, 65003, 65004)",
            "players_online",
            "another leader",
        ):
            self.assertIn(needle, LEADER)
        self.assertEqual(LEADER.count(fx.PLACEHOLDER), 1)
        for statement in re.findall(
            r"^(?:UPDATE|DELETE)[^;]*;", LEADER, re.MULTILINE | re.DOTALL
        ):
            self.assertIn("@b1_leader_id", statement)

    def test_template_numbers_skills_and_gear_match_the_declared_state(self):
        for vocation, (hp, mana, cap) in fx.VOCATION.items():
            self.assertIn(f"({vocation}, {hp}, {mana}, {cap})", LEADER)
            pairs = ", ".join(
                f"({pid}, {item})" for pid, item in sorted(fx.LOADOUT[vocation].items())
            )
            self.assertIn(
                f"(@b1_voc = {vocation} AND (pid, itemtype) IN ({pairs}))", LEADER
            )
        self.assertIn(
            "`maglevel` = 4, `skill_fist` = 50, `skill_club` = 50, `skill_sword` = 50",
            LEADER,
        )
        self.assertIn("= (50, 50, 50, 50, 50, 50, 50)", LEADER)

    def test_template_grants_no_balance_potions_or_coins(self):
        code = "\n".join(
            line for line in LEADER.splitlines() if not line.lstrip().startswith("--")
        )
        self.assertNotRegex(code.lower(), r"balance|bank")
        for item in fx.STOCK:
            self.assertNotRegex(code, rf"\b{item}\b")
        inserted = re.findall(r"^INSERT INTO `(\w+)`", code, re.MULTILINE)
        self.assertEqual(inserted, ["player_items", "qa_b1_fixture"])
        items = code[code.index("INSERT INTO `player_items`") :]
        items = items[: items.index(";")]
        self.assertEqual(
            sorted(re.findall(r"^  \(@b1_leader_id, (\d+),", items, re.MULTILINE)),
            ["1", "4", "5", "6", "7", "8"],
        )
        self.assertIn(
            "DELETE FROM `player_items` WHERE `player_id` = @b1_leader_id AND `pid` IN (1, 4, 5, 6, 7, 8);",
            code,
        )
        self.assertEqual(
            set(map(int, re.findall(r"\b(\d{4})\b", items))),
            {item for slots in fx.LOADOUT.values() for item in slots.values()},
        )

    def test_render_validates_the_name_and_needs_b1(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            b1_env(),
            patch.object(fx, "LEADER_SQL", Path(directory) / "leader.sql"),
        ):
            result = fx.render_leader("Daniel Leader")
            rendered = (Path(directory) / "leader.sql").read_text()
            self.assertIn("SET @b1_leader := 'Daniel Leader';", rendered)
            self.assertNotIn(fx.PLACEHOLDER, rendered)
            self.assertRegex(result["rendered_sha256"], r"^[0-9a-f]{64}$")
            for bad in (
                "O'Brien",
                "x",
                "Name; DROP",
                "Grizzle Alyronia",
                "a\\b",
                "Two  Spaces",
            ):
                with self.subTest(bad), self.assertRaises(ValueError):
                    fx.render_leader(bad)
        with (
            patch.dict(os.environ, {"CORE_QA_PROFILE": "stage1"}),
            self.assertRaisesRegex(RuntimeError, "refused"),
        ):
            fx.render_leader("Daniel Leader")


def leader_slice(
    vocation=3, name="Daniel Leader", guid=66100, account=65001, balance=0
):
    """A complete, consistent slice after leader-prep: the S0 pilots, the marker, one human and his blocks."""
    lines = [
        f"fixture\tfixture\t{fx.MARKER}",
        f"fixture\tleader\t{name}",
        "humans\t1\t1",
    ]
    pilots = [
        line
        for line in fx.expected_s0()
        if line.split("\t")[0] not in ("fixture", "humans")
    ]
    human = "\t".join(
        map(str, fx.player_fields(guid, account, name, vocation, balance))
    )
    slots = [
        f"slot\t{guid}\t{pid}\t{item}\t1"
        for pid, item in sorted({**fx.LOADOUT[vocation], 3: 1988}.items())
    ]
    stock = [f"stock\t{guid}\t{item}\t{7 if item == 266 else 0}" for item in fx.STOCK]
    by_tag = {}
    for line in pilots + [human] + slots + stock + [f"deaths\t{guid}\t0"]:
        by_tag.setdefault(line.split("\t")[0], []).append(line)
    return lines + [line for tag in fx.TAGS[2:] for line in by_tag.get(tag, [])]


class SliceTests(unittest.TestCase):
    def test_slice_is_read_only_and_covers_the_spec(self):
        self.assertIn("START TRANSACTION WITH CONSISTENT SNAPSHOT, READ ONLY;", SLICE)
        for statement in [s.strip() for s in SLICE.split(";") if s.strip()]:
            body = "\n".join(
                line for line in statement.splitlines() if not line.startswith("--")
            )
            self.assertRegex(
                body, r"^(SET SESSION TRANSACTION|START TRANSACTION|SELECT|COMMIT)"
            )
        for item in fx.STOCK:
            self.assertIn(f"SELECT {item}", SLICE)
        self.assertIn(
            "maglevel, skill_fist, skill_club, skill_sword, skill_axe, skill_dist, skill_shielding",
            SLICE,
        )
        self.assertEqual(tuple(re.findall(r"SELECT '(\w+)'", SLICE)), fx.TAGS)

    def test_s0_is_deterministic_pinned_and_its_own(self):
        lines = fx.expected_s0()
        self.assertEqual(len(lines), 2 + 3 + 21 + 21 + 3)
        self.assertEqual(fx.digest(lines), S0_SLICE_SHA256)
        self.assertEqual(fx.canonical("\r\n".join(lines) + "\r\n"), lines)
        self.assertEqual(fx.check(lines, "s0"), ([], {}))
        self.assertNotIn(S0_SLICE_SHA256, (HERE / "stage1_baseline.py").read_text())
        self.assertNotIn(S0_SLICE_SHA256, (HERE / "stage1-baseline.json").read_text())

    def test_slice_columns_are_named_as_slice_sql_selects_them(self):
        select = re.search(r"SELECT 'player', (.*?) FROM players", SLICE).group(1)
        self.assertEqual(tuple(select.split(", ")), fx.PLAYER_COLUMNS)
        self.assertEqual(set(fx.SHAPES), set(fx.TAGS))
        for line in fx.expected_s0():
            self.assertIsNotNone(fx.named(line.split("\t")), line)
        lines = fx.expected_s0()
        for bad in (
            "fixture\textra\tx\ty",
            "stock\t65001\t266",
            "slot\t65001\t1\tx\t1",
            "humans\t0",
        ):
            with self.subTest(bad):
                for stage in ("s0", "leader", "ready"):
                    problems = fx.check(lines + [bad], stage)[0]
                    self.assertIn(f"malformed: {bad.replace(chr(9), ' ')}", problems)

    def test_s0_names_every_difference(self):
        lines = fx.expected_s0()
        problems, _ = fx.check(
            [line.replace("\t20\t98800\t365", "\t19\t98800\t365") for line in lines],
            "s0",
        )
        self.assertEqual(len(problems), 2)
        self.assertEqual(
            fx.check(list(reversed(lines)), "s0")[0], ["line order differs"]
        )
        self.assertTrue(
            fx.check(lines + ["death\t65001\t1\t20\ta wolf\t0\ta wolf\t0"], "s0")[0]
        )
        self.assertTrue(
            any("duplicate" in p for p in fx.check(lines + [lines[-1]], "s0")[0])
        )
        with self.assertRaisesRegex(ValueError, "untagged"):
            fx.canonical("Warning: something\n")

    def test_leader_slice_complete_and_consistent_passes_with_observed_values(self):
        for vocation in fx.LOADOUT:
            problems, observed = fx.check(
                leader_slice(vocation, balance=1234), "leader"
            )
            self.assertEqual(problems, [], vocation)
            self.assertEqual(observed["balance"], "1234")
            self.assertEqual(observed["stock"]["266"], "7")
            self.assertEqual(observed["slots"]["3"], "1988")

    def test_leader_slice_refuses_every_inconsistency(self):
        good = leader_slice()

        def edit(old, new):
            return [new if line == old else line for line in good]

        cases = {
            "marker names another leader": edit(
                "fixture\tleader\tDaniel Leader", "fixture\tleader\tSomeone Else"
            ),
            "no leader in the marker": [
                line for line in good if not line.startswith("fixture\tleader")
            ],
            "old marker": edit(
                f"fixture\tfixture\t{fx.MARKER}", "fixture\tfixture\tb1-companions-v1"
            ),
            "ineligible account": leader_slice(account=65000),
            "humans count": edit("humans\t1\t1", "humans\t1\t2"),
            "humans missing": [line for line in good if not line.startswith("humans")],
            "leader death count": edit("deaths\t66100\t0", "deaths\t66100\t1"),
            "leader death row": good + ["death\t66100\t5\t20\ta wolf\t0\ta wolf\t0"],
            "leader deaths missing": [
                line for line in good if line != "deaths\t66100\t0"
            ],
            "stock block incomplete": [
                line for line in good if line != "stock\t66100\t3043\t0"
            ],
            "stock item not declared": good + ["stock\t66100\t2160\t1"],
            "slot not the loadout": edit(
                "slot\t66100\t6\t3277\t1", "slot\t66100\t6\t7378\t1"
            ),
            "slot missing": [
                line for line in good if line != "slot\t66100\t1\t3352\t1"
            ],
            "duplicate row": good + ["stock\t66100\t266\t9"],
            "second human": good
            + [
                "player\t66101"
                + good[[l.startswith("player\t66100") for l in good].index(True)][12:]
            ],
            "foreign slot": good + ["slot\t66200\t1\t3351\t1"],
            "pilot drift": [
                line.replace("\t14\n", "\t13\n")
                if line == "stock\t65001\t266\t14"
                else line
                for line in good
            ]
            + ["stock\t65001\t266\t13"],
            "pilot extra item": good + ["slot\t65001\t9\t3099\t1"],
            "leader not prepared": [
                line.replace("\t20\t98800\t305", "\t8\t4200\t305") for line in good
            ],
            "leader slot count 2": edit(
                "slot\t66100\t6\t3277\t1", "slot\t66100\t6\t3277\t2"
            ),
            "extra fixture row": good + ["fixture\textra\tx"],
            "extra malformed fixture row": good + ["fixture\textra\tx\ty"],
            "second leader row": good + ["fixture\tleader\tSomeone Else"],
            "malformed stock row": good + ["stock\t66100\t266"],
            "non-numeric slot": edit(
                "slot\t66100\t3\t1988\t1", "slot\t66100\t3\tbag\t1"
            ),
            "leader skills": [
                line.replace("\t4\t50\t50", "\t4\t10\t50")
                if line.startswith("player\t66100")
                else line
                for line in good
            ],
        }
        for name, lines in cases.items():
            with self.subTest(name):
                self.assertNotEqual(lines, good)
                self.assertTrue(fx.check(lines, "leader")[0], name)

    def test_ready_passes_the_fixture_money_and_records_the_leader(self):
        lines = leader_slice(balance=4321)
        # activation drift (HP, the ring of equipBot) is observed, not refused
        lines = [line.replace("\t365\t365\t95", "\t300\t365\t95") for line in lines] + [
            "slot\t65001\t9\t3099\t1"
        ]
        problems, observed = fx.check(lines, "ready")
        self.assertEqual(problems, [])
        self.assertEqual(observed["leader"]["balance"], "4321")
        self.assertEqual(observed["leader"]["stock"]["266"], "7")
        self.assertEqual(len(observed["pilots"]["65001"]), 2)
        self.assertEqual(observed["pilots"]["65003"], [])
        other = fx.check(leader_slice(balance=4322), "ready")[1]
        self.assertNotEqual(
            observed["leader"]["recorded_sha256"], other["leader"]["recorded_sha256"]
        )
        self.assertEqual(
            fx.check(leader_slice(balance=4321), "ready")[1]["leader"],
            observed["leader"],
        )

    def test_ready_refuses_funding_and_any_other_pilot_money(self):
        good = leader_slice()

        def pilot(guid, change):
            return [
                change(line) if line.split("\t")[1:2] == [str(guid)] else line
                for line in good
            ]

        def balance(value):
            return lambda line: (
                line.rsplit("\t", 1)[0] + f"\t{value}"
                if line.startswith("player")
                else line
            )

        cases = {
            "funding ran": (
                pilot(65003, balance(fx.SEED_BALANCE)),
                "bot_market_funding ran",
            ),
            "bank refilled": (pilot(65001, balance(500)), "balance 500, not 0"),
            "coins spent": (
                [
                    l.replace("stock\t65004\t3035\t100", "stock\t65004\t3035\t89")
                    for l in good
                ],
                "coins",
            ),
            "change in gold": (
                [
                    l.replace("stock\t65004\t3031\t0", "stock\t65004\t3031\t16")
                    for l in good
                ],
                "coins",
            ),
            "coin row missing": (
                [l for l in good if l != "stock\t65001\t3043\t0"],
                "coins",
            ),
            "pilot missing": (
                [l for l in good if not l.startswith("player\t65004")],
                "not exactly one player row",
            ),
            "no leader in the marker": (
                [l for l in good if not l.startswith("fixture\tleader")],
                "marker rows are not exactly",
            ),
            "leader stock incomplete": (
                [l for l in good if l != "stock\t66100\t3043\t0"],
                "stock rows are not exactly",
            ),
            "duplicate": (good + ["stock\t65001\t3035\t100"], "duplicate"),
        }
        for name, (lines, message) in cases.items():
            with self.subTest(name):
                self.assertNotEqual(lines, good)
                problems = fx.check(lines, "ready")[0]
                self.assertTrue(
                    any(message in problem for problem in problems), problems
                )

    def test_cli_check_reports_observed_and_exit_code(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / "l0.tsv"
            out.write_text("\n".join(leader_slice(balance=77)) + "\n")
            with patch("sys.stdout") as stdout:
                self.assertEqual(fx.main(["check", "leader", str(out)]), 0)
            printed = json.loads(
                "".join(call.args[0] for call in stdout.write.call_args_list)
            )
            self.assertEqual(printed["observed"]["balance"], "77")
            out.write_text("\n".join(fx.expected_s0()[1:]) + "\n")
            with patch("sys.stdout"):
                self.assertEqual(fx.main(["check", "s0", str(out)]), 1)


class ApplyPathTests(unittest.TestCase):
    def test_prepare_initdb_copies_stage1_files_and_adds_only_the_seed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            stage1, b1, evidence = (
                root / "runtime/initdb",
                root / "runtime/b1/initdb",
                root / "runtime/b1/evidence",
            )
            stage1.mkdir(parents=True)
            for name in ("000_schema.sql", "012_02_players.sql", "099_ids.sql"):
                (stage1 / name).write_text(f"-- {name}\n")
            before = {p.name: p.read_bytes() for p in stage1.iterdir()}
            with patch.multiple(fx, STAGE1_INITDB=stage1, INITDB=b1, EVIDENCE=evidence):
                with (
                    patch.dict(os.environ, {"CORE_QA_PROFILE": "stage1"}),
                    self.assertRaisesRegex(RuntimeError, "refused"),
                ):
                    fx.prepare_initdb()
                self.assertFalse(b1.exists())
                with b1_env():
                    b1.mkdir(parents=True)
                    (b1 / "stale.sql").write_text("stale")
                    manifest = fx.prepare_initdb()
            self.assertEqual({p.name: p.read_bytes() for p in stage1.iterdir()}, before)
            self.assertEqual(
                sorted(p.name for p in b1.iterdir()), [*sorted(before), fx.SEED_NAME]
            )
            self.assertEqual((b1 / fx.SEED_NAME).read_text(), SEED)
            self.assertEqual(
                json.loads((evidence / "initdb-manifest.json").read_text()), manifest
            )
            self.assertEqual(oct((b1 / fx.SEED_NAME).stat().st_mode & 0o777), "0o644")

    def test_prepare_initdb_refuses_without_prepare_py(self):
        with tempfile.TemporaryDirectory() as directory:
            missing = {
                "STAGE1_INITDB": Path(directory) / "none",
                "INITDB": Path(directory) / "b1",
            }
            with (
                b1_env(),
                patch.multiple(fx, **missing),
                self.assertRaisesRegex(RuntimeError, "prepare.py first"),
            ):
                fx.prepare_initdb()

    def test_b1_server_config_is_stage1_with_autonomous_off(self):
        stage1 = json.loads((HERE / "brain/server.json").read_text())
        b1 = json.loads((HERE / "b1/server.json").read_text())
        worker = json.loads((HERE / "brain/worker.json").read_text())
        self.assertEqual(b1, {**stage1, "autonomous_bot": 0})
        self.assertEqual(b1["socket_directory"], worker["socket_directory"])

    def test_only_the_b1_overlays_reach_the_fixture(self):
        self.assertIn(
            "      - ./runtime/b1/initdb:/docker-entrypoint-initdb.d:ro\n",
            (HERE / "compose.b1.yaml").read_text(),
        )
        self.assertIn(
            "      - ./b1/server.json:/etc/canary-core-qa/brain/server.json:ro\n",
            (HERE / "compose.b1-brain.yaml").read_text(),
        )
        for name in (
            "compose.yaml",
            "compose.brain-fake.yaml",
            "compose.game-pin.yaml",
            "prepare.py",
            "stage1_baseline.py",
            "stage2_handoff.py",
            "qa_return_attempt.py",
        ):
            text = (HERE / name).read_text()
            self.assertNotIn("b1/", text, name)
            self.assertNotIn("b1_fixture", text, name)


if __name__ == "__main__":
    unittest.main()
