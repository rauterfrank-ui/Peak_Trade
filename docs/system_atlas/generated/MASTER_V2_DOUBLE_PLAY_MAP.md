<!-- GENERATED/DO_NOT_EDIT -->
<!-- generator: scripts/ops/generate_system_atlas_v1.py -->
<!-- atlas_authority: NONE -->
<!-- schema_version: system_atlas.v1 -->

# Master V2 / Double Play Map

`ATLAS_AUTHORITY=NONE`  
`ATLAS_ROLE=EVIDENCE_BOUND_SYSTEM_TOPOLOGY_AND_NAVIGATION`  
`CANONICAL_AUTHORITY_IS_EXTERNAL_TO_ATLAS=true`  
`ATLAS_MUST_CITE_AUTHORITY=true`  
`ATLAS_MUST_NOT_CREATE_AUTHORITY=true`

Owner-bound Atlas relation (exact token `HAS_FUNCTIONAL_CORE` not found on origin/main): Master V2 and Double Play are Modul-Owner of one Trading Core. Census kind `FUNCTIONAL_CORE` is a label, not a Master Runbook token.

Not competing generations. Historical Vollautonomie ordering vs current Master Runbook ordering is CONTRADICTED (see C-DP-ORDER-001). Cap23 exclusivity is scoped to the analytical host; canary is a parallel instrument authority (C-CAP23-VS-CANARY-INSTRUMENT-001).

## Entities

| id | kind | status | epistemic |
| --- | --- | --- | --- |
| FUNCTIONAL_CORE:double_play | FUNCTIONAL_CORE | STILL_CURRENT_AND_CANONICALLY_SUPPORTED | STATUS=CANONICAL_AUTHORITY |
| SUBSYSTEM:master_v2 | SUBSYSTEM | STILL_CURRENT_AND_CANONICALLY_SUPPORTED | STATUS=CANONICAL_AUTHORITY |
| TERM:master_v2 | TERM | STILL_CURRENT_AND_CANONICALLY_SUPPORTED | STATUS=CANONICAL_AUTHORITY |

## Relations involving Master V2 / Double Play

