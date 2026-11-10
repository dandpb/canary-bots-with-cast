"""Offline tests of the B1 companion fixture: its numbers against the source, its SQL scope and guards, the
canonical slice and the B1-only apply path. No Docker, git, network or SQL."""

import csv
import json
import os
import re
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch

import b1_fixture as fx

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent.parent
SEED = (HERE / "b1/seed-companions.sql").read_text()
LEADER = (HERE / "b1/leader-prep.sql.template").read_text()
SLICE = (HERE / "b1/slice.sql").read_text()
# Pinned: the slice of the fresh B1 database at S0 (fx.expected_s0) and the query that produces it.
S0_SLICE_SHA256 = "b90457a629fa43b3a25e6afd8d7deac0d1356b70fd68c183871fb8011a6b9084"
PILOT_NAMES = {
    65001: "Grizzle Alyronia",
    65003: "Sever Heartspear",
    65004: "Galdon Whitehoof",
}


def gains():
    root = ET.parse(SOURCE / "data/XML/vocations.xml").getroot()
    return {
        int(v.get("id")): tuple(
            int(v.get(k)) for k in ("gainhp", "gainmana", "gaincap")
        )
        for v in root
    }


def exp_for_level(level):  # Player::getExpForLevel, player.cpp:4299-4301
    return (((level - 6) * level + 17) * level - 12) // 6 * 100


def b1_env(**extra):
    return patch.dict(os.environ, {"CORE_QA_PROFILE": "b1", **extra})


class SourceNumbersTests(unittest.TestCase):
    def test_level_20_experience_is_the_server_formula(self):
        text = (SOURCE / "src/creatures/players/player.cpp").read_text()
        self.assertIn(
            "return (((level - 6ULL) * level + 17ULL) * level - 12ULL) / 6ULL * 100ULL;",
            text,
        )
        self.assertEqual(exp_for_level(20), fx.EXPERIENCE)
        self.assertLess(exp_for_level(20), exp_for_level(21))

    def test_hp_mana_cap_are_the_vocation_values_at_level_20(self):
        # Level 1 = schema defaults 150 HP / 0 mana (schema.sql) and capacity 40000 (= 400 oz, player.hpp);
        # levels 2-8 gain as vocation None, 9-20 as the vocation (player.cpp level-up loop).
        schema = (SOURCE / "schema.sql").read_text()
        self.assertIn("`health` int(11) NOT NULL DEFAULT '150'", schema)
        self.assertIn("`mana` int(11) NOT NULL DEFAULT '0'", schema)
        self.assertIn(
            "uint32_t capacity = 40000;",
            (SOURCE / "src/creatures/players/player.hpp").read_text(),
        )
        g = gains()
        for vocation, (hp, mana, cap) in fx.VOCATION.items():
            with self.subTest(vocation=vocation):
                self.assertEqual(hp, 150 + 7 * g[0][0] + 12 * g[vocation][0])
                self.assertEqual(mana, 0 + 7 * g[0][1] + 12 * g[vocation][1])
                self.assertEqual(cap, 400 + 7 * g[0][2] + 12 * g[vocation][2])
        self.assertEqual(
            fx.VOCATION[4][:2], (365, 95)
        )  # tests/fixture/m5_qa.py knight anchor
        self.assertGreaterEqual(
            fx.VOCATION[2][1], 120
        )  # druid party heal needs mana >= 120

    def test_loadout_is_the_equipment_csv_row_in_the_hands_equipbot_uses(self):
        rows = {
            int(r["vocation"]): r
            for r in csv.DictReader((SOURCE / "data/bot/authored/equipment.csv").open())
            if r["level"] == "20"
        }
        data = (SOURCE / "src/creatures/players/bot/bot_data.cpp").read_text()
        self.assertIn(
            'eq.weapon = static_cast<uint16_t>(t.getIntOr(i, "slot_right"', data
        )
        self.assertIn('{CONST_SLOT_LEFT, eq.weapon, "weapon"}', data)
        self.assertIn('{CONST_SLOT_RIGHT, eq.shield, "shield"}', data)
        for vocation, slots in fx.LOADOUT.items():
            row = rows[vocation]
            self.assertEqual(
                slots,
                {
                    1: int(row["slot_head"]),
                    4: int(row["slot_armor"]),
                    5: int(row["slot_left"]),
                    6: int(row["slot_right"]),
                    7: int(row["slot_legs"]),
                    8: int(row["slot_feet"]),
                },
            )
            self.assertEqual(int(row["slot_backpack"]), fx.BACKPACK)

    def test_item_ids_exist_with_their_names(self):
        items = (SOURCE / "data/items/items.xml").read_text()
        names = {
            266: "health potion",
            268: "mana potion",
            236: "strong health potion",
            237: "strong mana potion",
            3031: "gold coin",
            3035: "platinum coin",
            3043: "crystal coin",
            2854: "backpack",
            3423: "blessed shield",
        }
        used = {item for slots in fx.LOADOUT.values() for item in slots.values()} | set(
            names
        )
        for item in used:
            self.assertRegex(items, rf'<item id="{item}" [^>]*name="')
        for item, name in names.items():
            self.assertIn(f'<item id="{item}" article="a" name="{name}">', items)

    def test_potions_are_the_level_20_types_twenty_each_and_buyable(self):
        potions = (SOURCE / "src/creatures/players/bot/bot_potions.hpp").read_text()
        self.assertIn("{ 266, 0, true, false, VOC_ANY }", potions)
        self.assertIn("{ 268, 0, false, true, VOC_ANY }", potions)
        self.assertIn("{ 236, 50,", potions)  # not counted, not bought below level 50
        self.assertIn("{ 237, 50,", potions)
        xodet = (SOURCE / "data-otservbr-global/npc/xodet.lua").read_text()
        self.assertIn("clientId = 266, buy = 50", xodet)
        self.assertIn("clientId = 268, buy = 56", xodet)
        for _name, _vocation, stock in fx.PILOTS.values():
            self.assertEqual(set(stock), {266, 268})
            self.assertEqual(sum(stock.values()), 20)
            self.assertTrue(all(count < 20 for count in stock.values()))
            refill = (20 - stock[266]) * 50 + (20 - stock[268]) * 56
            self.assertLess(refill, fx.BANK)

    def test_thais_is_town_8(self):
        self.assertIn(
            "THAIS = 8,",
            (SOURCE / "data-otservbr-global/lib/tables/town.lua").read_text(),
        )


