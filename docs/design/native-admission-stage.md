# #72 native admission: stage 1

Base: f72ddc0477931b8f797b493ec181309114f10d77. No edits to #82's
recording/replay_cli/runtime/tests or #81's tests/fixture helpers.

The native dispatcher admits one nonce per world/bot session. It captures O0,
uses O0.captured_ms as t0 and snapshots cumulative deaths D0, then allocates
B=S+1 exactly once. A telemetry frame tagged with run_nonce (the run_started marker) enters the existing
#75 FIFO. The immutable reply includes nonce/world/bot/B/t0/D0/O0 and source
commit/dirty state. Retrying the same nonce returns the identical reply even
if the bot subsequently dies. Another nonce cannot replace it. No sequence
reset, extra queue, delivery renumbering, or accounting change.

Only a clean build with a known source commit is eligible. CMake refreshes the
shared generated identity before core/bot_engine compilation, including rebuilds
without reconfiguration; failed Git lookup yields unknown/dirty. The worker must
compare that identity against an externally pinned build; the self-reported
commit is not binary attestation. Runtime world changes (including reload or
process restart) invalidate admission. Bot removal or process death cannot
complete without a new final watermark; admission is never resumed across them.
Normal deaths retain the same session and advance the same FIFO counter.

The standalone verifier consumes validated admission, telemetry and observations
from the trusted peer. It requires every telemetry sequence from B through the
terminal watermark inclusive, a run_started frame matching admission, no native
loss/pending state, no time or death regression, and a real observation captured
at least 1,800,000 ms after t0. Receipt time has no role in completion. A reply
cannot stand in for delivery of B. Failure is sticky. Exact retransmissions are
idempotent; altered duplicates fail. Death delta is measured from D0.

## Remaining gates (NO-GO for qualification)

This stage does not enable supervised worker admission. After #82: validate peer
socket and capabilities before any provider/intent/reflection; persist admission
and O0 before opening decisions; route validated packets through this verifier;
detect native bot removal/unavailability independently of a still-live status publisher;
seed recorder coverage at B; require durable contiguous committed coverage at
seal, #82 successful close/flush, and existing negative-stop/accounting precedence.
Freeze scoring on the first native horizon observation, close model/reflection
admission, and bound terminal drain/watchdogs. Persist failure on worker crash;
a standalone in-memory verifier is not crash recovery or a durable receipt.

The legacy worker remains unchanged and still must not be used to claim this
contract. The verifier has an 8192-frame hard limit and an independent
8192-observation fingerprint limit; exceeding either fails closed. Status faults
are sticky even before the horizon. Observation fingerprints include O0 and
compare full validated payloads, allowing exact retransmissions while rejecting
conflicts (including older observations).

Full game compilation/loader reload, integration pressure/death/rebind/crash tests,
independent review, supervised harness and isolated free native 30-minute QA
remain required. No deployment, provider calls, campaigns or reused claims are
authorized by this patch. Tests use newly generated data only.
