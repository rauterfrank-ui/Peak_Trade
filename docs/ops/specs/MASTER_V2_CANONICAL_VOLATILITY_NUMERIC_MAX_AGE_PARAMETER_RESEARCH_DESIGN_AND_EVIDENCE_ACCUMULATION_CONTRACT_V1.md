# MASTER_V2 Canonical Volatility Numeric Max-Age Parameter Research Design And Evidence Accumulation Contract v1

---
docs_token: DOCS_TOKEN_MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_PARAMETER_RESEARCH_DESIGN_AND_EVIDENCE_ACCUMULATION_CONTRACT_V1
STATUS: CAPABILITY_AVAILABLE
scope: research prerequisites for later operator-authorized numeric max-age research
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
NUMERIC_MAX_AGE_DECIDED: false
NUMERIC_MAX_AGE_SECONDS: null
THRESHOLD_STATUS: UNRESOLVED_MAX_AGE
ENFORCEMENT_ENABLED: false
ENFORCEMENT_APPLIED: false
ALPHA_ENFORCEMENT_ALLOWED: false
PARAMETER_RESEARCH_EXECUTED: false
THRESHOLD_SELECTED: false
HARD_STOP: true
---

> **Research-design and evidence-accumulation only.** Closes productive
> reuse &#47; restart labeling into non-enforcing age telemetry, a typed research
> evidence join, deterministic counterfactual diagnostics without enforcement,
> preregistered dimensions &#47; metrics &#47; controls, and a durable multi-session &#47;
> multi-regime ledger path. Does **not** select a numeric threshold, recommend
> candidates, execute parameter research, or enable Alpha enforcement.

## Machine summary

```
CAPABILITY_ID=MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_PARAMETER_RESEARCH_DESIGN_AND_EVIDENCE_ACCUMULATION_CONTRACT_V1
PREREGISTRATION_CONTRACT_VERSION=canonical_volatility_numeric_max_age_research_preregistration/v1
JOIN_CONTRACT_VERSION=canonical_volatility_numeric_max_age_research_evidence_join/v1
ACCUMULATION_LEDGER_VERSION=canonical_volatility_numeric_max_age_research_evidence_ledger/v1
AGE_REFERENCE_CLOCK=MARKET_EVENT_TIME
THRESHOLD_STATUS=UNRESOLVED_MAX_AGE
NUMERIC_MAX_AGE_SECONDS=null
ENFORCEMENT_ENABLED=false
ENFORCEMENT_APPLIED=false
ALPHA_ENFORCEMENT_ALLOWED=false
PARAMETER_RESEARCH_EXECUTED=false
THRESHOLD_SELECTED=false
COUNTERFACTUAL_ENFORCEMENT_ENABLED=false
PRESENCE_GATE_AUTHORITY_UNCHANGED=true
EXIT_RISK_SAFETY_INDEPENDENCE_MUST_REMAIN=true
EVENT_TIME_IS_AGE_AUTHORITY=true
WALLCLOCK_IS_NOT_AGE_AUTHORITY=true
REUSE_MUST_NOT_REFRESH_ESTIMATE_AS_OF=true
RESTART_MUST_NOT_REMATERIALIZE_VOLATILITY=true
LIVE_AUTHORIZATION=false
HARD_STOP=true
```

## Goals

1. Productive reuse &#47; restart labels wired into age telemetry
2. Typed research evidence join contract with identity &#47; conflict fail-closed
3. Deterministic counterfactual evaluation without enforcement
4. Complete machine-readable preregistration &#47; digested design contract
5. Durable multi-session &#47; multi-regime evidence accumulation with ledger integrity

## Non-goals

- numeric `max_age_seconds` selection or recommendation
- parameter research execution
- Alpha &#47; entry suppression by age
- Exit &#47; Risk &#47; Safety authority changes
- Live &#47; Testnet &#47; Paper &#47; Shadow activation
- new volatility estimator or Alpha default
- second decision authority or freshness-precedence change
- automatic repair &#47; truncation of corrupt ledgers

## TEIL A — Productive reuse &#47; restart wiring

Producer &#47; binding outcomes map to typed age labels via
`derive_reuse_and_restart_status_for_age_policy_v1` and are attached through:

```
CanonicalVolatilityProductiveRuntimeCmcTypedBindingHostV1
  → telemetry.reuse_status / telemetry.restart_status
  → evaluate_double_play_runtime_typed_volatility_presence_gate_v1(...)
  → evaluate_canonical_volatility_estimate_age_policy_v1(...)
```

### reuse_status

- `NOT_APPLICABLE`
- `FRESHLY_PRODUCED`
- `NO_SAMPLE_REUSE`
- `DUPLICATE_SAMPLE_REUSE`
- `OUT_OF_ORDER_REJECTED_REUSE`
- `WARMUP_WITHOUT_ESTIMATE`
- `UNKNOWN`

### restart_status

- `NOT_APPLICABLE`
- `RESTART_WITHOUT_ESTIMATE`
- `FIRST_PRODUCTION_AFTER_RESTART`
- `UNKNOWN`

