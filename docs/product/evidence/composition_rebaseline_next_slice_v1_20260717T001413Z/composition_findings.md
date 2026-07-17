# Composition Findings — Full-Page Rebaseline

Captured: `2026-07-17T00:15:57Z`
HEAD: `b113ef57d5f2995dc43afdec6f5e9c40c8563e41`
Browser: `GOOGLE_CHROME` · `REAL_CHROME_VERIFIED=True` · `CHROMIUM_FALLBACK_USED=False`
Path: `/market?timeframe=1h`
Viewports: `1440x900`, `1280x800`, `1728x1117`

## Aggregate gates

| Gate | Result |
|---|---|
| Landmark order | `True` |
| Horizontal overflow | `True` |
| Primary chart dominance (viewport ≥40%) | `True` |
| Engineering secondary | `True` |
| Console / page / failed / external | `0` / `0` / `0` / `0` |

## Measured landmark geometry (1440×900)

| Landmark | Start Y | End Y | Height px | Page share |
|---|---:|---:|---:|---:|
| GLOBAL_HEADER | 32 | 99 | 67 | 2.0% |
| PRIMARY_MARKET_SURFACE | 105 | 985 | 880 | 26.1% |
| DECISION_SURFACE | 997 | 2800 | 1803 | **53.4%** |
| OBSERVABILITY_SURFACE | 2812 | 3102 | 290 | 8.6% |
| ENGINEERING_DRAWER | 3118 | 3264 | 146 | 4.3% |

Page height: **3377 px**.

### Viewport metrics (all three)

| Viewport | Chart share of viewport | Chart share of primary | Eng share initial | Overflow px | Competing focus |
|---|---:|---:|---:|---:|---:|
| 1440×900 | 55.4% | 56.7% | 0.0% | 0 | 2 (chart+hero) |
| 1280×800 | 62.3% | 54.7% | 0.0% | 0 | 2 |
| 1728×1117 | 51.7% | 62.5% | 0.0% | 0 | 2 |

## Forensic answers

1. **Landmark order correct?** Yes — GLOBAL_HEADER → PRIMARY → DECISION → OBSERVABILITY → ENGINEERING on all viewports.
2. **More than one competing primary focus?** Soft yes above the fold: chart dominates, hero is secondary companion (2 focus points). No third peer-stage.
3. **Market chart dominant stage?** Yes above the fold (≥51% viewport share). Full-page narrative is weakened by Decision wall.
4. **Blickführung Header → Primary → Decision → Observability?** Partially. Header→Primary is clear; Decision consumes ~53% of page height and pushes Observability to Y≈2812.
5. **Engineering closed/secondary?** Yes — 0% of initial viewport; collapsed drawer height ~146 px at page bottom.
6. **Large unjustified empty regions?** No large inter-landmark gaps (>48 px) measured.
7. **Horizontal overflow?** No (`overflow_px=0` all viewports).
8. **Clipped content?** No clipping detected in geometry/screenshots for primary path.
9. **Excessive vertical density?** Yes inside DECISION_SURFACE (Top20 matrix + funnel + 4-column secondary grid stacked).
10. **Unnecessary repetition?** Mild: readiness/read-only/authority cues repeated across header, hero sentence, and safety tiles — acceptable for fail-closed posture; not the primary defect.
11. **Visual claims without canonical data owner?** No new claims observed; offline bundle provenance visible on chart/matrix.
12. **Layout helpers acting as product surfaces?** Secondary grid remains inside DECISION_SURFACE (correct landmark binding); visual weight of helpers rivals Primary on full-page scroll.
13. **Read-only / live-locked / non-authorizing markers?** Present (`readonly`, `live-locked`, `non-authorizing`, `trading-authority=false`).
14. **Responsive hierarchy consistent?** Yes — same landmark order and Decision-dominance pattern across 1280/1440/1728.

## Root composition defect (largest gain)

**DECISION_SURFACE vertical over-dominance on the full page** (~50–54% of page height across viewports). This delays Observability, flattens landmark rhythm, and makes Secondary Decision modules feel like a second primary stage after scroll — even though above-the-fold Primary Chart dominance already passes.

## Explicit non-defects (do not prioritize next)

- Chrome/Playwright harness and real Chrome verification work.
- Engineering Drawer secondary posture already acceptable.
- Horizontal overflow already clean.
- Above-fold chart dominance already meets ≥40% share.
