"""Disposable networkless PostgreSQL/admin lab; no existing gateway is accessed."""

import re
import subprocess
import tempfile
import time
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[3]
    image = "ghcr.io/berriai/litellm:v1.108.0@sha256:b59b9fd52a67891be4e8dae09ddd4e6c9265e9a8cb3f25f8dd73fbabe7659965"
    database = None
    temporary = tempfile.TemporaryDirectory(prefix="canary-gateway-lab-cids-")
    cidfiles = {
        role: Path(temporary.name) / (role + ".cid")
        for role in ("database", "schema", "test")
    }
    try:
        database = subprocess.check_output(
            [
                "docker",
                "run",
                "-d",
                "--rm",
                "--cidfile",
                str(cidfiles["database"]),
                "--network",
                "none",
                "--tmpfs",
                "/var/lib/postgresql/data",
                "-e",
                "POSTGRES_PASSWORD=synthetic-only",
                "postgres:16-alpine",
            ],
            text=True,
        ).strip()
        for _ in range(60):
            if (
                subprocess.run(
                    ["docker", "exec", database, "pg_isready", "-U", "postgres"],
                    capture_output=True,
                    check=False,
                ).returncode
                == 0
            ):
                break
            time.sleep(0.2)
        else:
            raise RuntimeError("Temporary PostgreSQL not ready")
        common = [
            "docker",
            "run",
            "--rm",
            "--network",
            "container:" + database,
            "-e",
            "DATABASE_URL=postgresql://postgres:synthetic-only@127.0.0.1:5432/postgres",
        ]
        subprocess.run(
            common
            + [
                "--cidfile",
                str(cidfiles["schema"]),
                "--entrypoint",
                "prisma",
                image,
                "db",
                "push",
                "--schema",
                "/app/schema.prisma",
                "--skip-generate",
            ],
            check=True,
            timeout=180,
        )
        subprocess.run(
            common
            + [
                "--cidfile",
                str(cidfiles["test"]),
                "-e",
                "CANARY_FAKE_ADMIN_DB=enabled",
                "-e",
                "PYTHONPATH=/source/deployment/brain/src",
                "-v",
                str(root) + ":/source:ro",
                "--entrypoint",
                "python",
                image,
                "/source/deployment/brain/tools/gateway_admin_routing_smoke.py",
            ],
            check=True,
            timeout=180,
        )
    finally:
        # Killing a timed-out Docker CLI does not stop its container. Only the
        # daemon-created IDs in this private directory belong to this run.
        for role in ("test", "schema", "database"):
            path = cidfiles[role]
            if path.is_file() and not path.is_symlink():
                identity = path.read_text().strip()
                if re.fullmatch(r"[a-f0-9]{64}", identity):
                    subprocess.run(
                        ["docker", "rm", "-f", identity],
                        capture_output=True,
                        check=False,
                    )
        temporary.cleanup()


if __name__ == "__main__":
    main()
