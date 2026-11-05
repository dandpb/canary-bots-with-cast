"""Matched native combat windows across bridge modes, without model calls."""

import argparse
import json
import time

import party_perf as perf
import party_qa as q


def snapshot():
    return q.command("return PartyScenario.snapshot()")


def population_snapshot():
    return q.command("""local states=Game.getBotHibernationStates();local awake,hibernated=0,0
for _,row in ipairs(states) do if row.hibernated then hibernated=hibernated+1 else awake=awake+1 end end
local status=Game.botCommand("_global","schedule status")
return {registered=tonumber(status:match("/ (%d+)$")) or #states,enumerated=#states,active=Game.botCountActive(),awake=awake,hibernated=hibernated,scheduler=status}""")


def main(output_name="party-combat-perf-raw.json", expected_population=3):
    assert (
        "/" not in output_name
        and "\\" not in output_name
        and output_name.endswith(".json")
    )
    q.reserve_output(output_name)
    q.verify()
    q.command(
        'PartyScenario=dofile("/qa-repo/tests/fixture/party_scenarios.lua");return true'
    )
    results = []
    for rep, order in enumerate(
        [
            ["disabled", "shadow", "active"],
            ["active", "disabled", "shadow"],
            ["shadow", "active", "disabled"],
        ],
        1,
    ):
        for mode in order:
            perf.mode(mode)
            initial_cleanup = q.command("""local removed=PartyScenario.reset()
PartyScenario.baseline()
PartyScenario.placeHunt()
Player("Party Leader A"):setFollowCreature(nil);Player("Party Leader B"):setFollowCreature(nil)
for _,p in ipairs(Game.getPlayers()) do p:addHealth(p:getMaxHealth()-p:getHealth());p:addMana(p:getMaxMana()-p:getMana()) end
return removed""")
            time.sleep(3)
            population_before = population_snapshot()
            assert population_before["registered"] == expected_population, (
                population_before
            )
            before = snapshot()
            perf.timings()
            start_cpu = perf.cpu()
            started = time.monotonic()
            samples = []
            last_wave = -20
            while time.monotonic() - started < 30:
                if time.monotonic() - started - last_wave >= 10:
                    q.command("return PartyScenario.wave()")
                    last_wave = time.monotonic() - started
                current = snapshot()
                samples.append(current)
                assert len(current.get("deaths", [])) == len(
                    before.get("deaths", [])
                ), current
                time.sleep(1)
            end_cpu = perf.cpu()
            ticks = perf.timings()
            after = snapshot()
            cleaned_after_window = q.command("return PartyScenario.cleanup()")
            population_after = population_snapshot()
            assert population_after["registered"] == expected_population, (
                population_after
            )
            result = {
                "repetition": rep,
                "mode": mode,
                "seconds": time.monotonic() - started,
                "setup_teleport_upper_bound": 5,
                "initial_cleanup": initial_cleanup,
                "removed_after_window": cleaned_after_window,
                "population_before": population_before,
                "population_after": population_after,
                "health_mana_reset_before_window": True,
                "xp_and_basic_potions_reset_before_window": True,
                "runtime_heals_or_teleports_by_fixture": 0,
                "before": before,
                "after": after,
                "samples": samples,
                "native_ticks_us": ticks,
                "bridge_p95_us": perf.percentile([v[1] for v in ticks], 0.95),
                "total_tick_p95_us": perf.percentile([v[0] for v in ticks], 0.95),
                "cpu_start": start_cpu,
                "cpu_end": end_cpu,
                "cgroup_cpu_seconds": (end_cpu["usage_usec"] - start_cpu["usage_usec"])
                / 1e6,
                "kills_delta": len(after.get("kills", []))
                - len(before.get("kills", [])),
                "spawned_delta": len(after.get("spawns", []))
                - len(before.get("spawns", [])),
                "worker": perf.read_worker() if mode != "disabled" else {},
            }
            assert len(ticks) >= 200, len(ticks)
            results.append(result)
            q.write_json(output_name, results)
            print(
                json.dumps(
                    {
                        k: result[k]
                        for k in [
                            "repetition",
                            "mode",
                            "seconds",
                            "bridge_p95_us",
                            "total_tick_p95_us",
                            "kills_delta",
                            "spawned_delta",
                        ]
                    }
                ),
                flush=True,
            )
    perf.stop_worker()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="party-combat-perf-raw.json")
    parser.add_argument("--population", type=int, default=3)
    args = parser.parse_args()
    main(args.output, args.population)
