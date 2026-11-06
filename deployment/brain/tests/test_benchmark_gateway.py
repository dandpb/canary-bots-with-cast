"""Private gateway lifecycle checks with fake Docker only."""

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from tools import benchmark_gateway as gateway

IMAGE = "sha256:" + "1" * 64
REVISION = "2" * 40
IDENTITY = "a" * 64
SENTINEL = "private-offline-env-value"


@pytest.fixture(autouse=True)
def restore_sigterm_handler():
    previous = signal.getsignal(signal.SIGTERM)
    try:
        yield
    finally:
        signal.signal(signal.SIGTERM, previous)


@pytest.fixture
def configured(tmp_path):
    runtime = tmp_path / "runtime"
    secrets = runtime / "secrets"
    secrets.mkdir(parents=True)
    for kind in ("provider", "worker", "ui"):
        path = secrets / ("litellm-" + kind + ".env")
        path.write_text("OFFLINE_VALUE=" + SENTINEL + "\n")
        path.chmod(0o600)
    policy = tmp_path / "policy.json"
    policy.write_text('{"model_list": []}\n')
    return runtime, policy


def main_arguments(configured, mode):
    runtime, policy = configured
    return [
        str(Path(gateway.__file__)),
        "--runtime",
        str(runtime),
        "--policy",
        str(policy),
        "--image",
        IMAGE,
        "--revision",
        REVISION,
        mode,
    ]


class FakeDocker:
    def __init__(
        self,
        *,
        existing=False,
        alias_before=False,
        alias_after=False,
        alias_after_start=False,
        foreign_at_create=None,
    ):
        self.existing = existing
        self.alias_before, self.alias_after = alias_before, alias_after
        self.alias_after_start = alias_after_start
        self.created = False
        self.calls = []
        self.create_error = None
        self.wait_error = KeyboardInterrupt()
        self.bad_metadata = None
        self.foreign_at_create = foreign_at_create
        self.foreign_status = None
        self.started = False
        self.health = {"Status": "running", "Health": {"Status": "healthy"}}

    def __call__(self, args, env):
        self.calls.append(list(args))
        if args[0] == "compose":
            if "config" in args:
                return ""
            assert "create" in args and "--no-recreate" in args
            assert "--no-build" in args and args[args.index("--pull") + 1] == "never"
            assert args[-1] == gateway.SERVICE
            if self.foreign_at_create:
                self.existing = True
                self.foreign_status = self.foreign_at_create
                return ""
            self.created = True
            if self.create_error is not None:
                raise self.create_error
            return ""
        if args[:2] == ["ps", "-aq"]:
            if any("io.canary.benchmark.session=" in item for item in args):
                return IDENTITY if self.created else ""
            return "b" * 64 if self.existing else ""
        if args[:2] == ["network", "inspect"]:
            aliases = (
                self.alias_before
                or (self.created and self.alias_after)
                or (self.started and self.alias_after_start)
            )
            return json.dumps(
                {
                    **({IDENTITY: {}} if self.created else {}),
                    **({"foreign": {}} if aliases else {}),
                }
            )
        if args[0] == "inspect" and "NetworkSettings" in args[2]:
            return json.dumps({gateway.NETWORK: {"Aliases": ["gateway"]}})
        if args[0] == "inspect" and args[2] == "{{json .State}}":
            assert self.started
            return json.dumps(self.health)
        if args[0] == "inspect":
            labels = {
                "com.docker.compose.project": gateway.PROJECT,
                "com.docker.compose.service": gateway.SERVICE,
                "io.canary.benchmark.role": "private-gateway",
                "io.canary.benchmark.session": env["CANARY_BENCHMARK_SESSION"],
            }
            data = {"image": env["CANARY_BENCHMARK_IMAGE"], "labels": labels}
            if self.bad_metadata == "image":
                data["image"] = "sha256:" + "3" * 64
            elif self.bad_metadata:
                labels[self.bad_metadata] = "foreign-owner"
            return json.dumps(data)
        if args[0] == "start":
            assert args == ["start", IDENTITY]
            self.started = True
            return ""
        if args[0] == "wait":
            assert args == ["wait", IDENTITY]
            if self.wait_error is not None:
                raise self.wait_error
            return "1"
        if args[0] == "logs":
            assert args == ["logs", IDENTITY]
            return SENTINEL
        if args[0] == "rm":
            assert args == ["rm", "--force", IDENTITY]
            self.created = False
            return ""
        raise AssertionError("Unexpected fake Docker operation: " + str(args))

    @property
    def removals(self):
        return [args for args in self.calls if args[0] == "rm"]


