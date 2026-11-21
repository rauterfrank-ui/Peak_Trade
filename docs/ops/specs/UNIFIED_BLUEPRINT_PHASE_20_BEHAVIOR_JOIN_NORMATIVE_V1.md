---
docs_token: DOCS_TOKEN_UNIFIED_BLUEPRINT_PHASE_20_BEHAVIOR_JOIN_NORMATIVE_V1
status: active
scope: Unified Blueprint Phase 20 MARKET_CONTEXT to REALIZED_BEHAVIOR N_BARS join
capability: UNIFIED_BLUEPRINT_PHASE_20_BEHAVIOR_JOIN_V1
last_updated: 2026-11-21
---

# Unified Blueprint Phase 20 — Behavior Join Normative V1

```text
DOCUMENT_CLASS=SUBORDINATE_GOVERNANCE_CONTRACT
AUTHORITY_RELATION=SUBORDINATE_TO_PEAK_TRADE_MASTER_RUNBOOK
WORKPACKAGE_ID=UNIFIED_BLUEPRINT_PHASE_20_BEHAVIOR_JOIN_V1
BLUEPRINT_AUTHORITY=NONE
RUNTIME_AUTHORIZATION_EFFECT=NONE
```

Prerequisite: Phase 19 orthogonal `MARKET_CONTEXT_V1` closure on `origin&#47;main`.

Join owner (offline MI/Learning; AUTHORITY=NONE):
`src/learning/market_intelligence_forecast_calibration_offline_stack_v1/realized_behavior_v1.py`

N_BARS realized-outcome backbone (unchanged SSOT):
`peak_trade.learning.ddo.n_bars_bar_evidence_supplier_v1` →
`peak_trade.learning.ddo.real_outcome_horizon_engine_v1`

Integration closure:
`config/governance/unified_blueprint_phase_20_behavior_join_v1.json`

## Verification

- `tests/learning/test_market_context_realized_behavior_join_v1.py`
- `tests/governance/test_unified_blueprint_phase_20_behavior_join_v1.py`
- `prove_unified_blueprint_phase_20_behavior_join_v1`


## Measurement content and context admission — 2026-11-04

For an OK N_BARS observation, supplied measurement must pass the existing supplier
measurement validation before forward-return/behavior use: content reference,
observation identity/context, scalar kind and evaluation time. Rejection is
MEASUREMENT_EVIDENCE_BINDING_INVALID. The supplier pair validator reuses the same
measurement-only function and retains full information-set checks. No missing
information-set payload, measurement formula or source authenticity is invented.
[Verification](../evidence/mi_realized_measurement_binding_v1_2026_11_04/README.md).


## O4 close-path endpoint admission — 2026-11-04

O4 identities must be unique. A supplied OK path ordered by observation bar refs
must match bound measurement first/last close prices. Reject duplicates or endpoint
mismatch before numeric derivation. Input list order does not determine canonical
order. This does not authenticate all interior close values or change formulas.
[Verification](../evidence/mi_realized_close_path_binding_v1_2026_11_04/README.md).

## Original behavior chronology — 2026-11-21

The existing context/horizon, context/evaluation, last-close/evaluation and O4
observation/evaluation bounds use exact source-clock ordering before behavior
derivation. UTC-Z timestamps retain all supported fractional digits. Numeric O4
`venue_event_time` retains its original unit, Unix seconds: finite integer/float
values are compared as their exact represented values against the original UTC
boundary. Nonfinite values cannot bypass that boundary. No milliseconds
conversion, tolerance, rounding or new horizon policy is introduced.

Original raw strings, measurement binding, missing-measurement semantics, N_BARS
ownership, prices, return/volatility formulas and behavior IDs/digests are retained.
Close-path excursion remains direction-neutral, classical MFE/MAE and transition
remain unresolved; this admission check does not certify interior O4 prices.
[Offline verification](../../../tests/learning/test_conditioned_learning_exact_clock_v1.py)
includes a valid numeric event below a fractional cutoff and negative probes
that must stop before the existing forward-behavior materializer.
