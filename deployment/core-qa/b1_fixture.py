"""B1 companion fixture only (CORE_QA_PROFILE=b1): the B1 initdb, the leader preparation, the authored
overlays and the canonical read-only DB slice. Offline: no Docker, git, network or SQL runs here (the overlay
install is only printed). B1_FIXTURE.md is the procedure; stage 1 (runtime/initdb, brain/server.json, its
volumes and baseline) is only read, never written or targeted."""

import argparse
import csv
import hashlib
import json
import os
import re
import shlex
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent.parent
SEED = HERE / "b1/seed-companions.sql"
LEADER_TEMPLATE = HERE / "b1/leader-prep.sql.template"
SLICE_SQL = HERE / "b1/slice.sql"
STAGE1_INITDB = HERE / "runtime/initdb"  # prepare.py writes it; read only here
INITDB = HERE / "runtime/b1/initdb"  # only compose.b1.yaml binds it
SEED_NAME = "900_b1_seed_companions.sql"  # after 000..099 of prepare.py
LEADER_SQL = HERE / "runtime/b1/leader-prep.sql"
AUTHORED = SOURCE / "data/bot/authored"
OVERLAY_DIR = HERE / "runtime/b1/authored"
OVERLAY_HUNTS = {"399"}  # v4 2.3: only Thais Paw Collector
EVIDENCE = HERE / "runtime/b1/evidence"
METHOD = "b1-fixture-slice-v2"
MARKER = "b1-companions-v3"
PLACEHOLDER = "@@LEADER_NAME@@"
PROJECT = "canary-qa-b1"
AUTHORED_TARGET = (
    "/canary/data/bot/authored"  # compose.yaml authored-data mount; BOT_AUTHORED_DIR
)

# Declared state (B1_FIXTURE.md has the sources). Per vocation at level 20: HP, mana, cap.
LEVEL, EXPERIENCE, TOWN, TEMPLE = 20, 98800, 8, (32369, 32241, 7)
SKILLS, MAGLEVEL = (
    50,
    4,
)  # simplified QA fixture: fist, club, sword, axe, distance, shielding, fishing
VOCATION = {
    1: (245, 395, 590),
    2: (245, 395, 590),
    3: (305, 215, 710),
    4: (365, 95, 770),
}
# B1 starter loadout by slot (1 head, 4 armor, 5 shield, 6 weapon, 7 legs, 8 feet; equipBot puts the
# equipment.csv slot_right weapon in slot 6 and slot_left in 5). Written to the B1 equipment.csv overlay for every
# level in OVERLAY_LEVELS, so equipBot re-equips exactly this.
LOADOUT = {
    1: {1: 3355, 4: 3361, 5: 3412, 6: 3074, 7: 3362, 8: 3552},
    2: {1: 3355, 4: 3361, 5: 3412, 6: 3066, 7: 3362, 8: 3552},
    3: {1: 3352, 4: 3359, 5: 3409, 6: 3277, 7: 3372, 8: 3552},
    4: {1: 3351, 4: 3357, 5: 3409, 6: 3264, 7: 3557, 8: 3552},
}
OVERLAY_LEVELS = range(20, 30)
BACKPACK = 2854
SEED_BALANCE = (
    100000000000  # 02_players.sql (the preimage), and what bot_market_funding.lua sets
)
PILOT_BALANCE = (
    0  # B1 common budget: no bank; b1/bot_market_funding.lua keeps the funding off
)
FUNDING_NOOP = (
    HERE / "b1/bot_market_funding.lua"
)  # compose.b1.yaml binds it read-only over FUNDING_TARGET
FUNDING_SOURCE = SOURCE / "data/scripts/globalevents/bot_market_funding.lua"
FUNDING_TARGET = "/canary/data/scripts/globalevents/bot_market_funding.lua"
READY_SLICE = "runtime/b1/evidence/ready/db-slice.tsv"  # the readiness slice, before T0
LOADOUT_SCOPE = (
    "every B1 bot of level 20-29 (vocations 1-4), not only the pilots, gets the B1 starter loadout when it is "
    "activated (equipBot); the other levels keep the source rows"
)
PILOTS = {  # id: name, vocation, potions (health 266, mana 268): 20 in all, each type under 20
    65001: ("Grizzle Alyronia", 4, {266: 14, 268: 6}),
    65003: ("Sever Heartspear", 3, {266: 10, 268: 10}),
    65004: ("Galdon Whitehoof", 2, {266: 6, 268: 14}),
}
COINS = {
    3031: 0,
    3035: 100,
    3043: 0,
}  # 100 platinum coins = 10000 gp, in the backpack; no gold, no crystal
WORTH = {3031: 1, 3035: 100, 3043: 10000}  # Item::getWorth (src/items/item.cpp)
BUDGET = 10000
STOCK = (236, 237, 266, 268, 3031, 3035, 3043)
TAGS = ("fixture", "humans", "player", "slot", "stock", "deaths", "death")
LEADER_NAME = re.compile(r"[A-Za-z][A-Za-z -]{1,27}[A-Za-z]")


