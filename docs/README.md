# Documentation & Maintenance Scripts (`docs`)

## Overview
Contains Doxygen/LDoc documentation templates (`Doxyfile.in`, `config.ld.in`), architecture design notes (`design/`), and standalone Python refactoring utilities (`python-scripts/`).

## Subdirectories & Boundaries
- `design`: Architecture & operational design notes (`design/fixture-persistence-witness.md`, `design/native-admission-stage.md`, `design/native-admission-validation.md`, `design/native-supervised-harness-interface.md`).
- `python-scripts`: [`./python-scripts/README.md`](./python-scripts/README.md) - Standalone Python utilities for batch-refactoring Lua monster callbacks and C++ `LuaScriptInterface` and `#include` conventions.
- [Consolidated Canary EGM review](reviews/2026-11-19-egm/consolidated_review_report.md) covers the server features, documentation and implementation readiness.
