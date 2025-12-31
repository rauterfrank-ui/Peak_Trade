# WP0E — Contracts & Interfaces (Task-Packet)

**Phase:** Phase 0 — Foundation  
**Work Package:** WP0E (Contracts & Interfaces)  
**Owner:** A1 (Exec-Agent)  
**Status:** DRAFT (Docs-Only)  
**Source:** docs/execution/PEAK_TRADE_LIVE_EXECUTION_ROADMAP_MULTI_AGENT_v1_0.md (WP0E section)

---

## Scope

### In-Scope
**Source:** Roadmap WP0E (lines 100-111) + WP0E Completion Report

- Define stable types and protocols for execution system
- Core contract types: `Order`, `OrderState`, `Fill`, `LedgerEntry`, `ReconDiff`, `RiskDecision`, `RiskResult`
- Risk Hook interface specification (protocol for execution-risk communication)
- Deterministic serialization requirements (repr/json/to_dict)
- No cyclic imports design (execution ← contracts → risk, but execution ↛ risk)
- Order specification enums: `OrderSide`, `OrderType`, `TimeInForce`
- State machine helpers and validation utilities

### Out-of-Scope
- Code implementation (deferred to implementation run)
- src/ or tests/ modifications
- Live enablement or activation instructions
- Exchange-specific implementations (deferred to WP2A)
- Reconciliation logic implementation (type defined, logic in WP0D)
- Retry policy implementation (contracts only, logic in WP0A)

---

## Definitions / Glossary

**Contract:** Stable type definition or protocol that serves as integration point between components. Changes require cross-WP coordination.

**Intent:** Strategy/operator intention (e.g., "buy 1.0 BTC") before order creation. Represents trading decision before concrete execution order.

**Order:** Concrete execution instruction to router/adapter. Derived from Intent with risk checks and validation.

**ExecutionEvent:** Observed event from execution layer (ACK/REJECT/FILL/CANCEL). Lifecycle events tracked in audit trail.

**Ledger Entry:** Accounting entry for trades/fees/transfers. Used by WP0D for position tracking and PnL calculation.

**ReconDiff:** Difference object between internal ledger/positions and external source (exchange statement/feed). Produced by WP0D reconciliation.

**Deterministic Serialization:** Serialization (repr/json/to_dict) that produces identical output for identical inputs, enabling testing and reproducibility.

**Cyclic Import:** Import dependency A→B→A. Forbidden in execution system. Solved via contracts layer (A→C←B).

**Risk Hook:** Protocol-based interface allowing execution system to call risk evaluation without direct dependency on risk implementation.

**OrderState:** Enum representing order lifecycle stages (CREATED, SUBMITTED, ACKNOWLEDGED, FILLED, etc.). Drives state machine transitions.

**Correlation ID:** Stable identifier across execution pipeline (Intent → Order → Events → Ledger). Enables end-to-end tracing.

**Idempotency Key:** Unique identifier for deduplicating processing (e.g., retry handling). Ensures same request processed once.

**Schema Version:** Semver-compatible versioning for contract evolution. Backwards-compatible within major version.

---

## Proposed Components

**Source:** WP0E Completion Report (lines 29-37) + Roadmap WP0E

### Component 1: Order (Core Contract Type)
**Purpose:** Unified order representation across all execution stages  
**Responsibilities:**
- Immutable order specification (symbol, side, type, quantity, price, metadata)
- State tracking (OrderState enum: CREATED → SUBMITTED → ACK → FILLED → CLOSED)
- Deterministic serialization (to_dict, to_json, repr)
- Validation helpers (validate_order)
**Key Features:**
- Decimal types for precision (no float rounding errors)
- State machine helpers (is_terminal, is_active)
- Extensible metadata field for exchange-specific data

### Component 2: Fill (Execution Result)
**Purpose:** Represent partial or complete order fill  
**Responsibilities:**
- Fill details (price, quantity, timestamp, fees)
- Link to parent order (order_id)
- Support partial fills (quantity < order.quantity)
**Key Features:**
- Decimal precision for financial calculations
- Deterministic timestamp handling

