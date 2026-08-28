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

## Federated information architecture (entrypoint)

Start here for subject/source/state lookup. Do not rediscover all
corpora. These layers are `AUTHORITY=NONE` navigation. They do not
replace the Master Runbook or Map of Truth.

| Layer | Path | Role |
|-------|------|------|
| L0 | [Federated Source Surface Registry](registries/FEDERATED_SOURCE_SURFACE_REGISTRY_V1.md) | Known source surfaces SS-01..SS-14 |
| L2 | [Information Object Reference Registry](registries/INFORMATION_OBJECT_REFERENCE_REGISTRY_V1.md) | Stable subjects → existing artifacts; Cap-2.1 chain; non-collapse bindings |
| L4 | [Current State Projection](registries/CURRENT_STATE_PROJECTION_V1.md) | Derived current-state view plus reconstruction tests |
| Maintenance | [Federated Entrypoint Maintenance Contract](FEDERATED_ENTRYPOINT_MAINTENANCE_CONTRACT_V1.md) | Required L0/L2/L4 impact checks for later persistence mutates |
| Completeness policy | [Forensic Completeness Scoping Contract](FORENSIC_COMPLETENESS_SCOPING_CONTRACT_V1.md) | Owner-selected `FEDERATED_SCOPED_COMPLETENESS_POLICY_V1` binding (AUTHORITY=NONE; not a universe census; not canonical) |

Reused L1 / L3 owners (not rewritten by the federated persist):

- P1 / P5 inventories
- [External Forensic Corpus Discovery](registries/EXTERNAL_FORENSIC_CORPUS_DISCOVERY_V1.md)
- [Cross-Corpus Relation Register](registries/CROSS_CORPUS_RELATION_REGISTER_V1.md)
- P6_5189 relation / node / set / proof registries
- existing observation identities under `inventories&#47;`

```text
FEDERATED_ENTRYPOINT_MATERIALIZED=true
PROJECTION_IS_NOT_CANONICAL=true
PROJECTION_IS_NOT_NEW_ADJUDICATION=true
COPY_OF_EXTERNAL_CORPUS_REQUIRED=false
HISTORICAL_OBSERVATION_REWRITE_COUNT=0
FEDERATED_ENTRYPOINT_MAINTENANCE_CONTRACT=docs/forensics/persistence/FEDERATED_ENTRYPOINT_MAINTENANCE_CONTRACT_V1.md
FORENSIC_COMPLETENESS_SCOPING_CONTRACT=docs/forensics/persistence/FORENSIC_COMPLETENESS_SCOPING_CONTRACT_V1.md
DEFAULT_DISCOVERY_ORDER=BASE_THEN_L0_THEN_L2_THEN_L4_THEN_TARGETED_PRIMARY_EVIDENCE
BROAD_REDISCOVERY_REQUIRES_INSUFFICIENCY_FINDING=true
```

## Layout

