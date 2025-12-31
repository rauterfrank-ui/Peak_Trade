# WP0D — Recon / Ledger / Accounting Bridge (Task-Packet)

**Phase:** Phase 0 — Foundation  
**Work Package:** WP0D (Recon / Ledger / Accounting Bridge)  
**Owner:** A5 (Recon-Agent)  
**Status:** DRAFT (Docs-Only)  
**Source:** docs/execution/PEAK_TRADE_LIVE_EXECUTION_ROADMAP_MULTI_AGENT_v1_0.md (WP0D section)

---

## Scope

### In-Scope
**Source:** Roadmap WP0D (lines 174-186) + user specification (recon + ledger/position accounting bridge)

- **Reconciliation Engine:** Compare internal ledger state with external/exchange state, detect divergences
- **Position Accounting Bridge:** Consume Fill events from WP0A/WP0C → update Position Ledger
- **ReconDiff Generation:** Identify discrepancies (missing fills, orphan orders, quantity mismatches, price drift)
- **Matching Rules:** Define criteria for matching internal orders/fills with exchange records
- **Observability Metrics:** orders/min, error rate, reconnects, latency (p95/p99), position drift
- **Structured Logging:** trace_id/session_id/strategy_id tagging for all events
- **Minimal Dashboard:** JSON export or read-only hook to existing Live-Track UI
- **Evidence Reports:** Reconciliation snapshots, position consistency validation, metrics summary

### Out-of-Scope
- Code implementation (deferred to implementation run)
- src/ or tests/ modifications
- Live enablement or activation instructions
- Real-time alerting (Ops runbooks define escalation, not WP0D implementation)
- Exchange API integration (WP0C provides fills, WP0D consumes)
- Historical data backfill (reconciliation scope limited to active session)

---

## Definitions / Glossary

**Ledger:**  
Internal bookkeeping of execution events (Trade/Fee/Adjustment). Single source of truth for accounting. Append-only, immutable.

**LedgerEntry:**  
Individual accounting entry (defined in WP0E). Categories: TRADE (qty, price, asset, side, fees), FEE (fee asset, fee amount, basis), ADJUSTMENT (manual/ops, rare, flagged).

**Reconciliation:**  
Process of comparing internal ledger state with external source (statement/feed) to detect discrepancies. Produces ReconDiff reports.

**ReconDiff:**  
Formalized delta with severity. Data structure (defined in WP0E) representing divergence between internal and external state. Includes discrepancy type, severity (INFO/WARN/FAIL), dimension (POSITION/CASH/FEES/TRADES), delta.

**Reconciliation Flow:**  
Conceptual pipeline: (1) Collect internal ledger snapshot (as-of time) → (2) Collect external reference snapshot (concept only) → (3) Match trades/fees/positions (rules documented) → (4) Produce ReconDiff list → (5) Severity evaluation.

**Matching Rules:**  
Deterministic criteria for matching internal vs external records. Prefer correlation_id/order_id if available. Fallback: (symbol, side, qty, price, time window). Tie-breaker: smallest time delta, then stable sort.

**Severity Taxonomy:**  
ReconDiff severity levels: INFO (negligible/expected timing drift), WARN (actionable mismatch requiring review), FAIL (hard mismatch, blocks GO).

**Position Ledger:**  
Single source of truth for positions and PnL. Tracks net position per symbol, average entry price, realized/unrealized PnL, cash balance. Updated by fills from WP0A/WP0C.

**Fill Event:**  
Execution result (partial or complete) from WP0C OrderExecutor. Consumed by Position Ledger to update positions. Format: Fill type (symbol, side, quantity, price, timestamp, fees).

**Mapping: ExecutionEvent → LedgerEntry:**  
Conceptual transformation rules. FILL event → TRADE entry (+ optional FEE entry). REJECT → no ledger movement (audit trail only). CANCEL_ACK → no ledger movement (order state update only).

**Position Drift:**  
Divergence between internal Position Ledger and exchange-reported positions. Measured as absolute delta (quantity mismatch) or percentage drift.

**Observability Metrics:**  
Quantitative measurements of system health: orders/min, error rate, reconnects, latency (p95/p99), recon drift rate.

**Structured Logging:**  
Log format with consistent fields (trace_id, session_id, strategy_id, timestamp, level, message, context). Enables querying and correlation.

**Evidence Report:**  
Auditable artifact (JSON/Markdown) documenting reconciliation results, position snapshots, metrics summary. Stored in `reports/observability/` or `reports/execution/`.

---

## Proposed Components

**Source:** Roadmap WP0D + existing Position Ledger (src/execution/position_ledger.py) + telemetry docs

### Component 1: ReconciliationEngine
**Purpose:**  
Compare internal ledger state with external/exchange state, detect divergences, generate ReconDiff reports.

**Responsibilities:**  
- Fetch internal state: Order Ledger (from WP0A), Position Ledger (local)
- Fetch external state: Exchange API snapshot (via WP0C adapter, read-only query)
- Apply matching rules: Match orders/fills by order_id, symbol+timestamp, quantity tolerance
- Detect discrepancies: Missing fills, orphan orders, quantity mismatches, price drift
- Generate ReconDiff: Create ReconDiff instances (type, description, resolution_hint)
- Produce reconciliation report: JSON/Markdown summary with all diffs

**Reconciliation Process:**  
```
1. Fetch internal snapshot: all open orders, all positions, all fills (last N hours)
2. Fetch external snapshot: exchange open orders, exchange positions
3. Match internal orders ↔ external orders (by order_id or client_id)
4. Match internal fills ↔ external fills (by trade_id or timestamp+quantity)
5. Match internal positions ↔ external positions (by symbol)
6. For each discrepancy → create ReconDiff(type, internal_value, external_value, hint)
7. Aggregate all diffs → reconciliation report (timestamped, stored in reports/)
```

**Matching Rules:**  
- **Order Match:** internal.order_id == external.order_id OR internal.client_id == external.client_order_id
- **Fill Match:** internal.fill_id == external.trade_id OR (symbol match AND timestamp within 5s AND quantity within 0.1%)
- **Position Match:** symbol match, quantity within tolerance (0.01 units or 1%, whichever larger)

**Tolerance Thresholds:**  
- Quantity: 0.1% or 0.01 units (whichever larger)
- Price: 0.5% (slippage/fee tolerance)
- Timestamp: ±5s (clock skew tolerance)

