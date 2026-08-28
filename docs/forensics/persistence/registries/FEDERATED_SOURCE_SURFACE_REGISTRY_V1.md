# FEDERATED_SOURCE_SURFACE_REGISTRY_V1

```text
DOCUMENT_CLASS=NON_AUTHORITATIVE_FEDERATED_SOURCE_SURFACE_REGISTRY
DOCUMENT_ROLE=L0_SOURCE_SURFACE_REGISTRY
LAYER=L0
AUTHORITY=NONE
TARGET_AUTHORITY=NONE
NAVIGATION_ONLY=true
SECOND_SSOT=false
SEMANTIC_AUTHORITY=false
CANONICAL=false
RUNTIME_AUTHORIZATION_EFFECT=NONE
INDEX_ENTRY_IS_NOT_ADJUDICATION=true
INDEX_ENTRY_IS_NOT_COMPLETENESS_PROOF=true
THIS_REGISTRY_IS_NOT_CANONICAL_AUTHORITY=true
THIS_REGISTRY_MUST_NOT_OVERRIDE_MASTER_RUNBOOK=true
THIS_REGISTRY_MUST_NOT_OVERRIDE_MAP_OF_TRUTH=true
THIS_REGISTRY_MUST_NOT_MERGE_SOURCE_IDENTITIES=true
THIS_REGISTRY_MUST_NOT_ASSIGN_ALTERNATIVE_P2_PATH=true
COPY_OF_EXTERNAL_CORPUS_PERFORMED=false
GLOBAL_SOURCE_UNIVERSE_EXHAUSTION_PROVEN=false
KNOWN_SOURCE_SURFACES_ENUMERATED=true
P2_UNRESOLVED_IS_NOT_P2_EMPTY=true
P2_EMPTY_INFERRED_FROM_UNRESOLVED_PATH=false
SOURCE_IDENTITY_COLLAPSED=false
NEW_DOMAIN_ONTOLOGY_CREATED=false
OWNER_GO=PEAK_TRADE_FEDERATED_FORENSIC_INFORMATION_ARCHITECTURE_L0_L2_L4_MATERIALIZATION_PERSIST_WORKPACKAGE_V1
bound_origin_main_sha=fc666414c3a12e5b98f0ea57131e4006fe4af9e6
```

Purpose: durable federated index of **known** information surfaces so a
later forensic agent can start from one repo-internal locator without
rediscovering all corpora.

This is not a universe census. Surfaces not listed here are not proven
absent.

## Reuse adjudication

```text
CAN_EXISTING_ARTIFACT_BE_EXTENDED_LOSSLESSLY=false
EXISTING_CANDIDATE=docs/forensics/persistence/registries/EXTERNAL_FORENSIC_CORPUS_DISCOVERY_V1.md
EXISTING_CANDIDATE_DOCUMENT_CLASS=NON_AUTHORITATIVE_DISCOVERY_REGISTRY
EXISTING_CANDIDATE_SCOPE=P2_OWNER_NAMED_CORPUS_PLUS_P1_P5_DISCOVERY_CLOSEOUT
LOSSLESS_EXTENSION_BLOCKED_BECAUSE=external-corpus-only contract cannot represent SS-01 canonical SSOT, SS-02 navigation, SS-03 persistence, SS-11 git history, SS-12 live transcripts, or SS-14 historical absent locators without misusing P2/P5 provenance classes
PARALLEL_REGISTRY_CREATION_FORBIDDEN_SEMANTIC=this file is the missing L0 federated index; it does not replace P2/P5 discovery
REUSED_WITHOUT_REWRITE=docs/forensics/persistence/registries/EXTERNAL_FORENSIC_CORPUS_DISCOVERY_V1.md
REUSED_WITHOUT_REWRITE_ALSO=docs/forensics/persistence/inventories/P1_REPO_FORENSIC_TREES_FILE_INVENTORY_V1.json
REUSED_WITHOUT_REWRITE_ALSO_2=docs/forensics/persistence/inventories/P5_DOCUMENTS_PEAK_TRADE_FORENSICS_FILE_INVENTORY_V1.json
HISTORICAL_OBSERVATION_REWRITE_COUNT=0
```

