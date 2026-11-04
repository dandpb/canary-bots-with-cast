"""Check the deployed HTTP login/cast contract and native game endpoints."""
import json
import re
import socket
import urllib.request
from urllib.parse import urljoin, urlsplit
import xml.etree.ElementTree as ET

base = "http://127.0.0.1:8080"
with urllib.request.urlopen(base, timeout=15) as response:
    assert response.status == 200
print("PASS website HTTP 200")
for origin in (base, "http://localhost:8080"):
    map_url = origin + "/index.php/worldmap"
    with urllib.request.urlopen(map_url, timeout=15) as response:
        page = response.read().decode()
    assert "Server Offline" not in page, "World Map reports an offline game"
    config = json.loads(re.search(r"window\.WORLDMAP_CFG\s*=\s*(\{.*?\});", page).group(1))
    data_url = urljoin(map_url, config["dataUrl"])
    assert urlsplit(data_url).netloc == urlsplit(map_url).netloc, "World Map crosses origins"
    with urllib.request.urlopen(data_url, timeout=15) as response:
        map_data = json.load(response)
    assert map_data.get("markers"), "World Map has no character positions"
    print(f"PASS World Map online and same-origin: {origin}, {len(map_data['markers'])} positions")
request = urllib.request.Request(
    base + "/login.php", data=json.dumps({"type": "login", "accountname": "@cast", "password": ""}).encode(),
    headers={"Content-Type": "application/json"},
)
with urllib.request.urlopen(request, timeout=15) as response:
    payload = json.load(response)
assert "errorMessage" not in payload, payload.get("errorMessage")
characters = payload["playdata"]["characters"]
assert characters, "Cast has no broadcasting characters yet"
print(f"PASS cast login: {len(characters)} characters")
for port in (7171, 7172, 7173):
    with socket.create_connection(("127.0.0.1", port), timeout=5) as connection:
        if port == 7172:
            assert connection.recv(1024), "Game protocol did not send its challenge"
    print(f"PASS TCP {port}")
with socket.create_connection(("127.0.0.1", 7173), timeout=10) as connection:
    connection.sendall(b"\x06\x00\xff\xffinfo")
    chunks = []
    while chunk := connection.recv(65536):
        chunks.append(chunk)
status = ET.fromstring(b"".join(chunks))
assert status.tag == "tsqp"
print("PASS native status:", status.find("serverinfo").attrib["client"], "players:", status.find("players").attrib["online"])
