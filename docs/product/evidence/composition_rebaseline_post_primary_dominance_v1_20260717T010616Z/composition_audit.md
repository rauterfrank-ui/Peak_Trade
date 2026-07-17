# Composition Audit — Post Primary-Dominance Rebaseline

Captured: `20260717T010616Z`
HEAD baseline: PR #5260 merge `1705bba16dcbe76aa1f4b3a06f132cd4a5a65c45`
Browser: Google Chrome · REAL_CHROME_VERIFIED=true · CHROMIUM_FALLBACK_USED=false
Path: `/market?timeframe=1h` via readonly visual-operator bundles
Viewports: 1440×900, 1280×800, 1728×1117
Mode: evidence-only rebaseline (then slice implementation on feature branch)

## Executive verdict

PR #5260 **held**: Primary page share 38.9% > Decision 32.7% (+6.2 pp), Decision height 790, Observability start Y 1848, chart viewport share ≥40%, landmark order/overflow/Engineering secondary PASS.

Remaining full-page composition tension is no longer mass inversion. The largest open composition defect is **missing intentional inter-landmark breathing**: Primary→Decision gap is only **2 px** (stages abut), Decision→Observability 12 px. After Primary dominance, stages still read as abutting slabs rather than discrete bands.

## Aggregate gates (post-merge, populated offline bundles)

| Gate | Result |
|---|---|
| Landmark order | PASS |
| Horizontal overflow | PASS |
| Primary chart dominance (≥40% VP) | PASS (~62%) |
| Primary ≥ Decision + 2 pp | PASS (38.9 vs 32.7) |
| Engineering secondary | PASS (closed, 0% VP) |
| Read-only / non-authorizing | Present |

## Measured gaps @1440×900 (BEFORE rhythm slice)

| Transition | Gap px |
|---|---:|
| Header → Primary | 5.6 |
| Primary → Decision | **2** |
| Decision → Observability | 12 |
| Observability → Engineering | 16 |

## Decision internals (unchanged by rebaseline)

Top-20 ~322 · Funnel ~233 · Secondary grid ~230 · bordered containers in Decision ≈16

## Root remaining composition gap

**Landmark vertical rhythm / fold transition air.** Mass hierarchy is correct; stage separation is not.
