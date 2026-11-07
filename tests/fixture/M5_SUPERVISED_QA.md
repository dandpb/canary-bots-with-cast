# Prospective free supervised QA (#72 remains open)

This launcher is for a fresh 1,800-second native/fake qualification, not a paid
campaign or historical supply-only probes. It does not authorize execution.
Old artifacts and producer snapshots must remain unchanged.

## Actual production activation interface

Combined base: main 3431b4046602875b161216ddb7be464eb4842f1a plus corrected native
integration c8b3878d3e576ff8ef1561cbb2614cb77532a349 (tree
09c0b5fe696c689a6de23bdd223bad262a99bc83). Native patch SHA-256:
556e3e524b14c1f69a8c006a231b6847cc211269b8e27d0c14e09ad6949c377a.

The harness uses runtime.Configuration.native_source_revision, the matching
Controller native_source_revision argument and SupervisedNative.durable_complete.
There is no marker to enable, and no harness-generated admission or fence packet.
A runtime lacking these integrated APIs fails before preparing resources.
The corrected sibling interface document is docs/design/native-supervised-harness-interface.md.

The production runtime owns admission nonce/retry, B/t0/D0/O0, peer socket identity,
native clock, first cutoff latch, contiguous committed coverage, fence nonce,
bounded close, durable proof and final seal. The harness calls runtime.run without
its own completion loop or stop event. Only its final run_stop/end verdict is
copied to stop.json. Missing/non-completed verdict fails. A completed verdict
also requires matching private admission, public admitted boundary, frozen native
horizon, terminal fence and post-close supervisor-native-qualified receipt in a
clean replay. No worker verdict or SQL save can move the scored window.

## Inputs (collect prospectively; never retrofit old evidence)

Set absolute paths:
- CANARY_M5_PRIVATE_ROOT, or caller-supplied TMPDIR: existing caller-owned private
  directory (no group/other permissions).
- CANARY_M5_QA: new child attempt root; prepare refuses to overwrite it.
- CANARY_M5_WORLD: immutable world under private root, outside attempt.
- CANARY_M5_NATIVE_BUILD: native binary/library directory under private root,
  outside attempt.
- CANARY_M5_NATIVE_SOURCE_REVISION: the actual clean native build's full source
  commit, independently attested by build/image receipts and runtime admission.

The manifest records source_revision for the clean harness checkout and
native_source_revision separately for the native build. Worker config and its
recording manifest both pin the latter, as the runtime API requires. Never label
a c8b3878d native binary with the later combined harness revision.

Use a clean committed source and its Python environment. The launcher uses
sys.executable and requires runtime imports from that same checkout. Binary hashes
are captured at preparation; native admission separately checks their source.
Rebuild/attest the base game image first. The inherited canary-party-qa:local
input is not proof of corrected source; preparation hash checks and native
admission remain required. Existing prepared manifests with another harness
revision/helper hash or missing native pin fail closed.

A sufficiently short shared private root is still required by native IPC:
directory <=80 characters and full AF_UNIX socket path <108 encoded bytes.
There is no automatic relocation. Offline tests use a live procfs fd alias
resolving to the exact attempt/socket directory; all actual files stay in TMPDIR.
That same-process test alias is not a container deployment recipe.

After independent integration/build/execution admission, entrypoints remain
m5_qa.py prepare and m5_qa.py native/fake. Do not run these during offline review:
they invoke Docker/game preparation. No world or binary inputs are generated here.

## Isolation, fake behavior and evidence

Configuration disallows credentials, gateways, operator endpoint, learning,
shared budget paths and pre-existing state/evidence. Production bookkeeping uses
only a new attempt-local worker.sqlite3. Credential reads, remote client/adapters,
reserve/settle and outside-Store paths are guarded. Zero inference rows are
required. Optional tracing is disabled; child environment contains only PATH,
PYTHONPATH, TMPDIR and private root. Real ledgers are never opened.

Fake mode now uses the production FakeProvider unchanged: it proposes continue.
For eligible party observations the arbiter selects/proposes continue, which is
a deliberate no-op and emits no native intent. For a solo idle observation whose
work filter removes continue, the proposal is rejected. The old scripted hunt/
resupply policy is not restored. These tests qualify wiring, not fake hunt
progression or equivalence to historical scripted runs; fake gameplay usefulness
remains an explicit prerequisite before any comparison claim.

#81 operation-time stop/SQL receipts and helper reconciliation remain intact.
#82 close behavior and #84 QA daily-save changes remain intact. Both successful
and failed synthetic attempts retain their DB/replay/stop artifacts. Runtime
cleans the worker socket, recorder thread, pending tasks, signal handlers and
lock; the test peer cleans its own socket/fd.

## Offline review evidence and remaining gates

test_m5_combined_supervision.py enters the actual runtime through m5_worker,
with real private AF_UNIX peer and fresh SQLite files. It asserts durable B/t0/D0/
O0, source pin, native B-through-terminal coverage, frozen XP/level, distinct fence,
no pre-close completed verdict, actual successful durable proof, after-flush seal
and cleanup. Negative cases include missing B, interior gap, wrong fence, peer
replacement and failed close, in native and fake modes. Synthetic capture clocks
jump 1,800 seconds; these seconds are not real elapsed QA time or gameplay.

Unit tests additionally reject a verdict-only stub without durable proof, missing
integration, unsafe paths/config, credentials/provider constructors, financial
operations and any inference row. No model endpoint is supplied.

Full server/engine build, matching binary/image attestation, independent combined
review, real QA admission/XP/SQL/resource evidence and an actual free isolated
30-minute native run are still outstanding. #72 stays open. No Docker, live
services, credentials, real ledger, production, push or merge was used to test
this adapter. Native integration files are frozen and unchanged by the adapter.
