# Peak_Trade – Developer Setup

Anleitung zum Einrichten der Entwicklungsumgebung.

---

## Voraussetzungen

- **Python 3.11+**
- **Git**
- Optional: VS Code, PyCharm oder andere IDE

---

## 1. Repository klonen

```bash
git clone <repo-url>
cd Peak_Trade
```

---

## 2. Virtual Environment erstellen

```bash
# Python venv erstellen
python3 -m venv .venv

# Aktivieren
source .venv/bin/activate      # Linux/macOS
.venv\Scripts\activate         # Windows
```

---

## 3. Dependencies installieren

```bash
pip install -r requirements.txt
```

**Core Dependencies (minimal, ohne Exchange-Provider):**
- `numpy`, `pandas` – Datenverarbeitung
- `pydantic`, `toml` – Config-Management
- `pyarrow` – Parquet-Caching
- `pytest`, `pytest-cov` – Testing

**Optionale Dependencies:**
- `ccxt` – Kraken Read-Only Datenprovider (optional; Core bleibt ohne `ccxt` importierbar)

---

## 4. Config erstellen

Peak_Trade lädt standardmäßig `config/config.toml`.

Wenn du eine alternative Config verwenden willst, setze:
- `PEAK_TRADE_CONFIG_PATH` (Environment Variable) oder übergib einen expliziten Pfad an CLI/Runner.

```bash
# Beispiel: alternative Config via ENV (Session-lokal)
export PEAK_TRADE_CONFIG_PATH="config/config.toml"
```

Hinweis: Die Default-Config in diesem Repo liegt unter `config/config.toml` (nicht `./config.toml`). <!-- pt:ref-target-ignore -->

```toml
[general]
active_strategy = "ma_crossover"

[backtest]
initial_cash = 10000.0

[strategy.ma_crossover]
fast_window = 20
slow_window = 50
price_col = "close"

[live]
base_currency = "EUR"
starting_cash_default = 10000.0
```

---

## 5. Installation verifizieren

```bash
# Imports testen
python3 -c "from src.core.peak_config import load_config; print('OK')"

# Backtest mit Dummy-Daten
python3 scripts/run_backtest.py --bars 100 -v

# Tests ausführen
python3 -m pytest tests/ -v
```

---

## Optional dependency gates

Diese Gates stellen sicher, dass optionale Dependencies (z.B. `ccxt`) den Import-Graph nicht „leaken“.

```bash
# 1) Leak-Scan (ccxt darf nur in src/data/providers/** importiert werden)
bash scripts/ops/check_optional_deps_leaks.sh

# 2) Packaging Importability Gate (E2E, 2 venvs: core vs .[kraken])
bash scripts/ops/check_optional_deps_importability.sh
```

---

## Typechecking (dev-only)

```bash
pip install -e ".[dev]"

# mypy (tolerant start)
mypy --config-file mypy.ini src tests
```

---

## Projektstruktur

```
Peak_Trade/
├── config/
│   └── config.toml          # Default-Konfiguration (Repo)
├── requirements.txt         # Python Dependencies
├── src/
│   ├── core/                # Config, Position Sizing, Risk
│   ├── data/                # Data Loading, Caching
│   ├── backtest/            # Engine, Stats
│   ├── strategies/          # BaseStrategy, Registry
│   ├── live/                # Orders, Broker, Risk-Limits
│   └── forward/             # Forward-Signale
├── scripts/                 # CLI-Runner
├── tests/                   # Unit Tests
├── docs/                    # Dokumentation
└── reports/                 # Generierte Reports (nicht im Git)
```

---

## Häufige Workflows

### Backtest ausführen

```bash
# Standard (Dummy-Daten)
python3 scripts/run_backtest.py

# Mit CSV-Daten
python3 scripts/run_backtest.py --data-file data/btc_eur_1h.csv

# Mit anderer Strategie
python3 scripts/run_backtest.py --strategy rsi_reversion

# Verbose-Modus
python3 scripts/run_backtest.py -v
```

### Forward-Signale & Paper-Trading

