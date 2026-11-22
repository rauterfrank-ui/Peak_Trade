---
docs_token: DOCS_TOKEN_UNIFIED_BLUEPRINT_PHASE_20_BEHAVIOR_JOIN_NORMATIVE_V1
status: active
scope: Unified Blueprint Phase 20 MARKET_CONTEXT to REALIZED_BEHAVIOR N_BARS join
capability: UNIFIED_BLUEPRINT_PHASE_20_BEHAVIOR_JOIN_V1
last_updated: 2026-11-22
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

## Declared quality metadata admission — 2026-11-22

At baseline `e742fcf0f944bdc769a458b93c775bc625201117`, native behavior
validation, conditioned learning/ingest and Phase-25 attribution are connected.
The behavior identity intentionally excludes quality_state. The producer already
emits fixed evidence-only, N_BARS and no-mutation declarations; the same fields
exist in the frozen import `9397d04a3`. Phase 25 copies supplied quality_state
into its quality_refs and includes it in the attribution evidence digest.
Previously, these declarations were not checked by the behavior validator.

The existing validator now admits supplied quality metadata only when it agrees
with that producer contract: NONE context/behavior authority, the original
N_BARS backbone, no duplicate outcome truth and no outcome-field mutation.
JOINED must agree with the declared OK outcome window; other declared windows
retain OUTCOME_INCOMPLETE. Exact boolean types are required: integer 1/0 do not
stand for True/False. A malformed or partial supplied quality object rejects.
Additional annotations are retained without acquiring authority.

Absent or null quality_state remains explicitly missing. No replacement quality,
default authority, successful-join claim or numerical label is fabricated. The
original digest validation runs first; its scope and identity formulas remain
unchanged. Successful records are returned without normalization or rewriting.

Verification: `tests/learning/test_realized_behavior_quality_semantics_v1.py`.
The original-source baseline contains 30 unblocked admissions across native
validation, real ingest and attribution, plus four passing preservation cases.
Three native probes publish contradictory declarations into attributed
quality_refs; JSON inspection and replay accept them under unchanged behavior
IDs/digests. This is transport of false declarations, not productive authority.
Four complete valid behavior/attribution/inspection/ingest/readback packets and
four stored learning files remain byte-identical. A separate native incomplete-
horizon control retains OUTCOME_INCOMPLETE and UNAVAILABLE behavior.

The first combined verification reaches two older conditioned-window probes
while constructing their test input: their changed incomplete window retained
the former JOINED quality declaration. Those two fixtures now declare the
matching OUTCOME_INCOMPLETE quality status so they remain natively admissible
and continue to test rejection against the independent original observation.
Their consumer expectations are unchanged. The failed initial verification is
retained separately; it is not replaced by a document-only proof.

The gate checks declared producer metadata, not independent source authenticity,
measurement correctness, interior O4 prices or numerical behavior truth. It does
not turn JOINED, PROVEN_TYPED or a quality reference into a forecast-quality or
PnL verdict. Classical MFE/MAE and transition remain unresolved; close-path
excursion remains direction-neutral. No behavior values, calibration methods,
units, record bodies, ID/digest algorithms, writer or productive authority change.
MI learning still transports its existing behavior reference/digest and snapshot;
no new quality payload is added. Later consumers with only historical references
cannot retrospectively check absent original metadata. Existing stored records
are not repaired or retroactively source-certified. Earlier pre-import history
and complete system operation are not established by this bounded check.
