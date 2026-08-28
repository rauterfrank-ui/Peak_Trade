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
