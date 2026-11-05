"""Native party scenarios with the production worker's explicit fake provider."""

import argparse
import json
import time

import party_perf as perf
import party_qa as q

RESULTS = {
    "base_revision": "33c6a57878e58ef1241d287d26bd5aa489b5cc50",
    "paid_calls": 0,
    "phases": [],
}


def snapshot():
    value = q.command("return PartyScenario.snapshot()")
    value["observed_at_monotonic"] = time.monotonic()
    value["native"] = json.loads(value["native"])
    try:
        value["brain"] = json.loads(value["brain"])
    except json.JSONDecodeError:
        pass
    value["worker"] = perf.read_worker()
    return value


def save(phase):
    RESULTS["phases"].append(phase)
    q.write_json("party-scenarios-raw.json", RESULTS)
    print(
        json.dumps(
            {
                "phase": phase["name"],
                "samples": len(phase.get("samples", [])),
                "result": phase.get("result"),
            }
        ),
        flush=True,
    )


def order(who, target, text):
    return q.command(
        f'return PartyQA("order",{who},{json.dumps(target, ensure_ascii=False)},{json.dumps(text, ensure_ascii=False)})'
    )


def sample_for(seconds):
    started = time.monotonic()
    samples = []
    while time.monotonic() - started < seconds:
        samples.append(snapshot())
        time.sleep(2)
    return samples


def initial_hunt():
    q.command("return PartyScenario.reset()")
    phase = {
        "name": "coordinated_native_hunt",
        "setup_teleport_upper_bound": 5,
        "samples": [],
        "before": q.command("return PartyScenario.placeHunt()"),
    }
    time.sleep(3)
    order(0, "Grizzle Alyronia", "hunt")
    started = time.monotonic()
    last_wave = -20
    while time.monotonic() - started < 120:
        if time.monotonic() - started - last_wave >= 30:
            q.command("return PartyScenario.wave()")
            last_wave = time.monotonic() - started
        phase["samples"].append(snapshot())
        time.sleep(2)
    # Deliberately end this bounded window through an ordinary leader retreat order.
    # A cancelled 15-minute hunt is never counted as a completed episode.
    order(0, "Grizzle Alyronia", "recue")
    phase["samples"] += sample_for(8)
    phase["after"] = snapshot()
    phase["result"] = "bounded_window_not_full_hunt_completion"
    save(phase)


def main(resume=False):
    if resume:
        saved = q.read_json("party-scenarios-raw.json")
        assert [p["name"] for p in saved["phases"]] == ["coordinated_native_hunt"]
        RESULTS.update(saved)
    else:
        q.reserve_output("party-scenarios-raw.json")
    q.verify()
    perf.mode("active")
    q.command(
        'PartyScenario=dofile("/qa-repo/tests/fixture/party_scenarios.lua");return true'
    )
    if not resume:
        initial_hunt()
    phase = {
        "name": "three_companion_resupply_and_return",
        "setup_teleport_upper_bound": 5,
        "samples": [],
        "before": q.command("return PartyScenario.placeSupply()"),
    }
    time.sleep(3)
    for name in ["Grizzle Alyronia", "Sever Heartspear", "Galdon Whitehoof"]:
        order(0, name, "reabasteça as poções e retorne")
    started = time.monotonic()
    while time.monotonic() - started < 180:
        current = snapshot()
        phase["samples"].append(current)
        terminal = {
            v["bot_id"]: v
            for v in current["worker"].get("outcomes", [])
            if v.get("reason") == "supplies_bought_and_party_rejoined"
        }
        if len(terminal) == 3:
            break
        time.sleep(2)
    phase["after"] = snapshot()
    phase["result"] = {str(k): v for k, v in terminal.items()}
    save(phase)
    phase = {"name": "leader_transfer", "samples": [], "before": snapshot()}
    # Use follow goals instead of repeating the previous PM/hold acceptance.
    for name in ["Grizzle Alyronia", "Sever Heartspear", "Galdon Whitehoof"]:
        order(0, name, "siga")
    time.sleep(2)
    phase["transfer_requested_at"] = time.monotonic()
    q.command('return PartyQA("transfer")')
    phase["samples"] = sample_for(8)
    # Obsolete leader must not supersede the current leader's authority.
    order(0, "Grizzle Alyronia", "hunt")
    phase["samples"] += sample_for(3)
    phase["after"] = snapshot()
    phase["result"] = "inspect_authority_and_cancelled_outcomes"
    save(phase)
    phase = {
        "name": "worker_loss_fallback",
        "samples": [],
        "setup_teleport_upper_bound": 5,
    }
    q.command(
        "PartyScenario.cleanup();PartyScenario.baseline();return PartyScenario.placeHunt()"
    )
    time.sleep(3)
    phase["before"] = snapshot()
    order(1, "Grizzle Alyronia", "hunt")
    # Secondary fixtures need goals lasting beyond the five-second heartbeat.
    # Their purpose here is worker-loss cancellation, not re-proving PM/hold.
    for name in ["Sever Heartspear", "Galdon Whitehoof"]:
        order(1, name, "fique aguardando")
    time.sleep(2)
    phase["goals_before_stop"] = snapshot()
    phase["worker_stop_at"] = time.monotonic()
    phase["worker_signal"] = "SIGKILL"
    perf.stop_worker("SIGKILL")
    phase["samples"] = sample_for(7)
    phase["before_fallback_combat"] = snapshot()
    phase["fallback_wave"] = q.command("return PartyScenario.wave()")
    phase["samples"] += sample_for(12)
    phase["after"] = snapshot()
    phase["result"] = "inspect_worker_alive_and_owned_goals"
    save(phase)
    phase = {"name": "worker_restart", "samples": [], "before": snapshot()}
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
    phase["samples"] = sample_for(8)
    phase["after"] = snapshot()
    phase["result"] = "inspect_no_resurrected_goals"
    save(phase)
    phase = {"name": "leader_disconnect", "samples": [], "before": snapshot()}
    q.command('return PartyQA("dropB")')
    phase["samples"] = sample_for(8)
    phase["after_first_drop"] = snapshot()
    q.command('return PartyQA("dropA")')
    phase["samples"] += sample_for(8)
    phase["after"] = snapshot()
    phase["result"] = "inspect_no_offline_authority"
    save(phase)
    print("SCENARIOS_FINISHED", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume-after-hunt", action="store_true")
    main(parser.parse_args().resume_after_hunt)
