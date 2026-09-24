---
docs_token: DOCS_TOKEN_V32_D27_F5_SHADOW_TEST_ENTRY_LIFECYCLE_ENFORCEMENT_V1
status: active
scope: D27 F5 shadow campaign test-entry lifecycle enforcement (bounded)
capability: V32_D27_F5_SHADOW_TEST_ENTRY_LIFECYCLE_ENFORCEMENT_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-24
---

# V32 D27 — F5 Shadow Test-Entry Lifecycle Enforcement V1

```text
DOCUMENT_CLASS=SUBORDINATE_GOVERNANCE_CONTRACT
AUTHORITY_RELATION=SUBORDINATE_TO_PEAK_TRADE_MASTER_RUNBOOK
WORKPACKAGE_ID=V32_D27_F5_SHADOW_TEST_ENTRY_LIFECYCLE_ENFORCEMENT_V1
BOUND_ORIGIN_MAIN_SHA=2a7dce95a6db85287a234b4b3b561db443202d59
PREDECESSOR=V32_D26_F5_SHADOW_D26_BASELINE_BINDING_OWNER_POLICY_ADJUDICATION_V1
PREDECESSOR_PR=6769
EXTERNAL_EFFECT_AUTHORIZED=false
NEW_AUTHORITY_CREATED=false
TRADING_DECISION_AUTHORITY_CHANGED=false
IMPLEMENTATION_MODE=COMPOSE_EXISTING
```

Decision: `config/governance/v32_d27_f5_shadow_test_entry_lifecycle_enforcement_v1_decision_v1.json`

Owner: `src/governance/d27_f5_shadow_test_entry_lifecycle_enforcement_v1.py`

## 1. Purpose

Fail-closed **lifecycle admission** at the earliest CURRENT F5 shadow execution seam
(`run_shadow_campaign_v1`) using **already adjudicated** entry predicates only:

- Pre-test matrix `TEST_ENTRY_GATE` for **F5-FRESH**
- Stage-1 structural manifest digest pin
- Calibration protocol digest pin

**D26 native baseline is OUT_OF_SCOPE** on this path (PR #6769).

## 2. Enforcement seam

| Step | Owner | Enforced |
| --- | --- | --- |
| Caller | CLI / Surface-B collector | indirect |
| **Admission** | `enforce_d27_f5_fresh_shadow_campaign_test_entry_lifecycle_v1` | **yes** |
| Shadow execution | `run_shadow_campaign_v1` | after admission only |

## 3. Entry conjunction (authorized)

```text
TEST_ENTRY_GATE=F5-FRESH:SHADOW_PURE_STACK_NUMERIC_EVIDENCE_PACK_VALIDATION_V1
AND declared_stage1_manifest_digest == sha256(STAGE1_MANIFEST_REL)
AND declared_calibration_protocol_digest == sha256(CALIBRATION_PROTOCOL_REL)
AND preparation_status=TEST_READY_SHADOW_RESEARCH
```

Missing / invalid / mismatch / unresolved source file ⇒ **DENY** (exception before shadow work).

## 4. Non-goals

- D26 native baseline on F5 shadow paths
- Productive numeric values or OWNER_VALUE_* mutation
- F5-SURV / F5-CAP per-token registry runtime wiring (separate surfaces)
- Promotion / external effect / trading authority change

## 5. Verification

- `tests/governance/test_d27_f5_shadow_test_entry_lifecycle_enforcement_v1.py`
- `tests/ops/test_productive_pure_stack_numeric_policy_shadow_campaign_v1.py` (digest deny)
