<!-- GENERATED/DO_NOT_EDIT -->
<!-- generator: scripts/ops/generate_system_atlas_v1.py -->
<!-- atlas_authority: NONE -->
<!-- schema_version: system_atlas.v1 -->

# Family / Child / MMR Map

`ATLAS_AUTHORITY=NONE`  
`ATLAS_ROLE=EVIDENCE_BOUND_SYSTEM_TOPOLOGY_AND_NAVIGATION`  
`CANONICAL_AUTHORITY_IS_EXTERNAL_TO_ATLAS=true`  
`ATLAS_MUST_CITE_AUTHORITY=true`  
`ATLAS_MUST_NOT_CREATE_AUTHORITY=true`

These terms have multiple observed meanings. They are not a single hierarchy.

## Terminology entities

| id | kind | status | do_not_confuse |
| --- | --- | --- | --- |
| TERM:btc_productive_proof_do_not_run | TERM | CURRENT_CANONICAL | GATE:btc_exclusion; superseded canary id BTC-USD_UM_XPERP-310404 |
| TERM:canary | TERM | CURRENT_CANONICAL |  |
| TERM:cap23 | TERM | CURRENT_CANONICAL |  |
| TERM:capability_closure_standard | TERM | CURRENT_CANONICAL | Program Definition of Done; pytest |
| TERM:double_play | TERM | STILL_CURRENT_AND_CANONICALLY_SUPPORTED | ops.double_play.evaluate_double_play (quarantined projection); dashboard family_id double_play |
| TERM:fail_closed | TERM | CURRENT_CANONICAL |  |
| TERM:live_authorized | TERM | CURRENT_CANONICAL | implementation presence; HMAC signer existence |
| TERM:master_v2 | TERM | STILL_CURRENT_AND_CANONICALLY_SUPPORTED |  |
| TERM:owner_go | TERM | CURRENT_CANONICAL |  |

## Observed parent/child records

| id | parent | type | child | role | epistemic |
| --- | --- | --- | --- | --- | --- |
| FCM:architectural_mmr | SUBSYSTEM:master_v2 | HAS_MMR | TERM:mmr_polyvalent | OPEN | STATUS=OPEN (not proven) |
| FCM:dashboard_canonical_decision | SYSTEM:peak_trade | HAS_FAMILY | FAMILY:dashboard_canonical_decision | projection_grouping | STATUS=FORENSIC_RAW |
| FCM:dashboard_double_play | SYSTEM:peak_trade | HAS_FAMILY | FAMILY:dashboard_double_play | projection_grouping | STATUS=FORENSIC_RAW |
| FCM:dashboard_dynamic_scope | SYSTEM:peak_trade | HAS_FAMILY | FAMILY:dashboard_dynamic_scope | projection_grouping | STATUS=FORENSIC_RAW |
| FCM:dashboard_econ | SYSTEM:peak_trade | HAS_FAMILY | FAMILY:dashboard_economic_summary | projection_grouping | STATUS=FORENSIC_RAW |
| FCM:dashboard_exec_recon | SYSTEM:peak_trade | HAS_FAMILY | FAMILY:dashboard_execution_reconciliation | projection_grouping | STATUS=FORENSIC_RAW |
| FCM:dashboard_regime | SYSTEM:peak_trade | HAS_FAMILY | FAMILY:dashboard_regime_bull_bear | projection_grouping | STATUS=FORENSIC_RAW |
| FCM:dashboard_risk | SYSTEM:peak_trade | HAS_FAMILY | FAMILY:dashboard_risk_sizing_capital | projection_grouping | STATUS=FORENSIC_RAW |
| FCM:dashboard_safety | SYSTEM:peak_trade | HAS_FAMILY | FAMILY:dashboard_safety_authority | projection_grouping | STATUS=FORENSIC_RAW |
| FCM:falls_parent_child | FORENSIC_REFERENCE:information_corpus_persistence_base | HAS_CHILD | TERM:falls_parent_child | falls_parent_child_not_ssot_child | STATUS=HISTORICAL |
| FCM:master_v2_functional_core | SUBSYSTEM:master_v2 | HAS_FUNCTIONAL_CORE | FUNCTIONAL_CORE:double_play | modul_owner_same_trading_core | STATUS=ADJUDICATED |
| FCM:nested_structural_child | FORENSIC_REFERENCE:information_corpus_persistence_base | HAS_CHILD | CHILD:nested_structural_child | nested_structural_child_not_ssot_child | STATUS=HISTORICAL |
| FCM:okx_instfamily | VENUE:okx | HAS_FAMILY | VENUE_FIELD:instFamily | instrument_family | STATUS=FORENSIC_RAW |
| FCM:okx_mmr_field | VENUE:okx | HAS_MMR | VENUE_FIELD:mmr | maintenance_margin_ratio | STATUS=FORENSIC_RAW |
| FCM:ssot_child | SYSTEM:peak_trade | HAS_SSOT_CHILD | TERM:ssot_child_unproven | OPEN | STATUS=OPEN (not proven) |

