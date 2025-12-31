# WP0A — Execution Core v1 (Task-Packet)

**Phase:** Phase 0 — Foundation  
**Work Package:** WP0A (Execution Core v1)  
**Owner:** A2 (Pipeline-Agent)  
**Status:** DRAFT (Docs-Only)  
**Source:** docs/execution/PEAK_TRADE_LIVE_EXECUTION_ROADMAP_MULTI_AGENT_v1_0.md (WP0A section)

---

## Scope

### In-Scope
**Source:** Roadmap WP0A (lines 114-133) + WP0A Completion Report

- Order State Machine (OSM) with deterministic, idempotent state transitions
- Order Ledger as single source of truth for order tracking and history
- Position Ledger as single source of truth for positions, PnL (realized/unrealized)
- Audit Log for append-only, deterministic audit trail
- Retry Policy with exponential backoff, jitter, and error taxonomy
- Risk hook integration (pre-submission checks via WP0E RiskHook protocol)
- Ledger entry generation for all state transitions
- Crash-restart resilience (in-memory rebuild from ledger)
- State transition validation (VALID_TRANSITIONS map)
- Position invariants: Position + Cash = Cumulative Fills, PnL = (Mark - Entry) × Qty

### Out-of-Scope
- Code implementation (deferred to implementation run)
- src/ or tests/ modifications
- Live enablement or activation instructions
- Persistence layer (database, file storage) — MVP is in-memory only
- Thread safety / concurrency (single-threaded MVP)
- Exchange-specific logic (deferred to WP0C routing/adapter)
- Reconciliation logic (deferred to WP0D)

---

## Definitions / Glossary

**Pipeline:** Deterministic execution flow from Intent/Decision to Event processing. Orchestrates stages (validation, risk, routing, execution, post-trade).

**Gate:** Hard abort/block decision point. Default NO-GO in live context (safety-first). Examples: Risk Gate (BLOCK), Kill Switch (BLOCKED).

**Post-Trade:** Processing after ExecutionEvent received (ledger updates, recon preparation, audit trail).

**Intent:** Strategy/operator decision before order creation (concept: "buy 1.0 BTC"). Converted to Order after validation and risk check.

**Order State Machine (OSM):** Deterministic finite state machine managing order lifecycle. Ensures valid transitions and idempotency.

**Idempotent Transition:** Transition that can be applied multiple times with same result (e.g., submit already-submitted order → success).

**Single Source of Truth (SSOT):** Authoritative data store for a domain. Order Ledger = SSOT for orders, Position Ledger = SSOT for positions.

**Audit Log:** Append-only, immutable record of all events and state changes. Enables reconstruction and compliance.

**Retry Policy:** Strategy for handling transient failures with exponential backoff, jitter, and error classification.

**Position Ledger:** Tracks net positions per symbol, average entry price, realized/unrealized PnL, cash balance.

**Fill:** Execution result (partial or complete) applied to order and position.

**Crash-Restart Resilience:** Ability to rebuild in-memory state from persistent audit log after system crash.

**Orchestrator:** Pipeline owner responsible for stage sequencing, correlation, idempotency, stop criteria enforcement.

---

## Proposed Components

**Source:** Roadmap WP0A DoD (lines 118-123) + WP0A Completion Report (lines 26-48, 59-97)

### Component 1: Order State Machine (OSM)
**Purpose:** Manage order lifecycle with deterministic, idempotent state transitions  
**Responsibilities:**
- Enforce valid state transitions (via VALID_TRANSITIONS map)
- Integrate risk checks before submission (via WP0E RiskHook protocol)
- Generate ledger entries for all transitions
- Ensure idempotency (applying same transition twice = success)
- Validate transitions and reject invalid ones with clear errors

**State Flow:**
```
CREATED → SUBMITTED → ACKNOWLEDGED → PARTIALLY_FILLED → FILLED (terminal)
                                  ↘ FILLED (terminal)
CREATED/SUBMITTED/ACKNOWLEDGED → CANCELLED (terminal)
CREATED/SUBMITTED/ACKNOWLEDGED → REJECTED (terminal)
CREATED/SUBMITTED/ACKNOWLEDGED → EXPIRED (terminal)
CREATED/SUBMITTED/ACKNOWLEDGED → FAILED (terminal)
```

