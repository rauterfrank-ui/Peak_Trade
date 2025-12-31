# WP0C — Order Routing / Adapter Layer (Task-Packet)

**Phase:** Phase 0 — Foundation  
**Work Package:** WP0C (Order Routing / Adapter Layer)  
**Owner:** A4 (Routing-Agent)  
**Status:** DRAFT (Docs-Only)  
**Source:** docs/execution/PEAK_TRADE_LIVE_EXECUTION_ROADMAP_MULTI_AGENT_v1_0.md (WP0C section)

---

## Scope

### In-Scope
**Source:** User specification + existing order system (src/orders/, src/execution_simple/)

- **Order Router:** Selects appropriate OrderExecutor based on ExecutionMode (paper/shadow/testnet/live)
- **Adapter Factory:** Registers and creates OrderExecutor instances
- **Execution Mode Logic:** Mapping from ExecutionMode to Executor implementation
- **Timeout/Retry Wrapper:** Resilience layer around order submission
- **Idempotency Guards:** Prevent duplicate order submission
- **Error Propagation:** Consistent error handling and reporting across adapters
- **Adapter Interface Alignment:** Ensure OrderExecutor protocol compatibility (WP0E)
- **Integration with WP0A:** OSM → Router → Executor → Fill propagation

### Out-of-Scope
- Code implementation (deferred to implementation run)
- src/ or tests/ modifications
- Live enablement or activation instructions
- Exchange-specific adapter implementations (PaperOrderExecutor already exists)
- Market data feeds (consumed, not provided)

---

## Definitions / Glossary

**Router:**  
Deterministic selection logic (policy/config driven) that chooses adapter for order execution. Phase-0: SIMULATED / PAPER / SHADOW routes only (no live).

**Adapter:**  
Abstraction of external execution interaction. Implements standardized interface (submit_order, cancel_order, stream_events). Phase-0: Paper/Shadow adapters only.

**Dispatch:**  
Act of transferring order to adapter for execution. Phase-0: documented boundary, no live dispatch.

**Route Policy:**  
Configuration-driven rules for adapter selection. Phase-0 default: All routes blocked except SIMULATED/PAPER/SHADOW.

**Router Inputs:**  
Order (WP0E), RiskDecision=ALLOW (WP0B), Session constraints (default blocked), Route policy (simulated/paper/shadow).

**Router Output:**  
`route_id` (string), `adapter_id` (string), `routing_reason` (short explanation).

**Adapter Boundary:**  
Interface contract for external execution. Capabilities: submit_order → ack/reject, cancel_order → cancel_ack/cancel_reject, stream_events → ExecutionEvents.

**Idempotency Key:**  
Unique identifier (idempotency_key in Order, WP0E common fields) to prevent duplicate order submission on retry. Adapter must honor: repeated submit with same key = no duplicate.

**Timeout Policy:**  
Maximum allowed time for order execution. Phase-0: Submit timeout → emit TIMEOUT event, no unbounded retry. Default: 30s.

**Retry Strategy:**  
Bounded retry logic for transient failures. Max retries (default: 3), exponential backoff (1s, 2s, 4s), jitter to avoid thundering herd.

**Error Propagation:**  
Adapter rejects → pipeline emits REJECT with reason (CONNECTIVITY_*, ADAPTER_*). Adapter exception → DEFER or fail-safe reject (never silent allow).

**Order Router (Alias):**  
Component that selects the appropriate OrderExecutor based on ExecutionMode and context (e.g., paper → PaperOrderExecutor, shadow → ShadowOrderExecutor).

**OrderExecutor:**  
Protocol (interface) defined in WP0E that all adapters implement. Methods: `execute_order(order) -> OrderExecutionResult`, `execute_orders(orders) -> List[OrderExecutionResult]`.

**ExecutionMode:**  
String constant defining execution environment: `paper`, `shadow`, `shadow_run`, `testnet_dry_run`, `dry_run`, `live_blocked`, `simulated`.

**Adapter Factory:**  
Registry/builder pattern to instantiate OrderExecutor based on config and mode.

---

## Proposed Components

**Source:** src/orders/ existing structure + WP0A integration needs

### Component 1: OrderRouter
**Purpose:**  
Route OrderRequest from WP0A OSM to the appropriate OrderExecutor based on ExecutionMode.

**Responsibilities:**  
- Inspect ExecutionContext.mode (from WP0A)
- Select matching OrderExecutor (via AdapterFactory)
- Delegate order submission to selected executor
- Return OrderExecutionResult to OSM

