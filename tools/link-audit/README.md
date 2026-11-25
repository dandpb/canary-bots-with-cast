# Link Audit Evidence Extractor (`tools/link-audit`)

## Overview
Contains `extract-link-audit-evidence.ps1`, a Windows PowerShell script that extracts MSVC linker, library, OpenSSL, Protobuf, `.map`, `.rsp`/`.tlog`, artifact size, and `vcpkg_installed` evidence from link-audit build directories.

## Interface
- `extract-link-audit-evidence.ps1` (`[extract-link-audit-evidence.ps1:InputDir]`): Accepts mandatory `-InputDir` plus optional `-OutputDir` (defaults to `<InputDir>/link-audit-extract`) and `-VcpkgInstalled`.

## Invariants
- Excludes `$OutputDir` when scanning `$InputDir` recursively for `*.log`/`*.txt` so re-running into a nested output directory does not self-ingest prior outputs (`[extract-link-audit-evidence.ps1]`).
- Halts immediately on errors (`$ErrorActionPreference = "Stop"`) and throws if `-InputDir` does not exist (`[extract-link-audit-evidence.ps1]`).

## Side Effects
- Creates `$OutputDir` and writes extracted UTF-8 evidence reports (`existing-logs-interesting-lines.txt`, `map-libs.txt`, `map-openssl-symbols.txt`, `map-protobuf-symbols.txt`, `link-metadata-interesting-lines.txt`, `artifact-sizes.txt`, `vcpkg-largest-files.txt`) (`[extract-link-audit-evidence.ps1]`).

## Verification
- Run on Windows PowerShell: `pwsh -File tools/link-audit/extract-link-audit-evidence.ps1 -InputDir <audit-dir>`.