---

### Component 2: Position Accounting Bridge
**Purpose:**  
Consume Fill events from WP0A/WP0C execution pipeline, update Position Ledger, maintain position invariants.

**Responsibilities:**  
- Subscribe to Fill events (from WP0A OSM after order filled)
- Validate fills (quantity > 0, price > 0, symbol valid)
- Apply fill to Position Ledger: update position, PnL, cash balance
- Enforce invariants: Position + Cash = Cumulative Fills
- Log all position updates (structured logging with trace_id)
- Emit position snapshot events (for dashboard/monitoring)

**Fill Application Logic:**  
```
ON Fill(symbol, side, quantity, price, fees):
  IF side == BUY:
    position[symbol].quantity += quantity
    position[symbol].cost_basis += (price * quantity) + fees
    cash_balance -= (price * quantity) + fees
  IF side == SELL:
    realized_pnl = (price - position[symbol].avg_entry_price) * quantity - fees
    position[symbol].quantity -= quantity
    position[symbol].realized_pnl += realized_pnl
    cash_balance += (price * quantity) - fees

  position[symbol].avg_entry_price = recalculate_vwap()
  position[symbol].last_updated = timestamp
```

**Invariant Checks:**  
- **Position Conservation:** sum(positions) + cash_balance == initial_capital + cumulative_pnl
- **No Negative Positions (if not shorting):** position[symbol].quantity >= 0 (configurable)
- **Cash Balance Non-Negative:** cash_balance >= 0 (unless margin enabled)

---

### Component 3: Metrics Collector
**Purpose:**  
Track quantitative health metrics for execution system (orders/min, error rate, latency).

**Responsibilities:**  
- Count events: orders submitted, fills received, errors, reconnects
- Measure latency: time from order submission to acknowledgement, submission to fill
- Calculate rates: orders/min, fills/min, errors/min
- Track percentiles: latency p50/p95/p99
- Expose metrics: JSON export for dashboard, periodic logging

**Key Metrics:**  
- **orders_submitted_total:** Counter (total orders submitted since start)
- **orders_filled_total:** Counter (total filled orders)
- **orders_rejected_total:** Counter (total rejected orders)
- **order_error_rate:** Rate (errors/min)
- **order_submission_latency_ms:** Histogram (p50/p95/p99)
- **fill_latency_ms:** Histogram (submission → fill time)
- **reconnects_total:** Counter (exchange reconnections)
- **position_drift_count:** Counter (reconciliation discrepancies detected)

**Metrics Export:**  
- JSON format: `{"metric": "orders_submitted_total", "value": 123, "timestamp": "2025-12-31T12:00:00Z"}`
- Periodic snapshot: Every 5 minutes → `reports/observability/metrics_snapshot_YYYYMMDD_HHMMSS.json`

---

### Component 4: Structured Logger
**Purpose:**  
Provide consistent, queryable logging with trace_id/session_id/strategy_id tagging.

**Responsibilities:**  
- Wrap standard logging with structured fields
- Inject context: trace_id, session_id, strategy_id, order_id
- Format: JSON or JSONL (append-only)
- Support log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Rotate logs: By session or time interval

**Log Schema:**  
```json
{
  "timestamp": "2025-12-31T12:00:00.123Z",
  "level": "INFO",
  "message": "Order submitted successfully",
  "trace_id": "abc123",
  "session_id": "session_2025_12_31",
  "strategy_id": "ma_crossover",
  "order_id": "order_001",
  "context": {"symbol": "BTC/EUR", "side": "buy", "quantity": 0.1}
}
```

**Integration:**  
- WP0A OSM logs all state transitions (CREATED → SUBMITTED → FILLED)
- WP0C OrderRouter logs routing decisions
- WP0D logs reconciliation results, position updates

---

### Component 5: Minimal Dashboard (JSON Export)
**Purpose:**  
Provide read-only snapshot of execution state for monitoring (no real-time UI in Phase 0).

**Responsibilities:**  
- Aggregate current state: open orders, positions, metrics summary
- Export to JSON: `reports/observability/dashboard_snapshot_YYYYMMDD_HHMMSS.json`
- Optional: Hook to existing Live-Track UI (read-only query endpoint)
- Refresh interval: Every 5-10 minutes (no real-time streaming)

**Dashboard Snapshot Schema:**  
```json
{
  "timestamp": "2025-12-31T12:00:00Z",
  "session_id": "session_2025_12_31",
  "metrics": {
    "orders_submitted_total": 123,
    "orders_filled_total": 120,
    "orders_rejected_total": 3,
    "order_error_rate": 0.024,
    "latency_p95_ms": 250,
    "position_drift_count": 0
  },
  "positions": [
    {"symbol": "BTC/EUR", "quantity": 0.1, "avg_entry_price": 50000, "unrealized_pnl": 500}
  ],
  "open_orders": [
    {"order_id": "order_124", "symbol": "ETH/EUR", "side": "buy", "quantity": 1.0, "state": "SUBMITTED"}
  ],
  "recent_errors": [
    {"timestamp": "2025-12-31T11:55:00Z", "message": "Network timeout", "order_id": "order_122"}
  ]
}
```

---

### Component 6: LedgerEntry Mapping & Reconciliation Flow (Docs-Only Concept)
**Source:** User specification — LedgerEntry categories, mapping rules, reconciliation flow

**Purpose:** Document LedgerEntry categories and ExecutionEvent → LedgerEntry mapping rules. Define reconciliation flow with matching rules and severity taxonomy.

**LedgerEntry Categories (WP0E Alignment):**

**1. TRADE:**
- **Fields:** `entry_id`, `correlation_id`, `event_time_utc`, `entry_type=TRADE`, `asset` (symbol), `quantity` (decimal), `price` (decimal), `side` (BUY/SELL), `fees` (optional, can be separate FEE entry), `source_event_id` (fill event_id)
- **Purpose:** Record trade execution (buy/sell)
- **Example:**
```json
{
  "entry_id": "ledger_001",
  "correlation_id": "corr_abc123",
  "event_time_utc": "2025-12-31T12:01:00Z",
  "entry_type": "TRADE",
  "asset": "BTC",
  "quantity": "0.1",
  "price": "50000.00",
  "side": "BUY",
  "fees": "5.00",
  "source_event_id": "event_fill_001"
}
```