**Routing Logic:**  
```
IF mode == "paper" → PaperOrderExecutor
IF mode in ["shadow", "shadow_run"] → ShadowOrderExecutor
IF mode in ["testnet_dry_run", "dry_run"] → TestnetOrderExecutor (dry-run stub)
IF mode == "live_blocked" → Reject immediately (safety gate)
IF mode == "simulated" → PaperOrderExecutor (alias)
ELSE → Reject with reason="unknown_mode"
```

**Fallback:** If executor unavailable, return status="rejected", reason="no_executor_for_mode".

---

### Component 2: AdapterFactory
**Purpose:**  
Registry and factory for OrderExecutor instances.

**Responsibilities:**  
- Register OrderExecutor implementations by mode
- Instantiate executors with required dependencies (e.g., PaperMarketContext for PaperOrderExecutor)
- Validate executor configuration at startup
- Provide executor lookup by ExecutionMode

**Registration Pattern:**  
```
factory.register("paper", lambda cfg: PaperOrderExecutor(PaperMarketContext(cfg)))
factory.register("shadow", lambda cfg: ShadowOrderExecutor(ShadowMarketContext(cfg)))
```

**Validation:** On startup, verify all required modes have registered executors.

---

### Component 3: Timeout/Retry Wrapper (ResilientOrderExecutor)
**Purpose:**  
Add resilience layer around raw OrderExecutor: timeouts, retries, error handling.

**Responsibilities:**  
- Wrap OrderExecutor.execute_order() with timeout (default: 30s)
- Retry on transient errors (network, temp unavailable) with exponential backoff
- Respect idempotency: use OrderRequest.client_id to detect retries
- Enforce max retries (default: 3)
- Convert exceptions to OrderExecutionResult (status="rejected", reason=error_msg)

**Retry Logic:**  
- Retry on: network timeout, 503 service unavailable, connection errors
- Do NOT retry on: 400 bad request, 401 unauthorized, validation errors
- Backoff: 1s, 2s, 4s (exponential with jitter)

**Timeout Handling:**  
If executor exceeds timeout → cancel operation → return status="rejected", reason="execution_timeout_30s".

---

### Component 4: Idempotency Guard
**Purpose:**  
Prevent duplicate order submissions on retry.

**Responsibilities:**  
- Track submitted client_ids (in-memory cache or persistent store)
- Before submission, check if client_id already submitted
- If duplicate detected → return cached OrderExecutionResult (or reject with reason="duplicate_client_id")
- Expire cache entries after TTL (e.g., 1 hour)

**Implementation Note:**  
- Requires OrderRequest.client_id to be mandatory for WP0C integration
- WP0A OSM must generate unique client_id per order (e.g., UUID or timestamp-based)

---

### Component 5: Error Propagation Handler
**Purpose:**  
Standardize error reporting from adapters to WP0A OSM.

**Responsibilities:**  
- Catch all exceptions from OrderExecutor.execute_order()
- Convert to OrderExecutionResult with status="rejected"
- Populate reason with actionable error message (no stack traces)
- Log full exception details for observability (WP0D)
- Return consistent error contract to WP0A

**Error Categories:**  
- **validation_error:** Invalid OrderRequest (e.g., negative quantity)
- **network_error:** Transient network failure
- **timeout_error:** Execution exceeded timeout
- **rejected_by_exchange:** Exchange rejected order (e.g., insufficient balance)
- **unknown_error:** Unexpected failure (catch-all)

**Error Contract:**  
```python
OrderExecutionResult(
    status="rejected",
    request=original_request,
    fill=None,
    reason="network_error: Connection timeout after 30s",
    metadata={"error_category": "network_error", "retry_count": 3}
)
```

---

### Component 6: Router Decision & Adapter Boundary (Docs-Only Concept)
**Source:** User specification — routing & adapter boundary documentation

**Purpose:** Document routing decision process and adapter interface contract (Phase-0: conceptual, no live implementation).

**Router Inputs:**
- **Order (WP0E):** OrderRequest with correlation_id, idempotency_key, symbol, side, qty, type, limit_price
- **RiskDecision=ALLOW (WP0B):** Risk gate passed (router only runs if ALLOW)
- **Session Constraints:** Default blocked (live routes disabled in Phase-0)
- **Route Policy:** Config-driven rules (Phase-0: SIMULATED / PAPER / SHADOW only)