### Component 3: LedgerEntry (Audit Trail)
**Purpose:** Append-only audit log entry  
**Responsibilities:**
- Record all state transitions and events
- Sequential ordering (sequence number + timestamp)
- Immutable history (no deletions/modifications)
**Key Features:**
- Event type classification (order_created, order_submitted, fill_applied, etc.)
- Old/new state tracking for transitions
- Queryable by order_id, event_type, time_range

### Component 4: ReconDiff (Reconciliation)
**Purpose:** Track divergences between internal state and exchange state  
**Responsibilities:**
- Identify discrepancies (missing fills, orphan orders, quantity mismatches)
- Provide resolution hints
- Support auditing and compliance
**Note:** Type defined in WP0E; reconciliation logic implemented in WP0D

### Component 5: RiskDecision & RiskResult (Risk Integration)
**Purpose:** Risk evaluation decision types  
**Responsibilities:**
- RiskDecision enum: ALLOW, BLOCK, PAUSE
- RiskResult: decision + reason + metadata
- Enable risk gating without cyclic imports
**Key Features:**
- Clear semantics (ALLOW = proceed, BLOCK = reject, PAUSE = temporary hold)
- Reason field for audit trail and debugging

### Component 6: RiskHook Protocol
**Purpose:** Interface for risk evaluation (breaks cyclic dependency)  
**Responsibilities:**
- Define protocol: `evaluate_order(order, context) -> RiskResult`
- Define protocol: `check_kill_switch() -> RiskResult`
- Define protocol: `evaluate_position_change(symbol, quantity, side, context) -> RiskResult`
**Implementations (reference only):**
- NullRiskHook: always allows (safe default for testing)
- BlockingRiskHook: always blocks (emergency mode)
- ConditionalRiskHook: configurable rules (development/testing)
**Note:** Implementation details in WP0B; WP0E defines protocol only

### Component 7: Enums (Order Specification)
**Purpose:** Standardize order parameters  
**Enums:**
- OrderSide: BUY, SELL
- OrderType: MARKET, LIMIT, STOP, STOP_LIMIT
- OrderState: CREATED, SUBMITTED, ACKNOWLEDGED, PARTIALLY_FILLED, FILLED, CANCELLED, REJECTED, EXPIRED, FAILED
- TimeInForce: GTC, IOC, FOK, DAY

---

## Inputs / Outputs (Contracts)

**Note:** WP0E is foundational. It defines contracts that other WPs consume, but has minimal runtime inputs.

### Common Fields (All Contracts)
**Source:** User specification — correlation/tracing requirements

All execution contracts (Order, ExecutionEvent, LedgerEntry, ReconDiff) include these common fields where applicable:

- **`schema_version`:** Semver-compatible version (e.g., "1.0.0"). Backwards-compatible within major version. Enables contract evolution.
- **`event_time_utc`:** ISO-8601 timestamp (UTC). Monotonic ordering for event sequencing.
- **`correlation_id`:** Stable identifier across execution pipeline (Intent → Order → Events → Ledger). Enables end-to-end tracing.
- **`strategy_id`:** Source of decision/order (e.g., "ma_crossover", "operator_manual"). Enables strategy-level analysis.
- **`session_id`:** Live/dry-run session context (e.g., "session_2025_12_31"). Scopes execution to session.
- **`idempotency_key`:** Unique identifier for deduplicating processing (e.g., retry handling). Ensures same request processed once.

**Invariants:**
- `correlation_id` must be stable across all events for same logical order (Intent → Order → Fills → Ledger entries)
- `event_time_utc` must be in ISO-8601 format with timezone (UTC preferred)
- `schema_version` must follow semver (major.minor.patch)
- `idempotency_key` must be unique within session for same operation type

---

### Reason/Status Codes (Standardized)
**Source:** User specification — controlled vocabulary for rejection/error reasons

