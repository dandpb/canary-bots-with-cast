"""Free QA entrypoint: production supervision owns admission, clocks and stops."""

import argparse
import asyncio
import inspect
import json
import os
import re
import sqlite3
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

from canary_brain import runtime
from canary_brain.store import Store


def forbidden(*_args, **_kwargs):
    raise RuntimeError("free QA forbids provider, credential and financial operations")


def require_native_admission():
    """Require the real integrated configuration/controller/durable-proof API."""
    expected = (
        Path(__file__).resolve().parents[2]
        / "deployment/brain/src/canary_brain/runtime.py"
    )
    if Path(runtime.__file__).resolve() != expected:
        raise RuntimeError("QA runtime must come from this source checkout")
    if (
        "native_source_revision" not in runtime.Configuration.model_fields
        or "native_source_revision"
        not in inspect.signature(runtime.Controller).parameters
    ):
        raise RuntimeError("production native admission integration is not available")
    from canary_brain.supervised_native import SupervisedNative

    if not callable(getattr(SupervisedNative, "durable_complete", None)):
        raise TypeError("production durable native qualification is not available")


def load_configuration(work, mode):
    if mode not in {"native", "fake"}:
        raise ValueError("free QA accepts only native or fake")
    root_value = os.environ.get("CANARY_M5_PRIVATE_ROOT") or os.environ.get("TMPDIR")
    if not root_value or not Path(root_value).is_absolute():
        raise ValueError("set an absolute private root")
    root = Path(root_value).resolve(strict=True)
    if root.stat().st_uid != os.getuid() or root.stat().st_mode & 0o077:
        raise ValueError("private root must be owned by this user and mode 0700")
    if (
        not work.is_absolute()
        or work != work.resolve()
        or not work.is_relative_to(root)
    ):
        raise ValueError("attempt must be below the private root without symlinks")
    if work == root or work.stat().st_uid != os.getuid() or work.stat().st_mode & 0o077:
        raise ValueError("attempt must be a private child directory")
    for path in (work / "worker.json", work / "socket", work / "socket/server.sock"):
        if path.is_symlink():
            raise ValueError("attempt inputs and socket paths must not be symlinks")
    config = runtime.Configuration.model_validate_json(
        (work / "worker.json").read_text()
    )
    if (
        config.provider != mode
        or config.mode != ("shadow" if mode == "native" else "active")
        or config.credential_file is not None
        or config.gateway is not None
        or config.budget_file is not None
        or config.operator_port is not None
        or config.run_cap_nanousd is not None
        or config.memory_mode != "frozen"
        or config.learning
        or not config.benchmark_supervision
        or config.run_seconds != 1800
        or config.state_file != work / "worker.sqlite3"
        or config.socket_directory.resolve() != (work / "socket").resolve()
        or config.recording is None
        or config.recording.path != work / "recording.sqlite3"
    ):
        raise ValueError("free QA requires isolated production benchmark supervision")
    manifests = config.recording.manifests
    if (
        len(manifests) != 1
        or manifests[0].bot_id != config.bots[0]
        or manifests[0].provider != mode
        or manifests[0].model != "none"
        or manifests[0].memory_mode != "frozen"
        or not manifests[0].experiment
        or not re.fullmatch(r"[0-9a-f]{40}", manifests[0].source_revision)
        or config.native_source_revision != manifests[0].source_revision
    ):
        raise ValueError("free QA requires a pinned single-bot experiment manifest")
    for name in ("worker.sqlite3", "recording.sqlite3", "stop.json"):
        if any(
            (work / (name + suffix)).exists() or (work / (name + suffix)).is_symlink()
            for suffix in ("", "-wal", "-shm", "-journal")
        ):
            raise ValueError(
                "attempt already has state/evidence; never resume or overwrite"
            )
    if (work / "supply-probe.json").exists():
        raise ValueError("supply-only probes are separate from timed qualification")
    return config