**Key Methods (Conceptual):**
- `create_order()` - Initialize order in CREATED state
- `submit_order()` - CREATED → SUBMITTED (with risk check)
- `acknowledge_order()` - SUBMITTED → ACKNOWLEDGED (exchange ACK)
- `apply_fill()` - ACKNOWLEDGED → PARTIALLY_FILLED or FILLED
- `cancel_order()` - Any non-terminal → CANCELLED
- `reject_order()` - Any non-terminal → REJECTED
- `fail_order()` - Any non-terminal → FAILED

**Risk Integration:**
- Pre-submission: Call RiskHook.evaluate_order()
- If BLOCK → reject submission, remain in CREATED
- If PAUSE → hold submission, retry later
- If ALLOW → proceed to SUBMITTED

### Component 2: Order Ledger
**Purpose:** Single source of truth for order tracking and history  
**Responsibilities:**
- Store all orders with current state
- Track order history (all transitions)
- Query orders by ID, symbol, state, time range
- Provide order snapshots for reconciliation
- Support deterministic serialization (JSON export)

**Key Features:**
- In-memory storage (MVP, persistence deferred)
- Efficient lookups (by order_id, symbol, state)
- Immutable history (transitions recorded, not modified)

### Component 3: Position Ledger
**Purpose:** Single source of truth for positions and PnL  
**Responsibilities:**
- Track net position per symbol (long/short/flat)
- Calculate volume-weighted average entry price
- Calculate realized PnL (on position reductions)
- Calculate unrealized PnL (mark-to-market)
- Track cash balance (updated on fills)
- Maintain fill history per symbol

**Position Logic:**
- **BUY fill:** Increase position, decrease cash
- **SELL fill:** Decrease position, increase cash
- **Position flip:** Long → Short or Short → Long handled correctly
- **Realized PnL:** Tracked when position reduced (close long/short)
- **Unrealized PnL:** (Current Mark Price - Avg Entry Price) × Position Quantity

**Invariants:**
- Position + Cash = Cumulative Fills
- PnL = (Mark Price - Avg Entry) × Quantity

### Component 4: Audit Log
**Purpose:** Append-only, deterministic audit trail  
**Responsibilities:**
- Record all state transitions and events
- Maintain sequential ordering (sequence number + timestamp)
- Support queries (by order_id, event_type, time_range)
- Enable crash-restart reconstruction
- Provide JSON export for persistence/compliance

**Design Principles:**
- **Append-only:** No deletions or modifications
- **Immutable:** Past entries never change
- **Deterministic:** Same inputs → same entries
- **Queryable:** Efficient filtering and retrieval

**Entry Structure (Conceptual):**
- Sequence number (monotonic)
- Timestamp (UTC, deterministic precision)
- Event type (order_created, order_submitted, fill_applied, etc.)
- Order ID
- Old state / New state (for transitions)
- Details (metadata, fill info, error messages)

### Component 5: Retry Policy
**Purpose:** Handle transient failures with exponential backoff and error taxonomy  
**Responsibilities:**
- Classify errors (RETRYABLE / NON_RETRYABLE / FATAL)
- Apply exponential backoff (delay *= base^attempt)
- Add jitter to avoid thundering herd
- Enforce max retries cap
- Log retry attempts for debugging

**Error Taxonomy:**
- **RETRYABLE:** NetworkError, TimeoutError, ConnectionError, ServiceUnavailable, RateLimitExceeded
- **NON_RETRYABLE:** ValidationError, ValueError, InvalidOrder, InsufficientBalance, OrderRejected
- **FATAL:** System-level failures requiring operator intervention

**Backoff Strategy:**
- Base delay (e.g., 100ms)
- Exponential multiplier (e.g., delay *= 2^attempt)
- Jitter (random offset to spread retries)
- Max retries (e.g., 5 attempts)
- Max delay cap (e.g., 30s)

