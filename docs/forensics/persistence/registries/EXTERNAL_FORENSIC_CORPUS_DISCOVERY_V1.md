# EXTERNAL_FORENSIC_CORPUS_DISCOVERY_V1

```text
DOCUMENT_CLASS=NON_AUTHORITATIVE_DISCOVERY_REGISTRY
AUTHORITY=NONE
TARGET_AUTHORITY=NONE
SECOND_SSOT=false
RUNTIME_AUTHORIZATION_EFFECT=NONE
OWNER_GO_TOKEN=EXTERNAL_FORENSIC_CORPUS_DISCOVERY_AUTHORIZED
OWNER_GO_VALUE=true
OWNER_GO_REPAIR=FORENSIC_FRAGMENT_CORPUS_PERSISTENCE_BOOTSTRAP_REPRESENTATION_REPAIR_ONLY
P2_UNRESOLVED_IS_NOT_P2_EMPTY=true
FILE_MUTATION_OF_EXTERNAL_CORPUS=false
SEMANTIC_CLASSIFICATION_PERFORMED_IN=MAIN_AGENT
SHELL_USED_FOR=PATH_RESOLUTION_INVENTORY_TYPE_SIZE_HASH_COUNTS_ONLY
```

## 0. Baseline at write

```text
BASELINE_VALIDATION=PASS_FOR_AUTHORIZED_ORTHOGONAL_FORENSIC_DISCOVERY
CURRENT_ORIGIN_MAIN_SHA=ede502f5c72be3e55f375f50a3bb70187c8e5a87
HEAD_SHA=c2ac084d9a442dce243396f04de06557268bb5cd
HEAD_WORKING_STATE_FILE_DIFF_VS_ORIGIN_MAIN_BYTES=0
WORKING_MODEL_DRIFT=NONE
MASTER_RUNBOOK_STATUS=CANONICAL_WORKING_AUTHORITY
MAP_OF_TRUTH_STATUS=NAVIGATION_ONLY_NO_SEMANTICS
CANONICAL_CURRENT_PHASE=11.13.5.Z2CF_POST_Z2CE_POST_6058_NORMAL_SYSTEM_NEXT_POINTER_ADJUDICATION_PERSIST
LAST_CANONICALLY_CLOSED_NORMAL_STEP=SECTION_11_13_5_Z2CE
EARLIEST_UNRESOLVED_DEPENDENCY=GLOBAL_UNIQUE_CANONICAL_NEXT_STEP=NONE_BY_P3_POLICY
P7_3_RESIDUAL=UNRESOLVED_FAIL_CLOSED
REQUESTED_STEP=EXTERNAL_FORENSIC_CORPUS_DISCOVERY_AND_PROVENANCE_REGISTRATION
REQUEST_MATCHES_CANONICAL_NEXT_STEP=false
AUTHORIZATION_REQUIRED=true
AUTHORIZATION_PRESENT=EXTERNAL_FORENSIC_CORPUS_DISCOVERY_AUTHORIZED=true
EXECUTION_SURFACE_TOUCHED=REPO_DOCS_FORENSICS_PERSISTENCE_ONLY
HARD_STOP_REASONS=NONE_FOR_AUTHORIZED_ORTHOGONAL_DISCOVERY
PROPOSED_SAFE_ACTION=REGISTER_P2_NOT_UNIQUELY_RESOLVED_AND_SEPARATE_P5_EVIDENCE_BOUND_INVENTORY
LIVE_AUTHORIZED=false
TESTNET_AUTHORIZED=false
```

SW-R-002 remains off the canonical finish sequence. This registry does
not place it onto that sequence.

## 1. P2 — Owner-named folder "Peak Trade Forensik"

### Resolution procedure (deterministic)

1. `HOME=&#47;Users&#47;frnkhrz`
2. Exact top-level directory named `Documents` under HOME: count=1,
   path=`/Users/frnkhrz/Documents`
3. Recursive walk of that Documents tree for directory basename exactly
   `Peak Trade Forensik`
4. Casefold match for the same literal
5. Spotlight `mdfind` exact FSName and DisplayName, scoped to Documents
   and to HOME

Discovery observations below count directory-name matches under the
resolved Documents root. They are not a P2 content inventory.

