# CROSS_CORPUS_RELATION_REGISTER_V1

```text
DOCUMENT_CLASS=NON_AUTHORITATIVE_CROSS_CORPUS_RELATION_REGISTER
AUTHORITY=NONE
TARGET_AUTHORITY=NONE
SECOND_SSOT=false
DEDUPLICATION_PERFORMED=false
SOURCE_IDENTITY_MERGED_ON_BYTE_IDENTICAL=false
MTIME_USED_AS_SEMANTIC_CURRENCY=false
FILENAME_SIMILARITY_ALONE_NOT_USED_AS_RELATION=true
```

Machine facts:
`docs/forensics/persistence/inventories/CROSS_CORPUS_RELATION_FACTS_V1.json`

## Axis 1 — Owner-named P2 vs repo

P2 corpus was not uniquely resolved. No comparison against a resolved
Owner-named folder was performed. That does not prove the P2 corpus is
empty or absent. P2 content remains UNKNOWN / NOT_ASSESSABLE.

```text
P2_CONTENT_INVENTORY_STATUS=NOT_PERFORMABLE_WITHOUT_RESOLVED_CORPUS
P2_CROSS_CORPUS_RELATION_STATUS=UNKNOWN
REPO_ONLY_INFORMATION=UNKNOWN
EXTERNAL_ONLY_INFORMATION=UNKNOWN
PRESENT_IN_BOTH=UNKNOWN
POSSIBLE_OVERLAP=UNKNOWN
CONFLICTING_INFORMATION=UNKNOWN
HISTORICAL_VARIANT=UNKNOWN
UNKNOWN_RELATION=P2_CORPUS_NOT_UNIQUELY_RESOLVED_CONTENT_NOT_ASSESSABLE
P2_CORPUS_ABSENT=false
P2_EMPTY_INFERRED_FROM_UNRESOLVED_PATH=false
```

## Axis 2 — P5 evidence-bound `Documents&#47;Peak_Trade&#47;forensics` vs repo

This axis is **not** P2. Provenance remains
`SOURCE_CLASS=LOCAL_EXTERNAL_FORENSIC_SOURCE` with
`SOURCE_CORPUS=DOCUMENTS_PEAK_TRADE_FORENSICS_EVIDENCE_BOUND_P5_NOT_OWNER_NAMED_FORENSIK_FOLDER`.

### BYTE_IDENTICAL (15 SHA identities)

Both locators kept. No source merge.

Notable:

| SHA256 prefix | Name | P5 locator | Repo locator |
|---------------|------|------------|--------------|
| `f26f6ec751b35fe9` | `PEAK_TRADE_SW_R_002_FORENSIC_DECISION_SURFACE_PRESERVATION.md` | `Documents&#47;Peak_Trade&#47;forensics&#47;…` | `docs&#47;forensics&#47;preservation&#47;…` | <!-- pt:ref-target-ignore -->
| `1704fcb4c9daab46` | `AUTHORITY_NONE.txt` | P5 transformation V1 | `forensics/derived/FORENSIC_STRUCTURE_SCHEMA_V1_TRANSFORMATION_V1/` |
| plus 13 other transformation-V1 report/manifest files | see JSON | P5 derived reports | git `forensics/derived/FORENSIC_STRUCTURE_SCHEMA_V1_TRANSFORMATION_V1/` |

`navigation_views.json` SHA `1b155495ef0d5ced` appears twice on P5
(report file and blobs copy) and in repo.

```text
CROSS_CORPUS_P5_REPO_BYTE_IDENTICAL_SHA_RECORDS=15
```

### CONTENT_OVERLAP_PROVEN + HISTORICAL_VARIANT

`PEAK_TRADE_TEMPORARY_FORENSIC_WORKING_RUNBOOK.md`

| Locator | SHA256 | bytes | lines |
|---------|--------|-------|-------|
| P5 `Documents&#47;Peak_Trade&#47;forensics&#47;…` | `a5a468f761e24e17…` | 8639369 | 121930 |
| Repo lossless-pack identity copy | `10d9293134426805…` | 8499032 | 118809 |

Proof of relatedness (not filename alone):

- identical opening title and identity block through the Target Doctrine
  Reconciliation Pass header;
- repo pack_manifest binds SHA `10d92931…` / 118809 lines;
- SW-R-002 binding binds SHA `a5a468f7…` / 121930 lines as forensic MD.

