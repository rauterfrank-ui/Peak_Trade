# FORENSIC_STRUCTURE_SCHEMA_V1 Binding-Candidate Alignment Index

```text
DOCUMENT_ROLE=TECHNICAL_IMPLEMENTATION_NOTE
DOCUMENT_AUTHORITY=NONE
OUTPUT_ROLE=DERIVED_NAVIGATION_OR_ANALYSIS_ONLY
OUTPUT_AUTHORITY=NONE
TARGET_AUTHORITY=NONE
OUTPUT_CANONICAL=false
SEMANTIC_BINDING_PERFORMED=false
OCCURRENCE_BINDING_PROVEN_COUNT=0
PROVEN_PARENTAGE_COUNT=0
RESIDUAL_CLOSE_PERFORMED=false
NOT_MASTER_RUNBOOK=true
NOT_MAP_OF_TRUTH=true
RUNTIME_AUTHORIZATION_EFFECT=NONE
SW_R_002_STATUS=OPEN
SW_R_004_STATUS=OPEN
SW_R_009_STATUS=OPEN
```

Additive derived layer over the A–L retained transformation and the
PR #6063 binding-disposition layer. It does not replace stages A–L, the
retained dataset, the bound Source, the bound Sidecar, or disposition
records.

Structuring is not canonization. A candidate is never proven.
Deterministic derivation is not semantic truth. Git tracking is not
authority.

## Bound inputs

Observational locators (not Desktop, not Downloads):

```text
SOURCE=/Users/frnkhrz/Documents/Peak_Trade/forensics/PEAK_TRADE_TEMPORARY_FORENSIC_WORKING_RUNBOOK.md
SIDECAR=/Users/frnkhrz/Documents/Peak_Trade/forensics/derived/PEAK_TRADE_TEMPORARY_FORENSIC_WORKING_RUNBOOK.structure-v1.json
EXPECTED_SOURCE_SHA256=a5a468f761e24e17fc0402dbf056df7d45090b3c58f0e9a2ad469569e908e212
EXPECTED_SIDECAR_SHA256=6f2928e67d45de2162df1589de77ea530061652181ba6efd9a0f528ca7e6ad6e
```

## Record classes

1. `T4_OVERLAY_RECORD` — 7175 first-class T4 rows, including 7088 Layer-3-NULL rows
2. `LAYER3_RELATION_RECORD` — 122 Layer-3 relations with existing disposition
3. `ENDPOINT_BINDING_CANDIDATE_RECORD` — 244 candidates, never proven
4. `VIEW_RECORD` — 12 views; ABSENT / NULL / PRESENT stay distinct
5. `CROSS_RESIDUAL_EVIDENCE_EDGE` — proven / possible / rejected; `close_order=false`
6. `NON_IDENTITY_RECORD` — first-class non-equations, not normalized away

## Persist

```text
./scripts/pt -m scripts.ops.run_forensic_structure_schema_v1_alignment_index --persist
```

Git-tracked reports: `forensics&#47;derived&#47;FORENSIC_STRUCTURE_SCHEMA_V1_BINDING_CANDIDATE_ALIGNMENT_INDEX_V1&#47;`

Large T4 shards remain externally retained with hash/manifest binding.
