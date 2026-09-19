---
docs_token: DOCS_TOKEN_OPTIMIZATION_SURFACE_FAMILIES_PRE_TEST_PREPARATION_V1
status: active
scope: Pre-test preparation matrix for CURRENT optimization parameter families; no search/OOS execution
capability: OPTIMIZATION_SURFACE_FAMILIES_PRE_TEST_PREPARATION_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-19
supersedes_status_closure: OPTIMIZATION_SURFACE_OWNER_GRANTS_MATERIALIZATION_V1
---

# Optimization Surface Families — Pre-Test Preparation V1

```text
DOCUMENT_CLASS=SUBORDINATE_GOVERNANCE_CONTRACT
AUTHORITY_RELATION=SUBORDINATE_TO_PEAK_TRADE_MASTER_RUNBOOK
WORKPACKAGE_ID=OPTIMIZATION_SURFACE_FAMILIES_PRE_TEST_PREPARATION_V1
BOUND_ORIGIN_MAIN_SHA=3abeffae801f2973408e8e613b1c03f903b08d0a
PREDECESSOR_CLOSED=NAKED_MV2_DOUBLE_PLAY_CORE_AUTHORITY_HARDENING_V1
LEARNING_PRODUCTIVE_AUTHORITY=NONE
OPTIMIZATION_PRODUCTIVE_AUTHORITY=NONE
EXTERNAL_EFFECT_AUTHORIZED=false
PRODUCTIVE_EFFECT=NONE
MV2_DOUBLE_PLAY_SOLE_TRADING_DECISION_AUTHORITY=true
CORE_BOUNDARY_CHANGED=false
TRADING_LOGIC_CHANGED=false
SEARCH_EXECUTION_AUTHORIZED=false
OOS_ROBUSTNESS_EXECUTION_AUTHORIZED=false
```

Machine-readable decision:
`config/governance/optimization_surface_families_pre_test_preparation_v1_decision_v1.json`

Code owner: `src/experiments/canonical_optimization_surface_families_pre_test_preparation_v1.py`

## 1. Purpose

Prepare every **CURRENT-relevant optimization parameter family** so that it either:

- **(A)** holds an explicit, isolated `TEST_READY` research-surface preparation record with a
  defined `TEST_ENTRY_GATE` (test phase **not** executed in this WP), or
- **(B)** terminates with a precise owner/authority blocker (`OWNER_DECISION_REQUIRED` or
  `EXCLUDED`).

PDF Concept v3 and System Atlas are navigation only (`ATLAS_AUTHORITY=NONE`).

## 2. Canonical family matrix (repo evidence)

| Gate | Family | Owner / seam | Domain | Authority boundary | Productive effect | Blocker |
| --- | --- | --- | --- | --- | --- | --- |
| **F1** | Volatility numeric max-age | `canonical_m9_*`, `canonical_volatility_numeric_max_age_parameter_research_execution_v1`, policy contract (non-enforcing) | Discrete `candidate_max_age_seconds` (operator-bound set) | Envelope-authorized research only; no enforcement/threshold selection | NONE | — |
| **F2** | Research backtest fee/slippage grid | `canonical_f2_*`, `parameter_sensitivity_v1` + Step29M grid SSOT | Discrete `fee_bps` × `slippage_bps` (9 combos) | Envelope-authorized; funding not a grid axis; OLS/signal_scale diagnostic-only elsewhere | NONE | — |
| **F3** | Strategy hyperparameter research | `parameter_sensitivity_v1` (strategy axis), `strategy_signal_binding_v1` | Per-strategy params under `strategy.*` | **Not** envelope-registered; core-touch firewall (`assert_optimization_core_touch_surface_admitted_v1`); MV2+DP sole decision | NONE | Owner grant + admission + non-core-touch scope |
| **F5-FRESH** | Pure-stack input freshness numeric | Shadow campaign `OWNER_VALUE_FUTURES_INPUT_FRESHNESS_MAX_AGE_SECONDS` | Shadow calibration protocol tokens | **Not** F1 dedupe: different owner token and seam vs MV2 volatility max-age policy | NONE | No optimizable envelope; shadow protocol only |
| **F5-SURV** | Pure-stack survival limits | Structural manifest survival tokens | Survival ratio, toxicity, leverage caps, etc. | Must not become casually optimizable | NONE | `OWNER_DECISION_REQUIRED` |
| **F5-CAP** | Pure-stack capital-slot numerics | Structural manifest capital-slot tokens | Reinvest fractions, vol floors, opportunity score floors | Must not become casually optimizable | NONE | `OWNER_DECISION_REQUIRED` |
| **META-M4–M8** | Optimization universe / meta replay plane | `canonical_optimization_universe_v1`, M7/M8 specs | Evidence identity & replay orchestration | Infrastructure only; not parameter families | NONE | `EXCLUDED` (not Gate-F1–F5 parameter surfaces) |
| **F4-Optuna** | Advanced search / Bayesian | `CANONICAL_ADVANCED_SEARCH_V1` | Search method vocabulary | No owner-authorized optimizable envelope on CURRENT main | NONE | `EXCLUDED` |
| **FUNDING-ONLY** | Funding-rate grid axis | Cost/funding bindings in backtest | Funding parameters | Explicitly out of F2 envelope non-goals | NONE | `EXCLUDED` |
| **OLS-DIAG** | OLS / signal_scale diagnostic | `parameter_sensitivity_productive_contract_v0` | `signal_scale` | `DIAGNOSTIC_ONLY` | NONE | `EXCLUDED` |
| **RISK-SIZE** | Risk / sizing grid | `parameter_sensitivity_v1` cfg path `risk_per_trade` | Risk sizing | Not in F2 allowed calibratable set; no envelope | NONE | `EXCLUDED` |

