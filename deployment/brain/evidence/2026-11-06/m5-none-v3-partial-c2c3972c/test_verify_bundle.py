"""Rehashed-copy controls; public files only, no SQLite or external calls."""

import hashlib
import json
import runpy
import shutil
import tempfile
import unittest
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
        index = {
            p.relative_to(self.copy).as_posix(): hashlib.sha256(
                p.read_bytes()
            ).hexdigest()
            for p in self.copy.rglob("*")
            if p.is_file() and p != self.copy / "checksums.json"
        }
        (self.copy / "checksums.json").write_text(json.dumps(index, indent=2) + "\n")

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


if __name__ == "__main__":
    unittest.main()
