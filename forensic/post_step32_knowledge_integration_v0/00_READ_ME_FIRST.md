# Forensic post-STEP32 knowledge collection — read me first

```text
DOCUMENT_CLASS=NON_AUTHORITATIVE_NAVIGATION_INDEX
DOCUMENT_ROLE=NAVIGATION_ONLY_NO_SEMANTICS
ARTIFACT_AUTHORITY=NONE
TARGET_AUTHORITY=NONE
SECOND_SSOT=false
MASTER_RUNBOOK_REMAINS_SOLE_SSOT=true
NOT_CANONICAL=true
NOT_THE_TARGET=true
NOT_THE_MASTER_RUNBOOK=true
NOT_A_NUMBERED_FORENSIC_STEP=true
STEP33=NOT_DEFINED
THIS_IS_NOT_FINAL_CANONIZATION=true
RUNTIME_AUTHORIZATION_EFFECT=NONE
FILE_PLACEMENT_IS_NOT_AUTHORITY_PROMOTION=true
PRODUCT_A_ALONE_CAN_RECONSTRUCT_ALL_EVIDENCE=false
```

This directory is a **working collection** of already-established forensic knowledge.

It is not a second source of truth. It is not a replacement for
`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`.
It does not authorize Live, Testnet, orders, credentials, or writes
outside this worktree.

The Master Runbook remains the sole semantic SSOT. The Map of Truth
remains navigation-only.

## What this collection is for

Make the completed read-only forensic sequence inspectable **without**
Cursor/chat memory: provenance, raw evidence, adjudicated findings,
historical intermediates, open points, negative results, and the M06
pre-write contract.

## What this collection is not

- not canonization
- not STEP33
- not an M06 Desktop write
- not a markdown materialization of the TARGET
- not a commit, push, PR, or merge
- not a claim that M06 contains all post-STEP32 evidence

## How to read (epistemic order)

1. This file (navigation + authority labels only).
2. `01_authority_and_epistemic_legend.md`
3. `02_provenance_source_registry.md` and `manifests/source_identities.json`
4. Raw identity copies under `evidence/raw_verbatim_identity_copies_authority_none/`
5. Curated findings and contracts (`05_`, `07_`, `09_`) — always as
   pointers into raw evidence, never as replacements.

## Layout

| Path | Role | Epistemic class |
|---|---|---|
| `00_READ_ME_FIRST.md` | entry navigation | NAVIGATION_INDEX |
| `01_authority_and_epistemic_legend.md` | class legend | NAVIGATION_INDEX |
| `02_provenance_source_registry.md` | source registry | SOURCE_IDENTITY_AND_PROVENANCE |
| `03_chronology.md` | sequence | HISTORICAL_INTERMEDIATE_STATE + NAVIGATION |
| `04_information_inventory.md` | exhaustive item map | NAVIGATION_INDEX |
| `05_adjudicated_findings.md` | curated findings | ADJUDICATED_FINDING |
| `06_historical_intermediate_states.md` | superseded artifacts | HISTORICAL_INTERMEDIATE_STATE |
| `07_unresolved_open_issues.md` | still open | OPEN_OR_CONTRADICTORY |
| `08_relationships.md` | established mappings | NAVIGATION_INDEX |
| `09_m06_preservation_recovery_contract.md` | M06 contract | TRANSFORMATION_OR_IMPLEMENTATION_CONTRACT |
| `10_step15_forbid_index.md` | FORBID navigation | NAVIGATION_INDEX (not a replacement of STEP15) |
| `11_adversarial_completeness_audit.md` | reverse audit | INTERPRETATION of completeness, not new facts |
| `12_what_this_collection_does_not_prove.md` | negative claims | ADJUDICATED_FINDING (limits) |
| `manifests/*.json` | machine-readable maps | NAVIGATION_INDEX / SOURCE_IDENTITY |
| `evidence/...` | byte-identical copies | RAW_VERBATIM_EVIDENCE |

Canonical SSOT and Map stay at their repository paths in this worktree
(bound SHA `652c2cd4f9e91160a46b86f02014fd019ec33ca5`). They are **not**
copied into `forensic/` so they are not mistaken for a second SSOT.

## Bound git context

```text
WORKTREE_BRANCH=forensic/post-step32-knowledge-integration
WORKTREE_BASE_SHA=652c2cd4f9e91160a46b86f02014fd019ec33ca5
PRIMARY_REPO_MUST_REMAIN_ON_MAIN=true
```
