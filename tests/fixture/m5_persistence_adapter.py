"""Prospective fixture producer/adapter. Never starts Docker, providers or a game."""

import json
import re
import time
from pathlib import Path

from canary_brain.persistence_witness import (
    binding_bytes,
    durable_complete,
    exclusive,
    publish_request,
    read_private,
)


def render_fixture(scripts, binding):
    """Call on freshly copied generated scripts, before building the QA image."""
    binding_bytes(binding)
    root = Path(__file__).resolve().parent
    target = scripts / "globalevents/aaa_m5_free_qa.lua"
    original = target.read_text()
    assert original.count('local event=GlobalEvent("M5FreeAudit")') == 1
    # Keep the existing pure JSON encoder, replace the legacy unbound live sampler.
    prefix = original[: original.index('local event=GlobalEvent("M5FreeAudit")')]
    module = scripts / "lib/m5_persistence.lua"
    assert not module.exists()
    exclusive(module, (root / "m5_persistence.lua").read_bytes())
    literal = (
        "{"
        + ",".join(
            "[" + json.dumps(k) + "]=" + (str(v) if type(v) is int else json.dumps(v))
            for k, v in sorted(binding.items())
        )
        + "}"
    )
    target.write_text(
        prefix
        + '\nlocal module=dofile("data/scripts/lib/m5_persistence.lua")\n'
        + "M5PersistenceAudit=module.new("
        + literal
        + ',"/qa-persistence",qa.encode)\n'
        + 'local death=CreatureEvent("M5PersistenceDeath")\nfunction death.onDeath(p) M5PersistenceAudit.death(p); return true end\ndeath:register()\n'
        + 'local event=GlobalEvent("M5FreeAudit")\nfunction event.onThink() return M5PersistenceAudit.think() end\nevent:interval(1000);event:register()\n'
    )
    manager = scripts / "globalevents/bot_manager.lua"
    body = manager.read_text()
    needle = 'player:registerEvent("BotDeath")'
    assert body.count(needle) == 1, "pinned loader hook missing or ambiguous"
    manager.write_text(
        body.replace(
            needle,
            needle
            + "\n\t\t\t\tassert(M5PersistenceAudit); M5PersistenceAudit.attach(player)",
        )
    )
    exclusive(
        scripts.parent / "persistence-binding.json", binding_bytes(binding) + b"\n"
    )


def stop_and_read(harness, directory, binding, *, world, require_native_receipt):
    """The caller supplies owned wait/read callbacks; this function issues no game commands.

    Normal stop is the fixture's synchronous Lua shutdown, not SIGTERM. The outer
    adapter still owns bounded finally/cleanup on ANY exception. require_native_receipt
    must audit the unchanged production completed stop and post-close seal first.
    """
    if require_native_receipt() is not True:
        raise ValueError("production receipt not verified")
    request = publish_request(directory, binding)
    code = harness.wait_game(timeout=210)
    stopped_wall = time.time()
    stopped_mono = time.monotonic()
    if type(code) is not int or code != 0:
        raise ValueError("unclean owned game exit")
    verify_shutdown_logs(harness.shutdown_logs(), binding["stop_nonce"])
    complete = durable_complete(directory, binding, world, request, code)
    sql_started = time.time()
    sql_mono = time.monotonic()
    saved = harness.character()
    read_wall = time.time()
    read_mono = time.monotonic()
    return (
        saved,
        {
            "world": world,
            "bot_id": binding["bot_id"],
            "game_stop_started_wall": request["started"]["wall"],
            "game_stopped_wall": stopped_wall,
            "sql_read_started_wall": sql_started,
            "sql_read_wall": read_wall,
            "game_stopped_monotonic": stopped_mono,
            "sql_read_started_monotonic": sql_mono,
            "sql_read_monotonic": read_mono,
        },
        {
            "binding": binding,
            "journal": read_private(directory / "audit.jsonl").decode("utf8"),
            "durable_complete": complete,
        },
    )


def verify_shutdown_logs(raw, nonce):
    """Pinned C8 shutdown_save batch is synchronous but Lua API is not a save ACK."""
    pre = ("[M5Persistence] pre " + nonce).encode()
    post = ("[M5Persistence] post " + nonce).encode()
    if raw.count(pre) != 1 or raw.count(post) != 1 or raw.index(pre) >= raw.index(post):
        raise ValueError("shutdown log boundary missing")
    for error in (
        b"Lua Script Error Detected",
        b"Call stack overflow. Too many lua script calls",
        b"Failed to durably save",
        b"Could not capture bot",
        b"player failures",
        b"Checkpoint statement failed",
        b"Failed to save player",
    ):
        if error in raw:
            raise ValueError("shutdown save failure")
    batch = raw[raw.index(pre) : raw.index(post)]
    if not re.search(rb"Captured 1 players for server save", batch) or not re.search(
        rb"Server saved 1 players in", batch
    ):
        raise ValueError("shutdown save batch not acknowledged")


def production_receipt_check(configuration):
    """Reuse the existing production receipt audit; never invent completion."""
    import sqlite3

    from m5_worker import require_final_receipt

    if configuration.provider != "native" or not configuration.benchmark_supervision:
        raise ValueError("native supervised configuration required")
    path = configuration.state_file
    if path.is_symlink() or not path.is_file():
        raise ValueError("private native state missing")
    db = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
    try:
        ending = db.execute(
            "SELECT data FROM records WHERE kind='run_stop' AND key='end'"
        ).fetchone()
        admission = db.execute(
            "SELECT data FROM records WHERE kind='native_admission' AND key=?",
            (configuration.recording.manifests[0].run_id,),
        ).fetchone()
    finally:
        db.close()
    if ending is None or admission is None:
        raise ValueError("native completion receipts missing")
    ending = json.loads(ending[0])
    if ending.get("reason") != "completed":
        raise ValueError("native worker did not complete")
    require_final_receipt(configuration, ending, admission[0])
    return True
