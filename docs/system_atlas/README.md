# Peak_Trade System Atlas

```text
ATLAS_AUTHORITY=NONE
ATLAS_ROLE=EVIDENCE_BOUND_SYSTEM_TOPOLOGY_AND_NAVIGATION
CANONICAL_AUTHORITY_IS_EXTERNAL_TO_ATLAS=true
ATLAS_MUST_CITE_AUTHORITY=true
ATLAS_MUST_NOT_CREATE_AUTHORITY=true
RUNTIME_AUTHORIZATION_EFFECT=NONE
```

This directory is an evidence-bound topology and navigation atlas. It is not a business SSOT, not a second Master Runbook, and not a runtime authorization surface.

- Canonical semantic authority remains `docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`.
- Map of Truth remains navigation-only.
- Generated markdown under `generated&#47;` is deterministic output. Do not edit it by hand.
- Census completeness flags in `census&#47;census_meta.yaml` are fail-closed: `false` unless every required search flag is proven.

Navigation:

```text
README.md
    -> Atlas authority and usage (this file + ATLAS_AUTHORITY_AND_USAGE.md)
docs/system_atlas/generated/SYSTEM_ATLAS.md
    -> complete primary human overview
specialized generated views
    -> exhaustive domain-specific detail
machine-readable Atlas records (YAML under this directory)
    -> source model
canonical authority
    -> remains external to Atlas (Master Runbook)
```

```text
SYSTEM_ATLAS_PRIMARY_ENTRYPOINT=docs/system_atlas/generated/SYSTEM_ATLAS.md
SYSTEM_ATLAS_MASTER_VIEW_COMPLETE=true
```

Usage:

```text
./scripts/pt scripts/ops/generate_system_atlas_v1.py
./scripts/pt scripts/ops/validate_system_atlas_v1.py
./scripts/pt scripts/ops/check_system_atlas_impact_v1.py --base origin/main
./scripts/pt -m pytest -q tests/ops/test_system_atlas_v1.py tests/ops/test_system_atlas_impact_v1.py
```

Do not edit generated Markdown by hand. Update machine-readable YAML first, then regenerate.

Future change coupling:

```text
IMPLEMENTATION CHANGE
-> ATLAS IMPACT DETECTION
-> ATLAS SOURCE UPDATE
-> GENERATED VIEWS
-> VALIDATION
-> CI GATE
-> MERGE
```

Allowed impact classifications: `ATLAS_IMPACT=UPDATED` or `ATLAS_IMPACT=NONE_WITH_PROOF`. Unmapped material architecture is `ATLAS_IMPACT=REVIEW_REQUIRED` (fail closed). This mechanism does not make the Atlas canonical authority.

Historical reconsolidation governance and the empty reconciliation ledger live
under `reconciliation&#47;`. That tree is governance/evidence only. It does not raise Atlas authority,
does not replace the Atlas census, and does not authorize runtime, trading, risk, or execution.

See `ATLAS_AUTHORITY_AND_USAGE.md` and `reconciliation&#47;README.md`.
