---
docs_token: DOCS_TOKEN_V32_D26_F5_SHADOW_D26_BASELINE_BINDING_OWNER_POLICY_ADJUDICATION_V1
status: active
scope: F5 shadow D26 baseline-binding owner-policy forensic adjudication (read-only)
capability: V32_D26_F5_SHADOW_D26_BASELINE_BINDING_OWNER_POLICY_ADJUDICATION_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-24
---

# V32 D26 × F5 — Shadow Baseline-Binding Owner-Policy Adjudication V1

```text
DOCUMENT_CLASS=SUBORDINATE_GOVERNANCE_CONTRACT
AUTHORITY_RELATION=SUBORDINATE_TO_PEAK_TRADE_MASTER_RUNBOOK
WORKPACKAGE_ID=V32_D26_F5_SHADOW_D26_BASELINE_BINDING_OWNER_POLICY_ADJUDICATION_V1
BOUND_ORIGIN_MAIN_SHA=f4dcb6ddfb89409ef4e736cab3756a747650ffac
PREDECESSOR=V32_D27_F5_SHADOW_TEST_ENTRY_AUTHORITY_SUBFAMILY_ADJUDICATION_V1
PREDECESSOR_PR=6768
EXTERNAL_EFFECT_AUTHORIZED=false
NEW_AUTHORITY_CREATED=false
TRADING_DECISION_AUTHORITY_CHANGED=false
IMPLEMENTATION_MODE=ADJUDICATION_ONLY
```

Decision:
`config/governance/v32_d26_f5_shadow_d26_baseline_binding_owner_policy_adjudication_v1_decision_v1.json`

Owner:
`src/governance/d26_f5_shadow_d26_baseline_binding_owner_policy_adjudication_v1.py`

## 1. Purpose

Resolve the **owner-policy blocker**
`f5_shadow_d26_baseline_binding_owner_policy_unresolved` by forensically adjudicating whether
**D26 native baseline evidence binding** or **Stage-1 / calibration-protocol digest pinning**
governs F5 shadow evidence-pack entry — without wiring, numeric mutation, or lifecycle enforcement.

## 2. Epistemic classes

| Class | Use in this WP |
| --- | --- |
| CANONICAL_AUTHORITY | Enforced digest pins, D26 classifiers, D27 F1/F2 admission scope |
| ALREADY_ADJUDICATED | D26 closure, D27 F1/F2 enforcement, D27 F5 subfamily matrix |
| NAVIGATION_INDEX_ONLY | Calibration protocol / campaign manifest prose (digest source files) |
| INTERPRETATION | — (none asserted as policy) |
| HYPOTHESIS | — (none asserted) |
| UNKNOWN | Absent only where no CURRENT path speaks |
| CONFLICTING | Reserved when non-hierarchical authorities contradict |

## 3. Authority graph (proven edges only)

```text
NAKED CORE (integrated replay SSOT)
  -> D26 passive native vs candidate classification (trading-decision / F1 / DDO / optimization evidence)
  -> D27 F1/F2 research entry (D26 native baseline REQUIRED at executor admission)
  -> F5 shadow numeric calibration (Stage-1 manifest digest + calibration protocol digest REQUIRED;
     D26 native baseline schema NOT IN SCOPE on shadow pack entry path)
```

No edge is invented from Concept PDF v3.2 alone; edges above cite CURRENT repo owners.

## 4. Conflict A/B adjudication

| Pole | CURRENT authority | Scope |
| --- | --- | --- |
| **A — D26 native baseline** | `platform_unified_native_vs_candidate_baseline_evidence_v1` + D27 F1/F2 admission | Trading-decision evidence influence classification; parameter-influence research executors F1/F2 |
| **B — Stage-1 / calibration protocol digest** | `run_shadow_campaign_v1` digest pins + F5 shadow registry refs | Pure-stack numeric shadow evidence pack integrity; F5-FRESH / F5-SURV / F5-CAP |

**Verdict:** `PROVEN_CURRENT` **domain-separated hierarchy** (not semantic harmonization):

- D27 lifecycle spec path **P6** explicitly marks F5 shadow entry **`BASELINE_BOUND=no`** while P2/P3 require D26.
- D27 enforcement scope **`TEST_READY_F1_F2_PARAMETER_INFLUENCE`** excludes F5 shadow families.
- D26 closure decision **`d27_blocked_by_d26=false`** — D26 closure does not mandate F5 shadow D26 binding.
- Shadow campaign runner enforces **`stage1_manifest_digest`** and **`calibration_protocol_digest`**; it does not invoke D26 classifiers.
- **`PRODUCTIVE_NUMERIC_VALUES_SET=0`** on shadow paths; baseline evidence remains passive (`AUTHORITY_EFFECT=NONE`).

Prior **`UNKNOWN_CONFLICTING`** in D27 F5 WP is **resolved** as orthogonal scoped authorities, not competing single entry gates.

## 5. Policy record (already belegt; not new runtime rules)

| Field | Value |
| --- | --- |
| `F5_SHADOW_PACK_ENTRY_AUTHORITY` | Stage-1 structural manifest digest + calibration protocol digest pin |
| `D26_NATIVE_BASELINE_ON_F5_SHADOW` | `OUT_OF_SCOPE` (not `ABSENT` as blocker) |
| `BASELINE_BEFORE_PARAMETER_INFLUENCE` | Enforced at F1/F2 via D27; F5 shadow emits provisional observations only |
| `BASELINE_EVIDENCE_PASSIVE_ONLY` | true (D26 classifiers non-enforcing) |

## 6. Earliest true blocker (unchanged)

`f5_shadow_test_entry_gate_not_lifecycle_enforced` — lifecycle wiring remains deferred; baseline-binding **policy** is no longer unresolved.

## 7. Verification

- `tests/governance/test_d26_f5_shadow_d26_baseline_binding_owner_policy_adjudication_v1.py`
