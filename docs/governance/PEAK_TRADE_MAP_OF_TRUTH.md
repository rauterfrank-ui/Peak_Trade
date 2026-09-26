# Peak Trade — Map of Truth

```text
DOCUMENT_CLASS=CURRENT_NAVIGATION_ONLY
DOCUMENT_ROLE=NAVIGATION_ONLY
MAP_OF_TRUTH_ROLE=NAVIGATION_ONLY
MAP_OF_TRUTH_AUTHORITY=NONE
MAP_OF_TRUTH_SEMANTIC_AUTHORITY_EFFECT=NONE
MAP_OF_TRUTH_INDEPENDENT_OPERATIONAL_TRUTH=NONE
THIS_DOCUMENT_DEFINES_NO_SEMANTICS=true
THIS_DOCUMENT_POINTS_ONLY_TO_CANONICAL_OWNERS=true
THIS_DOCUMENT_IS_NOT_A_SECOND_RUNBOOK=true
THIS_DOCUMENT_IS_NOT_A_SECOND_SSOT=true
PARALLEL_SSOT_CREATED=false
RUNTIME_AUTHORIZATION_EFFECT=NONE
```

**Role:** discovery / path resolution only.  
**Authority:** none.

An autonomous agent may use this document to answer:

```text
WHERE is the authoritative CURRENT information?
```

An autonomous agent must NOT use this document to answer:

```text
WHAT is the authoritative operational decision?
WHAT is authorized / activated / next?
```

Operational semantics, safety policy, activation state, productive
boundary, and authority ownership live only in:

1. `docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md` (CURRENT operational SSOT)
2. CURRENT `origin/main` code / config / contracts / tests / sealed evidence

If this map and the Master Runbook appear to disagree: **Master Runbook +
CURRENT code win**. Do not invent a third interpretation here.

------------------------------------------------------------------------

## 1. Canonical CURRENT operational SSOT

| Role | Path |
| --- | --- |
| CURRENT operational SSOT | [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) |
| Navigation only (this file) | [`docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md`](PEAK_TRADE_MAP_OF_TRUTH.md) |
| Python runtime contract | [`docs/runtime/PEAK_TRADE_PYTHON_RUNTIME_CONTRACT_V1.md`](../runtime/PEAK_TRADE_PYTHON_RUNTIME_CONTRACT_V1.md) |
| Agent entrypoint | [`AGENTS.md`](../../AGENTS.md) |

```text
CANONICAL_MASTER_RUNBOOK_PATH=docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md
CANONICAL_WORKING_AUTHORITY=docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md
CURSOR_MUST_READ_CANONICAL_RUNBOOK_FIRST=true
NO_PARALLEL_SEMANTIC_MODEL=true
```

Master Runbook CURRENT section navigation (headings, not historical phase IDs):

| Question | Master Runbook section |
| --- | --- |
| What is the system now? | CURRENT System Identity |
| Who owns what? | CURRENT Architecture and Authority Graph |
| Trading core chain | CURRENT Trading Core |
| Inputs | CURRENT Data and Input Contracts |
| Persistence | CURRENT State and Persistence Contracts |
| Risk / capital | CURRENT Risk and Capital Admissibility |
| Intent / execution boundary | CURRENT Order-Intent and Execution Boundaries |
| Safety | CURRENT Safety Invariants |
| Autonomy limits | CURRENT Autonomy Boundaries |
| Operating / activation facts | CURRENT Operating and Activation State |
| Dashboard role | CURRENT Observability and Landscape Dashboard |
| Learning / STEP29M / Optimization boundaries | CURRENT Learning, STEP29M, and Optimization Universe Boundaries |
| Historical names still in code | CURRENT Compatibility Identifiers |
| Remaining productive boundary | CURRENT Productive Boundary |

------------------------------------------------------------------------

## 2. CURRENT semantic capability surfaces (code navigation)

These paths are location pointers only. Semantics and authorization remain
in the Master Runbook and the named packages.

