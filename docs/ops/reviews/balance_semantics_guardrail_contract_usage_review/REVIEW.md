# BALANCE SEMANTICS GUARDRAIL CONTRACT USAGE REVIEW

## Purpose
Define where and how the balance-semantics guardrail contract (CONTRACT.md) should be applied in the codebase, without implementing runtime behavior in this slice.

## Scope
- contract-usage review only
- no runtime mutation
- no paper&#47;shadow&#47;testnet disturbance

## Contract Reference
- `docs&#47;ops&#47;reviews&#47;balance_semantics_guardrail_runtime_contract&#47;CONTRACT.md`

## Primary Usage Point: portfolio_monitor

### Hotspot
- File: `src&#47;live&#47;portfolio_monitor.py`
- Method: `_fetch_account_data()`
- Line: 346 — `balance.get("free", balance.get("cash"))`

### Recommended Invocation
A future guardrail should be invoked **at the boundary** where raw balance data is obtained, before assigning to `account_data["cash"]`:

1. **Inputs to pass**
   - raw balance-like payload (e.g. `balance` from `fetch_balance()`)
   - source metadata: `exchange_client` type, `fetch_balance` vs `cash` attribute
   - optional reconciliation context (if available)

2. **Output handling**
   - if `semantic_state == balance_semantics_blocked`: do not populate `snapshot.cash` for decision use; surface `operator_visible_state`
   - if `semantic_state == balance_semantics_warning`: populate `snapshot.cash` only when `decision_use_allowed`; surface `operator_visible_state`
   - if `semantic_state == balance_semantics_clear`: populate `snapshot.cash` under existing controls

3. **Constraint**
   - do not silently upgrade `cash` fallback into free&#47;usable capacity; the contract must classify before assignment

### Secondary Source: PaperBroker cash attribute
- Lines 351–358: fallback via `self._exchange_client.cash`
- Different semantics (paper-only, no exchange balance structure)
- Contract invocation should treat this as a distinct source; may classify as `balance_semantics_clear` when source is explicit and non-ambiguous

## Downstream Consumers

### LiveRiskLimits.evaluate_portfolio
- File: `src&#47;live&#47;risk_limits.py`
- Uses: `snapshot.cash` → `metrics["portfolio_cash"]`
- Decision-adjacent: risk checks may rely on portfolio_cash for limits

**Usage rule:** If the guardrail has not been invoked upstream, or if `semantic_state` is `balance_semantics_blocked`, consumers should not treat `snapshot.cash` as decision-grade. The contract outputs (`decision_use_allowed`, `operator_visible_state`) should flow through or be re-checked at consumption.

### Other consumers
- Any code that reads `LivePortfolioSnapshot.cash` for decisions should respect contract outputs when the guardrail is implemented

## Integration Options

| Option | Invocation point | Pros | Cons |
|--------|------------------|------|------|
| A. At fetch boundary | `_fetch_account_data()` before returning | Single point; raw balance available | Requires refactor of return shape |
| B. At snapshot build | `snapshot()` after `_fetch_account_data()` | Clear boundary | Must pass contract outputs through |
| C. At consumption | `evaluate_portfolio()` before using `snapshot.cash` | No portfolio_monitor change | Duplicated logic; raw balance may be lost |

**Recommendation:** Option A — invoke at fetch boundary, extend `account_data` or return shape to include contract outputs (`semantic_state`, `reason_code`, `decision_use_allowed`, `operator_visible_state`) so downstream consumers can act accordingly.

## Non-Goals
- no implementation in this slice
- no live-expansion work
- no weakening of existing guardrails

## Recommended Next Slice
- balance_semantics_guardrail_integration_plan (or implementation slice when ready)
