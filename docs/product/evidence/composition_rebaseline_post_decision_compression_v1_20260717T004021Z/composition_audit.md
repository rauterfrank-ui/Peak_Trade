# Composition Audit — Post Decision-Compression Rebaseline

Captured: `2026-07-17T00:40:21Z` (dir stamp)
HEAD: `8fa865061e671d065e93ad5619ce263b91c46fee`
Branch: `main`
Browser: Google Chrome · `REAL_CHROME_VERIFIED=true` · `CHROMIUM_FALLBACK_USED=false`
Path: `/market?timeframe=1h`
Viewports: `1440×900`, `1280×800`, `1728×1117`
Mode: evidence-only · no code changes

## 1. Executive verdict

The Decision-compression slice **held**: page height −805 px, Decision share 53.4% → 39.1%, Observability start Y 2812 → 2007, chart dominance unchanged (~55% viewport). Landmark order, alignment, overflow, and Engineering secondary posture remain clean.

Remaining full-page composition tension: **Decision is still the heaviest landmark by page share** (39.1% vs Primary 34.2%). Observability remains a second-scroll destination (~2.2× viewport). Above the fold, Primary Chart is the clear focal stage; below the fold, Decision still forms the longest reading block.

## 2. Aggregate gates

| Gate | Result |
|---|---|
| Landmark order | PASS |
| Horizontal overflow (all VPs) | PASS (`0` px) |
| Primary chart dominance (≥40% viewport) | PASS (51.7–62.3%) |
| Engineering secondary (<15% initial viewport) | PASS (`0%`) |
| Console / page / failed / external | `0` / `0` / `0` / `0` |
| Read-only / live-locked / non-authorizing / authority=false | Present |
| Decision compression marker | Present |

## 3. Measured landmark geometry (1440×900)

| Landmark | Start Y | Height px | Page share | Role |
|---|---:|---:|---:|---|
| GLOBAL_HEADER | 32 | 67 | 2.6% | Context / authority strip |
| PRIMARY_MARKET_SURFACE | 105 | 880 | **34.2%** | Market stage |
| DECISION_SURFACE | 989 | 1006 | **39.1%** | Decision stage (still largest) |
| OBSERVABILITY_SURFACE | 2007 | 290 | 11.3% | Economics / diagnostics |
| ENGINEERING_DRAWER | 2313 | 146 | 5.7% | Collapsed secondary |

Page height: **2572 px** (was 3377).

### Cross-viewport shares

| Viewport | Primary % | Decision % | Observability % | Obs start Y | Chart VP % | Competing focus |
|---|---:|---:|---:|---:|---:|---:|
| 1440×900 | 34.2 | **39.1** | 11.3 | 2007 | 55.4 | 2 (hero+chart) |
| 1280×800 | 34.3 | **39.9** | 10.9 | 2093 | 62.3 | 2 |
| 1728×1117 | 35.3 | **38.5** | 11.1 | 2051 | 51.7 | 4 |

## 4. Criterion scores

### 4.1 Visuelle Hierarchie der fünf Landmarks

**Score: Strong structure / mild weight inversion**

Order is correct and readable: Header → Primary → Decision → Observability → Engineering. Hierarchy by *position* is clear. Hierarchy by *full-page mass* still slightly favors Decision over Primary. Engineering correctly terminates as the lightest interactive stage.

### 4.2 Dominanz der Primary Market Surface

**Score: Strong above fold / contested on full page**

- Chart ≈55% of initial viewport @1440; hero ~12% of Primary; chart ~57% of Primary.
- Above fold: single dominant stage (chart), hero as companion — not a second peer stage.
- Full page: Primary 34.2% < Decision 39.1% → Primary is not yet the heaviest scroll block.

### 4.3 Vertikale Rhythmik

**Score: Adequate, slightly compressed between stages**

Inter-landmark gaps @1440: Header→Primary **5.6 px**, Primary→Decision **4 px**, Decision→Observability **12 px**, Observability→Engineering **16 px**. Rhythm is consistent but tight; stages abut more than they breathe. No large empty voids.

### 4.4 Weißraumverteilung

**Score: Internal density > inter-stage air**

Whitespace is mostly *inside* modules (matrix cells, funnel stages) rather than between landmarks. Decision still packs Matrix + Funnel + secondary 3-panel grid. Observability has more internal emptiness (NOT_COMPUTED placeholders) than structural air — feels sparse in content, not spacious by design.