```text
EXTERNAL_FORENSIC_CORPUS_STATUS=NOT_UNIQUELY_RESOLVED
EXTERNAL_FORENSIC_CORPUS_RESOLVED_PATH=
EXTERNAL_FORENSIC_CORPUS_ACCESS_MODE=NOT_APPLICABLE
EXTERNAL_FORENSIC_CORPUS_MUTATED=false
DOCUMENTS_ROOT_RESOLVED=/Users/frnkhrz/Documents
DOCUMENTS_ROOT_EXACT_COUNT=1
OWNER_NAMED_FOLDER_LITERAL_MATCH_COUNT_UNDER_DOCUMENTS=0
OWNER_NAMED_FOLDER_FORENSIK_NAME_MATCH_COUNT_UNDER_DOCUMENTS=0
EXACT_BASENAME_HIT_COUNT=0
CASEFOLD_HIT_COUNT=0
SPOTLIGHT_HIT_COUNT=0
CONTAINS_GERMAN_FORENSIK_DIRNAME_COUNT=0
ALTERNATIVE_DIRECTORY_ASSIGNED=false
```

No alternative directory was assigned as the Owner-named corpus.

Name-match count zero does not mean the unresolved P2 corpus is empty.
P2 contents remain UNKNOWN / NOT_ASSESSABLE until a unique path exists.

### Near-misses recorded, not assigned

These exist under Documents. They are **not** the Owner literal
`Peak Trade Forensik`.

| Path | Why recorded | Assigned as P2 |
|------|----------------|----------------|
| `/Users/frnkhrz/Documents/Peak_Trade` | top-level Peak_Trade under Documents | false |
| `/Users/frnkhrz/Documents/Peak_Trade/forensics` | evidence-bound in SW-R-002 preservation binding; basename `forensics` | false |
| `/Users/frnkhrz/Documents/Peak_Trade_forensic_workspace_preserve_20260814T205447Z` | name contains Peak_Trade and forensic | false |
| other `Peak_Trade_*` archive/evidence folders under Documents | Peak_Trade-related local archives | false |

```text
P2_CONTENT_INVENTORY_STATUS=NOT_PERFORMABLE_WITHOUT_RESOLVED_CORPUS
P2_FILE_COUNT=UNKNOWN
P2_RELEVANT_SOURCE_COUNT=UNKNOWN
P2_SOURCES_REGISTERED_COUNT=UNKNOWN
P2_READ_ONLY_OUTPUT_STATUS=UNKNOWN
P2_MULTI_REVIEW_BUNDLE_STATUS=UNKNOWN
P2_SYNTHESIS_ARTIFACT_STATUS=UNKNOWN
P2_HISTORICAL_VARIANT_STATUS=UNKNOWN
P2_CROSS_CORPUS_RELATION_STATUS=UNKNOWN
P2_EMPTY_INFERRED_FROM_UNRESOLVED_PATH=false
```

## 2. P1 — repo-internal forensic information fragments

Hashed trees (file identity only):

```text
docs/forensics          files=5   bytes=248403
docs/forensic           files=4   bytes=12243
forensic/               files=46  bytes=9539742
forensics/              files=74  bytes=12718493
HASHED_P1_FORENSIC_TREE_FILE_COUNT=129
HASHED_P1_FORENSIC_TREE_BYTE_SUM=22518881
```

Additional P1 trees listed by glob, not re-hashed this pass:

```text
tests/forensic_structure_schema_v1          files=16
scripts/ops/forensic_structure_schema_v1    files=48
```

Machine inventory:
`docs/forensics/persistence/inventories/P1_REPO_FORENSIC_TREES_FILE_INVENTORY_V1.json`

### Semantic classes observed in P1 (main-agent classification)

