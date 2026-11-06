# BALANCE SEMANTICS GUARDRAIL INTEGRATION PLAN

## Purpose
Define a docs-first integration plan for wiring the balance-semantics guardrail into the codebase, without implementing runtime behavior in this slice.

## Scope
- integration plan only
- no runtime mutation
- no paper&#47;shadow&#47;testnet disturbance

## References
- Contract: `docs&#47;ops&#47;reviews&#47;balance_semantics_guardrail_runtime_contract&#47;CONTRACT.md`
- Usage review: `docs&#47;ops&#47;reviews&#47;balance_semantics_guardrail_contract_usage_review&#47;REVIEW.md`

## Integration Target
- Primary: `src&#47;live&#47;portfolio_monitor.py` — `_fetch_account_data()` (line 346)
- Downstream: `src&#47;live&#47;risk_limits.py` — `evaluate_portfolio()` consuming `snapshot.cash`

## Phases

### Phase 1: Guardrail Classifier (Stub Implementation)
- Implement a narrow classifier that accepts raw balance payload and source metadata
- Returns contract outputs: `semantic_state`, `reason_code`, `decision_use_allowed`, `operator_visible_state`
- Unit-testable in isolation
- No callers yet; classifier is a pure function or small module

**Preconditions:**
- Treasury&#47;Balance Spec V2 and reconciliation docs remain the source of truth
- Classification rules align with CONTRACT.md semantic rules

### Phase 2: Extend portfolio_monitor Return Shape
- Extend `_fetch_account_data()` return to include contract outputs alongside `equity`, `cash`, `margin_used`
- Invoke classifier at fetch boundary (Option A from usage review) before assigning `cash`
- For `fetch_balance()` path: pass raw `balance` and source metadata to classifier
- For PaperBroker `cash` fallback: pass distinct source metadata; classifier may return `balance_semantics_clear` when source is explicit
- Do not populate `cash` for decision use when `semantic_state == balance_semantics_blocked`
- When `balance_semantics_warning`: populate `cash` only if `decision_use_allowed`; surface `operator_visible_state`

**Preconditions:**
- Phase 1 classifier is implemented and tested
- No silent upgrade of `cash` fallback into free&#47;usable capacity

### Phase 3: Extend LivePortfolioSnapshot
- Add optional fields for contract outputs: `balance_semantic_state`, `balance_reason_code`, `balance_operator_visible_state`
- Populate from `account_data` when present
- Downstream consumers can read these to decide whether to treat `snapshot.cash` as decision-grade

**Preconditions:**
- Phase 2 complete
- Backward compatible: existing callers continue to work; new fields are optional

### Phase 4: Downstream Consumer Handling
- In `LiveRiskLimits.evaluate_portfolio()`: when `snapshot.cash` is used for `metrics["portfolio_cash"]`, respect `balance_semantic_state`
- If `balance_semantics_blocked`: do not add `portfolio_cash` to decision-grade metrics, or add with explicit "not decision-grade" flag
- If `balance_semantics_warning`: include operator-visible state in alerts&#47;metrics
- Document any other consumers of `LivePortfolioSnapshot.cash` and apply same rules

**Preconditions:**
- Phase 3 complete
- No weakening of existing risk limits; conservative interpretation preserved

## Order of Execution
1. Phase 1 (classifier)
2. Phase 2 (fetch boundary integration)
3. Phase 3 (snapshot extension)
4. Phase 4 (consumer handling)

Phases 2–4 may be split into smaller PRs; Phase 1 should be merged before Phase 2.

## Rollout Constraints
- Validate on paper&#47;shadow before any live exposure
- No change to live trading behavior until guardrail is fully validated
- Preserve alignment with incident&#47;runbook semantics

## Non-Goals
- no implementation in this slice
- no live-expansion work
- no weakening of existing guardrails

## Recommended Next Slice
- balance_semantics_guardrail_classifier_stub (implementation) or further refinement of this plan