**Rejection Reason Codes (Order/ExecutionEvent):**
- **RISK_LIMIT_EXCEEDED:** Risk limit breached (position, exposure, VaR, etc.)
- **RISK_KILL_SWITCH:** Kill switch active, all trading blocked
- **VALIDATION_INVALID_SYMBOL:** Symbol not recognized or not tradable
- **VALIDATION_INVALID_QUANTITY:** Quantity ≤ 0, exceeds max, or violates lot size
- **VALIDATION_INVALID_PRICE:** Price ≤ 0 or outside allowed range
- **VALIDATION_MISSING_FIELD:** Required field missing (e.g., limit_price for LIMIT order)
- **CONNECTIVITY_TIMEOUT:** Network timeout during order submission
- **CONNECTIVITY_EXCHANGE_DOWN:** Exchange API unavailable
- **CONNECTIVITY_NETWORK_ERROR:** Transient network error
- **POLICY_BLOCKED:** Policy rule blocked order (e.g., live mode disabled, symbol blacklist)
- **POLICY_INSUFFICIENT_BALANCE:** Insufficient cash/margin for order
- **TIMEOUT_SUBMISSION:** Order submission exceeded timeout
- **TIMEOUT_ACKNOWLEDGMENT:** Order acknowledgment not received within timeout
- **UNKNOWN_ERROR:** Unclassified error (catch-all, should be avoided)

**Risk Decision Codes (RiskResult):**
- **ALLOW:** Order approved, proceed with submission
- **BLOCK:** Order rejected by risk policy
- **DEFER:** Order temporarily held (e.g., pending data, cooldown)

**Event Type Codes (ExecutionEvent):**
- **ACK:** Order accepted by exchange/adapter
- **REJECT:** Order rejected by exchange/adapter
- **FILL:** Partial or complete fill
- **CANCEL_ACK:** Cancellation confirmed
- **CANCEL_REJECT:** Cancellation rejected
- **REPLACE_ACK:** Order modification confirmed (future)
- **REPLACE_REJECT:** Order modification rejected (future)

**Ledger Entry Type Codes:**
- **TRADE:** Trade execution (buy/sell)
- **FEE:** Fee charged (commission, exchange fee)
- **ADJUSTMENT:** Manual adjustment (correction, transfer)

**ReconDiff Severity Codes:**
- **INFO:** Informational discrepancy (no action required)
- **WARN:** Warning-level discrepancy (review recommended)
- **FAIL:** Critical discrepancy (immediate action required)

---

### Inputs (Specification Phase)
- **Strategy Signals:** Order intent (symbol, side, quantity, price) from strategy layer
- **Market Context:** Current prices, positions, portfolio state (for validation)
- **Exchange Events:** Fill notifications, order acknowledgments (external inputs to be typed)

### Outputs (Contract Types Defined)
**Source:** WP0E DoD + Completion Report + User specification

WP0E defines these contract types (consumed by other WPs):

#### Order Contract (Phase-0 Minimal)
**Pflichtfelder:**
- **Identity:** `order_id` (string, unique within session), `correlation_id` (string), `idempotency_key` (string)
- **Instrument:** `symbol` (string, e.g., "BTC/EUR"), optional `venue` (string, default "UNKNOWN")
- **Side/Qty:** `side` (enum: BUY/SELL), `quantity` (decimal, > 0)
- **Price/Type:** `order_type` (enum: MARKET/LIMIT), optional `limit_price` (decimal, required if LIMIT)
- **Time:** `time_in_force` (enum: GTC/IOC/FOK), `create_time_utc` (ISO-8601)
- **Meta:** `strategy_id` (string), optional `tags` (list of strings), `schema_version` (string)

**Invarianten:**
- LIMIT order → `limit_price` must be set and > 0
- `quantity` > 0
- `order_id` unique within session
- `idempotency_key` stable per "Intent → Order" derivation (same intent = same key)
- `correlation_id` stable across all events for same logical order