**Router Output:**
- **`route_id` (string):** Unique identifier for routing decision (e.g., "route_paper_001")
- **`adapter_id` (string):** Selected adapter (e.g., "PaperOrderExecutor", "ShadowOrderExecutor")
- **`routing_reason` (string):** Short explanation (e.g., "mode=paper → PaperOrderExecutor", "live_blocked → REJECT")

**Router Decision Logic (Phase-0):**
```
IF mode == "paper" OR mode == "simulated":
  → route_id="route_paper", adapter_id="PaperOrderExecutor", routing_reason="paper mode"
IF mode in ["shadow", "shadow_run"]:
  → route_id="route_shadow", adapter_id="ShadowOrderExecutor", routing_reason="shadow mode"
IF mode in ["testnet_dry_run", "dry_run"]:
  → route_id="route_testnet_stub", adapter_id="TestnetOrderExecutor", routing_reason="testnet dry-run stub"
IF mode == "live_blocked" OR mode == "live":
  → REJECT with reason="POLICY_BLOCKED: Live routes disabled in Phase-0"
ELSE:
  → DEFER with reason="ROUTE_CONFIG_INVALID: Unknown mode"
```

**Adapter Boundary (Concept):**

**Capabilities (Interface Contract):**
1. **`submit_order(order: Order) -> ack/reject`**
   - Input: Order (WP0E contract)
   - Output: ExecutionEvent (ACK or REJECT, WP0E contract)
   - Idempotency: Repeated submit with same idempotency_key → no duplicate
   - Timeout: 30s default (configurable)

2. **`cancel_order(order_id: str) -> cancel_ack/cancel_reject`**
   - Input: order_id (string)
   - Output: ExecutionEvent (CANCEL_ACK or CANCEL_REJECT)
   - Timeout: 10s default

3. **`stream_events(correlation_id: str) -> ExecutionEvents`**
   - Input: correlation_id (for filtering)
   - Output: Stream of ExecutionEvents (ACK, REJECT, FILL, CANCEL_ACK)
   - Deduplication: Events deduplicated on event_id

**Reliability Rules (Concept):**
- **Idempotency Required:** Adapter must honor idempotency_key (no duplicate submissions)
- **Timeout Handling:** Submit timeout → emit TIMEOUT event, no unbounded retry
- **Retry Policy:** Max retries bounded (3), exponential backoff (1s, 2s, 4s), jitter
- **Error Propagation:** Adapter rejects → pipeline emits REJECT with reason (CONNECTIVITY_*, ADAPTER_*). Adapter exception → DEFER or fail-safe reject (never silent allow).

**Failure Modes (Adapter Boundary):**
- **Route Misconfig:** Unknown mode → DEFER with reason="ROUTE_CONFIG_INVALID"
- **Adapter Unavailable:** Adapter not registered → REJECT/DEFER with reason="CONNECTIVITY_DOWN"
- **Duplicate Event Stream:** Dedupe on event_id/idempotency_key
- **Partial Fills Across Reconnects:** Deterministic aggregation rule (sum fill_qty per order_id)

---

## Inputs / Outputs (Contracts)

**Source:** WP0A OSM integration + WP0E OrderExecutor protocol

### Inputs
**From WP0A (Order State Machine):**
- **OrderRequest:** Order details (symbol, side, quantity, order_type, limit_price, client_id, metadata)
  - Format: `OrderRequest` dataclass (defined in WP0E, implemented in src/orders/base.py)
  - client_id: MUST be unique per order (for idempotency)
- **ExecutionContext:** Execution environment (mode, strategy_id, session_id, timestamp)
  - mode: ExecutionMode string ("paper", "shadow", "testnet_dry_run", etc.)
  - Used by OrderRouter to select executor

**From Configuration:**
- **Executor Config:** Parameters for each executor (e.g., PaperMarketContext prices, slippage, fees)
- **Timeout/Retry Config:** Timeout duration (default 30s), max retries (default 3), backoff strategy

### Outputs
**To WP0A (Order State Machine):**
- **OrderExecutionResult:** Execution outcome
  - status: OrderStatus ("filled", "rejected", "partially_filled", "cancelled")
  - request: Original OrderRequest (for audit trail)
  - fill: OrderFill (if status="filled") with quantity, price, timestamp, fees
  - reason: String explanation (if rejected/failed)
  - metadata: Additional context (error_category, retry_count, executor_name, execution_time_ms)

