#!/usr/bin/env python3
"""Read-only live status panel for the canary-bots-wsl deployment, from Windows.

Complements the S1 digest (``deployment/wsl/ops-digest.py``): the digest is the
daily artifact with logs, Grizzle XP and save health; this panel is the fast
"is it up right now" check. It writes nothing, restarts nothing, and sends no
bot command. Every read is a ``docker ps`` / HTTP GET / TCP request, plus the
newest digest artifact on disk.

Works from Windows because Docker Desktop exposes the WSL engine's CLI and
the deployment publishes its ports on 127.0.0.1 (WSL localhost forwarding).

    python deployment/windows/canary-status.py
    python deployment/windows/canary-status.py --json
    python deployment/windows/canary-status.py --open   # also open the world map

Verdict semantics follow S1: a stopped or unhealthy service, an unanswered
status request, or zero players is RED; a starting service, low population,
an unreachable endpoint, or a stale/missing digest is AMBER. The historical
digest verdict is shown but never changes the live verdict.

Exit codes: 0 GREEN, 1 AMBER, 2 RED.
"""

import argparse
import json
import re
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from pathlib import Path

PROJECT = "canary-bots-wsl"
STATUS_PORT = 7173
MIN_PLAYERS_ONLINE = 10
DIGEST_MAX_AGE_SECONDS = 26 * 3600  # daily S1 cadence plus grace
DEFAULT_DIGEST_DIR = Path(__file__).resolve().parent.parent / "wsl" / "runtime" / "digests"
VERDICT_PATTERN = re.compile(r"\*\*Verdict:\s*(GREEN|AMBER|RED)\*\*")
EXIT_CODES = {"GREEN": 0, "AMBER": 1, "RED": 2}


def run(args, timeout=25):
    """Run a command and return (stdout, stderr, returncode) without raising."""
    try:
        proc = subprocess.run(
            args, check=False, text=True, capture_output=True, timeout=timeout
        )
    except subprocess.TimeoutExpired:
        return "", f"timeout after {timeout}s", 124
    except FileNotFoundError as exc:
        return "", str(exc), 127
    return proc.stdout, proc.stderr, proc.returncode


def health_from_status(status):
    if "(unhealthy)" in status:
        return "unhealthy"
    if "(health: starting)" in status:
        return "starting"
    if "(healthy)" in status:
        return "healthy"
    return "none"


def collect_services():
    """One docker ps call: every container in the Compose project, any state."""
    fmt = '{{.Names}}\t{{.Label "com.docker.compose.service"}}\t{{.State}}\t{{.Status}}'
    out, err, code = run(
        ["docker", "ps", "-a", "--filter",
         f"label=com.docker.compose.project={PROJECT}", "--format", fmt]
    )
    if code != 0:
        return [], err.strip() or f"docker ps exit {code}"
    services = []
    for line in out.strip().splitlines():
        parts = line.split("\t")
        if len(parts) < 4 or not parts[1]:
            continue
        services.append({
            "service": parts[1],
            "container": parts[0],
            "state": parts[2],
            "status": parts[3],
            "health": health_from_status(parts[3]),
        })
    services.sort(key=lambda item: item["service"])
    if not services:
        return [], f"no containers found for Compose project {PROJECT}"
    return services, None


def native_status(host, timeout):
    """Ask the game server for its status frame (the authoritative population)."""
    try:
        with socket.create_connection((host, STATUS_PORT), timeout=timeout) as conn:
            conn.settimeout(3)
            conn.sendall(b"\x06\x00\xff\xffinfo")
            chunks = []
            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                try:
                    chunk = conn.recv(65536)
                except TimeoutError:
                    break
                if not chunk:
                    break
                chunks.append(chunk)
                if b"</tsqp>" in b"".join(chunks):
                    break
    except OSError as exc:
        return None, f"status port unreachable: {exc}"
    payload = b"".join(chunks)
    if not payload:
        return None, "empty status frame (server may still be loading)"
    try:
        root = ET.fromstring(payload)
    except ET.ParseError as exc:
        return None, f"unparsable status frame: {exc}"
    server = root.find("serverinfo")
    players = root.find("players")
    if server is None or players is None:
        return None, "status frame missing serverinfo/players"
    return {
        "uptime_seconds": int(server.get("uptime", 0)),
        "client_protocol": server.get("client"),
        "server_version": server.get("version"),
        "server_name": server.get("servername"),
        "players_online": int(players.get("online", 0)),
        "players_peak": int(players.get("peak", 0)),
    }, None


