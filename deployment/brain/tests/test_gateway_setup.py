"""Gateway setup must preserve database identity and existing credentials."""

import runpy
from pathlib import Path
from urllib.parse import quote


def test_preparation_preserves_secrets_and_database_connection(tmp_path):
    script = Path(__file__).resolve().parents[2] / "wsl/setup-gateway.py"
    prepare = runpy.run_path(str(script))["prepare"]
    private = tmp_path / "runtime/secrets"
    private.mkdir(parents=True)
    db_password = "private-fixture@:/+"
    database = private / "litellm-db.env"
    database.write_text("POSTGRES_PASSWORD=" + db_password + "\n")
    worker = private / "litellm-worker.env"
    worker.write_text("LITELLM_MASTER_KEY=existing-local-fixture\n")
    result = prepare(tmp_path)
    assert len(result["created"]) == 3
    ui = (private / "litellm-ui.env").read_text()
    assert "postgresql://litellm:" + quote(db_password, safe="") + "@litellm-db:" in ui
    assert "UI_USERNAME=admin\n" in ui
    assert "UI_PASSWORD=" not in ui
    paths = [p for p in tmp_path.rglob("*") if p.is_file()]
    original = {p: p.read_bytes() for p in paths}
    repeated = prepare(tmp_path)
    assert repeated["created"] == []
    assert len(repeated["preserved"]) == 5
    assert original == {p: p.read_bytes() for p in paths}
    assert worker.read_text() == "LITELLM_MASTER_KEY=existing-local-fixture\n"
