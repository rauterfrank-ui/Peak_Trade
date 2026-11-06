---
docs_token: DOCS_TOKEN_GOVERNED_F1_M9_PRODUCTIVE_RUNTIME_THRESHOLD_CONSUMER_WIRING_REAL_MECHANICAL_CONTINUATION_V1
status: active
scope: F1/M9 productive runtime threshold consumer wiring (600s post-#6887/#6888; no activation)
workpackage_id: GOVERNED_F1_M9_PRODUCTIVE_RUNTIME_THRESHOLD_CONSUMER_WIRING_REAL_MECHANICAL_CONTINUATION_V1
last_updated: 2026-09-27
---

# Governed F1/M9 Productive Runtime Threshold Consumer Wiring Real Mechanical Continuation V1

```text
WORKPACKAGE_ID=GOVERNED_F1_M9_PRODUCTIVE_RUNTIME_THRESHOLD_CONSUMER_WIRING_REAL_MECHANICAL_CONTINUATION_V1
RATIFIED_THRESHOLD_NUMERIC_MAX_AGE_SECONDS=600
REAL_P4_TO_F1_M9_JOIN_NOT_CANONICAL=true
PRODUCTIVE_ACTIVATION_AUTHORIZED=false
CONTINUOUS_RUN_AUTHORIZED=false
EXTERNAL_EFFECT_AUTHORIZED=false
```

Owner WP:
`config/governance/governed_f1_m9_productive_runtime_threshold_consumer_wiring_wp_v1_owner_decision_v1.json`

Decision:
`config/governance/governed_f1_m9_productive_runtime_threshold_consumer_wiring_real_mechanical_continuation_v1_decision_v1.json`

## Authority lineage (CURRENT)

Post-#6887 threshold ratification and post-#6888 governed productive runtime apply start
(`configuration.runtime_applied=true`, digest **3f089595…** / **e556ea63…**). This WP wires the
already-ratified/applied value into the **CURRENT** productive runtime path only.

## Chain

```text
productive runtime cycle (hardening v2 bridge / integrated offline replay)
  → session-bound governed seam record (when present)
  → resolve_governed_runtime_seam_for_presence_gate_v1
  → evaluate_double_play_runtime_typed_volatility_presence_gate_v1
  → evaluate_bounded_threshold_enforcement_at_mv2_consumer_v1 (#6802 bounded decision)
  → apply_bounded_enforcement_to_double_play_alpha_v1 (MV2 alpha boundary)
  → STOP before Productive Activation / external effect
```

## Non-implications

- No Productive Activation
- No continuous run / daemonization
- No Real-P4 ↔ F1/M9 join
- No venue POST / credentials / permits
- No global `ENFORCEMENT_ENABLED=true`

## Verification

- `tests/governance/test_governed_f1_m9_productive_runtime_threshold_consumer_wiring_real_mechanical_continuation_v1.py`
- `src/governance/f1_m9_productive_runtime_threshold_consumer_wiring_v1.py`