def http_probe(url, timeout):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            body = response.read()
            return {"reachable": True, "status": response.status, "body": body}
    except urllib.error.HTTPError as exc:
        return {"reachable": True, "status": exc.code, "body": b""}
    except Exception as exc:  # noqa: BLE001 - the probe reports, never raises
        return {"reachable": False, "status": None, "note": type(exc).__name__,
                "body": b""}


def tcp_probe(host, port, timeout, expect_challenge=False):
    try:
        with socket.create_connection((host, port), timeout=timeout) as conn:
            if not expect_challenge:
                return {"reachable": True}
            conn.settimeout(timeout)
            return {"reachable": True, "challenge": bool(conn.recv(1024))}
    except OSError as exc:
        return {"reachable": False, "note": str(exc)}


def collect_endpoints(host, timeout):
    base = f"http://{host}:8080"
    endpoints = {}
    site = http_probe(base + "/", timeout)
    endpoints["site"] = {k: v for k, v in site.items() if k != "body"}
    worldmap = http_probe(base + "/index.php/worldmap", timeout)
    endpoints["worldmap"] = {k: v for k, v in worldmap.items() if k != "body"}
    if worldmap["reachable"]:
        page = worldmap["body"].decode(errors="replace")
        endpoints["worldmap"]["offline"] = "Server Offline" in page
    litellm = http_probe(f"http://{host}:4000/health/liveliness", timeout)
    endpoints["litellm"] = {k: v for k, v in litellm.items() if k != "body"}
    endpoints["tcp_7171"] = tcp_probe(host, 7171, timeout)
    endpoints["tcp_7172"] = tcp_probe(host, 7172, timeout, expect_challenge=True)
    return endpoints


def latest_digest(directory):
    """Newest markdown digest artifact: verdict line plus file age."""
    directory = Path(directory)
    if not directory.is_dir():
        return None, f"digest directory not found: {directory}"
    candidates = list(directory.glob("*.md"))
    if not candidates:
        return None, f"no digest artifact in {directory}"
    newest = max(candidates, key=lambda path: path.stat().st_mtime)
    try:
        head = newest.read_text(encoding="utf-8", errors="replace")[:4000]
    except OSError as exc:
        return None, f"unreadable digest {newest}: {exc}"
    match = VERDICT_PATTERN.search(head)
    return {
        "path": str(newest),
        "verdict": match.group(1) if match else None,
        "age_seconds": int(time.time() - newest.stat().st_mtime),
    }, None


def evaluate(report):
    """Turn collected facts into a verdict, findings and an exit code."""
    findings = []
    severity = "green"

    def escalate(level):
        nonlocal severity
        order = {"green": 0, "amber": 1, "red": 2}
        if order[level] > order[severity]:
            severity = level

    if report.get("services_error"):
        escalate("red")
        findings.append(f"docker collector failed: {report['services_error']}")
    for service in report.get("services", []):
        if service["state"] != "running":
            escalate("red")
            findings.append(
                f"service `{service['service']}` is {service['state']} "
                f"({service['status']})")
        elif service["health"] == "unhealthy":
            escalate("red")
            findings.append(f"service `{service['service']}` reports unhealthy")
        elif service["health"] == "starting":
            escalate("amber")
            findings.append(f"service `{service['service']}` is still starting")

    status = report.get("status")
    if not status:
        escalate("red")
        findings.append(
            f"the game server did not answer the status request: "
            f"{report.get('status_error')}")
    else:
        online = status.get("players_online")
        if online is not None:
            if online < 1:
                escalate("red")
                findings.append("no players are online")
            elif online < MIN_PLAYERS_ONLINE:
                escalate("amber")
                findings.append(f"only {online} players are online")

    for name, probe in (report.get("endpoints") or {}).items():
        if not probe.get("reachable"):
            escalate("amber")
            findings.append(f"{name} is not reachable")
        elif name == "worldmap" and probe.get("offline"):
            escalate("amber")
            findings.append("world map reports the game as offline")
        elif name == "tcp_7172" and not probe.get("challenge", True):
            escalate("amber")
            findings.append("game protocol port accepted TCP but sent no challenge")

    digest = report.get("digest")
    if not digest:
        escalate("amber")
        findings.append(
            f"no usable S1 digest artifact: {report.get('digest_error')}")
    elif digest["age_seconds"] > DIGEST_MAX_AGE_SECONDS:
        escalate("amber")
        findings.append(
            f"the newest digest is stale ({format_age(digest['age_seconds'])} old)")

    report["verdict"] = severity.upper()
    report["findings"] = findings
    report["exit_code"] = EXIT_CODES[report["verdict"]]
    return report


