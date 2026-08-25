# Adjudication contract V1 (derived, non-authoritative)

```text
DOCUMENT_ROLE=DERIVED_NAVIGATION_OR_ANALYSIS_ONLY
DOCUMENT_AUTHORITY=NONE
OUTPUT_AUTHORITY=NONE
TARGET_AUTHORITY=NONE
OUTPUT_CANONICAL=false
SEMANTIC_BINDING_PERFORMED=false
PROVEN_OCCURRENCE_IDENTITY_COUNT=0
PROVEN_PARENTAGE_COUNT=0
CURRENTNESS_ADJUDICATION_PERFORMED=false
SUPERSESSION_ADJUDICATION_PERFORMED=false
WINNER_SELECTED_COUNT=0
SW_R_002_STATUS=OPEN
SW_R_004_STATUS=OPEN
SW_R_009_STATUS=OPEN
THIS_DIRECTORY_IS_NOT_CANONICAL_AUTHORITY=true
```

Derived-only infrastructure for later candidate adjudication. This directory
does not replace the bound Source, the bound Sidecar, the A-L retained
transformation, the PR #6063 disposition layer, or the alignment index.

A better structure does not create authority. Candidate is never proven.
String reuse is not occurrence identity. Git tracking is not authority.

Regenerate with:

```text
./scripts/pt -m scripts.ops.run_forensic_structure_schema_v1_adjudication_contract --persist
```
