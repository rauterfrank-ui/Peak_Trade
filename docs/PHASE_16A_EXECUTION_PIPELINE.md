# Phase 16A – ExecutionPipeline (Core-Package & Klasse)

## Einleitung

Die **ExecutionPipeline** ist eine zentrale Komponente im Peak_Trade Framework, die Orders aus Strategien/Portfolios entgegennimmt, über **Environment & Safety** schickt, an den passenden **Executor** weiterreicht und Events für den **Run-Logger** erzeugt.

**Wichtig:** Phase 16A ist bewusst noch **ohne Live-Support**. Der LIVE-Mode wird hart blockiert, um sicherzustellen, dass keine echten Orders versehentlich ausgeführt werden können.

## Architektur-Überblick

```
Strategy/Portfolio
     │
     ▼
ExecutionPipeline
  ├─ Environment-Check (LIVE blockiert in Phase 16A)
  ├─ SafetyGuard (ensure_may_place_order)
  ├─ LiveRiskLimits (optional, check_orders)
  ├─ OrderExecutor (Paper/Testnet/Mock)
  └─ RunLogger (optional, log_event)
```

### Workflow

1. **Environment-Check**: Prüft den Environment-Mode (PAPER/TESTNET/LIVE)
   - LIVE-Mode wird in Phase 16A hart blockiert
2. **SafetyGuard-Check**: Prüft ob Order-Platzierung erlaubt ist
   - Wirft Exception bei Blockierung
3. **Risk-Check** (optional): Prüft Orders gegen LiveRiskLimits
   - Konvertiert OrderRequest → LiveOrderRequest
   - Gibt LiveRiskCheckResult zurück
4. **Executor**: Führt Orders aus (wenn alle Checks passiert)
   - PaperOrderExecutor, TestnetOrderExecutor, etc.
5. **Run-Logging** (optional): Loggt Events über LiveRunLogger
   - Erstellt LiveRunEvent für jede ausgeführte Order

## Public-API

### ExecutionPipeline

```python
class ExecutionPipeline:
    def __init__(
        self,
        executor: OrderExecutor,
        config: Optional[ExecutionPipelineConfig] = None,
        env_config: Optional[EnvironmentConfig] = None,
        safety_guard: Optional[SafetyGuard] = None,
        risk_limits: Optional[LiveRiskLimits] = None,
        run_logger: Optional[LiveRunLogger] = None,
    ) -> None:
        ...

    def execute_with_safety(
        self,
        orders: Sequence[OrderRequest],
        context: Optional[Dict[str, Any]] = None,
    ) -> ExecutionResult:
        """
        Führt Orders mit vollständigen Safety- und Risk-Checks aus.

        Returns:
            ExecutionResult mit Risk-Check-Ergebnis, executed_orders, rejected-Flag
        """
        ...
```

### ExecutionResult

```python
@dataclass
class ExecutionResult:
    risk_check: Optional[LiveRiskCheckResult]  # Ergebnis des Risk-Checks
    executed_orders: List[OrderExecutionResult]  # Ausgeführte Orders
    rejected: bool  # True wenn blockiert
    reason: Optional[str]  # Grund für Blockierung
    execution_results: List[OrderExecutionResult]  # Alias für executed_orders
```

## Beispiel-Nutzung

### Basis-Beispiel (Paper-Modus)

```python
from src.core.environment import EnvironmentConfig, TradingEnvironment
from src.live.safety import SafetyGuard
from src.orders.paper import PaperMarketContext, PaperOrderExecutor
from src.orders.base import OrderRequest
from src.execution import ExecutionPipeline

# Environment konfigurieren
env_config = EnvironmentConfig(environment=TradingEnvironment.PAPER)
safety_guard = SafetyGuard(env_config=env_config)

# Executor erstellen
market_context = PaperMarketContext(prices={"BTC/EUR": 50000.0})
executor = PaperOrderExecutor(market_context)

# Pipeline erstellen
pipeline = ExecutionPipeline(
    executor=executor,
    env_config=env_config,
    safety_guard=safety_guard,
)

# Order erstellen und ausführen
order = OrderRequest(symbol="BTC/EUR", side="buy", quantity=0.01)
result = pipeline.execute_with_safety([order])

if result.rejected:
    print(f"Order blockiert: {result.reason}")
else:
    print(f"Order ausgeführt: {len(result.executed_orders)} Orders")
    for exec_result in result.executed_orders:
        if exec_result.is_filled:
            print(f"  Filled: {exec_result.fill.quantity} @ {exec_result.fill.price}")
```

### Mit Risk-Limits