L1 inventories remain the file-identity owners. This registry points at
them. It does not copy their records.

Companion layers:

- L2 [`INFORMATION_OBJECT_REFERENCE_REGISTRY_V1.md`](INFORMATION_OBJECT_REFERENCE_REGISTRY_V1.md)
- L4 [`CURRENT_STATE_PROJECTION_V1.md`](CURRENT_STATE_PROJECTION_V1.md)
- Bootstrap [`../PEAK_TRADE_INFORMATION_CORPUS_PERSISTENCE_BASE.md`](../PEAK_TRADE_INFORMATION_CORPUS_PERSISTENCE_BASE.md)

## Guards

```text
KNOWN_SOURCE_SURFACES_ENUMERATED=true
KNOWN_SOURCE_SURFACE_COUNT=14
KNOWN_SOURCE_SURFACE_COUNT_SEMANTIC=enumerated_required_surfaces_SS-01_through_SS-14_from_prior_architecture_report;_not_a_closed_global_universe
GLOBAL_SOURCE_UNIVERSE_EXHAUSTION_PROVEN=false
5185_EQUALS_5189_EQUALS_5190=false
5185_EQUALS_5227=false
P2_CONTENT_INVENTORY_STATUS=NOT_PERFORMABLE_WITHOUT_RESOLVED_CORPUS
SS-10_REMAINS_UNRESOLVED=true
SS-10_CONVERTED_TO_EMPTY_OR_ABSENT=false
BYTE_IDENTICAL_DOES_NOT_MERGE_SOURCE_IDENTITY=true
```

## Source surfaces

