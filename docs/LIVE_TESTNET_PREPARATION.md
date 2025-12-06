# Phase 17 – Live/Testnet-Preparation & Safety-Layer

**Status:** Abgeschlossen (Phase 17)
**Stand:** Dezember 2024

---

## Ziel dieser Phase

Phase 17 bereitet die Architektur für zukünftiges Testnet- und Live-Trading vor,
**ohne** echte Orders zu implementieren. Der Fokus liegt auf:

1. **Environment-Abstraktion** (paper / testnet / live)
2. **Safety-Layer** zum Blocken gefährlicher Operationen
3. **Dry-Run-Executors** für Testnet-Simulation
4. **Klare Stubs** für Live-Trading (nicht implementiert)

> **WICHTIG:** In Phase 17 werden **KEINE** echten Orders an Börsen gesendet!
> Alle Testnet/Live-Funktionen sind reine Architektur-Vorbereitung.

---

## Übersicht der Environments

| Environment | Beschreibung | Echte Orders? | Phase 17 Verhalten |
|-------------|--------------|---------------|-------------------|
| `paper`     | Simulation / Backtest | Nein | PaperOrderExecutor |
| `testnet`   | Börsen-Testnet | Nein* | Dry-Run-Logging |
| `live`      | Echtes Trading | Nein | Blockiert (NotImplemented) |

*In zukünftigen Phasen könnte Testnet echte Testnet-Orders senden.

---

## Konfiguration

### Environment-Block in `config.toml`

```toml
[environment]
# Trading-Umgebung: "paper", "testnet", oder "live"
mode = "paper"

# Zusätzlicher Safety-Schalter für Live-Trading
enable_live_trading = false

# Erfordert Bestätigungs-Token für Live-Trading
require_confirm_token = true

# Bestätigungs-Token (muss "I_KNOW_WHAT_I_AM_DOING" sein)
confirm_token = ""

# Testnet im Dry-Run-Modus (empfohlen in Phase 17)
testnet_dry_run = true

# Alle Orders loggen
log_all_orders = true
```

### Empfohlene Einstellungen

| Szenario | mode | enable_live_trading | testnet_dry_run |
|----------|------|---------------------|-----------------|
| Backtesting | `paper` | `false` | - |
| Paper-Trading | `paper` | `false` | - |
| Testnet-Entwicklung | `testnet` | `false` | `true` |
| (Zukünftig) Live | `live` | `true` | - |

---

## Safety-Layer (SafetyGuard)

### Zweck

Der `SafetyGuard` stellt sicher, dass:

- Im Paper-Modus keine "echten" Order-Calls versucht werden
- Im Testnet-Modus Orders nur als Dry-Run ausgeführt werden
- Im Live-Modus strenge Bestätigungen erforderlich sind

### Exceptions

| Exception | Beschreibung |
|-----------|--------------|
| `SafetyBlockedError` | Basisklasse für alle Blockierungen |
| `PaperModeOrderError` | Paper-Modus erlaubt keine echten Orders |
| `TestnetDryRunOnlyError` | Testnet ist nur im Dry-Run verfügbar |
| `LiveNotImplementedError` | Live-Trading ist nicht implementiert |
| `LiveTradingDisabledError` | enable_live_trading = False |
| `ConfirmTokenInvalidError` | Bestätigungs-Token fehlt/falsch |

### Verwendung

```python
from src.core.environment import EnvironmentConfig, TradingEnvironment
from src.live.safety import SafetyGuard

# Environment konfigurieren
env_config = EnvironmentConfig(
    environment=TradingEnvironment.PAPER,
    enable_live_trading=False,
)

# SafetyGuard erstellen
guard = SafetyGuard(env_config=env_config)

# Vor Order-Platzierung prüfen (wirft Exception im Paper-Modus)
try:
    guard.ensure_may_place_order()
except PaperModeOrderError:
    print("Paper-Modus: Keine echten Orders erlaubt")
```

### Safety-Checks

| Methode | Beschreibung |
|---------|--------------|
| `ensure_may_place_order()` | Prüft ob Order-Platzierung erlaubt |
| `ensure_not_live()` | Stellt sicher, dass nicht im Live-Modus |
| `ensure_confirm_token()` | Prüft Bestätigungs-Token |
| `may_use_dry_run()` | Prüft ob Dry-Run erlaubt (immer True) |
| `get_effective_mode()` | Gibt effektiven Modus zurück |

### Audit-Log

Der SafetyGuard führt ein Audit-Log aller Safety-Checks:

```python
# Audit-Log abrufen
entries = guard.get_audit_log()
for entry in entries:
    print(f"{entry.timestamp}: {entry.action} -> {entry.allowed}")
```

---

## Order-Executors

### Übersicht

| Executor | Zweck | Phase 17 Status |
|----------|-------|-----------------|
| `PaperOrderExecutor` | Simulation | ✅ Vollständig |
| `TestnetOrderExecutor` | Testnet Dry-Run | ✅ Dry-Run |
| `LiveOrderExecutor` | Echtes Trading | ❌ Stub |
| `ExchangeOrderExecutor` | Unified Wrapper | ✅ Safety-Guard |

### PaperOrderExecutor

Unverändert aus Phase 15/16. Simuliert Orders ohne echte API-Calls.