def require_b1():
    if os.environ.get("CORE_QA_PROFILE") != "b1":
        raise RuntimeError(
            "b1_fixture writes only under CORE_QA_PROFILE=b1 (project canary-qa-b1); refused"
        )


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def player_fields(guid, account, name, vocation, balance):
    hp, mana, cap = VOCATION[vocation]
    skills = (SKILLS,) * 7
    return [
        "player",
        guid,
        account,
        name,
        vocation,
        LEVEL,
        EXPERIENCE,
        hp,
        hp,
        mana,
        mana,
        cap,
        MAGLEVEL,
        *skills,
        TOWN,
        *TEMPLE,
        balance,
    ]


def pilot_lines(guid):
    name, vocation, potions = PILOTS[guid]
    slots = {**LOADOUT[vocation], 3: BACKPACK}
    stock = {**potions, **COINS}
    return {
        "player": [
            "\t".join(
                map(str, player_fields(guid, 65000, name, vocation, PILOT_BALANCE))
            )
        ],
        "slot": [f"slot\t{guid}\t{pid}\t{slots[pid]}\t1" for pid in sorted(slots)],
        "stock": [f"stock\t{guid}\t{item}\t{stock.get(item, 0)}" for item in STOCK],
        "deaths": [f"deaths\t{guid}\t0"],
    }


def expected_s0():
    """The exact slice of the fresh B1 database after init, before MyAAC and the first game start."""
    lines = {"fixture": [f"fixture\tfixture\t{MARKER}"], "humans": ["humans\t0\t0"]}
    for guid in sorted(PILOTS):
        for tag, rows in pilot_lines(guid).items():
            lines.setdefault(tag, []).extend(rows)
    return [line for tag in TAGS for line in lines.get(tag, [])]


def canonical(text):
    """The `mariadb -N -B` output of slice.sql as its tagged lines, in output order; anything else is refused."""
    lines = [line.rstrip("\r") for line in text.split("\n") if line.strip()]
    foreign = [line for line in lines if line.split("\t", 1)[0] not in TAGS]
    if foreign:
        raise ValueError(
            f"slice output has {len(foreign)} untagged line(s); not a b1/slice.sql output"
        )
    return lines


def digest(lines):
    return sha256("".join(line + "\n" for line in lines).encode())


# The columns of each slice line after its tag, as b1/slice.sql selects them (a test compares the two).
PLAYER_COLUMNS = (
    "id", "account_id", "name", "vocation", "level", "experience", "health", "healthmax", "mana", "manamax",
    "cap", "maglevel", "skill_fist", "skill_club", "skill_sword", "skill_axe", "skill_dist", "skill_shielding",
    "skill_fishing", "town_id", "posx", "posy", "posz", "balance",
)  # fmt: skip
SHAPES = {
    "fixture": ("k", "v"),
    "humans": ("accounts", "players"),
    "player": PLAYER_COLUMNS,
    "slot": ("player_id", "pid", "itemtype", "count"),
    "stock": ("player_id", "itemtype", "count"),
    "deaths": ("player_id", "count"),
    "death": ("player_id", "time", "level", "killed_by", "is_player", "mostdamage_by", "mostdamage_is_player"),
}  # fmt: skip
TEXT_COLUMNS = {"k", "v", "name", "killed_by", "mostdamage_by"}
KEY_WIDTH = {"fixture": 1, "humans": 0, "player": 1, "slot": 2, "stock": 2, "deaths": 1}


