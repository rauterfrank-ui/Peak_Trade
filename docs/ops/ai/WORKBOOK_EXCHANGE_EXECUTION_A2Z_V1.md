# WORKBOOK — Exchange + Execution A2Z (v1)

## A) Scope & Guardrails (Non-goals)
- **NO LIVE**: Kein Live-Trading, keine Orders, keine Secrets.
- Nur Interface/Adapter, Mocks, Backtest/Shadow, Audit-Trails.
- Harte Deny-List für `LIVE&#47;TRADING_ENABLE&#47;PT_ARMED&#47;...` analog Ops-Loop.

## B) Anforderungen (must-have)
- Multi-Exchange-fähig (Kraken bleibt default).
- Einheitliches Order/Fill/Balance Schema (normalize layer).
- Deterministische Dry-Run/Shadow Pipeline, reproduzierbare Configs.
- Rate-limit / retry / idempotency / time sync / symbol mapping.

## C) Exchange-Klassen (Buckets)
- Tier 1: BTC/ETH + Majors (hohe Liquidität)
- Tier 2: Alts (höhere Varianz, Liquidity/Spread-Risiko)
- Tier 3: Illiquide/Scam-Risk (Crawler/Policy-Gate blockiert)

## D) Risiken (Checkliste)
- Regulierung/Geo-Fencing/KYC/Account freeze
- API downtime / partial fills / out-of-order events
- Funding/fees/hidden costs, withdrawal risks
- Market microstructure: spread, slippage, latency, maker/taker

## E) Adapter Architektur (Plan)
- `src&#47;exchanges&#47;`:
  - `base.py` (protocol)
  - `kraken.py` (default impl)
  - `ccxt_adapter.py` (optional abstraction)
- `src&#47;execution&#47;`:
  - order router (paper/shadow only)
  - strict kill-switch + budget caps
- `src&#47;schemas&#47;`:
  - canonical `OrderRequest&#47;OrderAck&#47;Fill&#47;Position&#47;Balance`

## F) Safety Gates (hard)
- Env deny-list + secret scanning
- Mode gating: research/shadow/testnet only
- Budget caps (daily notional cap) + max order size
- Symbol allowlist from crawler scores

## G) Test Strategy
- Unit: schema normalization, symbol map, idempotency keys
- Contract: recorded API fixtures (no secrets)
- Shadow: read-only market data ingest + readiness only

## H) Migration Plan (Kraken → multi-exchange)
- Keep Kraken as reference implementation.
- Add new exchange behind feature flag.
- Backtest parity + shadow parity before any broader enablement.

## I) Evidence + Artifacts
- `docs&#47;analysis&#47;p105&#47;README.md` (research notes)
- runbook: `docs&#47;ops&#47;ai&#47;exchange_execution_runbook_v1.md` (later)
- tests: file existence + minimal lint

## J) Finish Criteria
- Workbook merged
- Interfaces sketched + stubs compile
- No live paths introduced
- Guardrails present + tests green
