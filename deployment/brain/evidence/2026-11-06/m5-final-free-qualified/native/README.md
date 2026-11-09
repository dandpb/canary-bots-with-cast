# native

## Overview
Package implementation for `deployment/brain/evidence/2026-11-06/m5-final-free-qualified/native`, providing component logic and data interfaces for native.

## Interface
- `ScriptedFake` (`[producer-driver.py:ScriptedFake]`)
- `QualificationObserverError` (`[producer-driver.py:QualificationObserverError]`)
- `AttestedFixture` (`[producer-driver.py:AttestedFixture]`)
- `forbidden` (`[producer-driver.py:forbidden]`)
- `current_revision` (`[producer-driver.py:current_revision]`)
- `validate_result` (`[producer-driver.py:validate_result]`)
- `prepare` (`[producer-driver.py:prepare]`)
- `start_database` (`[producer-driver.py:start_database]`)

## Invariants
- Validation assertion: `assert not subprocess.check_output(` (`[producer-driver.py]`)
- Validation assertion: `assert (
        native_build_contract(frozen, native_revisi` (`[producer-driver.py]`)
- Validation assertion: `assert frozen["database_image_id"].startswith("sha256:")` (`[producer-driver.py]`)
- Validation assertion: `assert (
        benchmark.fixture_hash(fixture_root / "fixt` (`[producer-driver.py]`)

## Side Effects
- None

## Verification
- Run: `pytest`
