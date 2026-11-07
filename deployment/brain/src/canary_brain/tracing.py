"""Opt-in, background OTLP export of real agent calls and native action receipts."""

from __future__ import annotations

import json
import os
import re
import threading
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from functools import wraps
from typing import Any, ParamSpec, TypeVar

from .recording import public_data, request_context

_tracer: Any = None
_provider: Any = None
_bots: frozenset[int] = frozenset()
_actions: dict[str, tuple[Any, float]] = {}


P = ParamSpec("P")
T = TypeVar("T")


def _optional(function: Callable[P, T]) -> Callable[P, T | None]:
    """Wrap only tracing operations, never application work or a context body."""

    @wraps(function)
    def guarded(*args: P.args, **kwargs: P.kwargs) -> T | None:
        try:
            return function(*args, **kwargs)
        except Exception:  # noqa: BLE001 - tracing alone is best effort
            return None

    return guarded


def payload(value: Any) -> str:
    encoded = json.dumps(public_data(value), ensure_ascii=False, default=str)
    return re.sub(r"lens-trace-[A-Za-z0-9_-]+", "[redacted]", encoded)[:262144]


@_optional
def configure() -> None:
    global _tracer, _provider, _bots
    selected = os.getenv("CANARY_TRACE_BOTS", "")
    if not selected:
        return
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import SpanLimits, TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    _bots = frozenset(int(bot) for bot in selected.split(","))
    _provider = TracerProvider(
        shutdown_on_exit=False,  # Cleanup is bounded by shutdown_bounded instead.
        resource=Resource.create({"service.name": "canary-brain"}),
        span_limits=SpanLimits(max_attribute_length=262144),
    )
    _provider.add_span_processor(
        BatchSpanProcessor(
            OTLPSpanExporter(timeout=2),
            max_queue_size=512,
            max_export_batch_size=32,
            schedule_delay_millis=1000,
        )
    )
    _tracer = _provider.get_tracer("canary_brain")


class Capture:
    def __init__(self, span: Any = None) -> None:
        self.span = span

    @_optional
    def output(self, value: Any) -> None:
        if self.span is not None:
            self.span.set_attribute("output.value", payload(value))
            if isinstance(value, dict) and isinstance(value.get("usage"), dict):
                for field, attribute in (
                    ("input_tokens", "llm.token_count.prompt"),
                    ("output_tokens", "llm.token_count.completion"),
                ):
                    count = value["usage"].get(field)
                    if type(count) is int and count >= 0:
                        self.span.set_attribute(attribute, count)


@contextmanager
def capture(name: str, kind: str, value: Any, bot: int) -> Iterator[Capture]:
    if _tracer is None or bot not in _bots:
        yield Capture()
        return
    manager: Any = None
    span: Any = None
    try:
        manager = _tracer.start_as_current_span(
            name,
            attributes={
                "openinference.span.kind": kind,
                "agent.name": "Tarshaw" if bot == 65045 else f"Canary {bot}",
                "canary.bot.id": bot,
                "input.value": payload(value),
            },
            record_exception=False,
            set_status_on_exception=False,
        )
        span = manager.__enter__()
    except Exception:  # noqa: BLE001 - only tracing context entry
        manager = None
    try:
        if span is not None and kind == "LLM" and isinstance(value, dict):
            _optional(span.set_attribute)("llm.model_name", str(value.get("model", "")))
        yield Capture(span)
    except BaseException as error:
        if span is not None:
            _mark_error(span, error)
        raise
    finally:
        if manager is not None:
            # Never let tracing suppress or replace an application exception.
            _optional(manager.__exit__)(None, None, None)


@_optional
def _mark_error(span: Any, error: BaseException) -> None:
    from opentelemetry.trace import Status, StatusCode

    span.set_status(Status(StatusCode.ERROR))
    span.set_attribute("error.type", type(error).__name__)


def decision(bot: int, kind: str) -> Any:
    return capture(f"Canary {kind}", "AGENT", {"bot": bot, "task": kind}, bot)


def model_call(endpoint: str, body: dict[str, Any]) -> Any:
    return capture(f"OpenAI {endpoint}", "LLM", body, request_context.get()[0])


@_optional
def begin_action(packet: dict[str, Any]) -> None:
    bot = packet.get("bot_id")
    if _tracer is None or bot not in _bots:
        return
    now = time.monotonic()
    for action, (span, started) in list(_actions.items()):
        if now - started > 300 or len(_actions) >= 256:
            span.set_attribute("canary.receipt", "not_observed")
            span.end()
            del _actions[action]
    span = _tracer.start_span(
        str(packet.get("candidate_id", "native action")),
        attributes={
            "openinference.span.kind": "TOOL",
            "tool.id": str(packet["action_id"]),
            "input.value": payload(packet),
            "canary.bot.id": bot,
        },
    )
    _actions[str(packet["action_id"])] = (span, now)


@_optional
def action_receipt(outcome: dict[str, Any]) -> None:
    pending = _actions.pop(str(outcome["action_id"]), None)
    if pending:
        span, _ = pending
        span.set_attribute("output.value", payload(outcome))
        span.set_attribute("canary.receipt", str(outcome["status"]))
        span.end()


@_optional
def shutdown() -> None:
    global _tracer, _provider, _bots
    for span, _ in _actions.values():
        span.set_attribute("canary.receipt", "worker_stopped")
        span.end()
    _actions.clear()
    if _provider is not None:
        _provider.shutdown()
    _tracer, _provider, _bots = None, None, frozenset()


def shutdown_bounded(timeout: float = 2.0) -> None:
    """Bound exporter cleanup without leaving an executor thread stuck at exit."""
    worker = threading.Thread(target=_optional(shutdown), daemon=True)
    worker.start()
    worker.join(timeout)
