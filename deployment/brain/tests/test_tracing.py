import json
from types import SimpleNamespace

import pytest

pytest.importorskip("opentelemetry.sdk.trace")

from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from test_protocol import observation
from test_provider import APIResult

from canary_brain import tracing
from canary_brain.controller import Controller
from canary_brain.protocol import Outcome
from canary_brain.provider import Provider
from canary_brain.store import Store


@pytest.fixture
def exported(monkeypatch):
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    monkeypatch.setattr(tracing, "_tracer", provider.get_tracer("test"))
    monkeypatch.setattr(tracing, "_bots", frozenset({7}))
    yield exporter
    tracing.shutdown()
    provider.shutdown()


async def test_real_controller_call_and_native_receipt_share_trace_without_changing_budget(
    tmp_path, exported
):
    calls = []

    async def create(**body):
        calls.append(body)
        return APIResult()

    store = Store(tmp_path / "state.db")
    provider = Provider(
        store, SimpleNamespace(decisions=SimpleNamespace(create=create))
    )
    sent = []
    controller = Controller(store, provider, sent.append, mode="active")
    packet = observation()
    packet["mode"] = "active"
    await controller.handle(packet)
    await controller.drain()
    intent = next(item for item in sent if item["type"] == "intent")
    assert not any(
        s.attributes.get("openinference.span.kind") == "TOOL"
        for s in exported.get_finished_spans()
    )
    controller._outcome(
        Outcome(
            world="wrong-world",
            action_id=intent["action_id"],
            bot_id=7,
            status="accepted",
        )
    )
    assert not any(
        s.attributes.get("openinference.span.kind") == "TOOL"
        for s in exported.get_finished_spans()
    )
    controller._outcome(
        Outcome(
            world=intent["world"],
            action_id=intent["action_id"],
            bot_id=7,
            status="accepted",
        )
    )
    spans = exported.get_finished_spans()
    model = next(s for s in spans if s.name == "OpenAI decisions")
    tool = next(
        s for s in spans if s.attributes.get("openinference.span.kind") == "TOOL"
    )
    root = next(
        s for s in spans if s.attributes.get("openinference.span.kind") == "AGENT"
    )
    assert model.context.trace_id == tool.context.trace_id == root.context.trace_id
    assert model.parent.span_id == tool.parent.span_id == root.context.span_id
    assert json.loads(model.attributes["input.value"]) == calls[0]
    assert (
        json.loads(model.attributes["output.value"])["answers"][0]["choice"]
        == "resupply"
    )
    assert json.loads(tool.attributes["output.value"])["status"] == "accepted"
    assert "lease-a" not in tool.attributes["input.value"]
    assert store.budget()["spent"] == 10000
    assert len(calls) == 1


def test_bot_filter_and_exception_redaction(exported):
    with tracing.decision(8, "other"):
        pass
    assert not exported.get_finished_spans()
    with (
        pytest.raises(RuntimeError),
        tracing.capture(
            "failure",
            "LLM",
            {"authorization": "secret", "text": "sk-private lens-trace-private"},
            7,
        ),
    ):
        raise RuntimeError("credentials must not appear")
    span = exported.get_finished_spans()[0]
    assert span.status.status_code.name == "ERROR"
    assert span.attributes["error.type"] == "RuntimeError"
    assert "secret" not in span.attributes["input.value"]
    assert "private" not in span.attributes["input.value"]
    assert not span.events


async def test_gateway_calls_preserve_trace_and_spend_correlation(tmp_path, exported):
    from test_gateway import client, gateway

    from canary_brain.gateway import GatewayProvider
    from canary_brain.protocol import Observation
    from canary_brain.recording import attribution

    api, calls = client()
    store = Store(tmp_path / "budget.db")
    provider = GatewayProvider(store, api, gateway=gateway())
    with attribution(7), tracing.decision(7, "gateway"):
        assert (
            await provider.decide(Observation.model_validate(observation()))
            == "resupply"
        )
    model = next(
        s for s in exported.get_finished_spans() if s.name == "OpenAI responses"
    )
    root = next(s for s in exported.get_finished_spans() if s.name == "Canary gateway")
    assert model.context.trace_id == root.context.trace_id
    assert model.parent.span_id == root.context.span_id
    assert model.attributes["litellm.call_id"] == "gateway-request"
    assert model.attributes["canary.gateway.deployment_id"] == "deployment-a"
    recorded = json.loads(model.attributes["input.value"])
    assert recorded == {k: v for k, v in calls[0].items() if k != "extra_headers"}
    assert json.loads(model.attributes["output.value"])["model"] == "model-a"
    assert store.budget()["spent"] == 14
