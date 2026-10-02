---
docs_token: DOCS_TOKEN_TOP20_OPPORTUNITY_EVALUATION_RESIDENCY_AND_SCHEDULING_V1
status: active
scope: Cap2.2 Top20 evaluation continuity and non-preferential scheduling to ≤5 evaluation capacity
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
RUNTIME_ACTIVATION_ALLOWED: false
SELECTION_AUTHORITY: false
RANKING_AUTHORITY: false
TRADING_AUTHORITY: false
HARD_STOP: true
---

# Top20 Opportunity Evaluation Residency & Scheduling V1

```text
CAPABILITY_ID=TOP20_OPPORTUNITY_EVALUATION_RESIDENCY_V1
TOP20_EVALUATION_RESIDENCY_ENABLED=false
EARLY_RELEASE_ALLOWED=true
MAX_ACTIVE_EVALUATION_RESIDENTS=5
CONFIG_KEYS=top20_evaluation_residency_enabled;top20_evaluation_residency_max_pending;top20_evaluation_residency_duration_seconds
EVALUATION_COMPLETION=CANONICAL_INTEGRATED_OFFLINE_REPLAY_EXECUTED+VALID_GOVERNED_CYCLE_EVIDENCE
NATURAL_ENTER_REQUIRED_FOR_COMPLETION=false
```

Insert after FINAL VALID Cap2.2 persist; consume before staged N5 control plane orchestrator when enabled.

Admission snapshot duality: evaluation uses immutable `admission_snapshot_ref`; current Cap2.2 truth recorded separately in observations.

Operational defaults for `max_pending` and `duration_seconds` are config-only — not economic authority.

Owner package: `src/ops/top20_opportunity_evaluation_residency_v1/`.