**2. FEE:**
- **Fields:** `entry_id`, `correlation_id`, `event_time_utc`, `entry_type=FEE`, `fee_asset` (currency), `fee_amount` (decimal), `basis` (trade-related, e.g., "commission for order_001"), `source_event_id`
- **Purpose:** Record fees separately from trade (optional, can be embedded in TRADE)
- **Example:**
```json
{
  "entry_id": "ledger_002",
  "correlation_id": "corr_abc123",
  "event_time_utc": "2025-12-31T12:01:00Z",
  "entry_type": "FEE",
  "fee_asset": "EUR",
  "fee_amount": "5.00",
  "basis": "commission for order_001",
  "source_event_id": "event_fill_001"
}
```

**3. ADJUSTMENT:**
- **Fields:** `entry_id`, `correlation_id`, `event_time_utc`, `entry_type=ADJUSTMENT`, `asset`, `quantity`, `reason` (manual/ops adjustment), `operator` (who made adjustment), `flagged=true` (should be rare)
- **Purpose:** Manual/ops adjustments (corrections, transfers). Should be rare and flagged for review.
- **Example:**
```json
{
  "entry_id": "ledger_003",
  "correlation_id": "manual_adj_001",
  "event_time_utc": "2025-12-31T13:00:00Z",
  "entry_type": "ADJUSTMENT",
  "asset": "BTC",
  "quantity": "0.01",
  "reason": "Manual correction: duplicate fill removed",
  "operator": "ops_user",
  "flagged": true
}
```

**Mapping: ExecutionEvent → LedgerEntry (Concept):**

**FILL Event → TRADE Entry (+ optional FEE Entry):**
- **Input:** ExecutionEvent(type=FILL, order_id, fill_qty, fill_price, fee, fee_currency)
- **Output:** LedgerEntry(type=TRADE, asset=symbol, quantity=fill_qty, price=fill_price, side=order.side, fees=fee)
- **Optional:** Separate FEE entry if fee tracking required independently

**REJECT Event → No Ledger Movement:**
- **Input:** ExecutionEvent(type=REJECT, order_id, reason)
- **Output:** No LedgerEntry created (audit trail only via WP0A Audit Log)
- **Rationale:** Rejected orders do not affect positions/cash

**CANCEL_ACK Event → No Ledger Movement:**
- **Input:** ExecutionEvent(type=CANCEL_ACK, order_id)
- **Output:** No LedgerEntry created (order state update only)
- **Rationale:** Cancelled orders do not affect positions/cash (unless partially filled before cancel)

**ACK Event → No Ledger Movement:**
- **Input:** ExecutionEvent(type=ACK, order_id)
- **Output:** No LedgerEntry created (order state update only)
- **Rationale:** Acknowledgment does not affect positions/cash

**Reconciliation Flow (Concept):**

**Stage 1: Collect Internal Ledger Snapshot (as-of time)**
- **Input:** as_of_time_utc (e.g., "2025-12-31T23:59:59Z")
- **Process:** Query internal ledger for all TRADE/FEE entries up to as_of_time
- **Output:** Internal snapshot (list of LedgerEntry, positions, cash balance)

**Stage 2: Collect External Reference Snapshot (concept only)**
- **Input:** External source (statement/feed, Phase-0: mocked/stubbed)
- **Process:** Fetch external trades, positions, cash balance (concept: no real integration in Phase-0)
- **Output:** External snapshot (list of external trades, positions, cash)
- **Note:** Phase-0: External snapshot is conceptual/mocked (no live exchange API)

**Stage 3: Match Trades/Fees/Positions (rules documented)**
- **Input:** Internal snapshot, External snapshot
- **Process:** Apply matching rules (deterministic)
- **Matching Rules:**
  - **Prefer:** correlation_id / order_id if available in both internal and external
  - **Fallback:** Match by (symbol, side, qty, price, time window ±5s)
  - **Tie-Breaker:** Smallest time delta, then stable sort (alphabetical by entry_id)
- **Output:** Matched pairs (internal ↔ external) + unmatched entries (orphans)

**Stage 4: Produce ReconDiff List**
- **Input:** Matched pairs + unmatched entries
- **Process:** Identify discrepancies
- **ReconDiff Types:**
  - **Missing Fill (internal):** External trade exists, no matching internal LedgerEntry → dimension=TRADES, severity=FAIL
  - **Orphan Order (external):** Internal LedgerEntry exists, no matching external trade → dimension=TRADES, severity=WARN
  - **Quantity Mismatch:** Matched pair, but qty differs → dimension=POSITION, severity=FAIL (if >1%), WARN (if 0.1%-1%), INFO (if <0.1%)
  - **Price Drift:** Matched pair, but price differs → dimension=TRADES, severity=INFO (if <0.5%), WARN (if 0.5%-2%), FAIL (if >2%)
  - **Cash Mismatch:** Internal cash ≠ external cash → dimension=CASH, severity=FAIL
- **Output:** List of ReconDiff instances

**Stage 5: Severity Evaluation**
- **Input:** List of ReconDiff
- **Process:** Categorize by severity
- **Severity Taxonomy:**
  - **INFO:** Negligible/expected timing drift (e.g., price <0.5%, quantity <0.1%). No action required.
  - **WARN:** Actionable mismatch requiring review (e.g., orphan order, price 0.5%-2%, quantity 0.1%-1%). Operator investigation recommended.
  - **FAIL:** Hard mismatch, blocks GO (e.g., missing fill, quantity >1%, price >2%, cash mismatch). Must be resolved before proceeding.
- **Output:** Reconciliation report with severity summary

**Example ReconDiff (Missing Fill):**
```json
{
  "diff_id": "diff_001",
  "as_of_time_utc": "2025-12-31T23:59:59Z",
  "correlation_id": "unknown",
  "dimension": "TRADES",
  "expected": "internal: no entry",
  "observed": "external: BTC buy 0.1 @ 50000",
  "delta": "missing internal fill",
  "severity": "FAIL",
  "notes": "External trade detected, no matching internal LedgerEntry. Investigate missing fill."
}
```