| Path | Role |
|------|------|
| `AUTHORITY_NONE.txt` | Authority containment |
| `PEAK_TRADE_INFORMATION_CORPUS_PERSISTENCE_BASE.md` | This index |
| `FEDERATED_ENTRYPOINT_MAINTENANCE_CONTRACT_V1.md` | Process contract: L0/L2/L4 impact checks before later persistence mutates (AUTHORITY=NONE) |
| `FORENSIC_COMPLETENESS_SCOPING_CONTRACT_V1.md` | Owner-selected federated scoped completeness policy binding (AUTHORITY=NONE; not a universe census; not canonical runtime authority) |
| `registries&#47;FEDERATED_SOURCE_SURFACE_REGISTRY_V1.md` | L0 federated source-surface registry (AUTHORITY=NONE; not a universe census) |
| `registries&#47;INFORMATION_OBJECT_REFERENCE_REGISTRY_V1.md` | L2 subject→artifact reference registry (AUTHORITY=NONE; payloads stay in original artifacts) |
| `registries&#47;CURRENT_STATE_PROJECTION_V1.md` | L4 derived current-state projection (AUTHORITY=NONE; navigation only; not a new adjudication) |
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
| `inventories&#47;P6_POST_PR6105_REMAINING_RESIDUAL_FRONTIER_COMPLETENESS_AND_MAX_LEVERAGE_ADJUDICATION_OBSERVATION_V1.json` | Additive persist of the post-PR6105 remaining-residual-frontier, catalog-completeness, and max-leverage ranking (AUTHORITY=NONE; does not overwrite the OPTION_C decision file, census, or raw envelopes; completeness remains UNPROVEN not DISPROVEN; unique next step is an exhaustion finding for this live GFU eligibility/completeness-proof forensic ladder, not a unique closer of remaining residuals; index entry is not canonical adjudication or completeness proof; 45 was the count after the OPTION_C file) |
| `inventories&#47;P6_POST_PR6106_SEPARATE_RESIDUALS_FORENSIC_CLOSABILITY_AND_HIGHEST_LEVERAGE_WORKPACKAGE_ADJUDICATION_OBSERVATION_V1.json` | Additive persist of post-PR6106 per-residual forensic closability plus highest-leverage workpackage ranking (AUTHORITY=NONE; does not overwrite the PR6106 ranking file; ranking is a workpackage class not a unique residual closer; OPTION_A/B not selected; no network GET; no reclassification; index entry is not canonical adjudication or completeness proof; 46 was the count after the PR6106 ranking file) |
| `inventories&#47;P6_POST_PR6109_FEDERATED_OPEN_SYSTEM_FRONTIER_DEPENDENCY_CLOSABILITY_AND_MAX_LEVERAGE_ADJUDICATION_OBSERVATION_V1.json` | Additive persist of the post-PR6109 federated open-system-frontier reconstruction, dependency/closability classification, and max-leverage ranking (AUTHORITY=NONE; does not overwrite the PR6107 Cap-2.1 closability file; unique system-wide closer absent; OPTION_A/B not selected; OPTION_C not reopened; RISK007 not reopened; index entry is not canonical adjudication or completeness proof; 51 was the count after the maintenance-contract file) |
| `inventories&#47;P6_EXISTING_EVIDENCE_FEDERATED_L0_L2_L4_RECONCILIATION_AND_BACKFILL_OBSERVATION_V1.json` | Additive persist of existing-evidence L0/L2/L4 reconciliation and missing-projection backfill (AUTHORITY=NONE; does not overwrite A-OBS-PR6109; no re-adjudication; no new domain ontology; source identities not collapsed; index entry is not canonical adjudication or completeness proof; 52 was the count after the PR6109 system-frontier file) |
| `inventories&#47;P6_P3_CLASS_C_AUTHENTICATED_SUI_RUNTIME_GET_RAW_GET_SOURCE_ENVELOPES_V1.json` | Additive persist of six verbatim authenticated eea.okx.com GET source envelopes for the P3 Class C SUI runtime pack (AUTHORITY=NONE; six source identities not merged even where BODY_SHA256 matches historical empty-envelope or 11.13.2 config digests; uid redacted; index entry is not membership authority or completeness proof; 53 was the count after the reconciliation file) |
| `inventories&#47;P6_P3_CLASS_C_AUTHENTICATED_SUI_RUNTIME_GET_ADJUDICATION_OBSERVATION_V1.json` | Additive persist of the P3 Class C authenticated SUI runtime GET existing-contract application plus dependency cascade (AUTHORITY=NONE; does not overwrite A-OBS-PR6109 or A-OBS-RECON; does not consume canonical Class C; empty≠zero; Category C runtime TARGET_CATEGORY_C_NOT_OBSERVED this window is not universal absence; OPTION_A/B not selected; index entry is not canonical adjudication or completeness proof; 54 was the count after the raw envelopes file) |
| `inventories&#47;P6_P3_CLASS_D_Z2AP_FLATTEN_PREEXECUTION_READINESS_RAW_GET_SOURCE_ENVELOPES_V1.json` | Additive persist of five verbatim authenticated eea.okx.com GET source envelopes for the P3 Class D / Z2AP flatten pre-execution pack (AUTHORITY=NONE; five source identities not merged even where BODY_SHA256 matches historical empty-envelope digests; index entry is not flatten proof or completeness proof; 55 was the count after the Class C observation file) |
| `inventories&#47;P6_P3_CLASS_D_Z2AP_FLATTEN_PREEXECUTION_READINESS_ADJUDICATION_OBSERVATION_V1.json` | Additive persist of the P3 Class D / Z2AP flatten pre-execution readiness existing-contract application plus dependency cascade (AUTHORITY=NONE; does not overwrite A-OBS-P3C or Z2CB; does not consume canonical Class D; empty≠zero; EXECUTION_READY=false; OPTION_A/B not selected; index entry is not canonical adjudication or completeness proof; 56 was the count after the Class D raw envelopes file) |
| `inventories&#47;P6_P3_CLASS_D_Z2CK_BLOCKER_SUCCESS_PREDICATE_AND_TRANSPORT_GAP_ADJUDICATION_OBSERVATION_V1.json` | Additive persist of post-Z2CK blocker normalization, success-predicate contradiction preservation, and productive-transport gap application (AUTHORITY=NONE; does not overwrite A-OBS-P3D or Z2CB; does not consume canonical Class D; does not repair SUCCESS_PREDICATE_STATUS=CONTRADICTED; empty≠zero; EXECUTION_READY=false; OPTION_A/B not selected; index entry is not canonical adjudication or completeness proof; 57 was the count after the Class D observation file) |
| `inventories&#47;P6_Z2CL_CHOICE_B_AND_PRODUCTIVE_TRANSPORT_OFFLINE_IMPLEMENTATION_OBSERVATION_V1.json` | Additive persist of Owner CHOICE_B plus offline productive urllib implementation (AUTHORITY=NONE; does not overwrite A-OBS-Z2CK-BLK; historical Z2CK CONTRADICTED preserved; does not consume Class D or Z2AP; authenticated POST remains unresolved; OPTION_A/B not selected; index entry is not canonical adjudication or completeness proof; 58 was the count after the Z2CK blocker file) |
| `inventories&#47;P6_Z2CL_PREMERGE_INVARIANT_AUDIT_OBSERVATION_V1.json` | Additive persist of the PR #6116 first-head pre-merge trading-invariant audit (AUTHORITY=NONE; does not overwrite A-OBS-Z2CL; records DO_NOT_MERGE_YET and Choice-B FP count 12; index entry is not canonical adjudication or completeness proof; 59 was the count after the Z2CL implementation file) |
| `inventories&#47;P6_Z2CL_PREMERGE_CHOICE_B_CAUSAL_AND_TRANSPORT_HARDENING_OBSERVATION_V1.json` | Additive persist of pre-merge Choice-B causal binding plus productive-transport identity hardening (AUTHORITY=NONE; does not overwrite A-OBS-Z2CL or the premerge audit observation; does not consume Class D; authenticated POST remains unresolved; OPTION_A/B not selected; index entry is not canonical adjudication or completeness proof; 60 was the count after the premerge audit file) |
| `inventories&#47;P6_Z2CL_POST_MERGE_AUTHENTICATED_TRANSPORT_AND_RUNTIME_PROOF_SURFACES_ADJUDICATION_OBSERVATION_V1.json` | Additive persist of the post-Z2CL read-only authenticated-transport and runtime-proof-surface adjudication (AUTHORITY=NONE; does not overwrite A-OBS-Z2CL-HARDEN or earlier Z2CL/Z2CK/P3C/P3D identities; five productive runtime-proof surfaces remain 0 proven / 5 unproven; authenticated POST remains unresolved; index entry is not canonical adjudication or completeness proof; 61 was the count after the premerge hardening file) |
| `inventories&#47;P6_Z2CL_OFFLINE_SEMANTIC_BINDINGS_ADJUDICATION_OBSERVATION_V1.json` | Additive persist of the post-RT-PROOF offline semantic-binding implementation adjudication (AUTHORITY=NONE; does not overwrite A-OBS-Z2CL-RT-PROOF; offline fail-closed invariants are not productive runtime proofs; five productive runtime-proof surfaces remain 0 proven / 5 unproven; index entry is not canonical adjudication or completeness proof; 62 was the count after the RT-PROOF file) |
| `inventories&#47;P6_Z2CL_RUNTIME_UNIVERSE_RECONSTITUTION_OBSERVATION_V1.json` | Additive persist of reconstituted Z2CL SUI full-flatten runtime-universe and connection inventory (AUTHORITY=NONE; does not overwrite A-OBS-Z2CL-OFFLINE-SEM; universe remains OPEN not closed not exhausted; U-RF and CN labels are local audit labels not persistence identities; Z2CL is not Z2L; Category C send wiring absent as flatten_execute fact not global IN/OUT; index entry is not canonical adjudication completeness proof or universe closure; 63 was the count after the offline SEM file) |
| `inventories&#47;P6_Z2CL_IDENTITY_AND_HEADER_GAP_ADJUDICATION_OBSERVATION_V1.json` | Additive persist of D1 dirty-vs-committed U-RF-19/CN-12 locator contradiction and D2 committed receipt-identity vs forwarded-headers coverage gap (AUTHORITY=NONE; does not overwrite A-OBS-Z2CL-UNIVERSE-RECON; does not mint U-RF/CN/UC IDs; CN-20 remains committed ABSENT / dirty PRESENT; header gap is coverage not authentication; census-count discontinuity remains open; index entry is not canonical adjudication completeness proof or universe closure; 64 was the count after the universe-recon file) |
| `inventories&#47;P6_Z2CL_SCHEMA_NEGATIVE_CAPABILITY_AND_CENSUS_LINEAGE_OBSERVATION_V1.json` | Additive persist of schema/ontology negative-capability plus Census-48 lineage UNPROVEN (AUTHORITY=NONE; does not overwrite A-OBS-Z2CL-ID-HDR-GAP or A-OBS-Z2CL-UNIVERSE-RECON; does not mint UC/U-RF/CN/SET IDs; does not create a schema or ontology; R3 remains historical design-only; SW_R_002 remains OPEN_NO_TYPE_ONTOLOGY; structural sidecar/FSS remain non-semantic for census membership; P6_5189 SET register remains domain-scoped; no existing examined schema source-bound explains declared 48; count HARD_BLOCK remains OPEN; index entry is not canonical adjudication completeness proof universe closure or hard-block resolution; 65 was the count after the identity/header-gap file) |
| `inventories&#47;P6_Z2CL_COMPLETENESS_PRECONDITION_AND_CLOSED_UNIVERSE_EXCLUSION_GAP_OBSERVATION_V1.json` | Additive persist of completeness-precondition and closed-universe-exclusion gaps (AUTHORITY=NONE; does not overwrite A-OBS-Z2CL-SCHEMA-NC-CENSUS-LINEAGE; does not mint UC/U-RF/CN/SET IDs; does not create a schema, ontology, CU-exclusion contract, or census domain; 20 scoped exclusions remain distinct from 0 CU-exclusions; L0 remains non-census; 0/22 named domains currently completeness-ready as audit status not impossibility; repo+external union and completeness dedup remain undefined; dirty worktree remains unbound not globally included or excluded; count HARD_BLOCK remains OPEN; index entry is not canonical adjudication completeness proof universe closure or hard-block resolution; 66 was the count after the schema-nc census-lineage file) |
| `inventories&#47;P6_Z2CL_OD_01_08_RECONSTRUCTION_DELTA_OBSERVATION_V1.json` | Additive persist of OD-01..OD-08 reconstruction lineage (AUTHORITY=NONE; does not overwrite A-OBS-Z2CL-COMPLETENESS-PRECONDITION-GAPS; does not answer Owner semantic choices; does not create a choice menu or new semantic choice; ENUMERATED_ALLOWED_CHOICES remain NONE_PROVEN; UNIQUE_DECISION_ORDER_PROVEN=false; CROSS_SURFACE_DEPENDENCY_COUNT=0 is not semantic-independence proof; GAP_ID mappings are lineage not source-identity collapse; OD-07 preserves G-STOP-LIVE and G-Z2CL-STOP as separate identities; G-P2 is not OD-09; OD-01..OD-08 are not UQ1..UQ8/RD01..RD10, not IO-SWR002, and not Master-Runbook §20; OD-08 still carries Census-48 HARD_BLOCK with no proven gate order for OD-01..OD-07; 20 scoped exclusions remain distinct from 0 CU-exclusions; count HARD_BLOCK remains OPEN; index entry is not canonical adjudication completeness proof universe closure or hard-block resolution; 67 was the count after the completeness-precondition-gaps file) |
| `inventories&#47;P6_FEDERATED_SCOPED_COMPLETENESS_POLICY_OWNER_DECISION_OBSERVATION_V1.json` | Additive persist of the Owner-selected `FEDERATED_SCOPED_COMPLETENESS_POLICY_V1` decision bundle (AUTHORITY=NONE; does not overwrite A-OBS-Z2CL-OD-01-08-RECONSTRUCTION-DELTA; records OD-01=A through OD-08=A without creating a global forensic object, UC-IDs, or a union census domain; Census-48 remains unresolved historical assertion not an operational count; policy alone does not set `CLOSED_UNIVERSE_PROVEN` or `SOURCE_UNIVERSE_EXHAUSTED`; index entry is not canonical adjudication completeness proof or universe closure; 69 was the count after the scoping-contract file) |
| `inventories&#47;P1_SET_SNAPSHOT_FILE_IDENTITY_ENUMERATION_EXHAUSTION_OBSERVATION_V1.json` | Additive persist of Owner-selected `SNAPSHOT_FILE_IDENTITY_ENUMERATION_EXHAUSTION_V1` plus P1_SET snapshot completeness/exhaustion proof (AUTHORITY=NONE; does not overwrite A-OBS-FSC-POLICY or A-PER-P1INV; 129 path identities not collapsed onto 125 SHA; scoped exclusion `docs&#47;forensics&#47;persistence&#47;` remains; live growth is not P1 membership; Census-48 remains unresolved historical assertion; global closed universe remains unproven; index entry is not global completeness proof; 70 was the count after the FSC-policy observation file) |
| `inventories&#47;P5_SET_SNAPSHOT_FILE_IDENTITY_ENUMERATION_EXHAUSTION_OBSERVATION_V1.json` | Additive persist of Owner-selected `P5_SNAPSHOT_FILE_IDENTITY_ENUMERATION_EXHAUSTION_V1` plus P5_SET snapshot completeness/exhaustion proof (AUTHORITY=NONE; does not overwrite A-OBS-FSC-POLICY, A-OBS-P1-EXH, A-PER-P5INV, or A-PER-XFACTS; 44 file_locator identities not collapsed onto 28 P5-only locators or 27 P5-only SHA; 42 full-P5 SHA is fingerprint not membership; BYTE_IDENTICAL P5/P1 relations remain dual identity; P2 remains unresolved not empty; live Documents tree is not P5 membership; Census-48 remains unresolved historical assertion; global closed universe remains unproven; index entry is not global completeness proof; 71 was the count after the P1 exhaustion observation file) |

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
PRE_OPTION_C_DECISION_WORKPACKAGE_PERSISTENCE_ARTIFACT_COUNT=44
POST_OPTION_C_DECISION_FILE_PERSISTENCE_ARTIFACT_COUNT=45
PRE_POST_PR6105_RANKING_WORKPACKAGE_PERSISTENCE_ARTIFACT_COUNT=45
POST_POST_PR6105_RANKING_FILE_PERSISTENCE_ARTIFACT_COUNT=46
PRE_THIS_WORKPACKAGE_PERSISTENCE_ARTIFACT_COUNT=46
POST_THIS_WORKPACKAGE_PERSISTENCE_ARTIFACT_COUNT=47
PRE_FEDERATED_ARCHITECTURE_WORKPACKAGE_PERSISTENCE_ARTIFACT_COUNT=47
POST_FEDERATED_ARCHITECTURE_WORKPACKAGE_PERSISTENCE_ARTIFACT_COUNT=50
PRE_FEDERATED_MAINTENANCE_CONTRACT_WORKPACKAGE_PERSISTENCE_ARTIFACT_COUNT=50
POST_FEDERATED_MAINTENANCE_CONTRACT_WORKPACKAGE_PERSISTENCE_ARTIFACT_COUNT=51
PRE_POST_PR6109_SYSTEM_FRONTIER_WORKPACKAGE_PERSISTENCE_ARTIFACT_COUNT=51
POST_POST_PR6109_SYSTEM_FRONTIER_FILE_PERSISTENCE_ARTIFACT_COUNT=52
PRE_EXISTING_EVIDENCE_RECONCILIATION_WORKPACKAGE_PERSISTENCE_ARTIFACT_COUNT=52
POST_EXISTING_EVIDENCE_RECONCILIATION_FILE_PERSISTENCE_ARTIFACT_COUNT=53
PRE_P3_CLASS_C_GET_WORKPACKAGE_PERSISTENCE_ARTIFACT_COUNT=53
POST_P3_CLASS_C_RAW_ENVELOPES_FILE_PERSISTENCE_ARTIFACT_COUNT=54
POST_P3_CLASS_C_GET_WORKPACKAGE_PERSISTENCE_ARTIFACT_COUNT=55
PRE_P3_CLASS_D_Z2AP_READINESS_WORKPACKAGE_PERSISTENCE_ARTIFACT_COUNT=55
POST_P3_CLASS_D_Z2AP_READINESS_RAW_ENVELOPES_FILE_PERSISTENCE_ARTIFACT_COUNT=56
POST_P3_CLASS_D_Z2AP_READINESS_WORKPACKAGE_PERSISTENCE_ARTIFACT_COUNT=57
PRE_P3_Z2CK_BLOCKER_ADJUDICATION_WORKPACKAGE_PERSISTENCE_ARTIFACT_COUNT=57
POST_P3_Z2CK_BLOCKER_ADJUDICATION_FILE_PERSISTENCE_ARTIFACT_COUNT=58
PRE_P3_Z2CL_CHOICE_B_TRANSPORT_WORKPACKAGE_PERSISTENCE_ARTIFACT_COUNT=58
POST_P3_Z2CL_CHOICE_B_TRANSPORT_FILE_PERSISTENCE_ARTIFACT_COUNT=59
PRE_P3_Z2CL_PREMERGE_AUDIT_FILE_PERSISTENCE_ARTIFACT_COUNT=59
POST_P3_Z2CL_PREMERGE_AUDIT_FILE_PERSISTENCE_ARTIFACT_COUNT=60
PRE_P3_Z2CL_PREMERGE_HARDENING_FILE_PERSISTENCE_ARTIFACT_COUNT=60
POST_P3_Z2CL_PREMERGE_HARDENING_FILE_PERSISTENCE_ARTIFACT_COUNT=61
PRE_P3_Z2CL_RT_PROOF_ADJUDICATION_FILE_PERSISTENCE_ARTIFACT_COUNT=61
POST_P3_Z2CL_RT_PROOF_ADJUDICATION_FILE_PERSISTENCE_ARTIFACT_COUNT=62
PRE_P3_Z2CL_OFFLINE_SEM_FILE_PERSISTENCE_ARTIFACT_COUNT=62
POST_P3_Z2CL_OFFLINE_SEM_FILE_PERSISTENCE_ARTIFACT_COUNT=63
PRE_P3_Z2CL_UNIVERSE_RECON_FILE_PERSISTENCE_ARTIFACT_COUNT=63
POST_P3_Z2CL_UNIVERSE_RECON_FILE_PERSISTENCE_ARTIFACT_COUNT=64
PRE_P3_Z2CL_IDENTITY_HEADER_GAP_FILE_PERSISTENCE_ARTIFACT_COUNT=64
POST_P3_Z2CL_IDENTITY_HEADER_GAP_FILE_PERSISTENCE_ARTIFACT_COUNT=65
PRE_P3_Z2CL_SCHEMA_NC_CENSUS_LINEAGE_FILE_PERSISTENCE_ARTIFACT_COUNT=65
POST_P3_Z2CL_SCHEMA_NC_CENSUS_LINEAGE_FILE_PERSISTENCE_ARTIFACT_COUNT=66
PRE_P3_Z2CL_COMPLETENESS_PRECONDITION_GAPS_FILE_PERSISTENCE_ARTIFACT_COUNT=66
POST_P3_Z2CL_COMPLETENESS_PRECONDITION_GAPS_FILE_PERSISTENCE_ARTIFACT_COUNT=67
PRE_P3_Z2CL_OD_01_08_RECONSTRUCTION_DELTA_FILE_PERSISTENCE_ARTIFACT_COUNT=67
POST_P3_Z2CL_OD_01_08_RECONSTRUCTION_DELTA_FILE_PERSISTENCE_ARTIFACT_COUNT=68
PRE_FEDERATED_SCOPED_COMPLETENESS_POLICY_WORKPACKAGE_PERSISTENCE_ARTIFACT_COUNT=68
POST_FORENSIC_COMPLETENESS_SCOPING_CONTRACT_FILE_PERSISTENCE_ARTIFACT_COUNT=69
POST_FEDERATED_SCOPED_COMPLETENESS_POLICY_OWNER_DECISION_FILE_PERSISTENCE_ARTIFACT_COUNT=70
COUNT_39_IS_PRE_CLASS_A_SNAPSHOT_NOT_CURRENT=true
COUNT_40_IS_INTERMEDIATE_AFTER_CLASS_A_FILE_NOT_COLLAPSED_ONTO_41=true
COUNT_41_IS_PRE_CENSUS_WORKPACKAGE_SNAPSHOT_NOT_POST_CENSUS_CURRENT=true
COUNT_42_IS_INTERMEDIATE_AFTER_RAW_ENVELOPES_FILE_NOT_COLLAPSED_ONTO_43=true
COUNT_43_IS_POST_CENSUS_FILE_NOT_COLLAPSED_ONTO_44=true
COUNT_44_IS_POST_BINDING_ADJUDICATION_FILE_NOT_COLLAPSED_ONTO_45=true
COUNT_45_IS_POST_OPTION_C_FILE_NOT_COLLAPSED_ONTO_46=true
COUNT_46_IS_POST_PR6106_RANKING_FILE_NOT_COLLAPSED_ONTO_47=true
COUNT_47_IS_POST_PR6106_CLOSABILITY_FILE_NOT_COLLAPSED_ONTO_50=true
COUNT_50_IS_POST_FEDERATED_ARCHITECTURE_NOT_COLLAPSED_ONTO_51=true
COUNT_51_IS_POST_PR6109_MAINTENANCE_CONTRACT_NOT_COLLAPSED_ONTO_52=true
COUNT_52_IS_POST_PR6109_SYSTEM_FRONTIER_NOT_COLLAPSED_ONTO_53=true
COUNT_53_IS_POST_RECONCILIATION_NOT_COLLAPSED_ONTO_54=true
COUNT_54_IS_INTERMEDIATE_AFTER_P3_CLASS_C_RAW_ENVELOPES_NOT_COLLAPSED_ONTO_55=true
COUNT_55_IS_POST_CLASS_C_NOT_COLLAPSED_ONTO_56=true
COUNT_56_IS_INTERMEDIATE_AFTER_P3_CLASS_D_RAW_ENVELOPES_NOT_COLLAPSED_ONTO_57=true
COUNT_57_IS_POST_CLASS_D_NOT_COLLAPSED_ONTO_58=true
COUNT_58_IS_POST_Z2CK_BLOCKER_NOT_COLLAPSED_ONTO_59=true
COUNT_59_IS_POST_Z2CL_IMPLEMENTATION_NOT_COLLAPSED_ONTO_60=true
COUNT_60_IS_POST_Z2CL_PREMERGE_AUDIT_NOT_COLLAPSED_ONTO_61=true
COUNT_61_IS_POST_Z2CL_PREMERGE_HARDENING_NOT_COLLAPSED_ONTO_62=true
COUNT_62_IS_POST_Z2CL_RT_PROOF_NOT_COLLAPSED_ONTO_63=true
COUNT_63_IS_POST_Z2CL_OFFLINE_SEM_NOT_COLLAPSED_ONTO_64=true
COUNT_64_IS_POST_Z2CL_UNIVERSE_RECON_NOT_COLLAPSED_ONTO_65=true
COUNT_65_IS_POST_Z2CL_IDENTITY_HEADER_GAP_NOT_COLLAPSED_ONTO_66=true
COUNT_66_IS_POST_Z2CL_SCHEMA_NC_CENSUS_LINEAGE_NOT_COLLAPSED_ONTO_67=true
COUNT_67_IS_POST_Z2CL_COMPLETENESS_PRECONDITION_GAPS_NOT_COLLAPSED_ONTO_68=true
COUNT_68_IS_POST_Z2CL_OD_01_08_RECONSTRUCTION_DELTA_NOT_COLLAPSED_ONTO_69=true
COUNT_69_IS_INTERMEDIATE_AFTER_SCOPING_CONTRACT_NOT_COLLAPSED_ONTO_70=true
COUNT_70_IS_POST_FSC_POLICY_OBSERVATION_NOT_COLLAPSED_ONTO_71=true
COUNT_36_AND_37_AND_38_AND_39_AND_40_AND_41_AND_42_AND_43_AND_44_AND_45_AND_46_AND_47_AND_50_AND_51_AND_52_AND_53_AND_54_AND_55_AND_56_AND_57_AND_58_AND_59_AND_60_AND_61_AND_62_AND_63_AND_64_AND_65_AND_66_AND_67_AND_68_AND_69_AND_70_AND_71_NOT_COLLAPSED=true
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