**To WP0D (Observability / Ledger):**
- **Fill Events:** Emitted on status="filled" for reconciliation
  - Trigger: OrderExecutor returns OrderExecutionResult with fill != None
  - Consumed by: WP0D ledger for position tracking and PnL calculation

**To Audit Log:**
- **Routing Decisions:** Log which executor was selected for each order (mode → executor mapping)
- **Error Events:** Log all rejected orders with reason and error category

---

## Failure Modes & Handling

**Source:** Resilience requirements + existing executor error patterns

### Failure Mode 1: No Executor for ExecutionMode
**Scenario:**  
WP0A OSM sends OrderRequest with ExecutionContext.mode that has no registered executor in AdapterFactory.

**Impact:**  
Order cannot be routed → execution stalls → OSM state inconsistent.

**Mitigation:**  
- OrderRouter returns OrderExecutionResult(status="rejected", reason="no_executor_for_mode: {mode}")
- AdapterFactory validates all required modes at startup (fail-fast if missing)
- Default fallback: If mode unknown, use PaperOrderExecutor (safe simulation)
- OSM transitions to REJECTED state, logs error

---

### Failure Mode 2: Executor Timeout
**Scenario:**  
OrderExecutor.execute_order() exceeds timeout (e.g., network latency, exchange API slow).

**Impact:**  
Order state unknown → potential duplicate submission if retried naively.

**Mitigation:**  
- ResilientOrderExecutor wraps executor with timeout (default 30s)
- On timeout → return OrderExecutionResult(status="rejected", reason="execution_timeout_30s")
- Do NOT retry automatically (order state ambiguous)
- OSM logs timeout event, operator investigates
- Idempotency guard prevents duplicate if OSM retries with same client_id

---

### Failure Mode 3: Transient Network Error
**Scenario:**  
Network failure during order submission (connection reset, DNS timeout).

**Impact:**  
Order not submitted → execution fails → strategy may miss trade.

**Mitigation:**  
- ResilientOrderExecutor retries up to 3 times with exponential backoff (1s, 2s, 4s)
- Idempotency guard ensures same order not submitted twice
- After max retries → return OrderExecutionResult(status="rejected", reason="network_error: Max retries exceeded")
- OSM marks order REJECTED, emits alert to WP0D

---

### Failure Mode 4: Duplicate client_id
**Scenario:**  
WP0A OSM retries order submission with same client_id (e.g., after timeout).

**Impact:**  
Without idempotency guard → duplicate orders → unintended position doubling.

**Mitigation:**  
- Idempotency Guard tracks submitted client_ids (in-memory cache or persistent store)
- On duplicate detection → return cached OrderExecutionResult (if available) or reject with reason="duplicate_client_id"
- Cache expires after TTL (1 hour, configurable)
- WP0A OSM must generate globally unique client_id (UUID recommended)

---

### Failure Mode 5: Invalid OrderRequest
**Scenario:**  
OrderRequest fails validation (e.g., negative quantity, invalid symbol format, limit order without price).

**Impact:**  
Executor cannot process order → execution fails.

**Mitigation:**  
- OrderRequest.__post_init__() validates in WP0A before routing (preferred)
- If validation missed → OrderExecutor returns OrderExecutionResult(status="rejected", reason="validation_error: {details}")
- Error Propagation Handler ensures consistent error contract
- OSM transitions to REJECTED, logs validation error

---

### Failure Mode 6: Executor Crashes
**Scenario:**  
OrderExecutor.execute_order() raises unhandled exception (e.g., bug, unexpected API response).

**Impact:**  
Order execution aborts → OSM state inconsistent → potential system instability.

**Mitigation:**  
- Error Propagation Handler wraps all executor calls with try/except
- On exception → return OrderExecutionResult(status="rejected", reason="unknown_error: {exception_type}")
- Log full stack trace to WP0D for debugging
- Do NOT propagate exception to WP0A OSM (OSM should never crash due to executor failure)
- Circuit breaker (future): If executor fails >10 times in 1 min → disable temporarily

---

## Acceptance Criteria (Gate-Tauglich)

**Source:** User specification + Docs-only specification + testability requirements

