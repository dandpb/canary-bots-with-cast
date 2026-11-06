"""Reject incomplete clocks, unbound hunt outcomes and invented supply evidence."""

import copy
import unittest

from m5_qualification_gates import (
    fake_hunt_restart,
    native_phase_cycle,
    qualify_run,
    simultaneous_hunts,
)


def event(t_ms, kind, **data):
    return {"t_ms": t_ms, "kind": kind, "data": data}


def hunt(
    t_ms,
    action,
    *,
    kind="intent",
    status=None,
    bot_id=65001,
    world="world-a",
    operator=False,
    reason=None,
    metrics=None,
):
    data = {"action_id": action, "bot_id": bot_id, "world": world}
    if kind == "intent":
        data.update(candidate_id="hunt:399", mode="active", operator=operator)
    else:
        data.update(
            status=status, reason=reason or "objective_started", metrics=metrics or {}
        )
    return event(t_ms, kind, **data)


def fake_cycle():
    return [
        hunt(1, "first"),
        hunt(2, "first", kind="outcome", status="accepted"),
        hunt(
            300000,
            "first",
            kind="outcome",
            status="completed",
            reason="hunt_progress",
            metrics={"xp_delta": 725, "defeats_delta": 24},
        ),
        hunt(300001, "second"),
        hunt(300002, "second", kind="outcome", status="accepted"),
    ]


def phase(elapsed, name, script=77):
    return {
        "elapsed": elapsed,
        "command_id": int(elapsed),
        "status": f"Bot 'Grizzle': state=HUNTING hunt=[script={script} 'Hunt' phase={name} kills=3 wp=1]",
    }


class NativeCycleTests(unittest.TestCase):
    def test_ordered_cycle_includes_resume_and_tolerates_intermediate_phases(self):
        rows = [
            phase(541, "PATROLLING"),
            phase(647, "LEAVING"),
            phase(743, "RESUPPLYING"),
            phase(795, "PREPARING"),
            phase(946, "TRAVEL_TO"),
            phase(1020, "PATROLLING"),
        ]
        result = native_phase_cycle(rows)
        self.assertTrue(result["complete"])
        self.assertEqual(
            [row["phase"] for row in result["transitions"]],
            ["PATROLLING", "LEAVING", "RESUPPLYING", "PATROLLING"],
        )
        self.assertIn("does not establish an NPC purchase", result["meaning"])

    def test_reverse_or_incomplete_phases_do_not_qualify(self):
        self.assertFalse(
            native_phase_cycle(
                [phase(1, "RESUPPLYING"), phase(2, "LEAVING"), phase(3, "PATROLLING")]
            )["complete"]
        )
        self.assertFalse(
            native_phase_cycle(
                [phase(1, "PATROLLING"), phase(2, "LEAVING"), phase(3, "RESUPPLYING")]
            )["complete"]
        )

    def test_cannot_mix_departure_phases_from_two_hunts(self):
        rows = [
            phase(1, "PATROLLING", 77),
            phase(2, "LEAVING", 399),
            phase(3, "RESUPPLYING", 77),
            phase(4, "PATROLLING", 77),
        ]
        self.assertFalse(native_phase_cycle(rows)["complete"])

    def test_hunting_may_resume_with_a_new_hunt_after_resupply(self):
        rows = [
            phase(1, "PATROLLING"),
            phase(2, "LEAVING"),
            phase(3, "RESUPPLYING"),
            phase(4, "PATROLLING", 399),
        ]
        self.assertTrue(native_phase_cycle(rows)["complete"])


class FakeCycleTests(unittest.TestCase):
    def test_positive_bound_hunt_then_accepted_restart(self):
        result = fake_hunt_restart(fake_cycle())
        self.assertTrue(result["complete"])
        self.assertEqual(
            result["completed_hunt"]["identity"], ("first", 65001, "world-a")
        )
        self.assertEqual(result["restart"]["identity"], ("second", 65001, "world-a"))
        self.assertIn("not return or NPC purchase", result["meaning"])

    def test_completion_without_intent_or_accepted_ack_is_insufficient(self):
        events = fake_cycle()
        for removed in (0, 1):
            with self.subTest(removed=removed):
                self.assertFalse(
                    fake_hunt_restart(events[:removed] + events[removed + 1 :])[
                        "complete"
                    ]
                )

    def test_outcome_must_match_action_bot_and_world(self):
        for key, value in (
            ("action_id", "another"),
            ("bot_id", 65002),
            ("world", "world-b"),
        ):
            with self.subTest(key=key):
                events = fake_cycle()
                events[2]["data"][key] = value
                self.assertFalse(fake_hunt_restart(events)["complete"])

    def test_accepted_restart_requires_new_action_and_matching_context(self):
        events = fake_cycle()
        self.assertFalse(fake_hunt_restart(events[:-1])["complete"])
        for key, value in (
            ("action_id", "first"),
            ("world", "world-b"),
            ("bot_id", 65002),
        ):
            with self.subTest(key=key):
                changed = copy.deepcopy(events)
                for row in changed[-2:]:
                    row["data"][key] = value
                self.assertFalse(fake_hunt_restart(changed)["complete"])

    def test_no_progress_or_failed_objective_cannot_qualify(self):
        for change in (
            {"status": "failed"},
            {"reason": "no_confirmed_combat_progress"},
            {"metrics": {"xp_delta": 0, "defeats_delta": 24}},
            {"metrics": {"xp_delta": 725, "defeats_delta": 0}},
        ):
            events = fake_cycle()
            events[2]["data"].update(change)
            self.assertFalse(fake_hunt_restart(events)["complete"])

    def test_cannot_accept_a_restart_proposed_before_the_previous_completion(self):
        events = fake_cycle()
        events[-2]["t_ms"] = 299999
        self.assertFalse(fake_hunt_restart(events)["complete"])

    def test_human_or_automatic_operator_rescue_cannot_supply_the_restart(self):
        events = fake_cycle()
        events[-2]["data"]["operator"] = True
        self.assertFalse(fake_hunt_restart(events)["complete"])
        events = fake_cycle()
        events.insert(
            3, event(300000, "operator", operation="recover", automatic=False)
        )
        self.assertFalse(fake_hunt_restart(events)["complete"])


