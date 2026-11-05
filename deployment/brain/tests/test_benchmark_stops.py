import copy
import unittest

from canary_brain.benchmark_stops import Stops


def observation(**changes):
    data = {
        "type": "observation",
        "world": "w",
        "autonomous": True,
        "bot": {
            "position": [1, 2, 7],
            "xp": 100,
            "potions": 40,
            "alive": True,
            "objective_running": False,
        },
        "actions": [{"action": "hunt"}, {"action": "resupply"}],
    }
    data["bot"].update(changes)
    return data


def request(count=2):
    return {"phase": "requested", "observation": {"actions": [{}] * count}}


class SupervisorTests(unittest.TestCase):
    def test_horizon_starts_at_first_observation_not_launch(self):
        s = Stops(stall_seconds=99999)
        self.assertIsNone(s.check(900))
        s.observe(observation(), 1000)
        s.observe(observation(), 2799)
        self.assertIsNone(s.check(2799))
        s.observe(observation(), 2800)
        self.assertEqual(s.check(2800), "completed")

    def test_repeated_requests_do_not_restart_the_timeout(self):
        s = Stops()
        s.observe(observation(), 0)
        s.decision(request(), 0)
        s.decision(request(), 20)
        s.observe(observation(), 30)
        self.assertIsNone(s.check(30))
        self.assertEqual(s.check(30.01), "proposal_timeout")

    def test_unvalidated_proposal_does_not_clear_the_window(self):
        s = Stops()
        s.observe(observation(), 0)
        s.decision(request(), 0)
        s.decision({"phase": "model_proposed"}, 29)
        s.observe(observation(), 31)
        self.assertEqual(s.check(31), "proposal_timeout")

    def test_validated_selection_clears_the_window(self):
        s = Stops()
        s.observe(observation(), 0)
        s.decision(request(), 0)
        s.decision({"phase": "selected"}, 29)
        s.observe(observation(), 40)
        self.assertIsNone(s.check(40))

    def test_native_has_no_provider_timeout(self):
        s = Stops(model=False)
        s.observe(observation(), 0)
        s.decision(request(), 0)
        s.observe(observation(), 40)
        self.assertIsNone(s.check(40))

    def test_running_native_objective_closes_opportunity(self):
        s = Stops()
        s.observe(observation(), 0)
        s.decision(request(), 0)
        s.observe(observation(objective_running=True), 20)
        s.observe(observation(objective_running=True), 40)
        self.assertIsNone(s.check(40))

    def test_single_candidate_closes_opportunity(self):
        s = Stops()
        s.observe(observation(), 0)
        s.decision(request(), 0)
        s.decision(request(1), 20)
        s.observe(observation(), 40)
        self.assertIsNone(s.check(40))

    def test_candidate_disappearance_closes_opportunity(self):
        s = Stops()
        s.observe(observation(), 0)
        s.decision(request(), 0)
        p = observation()
        p["actions"] = [{"action": "continue"}, {"action": "hold"}]
        s.observe(p, 40)
        self.assertIsNone(s.check(40))

    def test_staleness_and_stall_are_different(self):
        s = Stops()
        s.observe(observation(), 0)
        self.assertEqual(s.check(5.01), "observation_stale")
        s.observe(observation(), 600)
        self.assertEqual(s.check(600), "stalled")

    def test_observed_movement_or_xp_resets_stall(self):
        for change in ({"position": [2, 2, 7]}, {"xp": 101}, {"potions": 39}):
            s = Stops()
            s.observe(observation(), 0)
            s.observe(observation(**change), 599)
            self.assertIsNone(s.check(600))

    def test_cumulative_deaths_have_an_initial_baseline(self):
        s = Stops()
        s.observe({"type": "telemetry", "world": "w", "deaths": 12}, 0)
        s.observe(observation(), 0)
        s.observe({"type": "telemetry", "world": "w", "deaths": 14}, 1)
        self.assertIsNone(s.check(1))
        s.observe({"type": "telemetry", "world": "w", "deaths": 15}, 2)
        self.assertEqual(s.check(2), "deaths_limit")

    def test_world_reset_stops_instead_of_restarting_the_clock(self):
        s = Stops()
        s.observe(observation(), 0)
        p = copy.deepcopy(observation())
        p["world"] = "next"
        s.observe(p, 1)
        self.assertEqual(s.check(1), "world_changed")


if __name__ == "__main__":
    unittest.main()
