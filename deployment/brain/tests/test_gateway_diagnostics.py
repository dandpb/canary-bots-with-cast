"""Finished gateway diagnostics explain rejected choices without recording output."""

import json

import pytest
from test_gateway_reasoning import configuration, sdk
from test_protocol import observation
from test_recording import recorder

from canary_brain.gateway import GatewayProvider
from canary_brain.protocol import Observation
from canary_brain.recording import ReplayReader, attribution
from canary_brain.store import Store


async def test_incomplete_choice_is_charged_and_records_only_safe_diagnostics(tmp_path):
    recording = recorder(tmp_path)
    store = Store(tmp_path / "synthetic.db")
    response = {
        "status": "incomplete",
        "incomplete_details": {"reason": "max_output_tokens"},
        "output": [],
        "usage": {
            "input_tokens": 429,
            "output_tokens": 256,
            "output_tokens_details": {"reasoning_tokens": 256},
            "total_tokens": 685,
        },
    }
    config = configuration(
        prices={
            "version": "synthetic-luna",
            "input_nanousd": 100,
            "cached_nanousd": 10,
            "cache_write_nanousd": 125,
            "output_nanousd": 500,
        }
    )
    try:
        async with sdk(response) as (client, requests):
            provider = GatewayProvider(
                store, client, gateway=config, recorder=recording
            )
            with (
                attribution(7, "incomplete-fixture"),
                pytest.raises(ValueError, match="one constrained choice"),
            ):
                await provider.decide(Observation.model_validate(observation()))
    finally:
        recording.close()
    assert len(requests) == 1
    assert store.budget()["spent"] == 170900
    assert store.budget()["reserved"] == 0
    events = list(ReplayReader(recording.config.path).all_events("qa:7"))
    finished = next(
        event["data"] for event in events if event["data"]["phase"] == "finished"
    )
    assert finished["gateway"]["response_status"] == "incomplete"
    assert finished["gateway"]["incomplete_reason"] == "max_output_tokens"
    assert finished["gateway"]["function_call_count"] == 0
    assert finished["gateway"]["single_choose_action"] is False
    assert finished["usage"]["output_tokens_details"]["reasoning_tokens"] == 256


async def test_valid_choice_records_structural_diagnostics_without_inventing_reason(
    tmp_path,
):
    recording = recorder(tmp_path)
    try:
        async with sdk() as (client, _):
            provider = GatewayProvider(
                Store(tmp_path / "synthetic.db"),
                client,
                gateway=configuration(),
                recorder=recording,
            )
            with attribution(7, "valid-fixture"):
                assert (
                    await provider.decide(Observation.model_validate(observation()))
                    == "resupply"
                )
    finally:
        recording.close()
    events = list(ReplayReader(recording.config.path).all_events("qa:7"))
    finished = next(
        event["data"] for event in events if event["data"]["phase"] == "finished"
    )
    assert finished["gateway"]["response_status"] == "completed"
    assert "incomplete_reason" not in finished["gateway"]
    assert finished["gateway"]["function_call_count"] == 1
    assert finished["gateway"]["single_choose_action"] is True


async def test_untrusted_response_metadata_and_output_are_never_diagnostics(tmp_path):
    marker = "SYNTHETIC_SECRET_DO_NOT_RECORD"
    response = {
        "status": marker,
        "incomplete_details": {"reason": marker, "secret": marker},
        "metadata": {"secret": marker},
        "output": [
            {"type": "function_call", "name": "choose_action", "arguments": marker},
            {"type": "function_call", "name": marker, "arguments": marker},
            {
                "type": "message",
                "role": "assistant",
                "content": [{"type": "output_text", "text": marker}],
            },
        ],
    }
    recording = recorder(tmp_path)
    store = Store(tmp_path / "synthetic.db")
    try:
        async with sdk(response) as (client, requests):
            provider = GatewayProvider(
                store, client, gateway=configuration(), recorder=recording
            )
            with (
                attribution(7, "malicious-fixture"),
                pytest.raises(ValueError, match="one constrained choice"),
            ):
                await provider.decide(Observation.model_validate(observation()))
    finally:
        recording.close()
    events = list(ReplayReader(recording.config.path).all_events("qa:7"))
    finished = next(
        event["data"] for event in events if event["data"]["phase"] == "finished"
    )
    assert "response_status" not in finished["gateway"]
    assert "incomplete_reason" not in finished["gateway"]
    assert finished["gateway"]["function_call_count"] == 2
    assert finished["gateway"]["single_choose_action"] is False
    assert marker not in json.dumps(events)
    assert store.budget()["spent"] == 14
    assert len(requests) == 1


@pytest.mark.parametrize("usage", [None, {}])
async def test_diagnostics_do_not_settle_missing_usage_or_accept_the_choice(
    tmp_path, usage
):
    path = tmp_path / "synthetic.db"
    recording = recorder(tmp_path)
    try:
        async with sdk({"usage": usage}) as (client, requests):
            provider = GatewayProvider(
                Store(path),
                client,
                gateway=configuration(decision_reasoning_effort="none"),
                recorder=recording,
            )
            with (
                attribution(7, "missing-usage-fixture"),
                pytest.raises(TypeError, match="usage"),
            ):
                await provider.decide(Observation.model_validate(observation()))
    finally:
        recording.close()
    events = list(ReplayReader(recording.config.path).all_events("qa:7"))
    assert not any(event["data"]["phase"] == "finished" for event in events)
    assert any(event["data"]["phase"] == "failed" for event in events)
    assert Store(path).budget()["reserved"] > 0
    assert Store(path).budget()["spent"] == 0
    assert len(requests) == 1
