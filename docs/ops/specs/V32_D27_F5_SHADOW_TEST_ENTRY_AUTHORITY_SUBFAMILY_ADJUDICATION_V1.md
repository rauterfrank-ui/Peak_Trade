---
docs_token: DOCS_TOKEN_V32_D27_F5_SHADOW_TEST_ENTRY_AUTHORITY_SUBFAMILY_ADJUDICATION_V1
status: active
scope: D27 F5 shadow/numeric subfamily forensic adjudication (read-only; no lifecycle wiring)
capability: V32_D27_F5_SHADOW_TEST_ENTRY_AUTHORITY_SUBFAMILY_ADJUDICATION_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-24
---

# V32 D27 — F5 Shadow Test-Entry Authority + Subfamily Adjudication V1

```text
DOCUMENT_CLASS=SUBORDINATE_GOVERNANCE_CONTRACT
AUTHORITY_RELATION=SUBORDINATE_TO_PEAK_TRADE_MASTER_RUNBOOK
WORKPACKAGE_ID=V32_D27_F5_SHADOW_TEST_ENTRY_AUTHORITY_SUBFAMILY_ADJUDICATION_V1
BOUND_ORIGIN_MAIN_SHA=17effb55562626344bc35f49e695740a22f04901
PREDECESSOR=V32_D27_TEST_ENTRY_LIFECYCLE_ENFORCEMENT_FORENSIC_BOUNDED_COMPLETION_V1
EXTERNAL_EFFECT_AUTHORIZED=false
NEW_AUTHORITY_CREATED=false
TRADING_DECISION_AUTHORITY_CHANGED=false
IMPLEMENTATION_MODE=ADJUDICATION_ONLY
```

Decision: `config/governance/v32_d27_f5_shadow_test_entry_authority_subfamily_adjudication_v1_decision_v1.json`

Owner: `src/governance/d27_f5_shadow_test_entry_authority_subfamily_adjudication_v1.py`

## 1. Purpose

Forensically decompose **F5** into its **belegte** subfamilies (`F5-FRESH`, `F5-SURV`, `F5-CAP`) and
adjudicate each separately. **No** F1/F2 template copying, **no** F5-FRESH ↔ F1 freshness dedupe,
**no** bounded lifecycle wiring in this WP (no subfamily meets `READY_FOR_BOUNDED_WIRING`).

## 2. Epistemic classes used

| Class | Use |
| --- | --- |
| CANONICAL_AUTHORITY | Matrix owner, D1 grant, shadow campaign constants |
| ALREADY_ADJUDICATED | D27 F1/F2 enforcement, pre-test preparation matrix |
| NAVIGATION_INDEX_ONLY | Calibration protocol / campaign manifest (digest checks only) |
| INTERPRETATION | Spec §2 vs §3 F5-FRESH envelope wording tension |
| HYPOTHESIS | — (none asserted) |
| UNKNOWN_CONFLICTING | D26 native baseline applicability to shadow evidence pack entry |

## 3. Path matrix (consumer → exit)

| PATH | SUBFAMILY | ENTRYPOINT | GATE_DEFINED | GATE_ENFORCED | BASELINE (D26) | LIFECYCLE_EXIT | VERDICT |
| --- | --- | --- | --- | --- | --- | --- | --- |
| P-F5-FRESH-ENV | F5-FRESH | `resolve_optimizable_envelope_v1` | indirect (surface registry) | no | no | n/a | PARTIAL_CURRENT |
| P-F5-FRESH-OBS | F5-FRESH | `collect_shadow_futures_input_freshness_age_v1` | n/a (collector) | no | no | observation return | PARTIAL_CURRENT |
| P-F5-FRESH-CAM | F5-FRESH | `run_shadow_campaign_v1` | matrix `SHADOW_PURE_STACK_NUMERIC_EVIDENCE_PACK_VALIDATION_V1` | **no** | **no** (stage1/protocol digests only) | `campaign_result.v1.json` | PARTIAL_CURRENT |
| P-F5-SURV-REG | F5-SURV | `shadow_per_token_calibration_entries_v1` | `SHADOW_PER_TOKEN_THRESHOLD_SENSITIVITY_V1` | no | no | registry only | PARTIAL_CURRENT |
| P-F5-SURV-CAM | F5-SURV | `run_shadow_campaign_v1` (survival tokens) | partial (observation notes) | no | no | evidence pack emit | PARTIAL_CURRENT |
| P-F5-CAP-REG | F5-CAP | `shadow_per_token_calibration_entries_v1` | `SHADOW_PER_TOKEN_THRESHOLD_SENSITIVITY_V1` | no | no | registry only | PARTIAL_CURRENT |
| P-F5-CAP-CAM | F5-CAP | `run_shadow_campaign_v1` (capital tokens) | partial | no | no | evidence pack emit | PARTIAL_CURRENT |

**Bypass:** any direct call to `run_shadow_campaign_v1`, collectors, or envelope resolver without D27
admission (currently all paths).

## 4. Subfamily adjudication matrix

See machine-readable rows from `build_f5_subfamily_adjudication_matrix_v1()`.

Summary:

| SUBFAMILY | VERDICT | WIRING_DECISION |
| --- | --- | --- |
| F5-FRESH | PARTIAL_CURRENT | OWNER_POLICY_REQUIRED |
| F5-SURV | PARTIAL_CURRENT | OWNER_POLICY_REQUIRED |
| F5-CAP | PARTIAL_CURRENT | OWNER_POLICY_REQUIRED |

## 5. Cross-cutting findings

- **`PRODUCTIVE_NUMERIC_VALUES_SET`**: CURRENT `0` in shadow campaign and Stage-2 boundary modules
  (`src/ops/productive_pure_stack_numeric_policy_shadow_campaign_v1/constants_v1.py`).
- **Shadow protocol**: validates `stage1_manifest_digest` + `calibration_protocol_digest`; does **not**
  mint Owner numeric values or productive thresholds (NAVIGATION_INDEX_ONLY + fail-closed emit).
- **`ResearchTestEntryGateV1`**: CANONICAL_AUTHORITY for gate **labels** on F5 matrix rows; not
  runtime-enforced on shadow paths (distinct from F1/F2 executors).
- **`resolve_optimizable_envelope_v1`**: envelope metadata/resolver only; **not** test-entry lifecycle
  authority (consistent with D27 spec P5).
- **F1 ↔ F5 isolation**: `F1_M9_DEDUPLICATION_FORBIDDEN` on F5-FRESH domain; distinct owner token
  `OWNER_VALUE_FUTURES_INPUT_FRESHNESS_MAX_AGE_SECONDS` vs F1 `candidate_max_age_seconds` seam.

## 6. Earliest true blocker (unchanged)

`f5_shadow_test_entry_gate_not_lifecycle_enforced` — plus **owner policy** for D26 baseline binding
semantics on shadow pack entry before any bounded D27 F5 seam.

## 7. Verification

- `tests/governance/test_d27_f5_shadow_test_entry_authority_subfamily_adjudication_v1.py`
