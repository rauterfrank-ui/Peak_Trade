# Peak_Trade Futures Trading Readiness Runbook v0

> **Repository note (non-authority):** This document is **docs-only**. It is **not** a live trading authorization, **not** a permission to place orders, run execution, or start trading or sandbox sessions, and **not** a runtime or infrastructure enable. Futures readiness is intentionally staged: inventory → classification → capability spec → data model → backtest realism → risk/safety → read-only dashboard → testnet/dry-run → evidence → **live only** after explicit external governance (not implied by this file or by repo state).

**Scope:** Deep-research-based operating runbook for safely evolving Peak_Trade toward crypto futures / perpetual futures support.

**Mode:** Cursor Multi-Agent orchestration, evidence-first, no live trading.

**Status:** Planning and audit runbook. Not a trading authorization. Not financial advice.

---

## Capability spec

- [Futures Capability Spec v0](../../specs/FUTURES_CAPABILITY_SPEC_V0.md) — non-authority capability ladder and boundaries; complements this runbook’s operational sequence.

---

## 0. Executive Summary

Peak_Trade should treat futures/perpetual trading as a separate capability class, not as “spot trading with leverage.” Futures require explicit models for instrument metadata, contract sizing, margin, leverage, liquidation, funding, position mode, order flags, exchange-specific constraints, testnet/sandbox routing, and non-live safety gates.

Current repo inventory suggests:

- The strongest explicit futures-like implementation is `src/markets/cme/` for offline CME NQ/MNQ-style work.
- Crypto execution/backtest appears mostly spot/cash-style.
- `kraken_futures_testnet` appears to need classification before it is shown as anything stronger than placeholder/testnet-surface in a dashboard.
- Market Dashboard v0 can be useful, but only as a read-only, futures-aware observability surface, not as an execution/control UI.
- Futures live trading is out of scope until testnet/dry-run/evidence/governance gates prove the full path.

External research anchors:

- Futures and virtual-currency derivatives are leveraged products; leverage amplifies gains and losses, and small price moves can cause large losses relative to margin. CFTC and futures-risk disclosures explicitly warn about leveraged virtual-currency futures risk.
- Futures exchanges expose fields and controls not present in spot: instrument contract metadata, tick/lot sizes, mark/index prices, funding, margin modes, leverage settings, position/ADL information, and futures order flags.
- Kraken and Binance futures APIs document distinct derivatives endpoints for instruments, leverage/margin settings, mark price/funding rate, and futures order placement.
- CCXT unifies some derivatives concepts, but exchange-specific params and flags remain critical.

---

## 1. Non-Negotiable Boundary

This runbook permits:

- Read-only repo inspection.
- Docs/spec creation.
- Unit tests using fixtures only.
- Offline backtest improvements.
- Dashboard read-only design.
- Testnet/dry-run planning.

This runbook forbids unless a later explicit governance step authorizes it:

- Live trading.
- Real order routing.
- Exchange calls with real credentials.
- Writing evidence into `out&#47;`, S3, registries, or archives.
- Mutating market-data caches.
- Starting bounded-pilot, shadow, paper, testnet, or live sessions.
- Treating a dashboard display as authorization.

---

## 2. External Futures Best-Practice Checklist

### 2.1 Product and Instrument Metadata

A futures/perpetual instrument model must include at least:

| Field | Why it matters |
|---|---|
| `instrument_type` | spot, margin, future, perpetual/swap, option |
| `exchange` | Binance, Kraken Futures, CME, OKX, Bybit, etc. |
| `symbol_native` | exchange-native instrument id |
| `symbol_unified` | canonical internal symbol |
| `base_asset` | e.g. BTC |
| `quote_asset` | e.g. USDT/USD/EUR |
| `settle_asset` | e.g. USDT, USD, BTC |
| `contract_type` | perpetual, quarterly, dated future |
| `expiry_ts` | null for perpetual |
| `contract_size` | multiplier / notional unit |
| `tick_size` | price increment |
| `lot_size` / `step_size` | quantity increment |
| `min_qty` / `max_qty` | order sizing bounds |
| `min_notional` | exchange order notional floor |
| `price_filter` | exchange price bounds |
| `reduce_only_supported` | capability flag |
| `post_only_supported` | capability flag |
| `position_mode_supported` | one-way / hedge |
| `margin_modes_supported` | isolated / cross |
| `max_leverage` | exchange cap, not user target |
| `funding_interval` | perp funding cadence |
| `mark_price_available` | liquidation/risk reference |
| `index_price_available` | fair-value reference |
| `testnet_supported` | explicit boolean |
| `live_supported` | must default false in Peak_Trade |

### 2.2 Market Data