```python
from src.orders import PaperOrderExecutor, PaperMarketContext

ctx = PaperMarketContext(prices={"BTC/EUR": 50000.0})
executor = PaperOrderExecutor(market_context=ctx)
result = executor.execute_order(order)  # Simulation
```

### TestnetOrderExecutor (Dry-Run)

Simuliert Testnet-Orders ohne echte API-Calls. Loggt alle Orders.

```python
from src.orders import TestnetOrderExecutor
from src.live.safety import SafetyGuard

guard = SafetyGuard(env_config=env_config)
executor = TestnetOrderExecutor(
    safety_guard=guard,
    simulated_prices={"BTC/EUR": 50000.0},
)

# Dry-Run - keine echten Orders
result = executor.execute_order(order)
print(result.metadata["mode"])  # "testnet_dry_run"
```

### LiveOrderExecutor (Stub)

**NICHT IMPLEMENTIERT** in Phase 17. Wirft immer Exception.

```python
from src.orders import LiveOrderExecutor

executor = LiveOrderExecutor(safety_guard=guard)
executor.execute_order(order)  # Raises LiveNotImplementedError
```

### ExchangeOrderExecutor (Unified)

Wrapper, der basierend auf Environment den richtigen Modus wählt:

```python
from src.orders import ExchangeOrderExecutor

executor = ExchangeOrderExecutor(
    safety_guard=guard,
    simulated_prices={"BTC/EUR": 50000.0},
)

# Paper -> Redirect-Hinweis
# Testnet -> Dry-Run
# Live -> Blockiert
result = executor.execute_order(order)
```

---

## Execution Modes

Die Executor-Metadata enthält einen `mode`-Wert:

| Mode | Beschreibung |
|------|--------------|
| `paper` | PaperOrderExecutor Simulation |
| `dry_run` | Allgemeiner Dry-Run |
| `testnet_dry_run` | Testnet Dry-Run (keine echten Orders) |
| `live_blocked` | Live blockiert |
| `simulated` | Simulierte Ausführung |

---

## Integration mit bestehendem Code

### BacktestEngine

Der BacktestEngine verwendet weiterhin den `PaperOrderExecutor`:

```python
from src.backtest import BacktestEngine

engine = BacktestEngine(
    strategy=strategy,
    use_execution_pipeline=True,
)
# Verwendet intern PaperOrderExecutor
```

### ExecutionPipeline

Die ExecutionPipeline unterstützt beliebige `OrderExecutor`:

```python
from src.execution import ExecutionPipeline, ExecutionPipelineConfig
from src.orders import TestnetOrderExecutor

executor = TestnetOrderExecutor(safety_guard=guard)
pipeline = ExecutionPipeline(
    config=config,
    order_executor=executor,  # Testnet Dry-Run
)
```

---

## Sicherheitshinweise

### Was ist sicher in Phase 17?

✅ Paper-Trading / Backtests
✅ Testnet Dry-Run (nur Logging)
✅ Order-Simulation mit PaperOrderExecutor
✅ Safety-Guard Integration testen

### Was ist NICHT verfügbar?

❌ Echte Testnet-Orders (ccxt create_order)
❌ Echte Live-Orders
❌ API-Calls zu Börsen für Order-Execution

### Wie werden echte Orders verhindert?

1. **SafetyGuard.ensure_may_place_order()** wirft Exceptions
2. **LiveOrderExecutor** ist ein Stub (NotImplementedError)
3. **testnet_dry_run=True** blockt echte Testnet-Orders
4. **enable_live_trading=False** blockt Live-Orders
5. **Confirm-Token** muss korrekt sein

---

## Dateien in Phase 17

### Neu erstellt

| Datei | Beschreibung |
|-------|--------------|
| `src/core/environment.py` | TradingEnvironment, EnvironmentConfig |
| `src/live/safety.py` | SafetyGuard, Safety-Exceptions |
| `src/orders/exchange.py` | Testnet/Live/Exchange Executors |
| `docs/LIVE_TESTNET_PREPARATION.md` | Diese Dokumentation |
| `tests/test_environment_and_safety.py` | Tests für Safety-Layer |

### Modifiziert

| Datei | Änderung |
|-------|----------|
| `config.toml` | Neuer [environment]-Block |
| `src/core/__init__.py` | Environment-Exports |
| `src/orders/__init__.py` | Executor-Exports |
| `src/live/__init__.py` | Safety-Exports |

---

## Nächste Schritte (Phase 18+)

### Phase 18: Testnet-Integration (optional)

- Echte Testnet-API-Calls (ccxt)
- Testnet-Credentials-Management
- Rate-Limiting & Error-Handling

### Phase 19+: Live-Trading (Zukunft)

- Live-Order-Execution mit strengen Limits
- Position-Tracking
- Real-Time-Risk-Monitoring
- Circuit-Breakers

---

## Zusammenfassung

Phase 17 etabliert eine robuste Safety-Architektur:

- **3 Environments**: paper, testnet, live
- **SafetyGuard**: Blockt alle gefährlichen Operationen
- **Dry-Run-Executors**: Testnet-Simulation ohne echte Orders
- **Audit-Logging**: Nachvollziehbare Safety-Checks
- **Konfigurations-Schalter**: Mehrfache Sicherheitsebenen

> **Das Wichtigste:** Keine echten Orders möglich in Phase 17!
