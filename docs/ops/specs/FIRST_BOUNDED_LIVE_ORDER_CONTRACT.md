# First Bounded Live Order Contract

status: DRAFT
last_updated: 2026-03-14
owner: Peak_Trade
purpose: Canonical contract for the first bounded real-money order path (wrapper → runner → exchange)
docs_token: DOCS_TOKEN_FIRST_BOUNDED_LIVE_ORDER_CONTRACT

## 1. Intent

This document defines the **single end-to-end contract** for the first bounded live order. It fixes the semantics for the first real order attempt and serves as the canonical reference before runtime enablement.

It does **not** authorize execution. It documents the agreed path and semantics.

## 2. Load-Bearing Needs

- kleinster echter bounded Live-Order-Pfad
- explizite Invocation vom Wrapper/Runner bis Exchange
- getrennte Live-Credentials und Config-Pfad
- klar begrenzter Order-Scope
- explizite Abort/NO_TRADE-Semantik
- ausreichende Evidence/Telemetry für den ersten echten Order-Versuch

## 3. Invocation Path

```
run_bounded_pilot_session.py (Gates GREEN)
  → run_execution_session.py --mode bounded_pilot [--steps N]
    → LiveSessionRunner.from_config(mode=bounded_pilot)
      → ExecutionPipeline (env=LIVE, bounded_pilot_mode=True)
        → ExchangeOrderExecutor + KrakenLiveClient
          → Kraken REST AddOrder
```

## 4. Credentials and Config

- **Credentials:** KRAKEN_API_KEY, KRAKEN_API_SECRET (ENV only)
- **Config:** [exchange.kraken_live] in config.toml
- **Factory:** build_trading_client_from_config when exchange.default_type="kraken_live"

## 5. Order-Scope

- One strictly operator-supervised pilot session
- Bounded by configured caps (exposure_state.caps_configured)
- Kill switch posture explicit
- Ambiguity posture NO_TRADE

## 6. Abort / NO_TRADE

Entry must not occur, or must be aborted immediately, if:

- pilot go/no-go != GO_FOR_NEXT_PHASE_ONLY
- kill switch active
- policy blocked
- any ambiguity about whether trading is allowed

**Rule:** ambiguity => NO_TRADE / safe stop

## 7. Evidence / Telemetry

- Live session registry (run_id, status, config, metrics)
- strategy_risk_telemetry (exposure gauge)
- trade_flow_telemetry (signals, orders blocked/approved)
- execution_events (order_submit, fill, order_reject)

## 8. Relationship

- Companion to: BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT
- Companion to: BOUNDED_PILOT_LIVE_ENTRY_GAP_NOTE
- Companion to: BOUNDED_PILOT_LIVE_ORDER_EXECUTION_DECISION_PACKAGE
- Source: first_bounded_live_order_path_review

## 9. Non-Goals

- No execution authority
- No code change (docs-only)
- No bypass of gates
