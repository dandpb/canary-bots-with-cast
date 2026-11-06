# Initial setup documentation validation

Validated on2026-11-06 against main `5e0be6ce811ff2e808ca0072cb388355313108b0`.
Daniel requested documentation covering the initial setup of the replay and
benchmark integration. No application runtime was changed and no paid call made.

The Portuguese guide covers new/existing WSL installs, image prerequisites,
LiteLLM UI/PostgreSQL, four distinct credential roles, named OpenAI/Gemini routes,
worker migration, the existing monthly ledger, recording, isolated experiment
admission, deadlines, offline archives/video, backup and temporary cleanup.
Root/brain/WSL documentation links to it. The API-only standalone recipe is
distinguished from the WSL UI deployment. Historical image labels/active profiles
are no longer presented as proof of the current runtime.

Both JSON worker/experiment templates now reference the existing reference
deployment's `state.sqlite3` ledger, rather than suggesting a new budget file.
Operator-specific mounts and canonical authority must still be verified before
using any template. A named-credential gateway example has explicit aliases,
unique deployment IDs, retry0 and no plaintext credentials.

Checks executed without applying Compose services:

- Shell syntax of all13 guide Bash blocks.
- Generated temporary gateway files; Compose `config --quiet` passed.
- Executed the credential-client snippet twice with disposable generated
  internal keys: contents preserved, mode0600, values never printed.
- Pydantic Configuration/Experiment schema checks for the modified examples;
  `validate_policy` accepted the two named routes.
- Relative links and heading anchors in the guide resolved.
- Actual offline CLI demo, list, summary, export, reimport and HTML report passed.
- Actual FFmpeg timelapse and JSON sidecar were generated offline.
- A temporary loopback replay server returned200 and was terminated in finally.
- Diff check passed. No temporary Docker container was created.

Private validation artifacts:
`/home/daniel/canary-maintenance/replay-docs-qa-20261106T095416Z`.
Final guide recheck after clarifying shell working directories:
`/home/daniel/canary-maintenance/replay-docs-qa-20261106T095538Z`.
These checks qualify documentation examples and the offline path. They do not
qualify a new game build, complete benchmark fixture or paid campaign.