| id | source | type | target | epistemic | evidence |
| --- | --- | --- | --- | --- | --- |
| REL:s_dp_contains_dp_capital_slot | FUNCTIONAL_CORE:double_play | CONTAINS | RUNTIME_COMPONENT:dp_capital_slot | STATUS=ADJUDICATED | src/trading/master_v2/double_play_composition.py,docs/system_atlas/census/master_v2_semantic_map.yaml |
| REL:s_dp_contains_dp_composition | FUNCTIONAL_CORE:double_play | CONTAINS | RUNTIME_COMPONENT:dp_composition | STATUS=ADJUDICATED | src/trading/master_v2/double_play_composition.py,docs/system_atlas/census/master_v2_semantic_map.yaml |
| REL:s_dp_contains_dp_core_wiring | FUNCTIONAL_CORE:double_play | CONTAINS | RUNTIME_COMPONENT:dp_core_wiring | STATUS=ADJUDICATED | src/trading/master_v2/double_play_composition.py,docs/system_atlas/census/master_v2_semantic_map.yaml |
| REL:s_dp_contains_dp_futures_input | FUNCTIONAL_CORE:double_play | CONTAINS | RUNTIME_COMPONENT:dp_futures_input | STATUS=ADJUDICATED | src/trading/master_v2/double_play_composition.py,docs/system_atlas/census/master_v2_semantic_map.yaml |
| REL:s_dp_contains_dp_state | FUNCTIONAL_CORE:double_play | CONTAINS | RUNTIME_COMPONENT:dp_state | STATUS=ADJUDICATED | src/trading/master_v2/double_play_composition.py,docs/system_atlas/census/master_v2_semantic_map.yaml |
| REL:s_dp_contains_dp_suitability | FUNCTIONAL_CORE:double_play | CONTAINS | RUNTIME_COMPONENT:dp_suitability | STATUS=ADJUDICATED | src/trading/master_v2/double_play_composition.py,docs/system_atlas/census/master_v2_semantic_map.yaml |
| REL:s_dp_contains_dp_survival | FUNCTIONAL_CORE:double_play | CONTAINS | RUNTIME_COMPONENT:dp_survival | STATUS=ADJUDICATED | src/trading/master_v2/double_play_composition.py,docs/system_atlas/census/master_v2_semantic_map.yaml |
| REL:s_master_v2_has_dp | SUBSYSTEM:master_v2 | HAS_FUNCTIONAL_CORE | FUNCTIONAL_CORE:double_play | STATUS=ADJUDICATED | docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md,docs/architecture/PEAK_TRADE_CANONICAL_UNIFIED_TRADING_SYSTEM_RUNBOOK_V2_6.md |
| REL:s_mv2_contains_dp_capital_slot | SUBSYSTEM:master_v2 | CONTAINS | RUNTIME_COMPONENT:dp_capital_slot | STATUS=FORENSIC_RAW | docs/system_atlas/census/master_v2_semantic_map.yaml |
| REL:s_mv2_contains_dp_composition | SUBSYSTEM:master_v2 | CONTAINS | RUNTIME_COMPONENT:dp_composition | STATUS=FORENSIC_RAW | docs/system_atlas/census/master_v2_semantic_map.yaml |
| REL:s_mv2_contains_dp_core_wiring | SUBSYSTEM:master_v2 | CONTAINS | RUNTIME_COMPONENT:dp_core_wiring | STATUS=FORENSIC_RAW | docs/system_atlas/census/master_v2_semantic_map.yaml |
| REL:s_mv2_contains_dp_dashboard_display | SUBSYSTEM:master_v2 | CONTAINS | RUNTIME_COMPONENT:dp_dashboard_display | STATUS=FORENSIC_RAW | docs/system_atlas/census/master_v2_semantic_map.yaml |
| REL:s_mv2_contains_dp_entry_exit_policy | SUBSYSTEM:master_v2 | CONTAINS | RUNTIME_COMPONENT:dp_entry_exit_policy | STATUS=FORENSIC_RAW | docs/system_atlas/census/master_v2_semantic_map.yaml |
| REL:s_mv2_contains_dp_evaluate_authority_boundary | SUBSYSTEM:master_v2 | CONTAINS | RUNTIME_COMPONENT:dp_evaluate_authority_boundary | STATUS=FORENSIC_RAW | docs/system_atlas/census/master_v2_semantic_map.yaml |
| REL:s_mv2_contains_dp_futures_input | SUBSYSTEM:master_v2 | CONTAINS | RUNTIME_COMPONENT:dp_futures_input | STATUS=FORENSIC_RAW | docs/system_atlas/census/master_v2_semantic_map.yaml |
| REL:s_mv2_contains_dp_offline_scenario_replay | SUBSYSTEM:master_v2 | CONTAINS | RUNTIME_COMPONENT:dp_offline_scenario_replay | STATUS=FORENSIC_RAW | docs/system_atlas/census/master_v2_semantic_map.yaml |
| REL:s_mv2_contains_dp_sole_authority_quarantine | SUBSYSTEM:master_v2 | CONTAINS | RUNTIME_COMPONENT:dp_sole_authority_quarantine | STATUS=FORENSIC_RAW | docs/system_atlas/census/master_v2_semantic_map.yaml |
| REL:s_mv2_contains_dp_state | SUBSYSTEM:master_v2 | CONTAINS | RUNTIME_COMPONENT:dp_state | STATUS=FORENSIC_RAW | docs/system_atlas/census/master_v2_semantic_map.yaml |
| REL:s_mv2_contains_dp_suitability | SUBSYSTEM:master_v2 | CONTAINS | RUNTIME_COMPONENT:dp_suitability | STATUS=FORENSIC_RAW | docs/system_atlas/census/master_v2_semantic_map.yaml |
| REL:s_mv2_contains_dp_survival | SUBSYSTEM:master_v2 | CONTAINS | RUNTIME_COMPONENT:dp_survival | STATUS=FORENSIC_RAW | docs/system_atlas/census/master_v2_semantic_map.yaml |
| REL:s_mv2_contains_dp_volatility_presence_gate | SUBSYSTEM:master_v2 | CONTAINS | RUNTIME_COMPONENT:dp_volatility_presence_gate | STATUS=FORENSIC_RAW | docs/system_atlas/census/master_v2_semantic_map.yaml |
| REL:s_mv2_contains_mv2_arithmetic_decimal | SUBSYSTEM:master_v2 | CONTAINS | RUNTIME_COMPONENT:mv2_arithmetic_decimal | STATUS=FORENSIC_RAW | docs/system_atlas/census/master_v2_semantic_map.yaml |
| REL:s_mv2_contains_mv2_canonical_market_context | SUBSYSTEM:master_v2 | CONTAINS | RUNTIME_COMPONENT:mv2_canonical_market_context | STATUS=FORENSIC_RAW | docs/system_atlas/census/master_v2_semantic_map.yaml |
| REL:s_mv2_contains_mv2_canonical_scope | SUBSYSTEM:master_v2 | CONTAINS | RUNTIME_COMPONENT:mv2_canonical_scope | STATUS=FORENSIC_RAW | docs/system_atlas/census/master_v2_semantic_map.yaml |
| REL:s_mv2_contains_mv2_canonical_trading_decision_evidence | SUBSYSTEM:master_v2 | CONTAINS | RUNTIME_COMPONENT:mv2_canonical_trading_decision_evidence | STATUS=FORENSIC_RAW | docs/system_atlas/census/master_v2_semantic_map.yaml |
| REL:s_mv2_contains_mv2_canonical_volatility | SUBSYSTEM:master_v2 | CONTAINS | RUNTIME_COMPONENT:mv2_canonical_volatility | STATUS=FORENSIC_RAW | docs/system_atlas/census/master_v2_semantic_map.yaml |
| REL:s_mv2_contains_mv2_capital_risk_sizing | SUBSYSTEM:master_v2 | CONTAINS | RUNTIME_COMPONENT:mv2_capital_risk_sizing | STATUS=FORENSIC_RAW | docs/system_atlas/census/master_v2_semantic_map.yaml |
| REL:s_mv2_contains_mv2_decision_packet | SUBSYSTEM:master_v2 | CONTAINS | RUNTIME_COMPONENT:mv2_decision_packet | STATUS=FORENSIC_RAW | docs/system_atlas/census/master_v2_semantic_map.yaml |
| REL:s_mv2_contains_mv2_directional_assessment | SUBSYSTEM:master_v2 | CONTAINS | RUNTIME_COMPONENT:mv2_directional_assessment | STATUS=FORENSIC_RAW | docs/system_atlas/census/master_v2_semantic_map.yaml |
| REL:s_mv2_contains_mv2_input_happy_path | SUBSYSTEM:master_v2 | CONTAINS | RUNTIME_COMPONENT:mv2_input_happy_path | STATUS=FORENSIC_RAW | docs/system_atlas/census/master_v2_semantic_map.yaml |
| REL:s_mv2_contains_mv2_integrated_replay | SUBSYSTEM:master_v2 | CONTAINS | RUNTIME_COMPONENT:mv2_integrated_replay | STATUS=FORENSIC_RAW | docs/system_atlas/census/master_v2_semantic_map.yaml |
| REL:s_mv2_contains_mv2_local_evaluator | SUBSYSTEM:master_v2 | CONTAINS | RUNTIME_COMPONENT:mv2_local_evaluator | STATUS=FORENSIC_RAW | docs/system_atlas/census/master_v2_semantic_map.yaml |
| REL:s_mv2_contains_mv2_offline_boundary_adapters | SUBSYSTEM:master_v2 | CONTAINS | RUNTIME_COMPONENT:mv2_offline_boundary_adapters | STATUS=FORENSIC_RAW | docs/system_atlas/census/master_v2_semantic_map.yaml |
| REL:s_mv2_contains_mv2_package_init | SUBSYSTEM:master_v2 | CONTAINS | RUNTIME_COMPONENT:mv2_package_init | STATUS=FORENSIC_RAW | docs/system_atlas/census/master_v2_semantic_map.yaml |
| REL:s_mv2_contains_mv2_parity_gap_assessment | SUBSYSTEM:master_v2 | CONTAINS | RUNTIME_COMPONENT:mv2_parity_gap_assessment | STATUS=FORENSIC_RAW | docs/system_atlas/census/master_v2_semantic_map.yaml |
| REL:s_mv2_contains_mv2_post_confirmation_ssc | SUBSYSTEM:master_v2 | CONTAINS | RUNTIME_COMPONENT:mv2_post_confirmation_ssc | STATUS=FORENSIC_RAW | docs/system_atlas/census/master_v2_semantic_map.yaml |
| REL:s_mv2_contains_mv2_pr4985_materiality_classifier | SUBSYSTEM:master_v2 | CONTAINS | RUNTIME_COMPONENT:mv2_pr4985_materiality_classifier | STATUS=FORENSIC_RAW | docs/system_atlas/census/master_v2_semantic_map.yaml |
| REL:s_mv2_contains_mv2_regime_bull_bear_readmodel | SUBSYSTEM:master_v2 | CONTAINS | RUNTIME_COMPONENT:mv2_regime_bull_bear_readmodel | STATUS=FORENSIC_RAW | docs/system_atlas/census/master_v2_semantic_map.yaml |
| REL:s_mv2_contains_mv2_runtime_bridge | SUBSYSTEM:master_v2 | CONTAINS | RUNTIME_COMPONENT:mv2_runtime_bridge | STATUS=FORENSIC_RAW | docs/system_atlas/census/master_v2_semantic_map.yaml |
| REL:s_mv2_contains_mv2_scenario_matrix | SUBSYSTEM:master_v2 | CONTAINS | RUNTIME_COMPONENT:mv2_scenario_matrix | STATUS=FORENSIC_RAW | docs/system_atlas/census/master_v2_semantic_map.yaml |
| REL:s_mv2_contains_mv2_scope_events | SUBSYSTEM:master_v2 | CONTAINS | RUNTIME_COMPONENT:mv2_scope_events | STATUS=FORENSIC_RAW | docs/system_atlas/census/master_v2_semantic_map.yaml |
| REL:s_mv2_contains_mv2_strategy_identity | SUBSYSTEM:master_v2 | CONTAINS | RUNTIME_COMPONENT:mv2_strategy_identity | STATUS=FORENSIC_RAW | docs/system_atlas/census/master_v2_semantic_map.yaml |
| REL:s_mv2_contains_mv2_surface_p | SUBSYSTEM:master_v2 | CONTAINS | RUNTIME_COMPONENT:mv2_surface_p | STATUS=FORENSIC_RAW | docs/system_atlas/census/master_v2_semantic_map.yaml |