**Failure Modes (Reconciliation):**
- **Missing External Data:** DEFER reconciliation, produce WARN/FAIL depending on scope (Phase-0: external data mocked, so DEFER acceptable)
- **Duplicate Fills:** Dedupe on event_id/idempotency_key before ledger entry creation
- **Rounding Drift:** Tolerance bands (quantity ±0.1%, price ±0.5%) documented, conservative defaults
- **Unmatched Trades:** FAIL severity default (configurable later, docs conservative)

---

## Inputs / Outputs (Contracts)

**Source:** WP0A ledger events + WP0C fill events + WP0E contracts

### Inputs
**From WP0A (Execution Core / OSM):**
- **Fill Events:** Emitted when order transitions to FILLED state
  - Format: `Fill` type (defined in WP0E): symbol, side, quantity, price, timestamp, fees, order_id
  - Trigger: OSM applies fill → emits Fill event → Position Accounting Bridge consumes
- **Order Ledger Snapshot:** Current state of all orders (for reconciliation)
  - Query: `get_all_orders(state=None)` → List[Order]
  - Used by: ReconciliationEngine to compare with exchange state
- **Audit Log Entries:** LedgerEntry stream for all state transitions
  - Format: `LedgerEntry` type (defined in WP0E): sequence, timestamp, event_type, order_id, old_state, new_state, metadata
  - Used by: Structured Logger for audit trail, metrics aggregation

**From WP0C (Order Routing / Adapter):**
- **OrderExecutionResult:** Execution outcome from executor
  - Format: `OrderExecutionResult` (status, fill, reason, metadata)
  - Used by: Metrics Collector to track latency (execution_time_ms in metadata)
- **Routing Errors:** Rejected orders with reason
  - Used by: Metrics Collector to track error rate

**From Configuration:**
- **Reconciliation Config:** Matching rules, tolerance thresholds, reconciliation interval
- **Metrics Config:** Refresh interval, snapshot storage path, metric retention
- **Logging Config:** Log level, session_id, output format (JSON/JSONL)

**From Exchange (via WP0C read-only query):**
- **Exchange Snapshot:** External state for reconciliation (optional, may not exist in Phase 0)
  - Format: Open orders list, positions list, fills list
  - Note: In Phase 0 (paper/shadow), exchange snapshot may be mocked or skipped

### Outputs
**To Monitoring / Ops:**
- **Metrics Snapshot:** JSON export of current metrics
  - Location: `reports/observability/metrics_snapshot_{timestamp}.json`
  - Frequency: Every 5 minutes (configurable)
  - Content: orders_submitted_total, error_rate, latency_p95, position_drift_count, etc.
- **Dashboard Snapshot:** JSON export of current execution state
  - Location: `reports/observability/dashboard_snapshot_{timestamp}.json`
  - Frequency: Every 5-10 minutes
  - Content: positions, open orders, recent errors, metrics summary

**To Audit / Compliance:**
- **Reconciliation Report:** ReconDiff summary with all discrepancies
  - Location: `reports/execution/reconciliation_report_{timestamp}.md` or `.json`
  - Frequency: On-demand or periodic (hourly/daily)
  - Content: List of ReconDiff instances (missing fills, orphan orders, quantity mismatches), resolution status
- **Position Snapshot:** Current positions + PnL + cash balance
  - Location: `reports/execution/position_snapshot_{timestamp}.json`
  - Frequency: Periodic (every hour) or on-demand
  - Content: All positions (symbol, quantity, avg_entry_price, realized_pnl, unrealized_pnl), cash_balance, invariants check

**To Structured Logging:**
- **JSONL Log Stream:** All events logged with structured fields
  - Location: `logs/execution/{session_id}.jsonl` (append-only)
  - Content: All order submissions, fills, errors, reconciliation results
  - Format: One JSON object per line (JSONL)

**To WP0A (Optional Feedback):**
- **Position Updates:** Notify OSM of current positions (for risk checks in WP0B)
  - Integration: WP0B queries Position Ledger for current exposure
  - Note: Position Ledger is read by WP0B, not pushed to OSM

---

## Failure Modes & Handling

**Source:** Reconciliation + ledger reliability requirements

### Failure Mode 1: Position Ledger Drift (Undetected)
**Scenario:**  
Fill event missed or incorrectly applied → Position Ledger out of sync with reality → incorrect risk calculations (WP0B uses stale positions).

**Impact:**  
- Risk limits evaluated on incorrect positions → potential over-exposure
- PnL calculations wrong → misleading performance metrics
- Reconciliation detects drift later, but real-time trading decisions already made

**Mitigation:**  
- **Fill Event Validation:** Validate fill before applying (quantity > 0, price > 0, symbol valid)
- **Idempotent Fill Application:** If fill applied twice → detect duplicate, do not double-count
- **Periodic Reconciliation:** Run ReconciliationEngine every hour → detect drift early
- **Position Invariant Checks:** After every fill → verify Position + Cash = Cumulative Fills
- **Alert on Drift:** If reconciliation detects discrepancy → emit alert (log WARNING)

---

### Failure Mode 2: Reconciliation False Positive
**Scenario:**  
ReconciliationEngine detects "discrepancy" due to clock skew, timing issues, or tolerance thresholds too strict → generates ReconDiff when no real issue.

**Impact:**  
- Alert fatigue → operators ignore real issues
- Unnecessary investigation time
- Reduced confidence in reconciliation system

**Mitigation:**  
- **Tolerance Thresholds:** Configure conservative thresholds (quantity ±0.1%, timestamp ±5s)
- **Retry Logic:** If discrepancy detected → wait 30s → re-check before creating ReconDiff
- **Categorize Diffs:** Mark diffs as INFO (informational), WARNING (needs review), ERROR (critical)
- **Manual Review:** Operators can dismiss false positives, log resolution in metadata

---

### Failure Mode 3: Metrics Collector Overflow
**Scenario:**  
High order volume → metrics collector cannot keep up → memory overflow or dropped metrics.

**Impact:**  
- Metrics incomplete → dashboard shows incorrect rates
- System instability (memory leak)

**Mitigation:**  
- **Bounded Buffers:** Use ring buffer for metrics (max 10k events, FIFO eviction)
- **Aggregation:** Store only aggregated metrics (counters, histograms), not every event
- **Periodic Flush:** Every 5 minutes → flush metrics to JSON, reset buffers
- **Backpressure:** If buffer full → log WARNING, drop oldest metrics (not crash)

---

