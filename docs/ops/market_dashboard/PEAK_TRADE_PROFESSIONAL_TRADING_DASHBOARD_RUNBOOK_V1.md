# Peak_Trade — Professional Trading Dashboard Runbook V1

```text
DOCUMENT_CLASS=CANONICAL_DERIVED_DASHBOARD_PRODUCT_RUNBOOK
AUTHORITY_CLASSIFICATION=PLAN_AND_BOUNDARY_ONLY
DASHBOARD_AUTHORITY_EFFECT=NONE
DASHBOARD_CONSUMER_ONLY=true
MASTER_RUNBOOK_IS_SSOT=true
LANDSCAPE_MASTER_RUNBOOK_V2_SUPERSEDES=false
RUNTIME_AUTHORIZATION_EFFECT=NONE
CANONICAL_REPO_PATH=docs/ops/market_dashboard/PEAK_TRADE_PROFESSIONAL_TRADING_DASHBOARD_RUNBOOK_V1.md
WP_ID=PROFESSIONAL_TRADING_DASHBOARD_RUNBOOK_V1_CANONICALIZATION
BASELINE_ORIGIN_MAIN_SHA=422b27305970a83f73b886cd7ab6f5db2180fa08
ATLAS_AUTHORITY=NONE
```

**Status:** Canonical product/architecture runbook (P0 ratification target)  
**Scope:** Market Dashboard Landscape V2 → Professional Read-Only Trading Workstation  
**Baseline:** `origin/main@422b27305970a83f73b886cd7ab6f5db2180fa08`  
**Authority:** Dashboard `AUTHORITY=NONE`; read-only visual consumer  
**Reference class:** Professional trading workstations such as OKX/Kraken Pro — reference class only, not a visual clone.

**Relationship (navigation only):** This runbook specializes the existing Landscape V2 read-only consumer toward a professional operator workstation. It does **not** supersede `docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md` (operational SSOT) or replace the historical consumer-closeout record in `docs/ops/market_dashboard/PEAK_TRADE_MARKET_DASHBOARD_LANDSCAPE_MASTER_RUNBOOK_V2.md`.

## 1. Mission

Transform the current Market Dashboard Landscape V2 from an engineering/status-oriented page into a professional, dense, operator-first trading workstation while preserving Peak_Trade's existing authority model and fail-closed semantics.

The target experience is:

`Chrome bookmark → localhost dashboard → immediately usable professional trading view`

No Cursor or terminal is required for normal viewing. The dashboard never becomes a trading authority and never sends orders.

## 2. Non-negotiable architecture

Data flow remains one-way:

`CURRENT Peak_Trade System → canonical/read-only outputs → dashboard binding/adapter → presentation → UI`

Never:

`Dashboard → Trading System`

Permanent invariants:

- `DASHBOARD_AUTHORITY=NONE`
- `DASHBOARD_CONSUMER_ONLY=true`
- no ranking/reselection
- no domain recomputation
- no trading/risk/safety/execution/learning/sizing/capital authority
- no writer/rewire/feedback path
- no invented fallback/default/confidence
- `MISSING_SOURCE`, `STALE`, `NOT_BOUND` remain fail-closed facts
- synthetic data is allowed only in isolated preview/test fixtures
- every repository PR includes factual Atlas updates with `ATLAS_AUTHORITY=NONE`

## 3. Product target

The dashboard shall feel like a professional trading workstation rather than a report or engineering diagnostics page.

### 3.1 Primary operator hierarchy

**Top market strip**
- Selected instrument
- mark/last price
- change
- Bull/Bear State Switch
- Master V2 / canonical decision
- Double Play state
- blockers
- aggregate source health

**Main workspace**
- Left rail: TOP-20 universe/ranking
- Center: dominant professional candlestick + volume chart
- Right rail: Peak_Trade Decision Panel

**Decision Panel**
- current scope
- regime
- Bull/Bear/Switch
- canonical decision
- Double Play
- blockers
- Risk / Sizing / Capital
- Safety

**Lower telemetry**
- Execution / Reconciliation
- Economic
- Source/Freshness health

**Engineering detail**
- collapsed by default
- source refs, schemas, IDs, digests, paths, projection/slot matrices, diagnostics and governance detail

## 4. Professional chart standard

The chart is the visual center of gravity and should consume roughly 60–70% of the primary workspace where practical.

Required presentation capabilities, subject to existing canonical data:
- candlesticks
- volume
- price axis
- time axis
- grid
- OHLC header
- interval
- current/last mark
- responsive scaling
- contained labels
- crosshair/tooltip interaction where implementable without changing domain authority
- no synthetic production values

The chart must use the existing read-only OHLCV path. UI enhancement must not create a second market-data authority.

## 5. Density and layout rules

- No unexplained hero whitespace.
- No card-wall design.
- No raw technical strings dominating operator view.
- No page-level horizontal overflow.
- Long IDs/reasons/paths must be contained; full value remains available in engineering detail.
- TOP-20 remains ordered exactly as supplied by the readmodel.
- Degraded states use the same stable grid as healthy states.
- `MISSING_SOURCE` remains visible but must not destroy the workstation layout.
- Desktop reference viewport: 1440×900.
- Narrow viewport guards remain required.

## 6. Current source reality

```text
CENSUS_EPISTEMIC_CLASS=FORENSIC_OPERATOR_LOCAL_AT_RATIFICATION_BASELINE
CENSUS_NOT_CONSUMER_CLOSEOUT_CENSUS=true
CONSUMER_CLOSEOUT_CENSUS=docs/ops/market_dashboard/MARKET_DASHBOARD_LANDSCAPE_V2_CURRENT_COMPLETION_CENSUS_V1.md
OWNER_REGISTRY=src/webui/market_dashboard_landscape_v2/owner_registry.py
```

