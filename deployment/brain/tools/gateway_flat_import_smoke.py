"""Pinned vendor flat loader and a real proxy startup, without inference."""

import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

from litellm.proxy.types_utils.utils import get_instance_fn


def main():
    source = Path(__file__).resolve().parents[1] / "src/canary_brain/gateway_policy.py"
    with tempfile.TemporaryDirectory(prefix="canary-flat-policy-") as directory:
        root = Path(directory)
        module = root / "gateway_policy.py"
        shutil.copyfile(source, module)
        policy = root / "gateway.yaml"
        policy.write_text(
            json.dumps(
                {
                    "model_list": [],
                    "router_settings": {"num_retries": 0},
                    "litellm_settings": {"num_retries": 0, "drop_params": False},
                    "general_settings": {
                        "master_key": "os.environ/LITELLM_MASTER_KEY",
                        "custom_auth": "gateway_policy.authenticate",
                        "custom_auth_settings": {"mode": "auto"},
                    },
                }
            )
        )
        os.environ["CANARY_GATEWAY_CONFIG"] = str(policy)
        assert "gateway_policy" not in sys.modules
        auth = get_instance_fn(
            "gateway_policy.authenticate", config_file_path=str(policy)
        )
        assert callable(auth) and Path(auth.__code__.co_filename) == module
        assert "gateway_policy" not in sys.modules
        assert auth.__globals__["_startup_policy"] == policy.read_bytes()
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            port = listener.getsockname()[1]
        env = {
            **os.environ,
            "LITELLM_LOCAL_MODEL_COST_MAP": "True",
            "CANARY_BENCHMARK_GATEWAY_ONLY": "1",
            "LITELLM_MASTER_KEY": "sk-synthetic-master",
            "LITELLM_WORKER_KEY": "sk-synthetic-worker",
            "STORE_MODEL_IN_DB": "True",
        }
        env.pop("DATABASE_URL", None)
        with (root / "proxy.log").open("w") as log:
            process = subprocess.Popen(
                [
                    "litellm",
                    "--config",
                    str(policy),
                    "--host",
                    "127.0.0.1",
                    "--port",
                    str(port),
                ],
                env=env,
                stdout=log,
                stderr=subprocess.STDOUT,
            )
            try:
                for _ in range(200):
                    try:
                        with urllib.request.urlopen(
                            f"http://127.0.0.1:{port}/health/readiness", timeout=1
                        ) as response:
                            assert response.status == 200
                        break
                    except OSError:
                        if process.poll() is not None:
                            raise RuntimeError((root / "proxy.log").read_text()[-4000:])
                        time.sleep(0.1)
                else:
                    raise AssertionError("Proxy readiness timeout")
                print(
                    json.dumps(
                        {
                            "python": sys.version.split()[0],
                            "vendor_flat_loader": True,
                            "module_unregistered": True,
                            "real_proxy_health": 200,
                            "inference_calls": 0,
                        }
                    )
                )
            finally:
                process.terminate()
                try:
                    process.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)


if __name__ == "__main__":
    main()
