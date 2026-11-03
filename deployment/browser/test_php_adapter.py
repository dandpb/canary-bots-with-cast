"""Execute the generated adapter with a fake MyAAC backend in a PHP container."""

import argparse
import base64
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from package_client import login_adapter


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--container", required=True)
    container = parser.parse_args().container
    adapter = base64.b64encode(login_adapter("game.example", 8444).encode()).decode()
    bodies = [
        json.dumps(
            {
                "session": {"sessionkey": "fixture"},
                "playdata": {
                    "worlds": [
                        {"externaladdress": "tcp.example", "externalport": 7172}
                    ],
                    "characters": [],
                },
            }
        ),
        json.dumps({"errorCode": 3, "errorMessage": "fixture refusal"}),
        "upstream-error",
    ]
    for index, body in enumerate(bodies):
        backend = base64.b64encode(
            ("<?php echo " + json.dumps(body) + ";").encode()
        ).decode()
        code = """<?php
$root = sys_get_temp_dir() . '/canary_adapter_' . bin2hex(random_bytes(8));
mkdir($root); mkdir($root . '/play');
file_put_contents($root . '/login.php', base64_decode('BACKEND'));
file_put_contents($root . '/play/login.php', base64_decode('ADAPTER'));
try { require $root . '/play/login.php'; }
finally { unlink($root . '/play/login.php'); unlink($root . '/login.php'); rmdir($root . '/play'); rmdir($root); }
""".replace("BACKEND", backend).replace("ADAPTER", adapter)
        result = subprocess.run(
            ["docker", "exec", "-i", container, "php"],
            input=code,
            text=True,
            capture_output=True,
            check=True,
        )
        assert not result.stderr, result.stderr
        if index == 0:
            data = json.loads(result.stdout)
            world = data["playdata"]["worlds"][0]
            assert all(
                world[key] == "game.example"
                for key in (
                    "externaladdress",
                    "externaladdressprotected",
                    "externaladdressunprotected",
                )
            )
            assert all(
                world[key] == 8444
                for key in (
                    "externalport",
                    "externalportprotected",
                    "externalportunprotected",
                )
            )
            assert data["session"]["sessionkey"] == "fixture"
        else:
            assert result.stdout == body
    print(
        "PASS: fixed WSS world fields, retained session, unchanged JSON/non-JSON errors"
    )


if __name__ == "__main__":
    main()
