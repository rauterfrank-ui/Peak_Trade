# WP0B — Risk Layer v1.0 (Task-Packet)

**Phase:** Phase 0 — Foundation  
**Work Package:** WP0B (Risk Layer v1.0)  
**Owner:** A3 (Risk-Agent)  
**Status:** DRAFT (Docs-Only)  
**Source:** docs/execution/PEAK_TRADE_LIVE_EXECUTION_ROADMAP_MULTI_AGENT_v1_0.md (WP0B section)

---

## Scope

### In-Scope
**Source:** Roadmap WP0B (lines 136-154) + Risk Layer Overview + Risk Layer Alignment

- Risk as "first-class citizen" in execution flow (pre-trade gating)
- RiskHook protocol implementation (from WP0E): evaluate_order(), check_kill_switch(), evaluate_position_change()
- Risk decision types: ALLOW, BLOCK, PAUSE (clear semantics for execution flow)
- Portfolio risk metrics: VaR/CVaR (Historical, Parametric, EWMA), Stress Testing
- Risk limits enforcement: Daily/Weekly Loss Limits, Max Drawdown Circuit Breaker
- Kill Switch: Manual + Auto trigger, state machine (ACTIVE → KILLED → RECOVERING)
- Kupiec POF test (VaR validation, regulatory compliance)
- Deterministic report generation (CI-friendly, reproducible)
- Risk context snapshot (portfolio state, positions, exposures at evaluation time)
- Risk audit trail (all decisions logged for compliance)
- Config-driven risk policies (enable/disable components, tune parameters)

### Out-of-Scope
- Code implementation (deferred to implementation run)
- src/ or tests/ modifications
- Live enablement or activation instructions
- Exchange connectivity (kill switch works without exchange, pre-trade only)
- Backtest risk metrics (handled by src/risk/, not runtime enforcement)
- Position sizing logic (handled by strategy layer, not risk runtime)
- Real-time market data (uses context provided by WP0A)

---

## Definitions / Glossary

**Risk Runtime Flow:** Deterministic evaluation pipeline: (1) Build Context Snapshot → (2) Evaluate Policies in order → (3) Produce Decision → (4) Emit Risk Audit Record → (5) Return to Pipeline Gate (WP0A).

**Context Snapshot:** Minimal, deterministic momentary state capture for risk decisions. Includes correlation_id, strategy_id, session_id, instrument (symbol, venue), order features (side, qty, type, limit_price), exposure proxies (current position, notional, open_orders_count), timestamp (as_of_time_utc).

**Policy:** Pure function over context → decision + reason. Deterministic evaluation (no hidden state, no randomness without capture). Examples: MaxOpenOrdersPolicy, NotionalLimitPolicy, SymbolBlocklistPolicy, SessionNotArmedPolicy.

**Policy Semantics:** Policies evaluated in defined order (P1, P2, ..., Pn). Short-circuit rules: REJECT terminates evaluation immediately; DEFER terminates evaluation (requires manual resolution); ALLOW continues to next policy (unless final policy).

**Risk Decision:** Tri-state outcome of risk evaluation: ALLOW (proceed), REJECT (block order, terminal), DEFER (temporary hold, requires manual resolution).

**Short-Circuit:** Evaluation terminates early on REJECT or DEFER. ALLOW continues to next policy. Conservative default: REJECT/DEFER stops pipeline immediately, no further policies evaluated.

**Risk Audit Record:** Immutable evidence of risk evaluation. Includes correlation_id, decision, reason_code, context snapshot reference, policy_id, timestamp. Enables compliance, debugging, post-mortem analysis.

**Conservative Defaults:** Unknown context, missing fields, policy errors → REJECT or DEFER (never implicit ALLOW). Safety-first principle. Example: Missing position data → DEFER with reason "RISK_UNKNOWN_CONTEXT".

