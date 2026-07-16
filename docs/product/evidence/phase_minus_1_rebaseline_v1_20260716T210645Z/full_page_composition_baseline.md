# Full-page Composition Baseline (Phase -1)

```text
GO_TOKEN=GO_VISUAL_OPERATOR_DASHBOARD_RUNBOOK_V1_3_PHASE_MINUS_1_REBASELINE_V1
BASE_URL=http://127.0.0.1:8767
PATH=/market?timeframe=1h
PRIMARY_BROWSER=GOOGLE_CHROME
PRIMARY_PLAYWRIGHT_CHANNEL=chrome
REAL_CHROME_VERIFIED=true
PLAYWRIGHT_CHROMIUM_FALLBACK_USED=false
VIEWPORTS=1280x800,1440x900,1728x1117,1024x768
```

## Landmark order (document order / measured Y)

Observed marker sequence on `origin&#47;main` foundation:

1. GLOBAL_HEADER
2. SAFETY_RAIL
3. PRIMARY_MARKET_SURFACE (hero)
4. DECISION_NARRATIVE (inside hero; **Y above chart**)
5. PRIMARY_CHART
6. RANKING
7. DECISION_FUNNEL
8. ECONOMIC
9. AI_DIAGNOSTICS
10. ENGINEERING_GOVERNANCE (collapsed)
11. ENGINEERING_DRAWER (collapsed)

`LANDMARK_ORDER_MONOTONIC` against the probe list is **false** because Decision Narrative sits above the Chart inside the hero. That conflicts with the runbook eye-path:

```text
EXPECTED: MARKET → CHART → DECISION → BLOCKER → RANKING → …
OBSERVED: MARKET/HERO+DECISION → CHART → RANKING → …
```

## Qualitative assessment (1440×900)

| Check | Observation | Gate impact |
|---|---|---|
| Chart dominance | Chart visible and materially tall (`PRIMARY_CHART_VISIBLE_HEIGHT_PX≈498`) | numeric OK |
| Hero weight | Hero present (`210px`) with decision sentence + critical state | competing with chart for attention |
| Decision narrative | `NOTUSDT steht auf Rang 1. Regime unavailable. Decision Blocked. Primärer Blocker: Preflight blocked.` | present |
| Primary blocker | Critical system state surface present in hero | present |
| Focal points | Counted `2` (chart + narrative) | numeric OK |
| Badge density | Probe counted `0` prominent status badges with strict selector | numeric OK; qualitative badge risk remains in ranking/meta |
| Border/card density | `VISIBLE_CARD_LIKE_COUNT≈5` | composition debt |
| Engineering share | Level-4 details closed by default (`LEVEL4_VISIBLE_ELEMENT_COUNT=0`) | numeric OK |
| Horizontal overflow | `0` on all tested viewports | pass |
| Unexplained whitespace | Secondary grid + large ranking block create fragmented below-fold flow | fail composition gate |
| Eye path | Decision before chart | fail visual-flow gate |
| Level-4 default | closed | pass |
| Card-wall / debug-panel feel | Secondary F5/DP/safety/watchlist grid still reads admin-like | fail composition/UX acceptance |

## Screenshots

Under `browser&#47;screenshots&#47;`:

- `phase_minus_1_1280x800_{full,viewport}.png`
- `phase_minus_1_1440x900_{full,viewport}.png`
- `phase_minus_1_1728x1117_{full,viewport}.png`
- `phase_minus_1_1024x768_{full,viewport}.png`

Harness cross-check also under `harness_crosscheck&#47;` (`COMPOSITION_CONTRACT_PASS=true` for foundation numeric contract; product §§17–22 gates remain closed).

## Gate verdict (product contracts §§17–22)

```text
COMPOSITION_GATE_PASS=false
LANDMARK_GATE_PASS=false
UX_ACCEPTANCE_GATE_PASS=false
FULL_PAGE_REVIEW_PASS=false
```

Reason: eye-path inversion, missing explicit landmark attributes, mixed secondary grid, ranking dominance, residual card chrome. Numeric geometry baseline alone is insufficient for product gate pass.