Not BYTE_IDENTICAL. P5 body contains 3121 lines not present in the repo
identity copy. Those extra lines are not semantically promoted here.

```text
HISTORICAL_VARIANT=PROVEN_FOR_WORKING_RUNBOOK_PAIR
WHICH_VARIANT_IS_SEMANTICALLY_CURRENT=NOT_INFERRED_FROM_MTIME
BOUND_FORENSIC_MD_IDENTITY_IN_SW_R_002_BINDING=a5a468f761e24e17fc0402dbf056df7d45090b3c58f0e9a2ad469569e908e212
REPO_PACK_IDENTITY=10d9293134426805f38996be848e1de853636d8e6f60745a2330bdfd94e3719f
```

### SAME_BASENAME without shared SHA — README.md

Multiple `README.md` files exist in repo schema-V1 derived packages and
one P5 structural-sidecar README. Filename match is not a relation.
Classification: `UNKNOWN_RELATION` (distinct package READMEs).

### P5-only unique SHA identities (27) and file locators (28)

```text
P5_ONLY_UNIQUE_SHA_COUNT=27
P5_ONLY_FILE_LOCATOR_COUNT=28
SOURCE_IDENTITY_MERGED=false
```

Two distinct P5 locators share payload SHA
`a5a468f761e24e17fc0402dbf056df7d45090b3c58f0e9a2ad469569e908e212`:
`PEAK_TRADE_TEMPORARY_FORENSIC_WORKING_RUNBOOK.md` and
`source.snapshot.md`. Byte identity is not source identity.

Includes: those two locators; sidecar JSON; T4 loss register;
structural-v1 jsonl pack; transformation-V1 blobs; alignment-index t4
overlay blob; three local tools; sha256-bound derived
manifest/validation files.

These are `EXTERNAL_ONLY` relative to git, still not P2.

### Repo-only relative to P5 (selected classes)

Not an exhaustive semantic catalog of all 129 hashed P1 files.

Proven repo-only relative to this P5 tree:

- SW-R-002 post-handoff analysis delta and its binding
- SW-R-002 working-state synthesis
- SW-R-002 preservation **binding** markdown (P5 has the preservation
  MD, not the repo binding file)
- `forensic/post_step32_knowledge_integration_v0/` collection
- lossless V2/V2.1 pack except the overlapping transformation reports
- schema V1 adjudication/disposition/alignment derived directories
- `docs&#47;forensic&#47;*.md` implementation notes
- tests and transformer scripts under `tests/` and `scripts/ops/`

### CONFLICTING_INFORMATION

No byte-level conflict was proven (no same-SHA different path claiming
different authority upgrade). Header identity of the two working
runbooks does not contradict; they are sequential variants.

```text
CROSS_CORPUS_CONFLICT_RECORDS_PROVEN=0
```

Desktop locators in older provenance registries (`exists=false`) vs P5
current path: `HISTORICAL_LOCATOR_ABSENT`, not a content conflict.

## Potential existing evidence candidates

The table lists candidate locators discovered this pass. It does not
assess or close any previously open gap.

```text
POTENTIAL_EXISTING_EVIDENCE_CANDIDATES_PRESENT=true
PREVIOUSLY_OPEN_GAP_CLOSURE_ASSESSED=false
GAP_CLOSED=false
POTENTIAL_EXISTING_EVIDENCE_FOR_PREVIOUSLY_OPEN_GAPS=CANDIDATES_PRESENT_CLOSURE_NOT_ASSESSED
```

| Previously recorded gap / absence | Potential P5 evidence | Proven close? |
|-----------------------------------|------------------------|---------------|
| Working-state S10 / forensic MD not in repo; SHA `a5a468f7…` recorded but `FORENSIC_MD_READ_THIS_STEP=false` | P5 file exists, hash matches binding | Locator+hash proven. Semantic gap (22 primitives unanswered; C1-Q1 unanswered) **not** closed |
| Sidecar SHA `6f2928e6…` and T4 loss register SHA `872e1e22…` bound but not git files | P5 files hash-match those bound SHAs | Identity proven. Content not ingested or adjudicated this pass |
| Schema V1 transformation blobs absent from git | P5 `blobs&#47;` present | Files exist. Not promoted to schema-V2 mapping proof |
| Extra 3121 lines vs repo working-runbook identity copy | P5 file longer | Byte difference proven. Meaning of extra lines UNKNOWN this pass |
| Owner-named folder `Peak Trade Forensik` as additional corpus | path not uniquely resolved; P2 content UNKNOWN | gap closure not assessed; P2 remains unresolved |

