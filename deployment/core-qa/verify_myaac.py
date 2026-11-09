"""Read-only MyAAC entrypoint/config receipt for the pinned QA base image."""

import hashlib
import json
import os
import re
import shlex
import subprocess
import tarfile
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOCK = json.loads((HERE / "image-lock.json").read_text())["web_base"]
# Public synthetic inputs of the MyAAC config.lua heredoc, never the operational .env: the stage-1 contract
# whose render image-lock.json pins as qa_config_sha256. Another profile changes only the keys of
# PROFILE_KEYS, from its preflight.PROFILES row (the same row its Compose render is checked against).
PUBLIC_FIXTURE = {
    "CANARY_SERVER_NAME": "Canary core QA",
    "CANARY_SERVER_IP": "127.0.0.1",
    "CANARY_LOGIN_PORT": "17171",
    "CANARY_GAME_PORT": "17172",
    "CANARY_STATUS_PORT": "17173",
    "CANARY_STATUS_TIMEOUT": "5000",
    "CANARY_DATA_PACK": "data-otservbr-global",
    "CANARY_DB_HOST": "database",
    "CANARY_DB_PORT": "3306",
    "CANARY_DB_USER": "canary",
    "CANARY_DB_PASSWORD": "qa-test-only",
    "CANARY_DB_NAME": "canary",
}
PROFILE_KEYS = ("CANARY_SERVER_NAME", "CANARY_LOGIN_PORT", "CANARY_GAME_PORT", "CANARY_STATUS_PORT")
# The config.lua line each PROFILE_KEYS value renders to (Canary config.lua names, as in config.lua.dist).
CONFIG_FIELDS = ('serverName = "{}"', "loginProtocolPort = {}", "gameProtocolPort = {}", "statusProtocolPort = {}")