### Failure Mode 4: Structured Logging Disk Full
**Scenario:**  
Long-running session → JSONL log file grows unbounded → disk full → system crash.

**Impact:**  
- Log writes fail → events lost
- System instability (cannot write)

**Mitigation:**  
- **Log Rotation:** Rotate logs by size (max 100MB per file) or time (daily)
- **Log Retention:** Keep only last N days (default 7 days), delete older logs
- **Disk Space Check:** On startup → verify sufficient disk space (warn if <1GB free)
- **Fallback:** If disk full → log to stderr (console), emit alert

---

### Failure Mode 5: Exchange API Unavailable (for Reconciliation)
**Scenario:**  
ReconciliationEngine cannot fetch external snapshot (exchange API down, network error).

**Impact:**  
- Reconciliation skipped → potential drifts undetected
- Compliance risk (no audit trail of reconciliation attempts)

**Mitigation:**  
- **Retry with Backoff:** If API call fails → retry 3x with exponential backoff (1s, 2s, 4s)
- **Graceful Degradation:** If all retries fail → log ERROR, skip reconciliation, emit alert
- **Document Gap:** Log "reconciliation skipped due to API unavailable" → audit trail
- **Manual Reconciliation:** Operators can trigger manual reconciliation later

---

### Failure Mode 6: ReconDiff Resolution Tracking Lost
**Scenario:**  
ReconDiff generated, operator investigates, but resolution not tracked → same issue reported repeatedly.

**Impact:**  
- Alert fatigue (same diff keeps appearing)
- Lost context (operator investigates same issue twice)

**Mitigation:**  
- **ReconDiff Metadata:** Include resolution_status (open/investigating/resolved/dismissed)
- **Persistence:** Store ReconDiff history in `reports/execution/recon_history.json`
- **Deduplication:** If same diff detected → update existing entry, do not create duplicate
- **Manual Resolution:** Operators can mark diff as "resolved" or "dismissed" with notes

---

## Acceptance Criteria (Gate-Tauglich)

**Source:** User specification + Roadmap WP0D DoD + reconciliation/ledger requirements

### Docs-Only Criteria (Phase-0 Foundation)
- [ ] **AC1:** LedgerEntry + ReconDiff concepts documented and aligned with WP0E. Categories: TRADE/FEE/ADJUSTMENT. ReconDiff severity: INFO/WARN/FAIL.
- [ ] **AC2:** Mapping rules ExecutionEvent → LedgerEntry described. FILL → TRADE (+ optional FEE), REJECT → no ledger movement, CANCEL_ACK → no ledger movement.
- [ ] **AC3:** Reconciliation flow described with deterministic matching guidance. 5 stages: Collect internal → Collect external → Match → Produce ReconDiff → Severity evaluation.
- [ ] **AC4:** Severity taxonomy (INFO/WARN/FAIL) documented with conservative defaults. FAIL: missing fill, quantity >1%, price >2%, cash mismatch. WARN: orphan order, price 0.5%-2%, quantity 0.1%-1%. INFO: price <0.5%, quantity <0.1%.
- [ ] **AC5:** Keine Live-Enablement-Anweisungen; docs-only. Phase-0: External snapshot conceptual/mocked.
- [ ] **AC6:** Keine Verweise/Links auf nicht-existierende Targets (link hygiene verified).

### ReconciliationEngine Criteria (Implementation)
- [ ] **Matching Rules Implemented:** Order, fill, position matching logic (by order_id, timestamp, quantity)
- [ ] **Tolerance Thresholds:** Quantity ±0.1%, price ±0.5%, timestamp ±5s (configurable)
- [ ] **ReconDiff Generation:** Detects discrepancies (missing fill, orphan order, quantity mismatch, price drift)
- [ ] **Resolution Hints:** Each ReconDiff includes actionable resolution_hint
- [ ] **Reconciliation Report:** JSON/Markdown export with all diffs, timestamped, stored in reports/
- [ ] **Periodic Execution:** ReconciliationEngine runs on schedule (hourly/daily, configurable)
- [ ] **External Snapshot Fetch:** Handles exchange API unavailable gracefully (retry, fallback)

### Position Accounting Bridge Criteria
- [ ] **Fill Event Consumption:** Subscribes to Fill events from WP0A OSM
- [ ] **Fill Validation:** Rejects invalid fills (quantity ≤ 0, price ≤ 0, invalid symbol)
- [ ] **Position Update Logic:** Correctly updates position (BUY → increase, SELL → decrease)
- [ ] **PnL Calculation:** Realized PnL on position reductions, unrealized PnL on mark-to-market
- [ ] **Cash Balance Tracking:** Cash updated on fills (BUY → decrease, SELL → increase)
- [ ] **Invariant Enforcement:** Position + Cash = Cumulative Fills (verified after each fill)
- [ ] **Idempotent Fill Application:** Duplicate fill detection → do not double-count
- [ ] **Position Snapshot Export:** JSON export with all positions, PnL, cash balance

### Metrics Collector Criteria
- [ ] **Core Metrics Tracked:** orders_submitted_total, orders_filled_total, orders_rejected_total, order_error_rate
- [ ] **Latency Metrics:** order_submission_latency_ms (p50/p95/p99), fill_latency_ms
- [ ] **Reconnect Tracking:** reconnects_total (exchange reconnections)
- [ ] **Position Drift Tracking:** position_drift_count (reconciliation discrepancies)
- [ ] **Metrics Export:** JSON format, periodic snapshot (every 5 min)
- [ ] **Bounded Buffers:** Ring buffer (max 10k events), FIFO eviction
- [ ] **Aggregation:** Counters, histograms (not every event stored)

### Structured Logging Criteria
- [ ] **Consistent Schema:** All logs include timestamp, level, message, trace_id, session_id, strategy_id
- [ ] **Context Injection:** order_id, symbol, side, quantity injected into log context
- [ ] **Log Levels:** DEBUG, INFO, WARNING, ERROR, CRITICAL supported
- [ ] **JSONL Format:** One JSON object per line (append-only)
- [ ] **Log Rotation:** By size (100MB) or time (daily)
- [ ] **Log Retention:** Last 7 days (configurable), older logs deleted
- [ ] **Disk Space Check:** Startup verification (warn if <1GB free)

