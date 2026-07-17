# Composition Plan — PRIMARY_PAGE_SHARE_DOMINANCE_V1

## Full-page analysis (BEFORE @1440×900, Chrome)

| Landmark | Height | Page share | Role |
|---|---:|---:|---|
| GLOBAL_HEADER | 67 | 2.6% | Context |
| PRIMARY_MARKET_SURFACE | 880 | **34.2%** | Market stage (not yet #1 by mass) |
| DECISION_SURFACE | 1006 | **39.1%** | Heaviest landmark |
| OBSERVABILITY_SURFACE | 290 | 11.3% | Third band |
| ENGINEERING_DRAWER | 146 | 5.7% | Collapsed secondary |

Decision internals: Top-20 ~399 · Funnel ~307 · Secondary grid ~293.

## Intent

Flip full-page mass so Primary is unambiguously #1 (≥ Decision + 2 pp), while chart remains the strongest above-fold focus and Decision stays clearly secondary.

## Allowed levers (presentation only)

1. **Decision secondary densify** — funnel stages / suitability / block-reasons + secondary 3-panel matrices (primary lever).
2. **Primary chart stage grow** — raise chart floor/clamp so hero+chart read as one dominant stage (absolute Primary mass).
3. **Modest Top-20 viewport window** — lower matrix max-height token only (no eligibility/semantics change).

## Targets @1440×900

| Metric | Before | Target |
|---|---:|---:|
| PRIMARY page share | 34.2% | ≥ Decision + 2 pp |
| DECISION page share | 39.1% | ≤ 34% |
| DECISION height | 1006 | ≤ 850 |
| OBS start Y | 2007 | ≤ 1850 |
| Chart VP share | ≥40% | no regression below 40% |
| Landmark order / overflow | PASS | PASS |

## Explicit non-goals

No business logic, SSOT, Master V2, Double Play semantics, producers, APIs, builder, contracts, Python runtime behavior.
