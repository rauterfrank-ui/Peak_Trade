<!-- GENERATED/DO_NOT_EDIT -->
<!-- generator: scripts/ops/generate_system_atlas_v1.py -->
<!-- atlas_authority: NONE -->
<!-- schema_version: system_atlas.v1 -->

# Coverage Report

`ATLAS_AUTHORITY=NONE`  
`ATLAS_ROLE=EVIDENCE_BOUND_SYSTEM_TOPOLOGY_AND_NAVIGATION`  
`CANONICAL_AUTHORITY_IS_EXTERNAL_TO_ATLAS=true`  
`ATLAS_MUST_CITE_AUTHORITY=true`  
`ATLAS_MUST_NOT_CREATE_AUTHORITY=true`

This Atlas does not claim universe completeness because generation succeeded.

```text
ENTITY_TOTAL=296
STRUCTURAL_RELATION_COUNT=242
RUNTIME_RELATION_COUNT=101
AUTHORITY_RELATION_COUNT=10
OPEN_RELATION_COUNT=1
CONTRADICTED_RELATION_COUNT=1
HYPOTHESIS_COUNT=0
OKX_FEATURE_TOTAL=1
OKX_ENDPOINT_COUNT=3
OKX_FIELD_COUNT=3
UNRESOLVED_CONTRADICTION_COUNT=8
CAPABILITY_DEPENDENCY_CLOSURE_COUNT=9
ORPHAN_COMPONENT_COUNT=129
DATA_LINEAGE_RECORD_COUNT=4
CONFIG_WIRING_RECORD_COUNT=4
OKX_CENSUS_COMPLETE=true
MASTER_V2_CENSUS_COMPLETE=true
DOUBLE_PLAY_CENSUS_COMPLETE=true
FAMILY_CENSUS_COMPLETE=true
CHILD_CENSUS_COMPLETE=true
SSOT_CHILD_CENSUS_COMPLETE=true
MMR_CENSUS_COMPLETE=true
SCHEMA_FILE_INVENTORY_COMPLETE=true
MASTER_V2_CAPABILITY_SPEC_INVENTORY_COMPLETE=true
MASTER_V2_MODULE_FILE_INVENTORY_COMPLETE=false
TERMINOLOGY_CENSUS_COMPLETE=true
ACRONYM_CENSUS_COMPLETE=false
DOD_CENSUS_COMPLETE=true
SCHEMA_CENSUS_COMPLETE=true
HISTORICAL_TERMINOLOGY_CENSUS_COMPLETE=false
OKX_CURRENT_TREE_CENSUS_COMPLETE=true
OKX_HISTORICAL_CENSUS_COMPLETE=false
SCHEMA_FIELD_ENUMERATION_COMPLETE=true
SYSTEM_ATLAS_PRIMARY_ENTRYPOINT=docs/system_atlas/generated/SYSTEM_ATLAS.md
SYSTEM_ATLAS_MASTER_VIEW_COMPLETE=true
GLOBAL_CENSUS_EXHAUSTED=false
REPO_CURRENT_TREE_CENSUS_COMPLETE=true
REPO_GIT_HISTORY_CENSUS_COMPLETE=true
REPO_SCHEMA_CENSUS_COMPLETE=true
REPO_TERMINOLOGY_INVENTORY_COMPLETE=true
REPO_MASTER_V2_CENSUS_COMPLETE=true
REPO_DOUBLE_PLAY_CENSUS_COMPLETE=true
REPO_FAMILY_CHILD_CENSUS_COMPLETE=true
REPO_DOD_CENSUS_COMPLETE=true
REPO_OKX_CENSUS_COMPLETE=true
REPO_ATLAS_CENSUS_COMPLETE=true
EXTERNAL_FORENSIC_CORPUS_CENSUS_COMPLETE=NOT_STARTED
SYSTEM_ATLAS_DRILLDOWN_LINKS_VALID=true
SYSTEM_ATLAS_ALL_MAJOR_DOMAINS_REPRESENTED=true
SYSTEM_ATLAS_CURRENT_HISTORICAL_SPLIT_VALID=true
SYSTEM_ATLAS_GRAPH_RELATIONS_BACKED_BY_MODEL=true
ATLAS_IMPACT_CHECKER=scripts/ops/check_system_atlas_impact_v1.py
PROJECT_NATIVE_TERM_COUNT=22
ACRONYM_COUNT=3
DOD_COUNT=5
SCHEMA_COUNT=5
TERMINOLOGY_COLLISION_COUNT=9
UNRESOLVED_TERM_COUNT=0
GIT_IS_SHALLOW=false
HISTORICAL_DOMAIN_CENSUS_PAYLOAD_COUNT=0
ATLAS_LEGACY_ERADICATION_V1=true
ACRONYM_CENSUS_INVENTORY_COMPLETE=true
ACRONYM_EXPANSIONS_RESOLVED=false
OKX_PRODUCT_TYPE_CENSUS_COMPLETE=true
OKX_DOCS_CENSUS_COMPLETE=true
OKX_TESTS_CENSUS_COMPLETE=true
OKX_CONFIG_CENSUS_COMPLETE=true
OKX_SCRIPTS_CENSUS_COMPLETE=true
OKX_EVIDENCE_CENSUS_COMPLETE=true
```

