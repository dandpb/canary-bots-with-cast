"""The free fixture uses its reviewed base instead of a mutable historical tag."""

import m5_qa as qa
import pytest


@pytest.mark.parametrize("reference", ["", "--all", "image with spaces"])
def test_missing_or_option_like_base_never_calls_docker(monkeypatch, reference):
    calls = []
    monkeypatch.setattr(qa, "command", lambda *args: calls.append(args))
    with pytest.raises(ValueError, match="CANARY_M5_BASE_IMAGE"):
        qa.pin_base_image(reference, "private:test")
    assert calls == []


def test_private_base_tag_uses_resolved_content_id(monkeypatch):
    image = "sha256:" + "a" * 64
    calls = []

    def docker(*args):
        calls.append(args)
        return image if args[1] == "image" else ""

    monkeypatch.setattr(qa, "command", docker)
    result = qa.pin_base_image("candidate:reviewed", "private:attempt")
    assert result == {
        "requested": "candidate:reviewed",
        "image_id": image,
        "private_tag": "private:attempt",
    }
    assert calls == [
        ("docker", "image", "inspect", "candidate:reviewed", "--format", "{{.Id}}"),
        ("docker", "tag", image, "private:attempt"),
        ("docker", "image", "inspect", "private:attempt", "--format", "{{.Id}}"),
    ]


def test_invalid_content_id_is_not_tagged(monkeypatch):
    calls = []
    monkeypatch.setattr(qa, "command", lambda *args: calls.append(args) or "unknown")
    with pytest.raises(ValueError, match="content ID"):
        qa.pin_base_image("candidate:reviewed", "private:attempt")
    assert len(calls) == 1


def test_changed_private_tag_is_rejected(monkeypatch):
    replies = iter(["sha256:" + "a" * 64, "", "sha256:" + "b" * 64])
    monkeypatch.setattr(qa, "command", lambda *args: next(replies))
    with pytest.raises(ValueError, match="tag changed"):
        qa.pin_base_image("candidate:reviewed", "private:attempt")