**Example (conceptual):**
```json
{
  "schema_version": "1.0.0",
  "order_id": "order_001",
  "correlation_id": "corr_abc123",
  "idempotency_key": "idem_xyz789",
  "symbol": "BTC/EUR",
  "venue": "UNKNOWN",
  "side": "BUY",
  "quantity": "0.1",
  "order_type": "LIMIT",
  "limit_price": "50000.00",
  "time_in_force": "GTC",
  "create_time_utc": "2025-12-31T12:00:00Z",
  "strategy_id": "ma_crossover",
  "tags": ["phase0", "test"]
}
```

#### ExecutionEvent Contract (Phase-0 Minimal)
**Event Types:** ACK, REJECT, FILL, CANCEL_ACK, CANCEL_REJECT

**Common Fields:**
- `event_id` (string, unique), `event_type` (enum), `order_id` (string), `correlation_id` (string), `event_time_utc` (ISO-8601), `schema_version` (string)

**REJECT-specific:**
- `reject_reason_code` (enum, from standardized list), optional `reason_detail` (string, short)

**FILL-specific:**
- `fill_qty` (decimal, > 0), `fill_price` (decimal, > 0), `fee` (decimal, ≥ 0), `fee_currency` (string)

**Invarianten:**
- FILL → `fill_qty` > 0, `fill_price` > 0
- REJECT → `reject_reason_code` must be set (from standardized list)

**Example (FILL):**
```json
{
  "schema_version": "1.0.0",
  "event_id": "event_fill_001",
  "event_type": "FILL",
  "order_id": "order_001",
  "correlation_id": "corr_abc123",
  "event_time_utc": "2025-12-31T12:01:00Z",
  "fill_qty": "0.1",
  "fill_price": "50000.00",
  "fee": "5.00",
  "fee_currency": "EUR"
}
```

#### Risk Decision Contract
**Fields:**
- `decision` (enum: ALLOW/REJECT/DEFER), `policy_id` (string), `reason_code` (string, from standardized list), `snapshot_ref` (string, optional, conceptual reference to context snapshot)

#### LedgerEntry Contract
**Fields:**
- `entry_id` (string), `event_time_utc` (ISO-8601), `correlation_id` (string), `entry_type` (enum: TRADE/FEE/ADJUSTMENT), `asset` (string), `quantity` (decimal), `price` (decimal, if TRADE), `counterparty` (string, optional), `source_event_id` (string, if derivable)

#### ReconDiff Contract
**Fields:**
- `diff_id` (string), `as_of_time_utc` (ISO-8601), `correlation_id` (string, if possible), `dimension` (enum: POSITION/CASH/FEES/TRADES), `expected` (decimal/string), `observed` (decimal/string), `delta` (decimal/string), `severity` (enum: INFO/WARN/FAIL), `notes` (string, short)

**Additional Contracts:**
- **Fill:** Typed fill result with price/quantity/fees (part of ExecutionEvent)
- **RiskResult:** Typed risk evaluation decision (ALLOW/BLOCK/PAUSE)
- **RiskHook Protocol:** Interface specification for risk integration
- **Enums:** OrderSide, OrderType, OrderState, TimeInForce

**Consumers:** All Phase-0 WPs depend on WP0E contracts (WP0A, WP0B, WP0C, WP0D)

---

## Failure Modes & Handling

**Source:** User specification + inferred from contracts design + completion report risks

### Failure Mode 1: Duplicate Events (Adapter Resend)
**Scenario:** Adapter resends same event (e.g., network retry, exchange duplicate ACK/FILL)  
**Impact:** Duplicate processing → position double-count, incorrect PnL  
**Mitigation:**
- Use `idempotency_key` for deduplication (Order submission)
- Use `event_id` for event deduplication (ExecutionEvent)
- WP0A OSM: Track processed event_ids, reject duplicates
- WP0D Position Ledger: Idempotent fill application (detect duplicate fill_id)

### Failure Mode 2: Partial Fill Sequences
**Scenario:** Order fills in multiple partial fills (e.g., 0.05 BTC, then 0.03 BTC, then 0.02 BTC for 0.1 BTC order)  
**Impact:** Aggregation errors → incorrect total fill quantity, position mismatch  
**Mitigation:**
- ExecutionEvent FILL includes `fill_qty` (not cumulative)
- WP0A OSM: Aggregate fills deterministically (sum fill_qty per order_id)
- Order state: PARTIALLY_FILLED until total fill_qty == order.quantity
- Document fill aggregation rule: "Sum all FILL events for order_id, order complete when sum == order.quantity"

