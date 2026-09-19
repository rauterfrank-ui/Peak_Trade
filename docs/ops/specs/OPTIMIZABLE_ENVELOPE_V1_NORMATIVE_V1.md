---
docs_token: DOCS_TOKEN_OPTIMIZABLE_ENVELOPE_V1_NORMATIVE_V1
status: active
scope: Optimizable envelope v1 contract and fail-closed resolver; zero authorized surfaces
capability: OPTIMIZABLE_ENVELOPE_V1_CONTRACT_AND_RESOLVER
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-19
---

# Optimizable Envelope V1 — Contract and Resolver

```text
DOCUMENT_CLASS=SUBORDINATE_GOVERNANCE_CONTRACT
AUTHORITY_RELATION=SUBORDINATE_TO_PEAK_TRADE_MASTER_RUNBOOK
WORKPACKAGE_ID=OPTIMIZABLE_ENVELOPE_V1_CONTRACT_AND_RESOLVER
BOUND_ORIGIN_MAIN_SHA=c889577bef56300f74039d921472f0638cbb8810
LEARNING_PRODUCTIVE_AUTHORITY=NONE
OPTIMIZATION_PRODUCTIVE_AUTHORITY=NONE
AUTHORIZED_SURFACE_COUNT=2
AUTHORIZED_SURFACE_IDS=VOLATILITY_NUMERIC_MAX_AGE_RESEARCH_OPTIMIZATION_V1,RESEARCH_BACKTEST_COST_GRID_FEE_SLIPPAGE_OPTIMIZATION_V1
ZERO_AUTHORIZED_PRODUCTIVE_TARGETS=true
RESEARCH_OPTIMIZATION_ONLY=true
EXTERNAL_EFFECT_AUTHORIZED=false
```

Machine-readable decision: `config/governance/optimizable_envelope_v1_decision_v1.json`

## 1. Separation

```text
SELF_LEARNING_UNIVERSE != OPTIMIZATION_UNIVERSE
OPTIMIZATION_UNIVERSE != OPTIMIZABLE_ENVELOPE_V1
```

Universe membership, evidence transfer, and envelope **contract existence** do **not** authorize
any optimizable surface. `AUTHORIZED_RESEARCH_OPTIMIZATION` is resolver vocabulary only until an
explicit owner-authorized, complete envelope is registered.

## 2. Owner

- `src/experiments/canonical_optimizable_envelope_v1.py`

## 3. Resolver (fail-closed)

Partial, missing, stale, ambiguous, or unregistered surfaces resolve to `NOT_AUTHORIZED`.
`PARTIAL` is never promoted to authorized. Owner maps are provenance evidence only.

## 4. Non-goals (deferred)

- Concrete optimizable surfaces and parameter values
- Search join, experiment-memory bind, promotion/productive apply
- Implicit authorization from existing owner maps