### Docs-Only Criteria (Phase-0 Foundation)
- [ ] **AC1:** Router Inputs/Outputs dokumentiert, inkl. default blocked routes (no live). Router Output: route_id, adapter_id, routing_reason.
- [ ] **AC2:** Adapter Interface klar beschrieben (submit_order, cancel_order, stream_events). Capabilities documented with input/output contracts.
- [ ] **AC3:** Timeout/Retry/Idempotency Regeln dokumentiert (bounded). Timeout: 30s, Max retries: 3, Idempotency: idempotency_key honored.
- [ ] **AC4:** Fehlerpropagation zurück in WP0A/WP0E Contracts konsistent. Error categories (validation_error, network_error, timeout_error, rejected_by_exchange, unknown_error) mapped to OrderExecutionResult.
- [ ] **AC5:** Keine Live-Enablement-Anweisungen; docs-only. Phase-0: SIMULATED/PAPER/SHADOW only, live routes blocked.
- [ ] **AC6:** Keine Verweise/Links auf nicht-existierende Targets (link hygiene verified).

### OrderRouter Criteria (Implementation)
- [ ] **Routing Logic Implemented:** OrderRouter selects executor based on ExecutionMode (paper/shadow/testnet/live_blocked)
- [ ] **Fallback Handling:** Unknown modes return status="rejected", reason="no_executor_for_mode"
- [ ] **Mode Coverage:** All defined ExecutionModes have routing rules (paper, shadow, shadow_run, testnet_dry_run, dry_run, live_blocked, simulated)
- [ ] **Integration with WP0A:** OSM calls OrderRouter with ExecutionContext, receives OrderExecutionResult

### AdapterFactory Criteria
- [ ] **Executor Registration:** Factory supports register(mode, executor_builder) pattern
- [ ] **Startup Validation:** Factory validates all required modes at initialization (fail-fast if missing)
- [ ] **Executor Instantiation:** Factory creates executor with required dependencies (e.g., PaperMarketContext)
- [ ] **Lookup API:** Factory provides get_executor(mode) → OrderExecutor

### Timeout/Retry Criteria
- [ ] **Timeout Enforcement:** ResilientOrderExecutor wraps executor with timeout (default 30s, configurable)
- [ ] **Timeout Handling:** On timeout → return status="rejected", reason="execution_timeout_{duration}s"
- [ ] **Retry Logic:** Transient errors (network, 503) retried up to max_retries (default 3) with exponential backoff
- [ ] **No Retry on Fatal Errors:** 400, 401, validation errors NOT retried
- [ ] **Backoff Strategy:** 1s, 2s, 4s with jitter (±20%)

### Idempotency Criteria
- [ ] **client_id Tracking:** Idempotency Guard tracks submitted client_ids (in-memory or persistent)
- [ ] **Duplicate Detection:** Duplicate client_id returns cached result or rejects with reason="duplicate_client_id"
- [ ] **Cache Expiry:** client_id cache expires after TTL (default 1 hour, configurable)
- [ ] **WP0A Requirement:** OSM generates unique client_id per order (UUID recommended)

### Error Propagation Criteria
- [ ] **Exception Handling:** All OrderExecutor calls wrapped in try/except
- [ ] **Consistent Error Contract:** Exceptions converted to OrderExecutionResult(status="rejected", reason=error_msg)
- [ ] **Error Categories:** reason includes category (validation_error, network_error, timeout_error, rejected_by_exchange, unknown_error)
- [ ] **Logging:** Full exception details logged to WP0D for observability
- [ ] **No Exception Leakage:** WP0A OSM never receives raw exceptions from executor

### Integration Testing Criteria
- [ ] **WP0A → WP0C → PaperOrderExecutor:** End-to-end order submission test (paper mode)
- [ ] **WP0C → WP0D Fill Events:** Filled orders emit events to WP0D ledger
- [ ] **Timeout Simulation:** Test executor timeout → status="rejected"
- [ ] **Retry Simulation:** Test transient network error → retry → success
- [ ] **Idempotency Test:** Submit order twice with same client_id → second rejected/cached
- [ ] **Unknown Mode Test:** Invalid ExecutionMode → status="rejected"

### Performance Criteria
- [ ] **Routing Overhead:** OrderRouter adds <1ms latency to order submission
- [ ] **Executor Selection:** AdapterFactory.get_executor() deterministic, no I/O
- [ ] **Idempotency Cache:** client_id lookup <1ms (in-memory cache)

### Documentation Criteria
- [ ] **OrderRouter API Documented:** Routing logic + fallback behavior
- [ ] **AdapterFactory Pattern Documented:** Registration + instantiation examples
- [ ] **Timeout/Retry Config Documented:** Default values + override mechanism
- [ ] **Error Contract Documented:** OrderExecutionResult.reason format + categories
- [ ] **Integration Guide:** WP0A OSM integration steps (client_id generation, error handling)

