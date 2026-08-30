<!-- GENERATED/DO_NOT_EDIT -->
<!-- generator: scripts/ops/generate_system_atlas_v1.py -->
<!-- atlas_authority: NONE -->
<!-- schema_version: system_atlas.v1 -->

# Terminology Collisions

`ATLAS_AUTHORITY=NONE`  
`ATLAS_ROLE=EVIDENCE_BOUND_SYSTEM_TOPOLOGY_AND_NAVIGATION`  
`CANONICAL_AUTHORITY_IS_EXTERNAL_TO_ATLAS=true`  
`ATLAS_MUST_CITE_AUTHORITY=true`  
`ATLAS_MUST_NOT_CREATE_AUTHORITY=true`

Collisions are preserved, not normalized.

### COLLISION:dod_vs_capability_closure

- term: `DoD &#47; Definition of Done`
- meaning_a: Program Definition of Done (Master Runbook §21 named DoD)
- source_a: `docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`
- meaning_b: Mandatory Capability Closure Standard (Master Runbook §11; not named DoD) plus historical Vollautonomie §§37-39 plus process/PR DoD headings
- source_b: `docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`
- status: `STATUS=CONTRADICTED (both sides preserved)`

### COLLISION:family_polyvalent

- term: `Family`
- meaning_a: Dashboard family_id grouping (8 projection-octet ids)
- source_a: `docs/ops/market_dashboard/market_dashboard_projection_octet_materialization_path_discovery_v1/FAMILY_MATRIX.json`
- meaning_b: OKX instFamily; strategy visual-map Family names; confirm-token FAMILY_*; Gate-Familien F1–F6; obligation_families; strategy_family field; NO_FAMILY_ONTOLOGY
- source_b: `src/ops/governed_futures_universe_producer_v1/eligibility_v1.py`
- status: `STATUS=CONTRADICTED (both sides preserved)`

### COLLISION:mmr_polyvalent

- term: `MMR &#47; mmr`
- meaning_a: Master Runbook Maintenance Margin Requirement (account-effective vs public-tier mmr)
- source_a: `docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`
- meaning_b: Architectural Master-V2 MMR kind (not found in scoped MASTER_V2 specs)
- source_b: `docs/ops/specs/`
- status: `STATUS=CONTRADICTED (both sides preserved)`

### COLLISION:c1_polyvalent

- term: `C1`
- meaning_a: Program status flag C1_PRODUCTIVELY_BOUND
- source_a: `docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`
- meaning_b: Package C Slice C1 (INV-045) Dynamic Scope owner boundary
- source_b: `tests/ops/test_master_v2_dynamic_scope_owner_boundary_contract_v0.py`
- status: `STATUS=CONTRADICTED (both sides preserved)`

### COLLISION:schema_vs_data_contract

- term: `Schema`
- meaning_a: SCHEMA_VERSION / JSON Schema / DOCUMENT_CLASS serialization shape
- source_a: `src/ops/governed_futures_universe_producer_v1/constants_v1.py`
- meaning_b: DATA_CONTRACT / dataclass DTO (e.g. BoundInstrumentV1) which may USE a schema without being one
- source_b: `src/ops/single_selected_future_runtime_binding_v1/models_v1.py`
- status: `STATUS=ADJUDICATED`

### COLLISION:ssot_child_vs_ssot

- term: `SSOT &#47; SSOT child`
- meaning_a: Single Source of Truth authority uniqueness
- source_a: `docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`
- meaning_b: SSOT child as an architectural kind — not found as a formal in-repo definition
- source_b: `docs/system_atlas/census/census_meta.yaml`
- status: `STATUS=OPEN (not proven)`

### COLLISION:double_play_order

- term: `Double Play ordering versus Survival&#47;Suitability`
- meaning_a: Master Runbook current chain Market State → Master V2 → Double Play → Survival/Suitability/Composition
- source_a: `docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`
- meaning_b: Historical Vollautonomie Survival → Suitability → Double Play → Canonical Trading Decision
- source_b: `docs/governance/Peak_Trade_Kanonisches_Vollautonomie_Runbook_v4.4.12.md`
- status: `STATUS=CONTRADICTED (both sides preserved)`

### COLLISION:code_vs_spec_quote_default

- term: `missing metadata never defaulted`
- meaning_a: Cap 2.1 spec claim that missing metadata is never defaulted
- source_a: `docs/ops/specs/MASTER_V2_CAPABILITY_2_1_GOVERNED_FUTURES_UNIVERSE_PRODUCER_V1.md`
- meaning_b: eligibility_v1._extract_base_quote defaults missing base from instId/uly; quote never from uly
- source_b: `src/ops/governed_futures_universe_producer_v1/eligibility_v1.py`
- status: `STATUS=CONTRADICTED (both sides preserved)`

### COLLISION:pending_status_token

- term: `PENDING`
- meaning_a: Evidence/support status SUPPORT_EVIDENCE_STATUS=PENDING
- source_a: `docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`
- meaning_b: Order-lifecycle SUBMIT_PENDING / OKX /api/v5/trade/orders-pending
- source_b: `docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`
- status: `STATUS=ADJUDICATED`