| Class | Repo locators | Notes |
|-------|----------------|-------|
| Canonical SSOT | `docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md` | not a forensic tree file; canonical authority |
| Navigation index | `docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md` | no semantics |
| SW-R-002 preservation | `docs/forensics/preservation/PEAK_TRADE_SW_R_002_FORENSIC_DECISION_SURFACE_PRESERVATION.md` | 22 primitives; AUTHORITY=NONE |
| SW-R-002 preservation binding | `docs/forensics/preservation/PEAK_TRADE_SW_R_002_FORENSIC_DECISION_SURFACE_PRESERVATION_BINDING.md` | identity metadata |
| Post-handoff read-only analysis delta | `docs/forensics/preservation/PEAK_TRADE_SW_R_002_POST_HANDOFF_READ_ONLY_ANALYSIS_PRESERVATION_DELTA.md` | 47 findings; does not answer owner decisions |
| Working-state synthesis | `docs/forensics/working_state/PEAK_TRADE_SW_R_002_WORKING_STATE.md` | non-authoritative join |
| Multi-step knowledge bundle | `forensic/post_step32_knowledge_integration_v0/` | P4 in-repo |
| Lossless V2/V2.1 pack | `forensic/lossless_structural_projection_v2_v2_1_pack_v1/` | identity copy of older working-runbook SHA `10d92931…` |
| Schema V1 derived layers | `forensics&#47;derived&#47;FORENSIC_STRUCTURE_SCHEMA_V1_*` | reports in git; large blobs not in git |
| Schema V1 implementation notes | `docs&#47;forensic&#47;*.md` | AUTHORITY=NONE |

## 3. P5 — evidence-bound local path, not P2

Repo evidence already names this path. This pass opened it read-only
because P5 permits evidence-backed local Peak_Trade outputs. It is
**not** the unresolved Owner-named folder.

```text
SOURCE_CLASS=LOCAL_EXTERNAL_FORENSIC_SOURCE
SOURCE_CORPUS=DOCUMENTS_PEAK_TRADE_FORENSICS_EVIDENCE_BOUND_P5_NOT_OWNER_NAMED_FORENSIK_FOLDER
P5_PATH=/Users/frnkhrz/Documents/Peak_Trade/forensics
P5_ACCESS_MODE=READ_ONLY
P5_MUTATED=false
P5_FILES=44
P5_BYTE_SUM=360050066
P5_ONLY_UNIQUE_SHA_COUNT=27
P5_ONLY_FILE_LOCATOR_COUNT=28
P5_ONLY_BY_SHA_BYTES=359674333
P5_SHARED_SHA_FILE_RECORDS=16
P5_VS_REPO_BYTE_IDENTICAL_SHA_RECORDS=15
P5_ONLY_UNIQUE_SHA_COUNT_IS_NOT_FILE_LOCATOR_COUNT=true
SOURCE_IDENTITY_MERGED=false
```

Evidence that this path is attested in-repo (not invented this pass):

- `docs/forensics/preservation/PEAK_TRADE_SW_R_002_FORENSIC_DECISION_SURFACE_PRESERVATION_BINDING.md`
  `ORIGINAL_LOCAL_SOURCE_PATH` / `FORENSIC_MD_PATH`
- `docs/forensics/working_state/PEAK_TRADE_SW_R_002_WORKING_STATE.md`
  records `FORENSIC_MD_PATH` and SHA `a5a468f7…`

Machine inventory:
`docs/forensics/persistence/inventories/P5_DOCUMENTS_PEAK_TRADE_FORENSICS_FILE_INVENTORY_V1.json`

### P5 file classes (main-agent classification)

**A. Bound current forensic working runbook (not in git as this SHA)**

```text
PATH=/Users/frnkhrz/Documents/Peak_Trade/forensics/PEAK_TRADE_TEMPORARY_FORENSIC_WORKING_RUNBOOK.md
SHA256=a5a468f761e24e17fc0402dbf056df7d45090b3c58f0e9a2ad469569e908e212
BYTES=8639369
LINES=121930
```

Second P5 file locator with the same payload SHA (not a merged source
identity):

```text
PATH=/Users/frnkhrz/Documents/Peak_Trade/forensics/derived/sha256-a5a468f761e24e17fc0402dbf056df7d45090b3c58f0e9a2ad469569e908e212/source.snapshot.md
SHA256=a5a468f761e24e17fc0402dbf056df7d45090b3c58f0e9a2ad469569e908e212
BYTES=8639369
SOURCE_IDENTITY_MERGED=false
BYTE_IDENTICAL_WITH_WORKING_RUNBOOK_LOCATOR=true
```