```python
from src.live.risk_limits import LiveRiskLimits

# Risk-Limits konfigurieren
risk_limits = LiveRiskLimits.from_config(cfg, starting_cash=10000.0)

# Pipeline mit Risk-Limits
pipeline = ExecutionPipeline(
    executor=executor,
    env_config=env_config,
    safety_guard=safety_guard,
    risk_limits=risk_limits,
)

# Order mit Kontext (für Notional-Berechnung)
order = OrderRequest(symbol="BTC/EUR", side="buy", quantity=0.01)
result = pipeline.execute_with_safety(
    [order],
    context={"current_price": 50000.0}
)

if result.risk_check and not result.risk_check.allowed:
    print(f"Risk-Check fehlgeschlagen: {result.risk_check.reasons}")
```

### Mit Run-Logging

```python
from src.live.run_logging import LiveRunLogger, LiveRunMetadata, ShadowPaperLoggingConfig

# Run-Logger erstellen
logging_cfg = ShadowPaperLoggingConfig(enabled=True, base_dir="live_runs")
metadata = LiveRunMetadata(
    run_id="test_run_001",
    mode="paper",
    strategy_name="ma_crossover",
    symbol="BTC/EUR",
    timeframe="1m",
)
run_logger = LiveRunLogger(logging_cfg, metadata)
run_logger.initialize()

# Pipeline mit Run-Logger
pipeline = ExecutionPipeline(
    executor=executor,
    env_config=env_config,
    safety_guard=safety_guard,
    run_logger=run_logger,
)

# Orders ausführen (werden automatisch geloggt)
result = pipeline.execute_with_safety([order])

# Logger finalisieren
run_logger.finalize()
```

## Safety-Notizen

### LIVE-Mode: Geblockt in Phase 16A

In Phase 16A wird der LIVE-Mode **hart blockiert**. Wenn `env_config.is_live == True`, gibt `execute_with_safety()` sofort ein `ExecutionResult` mit `rejected=True` zurück, ohne den Executor aufzurufen.

```python
if env_config.is_live:
    return ExecutionResult(
        rejected=True,
        reason="live_mode_not_supported_in_phase_16a",
        executed_orders=[],
    )
```

### Keine echten Netzwerk-Calls

Die ExecutionPipeline selbst macht **keine Netzwerk-Calls**. Alle IO-Operationen (Exchange-API-Calls, etc.) finden ausschließlich in den Executors statt. Die Pipeline ist eine reine Orchestrierungs-Schicht.

### Zukünftige Erweiterungen (Phase 16B/16C)

In späteren Phasen kann Live-Support hinzugefügt werden:

1. **Phase 16B**: Live-Executor-Integration
   - LiveOrderExecutor wird in die Pipeline integriert
   - Zusätzliche Safety-Gates für Live-Orders
   - Erweiterte Risk-Checks für Live-Trading

2. **Phase 16C**: Live-Orderflow
   - Echte Exchange-API-Integration
   - Order-Status-Tracking
   - Retry-Logik bei Fehlern

Die aktuelle Architektur ist so designed, dass diese Erweiterungen ohne Breaking Changes möglich sind.

## Integration mit bestehenden Komponenten

### ShadowSession

Die ExecutionPipeline kann bereits in `ShadowPaperSession` verwendet werden (siehe `src/live/shadow_session.py`). Die Session nutzt die Pipeline für Order-Ausführung:

```python
# In ShadowPaperSession.step_once()
orders = self._pipeline.signal_to_orders(event, position_size, current_position)
results = self._pipeline.execute_orders(orders)  # Oder execute_with_safety()
```

### BacktestEngine

Die Pipeline wird auch in Backtests verwendet:

```python
pipeline = ExecutionPipeline.for_paper(market_context)
results = pipeline.execute_from_signals(signals, prices, symbol="BTC/EUR")
```

## Testing

Unit-Tests befinden sich in `tests/test_execution_pipeline.py`:

- `test_execution_pipeline_blocks_live_mode`: LIVE-Mode wird blockiert
- `test_execution_pipeline_runs_safety_and_blocks_on_violation`: SafetyGuard blockiert
- `test_execution_pipeline_executes_orders_when_safe`: Normale Ausführung
- `test_execution_pipeline_blocks_on_risk_violation`: Risk-Limits blockieren
- `test_execution_pipeline_logs_events_when_logger_configured`: Run-Logging

Tests verwenden Fake-Implementierungen (FakeSafetyGuard, FakeRiskLimits, FakeRunLogger) für Isolation.

## Zusammenfassung

Phase 16A stellt eine **stabile, getestete ExecutionPipeline** bereit, die:

- ✅ Environment- und Safety-Checks durchführt
- ✅ Risk-Limits integriert (optional)
- ✅ Run-Logging unterstützt (optional)
- ✅ LIVE-Mode hart blockiert (Safety)
- ✅ In Shadow/Paper/Testnet-Kontexten verwendet werden kann
- ✅ Später ohne Breaking Changes für Live erweitert werden kann

Die Pipeline ist das zentrale Rückgrat zwischen Strategie/Portfolio und Executor und stellt sicher, dass alle Orders durch die Safety- und Risk-Layer laufen, bevor sie ausgeführt werden.

