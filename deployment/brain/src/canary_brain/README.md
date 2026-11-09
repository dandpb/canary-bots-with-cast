# canary_brain

## Overview
Package implementation for `deployment/brain/src/canary_brain`, providing component logic and data interfaces for canary_brain.

## Interface
- `Participant` (`[benchmark.py:Participant]`)
- `Experiment` (`[benchmark.py:Experiment]`)
- `DockerFixture` (`[benchmark.py:DockerFixture]`)
- `configured` (`[benchmark.py:configured]`)
- `distinct` (`[benchmark.py:distinct]`)
- `file_hash` (`[benchmark.py:file_hash]`)
- `fixture_hash` (`[benchmark.py:fixture_hash]`)
- `preflight` (`[benchmark.py:preflight]`)
- `TelemetryTail` (`[benchmark_stops.py:TelemetryTail]`)
- `Stops` (`[benchmark_stops.py:Stops]`)
- Subdirectory [`./dashboard/README.md`](./dashboard/README.md) - Sub-package for dashboard

## Invariants
- Validation assertion: `assert target is not None` (`[benchmark.py]`)
- Validation assertion: `assert server.server is not None` (`[replay_cli.py]`)
- Validation assertion: `assert (
                                native is not None
` (`[runtime.py]`)
- Validation assertion: `assert c.roster is not None` (`[supervised_native.py]`)
- Validation assertion: `assert c.benchmark_stops is not None` (`[supervised_native.py]`)
- Validation assertion: `assert c.recorder is not None and c.benchmark_stops is not N` (`[supervised_native.py]`)

## Side Effects
- None

## Verification
- Run: `pytest`