### Minimal Dashboard Criteria
- [ ] **Dashboard Snapshot:** JSON export of current execution state
- [ ] **Snapshot Content:** positions, open orders, recent errors, metrics summary
- [ ] **Refresh Interval:** Every 5-10 minutes (configurable)
- [ ] **Storage Location:** `reports/observability/dashboard_snapshot_{timestamp}.json`
- [ ] **Optional UI Hook:** Read-only query endpoint for existing Live-Track UI (Phase 0 not required)

### Integration Testing Criteria
- [ ] **WP0A → WP0D Fill Propagation:** Fill event from OSM → Position Ledger updated
- [ ] **Position Invariant Test:** Apply fills → verify Position + Cash = Cumulative Fills
- [ ] **Reconciliation Smoke Test:** Compare internal vs external snapshot → detect discrepancies
- [ ] **Metrics Aggregation Test:** Submit orders → metrics updated correctly
- [ ] **Structured Logging Test:** All events logged with trace_id/session_id
- [ ] **Dashboard Export Test:** Generate snapshot → verify JSON schema

### Performance Criteria
- [ ] **Fill Application Latency:** <1ms per fill
- [ ] **Reconciliation Runtime:** <10s for 1000 orders (benchmark)
- [ ] **Metrics Overhead:** <5% CPU impact
- [ ] **Log Write Latency:** <1ms per log entry (async I/O)

### Documentation Criteria
- [ ] **Reconciliation Documented:** Matching rules, tolerance thresholds, resolution hints
- [ ] **Position Ledger API Documented:** Fill application logic, invariants, PnL calculation
- [ ] **Metrics Specification:** All metrics defined (name, type, unit, description)
- [ ] **Structured Logging Schema:** Log format, required fields, examples
- [ ] **Dashboard Snapshot Schema:** JSON schema documented with examples

---

## Evidence Checklist

**Source:** Gate requirements + Roadmap WP0D Evidence (lines 183-185)

### Required Evidence Artifacts (Implementation Run)
- [ ] **Metrics Snapshot:** Periodic JSON export of execution metrics
  - Location pattern: `reports/observability/metrics_snapshot_YYYYMMDD_HHMMSS.json`
  - Content: orders_submitted_total, orders_filled_total, error_rate, latency_p95/p99, position_drift_count
  - Purpose: Demonstrate metrics collection + aggregation working
  - Frequency: Every 5 minutes (at least 3 snapshots in test session)

- [ ] **Structured Logging Sample:** JSONL log with trace_id/session_id/strategy_id
  - Location pattern: `reports/observability/logging_fields.md` (spec) + `logs/execution/{session_id}.jsonl` (sample)
  - Content: Documentation of log schema + sample log entries (order submission, fill, error)
  - Purpose: Verify structured logging implemented correctly

- [ ] **Reconciliation Report:** Smoke test with synthetic discrepancies
  - Location pattern: `reports/execution/reconciliation_report_YYYYMMDD_HHMMSS.json`
  - Content: ReconDiff instances (at least 3 types: missing fill, orphan order, quantity mismatch)
  - Purpose: Validate ReconciliationEngine detects discrepancies
  - Test Setup: Create internal order, no external match → detect orphan; external fill, no internal → detect missing fill

- [ ] **Position Snapshot:** Current positions + PnL + cash balance
  - Location pattern: `reports/execution/position_snapshot_YYYYMMDD_HHMMSS.json`
  - Content: All positions (symbol, quantity, avg_entry_price, realized_pnl, unrealized_pnl), cash_balance, invariants check result
  - Purpose: Demonstrate Position Ledger correctness

- [ ] **Dashboard Snapshot:** Execution state summary
  - Location pattern: `reports/observability/dashboard_snapshot_YYYYMMDD_HHMMSS.json`
  - Content: positions, open orders, recent errors, metrics summary
  - Purpose: Verify dashboard export functionality

- [ ] **Invariant Validation Report:** Position + Cash = Cumulative Fills
  - Location pattern: `reports/execution/invariant_validation_YYYYMMDD_HHMMSS.md`
  - Content: Test results verifying invariants hold after fills (BUY/SELL/position flip scenarios)
  - Purpose: Prove Position Ledger math correct

- [ ] **Integration Test Results:** WP0A → WP0D fill propagation
  - Location pattern: `tests/execution/test_wp0d_integration.py` (pytest output)
  - Content: Test fill event from OSM → Position Ledger update → metrics increment
  - Purpose: Verify cross-WP integration (A ↔ D)

- [ ] **Completion Report:** WP0D implementation documentation
  - Location pattern: `docs/execution/WP0D_IMPLEMENTATION_REPORT.md`

### Evidence Generation (Not in This Docs-Only Run)
**Note:** Evidence artifacts generated during implementation run, not docs-only prep.

---

## Integration Notes

**Source:** Cross-WP dependencies + execution flow

### Depends On
**WP0E (Contracts & Interfaces) — CRITICAL BLOCKER:**
- **Fill Type:** WP0D Position Accounting Bridge consumes Fill events
- **LedgerEntry Type:** WP0D Structured Logger logs LedgerEntry stream
- **ReconDiff Type:** WP0D ReconciliationEngine produces ReconDiff instances
- **Dependency:** WP0E must finalize these types before WP0D implementation

**WP0A (Execution Core / OSM) — CRITICAL BLOCKER:**
- **Fill Events:** WP0A OSM emits Fill events when order transitions to FILLED
- **Order Ledger Query:** WP0D ReconciliationEngine queries Order Ledger for snapshot
- **Audit Log Stream:** WP0D consumes LedgerEntry events for structured logging
- **Integration Point:** OSM.apply_fill() → emit Fill event → Position Accounting Bridge consumes

**WP0C (Order Routing / Adapter) — INDIRECT:**
- **OrderExecutionResult:** WP0D Metrics Collector tracks latency from metadata
- **Routing Errors:** WP0D tracks error rate from rejected orders
- **Integration:** WP0C returns OrderExecutionResult → WP0A OSM → WP0D observes

**Existing Infrastructure:**
- **Position Ledger:** Already exists (src/execution/position_ledger.py), WP0D extends/integrates
- **Execution Telemetry:** Already exists (JSONL logging, events), WP0D aligns with existing patterns

### Consumed By
**WP0B (Risk Layer) — DOWNSTREAM:**
- **Position Ledger Query:** WP0B evaluates risk based on current positions
- **Integration:** WP0B.evaluate_order() → queries Position Ledger for current exposure
- **Note:** Position Ledger is read-only for WP0B (no write access)