| SOURCE_SURFACE_ID | SOURCE_CLASS | ROOT_OR_LOCATOR | AUTHORITY_STATUS | PROVENANCE_STATUS | TEMPORAL_ROLE | IDENTITY_RULE | DISCOVERY_STATUS | COMPLETENESS_STATUS |
|---|---|---|---|---|---|---|---|---|
| SS-01 | CANONICAL_AUTHORITY | [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../../../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) | SOLE_CANONICAL_SSOT | REPO_INTERNAL_CURRENT | CURRENT_FOR_FINISH_SEQUENCE | PATH+GIT_SHA | POINTER_READ_THIS_PERSIST | UNPROVEN |
| SS-02 | NAVIGATION_ONLY | [`docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md`](../../../governance/PEAK_TRADE_MAP_OF_TRUTH.md) | NONE | REPO_INTERNAL_CURRENT | CURRENT_FOR_NAVIGATION | PATH+GIT_SHA | POINTER_READ_THIS_PERSIST | NOT_A_UNIVERSE |
| SS-03 | REPO_FORENSIC_PERSISTENCE | [`docs/forensics/persistence/`](../PEAK_TRADE_INFORMATION_CORPUS_PERSISTENCE_BASE.md) | NONE | REPO_INTERNAL | CURRENT_FOR_FORENSIC_INDEX | PATH+GIT_SHA; index≠adjudication | TREE_ENUMERATED_ON_ORIGIN_MAIN | UNPROVEN |
| SS-04 | REPO_FORENSIC_NON_PERSISTENCE | `docs&#47;forensics&#47;` minus `persistence&#47;` | NONE | REPO_INTERNAL | MIXED_CURRENT_PRESERVATION | PATH+SHA | ENUMERATED_IN_P1_PLUS_LIVE_TREE | UNPROVEN |
| SS-05 | REPO_FORENSIC_NON_PERSISTENCE | `docs&#47;forensic&#47;` | NONE | REPO_INTERNAL | CURRENT_FOR_FSS_NOTES | PATH | ENUMERATED_4 | UNPROVEN |
| SS-06 | REPO_FORENSIC_NON_PERSISTENCE | `forensics&#47;` | NONE | REPO_INTERNAL | CURRENT_FOR_FSS_DERIVED_REPORTS | PATH+SHA | P1_SNAPSHOT_74_REPORTS_IN_GIT | UNPROVEN |
| SS-07 | REPO_FORENSIC_NON_PERSISTENCE | `forensic&#47;` | NONE | REPO_INTERNAL | MIXED_HISTORICAL_PRESERVATION | PATH+SHA | P1_SNAPSHOT_PLUS_LIVE_GROWTH | UNPROVEN |
| SS-08 | EXTERNAL_FORENSIC_WORKING_MATERIAL | `/Users&#47;frnkhrz&#47;Documents&#47;Peak_Trade&#47;forensics` | NONE | LOCAL_EXTERNAL; P5 not P2 | CURRENT_FOR_BOUND_WORKING_MD | ABSOLUTE_PATH+SHA; not repo identity | REGISTERED_IN_P5_INVENTORY | UNPROVEN |
| SS-09 | EXTERNAL_DERIVED_FORENSIC_MATERIAL | P5 `derived&#47;` plus P5 `tools&#47;` | NONE | LOCAL_EXTERNAL derived from SS-08 | DERIVED_FROM_SS-08 | PATH+SHA | INCLUDED_IN_P5_INVENTORY | UNPROVEN |
| SS-10 | UNRESOLVED_OWNER_NAMED_CORPUS | Owner-named folder `Peak Trade Forensik` | NONE | P2 NOT_UNIQUELY_RESOLVED | UNKNOWN | MUST_NOT_ASSIGN_ALTERNATIVE | NAME_MATCH_0_UNDER_DOCUMENTS | UNKNOWN |
| SS-11 | GIT_HISTORY | local `.git` / `origin&#47;main` | EVIDENCE_NOT_DOMAIN_AUTHORITY | GIT_OBJECT_STORE | HISTORICAL+CURRENT_SHAS | COMMIT_SHA+TREE | USED_FOR_BINDING_SHA | UNPROVEN |
| SS-12 | AGENT_TRANSCRIPT_EVIDENCE | `~&#47;.cursor&#47;projects&#47;Users-frnkhrz-Peak-Trade&#47;agent-transcripts` | NONE | CHAT_SURFACE | LIVE_GLOB_NOT_EQUAL_HISTORICAL_5185 | PATH+JSONL; not SSOT | LOCATOR_PROVEN_IN_DISCOVERY_REGISTRY | UNPROVEN |
| SS-13 | REPO_PRESERVATION_TRANSCRIPT_SUBSET | [`90a346c4-5419-436a-9d7f-e2a893c4aad5.jsonl`](../../../../forensic/p6_proven_relevant_jsonl_identity_copies_v1/evidence/raw_verbatim_identity_copies_authority_none/transcripts/90a346c4-5419-436a-9d7f-e2a893c4aad5.jsonl) (tree `forensic&#47;p6_proven_relevant_jsonl_identity_copies_v1&#47;`, 170 git files) | NONE | REPO_PRESERVATION_SUBSET | HISTORICAL_RELEVANT_SUBSET | PATH+SHA copies | IDENTITY_COPIES_PRESENT | UNPROVEN |
| SS-14 | HISTORICAL_LOCATOR_ABSENT | Desktop originals named in [`forensic/post_step32_knowledge_integration_v0/manifests/source_identities.json`](../../../../forensic/post_step32_knowledge_integration_v0/manifests/source_identities.json) | NONE | HISTORICAL_LOCATOR | HISTORICAL | PATH_RECORDED_ABSENT_NOT_REASSIGNED | PROBED_ABSENT_IN_DISCOVERY_REGISTRY | N/A |

## Surface notes (evidence-supported only)

### SS-01 CANONICAL_AUTHORITY

Sole canonical SSOT. Forensic registries must not override it.
Current finish-sequence persist cited by L4: §11.13.5.Z2CI.
`LIVE_AUTHORIZED=false` remains a canonical fail-closed gate, not a
forensic promotion.

### SS-02 NAVIGATION_ONLY

Map of Truth defines no semantics. It points at canonical owners.

### SS-03 REPO_FORENSIC_PERSISTENCE

Owner of this federated architecture. File identities live in git.
Index entry is not adjudication. Count contracts in the Persistence
Base remain uncollapsed.

### SS-04 through SS-07 REPO_FORENSIC_NON_PERSISTENCE