Futures dashboards and backtests should distinguish:

- Last/trade price.
- Mark price.
- Index price.
- Funding rate.
- Next funding timestamp.
- Open interest.
- Volume.
- Liquidation-volume analytics if available.
- Order book depth.
- Contract metadata freshness.
- Cache provenance.

For perpetuals, mark/index/funding data are not optional for realistic risk display. Binance documents a futures endpoint for mark price and funding rate (`&#47;fapi&#47;v1&#47;premiumIndex`), and Kraken Futures exposes futures market-data endpoints such as tickers and instruments.

### 2.3 Margin, Leverage, and Liquidation

Required before any futures testnet/live work:

- Isolated/cross margin mode.
- Initial margin.
- Maintenance margin.
- Used margin.
- Free margin.
- Wallet balance vs margin balance.
- Unrealized PnL.
- Liquidation price.
- Liquidation distance.
- Margin ratio.
- Leverage cap.
- Requested leverage vs effective leverage.
- Exchange leverage-preference API behavior.

Kraken’s derivatives documentation explicitly treats leverage preferences as setting cross/isolated margin behavior; specifying max leverage can set isolated margin. Kraken support documentation also emphasizes that derivatives leverage magnifies profits and losses. CFTC similarly warns that leveraged virtual-currency futures can amplify losses.

### 2.4 Funding

Perpetual futures require:

- Funding rate.
- Funding interval.
- Funding timestamp.
- Funding PnL in backtests.
- Historical funding series.
- Funding source/provenance.
- Funding stress scenarios.

A backtest that ignores funding is not a realistic perpetuals backtest.

### 2.5 Order Model

Futures order model must explicitly support or reject:

| Feature | Required handling |
|---|---|
| market/limit | standard |
| stop-market | supported or rejected |
| take-profit-market | supported or rejected |
| trailing-stop | supported or rejected |
| post-only | supported or rejected |
| reduce-only | supported or rejected |
| close-position | supported or rejected |
| time-in-force | GTC/IOC/FOK/etc. |
| position side | long/short/both |
| position mode | one-way vs hedge |
| client order id | idempotency / reconciliation |
| trigger price type | last/mark/index where exchange supports it |
| price protect | exchange-specific behavior |
| slippage controls | fail-closed if missing |
| notional cap | risk layer |
| margin/leverage preflight | before order construction |

Binance futures order docs expose futures-specific parameters such as position side, reduce-only, close-position, stop price, activation price, callback rate, and working type. Kraken Futures order docs expose futures contract order placement and order types such as limit, stop, take profit, and IOC.

### 2.6 Exchange Adapter and Testnet

A futures adapter must not be inferred from a symbol label. It must prove:

- Separate futures endpoint base URL.
- Explicit sandbox/testnet mode.
- API key scope validation.
- No default live endpoint.
- Time sync / nonce/signature handling.
- Instrument discovery.
- Account/margin snapshot.
- Position fetch.
- Open orders fetch.
- Order validate/test endpoint if supported.
- Dry-run order construction without sending.
- Idempotent client IDs.
- Cancel/close/reduce-only path.
- Fail-closed if margin/leverage/instrument metadata missing.

### 2.7 Risk and Safety

Before testnet:

- Max leverage cap, default <= 1x until explicitly changed.
- Max notional exposure.
- Max symbol exposure.
- Max total exposure.
- Max daily loss.
- Max drawdown.
- Max liquidation-proximity threshold.
- Funding-rate cutoff.
- Spread/slippage cutoff.
- Data freshness cutoff.
- Exchange connectivity cutoff.
- KillSwitch hard veto.
- Reduce-only emergency mode.
- No-live gate independent of dashboard.
- Audit log for all preflight decisions.

Before live:

- All above plus external evidence, operator signoff, incident runbooks, circuit breakers, rollback, and immutable archive.

---

## 3. Cursor Multi-Agent Role Setup

Use these agents:

1. **Repo Inventory Agent**  
   Reads files and classifies futures surfaces.

2. **Exchange Adapter Agent**  
   Maps exchange/testnet/order/position code.

3. **Risk & Safety Agent**  
   Maps RiskGate, SafetyGuard, LiveRiskLimits, KillSwitch, futures gaps.

4. **Backtest Realism Agent**  
   Checks fees, slippage, leverage, margin, liquidation, funding.

5. **Dashboard Agent**  
   Defines safe read-only dashboard data model and UI boundaries.

6. **Governance Agent**  
   Defines staged build order, gates, evidence, and no-live constraints.

7. **Test Contract Agent**  
   Proposes fixture-only tests; no exchange calls.

---

## 4. Cursor Multi-Agent Runbook

