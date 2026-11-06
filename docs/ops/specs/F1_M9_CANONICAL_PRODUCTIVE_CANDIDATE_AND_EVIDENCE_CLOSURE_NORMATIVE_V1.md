---
docs_token: DOCS_TOKEN_F1_M9_CANONICAL_PRODUCTIVE_CANDIDATE_AND_EVIDENCE_CLOSURE_NORMATIVE_V1
status: active
scope: F1/M9 canonical productive candidate and evidence closure (read-only census)
workpackage_id: F1_M9_CANONICAL_PRODUCTIVE_CANDIDATE_AND_EVIDENCE_CLOSURE_V1
last_updated: 2026-09-24
---

# F1/M9 Canonical Productive Candidate and Evidence Closure V1

```text
WORKPACKAGE_ID=F1_M9_CANONICAL_PRODUCTIVE_CANDIDATE_AND_EVIDENCE_CLOSURE_V1
PREDECESSOR=F1_M9_REAL_PRODUCTIVE_APPLY_GOVERNED_PREPARATION_V1
CANONICAL_PRODUCTIVE_CANDIDATE_RESOLVED=false
OWNER_POLICY_REQUIRED=true
NEW_PROSPECTIVE_CAMPAIGN_REQUIRED=true
```

Owner: `src/governance/f1_m9_canonical_productive_candidate_evidence_census_v1.py`

## CURRENT conclusion (tracked/canonical only)

Active preregistered campaign `cv_maxage_productive_evidence_campaign_v1_f5e3f95105cd847f`
accumulated **counterfactual** real public-MD session evidence. Preregistration aborts on
`THRESHOLD_SELECTION` and forbids parameter decision. This evidence **cannot** be retroactively
reinterpreted as productive candidate selection authority.

M9-S1 owner input authorizes **research execution only** (`numeric_threshold_selection_authorized=false`).
Optimizable surface and risk constraints forbid threshold selection. No tracked optimization ingress
snapshot binds a single `max_age_seconds` candidate to F1/M9 productive apply.

## Next path (fail-closed)

1. **Owner policy** for an authorized selection rule (not best-performance cherry-pick).
2. **New prospective preregistration/campaign** that explicitly permits candidate/threshold selection
   before decision-bearing evidence is produced.
3. Then separate explicit productive authorization and digest-bound real apply (preparation slice).

## Verification

`tests/governance/test_f1_m9_canonical_productive_candidate_evidence_closure_v1.py`
