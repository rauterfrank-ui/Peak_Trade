---
docs_token: DOCS_TOKEN_M9_VOLATILITY_NUMERIC_MAX_AGE_OPTIMIZABLE_SURFACE_NORMATIVE_V1
status: active
scope: Owner-authorized M9 optimizable surface for volatility numeric max-age research optimization only
capability: M9_VOLATILITY_NUMERIC_MAX_AGE_OPTIMIZABLE_SURFACE_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-19
---

# M9 — Volatility Numeric Max-Age Optimizable Surface V1

```text
DOCUMENT_CLASS=SUBORDINATE_GOVERNANCE_CONTRACT
WORKPACKAGE_ID=M9_VOLATILITY_MAX_AGE_OPTIMIZABLE_SURFACE_IMPLEMENTATION_V1
BOUND_ORIGIN_MAIN_SHA=c889577bef56300f74039d921472f0638cbb8810
AUTHORIZED_SURFACE_ID=VOLATILITY_NUMERIC_MAX_AGE_RESEARCH_OPTIMIZATION_V1
AUTHORIZED_SURFACE_COUNT=1
RESEARCH_OPTIMIZATION_ONLY=true
PRODUCTIVE_TRADING_EFFECT=NONE
THRESHOLD_SELECTION_AUTHORIZED=false
ENFORCEMENT_AUTHORIZED=false
EXTERNAL_EFFECT_AUTHORIZED=false
```

Machine-readable decision:
`config/governance/m9_volatility_numeric_max_age_optimizable_surface_v1_decision_v1.json`

## Owner

- Registry bootstrap: `src/experiments/canonical_m9_volatility_numeric_max_age_optimizable_surface_v1.py`
- Resolver: `src/experiments/canonical_optimizable_envelope_v1.py`

## Constraint artifacts

- Owner grant: `config/governance/m9_volatility_numeric_max_age_optimizable_surface_owner_grant_v1.json`
- Domain: `config/governance/optimizable_envelope/volatility_numeric_max_age_allowed_policy_domain_v1.json`
- Bounds: `config/governance/optimizable_envelope/volatility_numeric_max_age_discrete_bounds_v1.json`
- Change rate: `config/governance/optimizable_envelope/volatility_numeric_max_age_change_rate_v1.json`
- Risk: `config/governance/optimizable_envelope/volatility_numeric_max_age_risk_constraints_v1.json`
- Evidence: `config/governance/optimizable_envelope/volatility_numeric_max_age_evidence_requirements_v1.json`

## Non-goals

- Threshold selection, enforcement, promotion, Master V2 / Double Play mutation
- Additional optimizable surfaces
- Productive trading or execution authority
