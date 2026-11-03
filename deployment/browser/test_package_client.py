import importlib.util
import json
import re
import tempfile
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "package_client", Path(__file__).with_name("package_client.py")
)
client = importlib.util.module_from_spec(spec)
spec.loader.exec_module(client)


class PackagingTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.paths = {
            key: root / key for key in ("build", "runtime", "assets", "sounds")
        }
        for path in self.paths.values():
            path.mkdir()
        self.paths["init"] = root / "init.lua"
        self.paths["config"] = root / "config.ini"
        self.paths["output"] = root / "published"
        self.paths["init"].write_text(
            "Services={status='https://site.example/login.php'}\ng_modules.ensureModuleLoaded('modulelib')\n"
        )
        self.paths["config"].write_text("[render]\nmaxAtlasSize=2048\n")
        module = self.paths["runtime"] / "modules/client_entergame/entergame.lua"
        module.parent.mkdir(parents=True)
        module.write_text(client.LOGIN_CALL)
        (self.paths["assets"] / "appearances-fixture.dat").write_bytes(b"asset")
        (self.paths["sounds"] / "catalog.json").write_bytes(b"{}")
        meta = {
            "files": [
                {"filename": "/init.lua", "start": 0, "end": 3},
                {
                    "filename": "/modules/client_entergame/entergame.lua",
                    "start": 3,
                    "end": 6,
                },
            ],
            "remote_package_size": 6,
            "package_uuid": "fixture",
        }
        literal = re.sub(
            r'"(files|filename|start|end|remote_package_size|package_uuid)":',
            r"\1:",
            json.dumps(meta, separators=(",", ":")),
        )
        script = (
            '(function(){function loadPackage(metadata){var PACKAGE_UUID=metadata["package_uuid"];}loadPackage('
            + literal
            + ')})();var data="otclient.data";var proxiedFunctionTable=[_emscripten_websocket_new];'
            + client.FETCH_SIGNATURE
            + "}"
        )
        (self.paths["build"] / "otclient.js").write_text(script)
        (self.paths["build"] / "otclient.data").write_bytes(b"oldold")
        (self.paths["build"] / "otclient.wasm").write_bytes(b"\0asm")
        (self.paths["build"] / "otclient.html").write_text(
            "<title>Loading</title><script src=otclient.js></script>"
        )
        self.options = {
            **self.paths,
            "login_url": "https://site.example/play/login.php",
            "gateway_host": "game.example",
            "gateway_port": 8444,
        }

    def test_package_has_contiguous_offsets_updated_lua_assets_and_hashes(self):
        meta = client.package(**self.options)
        output = self.paths["output"]
        raw = next(output.glob("*.data")).read_bytes()
        end = 0
        contents = {}
        for entry in meta["files"]:
            self.assertEqual(entry["start"], end)
            contents[entry["filename"]] = raw[entry["start"] : entry["end"]]
            end = entry["end"]
        self.assertEqual(end, len(raw))
        self.assertIn(b"https://site.example/play/login.php", contents["/init.lua"])
        self.assertIn(b"HTTP.post", contents["/modules/client_entergame/entergame.lua"])
        self.assertEqual(
            contents["/data/things/1500/appearances-fixture.dat"], b"asset"
        )
        self.assertEqual(contents["/config.ini"], self.paths["config"].read_bytes())
        manifest = json.loads((output / "package-manifest.json").read_text())
        for name, checksum in manifest.items():
            self.assertEqual(client.digest((output / name).read_bytes()), checksum)
        self.assertIn(
            "proxyToMainThread(1,0,1,fetch)", (output / "otclient.js").read_text()
        )

    def test_unsupported_fetch_layout_does_not_publish_partial_output(self):
        path = self.paths["build"] / "otclient.js"
        path.write_text(
            path.read_text().replace(
                client.FETCH_SIGNATURE, "unsupported_fetch_layout{"
            )
        )
        with self.assertRaises(ValueError):
            client.package(**self.options)
        self.assertFalse(self.paths["output"].exists())

    def test_mismatched_metadata_is_rejected(self):
        (self.paths["build"] / "otclient.data").write_bytes(b"wrong size")
        with self.assertRaises(ValueError):
            client.package(**self.options)

    def test_minified_integer_offsets_in_exponential_notation(self):
        path = self.paths["build"] / "otclient.js"
        path.write_text(path.read_text().replace("end:6", "end:6e0"))
        meta = client.package(**self.options)
        self.assertTrue(
            all(
                type(row["start"]) is int and type(row["end"]) is int
                for row in meta["files"]
            )
        )

    def test_fractional_offsets_are_rejected(self):
        path = self.paths["build"] / "otclient.js"
        path.write_text(path.read_text().replace("end:6", "end:5.5"))
        with self.assertRaises(ValueError):
            client.package(**self.options)

    def test_existing_deployment_is_preserved(self):
        self.paths["output"].mkdir()
        marker = self.paths["output"] / "keep"
        marker.write_text("existing deployment")
        with self.assertRaises(ValueError):
            client.package(**self.options)
        self.assertEqual(marker.read_text(), "existing deployment")

    def test_plain_http_and_gateway_injection_are_rejected(self):
        for changes in (
            {"login_url": "http://site.example/login.php"},
            {"gateway_host": 'bad"host'},
            {"gateway_port": 0},
        ):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                client.package(**{**self.options, **changes})

    def test_saved_credentials_are_not_packaged(self):
        self.paths["init"].write_text(
            self.paths["init"].read_text() + 'password="fixture-only"\n'
        )
        with self.assertRaises(ValueError):
            client.package(**self.options)


if __name__ == "__main__":
    unittest.main()