### Phase 0 — Freeze Boundary

**Goal:** Ensure no one accidentally turns inventory work into execution work.

**Allowed:** read-only inspection, `/tmp` reports.  
**Forbidden:** exchange calls, cache writes, testnet/live/paper/shadow, Docker/WebUI start.

**Cursor prompt:**

```bash
cd ~/Peak_Trade && \
git checkout main && \
git pull --ff-only origin main && \
test -z "$(git status --porcelain)" && \
mkdir -p /tmp/peak_trade_futures_program_v0
```

---

### Phase 1 — Repo Futures Inventory

**Goal:** Classify current repo as spot-only, generic-market, futures-aware, partial, absent, unclear.

**Outputs:**

- `FUTURES_REPO_INVENTORY_V0.md`
- `FUTURES_REPO_LEDGER_V0.md`
- `FUTURES_CAPABILITY_MAP_V0.md`

**Key searches:**

```bash
git grep -nE 'future|futures|perp|perpetual|margin|leverage|liquidation|funding|contract_size|reduce_only|post_only|testnet|exchange|order|position' -- docs src tests scripts config .github 2>/dev/null
```

**Decision:** Do not build anything until `kraken_futures_testnet` and futures capability gaps are classified.

---

### Phase 2 — Kraken Futures/Testnet Classification

**Goal:** Determine if `kraken_futures_testnet` is:

1. UI/registry label only.
2. CLI/session label only.
3. dry-run/testnet placeholder.
4. partial adapter.
5. real futures-testnet adapter, not live-ready.
6. unclear.

**Files to inspect:**

- `src/experiments/live_session_registry.py`
- `scripts/run_execution_session.py`
- execution/session/orchestrator code
- exchange adapters
- WebUI tests/docs mentioning `kraken_futures_testnet`

**Outputs:**

- `KRAKEN_FUTURES_TESTNET_CLASSIFICATION_V0.md`
- `KRAKEN_FUTURES_TESTNET_CALLPATH_MAP_V0.md`
- `MARKET_DASHBOARD_KRAKEN_FUTURES_IMPLICATIONS_V0.md`

**Exit criteria:** Dashboard can display one of: unsupported / placeholder / partial / testnet-only / supported-readonly. It must not display live-ready.

---

### Phase 3 — Futures Capability Spec

**Goal:** Write one canonical docs-only spec before implementation.

**Branch:** `docs/futures-capability-spec-v0` <!-- pt:ref-target-ignore --> (example branch name; not a path)

**Target doc:**  
`docs&#47;ops&#47;specs&#47;FUTURES_CAPABILITY_SPEC_V0.md` <!-- pt:ref-target-ignore --> (planned spec; not in repo yet)

**Required sections:**

1. Scope and no-live boundary.
2. Spot vs futures vs perpetual definitions.
3. Instrument metadata contract.
4. Market-data contract.
5. Funding contract.
6. Margin/leverage/liquidation contract.
7. Order model contract.
8. Exchange adapter contract.
9. Backtest realism requirements.
10. Risk/safety requirements.
11. Dashboard display requirements.
12. Testnet/dry-run requirements.
13. Evidence/governance gates.
14. Safe build order.

**Validation:**

```bash
uv run python scripts/ops/validate_docs_token_policy.py --tracked-docs
bash scripts/ops/verify_docs_reference_targets.sh --docs-root docs
bash scripts/ops/pt_docs_gates_snapshot.sh --changed
```

---

### Phase 4 — Data Model Contract

**Goal:** Add contract tests or schema stubs for futures metadata before runtime code.

**Possible files:**

- `src&#47;markets&#47;futures_contract.py` <!-- pt:ref-target-ignore --> (illustrative)
- `src&#47;markets&#47;instrument.py` <!-- pt:ref-target-ignore --> (illustrative)
- `tests&#47;markets&#47;test_futures_contract_schema.py` <!-- pt:ref-target-ignore --> (illustrative)

**Invariant:**

- Futures instrument cannot be used without contract type, tick size, lot size, settle asset, and margin mode capability.
- Perpetual cannot be used without funding metadata placeholder.
- Dashboard cannot mark instrument live-ready from metadata.

**No exchange calls. No caches.**

---

### Phase 5 — Backtest Futures Realism

**Goal:** Add offline modeling only.

Required realism:

- futures fee schedule
- slippage
- leverage
- initial/maintenance margin
- liquidation
- funding PnL
- contract size
- notional exposure
- reduce-only simulation
- stop/take-profit semantics

**Acceptance criteria:**

- Deterministic fixture tests.
- No real market data fetch.
- No order execution.
- Monte Carlo/stress hooks for liquidation/funding shocks.

---