Producer persistence restores mark-history only and does **not** rematerialize
a typed estimate across process restart. Therefore restore is labeled
`RESTART_WITHOUT_ESTIMATE` until a fresh `PRODUCED` estimate. There is no
restored-existing-estimate restart status.

Reuse must not refresh `as_of_event_time`. Restart &#47; restore must not
rematerialize volatility as a freshness reset.

## Machine-readable preregistration

`CanonicalVolatilityMaxAgeResearchDesignContractV1` is immutable, versioned,
and SHA-256 digested (`preregistration_digest`). Required fields:

- `research_question`
- `candidate_threshold_source`
- `candidate_dimensions`
- `dataset_scope`
- `session_scope`
- `instrument_scope`
- `regime_dimensions`
- `metrics`
- `cost_assumptions`
- `leakage_controls`
- `purged_split_policy`
- `embargo_policy`
- `walk_forward_design`
- `stress_controls`
- `robustness_controls`
- `rejection_criteria`
- `selection_criteria`
- `final_holdout_policy`
- `minimum_evidence_requirements`
- `threshold_status` (`UNRESOLVED_MAX_AGE`)
- `enforcement_applied` (`false`)

Selection criteria require robust regions, costs, drawdown, parameter
stability, multi-session &#47; multi-regime agreement, and sealed final holdout
confirmation. Point-selection by best Sharpe, maximum PnL, maximum trade
count, or single best configuration is rejected.

No concrete numeric max-age candidate values are introduced by this
capability.

## Research evidence join

`CanonicalVolatilityMaxAgeResearchEvidenceJoinV1` joins age evidence with
producer &#47; binding labels, regime &#47; session strata, decision outcome, and
economic metrics.

Required nonempty identities:

- `session_id`
- `cycle_id`
- `instrument_id`
- `regime_id`
- `join_contract_version`
- `threshold_status`

Empty &#47; whitespace identities fail closed. Identity conflicts across cycle,
binding, presence-gate, and age-evidence projections fail closed
(`cross_session_join_conflict`, `cross_instrument_join_conflict`,
`cross_cycle_join_conflict`). Productive `threshold_status` remains
`UNRESOLVED_MAX_AGE` and `enforcement_applied=false`.

## Counterfactual path

`evaluate_counterfactual_max_age_threshold_diagnostic_v1` accepts a
caller-supplied candidate argument for diagnostic labeling only
(`WOULD_BE_FRESH_IF_THRESHOLD` &#47; `WOULD_BE_STALE_IF_THRESHOLD`). It must not
mutate Alpha decisions, demote trading gates, or ratify a threshold.

## Evidence accumulation

Hardening-bridge cycles attach
`canonical_volatility_max_age_research_evidence_join` and accumulate into:

- in-memory `HardenedBridgeSessionStateV2.max_age_research_evidence_ledger`
- optional durable JSONL via `max_age_research_evidence_ledger_path`

### Ledger record identity

Business identity:

`join_contract_version + session_id + cycle_id + instrument_id`

Full record identity additionally includes `join_digest`.

### Duplicate policy

- identical business identity + identical digest → idempotent no-op on append
- identical business identity + divergent digest → contract error conflict
- new identity → append

### Load integrity

`load_max_age_research_evidence_ledger_v1` fail-closes on:

- corrupt JSON (`ledger_corrupt_json`)
- schema &#47; nonempty identity failures
- recomputed `join_digest` mismatch
- `threshold_status != UNRESOLVED_MAX_AGE`
- `enforcement_applied=true`
- `numeric_threshold_selected=true`
- duplicate &#47; conflict rows already persisted

No silent repair or truncation of corrupt ledgers.

Default durable relative path:

`docs&#47;evidence&#47;canonical_volatility_numeric_max_age_research_evidence_ledger_v1&#47;research_evidence_ledger.jsonl`

## Explicit remaining boundary

```
NEXT_AFTER_THIS_CAPABILITY=
SEPARATE_OPERATOR_AUTHORIZED_NUMERIC_MAX_AGE_PARAMETER_RESEARCH_AND_SELECTION
```

That later capability requires separate operator authorization and is **not**
part of this delivery. Numeric max-age remains unresolved; enforcement remains
disabled.

## Owners

| Artifact | Path |
|---|---|
| Research design &#47; join &#47; counterfactual &#47; ledger | `src&#47;trading&#47;master_v2&#47;canonical_volatility_numeric_max_age_parameter_research_design_and_evidence_accumulation_contract_v1.py` |
| Reuse &#47; restart labels | `src&#47;trading&#47;master_v2&#47;canonical_volatility_numeric_max_age_policy_contract_and_non_enforcing_telemetry_v1.py` |
| Binding telemetry | `src&#47;trading&#47;master_v2&#47;canonical_volatility_productive_runtime_cmc_typed_binding_v1.py` |
| Bridge wiring | `src&#47;ops&#47;wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2&#47;hardening_cycle_bridge_v2.py` |
| Spec | this document |
| Tests | `tests&#47;trading&#47;master_v2&#47;test_canonical_volatility_numeric_max_age_parameter_research_design_and_evidence_accumulation_contract_v1.py` |