```bash
# 1. Signale generieren
python3 scripts/generate_forward_signals.py --strategy ma_crossover

# 2. Order-Preview
python3 scripts/preview_live_orders.py --signals reports/forward/*_signals.csv

# 3. Paper-Trade
python3 scripts/paper_trade_from_orders.py --orders reports/live/*_orders.csv
```

### Tests ausführen

```bash
# Alle Tests
python3 -m pytest tests/

# Mit Coverage
python3 -m pytest tests/ --cov=src --cov-report=html

# Einzelne Test-Datei
python3 -m pytest tests/test_strategies.py -v
```

---

## IDE-Konfiguration

### VS Code

Empfohlene Extensions:
- Python (Microsoft)
- Pylance
- Python Test Explorer

`.vscode&#47;settings.json`:
```json
{
  "python.defaultInterpreterPath": ".venv/bin/python",
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["tests/"]
}
```

### PyCharm

1. File → Settings → Project → Python Interpreter
2. `.venv` als Interpreter auswählen
3. Run/Debug Configuration für pytest erstellen

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'src'"

```bash
# Projekt-Root zum PYTHONPATH hinzufügen
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Oder direkt aus Projekt-Root ausführen
cd Peak_Trade
python3 scripts/run_backtest.py
```

### "Config not found"

```bash
# Sicherstellen, dass die Config existiert
ls config/config.toml

# Alternativ explizit angeben
python3 scripts/run_backtest.py --config config/config.toml
```

### "ccxt not found"

```bash
# Optionalen Kraken-Provider installieren
pip install ccxt

# oder als Extra (wenn installiert im Editable-Mode):
pip install -e ".[kraken]"
```

---

## Exchange-Setup (Read-Only)

Das Exchange-Layer ermöglicht **lesenden Zugriff** auf Exchange-Daten über ccxt.
Keine Order-Platzierung in diesem Layer!

### Konfiguration

In `config/config.toml`:

```toml
[exchange]
id = "kraken"              # Exchange-ID (kraken, binance, etc.)
sandbox = true             # Sandbox/Testnet (falls unterstützt)
enable_rate_limit = true   # Rate-Limiting (empfohlen)

[exchange.credentials]
api_key = ""               # Für Balance/Orders (optional)
secret = ""                # Für Balance/Orders (optional)

[exchange.options]
# timeout = 30000          # Request-Timeout in ms
# verbose = false          # Debug-Logging
```

### Verfügbare Modi

```bash
# Exchange-Status anzeigen
python3 scripts/inspect_exchange.py --mode status

# Ticker abrufen
python3 scripts/inspect_exchange.py --mode ticker --symbol BTC/EUR

# OHLCV-Daten (Candlesticks)
python3 scripts/inspect_exchange.py --mode ohlcv --symbol BTC/EUR --timeframe 1h --limit 20

# Verfügbare Märkte auflisten
python3 scripts/inspect_exchange.py --mode markets --limit 50

# Balance anzeigen (erfordert API-Key)
python3 scripts/inspect_exchange.py --mode balance

# Offene Orders anzeigen (erfordert API-Key)
python3 scripts/inspect_exchange.py --mode orders
```

### Programmatische Nutzung

```python
from src.core.peak_config import load_config
from src.exchange import build_exchange_client_from_config

cfg = load_config()
client = build_exchange_client_from_config(cfg)

# Ticker
ticker = client.fetch_ticker("BTC/EUR")
print(f"BTC/EUR: {ticker.last}")

# OHLCV-Daten als DataFrame
df = client.fetch_ohlcv("BTC/EUR", timeframe="1h", limit=100)
print(df.tail())
```

### Integration-Tests

Exchange-Integration-Tests sind standardmäßig deaktiviert (keine Netzwerk-Requests).
Zum Aktivieren:

```bash
PEAK_TRADE_EXCHANGE_TESTS=1 python3 -m pytest tests/test_exchange_smoke.py -v
```

---

## Weiterführende Dokumentation

- [README.md](../README.md) – Quickstart
- [ARCHITECTURE.md](ARCHITECTURE.md) – System-Architektur
- [STRATEGY_DEV_GUIDE.md](STRATEGY_DEV_GUIDE.md) – Neue Strategien entwickeln
- [LIVE_WORKFLOWS.md](LIVE_WORKFLOWS.md) – Forward/Paper/Live Workflows