---

## Evidence Checklist

**Source:** Gate requirements + acceptance criteria verification

### Required Evidence Artifacts (Implementation Run)
- [ ] **OrderRouter Smoke Test Report:** Verify routing logic for all ExecutionModes
  - Location pattern: `reports/execution/order_router_smoke_test_*.md`
  - Content: Test each mode (paper/shadow/testnet/live_blocked) → correct executor selected
  - Purpose: Validate routing logic deterministic
- [ ] **Adapter Integration Test Results:** End-to-end WP0A → WP0C → Executor → WP0D
  - Location pattern: `tests/execution/test_adapter_integration.py` (pytest output)
  - Coverage: OrderRouter, AdapterFactory, PaperOrderExecutor, Fill event propagation
  - Purpose: Verify cross-WP integration (A, C, D)
- [ ] **Timeout/Retry Simulation Report:** Test resilience layer
  - Location pattern: `reports/execution/timeout_retry_simulation_*.md`
  - Content: Simulate executor timeout → rejected; transient error → retry → success
  - Purpose: Validate ResilientOrderExecutor behavior
- [ ] **Idempotency Test Report:** Duplicate client_id handling
  - Location pattern: `tests/execution/test_idempotency.py` (pytest output)
  - Content: Submit order twice with same client_id → second rejected or cached
  - Purpose: Prevent duplicate orders
- [ ] **Error Propagation Test Report:** Exception → OrderExecutionResult conversion
  - Location pattern: `tests/execution/test_error_propagation.py` (pytest output)
  - Content: Trigger executor exceptions → verify status="rejected", reason populated
  - Purpose: Ensure consistent error contract
- [ ] **Performance Benchmark:** Routing and executor overhead
  - Location pattern: `reports/execution/performance_benchmark_*.md`
  - Content: Measure OrderRouter latency (<1ms), AdapterFactory lookup (<1ms)
  - Purpose: Verify low overhead
- [ ] **Completion Report:** WP0C implementation documentation
  - Location pattern: "docs/execution/WP0C_IMPLEMENTATION_REPORT.md" (future)

### Evidence Generation (Not in This Docs-Only Run)
**Note:** Evidence artifacts generated during implementation run, not docs-only prep.

---

## Integration Notes

**Source:** Cross-WP dependencies + execution flow

### Depends On
**WP0E (Contracts & Interfaces) — CRITICAL BLOCKER:**
- **OrderExecutor Protocol:** WP0C implements OrderRouter that delegates to executors conforming to OrderExecutor protocol
- **OrderRequest/OrderExecutionResult:** WP0C consumes/produces these contracts
- **Dependency:** WP0E must finalize OrderExecutor interface before WP0C implementation

**WP0A (Execution Core / OSM) — CRITICAL BLOCKER:**
- **ExecutionContext:** WP0A provides ExecutionContext.mode to WP0C for routing
- **client_id Generation:** WP0A OSM must generate unique client_id per order (for idempotency)
- **Error Handling:** WP0A OSM must handle OrderExecutionResult.status="rejected" gracefully
- **Integration Point:** OSM.submit_order() → OrderRouter.route() → OrderExecutor.execute_order()

**Existing Order System (src/orders/) — FOUNDATION:**
- **PaperOrderExecutor:** Already implemented, WP0C routes to it for "paper" mode
- **ShadowOrderExecutor:** Already implemented, WP0C routes to it for "shadow" mode
- **TestnetOrderExecutor:** Stub exists, WP0C routes to it for "testnet_dry_run" mode
- **Dependency:** WP0C leverages existing executors, no reimplementation needed

### Consumed By
**WP0D (Observability / Ledger) — DOWNSTREAM:**
- **Fill Events:** WP0C emits OrderExecutionResult with status="filled" → WP0D consumes for position tracking
- **Error Logs:** WP0C logs rejected orders → WP0D aggregates for alerts
- **Integration:** WP0C does NOT directly call WP0D; WP0A OSM propagates fills to WP0D

**WP0B (Risk Layer) — INDIRECT:**
- **Risk Decisions:** WP0B evaluates order BEFORE WP0C routing (pre-trade gate)
- **No Direct Dependency:** WP0C does not call WP0B; WP0A OSM calls WP0B → WP0C sequentially