---

### Component 6: Pipeline Stages (Phase-0 Orchestration)
**Source:** User specification — end-to-end flow from Intent to Recon Hand-off

**Purpose:** Document deterministic execution pipeline with clear stage boundaries and responsibilities.

**Stage Map (Phase-0):**

**1. Intent Intake**
- **Source:** Strategy layer / operator
- **Input:** Trading decision (symbol, side, quantity, price, strategy_id)
- **Output:** Intent concept (not yet Order)
- **Responsibility:** Orchestrator receives intent, generates correlation_id, idempotency_key

**2. Contract Validation**
- **Source:** WP0E invariants
- **Input:** Intent → Order (WP0E contract)
- **Validation:** Check Pflichtfelder (quantity > 0, LIMIT → limit_price set, etc.)
- **Output:** Valid Order OR Rejection (reason: VALIDATION_*)
- **Responsibility:** Orchestrator applies WP0E invariants

**3. Pre-Trade Risk Gate**
- **Source:** WP0B Risk Runtime
- **Input:** Order + Context (positions, exposure, limits)
- **Process:** Call RiskHook.evaluate_order(order, context) → RiskResult
- **Output:** RiskDecision (ALLOW/BLOCK/DEFER) + reason_code
- **Responsibility:** Risk Runtime produces decision; Orchestrator enforces
- **Gate Logic:**
  - ALLOW → proceed to Stage 4 (Route Selection)
  - BLOCK → reject order, emit REJECTED event (reason: RISK_*)
  - DEFER → hold order, retry later (bounded retries)

**4. Route Selection**
- **Source:** WP0C Router
- **Input:** Order + ExecutionMode (paper/shadow/testnet/live_blocked)
- **Process:** Router selects Adapter based on mode + policy
- **Output:** Selected Adapter OR Rejection (reason: POLICY_BLOCKED, no executor)
- **Responsibility:** Router (WP0C) selects adapter; Orchestrator coordinates
- **Note:** Phase-0 default: live_blocked (no real exchange routing)

**5. Adapter Dispatch**
- **Source:** WP0C Adapter
- **Input:** Order + idempotency_key
- **Process:** Adapter.execute_order(order) → OrderExecutionResult
- **Output:** ExecutionEvent (ACK/REJECT/FILL) OR Timeout
- **Responsibility:** Adapter encapsulates external interaction; Orchestrator handles timeout/retry
- **Timeout:** 30s default, configured per adapter
- **Idempotency:** idempotency_key prevents duplicate submission on retry

**6. Execution Event Handling**
- **Input:** ExecutionEvent (ACK/REJECT/FILL/CANCEL_ACK from adapter)
- **Process:** Parse event → apply to OSM → update Order Ledger
- **Event Types:**
  - **ACK:** Order accepted → SUBMITTED → ACKNOWLEDGED
  - **REJECT:** Order rejected → REJECTED (reason from adapter)
  - **FILL:** Order filled (partial/full) → PARTIALLY_FILLED or FILLED → apply to Position Ledger
  - **CANCEL_ACK:** Order cancelled → CANCELLED
- **Output:** Updated Order state, emitted Fill event (if FILL)
- **Responsibility:** Orchestrator applies event to OSM, emits downstream events

**7. Post-Trade Hooks**
- **Input:** Fill event (from Stage 6)
- **Process:**
  - Generate Audit Log entry (LedgerEntry)
  - Update Position Ledger (apply fill → position, PnL, cash)
  - Emit Fill event to WP0D (Position Accounting Bridge)
- **Output:** LedgerEntry, Position update, Fill event propagation
- **Responsibility:** Orchestrator coordinates; Position Ledger (WP0D) consumes Fill event

**8. Recon Hand-off**
- **Input:** Order Ledger snapshot, Position Ledger snapshot
- **Process:** Prepare data for WP0D ReconciliationEngine (concept: compare internal vs external)
- **Output:** Recon preparation data (snapshots for matching)
- **Responsibility:** Orchestrator provides snapshots to WP0D on-demand
- **Note:** Phase-0: No real exchange data; recon is conceptual/smoke test

