# MASTER_V2 Canonical Volatility Numeric Max-Age Parameter Research Execution v1

---
docs_token: DOCS_TOKEN_MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_PARAMETER_RESEARCH_EXECUTION_V1
STATUS: CAPABILITY_AVAILABLE
scope: non-enforcing parameter research execution for canonical volatility numeric max-age
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
NUMERIC_MAX_AGE_DECIDED: false
NUMERIC_MAX_AGE_SECONDS: null
THRESHOLD_STATUS: UNRESOLVED_MAX_AGE
ENFORCEMENT_ENABLED: false
ENFORCEMENT_APPLIED: false
NUMERIC_THRESHOLD_SELECTED: false
PARAMETER_PROMOTED: false
ALPHA_DECISION_MUTATION_ALLOWED: false
COUNTERFACTUAL_ONLY: true
HARD_STOP: true
---

> **Research execution only.** Runs the preregistered, reproducible, strictly
> non-enforcing parameter study for Canonical Volatility Numeric Max Age.
> May emit evidence and diagnostic results. Must **not** select, ratify,
> promote, or productively apply a numeric threshold.

## Machine summary

```
CAPABILITY_ID=MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_PARAMETER_RESEARCH_EXECUTION_V1
PREREGISTRATION_CONTRACT=CanonicalVolatilityMaxAgeResearchDesignContractV1
EXPECTED_PREREGISTRATION_DIGEST=965f6e09e50e434e363d380c2d62e43041a37ad7d87956e590609a16f011b537
AGE_REFERENCE_CLOCK=MARKET_EVENT_TIME
AGE_UNIT=SECONDS
AGE_FORMULA=reference_market_event_time_minus_volatility_as_of_event_time
BASELINE=UNRESOLVED_MAX_AGE_NON_ENFORCING
ENFORCEMENT_DURING_RESEARCH=false
COUNTERFACTUAL_ONLY=true
ALPHA_DECISION_MUTATION_ALLOWED=false
NUMERIC_THRESHOLD_SELECTED=false
PARAMETER_PROMOTED=false
THRESHOLD_STATUS=UNRESOLVED_MAX_AGE
HARD_STOP=true
```

## Authority boundary

| Surface | Authority |
|---|---|
| Research evidence &#47; diagnostics | this capability |
| Preregistration design &#47; join &#47; ledger schema | design accumulation contract |
| Productive Alpha &#47; entry &#47; exit &#47; risk &#47; safety | unchanged; out of scope |
| Numeric max-age selection &#47; promotion &#47; enforcement | forbidden |

## Owners

| Artifact | Path |
|---|---|
| Research execution package | `src&#47;research&#47;canonical_volatility_numeric_max_age_parameter_research_execution_v1&#47;` |
| CLI entrypoint | `scripts&#47;ops&#47;run_canonical_volatility_numeric_max_age_parameter_research_execution_v1.py` |
| Spec | this document |
| Tests | `tests&#47;research&#47;test_canonical_volatility_numeric_max_age_parameter_research_execution_v1.py` |
| Preregistration owner | `src&#47;trading&#47;master_v2&#47;canonical_volatility_numeric_max_age_parameter_research_design_and_evidence_accumulation_contract_v1.py` |

## Pre-evaluation artifacts

Before any result scoring the runner binds and digests:

1. `research_execution_manifest.json`
2. `candidate_domain.json`
3. `hypothesis_contract.json`
4. `split_and_embargo_contract.json`
5. `robustness_execution_contract.json`

Candidate values are explicit operator &#47; caller research arguments only. They
are **not** config defaults, policy literals, or productive thresholds.

## Leakage controls

- purged chronological splits
- walk-forward on non-holdout only
- sealed final holdout until terminal evaluation
- event-time embargo derived from lookback &#47; holding &#47; survival &#47; label horizons
- no random IID shuffle of overlapping samples
- no holdout-driven candidate selection
- no retrospective regime relabeling
- no future event-time labels

## Evidence output

Versioned under:

`docs&#47;evidence&#47;canonical_volatility_numeric_max_age_parameter_research_execution_v1&#47;<execution_id>&#47;`

Local evidence output is gitignored. Productive ledgers are never invented.

## Non-goals

- numeric threshold selection or single-point recommendation
- parameter promotion into productive policy &#47; config
- Alpha enforcement or decision mutation
- live &#47; testnet &#47; paper order activation
- synthetic invention of missing productive evidence

## Explicit remaining boundary

```
NEXT_AFTER_THIS_CAPABILITY=
SEPARATE_OWNER_AUTHORIZED_THRESHOLD_SELECTION_OR_FURTHER_EVIDENCE_ACCUMULATION
```

`HARD_STOP=true` remains. `READY_FOR_THRESHOLD_SELECTION=false`,
`READY_FOR_PARAMETER_PROMOTION=false`, `READY_FOR_ENFORCEMENT=false`.
)