**Reason Codes (Controlled Vocabulary):** Standardized codes for risk decisions. Examples: RISK_MAX_OPEN_ORDERS, RISK_NOTIONAL_LIMIT, RISK_SYMBOL_BLOCKLIST, RISK_SESSION_NOT_ARMED, RISK_UNKNOWN_CONTEXT, RISK_POLICY_ERROR.

**RiskHook Protocol:** Interface (from WP0E) allowing execution system to call risk evaluation without direct dependency on risk implementation.

**Kill Switch:** Emergency halt mechanism (Layer 4 defense-in-depth) that blocks all orders when triggered. State machine: ACTIVE → KILLED → RECOVERING.

**VaR (Value at Risk):** Maximum expected loss at given confidence level (e.g., 95%) over time horizon. Used for portfolio risk assessment.

**CVaR (Conditional VaR / Expected Shortfall):** Average loss beyond VaR threshold. More conservative than VaR, captures tail risk.

**Kupiec POF Test:** Proportion of Failures test for VaR validation. Checks if observed exceptions match expected rate (regulatory compliance).

**Circuit Breaker:** Auto-trigger mechanism that halts trading when loss limit exceeded (e.g., max drawdown > 20%).

**Risk Context:** Snapshot of portfolio state at evaluation time (positions, cash, unrealized PnL, exposures) used for risk calculation.

**Risk Audit Trail:** Immutable log of all risk decisions (ALLOW/BLOCK/PAUSE) with context, enabling compliance and debugging.

---

## Proposed Components

**Source:** Roadmap WP0B DoD (lines 140-149) + Risk Layer Overview + Kill Switch docs

### Component 1: RiskHook Implementation (WP0E Protocol)
**Purpose:** Implement RiskHook protocol to integrate risk evaluation into execution flow  
**Responsibilities:**
- Implement evaluate_order(order, context) → RiskResult
- Implement check_kill_switch() → RiskResult
- Implement evaluate_position_change(symbol, qty, side, context) → RiskResult
- Return RiskResult with decision (ALLOW/BLOCK/PAUSE), reason, metadata
- Log all decisions to risk audit trail

**Decision Logic:**
1. Check kill switch first (if KILLED → BLOCK all orders)
2. Evaluate portfolio risk metrics (VaR, CVaR, stress)
3. Check loss limits (daily, weekly, max DD)
4. Check position limits (per-symbol, gross exposure)
5. Return ALLOW if all checks pass, BLOCK if any fail, PAUSE if temporary issue

### Component 2: Kill Switch (Emergency Halt)
**Purpose:** Emergency mechanism to halt all trading  
**Responsibilities:**
- State machine: ACTIVE, KILLED, RECOVERING
- Manual trigger (operator command)
- Auto trigger (max DD, loss limits, external signal)
- Persist state across restarts
- Block all orders when KILLED
- Cooldown period before RECOVERING → ACTIVE

**State Transitions:**
```
ACTIVE → KILLED (manual/auto trigger)
KILLED → RECOVERING (operator approval)
RECOVERING → ACTIVE (after cooldown, checks pass)
```

**Trigger Mechanisms:**
- **Manual:** Operator CLI/API command
- **Auto-MaxDD:** Drawdown > threshold (e.g., 20%)
- **Auto-DailyLoss:** Daily loss > limit
- **Auto-WeeklyLoss:** Weekly loss > limit
- **External:** Watchdog signal, exchange outage, etc.

### Component 3: Portfolio Risk Metrics (VaR/CVaR/Stress)
**Purpose:** Calculate portfolio risk exposure for pre-trade decisions  
**Responsibilities:**
- Historical VaR/CVaR (rolling window, e.g., 252 days)
- Parametric VaR/CVaR (Gaussian assumption)
- EWMA VaR/CVaR (exponentially weighted moving average)
- Stress testing (apply historical scenarios, e.g., COVID crash, FTX collapse)
- Deterministic calculation (same inputs → same outputs)
- CI-friendly (fast, no external dependencies)

