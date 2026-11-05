# LiteLLM grouped with the WSL stack

Daniel authorized adding LiteLLM to the existing `canary-bots-wsl` Compose
project and removing stopped containers no longer in use. The local deployment
is `/home/daniel/canary-bots-wsl/deployment/wsl/compose.yaml`.

## Deployment

Added the optional `gateway` profile and `litellm` service to the existing Compose
file. It shares the project's network and appears as
`canary-bots-wsl-litellm-1`. Only loopback port4000 is published. The optional
profile does not change ordinary database/game/web startup. No dependency or
provider setting of the existing worker was changed.

`setup-gateway.py` creates missing local policy/internal-key/provider-env files
with mode0600 and preserves every existing file. Temporary-directory verification
checked a second invocation preserves keys and operator-edited configuration.
The bootstrap policy has zero model deployments, so this is not inference/account
qualification and does not initiate paid calls.

The service was started with `up -d --no-deps --no-build litellm`, then only that
service was rebuilt/recreated for the authentication correction below. Existing
game, worker, database and web container IDs and StartedAt values stayed identical.
Readiness returned200 and Docker health was healthy. The gateway and existing
worker share the project network.

## Missing-key regression

An actual unauthenticated POST initially returned500: LiteLLM passed `None` into
the custom authentication function, which called `removeprefix` on it. Its error
handler then encountered an optional Prisma dependency. The custom function now
rejects absent/non-string credentials before comparing the internal key.

Thirteen gateway/authentication tests passed, including missing, empty and wrong
keys. Lint/format and compilation passed for changed Python files. Real local
HTTP verification after rebuilding produced:

- readiness200;
- absent credential401;
- valid internal credential with zero configured models400;
- zero provider credentials read or paid calls.

The rebuilt local image ID is
`sha256:6b2498fa2e23faa4a23a99420fc47bc77a87f8e19e493fac80ff02e3ddb3ff48`.
LiteLLM remains version1.108.0. The previous pinned QA image is retained; this
deployment does not relabel old benchmark evidence. OpenAI/Gemini selection,
provider credentials and real-account qualification remain separate work.

## Container cleanup

Removed27 explicitly identified stopped QA/build/demo/obsolete containers,
including the old ai-memory3.1 rollback container and welcome-to-docker. Each was
rechecked as stopped immediately before `docker rm`, with no force or volume
deletion. Logs and metadata were retained privately under
`/home/daniel/canary-maintenance/container-cleanup-20261105T205225Z`.

All five containers active before cleanup remained running. After adding the
gateway, six active containers remain: database/game/brain/web/litellm in
`canary-bots-wsl` plus current `ai-memory`. No images, volumes or application data
were deleted. The workspace's canonical AGENTS.md now records grouping related
runtime services and cleaning temporary containers after use.

Deployment backup/verification is retained privately under
`/home/daniel/canary-maintenance/litellm-grouping-20261105T205514Z`.
No runtime env, internal key or provider credential is included in this change.
