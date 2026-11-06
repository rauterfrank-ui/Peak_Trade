---
docs_token: DOCS_TOKEN_CURRENT_PRODUCTIVE_ACTIVATION_POLICY_V1
status: active
scope: CURRENT Productive Activation policy — bounded PRE_EXTERNAL runtime admission only
workpackage_id: CURRENT_PRODUCTIVE_ACTIVATION_POLICY_V1
last_updated: 2026-09-27
---

# CURRENT Productive Activation Policy V1

```text
WORKPACKAGE_ID=CURRENT_PRODUCTIVE_ACTIVATION_POLICY_V1
BASELINE_ORIGIN_MAIN_SHA=958657754033f432dc723fc4f56412f2de9430dd
PRODUCTIVE_ACTIVATION_SEMANTIC=BOUNDED_PRE_EXTERNAL_RUNTIME_ADMISSION
CONTINUOUS_RUN_AUTHORIZED=false
EXTERNAL_EFFECT_AUTHORIZED=false
POST_ALLOWED=false
```

Owner record:
`config/governance/current_productive_activation_policy_v1_record.json`

Owner GO:
`config/governance/current_productive_activation_policy_owner_go_v1_decision.json`

## Semantic contract

| Layer | Meaning |
| --- | --- |
| Policy authorization | Singular owner `governance.current_productive_activation_policy_v1`; lineage-bound record + Owner GO. |
| Policy evidence | Decision-config digests, F1/M9 600s + threshold/apply digests, forensic review binding. |
| Runtime admission | `evaluate_productive_runtime_admission_v1(runtime_surface)` — fail-closed. |
| Bounded runtime execution | F1/M9 consumer path after admission; enforcement remains bounded (#6802). |
| Continuous-run authority | **Not granted** (`CONTINUOUS_RUN_AUTHORIZED=false`). |
| External-effect authority | **Not granted** (`EXTERNAL_EFFECT_AUTHORIZED=false`). |

## Authority lattice

```text
PRODUCTIVE_ACTIVATION => PRODUCTIVE_RUNTIME_ADMISSION (named surface)
PRODUCTIVE_RUNTIME_ADMISSION -/-> CONTINUOUS_RUN
PRODUCTIVE_RUNTIME_ADMISSION -/-> EXTERNAL_EFFECT
PRODUCTIVE_RUNTIME_ADMISSION -/-> PERMIT / WIRE_SEND / POST / CREDENTIAL_ACCESS
```

P5.10 `PRODUCTIVE_CYCLE_LAYERED_CORE_BIND_ENABLED` is **not** this policy.

## Runtime binding (#6889 path)

```text
evaluate_productive_runtime_admission_v1(surface)
  → evaluate_f1_m9_productive_runtime_threshold_consumer_path_v1(..., runtime_surface=surface)
  → seam transport → presence gate → bounded enforcement → MV2 alpha
  → terminates at PRE_EXTERNAL orchestration boundary (no POST)
```

Surfaces: `F1_M9_THRESHOLD_CONSUMER_HARDENING_V2_BRIDGE`, `F1_M9_THRESHOLD_CONSUMER_INTEGRATED_OFFLINE_REPLAY`.

Code: `src/governance/current_productive_activation_policy_v1.py`