**Monitoring / Ops — DOWNSTREAM:**
- **Metrics Snapshots:** Ops runbooks consume metrics for alerting (error rate, latency)
- **Reconciliation Reports:** Compliance team reviews ReconDiff reports
- **Dashboard Snapshots:** Operators monitor execution state via dashboard exports

**Audit / Compliance — DOWNSTREAM:**
- **Structured Logs:** Audit trail for all events (JSONL logs)
- **Position Snapshots:** Compliance verification (position + cash + PnL)
- **Reconciliation Reports:** Discrepancy investigation

### Integration Sequence
**Phase 0 Execution Order:**
1. **WP0E First:** Define Fill, LedgerEntry, ReconDiff types (contracts)
2. **WP0A Next:** Implement OSM with Fill event emission
3. **WP0D Parallel with WP0B/WP0C (after WP0A core ready):**
   - WP0D: Implement Position Accounting Bridge (consumes fills from WP0A)
   - WP0D: Implement Metrics Collector (observes WP0A/WP0C)
   - WP0D: Implement ReconciliationEngine (queries WP0A Order Ledger)
4. **Integration Test (WP0A + WP0D):** OSM → Fill event → Position Ledger → Invariant check
5. **WP0B Integration:** Risk Layer queries Position Ledger for current exposure

**Critical Path:** WP0E → WP0A (Fill events) → WP0D (Position Bridge) → WP0B (Position query)

### Cross-WP Interfaces
**WP0A ↔ WP0D:**
- **Input (WP0A → WP0D):** Fill events (emitted by OSM), LedgerEntry stream, Order Ledger snapshot
- **Output (WP0D → WP0A):** None (WP0D is observer/consumer, not producer to WP0A)

**WP0D ↔ WP0B:**
- **Query (WP0B → WP0D):** Position Ledger read-only query (get_position(symbol), get_all_positions())
- **Note:** WP0B does NOT write to Position Ledger (one-way dependency)

**WP0C ↔ WP0D:**
- **Indirect (via WP0A):** WP0C produces OrderExecutionResult → WP0A OSM → WP0D observes metadata

**WP0E → WP0D:**
- **Contract:** Fill, LedgerEntry, ReconDiff types
- **WP0D Conformance:** Position Accounting Bridge applies Fill correctly, ReconciliationEngine produces ReconDiff

### Conflict Avoidance
**File Ownership (as per Ownership Matrix):**
- **WP0D (A5) Owns:** `src/execution/reconciliation.py` (new), `src/execution/metrics.py` (new), `src/observability/*` (new), `tests/execution/test_reconciliation.py` (new), `tests/observability/*` (new)
- **WP0A (A2) Owns:** `src/execution/position_ledger.py` (existing), `src/execution/order_ledger.py` (existing)
- **Shared Files:** `src/execution/position_ledger.py` (WP0A owns, WP0D extends) — Coordination required!
- **Integration Coordination:** A0 Integrator mediates WP0A ↔ WP0D interface (Fill event schema, Position Ledger API)

### Open Questions / Coordination Needs
**Q1: Position Ledger Ownership?**
- **Issue:** Position Ledger already exists (WP0A created it), but WP0D extends it (reconciliation, metrics)
- **Proposal:** WP0A owns `src/execution/position_ledger.py`, WP0D adds `src/execution/position_bridge.py` (wrapper/extension)
- **Action:** Coordinate with WP0A (A2) on Position Ledger API (get/apply_fill methods)

**Q2: Fill Event Emission Mechanism?**
- **Issue:** How does WP0A OSM emit Fill events? Direct function call, event bus, pub/sub?
- **Proposal:** Direct function call: `position_bridge.apply_fill(fill)` after OSM state transition
- **Action:** Agree on Fill event schema (must include order_id, symbol, side, quantity, price, fees, timestamp)

**Q3: Exchange Snapshot Source (for Reconciliation)?**
- **Issue:** ReconciliationEngine needs external state to compare; where does it come from?
- **Proposal Phase 0:** Mock/stub external snapshot (no real exchange API in paper/shadow mode)
- **Proposal Phase 1+:** WP0C adapter provides read-only query method (get_open_orders, get_positions)
- **Action:** Define minimal exchange snapshot interface for reconciliation (defer to Phase 1 if not needed in Phase 0)

**Q4: Metrics Storage/Retention?**
- **Issue:** Metrics snapshots accumulate over time; how long to retain?
- **Proposal:** Keep last 7 days, delete older snapshots (configurable)
- **Action:** Document retention policy in implementation report

---

## Next Implementation Run

**Note:** This is a docs-only specification. Code implementation follows in separate PR.

### Implementation Approach (Docs-Only Description)

**Step 1: Position Accounting Bridge (Day 1-2)**
- Implement `src/execution/position_bridge.py`:
  - `PositionAccountingBridge` class with `apply_fill(fill: Fill)` method
  - Fill validation logic (quantity > 0, price > 0, symbol valid)
  - Position update logic (BUY/SELL, position flip handling)
  - PnL calculation (realized on reduction, unrealized on mark-to-market)
  - Cash balance tracking
  - Invariant checks (Position + Cash = Cumulative Fills)
  - Idempotent fill application (duplicate detection)
- Integration: Hook into WP0A OSM (OSM emits Fill event → PositionAccountingBridge.apply_fill())
- Test: `tests/execution/test_position_bridge.py` (fill application, PnL, invariants, idempotency)

**Step 2: Metrics Collector (Day 2-3)**
- Implement `src/execution/metrics.py`:
  - `MetricsCollector` class with `record_order_submitted()`, `record_fill()`, `record_error()`, `record_latency()`
  - Counter metrics (orders_submitted_total, orders_filled_total, orders_rejected_total, reconnects_total)
  - Histogram metrics (order_submission_latency_ms, fill_latency_ms) with p50/p95/p99
  - Ring buffer for bounded storage (max 10k events, FIFO eviction)
  - Periodic snapshot export (`export_metrics() -> Dict`)
- Integration: Hook into WP0A OSM (track order events), WP0C (track routing errors/latency)
- Test: `tests/execution/test_metrics.py` (counters, histograms, percentiles, bounded buffers)

