---
docs_token: DOCS_TOKEN_M9_S1_OPERATOR_AUTHORIZED_NUMERIC_MAX_AGE_PARAMETER_RESEARCH_AND_SELECTION_NORMATIVE_V1
status: active
scope: M9-S1 operator-authorized numeric max-age parameter research and owner-review selection boundary
workpackage_id: M9_S1_OPERATOR_AUTHORIZED_NUMERIC_MAX_AGE_PARAMETER_RESEARCH_AND_SELECTION_V1
last_updated: 2026-09-20
---

# M9-S1 Operator-Authorized Numeric Max-Age Parameter Research and Selection V1

```text
WP_ID=M9_S1_OPERATOR_AUTHORIZED_NUMERIC_MAX_AGE_PARAMETER_RESEARCH_AND_SELECTION_V1
PREDECESSOR=M10_RUNTIME_SEAM_RESEARCH_JOIN_RECONCILIATION_CLOSED
SURFACE=VOLATILITY_NUMERIC_MAX_AGE (M9-S1)
CANDIDATE_PARAMETER=candidate_max_age_seconds
LIVE_AUTHORIZED=false
ORDERS_ALLOWED=false
NUMERIC_MAX_AGE_DECIDED=false
ENFORCEMENT_ENABLED=false
EXTERNAL_EFFECT_AUTHORIZED=false
```

## Chain (this workpackage)

```text
Operator authorization (research-only)
  → canonical parameter research execution (reuse)
  → evidence artifacts (PROPOSAL_ONLY)
  → owner-review selection boundary (UNRESOLVED_OWNER_DECISION)
  → STOP
```

## Not in scope

- Numeric max-age ratification or single-point selection from evidence
- Governed productive configuration, parameter seam materialization, enforcement
- Trading-decision authority change (MV2 + Double Play unchanged)
- External effect

## Owners

| Artifact | Path |
|---|---|
| Authorization + selection boundary | `src/governance/m9_s1_operator_authorized_numeric_max_age_parameter_research_and_selection_v1.py` |
| Research execution (reuse) | `src/research/canonical_volatility_numeric_max_age_parameter_research_execution_v1/` |
| Decision | `config/governance/m9_s1_operator_authorized_numeric_max_age_parameter_research_and_selection_v1_decision_v1.json` |
| Owner boundary | `config/governance/m9_s1_operator_authorized_numeric_max_age_parameter_research_and_selection_v1_owner_boundary_v1.json` |
| Committed owner input | `config/governance/m9_s1_operator_authorized_numeric_max_age_parameter_research_and_selection_v1_owner_input_v1.json` |
| Tests | `tests/governance/test_m9_s1_operator_authorized_numeric_max_age_parameter_research_and_selection_v1.py` |

## Remaining boundary after this capability

```text
NEXT_AFTER_THIS_CAPABILITY=
SEPARATE_OWNER_AUTHORIZED_THRESHOLD_SELECTION_OR_FURTHER_EVIDENCE_ACCUMULATION
SELECTION_RESULT=UNRESOLVED_OWNER_DECISION
```

Preregistered selection criteria forbid deterministic best-point selection; only operator
authorized threshold selection after research may close `C1_G10_NUMERIC_MAX_AGE_THRESHOLD_VALUE`.
