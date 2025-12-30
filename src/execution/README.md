# Execution Module (Full-Featured)

**Location:** `src/execution/`  
**Purpose:** Production execution pipeline with full feature set  
**Status:** Production-ready

---

## Purpose

This module provides the **full-featured execution pipeline** for:
1. Signal-to-order conversion
2. Order state management
3. Risk hook integration
4. Retry policies
5. Ledger and audit trail

**Used In:** Live trading, paper trading, shadow mode, testnet

---

## Relationship to `src/execution_simple/`

| Aspect | `src/execution/` (This Module) | `src/execution_simple/` |
|--------|-------------------------------|-------------------------|
| **Purpose** | Production execution | Simplified/legacy |
| **Features** | Full (state machine, retry, audit) | Basic |
| **Status** | Active (production) | Legacy/deprecated? |
| **Used In** | Live/shadow sessions | Old backtest code? |

**Recommendation:** Use `src/execution/` for all new code. `src/execution_simple/` appears to be legacy.

---

## Key Components

### ExecutionPipeline (`pipeline.py`)
Main execution orchestration:
- Signal → OrderIntent → OrderRequest
- Order generation and execution
- Result tracking

### Order State Machine (`order_state_machine.py`)
Deterministic order lifecycle:
- States: CREATED → SUBMITTED → ACKNOWLEDGED → FILLED
- Idempotent transitions
- Validation

### Contracts (`contracts.py`)
Order and fill data structures:
- Order (with state, timestamps, metadata)
- Fill (execution details)
- LedgerEntry (accounting)

### Retry Policy (`retry_policy.py`)
Exponential backoff with jitter:
- Configurable max retries
- Error classification (retryable vs non-retryable)

### Order Ledger (`order_ledger.py`)
Audit trail for all orders

---

## Usage

```python
from src.execution.pipeline import ExecutionPipeline

# Create pipeline
pipeline = ExecutionPipeline.for_paper(market_context)

# Execute orders
results = pipeline.execute_orders([order1, order2])
```

---

## For Live Trading

**Use this module (`src/execution/`)** for live trading.

**Status:** ✅ Production-ready
- Well-tested
- State machine ensures correctness
- Retry policies handle transient errors
- Audit trail for compliance

---

## Revision History

| Date | Version | Changes |
|------|---------|---------|
| 2025-12-30 | 1.0 | Initial README for FND-0003 remediation |