**Pipeline Responsibilities:**
- **Orchestrator (Pipeline Owner — WP0A):**
  - Stage sequencing (1 → 2 → 3 → ... → 8)
  - Correlation tracking (correlation_id stable across all stages)
  - Idempotency enforcement (idempotency_key prevents duplicate processing)
  - Stop criteria enforcement (BLOCK → halt, TIMEOUT → controlled failure)
- **Risk Runtime (WP0B):** Produces ALLOW/REJECT/DEFER decisions with reason codes
- **Router (WP0C):** Selects adapter based on policy/config
- **Adapter (WP0C):** Encapsulates external interaction (Phase-0: stubbed/mocked)
- **Auditor (WP0A):** Produces structured audit trail (LedgerEntry for all transitions)

---

## Inputs / Outputs (Contracts)

**Source:** WP0E contracts + Roadmap WP0A dependencies

### Inputs
- **Order (from WP0E):** Typed order specification (symbol, side, type, quantity, price)
- **RiskResult (from WP0B):** Risk evaluation decision (ALLOW/BLOCK/PAUSE) via RiskHook protocol
- **Fill Events (from WP0C):** Execution results from order routing/adapter layer
- **Market Context:** Current prices for PnL calculation (mark-to-market)

### Outputs
- **Order with State:** Order + current OrderState (CREATED, SUBMITTED, ACKNOWLEDGED, FILLED, etc.)
- **LedgerEntry (to WP0D):** Audit trail entries for all state transitions
- **Position State:** Current positions per symbol (quantity, avg entry, PnL)
- **Cash Balance:** Current cash after fills applied
- **Execution Decisions:** Submit/cancel/retry decisions based on OSM logic

**Contracts Used (from WP0E):**
- Order (input/output)
- OrderState enum
- Fill (input from WP0C)
- LedgerEntry (output to audit log)
- RiskHook protocol (for risk integration)
- RiskResult (input from WP0B)

---

## Failure Modes & Handling

**Source:** Completion Report risks (lines 175-199) + inferred from OSM/ledger design

### Failure Mode 1: Invalid State Transition
**Scenario:** Attempt to transition from invalid current state (e.g., submit already-filled order)  
**Impact:** Order stuck in wrong state, execution flow broken, audit trail inconsistent  
**Mitigation:**
- VALID_TRANSITIONS map enforces allowed transitions
- Validation before state change
- Clear error messages for invalid transitions
- Idempotency: re-applying valid transition = success (no-op)

### Failure Mode 2: Risk Hook Failure
**Scenario:** RiskHook.evaluate_order() raises exception or times out  
**Impact:** Order submission blocked, unable to proceed  
**Mitigation:**
- Timeout on risk evaluation (e.g., 5s)
- Default to BLOCK on risk hook failure (safe default)
- Log risk hook errors for debugging
- Retry transient failures (network errors)
- Fallback to NullRiskHook in degraded mode (operator-approved only)

### Failure Mode 3: Ledger Invariant Violation
**Scenario:** Position + Cash ≠ Cumulative Fills after fill application  
**Impact:** Accounting error, PnL incorrect, compliance risk  
**Mitigation:**
- Validate invariants after each fill
- Assert invariants in tests
- Detailed logging of fill applications
- Reconciliation checks (WP0D) detect violations
- Halt execution if invariant violated (fail-safe)

### Failure Mode 4: Crash Before Audit Log Persistence
**Scenario:** System crashes after state change but before audit log persisted  
**Impact:** State lost, unable to reconstruct, orphan orders  
**Mitigation:**
- In-memory MVP: Accept data loss (acceptable for Phase-0)
- Future: Write-ahead logging (WAL) before state changes
- Future: Periodic snapshots of ledgers
- Crash-restart simulation tests validate reconstruction logic

### Failure Mode 5: Retry Exhaustion
**Scenario:** Transient error persists beyond max retries  
**Impact:** Order submission fails permanently  
**Mitigation:**
- Exponential backoff with jitter reduces load
- Max retries tuned to balance responsiveness + resilience
- Non-retryable errors fail fast (no retry waste)
- Dead letter queue (DLQ) for exhausted retries (future)
- Operator alerts on repeated failures