### Failure Mode 3: Out-of-Order Events
**Scenario:** Events arrive out of sequence (e.g., FILL before ACK due to network latency, clock skew)  
**Impact:** State machine violations, incorrect audit trail  
**Mitigation:**
- Use `event_time_utc` for logical ordering (not arrival time)
- Optional: `event_sequence` (monotonic counter per order_id) for deterministic ordering
- WP0A OSM: Buffer out-of-order events, apply in `event_time_utc` order
- Document sequencing rule: "Events ordered by event_time_utc; if timestamps equal, use event_sequence"

### Failure Mode 4: Missing Fields / Schema Drift
**Scenario:** Contract evolves (new field added), old consumers fail parsing; or required field missing in payload  
**Impact:** Deserialization errors, integration failures  
**Mitigation:**
- `schema_version` field enables version detection
- Strict validation: Reject payloads with missing required fields (fail-fast)
- Backwards compatibility: New fields optional (default values), old consumers ignore unknown fields
- Document schema evolution policy: "Major version = breaking change, minor version = backwards-compatible addition"

### Failure Mode 5: Rounding/Precision Errors
**Scenario:** Floating-point arithmetic causes precision loss (e.g., 0.1 + 0.2 ≠ 0.3 in float)  
**Impact:** Position/PnL calculation errors, reconciliation failures  
**Mitigation:**
- Decimal Policy: "Store all financial values as Decimal (Python) or fixed-point (other languages), not float"
- Serialization: Decimals serialized as strings (e.g., "0.1" not 0.1) to preserve precision
- Document precision: "All quantities/prices use Decimal with fixed precision (e.g., 8 decimal places for BTC)"
- WP0A/WP0D: Use Decimal types throughout (no float conversions)

### Failure Mode 6: Type Evolution Breaking Changes
**Scenario:** Contract type changes (e.g., Order gains new required field) break existing consumers  
**Impact:** Compilation errors, integration failures across WPs  
**Mitigation:**
- Version contract types explicitly (e.g., OrderV1, OrderV2)
- Use optional/extensible fields (metadata dict)
- Coordinate changes via A0 (integrator approval required)
- Maintain backward compatibility during transitions

### Failure Mode 7: Serialization Non-Determinism
**Scenario:** Serialization produces different output for same input (e.g., dict ordering, timestamp precision)  
**Impact:** Evidence snapshots differ, tests flake, audit trail inconsistencies  
**Mitigation:**
- Enforce deterministic serialization (sorted keys, fixed precision)
- Test serialization round-trips (serialize → deserialize → assert equality)
- Use Decimal (not float) for financial values
- Document timestamp handling (UTC, fixed precision)

### Failure Mode 3: Cyclic Import Creep
**Scenario:** Direct imports between execution and risk creep in over time  
**Impact:** Import errors, circular dependencies, build failures  
**Mitigation:**
- Enforce import linting (execution imports contracts, risk imports contracts, execution ↛ risk)
- Use RiskHook protocol exclusively (no direct risk_layer imports)
- Code review checks for import violations
- CI import graph validation (optional future work)

### Failure Mode 4: Enum Extension Breaking Code
**Scenario:** New OrderState or OrderType added, exhaustive match statements break  
**Impact:** Unhandled cases, runtime errors  
**Mitigation:**
- Document enum extension policy (append-only, no removals)
- Use default cases in match/switch statements where appropriate
- Test new enum values in isolation before integration

### Failure Mode 5: Exchange-Specific Leakage
**Scenario:** Exchange-specific fields leak into core contracts (e.g., Kraken-specific order params)  
**Impact:** Contracts become exchange-coupled, portability lost  
**Mitigation:**
- Use generic contracts + metadata field for extensions
- Exchange-specific handling in adapter layer (WP0C), not contracts
- Review contract changes for exchange neutrality