**VaR Methods:**
- **Historical:** Sort returns, take percentile (non-parametric)
- **Parametric:** Assume normal distribution, use μ ± z*σ
- **EWMA:** Weight recent data more heavily

**Stress Scenarios (Example):**
- COVID Crash 2020 (-50% BTC)
- China Ban 2021 (-30% BTC)
- Luna Collapse 2022 (-60% LUNA, -10% BTC)
- FTX Collapse 2022 (-20% BTC, liquidity crunch)
- Bear Market 2018 (-80% from peak)

### Component 4: Loss Limits Enforcer
**Purpose:** Enforce daily/weekly loss limits and max drawdown circuit breaker  
**Responsibilities:**
- Track cumulative P&L (daily, weekly, all-time)
- Calculate drawdown from peak equity
- Compare against configured limits
- Block orders if limits breached
- Trigger kill switch if max DD exceeded

**Limits (Configurable):**
- Daily loss limit (e.g., -5% of starting capital)
- Weekly loss limit (e.g., -10% of starting capital)
- Max drawdown (e.g., -20% from peak equity)
- Position limit per symbol (e.g., 10% of portfolio)
- Gross exposure limit (e.g., 100% of capital, no leverage)

**Circuit Breaker Logic:**
- If max DD > threshold → Auto-trigger kill switch
- If daily/weekly loss > limit → BLOCK new orders (existing can close)
- If position limit exceeded → BLOCK orders increasing position

### Component 5: Kupiec POF Test (VaR Validation)
**Purpose:** Validate VaR models for regulatory compliance  
**Responsibilities:**
- Count VaR exceptions (actual loss > VaR prediction)
- Calculate expected exception rate (1 - confidence level)
- Run Kupiec likelihood ratio test
- Generate traffic light report (green/yellow/red)
- Deterministic, CI-friendly

**Test Logic:**
- Collect N days of returns + VaR predictions
- Count exceptions (days where loss > VaR)
- Expected exceptions = N * (1 - confidence)
- If actual ≈ expected → VaR model valid (green)
- If actual >> expected → VaR model underestimates risk (red)

### Component 6: Risk Context Snapshot
**Purpose:** Capture portfolio state at risk evaluation time  
**Responsibilities:**
- Current positions (symbol, qty, avg_entry, unrealized_pnl)
- Cash balance
- Gross/net exposure
- Realized PnL (daily, weekly, all-time)
- Drawdown from peak
- Open orders (pending risk)

---

### Component 7: Risk Runtime Flow (Phase-0 Orchestration)
**Source:** User specification — deterministic evaluation pipeline

**Purpose:** Document end-to-end risk evaluation flow with clear stage boundaries and policy semantics.

**Risk Runtime Flow (5 Stages):**

**1. Build Context Snapshot (Deterministic)**
- **Input:** Order (from WP0A), Portfolio State (from WP0D Position Ledger)
- **Process:** Assemble minimal, deterministic context snapshot
- **Context Fields:**
  - `correlation_id`, `strategy_id`, `session_id` (from Order, WP0E common fields)
  - Instrument: `symbol`, optional `venue`
  - Order features: `side`, `qty`, `type`, optional `limit_price`
  - Exposure proxies: `current_position` (from Position Ledger), `notional` (qty × price), `open_orders_count`
  - Time: `as_of_time_utc` (snapshot timestamp)
- **Output:** Context Snapshot (deterministic, reproducible)
- **Responsibility:** Risk Runtime builds snapshot from WP0A Order + WP0D Position Ledger