class SeedSqlTests(unittest.TestCase):
    def test_seed_rows_carry_exactly_the_declared_state(self):
        for guid, (name, vocation, stock) in fx.PILOTS.items():
            hp, mana, cap = fx.VOCATION[vocation]
            update = re.search(
                rf"UPDATE `players` SET ([^;]*?)\n\s+WHERE `id` = {guid} AND `name` = '{name}' "
                rf"AND `vocation` = {vocation} AND `account_id` = 65000;",
                SEED,
                re.DOTALL,
            )
            self.assertIsNotNone(update, guid)
            values = dict(re.findall(r"`(\w+)` = (\d+)", update.group(1)))
            self.assertEqual(
                values,
                {
                    k: str(v)
                    for k, v in {
                        "level": 20,
                        "experience": 98800,
                        "health": hp,
                        "healthmax": hp,
                        "mana": mana,
                        "manamax": mana,
                        "cap": cap,
                        "town_id": 8,
                        "posx": 32369,
                        "posy": 32241,
                        "posz": 7,
                        "balance": 10000,
                    }.items()
                },
            )
            self.assertIn(
                f"({guid}, 20, 98800, {hp}, {hp}, {mana}, {mana}, {cap}, 8, 32369, 32241, 7, 10000)",
                SEED,
            )
            rows = re.findall(rf"\({guid}, (\d+), (\d+), (\d+), (\d+), ''\)", SEED)
            slots = {
                int(pid): int(item)
                for pid, _sid, item, _count in rows
                if int(pid) <= 11
            }
            self.assertEqual(slots, {**fx.LOADOUT[vocation], 3: fx.BACKPACK})
            potions = {
                int(item): int(count) for pid, _sid, item, count in rows if pid == "103"
            }
            self.assertEqual(potions, stock)
            self.assertEqual(len({sid for _pid, sid, _item, _count in rows}), len(rows))

    def test_every_write_is_scoped_by_explicit_ids(self):
        statements = re.findall(
            r"^(UPDATE|DELETE|INSERT)[^;]*;", SEED, re.MULTILINE | re.DOTALL
        )
        self.assertEqual(len(statements), 6)
        for match in re.finditer(
            r"^(UPDATE `players`|DELETE FROM `player_items`)[^;]*;",
            SEED,
            re.MULTILINE | re.DOTALL,
        ):
            self.assertRegex(
                match.group(),
                r"WHERE `(id|player_id)` (= 6500[134]|IN \(65001, 65003, 65004\))",
            )
        inserts = re.findall(r"^INSERT INTO `(\w+)`", SEED, re.MULTILINE)
        self.assertEqual(inserts, ["qa_b1_fixture", "player_items"])
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
                text.lower(), r"password|insert into `?accounts|insert into `?players"
            )
        self.assertNotRegex(LEADER, r"UPDATE `?accounts")

    def test_seed_refuses_a_played_database_and_checks_its_result(self):
        self.assertIn("SELECT COUNT(*) FROM accounts WHERE id >= 65001) <> 0", SEED)
        self.assertIn("SELECT COUNT(*) FROM players WHERE id >= 66100) <> 0", SEED)
        self.assertEqual(SEED.count("SIGNAL SQLSTATE '45000'"), 6)
        self.assertEqual(SEED.count("DELIMITER //"), 2)
        self.assertTrue(SEED.rstrip().endswith("COMMIT;"))


