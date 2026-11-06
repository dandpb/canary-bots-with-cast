"""A timeout must stop owned lab containers even when Docker CLI was killed."""

import runpy
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest


@pytest.mark.parametrize("failing_role", ["schema", "test"])
def test_lab_cli_timeout_cleans_only_created_container_ids(monkeypatch, failing_role):
    script = (
        Path(__file__).resolve().parents[1] / "tools/run_gateway_admin_routing_smoke.py"
    )
    namespace = runpy.run_path(str(script))
    owned = {"database": "1" * 64, "schema": "2" * 64, "test": "3" * 64}
    paths = []
    removed = []

    def start(args, **kwargs):
        path = Path(args[args.index("--cidfile") + 1])
        path.write_text(owned["database"])
        paths.append(path)
        return owned["database"] + "\n"

    def run(args, **kwargs):
        if args[1] == "exec":
            return SimpleNamespace(returncode=0)
        if args[1] == "rm":
            removed.append(args[-1])
            return SimpleNamespace(returncode=0)
        role = "schema" if "prisma" in args else "test"
        path = Path(args[args.index("--cidfile") + 1])
        path.write_text(owned[role])
        paths.append(path)
        if role == failing_role:
            raise subprocess.TimeoutExpired(args, 180)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(subprocess, "check_output", start)
    monkeypatch.setattr(subprocess, "run", run)
    with pytest.raises(subprocess.TimeoutExpired):
        namespace["main"]()
    assert removed == (
        [owned["schema"], owned["database"]]
        if failing_role == "schema"
        else [owned["test"], owned["schema"], owned["database"]]
    )
    assert all(not path.exists() for path in paths)