**2. Evaluate Policies in Defined Order**
- **Input:** Context Snapshot
- **Process:** Iterate through policies in configured order (P1, P2, ..., Pn)
- **Policy Examples (Phase-0 Starter Set):**
  - **P1: SessionNotArmedPolicy** — Check if session armed for trading (default: NOT_ARMED → REJECT)
  - **P2: KillSwitchPolicy** — Check kill switch state (KILLED → REJECT, RECOVERING → DEFER)
  - **P3: SymbolBlocklistPolicy** — Check if symbol blacklisted (blocked → REJECT)
  - **P4: MaxOpenOrdersPolicy** — Check open_orders_count ≤ max_open_orders (exceeded → REJECT)
  - **P5: NotionalLimitPolicy** — Check notional ≤ max_notional_per_order (exceeded → REJECT)
  - **P6: PositionLimitPolicy** — Check current_position + qty ≤ max_position_per_symbol (exceeded → REJECT)
  - **P7: DailyLossLimitPolicy** — Check daily_pnl ≥ -max_daily_loss (breached → REJECT + trigger kill switch)
- **Short-Circuit Rules:**
  - **REJECT:** Terminate evaluation immediately, return REJECT decision (no further policies evaluated)
  - **DEFER:** Terminate evaluation immediately, return DEFER decision (requires manual resolution)
  - **ALLOW:** Continue to next policy (unless final policy, then return ALLOW)
- **Output:** Decision (ALLOW/REJECT/DEFER) + reason_code + policy_id
- **Responsibility:** Risk Runtime orchestrates policy evaluation, enforces short-circuit

**3. Produce Decision (ALLOW/REJECT/DEFER)**
- **Input:** Policy evaluation result (decision + reason_code + policy_id)
- **Process:** Finalize decision, populate RiskResult
- **RiskResult Fields:**
  - `decision`: ALLOW / REJECT / DEFER
  - `reason_code`: From standardized list (RISK_MAX_OPEN_ORDERS, RISK_NOTIONAL_LIMIT, RISK_SESSION_NOT_ARMED, etc.)
  - `policy_id`: Which policy produced decision (for debugging)
  - `metadata`: Context snapshot reference, evaluation_time_ms
- **Output:** RiskResult (WP0E contract)
- **Responsibility:** Risk Runtime packages result for WP0A

**4. Emit Risk Audit Record (Structured)**
- **Input:** RiskResult + Context Snapshot
- **Process:** Generate immutable audit record
- **Risk Audit Record Fields:**
  - `audit_id` (unique), `correlation_id` (from Order)
  - `decision` (ALLOW/REJECT/DEFER), `reason_code`, `policy_id`
  - `context_snapshot_ref` (reference to snapshot, not full snapshot to save space)
  - `order_id`, `symbol`, `side`, `qty`
  - `timestamp` (event_time_utc)
- **Output:** Risk Audit Record (appended to audit log)
- **Responsibility:** Risk Runtime logs all decisions for compliance
- **Note:** Audit records immutable, append-only (no deletions/modifications)

**5. Return to Pipeline Gate (WP0A)**
- **Input:** RiskResult
- **Process:** Return RiskResult to WP0A OSM
- **WP0A Gate Logic:**
  - **ALLOW:** Proceed to Stage 4 (Route Selection, WP0C)
  - **REJECT:** OSM transition CREATED → REJECTED, emit REJECTED event, stop pipeline
  - **DEFER:** OSM holds order, retry later (bounded retries), operator notification
- **Output:** Pipeline continues (ALLOW) or halts (REJECT/DEFER)
- **Responsibility:** WP0A OSM enforces risk decision

**Policy Semantics (Concept):**
- **Deterministic Evaluation Order:** Policies evaluated in fixed order (P1 → P2 → ... → Pn), no randomness
- **Short-Circuit:** REJECT/DEFER terminates immediately (conservative, fail-fast)
- **Pure Functions:** Policies are pure functions (context → decision), no side effects (except audit logging)
- **Conservative Defaults:** Missing context fields → DEFER with reason "RISK_UNKNOWN_CONTEXT" (never implicit ALLOW)
- **Policy Errors:** Policy exception → DEFER with reason "RISK_POLICY_ERROR" (safe default, no silent allow)

