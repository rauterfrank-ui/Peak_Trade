# Canonical Integration Trace

Legend per stage: `BOUND` | `ACTIVATED` | `NOT_BOUND` | `BYPASSED` | `FAIL_CLOSED` | `NOT_APPLICABLE`

Authority tag: `CANONICAL_AUTHORITY` | `STRATEGY_INTENT_PRODUCER` | `INFORMATION_SOURCE` | `RISK_OR_COST_INPUT` | `CONSUMER_PROJECTION` | `NON_AUTHORITY` | `LEGACY_AUTHORITY` | `UNRESOLVED`

## Ehlers (`ehlers_cycle_filter`)

| Stage | Status | Tag |
|---|---|---|
| Market Data / Research Data | BOUND (OHLCV close for strategy; offline dataset binding for STEP29M) | INFORMATION_SOURCE |
| Feature Producer | BOUND (Super Smoother inside strategy) | INFORMATION_SOURCE |
| Strategy Producer | BOUND (`generate_signals` → 0/1) | STRATEGY_INTENT_PRODUCER |
| Adapter (signal binding / warmup) | BOUND (params/warmup in `strategy_signal_binding_v1`) | CONSUMER_PROJECTION |
| Canonical Market Context (MV2) | NOT_BOUND | NON_AUTHORITY |
| Dynamic Scope | NOT_BOUND | NON_AUTHORITY |
| Scope Event | NOT_BOUND | NON_AUTHORITY |
| transition_state / Dynamic Switch | NOT_BOUND | NON_AUTHORITY |
| Bull/Bear selected future | NOT_BOUND | NON_AUTHORITY |
| Agreement / Composition | BOUND_NOT_ACTIVATED (encoding class known; side NEUTRAL; not composite child by default) | CONSUMER_PROJECTION |
| CRS / Order Intent | NOT_BOUND | NON_AUTHORITY |
| Risk / Sizing | NOT_BOUND in runtime; offline STEP29M sizing policy for research eval only | NON_AUTHORITY |
| Quantity | NOT_BOUND | NON_AUTHORITY |
| Execution Eligibility | NOT_BOUND (`IS_LIVE_READY=False`) | FAIL_CLOSED / NON_AUTHORITY |
| Trade Intent | NOT_BOUND for live; offline backtest only if explicitly selected | NON_AUTHORITY |
| Execution Kernel | NOT_BOUND | NON_AUTHORITY |
| Observability / Reports | BOUND (R&D UI/presets, offline evidence) | NON_AUTHORITY |

**Chain verdict:** `RESEARCH_ONLY` (offline research binding COMPLETE with `authority_effect=NONE`; canonical MV2 chain NOT_BOUND).

## Bouchaud (`bouchaud_microstructure` / OHLCV proxy v1)

| Stage | Status | Tag |
|---|---|---|
| Market Data / Research Data | BOUND (OHLCV bars; optional bid/ask sizes) | INFORMATION_SOURCE |
| Feature Producer | BOUND (proxy pressure features; separate research matrix) | INFORMATION_SOURCE |
| Strategy Producer | BOUND (`generate_signals` → 0/1) | STRATEGY_INTENT_PRODUCER |
| Adapter | BOUND (warmup/params; STEP29M adapters) | CONSUMER_PROJECTION |
| Canonical Market Context (MV2) | NOT_BOUND | NON_AUTHORITY |
| Dynamic Scope | NOT_BOUND | NON_AUTHORITY |
| Scope Event | NOT_BOUND | NON_AUTHORITY |
| transition_state / Dynamic Switch | NOT_BOUND | NON_AUTHORITY |
| Bull/Bear selected future | NOT_BOUND | NON_AUTHORITY |
| Agreement / Composition | BOUND_NOT_ACTIVATED (encoding only; NEUTRAL) | CONSUMER_PROJECTION |
| CRS / Order Intent | NOT_BOUND | NON_AUTHORITY |
| Risk / Sizing | NOT_BOUND runtime; offline research cost binding modelled | NON_AUTHORITY |
| Quantity | NOT_BOUND | NON_AUTHORITY |
| Execution Eligibility | NOT_BOUND | FAIL_CLOSED / NON_AUTHORITY |
| Trade Intent | NOT_BOUND live | NON_AUTHORITY |
| Execution Kernel | NOT_BOUND | NON_AUTHORITY |
| Observability / Reports | BOUND (offline diagnostics / promotion research consumers) | NON_AUTHORITY |

**Chain verdict:** `RESEARCH_ONLY`.

## Master V2 / Double Play note

`docs/ops/specs/STRATEGY_TO_MASTER_V2_INTEGRATION_CONTRACT_V0.md` classifies both as `research-only`. No references under `src/trading/master_v2/` to either strategy id. Canonical system-state / direction / switch authority remains Master V2 / Double Play / Dynamic Scope / `transition_state` only.