### Failure Mode 6: Race Condition (Multi-threaded)
**Scenario:** Concurrent access to Order/Position ledgers (out of scope for MVP)  
**Impact:** State corruption, lost updates, inconsistent reads  
**Mitigation:**
- MVP: Single-threaded execution (no concurrency)
- Future: Locking/transactions for thread safety
- Document single-threaded constraint in DoD

### Failure Mode 7: Fill Duplication
**Scenario:** Same fill applied twice (e.g., exchange sends duplicate fill event)  
**Impact:** Position doubled, PnL incorrect  
**Mitigation:**
- Fill idempotency: check if fill already applied (by fill_id)
- Deduplication logic in fill handler
- Audit log tracks all fills (detect duplicates)
- Reconciliation (WP0D) detects over-fills

---

## Acceptance Criteria (Gate-Tauglich)

**Source:** User specification + Roadmap WP0A DoD (lines 118-128) + Completion Report

### Docs-Only Criteria (Phase-0 Foundation)
- [ ] **AC1:** Stage Map clearly described (8 stages: Intent Intake → Recon Hand-off), including gate points and default blocking
- [ ] **AC2:** Inputs/Outputs mapped to WP0E contracts (no contradictions with Order, ExecutionEvent, LedgerEntry, ReconDiff)
- [ ] **AC3:** Risk Gate Integration (WP0B) clearly defined: when ALLOW/REJECT/DEFER applies, what happens at each decision
- [ ] **AC4:** Router/Adapter Boundary (WP0C) cleanly separated (timeouts/retries/idempotency conceptually documented)
- [ ] **AC5:** Downstream Hand-off (WP0D) clearly described (ledger/recon outputs, Fill event propagation)
- [ ] **AC6:** No Live-Enablement instructions; docs-only (safety-first, default blocked)
- [ ] **AC7:** No references/links to non-existent targets (link hygiene verified)
- [ ] **AC8:** Pipeline responsibilities documented (Orchestrator, Risk Runtime, Router, Adapter, Auditor)
- [ ] **AC9:** Failure modes documented for pipeline stages (validation fail, risk reject, adapter timeout, duplicate dispatch, out-of-order events)
- [ ] **AC10:** Sequenzdiagramm (textual) provided for SUCCESS and REJECT cases

### Order State Machine Criteria (Implementation)
- [ ] All required states defined: CREATED, SUBMITTED, ACKNOWLEDGED, PARTIALLY_FILLED, FILLED, CANCELLED, REJECTED, EXPIRED, FAILED
- [ ] State transitions validated via VALID_TRANSITIONS map
- [ ] Idempotent transitions implemented (re-apply = success)
- [ ] Invalid transitions rejected with clear errors
- [ ] Risk hook integration: submit_order() calls RiskHook.evaluate_order()
- [ ] Risk BLOCK decision prevents submission
- [ ] Ledger entry generated for every transition
- [ ] State machine coverage: all transitions tested

### Order Ledger Criteria
- [ ] Single source of truth for orders implemented
- [ ] Order lookup by ID, symbol, state, time range
- [ ] Order history tracked (all transitions)
- [ ] Deterministic JSON export
- [ ] In-memory storage (MVP)

### Position Ledger Criteria
- [ ] Single source of truth for positions implemented
- [ ] Position tracking per symbol (long/short/flat)
- [ ] Volume-weighted average entry price calculated
- [ ] Realized PnL tracked on position reductions
- [ ] Unrealized PnL calculated: (Mark - Entry) × Quantity
- [ ] Cash balance updated on fills
- [ ] Position flips handled (long ↔ short)
- [ ] Invariants validated: Position + Cash = Cumulative Fills
- [ ] Invariants validated: PnL = (Mark - Entry) × Qty

