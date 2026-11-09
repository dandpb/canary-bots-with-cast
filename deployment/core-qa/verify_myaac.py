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


def rendered_config(script):
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
        env = {
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
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
        subprocess.run(["bash", "-c", shell], env=env, check=True, capture_output=True)
        return output.read_bytes()


def verify():
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
    return {
        "image_id": actual_id,
        "entrypoint_sha256": script_digest,
        "qa_config_sha256": config_digest,
    }


if __name__ == "__main__":
    print("QA MyAAC config.lua SHA-256:", verify()["qa_config_sha256"])
