"""Package a compatible OTClient Redemption browser build for a MyAAC site."""

import argparse
import hashlib
import json
import os
import re
import shutil
import tempfile
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit

LOGIN_CALL = """    local http = LoginHttp.create()
    http:httpLogin(host, path, G.port, G.account, G.password, G.requestId, httpLogin, G.authenticatorToken)"""
ASYNC_LOGIN = """    -- WebAssembly's game worker must not block the browser's fetch callbacks.
    local requestId = G.requestId
    HTTP.post(G.host, json.encode({
        type = 'login', email = G.account, password = G.password,
        stayloggedin = true, token = G.authenticatorToken
    }), function(message, err)
        if err then
            EnterGame.loginFailed(requestId, 'Falha ao conectar ao login HTTPS.', 3)
            return
        end
        local ok, response = pcall(json.decode, message)
        if not ok or type(response) ~= 'table' then
            EnterGame.loginFailed(requestId, 'Resposta de login inválida.', 3)
            return
        end
        if response.errorCode and response.errorCode ~= 0 then
            EnterGame.loginFailed(requestId, response.errorMessage or 'Login recusado.', response.errorCode)
            return
        end
        if not response.session or not response.playdata then
            EnterGame.loginFailed(requestId, 'Resposta de login incompleta.', 3)
            return
        end
        EnterGame.loginSuccess(requestId, json.encode(response.session),
            json.encode(response.playdata.worlds), json.encode(response.playdata.characters))
    end, false)"""
FETCH_SIGNATURE = "function _emscripten_start_fetch(fetch,successcb,errorcb,progresscb,readystatechangecb){"
HEADERS = """Options -Indexes
DirectoryIndex index.html
Header always set Cross-Origin-Opener-Policy "same-origin"
Header always set Cross-Origin-Embedder-Policy "require-corp"
Header always set Cross-Origin-Resource-Policy "same-origin"
Header always set Cache-Control "no-cache"
AddType application/wasm .wasm
AddType application/octet-stream .data
"""


def digest(data):
    return hashlib.sha256(data).hexdigest()


def login_adapter(host, port):
    if (
        not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9.-]{0,252}", host)
        or not 1 <= port <= 65535
    ):
        raise ValueError("provide a DNS gateway host and valid port")
    return """<?php
// Deploy under the MyAAC root (for example /play/login.php).
chdir(dirname(__DIR__));
header('Content-Type: application/json; charset=utf-8');
ob_start(static function (string $body): string {
    $data = json_decode($body, true);
    if (!is_array($data) || !isset($data['playdata']['worlds']) || !is_array($data['playdata']['worlds'])) return $body;
    foreach ($data['playdata']['worlds'] as $world) { if (!is_array($world)) return $body; }
    foreach ($data['playdata']['worlds'] as &$world) {
        foreach (['externaladdress', 'externaladdressprotected', 'externaladdressunprotected'] as $key) {
            $world[$key] = GATEWAY_HOST;
        }
        foreach (['externalport', 'externalportprotected', 'externalportunprotected'] as $key) {
            $world[$key] = GATEWAY_PORT;
        }
    }
    unset($world);
    $encoded = json_encode($data, JSON_UNESCAPED_SLASHES);
    return $encoded === false ? $body : $encoded;
});
require 'login.php';
""".replace("GATEWAY_HOST", json.dumps(host)).replace("GATEWAY_PORT", str(port))