**Step 3: Structured Logger (Day 3)**
- Implement `src/observability/structured_logger.py`:
  - `StructuredLogger` class wrapping standard logging with context injection
  - Log schema: timestamp, level, message, trace_id, session_id, strategy_id, order_id, context
  - JSONL format (one JSON object per line)
  - Log rotation (by size: 100MB, or by time: daily)
  - Log retention (last 7 days, configurable)
  - Disk space check on startup
- Integration: Replace print/log statements in WP0A/WP0C/WP0D with structured logging
- Test: `tests/observability/test_structured_logger.py` (schema, JSONL format, rotation, retention)

**Step 4: ReconciliationEngine (Day 4-5)**
- Implement `src/execution/reconciliation.py`:
  - `ReconciliationEngine` class with `reconcile() -> List[ReconDiff]` method
  - Fetch internal snapshot (Order Ledger, Position Ledger)
  - Fetch external snapshot (mock/stub for Phase 0, real API later)
  - Matching rules (order, fill, position matching)
  - Tolerance thresholds (quantity ±0.1%, price ±0.5%, timestamp ±5s)
  - ReconDiff generation (missing fill, orphan order, quantity mismatch, price drift)
  - Reconciliation report export (JSON/Markdown)
- Integration: Run periodically (hourly/daily), or on-demand via CLI/API
- Test: `tests/execution/test_reconciliation.py` (matching, tolerance, diff generation, report export)

**Step 5: Minimal Dashboard (Day 5)**
- Implement `src/observability/dashboard.py`:
  - `DashboardExporter` class with `export_snapshot() -> Dict` method
  - Aggregate current state (positions, open orders, recent errors, metrics summary)
  - Export to JSON (`reports/observability/dashboard_snapshot_{timestamp}.json`)
  - Periodic refresh (every 5-10 minutes, configurable)
  - Optional: HTTP endpoint for read-only query (defer to Phase 1 if not needed)
- Integration: Run as background task (asyncio, threading, or periodic CLI call)
- Test: `tests/observability/test_dashboard.py` (snapshot schema, export, refresh)

**Step 6: Integration Testing (Day 6)**
- Implement end-to-end tests:
  - `tests/execution/test_wp0d_integration.py`: WP0A → WP0D fill propagation
    - Create order in OSM → submit → fill → verify Position Ledger updated
    - Verify metrics incremented (orders_submitted_total, orders_filled_total)
    - Verify structured log entries created (order_submitted, fill_applied)
  - `tests/execution/test_position_invariants.py`: Verify Position + Cash = Cumulative Fills after BUY/SELL/flip scenarios
  - `tests/execution/test_reconciliation_smoke.py`: Create synthetic discrepancies → verify ReconciliationEngine detects them

**Step 7: Evidence Generation (Day 7)**
- Run periodic snapshots during test session → `reports/observability/metrics_snapshot_*.json` (at least 3)
- Generate structured logging sample → `reports/observability/logging_fields.md` + sample JSONL
- Run reconciliation smoke test → `reports/execution/reconciliation_report_*.json`
- Export position snapshot → `reports/execution/position_snapshot_*.json`
- Export dashboard snapshot → `reports/observability/dashboard_snapshot_*.json`
- Run invariant validation tests → `reports/execution/invariant_validation_*.md`
- Write WP0D completion report: `docs/execution/WP0D_IMPLEMENTATION_REPORT.md`

---

### Implementation Checklist (Gate-Ready)

**Pre-Implementation:**
- [ ] WP0E contracts finalized (Fill, LedgerEntry, ReconDiff types)
- [ ] WP0A Fill event emission mechanism agreed (direct call vs pub/sub)
- [ ] Position Ledger API agreed (WP0A owns, WP0D extends/queries)
- [ ] Ownership Matrix consulted: WP0D owns `src/execution/reconciliation.py`, `src/observability/*`, etc.

**Implementation Sequence:**
- [ ] Implement Position Accounting Bridge (apply_fill, PnL, invariants, idempotency)
- [ ] Implement Metrics Collector (counters, histograms, bounded buffers, export)
- [ ] Implement Structured Logger (JSONL, rotation, retention, context injection)
- [ ] Implement ReconciliationEngine (matching, tolerance, diff generation, report)
- [ ] Implement Minimal Dashboard (snapshot export, periodic refresh)
- [ ] Add WP0A integration hooks (Fill event → Position Bridge, metrics tracking)
- [ ] Add WP0C integration hooks (OrderExecutionResult → metrics tracking)

**Testing:**
- [ ] Unit tests for Position Bridge (fill application, PnL, invariants, idempotency)
- [ ] Unit tests for Metrics Collector (counters, histograms, percentiles, bounded buffers)
- [ ] Unit tests for Structured Logger (schema, JSONL, rotation, retention)
- [ ] Unit tests for ReconciliationEngine (matching, tolerance, diff generation)
- [ ] Integration tests (WP0A → WP0D fill propagation, position invariants)
- [ ] Reconciliation smoke test (synthetic discrepancies → detected)
- [ ] Test coverage >90% for WP0D modules

**Evidence Artifacts:**
- [ ] Metrics snapshot (at least 3 periodic snapshots)
- [ ] Structured logging sample (spec + JSONL sample)
- [ ] Reconciliation report (smoke test with synthetic diffs)
- [ ] Position snapshot (positions + PnL + cash + invariants)
- [ ] Dashboard snapshot (execution state summary)
- [ ] Invariant validation report (Position + Cash = Fills)
- [ ] Integration test results (pytest output)
- [ ] WP0D completion report

**Integration:**
- [ ] Coordinate with WP0A (A2) on Fill event schema + Position Ledger API
- [ ] Coordinate with WP0C (A4) on OrderExecutionResult metadata (execution_time_ms)
- [ ] Verify WP0B (A3) can query Position Ledger (read-only)
- [ ] Link-hygiene check: All references to WP0A, WP0C, WP0E, WP0B valid
- [ ] Update Ownership Matrix: Confirm WP0D file ownership

**Gate Readiness:**
- [ ] All acceptance criteria met (35+ criteria)
- [ ] All evidence artifacts produced
- [ ] CI/tests passing (no failures)
- [ ] Linter clean (ruff format, no errors)
- [ ] Integration Day Plan updated with WP0D merge steps
- [ ] Phase-0 Gate Report updated with WP0D status