Current forensic census established (operator-local binding/freshness at ratification baseline; distinct from consumer-closeout COMPLETE regions):

- 13 owner-relevant surfaces
- 1 fresh/available: OHLCV
- 4 stale: Universe/Ranking, Market Identity, Dynamic Scope, Canonical Decision
- 6 missing-source: Regime, Double Play, Risk/Sizing/Capital, Execution/Reconciliation, Economic, Safety
- 2 intentional NOT_BOUND: Autonomy, Diagnostics

The dashboard consumer is fail-closed and is not the primary cause of these gaps.

Primary upstream causes:
1. presentation/materializer pipeline not operationally invoked,
2. missing durable dashboard projections,
3. stale July/August exports,
4. intentionally unbound capabilities.

## 7. Delivery program

### Phase P0 — Runbook ratification
Adopt this document as the bounded product/architecture target. No implementation in the ratification step beyond required governance/navigation updates.

**Exit:** Owner confirms target architecture and visual standard.

### Phase P1 — Professional Workstation Preview V2
Create isolated FULL and DEGRADED previews at 1440×900.

Preview must demonstrate:
- exchange-class density and hierarchy,
- dominant professional chart,
- compact TOP-20 rail,
- Peak_Trade Decision Panel replacing an exchange order-entry panel,
- compact lower telemetry,
- collapsed engineering detail,
- stable degraded layout.

No repository/runtime mutation.

**Exit:** Owner visually approves preview.

### Phase P2 — Presentation Implementation
One bounded presentation PR implementing the approved V2 composition.

Allowed:
- template/CSS/presentation-only helpers
- chart presentation enhancements using existing OHLCV
- tests/docs/Atlas

Forbidden:
- source repair
- new producer
- new authority
- synthetic runtime values
- domain recomputation

**Exit:** real dashboard matches approved preview closely in healthy/degraded fixtures; existing bindings unchanged.

### Phase D1 — Regime + Double Play projection
Materialize existing CURRENT decision/domain evidence into durable read-only dashboard projections.

**Exit:** S04/S06 no longer `MISSING_SOURCE` when valid CURRENT evidence exists.

### Phase D2 — Operational materializer invocation
Create a governed, bounded read-only invocation path for required presentation materializers.

No trading/execution effects.

**Exit:** projections refresh without Cursor/manual developer workflow.

### Phase D3 — Fresh Universe / Scope / Decision
Refresh stale CURRENT readmodels through canonical governed producers. Do not relabel old timestamps.

**Exit:** stale quartet becomes fresh only when genuinely regenerated.

### Phase D4 — Risk / Execution / Economic / Safety
For each family, prove canonical upstream source and create only the minimum durable read-only projection required by the dashboard.

May be one bounded PR only if dependency census proves common mechanics and independent semantics; otherwise split.

**Exit:** each surface is either genuinely AVAILABLE/FRESH or remains explicitly fail-closed with a proven reason.

### Phase V — Final owner acceptance
Validate the real localhost dashboard through the Chrome bookmark.

Required:
- professional workstation composition
- no large dead areas
- real chart
- correct TOP-20 order
- decision/DP/regime visible when sourced
- risk/capital/safety visible when sourced
- degraded state stable
- engineering detail secondary
- no invented values
- no dashboard authority
- autostart/bookmark still works

## 8. PR and owner-gate discipline

For every implementation slice:
1. pin `origin/main`
2. perform bounded census before mutation where dependencies are uncertain
3. one PR at a time
4. factual Atlas update in the same PR
5. all required checks terminal green
6. no admin bypass
7. final diff identity and scope verification
8. stop before merge
9. merge only after explicit `OWNER_MERGE_GO`
10. squash merge

If a slice discovers an `UNKNOWN` that could affect authority, semantics, producer ownership, or deletion safety, stop rather than infer.

## 9. Acceptance criteria

The program is complete only when all are true:

- `READY_FOR_ONE_CLICK_DASHBOARD=true`
- `PROFESSIONAL_WORKSTATION_LAYOUT=true`
- `LARGE_EMPTY_HERO_SPACE=false`
- `CHART_DOMINANT_AND_PROFESSIONAL=true`
- `TOP20_ORDER_PRESERVED=true`
- `DECISION_PANEL_OPERATOR_FIRST=true`
- `ENGINEERING_DETAIL_SECONDARY=true`
- `DEGRADED_LAYOUT_STABLE=true`
- `DASHBOARD_CONSUMER_ONLY=true`
- `DASHBOARD_AUTHORITY=NONE`
- `DOMAIN_RECOMPUTATION=false`
- `SYNTHETIC_RUNTIME_VALUES=false`
- `RUNTIME_FALLBACK_ADDED=false`
- all displayed availability/freshness states derive from real read-only sources
- Chrome bookmark and LaunchAgent remain operational

## 10. Explicit non-goals

This runbook does not authorize:
- order entry from the dashboard
- changing Master V2 or Double Play decision authority
- changing ranking/selection authority
- enabling N>1
- changing live permits
- changing capital/risk authority
- inventing Autonomy or Diagnostics producers
- hiding source failures
- copying proprietary exchange UI pixel-for-pixel

## 11. Canonical next step

After Owner ratification:

`LANDSCAPE_V2_PROFESSIONAL_TRADING_WORKSTATION_PREVIEW_V2`

This is a preview-only step. Production implementation requires a separate `OWNER_GO`.
