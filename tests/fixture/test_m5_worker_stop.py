"""Free harness delegates to production; no game, sockets or provider are started."""

import importlib.util
import json
from pathlib import Path

import m5_qa as qa
import m5_worker as worker
import pytest
from canary_brain import runtime
from canary_brain.store import Store


@pytest.fixture
def attempt(tmp_path, monkeypatch):
    monkeypatch.setenv("CANARY_M5_PRIVATE_ROOT", str(tmp_path))
    work = tmp_path / "attempt"
    work.mkdir(mode=0o700)
    monkeypatch.setattr(qa, "WORK", tmp_path)
    manifest = {
        "fixture_sha256": "a" * 64,
        "source_revision": "a" * 40,
        "native_source_revision": "b" * 40,
        "image_id": "sha256:" + "c" * 64,
        "overrides": {},
        "harness_sha256": {},
    }

    def configure(mode="native"):
        config = qa.worker_configuration(work, mode, manifest)
        (work / "worker.json").write_text(json.dumps(config))
        return config

    configure()
    return work, configure


def integrated(monkeypatch):
    worker.require_native_admission()


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ["native", "fake"])
async def test_delegates_clock_completion_and_stop_details_to_production(
    attempt, monkeypatch, mode
):
    work, configure = attempt
    configure(mode)
    integrated(monkeypatch)
    called = []
    ending = {
        "reason": "completed",
        "observed_seconds": 1800,
        "native_seconds": 1800,
        "required_sequence": 1802,
    }

    async def production(config):
        called.append(config)
        assert config.benchmark_supervision is True
        assert config.run_seconds == 1800
        assert config.provider == mode
        assert config.budget_file is None
        state = runtime.Store(config.state_file)
        state.put("run_stop", "end", ending)

    monkeypatch.setattr(runtime, "run", production)
    # A stub verdict alone no longer exports a successful qualification.
    with pytest.raises(RuntimeError, match="durable admission/replay proof"):
        await worker.run_worker(work, mode)
    assert len(called) == 1
    assert json.loads((work / "stop.json").read_text()) == ending


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "reason", [None, "world_changed", "native_transport_unconfirmed"]
)
async def test_early_exit_or_production_failure_cannot_become_completed(
    attempt, monkeypatch, reason
):
    work, _ = attempt
    integrated(monkeypatch)

    async def production(config):
        state = runtime.Store(config.state_file)
        if reason:
            state.put("run_stop", "end", {"reason": reason})

    monkeypatch.setattr(runtime, "run", production)
    with pytest.raises(RuntimeError, match="did not complete"):
        await worker.run_worker(work, "native")
    assert json.loads((work / "stop.json").read_text())["reason"] == (
        reason or "runtime_ended"
    )


@pytest.mark.asyncio
async def test_missing_integration_fails_before_config_state_or_runtime(
    tmp_path, monkeypatch
):
    monkeypatch.delitem(runtime.Configuration.model_fields, "native_source_revision")

    async def forbidden_runtime(*_args, **_kwargs):
        pytest.fail("unqualified runtime entered")

    monkeypatch.setattr(runtime, "run", forbidden_runtime)
    with pytest.raises(RuntimeError, match="integration is not available"):
        await worker.run_worker(tmp_path / "nonexistent", "native")
    assert not list(tmp_path.iterdir())


def test_producer_preflight_cannot_start_resources_on_unintegrated_main(monkeypatch):
    monkeypatch.delitem(runtime.Configuration.model_fields, "native_source_revision")
    monkeypatch.setattr(
        qa, "command", lambda *_a, **_k: pytest.fail("resource command")
    )
    for action in (qa.prepare, lambda: qa.run("native")):
        with pytest.raises(RuntimeError, match="integration is not available"):
            action()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "operation",
    [
        "credential",
        "client",
        "provider",
        "gateway",
        "reserve",
        "settle",
        "outside_store",
    ],
)
async def test_provider_and_financial_operations_are_blocked(
    attempt, monkeypatch, operation
):
    work, _ = attempt
    integrated(monkeypatch)
    outside = work.parent / "real-ledger.sqlite3"

    async def production(config):
        if operation == "credential":
            runtime.read_credential(outside)
        elif operation == "client":
            runtime.AsyncOpenAI()
        elif operation == "provider":
            runtime.Provider()
        elif operation == "gateway":
            runtime.GatewayProvider()
        elif operation == "outside_store":
            runtime.Store(outside)
        else:
            getattr(runtime.Store(config.state_file), operation)("id", 1)

    monkeypatch.setattr(runtime, "run", production)
    with pytest.raises(RuntimeError, match="forbids"):
        await worker.run_worker(work, "native")
    assert not outside.exists()
    assert not (work / "stop.json").exists()
    # Global guards restore after failure.
    assert runtime.Store is Store


