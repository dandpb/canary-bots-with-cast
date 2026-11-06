"""Pure file-copy controls; no SQLite, runtime, credentials, or external access."""

import hashlib
import json
import runpy
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path

MODULE = runpy.run_path(str(Path(__file__).with_name("verify_financial_v2.py")))
PARENT = MODULE["PARENT"]
verify = MODULE["verify"]
v1_verify = MODULE["v1_verify"]
FIRST = "2ad399344ae54433b080c600156eefd6"
SECOND = "81c26627802f4161a43d40a0d0b1f26f"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def hashes(root):
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in root.rglob("*")
        if path.is_file()
    }


def rehash(root):
    finance = root / "finance-1821"
    nested = read(finance / "checksums.json")
    contents = nested.get("files", nested)
    for name in contents:
        contents[name] = hashlib.sha256((finance / name).read_bytes()).hexdigest()
    write(finance / "checksums.json", nested)
    index = hashes(root)
    del index["checksums.json"]
    write(root / "checksums.json", index)


def swap_rows(rows, id_key, spent_key):
    indexed = {row[id_key]: row for row in rows}
    first, second = indexed[FIRST], indexed[SECOND]
    first[spent_key], second[spent_key] = second[spent_key], first[spent_key]


class FinancialControls(unittest.TestCase):
    def setUp(self):
        self.original = hashes(PARENT)
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.copy = Path(self.temporary.name) / "public-copy"
        shutil.copytree(PARENT, self.copy)

    def tearDown(self):
        self.assertEqual(hashes(PARENT), self.original, "published parent changed")

    def mutate(self, name, function):
        path = self.copy / name
        value = read(path)
        function(value)
        write(path, value)
        rehash(self.copy)

    def reject_after_v1_pass(self, message):
        self.assertEqual(v1_verify(self.copy)["accounting_rows"], 10)
        with self.assertRaisesRegex(ValueError, message):
            verify(self.copy)

    def test_published_data_passes_without_parent_changes(self):
        MODULE["verify_supplement"]()
        result = verify(self.copy)
        self.assertEqual(result["known_new_spent_nanousd"], 285800)
        self.assertEqual(result["unknown_new_reserved_nanousd"], 942250)
        self.assertEqual(result["prior_known_spent_nanousd"], 577700)
        self.assertEqual(result["prior_unknown_reserved_nanousd"], 3357050)
        self.assertEqual(result["cumulative_liability_nanousd"], 5162800)
        self.assertIs(result["financial_final"], False)

    def test_finance_reproduction_summary_partition(self):
        self.mutate(
            "summary.json",
            lambda value: value.update(
                known_new_spent_nanousd=0,
                cumulative_known_spent_nanousd=0,
                cumulative_unknown_reserved_nanousd=5162800,
            ),
        )
        self.reject_after_v1_pass("summary known_new_spent_nanousd does not reconcile")

    def test_finance_reproduction_ledger_spend_swap(self):
        self.mutate(
            "closed-executor-ledger-projection.json",
            lambda value: swap_rows(value["requests"], "id", "spent"),
        )
        self.reject_after_v1_pass("replay settled spend does not reconcile")

    def test_coordinated_ledger_and_finance_swap_still_rejected(self):
        self.mutate(
            "closed-executor-ledger-projection.json",
            lambda value: swap_rows(value["requests"], "id", "spent"),
        )
        self.mutate(
            "finance-1821/r2-postclosure-financial.public.json",
            lambda value: swap_rows(
                value["new_requests"], "request_id", "spent_nanousd"
            ),
        )
        self.reject_after_v1_pass("replay settled spend does not reconcile")

    def test_usage_pricing_rejects_coordinated_three_source_spend_swap(self):
        self.mutate(
            "closed-executor-ledger-projection.json",
            lambda value: swap_rows(value["requests"], "id", "spent"),
        )
        self.mutate(
            "finance-1821/r2-postclosure-financial.public.json",
            lambda value: swap_rows(
                value["new_requests"], "request_id", "spent_nanousd"
            ),
        )
        path = self.copy / "openai-r2-decisions.replay.zip"
        with zipfile.ZipFile(path) as archive:
            members = {name: archive.read(name) for name in archive.namelist()}
        for name in members.keys() - {"integrity.json", "run.json"}:
            events = json.loads(members[name])
            finished = [
                event["data"]
                for event in events
                if event["kind"] == "request" and event["data"]["phase"] == "finished"
            ]
            swap_rows(finished, "request_id", "spent_nanousd")
            members[name] = json.dumps(events).encode()
        integrity = json.loads(members["integrity.json"])
        integrity["sha256"] = {
            name: hashlib.sha256(data).hexdigest()
            for name, data in members.items()
            if name != "integrity.json"
        }
        members["integrity.json"] = json.dumps(integrity).encode()
        with zipfile.ZipFile(path, "w") as archive:
            for name, data in members.items():
                archive.writestr(name, data)
        rehash(self.copy)
        self.reject_after_v1_pass("usage-priced spend does not reconcile")

    def test_summary_money_requires_integer_not_equal_float_or_string(self):
        for amount in (285800.0, "285800"):
            with self.subTest(amount=amount):
                self.mutate(
                    "summary.json",
                    lambda value, amount=amount: value.update(
                        known_new_spent_nanousd=amount
                    ),
                )
                self.reject_after_v1_pass("must be a nonnegative integer")

    def test_boolean_claim_count_is_not_an_integer_count(self):
        self.mutate(
            "finance-1821/r2-postclosure-financial.public.json",
            lambda value: value["recovery_claim"].update(count=True),
        )
        self.reject_after_v1_pass("claim count must be a nonnegative integer")

    def test_row_money_rejects_equal_floats_in_each_source(self):
        cases = [
            ("closed-executor-ledger-projection.json", "requests", "id", "reserved"),
            ("closed-executor-ledger-projection.json", "requests", "id", "spent"),
            (
                "finance-1821/r2-postclosure-financial.public.json",
                "new_requests",
                "request_id",
                "spent_nanousd",
            ),
        ]
        for name, rows_key, id_key, money_key in cases:
            with self.subTest(source=name, money_key=money_key):
                shutil.copytree(PARENT, self.copy, dirs_exist_ok=True)

                def change(
                    value, rows_key=rows_key, id_key=id_key, money_key=money_key
                ):
                    row = next(row for row in value[rows_key] if row[id_key] == FIRST)
                    row[money_key] = float(row[money_key])

                self.mutate(name, change)
                self.reject_after_v1_pass("must be a nonnegative integer")

    def test_new_request_run_identity_must_match_replay(self):
        def change(value):
            next(row for row in value["requests"] if row["id"] == FIRST)["run_id"] = (
                "other"
            )

        self.mutate("closed-executor-ledger-projection.json", change)
        self.reject_after_v1_pass("new ledger run ID differs")

    def test_new_settled_reservation_must_match_replay(self):
        def change(value):
            next(row for row in value["requests"] if row["id"] == FIRST)[
                "reserved"
            ] += 1

        self.mutate("closed-executor-ledger-projection.json", change)
        self.reject_after_v1_pass("replay reservation does not reconcile")


if __name__ == "__main__":
    unittest.main()
