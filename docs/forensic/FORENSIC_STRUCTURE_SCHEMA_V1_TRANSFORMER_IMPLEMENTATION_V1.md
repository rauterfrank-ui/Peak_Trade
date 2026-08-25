# FORENSIC_STRUCTURE_SCHEMA_V1 Transformer Implementation

```text
DOCUMENT_ROLE=TECHNICAL_IMPLEMENTATION_NOTE
DOCUMENT_AUTHORITY=NONE
OUTPUT_ROLE=TEST_ARTIFACT_ONLY
NOT_CANONICAL=true
NOT_MASTER_RUNBOOK=true
NOT_MAP_OF_TRUTH=true
RUNTIME_AUTHORIZATION_EFFECT=NONE
RETAINED_OUTPUT_ROLE=DERIVED_FORENSIC_STRUCTURE
RETAINED_OUTPUT_AUTHORITY=NONE
```

This note documents the implemented read-only transformer. It does not
promote authority, currentness, gates, pointers, or canonical status.

## What was implemented

Python package:

- `scripts/ops/forensic_structure_schema_v1/`
- runner: `scripts/ops/run_forensic_structure_schema_v1_transformer.py`

Tests:

- `tests/forensic_structure_schema_v1/`
- `tests/scripts/test_run_forensic_structure_schema_v1_transformer.py`

The transformer consumes only the bound Documents locator source and
sidecar. It does not import the source into the repo and does not write
those files.

## Pipeline stages

Stages remain separate modules:

1. A Immutable Input Verification
2. B Raw Occurrence Registry
3. C Overlay Registry
4. D Provenance Registry
5. E Non-Inference Guard
6. F Semantic Envelope Projection
7. G Relation Projection
8. H Residual Registry
9. I Invariant Validation
10. J Losslessness Audit
11. K Contract-Test Evaluation
12. L Output Eligibility Decision

`OUTPUT_ELIGIBLE=true` means stages A–L passed contract checks. A separate
Owner-GO is required to persist a retained derived dataset. When that GO is
present, the merged transformer writes:

```text
OUTPUT_ROLE=DERIVED_FORENSIC_STRUCTURE
OUTPUT_AUTHORITY=NONE
OUTPUT_IS_CANONICAL=false
```

Retained reports live at
`forensics/derived/FORENSIC_STRUCTURE_SCHEMA_V1_TRANSFORMATION_V1/`.
Large dataset shards are regenerated with:

```text
./scripts/pt scripts/ops/run_forensic_structure_schema_v1_transformer.py --persist-retained-derived
```

The retained output is not a source replacement, not Master Runbook, and
not Map of Truth.

## Identity and joins

Token `occ-*` IDs and Layer-1 `occ-*` IDs are disjoint spaces.
Equality join between them is forbidden. The closed join set is:

```text
BYTE_RANGE_EXACT
OVERLAY_REFERENCE
LAYER1_OCCURRENCE_REFERENCE
EXPLICIT_ALIAS_MAP_NAVIGATION_ONLY
DOCUMENTARY_STRING_ENDPOINT
UNRESOLVED
```

Line-equality is not a join. Hash-equality is not identity.

## Residuals

SW-R-001 through SW-R-015 and DR-001, DR-002, DR-003, DR-006, DR-007,
DR-008 remain `OPEN`. A passing test does not close a residual.

## Defaults

When positive semantics are not bound:

```text
AUTHORITY_STATUS=NONE
CURRENTNESS_STATUS=CURRENTNESS_UNKNOWN
EPISTEMIC_CLASS=UNCLASSIFIED
GATE_MEMBERSHIP=UNKNOWN
SUPERSESSION=UNKNOWN
PRIMARY_LABEL=NONE
SEMANTIC_CONTAINER=NOT_ADJUDICATED
WINNER_SELECTED=false
```

ABSENT, JSON null, UNKNOWN, UNCLASSIFIED, NONE, and false are distinct
in test serialization.

## Bound local validation

Source and sidecar remain outside the git index. Local tests require:

```text
SOURCE=/Users/frnkhrz/Documents/Peak_Trade/forensics/PEAK_TRADE_TEMPORARY_FORENSIC_WORKING_RUNBOOK.md
SIDECAR=/Users/frnkhrz/Documents/Peak_Trade/forensics/derived/PEAK_TRADE_TEMPORARY_FORENSIC_WORKING_RUNBOOK.structure-v1.json
```

CI without those files skips bound integration tests and still runs
unit guards.