class LeaderTests(unittest.TestCase):
    def test_template_guards_ids_marker_and_online(self):
        for needle in (
            "qa_b1_fixture",
            "id >= 66100 AND account_id >= 65001",
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

    def test_template_numbers_match_the_declared_state(self):
        for vocation, (hp, mana, cap) in fx.VOCATION.items():
            self.assertIn(f"({vocation}, {hp}, {mana}, {cap})", LEADER)
        for vocation, slots in fx.LOADOUT.items():
            for item in slots.values():
                self.assertIn(str(item), LEADER)

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


class SliceTests(unittest.TestCase):
    def output(self, lines):
        return "\n".join(lines) + "\n"

    def test_slice_is_read_only_and_covers_the_spec(self):
        self.assertIn("START TRANSACTION WITH CONSISTENT SNAPSHOT, READ ONLY;", SLICE)
        statements = [
            s.strip()
            for s in SLICE.split(";")
            if s.strip() and not s.strip().startswith("--")
        ]
        for statement in statements:
            body = "\n".join(
                line for line in statement.splitlines() if not line.startswith("--")
            )
            self.assertRegex(
                body, r"^(SET SESSION TRANSACTION|START TRANSACTION|SELECT|COMMIT)"
            )
        for item in fx.STOCK:
            self.assertIn(f"SELECT {item}", SLICE)
        self.assertIn("player_deaths", SLICE)
        self.assertEqual(tuple(re.findall(r"SELECT '(\w+)'", SLICE)), fx.TAGS)

    def test_s0_is_deterministic_pinned_and_its_own(self):
        lines = fx.expected_s0()
        self.assertEqual(len(lines), 2 + 3 + 21 + 21 + 3)
        self.assertEqual(fx.digest(lines), S0_SLICE_SHA256)
        self.assertEqual(fx.canonical(self.output(lines).replace("\n", "\r\n")), lines)
        self.assertEqual(fx.check(lines, "s0"), [])
        stage1 = (HERE / "stage1_baseline.py").read_text()
        self.assertNotIn(S0_SLICE_SHA256, stage1)
        self.assertNotIn(S0_SLICE_SHA256, (HERE / "stage1-baseline.json").read_text())

    def test_check_names_every_difference(self):
        lines = fx.expected_s0()
        changed = [
            line.replace("\t20\t98800\t365", "\t19\t98800\t365") for line in lines
        ]
        problems = fx.check(changed, "s0")
        self.assertEqual(len(problems), 2)
        self.assertTrue(any("missing: player\t65001" in p for p in problems))
        self.assertEqual(fx.check(list(reversed(lines)), "s0"), ["line order differs"])
        self.assertTrue(
            fx.check(lines + ["death\t65001\t1\t20\ta wolf\t0\ta wolf\t0"], "s0")
        )
        with self.assertRaisesRegex(ValueError, "untagged"):
            fx.canonical("Warning: something\n")

    def test_leader_stage_accepts_a_prepared_leader_only(self):
        hp, mana, cap = fx.VOCATION[3]
        base = [line for line in fx.expected_s0() if not line.startswith("humans")]
        leader = [
            f"player\t66100\t65001\tDaniel Leader\t3\t20\t98800\t{hp}\t{hp}\t{mana}\t{mana}\t{cap}"
            + "\t8\t32369\t32241\t7\t0"
        ]
        slots = [
            f"slot\t66100\t{pid}\t{item}\t1" for pid, item in fx.LOADOUT[3].items()
        ]
        good = [
            "fixture\tleader\tDaniel Leader",
            *base,
            "humans\t1\t1",
            *leader,
            *slots,
        ]
        self.assertEqual(fx.check(good, "leader"), [])
        self.assertTrue(
            fx.check(
                [line for line in good if not line.startswith("fixture\tleader")],
                "leader",
            )
        )
        self.assertTrue(
            fx.check(
                [line.replace("\t8\t32369", "\t1\t32369") for line in good], "leader"
            )
        )
        self.assertTrue(fx.check(good[:-1], "leader"))

    def test_cli_check_exit_code(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / "s0.tsv"
            out.write_text(self.output(fx.expected_s0()))
            with patch("sys.stdout"):
                self.assertEqual(fx.main(["check", "s0", str(out)]), 0)
                out.write_text(self.output(fx.expected_s0()[1:]))
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
                    (b1.mkdir(parents=True), (b1 / "stale.sql").write_text("stale"))
                    manifest = fx.prepare_initdb()
            self.assertEqual({p.name: p.read_bytes() for p in stage1.iterdir()}, before)
            self.assertEqual(
                sorted(p.name for p in b1.iterdir()), [*sorted(before), fx.SEED_NAME]
            )
            self.assertEqual((b1 / fx.SEED_NAME).read_text(), SEED)
            self.assertEqual(
                sorted(manifest["files"]), sorted(p.name for p in b1.iterdir())
            )
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

    def test_overlay_enables_only_hunt_399_and_changes_nothing_else(self):
        source = fx.HUNTS.read_text()
        overlay = fx.overlay_text(source)
        rows = list(csv.DictReader(overlay.splitlines()))
        self.assertEqual([r["id"] for r in rows if r["enabled"] == "1"], ["399"])
        original = list(csv.DictReader(source.splitlines()))
        self.assertEqual(len(rows), len(original))
        for new, old in zip(rows, original):
            self.assertEqual(
                {k: v for k, v in new.items() if k != "enabled"},
                {k: v for k, v in old.items() if k != "enabled"},
            )
        self.assertEqual(overlay.count("\n"), source.count("\n"))

    def test_b1_server_config_is_stage1_with_autonomous_off(self):
        stage1 = json.loads((HERE / "brain/server.json").read_text())
        b1 = json.loads((HERE / "b1/server.json").read_text())
        worker = json.loads((HERE / "brain/worker.json").read_text())
        self.assertEqual(b1, {**stage1, "autonomous_bot": 0})
        self.assertEqual(b1["bots"], [65001, 65004, 65003])
        self.assertEqual(b1["socket_directory"], worker["socket_directory"])

    def test_only_the_b1_overlays_reach_the_fixture(self):
        b1 = (HERE / "compose.b1.yaml").read_text()
        brain = (HERE / "compose.b1-brain.yaml").read_text()
        self.assertIn(
            "      - ./runtime/b1/initdb:/docker-entrypoint-initdb.d:ro\n", b1
        )
        self.assertIn(
            "      - ./b1/server.json:/etc/canary-core-qa/brain/server.json:ro\n", brain
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
