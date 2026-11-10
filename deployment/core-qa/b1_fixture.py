"""B1 companion fixture only (CORE_QA_PROFILE=b1): the B1 initdb, the leader preparation, the hunt overlay
and the canonical read-only DB slice. Offline: no Docker, git, network or SQL here. B1_FIXTURE.md is the
procedure; stage 1 (runtime/initdb, brain/server.json, its baseline) is only read, never written."""

import argparse
import csv
import hashlib
import json
import os
import re
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
HUNTS = SOURCE / "data/bot/authored/hunt_scripts.csv"
OVERLAY = HERE / "runtime/b1/authored/hunt_scripts.csv"
OVERLAY_HUNTS = {"399"}  # v4 2.3: only Thais Paw Collector
EVIDENCE = HERE / "runtime/b1/evidence"
METHOD = "b1-fixture-slice-v1"
PLACEHOLDER = "@@LEADER_NAME@@"

# Declared state (B1_FIXTURE.md has the sources). Per vocation at level 20: HP, mana, cap and the
# equipment.csv level-20 row by slot (5 = shield, 6 = weapon, as equipBot places them).
LEVEL, EXPERIENCE, TOWN, TEMPLE, BANK = 20, 98800, 8, (32369, 32241, 7), 10000
VOCATION = {
    1: (245, 395, 590),
    2: (245, 395, 590),
    3: (305, 215, 710),
    4: (365, 95, 770),
}
LOADOUT = {
    1: {1: 3365, 4: 3388, 5: 3423, 6: 3072, 7: 3363, 8: 3555},
    2: {1: 3365, 4: 3388, 5: 3423, 6: 3069, 7: 3363, 8: 3555},
    3: {1: 3365, 4: 3366, 5: 3423, 6: 3347, 7: 3363, 8: 3555},
    4: {1: 3365, 4: 3366, 5: 3423, 6: 3284, 7: 3363, 8: 3555},
}
BACKPACK = 2854
PILOTS = {  # id: name, vocation, potions (health 266, mana 268), 20 in all, each type under 20
    65001: ("Grizzle Alyronia", 4, {266: 14, 268: 6}),
    65003: ("Sever Heartspear", 3, {266: 10, 268: 10}),
    65004: ("Galdon Whitehoof", 2, {266: 6, 268: 14}),
}
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


def player_line(guid, account, name, vocation):
    hp, mana, cap = VOCATION[vocation]
    return "\t".join(
        map(
            str,
            (
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
                TOWN,
                *TEMPLE,
                BANK,
            ),
        )
    )


def pilot_lines(guid):
    name, vocation, potions = PILOTS[guid]
    slots = {**LOADOUT[vocation], 3: BACKPACK}
    return {
        "player": [player_line(guid, 65000, name, vocation)],
        "slot": [f"slot\t{guid}\t{pid}\t{slots[pid]}\t1" for pid in sorted(slots)],
        "stock": [f"stock\t{guid}\t{item}\t{potions.get(item, 0)}" for item in STOCK],
        "deaths": [f"deaths\t{guid}\t0"],
    }


def expected_s0():
    """The exact slice of the fresh B1 database after init, before MyAAC and the first game start."""
    lines = {
        "fixture": ["fixture\tfixture\tb1-companions-v1"],
        "humans": ["humans\t0\t0"],
        "player": [],
        "slot": [],
        "stock": [],
        "deaths": [],
    }
    for guid in sorted(PILOTS):
        for tag, rows in pilot_lines(guid).items():
            lines[tag] += rows
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


def check(lines, stage):
    """Differences from the declared state. s0: exactly expected_s0(). leader: the pilots as in S0 and every
    QA-created character (id >= 66100) prepared as leader-prep.sql.template declares."""
    if stage == "s0":
        expected = expected_s0()
        problems = [f"missing: {line}" for line in expected if line not in lines] + [
            f"unexpected: {line}" for line in lines if line not in expected
        ]
        return problems or (["line order differs"] if lines != expected else [])
    problems = [
        f"missing: {line}"
        for line in expected_s0()
        if line.split("\t")[0] not in ("humans",) and line not in lines
    ]
    humans = [
        line.split("\t")
        for line in lines
        if line.startswith("player\t") and int(line.split("\t")[1]) >= 66100
    ]
    if not humans:
        problems.append("no QA-created character (id >= 66100)")
    if not any(line.startswith("fixture\tleader\t") for line in lines):
        problems.append("no prepared leader in qa_b1_fixture")
    for row in humans:
        guid, vocation = int(row[1]), int(row[4])
        # name .. posz; the leader's balance is his own (not declared)
        if (
            vocation not in VOCATION
            or row[3:-1]
            != player_line(guid, row[2], row[3], vocation).split("\t")[3:-1]
        ):
            problems.append("leader row differs: " + " ".join(row))
            continue
        for pid, item in LOADOUT[vocation].items():
            if f"slot\t{guid}\t{pid}\t{item}\t1" not in lines:
                problems.append(f"leader {guid} slot {pid} is not {item}")
    return problems


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


def overlay_text(text):
    """hunt_scripts.csv with only OVERLAY_HUNTS enabled; every other byte as in the source."""
    lines = text.splitlines(keepends=True)
    header = lines[0].rstrip("\r\n").split(",")
    column, out = header.index("enabled"), [lines[0]]
    for line in lines[1:]:
        body = line.rstrip("\r\n")
        head, *tail = body.rsplit(
            ",", len(header) - column
        )  # tail[0] is "enabled", unquoted columns after it
        fields = next(csv.reader([body]))
        if (
            len(fields) != len(header)
            or fields[column:] != tail
            or '"' in ",".join(tail)
        ):
            raise ValueError(f"hunt_scripts.csv line is not as expected: {body[:40]!r}")
        tail[0] = "1" if fields[0] in OVERLAY_HUNTS else "0"
        out.append(",".join([head, *tail]) + line[len(body) :])
    return "".join(out)


def render_overlay():
    require_b1()
    OVERLAY.parent.mkdir(parents=True, exist_ok=True)
    OVERLAY.write_text(overlay_text(HUNTS.read_text()))
    return {
        "source_sha256": sha256(HUNTS.read_bytes()),
        "overlay_sha256": sha256(OVERLAY.read_bytes()),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    sub.add_parser("prepare-initdb")
    sub.add_parser("render-overlay")
    sub.add_parser("expected")
    leader = sub.add_parser("render-leader")
    leader.add_argument("name")
    checked = sub.add_parser("check")
    checked.add_argument("stage", choices=("s0", "leader"))
    checked.add_argument(
        "output", type=Path, help="the mariadb -N -B output of b1/slice.sql"
    )
    args = parser.parse_args(argv)
    if args.action == "prepare-initdb":
        result = prepare_initdb()
    elif args.action == "render-overlay":
        result = render_overlay()
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
        problems = check(lines, args.stage)
        result = {
            "method": METHOD,
            "stage": args.stage,
            "sql_sha256": sha256(SLICE_SQL.read_bytes()),
            "output_sha256": sha256(args.output.read_bytes()),
            "slice_sha256": digest(lines),
            "problems": problems,
        }
        print(json.dumps(result, indent=2, sort_keys=True))
        return 1 if problems else 0
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
