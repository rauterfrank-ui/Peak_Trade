---
docs_token: DOCS_TOKEN_F1_M9_PROSPECTIVE_CAMPAIGN_AUTHORIZED_RUN_ORCHESTRATION_NORMATIVE_V1
status: active
scope: F1/M9 terminal authorized campaign run orchestration owner (max-build; no live campaign)
workpackage_id: F1_M9_PROSPECTIVE_CAMPAIGN_AUTHORIZED_RUN_ORCHESTRATION_OWNER_V1
last_updated: 2026-09-24
---

# F1/M9 Prospective Campaign Authorized Run Orchestration V1

```text
WORKPACKAGE_ID=F1_M9_PROSPECTIVE_CAMPAIGN_AUTHORIZED_RUN_ORCHESTRATION_OWNER_V1
PREDECESSOR=F1_M9_PROSPECTIVE_SELECTION_CAMPAIGN_EXECUTION_OWNER_MAX_BUILD_V1
ORCHESTRATION_OWNER_ID=f1_m9_prospective_campaign_authorized_run_orchestration_v1
PUBLIC_MARKET_DATA_EXTERNAL_READ_OCCURRED=false
CAMPAIGN_EXECUTED=false
REAL_EVIDENCE_WRITTEN=false
```

Entry owner: `src/governance/f1_m9_prospective_candidate_selection_campaign_execution_v1/authorized_run_orchestration_v1.py`

Decision: `config/governance/f1_m9_prospective_campaign_authorized_run_orchestration_v1_decision_v1.json`

## Lifecycle (terminal path)

Runtime authorization verify → atomic exactly-once consume → preregistered REAL public-MD supplier binding → preregistered sessions/work units → evidence generation → durable append-only materialization → provenance/integrity sealing → contamination + historical leakage guards → campaign completeness → OOS/robustness/economic evidence → deterministic replay → `apply_f1_m9_selection_rule_v1` → terminal campaign verdict.

Default production entry (build slice): binding verification only — `REAL_EFFECTS_DISABLED_IN_BUILD_SLICE`.

Hermetic isolated execution (tests): full terminal path under `tmp_path` with simulated public-MD sessions; module-level REAL-effect flags remain false.

## Verification

`tests/governance/test_f1_m9_prospective_campaign_authorized_run_orchestration_v1.py`
