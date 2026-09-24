---
docs_token: DOCS_TOKEN_F1_M9_PRODUCTIVE_CANDIDATE_SELECTION_POLICY_AND_PROSPECTIVE_CAMPAIGN_NORMATIVE_V1
status: active
scope: F1/M9 owner selection policy and prospective campaign preregistration only
workpackage_id: F1_M9_PRODUCTIVE_CANDIDATE_SELECTION_POLICY_AND_PROSPECTIVE_CAMPAIGN_V1
last_updated: 2026-09-24
---

# F1/M9 Productive Candidate Selection Policy and Prospective Campaign V1

```text
WORKPACKAGE_ID=F1_M9_PRODUCTIVE_CANDIDATE_SELECTION_POLICY_AND_PROSPECTIVE_CAMPAIGN_V1
PREDECESSOR=F1_M9_CANONICAL_PRODUCTIVE_CANDIDATE_AND_EVIDENCE_CLOSURE_V1
CANDIDATE_SELECTION_AUTHORITY=F1_M9_SCOPED_RESEARCH_TO_PROPOSAL_SELECTION_ONLY
NEW_PROSPECTIVE_CAMPAIGN_EXECUTED=false
CANONICAL_PRODUCTIVE_CANDIDATE_RESOLVED=false
```

Owner modules:

- `src/governance/f1_m9_productive_candidate_selection_policy_v1.py`
- `src/governance/f1_m9_prospective_candidate_selection_campaign_preregistration_v1.py`
- `src/governance/f1_m9_prospective_candidate_selection_evidence_leakage_guard_v1.py`
- `src/governance/f1_m9_productive_candidate_selection_policy_closure_v1.py`

Historical campaign `cv_maxage_productive_evidence_campaign_v1_f5e3f95105cd847f` remains
**counterfactual-only** with `THRESHOLD_SELECTION` abort-blocked. Its evidence is research
context only and must not decide the new prospective selection outcome.

## Verification

`tests/governance/test_f1_m9_productive_candidate_selection_policy_and_prospective_campaign_v1.py`
