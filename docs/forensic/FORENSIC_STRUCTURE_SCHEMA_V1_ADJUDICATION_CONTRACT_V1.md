# FORENSIC_STRUCTURE_SCHEMA_V1 Adjudication Contract V1

```text
DOCUMENT_ROLE=TECHNICAL_IMPLEMENTATION_NOTE
DOCUMENT_AUTHORITY=NONE
OUTPUT_ROLE=DERIVED_NAVIGATION_OR_ANALYSIS_ONLY
OUTPUT_AUTHORITY=NONE
TARGET_AUTHORITY=NONE
OUTPUT_CANONICAL=false
SEMANTIC_BINDING_PERFORMED=false
PROVEN_OCCURRENCE_IDENTITY_COUNT=0
PROVEN_PARENTAGE_COUNT=0
CURRENTNESS_ADJUDICATION_PERFORMED=false
SUPERSESSION_ADJUDICATION_PERFORMED=false
WINNER_SELECTED_COUNT=0
RESIDUAL_CLOSE_PERFORMED=false
NOT_MASTER_RUNBOOK=true
NOT_MAP_OF_TRUTH=true
RUNTIME_AUTHORIZATION_EFFECT=NONE
SW_R_002_STATUS=OPEN
SW_R_004_STATUS=OPEN
SW_R_009_STATUS=OPEN
```

Additive derived-only infrastructure over the binding-candidate alignment
index. It does not replace stages A-L, the retained dataset, the bound
Source, the bound Sidecar, the disposition layer, or the alignment index.

A better structure does not create authority. Classification is not
occurrence identity. Git tracking is not canonization.

## Bound inputs

Observational locators (not Desktop, not Downloads):

```text
SOURCE=/Users/frnkhrz/Documents/Peak_Trade/forensics/PEAK_TRADE_TEMPORARY_FORENSIC_WORKING_RUNBOOK.md
SIDECAR=/Users/frnkhrz/Documents/Peak_Trade/forensics/derived/PEAK_TRADE_TEMPORARY_FORENSIC_WORKING_RUNBOOK.structure-v1.json
CANDIDATE_INDEX=forensics/derived/FORENSIC_STRUCTURE_SCHEMA_V1_BINDING_CANDIDATE_ALIGNMENT_INDEX_V1/endpoint_binding_candidate_records.json
EXPECTED_SOURCE_SHA256=a5a468f761e24e17fc0402dbf056df7d45090b3c58f0e9a2ad469569e908e212
EXPECTED_SIDECAR_SHA256=6f2928e67d45de2162df1589de77ea530061652181ba6efd9a0f528ca7e6ad6e
EXPECTED_CANDIDATE_SHARD_SHA256=9eaded3909af1c5e89148b93650b08448a5b51eda359d2c51b8ea86f798c075e
EXPECTED_T4_SHARD_SHA256=53773007b39c3997ce55eae312e54e3fece80dbe9cb594316a7dbab3e3134ec1
```

## What this contract records

1. Dimension model — 15 first-class dimensions. Only `OCCURRENCE_IDENTITY` is executed, and only as classify/disqualify.
2. Outcome/reason-code vocabulary — `PROVEN_OCCURRENCE_IDENTITY` exists in the schema and is runtime-forbidden under this GO.
3. Competing-set / ambiguity graph — 8 sets / 18 members. String reuse is not a duplicate record and not occurrence identity. The original 6 `AMBIGUOUS_BINDING` candidates remain distinct from the other 12 members.
4. Per-candidate negative-evidence index — NI-001..NI-017 plus disposition disqualifiers, with explicit `applicable=true` or `applicable=false`.
5. Fail-closed evaluator — no heuristic identity, no positive occurrence bind.
6. Non-inference audit — machine-checkable `NO_BIND_FROM_*` assertions.
7. Execution boundaries A-H — this GO authorizes infrastructure only. It does not authorize semantic Boundary A execution and does not authorize B-H.

## Explicit non-equations retained

Occurrence Binding ≠ Semantic Equivalence ≠ Parentage ≠ Currentness ≠
Supersession ≠ Winner ≠ Authority. Chronology ≠ Dependency.
Mechanical Order ≠ Dependency. Alias ≠ Source Occurrence.
Overlay ≠ Layer-1 Occurrence. Navigation Link ≠ Identity.
Corpus SHA Equality ≠ Occurrence Identity.
OPEN ≠ UNPROVEN ≠ CLOSED. ABSENT ≠ FALSE. UNKNOWN ≠ FALSE.

## Persist

```text
./scripts/pt -m scripts.ops.run_forensic_structure_schema_v1_adjudication_contract --persist
```

Git-tracked reports: `forensics&#47;derived&#47;FORENSIC_STRUCTURE_SCHEMA_V1_ADJUDICATION_CONTRACT_V1&#47;`