### Phase 6 — Risk/Safety Contracts

**Goal:** Prevent futures path from bypassing risk.

Required tests:

- Futures notional exposure cap.
- Liquidation-distance cutoff.
- Funding-rate cutoff.
- Leverage max cap.
- KillSwitch veto.
- Reduce-only emergency mode.
- No-live gate independent of dashboard.
- No route to exchange adapter without explicit dry-run/testnet governance.

---

### Phase 7 — Market Dashboard v0

**Goal:** Read-only futures-aware dashboard.

**Allowed display:**

- instrument type
- exchange
- symbol
- mark/index/last price if available from read-only fixtures or approved source
- funding rate / next funding if available
- margin mode
- leverage cap
- notional exposure placeholder
- liquidation-distance placeholder
- data source/provenance
- cache/write status
- “No Live Authorization” banner

**Forbidden controls:**

- place order
- cancel order
- change leverage
- change margin mode
- enable live
- arm execution
- toggle KillSwitch
- write evidence
- trigger fetch/cache writes unless explicitly approved

**Implementation only after Phases 1–3.**

---

### Phase 8 — Testnet/Dry-Run Only

**Goal:** Only after adapter classification and risk contracts.

Requirements:

- Testnet endpoint proof.
- API key scope check.
- dry-run default.
- no live endpoint default.
- no secrets in logs.
- no account real-money access.
- order construction tests.
- cancel/reduce-only tests.
- position fetch tests with fixture/mock first.

---

### Phase 9 — Candidate-Specific Evidence

Only after a real candidate:

- `candidate_id`
- governance reviewer
- archive root
- L1-L3 evidence plan
- testnet-only or dry-run-only mode
- checksums
- immutable archive
- no-live signoff

---

### Phase 10 — Live Futures

Out of scope.

Live futures requires:

- all above stages complete
- external governance signoff
- incident runbooks
- capital envelope
- hard risk caps
- KillSwitch drills
- testnet evidence
- operator dry-run
- pre-live checklist
- legal/regulatory self-check
- explicit enable/arm/confirm-token gates

---

## 5. Futures Capability “Definition of Done”

Peak_Trade can be called **futures-aware** only when:

- Instrument metadata exists and is tested.
- Funding/margin/liquidation are represented.
- Backtests include futures realism.
- Risk/safety understands futures.
- Dashboard clearly separates spot vs futures.
- Testnet adapter is proven or explicitly unsupported.
- Live remains false unless governance approves.

Peak_Trade can be called **futures-testnet-ready** only when:

- testnet endpoint and credentials are isolated.
- no live endpoint path can be reached accidentally.
- order construction is futures-specific.
- risk and kill-switch are active in testnet.
- evidence exists for dry-run/testnet flows.

Peak_Trade can be called **futures-live-ready** only after external governance and evidence, not from repo state alone.

---

## 6. Best-Practice Build Order

1. Futures repo inventory.
2. Kraken futures/testnet classification.
3. Docs-only Futures Capability Spec.
4. Instrument metadata contract.
5. Futures data-source/provenance contract.
6. Backtest realism.
7. Risk/safety contracts.
8. Read-only dashboard.
9. Testnet dry-run.
10. Evidence capture.
11. Governance.
12. Live only later.

---

## 7. Source Notes

These external sources informed the runbook:

- CFTC virtual currency risk advisory: https://www.cftc.gov/LearnAndProtect/AdvisoriesAndArticles/understand_risks_of_virtual_currency.html
- CME/FIA futures risk disclosure: https://www.cmegroup.com/fcm/files/fia-risk-disclosure.pdf
- Binance USDⓈ-M Futures New Order API: https://developers.binance.com/docs/derivatives/usds-margined-futures/trade/rest-api
- Binance Futures Mark Price and Funding Rate API: https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Mark-Price
- Binance Futures Exchange Information API: https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Exchange-Information
- Binance Coin-M Futures common definitions / lot-size filters: https://developers.binance.com/docs/derivatives/coin-margined-futures/common-definition
- Kraken Futures instruments API: https://docs.kraken.com/api/docs/futures-api/trading/get-instruments
- Kraken Futures send-order API: https://docs.kraken.com/api/docs/futures-api/trading/send-order/
- Kraken leverage settings API: https://docs.kraken.com/api/docs/futures-api/trading/set-leverage-setting
- Kraken leverage and margining derivatives article: https://support.kraken.com/articles/360022835651-leverage-margining-summary-derivatives
- Kraken contract specifications: https://support.kraken.com/articles/contract-specifications
- CCXT manual: https://docs.ccxt.com/README
- CCXT Kraken Futures docs: https://docs.ccxt.com/exchanges/krakenfutures