class FullGateTests(unittest.TestCase):
    def qualified(
        self,
        *,
        mode="fake",
        span=1800,
        observed=1800,
        elapsed=1800,
        reason="completed",
        metrics=None,
        saved_xp=200,
        initial_xp=100,
        extra=(),
        cycle=True,
    ):
        choices = [
            {"id": "hunt:77", "action": "hunt"},
            {"id": "hunt:399", "action": "hunt"},
        ]
        events = (
            [event(0, "sample", bot={"xp": 100}, actions=choices)]
            + (fake_cycle() if cycle else [])
            + [
                event(int(span * 1000), "sample", bot={"xp": 200}, actions=[]),
                event(
                    int(span * 1000),
                    "lifecycle",
                    phase="run_supervisor_stop",
                    reason=reason,
                    observed_seconds=observed,
                    elapsed_seconds=elapsed,
                ),
            ]
            + list(extra)
        )
        baseline_metrics = {
            "gaps": 0,
            "deaths": 0,
            "deaths_observed": True,
            "interventions": 0,
            "automatic_recoveries_requested": 0,
        }
        baseline_metrics.update(metrics or {})
        rows = (
            [
                phase(541, "PATROLLING"),
                phase(647, "LEAVING"),
                phase(743, "RESUPPLYING"),
                phase(1020, "PATROLLING"),
            ]
            if cycle
            else []
        )
        return qualify_run(
            mode=mode,
            run={"status": "completed", "incomplete": False},
            events=events,
            metrics=baseline_metrics,
            initial={"experience": initial_xp},
            saved={"experience": saved_xp},
            requests=0,
            statuses=rows,
        )

    def test_native_and_fake_run_checks_pass_independently_of_purchase_gate(self):
        for mode in ("native", "fake"):
            with self.subTest(mode=mode):
                result = self.qualified(mode=mode)
                self.assertTrue(result["accepted"], result["checks"])
                self.assertIn(
                    "NPC purchase/return proof remain separate", result["scope"]
                )

    def test_all_three_clocks_have_inclusive_bounds(self):
        for parameter in ("span", "observed", "elapsed"):
            for value, accepted in (
                (1799.999, False),
                (1800, True),
                (1805, True),
                (1805.001, False),
            ):
                with self.subTest(parameter=parameter, value=value):
                    self.assertEqual(
                        self.qualified(**{parameter: value})["accepted"], accepted
                    )

    def test_recorded_xp_without_database_persistence_is_rejected(self):
        self.assertFalse(self.qualified(saved_xp=100)["accepted"])
        self.assertFalse(self.qualified(initial_xp=200)["accepted"])

    def test_progress_and_horizon_cannot_qualify_without_required_cycle(self):
        for mode in ("native", "fake"):
            result = self.qualified(mode=mode, cycle=False)
            self.assertFalse(result["accepted"])
            self.assertFalse(result["checks"]["hunt_cycle"])

    def test_cleanup_time_hunt_outcomes_do_not_qualify_the_recorded_window(self):
        later = copy.deepcopy(fake_cycle())
        for row in later:
            row["t_ms"] += 1800001
        self.assertFalse(self.qualified(cycle=False, extra=later)["accepted"])

    def test_completion_reason_and_missing_telemetry_cannot_be_masked(self):
        self.assertFalse(self.qualified(reason="budget_stop")["accepted"])
        for metrics in (
            {"gaps": 1},
            {"deaths": 1},
            {"deaths_observed": False},
            {"interventions": 1},
        ):
            self.assertFalse(self.qualified(metrics=metrics)["accepted"])

    def test_automatic_recovery_metric_does_not_mask_a_rejected_gate(self):
        accepted = self.qualified(metrics={"automatic_recoveries_requested": 1})
        self.assertTrue(accepted["accepted"])
        self.assertEqual(accepted["evidence"]["automatic_recoveries_requested"], 1)
        self.assertFalse(
            self.qualified(
                reason="stalled", metrics={"automatic_recoveries_requested": 1}
            )["accepted"]
        )

    def test_human_intervention_event_rejects_even_if_metric_says_zero(self):
        self.assertFalse(
            self.qualified(
                extra=[event(600000, "operator", operation="recover", automatic=False)]
            )["accepted"]
        )

    def test_multiple_terminal_stops_cannot_hide_an_earlier_failure(self):
        result = self.qualified(
            extra=[
                event(
                    1799000,
                    "lifecycle",
                    phase="run_supervisor_stop",
                    reason="budget_stop",
                    observed_seconds=1799,
                    elapsed_seconds=1799,
                )
            ]
        )
        self.assertFalse(result["accepted"])

    def test_hunts_must_be_simultaneous_not_just_ever_present(self):
        events = [
            event(0, "sample", actions=[{"id": "hunt:77", "action": "hunt"}]),
            event(1, "sample", actions=[{"id": "hunt:399", "action": "hunt"}]),
        ]
        self.assertFalse(simultaneous_hunts(events)["offered"])


if __name__ == "__main__":
    unittest.main()
