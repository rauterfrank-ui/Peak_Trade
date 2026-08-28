# Peak_Trade Information Corpus Persistence Base

```text
DOCUMENT_CLASS=NON_AUTHORITATIVE_INFORMATION_CORPUS_PERSISTENCE_BASE
DOCUMENT_ROLE=REGISTRY_AND_NAVIGATION_ONLY
AUTHORITY=NONE
TARGET_AUTHORITY=NONE
NAVIGATION_ONLY=true
INDEX_ENTRY_IS_NOT_ADJUDICATION=true
INDEX_ENTRY_IS_NOT_COMPLETENESS_PROOF=true
CANONICAL=false
SECOND_SSOT=false
SEMANTIC_AUTHORITY=false
RUNTIME_AUTHORIZATION_EFFECT=NONE

MASTER_RUNBOOK_REMAINS_SOLE_CANONICAL_SSOT=true
MAP_OF_TRUTH_REMAINS_NAVIGATION_ONLY=true
THIS_BASE_MUST_NOT_OVERRIDE_MASTER_RUNBOOK=true
THIS_BASE_MUST_NOT_OVERRIDE_MAP_OF_TRUTH=true
THIS_BASE_MUST_NOT_BE_USED_AS_OWNER_DECISION_AUTHORITY=true
THIS_BASE_MUST_NOT_BE_USED_AS_TYPE_ONTOLOGY_AUTHORITY=true
THIS_BASE_MUST_NOT_ACTIVATE_LIVE_TESTNET_ORDERS_OR_CREDENTIALS=true

EXTERNAL_SOURCE_FOLDER_IS_NOT_THIS_BASE=true
OWNER_NAMED_PEAK_TRADE_FORENSIK_FOLDER_IS_NOT_SSOT=true
```

Purpose: persist discovery, identity, and provenance registration for
Peak_Trade information-corpus work so a later main agent can continue
without chat memory.

This directory may register locators and hashes from repo sources and
from authorized external read-only surfaces. It must not rewrite those
sources. It must not present an external locator as originally
repo-internal.

## Layout