**Reason Codes (Controlled Vocabulary):**
- **RISK_MAX_OPEN_ORDERS:** Open orders count exceeds limit
- **RISK_NOTIONAL_LIMIT:** Order notional exceeds per-order limit
- **RISK_SYMBOL_BLOCKLIST:** Symbol on blacklist
- **RISK_SESSION_NOT_ARMED:** Session not armed for trading (default blocked)
- **RISK_UNKNOWN_CONTEXT:** Missing context fields (conservative DEFER)
- **RISK_POLICY_ERROR:** Policy evaluation exception (conservative DEFER)
- **RISK_KILL_SWITCH_KILLED:** Kill switch in KILLED state (all trading blocked)
- **RISK_KILL_SWITCH_RECOVERING:** Kill switch in RECOVERING state (temporary hold)
- **RISK_POSITION_LIMIT:** Position limit exceeded
- **RISK_DAILY_LOSS_LIMIT:** Daily loss limit breached

---

## Inputs / Outputs (Contracts)

**Source:** WP0E RiskHook Protocol + Roadmap WP0B dependencies

### Inputs
- **Order (from WP0E):** Order to evaluate (symbol, side, quantity, price)
- **Portfolio Context (from WP0A):** Current positions, cash, PnL, open orders
- **Market Data:** Current prices for mark-to-market (for PnL/VaR calculation)
- **Historical Returns:** Rolling window for VaR/CVaR (e.g., 252 days)
- **Risk Config:** Limits, VaR parameters, kill switch state

### Outputs
- **RiskResult (to WP0A):** Decision (ALLOW/BLOCK/PAUSE), reason, metadata
  - ALLOW: Order approved, proceed to submission
  - BLOCK: Order rejected, provide reason (e.g., "max DD exceeded", "kill switch KILLED")
  - PAUSE: Temporary hold, retry later (e.g., "kill switch RECOVERING")
- **Risk Audit Log Entry:** Decision + context + timestamp for compliance
- **VaR Report (evidence):** Portfolio VaR/CVaR + Kupiec POF results
- **Stress Report (evidence):** Scenario impacts + portfolio resilience

**Contracts Used (from WP0E):**
- Order (input)
- RiskHook Protocol (interface)
- RiskResult (output)
- RiskDecision enum (ALLOW/BLOCK/PAUSE)

---

## Failure Modes & Handling

**Source:** Inferred from risk runtime design + kill switch state machine

### Failure Mode 1: VaR Calculation Failure
**Scenario:** Insufficient historical data or calculation error during VaR evaluation  
**Impact:** Unable to assess portfolio risk, risk evaluation blocks  
**Mitigation:**
- Fallback to conservative default (e.g., assume high risk, BLOCK)
- Require minimum data window (e.g., 30 days) before enabling VaR checks
- Log VaR calculation errors for debugging
- Graceful degradation: disable VaR if unstable, rely on loss limits only

### Failure Mode 2: Kill Switch State Corruption
**Scenario:** Kill switch state file corrupted, state ambiguous on restart  
**Impact:** Unclear if trading allowed, potential unsafe resumption  
**Mitigation:**
- Default to KILLED state if state unclear (safe default)
- Validate state file on load (checksum, schema validation)
- Require operator confirmation before ACTIVE
- Audit log tracks all state transitions

### Failure Mode 3: Loss Limit False Positive
**Scenario:** PnL calculation error causes false limit breach (e.g., missing fill, wrong price)  
**Impact:** Trading halted unnecessarily, lost opportunities  
**Mitigation:**
- Validate PnL against reconciliation (WP0D)
- Require operator override for limit resets
- Log all limit breaches with context for review
- Separate daily/weekly/max DD limits (multiple trip wires)