def test_check_reads_no_env_values_and_does_not_create_runtime_files(
    configured, monkeypatch, capsys
):
    runtime, _ = configured
    before = {
        p: (p.read_bytes(), p.stat().st_mode) for p in runtime.rglob("*") if p.is_file()
    }
    original_open = Path.open

    def no_secret_reads(path, *args, **kwargs):
        assert path.parent.name != "secrets", "launcher must not open env values"
        return original_open(path, *args, **kwargs)

    fake = FakeDocker()
    with monkeypatch.context() as scoped:
        scoped.setattr(Path, "open", no_secret_reads)
        scoped.setattr(gateway, "invoke", fake)
        scoped.setattr(sys, "argv", main_arguments(configured, "--check"))
        gateway.main()
    assert before == {
        p: (p.read_bytes(), p.stat().st_mode) for p in runtime.rglob("*") if p.is_file()
    }
    assert fake.calls == [gateway.compose("config", "--quiet")]
    assert SENTINEL not in capsys.readouterr().out
    assert not (runtime / ".benchmark-gateway.lock").exists()


def test_check_does_not_echo_secret_bearing_compose_errors(
    configured, monkeypatch, capsys
):
    def fail(args, environment):
        raise subprocess.CalledProcessError(
            1, ["docker"], output=SENTINEL, stderr=SENTINEL
        )

    monkeypatch.setattr(gateway, "invoke", fail)
    monkeypatch.setattr(sys, "argv", main_arguments(configured, "--check"))
    with pytest.raises(SystemExit) as stopped:
        gateway.main()
    assert stopped.value.code == 1
    captured = capsys.readouterr()
    assert SENTINEL not in captured.out + captured.err
    assert "CalledProcessError" in captured.err


@pytest.mark.parametrize("invalid", ["permissions", "symlink"])
def test_invalid_env_destination_is_rejected_before_compose(
    configured, monkeypatch, invalid
):
    private = configured[0] / "secrets/litellm-worker.env"
    if invalid == "permissions":
        private.chmod(0o640)
    else:
        destination = private.with_suffix(".original")
        private.rename(destination)
        private.symlink_to(destination)
    fake = FakeDocker()
    monkeypatch.setattr(gateway, "invoke", fake)
    with pytest.raises(ValueError):
        gateway.environment(*configured, IMAGE, REVISION)
    assert fake.calls == []


@pytest.mark.parametrize("conflict", ["service", "alias"])
def test_preexisting_service_or_external_alias_is_preserved(
    configured, monkeypatch, conflict
):
    fake = FakeDocker(existing=conflict == "service", alias_before=conflict == "alias")
    monkeypatch.setattr(gateway, "invoke", fake)
    env = gateway.environment(*configured, IMAGE, REVISION)
    with pytest.raises(ValueError, match="already"):
        gateway.serve(env)
    assert not fake.created and not fake.removals
    assert not any(args[0] == "compose" for args in fake.calls)


def test_startup_failure_after_creation_removes_only_owned_container(
    configured, monkeypatch, capsys
):
    fake = FakeDocker()
    fake.create_error = subprocess.CalledProcessError(1, ["docker"], stderr=SENTINEL)
    monkeypatch.setattr(gateway, "invoke", fake)
    env = gateway.environment(*configured, IMAGE, REVISION)
    with pytest.raises(subprocess.CalledProcessError):
        gateway.serve(env)
    assert fake.removals == [["rm", "--force", IDENTITY]]
    assert not fake.created
    assert not fake.started
    logs = list(configured[0].glob("benchmark-gateway-*.log"))
    assert len(logs) == 1 and logs[0].stat().st_mode & 0o777 == 0o600
    assert logs[0].read_text() == SENTINEL
    assert SENTINEL not in capsys.readouterr().out


