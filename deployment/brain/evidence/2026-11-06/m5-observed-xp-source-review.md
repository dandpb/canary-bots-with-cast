# Timed qualification evidence and source checks

Independent static review compared application `1e25dc174` with main `92e0084db`.
The two active final free runs retain application `1e25dc174` and native build
`d43050147`. This follow-up was developed in a different worktree; it changes no
active source, fixture, image, state, recording or service.

## Standards

No documented blocking violation was found. The reviewer identified one possible
P3 duplication: the timed and low-stock drivers separately attest image/binary
identities. This maintenance concern is retained; refactoring that shared shape
is unnecessary for accepting the current evidence and would expand the change.

## Spec

Two P2 acceptance/attribution gaps were found and corrected:

1. The old `positive_xp_persisted` compared saved XP only with the pre-start DB.
   DB100, first observed200, last observed200 and saved200 could pass despite no
   XP during the observed horizon. The new `positive_xp_observed` also requires
   integer first/last XP, a positive observed delta and agreement with the replay
   summary. Persistence remains independently mandatory. First XP and observed
   delta are included in the evidence. Genuine startup XP followed by positive
   observed progress is still accepted.
2. The timed driver attested Git HEAD of its own root without verifying imported
   worker modules. A driver in A with `PYTHONPATH=B/src` could label B's runtime
   as A. It now rejects missing or foreign `runtime.py`/`benchmark.py` sources
   before reading Git status/revision. A dirty matching checkout remains rejected.

The recorded launcher already explicitly sets `PYTHONPATH` to the frozen source
and checks its clean revision/driver hashes. The review does not establish that
the active runs imported a foreign runtime. It also does not establish zero XP
in those runs: their positive observed deltas are visible in read-only checkpoints.
After shutdown their preserved raw evidence must be independently reevaluated
using the corrected acceptance code, with both producer and evaluator revisions
reported. Do not silently replace their original qualification files or claim
that the later driver guard executed in the earlier process.

## Validation

Before the fix, the new tests reproduced nine failing subcases: startup-only XP
in native/fake, negative/missing/inconsistent observed XP and missing/foreign
runtime imports. After the fix, all40 directed tests passed, including the
existing low-stock contract and real signal/cleanup tests. Ruff lint/format
passed on the four affected Python files.

```sh
PYTHONPATH=deployment/brain/src:tests/fixture python -m unittest \
  test_m5_qualification_gates test_m5_current_source test_m5_current_lowstock -v
```

No provider credentials, paid inference, production changes or scored campaign
were used. These are qualification guards, not evidence of a model ranking,
new live gameplay, or paid admission.