@pytest.mark.parametrize(
    "change",
    [
        {"benchmark_supervision": False},
        {"run_seconds": None},
        {"provider": "openai"},
        {"credential_file": "/private/key"},
        {"budget_file": "/canonical/ledger.sqlite3"},
        {"state_file": "/canonical/ledger.sqlite3"},
        {"operator_port": 8765},
        {"memory_mode": "independent"},
        {"learning": True},
    ],
)
def test_unsafe_config_rejected_before_runtime(attempt, change):
    work, _ = attempt
    config = json.loads((work / "worker.json").read_text())
    config.update(change)
    (work / "worker.json").write_text(json.dumps(config))
    with pytest.raises(ValueError):
        worker.load_configuration(work, "native")


def test_existing_state_never_resumed_or_modified(attempt):
    work, _ = attempt
    sentinel = work / "worker.sqlite3"
    sentinel.write_bytes(b"previous evidence")
    with pytest.raises(ValueError, match="never resume"):
        worker.load_configuration(work, "native")
    assert sentinel.read_bytes() == b"previous evidence"


def test_private_paths_and_environment(tmp_path, monkeypatch):
    monkeypatch.setenv("CANARY_M5_PRIVATE_ROOT", str(tmp_path))
    monkeypatch.setenv("CANARY_M5_QA", str(tmp_path / "new-attempt"))
    monkeypatch.setenv("CANARY_M5_WORLD", str(tmp_path / "world.otbm"))
    monkeypatch.setenv("CANARY_M5_NATIVE_BUILD", str(tmp_path / "build"))
    monkeypatch.setenv("OPENAI_API_KEY", "never-pass")
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "never-pass")
    qa.configure_paths()
    assert qa.WORK == tmp_path / "new-attempt"
    assert qa.WORLD == tmp_path / "world.otbm"
    env = qa.worker_environment(qa.WORK / "native")
    assert set(env) == {"PATH", "PYTHONPATH", "TMPDIR", "CANARY_M5_PRIVATE_ROOT"}
    assert env["TMPDIR"] == str(qa.WORK / "native")
    assert "OPENAI_API_KEY" not in env
    monkeypatch.setenv("CANARY_M5_QA", str(tmp_path.parent / "escape"))
    with pytest.raises(ValueError, match="below the private root"):
        qa.configure_paths()


def test_symlink_escape_is_rejected(attempt, monkeypatch):
    work, _ = attempt
    alias = work.parent / "alias"
    alias.symlink_to(work, target_is_directory=True)
    with pytest.raises(ValueError, match="without symlinks"):
        worker.load_configuration(alias, "native")


def test_import_has_no_runtime_or_cli_side_effects(monkeypatch):
    monkeypatch.setattr(
        runtime, "run", lambda *_a, **_k: pytest.fail("runtime on import")
    )
    spec = importlib.util.spec_from_file_location(
        "free_worker_import", Path(worker.__file__)
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)


def test_socket_symlink_to_another_peer_is_rejected(attempt):
    work, _ = attempt
    (work / "socket").symlink_to(work.parent, target_is_directory=True)
    with pytest.raises(ValueError, match="socket paths"):
        worker.load_configuration(work, "native")


def test_current_source_must_be_clean_and_match_import(monkeypatch):
    calls = []

    def git(*args, **kwargs):
        calls.append(args)
        if "status" in args:
            return " M tests/fixture/m5_worker.py"
        pytest.fail("revision attested before dirty check")

    monkeypatch.setattr(qa, "command", git)
    with pytest.raises(ValueError, match="clean committed"):
        qa.require_current_source()
    assert len(calls) == 1


@pytest.mark.asyncio
async def test_any_inference_row_blocks_stop_export_even_if_supervisor_completed(
    attempt, monkeypatch
):
    work, _ = attempt
    integrated(monkeypatch)

    async def production(config):
        state = runtime.Store(config.state_file)
        with state.connection() as db:
            db.execute(
                "INSERT INTO requests(id,month,reserved,spent) VALUES ('unexpected','2026-11',0,0)"
            )
        state.put("run_stop", "end", {"reason": "completed"})

    monkeypatch.setattr(runtime, "run", production)
    with pytest.raises(RuntimeError, match="forbids"):
        await worker.run_worker(work, "native")
    assert not (work / "stop.json").exists()


def test_worker_rejects_runtime_imported_from_other_source(monkeypatch, tmp_path):
    integrated(monkeypatch)
    monkeypatch.setattr(runtime, "__file__", str(tmp_path / "runtime.py"))
    with pytest.raises(RuntimeError, match="this source checkout"):
        worker.require_native_admission()


def test_native_build_pin_is_distinct_from_harness_source(attempt):
    work, configure = attempt
    config = configure()
    assert config["native_source_revision"] == "b" * 40
    assert config["recording"]["manifests"][0]["source_revision"] == "b" * 40
    assert worker.load_configuration(work, "native").native_source_revision == "b" * 40
    config["native_source_revision"] = "c" * 40
    (work / "worker.json").write_text(json.dumps(config))
    with pytest.raises(ValueError, match="source pins must agree"):
        worker.load_configuration(work, "native")


def test_missing_native_pin_never_falls_back_to_harness_revision(attempt):
    work, _ = attempt
    with pytest.raises(ValueError, match="actual native build source"):
        qa.worker_configuration(work, "native", {"source_revision": "a" * 40})
