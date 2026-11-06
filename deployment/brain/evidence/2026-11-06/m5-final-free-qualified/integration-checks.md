# Combined source checks after integrating main

PR25 head `8e6c5375849399eb4aaa738c8b64204423546c5c` was fast-forwarded in the isolated evidence worktree, then main `1f025f0ea7cd7f95e7602584aa666ba0de844bf9` was merged normally as `6f4ad88c34951189b544d857df60db6700fb9c79`. The merge had no textual conflict. This includes cleanup #51 and trial attestations #53; it does not change the producer source recorded by B.

Results on that combined source:

- Fixture/observer/source/goal guards: **67 tests passed** (`unittest`, 73.097 s).
- Attestations, subprocess cwd, benchmark horizon, pilot wrapper and benchmark: **77 tests passed** (`pytest`, 20.85 s).
- Ruff lint and format: passed for the three QA implementation files and two new offline verifiers.
- Strict mypy: passed for `src/canary_brain/benchmark.py` and `tools/m5_pilot.py`.
- Offline evidence verification: B replays 3296/5750 events; supply 207 events; prior current bundle 42 hashes plus 89 historical checksums, navigation 75 hashes, interrupted A 48 hashes. Their prior accepted/failed verdicts remain unchanged.
- Preservation: all **326 pre-existing evidence Git blobs** at head `8e6c5375` are unchanged, with working-byte SHA256 recorded in `previous-evidence-preservation.json`.

Representative commands, using the repository's Python test dependencies:

```bash
# Repository root
PYTHONPATH=deployment/brain/src:tests/fixture python -m unittest discover -s tests/fixture -p 'test_m5*.py'

cd deployment/brain
PYTHONPATH=src:. python -m pytest tests/test_m5_attestations.py tests/test_subprocess_cwd.py tests/test_benchmark_horizon.py tests/test_m5_pilot.py tests/test_benchmark.py -q
MYPYPATH=src python -m mypy --strict src/canary_brain/benchmark.py tools/m5_pilot.py
```

The first runtime test invocation used an incomplete import path and failed during collection; it was corrected to the `deployment/brain` working directory with `PYTHONPATH=src:.`, after which all 77 tests passed. No implementation fix was needed for that invocation error.

These checks used pure/disposable test fixtures and closed evidence files. They sent no provider request, accessed no credential/canonical ledger, launched no production stack and repeated no 30-minute run. They do not establish a paid comparison or human acceptance.