def named(fields):
    """A slice row as {column: value}, or None when its shape is not the slice's (column count or a number)."""
    columns = SHAPES.get(fields[0])
    if columns is None or len(fields) != len(columns) + 1:
        return None
    row = dict(zip(columns, fields[1:]))
    if any(
        not re.fullmatch(r"-?\d+", value)
        for column, value in row.items()
        if column not in TEXT_COLUMNS
    ):
        return None
    return row


def row_key(fields):
    """The identity of a slice row: one row per key, or the slice is contradictory."""
    width = KEY_WIDTH.get(fields[0], len(fields) - 1)
    return tuple(fields[: 1 + width])


def shape_problems(rows):
    keys = [row_key(fields) for fields in rows]
    problems = [
        f"duplicate: {' '.join(key)}"
        for index, key in enumerate(keys)
        if key in keys[:index]
    ]
    problems += [
        f"malformed: {' '.join(fields)}" for fields in rows if named(fields) is None
    ]
    return problems


def marker(rows):
    """The marker rows as {k: v} when they are exactly the B1 marker and one leader name, else None."""
    fixture = [named(fields) for fields in rows if fields[0] == "fixture"]
    pairs = {row["k"]: row["v"] for row in fixture if row}
    if (
        len(fixture) != 2
        or pairs.keys() != {"fixture", "leader"}
        or pairs["fixture"] != MARKER
    ):
        return None
    return pairs


def the_leader(rows, pairs):
    """The one player row >= 66100, named as the marker's leader, of an account >= 65001 and vocation 1-4."""
    humans = [
        named(fields) for fields in rows if fields[0] == "player" and named(fields)
    ]
    humans = [row for row in humans if int(row["id"]) >= 66100]
    if pairs is None or len(humans) != 1 or humans[0]["name"] != pairs["leader"]:
        return None, "not exactly one character >= 66100 named as the marker's leader"
    human = humans[0]
    if int(human["account_id"]) < 65001 or int(human["vocation"]) not in VOCATION:
        return None, f"leader {human['id']} account or vocation is not eligible"
    return human, None


def check_ready(lines, rows):
    """After the game start (the funding window past) and before T0: the pilots' money is still the fixture
    (balance 0, exactly the fixture coins, worth 10000); 100000000000 means bot_market_funding ran. The marker
    names the one leader; his balance and stock are recorded as observed (hashed), never expected. Other
    pilot changes (activation: HP, ring, position) are observed, not refused."""
    problems, observed = [], {"pilots": {}}
    good = [
        (line, fields, named(fields))
        for line, fields in zip(lines, rows)
        if named(fields)
    ]
    for guid in sorted(PILOTS):
        mine = [
            (line, fields, row) for line, fields, row in good if fields[1] == str(guid)
        ]
        player = [row for _line, fields, row in mine if fields[0] == "player"]
        stock = {
            row["itemtype"]: row["count"]
            for _line, fields, row in mine
            if fields[0] == "stock"
        }
        if len(player) != 1:
            problems.append(f"pilot {guid}: not exactly one player row")
            continue
        balance = player[0]["balance"]
        if balance == str(SEED_BALANCE):
            problems.append(
                f"pilot {guid}: balance {SEED_BALANCE}: bot_market_funding ran (B1 bind missing?)"
            )
        elif balance != str(PILOT_BALANCE):
            problems.append(f"pilot {guid}: balance {balance}, not {PILOT_BALANCE}")
        coins = {item: stock.get(str(item)) for item in COINS}
        if coins != {item: str(count) for item, count in COINS.items()}:
            problems.append(f"pilot {guid}: coins {coins}, not the fixture {COINS}")
        expected = {line for block in pilot_lines(guid).values() for line in block}
        observed["pilots"][str(guid)] = [
            line for line, _fields, _row in mine if line not in expected
        ]
    pairs = marker(rows)
    if pairs is None:
        problems.append("marker rows are not exactly the B1 marker and one leader")
    if [fields for fields in rows if fields[0] == "humans"] != [["humans", "1", "1"]]:
        problems.append(
            "humans is not exactly one account >= 65001 and one character >= 66100"
        )
    human, refused = the_leader(rows, pairs)
    if human is None:
        return problems + [refused], observed
    guid = human["id"]
    stock = [
        line
        for line, fields, _row in good
        if fields[0] == "stock" and fields[1] == guid
    ]
    if sorted(line.split("\t")[2] for line in stock) != sorted(map(str, STOCK)):
        problems.append(f"leader {guid} stock rows are not exactly {STOCK}")
    recorded = [f"balance\t{guid}\t{human['balance']}", *stock]
    observed["leader"] = {
        "balance": human["balance"],
        "stock": {line.split("\t")[2]: line.split("\t")[3] for line in stock},
        "recorded_sha256": digest(recorded),
    }
    return problems, observed