## Family/Child/MMR records (heterogeneous meanings; not collapsed)

| id | parent | type | child | meaning_class | epistemic |
| --- | --- | --- | --- | --- | --- |
| FCM:architectural_mmr | SUBSYSTEM:master_v2 | HAS_MMR | TERM:mmr_polyvalent | architectural_unproven | STATUS=OPEN (not proven) |
| FCM:dashboard_canonical_decision | SYSTEM:peak_trade | HAS_FAMILY | FAMILY:dashboard_canonical_decision | dashboard_family_id | STATUS=FORENSIC_RAW |
| FCM:dashboard_double_play | SYSTEM:peak_trade | HAS_FAMILY | FAMILY:dashboard_double_play | dashboard_family_id | STATUS=FORENSIC_RAW |
| FCM:dashboard_dynamic_scope | SYSTEM:peak_trade | HAS_FAMILY | FAMILY:dashboard_dynamic_scope | dashboard_family_id | STATUS=FORENSIC_RAW |
| FCM:dashboard_econ | SYSTEM:peak_trade | HAS_FAMILY | FAMILY:dashboard_economic_summary | dashboard_family_id | STATUS=FORENSIC_RAW |
| FCM:dashboard_exec_recon | SYSTEM:peak_trade | HAS_FAMILY | FAMILY:dashboard_execution_reconciliation | dashboard_family_id | STATUS=FORENSIC_RAW |
| FCM:dashboard_regime | SYSTEM:peak_trade | HAS_FAMILY | FAMILY:dashboard_regime_bull_bear | dashboard_family_id | STATUS=FORENSIC_RAW |
| FCM:dashboard_risk | SYSTEM:peak_trade | HAS_FAMILY | FAMILY:dashboard_risk_sizing_capital | dashboard_family_id | STATUS=FORENSIC_RAW |
| FCM:dashboard_safety | SYSTEM:peak_trade | HAS_FAMILY | FAMILY:dashboard_safety_authority | dashboard_family_id | STATUS=FORENSIC_RAW |
| FCM:falls_parent_child | FORENSIC_REFERENCE:information_corpus_persistence_base | HAS_CHILD | TERM:falls_parent_child | forensic_falls_coupling | STATUS=HISTORICAL |
| FCM:master_v2_functional_core | SUBSYSTEM:master_v2 | HAS_FUNCTIONAL_CORE | FUNCTIONAL_CORE:double_play | owner_bound_atlas_label | STATUS=ADJUDICATED |
| FCM:nested_structural_child | FORENSIC_REFERENCE:information_corpus_persistence_base | HAS_CHILD | CHILD:nested_structural_child | forensic_lossless_structure | STATUS=HISTORICAL |
| FCM:okx_instfamily | VENUE:okx | HAS_FAMILY | VENUE_FIELD:instFamily | okx_venue_field | STATUS=FORENSIC_RAW |
| FCM:okx_mmr_field | VENUE:okx | HAS_MMR | VENUE_FIELD:mmr | okx_venue_field | STATUS=FORENSIC_RAW |
| FCM:ssot_child | SYSTEM:peak_trade | HAS_SSOT_CHILD | TERM:ssot_child_unproven | unproven_kind | STATUS=OPEN (not proven) |

