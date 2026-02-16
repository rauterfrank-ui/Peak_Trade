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
- Kraken (baseline)
- Coinbase Advanced
- OKX
- Bybit

> v0 is documentation + mock interfaces only. No live trading, no real keys, no network calls.
