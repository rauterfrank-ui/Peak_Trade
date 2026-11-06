# Canonical Chain Trace

**Orchestrator (offline productive):** `run_integrated_offline_trading_logic_replay_v1`  
**Wiring:** `run_mv2_research_backtest_wiring_v1` / `mv2_research_wiring_v1.py`  
**Authority quarantine:** `double_play_sole_authority_quarantine_v1` (`RUNTIME_BRIDGE_STATUS=BOUND_NOT_ACTIVATED`)

Code-order note: composition runs before `transition_state` in the orchestrator, but consumes pre-transition scope/CHOP projections. Stages below follow logical authority order toward a trade.

| # | Stage | Owner (file::symbol) | Producer | Consumer | Input | Output | Status | Class |
|---|-------|----------------------|----------|----------|-------|--------|--------|-------|
| 1 | Strategy Signal | `backtest&#47;strategy_signal_binding_v1.py::execute_configured_strategy_signal_series_v1` | Strategy series (e.g. Bollinger) | Agreement normalizer | Bars + strategy config | `StrategySignalBindingResultV1` (`cycle_signal_value`) | **BOUND** | NON_AUTHORITY (raw signal) |
| 2 | Canonical Market Context | `trading&#47;master_v2&#47;canonical_market_context_v1.py::bind_canonical_market_context_event` | MV2 bar binding | Orchestrator / scope init | Bar/mark/features | `CanonicalMarketContextV1` | **BOUND** | AUTHORITY |
| 3 | Canonical Scope / RuntimeScopeState | `canonical_scope_initialization_v1.py::initialize_canonical_scope` + `double_play_state.py::RuntimeScopeState` | CMC + prior scope | Trailing + events + switch | CMC, prior state | Scope snapshot + runtime scope | **BOUND** | AUTHORITY |
| 4 | Dynamic Scope Update | `double_play_state.py::update_dynamic_boundaries` | Orchestrator (mark + active side) | Scope-event generator | mark, ActiveSide, rules | Trailing boundaries | **BOUND** | AUTHORITY |
| 5 | Scope Event | `deterministic_scope_event_generator_v1.py::generate_deterministic_scope_event` | Trailing-aware scope | `transition_state` / CHOP policy | Scope + distances | Deterministic `ScopeEvent` | **BOUND** (scenario injection fail-closed) | AUTHORITY |
| 6 | transition_state / Dynamic Switch | `double_play_state.py::transition_state` (+ `apply_chop_scope_event_policy_v1`) | Mapped scope event | Entry/exit / continuity | SideState, ScopeEvent, envelope | Next SideState + TransitionDecision | **BOUND** | AUTHORITY |
| 7 | Bull-or-Bear selected future | `directional_assessment_v1.py::evaluate_directional_assessment_v1` + `double_play_composition_matrix_v1.py` | Dual-lane DA | Survival/suitability/composition | CMC/price path, scope ref | Bull/Bear assessments; later `selected_side` | **BOUND** machinery; direction unresolved on Bollinger funnel | AUTHORITY inputs / composition AUTHORITY |
| 8 | Agreement / Composition | `strategy_signal_suitability_agreement_adapter_v1.py::_resolve_entry_side_carrier_v1` → `mv2_research_wiring_v1.py::resolve_agreement_bound_directional_cycle_v1` → `double_play_composition_matrix_v1.py` | Strategy agreement material | Entry/exit + evidence | encoding, cycle, **entry_side**, DA/suit | Direction or unresolved; CompositionStatus | **BOUND** contracts; productive Bollinger **FAIL_CLOSED** on `entry_side=NONE` → observe | AUTHORITY |
| 9 | CRS / Order Intent | CRS: `capital_risk_sizing_offline_replay_binding_adapter_v0.py` · OI: `canonical_order_intent_offline_replay_binding_adapter_v0.py` | Decision evidence | Plan-only / parity envelopes | Actionable decision + capital | CRS decision / CanonicalOrderIntent | **BOUND_OFFLINE**; funnel **NOT_REACHED** as blocker | AUTHORITY (offline non-activating) |
| 10 | Risk / Sizing | `governance&#47;capital_risk_sizing_v1.py::evaluate_capital_risk_sizing_v1` | CRS adapter | Order-intent builder | Side, equity, stop, qty constraints | `CapitalRiskSizingDecisionV1` | **BOUND**; funnel **NOT_REACHED** | AUTHORITY |
| 11 | Quantity Status | CRS provenance + `double_play_entry_exit_policy_v0.py` default | Entry/exit / CRS | Evidence + eligibility | Sizing / policy | `NOT_BOUND` \| `PASS` \| `REDUCE` \| `BLOCK` | Offline default **NOT_BOUND**; funnel **NOT_REACHED** | AUTHORITY field |
| 12 | Execution Eligibility | `double_play_entry_exit_policy_v0.py::evaluate_double_play_entry_exit_policy_v0` | Entry/exit | Bridge / intent pipeline | Composition + gates | `execution_eligible=false` offline | **BOUND** + **FAIL_CLOSED** | AUTHORITY veto |
| 13 | Trade Intent | `governance&#47;canonical_order_intent_v1.py::build_canonical_order_intent_v1` | OI offline binding | Plan-only boundary | Sizing + action/side | Intent with submission blocked | **BOUND**; typically not materialized on observe | AUTHORITY |
| 14 | Execution Kernel | `canonical_core_runtime_integration_bridge_v0.py` + `plan_only_boundary_v0.py` | Intent / evidence | (none activated) | Plan + flags | Plan-only PASS; `BOUND_NOT_ACTIVATED` | **BOUND** + **NOT_ACTIVATED** | AUTHORITY (block) / NON_AUTHORITY (live unlock) |

## First trade block on productive zero-trade funnel

**Stage 8 — Agreement / Composition** (see `first_real_blocker.md`).

Downstream stages 9–14 are not reached as economic blockers on the Bollinger panel funnel. Runtime bridge `BOUND_NOT_ACTIVATED` is intentional live policy and is **not** the offline funnel’s first causal fail.

## Prior reaudit anchors (still consistent)

- `docs/product/evidence/read_only_canonical_chain_and_zero_trade_blocker_reaudit_v1_20260717T235727Z/decision.json`
- Dominant first failed stage: `directional_agreement` / `entry_side=NONE`
- `TRADE_COUNT=0`, `RUNTIME_BRIDGE_STATE=BOUND_NOT_ACTIVATED`