Hashed P1 snapshot
([`../inventories/P1_REPO_FORENSIC_TREES_FILE_INVENTORY_V1.json`](../inventories/P1_REPO_FORENSIC_TREES_FILE_INVENTORY_V1.json))
is a discovery-pass snapshot, not a live census, and does not include
the persistence tree. Live tree growth must not collapse onto the
hashed 129-file count.

SS-04 includes SW_R_002 preservation, binding, post-handoff delta, and
working-state synthesis under `docs&#47;forensics&#47;`.

SS-05 is FSS-V1 implementation notes (4 markdown files).

SS-06 holds FSS-V1 derived reports in git; blob bodies are P5-only
(SS-09).

SS-07 includes the lossless working-runbook identity copy and the
R3 transcript identity copy under SS-13's parent `forensic&#47;` tree.
SS-13 is the transcript-subset identity, not a merge of SS-07.

### SS-08 / SS-09 external forensic material

Evidence-bound P5 root, not the Owner-named Forensik folder.
Inventory owner:
[`../inventories/P5_DOCUMENTS_PEAK_TRADE_FORENSICS_FILE_INVENTORY_V1.json`](../inventories/P5_DOCUMENTS_PEAK_TRADE_FORENSICS_FILE_INVENTORY_V1.json)

Large bodies are referenced by locator+hash only. This persist does
not copy them.

Discovery narrative remains:
[`EXTERNAL_FORENSIC_CORPUS_DISCOVERY_V1.md`](EXTERNAL_FORENSIC_CORPUS_DISCOVERY_V1.md)

### SS-10 UNRESOLVED_OWNER_NAMED_CORPUS

```text
EXTERNAL_FORENSIC_CORPUS_STATUS=NOT_UNIQUELY_RESOLVED
EXTERNAL_FORENSIC_CORPUS_RESOLVED_PATH=
P2_CONTENT_INVENTORY_STATUS=NOT_PERFORMABLE_WITHOUT_RESOLVED_CORPUS
P2_FILE_COUNT=UNKNOWN
ALTERNATIVE_DIRECTORY_ASSIGNED=false
P2_EMPTY_INFERRED_FROM_UNRESOLVED_PATH=false
P2_CORPUS_ABSENT=false
```

Unresolved is not empty and not absent. P5 must not be substituted.

### SS-11 GIT_HISTORY

Provenance for SHAs and tree membership. Not domain authority.

### SS-12 / SS-13 transcript surfaces

SS-12 is the live chat glob. SS-13 is a governed identity-copy subset
in git. Count contracts 5185 / 5189 / 5190 / 5227 remain uncollapsed.
P6_5189 relation graph is a different object (see L2 `IO-P6GRAPH`).

### SS-14 HISTORICAL_LOCATOR_ABSENT

Desktop originals recorded in post_step32 `source_identities.json`
were probed absent in
[`EXTERNAL_FORENSIC_CORPUS_DISCOVERY_V1.md`](EXTERNAL_FORENSIC_CORPUS_DISCOVERY_V1.md).
They were not reassigned to P5. Repo identity copies under
`forensic&#47;post_step32_knowledge_integration_v0&#47;` are a different
source identity.

## Where to look next

| Question | Next locator |
|----------|----------------|
| Which stable subject does a surface support? | [`INFORMATION_OBJECT_REFERENCE_REGISTRY_V1.md`](INFORMATION_OBJECT_REFERENCE_REGISTRY_V1.md) |
| What is the current known state of a subject? | [`CURRENT_STATE_PROJECTION_V1.md`](CURRENT_STATE_PROJECTION_V1.md) |
| P2/P5 discovery narrative | [`EXTERNAL_FORENSIC_CORPUS_DISCOVERY_V1.md`](EXTERNAL_FORENSIC_CORPUS_DISCOVERY_V1.md) |
| P5↔repo byte identity | [`CROSS_CORPUS_RELATION_REGISTER_V1.md`](CROSS_CORPUS_RELATION_REGISTER_V1.md) |
| P6_5189 edges | [`P6_5189_RELATION_LEDGER_V1.json`](P6_5189_RELATION_LEDGER_V1.json) |
