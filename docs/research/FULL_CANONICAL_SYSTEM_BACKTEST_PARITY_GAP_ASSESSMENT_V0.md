# Full Canonical System Backtest Parity Gap Matrix v0

Assessment-only. No runtime authority. No economic evaluation.

NEXT_RECOMMENDED_SLICE=CANONICAL_ORDER_INTENT_OFFLINE_REPLAY_BINDING_PARITY_REWIRE_V0

| ID | Surface | Status | Canonical Owner(s) | Missing Binding |
|----|---------|--------|------------------|-----------------|
| A | Bull/Bear State Switch | PARTIAL | `src/trading/master_v2/double_play_state.py`, `src/trading/master_v2/directional_assessment_v1.py` | End-to-end state-switch parity Integrated tick vs Scenario tick (not only composition matrix alignment) |
| B | Scope adverse exit | PARTIAL | `src/trading/master_v2/deterministic_scope_event_generator_v1.py`, `src/trading/master_v2/double_play_entry_exit_policy_v0.py` | Scenario replay binding to deterministic_scope_event_generator_v1 + entry-exit adverse-exit path |
| C | Reversal preparation | PARTIAL | `src/trading/master_v2/double_play_composition_matrix_v1.py`, `src/trading/master_v2/double_play_entry_exit_policy_v0.py` | Scenario tick -> entry-exit REVERSAL_PREPARATION_EXIT policy evaluation |
| D | Flat-before-opposite-side invariant | PARTIAL | `src/trading/master_v2/double_play_state.py`, `src/trading/master_v2/double_play_entry_exit_policy_v0.py` | Scenario replay -> evaluate_double_play_entry_exit_policy_v0() for flat-before-opposite-side invariant |
| E | Survival and Suitability | PARTIAL | `src/trading/master_v2/survival_assessment_v1.py`, `src/trading/master_v2/suitability_binding_v1.py`, ... | Scenario direct binding to survival_assessment_v1 / suitability_binding_v1 instead of legacy envelope projection |
| F | Double Play composition | PASS | `src/trading/master_v2/double_play_composition_matrix_v1.py`, `src/trading/master_v2/double_play_composition_scenario_matrix_adapter_v0.py` | — |
| G | Entry / Position / Exit Policy | PASS | `src/trading/master_v2/double_play_entry_exit_policy_v0.py` | — |
| H | Capital / Risk / Sizing | PARTIAL | `src/governance/capital_risk_sizing_v1.py`, `src/trading/master_v2/double_play_capital_slot.py` | Backtest mv2_research_wiring_v1 unified sizing chain parity |
| I | Canonical Order Intent boundary | NOT_APPLICABLE | `src/governance/canonical_order_intent_v1.py`, `src/governance/runbook_progress_registry_v1.py` | Runtime bridge Slice B activation (out of offline assessment scope) |
| J | Safety Kernel semantics | PARTIAL | `src/meta/learning_loop/runtime_eligibility_v1.py`, `src/meta/learning_loop/killswitch_writer_fencing_and_independent_read_paths_v1.py` | Unified safety-kernel semantics across Integrated / Scenario / Runtime |
| K | KillSwitch boundary semantics | PARTIAL | `src/meta/learning_loop/killswitch_writer_fencing_and_independent_read_paths_v1.py`, `src/risk_layer/kill_switch/core.py` | Integrated replay explicit KillSwitch state-machine or kernel-read binding |
| L | Reconciliation and Unknown Outcome semantics | PARTIAL | `src/trading/master_v2/double_play_entry_exit_policy_v0.py`, `src/governance/capital_risk_sizing_v1.py`, ... | Scenario replay reconciliation/unknown-outcome fixtures + parity tests |
| M | Promotion Gate boundary | NOT_APPLICABLE | `src/governance/promotion_loop/promotion_economic_gate_v1.py`, `docs/ops/specs/MASTER_V2_PROMOTION_STATE_MACHINE_V1.md` | — |
| N | AI / Observability / Explainability boundary | PARTIAL | `src/trading/master_v2/canonical_trading_decision_evidence_v1.py`, `src/trading/master_v2/double_play_dashboard_display.py`, ... | Common explainability envelope across Integrated vs Scenario (harness extracts different field sets) |
| O | Feedback / Learning boundary | NOT_APPLICABLE | `src/meta/learning_loop/runtime_observation_feedback_v1.py`, `src/meta/learning_loop/deploy_inactive_v1.py` | — |
| P | Backtest / Offline Replay / Scenario Replay / Runtime decision parity | PARTIAL | `src/trading/master_v2/integrated_vs_scenario_replay_full_system_parity_harness_v0.py`, `src/trading/master_v2/evaluate_double_play_authority_boundary_v0.py` | Full 4-way parity suite including backtest bar wiring, runtime bridge activation, entry-exit/capital/intent surfaces |

## Summary

PARITY_SURFACES_ASSESSED=16
PASS_SURFACES=2
PARTIAL_SURFACES=11
GAP_SURFACES=0
NOT_APPLICABLE_SURFACES=3

FULL_CANONICAL_CHAIN_WIRED=false
BACKTEST_RUNTIME_DECISION_PARITY_PASS=false
SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE=false