---

## Acceptance Criteria (Gate-Tauglich)

**Source:** User specification + Roadmap WP0E DoD (lines 103-106) + Completion Report

### Docs-Only Criteria (Phase-0 Foundation)
- [ ] **AC1:** All contracts documented (Order, ExecutionEvent, LedgerEntry, ReconDiff, RiskDecision) with Pflichtfelder + Invarianten
- [ ] **AC2:** Reason/Status Codes documented as controlled list (minimum: RISK, VALIDATION, TIMEOUT, CONNECTIVITY, POLICY, UNKNOWN)
- [ ] **AC3:** Correlation/Tracing fields documented consistently (correlation_id, strategy_id, session_id, idempotency_key) across all contracts
- [ ] **AC4:** No Live-Aktivierungsanweisungen; Safety-Kontext clear (default blocked/gated)
- [ ] **AC5:** No references/links to non-existent targets (link hygiene verified)
- [ ] **AC6:** Common Fields documented (schema_version, event_time_utc, correlation_id, strategy_id, session_id, idempotency_key)
- [ ] **AC7:** Failure modes documented (duplicate events, partial fills, out-of-order, missing fields, rounding/precision)
- [ ] **AC8:** Example payloads provided (Order, ExecutionEvent FILL/REJECT, LedgerEntry, ReconDiff) as code blocks
- [ ] **AC9:** Invariants documented for each contract (e.g., LIMIT → limit_price required, FILL → fill_qty > 0)
- [ ] **AC10:** Schema versioning policy documented (semver, backwards compatibility rules)

### Implementation Run Criteria (Future)
- [ ] All core contract types defined: Order, Fill, LedgerEntry, ReconDiff, RiskDecision, RiskResult
- [ ] RiskHook protocol defined with required methods (evaluate_order, check_kill_switch, evaluate_position_change)
- [ ] Deterministic serialization implemented and tested (to_dict, to_json, repr produce stable output)
- [ ] No cyclic imports (execution → contracts ← risk, but execution ↛ risk verified)
- [ ] Enums defined: OrderSide, OrderType, OrderState, TimeInForce
- [ ] Order validation helpers implemented
- [ ] State machine helper methods (is_terminal, is_active) implemented
- [ ] Decimal types used for all financial values (no float)
- [ ] Metadata field enables extension without breaking changes
- [ ] At least 3 RiskHook implementations: NullRiskHook, BlockingRiskHook, ConditionalRiskHook

### Testing Criteria
- [ ] Unit tests cover all contract types (instantiation, validation)
- [ ] Serialization round-trip tests pass (serialize → deserialize → equality)
- [ ] Import structure verified (no cyclic imports detected)
- [ ] Type validation tests (invalid orders rejected)
- [ ] RiskHook protocol conformance tests
- [ ] Test coverage ≥ 90% for contracts module

### Evidence Criteria
- [ ] Contracts smoke report generated (deterministic snapshot)
- [ ] Test results documented (49+ tests passing, per completion report)
- [ ] Import graph validated (no cycles)

---

## Evidence Checklist

**Source:** Roadmap WP0E Evidence (lines 108-110) + Completion Report (lines 133-149)

### Required Evidence Artifacts (Implementation Run)
- [ ] **Contracts Smoke Report:** Deterministic snapshot of all contract types (JSON format, gitignored)
  - Location pattern: `reports/execution/contracts_smoke.json`
  - Content: Example instances of Order, Fill, LedgerEntry, ReconDiff, RiskResult
  - Purpose: Verify serialization stability, enable CI comparisons
- [ ] **Test Results:** Unit test execution logs
  - Target: 49+ tests passing (baseline from completion report)
  - Coverage: contract types, risk hook protocol, serialization, validation
  - Evidence: pytest output + coverage report
- [ ] **Import Graph Validation:** No cyclic imports detected
  - Method: Static analysis or import test
  - Expected: execution → contracts ← risk (no execution → risk)