### Audit Log Criteria
- [ ] Append-only log implemented
- [ ] Sequential ordering (sequence number + timestamp)
- [ ] Query support (order_id, event_type, time_range)
- [ ] JSON export for persistence
- [ ] No deletions or modifications (immutability enforced)
- [ ] All state transitions logged

### Retry Policy Criteria
- [ ] Error taxonomy defined (RETRYABLE / NON_RETRYABLE / FATAL)
- [ ] Exponential backoff implemented
- [ ] Jitter added to backoff
- [ ] Max retries enforced
- [ ] Max delay cap enforced
- [ ] Retry attempts logged

### Testing Criteria
- [ ] State transition matrix tested (all valid transitions)
- [ ] Idempotency tests pass
- [ ] Ledger invariant tests pass
- [ ] Crash-restart simulation test implemented
- [ ] Integration test: full order lifecycle (create → submit → ack → fill → close)
- [ ] Test coverage ≥ 90% for execution core modules
- [ ] 12+ smoke tests passing (baseline from completion report)

### Evidence Criteria
- [ ] State machine coverage report generated
- [ ] Crash-restart simulation evidence generated
- [ ] Test results documented

---

## Evidence Checklist

**Source:** User specification + Roadmap WP0A Evidence (lines 130-132) + Completion Report evidence sections

### Required Evidence Artifacts (Docs-Only Phase)
- [ ] **EV1: Sequenzdiagramm (textuell) für SUCCESS und REJECT-Fälle**

**SUCCESS Flow (Intent → Fill):**
```
1. Strategy → Orchestrator: Intent (symbol=BTC/EUR, side=BUY, qty=0.1, price=50000)
2. Orchestrator: Generate correlation_id=corr_123, idempotency_key=idem_456
3. Orchestrator: Validate Intent → Order (WP0E invariants) ✓
4. Orchestrator → Risk Runtime (WP0B): evaluate_order(order_001, context)
5. Risk Runtime → Orchestrator: RiskResult(decision=ALLOW)
6. Orchestrator: OSM CREATED → SUBMITTED
7. Orchestrator → Router (WP0C): route(order_001, mode=paper)
8. Router → Adapter: execute_order(order_001)
9. Adapter → Orchestrator: ExecutionEvent(ACK)
10. Orchestrator: OSM SUBMITTED → ACKNOWLEDGED
11. Adapter → Orchestrator: ExecutionEvent(FILL, qty=0.1, price=50000)
12. Orchestrator: OSM ACKNOWLEDGED → FILLED
13. Orchestrator → Position Ledger (WP0D): apply_fill(fill)
14. Orchestrator → Audit Log: LedgerEntry(TRADE)
15. END: Order FILLED, Position updated
```

**REJECT Flow (Risk Block):**
```
1. Strategy → Orchestrator: Intent (symbol=BTC/EUR, side=BUY, qty=10.0)
2. Orchestrator: Generate correlation_id, idempotency_key
3. Orchestrator: Validate Intent → Order ✓
4. Orchestrator → Risk Runtime (WP0B): evaluate_order(order_002)
5. Risk Runtime: Check limits → Position 0.5 + 10.0 > Max 1.0
6. Risk Runtime → Orchestrator: RiskResult(decision=BLOCK, reason=RISK_LIMIT_EXCEEDED)
7. Orchestrator: OSM CREATED → REJECTED
8. Orchestrator → Audit Log: LedgerEntry(ORDER_REJECTED, reason=RISK_LIMIT_EXCEEDED)
9. END: Order REJECTED, No adapter call, No position change
```

**REJECT Flow (Validation Fail):**
```
1. Strategy → Orchestrator: Intent (qty=-0.1)
2. Orchestrator: Validate Intent → Order
3. Orchestrator: Check quantity > 0 ✗ → VALIDATION_INVALID_QUANTITY
4. Orchestrator: Reject immediately (no Order created)
5. Orchestrator → Audit Log: LedgerEntry(VALIDATION_FAILED)
6. END: Order REJECTED (pre-creation)
```

- [ ] **EV2: Audit Trail Spec (minimal fields)**
  - Fields: correlation_id, order_id, event_type, event_time_utc, old_state, new_state, reason_code, decision, metadata
  - Format: LedgerEntry (WP0E contract)