@pytest.mark.parametrize(
    "error", [KeyboardInterrupt(), RuntimeError("fake wait failure")]
)
def test_wait_interruption_cleans_owned_container_and_keeps_lease_file(
    configured, monkeypatch, error
):
    fake = FakeDocker()
    fake.wait_error = error
    monkeypatch.setattr(gateway, "invoke", fake)
    env = gateway.environment(*configured, IMAGE, REVISION)
    with pytest.raises(type(error)):
        gateway.serve(env)
    assert fake.removals == [["rm", "--force", IDENTITY]]
    assert not fake.created
    assert (configured[0] / ".benchmark-gateway.lock").is_file()
    # The kernel lease was released, but its inode remains available for reuse.
    with gateway.lease(configured[0]):
        pass


@pytest.mark.parametrize(
    "mismatch",
    [
        "image",
        "com.docker.compose.project",
        "com.docker.compose.service",
        "io.canary.benchmark.role",
        "io.canary.benchmark.session",
    ],
)
def test_metadata_mismatch_never_deletes_foreign_container(
    configured, monkeypatch, mismatch
):
    fake = FakeDocker()
    fake.bad_metadata = mismatch
    monkeypatch.setattr(gateway, "invoke", fake)
    with pytest.raises(ValueError, match="owned by another"):
        gateway.serve(gateway.environment(*configured, IMAGE, REVISION))
    assert fake.created and not fake.removals
    assert not fake.started


def test_alias_race_cleans_only_this_launchers_container(configured, monkeypatch):
    fake = FakeDocker(alias_after=True)
    monkeypatch.setattr(gateway, "invoke", fake)
    with pytest.raises(ValueError, match="already occupied"):
        gateway.serve(gateway.environment(*configured, IMAGE, REVISION))
    assert fake.removals == [["rm", "--force", IDENTITY]]
    assert not fake.started


def test_alias_race_after_start_cleans_only_this_launchers_container(
    configured, monkeypatch
):
    fake = FakeDocker(alias_after_start=True)
    monkeypatch.setattr(gateway, "invoke", fake)
    with pytest.raises(ValueError, match="already occupied"):
        gateway.serve(gateway.environment(*configured, IMAGE, REVISION))
    assert fake.started and fake.removals == [["rm", "--force", IDENTITY]]
    assert not any(args[0] == "wait" for args in fake.calls)


@pytest.mark.parametrize("foreign_status", ["running", "exited"])
def test_service_created_by_another_operator_during_create_is_not_adopted(
    configured, monkeypatch, foreign_status
):
    fake = FakeDocker(foreign_at_create=foreign_status)
    monkeypatch.setattr(gateway, "invoke", fake)
    with pytest.raises(ValueError, match="refusing to adopt another service"):
        gateway.serve(gateway.environment(*configured, IMAGE, REVISION))
    assert fake.existing and fake.foreign_status == foreign_status
    assert not fake.created and not fake.started and not fake.removals
    assert not any(args[0] in {"start", "wait", "logs", "rm"} for args in fake.calls)
    create = next(args for args in fake.calls if args[0] == "compose")
    assert "--no-recreate" in create and "up" not in create


@pytest.mark.parametrize(
    "state",
    [
        {"Status": "exited"},
        {"Status": "running", "Health": {"Status": "unhealthy"}},
    ],
)
def test_owned_gateway_health_failure_is_cleaned(configured, monkeypatch, state):
    fake = FakeDocker()
    fake.health = state
    monkeypatch.setattr(gateway, "invoke", fake)
    with pytest.raises(ValueError, match="failed its healthcheck"):
        gateway.serve(gateway.environment(*configured, IMAGE, REVISION))
    assert fake.started and not fake.created
    assert fake.removals == [["rm", "--force", IDENTITY]]
    assert not any(args[0] == "wait" for args in fake.calls)


def test_health_readiness_deadline_cleans_without_entering_wait(
    configured, monkeypatch
):
    fake = FakeDocker()
    fake.health = {"Status": "running", "Health": {"Status": "starting"}}
    moments = iter([0, 121])
    monkeypatch.setattr(gateway, "invoke", fake)
    monkeypatch.setattr(
        gateway,
        "time",
        SimpleNamespace(monotonic=lambda: next(moments), sleep=lambda _: None),
    )
    with pytest.raises(ValueError, match="within 120 seconds"):
        gateway.serve(gateway.environment(*configured, IMAGE, REVISION))
    assert fake.started and not fake.created
    assert fake.removals == [["rm", "--force", IDENTITY]]
    assert not any(args[0] == "wait" for args in fake.calls)


