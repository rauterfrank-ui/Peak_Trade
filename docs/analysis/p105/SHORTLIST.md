# P105 — Exchange Shortlist (paper/shadow only)

## Shortlist (2–3)
1) Kraken (baseline / reference)
2) Coinbase Advanced (regulated-heavy, strong USD liquidity; alt breadth moderate)
3) OKX *or* Bybit (alt/perps breadth; regional gating risk)  <!-- choose one later -->

## Selection criteria (must-pass)
- EU accessibility for account + API usage (spot at minimum)
- Stable REST+WS behavior (reconnect, rate-limits, order lifecycle determinism)
- Clear key scopes + subaccounts + IP allowlist
- Capability fit: post-only, reduce-only, stop orders, batch cancel
- Operational maturity: incident transparency, maintenance predictability

## "Do-not" (for now)
- Alt-heavy high-risk venues (KuCoin/Gate/MEXC) until we have hardened counterparty + incident playbooks.
- DEX execution path until we have MEV/slippage/chain-risk model + separate adapter family.
