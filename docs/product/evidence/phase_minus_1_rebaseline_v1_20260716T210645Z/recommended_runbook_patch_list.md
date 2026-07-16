# Recommended Runbook Patch List (advisory)

```text
DOCUMENT_ROLE=NON_CANONICAL_RECOMMENDATION_LOG
MAY_NOT_OVERRIDE_RUNBOOK=true
PATCHES_REQUIRE_SEPARATE_RATIFICATION=true
SLICE=PHASE_MINUS_1_REBASELINE_V1
```

This list does **not** patch the Product Runbook. Ratifizierte Änderungen brauchen einen eigenen Auftrag.

| ID | Severity | Finding | Recommended patch (later) |
|---|---|---|---|
| P1 | MEDIUM | §20.2 still shows illustrative `<repo-bound-owner>` placeholders in the runbook text | Replace illustrative placeholders with pointer to `landmark_owner_binding_matrix.json` as the binding evidence owner |
| P2 | LOW | Eye-path short form vs hero-nested decision can be misread | Add explicit note that Decision may be composed with Primary Market Surface but chart Y-order remains primary |
| P3 | LOW | Phase -1 artifact list predates landmark/SSOT extras | Optionally extend Phase -1 Pflichtartefakte list to include landmark/SSOT/geometry/PR5250 files already produced here |
| P4 | INFO | `docs/product/RUNBOOK_PATCH_RECOMMENDATIONS.md` is older bootstrap advice | Keep as historical; do not treat as SSOT |

No silent runbook mutation in this slice.