## A–F answers

### A. Information classes found only in "Peak Trade Forensik"

UNKNOWN / NOT_ASSESSABLE. The Owner-named folder was not uniquely
resolved. No P2 content inventory was performed.

Separately, classes found only in P5 (not P2): bound current working
runbook SHA `a5a468f7…`; its lossless derived packs and blobs; T4 loss
register; structural sidecar; local transform tools.

### B. Artefacts there that contain earlier read-only work

P2: UNKNOWN (`P2_READ_ONLY_OUTPUT_STATUS=UNKNOWN`).

P5: the bound working runbook is itself a persisted chronological
read-only forensic working artefact. The SW-R-002 preservation MD is
BYTE_IDENTICAL with the repo preservation file. Derived sidecar and
schema-V1 reports are derived read-only outputs over that source.

### C. Artefacts that bundle several earlier analyses

P2: UNKNOWN (`P2_MULTI_REVIEW_BUNDLE_STATUS=UNKNOWN`).

P5: the working runbook bundles many forensic passes in one file.
`derived&#47;sha256-a5a468f7…&#47;` and `structural-v1-20260825T100541Z&#47;`
bundle structural projections of that whole file.

Repo P4 bundles (`post_step32_knowledge_integration_v0`, SW-R-002
working state) are not in P5.

### D. Historical variants of repo contents

P2: UNKNOWN (`P2_HISTORICAL_VARIANT_STATUS=UNKNOWN`).

P5 vs repo: working runbook pair above (`a5a468f7…` vs `10d92931…`).
SW-R-002 preservation MD is not a variant; it is BYTE_IDENTICAL.

### E. External information that may matter for later corpus completeness

P2: UNKNOWN (`P2_CONTENT_INVENTORY_STATUS=NOT_PERFORMABLE_WITHOUT_RESOLVED_CORPUS`).

P5 (registered, not copied, not made SSOT):

- current bound forensic MD at SHA `a5a468f7…` (121930 lines)
- sidecar and T4 loss register already SHA-bound in SW-R-002 binding
- schema-V1 blob payloads not stored in git
- local tools that generated those derived artefacts
- extra lines after the repo identity copy of the working runbook

### F. Relations proven vs UNKNOWN

**Proven**

- P2 directory-name resolution under Documents produced zero literal / Forensik-name matches (`OWNER_NAMED_FOLDER_LITERAL_MATCH_COUNT_UNDER_DOCUMENTS=0`); P2 content remains UNKNOWN
- P5 path exists and was not mutated
- 15 SHA BYTE_IDENTICAL identities between P5 and repo
- working-runbook pair is CONTENT_OVERLAP_PROVEN and HISTORICAL_VARIANT
- sidecar SHA and T4 loss-register SHA in the SW-R-002 binding match P5 files
- Desktop STEP15 / working-runbook originals from post_step32 registry
  are currently absent

**UNKNOWN**

- contents of the Owner-named folder `Peak Trade Forensik`
- semantic meaning of the 3121-line delta between working-runbook SHAs
- whether P5 blobs close any schema-V2 mapping or SW-R-002 owner
  questions
- whether any other local folder is the intended Owner-named corpus
- P6 transcript semantic overlap with P1/P5 (not ingested)
- README.md same-basename files across packages

## Navigation only — P6_5189 observation graph is a different surface

This register remains the P2-vs-repo and P5-vs-repo cross-corpus axes.
It is **not** the P6_5189 relation / dependency / proof-obligation graph.
Axis-1 and Axis-2 semantics above are unchanged.

P6_5189 graph locators (AUTHORITY=NONE; navigation only):

- `docs&#47;forensics&#47;persistence&#47;registries&#47;P6_5189_RELATION_LEDGER_V1.json`
- `docs&#47;forensics&#47;persistence&#47;registries&#47;P6_5189_RELATION_NODE_REGISTER_V1.json`
- `docs&#47;forensics&#47;persistence&#47;registries&#47;P6_5189_SET_AND_UNIVERSE_REGISTER_V1.json`
- `docs&#47;forensics&#47;persistence&#47;registries&#47;P6_5189_PROOF_OBLIGATION_MATRIX_V1.json`
