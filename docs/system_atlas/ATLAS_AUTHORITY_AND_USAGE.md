# Atlas Authority and Usage

```text
ATLAS_AUTHORITY=NONE
ATLAS_ROLE=EVIDENCE_BOUND_SYSTEM_TOPOLOGY_AND_NAVIGATION
CANONICAL_AUTHORITY_IS_EXTERNAL_TO_ATLAS=true
ATLAS_MUST_CITE_AUTHORITY=true
ATLAS_MUST_NOT_CREATE_AUTHORITY=true
```

## What this Atlas may do

- Inventory Peak_Trade-native constructs from origin/main, code, tests, config, schemas, docs, runbooks, forensic persistence, and bounded git history.
- Record producers, consumers, relations, contradictions, and OPEN gaps.
- Generate navigation views. Generated files are not authority.

## What this Atlas must not do

- Create, mutate, or replace canonical authority.
- Equate IMPLEMENTATION with ACTIVATION, MERGED with PRODUCTIVELY_PROVEN, or FIXTURE_PASS with PRODUCTIVE_EVIDENCE.
- Authorize Live, Testnet, credentials, orders, or capital movement.
- Normalize terminology collisions.
- Invent acronym expansions.
- Repair XPERP / `uly` / quote identity as a side effect of census.

## How to read a term

For any unfamiliar construct, use generated `PROJECT_TERMINOLOGY.md`, `ACRONYM_REGISTER.md`, `DOD_MAP.md`, and `SCHEMA_MAP.md` to answer:

- WHAT_IS_IT
- WHERE_DID_IT_COME_FROM
- WHAT_DOES_IT_BELONG_TO
- WHAT_DEPENDS_ON_IT / WHAT_IT_DEPENDS_ON
- IS_IT_CURRENT / HISTORICAL / CANONICAL
- WHAT_PROVES_ITS_MEANING
- WHAT_REPLACED_IT_IF_ANY
- WHAT_REMAINS_OPEN

If a field is unproven, the Atlas records `OPEN` rather than guessing.

## Navigation rule

```text
README.md
    -> explains Atlas authority/usage
SYSTEM_ATLAS.md
    -> complete primary human overview (not an index-only file)
specialized generated views
    -> exhaustive domain-specific detail
machine-readable Atlas records
    -> source model
canonical authority
    -> remains external to Atlas
```

`docs/system_atlas/generated/SYSTEM_ATLAS.md` is the primary human entrypoint. Specialized files are drill-down views. Do not treat a generated overview as canonical SSOT.

## Change coupling / drift prevention

This Atlas must stay synchronized with future architecture and runtime changes. Synchronization does **not** make the Atlas canonical authority. Canonical authority remains the Master Runbook and must still be cited by Atlas records.

```text
IMPLEMENTATION CHANGE
-> ATLAS IMPACT DETECTION
-> ATLAS SOURCE UPDATE
-> GENERATED VIEWS
-> VALIDATION
-> CI GATE
-> MERGE
```

1. Do not manually patch generated Markdown.
2. Update machine-readable records first (`docs/system_atlas/**/*.yaml` except `generated/`).
3. Run `./scripts/pt scripts/ops/generate_system_atlas_v1.py`.
4. Run `./scripts/pt scripts/ops/validate_system_atlas_v1.py`.
5. Run `./scripts/pt scripts/ops/check_system_atlas_impact_v1.py --base origin/main`.
6. Every material PR must report exactly one of `ATLAS_IMPACT=UPDATED` or `ATLAS_IMPACT=NONE_WITH_PROOF`.
7. If impact cannot be determined: `ATLAS_IMPACT=REVIEW_REQUIRED` and `SYSTEM_ATLAS_DRIFT_DETECTED=true`.
8. Before merge, provenance fields may be `PENDING_CHANGE`. After merge, bind the real commit/PR; do not invent identifiers beforehand.

When implementation adds a connection such as `A -> CONSUMES -> B`, the same workpackage must add/update the machine-readable relation, evidence, dependency closures, regenerate views, validate, and report Atlas impact.

Entities may declare `source_paths` and `source_symbols`. The impact checker also indexes `evidence_sources` / `authority_sources` that look like repository paths. The checker does not claim perfect semantic inference.
