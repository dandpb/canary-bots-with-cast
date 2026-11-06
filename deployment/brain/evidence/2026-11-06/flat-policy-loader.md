# Flat LiteLLM policy import/startup regression

Base: main `b612057ce766ea937eea1fa23d81fcff587fbf4b` (#37).
The isolated deployment failed before readiness because LiteLLM1.108.0's
`litellm.proxy.types_utils.utils.get_instance_fn` loads
`gateway_policy.authenticate` with `spec.loader.exec_module` without registering
that flat module in `sys.modules`. Deferred dataclass field annotations then
caused dataclasses `_is_type` to access `None.__dict__` (also reproduced on3.12).
Package-qualified import tests had registered modules and did not expose it.

The sole runtime change removes `from __future__ import annotations` from the
policy. All its annotations already resolve in declaration order on Python3.11+;
there is no forward reference requiring deferral. Dispatch/credential/price
behavior is unchanged.

The new stdlib regression failed on the base with the same AttributeError,
then passed after the two-line removal.43 policy/auth/SDK-usage directed tests,
Ruff and strict mypy for the changed module passed.

`gateway_flat_import_smoke.py` also invoked the exact vendor loader and started
a new real proxy with the flat config/file layout. Only readiness was queried;
no inference, credential DB or running service was accessed:

```sh
docker run --rm --network none -e LITELLM_LOCAL_MODEL_COST_MAP=True \
  -v /mnt/e/Development/tibia/.scratch/gateway-flat-loader-fix-20261106:/source:ro \
  --entrypoint python \
  ghcr.io/berriai/litellm:v1.108.0@sha256:b59b9fd52a67891be4e8dae09ddd4e6c9265e9a8cb3f25f8dd73fbabe7659965 \
  /source/deployment/brain/tools/gateway_flat_import_smoke.py
```

Observed JSON: Python3.13.18, vendor flat loader=true, module still unregistered,
real proxy health200, inference calls0. The proxy was terminated in finally and
the disposable container removed. This qualifies import and startup only;
private credential/bootstrap and provider conformance remain separate gates.
