"""Validate and summarize recorded QA observations, keeping raw measurements."""

import gzip
import json

import party_perf as perf
import party_qa as q


def native(snapshot):
    value = snapshot["native"]
    return json.loads(value) if isinstance(value, str) else value


def players(snapshot):
    return {p["guid"]: p for p in snapshot["players"] if not p.get("offline")}


def xp_delta(before, after):
    a, b = players(before), players(after)
    return {str(guid): b[guid]["xp"] - a[guid]["xp"] for guid in a if guid in b}


def matrix(rows, combat=False):
    result = {}
    assert len(rows) == 9, len(rows)
    for mode in ["disabled", "shadow", "active"]:
        group = [r for r in rows if r["mode"] == mode]
        assert len(group) == 3
        ticks = [v for r in group for v in r["native_ticks_us"]]
        durations = [r["seconds" if combat else "duration_seconds"] for r in group]
        snapshots = [v for r in group for v in r["samples" if combat else "snapshots"]]
        walk = max(
            (
                p["walk_queue"]
                for s in snapshots
                for p in (native(s) if combat else s["native"])
            ),
            default=0,
        )
        workers = [r.get("worker" if combat else "worker_end", {}) for r in group]
        record = {
            "repetitions": 3,
            "native_ticks": len(ticks),
            "duration_seconds": durations,
            "bridge_window_p95_ms": [r["bridge_p95_us"] / 1000 for r in group],
            "total_tick_window_p95_ms": [r["total_tick_p95_us"] / 1000 for r in group],
            "bridge_pooled_p95_ms": perf.percentile([v[1] for v in ticks], 0.95) / 1000,
            "total_tick_pooled_p95_ms": perf.percentile([v[0] for v in ticks], 0.95)
            / 1000,
            "bridge_pooled_p99_ms": perf.percentile([v[1] for v in ticks], 0.99) / 1000,
            "total_tick_pooled_p99_ms": perf.percentile([v[0] for v in ticks], 0.99)
            / 1000,
            "bridge_max_ms": max(v[1] for v in ticks) / 1000,
            "total_tick_max_ms": max(v[0] for v in ticks) / 1000,
            "bridge_ticks_over_2ms": sum(v[1] > 2000 for v in ticks),
            "container_cpu_one_core_percent": [
                r["cgroup_cpu_seconds"] / seconds * 100
                for r, seconds in zip(group, durations, strict=True)
            ],
            "walk_queue_max_observed": walk,
            "controller_pending_peak": max(
                (w.get("pending_peak", 0) for w in workers), default=0
            ),
        }
        if mode != "disabled":
            assert all(r["bridge_p95_us"] < 2000 for r in group)
        if combat:
            assert all(len(r["after"]["deaths"]) == 0 for r in group)
            assert all(
                r["before"]["kills"] == {} or len(r["before"]["kills"]) == 0
                for r in group
            )
            record.update(
                {
                    "defeats": [r["kills_delta"] for r in group],
                    "spawned": [r["spawned_delta"] for r in group],
                    "removed_after_measurement": [
                        len(r["removed_after_window"]) for r in group
                    ],
                    "xp_delta_by_guid": [
                        xp_delta(r["before"], r["after"]) for r in group
                    ],
                    "damage_sources": [
                        sorted({v["attacker"] for v in r["after"]["damage"]})
                        for r in group
                    ],
                    "deaths": 0,
                }
            )
            populations = [
                r[key]
                for r in group
                for key in ["population_before", "population_after"]
                if key in r
            ]
            if populations:
                record["population_registered_range"] = [
                    min(p["registered"] for p in populations),
                    max(p["registered"] for p in populations),
                ]
                record["population_awake_range"] = [
                    min(p["awake"] for p in populations),
                    max(p["awake"] for p in populations),
                ]
                record["population_hibernated_range"] = [
                    min(p["hibernated"] for p in populations),
                    max(p["hibernated"] for p in populations),
                ]
            assert all(
                r["kills_delta"] + len(r["removed_after_window"]) == r["spawned_delta"]
                for r in group
            )
        result[mode] = record
    return result