def format_age(seconds):
    if seconds < 3600:
        return f"{seconds // 60}m"
    if seconds < 86400:
        return f"{seconds // 3600}h{(seconds % 3600) // 60:02d}m"
    return f"{seconds // 86400}d{(seconds % 86400) // 3600:02d}h"


def format_uptime(seconds):
    return format_age(seconds)


def render(report):
    lines = [
        f"canary-status - {PROJECT} @ {report['host']} (read-only)",
        f"VERDICT: {report['verdict']}",
        "",
        "services",
    ]
    if report.get("services_error"):
        lines.append(f"  ERROR: {report['services_error']}")
    for service in report.get("services", []):
        lines.append(
            f"  {service['service']:<18} {service['state']:<9} "
            f"{service['health']:<9} {service['status']}")
    lines.append("")
    lines.append("server (native status :7173)")
    status = report.get("status")
    if status:
        lines.append(
            f"  {status['players_online']} online (peak {status['players_peak']})"
            f" - uptime {format_uptime(status['uptime_seconds'])}"
            f" - protocol {status['client_protocol']}"
            f" - version {status['server_version']}")
    else:
        lines.append(f"  ERROR: {report.get('status_error')}")
    lines.append("")
    lines.append("endpoints")
    for name, probe in (report.get("endpoints") or {}).items():
        if probe.get("reachable"):
            detail = probe.get("status", "open")
            if name == "worldmap":
                detail = f"{detail} ({'offline' if probe.get('offline') else 'online'})"
            if name == "tcp_7172":
                detail = "open (challenge)" if probe.get("challenge") else "open (no challenge)"
            lines.append(f"  {name:<12} OK   {detail}")
        else:
            lines.append(f"  {name:<12} FAIL {probe.get('note', 'unreachable')}")
    lines.append("")
    lines.append("last S1 digest")
    digest = report.get("digest")
    if digest:
        verdict = digest["verdict"] or "unknown"
        lines.append(
            f"  {verdict} - {Path(digest['path']).name} "
            f"- {format_age(digest['age_seconds'])} ago")
    else:
        lines.append(f"  ERROR: {report.get('digest_error')}")
    if report["findings"]:
        lines.append("")
        lines.append("findings")
        lines.extend(f"  - {finding}" for finding in report["findings"])
    return "\n".join(lines)


def collect(args):
    services, services_error = collect_services()
    status, status_error = native_status(args.host, args.timeout)
    digest, digest_error = latest_digest(args.digest_dir)
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "host": args.host,
        "compose_project": PROJECT,
        "services": services,
        "services_error": services_error,
        "status": status,
        "status_error": status_error,
        "endpoints": collect_endpoints(args.host, args.timeout),
        "digest": digest,
        "digest_error": digest_error,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--host", default="127.0.0.1",
                        help="deployment host (default: 127.0.0.1)")
    parser.add_argument("--timeout", type=float, default=8.0,
                        help="per-probe timeout in seconds (default: 8)")
    parser.add_argument("--digest-dir", type=Path, default=DEFAULT_DIGEST_DIR,
                        help="S1 digest directory (default: ../wsl/runtime/digests)")
    parser.add_argument("--json", action="store_true",
                        help="emit the full report as JSON")
    parser.add_argument("--open", action="store_true",
                        help="open the world map in the default browser")
    args = parser.parse_args()

    report = evaluate(collect(args))
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(render(report))
    if args.open:
        worldmap = report["endpoints"].get("worldmap", {})
        url = f"http://{args.host}:8080/index.php/worldmap"
        if worldmap.get("reachable") and not worldmap.get("offline"):
            webbrowser.open(url)
            print(f"opened {url}")
        else:
            print(f"world map not reachable; did not open {url}")
    return report["exit_code"]


if __name__ == "__main__":
    sys.exit(main())