| Path | Role |
|------|------|
| `AUTHORITY_NONE.txt` | Authority containment |
| `PEAK_TRADE_INFORMATION_CORPUS_PERSISTENCE_BASE.md` | This index |
| `registries&#47;EXTERNAL_FORENSIC_CORPUS_DISCOVERY_V1.md` | P2 discovery closeout plus P1/P3–P7 inventory |
| `registries&#47;CROSS_CORPUS_RELATION_REGISTER_V1.md` | Proven vs unknown relations (P2/P5-vs-repo axes; **not** the P6_5189 observation graph) |
| `registries&#47;P6_5189_RELATION_LEDGER_V1.json` | Central P6_5189 relation ledger (AUTHORITY=NONE; index entry is not adjudication) |
| `registries&#47;P6_5189_RELATION_NODE_REGISTER_V1.json` | P6_5189 relation node register (AUTHORITY=NONE; node identity is not source identity) |
| `registries&#47;P6_5189_SET_AND_UNIVERSE_REGISTER_V1.json` | P6_5189 set/universe register (AUTHORITY=NONE; counts not normalized; 5185 != 5189 != 5190) |
| `registries&#47;P6_5189_PROOF_OBLIGATION_MATRIX_V1.json` | P6_5189 proof-obligation matrix (AUTHORITY=NONE; source graph is not the proof graph; index entry is not completeness proof) |
| `inventories&#47;P1_REPO_FORENSIC_TREES_FILE_INVENTORY_V1.json` | Repo forensic-tree file identities |
| `inventories&#47;P1_REPO_FORENSIC_TREES_FILE_INVENTORY_V1.contract.json` | P1 historical snapshot membership contract sidecar (AUTHORITY=NONE; not a live census) |
| `inventories&#47;P5_DOCUMENTS_PEAK_TRADE_FORENSICS_FILE_INVENTORY_V1.json` | Evidence-bound local `Documents&#47;Peak_Trade&#47;forensics` identities |
| `inventories&#47;CROSS_CORPUS_RELATION_FACTS_V1.json` | Machine relation facts |
| `inventories&#47;P6_5189_FINAL_4_UNRESOLVED_RESOLUTION_OBSERVATION_V1.json` | Additive P6 5189 final-4 coverage observation (AUTHORITY=NONE) |
| `inventories&#47;P6_5189_FINAL_2_UNRESOLVED_RECOVERY_OBSERVATION_V1.json` | Additive P6 5189 final-2 recovery coverage observation (AUTHORITY=NONE) |
| `inventories&#47;P6_5189_FINAL_1_UNRESOLVED_RECOVERY_OBSERVATION_V1.json` | Additive P6 5189 final-1 recovery coverage observation (AUTHORITY=NONE) |
| `inventories&#47;P6_5189_5011_SOURCE_SET_LOCALIZATION_OBSERVATION_V1.json` | Additive P6 5189 5011 source-set localization observation (AUTHORITY=NONE) |
| `inventories&#47;P6_5189_NON_P2_ARCHIVE_LOCALIZATION_OBSERVATION_V1.json` | Additive P6 5189 non-P2 archive localization observation (AUTHORITY=NONE) |
| `inventories&#47;P6_5189_RAW_EXECUTION_RECOVERY_OBSERVATION_V1.json` | Additive P6 5189 raw-execution-recovery observation (AUTHORITY=NONE) |
| `inventories&#47;P6_5189_PERSISTED_EVIDENCE_COMPLETENESS_AND_CLOSURE_SYNTHESIS_OBSERVATION_V1.json` | Additive P6 5189 completeness-and-closure synthesis observation (AUTHORITY=NONE) |
| `inventories&#47;P6_5189_37G_ARCHIVE_SQLITE_VSCDB_BODY_PREIMAGE_PROBE_OBSERVATION_V1.json` | Additive P6 5189 37G-archive sqlite/vscdb-body preimage-probe observation (AUTHORITY=NONE) |
| `inventories&#47;P6_5189_POST_SQLITE_RESIDUAL_FRONTIER_OBSERVATION_V1.json` | Additive P6 5189 post-PR6081 residual-frontier observation (AUTHORITY=NONE) |
| `inventories&#47;P6_5189_SCOPED_IRREDUCIBLE_HISTORICAL_UNKNOWN_TWO_FULL_SHA_PREIMAGES_OWNER_ADJUDICATION_V1.json` | Additive P6 5189 scoped Owner acceptance of two full-SHA preimages as irreducible on examined identified surfaces (AUTHORITY=NONE) |
| `inventories&#47;P6_5189_SLICE_5_NO_CONTRADICTION_LAYERED_STATUSES_OBSERVATION_V1.json` | Additive P6 5189 Slice-5 no-contradiction layered-statuses observation (AUTHORITY=NONE) |
| `inventories&#47;P6_5189_PREFIX_60164328_ATTESTATION_ANATOMY_AND_PREDICATE_SEPARATION_OBSERVATION_V1.json` | Additive P6 5189 prefix-60164328 attestation-anatomy and predicate-separation observation (AUTHORITY=NONE) |
| `inventories&#47;P6_5189_OPEN_FRONTIER_DEPENDENCY_AND_CLOSURE_CRITICAL_PATH_SYNTHESIS_OBSERVATION_V1.json` | Additive P6 5189 open-frontier dependency and closure-critical-path synthesis observation (AUTHORITY=NONE; index entry is not adjudication) |
| `inventories&#47;P6_5189_COUNT_DRIFT_3946_3951_LOCATOR_SEMANTICS_ADJUDICATION_OBSERVATION_V1.json` | Additive P6 5189 count-drift 3946/3951 locator-semantics observation (AUTHORITY=NONE; index entry is not adjudication) |
| `inventories&#47;P6_5189_POST_COUNT_DRIFT_GLOBAL_CLOSURE_FRONTIER_AND_MAX_LEVERAGE_NEXT_STEP_ADJUDICATION_OBSERVATION_V1.json` | Additive P6 5189 post-count-drift global-closure frontier observation (AUTHORITY=NONE; index entry is not adjudication) |
| `inventories&#47;P6_5189_UNRESOLVED_DEPENDENCY_MATRIX_AND_GAP_CLOSED_INBOUND_RELATIONS_ADJUDICATION_OBSERVATION_V1.json` | Additive P6 5189 unresolved-dependency-matrix observation (AUTHORITY=NONE; index entry is not adjudication) |
| `inventories&#47;P6_5189_UNRESOLVED_RELATION_EVIDENCE_SURFACE_EXHAUSTION_AND_OWNER_DECISION_BOUNDARY_ADJUDICATION_OBSERVATION_V1.json` | Additive P6 5189 unresolved-relation evidence-surface exhaustion observation (AUTHORITY=NONE; index entry is not adjudication) |
| `inventories&#47;P6_5189_GLOBAL_EVIDENCE_SURFACE_UNIVERSE_COMPLETENESS_AND_EXHAUSTION_ADJUDICATION_OBSERVATION_V1.json` | Additive P6 5189 global evidence-surface universe observation (AUTHORITY=NONE; index entry is not completeness proof) |
| `inventories&#47;P6_5189_UNRESOLVED_PAIR_CLOSURE_MODE_AND_MAX_LEVERAGE_FRONTIER_ADJUDICATION_OBSERVATION_V1.json` | Additive P6 5189 unresolved-pair closure-mode observation (AUTHORITY=NONE; index entry is not adjudication) |
| `inventories&#47;P6_5189_UNRESOLVED_PAIR_DEP_NON_PROOF_OBLIGATION_AND_SHARED_DISCRIMINANT_SYNTHESIS_OBSERVATION_V1.json` | Additive P6 5189 unresolved-pair DEP/NON proof-obligation observation (AUTHORITY=NONE; index entry is not adjudication) |
| `inventories&#47;P6_5189_HISTORICAL_SOURCE_SET_UNIVERSE_AND_POSITIVE_MEMBERSHIP_LEDGER_AND_THREE_HASH_NON_INFERENCE_OBSERVATION_V1.json` | Additive P6 5189 historical source-set universe and membership-ledger observation (AUTHORITY=NONE; index entry is not completeness proof) |
| `inventories&#47;P6_5189_UNRESOLVED_PAIR_MAX_LEVERAGE_MULTI_STEP_READ_ONLY_WORKPACKAGE_OBSERVATION_V1.json` | Additive P6 5189 unresolved-pair max-leverage multi-step read-only workpackage observation (AUTHORITY=NONE; distinct from historical-source-set observation) |
| `inventories&#47;P6_5189_POST_GLOBAL_CLOSURE_MAX_LEVERAGE_FRONTIER_ADJUDICATION_READ_ONLY_OBSERVATION_V1.json` | Additive historical coverage of the post-global-closure max-leverage read-only execution and its negative finding (AUTHORITY=NONE; distinct from unresolved-dependency-matrix observation) |
| `inventories&#47;P6_5189_COMPLETENESS_REVALIDATION_OBSERVATION_V1.json` | Additive P6 5189 completeness-revalidation observation (AUTHORITY=NONE; distinct from 5011 localization and from completeness-synthesis observation; index entry is not completeness proof) |
| `inventories&#47;P6_5189_FORENSIC_LAYER_COMPLETENESS_AUDIT_AND_EXISTING_EVIDENCE_GRAPH_REPRESENTATION_REPAIR_OBSERVATION_V1.json` | Additive persist of the layer-completeness / cross-layer-coverage read-only audit plus existing-evidence graph-representation repair (AUTHORITY=NONE; index entry is not completeness proof; 36 was the pre-workpackage count) |
| `inventories&#47;P6_5189_DOMAIN_IDENTITY_NON_JOIN_AND_MARKET_ROLE_OBSERVATION_V1.json` | Additive persist of the domain-instrument-identity non-join and MARKET role observation (AUTHORITY=NONE; not a P6 source set; does not add members to the P6 set/universe register; index entry is not adjudication or completeness proof; 37 was the pre-that-workpackage count) |
| `inventories&#47;P6_5189_DOMAIN_IDENTITY_D01_D03_OWNER_DECISION_ADJUDICATION_OBSERVATION_V1.json` | Additive persist of the D01–D03 owner-decision adjudication (AUTHORITY=NONE; does not overwrite the PR-6101 observation; index entry is not canonical adjudication or completeness proof; 38 was the pre-that-workpackage count) |
| `inventories&#47;P6_CAP2_GAP_U_RISK_007_CLASS_A_FALSE_GAP_ADJUDICATION_OBSERVATION_V1.json` | Additive persist of the GAP-U-RISK-007 CLASS_A false-gap layer (AUTHORITY=NONE; does not overwrite the PR-6101 UNPROVEN original predicate or the PR-6102 unchanged record; CLASS_A is report language not a new persistence status class; index entry is not canonical adjudication or completeness proof; 39 was the pre-this-workpackage count before the CLASS_A file) |
| `inventories&#47;P6_CAP2_DUAL_EXECUTION_SURFACE_AND_LIVE_FRONTIER_ADJUDICATION_OBSERVATION_V1.json` | Additive persist of the Cap-2 dual-execution-surface and remaining live-frontier read-only layer (AUTHORITY=NONE; does not overwrite the CLASS_A file; Step-C result forms are report language not new persistence enums; index entry is not canonical adjudication or completeness proof; 40 was the count after the CLASS_A file) |
| `inventories&#47;P6_LIVE_GFU_NETWORK_GET_ONLY_RAW_GET_SOURCE_ENVELOPES_V1.json` | Additive persist of four verbatim eea.okx.com public GET source envelopes for the live GFU census (AUTHORITY=NONE; four source identities not merged; index entry is not membership authority or completeness proof; 41 was the count after the dual-surface file) |
| `inventories&#47;P6_LIVE_GFU_NETWORK_GET_ONLY_CENSUS_AND_GAP_ADJUDICATION_OBSERVATION_V1.json` | Additive persist of the NETWORK_GET_ONLY Cap-2.1 eligibility application plus separate GAP-U-GFU-LIVE and GAP-U-CAN-006 adjudication (AUTHORITY=NONE; does not overwrite the dual-surface file; result forms are report language not new persistence enums; GET metadata is not membership authority; index entry is not canonical adjudication or completeness proof; 42 was the count after the raw envelopes file) |
| `inventories&#47;P6_CAP21_SOURCE_EVENT_TIME_CROSS_SOURCE_BINDING_ADJUDICATION_OBSERVATION_V1.json` | Additive persist of the Cap-2.1 `source_event_time` cross-source binding contract adjudication plus Owner Decision Boundary `CAP21_SOURCE_EVENT_TIME_CROSS_SOURCE_BINDING_V1` (AUTHORITY=NONE; does not overwrite the census or raw-envelope files; A/B/C/D result forms are report language not new persistence enums; no offline reclassification; index entry is not canonical adjudication or completeness proof; 43 was the count after the census file) |
| `inventories&#47;P6_CAP21_SOURCE_EVENT_TIME_CROSS_SOURCE_BINDING_V1_OPTION_C_DECISION_OBSERVATION_V1.json` | Additive persist of Owner OPTION_C `DEFER_KEEP_UNPROVEN` for `CAP21_SOURCE_EVENT_TIME_CROSS_SOURCE_BINDING_V1` plus restatement that the 645 observed rows remain UNPROVEN (AUTHORITY=NONE; does not overwrite the decision-surface file; OPTION_C is not OPTION_A allow and not OPTION_B prohibit; no reclassification; no network GET; no canonical mutation; index entry is not canonical adjudication or completeness proof; 44 was the count after the decision-surface file) |

