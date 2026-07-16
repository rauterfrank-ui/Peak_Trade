# Visual Gap Assessment — Phase -1 vs Runbook v1.3 §§17–22

```text
BASELINE=origin/main foundation (post PR #5249)
EVALUATION_BASIS=docs/product/Peak_Trade_Visual_Operator_Dashboard_Product_Runbook_v1.3.md
PR5250_USED_AS_BASE=false
```

## Gaps blocking product gates

1. **Eye-path** — Decision narrative appears above the primary chart.
2. **Landmark cohesion** — Secondary grid mixes Decision (safety/DP) with Observability (watchlist/F5).
3. **Landmark markers** — No explicit §19 `data-landmark-*` attributes.
4. **Engineering identity** — Multiple collapsed details instead of one ENGINEERING_DRAWER landmark.
5. **Information density** — Ranking block ~1035px tall dominates below-fold scanning.
6. **Composition chrome** — Residual card/border wrappers remain on main foundation.
7. **Consolidated gate** — `COMPOSITION_GATE_PASS`, `LANDMARK_GATE_PASS`, `UX_ACCEPTANCE_GATE_PASS`, `FULL_PAGE_REVIEW_PASS` all false.

## Non-gaps / preserved strengths

- Single render chain / single resolver.
- Chrome-primary Playwright harness exists and passes foundation numeric contract.
- Header height, chart visibility, overflow, Level-4 default closed meet numeric thresholds on 1440×900.
- Consumer-only posture largely intact; no confirmed second business truth.

## Recommended first mutation slice

`S1 Composition/Landmark Foundation` only — no new functional surfaces until gates flip.
