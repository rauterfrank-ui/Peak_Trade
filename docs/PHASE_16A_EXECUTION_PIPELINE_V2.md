# Phase 16A – ExecutionPipeline V2 (Governance-aware, keine echten Live-Orders)

## Ziel

Die **ExecutionPipeline V2** erweitert die bestehende Pipeline um:
- **Governance-Integration**: `get_governance_status("live_order_execution")` wird geprüft
- **Live-Blocking**: Bei `env="live"` wird eine `GovernanceViolationError` / `LiveExecutionLockedError` geworfen
- **Zentrale `submit_order()`-Methode**: Neue High-Level-API mit `OrderIntent`
- **Environment-Executor-Mapping**: Klare Zuordnung von Environment zu Executor

## Nicht-Ziele

- ❌ Keine echten Live-Orders – `live_order_execution` bleibt `"locked"`
- ❌ Keine Live-Exchange-Integration
- ❌ Keine Änderungen an bestehenden Risk-Limits oder Safety-Guards

## Architektur-Skizze

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Strategy / Portfolio                            │
└─────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         OrderIntent                                      │
│  - symbol: "BTC/EUR"                                                    │
│  - side: "buy"                                                          │
│  - quantity: 0.01                                                       │
│  - strategy_key: "ma_crossover"                                         │
│  - current_price: 50000.0                                               │
└─────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                  ExecutionPipeline.submit_order(intent)                 │
│ ┌─────────────────────────────────────────────────────────────────────┐ │
│ │  1. Input Validation                                                │ │
│ │     - quantity > 0?                                                 │ │
│ │     - symbol valid?                                                 │ │
│ └─────────────────────────────────────────────────────────────────────┘ │
│                                   │                                     │
│                                   ▼                                     │
│ ┌─────────────────────────────────────────────────────────────────────┐ │
│ │  2. Governance-Check                                                │ │
│ │     get_governance_status("live_order_execution")                   │ │
│ │     ┌────────────────────────────────────────┐                      │ │
│ │     │ env="live" && status="locked"?         │                      │ │
│ │     │   → LiveExecutionLockedError           │                      │ │
│ │     │   → oder: ExecutionResult(BLOCKED)     │                      │ │
│ │     └────────────────────────────────────────┘                      │ │
│ └─────────────────────────────────────────────────────────────────────┘ │
│                                   │                                     │
│                                   ▼                                     │
│ ┌─────────────────────────────────────────────────────────────────────┐ │
│ │  3. SafetyGuard-Check                                               │ │
│ │     ensure_may_place_order(is_testnet=...)                          │ │
│ └─────────────────────────────────────────────────────────────────────┘ │
│                                   │                                     │
│                                   ▼                                     │
│ ┌─────────────────────────────────────────────────────────────────────┐ │
│ │  4. Risk-Check (LiveRiskLimits)                                     │ │
│ │     check_orders([LiveOrderRequest])                                │ │
│ │     ┌────────────────────────────────────────┐                      │ │
│ │     │ allowed=False?                         │                      │ │
│ │     │   → ExecutionResult(BLOCKED_BY_RISK)   │                      │ │
│ │     └────────────────────────────────────────┘                      │ │
│ └─────────────────────────────────────────────────────────────────────┘ │
│                                   │                                     │
│                                   ▼                                     │
│ ┌─────────────────────────────────────────────────────────────────────┐ │
│ │  5. Executor-Dispatch (nach Environment)                            │ │
│ │     ┌──────────────────────────────────────────────────┐            │ │
│ │     │ paper  → PaperOrderExecutor                      │            │ │
│ │     │ shadow → ShadowOrderExecutor                     │            │ │
│ │     │ testnet→ TestnetExchangeOrderExecutor (dry-run)  │            │ │
│ │     │ live   → 🚫 GESPERRT (Governance-Lock)           │            │ │
│ │     └──────────────────────────────────────────────────┘            │ │
│ └─────────────────────────────────────────────────────────────────────┘ │
│                                   │                                     │
│                                   ▼                                     │
│ ┌─────────────────────────────────────────────────────────────────────┐ │
│ │  6. Run-Logging (optional)                                          │ │
│ │     LiveRunLogger.log_event(...)                                    │ │
│ └─────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         ExecutionResult                                  │
│  - status: SUCCESS | BLOCKED_BY_RISK | BLOCKED_BY_GOVERNANCE | ...      │
│  - executed_orders: [OrderExecutionResult]                              │
│  - rejected: bool                                                       │
│  - reason: str                                                          │
│  - environment: "paper" | "shadow" | "testnet" | "live"                 │
│  - governance_status: "locked" | "approved_2026" | ...                  │
└─────────────────────────────────────────────────────────────────────────┘
```

## Governance-Hinweis

### Live-Order-Execution ist gesperrt

```python
# In src/governance/go_no_go.py:
_FEATURE_STATUS_MAP = {
    "live_order_execution": "locked",  # ← GESPERRT
    "live_alerts_cluster_82_85": "approved_2026",
}
```

### Pipeline-Verhalten bei `env="live"`

```python
# Option 1: Exception werfen (Default)
result = pipeline.submit_order(intent, raise_on_governance_violation=True)
# → wirft LiveExecutionLockedError