def scenarios(data):
    phases = {p["name"]: p for p in data["phases"]}
    hunt = phases["coordinated_native_hunt"]
    guided = [
        s
        for s in hunt["samples"]
        if isinstance(s["brain"], dict)
        and any(
            v["bot"] == 65001 and v["objective"] == "hunt" and v["running"]
            for v in s["brain"]["sessions"]
        )
    ]
    result = {
        "hunt": {
            "guided_hunt_samples": len(guided),
            "defeats": len(hunt["after"]["kills"]) - len(hunt["before"]["kills"]),
            "xp_delta": xp_delta(hunt["before"], hunt["after"]),
            "guide_positions": len(
                {
                    tuple(p["position"])
                    for s in guided
                    for p in native(s)
                    if p["guid"] == 65001
                }
            ),
            "damage_sources": sorted({v["attacker"] for v in hunt["after"]["damage"]}),
            "complete_15_minute_hunts": 0,
            "deaths": len(hunt["after"]["deaths"]),
        }
    }
    assert result["hunt"]["guided_hunt_samples"] > 0, result["hunt"]
    assert result["hunt"]["defeats"] > 0 and result["hunt"]["guide_positions"] > 1, (
        result["hunt"]
    )
    supply = phases["three_companion_resupply_and_return"]
    a, b = players(supply["before"]), players(supply["after"])
    terminal = {
        v["bot_id"]: v
        for v in supply["after"]["worker"]["outcomes"]
        if v.get("reason") == "supplies_bought_and_party_rejoined"
    }
    assert set(terminal) == {65001, 65003, 65004}, terminal
    result["resupply"] = {}
    for guid in [65001, 65003, 65004]:
        record = {
            "potions_before": a[guid]["health_potions"] + a[guid]["mana_potions"],
            "potions_after": b[guid]["health_potions"] + b[guid]["mana_potions"],
            "funds_spent": a[guid]["bank"]
            + a[guid]["money"]
            - b[guid]["bank"]
            - b[guid]["money"],
            "native_outcome": terminal[guid],
        }
        assert (
            record["potions_before"] == 2
            and record["potions_after"] >= 40
            and record["funds_spent"] > 0
        ), record
        result["resupply"][str(guid)] = record
    transfer = phases["leader_transfer"]
    assert all(p["leader"] == 64998 for p in native(transfer["after"]))
    assert all(p["leader"] == 64998 for p in transfer["after"]["brain"]["sessions"])
    assert not any(
        p["bot"] == 65001 and p["objective"] == "hunt" and p["running"]
        for p in transfer["after"]["brain"]["sessions"]
    )
    result["leader_transfer"] = {
        "new_leader": 64998,
        "old_leader_started_hunt": False,
        "authority_changed_outcomes": [
            o
            for o in transfer["after"]["worker"]["outcomes"]
            if o.get("reason") == "authority_changed"
        ],
    }
    fallback = phases["worker_loss_fallback"]
    active = fallback["goals_before_stop"]["brain"]["sessions"]
    assert sum(p["running"] for p in active) == 3, active
    assert fallback["after"]["brain"]["worker_alive"] is False
    assert not any(p["running"] for p in fallback["after"]["brain"]["sessions"])
    ceased = [
        s["observed_at_monotonic"] - fallback["worker_stop_at"]
        for s in fallback["samples"]
        if isinstance(s["brain"], dict)
        and not s["brain"]["worker_alive"]
        and not any(p["running"] for p in s["brain"]["sessions"])
    ]
    kills = len(fallback["after"]["kills"]) - len(
        fallback["before_fallback_combat"]["kills"]
    )
    assert kills > 0, kills
    result["worker_loss"] = {
        "goals_before_stop": 3,
        "running_after_stop": 0,
        "first_observed_fallback_seconds": min(ceased),
        "observation_lower_bound_seconds": max(
            [0]
            + [
                s["observed_at_monotonic"] - fallback["worker_stop_at"]
                for s in fallback["samples"]
                if isinstance(s["brain"], dict) and s["brain"]["worker_alive"]
            ]
        ),
        "confirmed_defeats_after_worker_stop": kills,
    }
    restart = phases["worker_restart"]
    assert restart["after"]["brain"]["worker_alive"] is True
    assert not any(p["running"] for p in restart["after"]["brain"]["sessions"])
    result["worker_restart"] = {"worker_alive": True, "resurrected_goals": 0}
    disconnected = phases["leader_disconnect"]
    assert all(p["leader"] == 64999 for p in native(disconnected["after_first_drop"]))
    assert all(
        p["leader"] == 0 and p["members"] == 0 for p in native(disconnected["after"])
    )
    assert all(
        p["leader"] == 0 and not p["running"]
        for p in disconnected["after"]["brain"]["sessions"]
    )
    result["disconnect"] = {
        "leader_after_B_disconnect": 64999,
        "authority_after_all_disconnect": 0,
        "retained_human_party_members": 0,
    }
    assert all(len(p["after"]["deaths"]) == 0 for p in phases.values())
    result["deaths_all_phases"] = 0
    return result


def main():
    identity = q.run_id()
    population = q.WORK / "party-population-perf-raw.json"
    raw_files = [
        "party-perf-raw.json",
        "party-combat-perf-raw.json",
        "party-scenarios-raw.json",
        "party-variety-raw.json",
    ]
    metadata_files = [
        "party-environment.json",
        "party-runtime-source-comparison.json",
        "party-datapack-normalized-blobs.json",
    ]
    if population.exists():
        raw_files.append("party-population-perf-raw.json")
        metadata_files.append("party-population-load.json")
    metadata_files += [
        name
        for name in [
            "financial-and-pending.json",
            "teardown.json",
            "fixture-command-regression.json",
        ]
        if (q.WORK / name).exists()
    ]
    # Snapshot and validate every input before publishing anything. Never reread
    # an artifact after validating it or silently accept untagged historical data.
    inputs = {name: q.read_json(name, identity) for name in raw_files + metadata_files}
    idle = inputs["party-perf-raw.json"]
    combat = inputs["party-combat-perf-raw.json"]
    functional = inputs["party-scenarios-raw.json"]
    result = {
        "run_id": identity,
        "native_base": functional["base_revision"],
        "death_observer_scope": "five party fixture avatars; background mortality not classified",
        "intervention_observer_scope": "setup_teleports in retained raw files is a planned upper bound of five; zero fixture-injected heals/teleports during timed combat; native automatic rescues not exhaustively classified",
        "idle_follow": matrix(idle),
        "combat": matrix(combat, True),
        "scenarios": scenarios(functional),
    }
    if "party-population-perf-raw.json" in inputs:
        result["population_combat"] = matrix(
            inputs["party-population-perf-raw.json"], True
        )
    target = q.report_directory(identity)
    target.mkdir(parents=True, exist_ok=True)
    for file in raw_files:
        data = inputs[file]
        (target / (file + ".gz")).write_bytes(
            gzip.compress(json.dumps(data, separators=(",", ":")).encode(), mtime=0)
        )
    for file in metadata_files:
        (target / file).write_text(json.dumps(inputs[file], indent=2) + "\n")
    (target / "summary.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