```text
PRE_LAYER_COMPLETENESS_WORKPACKAGE_PERSISTENCE_ARTIFACT_COUNT=36
POST_LAYER_COMPLETENESS_WORKPACKAGE_PERSISTENCE_ARTIFACT_COUNT=37
COUNT_36_IS_HISTORICAL_SNAPSHOT_NOT_CURRENT=true
PRE_PR6101_DOMAIN_IDENTITY_WORKPACKAGE_PERSISTENCE_ARTIFACT_COUNT=37
POST_PR6101_DOMAIN_IDENTITY_WORKPACKAGE_PERSISTENCE_ARTIFACT_COUNT=38
COUNT_37_IS_PRE_PR6101_SNAPSHOT_NOT_CURRENT=true
PRE_PR6102_D01_D03_WORKPACKAGE_PERSISTENCE_ARTIFACT_COUNT=38
POST_PR6102_D01_D03_WORKPACKAGE_PERSISTENCE_ARTIFACT_COUNT=39
COUNT_38_IS_PRE_PR6102_SNAPSHOT_NOT_CURRENT=true
PRE_CLASS_A_FILE_PERSISTENCE_ARTIFACT_COUNT=39
POST_CLASS_A_FILE_PERSISTENCE_ARTIFACT_COUNT=40
PRE_DUAL_SURFACE_FILE_PERSISTENCE_ARTIFACT_COUNT=40
POST_DUAL_SURFACE_FILE_PERSISTENCE_ARTIFACT_COUNT=41
PRE_CENSUS_WORKPACKAGE_PERSISTENCE_ARTIFACT_COUNT=41
POST_RAW_ENVELOPES_FILE_PERSISTENCE_ARTIFACT_COUNT=42
POST_CENSUS_FILE_PERSISTENCE_ARTIFACT_COUNT=43
PRE_BINDING_ADJUDICATION_WORKPACKAGE_PERSISTENCE_ARTIFACT_COUNT=43
POST_BINDING_ADJUDICATION_FILE_PERSISTENCE_ARTIFACT_COUNT=44
PRE_THIS_WORKPACKAGE_PERSISTENCE_ARTIFACT_COUNT=44
POST_THIS_WORKPACKAGE_PERSISTENCE_ARTIFACT_COUNT=45
COUNT_39_IS_PRE_CLASS_A_SNAPSHOT_NOT_CURRENT=true
COUNT_40_IS_INTERMEDIATE_AFTER_CLASS_A_FILE_NOT_COLLAPSED_ONTO_41=true
COUNT_41_IS_PRE_CENSUS_WORKPACKAGE_SNAPSHOT_NOT_POST_CENSUS_CURRENT=true
COUNT_42_IS_INTERMEDIATE_AFTER_RAW_ENVELOPES_FILE_NOT_COLLAPSED_ONTO_43=true
COUNT_43_IS_POST_CENSUS_FILE_NOT_COLLAPSED_ONTO_44=true
COUNT_44_IS_POST_BINDING_ADJUDICATION_FILE_NOT_COLLAPSED_ONTO_45=true
COUNT_36_AND_37_AND_38_AND_39_AND_40_AND_41_AND_42_AND_43_AND_44_AND_45_NOT_COLLAPSED=true
INDEX_ENTRY_IS_NOT_COMPLETENESS_PROOF=true
INDEX_ENTRY_IS_NOT_ADJUDICATION=true
NAVIGATION_ONLY=true
THIS_INDEX_ENTRY_IS_NOT_A_P6_SOURCE_SET=true
```


## Provenance classes used here

```text
SOURCE_CLASS=REPO_INTERNAL
SOURCE_CLASS=LOCAL_EXTERNAL_FORENSIC_SOURCE
SOURCE_CORPUS=OWNER_NAMED_PEAK_TRADE_FORENSIK_FOLDER
SOURCE_CORPUS_P2_STATUS=NOT_UNIQUELY_RESOLVED
P2_CONTENT_INVENTORY_STATUS=NOT_PERFORMABLE_WITHOUT_RESOLVED_CORPUS
P2_UNRESOLVED_IS_NOT_P2_EMPTY=true
SOURCE_CORPUS=DOCUMENTS_PEAK_TRADE_FORENSICS_EVIDENCE_BOUND_P5_NOT_OWNER_NAMED_FORENSIK_FOLDER
```

BYTE_IDENTICAL does not merge source identity. Both locators remain.
Unresolved P2 is not an empty-corpus claim.
