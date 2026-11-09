"""Scored providers must not start against mutable game/database images."""

import json

import pytest
from test_benchmark import experiment
from test_gateway import gateway

from canary_brain import runtime
from canary_brain.benchmark import DockerFixture, Participant, preflight
from canary_brain.recording import digest


@pytest.mark.parametrize("field", ["game_image", "database_image"])
def test_paid_preflight_rejects_mutable_image_before_any_credential_read(
    tmp_path, monkeypatch, field
):
    config = experiment(tmp_path).model_copy(
        update={
            "participants": [
                Participant(name="model", kind="litellm", gateway=gateway())
            ],
            "game_image": "sha256:" + "a" * 64,
            "database_image": "mariadb@sha256:" + "b" * 64,
        }
    )
    setattr(config, field, "mutable:latest")

    def forbidden(*args, **kwargs):
        raise AssertionError("must reject images before reading credentials")

    monkeypatch.setattr(runtime, "read_credential", forbidden)
    with pytest.raises(ValueError, match="immutable image"):
        preflight(config)


def test_database_pin_changes_fingerprint_and_reaches_compose(tmp_path):
    config = experiment(tmp_path)
    before = digest(config.model_dump(mode="json"))
    config.database_image = "mariadb@sha256:" + "b" * 64
    assert digest(config.model_dump(mode="json")) != before
    harness = DockerFixture(config, config.output / "native-0", "pin-only")
    harness.prepare(config.participants[0])
    assert (
        json.loads(harness.compose.read_text())["services"]["database"]["image"]
        == config.database_image
    )


def test_paid_preflight_accepts_pins_without_contacting_a_provider(
    tmp_path, monkeypatch
):
    config = experiment(tmp_path).model_copy(
        update={
            "participants": [
                Participant(name="model", kind="litellm", gateway=gateway())
            ],
            "game_image": "sha256:" + "a" * 64,
            "database_image": "mariadb@sha256:" + "b" * 64,
            "gateway_credential": tmp_path / "not-read.env",
        }
    )
    monkeypatch.setattr(runtime, "read_credential", lambda *args: "local-test-only")
    assert preflight(config)["runs"] == 1