### Integration Sequence
**Phase 0 Execution Order:**
1. **WP0E First:** Define OrderExecutor protocol (contracts)
2. **WP0A + WP0C Parallel (with coordination):**
   - WP0A: Implement OSM with ExecutionContext.mode
   - WP0C: Implement OrderRouter with mode-based routing
   - **Coordination Point:** Agree on ExecutionContext schema, client_id generation strategy
3. **Integration Test (WP0A + WP0C):** OSM → Router → PaperOrderExecutor → Fill
4. **WP0B Integration:** Add risk gate before WP0C routing (WP0A orchestrates)
5. **WP0D Integration:** OSM propagates fills from WP0C to WP0D ledger

**Critical Path:** WP0E → WP0A/WP0C (parallel) → Integration Test → WP0B/WP0D hookup

### Cross-WP Interfaces
**WP0A ↔ WP0C:**
- **Input:** ExecutionContext (mode, strategy_id, session_id, timestamp)
- **Input:** OrderRequest (symbol, side, quantity, order_type, client_id, metadata)
- **Output:** OrderExecutionResult (status, fill, reason, metadata)

**WP0C ↔ WP0D:**
- **Indirect (via WP0A):** WP0C returns OrderExecutionResult → WP0A emits Fill event → WP0D consumes

**WP0E → WP0C:**
- **Contract:** OrderExecutor protocol implementation
- **WP0C Conformance:** OrderRouter wraps executors, preserves protocol semantics

### Conflict Avoidance
**File Ownership (as per Ownership Matrix):**
- **WP0C (A4) Owns:** "src/orders/router.py" (new), "src/orders/factory.py" (new), "src/orders/resilient_executor.py" (new), "tests/orders/test_router.py" (new)
- **WP0A (A2) Owns:** "src/execution/order_state_machine.py", "src/execution/execution_context.py"
- **Shared Files:** None (WP0C does NOT modify WP0A files)
- **Integration Coordination:** A0 Integrator mediates WP0A ↔ WP0C interface agreement

### Open Questions / Coordination Needs
**Q1: ExecutionContext Schema?**
- **Issue:** WP0C needs ExecutionContext.mode; WP0A defines ExecutionContext
- **Action:** Coordinate with WP0A (A2) on schema (mode: str, strategy_id: str, session_id: str, timestamp: datetime)

**Q2: client_id Generation Strategy?**
- **Issue:** WP0C idempotency guard requires unique client_id; WP0A OSM generates it
- **Action:** Agree on format (UUID recommended) and uniqueness scope (global or per-session)

**Q3: Retry Ownership?**
- **Issue:** Should WP0A OSM retry rejected orders, or does WP0C ResilientOrderExecutor handle it?
- **Proposal:** WP0C retries transient errors (network); WP0A does NOT retry (avoids duplicate logic)
- **Action:** Document retry ownership in integration guide

---

## Next Implementation Run

**Note:** This is a docs-only specification. Code implementation follows in separate PR.

### Implementation Approach (Docs-Only Description)

**Step 1: AdapterFactory Foundation (Day 1)**
- Implement "src/orders/factory.py":
  - `AdapterFactory` class with `register(mode, builder)` and `get_executor(mode)` methods
  - Startup validation: fail-fast if required modes missing
  - Example registration: `factory.register("paper", lambda cfg: PaperOrderExecutor(...))`
- Test: `tests/orders/test_factory.py` (registration, lookup, validation)

**Step 2: OrderRouter Core (Day 1-2)**
- Implement "src/orders/router.py":
  - `OrderRouter` class with `route(order_request, execution_context) -> OrderExecutionResult`
  - Mode-based routing logic (paper → PaperOrderExecutor, shadow → ShadowOrderExecutor, etc.)
  - Fallback for unknown modes (status="rejected", reason="no_executor_for_mode")
- Test: `tests/orders/test_router.py` (routing logic, fallback, mode coverage)

**Step 3: ResilientOrderExecutor Wrapper (Day 2-3)**
- Implement "src/orders/resilient_executor.py":
  - Wrap OrderExecutor with timeout (default 30s)
  - Retry logic (max 3, exponential backoff, transient errors only)
  - Exception → OrderExecutionResult conversion (status="rejected", reason populated)
- Test: `tests/orders/test_resilient_executor.py` (timeout, retry, exception handling)

**Step 4: Idempotency Guard (Day 3)**
- Implement idempotency logic in `OrderRouter` or separate `IdempotencyGuard`:
  - Track client_ids (in-memory dict or persistent cache)
  - Duplicate detection → reject or return cached result
  - TTL expiry (default 1 hour)