| Semantic identity / domain | CURRENT surface |
| --- | --- |
| Full-Core live-path authority | `src/ops/full_core_live_path_composition_root_v1/` |
| `full_core_live_path_authority_v1` | `src/ops/full_core_live_path_composition_root_v1/constants_v1.py` |
| `capital_risk_admissibility_owner_v1` | `src/ops/full_core_live_path_composition_root_v1/` (risk admissibility modules) |
| `canonical_order_intent_owner_v1` | `src/ops/full_core_live_path_composition_root_v1/` |
| `stateful_no_order_host_join_v1` | `src/ops/full_core_live_path_composition_root_v1/` |
| Cap 7.2 host activation binding implementation | `src/ops/single_future_stateful_no_order_runtime_activation_v1/host_binding_v1.py` |
| Occupied-lane N=5 Full-Autonomy runtime completion | `src/ops/current_mf_n5_full_autonomy_runtime_n5_completion_v1/` |
| `send_capable_adapter_v1` | `src/ops/governed_productive_account_equity_authority_producer_v1/` and Full-Core composition root |
| K1 governed-cycle credential bind (navigation only) | `src/ops/full_core_live_path_composition_root_v1/checkout_independent_credential_governed_cycle_occupancy_bind_v1.py` |
| K1 macOS Keychain backend kind (navigation only) | `src/ops/full_core_live_path_composition_root_v1/checkout_independent_credential_source_backend_kind_v1.py` |
| Exactly-one governed cycle | `src/ops/full_core_live_path_composition_root_v1/current_productive_governed_cycle_orchestrator_v1.py` |
| `governed_continuous_cycle_orchestrator_v1` | `src/ops/full_core_live_path_composition_root_v1/current_productive_governed_continuous_cycle_orchestrator_v1.py` |
| Venue-plan tdMode and order-environment authority (navigation only) | `src/ops/full_core_live_path_composition_root_v1/current_productive_venue_plan_td_mode_and_order_environment_authority_v1.py` |
| Single Selected Future policy | `src/ops/single_selected_future_policy_v1/` |
| Single Selected Future binding | `src/ops/single_selected_future_runtime_binding_v1/` |
| Peak_Trade Future Profile Snapshot (B07) | `src/ops/future_profile_snapshot_v1/` |
| Peak_Trade research/backtest/live parity proof (B09) | `src/ops/peak_trade_research_backtest_live_parity_v1/` / `docs/evidence/peak_trade_research_backtest_live_parity_v1/SUMMARY.json` |
| Peak_Trade robustness and stress proof (B10) | `src/ops/peak_trade_robustness_and_stress_v1/` / `docs/evidence/peak_trade_robustness_and_stress_v1/SUMMARY.json` |
| Peak_Trade operator profile and explainability view (B11) | `src/ops/peak_trade_operator_profile_explainability_v1/` / `docs/evidence/peak_trade_operator_profile_explainability_v1/SUMMARY.json` |
| Peak_Trade canonical truth sync and closure record (B12) | `docs/evidence/peak_trade_canonical_truth_sync_and_closure_v1/SUMMARY.json` |
| Elementary C1 mark direction identity | `src/trading/market_state/elementary_direction_v1.py` |
| Governed universe | `src/ops/governed_futures_universe_producer_v1/` |
| Productive ranking | `src/ops/productive_futures_ranking_producer_v1/` |
| STEP29M post-selection offline binding | `src/backtest/step29m_current_single_selected_future_dynamic_binding_v1.py` |
| Optimization Universe (first-class offline) | `src/experiments/canonical_optimization_universe_v1.py` |
| Learning / DDO capture and export | `src/learning/deterministic_decision_outcome_v0/` |
| Unified Blueprint Phase 16 CMC census (navigation) | `docs/ops/specs/UNIFIED_BLUEPRINT_PHASE_16_CMC_NON_PRICE_CENSUS_NORMATIVE_V1.md` / `src/governance/unified_blueprint_phase_16_cmc_non_price_census_v1.py` |
| MI/Learning MARKET_CONTEXT_V1 (non-price compositional; AUTHORITY=NONE) | `docs/ops/specs/UNIFIED_BLUEPRINT_PHASE_17_NORMATIVE_NON_PRICE_CMC_CONTRACT_NORMATIVE_V1.md` / `src/learning/market_intelligence_forecast_calibration_offline_stack_v1/market_context_v1.py` |
| MI/Learning Phase 18 existing-fact MARKET_CONTEXT_V1 materialization (AUTHORITY=NONE) | `docs/ops/specs/UNIFIED_BLUEPRINT_PHASE_18_EXISTING_FACT_MARKET_CONTEXT_MATERIALIZATION_NORMATIVE_V1.md` / `src/learning/market_intelligence_forecast_calibration_offline_stack_v1/market_context_existing_fact_materialization_v1.py` |
| MI/Learning Phase 19 orthogonal context (derivatives + cross-market; AUTHORITY=NONE) | `docs/ops/specs/UNIFIED_BLUEPRINT_PHASE_19_ORTHOGONAL_CONTEXT_NORMATIVE_V1.md` / `src/learning/market_intelligence_forecast_calibration_offline_stack_v1/market_context_phase_19_orthogonal_materialization_v1.py` |
| MI/Learning Phase 20 behavior join (MARKET_CONTEXT → REALIZED_BEHAVIOR; AUTHORITY=NONE) | `docs/ops/specs/UNIFIED_BLUEPRINT_PHASE_20_BEHAVIOR_JOIN_NORMATIVE_V1.md` / `src/learning/market_intelligence_forecast_calibration_offline_stack_v1/realized_behavior_v1.py` |
| Master V2 / Double Play decision path | `trading` package / integrated offline trading-logic replay owners (see Master Runbook) |
| V3.2 naked MV2 baseline-first lifecycle resolution (#6764) | `docs/ops/specs/V32_NAKED_MV2_DOUBLE_PLAY_BASELINE_FIRST_AUTHORITY_AND_LIFECYCLE_RESOLUTION_V1.md` / `src/governance/naked_mv2_double_play_baseline_first_lifecycle_resolution_v1.py` |
| Concept PDF v3/v3.2 CURRENT MV2+DP alignment (navigation) | `docs/ops/specs/V32_CURRENT_MV2_DP_CONCEPT_ALIGNMENT_V1.md` / `docs/ops/specs/PEAK_TRADE_META_LEARNING_OPTIMIZATION_UNIVERSE_CONCEPT_V3_2_CURRENT_MV2_DP_ALIGNMENT_ADDENDUM_V1.md` |
| Concept PDF v3.3 final DoD D1–D29 + Restblöcke A–H adjudication (navigation) | `docs/ops/specs/META_LEARNING_OPTIMIZATION_UNIVERSE_PDF_V3_3_FINAL_COMPLETION_ADJUDICATION_V1.md` / `src/governance/meta_learning_optimization_universe_pdf_v3_3_final_completion_adjudication_v1.py` / `src/governance/pdf_v3_3_topic_completion_composition_v1.py` |
| D26 native vs candidate baseline evidence (navigation) | `docs/ops/specs/V32_D26_PLATFORM_UNIFIED_NATIVE_VS_CANDIDATE_BASELINE_EVIDENCE_CLOSURE_V1.md` |
| D26 × F5 shadow baseline-binding owner policy (navigation) | `docs/ops/specs/V32_D26_F5_SHADOW_D26_BASELINE_BINDING_OWNER_POLICY_ADJUDICATION_V1.md` |
| D27 F5 shadow test-entry lifecycle enforcement (navigation) | `docs/ops/specs/V32_D27_F5_SHADOW_TEST_ENTRY_LIFECYCLE_ENFORCEMENT_V1.md` |
| Post-D27 global test-entry lifecycle closure (navigation) | `docs/ops/specs/V32_POST_D27_TEST_ENTRY_LIFECYCLE_GLOBAL_CLOSURE_ADJUDICATION_V1.md` |
| D28/D29 optimization productive join policy adjudication (navigation) | `docs/ops/specs/V32_D28_D29_OPTIMIZATION_PRODUCTIVE_JOIN_POLICY_ADJUDICATION_V1.md` / `src/governance/v32_d28_d29_optimization_productive_join_policy_adjudication_v1.py` |
| D28/D29 scoped F1/M9 optimization productive join policy (navigation) | `docs/ops/specs/V32_D28_D29_SCOPED_OPTIMIZATION_PRODUCTIVE_JOIN_F1_M9_MAX_BUILD_V1.md` / `src/governance/v32_d28_d29_scoped_optimization_productive_join_policy_v1.py` |
| D29 F1/M9 per-ingress productive authorization/apply adjudication (navigation) | `docs/ops/specs/V32_D29_F1_M9_PER_INGRESS_PRODUCTIVE_AUTHORIZATION_APPLY_ADJUDICATION_AND_MAX_BUILD_V1.md` / `src/governance/v32_d29_f1_m9_per_ingress_productive_authorization_apply_adjudication_v1.py` |
| F1/M9 scoped Owner Productive Apply authority (navigation) | `docs/ops/specs/F1_M9_SCOPED_OWNER_APPLY_AUTHORITY_NORMATIVE_V1.md` / `src/governance/f1_m9_scoped_owner_apply_authority_v1.py` |
| F1/M9 scoped Owner Threshold Value authority (navigation) | `docs/ops/specs/F1_M9_SCOPED_OWNER_THRESHOLD_VALUE_AUTHORITY_NORMATIVE_V1.md` / `src/governance/f1_m9_scoped_owner_threshold_value_authority_v1.py` |
| Treasury Phase 1 offline contracts | `docs/ops/specs/TREASURY_PHASE_1_OFFLINE_CONTRACTS_V1.md` / `src/ops/treasury_phase_1_offline_contracts_v1/` |
| Treasury Phase 2 read-only reconciliation | `docs/ops/specs/TREASURY_PHASE_2_READ_ONLY_RECONCILIATION_FOUNDATION_V1.md` / `src/ops/treasury_phase_2_read_only_reconciliation_v1/` |
| Treasury Phase 3 shadow enforcement | `docs/ops/specs/TREASURY_PHASE_3_SHADOW_ENFORCEMENT_V1.md` / `src/ops/treasury_phase_3_shadow_enforcement_v1/` |
| Treasury PDF current-head rebind census | `docs/ops/specs/TREASURY_PDF_CURRENT_HEAD_REBIND_AND_CENSUS_V1.md` / `src/ops/treasury_pdf_current_head_rebind_and_census_v1/` |
| Canonical Python launcher | `scripts/pt` |
| Canonical interpreter | `.venv&#47;bin&#47;python` |

------------------------------------------------------------------------

## 3. Useful CURRENT related documents (non-SSOT)

These documents may help locate surfaces. They are **not** operational
authority and must not be read as activation or next-step instructions.

| Path | Navigation note |
| --- | --- |
| [`config/governance/current_system_interaction_authority_map_v1/source_v1.json`](../../config/governance/current_system_interaction_authority_map_v1/source_v1.json) | **Navigation only:** structured source for CURRENT System Interaction & Authority Map (`AUTHORITY=NONE`, `map_authority=NONE`); derived read-only views under [`docs/governance/current_system_interaction_authority_map_v1/generated/`](current_system_interaction_authority_map_v1/generated/); not operational SSOT |
| [`docs/governance/PEAK_TRADE_CANONICAL_RUNTIME_TRUTH_MAP_V1.md`](PEAK_TRADE_CANONICAL_RUNTIME_TRUTH_MAP_V1.md) | Historical/runtime discovery aid; reconcile against Master Runbook + CURRENT code before use |
| [`docs/governance/PEAK_TRADE_IMPLEMENTATION_CONTRACT.md`](PEAK_TRADE_IMPLEMENTATION_CONTRACT.md) | Short navigation contract; not a second SSOT |
| [`docs/ops/registry/DOCS_TRUTH_MAP.md`](../ops/registry/DOCS_TRUTH_MAP.md) | Docs drift registry; not a runbook |
| [`docs/ops/specs/GOVERNANCE_VERIFICATION_MINIMUM_LOCAL_CI_DEDUP_V1.md`](../ops/specs/GOVERNANCE_VERIFICATION_MINIMUM_LOCAL_CI_DEDUP_V1.md) | Local CI dedup navigation |
| [`docs/ops/market_dashboard/PEAK_TRADE_MARKET_DASHBOARD_LANDSCAPE_MASTER_RUNBOOK_V2.md`](../ops/market_dashboard/PEAK_TRADE_MARKET_DASHBOARD_LANDSCAPE_MASTER_RUNBOOK_V2.md) | Landscape Dashboard consumer docs; read-only / non-authority |
| [`docs/ops/market_dashboard/LANDSCAPE_CURRENT_DOCUMENTATION_RECONCILIATION_V1.md`](../ops/market_dashboard/LANDSCAPE_CURRENT_DOCUMENTATION_RECONCILIATION_V1.md) | Factual pointer reconciliation (Landscape closeout vs post-closeout Presentation-Ops); navigation only |
| [`docs/ops/market_dashboard/PEAK_TRADE_PROFESSIONAL_TRADING_DASHBOARD_RUNBOOK_V1.md`](../ops/market_dashboard/PEAK_TRADE_PROFESSIONAL_TRADING_DASHBOARD_RUNBOOK_V1.md) | Professional workstation plan/boundary for Landscape V2; navigation only; read-only / non-authority |
| [`docs/runtime/PEAK_TRADE_PYTHON_RUNTIME_CONTRACT_V1.md`](../runtime/PEAK_TRADE_PYTHON_RUNTIME_CONTRACT_V1.md) | Python launcher/interpreter contract |
| [`docs/ops/specs/ELEMENTARY_DIRECTION_PRIMITIVE_V1.md`](../ops/specs/ELEMENTARY_DIRECTION_PRIMITIVE_V1.md) | Navigation to C1 mark-to-mark identity primitive; not a trading-decision owner |
| [`docs/ops/specs/DDO_DURABLE_EVIDENCE_STORAGE_OWNER_CONTRACT_V1.md`](../ops/specs/DDO_DURABLE_EVIDENCE_STORAGE_OWNER_CONTRACT_V1.md) | Navigation-only DDO durable evidence storage-owner contract; not trading authority |
| [`docs/ops/specs/FULL_CORE_RUNNING_ACCOUNT_EQUITY_PARALLEL_DECOUPLED_TRACKS_AUTHORITY_INTERFACE_RECONCILIATION_CONTRACT_V1.md`](../ops/specs/FULL_CORE_RUNNING_ACCOUNT_EQUITY_PARALLEL_DECOUPLED_TRACKS_AUTHORITY_INTERFACE_RECONCILIATION_CONTRACT_V1.md) | Navigation-only parallel-decoupled tracks Authority&#47;Interface&#47;Reconciliation contract; not sizing mint; not mapping authority |
| [`docs/ops/specs/FULL_CORE_SOURCE_TO_SEMANTIC_MAPPING_AND_SIZING_PRODUCER_BIND_UNDER_PARALLEL_DECOUPLED_TRACKS_V1.md`](../ops/specs/FULL_CORE_SOURCE_TO_SEMANTIC_MAPPING_AND_SIZING_PRODUCER_BIND_UNDER_PARALLEL_DECOUPLED_TRACKS_V1.md) | Navigation-only OPTION_B producer Source→Semantic mapping ratification under parallel tracks; offline STEP-29P proof; not numeric venue bind |

```text
MAP_OF_TRUTH_AUTHORITY=NAVIGATION_ONLY
CURRENT_SYSTEM_INTERACTION_AUTHORITY_MAP_V1_SOURCE=config/governance/current_system_interaction_authority_map_v1/source_v1.json
CURRENT_SYSTEM_INTERACTION_AUTHORITY_MAP_V1_GENERATED_VIEWS=docs/governance/current_system_interaction_authority_map_v1/generated/
CURRENT_SYSTEM_INTERACTION_AUTHORITY_MAP_V1_ROLE=NAVIGATION_ONLY
CURRENT_SYSTEM_INTERACTION_AUTHORITY_MAP_V1_AUTHORITY=NONE
DDO_AUTHORITY_EFFECT=NONE
RUNNING_ACCOUNT_EQUITY_PARALLEL_DECOUPLED_TRACKS_CONTRACT_NAV=docs/ops/specs/FULL_CORE_RUNNING_ACCOUNT_EQUITY_PARALLEL_DECOUPLED_TRACKS_AUTHORITY_INTERFACE_RECONCILIATION_CONTRACT_V1.md
RUNNING_ACCOUNT_EQUITY_PARALLEL_DECOUPLED_TRACKS_CONTRACT_ROLE=NAVIGATION_POINTER_ONLY
DDO_DURABLE_EVIDENCE_STORAGE_OWNER_CONTRACT_NAV=docs/ops/specs/DDO_DURABLE_EVIDENCE_STORAGE_OWNER_CONTRACT_V1.md
DDO_DURABLE_EVIDENCE_STORAGE_OWNER_CONTRACT_ROLE=NAVIGATION_POINTER_ONLY
DDO_LEDGER_DURABILITY_HARDENING_AND_HOST_BINDING_PREP_ROLE=NAVIGATION_POINTER_ONLY
DDO_PRODUCTIVE_HOST_SCOPE_INPUT_BINDING_ROLE=NAVIGATION_POINTER_ONLY
DDO_PRODUCTIVE_HOST_DURABLE_LEDGER_BINDING_ROLE=NAVIGATION_POINTER_ONLY
DDO_A1_UNATTENDED_DURABILITY_POLICY_BOUNDARY_ROLE=NAVIGATION_POINTER_ONLY
DDO_A1_UNATTENDED_DURABILITY_RUNTIME_AUTHORIZATION_ROLE=NAVIGATION_POINTER_ONLY
DDO_A1_CRASH_DURABILITY_ATOMIC_REPLACE_OR_EXPLICIT_NONREQUIREMENT_ROLE=NAVIGATION_POINTER_ONLY
DDO_A1_DURABILITY_FAILURE_POLICY_BINDING_ROLE=NAVIGATION_POINTER_ONLY
DDO_A1_DURABILITY_TO_ADMISSION_AND_REPLAY_BINDING_ROLE=NAVIGATION_POINTER_ONLY
DDO_A1_CRASH_DURABILITY_PROOF_OR_EXPLICIT_NONPROVABILITY_CLOSURE_ROLE=NAVIGATION_POINTER_ONLY
DDO_A1_MUTATION_CRITICAL_CONTROL_STATE_STORAGE_OWNER_CONTRACT_ROLE=NAVIGATION_POINTER_ONLY
DDO_A1_MUTATION_CRITICAL_CONTROL_STATE_DURABLE_STORAGE_IMPLEMENTATION_AND_CRASH_REPROOF_ROLE=NAVIGATION_POINTER_ONLY
```

------------------------------------------------------------------------

## 4. Compatibility-only name navigation

Some CURRENT files, claim keys, and evidence directories still use historical
names. Treat them as location compatibility only:

```text
CLASS=HISTORICAL_COMPATIBILITY_ONLY
AUTHORITY_EFFECT=NONE
```

Examples (non-exhaustive; authoritative list is in Master Runbook
**CURRENT Compatibility Identifiers**):

- `STEP_29P`, `STEP_29Q`, `PLAN_ONLY`
- `CAP_7_2`, `CAP_11_1`
- `SECTION_11_13_5_*`, `SECTION_11_14_*`
- `EH.S5` / `EH.S6`
- `CAPABILITY_2_3_*`, `CAPABILITY_2_4_*`
- Historically named module/evidence paths under `src/ops/` and `evidence/ops/`

Do not interpret these names as CURRENT phase, next action, or independent
authority.

------------------------------------------------------------------------

## 5. Explicit non-authority

This Map of Truth does **not** define or authorize:

- trading semantics
- authority ownership beyond pointing to owners
- activation / arming / wire-send / POST
- productive next action
- safety policy
- execution policy
- Live / Testnet / credential / capital movement
- Clean Trading Core status (read Master Runbook)
- standing LIVE_* predicate interpretation (read Master Runbook + CURRENT constants)

```text
LIVE_AUTHORIZED_BY_THIS_DOCUMENT=false
TESTNET_AUTHORIZED_BY_THIS_DOCUMENT=false
ORDERS_ALLOWED_BY_THIS_DOCUMENT=false
SCHEDULER_RUNTIME_ALLOWED_BY_THIS_DOCUMENT=false
DASHBOARD_AUTHORITY_EFFECT=NONE
```

Notion is not a Peak_Trade component and is not a navigation authority for
CURRENT operational truth.

------------------------------------------------------------------------

## 6. Guidance for new agents

1. Read [`PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) fully before mutation.
2. Revalidate current `origin/main`.
3. Use this map only to find paths.
4. Prove runtime facts from code/config/persistence/tests/evidence.
5. Fail closed on drift or ambiguity.
6. Do not follow historical Cap/Phase/Step/Section/EH/Z2/Pxx/Dxx workflow
   pointers as CURRENT instructions.
