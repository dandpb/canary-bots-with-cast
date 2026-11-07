"""Tracing faults must not change native delivery or durable billing."""

import sqlite3
import threading
import time
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from test_protocol import observation
from test_provider import APIResult

from canary_brain import tracing
from canary_brain.controller import Controller
from canary_brain.provider import Provider
from canary_brain.store import Store


@pytest.mark.parametrize(
    "fault", ["start_span", "start_as_current_span", "output", "exit"]
)
async def test_trace_fault_preserves_send_and_actual_settlement(
    tmp_path, monkeypatch, fault
):
    span = Mock()
    manager = Mock()
    manager.__enter__ = Mock(return_value=span)
    manager.__exit__ = Mock(return_value=False)
    tracer = Mock()
    tracer.start_as_current_span.return_value = manager
    if fault == "output":
        span.set_attribute.side_effect = RuntimeError("trace output failed")
    elif fault == "exit":
        manager.__exit__.side_effect = RuntimeError("trace exit failed")
    else:
        getattr(tracer, fault).side_effect = RuntimeError("trace start failed")
    monkeypatch.setattr(tracing, "_tracer", tracer)
    monkeypatch.setattr(tracing, "_bots", frozenset({7}))
    monkeypatch.setattr(tracing, "_actions", {})
    calls = []

    async def create(**body):
        calls.append(body)
        return APIResult()

    store = Store(tmp_path / "state.db")
    settle = Mock(wraps=store.settle)
    monkeypatch.setattr(store, "settle", settle)
    provider = Provider(
        store, SimpleNamespace(decisions=SimpleNamespace(create=create))
    )
    sent = []
    controller = Controller(store, provider, sent.append, mode="active")
    packet = observation()
    packet["mode"] = "active"
    await controller.handle(packet)
    await controller.drain()
    assert len([p for p in sent if p["type"] == "intent"]) == 1
    assert len(calls) == 1
    assert settle.call_count == 1
    assert settle.call_args.args[1] == 10000
    assert store.budget()["spent"] == 10000
    assert store.budget()["reserved"] == 0
    assert provider.backoff == {}
    await controller.close()


@pytest.mark.parametrize(
    "error", [RuntimeError("provider"), sqlite3.OperationalError("disk")]
)
def test_application_error_survives_tracing_teardown(monkeypatch, error):
    manager = Mock()
    manager.__enter__ = Mock(return_value=Mock())
    manager.__exit__ = Mock(side_effect=RuntimeError("tracing teardown"))
    monkeypatch.setattr(
        tracing,
        "_tracer",
        SimpleNamespace(start_as_current_span=lambda *a, **kw: manager),
    )
    monkeypatch.setattr(tracing, "_bots", frozenset({7}))
    with pytest.raises(type(error)) as caught, tracing.decision(7, "test"):
        raise error
    assert caught.value is error


def test_shutdown_is_bounded_and_daemonized(monkeypatch):
    entered = threading.Event()
    release = threading.Event()
    finished = threading.Event()

    daemon = []

    def stuck():
        daemon.append(threading.current_thread().daemon)
        entered.set()
        release.wait()
        finished.set()

    monkeypatch.setattr(tracing, "_provider", SimpleNamespace(shutdown=stuck))
    monkeypatch.setattr(tracing, "_actions", {})
    try:
        started = time.monotonic()
        tracing.shutdown_bounded(0.02)
        assert time.monotonic() - started < 0.5
        assert daemon == [True]
        assert entered.is_set()
        assert not finished.is_set()
    finally:
        release.set()
        assert finished.wait(1)


def test_no_opt_in_never_touches_tracer(monkeypatch):
    tracer = Mock()
    monkeypatch.setattr(tracing, "_tracer", tracer)
    monkeypatch.setattr(tracing, "_bots", frozenset())
    with tracing.decision(7, "test") as capture:
        capture.output({"usage": {"input_tokens": 1}})
    tracing.begin_action({"bot_id": 7})
    assert not tracer.mock_calls


@pytest.mark.parametrize("stage", ["provider", "settle"])
async def test_provider_and_sqlite_failures_are_not_swallowed(
    tmp_path, monkeypatch, stage
):
    store = Store(tmp_path / "state.db")
    error = (
        RuntimeError("provider")
        if stage == "provider"
        else sqlite3.OperationalError("disk")
    )
    calls = []

    async def create(**body):
        calls.append(body)
        if stage == "provider":
            raise error
        return APIResult()

    if stage == "settle":
        monkeypatch.setattr(store, "settle", Mock(side_effect=error))
    provider = Provider(
        store, SimpleNamespace(decisions=SimpleNamespace(create=create))
    )
    with pytest.raises(type(error)) as caught:
        await provider._request("decisions", {}, 1)
    assert caught.value is error
    assert len(calls) == 1
    assert store.budget()["spent"] == 0
    assert store.budget()["reserved"] > 0
