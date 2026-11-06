# MASTER_V2 Canonical Volatility Default Quarantine v1

---
docs_token: DOCS_TOKEN_MASTER_V2_CANONICAL_VOLATILITY_DEFAULT_QUARANTINE_V1
STATUS: CAPABILITY_AVAILABLE
scope: quarantine productive untyped volatility defaults and strategy floors; reuse C1
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
RUNTIME_WIRING: false
RUNTIME_PRODUCER_CUTOVER: false
PARAMETER_EFFECT: false
PARAMETER_RESEARCH: false
TRADING_LOGIC_EFFECT: false
HARD_STOP: true
---

> **Non-authorizing C2 quarantine.** Closes productive silent defaults
> (`0.2` / `0.02` / `1.0`) and the strategy-authority floor (`1e-9`) outside the
> C1 typed-binding path. Does **not** redefine those numeric identities, invent
> estimators, adapters, semantics, runtime wiring, or parameter recommendations.
> Does **not** alter survival / suitability volatility surfaces.

## Machine summary

```
CAPABILITY_ID=MASTER_V2_CANONICAL_VOLATILITY_DEFAULT_QUARANTINE_V1
QUARANTINE_OWNER=trading.master_v2.canonical_volatility_default_quarantine_v1
TYPED_TRANSPORT_MODEL=A
C1_REUSED=true
SINGLE_QUARANTINE_AUTHORITY=true
SECOND_VALIDATION_AUTHORITY=false
SECOND_ADAPTER_AUTHORITY=false
SECOND_ESTIMATOR=false
SECOND_SEMANTICS_AUTHORITY=false
MV2_FALLBACK_0_2_ADMISSIBLE=false
FLOOR_POLICY=NONE
RUNTIME_WIRING=false
RUNTIME_PRODUCER_CUTOVER=false
PARAMETER_RESEARCH=false
LIVE_AUTHORIZATION=false
HARD_STOP=true
```

## Quarantine authority

Exactly one policy owner:

`trading.master_v2.canonical_volatility_default_quarantine_v1`

C1 remains sole authority for typed validation, typed-to-legacy adaptation, typed
identity digests, and typed evidence provenance.

## Typed vs legacy path

```
Typed:
  CanonicalVolatilityEstimateV1
    → C1 validate_canonical_volatility_estimate_v1
    → C1 adapt_canonical_volatility_estimate_to_legacy_float_v1
    → float consumer

Legacy:
  Explicit legacy float
    → C2 quarantine_legacy_volatility_input_v1
    → admitted disposition + quarantine digest / evidence
    → float consumer

Forbidden:
  Missing / implicit → 0.2 / 0.02 / 1.0 / 1e-9 → float consumer
  Unknown / zero / invalid → numeric floor → float consumer
```

## Value treatment (identities unchanged)

| Value | Prior behavior | C2 behavior |
|---|---|---|
| `0.2` | silent historical bind fallback | missing rejected; explicit bar value quarantined |
| `0.02` | implicit replay rules default | explicit `LEGACY_EXPLICIT_REPLAY_DEFAULT` quarantined + digest |
| `1.0` | `DynamicScopeRules` constructor default | default removed (`None`); bare productive use unmaterialized |
| `1e-9` | `max(snapshot.vol, 1e-9)` strategy floor | removed; `floor_policy=NONE` enforced; zero/unknown fail-closed |

No historical claim that `0.2` or `0.02` is economically correct or incorrect.

## Evidence / digest contract

Admitted productive legacy paths emit:

- `quarantine_contract_version`
- `disposition`
- `semantic_name`
- `legacy_value`
- `source_kind`
- `explicit_or_implicit`
- `fallback_or_default_or_floor`
- `source_digest`
- `quarantine_digest`
- `typed_binding_present`
- `canonical_estimate_present`
- `authority_effect`
- `rejection_reason`

Invariants:

- quarantine digest never replaces C1 typed estimate / adaptation / binding digests
- legacy defaults never appear as `canonical_volatility_estimate`
- `fallback_used=true` remains rejected on the typed path

## Fail-closed matrix

| Condition | Disposition |
|---|---|
| Missing volatility | `REJECTED_UNKNOWN` |
| Implicit / silent default | `REJECTED_SILENT_DEFAULT` |
| Non-finite / negative / zero | `REJECTED_INVALID` |
| Typed vs legacy mismatch | `REJECTED_POLICY_CONFLICT` |
| Strategy authority floor | `REJECTED_POLICY_CONFLICT` / `FLOOR_FORBIDDEN` |
| Explicit legacy / fixture | `EXPLICIT_LEGACY_QUARANTINED` / `TEST_FIXTURE_ALLOWED` |
| Typed bound | `TYPED_BOUND` (via C1) |

## Gaps closed (assessment G1–G15)

Closed by C2:

- `G1_SILENT_FALLBACK_PATH_EXISTS`
- `G2_UNTYPED_PRODUCTIVE_DEFAULT_EXISTS`
- `G4_FALLBACK_EVIDENCE_MISSING`
- `G5_DEFAULT_DIGEST_MISSING`
- `G9_DEFAULT_CONFLICT_EXISTS`
- `G10_NUMERIC_FLOOR_SEMANTIC_LEAK_EXISTS`
- `G11_TEST_PRODUCTION_SEMANTICS_CONFLATED`
- `G12_CONFIG_CODE_DEFAULT_DRIFT_EXISTS`
- `G13_SPEC_CODE_DEFAULT_DRIFT_EXISTS`
- `G14_UNKNOWN_VOLATILITY_FAILS_OPEN`

Remaining:

- `G3_UNTYPED_EXPLICIT_LEGACY_STILL_ADMISSIBLE`
- `G6_UNIT_AMBIGUITY_ON_EXPLICIT_LEGACY`
- `G7_HORIZON_AMBIGUITY_ON_EXPLICIT_LEGACY`
- `G8_ESTIMATOR_AMBIGUITY_ON_EXPLICIT_LEGACY`
- `G15_COMPETING_NON_ALIAS_PRODUCERS`
- C1 remaining producer / max-age / wiring gaps
- C3 typed runtime producer assessment

## Non-goals

- Runtime producer cutover
- Runtime wiring / Double Play hot-path cutover
- Parameter research or value redesign
- Survival / suitability volatility redefinition
- Composition / entry / exit / state machine redesign
- Second estimator / adapter / validation / semantics authority
- Live / testnet / order authorization

## Owners (reuse-before-new)

| Surface | Owner |
|---|---|
| Quarantine policy | `canonical_volatility_default_quarantine_v1` |
| Typed validation / adapter | `canonical_volatility_estimate_typed_consumption_contract_v1` |
| Binding / typed digests | `canonical_volatility_binding_and_provenance_transport_v1` |
| Semantics | `canonical_volatility_estimate_feature_contract_v1` |
| Estimator | `canonical_volatility_estimate_materializer_v1` |
| Tests | `tests/trading/master_v2/test_canonical_volatility_default_quarantine_v1.py` |
