"""Behavior tests for canary-status: verdict rollup and digest artifact parsing.

Seams under test: ``evaluate(report)`` (the verdict a consumer acts on) and
``latest_digest(directory)`` (the S1 artifact the panel surfaces). No Docker,
no network: fixtures are literal facts, expected verdicts come from the S1
contract in AI_WORKFLOW.md, not from the implementation.
"""

import importlib.util
import os
import tempfile
import time
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("canary-status.py")
spec = importlib.util.spec_from_file_location("canary_status", MODULE_PATH)
cs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cs)


def healthy_report():
    return {
        "services": [
            {"service": name, "state": "running", "health": "healthy",
             "status": "Up 3 hours (healthy)"}
            for name in ("database", "game", "web")
        ],
        "services_error": None,
        "status": {"players_online": 501, "players_peak": 82,
                   "uptime_seconds": 9685, "client_protocol": "15.0",
                   "server_version": "3.0"},
        "status_error": None,
        "endpoints": {
            "site": {"reachable": True, "status": 200},
            "worldmap": {"reachable": True, "status": 200, "offline": False},
            "litellm": {"reachable": True, "status": 200},
            "tcp_7171": {"reachable": True},
            "tcp_7172": {"reachable": True, "challenge": True},
        },
        "digest": {"path": "2026-11-19.md", "verdict": "GREEN",
                   "age_seconds": 60},
        "digest_error": None,
    }


class EvaluateVerdict(unittest.TestCase):
    def test_all_healthy_is_green(self):
        report = cs.evaluate(healthy_report())
        self.assertEqual(report["verdict"], "GREEN")
        self.assertEqual(report["exit_code"], 0)
        self.assertEqual(report["findings"], [])

    def test_exited_service_is_red(self):
        report = healthy_report()
        report["services"].append(
            {"service": "clickhouse", "state": "exited", "health": "none",
             "status": "Exited (0) 6 days ago"})
        report = cs.evaluate(report)
        self.assertEqual(report["verdict"], "RED")
        self.assertEqual(report["exit_code"], 2)
        self.assertTrue(any("clickhouse" in f for f in report["findings"]))

    def test_unhealthy_service_is_red(self):
        report = healthy_report()
        report["services"][1]["health"] = "unhealthy"
        self.assertEqual(cs.evaluate(report)["verdict"], "RED")

    def test_starting_service_is_amber(self):
        report = healthy_report()
        report["services"][1]["health"] = "starting"
        self.assertEqual(cs.evaluate(report)["verdict"], "AMBER")

    def test_unanswered_status_request_is_red(self):
        report = healthy_report()
        report["status"] = None
        report["status_error"] = "status port unreachable"
        self.assertEqual(cs.evaluate(report)["verdict"], "RED")

    def test_empty_population_is_red_and_low_is_amber(self):
        report = healthy_report()
        report["status"]["players_online"] = 0
        self.assertEqual(cs.evaluate(report)["verdict"], "RED")
        report = healthy_report()
        report["status"]["players_online"] = 5
        self.assertEqual(cs.evaluate(report)["verdict"], "AMBER")

    def test_unreachable_endpoint_is_amber(self):
        report = healthy_report()
        report["endpoints"]["litellm"] = {"reachable": False, "status": None}
        report = cs.evaluate(report)
        self.assertEqual(report["verdict"], "AMBER")
        self.assertTrue(any("litellm" in f for f in report["findings"]))

    def test_worldmap_reporting_offline_is_amber(self):
        report = healthy_report()
        report["endpoints"]["worldmap"]["offline"] = True
        self.assertEqual(cs.evaluate(report)["verdict"], "AMBER")

    def test_docker_collector_failure_is_red(self):
        report = healthy_report()
        report["services"] = []
        report["services_error"] = "docker unreachable"
        self.assertEqual(cs.evaluate(report)["verdict"], "RED")

    def test_stale_or_missing_digest_is_amber(self):
        report = healthy_report()
        report["digest"]["age_seconds"] = 30 * 3600
        self.assertEqual(cs.evaluate(report)["verdict"], "AMBER")
        report = healthy_report()
        report["digest"] = None
        report["digest_error"] = "no digest artifact"
        self.assertEqual(cs.evaluate(report)["verdict"], "AMBER")

    def test_historical_digest_verdict_does_not_change_live_verdict(self):
        report = healthy_report()
        report["digest"]["verdict"] = "RED"
        self.assertEqual(cs.evaluate(report)["verdict"], "GREEN")


class LatestDigest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)

    def _write(self, name, body, age_seconds):
        path = self.dir / name
        path.write_text(body, encoding="utf-8")
        stamp = time.time() - age_seconds
        os.utime(path, (stamp, stamp))
        return path

    def test_picks_newest_markdown_and_parses_verdict(self):
        self._write("2026-11-18.md", "# old\n\n**Verdict: GREEN**\n", 90000)
        newer = self._write(
            "2026-11-19-status.md",
            "# Canary bots ops digest - 2026-11-19T23:37:14+00:00\n\n"
            "**Verdict: RED**\n", 3600)
        digest, error = cs.latest_digest(self.dir)
        self.assertIsNone(error)
        self.assertEqual(digest["path"], str(newer))
        self.assertEqual(digest["verdict"], "RED")
        self.assertTrue(3500 < digest["age_seconds"] < 3700)

    def test_missing_directory_reports_error_not_crash(self):
        digest, error = cs.latest_digest(self.dir / "absent")
        self.assertIsNone(digest)
        self.assertTrue(error)

    def test_markdown_without_verdict_line_is_unknown(self):
        self._write("notes.md", "# scratch notes\nno verdict here\n", 60)
        digest, error = cs.latest_digest(self.dir)
        self.assertIsNone(error)
        self.assertIsNone(digest["verdict"])


if __name__ == "__main__":
    unittest.main()
