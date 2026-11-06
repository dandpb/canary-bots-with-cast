"""Exercise the real campaign runner with a real private game and no inference.

Only Compose preparation adds the pinned database, internal network and audit
mount required by the existing QA image. Worker, clocks, recorder, supervision,
classification, server, database and teardown use the actual implementations.
"""

import asyncio
import hashlib
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

from canary_brain import benchmark, runtime
from canary_brain.recording import ReplayReader

source, fixture_root, work = map(Path, sys.argv[1:])
work.mkdir(mode=0o700, exist_ok=False)
(work / "frozen-driver.py").write_bytes(Path(__file__).read_bytes())
manifest = json.loads((fixture_root / "manifest.json").read_text())
revision = subprocess.check_output(
    ["git", "-C", str(source), "rev-parse", "HEAD"], text=True
).strip()
subprocess.run(
    [
        "git",
        "-C",
        str(source),
        "-c",
        "core.autocrlf=true",
        "diff",
        "--quiet",
        "--",
        "deployment/brain/src",
    ],
    check=True,
)


def forbidden(*args, **kwargs):
    raise AssertionError(
        "real runner smoke cannot read provider credentials or call a provider"
    )


runtime.read_credential = forbidden
runtime.AsyncOpenAI = forbidden
original = benchmark.DockerFixture
database = "sha256:a794d9eb009e20de605858a11f32f63b4075cbd197c650436f0e3b457e4caed7"


class AttestedFixture(original):
    def prepare(self, participant):
        super().prepare(participant)
        compose = json.loads(self.compose.read_text())
        compose["services"]["database"]["image"] = database
        compose["services"]["game"]["volumes"].append(f"{self.directory}:/m5")
        compose["networks"] = {"default": {"internal": True}}
        self.compose.write_text(json.dumps(compose))

    def start_database(self):
        super().start_database()
        actual = subprocess.check_output(
            [
                "docker",
                "inspect",
                self.project + "-database-1",
                "--format",
                "{{.Image}}",
            ],
            text=True,
        ).strip()
        assert actual == database


benchmark.DockerFixture = AttestedFixture
experiment = benchmark.Experiment(
    name="m5-runner-free-smoke",
    output=work / "runs",
    fixture=fixture_root / "fixture",
    world_map=Path("/tmp/canary-lifecycle-qa-world.otbm"),
    budget_file=work / "offline-ledger.sqlite3",
    game_image=manifest["image_id"],
    bot_id=65001,
    participants=[benchmark.Participant(name="native", kind="native")],
    repetitions=1,
    seconds=10,
    source_revision=revision,
    expected_initial_sha256=manifest["fixture_sha256"],
)
asyncio.run(benchmark.run_campaign(experiment, live=True))
reader = ReplayReader(experiment.output / "recording.sqlite3")
run = reader.runs()[0]
samples = [e["t_ms"] for e in reader.all_events(run["id"]) if e["kind"] == "sample"]
with sqlite3.connect(experiment.budget_file) as db:
    requests = db.execute("SELECT COUNT(*) FROM requests").fetchone()[0]
assert run["status"] == "completed" and not run["incomplete"]
assert max(samples) - min(samples) >= 10000 and requests == 0
result = {
    "source_revision": revision,
    "driver_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    "game_image": manifest["image_id"],
    "database_image": database,
    "fixture_sha256": manifest["fixture_sha256"],
    "configured_seconds": 10,
    "recorded_seconds": (max(samples) - min(samples)) / 1000,
    "status": run["status"],
    "incomplete": run["incomplete"],
    "inference_requests": requests,
    "scope": "Real campaign runner, native-only, short integration smoke; not another 30-minute qualification or an inference/account-access test.",
}
(work / "smoke-result.json").write_text(json.dumps(result, indent=2))
print(json.dumps(result, indent=2))