def entrypoint_from_image():
    proc = subprocess.Popen(
        ["docker", "image", "save", LOCK["ref"]], stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    script = None
    try:
        with tarfile.open(fileobj=proc.stdout, mode="r|") as archive:
            for blob in archive:
                if not blob.name.startswith("blobs/sha256/"):
                    continue
                try:
                    layer = tarfile.open(fileobj=archive.extractfile(blob), mode="r|*")
                except tarfile.ReadError:
                    continue
                for item in layer:
                    if item.isfile() and item.name == "usr/local/bin/myaac-entrypoint":
                        script = layer.extractfile(item).read()
        stderr = proc.stderr.read()
        if proc.wait() != 0:
            raise RuntimeError("read-only image export failed: " + stderr.decode("utf-8", "replace")[:300])
    finally:
        proc.stdout.close()
        proc.stderr.close()
        if proc.poll() is None:
            proc.kill()
            proc.wait()
    if script is None:
        raise RuntimeError("MyAAC entrypoint absent from the pinned image")
    return script


def profile_fixture(profile):
    """The public fixture for a preflight.PROFILES row: only its server name and ports differ."""
    ports = profile["ports"]
    values = (profile["server_name"], ports["login"], ports["game"], ports["status"])
    return {**PUBLIC_FIXTURE, **{key: str(value) for key, value in zip(PROFILE_KEYS, values, strict=True)}}


def fixture_sha256(fixture):
    return hashlib.sha256(json.dumps(fixture, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def rendered_config(script, fixture=None):
    source = script.decode("utf-8")
    function_start = source.index("escape_lua() {")
    function_end = source.index("\n}\n", function_start) + 3
    config_start = source.index("cat > /canary/config.lua <<EOF")
    config_end = source.index("\nEOF", config_start) + 4
    with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR") or HERE) as directory:
        output = Path(directory) / "config.lua"
        heredoc = source[config_start:config_end].replace(
            "cat > /canary/config.lua", f"cat > {shlex.quote(str(output))}", 1,
        )
        shell = "set -eu\n" + source[function_start:function_end] + "\n" + heredoc + "\n"
        env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), **(fixture or PUBLIC_FIXTURE)}
        subprocess.run(["bash", "-c", shell], env=env, check=True, capture_output=True)
        return output.read_bytes()


def expected_profile_config(stage1_config, fixture, profile):
    """The bytes the profile config must be: the pinned stage-1 config with each CONFIG_FIELDS line, anchored
    as a whole line and present exactly once, rewritten with the profile's fixture value. Built from the pinned
    render and the profile row only, never from the config under check."""
    expected = stage1_config
    for key, line in zip(PROFILE_KEYS, CONFIG_FIELDS, strict=True):
        if re.search(r'["\\\n]', fixture[key]):
            raise RuntimeError(f"MyAAC {profile['name']} {key} is not a plain value; refused")
        anchored = re.compile(rb"(?m)^" + re.escape(line.format(PUBLIC_FIXTURE[key]).encode()) + rb"$")
        found = len(anchored.findall(stage1_config))
        if found != 1:
            raise RuntimeError(f"pinned stage-1 MyAAC config has {found} '{line.format(PUBLIC_FIXTURE[key])}' "
                               "lines, not exactly 1; refused")
        replacement = line.format(fixture[key]).encode()
        expected = anchored.sub(lambda _match, value=replacement: value, expected)
    return expected


def assert_profile_config(stage1_config, config, fixture, profile):
    """The profile config equals, byte for byte, expected_profile_config()."""
    if config != expected_profile_config(stage1_config, fixture, profile):
        raise RuntimeError(f"MyAAC generated config is not the expected {profile['name']} config (the pinned "
                           f"stage-1 config with the {profile['name']} server name and ports); refused")


def verify(profile=None):
    """profile None or stage1: the stage-1 contract, unchanged. Another preflight.PROFILES row: the same pinned
    image and entrypoint render the public fixture of that profile, attested against the pinned stage-1 render."""
    image = LOCK["ref"]
    actual_id = subprocess.run(
        ["docker", "image", "inspect", image, "--format", "{{.Id}}"],
        check=True, capture_output=True, text=True,
    ).stdout.strip()
    if actual_id != LOCK["id"]:
        raise RuntimeError("MyAAC image ID differs from image-lock.json")
    script = entrypoint_from_image()
    script_digest = hashlib.sha256(script).hexdigest()
    if script_digest != LOCK["entrypoint_sha256"]:
        raise RuntimeError("MyAAC entrypoint differs from image-lock.json")
    config = rendered_config(script)
    if not re.search(rb"(?m)^gameProtocolPort = 17172$", config):
        raise RuntimeError("MyAAC generated config does not advertise QA game port 17172")
    config_digest = hashlib.sha256(config).hexdigest()
    expected = LOCK.get("qa_config_sha256")
    if expected and config_digest != expected:
        raise RuntimeError("MyAAC generated config differs from image-lock.json")
    if profile is None or profile["name"] == "stage1":
        return {
            "image_id": actual_id,
            "entrypoint_sha256": script_digest,
            "qa_config_sha256": config_digest,
        }
    if not expected:
        raise RuntimeError("image-lock.json pins no stage-1 qa_config_sha256 to attest another profile against")
    fixture = profile_fixture(profile)
    profile_config = rendered_config(script, fixture)
    assert_profile_config(config, profile_config, fixture, profile)
    profile_digest = hashlib.sha256(profile_config).hexdigest()
    return {
        "image_id": actual_id,
        "entrypoint_sha256": script_digest,
        "qa_config_sha256": profile_digest,
        "attestation": {
            "profile": profile["name"],
            "fixture": "verify_myaac.PUBLIC_FIXTURE with the profile's " + ", ".join(PROFILE_KEYS),
            "fixture_sha256": fixture_sha256(fixture),
            "stage1_fixture_sha256": fixture_sha256(PUBLIC_FIXTURE),
            "stage1_config_sha256": config_digest,
            "config_sha256": profile_digest,
            "game_protocol_port": profile["ports"]["game"],
        },
    }


if __name__ == "__main__":
    print("QA MyAAC config.lua SHA-256:", verify()["qa_config_sha256"])