### 4.5 Scan-Pfad des Operators

**Score: Clear Z/top-down above fold; Decision wall after first scroll**

Expected path: Header authority cues → Hero (symbol/price) → Chart (primary read) → Decision tip → Matrix/funnel → Observability → Engineering.

@1440: Decision starts at Y≈989 (just below fold) — first scroll immediately enters Decision. Observability requires ~2.2 scrolls. Engineering never competes above fold (0% viewport share).

### 4.6 Balance Decision vs Observability

**Score: Improved vs pre-slice; still Decision-heavy**

Decision:Observability page-share ≈ **3.5:1** (39.1 vs 11.3). Pre-slice was worse (~6.2:1 at 53.4 vs 8.6). Observability is no longer buried at Y≈2812, but remains a late secondary destination rather than a balanced counterpart.

### 4.7 Gewicht des Engineering Drawers

**Score: Correct / secondary**

Collapsed, ~146 px, ~5.7% page, **0%** initial viewport, drawer closed. Does not compete with Primary or Decision.

### 4.8 Alignment aller Landmark-Blöcke

**Score: Excellent**

Left edge spread **0 px**, width spread **0 px** (all landmarks 16 → 1408 @1440). Full-bleed column alignment is compositionally clean.

### 4.9 Verhältnis Hero / Chart / Decision Surface

| Ratio | Value @1440 |
|---|---:|
| Hero / Primary | 12.1% |
| Chart / Primary | 56.7% |
| Chart / Viewport | 55.4% |
| Primary / Page | 34.2% |
| Decision / Page | 39.1% |
| Decision / Primary (height) | 1.14× |

Hero correctly subordinates to chart. Decision still outmasses Primary on the page (~1.14× height).

### 4.10 Focal Points

Above fold @1440: **2** competing focus regions (hero + primary_chart) — acceptable; chart wins by area. @1728: **4** (taller viewport pulls Decision tip into competition). No Engineering focal leak. Full-page secondary focals: SYSTEM DECISION / Blocked block, Top-20 matrix, funnel bar — intentional Decision internals, but collectively prolong the Decision stage.

### 4.11 Informationsdichte

**Score: High inside Decision; Primary appropriate; Observability sparse**

Primary density matches a market stage. Decision remains the densest landmark (matrix rows + funnel stages + watchlist/Double-Play/safety tiles). Observability shows low *filled* density (placeholders / MISSING_SOURCE) which reads as unfinished rather than calm.

### 4.12 Lesefluss

**Score: Good until mid-Decision; then tabular fatigue**

Flow Header→Hero→Chart is smooth. Entering Decision, the Blocked summary is a strong verbal anchor; Top-20 then Funnel then secondary grid force a long tabular read before Observability. Compression reduced the wall height but not the *sequence length* of Decision sub-modules.

## 5. Delta vs pre-compression rebaseline

| Metric | Before | After slice / now | Delta |
|---|---:|---:|---:|
| Page height | 3377 | 2572 | −805 |
| Decision height | 1803 | 1006 | −797 |
| Decision page share | 53.4% | 39.1% | −14.3 pp |
| Primary page share | 26.1% | 34.2% | +8.1 pp |
| Observability start Y | 2812 | 2007 | −805 |
| Chart viewport share | 55.4% | 55.4% | 0 |

Slice acceptance targets (≤1350 px Decision, ≤40% share, Obs Y ≤2200) remain **met**.

## 6. Root remaining composition gap

**Full-page Primary vs Decision mass balance.** Decision is still ~5 pp heavier than Primary and still the longest continuous scroll stage. Secondary Decision modules (funnel + compact grid) are the main residual vertical consumers after Top-20 densification.

Non-defects (do not prioritize): Chrome harness, Engineering secondary posture, horizontal overflow, above-fold chart dominance, landmark order/alignment.

## 7. Screenshot evidence index

- `screenshots/full_page_1440x900.png`
- `screenshots/full_page_1280x800.png`
- `screenshots/full_page_1728x1117.png`
- `screenshots/viewport_1440x900.png`
- `screenshots/viewport_1280x800.png`
- `screenshots/viewport_1728x1117.png`
- Geometry: `composition_geometry.json`
- Browser: `browser_report.json`