### Failure Mode 4: Risk Evaluation Timeout
**Scenario:** VaR/Stress calculation takes too long, blocks order submission  
**Impact:** Order latency, missed trading opportunities  
**Mitigation:**
- Set timeout on risk evaluation (e.g., 1-2s)
- Default to BLOCK on timeout (safe default)
- Pre-calculate VaR/Stress periodically (e.g., every 5 min), cache results
- Log timeouts for performance tuning

### Failure Mode 5: Kill Switch Trigger Storm
**Scenario:** Multiple auto-triggers fire simultaneously (e.g., max DD + daily loss)  
**Impact:** Confusion about trigger reason, unclear recovery path  
**Mitigation:**
- Priority ordering of triggers (max DD > daily > weekly)
- Log all triggers with context
- Operator sees primary trigger in UI
- Recovery checklist addresses all trigger conditions

### Failure Mode 6: Stress Scenario Stale Data
**Scenario:** Stress scenarios outdated (e.g., using 2020 COVID but now 2025)  
**Impact:** Stress test irrelevant, underestimates current risks  
**Mitigation:**
- Document scenario update cadence (e.g., quarterly)
- Operator review of scenarios before live use
- Version scenarios (COVID_2020_v1.json)
- Flag scenarios older than X months in reports

---

## Acceptance Criteria (Gate-Tauglich)

**Source:** Roadmap WP0B DoD (lines 140-149)

### RiskHook Implementation Criteria
- [ ] RiskHook protocol implemented (evaluate_order, check_kill_switch, evaluate_position_change)
- [ ] Returns RiskResult with decision (ALLOW/BLOCK/PAUSE) + reason + metadata
- [ ] Integrates with WP0A OSM (called before CREATED → SUBMITTED)
- [ ] All decisions logged to risk audit trail

### Kill Switch Criteria
- [ ] State machine implemented (ACTIVE, KILLED, RECOVERING)
- [ ] Manual trigger (operator command)
- [ ] Auto triggers (max DD, daily/weekly loss)
- [ ] State persisted across restarts
- [ ] check_kill_switch() returns BLOCK when KILLED, PAUSE when RECOVERING
- [ ] Cooldown period enforced before RECOVERING → ACTIVE

### Risk Metrics Criteria
- [ ] Portfolio VaR implemented (Historical, Parametric, EWMA)
- [ ] Portfolio CVaR implemented
- [ ] Stress testing implemented (apply scenarios, calculate impact)
- [ ] Deterministic (same inputs → same outputs)
- [ ] CI-friendly (fast, no external deps)

### Loss Limits Criteria
- [ ] Daily loss limit enforced
- [ ] Weekly loss limit enforced
- [ ] Max drawdown circuit breaker enforced
- [ ] Position limits per symbol enforced
- [ ] Gross exposure limit enforced

### Kupiec POF Test Criteria
- [ ] VaR exceptions counted
- [ ] Likelihood ratio test calculated
- [ ] Traffic light report generated (green/yellow/red)

### Testing Criteria
- [ ] Limits trigger deterministically in tests
- [ ] Kill switch behavior simulated (manual + auto triggers)
- [ ] Report generators stable (CI-friendly, no flakiness)
- [ ] Test coverage ≥ 90% for risk runtime modules
- [ ] Integration test: WP0A OSM calls RiskHook.evaluate_order()

### Evidence Criteria
- [ ] VaR/CVaR/Kupiec reports generated
- [ ] Stress suite reports generated
- [ ] Risk audit trail demonstrates decision logging Human: continue

---

## Evidence Checklist

**Source:** Roadmap WP0B Evidence (lines 151-153)

### Required Evidence Artifacts (Implementation Run)
- [ ] **VaR/CVaR/Kupiec Report:** Portfolio risk metrics + validation
  - Location pattern: `reports/risk/var_cvar_kupiec_*.md`
  - Content: Historical/Parametric/EWMA VaR, CVaR, Kupiec POF test results, traffic light status
  - Purpose: Demonstrate VaR validity, regulatory compliance