def require_final_receipt(config, ending, private_admission):
    """Audit production's post-close seal; do not infer success from a verdict alone."""
    from canary_brain.native_admission import Admission
    from canary_brain.recording import ReplayReader, public_data

    if not config.recording.path.is_file() or private_admission is None:
        raise RuntimeError("completed worker lacks durable admission/replay proof")
    admission = Admission.model_validate_json(private_admission)
    if (
        admission.source != config.native_source_revision
        or admission.source_dirty
        or admission.fault
        or admission.bot_id != config.bots[0]
    ):
        raise RuntimeError("completed worker admission identity mismatch")
    reader = ReplayReader(config.recording.path)
    identity = config.recording.manifests[0].run_id
    with reader.snapshot() as snapshot:
        metadata = snapshot.run(identity)
        events = {e["key"]: e for e in snapshot.all_events(identity)}
    admitted = events.get("native-admission", {}).get("data")
    seal = events.get("supervisor-native-qualified", {}).get("data", {})
    cutoff = events.get("horizon-final-sample", {}).get("data", {})
    fence = events.get("native-terminal-fence", {}).get("data", {})
    if (
        metadata["incomplete"]
        or admitted
        != {"phase": "native_admitted", **public_data(admission.model_dump())}
        or seal.get("phase") != "run_supervisor_stop"
        or seal.get("after_flush") is not True
        or any(seal.get(key) != value for key, value in ending.items())
        or cutoff.get("world") != admission.world
        or cutoff.get("bot", {}).get("id") != admission.bot_id
        or type(cutoff.get("captured_ms")) is not int
        or cutoff["captured_ms"] - admission.captured_ms < 1800000
        or fence.get("phase") != "native_terminal_fence"
        or fence.get("world") != admission.world
        or fence.get("bot_id") != admission.bot_id
        or not fence.get("fence_nonce")
        or fence["fence_nonce"] == admission.nonce
    ):
        raise RuntimeError("completed worker lacks a matching post-close native seal")


async def run_worker(work, mode):
    require_native_admission()  # Before parsing paths, creating Store or opening sockets.
    config = load_configuration(work, mode)
    expected_state = work / "worker.sqlite3"

    class PrivateStore(Store):
        def __init__(self, path, *args, **kwargs):
            if Path(path) != expected_state or Path(path).is_symlink():
                forbidden()
            super().__init__(path, *args, **kwargs)

    # Defense in depth: runtime uses a fresh local state DB, never a shared ledger.
    # Disable optional exporters too; no trace endpoint belongs in a free QA run.
    with ExitStack() as stack:
        for target in ("read_credential", "AsyncOpenAI", "Provider", "GatewayProvider"):
            stack.enter_context(patch.object(runtime, target, forbidden))
        stack.enter_context(patch.object(runtime, "Store", PrivateStore))
        stack.enter_context(patch.object(Store, "reserve", forbidden))
        stack.enter_context(patch.object(Store, "settle", forbidden))
        stack.enter_context(patch.object(runtime.tracing, "configure", lambda: None))
        await runtime.run(config)  # No private stop event, timer, Controller or Stops.
    with sqlite3.connect(expected_state.as_uri() + "?mode=ro", uri=True) as db:
        requests = db.execute("SELECT COUNT(*) FROM requests").fetchone()[0]
        row = db.execute(
            "SELECT data FROM records WHERE kind='run_stop' AND key='end'"
        ).fetchone()
        admission_row = db.execute(
            "SELECT data FROM records WHERE kind='native_admission' AND key=?",
            (config.recording.manifests[0].run_id,),
        ).fetchone()
    if requests:
        forbidden()
    ending = json.loads(row[0]) if row else {"reason": "runtime_ended"}
    with (work / "stop.json").open("x") as stream:
        json.dump(ending, stream)
    if not row or ending.get("reason") != "completed":
        raise RuntimeError("production supervisor did not complete the qualification")
    require_final_receipt(config, ending, admission_row[0] if admission_row else None)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("work", type=Path)
    parser.add_argument("mode", choices=["native", "fake"])
    args = parser.parse_args()
    asyncio.run(run_worker(args.work, args.mode))
