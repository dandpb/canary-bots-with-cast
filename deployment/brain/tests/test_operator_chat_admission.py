"""Actual Supervisor.chat calls must share the controller model admission fence."""

import asyncio

import pytest
from test_protocol import observation
from test_supervised_admission import admission, finish, frame, hello, make

from canary_brain.provider import Proposal


class Spy:
    def __init__(self):
        self.calls = 0
        self.started = asyncio.Event()
        self.release = asyncio.Event()
        self.block = False
        self.ignore_cancel = False

    async def converse(self, *args):
        self.calls += 1
        self.started.set()
        if self.block and self.calls == 1:
            try:
                await self.release.wait()
            except asyncio.CancelledError:
                if not self.ignore_cancel:
                    raise
                await self.release.wait()
        return Proposal(reply="offline spy", candidate_id="continue", effort="low")


async def setup_chat(c):
    initial = observation() | {"mode": "active", "autonomous": True, "party": None}
    initial["bot"]["objective_running"] = True
    await hello(c)
    await c.handle(frame(c))
    await c.handle(admission(c, observation=initial))
    return initial


@pytest.mark.parametrize("boundary", ["cutoff", "close"])
async def test_chat_after_cutoff_or_close_never_calls_model(tmp_path, boundary):
    c, r, _ = make(tmp_path, mode="active", memory_mode="frozen")
    spy = Spy()
    try:
        initial = await setup_chat(c)
        c.model = spy
        if boundary == "cutoff":
            await c.handle(initial | {"sequence": 11, "captured_ms": 1801000})
        else:
            await c.close()
        with pytest.raises(ValueError):
            await c.supervisor.chat(7, "Offline test", False)
        # Also guard direct _chat callers, so the raw model path cannot bypass it.
        with pytest.raises(ValueError):
            await c.supervisor._chat(7, "Offline test", False)
        assert spy.calls == 0
    finally:
        await finish(c, r)


async def test_close_before_b_cannot_reopen_chat_admission(tmp_path):
    c, r, _ = make(tmp_path, mode="active", memory_mode="frozen")
    spy = Spy()
    try:
        await hello(c)
        await c.handle(admission(c))
        await c.close()
        await c.handle(frame(c))
        c.model = spy
        with pytest.raises(ValueError):
            await c.supervisor.chat(7, "Offline test", False)
        assert spy.calls == 0
    finally:
        await finish(c, r)


@pytest.mark.parametrize("ignore_cancel", [False, True])
async def test_running_chat_is_bounded_tracked_and_cannot_reopen(
    tmp_path, ignore_cancel
):
    c, r, _ = make(tmp_path, mode="active", memory_mode="frozen")
    spy = Spy()
    task = None
    try:
        await setup_chat(c)
        c.model = spy
        spy.block = True
        spy.ignore_cancel = ignore_cancel
        task = asyncio.create_task(c.supervisor.chat(7, "Offline test", False))
        await asyncio.wait_for(spy.started.wait(), timeout=2)
        # A second direct chat cannot create another provider request for this bot.
        with pytest.raises(ValueError):
            await c.supervisor.chat(7, "Another test", False)
        await asyncio.wait_for(c.close(), timeout=1.5)
        if ignore_cancel:
            assert c.native_run.failure == "model_shutdown_timeout"
        with pytest.raises(ValueError):
            await c.supervisor.chat(7, "After close", False)
        assert spy.calls == 1
        spy.release.set()
        result = await asyncio.gather(task, return_exceptions=True)
        assert isinstance(result[0], (ValueError, asyncio.CancelledError))
        assert not c.operator_tasks
    finally:
        spy.release.set()
        if task is not None:
            await asyncio.gather(task, return_exceptions=True)
        await finish(c, r)