- [ ] **Stress Suite Report:** Historical scenario impacts
  - Location pattern: `reports/risk/stress_suite_*.md`
  - Content: Scenario definitions, portfolio impact (% loss), resilience assessment
  - Purpose: Demonstrate stress preparedness, tail risk awareness
- [ ] **Kill Switch Audit Log:** State transitions + triggers
  - Content: All kill switch events (trigger reason, timestamp, operator actions)
  - Purpose: Compliance, post-mortem analysis
- [ ] **Risk Decisions Audit:** All evaluate_order() calls + outcomes
  - Content: Order ID, decision (ALLOW/BLOCK/PAUSE), reason, context snapshot
  - Purpose: Audit trail, compliance, debugging
- [ ] **Test Results:** Comprehensive risk runtime tests
  - Target: Limits deterministic, kill switch simulation, report generation
  - Coverage: RiskHook, kill switch, VaR, limits, Kupiec
  - Evidence: pytest output + coverage report
- [ ] **Completion Report:** WP0B implementation documentation
  - Location pattern: `docs/execution/WP0B_IMPLEMENTATION_REPORT.md`

### Evidence Generation (Not in This Docs-Only Run)
**Note:** Evidence artifacts generated during implementation run, not docs-only prep.

---

## Integration Notes

**Source:** Roadmap dependency graph + RiskHook protocol from WP0E

### Depends On
- **WP0E (Contracts & Interfaces):** REQUIRED, BLOCKING
  - Uses: RiskHook Protocol (evaluate_order, check_kill_switch, evaluate_position_change)
  - Uses: RiskResult type (decision + reason + metadata)
  - Uses: RiskDecision enum (ALLOW/BLOCK/PAUSE)
  - Uses: Order type (to evaluate)
  - Integration Point: WP0B implements RiskHook protocol defined by WP0E
  - **Critical:** WP0E must be complete before WP0B (protocol definition required)

### Consumed By
- **WP0A (Execution Core):** OSM calls RiskHook.evaluate_order() before order submission
  - Integration Point: Pre-submission risk gate
  - Data Flow: WP0A (Order + context) → WP0B (evaluate) → WP0B (RiskResult) → WP0A (ALLOW/BLOCK/PAUSE)
  - Timing: Before CREATED → SUBMITTED transition
  - Handling: ALLOW=proceed, BLOCK=reject order, PAUSE=retry later
- **WP0C (Order Routing):** Indirectly (via WP0A), risk approval required before routing
- **WP0D (Recon/Ledger):** Consumes risk audit trail for compliance reporting

### Integration Sequence
1. **WP0E first (blocker):** RiskHook protocol must exist
2. **WP0B implementation:** Can proceed once WP0E complete
3. **Parallel with WP0A:** WP0A and WP0B develop in parallel (both depend only on WP0E)
4. **Integration testing:** WP0A + WP0B together (OSM calls RiskHook)
5. **WP0C after WP0A+WP0B:** Routing assumes risk-approved orders

**Critical Path:** WP0E → WP0B (parallel with WP0A) → Integration

### Cross-WP Interfaces
- **WP0B → WP0A (via RiskHook):**
  - **evaluate_order(order, context):** Pre-submission check
    - Input: Order, portfolio context (positions, cash, PnL)
    - Output: RiskResult (ALLOW/BLOCK/PAUSE + reason)
    - Timing: Called by OSM.submit_order() before state transition
  - **check_kill_switch():** Global trading halt check
    - Input: None (checks internal kill switch state)
    - Output: RiskResult (ALLOW if ACTIVE, BLOCK if KILLED, PAUSE if RECOVERING)
    - Timing: Called on every order, first check
  - **evaluate_position_change(symbol, qty, side, context):** Position limit check
    - Input: Proposed position change
    - Output: RiskResult (ALLOW if within limits, BLOCK if exceeds)
    - Timing: Called before applying fills (by WP0A Position Ledger)