def package(
    build,
    runtime,
    init,
    config,
    assets,
    sounds,
    output,
    login_url,
    gateway_host,
    gateway_port,
    locale="pt",
):
    url = urlsplit(login_url)
    if (
        url.scheme != "https"
        or not url.hostname
        or url.username
        or url.password
        or url.query
        or url.fragment
        or any(c in login_url for c in "\"'\\\r\n\t")
        or not url.path.endswith("/login.php")
    ):
        raise ValueError(
            "login URL must be HTTPS without credentials, query or fragment"
        )
    if not re.fullmatch(r"[a-z]{2}", locale):
        raise ValueError("locale must contain two lowercase letters")
    adapter = login_adapter(gateway_host, gateway_port)
    output = Path(output)
    if output.exists():
        raise ValueError(
            "output must be a new directory; existing deployments are never overwritten"
        )
    js = (Path(build) / "otclient.js").read_text()
    old = (Path(build) / "otclient.data").read_bytes()
    start = js.index("({files:[") + 1
    end = js.index("})})();", start) + 1
    literal = js[start:end]
    metadata = json.loads(
        re.sub(
            r"([,{])\s*(files|filename|start|end|remote_package_size|package_uuid):",
            r'\1"\2":',
            literal,
        )
    )
    if metadata["remote_package_size"] != len(old):
        raise ValueError("JavaScript metadata does not match its data file")
    init_text = Path(init).read_text()
    config_bytes = Path(config).read_bytes()
    for text in (init_text, config_bytes.decode()):
        if re.search(
            r'\b(account|password|token|sessionkey)\s*=\s*["\'][^"\']+',
            text,
            re.IGNORECASE,
        ):
            raise ValueError("use fresh client configuration without saved credentials")
    init_text, changed = re.subn(r'https?://[^\s"\']+/login\.php', login_url, init_text)
    if not changed:
        raise ValueError("init.lua must contain a configured HTTP login.php service")
    anchor = "g_modules.ensureModuleLoaded('modulelib')"
    if init_text.count(anchor) != 1:
        raise ValueError("unsupported client initialization layout")
    init_text = init_text.replace(
        anchor,
        anchor
        + f"\nif g_settings.get('locale', 'false') == 'false' then g_settings.set('locale', '{locale}') end\nif g_settings.get('showOutfitsOnList', 'unset') == 'unset' then g_settings.set('showOutfitsOnList', false) end",
    )
    enter = (Path(runtime) / "modules/client_entergame/entergame.lua").read_text()
    if enter.count(LOGIN_CALL) != 1:
        raise ValueError("unsupported client login adapter")
    enter = enter.replace(LOGIN_CALL, ASYNC_LOGIN)
    overrides = {
        "/init.lua": init_text.encode(),
        "/modules/client_entergame/entergame.lua": enter.encode(),
        "/config.ini": config_bytes,
    }
    for folder, prefix in (
        (assets, "/data/things/1500/"),
        (sounds, "/data/sounds/1500/"),
    ):
        paths = sorted(p for p in Path(folder).iterdir() if p.is_file())
        if not paths:
            raise ValueError("asset and sound directories must not be empty")
        overrides.update({prefix + path.name: path.read_bytes() for path in paths})
    chunks, files, seen = [], [], set()
    offset = 0
    for entry in metadata["files"]:
        name = entry["filename"]
        if (
            name in seen
            or not name.startswith("/")
            or ".." in PurePosixPath(name).parts
        ):
            raise ValueError("invalid or duplicate package path")
        # Minified Emscripten metadata uses exponential notation for some integers.
        bounds = (entry["start"], entry["end"])
        if (
            not all(
                type(v) in (int, float) and 0 <= v <= len(old) and int(v) == v
                for v in bounds
            )
            or bounds[0] > bounds[1]
        ):
            raise ValueError("invalid package byte range")
        seen.add(name)
        data = overrides.get(name, old[int(bounds[0]) : int(bounds[1])])
        chunks.append(data)
        files.append({"filename": name, "start": offset, "end": offset + len(data)})
        offset += len(data)
    if not {"/init.lua", "/modules/client_entergame/entergame.lua"}.issubset(seen):
        raise ValueError("client package lacks required runtime files")
    for name, data in overrides.items():
        if name not in seen:
            chunks.append(data)
            files.append({"filename": name, "start": offset, "end": offset + len(data)})
            offset += len(data)
    data = b"".join(chunks)
    data_name = "otclient-" + digest(data)[:12] + ".data"
    meta = {
        "files": files,
        "remote_package_size": len(data),
        "package_uuid": "sha256-" + digest(data),
    }
    js = js[:start] + json.dumps(meta, separators=(",", ":")) + js[end:]
    if '"otclient.data"' not in js:
        raise ValueError("unsupported Emscripten data loader")
    js = js.replace('"otclient.data"', json.dumps(data_name))
    marker = 'var PACKAGE_UUID=metadata["package_uuid"];'
    if js.count(marker) != 1 or js.count(FETCH_SIGNATURE) != 1:
        raise ValueError("unsupported Emscripten fetch or filesystem layout")
    js = js.replace(
        marker,
        'Module["FS_createPath"]("/data/things","1500",true,true);Module["FS_createPath"]("/data","sounds",true,true);Module["FS_createPath"]("/data/sounds","1500",true,true);'
        + marker,
    )
    proxy = re.search(r"var proxiedFunctionTable=\[([^\]]*)\]", js)
    if not proxy or "_emscripten_websocket_new" not in proxy[1].split(","):
        raise ValueError("unsupported Emscripten main-thread proxy table")
    index = len(proxy[1].split(","))
    js = (
        js[: proxy.start(1)]
        + proxy[1]
        + ",_emscripten_start_fetch"
        + js[proxy.end(1) :]
    )
    js = js.replace(
        FETCH_SIGNATURE,
        FETCH_SIGNATURE
        + f"if(ENVIRONMENT_IS_PTHREAD)return proxyToMainThread({index},0,1,fetch);",
    )
    html = (
        (Path(build) / "otclient.html")
        .read_text()
        .replace(
            "<title>Loading</title>",
            '<title>Canary Bots</title><link rel="icon" href="data:,">',
        )
    )
    if "src=otclient.js" not in html:
        raise ValueError("unsupported browser shell")
    html = html.replace(
        "src=otclient.js", "src=otclient.js?v=" + digest(js.encode())[:12]
    )
    if locale == "pt":
        html = html.replace(">Start</button>", ">Iniciar jogo</button>")
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=output.name + ".", dir=output.parent))
    try:
        (stage / data_name).write_bytes(data)
        (stage / "otclient.js").write_text(js)
        shutil.copyfile(Path(build) / "otclient.wasm", stage / "otclient.wasm")
        (stage / "index.html").write_text(html)
        (stage / ".htaccess").write_text(HEADERS)
        (stage / "login.php").write_text(adapter)
        (stage / "init.lua").write_text(init_text)
        (stage / "entergame.lua").write_text(enter)
        manifest = {
            path.name: digest(path.read_bytes())
            for path in stage.iterdir()
            if path.is_file()
        }
        (stage / "package-manifest.json").write_text(
            json.dumps(manifest, indent=2) + "\n"
        )
        os.rename(stage, output)
    finally:
        if stage.exists():
            shutil.rmtree(stage)
    return meta


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in (
        "build",
        "runtime",
        "init",
        "config",
        "assets",
        "sounds",
        "output",
        "login-url",
        "gateway-host",
    ):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--gateway-port", type=int, default=8444)
    parser.add_argument("--locale", default="pt")
    args = vars(parser.parse_args())
    meta = package(**args)
    print(
        json.dumps(
            {
                "files": len(meta["files"]),
                "bytes": meta["remote_package_size"],
                "uuid": meta["package_uuid"],
            }
        )
    )


if __name__ == "__main__":
    main()
