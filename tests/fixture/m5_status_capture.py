"""Offline arbiter for real native status replies; not a qualification input yet.

The caller supplies a command transport and a durable event sink. A trace line
only asks for a status command; it can never manufacture a status observation.
This module does not connect to SQL, start a fixture, or infer a hunt instance.
"""

import asyncio
import contextlib
import dataclasses
import re
import time
from collections import deque


TRACE = re.compile(
    r"\[HUNT:PHASE\] mono_ms=(\d+) bot_guid=(\d+) script_id=(\d+) "
    r"from=(PREPARING|TRAVEL_TO|PATROLLING|LEAVING|RESUPPLYING) "
    r"to=(PREPARING|TRAVEL_TO|PATROLLING|LEAVING|RESUPPLYING)(?:\s|$)"
)
HUNT = re.compile(r"hunt=\[script=(\d+).*?\bphase=([A-Z_]+)\b")
STATUS_SUFFIX = re.compile(
    r" state=[A-Z_]+ pos=\(\d+,\d+,\d+\) active=(?:yes|no)(?: [^\r\n]*)?\s*"
)


@dataclasses.dataclass(frozen=True)
class ExternalEpoch:
    run_id: str
    world_sha256: str
    game_container_id: str
    game_started_at: str
    bot_guid: int
    bot_name: str
    script_id: int

    def __post_init__(self):
        if not all((self.run_id, self.world_sha256, self.game_container_id,
                    self.game_started_at, self.bot_name)):
            raise ValueError("external epoch has a missing binding")
        if self.bot_guid <= 0 or self.script_id <= 0:
            raise ValueError("invalid bot/script binding")


@dataclasses.dataclass(frozen=True)
class Request:
    sequence: int
    source: str
    enqueued_mono: float
    epoch: ExternalEpoch
    hint_mono_ms: int | None = None
    hint_phase: str | None = None


class CaptureHalted(RuntimeError):
    """No further commands may be dispatched in this observer attempt."""