**B. Historical / overlapping repo identity copy (different SHA)**

Repo pack copy:

```text
PATH=forensic/lossless_structural_projection_v2_v2_1_pack_v1/evidence/raw_verbatim_identity_copies_authority_none/PEAK_TRADE_TEMPORARY_FORENSIC_WORKING_RUNBOOK.md
SHA256=10d9293134426805f38996be848e1de853636d8e6f60745a2330bdfd94e3719f
BYTES=8499032
LINES=118809
PACK_MANIFEST_ORIGINAL_PATH=/Users/frnkhrz/Downloads/PEAK_TRADE_TEMPORARY_FORENSIC_WORKING_RUNBOOK.md
```

Same document header observed at start of both files.
Not BYTE_IDENTICAL.
Relation: `CONTENT_OVERLAP_PROVEN` plus `HISTORICAL_VARIANT`.
P5 file has 3121 additional lines / 140337 additional bytes.
mtime is not used as semantic currency.
The SW-R-002 binding already binds SHA `a5a468f7…` as the forensic-MD
identity.

**C. SW-R-002 preservation MD**

```text
P5_AND_REPO_SHA256=f26f6ec751b35fe95da1414fd2e7ed78ad419efd707d540210e899e6dfe39b3f
RELATION=BYTE_IDENTICAL
SOURCE_IDENTITY_MERGED=false
```

**D. Sidecar / T4 loss register bound by SHA in the preservation binding,
not present as git files**

```text
SIDECAR_SHA256=6f2928e67d45de2162df1589de77ea530061652181ba6efd9a0f528ca7e6ad6e
SIDECAR_P5_PATH=derived/PEAK_TRADE_TEMPORARY_FORENSIC_WORKING_RUNBOOK.structure-v1.json
T4_LOSS_REGISTER_SHA256=872e1e22fc3e46d8eb3b2975183ca6ce20d1c31fae9992ffd7b863b30db39113
T4_LOSS_REGISTER_P5_PATH=derived/PEAK_TRADE_TEMPORARY_FORENSIC_WORKING_RUNBOOK.t4-unprojected-relation-loss-register-v1.jsonl
```

**E. Lossless struct transform derived pack (P5-only bodies)**

`derived&#47;sha256-a5a468f7…&#47;` including `records.jsonl`, `quarantine.jsonl`,
validation reports, and `structural-v1-20260825T100541Z&#47;` sidecar.
Manifest declares `no_loss_proof=PASS` and reconstructed SHA equal to
source SHA. That is P5-local derived evidence, not canonical authority.

**F. Schema V1 transformation reports BYTE_IDENTICAL with repo;
blobs P5-only**

Reports under
`derived&#47;FORENSIC_STRUCTURE_SCHEMA_V1_TRANSFORMATION_V1&#47;` match git.
Blob files (`semantic_envelopes.json`, `layer1_occurrences.json`,
`traceability_records.json`, `overlay_index.json`,
`provenance_registry.json`, `relation_envelopes.json`,
`dataset_header.json`) are P5-only.

Alignment-index blob
`derived&#47;FORENSIC_STRUCTURE_SCHEMA_V1_BINDING_CANDIDATE_ALIGNMENT_INDEX_V1&#47;blobs&#47;t4_overlay_records.json`
is P5-only.

**G. Local forensic tools (P5-only)**

```text
tools/pt_forensic_lossless_struct_v1.py
tools/pt_forensic_structural_sidecar_v1.py
tools/probe_fence_counts_v1.py
```

Hard-coded to the P5 working-runbook path and SHA `a5a468f7…`.
Not copied into this persistence base.

## 4. P3 — already persisted forensic / preservation / analysis results

In-repo (selected):

- SW-R-002 preservation + binding
- post-handoff analysis delta + binding
- `forensics&#47;derived&#47;*` schema-V1 layers
- `forensic/post_step32_knowledge_integration_v0/`
- `forensic&#47;lossless_*` packs

## 5. P4 — multi-review bundles and syntheses

In-repo:

- `forensic/post_step32_knowledge_integration_v0/` (STEP8–STEP32 plus
  transcripts)
- `docs/forensics/working_state/PEAK_TRADE_SW_R_002_WORKING_STATE.md`

