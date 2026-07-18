# Canonical Integration Trace (Master V2 / Double Play)

Authority baseline (unchanged): Master V2 / Double Play / Dynamic Scope / `transition_state` remain the only canonical system-state and switch authority.

## Shared chain template

For each real component, stages are marked:
`BOUND` | `ACTIVATED` | `NOT_BOUND` | `BYPASSED` | `FAIL_CLOSED` | `NOT_APPLICABLE`

Authority class: `Authority` | `Projection` | `Non-Authority` | `Consumer-only`

---

## A) `ElKarouiVolatilityStrategy` / `ElKarouiVolModel`

| Stage | Status | Notes |
|---|---|---|
| Source / Input | BOUND | OHLCV close → returns (when strategy invoked) |
| Producer | BOUND | `ElKarouiVolModel.regime_series` / strategy `generate_signals` |
| Adapter | NOT_BOUND | No Master V2 adapter consumes this as live producer |
| Canonical Market Context | NOT_BOUND | Not a MV2 market-context producer |
| Dynamic Scope | NOT_BOUND | Does not mutate scope |
| transition_state / Dynamic Switch | NOT_BOUND | No calls from `trading/master_v2` |
| Bull/Bear selected future | NOT_BOUND | |
| Agreement / Composition | NOT_BOUND (prod) / BOUND (encoding catalog) | Listed in agreement adapter encoding owners only; not active composition authority |
| Risk / Sizing | NOT_BOUND (MV2) | Local regime multipliers / vol scaling exist inside R&D model only |
| Quantity | NOT_BOUND | |
| Execution Eligibility | FAIL_CLOSED (live) | Class + tiering + R&D gates block live; registry metadata triangle is conflicting but Dual-source contracts treat as research-only |
| Trade Intent | NOT_BOUND | Not in execution kernel path |
| Execution Kernel | NOT_BOUND | No imports under `src/execution` |

**Authority class:** Non-Authority (relative to MV2). Strategy Intent only when explicitly run as R&D/backtest strategy.

**Chain status:** `NOT_BOUND` to canonical MV2; overall posture `RESEARCH_ONLY`.

---

## B) `ArmstrongCycleStrategy` / `ArmstrongCycleModel`

| Stage | Status | Notes |
|---|---|---|
| Source / Input | BOUND | Calendar date vs reference peak |
| Producer | BOUND | Phase → position map |
| Adapter | NOT_BOUND | |
| Canonical Market Context | NOT_BOUND | |
| Dynamic Scope | NOT_BOUND | |
| transition_state / Dynamic Switch | NOT_BOUND | |
| Bull/Bear selected future | NOT_BOUND | |
| Agreement / Composition | NOT_BOUND (prod) / BOUND (encoding catalog) | `armstrong_cycle` in POSITIONAL_LONG01 owners |
| Risk / Sizing | NOT_BOUND (MV2) | Local `risk_multipliers` in cycle model |
| Quantity | NOT_BOUND | |
| Execution Eligibility | FAIL_CLOSED (live) | Class `IS_LIVE_READY=False`; tiering `allow_live=false`; strategy-switch sanity treats as R&D |
| Trade Intent / Execution Kernel | NOT_BOUND | |

**Authority class:** Non-Authority for MV2. Research Strategy Intent when invoked offline.

---

## C) Legacy `ecm_cycle` (`src/strategies/ecm.py`)

| Stage | Status | Notes |
|---|---|---|
| Source / Input | BOUND | Date + close MA trend |
| Producer | BOUND | ENTRY (+1) / EXIT (-1) / 0 |
| Adapter | BOUND (catalog) | `ENTRY_EXIT_EVENT` owner in suitability agreement adapter |
| OBL_B05 side authority | FAIL_CLOSED / KEEP_NONE | `activation_slice_eligible=false`; `authority_source=NONE` |
| Dynamic Scope / transition_state | NOT_BOUND | |
| MV2 Bull/Bear | NOT_BOUND | |
| Curated config list | BOUND (name only) | Appears in `config/config.toml` strategy name lists — **config presence ≠ MV2 activation** |
| Execution | NOT_BOUND for live MV2 | Functional loader available for offline/demo scripts |

**Authority class:** Legacy Non-Authority specialist producer; not ratified side authority.

---

## D) Double Play suitability projection

| Item | Status |
|---|---|
| Field `StrategyMetadata.ecm_or_armstrong_surface` | Projection / Non-Authority |
| Use as suitability grant | FAIL_CLOSED — explicit message that ECM/Armstrong name alone cannot grant suitability |
| Live authorization flag on projection | `live_authorization=False` by construction |

---

## Summary
Neither El Karoui nor Armstrong components are bound into the productive Master V2 / Double Play system-state chain. They remain R&D/legacy strategy surfaces with optional offline research composition.
