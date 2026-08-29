# MASTER V2 — A06 Capital → Risk → Sizing → Position Intent restore v1

status: ACTIVE
last_updated: 2026-08-29
owner: Peak_Trade
purpose: Current-system mapping of restored A06 semantic stages. Not canonical authority.
docs_token: DOCS_TOKEN_MASTER_V2_A06_CAPITAL_RISK_SIZING_INTENT_RESTORE_V1

```text
HISTORICAL_REFERENCE_AUTHORITY=NONE
REFERENCE_MODEL=MASTER_V2_DOUBLE_PLAY_CONSERVED_REFERENCE_V1
REFERENCE_FIRST=true
CURRENT_SYSTEM_ADAPTATION=true
A06_ONLY=true
NO_TRADING=true
NO_LIVE_AUTHORITY=true
NO_EXECUTION_AUTHORITY=true
CANONICAL_MUTATION=false
```

## 1) Historical obligation source

Obligations are derived from the repo-preserved forensic historical reference
(PR #6130; SHA-256 `a5a468f761e24e17fc0402dbf056df7d45090b3c58f0e9a2ad469569e908e212`).
That package has `AUTHORITY=NONE`. It is not promoted to canonical working
authority. Current-system code is adapted to the proven stage obligations.

Primary historical anchors (forensic blob, not SSOT):

- Canonical target chain / stage classification around forensic lines 16892–16970
  (`Risk`, `Sizing &#47; exposure`, `Execution decision &#47; Intent` as distinct stages)
- Capital-path layering in `MASTER_V2_SCOPE_CAPITAL_ENVELOPE_CLARIFICATION_V1`
  (Scope/Capital Envelope upstream of Risk/Exposure caps)
- Current-system STEP 29P/29Q owners:
  `src/governance/capital_risk_sizing_v1.py`
  `src/governance/canonical_order_intent_v1.py`

## 2) Current A06 implementation mapping

```text
Registry snapshot
  → Suitability
  → Integrated Replay (compute owner)
  → Double Play / SideState
  → CanonicalTradingDecisionEvidenceV1
  → CAPITAL_ENVELOPE  (ScopeCapitalEnvelopeV1)
  → RISK              (PreSizingRiskAssessmentV1)
  → SIZING            (CanonicalPositionSizingV1)
  → POSITION_INTENT   (CanonicalOrderIntentV1, PLAN_ONLY)
```

Current-system owners:

| Semantic stage | Current type | Module |
|---|---|---|
| Decision Evidence | `CanonicalTradingDecisionEvidenceV1` | `trading.master_v2.canonical_trading_decision_evidence_v1` |
| Capital Envelope | `ScopeCapitalEnvelopeV1` | `src.governance.capital_risk_sizing_v1` |
| Risk | `PreSizingRiskAssessmentV1` | `src.governance.capital_risk_sizing_v1` |
| Sizing | `CanonicalPositionSizingV1` | `src.governance.capital_risk_sizing_v1` |
| Position Intent | `CanonicalOrderIntentV1` | `src.governance.canonical_order_intent_v1` |
| A06 restore facade | `capital_risk_sizing_intent_restore_v1` | `trading.master_v2.capital_risk_sizing_intent_restore_v1` |

A01–A05 core wiring remains the upstream path. Integrated Replay remains the
decision/replay compute owner. The Decision Packet remains derived handoff only.

## 3) Semantic-stage vs module-separation

```text
FUNCTIONAL_STAGE_SEPARATION_REQUIRED=true
MANDATORY_MODULE_SEPARATION=false
SEMANTIC_STAGE_OWNERSHIP_SEPARATE=true
IMPLEMENTATION_MODULE_OWNERSHIP_MAY_BE_COMBINED=true
```

Capital Envelope, Risk, and Sizing remain independently observable stages even
though they share `capital_risk_sizing_v1.py`. Position Intent remains a
downstream module (`canonical_order_intent_v1.py`) and is non-executing.

## 4) AUTH-014 disposition

```text
AUTH_014_STATUS=CONSERVATIVE_SEMANTIC_STAGES_SEPARATE_MODULE_MAY_COMBINE
AUTH_014_POLICY_CHOICE_REQUIRED=false
AUTH_014_OWNER_QUESTION=NONE
STOP_BEFORE_SEMANTIC_CHOICE=false
```

Historical evidence requires functional Capital → Risk → Sizing boundaries.
It does not require mutually incompatible Python-module ownership that cannot
be represented conservatively. No owner-policy choice is made or required.

## 5) Fail-closed behavior

The restore facade fails closed for:

- missing / non-authoritative decision evidence
- unknown, ambiguous, or snapshot-mismatched strategy identity
- missing Capital Envelope output
- Capital→Risk provenance mismatch / duplicate inconsistent identifiers
- Risk rejection
- Sizing without valid risk approval
- Position Intent without valid sizing
- legacy Decision Packet offered as independent compute authority
- downstream attempt to override Double Play / SideState authority
- accidental execution / live / order-submit authorization

The A06 path calls `evaluate_quantity_chain_v1` with the authoritative replay
evidence. It does not use the legacy flat-input synthesizer
(`evaluate_capital_risk_sizing_v1` / `replay_id="legacy-replay"`) as decision
authority.

## 6) Non-execution boundary

Existing project-standard equivalents are reused; no new live vocabulary:

```text
EXECUTION_MODE=PLAN_ONLY
ORDER_SUBMIT_AUTHORIZED=false
LIVE_AUTHORIZED=false
RUNTIME_BRIDGE_STATUS=BOUND_NOT_ACTIVATED
CanonicalOrderIntentV1.submission_authorized=false
CanonicalOrderIntentV1.execution_eligible=false
plan_only_boundary_owner=src.execution_pipeline.plan_only_boundary_v0
```

## 7) Remaining unresolved work (not this slice)

```text
A07_PARITY_RESTORE=false
A08_SAFETY_INVARIANT_RESTORE=false
A09_KILL_SWITCH_RESTORE=false
A10_SINGLE_WRITER_RESTORE=false
A11_EV_RESTORE=false
A12_LIVE_GATE_RESTORE=false
A13_CONFIG_REBIND=false
A15_DOC_SELECTOR_REBIND=false
```
