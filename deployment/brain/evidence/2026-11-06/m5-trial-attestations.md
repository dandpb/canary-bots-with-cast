# M5 automatic trial attestations

Refs #10. Scope: wrapper-only metadata capture, before each scored game starts
and after its canonical teardown. No worker/game/provider configuration, trial
schedule, TTL, price, budget, financial authority or retry behavior changes.
The implementation builds on the stable-cwd #49 head346c7d51827b1def14f29fc4cf6c8551b743de87.

## Required behavior

Capture real game/database IDs and images, exact project/service labels,
unpublished host ports, essential bind mounts and one internal project network
before observations can trigger the worker API. Unprovable metadata must not
become images_verified. After canonical down, inspect resources for that exact
project; only a successful down and zero remaining containers/networks can set
resources_cleaned. Preserve failure/observer evidence and propagate errors.
Do not query Config.Env, authentication headers or full inspect, export a ledger
copy, perform broader deletion, or add retries.

## Resulting behavior

- The game is created without start, both containers/network are inspected using
  field-specific Docker templates, then the exact created service is started.
  Running IDs/network are checked again. Before-start verification prevents
  model calls from preceding the image/scope gate.
  Every already-running container, including the database, must have the owned
  NetworkID and endpoint even at the pre-start gate. Mount expectations are
  anchored to canonical trial/world paths, independently of mutable Compose.
- Actual safe metadata is captured in0600 per-trial trial-attestation.json and
  aggregate game/trial-attestations.json. The aggregate trials map is keyed by
  canonical run_id and can be passed directly to m5_report.py --attestation.
- Canonical DockerFixture.close still owns one project-scoped down. Subsequent
  inspection only lists/reads exact-project resources, never deletes leftovers.
  Failure, timeout or leftover produces resources_cleaned false and raises.
- Selected labels and mount fields are rebuilt from an allowlist. Only failure
  type/stage is persisted; exception messages, Env and AuthHeader are excluded.
  Docker metadata queries have cwd=/ and20-second timeouts. Existing wrapper
  preflight inspect calls also gain bounded timeouts.
- Failed attempts retain captured admission/input bytes, execution results and
  the canonical-volume lease release behavior. No campaign admission is enabled.

## Offline validation

Tests use an in-memory Docker fake and temporary files/SQLite from the existing
admission fixture. No real daemon/container, production ledger, credential or
provider is contacted. Cases cover pre-start ordering, real-image mismatch,
foreign labels, host ports, altered mount, external network, changed container
ID, active/foreign leftovers, close failure, inspection timeout, redaction,
observer+cleanup errors, input capture and lease release.
Independent review reproduced two initial P2 cases (running database in a
different network; matching foreign mounts in both Compose and actual metadata).
Both are now rejected before game start by dedicated regressions.

CLI semantics were checked against Docker's official
[create reference](https://docs.docker.com/reference/cli/docker/compose/create/)
and [start reference](https://docs.docker.com/reference/cli/docker/compose/start/):
creation does not start the game; start operates on existing containers and can
wait for healthy services.

Run from stable cwd / with PYTHONPATH containing deployment/brain,
deployment/brain/src and the installed development-tool directory:

```sh
python -m pytest -q /absolute/source/deployment/brain/tests/test_m5_attestations.py \
  /absolute/source/deployment/brain/tests/test_m5_pilot.py
python -m ruff check --no-cache --config /absolute/source/deployment/brain/pyproject.toml \
  --config "src=['/absolute/source/deployment/brain/src']" \
  /absolute/source/deployment/brain/tools/m5_pilot.py \
  /absolute/source/deployment/brain/tests/test_m5_attestations.py \
  /absolute/source/deployment/brain/tests/test_m5_pilot.py
python -m mypy --cache-dir /tmp/m5-attestation-mypy-cache \
  --config-file /absolute/source/deployment/brain/pyproject.toml \
  /absolute/source/deployment/brain/tools/m5_pilot.py
```

Live Docker behavior and the paid campaign still require the independent gates.
The external candidate admission remains false and final source/hash approvals
remain null. Existing frozen QA/output files were not changed by this PR.