- [ ] **EV3: Gate Report Einträge (WP0A "PASS (Docs)")**
  - Content: All AC1-AC10 criteria met, no blockers

### Required Evidence Artifacts (Implementation Run)
- [ ] **State Machine Coverage Report:** Document all state transitions tested
  - Location pattern: `reports/execution/state_machine_coverage.md`
  - Content: Transition matrix (from_state → to_state), idempotency tests, invalid transition tests
  - Purpose: Verify OSM completeness, demonstrate gate-tauglich quality
- [ ] **Crash-Restart Simulation:** Evidence of in-memory rebuild from audit log
  - Location pattern: `reports/execution/crash_restart_simulation.json`
  - Content: Scenario (orders submitted, crash, restart), state before/after, validation results
  - Purpose: Prove resilience, demonstrate audit log sufficiency
- [ ] **Ledger Invariant Tests:** Evidence of position/cash invariants validated
  - Content: Test results showing Position + Cash = Cumulative Fills
  - Purpose: Prove accounting correctness
- [ ] **Test Results:** Comprehensive test execution logs
  - Target: 12+ tests passing (baseline from completion report)
  - Coverage: OSM (2 tests), Order Ledger (2), Position Ledger (2), Audit Log (2), Retry Policy (3), Integration (1+)
  - Evidence: pytest output + coverage report
- [ ] **Completion Report:** Structured documentation of WP0A implementation
  - Location pattern: `docs/execution/WP0A_IMPLEMENTATION_REPORT.md`
  - Content: DoD verification, files changed, test results, risks, integration notes
  - Status: Template exists (WP0A_COMPLETION_REPORT.md), reuse for implementation run

### Evidence Generation (Not in This Docs-Only Run)
**Note:** Evidence artifacts are generated during implementation run, not this docs-only prep. This checklist defines what MUST exist post-implementation.

---

## Integration Notes

**Source:** Roadmap dependency graph + Phase-0 WP interdependencies

### Depends On
- **WP0E (Contracts & Interfaces):** REQUIRED, BLOCKING
  - Uses: Order, OrderState, Fill, LedgerEntry types
  - Uses: RiskHook protocol for risk integration
  - Integration Point: All WP0A components consume WP0E contracts
  - **Critical:** WP0E must be implemented before WP0A (integrator-blocker)

### Consumed By
- **WP0B (Risk Layer):** RiskHook.evaluate_order() called by OSM.submit_order()
  - Integration Point: Pre-submission risk check
  - Data Flow: WP0A (Order) → WP0B (RiskResult) → WP0A (proceed/block)
- **WP0C (Order Routing):** Consumes Order + state for routing decisions
  - Integration Point: WP0A provides orders to route
  - Data Flow: WP0A (Order + state) → WP0C (routing) → WP0C (Fill) → WP0A (apply_fill)
- **WP0D (Recon/Ledger):** Consumes LedgerEntry, Fill for reconciliation
  - Integration Point: Audit log + fill history
  - Data Flow: WP0A (LedgerEntry, Fill) → WP0D (reconciliation) → WP0D (ReconDiff)

### Integration Sequence
1. **WP0E first (blocker):** Contracts must exist before WP0A
2. **WP0A implementation:** Can proceed once WP0E complete
3. **Parallel with WP0B:** WP0A and WP0B can develop in parallel (both depend only on WP0E)
4. **WP0C after WP0A:** Routing needs Order + state from WP0A
5. **WP0D after WP0A:** Recon needs LedgerEntry + Fill from WP0A

**Critical Path:** WP0E → WP0A → WP0C → WP0D (serial dependencies)

### Cross-WP Interfaces
- **WP0A → WP0B (Risk):**
  - Call: `RiskHook.evaluate_order(order, context) -> RiskResult`
  - Timing: Before CREATED → SUBMITTED transition
  - Handling: ALLOW=proceed, BLOCK=reject, PAUSE=retry later