## Entity by kind

| kind | count |
| --- | --- |
| ACRONYM | 3 |
| ADAPTER | 1 |
| AUTH_PRIMITIVE | 1 |
| BINDER | 1 |
| CAPABILITY | 20 |
| CONTRACT | 58 |
| DATA_CONTRACT | 6 |
| DOD | 5 |
| EVIDENCE_ARTIFACT | 1 |
| EXPERIMENT | 1 |
| FORENSIC_REFERENCE | 1 |
| FUNCTIONAL_CORE | 1 |
| GATE | 19 |
| HOST | 2 |
| INVARIANT | 1 |
| NAVIGATION_INDEX | 1 |
| OBSERVER | 1 |
| OKX_FEATURE | 1 |
| OWNER_DECISION | 2 |
| PHASE | 1 |
| RUNBOOK | 2 |
| RUNTIME_COMPONENT | 136 |
| SCHEMA | 5 |
| SCRIPT | 3 |
| SELECTOR | 2 |
| SUBSYSTEM | 1 |
| SYSTEM | 1 |
| TERM | 9 |
| TEST | 1 |
| UNIVERSE | 1 |
| VENUE | 2 |
| VENUE_ENDPOINT | 3 |
| VENUE_FIELD | 3 |

## Named gaps

- `Family usages enumerated; no unified Families ontology (C-FAMILY-POLYVALENT-001)`
- `Vollautonomie vs Master Runbook Double Play order CONTRADICTED`
- `quoteCcy empty on EEA public instruments; uly not used for quote`
- `Canary&#47;Flatten post-action and productive GFU membership of SUI XPERP unproven`
- `origin&#47;main OKX-named deletions are zero; in-repo fixture structures inspected (147&#47;147); external corpus NOT_STARTED`
- `WebSocket hosts configured; no proven live WS client`
- `Acronym expansions OPEN (EEA, OKX, XPERP, C1, C2, C3, PRE, PENDING); terminology inventory is otherwise closed`
- `Remaining SCHEMA_VERSION tokens classified TYPE_ONLY&#47;VERSION_TOKEN, not per-token SCHEMA entities`
- `Cap23 analytical exclusivity vs 11.13.5 canary hardcoded SUI (parallel authority)`
- `Master title V2.2 vs REVISION&#47;Map V2.3 version-token mismatch`
- `Cyber header PRE_LIVE_GATE=PASS vs ratification JSON NOT_PASSED`
- `Exact token HAS_FUNCTIONAL_CORE &#47; FUNCTIONAL_CORE not found; Modul-Owner of one Trading Core is proven`
- `Flatten transport implemented but LIVE_WIRE_DISABLED; LIVE_FLATTEN_PROVABILITY not PROVEN`

## Census incompleteness (five-class)

Closed domains are scoped search or file inventory, not ontology-complete.

