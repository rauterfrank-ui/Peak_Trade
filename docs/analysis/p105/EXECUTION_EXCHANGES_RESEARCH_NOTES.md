# P105 — Exchange/Execution Deep Research Notes (paper/shadow only)

## Scope / Guardrails
- **No live trading.** Research-only: API surface, market structure, product coverage, operational risk, legal/compliance constraints (high-level).
- Target user context: **DE/EU resident** (MiCA/AML/Tax realities). This is not legal advice.

## Terms
- **CEX**: Centralized exchange (custodial, KYC).
- **DEX**: Decentralized exchange (non-custodial, on-chain execution).
- **Alts**: "Altcoins" = crypto assets other than BTC (often ETH excluded too). Typically higher liquidity fragmentation, higher listing churn, higher risk.

## What "Kraken EU-only" usually means (practically)
- Not EU-only, but **product availability & leverage** can be jurisdiction-gated.
- EU users often see stricter defaults: leverage limits, derivatives availability, onboarding friction.

## Decision axes (what matters for Peak_Trade)
1. **Market coverage**: spot + perps; listing breadth for alts; stablecoin pairs.
2. **Execution quality**: latency, matching engine, maker/taker, post-only, reduce-only, OCO/stop support.
3. **API**: REST + WS reliability, order rate limits, deterministic semantics (idempotency), timestamp rules.
4. **Risk controls**: subaccounts, API key scopes, IP allowlist, withdraw lock, kill switch semantics.
5. **Ops reliability**: incident history, maintenance windows, status page truth, websocket reconnect behavior.
6. **Custody/legal**: KYC, asset segregation, regulatory posture, counterparty risk.
7. **Costs**: fees, funding, borrow rates, hidden slippage due to liquidity.

## Candidate buckets (high-level)
### A) "Mainstream CEX" (broad liquidity, strong APIs)
- **Binance**: very broad alts + deep liquidity; region restrictions for EU; compliance risk varies by country; API mature.
- **OKX**: strong perps + breadth; regional restrictions; API decent.
- **Bybit**: strong perps + liquidity; jurisdiction gating; API mature.
- **Coinbase Advanced**: strong compliance + USD liquidity; fewer alts vs Binance/OKX; perps availability varies.
- **Kraken**: strong compliance reputation; good spot; perps/derivatives availability may be limited by region.

### B) "Alt-heavy / listings-first"
- **KuCoin / Gate.io / MEXC**: broad listings; higher counterparty/regulatory risk perception; API quality varies; beware operational hazards.

### C) "DEX execution" (non-custodial, composable)
- **Uniswap v3/v4, 1inch, CowSwap** (Ethereum + L2s), **Jupiter** (Solana), **Raydium/Orca** etc.
- Pros: self-custody, broad token surface.
- Cons: MEV, gas, chain outages, slippage, partial fills semantics differ, complex accounting, harder risk model.

## Risks & tradeoffs (Kraken vs "go international")
### Kraken (Pros)
- Lower perceived counterparty/regulatory risk; stable ops.
- Cleaner KYC/AML posture for EU users.
- Typically good fiat rails.

### Kraken (Cons)
- Potentially narrower alt coverage / region-gated products.
- If your edge needs "new listings churn", you may outgrow it.

### Switching to alt-heavy CEX (Pros)
- More alts, more listing churn, potentially more opportunity surface.
- Often deeper perps liquidity for mid/long-tail alts.

### Switching to alt-heavy CEX (Cons)
- Higher counterparty risk; more frequent delists/halts.
- Operational risk (WS instability, rate limits, incidents).
- Compliance uncertainty for EU residents; account restrictions can change.

### DEX route (Pros)
- Maximum asset surface, self-custody.
- No "exchange lock-in" if abstracted well.

### DEX route (Cons)
- Execution becomes *protocol + chain* dependent.
- MEV and sandwich risk for "market" orders.
- Fee model (gas) + latency makes tight intraday strategies harder.

## Recommended architecture direction (Peak_Trade)
### 1) Keep Kraken as **baseline connector**
- Maintain "known-good" CEX path.
- Use it as reference for risk & determinism.

### 2) Add **ExecutionAdapter v2** interface (exchange-agnostic)
- Normalize:
  - symbols / instruments (spot/perp)
  - order types (market/limit/post-only/reduce-only)
  - time-in-force
  - leverage/margin flags (if any)
  - fills stream semantics
- Provide exchange-specific capability flags:
  - supports_post_only, supports_reduce_only, supports_oco, supports_trailing_stop, supports_batch_cancel, etc.

### 3) Add **Exchange Capability Matrix + Contract Tests**
- Contract tests per adapter:
  - idempotent clientOrderId
  - cancel semantics
  - WS reconnect + sequence gaps
  - minNotional/stepSize rounding rules
  - deterministic fee model mapping

### 4) Safety-first gating (already your philosophy)
- Continue:
  - paper/shadow/testnet/live gates
  - "armed/enabled + confirm token"
  - deny-lists for live env vars in ops scripts

## Next concrete step
- Build a **shortlist** of 2–3 target exchanges based on:
  - EU accessibility
  - alt coverage you actually need
  - API maturity + reliability
- Then implement adapter scaffolds with mocked integration tests (no keys).
