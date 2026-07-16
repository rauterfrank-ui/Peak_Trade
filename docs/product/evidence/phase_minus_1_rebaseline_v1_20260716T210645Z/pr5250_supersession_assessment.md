# PR #5250 Supersession Assessment (read-only)

```text
PR=5250
STATE=OPEN
MERGED=false
HEAD_REF=feat/market-dashboard-composition-first-refactor-v1
HEAD_OID=9739781698ac076187151e47abc0c93754d7bd8a
CI_STATUS=GREEN
CODE_IMPORTED_INTO_THIS_SLICE=false
MERGE_RECOMMENDED=false
```

## What PR #5250 changes

54 files / +1007 / −49, primarily:

- `static&#47;css&#47;peak_trade_dashboard_design_tokens_v1.css`
- `static&#47;css&#47;peak_trade_dashboard_layout_v1.css`
- `templates&#47;peak_trade_dashboard&#47;market_v0.html`
- Visual Operator partials (header, hero, chart, ranking, funnel, economic, AI)
- `tests&#47;webui&#47;test_market_dashboard_composition_first_refactor_v1.py`
- Large evidence tree under `docs&#47;product&#47;evidence&#47;visual_composition_first_refactor_v1_20260716T221000Z&#47;`

Intent: composition-first chrome reduction (less card wall / badge wall).

## Assessment against updated Runbook v1.3 (§§17–22)

| Topic | Finding |
|---|---|
| Composition-first | Directionally aligned, but measured against pre-§17–22 baseline |
| Landmark Architecture | Does not introduce §19 landmark ownership / `data-landmark-*` binding |
| UX Acceptance / Geometry | Improves some chrome metrics; does not rebaseline to new consolidated gate |
| Eye-path | Does not resolve Decision-above-Chart inversion observed on main |
| SSOT / Consumer-only | Presentation-only CSS/template changes; no core semantics claimed |
| CI green | **Not** sufficient for merge recommendation |

## Reuse posture

- Do **not** merge PR #5250.
- Do **not** use its branch as implementation base.
- Do **not** cherry-pick into this Phase -1 branch.
- Later slices may independently re-implement useful presentation ideas after revalidation against §§17–22; that is not an import of #5250.

## Disposition

```text
PR5250_DISPOSITION_RECOMMENDATION=SUPERSEDE_WITHOUT_MERGE
```

PR #5250 remains OPEN and unchanged until a separate explicit operator GO.