## 3. Family closure (Owner grants materialized)

| Gate | Status |
| --- | --- |
| F1 | TEST_READY |
| F2 | TEST_READY |
| F5-FRESH | TEST_READY_SHADOW_RESEARCH |
| F5-SURV | TEST_READY_PER_TOKEN_SHADOW_CALIBRATION_ONLY |
| F5-CAP | TEST_READY_PER_TOKEN_SHADOW_CALIBRATION_ONLY |
| F3 | EXCLUDED_BY_AUTHORITY_BOUNDARY |
| F4-Optuna | EXCLUDED |
| Funding-only | EXCLUDED_AS_OPTIMIZATION_AXIS |
| OLS | DIAGNOSTIC_ONLY |
| Risk/Sizing | CONSTITUTIONAL_NOT_OPTIMIZABLE |

Authorized optimizable envelope surfaces (3):

1. **F1** — `VOLATILITY_NUMERIC_MAX_AGE_RESEARCH_OPTIMIZATION_V1`
2. **F2** — `RESEARCH_BACKTEST_COST_GRID_FEE_SLIPPAGE_OPTIMIZATION_V1`
3. **F5-FRESH** — `F5_FRESH_FUTURES_INPUT_FRESHNESS_MAX_AGE_SHADOW_RESEARCH_V1` (Owner D1)

Cross-surface isolation: distinct `surface_id`, `envelope_identity`, `target_family`, owner refs,
candidate state, and resolver admission (proven in contract tests).

## 4. TEST_ENTRY_GATE (defined, not executed)

| Family | Next test phase gate (not run in this WP) |
| --- | --- |
| F1 | `PREREGISTERED_VOLATILITY_MAX_AGE_PARAMETER_RESEARCH_EXECUTION_V1` then bounded robustness evidence accumulation per M9 evidence requirements |
| F2 | `DETERMINISTIC_F2_COST_GRID_IDENTITY_REPLAY_V1` then Step29M-bounded sensitivity/OOS economic evaluation binding |
| F5-FRESH | `SHADOW_PURE_STACK_NUMERIC_EVIDENCE_PACK_VALIDATION_V1` (protocol-only; not optimizer search) |

## 5. OWNER_DECISION_REQUIRED (B)

- **F3** — strategy hyperparameter optimizable surface: requires explicit owner grant, complete
  optimizable envelope, ten-key core-touch admission metadata, and proof that variation does not
  rewrite MV2+Double Play trading-decision semantics.
- **F5-FRESH** — shadow freshness token: protocol-level test entry only until owner defines an
  optimizable envelope distinct from F1.
- **F5-SURV**, **F5-CAP** — pure-stack survival/capital numerics: explicit owner authorization
  before any research grid or envelope registration.

## 6. EXCLUDED (B)

F4-Optuna, funding-only optimization axis, OLS/signal_scale diagnostic variation, risk/sizing
grid, META-M4–M8 infrastructure plane — unless a future governed envelope explicitly authorizes
a distinct surface (not present on bound main).

## 7. Non-goals

- Running optimization, OOS, robustness, or search test campaigns
- Registering F3/F5 optimizable envelopes without owner GO
- Promotion, productive apply, instrument reselection, core mutation, external effects
