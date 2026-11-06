"""Financial diagnostic failures never hide the original provider outcome."""

import asyncio
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from canary_brain.gateway import GatewayConfiguration, GatewayProvider
from canary_brain.protocol import Observation
from canary_brain.provider import Prices
from canary_brain.recording import (
    Manifest,
    Recorder,
    RecordingConfiguration,
    ReplayReader,
    attribution,
)
from canary_brain.store import Store


class FinancialFailureTests(unittest.IsolatedAsyncioTestCase):
    async def exercise(self, outcome):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ledger, recording = (
                root / "synthetic-ledger.db",
                root / "synthetic-replay.db",
            )
            store = Store(ledger)
            locker = sqlite3.connect(ledger)
            recorder = Recorder(
                RecordingConfiguration(path=recording, namespace="synthetic"),
                [
                    Manifest(
                        run_id="synthetic:1",
                        bot_id=1,
                        lineage="synthetic",
                        synthetic=True,
                    )
                ],
            )
            config = GatewayConfiguration(
                alias="synthetic",
                effective_model="synthetic-model",
                deployment_id="synthetic-deployment",
                provider="test",
                version="offline",
                configuration_sha256="a" * 64,
                prices=Prices(
                    version="offline",
                    input_nanousd=1,
                    cached_nanousd=1,
                    cache_write_nanousd=1,
                    output_nanousd=1,
                ),
            )

            async def create(**body):
                locker.execute("BEGIN IMMEDIATE")
                if outcome == "deadline":
                    await asyncio.sleep(1)
                payload = {"model": "synthetic", "id": "offline", "output": []}
                if outcome == "settle":
                    payload["usage"] = {"input_tokens": 10, "output_tokens": 2}
                return SimpleNamespace(
                    headers={"x-litellm-model-id": "synthetic-deployment"},
                    parse=lambda: SimpleNamespace(model_dump=lambda **_: payload),
                )

            client = SimpleNamespace(
                responses=SimpleNamespace(
                    with_raw_response=SimpleNamespace(create=create)
                )
            )
            provider = GatewayProvider(
                store, client, 0.03, gateway=config, recorder=recorder
            )
            snapshot = Observation.model_validate(
                {
                    "version": 1,
                    "type": "observation",
                    "world": "synthetic",
                    "sequence": 1,
                    "captured_ms": 1,
                    "lease": "synthetic",
                    "objective_generation": 1,
                    "bot": {
                        "id": 1,
                        "name": "Synthetic",
                        "level": 8,
                        "vocation": 1,
                        "state": "IDLE",
                        "position": [1, 1, 7],
                        "health": 100,
                        "mana": 100,
                        "potions": 10,
                        "xp": 4200,
                        "alive": True,
                    },
                    "actions": [
                        {
                            "id": "continue",
                            "action": "continue",
                            "description": "Keep moving",
                            "ttl_ms": 1000,
                        },
                        {
                            "id": "resupply",
                            "action": "resupply",
                            "description": "Restock",
                            "ttl_ms": 1000,
                        },
                    ],
                }
            )
            expected = {
                "deadline": TimeoutError,
                "usage": TypeError,
                "settle": sqlite3.OperationalError,
            }[outcome]
            try:
                with (
                    self.assertRaises(expected) as caught,
                    attribution(1, "synthetic-decision"),
                ):
                    await provider.decide(snapshot)
            finally:
                locker.rollback()
                locker.close()
                recorder.close()
            events = [
                event["data"]
                for event in ReplayReader(recording).all_events("synthetic:1")
                if event["kind"] == "request"
            ]
            self.assertEqual(
                [event["phase"] for event in events], ["reserved", "failed"]
            )
            failed = events[-1]
            self.assertEqual(failed["error"], expected.__name__)
            self.assertEqual(
                failed["diagnostic_failure"]["sqlite_errorcode"], sqlite3.SQLITE_BUSY
            )
            self.assertEqual(failed["diagnostic_failure"]["stage"], "store.put")
            self.assertTrue(failed["unsettled"])
            self.assertEqual(store.budget()["reserved"], events[0]["reserved_nanousd"])
            if outcome == "settle":
                self.assertEqual(caught.exception.sqlite_errorcode, sqlite3.SQLITE_BUSY)
                self.assertEqual(failed["sqlite_errorcode"], sqlite3.SQLITE_BUSY)
                self.assertEqual(failed["stage"], "store.settle")
            if outcome == "deadline":
                self.assertEqual(failed["timeout_origin"], "outer_deadline")
            self.assertNotIn("database is locked", json.dumps(failed))

    async def test_storage_error_cannot_hide_the_original_usage_error(self):
        await self.exercise("usage")

    async def test_storage_error_cannot_hide_the_original_deadline(self):
        await self.exercise("deadline")

    async def test_original_sqlite_code_and_stage_survive_another_sqlite_failure(self):
        await self.exercise("settle")


if __name__ == "__main__":
    unittest.main()