def check(lines, stage):
    """Problems of a slice against the declared state, and the observed values that are not declared. Every
    row must have its tag's shape and appear once per key (shape_problems), in every stage.

    s0: exactly expected_s0(). leader: exactly the S0 pilot rows, the two marker rows naming the one leader,
    humans 1 1, and the leader's rows complete: his player row as leader-prep declares it (balance observed),
    his six loadout slots as whole rows (item, count 1; other slots observed), one stock row per STOCK item
    (observed), deaths 0 and no death row. ready: check_ready."""
    rows = [line.split("\t") for line in lines]
    problems = shape_problems(rows)
    if stage == "ready":
        ready_problems, observed = check_ready(lines, rows)
        return problems + ready_problems, observed
    if stage == "s0":
        expected = expected_s0()
        problems += [f"missing: {line}" for line in expected if line not in lines]
        problems += [f"unexpected: {line}" for line in lines if line not in expected]
        if not problems and lines != expected:
            problems.append("line order differs")
        return problems, {}
    pilots = [
        line
        for line in expected_s0()
        if line.split("\t")[0] not in ("fixture", "humans")
    ]
    problems += [f"missing: {line}" for line in pilots if line not in lines]
    pairs = marker(rows)
    if pairs is None:
        problems.append("marker rows are not exactly the B1 marker and one leader")
    if [fields for fields in rows if fields[0] == "humans"] != [["humans", "1", "1"]]:
        problems.append(
            "humans is not exactly one account >= 65001 and one character >= 66100"
        )
    human, refused = the_leader(rows, pairs)
    if human is None:
        return problems + [refused], {}
    guid, vocation = human["id"], int(human["vocation"])
    declared = dict(
        zip(
            PLAYER_COLUMNS,
            map(
                str,
                player_fields(
                    int(guid),
                    human["account_id"],
                    pairs["leader"],
                    vocation,
                    human["balance"],
                )[1:],
            ),
        )
    )
    if human != declared:
        changed = sorted(
            column for column in PLAYER_COLUMNS if human[column] != declared[column]
        )
        problems.append(f"leader {guid} row differs in {', '.join(changed)}")
    allowed = set(pilots) | {
        "humans\t1\t1",
        f"fixture\tfixture\t{MARKER}",
        f"fixture\tleader\t{pairs['leader']}",
    }
    allowed.add("\t".join(["player", *human.values()]))
    required = [
        f"slot\t{guid}\t{pid}\t{item}\t1"
        for pid, item in sorted(LOADOUT[vocation].items())
    ]
    problems += [
        f"leader {guid} lacks the declared slot row {line!r}"
        for line in required
        if line not in lines
    ]
    good = [
        (line, fields, named(fields))
        for line, fields in zip(lines, rows)
        if named(fields)
    ]
    slots = [
        (line, row)
        for line, fields, row in good
        if fields[0] == "slot" and fields[1] == guid
    ]
    allowed |= {line for line, row in slots if 1 <= int(row["pid"]) <= 11}
    stock = [
        (line, row)
        for line, fields, row in good
        if fields[0] == "stock" and fields[1] == guid
    ]
    if sorted(row["itemtype"] for _line, row in stock) != sorted(map(str, STOCK)):
        problems.append(f"leader {guid} stock rows are not exactly {STOCK}")
    allowed |= {line for line, _row in stock}
    deaths = f"deaths\t{guid}\t0"
    if deaths not in lines:
        problems.append(f"leader {guid} deaths is not 0 before the game")
    allowed.add(deaths)
    problems += [f"unexpected: {line}" for line in lines if line not in allowed]
    observed = {
        "balance": human["balance"],
        "slots": {row["pid"]: row["itemtype"] for _line, row in slots},
        "stock": {row["itemtype"]: row["count"] for _line, row in stock},
    }
    return problems, observed