# Option 2: Result ohne Exception
result = pipeline.submit_order(intent, raise_on_governance_violation=False)
# → result.status == ExecutionStatus.BLOCKED_BY_GOVERNANCE
# → result.is_blocked_by_governance == True
```

## Environment-Executor-Mapping

| Environment | Executor | Verhalten |
|-------------|----------|-----------|
| `paper` | `PaperOrderExecutor` | Simulation ohne echte Orders |
| `shadow` | `ShadowOrderExecutor` | Read-only Simulation, Logging |
| `testnet` | `TestnetExchangeOrderExecutor` | Testnet-Orders (dry-run in Phase 16A) |
| `live` | **KEIN EXECUTOR** | Governance-Lock → `LiveExecutionLockedError` |

## API-Übersicht

### OrderIntent

```python
@dataclass
class OrderIntent:
    symbol: str              # z.B. "BTC/EUR"
    side: OrderSide          # "buy" oder "sell"
    quantity: float          # Menge
    order_type: str = "market"  # "market" oder "limit"
    limit_price: Optional[float] = None
    strategy_key: Optional[str] = None
    current_price: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
```

### submit_order()

```python
def submit_order(
    self,
    intent: OrderIntent,
    *,
    raise_on_governance_violation: bool = True,
) -> ExecutionResult:
    """
    Zentrale Methode für Governance-aware Order-Submission.

    Args:
        intent: OrderIntent mit Order-Details
        raise_on_governance_violation: Exception bei Live-Block werfen?

    Returns:
        ExecutionResult mit Status, executed_orders, governance_status

    Raises:
        LiveExecutionLockedError: Bei env="live" (wenn raise=True)
    """
```

### ExecutionResult (erweitert)

```python
@dataclass
class ExecutionResult:
    # Bestehende Felder
    risk_check: Optional[LiveRiskCheckResult]
    executed_orders: List[OrderExecutionResult]
    rejected: bool
    reason: Optional[str]

    # Neue Felder (Phase 16A V2)
    status: ExecutionStatus  # SUCCESS, BLOCKED_BY_RISK, BLOCKED_BY_GOVERNANCE, ...
    environment: Optional[str]  # "paper", "shadow", "testnet", "live"
    governance_status: Optional[GovernanceStatus]  # "locked", "approved_2026", ...
```

### ExecutionStatus (neu)

```python
class ExecutionStatus(str, Enum):
    SUCCESS = "success"
    BLOCKED_BY_RISK = "blocked_by_risk"
    BLOCKED_BY_GOVERNANCE = "blocked_by_governance"
    BLOCKED_BY_SAFETY = "blocked_by_safety"
    BLOCKED_BY_ENVIRONMENT = "blocked_by_environment"
    REJECTED = "rejected"
    ERROR = "error"
    INVALID = "invalid"  # Ungueltiger Input (z.B. quantity <= 0)
```

## Exceptions

### GovernanceViolationError

```python
class GovernanceViolationError(ExecutionPipelineError):
    """Governance-Verletzung: Operation ist gesperrt."""
    feature_key: str  # z.B. "live_order_execution"
    status: GovernanceStatus  # z.B. "locked"
    message: str
```

### LiveExecutionLockedError

```python
class LiveExecutionLockedError(GovernanceViolationError):
    """Live-Execution ist governance-seitig gesperrt."""
    # Spezialisiert für live_order_execution == "locked"
```

## Beispiel-Usage

### Paper-Trading

```python
from src.execution import ExecutionPipeline, OrderIntent
from src.core.environment import EnvironmentConfig, TradingEnvironment
from src.orders.paper import PaperMarketContext, PaperOrderExecutor

# Setup
env_config = EnvironmentConfig(environment=TradingEnvironment.PAPER)
executor = PaperOrderExecutor(PaperMarketContext(prices={"BTC/EUR": 50000.0}))
pipeline = ExecutionPipeline(executor=executor, env_config=env_config)

# Order Intent erstellen
intent = OrderIntent(
    symbol="BTC/EUR",
    side="buy",
    quantity=0.01,
    strategy_key="ma_crossover",
    current_price=50000.0,
)

# Order ausführen
result = pipeline.submit_order(intent)