- Test: `tests/orders/test_idempotency.py` (duplicate detection, cache expiry)

**Step 5: Integration with WP0A (Day 4)**
- Coordinate with WP0A (A2) on ExecutionContext schema and client_id generation
- Add integration test: `tests/execution/test_order_routing_integration.py`
  - WP0A OSM → OrderRouter → PaperOrderExecutor → OrderExecutionResult → WP0D Fill event
  - Test paper, shadow, testnet_dry_run modes
- Verify error handling: timeout → rejected, invalid mode → rejected

**Step 6: Error Propagation & Logging (Day 4)**
- Implement error handling in OrderRouter:
  - Catch all exceptions from executors
  - Convert to OrderExecutionResult with error categories
  - Log full exception details to WP0D (structured logging)
- Test: `tests/orders/test_error_propagation.py` (exception → rejected, logging)

**Step 7: Evidence Generation (Day 5)**
- Run smoke tests for all ExecutionModes → `reports/execution/order_router_smoke_test_*.md`
- Run integration tests (WP0A + WP0C + WP0D) → pytest output
- Generate timeout/retry simulation report
- Performance benchmark: routing latency, factory lookup time
- Write WP0C completion report: "docs/execution/WP0C_IMPLEMENTATION_REPORT.md" (future)

---

### Implementation Checklist (Gate-Ready)

**Pre-Implementation:**
- [ ] WP0E contracts finalized (OrderExecutor protocol, OrderRequest, OrderExecutionResult)
- [ ] WP0A ExecutionContext schema agreed (mode, strategy_id, session_id, timestamp)
- [ ] WP0A client_id generation strategy agreed (UUID format)
- [ ] Ownership Matrix consulted: WP0C owns "src/orders/router.py", "factory.py", "resilient_executor.py"

**Implementation Sequence:**
- [ ] Implement AdapterFactory (registration + lookup + validation)
- [ ] Implement OrderRouter (mode-based routing + fallback)
- [ ] Implement ResilientOrderExecutor (timeout + retry + exception handling)
- [ ] Implement Idempotency Guard (client_id tracking + duplicate rejection)
- [ ] Add WP0A integration tests (OSM → Router → Executor → Fill)
- [ ] Add error propagation tests (exception → OrderExecutionResult)
- [ ] Add timeout/retry simulation tests
- [ ] Add idempotency tests (duplicate client_id)

**Testing:**
- [ ] Unit tests for OrderRouter (all modes, fallback)
- [ ] Unit tests for AdapterFactory (registration, lookup, validation)
- [ ] Unit tests for ResilientOrderExecutor (timeout, retry, backoff)
- [ ] Unit tests for Idempotency Guard (duplicate detection, TTL)
- [ ] Integration tests (WP0A + WP0C + PaperOrderExecutor)
- [ ] Performance benchmarks (routing <1ms, factory <1ms)
- [ ] Test coverage >90% for WP0C modules

**Evidence Artifacts:**
- [ ] Order router smoke test report
- [ ] Adapter integration test results (pytest output)
- [ ] Timeout/retry simulation report
- [ ] Idempotency test report
- [ ] Error propagation test report
- [ ] Performance benchmark report
- [ ] WP0C completion report

**Integration:**
- [ ] Coordinate with WP0A (A2) on ExecutionContext schema
- [ ] Coordinate with WP0A (A2) on client_id generation
- [ ] Verify WP0D (A5) receives Fill events from OSM (not directly from WP0C)
- [ ] Link-hygiene check: All references to WP0A, WP0E, WP0D valid
- [ ] Update Ownership Matrix: Confirm WP0C file ownership

**Gate Readiness:**
- [ ] All acceptance criteria met (30+ criteria)
- [ ] All evidence artifacts produced
- [ ] CI/tests passing (no failures)
- [ ] Linter clean (ruff format, no errors)
- [ ] Integration Day Plan updated with WP0C merge steps
- [ ] Phase-0 Gate Report updated with WP0C status

**Implementation Checklist:**
- [ ] Implement routing/adapter in "src/execution/routing.py" or "src/orders/"
- [ ] Write unit/integration tests in "tests/execution/" or "tests/orders/"
- [ ] Generate evidence reports in "reports/execution/"
- [ ] Create completion report: "docs/execution/WP0C_IMPLEMENTATION_REPORT.md" (future)

---

**WP0C Task-Packet Status:** INITIALIZED (awaiting A4 completion)  
**Last Updated:** 2025-12-31 (A0 initialization)