## Git chronology (origin/main after unshallow)

Owner-bound Master V2 / Double Play same-system relation is not reinterpreted.

| id | when | pr | what | status |
| --- | --- | --- | --- | --- |
| HIST:ops_double_play_switch_gate | 2026-02-20 | #1531 | Deterministic switch-gate + double-play runbook (before Master V2 tree) | HISTORICAL_ONLY |
| HIST:ops_double_play_specialists | 2026-02-20 | #1535 | src/ops/double_play bull/bear specialists scaffold (safe default off) | CURRENT_NONCANONICAL |
| HIST:master_v2_tree | 2026-04-23 | #2822 | Master V2 canonical dry-flow tree introduced | STILL_CURRENT_AND_CANONICALLY_SUPPORTED |
| HIST:dp_pure_stack | 2026-04-25 | #3035 | Double Play pure scope/state then survival/suitability/composition on Master V2 | STILL_CURRENT_AND_CANONICALLY_SUPPORTED |
| HIST:webui_dp_dashboard_removed | 2026-07-17 | OPEN | Market-dashboard Double Play webui stack deleted | REMOVED |
| HIST:cap21_gfu | 2026-08-02 | OPEN | Capability 2.1 GFU producer introduced (uly base-only from first commit) | CURRENT_NONCANONICAL |
| HIST:dp_core_wiring_restored | 2026-08-29 | #6131 | Restore current-system Double-Play core wiring on Master V2 | CURRENT_NONCANONICAL |
| HIST:selector_policy_reverted | 2026-08-30 | #6166 | Revert Master V2 minimal selector policy (#6165) | REJECTED |
| HIST:wp_fa_07 | 2026-09-01 | #6209 | Bind DDO to existing experiment identity and offline drift contracts (WP-FA-07) | CURRENT_NONCANONICAL |