### Integration Risks
1. **Risk Evaluation Latency:** Slow VaR/Stress calculation delays order submission
   - Mitigation: Timeout (1-2s), cache periodic calculations, default to BLOCK on timeout
2. **Context Staleness:** Portfolio context outdated by time risk evaluates
   - Mitigation: WP0A provides fresh context snapshot at evaluation time, timestamp context
3. **Kill Switch Coordination:** Kill switch state changes while order in-flight
   - Mitigation: Re-check kill switch at each state transition, idempotent checks
4. **Audit Log Completeness:** Risk decisions not logged, compliance gap
   - Mitigation: Log ALL evaluate_order() calls, include full context in log

### Breaking Change Protocol
If WP0B must change RiskHook interface:
1. Notify A0 + WP0E (contract owner) + WP0A (consumer)
2. Version interface if breaking (RiskHookV2)
3. Coordinate migration across all consumers
4. Update WP0E contracts + WP0B implementation + WP0A integration

---

## Next Implementation Run

**Note:** This is a docs-only specification. Code implementation follows in separate PR.

### Implementation Approach
- **Module Locations:** Risk runtime modules (RiskHook impl, kill switch, limits, VaR/Stress)
  - Leverage existing `src/risk_layer/` (kill switch, VaR backtest)
  - Leverage existing `src/risk/` (VaR, CVaR, stress calculations)
  - New: RiskHook implementation bridging WP0E protocol to risk layer
- **Test Locations:** Risk runtime tests (unit + integration with WP0A)
- **Evidence Locations:** Risk reports (gitignored, generated on-demand)

### Implementation Checklist
- [ ] Implement RiskHook protocol (evaluate_order, check_kill_switch, evaluate_position_change)
- [ ] Integrate kill switch (existing `src/risk_layer/kill_switch/`)
- [ ] Implement loss limits enforcer (daily, weekly, max DD circuit breaker)
- [ ] Integrate VaR/CVaR calculations (existing `src/risk/var.py`)
- [ ] Integrate stress testing (existing `src/risk/stress_tester.py`)
- [ ] Implement Kupiec POF test (existing `src/risk_layer/var_backtest/kupiec_pof.py`)
- [ ] Implement risk context snapshot (portfolio state at evaluation time)
- [ ] Implement risk audit trail (log all decisions)
- [ ] Write unit tests (RiskHook, limits, kill switch integration)
- [ ] Write integration test (WP0A OSM → RiskHook.evaluate_order())
- [ ] Generate VaR/CVaR/Kupiec report (evidence)
- [ ] Generate stress suite report (evidence)
- [ ] Create completion report documenting DoD verification

### Implementation Sequence (Within WP0B)
1. **Contracts First:** Ensure WP0E complete (RiskHook protocol, RiskResult type available)
2. **RiskHook Skeleton:** Implement protocol methods (stub logic initially)
3. **Kill Switch Integration:** Wire check_kill_switch() to existing kill switch
4. **Limits Enforcer:** Daily/weekly loss, max DD, position limits
5. **VaR/Stress Integration:** Call existing src/risk/ calculations
6. **Kupiec POF:** Validate VaR using existing backtest module
7. **Audit Trail:** Log all decisions with context
8. **Integration:** Test with WP0A (OSM calls RiskHook)

### Post-Implementation
- [ ] Update Integration Day Plan with WP0B status
- [ ] Notify A0: WP0B complete, ready for WP0A integration testing
- [ ] Provide completion report link to WP0A (for integration)
- [ ] Coordinate with WP0A on context snapshot requirements
- [ ] Verify no performance regression (risk evaluation < 2s)

---

**WP0B Task-Packet Status:** ✅ COMPLETE (A3)  
**Last Updated:** 2025-12-31 (A3 completion)  
**Source Traceability:** Roadmap WP0B (lines 136-154) + Risk Layer Overview + Kill Switch docs  
**Link Hygiene:** ✅ All references point to existing docs or intra-PR files (WP0E, WP0A)
