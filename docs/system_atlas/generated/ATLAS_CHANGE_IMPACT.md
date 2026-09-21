<!-- GENERATED/DO_NOT_EDIT -->
<!-- generator: scripts/ops/generate_system_atlas_v1.py -->
<!-- atlas_authority: NONE -->
<!-- schema_version: system_atlas.v1 -->

`ATLAS_AUTHORITY=NONE`  
`ATLAS_ROLE=EVIDENCE_BOUND_SYSTEM_TOPOLOGY_AND_NAVIGATION`  
`CANONICAL_AUTHORITY_IS_EXTERNAL_TO_ATLAS=true`  
`ATLAS_MUST_CITE_AUTHORITY=true`  
`ATLAS_MUST_NOT_CREATE_AUTHORITY=true`

# Atlas Change Impact

This view is topology change-coupling, not canonical authority.

```text
ATLAS_IMPACT=UPDATED
ATLAS_CHANGED_ENTITY_COUNT=10
ATLAS_CHANGED_RELATION_COUNT=3
ATLAS_REVIEW_REQUIRED_COUNT=0
ATLAS_GENERATED_FILES_CURRENT=true
ATLAS_VALIDATION_STATUS=OK
SYSTEM_ATLAS_DRIFT_DETECTED=false
```

Live PRs are classified by `scripts/ops/check_system_atlas_impact_v1.py`. Do not invent commit or PR identifiers before they exist. Before merge, provenance may be `CURRENT_CAPITAL_RISK_SIZING_HISTORICAL_DEFAULT_DEAUTHORIZATION_V1`.

## Workflow

1. Implement the code.
2. Add/update machine-readable Atlas records (relations, evidence, closures).
3. Regenerate views (`generate_system_atlas_v1.py`).
4. Validate (`validate_system_atlas_v1.py`).
5. Run the impact checker.
6. Report `ATLAS_IMPACT=UPDATED` or `ATLAS_IMPACT=NONE_WITH_PROOF`.

Do not manually patch generated Markdown.

## CHANGED_ENTITIES

| id |
| --- |
| `CONTRACT:current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1` |
| `CONTRACT:step29m_current_single_selected_future_dynamic_binding_v1` |
| `GATE:full_core_capital_admission_v1` |
| `GATE:portfolio_capital_reservation_budget_v1` |
| `RUNTIME_COMPONENT:full_core_live_path_composition_root_v1` |
| `RUNTIME_COMPONENT:mv2_capital_risk_sizing` |
| `RUNTIME_COMPONENT:mv2_integrated_replay` |
| `RUNTIME_COMPONENT:mv2_offline_boundary_adapters` |
| `RUNTIME_COMPONENT:ddo_capture_v0` |
| `SUBSYSTEM:master_v2` |

## CHANGED_RELATIONS

| id |
| --- |
| `REL:r_ddo_capture_observes_integrated_replay` |
| `REL:r_enter_live_29p_join_consumes_portfolio_budget` |
| `REL:s_fa_occupied_lane_governed_cycle_n1_consumer_depends_on_portfolio_budget` |

## NEW_RELATIONS

| id |
| --- |
| _(none)_ |

## REMOVED_RELATIONS

| id |
| --- |
| _(none)_ |

## AFFECTED_DEPENDENCY_CLOSURES

| id |
| --- |
| _(none)_ |

## AFFECTED_OKX_SURFACES

| id |
| --- |
| _(none)_ |

## AFFECTED_SAFETY_SURFACES

| id |
| --- |
| `GATE:full_core_capital_admission_v1` |
| `GATE:portfolio_capital_reservation_budget_v1` |

## AFFECTED_SCHEMAS

| id |
| --- |
| _(none)_ |

## REVIEW_REQUIRED_ITEMS

| item |
| --- |
| _(none)_ |

## Notes

- Deauthorize historical technical defaults 25/500/100/10000 from CURRENT capital/risk/sizing decision paths; isolated offline-replay fixture binding only; productive limits fail-closed until authorized producer. Navigation-only Atlas updates; no new risk policy; adverse_exit_distance=80.0 unchanged; no live/testnet/order authority. ATLAS_AUTHORITY=NONE.
- introduced_by=CURRENT_CAPITAL_RISK_SIZING_HISTORICAL_DEFAULT_DEAUTHORIZATION_V1
- modified_by=CURRENT_CAPITAL_RISK_SIZING_HISTORICAL_DEFAULT_DEAUTHORIZATION_V1

`ATLAS_AUTHORITY=NONE`. This mechanism keeps the Atlas current. It does not make the Atlas canonical SSOT.
