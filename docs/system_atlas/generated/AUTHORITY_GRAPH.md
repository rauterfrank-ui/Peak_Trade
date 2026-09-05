<!-- GENERATED/DO_NOT_EDIT -->
<!-- generator: scripts/ops/generate_system_atlas_v1.py -->
<!-- atlas_authority: NONE -->
<!-- schema_version: system_atlas.v1 -->

# Authority graph — why are we allowed to believe this?

`ATLAS_AUTHORITY=NONE`  
`ATLAS_ROLE=EVIDENCE_BOUND_SYSTEM_TOPOLOGY_AND_NAVIGATION`  
`CANONICAL_AUTHORITY_IS_EXTERNAL_TO_ATLAS=true`  
`ATLAS_MUST_CITE_AUTHORITY=true`  
`ATLAS_MUST_NOT_CREATE_AUTHORITY=true`

Implementation and tests cannot confer authority upward.

| id | source | type | target | epistemic | evidence |
| --- | --- | --- | --- | --- | --- |
| REL:a_forensic_does_not_authorize | FORENSIC_REFERENCE:information_corpus_persistence_base | DOES_NOT_AUTHORIZE | SYSTEM:peak_trade | STATUS=FORENSIC_RAW | docs/forensics/persistence/PEAK_TRADE_INFORMATION_CORPUS_PERSISTENCE_BASE.md |
| REL:a_map_documents_runbook | NAVIGATION_INDEX:map_of_truth | DOCUMENTS | RUNBOOK:canonical_master_runbook | STATUS=NAVIGATION_ONLY | docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md |
| REL:a_owner_binds_btc | OWNER_DECISION:btc_excluded | BINDS | GATE:btc_exclusion | STATUS=CANONICAL_AUTHORITY | src/ops/governed_futures_universe_producer_v1/constants_v1.py |
| REL:a_owner_binds_cap23 | OWNER_DECISION:cap23_exclusive_selection | BINDS | CAPABILITY:cap_2_3_single_selected_future | STATUS=CANONICAL_AUTHORITY | docs/ops/specs/MASTER_V2_CAPABILITY_2_3_SINGLE_SELECTED_FUTURE_POLICY_V1.md |
| REL:a_runbook_does_not_authorize_live | RUNBOOK:canonical_master_runbook | DOES_NOT_AUTHORIZE | GATE:live_authorized_false | STATUS=CANONICAL_AUTHORITY | docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md |
| REL:a_runbook_governs_system | RUNBOOK:canonical_master_runbook | GOVERNS | SYSTEM:peak_trade | STATUS=CANONICAL_AUTHORITY | docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md |
| REL:a_spec_claims_cap21 | CAPABILITY:cap_2_1_gfu | CLAIMS_TO_IMPLEMENT | INVARIANT:missing_metadata_never_defaulted | STATUS=CONTRADICTED (both sides preserved) | docs/ops/specs/MASTER_V2_CAPABILITY_2_1_GOVERNED_FUTURES_UNIVERSE_PRODUCER_V1.md,src/ops/governed_futures_universe_producer_v1/eligibility_v1.py |
| REL:a_standing_live_does_not_authorize_treasury | GATE:full_core_live_path_standing_live_gates_v1 | DOES_NOT_AUTHORIZE | GATE:treasury_phase_1_offline_contracts_v1 | STATUS=FORENSIC_RAW | src/ops/treasury_phase_1_offline_contracts_v1/authority_v1.py,docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md |
| REL:a_step_29p_risk_admissible_does_not_authorize_port_construction | GATE:full_core_capital_admission_v1 | DOES_NOT_AUTHORIZE | GATE:full_core_live_path_execution_boundary_halt_before_wire_v1 | STATUS=FORENSIC_RAW | src/ops/full_core_live_path_composition_root_v1/step_29p_capital_risk_admissibility_v1.py,docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md |
| REL:a_treasury_phase_1_does_not_authorize_live | GATE:treasury_phase_1_offline_contracts_v1 | DOES_NOT_AUTHORIZE | GATE:live_authorized_false | STATUS=FORENSIC_RAW | src/ops/treasury_phase_1_offline_contracts_v1/authority_v1.py,docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md |

