---
docs_token: DOCS_TOKEN_CURRENT_CONTINUOUS_RUN_POLICY_V1
status: active
scope: CURRENT Continuous Run policy — governed repeated PRE_EXTERNAL-bounded productive cycles only
workpackage_id: CURRENT_CONTINUOUS_RUN_POLICY_V1
last_updated: 2026-09-27
---

# CURRENT Continuous Run Policy V1

```text
WORKPACKAGE_ID=CURRENT_CONTINUOUS_RUN_POLICY_V1
BASELINE_ORIGIN_MAIN_SHA=79a8b581e66346b7d40cf402cbc8f1f05f156678
CONTINUOUS_RUN_SEMANTIC=GOVERNED_REPEATED_BOUNDED_PRE_EXTERNAL_PRODUCTIVE_CYCLES
EXTERNAL_EFFECT_AUTHORIZED=false
POST_ALLOWED=false
```

Owner record:
`config/governance/current_continuous_run_policy_v1_record.json`

Owner GO:
`config/governance/current_continuous_run_policy_owner_go_v1_decision.json`

## Semantic contract

| Layer | Meaning |
| --- | --- |
| Policy authorization | Singular owner `governance.current_continuous_run_policy_v1`; lineage-bound record + Owner GO. |
| Prerequisite | Valid CURRENT Productive Activation policy (#6891) with unchanged F1/M9 600s lineage. |
| Runtime admission | `evaluate_continuous_runtime_admission_v1()` — fail-closed; requires fresh Productive Activation on every cycle. |
| Orchestration surface | `run_policy_governed_current_productive_continuous_cycle_run_v1` → S6 sequencer with per-iteration revalidation. |
| Bounded cycle | Productive Activation admission → F1/M9 consumer → S5 one-cycle (injected offline) → PRE_EXTERNAL terminal. |
| External-effect authority | **Not granted** (`EXTERNAL_EFFECT_AUTHORIZED=false`). |

## Authority lattice

```text
PRODUCTIVE_ACTIVATION => PRODUCTIVE_RUNTIME_ADMISSION
CONTINUOUS_RUN => CONTINUOUS_RUNTIME_ADMISSION (requires valid Productive Activation)
CONTINUOUS_RUN -/-> EXTERNAL_EFFECT
CONTINUOUS_RUN -/-> PERMIT / WIRE_SEND / POST / CREDENTIAL_ACCESS
PRODUCTIVE_ACTIVATION -/-> CONTINUOUS_RUN
```

Module pin `CONTINUOUS_RUN_AUTHORIZED=false` on the S6 orchestrator remains a static fail-closed census guard; runtime authority flows only through this policy record and admission evaluator.

Code: `src/governance/current_continuous_run_policy_v1.py`
Runtime binding: `src/governance/current_continuous_run_runtime_binding_v1.py`