P5 (not P2): the bound working runbook itself is a chronological
multi-pass forensic bundle. Derived sidecar/transform packs bundle
structure over that source.

## 6. P6 — accessible Cursor agent outputs

```text
P6_SURFACE=/Users/frnkhrz/.cursor/projects/Users-frnkhrz-Peak-Trade/agent-transcripts
P6_JSONL_GLOB_COUNT_OBSERVED=5185
P6_INGESTED_INTO_THIS_BASE=false
P6_AUTHORITY=NONE
```

Chat output is not repo evidence unless copied under an explicit
preservation GO. This pass registers the locator only.

Desktop originals named in
`forensic/post_step32_knowledge_integration_v0/manifests/source_identities.json`
were probed:

```text
/Users/frnkhrz/Desktop/PEAK_TRADE_TEMPORARY_FORENSIC_WORKING_RUNBOOK.md  exists=false
/Users/frnkhrz/Desktop/PEAK_TRADE_FORENSIC_STEP15_NON_AUTHORITATIVE_TRANSFORMATION_INVARIANT_CONTRACT.md  exists=false
```

Those Desktop paths are historical locators. They were not reassigned.

## 7. P7 — overall / integration overviews (repo)

Navigation samples only; none promoted:

- `docs/PEAK_TRADE_OVERVIEW.md`
- `docs/ARCHITECTURE_OVERVIEW.md`
- `docs/PEAK_TRADE_COMPLETE_OVERVIEW_2025-12-07.md`
- `docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md`

Derived overviews remain non-SSOT.

## 8. Owner-named corpus status (P2)

P2 path resolution failed. That is a proven zero-result **name-match**
discovery, not a proven empty corpus.

P5 counters are separate and must not be substituted.

```text
EXTERNAL_FORENSIC_CORPUS_STATUS=NOT_UNIQUELY_RESOLVED
EXTERNAL_FORENSIC_CORPUS_RESOLVED_PATH=
EXTERNAL_FORENSIC_CORPUS_MUTATED=false
OWNER_NAMED_FOLDER_LITERAL_MATCH_COUNT_UNDER_DOCUMENTS=0
OWNER_NAMED_FOLDER_FORENSIK_NAME_MATCH_COUNT_UNDER_DOCUMENTS=0

P2_CONTENT_INVENTORY_STATUS=NOT_PERFORMABLE_WITHOUT_RESOLVED_CORPUS
P2_FILE_COUNT=UNKNOWN
P2_RELEVANT_SOURCE_COUNT=UNKNOWN
P2_SOURCES_REGISTERED_COUNT=UNKNOWN
P2_READ_ONLY_OUTPUT_STATUS=UNKNOWN
P2_MULTI_REVIEW_BUNDLE_STATUS=UNKNOWN
P2_SYNTHESIS_ARTIFACT_STATUS=UNKNOWN
P2_HISTORICAL_VARIANT_STATUS=UNKNOWN
P2_CROSS_CORPUS_RELATION_STATUS=UNKNOWN

EXTERNAL_FILES_DISCOVERED=UNKNOWN
EXTERNAL_RELEVANT_SOURCES_DISCOVERED=UNKNOWN
EXTERNAL_SOURCES_REGISTERED=UNKNOWN
EXTERNAL_ONLY_INFORMATION_RECORDS=UNKNOWN
REPO_ONLY_INFORMATION_RECORDS=UNKNOWN
CROSS_CORPUS_BYTE_IDENTICAL_RECORDS=UNKNOWN
CROSS_CORPUS_OVERLAP_RECORDS=UNKNOWN
CROSS_CORPUS_CONFLICT_RECORDS=UNKNOWN
CROSS_CORPUS_UNKNOWN_RELATION_RECORDS=UNKNOWN
EXTERNAL_READ_ONLY_OUTPUTS_FOUND=UNKNOWN
EXTERNAL_MULTI_REVIEW_BUNDLES_FOUND=UNKNOWN
EXTERNAL_SYNTHESIS_ARTIFACTS_FOUND=UNKNOWN
```

P5-vs-repo (not P2) facts are in
`CROSS_CORPUS_RELATION_REGISTER_V1.md`.