def test_overlapping_launcher_cannot_reach_docker(configured, monkeypatch):
    fake = FakeDocker()
    monkeypatch.setattr(gateway, "invoke", fake)
    env = gateway.environment(*configured, IMAGE, REVISION)
    with gateway.lease(configured[0]), pytest.raises(BlockingIOError):
        gateway.serve(env)
    assert fake.calls == []


def test_sigterm_real_launcher_process_uses_fake_docker_and_cleans(
    configured, tmp_path
):
    """Only the launcher and a Python fake CLI execute; Docker is never invoked."""
    executable = tmp_path / "bin"
    executable.mkdir()
    state = tmp_path / "fake-state.json"
    trace = tmp_path / "fake-trace.jsonl"
    ready = tmp_path / "fake-wait-ready"
    docker = executable / "docker"
    docker.write_text(
        "#!"
        + sys.executable
        + "\n"
        + """import json, os, sys, time
from pathlib import Path
args=sys.argv[1:]
state=Path(os.environ['FAKE_STATE'])
with Path(os.environ['FAKE_TRACE']).open('a') as log:
    log.write(json.dumps(args)+'\\n')
created=state.exists() and json.loads(state.read_text()).get('created', False)
identity='a'*64
if args[0]=='compose':
    if 'create' in args:
        assert '--no-recreate' in args and '--no-build' in args
        assert args[args.index('--pull')+1]=='never'
        state.write_text(json.dumps({'created':True}))
elif args[0]=='ps':
    print(identity if created else '')
elif args[:2]==['network','inspect']:
    print(json.dumps({identity:{}} if created else {}))
elif args[0]=='inspect' and 'NetworkSettings' in args[2]:
    print(json.dumps({'canary-bots-wsl_default':{'Aliases':['gateway']}}))
elif args[0]=='inspect' and args[2]=='{{json .State}}':
    print(json.dumps({'Status':'running','Health':{'Status':'healthy'}}))
elif args[0]=='inspect':
    print(json.dumps({'image':os.environ['CANARY_BENCHMARK_IMAGE'],'labels':{
      'com.docker.compose.project':'canary-bots-wsl',
      'com.docker.compose.service':'benchmark-gateway',
      'io.canary.benchmark.role':'private-gateway',
      'io.canary.benchmark.session':os.environ['CANARY_BENCHMARK_SESSION']}}))
elif args[0]=='start':
    assert args==['start',identity] and created
elif args[0]=='wait':
    Path(os.environ['FAKE_READY']).touch()
    while True: time.sleep(.1)
elif args[0]=='logs': print('private-offline-env-value')
elif args[0]=='rm':
    assert args==['rm','--force',identity]
    state.write_text(json.dumps({'created':False}))
else: raise SystemExit(9)
"""
    )
    docker.chmod(0o700)
    environment = {
        **os.environ,
        "PATH": str(executable) + os.pathsep + os.environ.get("PATH", ""),
        "FAKE_STATE": str(state),
        "FAKE_TRACE": str(trace),
        "FAKE_READY": str(ready),
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    process = subprocess.Popen(
        [sys.executable, *main_arguments(configured, "--serve")],
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    try:
        deadline = time.monotonic() + 15
        while not ready.exists():
            assert process.poll() is None, "fake launcher exited before wait"
            assert time.monotonic() < deadline, "fake launcher never reached wait"
            time.sleep(0.02)
        process.send_signal(signal.SIGTERM)
        stdout, stderr = process.communicate(timeout=15)
        assert process.returncode == 130
        assert "owned containers cleaned" in stderr
        assert SENTINEL not in stdout + stderr
        assert json.loads(state.read_text()) == {"created": False}
        calls = [json.loads(line) for line in trace.read_text().splitlines()]
        assert [args for args in calls if args[0] == "rm"] == [
            ["rm", "--force", IDENTITY]
        ]
    finally:
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGKILL)
            process.communicate(timeout=5)
