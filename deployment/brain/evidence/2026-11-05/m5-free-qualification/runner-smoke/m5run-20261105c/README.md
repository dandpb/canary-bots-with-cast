# m5run-20261105c

## Overview
Package implementation for `deployment/brain/evidence/2026-11-05/m5-free-qualification/runner-smoke/m5run-20261105c`, providing component logic and data interfaces for m5run-20261105c.

## Interface
- `AttestedFixture` (`[frozen-driver.py:AttestedFixture]`)
- `forbidden` (`[frozen-driver.py:forbidden]`)
- `prepare` (`[frozen-driver.py:prepare]`)
- `start_database` (`[frozen-driver.py:start_database]`)

## Invariants
- Validation assertion: `assert actual == database` (`[frozen-driver.py]`)
- Validation assertion: `assert run["status"] == "completed" and not run["incomplete"` (`[frozen-driver.py]`)
- Validation assertion: `assert max(samples) - min(samples) >= 10000 and requests == ` (`[frozen-driver.py]`)

## Side Effects
- None

## Verification
- Run: `pytest`
