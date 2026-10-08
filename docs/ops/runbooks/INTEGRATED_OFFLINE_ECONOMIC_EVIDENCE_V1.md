# INTEGRATED_OFFLINE_ECONOMIC_EVIDENCE_V1

```text
status: INCREMENT_A_CONTRACT_ONLY
capability: INTEGRATED_OFFLINE_ECONOMIC_EVIDENCE_V1
owner: ops.integrated_offline_economic_evidence_v1
authority_effect: NONE
```

Increment A establishes schema, domain reference contracts, fail-closed verifiers,
and config-bound discovery. It does **not** produce productive offline-economic
evidence and does **not** wire adjudication or economic-validity emission.

Reference verification compares `implementation_surface_digest_sha256` and
`config_digest_sha256` against authoritative verifier context (head-bound
implementation surface digest and this capability config digest). Missing
expected binding values fail closed.

## Schema v1.1 (B1 identity)

`schema_version=v1.1` adds `canonical_identity_binding_v1` and
`evidence_scope_class`. Productive scope `PRODUCTIVE_CURRENT` requires
`verify_canonical_identity_binding_v1` (fail-closed). Legacy `schema_version=v1`
contract-test mechanics remain nonproductive. Canonical execution model class:
`SIMULATED_ECONOMICS_BRIDGE`. Residency: when Cap 2.3 gate disabled, declare
`residency_applicability=NOT_ENABLED_FOR_EVIDENCE_SCOPE`.

## Artifacts

- Top-level index: `INTEGRATED_OFFLINE_ECONOMIC_EVIDENCE_V1.json`
- Domain artifacts referenced by provenance fields (no duplication of large payloads)

## Config

- `config/ops/integrated_offline_economic_evidence_v1.toml`
- `canonical_evidence_relpath` defaults unset (discovery fail-closed)

This config file is **not** currently listed in
`IMPLEMENTATION_SURFACE_RELPATHS` for head-bound correctness. Adding it there
in a future increment will require a correctness reproof fixpoint (same pattern
as economic bundle rebind).

## Forbidden substitutions

Integrated verification rejects authority claims based solely on: 6h wallclock
soak, v1.1 bundle-only, B10 ranking robustness, STEP 29M status booleans, or
manual aggregate completion flags.