if result.is_success:
    print(f"Order ausgefuehrt: {len(result.executed_orders)} Orders")
    for order in result.executed_orders:
        print(f"  {order.fill.side} {order.fill.quantity} @ {order.fill.price}")
else:
    print(f"Order blockiert: {result.status.value}")
    print(f"Grund: {result.reason}")
```

### Live-Trading (Governance-Block)

```python
from src.execution import ExecutionPipeline, OrderIntent, LiveExecutionLockedError
from src.core.environment import EnvironmentConfig, TradingEnvironment
from src.orders.paper import PaperMarketContext, PaperOrderExecutor

# Setup mit LIVE-Mode
env_config = EnvironmentConfig(environment=TradingEnvironment.LIVE)
executor = PaperOrderExecutor(PaperMarketContext(prices={"BTC/EUR": 50000.0}))
pipeline = ExecutionPipeline(executor=executor, env_config=env_config)

intent = OrderIntent(symbol="BTC/EUR", side="buy", quantity=0.01)

# Option 1: Exception
try:
    result = pipeline.submit_order(intent)
except LiveExecutionLockedError as e:
    print(f"Governance-Block: {e.message}")
    print(f"Feature: {e.feature_key}, Status: {e.status}")

# Option 2: Result ohne Exception
result = pipeline.submit_order(intent, raise_on_governance_violation=False)
if result.is_blocked_by_governance:
    print(f"Governance blockiert: {result.reason}")
    print(f"Governance-Status: {result.governance_status}")
```

## Tests / Akzeptanzkriterien

### Testdatei: `tests/test_execution_pipeline_governance.py`

| Test | Beschreibung | Status |
|------|--------------|--------|
| `test_live_env_raises_governance_exception` | env="live" → LiveExecutionLockedError | ✅ |
| `test_live_env_returns_blocked_result_without_raise` | env="live" + no-raise → BLOCKED_BY_GOVERNANCE | ✅ |
| `test_governance_module_is_actually_called` | get_governance_status("live_order_execution") wird aufgerufen | ✅ |
| `test_paper_env_executes_orders` | env="paper" + Risk ok → Orders ausgeführt | ✅ |
| `test_shadow_env_executes_orders` | env="shadow" + Risk ok → Shadow-Orders ausgeführt | ✅ |
| `test_testnet_env_executes_orders` | env="testnet" + Risk ok → Orders ausgeführt | ✅ |
| `test_risk_fail_blocks_execution` | Risk-Fail → BLOCKED_BY_RISK | ✅ |
| `test_no_executor_call_when_live_blocked` | Live-Block → Executor NICHT aufgerufen | ✅ |
| `test_order_intent_to_order_request_conversion` | OrderIntent → OrderRequest korrekt | ✅ |
| `test_governance_status_in_result` | governance_status im Result gesetzt | ✅ |
| `test_invalid_quantity_returns_error` | quantity <= 0 → INVALID | ✅ |

### Test-Ausführung

```bash
# Nur Governance-Tests
python3 -m pytest tests/test_execution_pipeline_governance.py -v

# Alle ExecutionPipeline-Tests
python3 -m pytest tests/test_execution_pipeline.py tests/test_execution_pipeline_governance.py -v
```

## Zukünftige Erweiterungen

### Phase 16B: Governance-Unlock für Testnet

```python
# Mögliche zukünftige Erweiterung in go_no_go.py:
_FEATURE_STATUS_MAP = {
    "live_order_execution": "locked",
    "testnet_order_execution": "approved_2026",  # NEU
}
```

### Phase 16C: Live-Order-Execution (zukünftig)

```python
# Wenn live_order_execution "approved" wird:
_FEATURE_STATUS_MAP = {
    "live_order_execution": "approved_2027",  # ZUKÜNFTIG
}
```

## Zusammenfassung

Phase 16A V2 stellt eine **governance-aware ExecutionPipeline** bereit:

- ✅ **Governance-Integration**: `get_governance_status("live_order_execution")` wird geprüft
- ✅ **Live-Blocking**: Bei `env="live"` wird `LiveExecutionLockedError` geworfen
- ✅ **Keine echten Live-Orders**: `live_order_execution` bleibt `"locked"`
- ✅ **Neue `submit_order()`-API**: Mit `OrderIntent` und detailliertem `ExecutionResult`
- ✅ **Environment-Mapping**: paper/shadow/testnet → passender Executor
- ✅ **Risk-Integration**: Bestehende `LiveRiskLimits` werden genutzt
- ✅ **15+ neue Tests**: Alle Akzeptanzkriterien abgedeckt

Die Pipeline ist so designed, dass zukünftige Governance-Änderungen (z.B. Unlock für Live) ohne Breaking Changes möglich sind.