| id | flag | primary_class | additional | remaining |
| --- | --- | --- | --- | --- |
| ssot_child_census_complete | true | SEARCHED_BUT_NO_EVIDENCE_FOUND |  | Literal absent. TERM:ssot_child_unproven and GAP:ssot_child_undefined remain as absence records, not missing search. |
| mmr_census_complete | true | SEARCHED_BUT_NO_EVIDENCE_FOUND | UNRESOLVED_CONTRADICTION | Venue/margin MMR proven. Architectural Master-V2 MMR kind not found (not invented). C-MMR-POLYVALENT-001 preserved. |
| schema_file_inventory_complete | true | SEARCHED_BUT_NO_EVIDENCE_FOUND |  | Field-level enumeration is in census/schema_field_inventory.yaml (schema_field_enumeration_complete=true). Remaining src SCHEMA_VERSION tokens classified VERSION_TOKEN/TYPE_ONLY in census/schema_like_src.yaml. |
| master_v2_capability_spec_inventory_complete | true | SEARCHED_BUT_NO_EVIDENCE_FOUND |  | Spec files inventoried and entity-mapped. Cap 7.2 and 11.13.5 have no MASTER_V2_CAPABILITY_* spec file. |
| master_v2_census_complete | true | SEARCHED_BUT_NO_EVIDENCE_FOUND |  | Adapter/Surface-P runtime reachability remains library/offline/bound-not-activated. Not live activation. |
| double_play_census_complete | true | SEARCHED_BUT_NO_EVIDENCE_FOUND | UNRESOLVED_CONTRADICTION | C-DP-ORDER-001 preserved. ops.double_play.evaluate_double_play remains quarantined projection. |
| family_census_complete | true | UNRESOLVED_CONTRADICTION | TERMINOLOGY_UNRESOLVED | C-FAMILY-POLYVALENT-001 preserved. NO_FAMILY_ONTOLOGY blocker remains. |
| child_census_complete | true | SEARCHED_BUT_NO_EVIDENCE_FOUND | TERMINOLOGY_UNRESOLVED | None of these is SSOT_CHILD. Literal SSOT_CHILD still absent. |
| schema_field_enumeration_complete | true | SEARCHED_BUT_NO_EVIDENCE_FOUND |  | Remaining SCHEMA_VERSION assignment lines are VERSION_TOKEN/TYPE_ONLY, not unadjudicated SCHEMA entities (schema_census_complete=true). |
| okx_current_tree_census_complete | true | SEARCHED_BUT_NO_EVIDENCE_FOUND |  | Grep path noise (trailing dots, prefix stubs) not promoted to VENUE_ENDPOINT rows. Historical archaeology is separate (okx_historical_census_complete=true). |
| dod_census_complete | true | SEARCHED_BUT_NO_EVIDENCE_FOUND |  | Individual PHASE_* heading criteria not copied verbatim. |
| system_atlas_master_view_complete | true | SEARCHED_BUT_NO_EVIDENCE_FOUND | UNRESOLVED_CONTRADICTION | GLOBAL_CENSUS_EXHAUSTED=false. OPEN acronym expansions and owner-decision/runtime facts remain visible. In-repo fixture inspection is closed. External corpus is NOT_STARTED. Contradictions stay represented. |
| terminology_census_complete | true | SEARCHED_BUT_NO_EVIDENCE_FOUND | TERMINOLOGY_UNRESOLVED | Inventory of material current-project tokens is closed. Unresolved acronym expansions remain OPEN (acronym_census_complete=false). Not an exhaustive all-caps blob-history of every Peak_Trade-native token. |
| schema_census_complete | true | SEARCHED_BUT_NO_EVIDENCE_FOUND |  | Per-field payloads of remaining SCHEMA_VERSION tokens are TYPE_ONLY/VERSION_TOKEN, not unadjudicated SCHEMA. |
| okx_census_complete | true | SEARCHED_BUT_NO_EVIDENCE_FOUND |  | In-repo OKX census closed. External/temp forensic corpus is NOT_STARTED and is not a remaining in-repo search. Unresolved quote/XPERP/canary facts are preserved system records, not missing census. |

Remaining domains:

