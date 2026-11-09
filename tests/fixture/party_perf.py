"""Rotated, repeated three-mode fixture; writes every measured native tick."""

import argparse
import json
import math
import time

import party_qa as q


def read_worker():
    raw = q.docker(
        "exec", q.GAME, "cat", "/canary/party-worker-metrics.json", check=False
    )
    return json.loads(raw) if raw else {}


def stop_worker(signal_name="SIGTERM"):
    assert signal_name in {"SIGTERM", "SIGKILL"}
    q.verify()
    q.docker(
        "exec",
        q.GAME,
        "python3",
        "-c",
        "from pathlib import Path;import os,signal;p=Path('/canary/party-worker.pid');"
        "proc=Path('/proc/'+p.read_text()) if p.exists() else None;"
        "os.kill(int(p.read_text()),signal."
        + signal_name
        + ") if proc and proc.exists() and b'party_worker.py' in (proc/'cmdline').read_bytes() else None",
        check=False,
    )
    time.sleep(1)


def mode(name):
    stop_worker()
    (q.WORK / "brain.json").write_text(
        json.dumps(
            {
                "mode": name,
                "bots": [65001, 65003, 65004],
                "socket_directory": "/run/party-brain",
            }
        )
    )
    q.command('return Game.botCommand("_global","brain reload")')
    if name != "disabled":
        config = {
            "mode": name,
            "provider": "fake",
            "bots": [65001, 65003, 65004],
            "socket_directory": "/run/party-brain",
            "state_file": f"/canary/party-{time.time_ns()}.sqlite3",
            "memory_mode": "frozen",
            "learning": False,
        }
        (q.WORK / "worker.json").write_text(json.dumps(config))
        q.docker(
            "exec",
            "-d",
            "-e",
            "PYTHONPATH=/qa-repo/deployment/brain/src:/qa-deps",
            q.GAME,
            "sh",
            "-c",
            "exec python3 /qa-repo/tests/fixture/party_worker.py >/canary/party-worker.log 2>&1",
        )
    time.sleep(5)


def native():
    return json.loads(q.command('return PartyQA("inspect")'))


def timings():
    return json.loads(q.command('return PartyQA("timings")'))


def cpu():
    raw = q.docker("exec", q.GAME, "cat", "/sys/fs/cgroup/cpu.stat")
    return {k: int(v) for k, v in (row.split() for row in raw.splitlines())}


def percentile(values, p):
    return sorted(values)[max(0, math.ceil(len(values) * p) - 1)]


def main(seconds=60):
    q.reserve_output("party-perf-raw.json")
    q.verify()
    results = []
    # Rotation spreads host/background drift across the three treatments.
    for repetition, order in enumerate(
        [
            ["disabled", "shadow", "active"],
            ["active", "disabled", "shadow"],
            ["shadow", "active", "disabled"],
        ],
        1,
    ):
        for name in order:
            mode(name)
            before = native()
            assert all(
                row["members"] == 5 and row["leader"] == 64999 and not row["paused"]
                for row in before
            ), before
            timings()
            start_cpu = cpu()
            start_worker = read_worker() if name != "disabled" else {}
            started = time.monotonic()
            snapshots = []
            while time.monotonic() - started < seconds:
                time.sleep(5)
                state = native()
                assert all(
                    row["hp"] > 0 and row["members"] == 5 and row["leader"] == 64999
                    for row in state
                ), state
                snapshots.append(
                    {
                        "at": time.monotonic(),
                        "native": state,
                        "worker": read_worker() if name != "disabled" else {},
                    }
                )
            duration = time.monotonic() - started
            end_cpu = cpu()
            samples = timings()
            after = native()
            assert len(samples) >= 200, len(samples)
            assert all(
                row["hp"] > 0 and row["members"] == 5 and row["leader"] == 64999
                for row in after
            ), after
            total = [v[0] for v in samples]
            bridge = [v[1] for v in samples]
            end_worker = read_worker() if name != "disabled" else {}
            result = {
                "repetition": repetition,
                "mode": name,
                "duration_seconds": duration,
                "native_ticks_us": samples,
                "bridge_p95_us": percentile(bridge, 0.95),
                "total_tick_p95_us": percentile(total, 0.95),
                "bridge_max_us": max(bridge),
                "total_tick_max_us": max(total),
                "cpu_start": start_cpu,
                "cpu_end": end_cpu,
                "cgroup_cpu_seconds": (end_cpu["usage_usec"] - start_cpu["usage_usec"])
                / 1e6,
                "worker_start": start_worker,
                "worker_end": end_worker,
                "before": before,
                "after": after,
                "snapshots": snapshots,
            }
            results.append(result)
            q.write_json("party-perf-raw.json", results)
            print(
                json.dumps(
                    {
                        k: result[k]
                        for k in [
                            "repetition",
                            "mode",
                            "duration_seconds",
                            "bridge_p95_us",
                            "total_tick_p95_us",
                            "cgroup_cpu_seconds",
                        ]
                    }
                ),
                flush=True,
            )
    stop_worker()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--seconds", type=int, default=60, choices=range(30, 301))
    main(parser.parse_args().seconds)