- **WP0A → WP0C (Routing):**
  - Input to WP0C: Order + current state
  - Output from WP0C: Fill events
  - Timing: After SUBMITTED → ACKNOWLEDGED
- **WP0A → WP0D (Recon):**
  - Input to WP0D: LedgerEntry stream, Fill history
  - Output from WP0D: ReconDiff (if divergence detected)
  - Timing: Continuous (audit log) + periodic (reconciliation runs)

### Integration Risks
1. **Risk Hook Latency:** If WP0B risk evaluation is slow, submission path blocked
   - Mitigation: Timeout on risk evaluation (e.g., 5s), default to BLOCK
2. **Fill Duplication:** If WP0C sends duplicate fill events, position corrupted
   - Mitigation: Fill deduplication in WP0A, idempotency checks
3. **Audit Log Completeness:** If WP0D requires fields not in LedgerEntry, recon fails
   - Mitigation: Coordinate LedgerEntry schema with WP0D needs (via A0)

### Breaking Change Protocol
If WP0A must change interfaces (e.g., LedgerEntry schema):
1. Notify A0 + affected WPs (WP0B/C/D)
2. Version changes if breaking
3. Coordinate migration
4. Update completion reports

---

## Next Implementation Run

**Note:** This is a docs-only specification. Code implementation follows in separate PR.

### Implementation Approach
- **Module Locations:** Execution core modules (OSM, ledgers, retry policy)
- **Test Locations:** Execution tests (unit + integration)
- **Evidence Locations:** Execution reports (gitignored, generated on-demand)

### Implementation Checklist
- [ ] Implement Order State Machine per "Proposed Components" (CREATED → ... → FILLED)
- [ ] Implement Order Ledger (single source of truth)
- [ ] Implement Position Ledger (PnL tracking, invariants)
- [ ] Implement Audit Log (append-only, sequential)
- [ ] Implement Retry Policy (exponential backoff, error taxonomy)
- [ ] Integrate RiskHook protocol (call WP0B risk evaluation)
- [ ] Write unit tests (target: 12+ tests, baseline from completion report)
- [ ] Write state transition matrix tests (all transitions)
- [ ] Write ledger invariant tests (Position + Cash = Fills)
- [ ] Write crash-restart simulation test
- [ ] Write integration test (full order lifecycle)
- [ ] Generate state machine coverage report (evidence)
- [ ] Generate crash-restart simulation evidence (evidence)
- [ ] Create completion report documenting DoD verification

### Reference Implementation
**Note:** WP0A_COMPLETION_REPORT.md shows WP0A was already implemented. Implementation run should:
1. Review existing implementation for alignment with this spec
2. Fill gaps if any (unlikely, completion report shows full coverage)
3. Update evidence artifacts if needed (state machine coverage, crash-restart simulation)
4. Confirm acceptance criteria still met (12+ tests, invariants validated)

### Implementation Sequence (Within WP0A)
1. **Contracts First:** Ensure WP0E complete (Order, Fill, LedgerEntry types available)
2. **OSM + Order Ledger:** Core state machine + order tracking
3. **Position Ledger:** PnL tracking, invariants
4. **Audit Log:** Append-only trail (feeds WP0D reconciliation)
5. **Retry Policy:** Error handling + backoff
6. **Integration:** Wire OSM → Risk Hook → Routing

### Post-Implementation
- [ ] Update Integration Day Plan with WP0A status
- [ ] Notify A0: WP0A complete, unblocking WP0C/WP0D
- [ ] Provide completion report link to downstream WPs (WP0C, WP0D)
- [ ] Coordinate with WP0B on RiskHook integration testing
- [ ] Coordinate with WP0C on Fill event format
- [ ] Coordinate with WP0D on LedgerEntry schema sufficiency

---

**WP0A Task-Packet Status:** ✅ COMPLETE (A2)  
**Last Updated:** 2025-12-31 (A2 completion)  
**Source Traceability:** Roadmap WP0A (lines 114-133) + WP0A_COMPLETION_REPORT.md  
**Link Hygiene:** ✅ All references point to existing docs or intra-PR files (WP0E)
