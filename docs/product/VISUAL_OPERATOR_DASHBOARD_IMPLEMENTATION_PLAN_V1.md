# Visual Operator Dashboard — Implementation Plan v1

> **Status:** PLAN ONLY — `STOP_BEFORE_IMPLEMENTATION=true` for any further unrelated UI slice
> **Authority:** [Peak_Trade_Runbook_v1.3_Composition_Landmark_Master_Runbook.md](Peak_Trade_Runbook_v1.3_Composition_Landmark_Master_Runbook.md) (compatibility surface: [Peak_Trade_Visual_Operator_Dashboard_Product_Runbook_v1.3.md](Peak_Trade_Visual_Operator_Dashboard_Product_Runbook_v1.3.md))
> **Bootstrap GO:** `GO_PEAK_TRADE_VISUAL_OPERATOR_DASHBOARD_RUNBOOK_REPOSITORY_BOOTSTRAP_V1`
> **Next implementable slice:** awaiting post-dominance composition rebaseline (separate GO)
> **Authorized slice in flight / implemented:** `COMPOSITION_PRIMARY_PAGE_SHARE_DOMINANCE_V1`
> **Rebaseline evidence:** [composition_rebaseline_post_decision_compression_v1_20260717T004021Z](evidence/composition_rebaseline_post_decision_compression_v1_20260717T004021Z/)
> **After evidence:** [composition_primary_page_share_dominance_v1_20260717T004501Z](evidence/composition_primary_page_share_dominance_v1_20260717T004501Z/)
> **Branch context at original plan time:** `feat/market-dashboard-visual-operator-surface-v1` @ `20969b4…` · PR [#5244](https://github.com/rauterfrank-ui/Peak_Trade/pull/5244)

```text
CANONICAL_PRODUCT_SPEC=docs/product/Peak_Trade_Runbook_v1.3_Composition_Landmark_Master_Runbook.md
DOCUMENT_ROLE=DERIVED_IMPLEMENTATION_PLAN
MAY_NOT_OVERRIDE_RUNBOOK=true
IMPLEMENTATION_READY=true
STOP_BEFORE_IMPLEMENTATION=true
ONE_BOUNDED_PR_PER_SLICE=true
REUSE_BEFORE_NEW=true
NO_TRADING_SEMANTICS_EFFECT=true
NO_RUNTIME_AUTHORITY_EFFECT=true
```

Dieses Dokument ist abgeleitet und dem Product Runbook untergeordnet. Bei Widerspruch gilt ausschließlich das Runbook (PART I normativ; PART II technische Discovery-/Ist-Referenz; eigenständige Discovery-Exporte sind keine Produkt-SSOT).

---

## Preconditions (every slice)

1. `git fetch origin --prune`; record `HEAD`, `origin&#47;main`, worktree, PR state.
2. Re-verify Render Chain + Owner Matrix against repo (Runbook §0A / §0C).
3. Resolve open items from [RUNBOOK_PATCH_RECOMMENDATIONS.md](RUNBOOK_PATCH_RECOMMENDATIONS.md) that block the slice (especially R3/R4 for later phases).
4. Focused tests + screenshots + provenance; stop before merge.

---

## PHASE -1 / 0 — Discovery & baseline (docs/evidence)

| Field | Plan |
|-------|------|
| Goal | Durable inventories; no UI mutation |
| Affected files | `docs&#47;product&#47;*` companions; optional Phase -1 JSON/MD artifacts listed in Runbook §7; **no** `src/` / templates mutation |
| Owners | Product docs under `docs/product/`; technical chronicle `docs/webui/MARKET_SURFACE_V0.md` (pointer only) |
| Expected PR | Docs-only bootstrap / discovery closeout |
| Tests | Docs reference/token gates if docs paths change; no UI tests required for pure docs |
| Screenshots | Optional current full-page baseline (evidence only) |
| Risks | Treating Discovery SHAs as merge authority; dual SSOT with `MARKET_SURFACE_V0.md` (see R1) |

**Bootstrap status:** Product Runbook anchored; patch list + this plan created. Phase -1 JSON matrices still optional (R10).

---

## PHASE 1A — Compact Header + Chart above the fold

| Field | Plan |
|-------|------|
| Goal | Single safety rail; chart materially visible at 1440×900; close D1–D3/D6 partially |
| Affected files | `templates/peak_trade_dashboard/market_v0.html`; `partials&#47;market_visual_operator_header_v1.html`; `partials&#47;market_primary_operator_hero_v1.html`; `partials&#47;market_primary_close_chart_v1.html`; possibly compact F5 partial remove-from-hero; CSS classes in those templates only |
| Owners | Template partials above; context orchestration stays in `market_surface.py` / `market_visual_operator_surface_v1` (**reuse**, no new producers) |
| Expected PR | `feat(webui): compact visual operator header and chart-above-fold (1A)` |
| Tests | Geometry / duplicate-status / structure contracts — extend `tests/webui/test_market_visual_operator_surface_v1.py`, `test_market_dashboard_readonly_structure_contract_v0.py`, `test_market_terminal_layout_v1.py`, `test_market_dashboard_responsive_polish_v1.py` as needed |
| Screenshots | 1440×900 header+hero+chart; full page desktop; no dual rails |
| Risks | Accidental semantic change to safety/decision values; breaking IA v2 markers; large empty region regressions |

**Forbidden:** data producer changes; trading/risk/authority semantics; new parallel render chain.

---

## PHASE 1B — Design tokens, grid, vendorized assets

| Field | Plan |
|-------|------|
| Goal | Central token owner; remove Tailwind/Chart.js CDN from target path; responsive grid |
| Affected files | New or existing central CSS/token surface (prefer extend existing static/CSS under dashboard, **no** second design system); `templates/peak_trade_dashboard/base.html`; asset bundle under `static/`; detail Chart.js script tags in DP/legacy partials |
| Owners | `base.html` + static vendor tree; primary chart remains SSR SVG |
| Expected PR | `feat(webui): vendorize dashboard assets and bind design tokens (1B)` |
| Tests | Token uniqueness; network allowlist / no unexpected external requests; responsive grid contracts |
| Screenshots | Desktop / narrow / wide |
| Risks | Breaking Tailwind utility classes if CDN removed without local build; Chart.js detail charts blank without vendor path |

---

## PHASE 2 — Operator Overview / Decision Narrative

| Field | Plan |
|-------|------|
| Goal | Five-second summary; single decision sentence; critical system state compact |
| Affected files | `partials&#47;market_primary_operator_hero_v1.html`; `operator_header_display_v1.py` / visual surface context builders; possibly thin display adapters only |
| Owners | Display adapters in `market_visual_operator_surface_v1&#47;`; core decision owners unchanged |
| Expected PR | `feat(webui): operator overview decision narrative (phase 2)` |
| Tests | Decision sentence presence; content priority; no invented interpretation |
| Screenshots | Overview states (fresh / stale / missing / blocked) |
| Risks | Narrative that implies authorization or profitability |

---

## PHASE 3 — Chart polish

| Field | Plan |
|-------|------|
| Goal | Real candles/volume polish; tooltip metadata; stale overlay; instrument sync |
| Affected files | `partials&#47;market_primary_close_chart_v1.html`; narrow context fields from existing OHLCV builders |
| Owners | `market_futures_ohlcv_runtime_v0.py` (reuse); SSR SVG partial |
| Expected PR | `feat(webui): primary chart polish real-data overlays (phase 3)` |
| Tests | Real-data only; no synthetic bars; gap/stale/missing overlays |
| Screenshots | Fresh / stale / missing |
| Risks | Synthetic fallback temptation; client Chart.js reintroduction on primary |

---

## PHASE 4A — Ranking data contract

| Field | Plan |
|-------|------|
| Goal | Sparse-field policy; stable sort/tie-break; hide data-blocked columns |
| Affected files | Ranking readmodel/runtime display mapping; possibly `market_ranking_funnel_runtime_v0.py` **display mapping only** if required — prefer template/contract first |
| Owners | `market_ranking_funnel_runtime_v0.py` / readmodel; `partials&#47;market_governed_top20_primary_v1.html` |
| Expected PR | `feat(webui): ranking sparse-field display contract (4A)` |
| Tests | Stable sort; Top20/50 distinct; unavailable not dominant |
| Screenshots | Data-state samples |
| Risks | Inventing Rank Delta / Regime without producer (explicitly forbidden) |

---

## PHASE 4B — Ranking visual surface

| Field | Plan |
|-------|------|
| Goal | Single canonical ranking component; overflow-safe; score visuals |
| Affected files | `partials&#47;market_governed_top20_primary_v1.html`; watchlist partial as nav aid only |
| Owners | Same ranking owners; **no** second ranking component |
| Expected PR | `feat(webui): ranking visual density and overflow guards (4B)` |
| Tests | Overflow DOM assertions; Top20/50; selection marker |
| Screenshots | Top20 / Top50 / narrow |
| Risks | Duplicate ranking UIs; horizontal scroll |

---

## PHASE 4C — Selection context binding

| Field | Plan |
|-------|------|
| Goal | Atomic `selection_context_id` + snapshot identity across surfaces |
| Affected files | `src/webui/market_surface.py`; `market_visual_operator_surface_v1&#47;*` context builders; templates consuming context IDs |
| Owners | New digest helper colocated with visual surface package (**adapter only**); no core semantic owners |
| Expected PR | `feat(webui): atomic selection context and snapshot identity (4C)` |
| Tests | Atomic context; URL state; back/forward; mismatch fail-closed |
| Screenshots | Symbol switch coherence |
| Risks | Partial surface commit; fleet-level evidence looking instrument-scoped (must label) |

**Depends on:** R3 acceptance (document missing → implement).

---

## PHASE 5A — Activity state contract

| Field | Plan |
|-------|------|
| Goal | Remove bare misleading `ACTIVE`; evidence-required `PROCESSED` |
| Affected files | `decision_funnel_display_v1.py`; funnel/DP compact partials; related contracts |
| Owners | Display contracts only; Master V2 / Double-Play decision logic untouched |
| Expected PR | `feat(webui): decision activity state contract (5A)` |
| Tests | No bare ACTIVE; PROCESSED requires evidence; state enum coverage |
| Screenshots | All activity states |
| Risks | Changing decision semantics instead of labels |

---

## PHASE 5B — Funnel visual alignment

| Field | Plan |
|-------|------|
| Goal | Canonical stage order; selection-bound or explicitly `NOT_INSTRUMENT_SCOPED` |
| Affected files | `partials&#47;market_decision_funnel_visual_v1.html`; funnel context; DP compact labeling |
| Owners | Existing funnel display adapter |
| Expected PR | `feat(webui): decision funnel visual alignment and scope markers (5B)` |
| Tests | Stage order; scope markers; block reasons visible |
| Screenshots | Funnel / block states |
| Risks | Pretending baseline funnel is instrument-scoped |

---

## PHASE 6 — Risk / Safety compact

| Field | Plan |
|-------|------|
| Goal | Semantic groups; unambiguous no-authority; taxonomy `NOT_APPLICABLE`/`MISSING`/`STALE`/`INVALID` distinct |
| Affected files | `partials&#47;market_safety_compact_v1.html`; safety matrix / current-state display wiring |
| Owners | Existing safety matrix + current state snapshot (reuse derivation) |
| Expected PR | `feat(webui): risk safety compact semantics (phase 6)` |
| Tests | State taxonomy; authority ambiguity guards |
| Screenshots | No-position / missing / stale |
| Risks | Authority lift; conflating risk states visually |

---

## PHASE 7 — Economic visuals

| Field | Plan |
|-------|------|
| Goal | Scope/compatibility visible; negative/zero preserved; honest missing curves |
| Affected files | `partials&#47;market_economic_observability_visual_v1.html`; `economic_observability_display_v1.py` |
| Owners | Existing economic display adapter + baseline evidence |
| Expected PR | `feat(webui): economic observability visuals with scope labels (phase 7)` |
| Tests | Negative/zero preservation; scope compatibility; no profitability overclaim |
| Screenshots | Fail / zero / missing curves |
| Risks | Implying instrument-matched economic truth for fleet baseline |

---

## PHASE 8 — AI / Linear diagnostics

| Field | Plan |
|-------|------|
| Goal | Summary in Level 2; details Level 3; no giant empty cards |
| Affected files | `partials&#47;market_ai_linear_diagnostics_visual_v1.html`; `ai_linear_diagnostics_display_v1.py`; diagnostics drawer |
| Owners | Existing linear diagnostics adapter |
| Expected PR | `feat(webui): linear diagnostics summary detail split (phase 8)` |
| Tests | Summary/detail separation; explicit missing |
| Screenshots | Summary + expanded |
| Risks | Overclaiming model authority |

---

## PHASE 9 — Governance consolidation

| Field | Plan |
|-------|------|
| Goal | Engineering/governance collapsed by default; operator-first primary flow |
| Affected files | `partials&#47;market_current_state_compact_v1.html`; `market_diagnostics_drawer_v1.html`; legacy panels placement in `market_v0.html` |
| Owners | Existing collapsed current-state / drawer patterns |
| Expected PR | `feat(webui): collapse governance engineering details (phase 9)` |
| Tests | Collapsed default; no raw JSON default in primary |
| Screenshots | Collapsed / expanded |
| Risks | Hiding required safety visibility (keep Level-1 safety rail intact) |

---

## PHASE 10 — Demo readiness

| Field | Plan |
|-------|------|
| Goal | Chrome/Playwright (`channel=chrome`) primary evidence; Safari/WebKit secondary only; console clean; visual regression; network allowlist zero; a11y basics |
| Affected files | Browser test infra / evidence dirs; possibly small polish only |
| Owners | New or extended browser harness under `tests/webui/` (reuse structure contracts first; add E2E owner only if missing — closes R6) |
| Expected PR | `test(webui): visual operator demo readiness evidence (phase 10)` |
| Tests | Visual regression, console, network, a11y, five-second checklist evidence |
| Screenshots | Full §10 matrix |
| Risks | Claiming WebKit == real Safari; merge with open blockers |

---

## Cross-cutting PR rules (all phases)

```text
ONE_BOUNDED_PR=true
STOP_BEFORE_MERGE=true
FOCUSED_TESTS_REQUIRED=true
VISUAL_SCREENSHOTS_REQUIRED=true
SOURCE_MANIFEST_VERIFY_REQUIRED=true
IMPLEMENTATION_MANIFEST_REQUIRED=true
TRADING_SEMANTICS_EFFECT=NONE
RUNTIME_EFFECT=NONE
AUTHORITY_EFFECT=NONE
```

## Explicit stop / authorized next slice

Phases 1A / 1B / 2 composition foundation work is already evidenced under `docs&#47;product&#47;evidence&#47;phase_*` and must not be re-opened as the next step. The post-PR#5257 Chrome full-page rebaseline authorizes exactly one next presentation slice:

```text
IMPLEMENTED_SLICE=COMPOSITION_PRIMARY_PAGE_SHARE_DOMINANCE_V1
IMPLEMENTED_SLICE_EVIDENCE=docs/product/evidence/composition_primary_page_share_dominance_v1_20260717T004501Z/
IMPLEMENTED_SLICE_SCOPE=templates/CSS presentation only; reuse existing ViewModels; no data-contract or authority changes
BASELINE_EVIDENCE=docs/product/evidence/composition_rebaseline_post_decision_compression_v1_20260717T004021Z/
PRIOR_SLICE=COMPOSITION_DECISION_SURFACE_VERTICAL_COMPRESSION_V1
NEXT_SLICE=AWAITING_POST_DOMINANCE_REBASELINE
STOP_BEFORE_NEXT_UNRELATED_SLICE=true
```

### Before / after measured (1440×900, real Chrome)

| Metric | Post-compression baseline | After dominance slice | Target |
|---|---:|---:|---:|
| PRIMARY_MARKET_SURFACE page share | 34.2% | 38.9% | ≥ Decision + 2 pp |
| DECISION_SURFACE page share | 39.1% | 32.7% | ≤ 34% |
| DECISION_SURFACE height | 1006 px | 790 px | ≤ 850 |
| OBSERVABILITY_SURFACE start Y | 2007 | 1848 | ≤ 1850 |
| PRIMARY chart viewport share | ≥40% | 50.0% | ≥ 40% |
| Horizontal overflow | 0 | 0 | 0 |

