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

## Schema v1.1 (B1 identity + B2 bridge/equivalence content)

`schema_version=v1.1` adds `canonical_identity_binding_v1` and
`evidence_scope_class`. Productive scope `PRODUCTIVE_CURRENT` requires
`verify_canonical_identity_binding_v1` (fail-closed). Legacy `schema_version=v1`
contract-test mechanics remain nonproductive. Canonical execution model class:
`SIMULATED_ECONOMICS_BRIDGE`. Residency: when Cap 2.3 gate disabled, declare
`residency_applicability=NOT_ENABLED_FOR_EVIDENCE_SCOPE`.

## B2 (CURRENT_OFFLINE_MD_BRIDGE_V1 + CURRENT_OFFLINE_DECISION_EQUIVALENCE_V1)

Increment B2 adds fail-closed verifiers for:

- `CURRENT_OFFLINE_MD_BRIDGE_V1.json` — semantic compatibility between CURRENT
  market-data semantics and `backtest.admissible_versioned_futures_dataset_v1`
  (no byte-identity claims).
- `CURRENT_OFFLINE_DECISION_EQUIVALENCE_V1.json` — row-wise decision parity with
  deterministic decision-input fingerprint recompute.

For `PRODUCTIVE_CURRENT`, `verify_canonical_identity_binding_v1` with `repo_root`
loads referenced attestation artifacts, verifies digests, and requires MD bridge +
decision-equivalence verifier PASS. This does **not** complete offline economic
evidence, enable discovery, or emit economic validity.

Comparison classes: `CONTRACT_TEST_MECHANICS`, `CONTROLLED_FIXTURE`,
`PRODUCTIVE_CURRENT` (no caller-side escalation).

## Productive completion (E2E proof chain)

`productive_offline_economic_completion_v1` produces a governed
`PRODUCTIVE_CURRENT` bundle: MD bridge, decision equivalence (replay delegate
vs offline replay), simulated economics metrics, WF/MC/stress domains, and
integrated index v1.1. `integrated_offline_economic_validity_adjudication_v1`
derives `ECONOMIC_VALIDITY_PASS` from verified evidence only (AUTHORITY=NONE).
Zero-trade outcomes may yield technical proof complete with economic policy FAIL.

## CURRENT sample-count policy (authoritative for PRODUCTIVE_CURRENT)

Owner: `ops.current_integrated_offline_economic_policy_v1`

Config: `config/ops/current_integrated_offline_economic_policy_v1.toml`

Integrated evidence binds `canonical_identity_binding_v1.economic_policy_reference_v1`
with a deterministic `policy_digest_sha256` (not a stub digest).

| Term | Meaning |
|------|---------|
| **TRADE** (qualifying) | One completed economic position round trip: FLAT → NONZERO EXPOSURE → FLAT |
| **ENTRY** | Exposure transition flat → nonzero; does **not** increment `trade_count` |
| **FILL** | Simulated execution event; does **not** increment `trade_count` |
| **PARTIAL REDUCTION** | Nonzero → smaller nonzero; stays within one open lifecycle |
| **REALIZED LEG** | PnL recognized on a reducing fill; tracked as `realized_leg_count` |
| **COMPLETED ROUND TRIP** | Lifecycle closed at flat; increments authoritative `trade_count` |

`minimum_trade_count = 50` means **50 completed economic round trips** for CURRENT
integrated offline qualification.

Reversal fills that cross through flat in one simulated action are treated as
close-then-open (complete lifecycle, then new lifecycle).

Metrics domain fields (non-exhaustive): `trade_count` (= completed round trips),
`completed_trade_count`, `entry_count`, `fill_count`, `realized_leg_count`,
`win_leg_count`, `loss_leg_count`, `winning_completed_trades`,
`losing_completed_trades`, `trade_count_semantic`.

STEP29M `economic_validity_policy_v1` / `config [validation] min_trades` are
**provenance reference only** for the numeric threshold 50 — not authority over
CURRENT semantics or adjudication binding.

## Artifacts

- Top-level index: `INTEGRATED_OFFLINE_ECONOMIC_EVIDENCE_V1.json`
- Domain artifacts referenced by provenance fields (no duplication of large payloads)

## Config

- `config/ops/integrated_offline_economic_evidence_v1.toml`
- `config/ops/current_integrated_offline_economic_policy_v1.toml`
- `canonical_evidence_relpath` defaults unset (discovery fail-closed)

This config file is **not** currently listed in
`IMPLEMENTATION_SURFACE_RELPATHS` for head-bound correctness. Adding it there
in a future increment will require a correctness reproof fixpoint (same pattern
as economic bundle rebind).

## Forbidden substitutions

Integrated verification rejects authority claims based solely on: 6h wallclock
soak, v1.1 bundle-only, B10 ranking robustness, STEP 29M status booleans, or
manual aggregate completion flags.