def prepare_initdb():
    """runtime/b1/initdb = the files of runtime/initdb, byte for byte, plus the B1 seed. Returns the manifest."""
    require_b1()
    sources = sorted(path for path in STAGE1_INITDB.glob("*") if path.is_file())
    if not sources or any(
        path.suffix != ".sql" or path.name >= SEED_NAME for path in sources
    ):
        raise RuntimeError(
            "runtime/initdb is empty or unexpected; run prepare.py first"
        )
    os.umask(0o077)
    INITDB.mkdir(parents=True, exist_ok=True)
    for stale in INITDB.glob("*"):
        stale.unlink()
    for source, name in [(path, path.name) for path in sources] + [(SEED, SEED_NAME)]:
        shutil.copyfile(source, INITDB / name)
        (INITDB / name).chmod(0o644)
    INITDB.chmod(0o755)
    manifest = {
        "profile": "b1",
        "initdb": "runtime/b1/initdb",
        "files": {
            path.name: sha256(path.read_bytes()) for path in sorted(INITDB.glob("*"))
        },
        "seed_sha256": sha256(SEED.read_bytes()),
    }
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    (EVIDENCE / "initdb-manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    )
    return manifest


def render_leader(name):
    if (
        not LEADER_NAME.fullmatch(name)
        or "  " in name
        or name in {pilot[0] for pilot in PILOTS.values()}
    ):
        raise ValueError(
            "leader name must be 3-29 letters, spaces or hyphens and not a pilot; refused"
        )
    require_b1()
    template = LEADER_TEMPLATE.read_text()
    if template.count(PLACEHOLDER) != 1:
        raise RuntimeError(
            "leader template must hold the name placeholder exactly once"
        )
    LEADER_SQL.parent.mkdir(parents=True, exist_ok=True)
    LEADER_SQL.write_text(template.replace(PLACEHOLDER, name))
    return {
        "template_sha256": sha256(template.encode()),
        "rendered_sha256": sha256(LEADER_SQL.read_bytes()),
    }


def rewrite_column(text, change):
    """text (CSV, header first) with change(row) -> new row applied to each data line. Only the columns that
    change are rewritten, and only when they and every column after them are unquoted; all other bytes,
    quoted names and line endings included, stay as in the source."""
    lines = text.splitlines(keepends=True)
    header = lines[0].rstrip("\r\n").split(",")
    out = [lines[0]]
    for line in lines[1:]:
        body = line.rstrip("\r\n")
        fields = next(csv.reader([body]))
        if len(fields) != len(header):
            raise ValueError(f"CSV line is not as expected: {body[:40]!r}")
        row = dict(zip(header, fields))
        new = change(row)
        changed = [
            index
            for index, column in enumerate(header)
            if new and str(new[column]) != row[column]
        ]
        if not changed:
            out.append(line)
            continue
        head, *tail = body.rsplit(",", len(header) - changed[0])
        if fields[changed[0] :] != tail or '"' in ",".join(tail):
            raise ValueError(
                f"CSV line to rewrite is not plain after column {header[changed[0]]}: {body[:40]!r}"
            )
        tail = [str(new[column]) for column in header[changed[0] :]]
        out.append(",".join([head, *tail]) + line[len(body) :])
    return "".join(out)


def hunts_overlay(text):
    """hunt_scripts.csv with only OVERLAY_HUNTS enabled."""
    return rewrite_column(
        text, lambda row: {**row, "enabled": "1" if row["id"] in OVERLAY_HUNTS else "0"}
    )


def equipment_overlay(text):
    """equipment.csv with the B1 starter loadout for every vocation at OVERLAY_LEVELS; other rows unchanged."""

    def change(row):
        level, vocation = int(row["level"]), int(row["vocation"])
        if level not in OVERLAY_LEVELS or vocation not in LOADOUT:
            return None
        slots = LOADOUT[vocation]
        return {
            **row,
            "slot_head": slots[1],
            "slot_armor": slots[4],
            "slot_legs": slots[7],
            "slot_feet": slots[8],
            "slot_right": slots[6],
            "slot_left": slots[5],
            "slot_backpack": BACKPACK,
        }

    overlay = rewrite_column(text, change)
    rows = {
        (row["level"], row["vocation"]) for row in csv.DictReader(overlay.splitlines())
    }
    if (
        not {
            (str(level), str(vocation))
            for level in OVERLAY_LEVELS
            for vocation in LOADOUT
        }
        <= rows
    ):
        raise ValueError(
            "equipment.csv lacks a level/vocation row the B1 overlay must replace"
        )
    return overlay


OVERLAYS = {"equipment.csv": equipment_overlay, "hunt_scripts.csv": hunts_overlay}


def render_overlays():
    """runtime/b1/authored/<file> for each overlay, with source and overlay hashes (overlay-manifest.json)."""
    require_b1()
    OVERLAY_DIR.mkdir(parents=True, exist_ok=True)
    manifest = {
        "profile": "b1",
        "target": AUTHORED_TARGET,
        "files": {},
        "loadout_scope": LOADOUT_SCOPE,
        "binds": {FUNDING_TARGET: funding_bind()},
    }
    for name, render in OVERLAYS.items():
        source = (AUTHORED / name).read_bytes()
        (OVERLAY_DIR / name).write_text(render(source.decode()))
        (OVERLAY_DIR / name).chmod(0o644)
        manifest["files"][name] = {
            "source_sha256": sha256(source),
            "overlay_sha256": sha256((OVERLAY_DIR / name).read_bytes()),
        }
    OVERLAY_DIR.chmod(0o755)
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    (EVIDENCE / "overlay-manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    )
    return manifest


def funding_bind():
    """The funding no-op is not in authored-data (that volume is /canary/data/bot/authored; the script is
    /canary/data/scripts/globalevents in the image): compose.b1.yaml binds it read-only, and the preflight
    requires that bind in every B1 render (PROFILES["b1"]["binds"], assert_profile_binds)."""
    return {
        "source": str(FUNDING_NOOP.relative_to(HERE)),
        "sha256": sha256(FUNDING_NOOP.read_bytes()),
        "replaces_sha256": sha256(FUNDING_SOURCE.read_bytes()),
        "via": "compose.b1.yaml read-only bind, not authored-data",
    }


def b1_project(project=None):
    """project (default canary-qa-b1) if it is the B1 project of the preflight profiles, else refused."""
    import preflight  # the profile table is the single source of the project names

    project = project or PROJECT
    require_b1()
    b1, stage1 = (
        preflight.PROFILES["b1"]["project"],
        preflight.PROFILES["stage1"]["project"],
    )
    if project != b1 or project.startswith(stage1) or stage1 in project:
        raise RuntimeError(
            f"overlay install is for the B1 project {b1} only, never {stage1}; refused"
        )
    return project, stage1


def compose_argv(project):
    return [
        "env",
        "-u",
        "MARIADB_PASSWORD",
        "-u",
        "MARIADB_ROOT_PASSWORD",
        "-u",
        "BOT_PLAYERS_ONLINE",
        "docker",
        "compose",
        "-p",
        project,
        "-f",
        "compose.yaml",
        "-f",
        "compose.brain-fake.yaml",
        "-f",
        "compose.b1.yaml",
        "-f",
        "compose.b1-brain.yaml",
        "--env-file",
        ".env",
    ]


def install_commands(project=None):
    """The future, NOT executed, commands that put the overlays into the B1 authored-data volume. Only the
    canary-qa-b1 project and its own volume and image; anything that could name stage 1 is refused."""
    project, stage1 = b1_project(project)
    volume, image = f"{project}_authored-data", f"{project}-game:local"
    files = sorted(OVERLAYS)
    compose = compose_argv(project)
    copy = " && ".join(
        [
            f"cp {' '.join(f'/b1-overlay/{name}' for name in files)} {AUTHORED_TARGET}/",
            f"sha256sum {' '.join(f'{AUTHORED_TARGET}/{name}' for name in files)}",
        ]
    )
    commands = [
        [*compose, "create", "--no-build", "--pull", "never", "game"],
        [
            "docker",
            "run",
            "--rm",
            "--pull",
            "never",
            "--network",
            "none",
            "-v",
            f"{volume}:{AUTHORED_TARGET}",
            "-v",
            f"{OVERLAY_DIR}:/b1-overlay:ro",
            "--entrypoint",
            "sh",
            image,
            "-c",
            copy,
        ],
    ]
    if any(stage1 in part for command in commands for part in command):
        raise RuntimeError(f"overlay install names {stage1}; refused")
    return [shlex.join(command) for command in commands]


def readiness_commands(project=None):
    """The future, NOT executed, readiness checkpoint after the game start and before T0: the funding no-op is
    what the B1 game runs, no BotMarketFunding line was logged, and (at least 60 s after the game is healthy,
    past the 30 s funding delay) the slice passes `check ready`."""
    project, stage1 = b1_project(project)
    compose = compose_argv(project)
    commands = [
        [*compose, "exec", "-T", "game", "sha256sum", FUNDING_TARGET],
        [*compose, "logs", "--no-color", "game"],
        [
            "sh",
            "-c",
            f"docker exec -i {project}-database-1 mariadb -ucanary -N -B canary < b1/slice.sql > {READY_SLICE}",
        ],
        [
            "python3",
            "b1_fixture.py",
            "check",
            "ready",
            READY_SLICE,
        ],
    ]
    if any(stage1 in part for command in commands for part in command):
        raise RuntimeError(f"readiness names {stage1}; refused")
    return [shlex.join(command) for command in commands]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    sub.add_parser("prepare-initdb")
    sub.add_parser("render-overlays")
    sub.add_parser(
        "install-plan", help="print (never run) the overlay install commands"
    )
    sub.add_parser("expected")
    leader = sub.add_parser("render-leader")
    leader.add_argument("name")
    checked = sub.add_parser("check")
    checked.add_argument("stage", choices=("s0", "leader", "ready"))
    checked.add_argument(
        "output", type=Path, help="the mariadb -N -B output of b1/slice.sql"
    )
    args = parser.parse_args(argv)
    if args.action == "prepare-initdb":
        result = prepare_initdb()
    elif args.action == "render-overlays":
        result = render_overlays()
    elif args.action == "install-plan":
        result = {
            "executed": False,
            "commands": install_commands(),
            "loadout_scope": LOADOUT_SCOPE,
            "funding_bind": {FUNDING_TARGET: funding_bind()},
            "readiness": {
                "commands": readiness_commands(),
                "expect": [
                    f"sha256sum prints {funding_bind()['sha256']}",
                    "the game log has no [BotMarketFunding] line",
                    "check ready: no problems; the leader balance and stock are observed only",
                ],
            },
        }
    elif args.action == "render-leader":
        result = render_leader(args.name)
    elif args.action == "expected":
        lines = expected_s0()
        result = {
            "method": METHOD,
            "sql_sha256": sha256(SLICE_SQL.read_bytes()),
            "slice_sha256": digest(lines),
            "lines": lines,
        }
    else:
        lines = canonical(args.output.read_text(encoding="utf-8"))
        problems, observed = check(lines, args.stage)
        result = {
            "method": METHOD,
            "stage": args.stage,
            "sql_sha256": sha256(SLICE_SQL.read_bytes()),
            "output_sha256": sha256(args.output.read_bytes()),
            "slice_sha256": digest(lines),
            "observed": observed,
            "problems": problems,
        }
        print(json.dumps(result, indent=2, sort_keys=True))
        return 1 if problems else 0
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
