# Design Review Gate — Phase 2 Operator Overview

```text
GO_TOKEN=GO_VISUAL_OPERATOR_DASHBOARD_DESIGN_GATE_AND_PHASE3_PREP_V1
PR_NUMBER=5247
CANONICAL_RUNBOOK=docs/product/Peak_Trade_Visual_Operator_Dashboard_Product_Runbook_v1.3.md
PRIMARY_BROWSER=GOOGLE_CHROME
PLAYWRIGHT_CHANNEL=chrome
REAL_CHROME_VERIFIED=true
CHROMIUM_FALLBACK_USED=false
CONSOLE_ERRORS=0
NETWORK_ASSERTIONS=SELF_ONLY_PASS
HORIZONTAL_OVERFLOW=false
CHART_TOP_VISIBLE_1440x900=true
CHART_MATERIALLY_VISIBLE_1440x900=true
NO_UI_FEATURE_CHANGES_IN_THIS_GATE=true
```

Scope: UX / Visual Design only. Trading logic, data quality, core producers are out of scope.

## A. Positiv

1. **Above-the-fold hierarchy** — Global header → compact market header/safety rail → Operator Overview hero → chart start is readable at 1440×900.
2. **Hero layout (8/4)** — Selected instrument + decision narrative dominate; Critical System State is a calm right rail, not an alarm wall for expected disabled states.
3. **Decision narrative** — Single deterministic sentence answers instrument, rank, regime honesty, decision, and primary blocker within five seconds.
4. **Chart priority** — Chart top ≈407px, height ≈458px at 1440×900; material candle+volume area is inside the fold.
5. **Whitespace** — Dense terminal density without giant unexplained empty regions above the chart.
6. **Progressive disclosure** — Ranking/F5/contract/freshness and chart diagnostics remain secondary/collapsed.
7. **Premium terminal impression** — Dark surface, mono metrics, clear section borders; reads as operator tooling rather than a marketing dashboard.
8. **Chrome/Playwright evidence** — Real Chrome channel verified; console/network/overflow gates green for this review pass.

## B. Negativ

1. **Badge density in the visual operator header** — Multiple status pills (READ-ONLY, FUTURES-ONLY, PREFLIGHT BLOCKED, LIVE LOCKED, FRESH, AUTHORITY, ECON, AI) still form a dense strip above the hero.
2. **Status repetition** — Preflight/Blocked appears in the safety rail, decision sentence, and Critical System State; useful for fail-closed clarity, but visually redundant.
3. **AI label inconsistency surface** — Header still surfaces legacy `AI - ACTIVE` styling while Phase 2 overview maps display activity to `PROCESSED` (honest mapping, but two labels compete).
4. **Regime secondary fields** — Trend/regime beyond a single token remain largely unavailable; hierarchy is correct, but Market Regime as HERO_SECONDARY is visually thin.
5. **Global app nav density** — Shell navigation remains busy relative to the market operator focus (shared shell, not Phase-2-owned).

## C. Verbesserungen

1. Soft-collapse or de-emphasize non-critical header pills so Safety Rail remains one calm strip (not a badge wall).
2. Align header AI chip display with overview activity vocabulary (`PROCESSED` / allowed states) without inventing new semantics.
3. Keep Critical System State calm; avoid repeating the same blocker in three equal-weight treatments — one primary, others secondary.
4. Phase 3 should deepen chart meta (tooltip, windowing, stale overlay) without growing hero height.
5. Optional later: reduce shell nav visual weight on `/market` only if a shared shell owner exists (out of Phase 2/3 unless reuse-bound).

## D. Priorisierung

### HIGH

- Preserve chart material visibility at 1440×900 in any follow-up work.
- Do not re-introduce KPI card walls or F5 dumps into the hero.

### MEDIUM

- Reduce header badge-wall density / duplicate blocker emphasis.
- Harmonize AI activity display labels between header and overview.

### LOW

- Shell nav density on market route.
- Cosmetic spacing polish once Phase 3 chart contracts land.

## E. Screenshot-Referenzen

Chrome Design Gate capture set:

1. Header — `docs/product/evidence/phase_2_20260716T184639Z/design_review/gate_chrome/01_header_1440x900.png`
2. Hero — `docs/product/evidence/phase_2_20260716T184639Z/design_review/gate_chrome/02_hero_1440x900.png`
3. Hero + Chart — `docs/product/evidence/phase_2_20260716T184639Z/design_review/gate_chrome/03_hero_chart_1440x900.png`
4. Above Fold — `docs/product/evidence/phase_2_20260716T184639Z/design_review/gate_chrome/04_above_fold_1440x900.png`
5. Full Desktop — `docs/product/evidence/phase_2_20260716T184639Z/design_review/gate_chrome/05_full_desktop_1440x900.png`
6. Narrow Desktop — `docs/product/evidence/phase_2_20260716T184639Z/design_review/gate_chrome/06_narrow_1280x800.png`
7. Wide Desktop — `docs/product/evidence/phase_2_20260716T184639Z/design_review/gate_chrome/07_wide_1728x1117.png`

Browser report:

- `docs/product/evidence/phase_2_20260716T184639Z/design_review/gate_chrome/design_gate_browser_report.json`

## F. Runbook-Konformität

| Runbook expectation | Assessment |
|---|---|
| HERO_PRIMARY = selected instrument + decision narrative | PASS |
| HERO_LAYOUT 8/4 with critical system state | PASS |
| Compact metadata row (not KPI wall) | PASS |
| Chart materially above fold @ 1440×900 | PASS |
| No horizontal main scroll | PASS |
| No giant empty region above chart | PASS |
| Secondary engineering collapsed | PASS |
| Five-second operator summary | PASS |
| Chrome primary evidence | PASS |
| Safari not required for this gate | PASS (secondary only) |

Remaining MEDIUM items do not block Phase 2 visual exit criteria; they are polish / Phase-3-adjacent.

DESIGN_GATE=PASS
