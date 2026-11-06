"""Rehashed-copy controls; public files only, no SQLite or external calls."""

import hashlib
import json
import runpy
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
verify = runpy.run_path(str(ROOT / "verify_bundle.py"))["verify"]


class PublicControls(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.copy = Path(self.temporary.name) / "copy"
        shutil.copytree(ROOT, self.copy)

    def change(self, name, function):
        path = self.copy / name
        value = json.loads(path.read_text())
        function(value)
        path.write_text(json.dumps(value, indent=2) + "\n")
        self.reindex()

    def reindex(self):
        index = {
            p.relative_to(self.copy).as_posix(): hashlib.sha256(
                p.read_bytes()
            ).hexdigest()
            for p in self.copy.rglob("*")
            if p.is_file() and p != self.copy / "checksums.json"
        }
        (self.copy / "checksums.json").write_text(json.dumps(index, indent=2) + "\n")

    def archive_run_change(self, name, function):
        path = self.copy / "replays" / name
        with zipfile.ZipFile(path) as archive:
            contents = {n: archive.read(n) for n in archive.namelist()}
        metadata = json.loads(contents["run.json"])
        function(metadata)
        contents["run.json"] = json.dumps(metadata).encode()
        integrity = json.loads(contents["integrity.json"])
        integrity["sha256"] = {
            n: hashlib.sha256(data).hexdigest()
            for n, data in contents.items()
            if n != "integrity.json"
        }
        contents["integrity.json"] = json.dumps(integrity).encode()
        with zipfile.ZipFile(path, "w") as archive:
            for n, data in contents.items():
                archive.writestr(n, data)
        self.reindex()

    def test_actual_partial_bundle_passes(self):
        self.assertEqual(verify(self.copy)["selected_financial_rows"], 18)

    def test_no_fabricated_comparative_completion(self):
        self.change(
            "summary.json",
            lambda v: v.update(
                comparative_pilot_completed=True,
                completed_game_runs=9,
                ai_game_runs_started=6,
            ),
        )
        with self.assertRaisesRegex(ValueError, "partial campaign forged"):
            verify(self.copy)

    def test_missing_game_metrics_remain_unobserved(self):
        self.change(
            "summary.json",
            lambda v: v.update(not_started_gameplay_metrics={"xp": 0, "deaths": 0}),
        )
        with self.assertRaisesRegex(ValueError, "missing games forged"):
            verify(self.copy)

    def test_known_unknown_partition_not_just_grand_total(self):
        self.change(
            "summary.json",
            lambda v: v.update(known_spent_nanousd=0, unknown_reserved_nanousd=7227375),
        )
        with self.assertRaisesRegex(ValueError, "summary financial partition"):
            verify(self.copy)

    def test_per_id_spend_swap_preserving_totals_rejected(self):
        def swap(value):
            rows = [r for r in value["requests"] if r["spent"] is not None]
            first = rows[0]
            second = next(r for r in rows if r["spent"] != first["spent"])
            first["spent"], second["spent"] = second["spent"], first["spent"]

        self.change("closed-executor-ledger.json", swap)
        with self.assertRaisesRegex(ValueError, "per-request Finance mismatch"):
            verify(self.copy)

    def test_equal_float_is_not_integer_reservation(self):
        self.change(
            "closed-executor-ledger.json",
            lambda v: v["requests"][0].update(
                reserved=float(v["requests"][0]["reserved"])
            ),
        )
        with self.assertRaisesRegex(ValueError, "invalid monetary integer"):
            verify(self.copy)

    def test_acceptance_cannot_contradict_canonical_report(self):
        self.change(
            "report/acceptance.json",
            lambda v: v.update(
                ready_for_review=True, financial_final=True, findings=[]
            ),
        )
        with self.assertRaisesRegex(ValueError, "acceptance contradicts"):
            verify(self.copy)

    def test_canonical_native_cannot_become_openai_completed_xp(self):
        def forge(v):
            row = v["runs"][0]
            row.update(
                participant="openai",
                status="completed",
                stop_reason="completed",
                observed_span_ms=1800000,
            )
            row["metrics"].update(xp_delta=50000)

        self.change("report/report.json", forge)
        with self.assertRaisesRegex(ValueError, "original canonical output changed"):
            verify(self.copy)

    def test_probe_unknown_cost_cannot_be_forged_as_final_zero(self):
        self.change(
            "openai-probe-result.json",
            lambda v: v["qualification"].update(
                liability_nanousd=0, unknown_nanousd=0, financial_final=True
            ),
        )
        with self.assertRaisesRegex(ValueError, "original canonical output changed"):
            verify(self.copy)

    def test_global_cost_cannot_be_attributed_to_native(self):
        self.change(
            "report/report.json",
            lambda v: v["runs"][0].update(ledger_spent_nanousd=v["settled_nanousd"]),
        )
        with self.assertRaisesRegex(ValueError, "original canonical output changed"):
            verify(self.copy)

    def test_critical_findings_cannot_be_replaced_preserving_count(self):
        def forge(v):
            for finding in v["findings"][:4]:
                finding["code"] = "benign"

        self.change("report/report.json", forge)
        with self.assertRaisesRegex(ValueError, "original canonical output changed"):
            verify(self.copy)

    def test_sidecar_cannot_claim_full_horizon_or_frames(self):
        self.change(
            "video/native-partial-60x.mp4.json",
            lambda v: v.update(video_seconds=1800, frames=43200, end_ms=1800000),
        )
        with self.assertRaisesRegex(ValueError, "video"):
            verify(self.copy)

    def test_openai_failed_recorder_state_cannot_be_relabelled_completed(self):
        self.archive_run_change(
            "openai-probe.replay.zip",
            lambda v: v.update(status="completed", incomplete=False),
        )
        with self.assertRaisesRegex(ValueError, "probe recorder state relabelled"):
            verify(self.copy)

    def test_complete_cap_cannot_be_raised_in_summary(self):
        self.change(
            "summary.json", lambda v: v.update(complete_cap_nanousd=70000000000)
        )
        with self.assertRaisesRegex(ValueError, "complete cap differs"):
            verify(self.copy)

    def test_partial_native_progress_cannot_be_invented(self):
        self.change(
            "summary.json",
            lambda v: v["native_fragment"].update(xp_delta_observed=9999),
        )
        with self.assertRaisesRegex(
            ValueError, "partial fragment metrics/scope changed"
        ):
            verify(self.copy)

    def test_derived_probe_metrics_cannot_erase_unknown_liability(self):
        self.change(
            "probe-metrics.json",
            lambda v: v["probes"]["openai"]["qualification"].update(
                liability_nanousd=0, unknown_nanousd=0, financial_final=True
            ),
        )
        with self.assertRaisesRegex(ValueError, "original canonical output changed"):
            verify(self.copy)

    def test_execution_output_cannot_claim_success_against_closure(self):
        def forge(value):
            value["campaign"] = {
                "completed_game_runs": 9,
                "winner": "openai",
                "status": "completed",
            }
            del value["error_type"]
            del value["failure"]

        self.change("execution-result.json", forge)
        with self.assertRaisesRegex(
            ValueError, "execution result contradicts closed invocation"
        ):
            verify(self.copy)


if __name__ == "__main__":
    unittest.main()