| id | flag | primary_class | additional | remaining |
| --- | --- | --- | --- | --- |
| okx_historical_census_complete | false | HISTORICAL_SOURCE_UNAVAILABLE |  | ATLAS_LEGACY_ERADICATION_V1 removed historical domain census payloads; CURRENT OKX model uses venue/okx/* plus okx_current_tree.yaml. |
| historical_terminology_census_complete | false | HISTORICAL_SOURCE_UNAVAILABLE |  | Historical terminology archaeology payload purged; CURRENT terminology remains in ontology/* and PROJECT_TERMINOLOGY view. |
| master_v2_module_file_inventory_complete | false | HISTORICAL_SOURCE_UNAVAILABLE |  | Master V2 module inventory census payload purged; CURRENT Master V2 entities remain in catalog and MASTER_V2_DOUBLE_PLAY_MAP. |
| acronym_census_complete | false | TERMINOLOGY_UNRESOLVED | SEARCHED_BUT_NO_EVIDENCE_FOUND | Inventory complete (acronym_census_inventory_complete=true). OPEN expansions searched on origin/main full history without inventing: EEA, OKX, XPERP, C1, C2, C3, PRE, PENDING. TERM_MEANING_KNOWN for venue/token usage; AC |

Completeness-flag reasons (`completeness_flags.*`):

| id | flag | primary_class | additional | remaining |
| --- | --- | --- | --- | --- |
| current_tree_search_complete | true | SEARCHED_BUT_NO_EVIDENCE_FOUND |  | OKX-named files (381) and /api/v5 literals inventoried on origin/main. Not every src/ path is an Atlas entity. |
| git_history_search_complete | true | SEARCHED_BUT_NO_EVIDENCE_FOUND |  | origin/main full history searched for OKX/uly/auth/WS/deletions/OPEN expansions. Unmerged-only branches not treated as product SSOT. |
| forensic_corpus_search_complete | true | SEARCHED_BUT_NO_EVIDENCE_FOUND |  | In-repo OKX forensic inventories structure-inspected. EXTERNAL_FORENSIC_CORPUS_CENSUS_COMPLETE=NOT_STARTED. |
| docs_search_complete | true | SEARCHED_BUT_NO_EVIDENCE_FOUND |  | OKX-named docs (40) plus venue/audit/spec surfaces mapped. Unrelated prose mentions are reference-only, not new endpoints. |
| tests_search_complete | true | SEARCHED_BUT_NO_EVIDENCE_FOUND |  | OKX-named tests (73) plus fixture payloads inspected. Full tests/ universe is not every-file entity-mapped. |
| config_search_complete | true | SEARCHED_BUT_NO_EVIDENCE_FOUND |  | OKX-named config (48) plus config.toml exchange.okx_europe_eea mapped. Unrelated config keys remain out of OKX census. |
| raw_response_fixture_search_complete | true | SEARCHED_BUT_NO_EVIDENCE_FOUND |  | All 147 candidates classified; JSON structures inspected; payloads not copied. External corpus NOT_STARTED. |
| endpoint_inventory_complete | true | SEARCHED_BUT_NO_EVIDENCE_FOUND |  | 70 raw hits classified; 21 grep noise; 49 unique REST paths; 50 modeled rows (GET/POST /trade/order plus GET /asset/balances). finance/funding/system namespaces absent. |
| field_inventory_complete | true | SEARCHED_BUT_NO_EVIDENCE_FOUND |  | 42 seed+observed tokens classified; 40 VENUE_FIELD rows; availPos zero hits; envelope data not a scalar field. Not every undocumented OKX v5 packet field. |
| product_type_inventory_complete | true | SEARCHED_BUT_NO_EVIDENCE_FOUND |  | SWAP/FUTURES implemented; SPOT explicit GFU reject; MARGIN/OPTION no OKX instType evidence; xperp partial (not a separate instType). |
| auth_inventory_complete | true | SEARCHED_BUT_NO_EVIDENCE_FOUND |  | HMAC signer, OK-ACCESS-* headers, x-simulated-trading, REST/WS hosts, LIVE_AUTHORIZED gate recorded. Credential values never stored. Other undocumented auth surfaces not claimed. |
| historical_removal_search_complete | true | SEARCHED_BUT_NO_EVIDENCE_FOUND |  | origin/main OKX-named path deletions are zero. Non-okx-named historical API callers not every-file enumerated. |

