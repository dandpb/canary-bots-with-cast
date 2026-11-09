"""Passive trace is diagnostic and cannot manufacture a qualified hunt."""

import unittest

from hunt_phase_trace import diagnose


BOT_NAME = "Grizzle Alyronia"
BOT_GUID = 65001
SCRIPT_ID = 399


def status(elapsed, phase, *, bot=BOT_NAME, script=SCRIPT_ID,
           guid=None, hunt_instance=None):
    row = {
        "elapsed": elapsed,
        "command_id": int(elapsed),
        "status": (
            f"Bot '{bot}': state=HUNTING "
            f"hunt=[script={script} 'Hunt' phase={phase} kills=78 wp=1]"
        ),
    }
    if guid is not None:
        row["bot_guid"] = guid
    if hunt_instance is not None:
        row["hunt_instance_id"] = hunt_instance
    return row


def trace(mono_ms, old, new, *, bot=BOT_GUID, script=SCRIPT_ID):
    return (
        f"[HUNT:PHASE] mono_ms={mono_ms} bot_guid={bot} script_id={script} "
        f"from={old} to={new}"
    )


def diagnose_target(lines, rows):
    return diagnose(lines, rows, bot_guid=BOT_GUID, script_id=SCRIPT_ID,
                    bot_name=BOT_NAME)


class HuntPhaseTraceTests(unittest.TestCase):
    def test_short_leaving_is_diagnostic_not_a_status_sample(self):
        lines = [
            trace(100_000, "PATROLLING", "LEAVING"),
            trace(102_000, "LEAVING", "RESUPPLYING"),
            trace(125_000, "RESUPPLYING", "PATROLLING"),
        ]
        rows = [status(100, "PATROLLING"), status(110, "RESUPPLYING"),
                status(135, "PATROLLING")]
        result = diagnose_target(lines, rows)
        self.assertTrue(result["trace_observed_links_match"])
        self.assertEqual(result["trace_coverage"], "partial")
        self.assertEqual([row["to"] for row in result["transitions"]],
                         ["LEAVING", "RESUPPLYING", "PATROLLING"])
        self.assertFalse(result["status_phase_sequence_observed"])
        self.assertFalse(result["status_hunt_cycle_proven"])

    def test_explicit_correlated_status_can_prove_one_hunt(self):
        rows = [status(100, "PATROLLING", guid=BOT_GUID, hunt_instance="a"),
                status(101, "LEAVING", guid=BOT_GUID, hunt_instance="a"),
                status(110, "RESUPPLYING", guid=BOT_GUID, hunt_instance="a"),
                status(135, "PATROLLING", guid=BOT_GUID, hunt_instance="a")]
        result = diagnose_target([], rows)
        self.assertTrue(result["status_phase_sequence_observed"])
        self.assertTrue(result["status_hunt_cycle_proven"])
        self.assertEqual(result["transitions"], [])
        self.assertFalse(result["trace_observed_links_match"])

    def test_foreign_bot_or_script_cannot_complete_target(self):
        rows = [status(100, "PATROLLING"),
                status(101, "LEAVING", bot="Someone Else"),
                status(102, "RESUPPLYING", script=77),
                status(103, "PATROLLING")]
        result = diagnose_target([], rows)
        self.assertFalse(result["status_phase_sequence_observed"])
        self.assertFalse(result["status_hunt_cycle_proven"])

    def test_other_trace_identity_and_missing_link_are_not_merged(self):
        lines = [trace(100_000, "PATROLLING", "LEAVING"),
                 trace(101_000, "LEAVING", "RESUPPLYING", bot=65002),
                 trace(102_000, "RESUPPLYING", "PATROLLING")]
        result = diagnose_target(lines, [])
        self.assertEqual(len(result["transitions"]), 2)
        self.assertFalse(result["trace_observed_links_match"])

    def test_singleton_is_not_contiguity_proof(self):
        result = diagnose_target([trace(100_000, "PATROLLING", "LEAVING")], [])
        self.assertFalse(result["trace_observed_links_match"])
        self.assertEqual(result["trace_coverage"], "partial")

    def test_matching_observed_links_cannot_rule_out_lost_cycle(self):
        # An unobserved cycle could leave the phase at LEAVING again between
        # these two events. Adjacency is not coverage or a loss-free claim.
        lines = [trace(100_000, "PATROLLING", "LEAVING"),
                 trace(130_000, "LEAVING", "RESUPPLYING")]
        result = diagnose_target(lines, [])
        self.assertTrue(result["trace_observed_links_match"])
        self.assertEqual(result["trace_coverage"], "partial")

    def test_final_patrolling_from_another_hunt_is_not_proven(self):
        rows = [status(100, "PATROLLING", guid=BOT_GUID, hunt_instance="a"),
                status(101, "LEAVING", guid=BOT_GUID, hunt_instance="a"),
                status(110, "RESUPPLYING", guid=BOT_GUID, hunt_instance="a"),
                status(135, "PATROLLING", guid=BOT_GUID, hunt_instance="b")]
        result = diagnose_target([], rows)
        self.assertTrue(result["status_phase_sequence_observed"])
        self.assertFalse(result["status_same_hunt_proven"])
        self.assertFalse(result["status_hunt_cycle_proven"])

    def test_historical_status_without_guid_or_instance_is_not_proof(self):
        rows = [status(100, "PATROLLING"), status(101, "LEAVING"),
                status(110, "RESUPPLYING"), status(135, "PATROLLING")]
        result = diagnose_target([], rows)
        self.assertTrue(result["status_phase_sequence_observed"])
        self.assertFalse(result["status_hunt_cycle_proven"])


if __name__ == "__main__":
    unittest.main()