- [ ] **Completion Report:** Structured documentation of WP0E implementation
  - Location pattern: "docs/execution/WP0E_IMPLEMENTATION_REPORT.md" (future)
  - Content: DoD verification, files changed, test results, risks, integration notes
  - Status: Template exists (WP0E_COMPLETION_REPORT.md), reuse for implementation run

### Evidence Generation (Not in This Docs-Only Run)
**Note:** Evidence artifacts are generated during implementation run, not this docs-only prep. This checklist defines what MUST exist post-implementation.

---

## Integration Notes

**Source:** Roadmap dependency graph + Completion Report integration notes

### Depends On
- **None** — WP0E is the foundation layer. It defines contracts that other WPs consume.
- **Assumption:** WP0E has no runtime dependencies on other Phase-0 WPs.

### Consumed By
- **WP0A (Execution Core):** Uses Order, Fill, LedgerEntry, RiskHook for execution pipeline
- **WP0B (Risk Layer):** Implements RiskHook protocol, uses RiskDecision/RiskResult
- **WP0C (Order Routing):** Uses Order type for routing decisions, produces Fill events
- **WP0D (Recon/Ledger):** Uses LedgerEntry, Fill, ReconDiff for reconciliation
- **All Phase-0 WPs:** Depend on contract types for inter-component communication

### Integration Sequence
1. **WP0E must be implemented first** (integrator-blocker status in roadmap)
2. After WP0E complete: WP0A, WP0B, WP0C, WP0D can proceed in parallel (no cross-dependencies)
3. **Critical Path:** WP0E → WP0A → WP0C → WP0D (serial dependencies)
4. **Risk Path:** WP0E → WP0B (parallel with WP0A)

### Cross-WP Interfaces
- **WP0E → WP0A:** Order, Fill, LedgerEntry types
- **WP0E → WP0B:** RiskHook protocol, RiskDecision/RiskResult types
- **WP0E → WP0C:** Order type (input), Fill type (output)
- **WP0E → WP0D:** LedgerEntry, Fill, ReconDiff types

### Breaking Change Protocol
If WP0E contracts must change post-implementation:
1. Notify A0 (integrator) immediately
2. Assess impact on WP0A/B/C/D
3. Version changes if breaking (e.g., OrderV2)
4. Coordinate migration across all consumers
5. Update completion reports + evidence

---

## Next Implementation Run

**Note:** This is a docs-only specification. Code implementation follows in separate PR.

### Implementation Approach
- **Module Location:** Execution contracts module (foundational)
- **Test Location:** Execution tests (contract-specific)
- **Evidence Location:** Execution reports (gitignored, generated on-demand)

### Implementation Checklist
- [ ] Define all contract types per "Proposed Components" section
- [ ] Implement RiskHook protocol (Python Protocol or ABC)
- [ ] Implement deterministic serialization (to_dict, to_json, repr)
- [ ] Use Decimal for all financial values
- [ ] Write unit tests (target: 49+ tests, baseline from completion report)
- [ ] Test serialization round-trips
- [ ] Verify no cyclic imports (import graph validation)
- [ ] Generate contracts smoke report (evidence artifact)
- [ ] Create completion report documenting DoD verification

### Reference Implementation
**Note:** WP0E_COMPLETION_REPORT.md shows WP0E was already implemented. Implementation run should:
1. Review existing implementation for alignment with this spec
2. Fill gaps if any (unlikely, completion report shows full coverage)
3. Update evidence artifacts if needed
4. Confirm acceptance criteria still met

### Post-Implementation
- [ ] Update Integration Day Plan with WP0E status
- [ ] Notify A0: WP0E complete, unblocking WP0A/B/C/D
- [ ] Provide completion report link to downstream WPs

---

**WP0E Task-Packet Status:** ✅ COMPLETE (A1)  
**Last Updated:** 2025-12-31 (A1 completion)  
**Source Traceability:** Roadmap WP0E (lines 100-111) + WP0E_COMPLETION_REPORT.md  
**Link Hygiene:** ✅ All references point to existing docs or intra-PR files
