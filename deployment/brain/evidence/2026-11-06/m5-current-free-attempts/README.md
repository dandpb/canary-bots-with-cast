# Current free attempts — paid pilot blocked

Append-only evidence added after the original PR25 head. The native attempt completed; the scripted fake stopped stalled before the requested horizon. Overall qualification remains **not accepted** and **paid pilot not admitted**.

## Current free qualification: not accepted

Native completed; the scripted fake failed on stagnation before 30 minutes. This bundle does not admit a paid pilot. Original files/identities were preserved.

| Participant | Requested s | Sampled span s | Worker elapsed s | Worker observed s | Status/reason | Saved XP | Gain | Deaths/gaps/inference |
| --- | ---: | ---: | ---: | ---: | --- | ---: | ---: | --- |
| native | 1800 | 1800.493 | 1800.513543 | 1800.452832 | completed/completed | 107149 | +8349 | 0/0/0 |
| fake | 1800 | 1508.244 | 1508.715815 | 1508.565188 | failed/stalled | 100793 | +1993 | 0/0/0 |

## Evidence and interpretation

- Same fixture/map/game/database/binary identities, retained in qualification-consolidated.json and per-run attestations. Worker/driver source c9e447c500d1c245e7ea3736934eacfda0b5d445; original driver SHA b3039ab8ce70d6fb2ea06aadcde10be37969a9f3daca1f983cf22d1434dab060.
- Native run ID: m5-current-native-17b62eabb7:native:0. Its strict evidence consistency check passed, without admitting the pair or paid pilot.
- Fake run ID: m5-current-fake-d6226a4777:fake:0. Strict free qualification correctly reports qualification_not_completed; its interrupted horizon is never normalized to 1800 seconds.
- Native phase parsing uses hunt.phase, not outer state. The ordered patrol→leave→resupply→patrol chain is recorded separately; an actual NPC purchase is not asserted.
- Fake return_route_unavailable occurs in the replay; see fake/return-failure-events.json (including event 3873 at t1266733 ms). It is an observed failure preceding the terminal stalled stop, not a proven root cause.
- Metrics v2 reports fake stalled_ms=0 under narrower sample observability conditions. This does not override the authoritative supervisor stop reason stalled.
- Timeline span is measured between first/last samples; full recording envelope includes lifecycle boundaries and must not be used to inflate the scored horizon.
- No deaths, interventions, recording gaps or inference requests observed in either run. Zero API cost is supported by empty offline QA ledgers, not by creating/copying a paid authority.
- Human interventions were zero in both runs. Automatic recovery requests were native 0 / fake 1; the fake recovery requested a hold and a new choice, without teleportation, and did not prevent its later stalled stop.
- Both runtime image inspections captured running scoped containers with no published ports; later scoped inspections show no owned containers/networks remain. Bind evidence was retained.
- Diagnostic attempts and a future repair/rerun need new identities and separate reports. This failed fake remains part of the outcome history.

## Reproduce the offline review

Use tools/m5_report.py from reporter revision fd9e820b (or a reviewed successor) with the current Python package. Run from the repository's `deployment/brain` directory with the package dependencies installed. All commands below are offline:

```bash
PYTHONPATH=src python tools/m5_report.py --recording /path/to/bundle/native/native.replay.zip --experiment /path/to/bundle/native/experiment.json --trials /path/to/bundle/native/trials.json --ledger /path/to/bundle/native/offline-ledger-export.json --output /path/to/new-native-review --require-completed
PYTHONPATH=src python tools/m5_report.py --recording /path/to/bundle/fake/fake.replay.zip --experiment /path/to/bundle/fake/experiment.json --trials /path/to/bundle/fake/trials.json --ledger /path/to/bundle/fake/offline-ledger-export.json --output /path/to/new-fake-review --require-completed
```

Expected exit: native 0; fake 2 with qualification_not_completed. Use a new output directory; do not overwrite earlier reviews.

source-sha256.json preserves original bytes provenance. checksums.json covers published artifacts; ZIP internal integrity was validated by fresh import. No game/map/native binaries, private env files or whole ledgers are included.

Native phase timestamps retain the status observer elapsed clock; they are not substituted for replay t_ms or supervisor clocks.

The fake did perform useful earlier work: three confirmed hunt_progress outcomes and 65 confirmed objective defeats were recorded. Its later return/stall failure does not erase the +1993 XP, nor does that earlier progress satisfy the missing 1800-second horizon or a completed resupply/return cycle.

## Publication and preservation

Historical 2026-11-05 artifacts/index/verification were left byte-for-byte unchanged, including 89 files covered by their original checksums. historical-preservation.json records their unchanged Git blobs.

These current artifacts are derived public copies. Absolute private prefixes were replaced with descriptive path labels; public-provenance.json links every copy to the audited private bundle hash. Never interpret an original pre-label hash as the public checksum; use checksums.json for this directory. The two replay ZIPs remain byte-for-byte unchanged.

Independent audit current_evidence_audit reported zero findings: 39 source-bundle checksums, 27 original source hashes, fresh archive imports (native 3301 / fake 4189 logical events), strict native exit 0 and fake exit 2. This audit does not turn the failed fake attempt into a completed one.

Driver source for both attempts is c9e447c500d1c245e7ea3736934eacfda0b5d445; it is not relabeled as newer main. The current C9 driver/harness source will be published separately under coordination. No low-stock 64c8a48e diagnostic is included here.

The consolidated `no_containers_started` flag describes only this offline review/export step. The original game attempts did start isolated containers; their running image and later cleanup inspections are retained.

Run `python verify_bundle.py` from this directory for the stdlib-only hash, archive and outcome check. Add `--repository /path/to/checkout` to recheck all 89 historical file hashes and Git blobs. It writes no files and calls no provider, Docker service or game database. This is evidence verification, not qualification acceptance.
