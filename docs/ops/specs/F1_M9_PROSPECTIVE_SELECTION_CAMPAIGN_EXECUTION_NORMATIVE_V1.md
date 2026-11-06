---
docs_token: DOCS_TOKEN_F1_M9_PROSPECTIVE_SELECTION_CAMPAIGN_EXECUTION_NORMATIVE_V1
status: active
scope: F1/M9 prospective candidate-selection campaign execution owner (max-build; no live campaign)
workpackage_id: F1_M9_PROSPECTIVE_SELECTION_CAMPAIGN_EXECUTION_OWNER_MAX_BUILD_V1
last_updated: 2026-09-24
---

# F1/M9 Prospective Candidate Selection Campaign Execution V1

```text
WORKPACKAGE_ID=F1_M9_PROSPECTIVE_SELECTION_CAMPAIGN_EXECUTION_OWNER_MAX_BUILD_V1
PREDECESSOR=F1_M9_PRODUCTIVE_CANDIDATE_SELECTION_POLICY_AND_PROSPECTIVE_CAMPAIGN_V1
EXECUTION_OWNER_ID=f1_m9_prospective_candidate_selection_campaign_execution_v1
REAL_CAMPAIGN_EXECUTION_AUTHORIZED=false
CAMPAIGN_EXECUTED=false
```

Owner package: `src/governance/f1_m9_prospective_candidate_selection_campaign_execution_v1/`

Decision: `config/governance/f1_m9_prospective_candidate_selection_campaign_execution_v1_decision_v1.json`

## Modes

| Mode | Network | Durable REAL evidence | Selection |
| --- | --- | --- | --- |
| `EXECUTION_PROOF` | No | No | No |
| `AUTHORIZED_CAMPAIGN_EXECUTION` | Only with runtime record + `public_market_data_read_authorized` | Only with `durable_evidence_write_authorized` | After sealed completeness |

Runtime authorization is **separate** from frozen preregistration JSON fields
(`campaign_execution_authorized=false` in preregistration remains unchanged).

Terminal authorized-run orchestration owner (successor): `authorized_run_orchestration_v1`
— see `docs/ops/specs/F1_M9_PROSPECTIVE_CAMPAIGN_AUTHORIZED_RUN_ORCHESTRATION_NORMATIVE_V1.md`.

## Verification

`tests/governance/test_f1_m9_prospective_candidate_selection_campaign_execution_v1.py`