class StatusCapture:
    """One-command arbiter shared by periodic observations and phase hints.

    submit(bot_name) returns the DB command ID. fetch(command_id) awaits the
    processed reply. Neither callback is cancelled on timeout/shutdown: SQL may
    still execute. After a timeout the arbiter stays fenced even after a late
    result, so the response cannot be assigned to a later hint or epoch.
    """

    def __init__(self, epoch, submit, fetch, emit, *, queue_limit=4,
                 command_timeout=3.0, max_queue_age=2.0, clock=time.monotonic):
        if queue_limit < 1 or command_timeout <= 0 or max_queue_age <= 0:
            raise ValueError("invalid capture bounds")
        self.epoch = epoch
        self.submit = submit
        self.fetch = fetch
        self.emit = emit
        self.queue_limit = queue_limit
        self.command_timeout = command_timeout
        self.max_queue_age = max_queue_age
        self.clock = clock
        self.queue = deque()
        self.sequence = 0
        self.active = None
        self.command_id = None
        self.fenced = False
        self.closed = False
        self._lock = asyncio.Lock()
        self._task = None

    def _record(self, event, request=None, **data):
        row = {
            "event": event,
            "at_mono": self.clock(),
            "sequence": request.sequence if request else None,
            "source": request.source if request else None,
            "external_epoch": dataclasses.asdict(request.epoch if request else self.epoch),
            "internal_epoch": "not_demonstrated",
            "hunt_instance_id": None,
            **data,
        }
        try:
            self.emit(row)
        except Exception:
            self.fenced = True
            raise

    def _offer(self, source, *, hint_mono_ms=None, hint_phase=None):
        if self.fenced or self.closed:
            raise CaptureHalted("capture is fenced or closed")
        if len(self.queue) >= self.queue_limit:
            self.fenced = True
            self._record("queue_overflow", queued=len(self.queue))
            raise CaptureHalted("status queue overflow")
        self.sequence += 1
        request = Request(self.sequence, source, self.clock(), self.epoch,
                          hint_mono_ms, hint_phase)
        self.queue.append(request)
        self._record("queued", request, queued=len(self.queue),
                     hint_mono_ms=hint_mono_ms, hint_phase=hint_phase)
        return request.sequence

    def periodic(self):
        return self._offer("periodic")

    def hint(self, line):
        match = TRACE.search(line)
        if not match:
            return None
        if int(match.group(2)) != self.epoch.bot_guid or int(match.group(3)) != self.epoch.script_id:
            return None
        return self._offer("phase_hint", hint_mono_ms=int(match.group(1)),
                           hint_phase=match.group(5))

    def change_epoch(self, epoch):
        if epoch == self.epoch:
            return
        self.fenced = True
        self._record("epoch_changed", pending_command_id=self.command_id,
                     queued=len(self.queue), next_external_epoch=dataclasses.asdict(epoch))

    def shutdown(self):
        self.closed = True
        self.fenced = True
        self._record("shutdown", pending_command_id=self.command_id,
                     pending_sequence=self.active.sequence if self.active else None,
                     queued=len(self.queue))

    def _late_completion(self, task):
        # The task belongs only to self.active; never release the fence here.
        if not (self.fenced or self.closed):
            return
        try:
            command_id, status = task.result()
            self._record("late_reply", self.active, command_id=command_id,
                         status=status, accepted=False)
        except BaseException as error:
            self._record("late_error", self.active, command_id=self.command_id,
                         error_type=type(error).__name__, accepted=False)

    async def _execute(self, request):
        command_id = int(await self.submit(request.epoch.bot_name))
        if command_id <= 0:
            raise ValueError("native status command has no valid identity")
        self.command_id = command_id
        self._record("submitted", request, command_id=command_id)
        return command_id, await self.fetch(command_id)

    @contextlib.asynccontextmanager
    async def _arbiter(self):
        try:
            await self._lock.acquire()
        except asyncio.CancelledError:
            # This caller never owned the lock. The active SQL may still finish;
            # keep its identity and fence the whole attempt before it can dispatch again.
            self.fenced = True
            self._record("cancelled_waiting_arbiter",
                         pending_command_id=self.command_id,
                         pending_sequence=self.active.sequence if self.active else None,
                         queued_sequences=[request.sequence for request in self.queue])
            raise
        try:
            yield
        finally:
            self._lock.release()

    async def capture_next(self):
        """Consume one queued request; concurrent callers still dispatch serially."""
        async with self._arbiter():
            if self.fenced or self.closed:
                raise CaptureHalted("capture is fenced or closed")
            if not self.queue:
                return None
            request = self.queue.popleft()
            age = self.clock() - request.enqueued_mono
            if age > self.max_queue_age:
                self.fenced = True
                self._record("queue_expired", request, queue_age=age)
                raise CaptureHalted("status request aged out")
            self.active = request
            self.command_id = None
            task = asyncio.create_task(self._execute(request))
            self._task = task
            try:
                command_id, status = await asyncio.wait_for(
                    asyncio.shield(task), timeout=self.command_timeout
                )
            except asyncio.TimeoutError as error:
                self.fenced = True
                self._record("timeout_pending", request,
                             command_id=self.command_id, queue_age=age,
                             pending_identity_known=self.command_id is not None)
                task.add_done_callback(self._late_completion)
                raise CaptureHalted("status command timed out; execution may continue") from error
            except asyncio.CancelledError:
                self.fenced = True
                self._record("cancelled_pending", request, command_id=self.command_id)
                task.add_done_callback(self._late_completion)
                raise
            except Exception as error:
                self.fenced = True
                self._record("command_error", request, command_id=self.command_id,
                             error_type=type(error).__name__)
                raise CaptureHalted("status command failed") from error
            finally:
                self._task = None
            if self.fenced or self.closed:
                self._record("late_reply", request, command_id=command_id,
                             status=status, accepted=False)
                raise CaptureHalted("status reply arrived after capture closed")
            prefix = f"Bot '{request.epoch.bot_name}':"
            if (not isinstance(status, str) or not status.startswith(prefix)
                    or "\n" in status or "\r" in status
                    or not STATUS_SUFFIX.fullmatch(status[len(prefix):])):
                self.fenced = True
                self._record("invalid_status", request, command_id=command_id)
                raise CaptureHalted("native status reply has wrong identity or shape")
            match = HUNT.search(status)
            observed_script = int(match.group(1)) if match else None
            observed_phase = match.group(2) if match else None
            row = {
                "event": "status_observed",
                "sequence": request.sequence,
                "source": request.source,
                "command_id": command_id,
                "status": status,
                "elapsed_mono": self.clock() - request.enqueued_mono,
                "external_epoch": dataclasses.asdict(request.epoch),
                "internal_epoch": "not_demonstrated",
                "hunt_instance_id": None,
                "observed_script_id": observed_script,
                "observed_phase": observed_phase,
                "target_script_matches": observed_script == request.epoch.script_id,
                "hint_mono_ms": request.hint_mono_ms,
                "hint_phase": request.hint_phase,
                "hint_phase_matches": bool(request.hint_phase and
                                           observed_script == request.epoch.script_id and
                                           observed_phase == request.hint_phase),
            }
            try:
                self.emit(row)
            except Exception:
                self.fenced = True
                raise
            self.active = None
            self.command_id = None
            return row
