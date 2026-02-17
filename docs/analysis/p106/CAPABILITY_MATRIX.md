# P106 — Execution Adapter Capability Matrix (paper/shadow only)

## Capabilities (v0)
- auth: api_key, oauth2
- markets: spot, margin, perp
- order_types: market, limit, stop, stop_limit, take_profit
- flags: post_only, reduce_only, ioc, fok
- leverage: set_leverage, isolated/cross
- position_mode: one_way/hedge
- ws: trades, orderbook, orders, fills
- limits: rate_limits_disclosed, order_rate_limit
- account: subaccounts, portfolio_margin
- safety: cancel_all, batch_cancel, kill_switch

## Rows (v0)
- Mock (testing baseline)
- Kraken (baseline)
- Coinbase Advanced
- OKX
- Bybit

## Registry (P111)
Selector: `src&#47;execution&#47;adapters&#47;registry_v1.py` — `select_execution_adapter_v1(name, market=...)` for mocks-only providers.

> v0 is documentation + mock interfaces only. No live trading, no real keys, no network calls.
