# Peak_Trade – Setup & Code-Notizen für neuen Chat

> **CURRENT TRUTH (2026-09):** This file is a historical setup snapshot, not current SSOT.
> Kraken adapters (`src&#47;data&#47;kraken.py`, `kraken_live.py`, `kraken_testnet.py`) are **absent** and not selectable. <!-- pt:ref-target-ignore -->
> `KRAKEN_API_KEY` / `KRAKEN_API_SECRET` are **not** current operative credentials or live-readiness signals.
> Current operative venue target is OKX EEA. This note does **not** retarget Kraken names to OKX live credentials.

Diese Datei fasst einen **historischen** Projektstand von Peak_Trade zusammen. Nicht als aktuelle operative Anleitung verwenden.

---

## 1. Ziel des Projekts

- Python-Projekt **Peak_Trade** für Backtests und später Live-Trading.
- Zentrale **Konfiguration über `config.toml`** + `src/core/config.py`.
- Sichere Behandlung von API-Credentials (nur über **Environment-Variablen**, keine Keys in Dateien).
- Historical note: a Kraken OHLCV module used to live under `src/data/`. That module is **absent** and not current. <!-- pt:ref-target-ignore -->

---

## 2. Projektstruktur

Im Verzeichnis `~/Peak_Trade`:

```text
~/Peak_Trade
├── .venv/                  # Virtuelle Umgebung (Python 3.9)
├── config.toml             # Hauptkonfiguration
├── requirements.txt        # Python-Abhängigkeiten
└── src/
    ├── core/
    │   ├── __init__.py
    │   └── config.py
    ├── data/
    │   ├── __init__.py
    │   └── (Kraken adapter removed; not current)
    ├── backtest/
    │   └── __init__.py
    ├── risk/
    │   └── __init__.py
    └── live/
        └── __init__.py
```

---

## 3. Virtuelle Umgebung & Pakete

### venv anlegen

```bash
cd ~/Peak_Trade
python3 -m venv .venv
source .venv/bin/activate
```

### Wichtige Pakete installieren

```bash
pip install tomli ccxt pandas numpy backtrader cvxpy matplotlib python-dotenv
```

(Die meisten davon hattest du schon über `requirements.txt` installiert.)

---

## 4. Konfigurationsdatei `config.toml`

Beispielinhalt (im Projekt-Root `~/Peak_Trade/config.toml`):

```toml
# Peak_Trade Hauptkonfiguration

[risk]
max_position_size_pct = 5.0
max_total_exposure_pct = 30.0
max_drawdown_pct = 15.0
daily_loss_limit_pct = 3.0
default_stop_loss_pct = 2.0
default_take_profit_pct = 4.0

[backtest]
initial_cash = 10000.0
commission_pct = 0.1
slippage_pct = 0.05
data_dir = "data"
results_dir = "results"

[exchange]
name = "dummy"
# Historical Kraken env names are not current operative credentials.
api_key_env = ""
api_secret_env = ""
rate_limit_ms = 1000
testnet = true

[[strategies]]
name = "momentum_1h"
timeframe = "1h"
symbols = ["BTC/EUR", "ETH/EUR"]
parameters = { rsi_period = 14, rsi_oversold = 30, rsi_overbought = 70 }
```

---

## 5. `src/core/config.py` – wichtigste Ideen (historical snapshot)

The embedded source below is a **historical snapshot**. Default exchange name `kraken` and `KRAKEN_API_*` env names in that dump are **not** current operative defaults.

Die Datei enthält:

- `ConfigError` – eigener Exception-Typ  
- Dataclasses: `RiskConfig`, `BacktestConfig`, `ExchangeConfig`, `StrategyConfig`
- Klasse `PeakTradeConfig` mit:
  - Laden von `config.toml` (mit `tomli` bei Python 3.9)
  - Parsen der Sektionen `[risk]`, `[backtest]`, `[exchange]`, `[[strategies]]`
  - Validierung der Werte (Prozente etc.)
  - Funktion `get_exchange_credentials()` → holt API-Key/Secret aus Environment
- Convenience-Funktion `load_config(path: Optional[Path] = None)`
- `if __name__ == "__main__":` block, der die Konfiguration lädt und schön ausgibt.

### Voller Code (Stand am Ende der Session)

```python
"""
Peak_Trade Konfigurationsmodul
Lädt und validiert config.toml für alle Subsysteme
"""

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, Optional

# Python 3.11+ hat tomllib eingebaut, davor tomli aus PyPI
if sys.version_info >= (3, 11):
    import tomllib as toml_mod
else:
    import tomli as toml_mod


class ConfigError(Exception):
    """Peak_Trade Konfigurationsfehler"""
    pass


def _validate_percentage(value: float, name: str, allow_zero: bool = False) -> None:
    """Validiert Prozent-Werte."""
    condition = (0 <= value <= 100) if allow_zero else (0 < value <= 100)
    if not condition:
        range_str = "0 bis 100" if allow_zero else "größer als 0 und maximal 100"
        raise ConfigError(f"{name} ungültig: {value}. Muss {range_str} sein")


@dataclass(frozen=True)
class RiskConfig:
    max_position_size_pct: float
    max_total_exposure_pct: float
    max_drawdown_pct: float
    daily_loss_limit_pct: float
    default_stop_loss_pct: float
    default_take_profit_pct: float

    def __post_init__(self):
        _validate_percentage(self.max_position_size_pct, "max_position_size_pct")
        _validate_percentage(self.max_total_exposure_pct, "max_total_exposure_pct")
        _validate_percentage(self.max_drawdown_pct, "max_drawdown_pct")
        _validate_percentage(self.daily_loss_limit_pct, "daily_loss_limit_pct")
        _validate_percentage(self.default_stop_loss_pct, "default_stop_loss_pct")
        _validate_percentage(self.default_take_profit_pct, "default_take_profit_pct")


@dataclass(frozen=True)
class BacktestConfig:
    initial_cash: float
    commission_pct: float
    slippage_pct: float
    data_dir: Path
    results_dir: Path

    def __post_init__(self):
        if self.initial_cash <= 0:
            raise ConfigError("initial_cash muss positiv sein")
        _validate_percentage(self.commission_pct, "commission_pct", allow_zero=True)
        _validate_percentage(self.slippage_pct, "slippage_pct", allow_zero=True)


@dataclass(frozen=True)
class ExchangeConfig:
    name: str
    api_key_env: str
    api_secret_env: str
    rate_limit_ms: int
    testnet: bool = True

    def __post_init__(self):
        if not self.name.strip():
            raise ConfigError("exchange name must be non-empty")
        # Historical multi-venue lists are not current options.
        # Operative venue binding remains the existing OKX EEA contracts.
        if self.rate_limit_ms < 50:
            raise ConfigError("rate_limit_ms zu niedrig (mind. 50ms)")


@dataclass(frozen=True)
class StrategyConfig:
    name: str
    timeframe: str
    symbols: list[str]
    parameters: Dict[str, Any]


class PeakTradeConfig:
    """Hauptkonfigurationsklasse für Peak_Trade"""

    def __init__(self, config_path: Optional[Path] = None):
        if config_path is None:
            config_path = Path.home() / "Peak_Trade" / "config.toml"
        self.config_path = config_path
        self._raw_config = self._load_toml()

        self.risk = self._parse_risk()
        self.backtest = self._parse_backtest()
        self.exchange = self._parse_exchange()
        self.strategies = self._parse_strategies()

    def _load_toml(self) -> Dict[str, Any]:
        if not self.config_path.exists():
            raise ConfigError(
                f"Config nicht gefunden: {self.config_path}\n"
                f"Erstelle eine config.toml im Verzeichnis {self.config_path.parent}!"
            )
        try:
            with open(self.config_path, "rb") as f:
                return toml_mod.load(f)
        except Exception as e:
            raise ConfigError(f"Fehler beim Laden von {self.config_path}: {e}") from e

    def _parse_risk(self) -> RiskConfig:
        data = self._raw_config.get("risk", {})
        return RiskConfig(
            max_position_size_pct=data.get("max_position_size_pct", 10.0),
            max_total_exposure_pct=data.get("max_total_exposure_pct", 50.0),
            max_drawdown_pct=data.get("max_drawdown_pct", 20.0),
            daily_loss_limit_pct=data.get("daily_loss_limit_pct", 5.0),
            default_stop_loss_pct=data.get("default_stop_loss_pct", 2.0),
            default_take_profit_pct=data.get("default_take_profit_pct", 4.0),
        )

    def _parse_backtest(self) -> BacktestConfig:
        data = self._raw_config.get("backtest", {})
        root = self.config_path.parent
        return BacktestConfig(
            initial_cash=data.get("initial_cash", 10000.0),
            commission_pct=data.get("commission_pct", 0.1),
            slippage_pct=data.get("slippage_pct", 0.05),
            data_dir=root / data.get("data_dir", "data"),
            results_dir=root / data.get("results_dir", "results"),
        )

    def _parse_exchange(self) -> ExchangeConfig:
        data = self._raw_config.get("exchange", {})
        return ExchangeConfig(
            name=data.get("name", "kraken"),
            api_key_env=data.get("api_key_env", "KRAKEN_API_KEY"),
            api_secret_env=data.get("api_secret_env", "KRAKEN_API_SECRET"),
            rate_limit_ms=data.get("rate_limit_ms", 1000),
            testnet=data.get("testnet", True),
        )

    def _parse_strategies(self) -> Dict[str, StrategyConfig]:
        strategies: Dict[str, StrategyConfig] = {}
        for i, s in enumerate(self._raw_config.get("strategies", [])):
            if "name" not in s:
                raise ConfigError(f"Strategie #{i+1} hat kein 'name'-Feld")
            name = s["name"]
            strategies[name] = StrategyConfig(
                name=name,
                timeframe=s.get("timeframe", "1h"),
                symbols=s.get("symbols", []),
                parameters=s.get("parameters", {}),
            )
        return strategies

    def get_strategy(self, name: str) -> StrategyConfig:
        if name not in self.strategies:
            raise ConfigError(
                f"Strategie '{name}' nicht gefunden. Verfügbar: {list(self.strategies.keys())}"
            )
        return self.strategies[name]

    def get_exchange_credentials(self) -> tuple[str, str]:
        key = os.getenv(self.exchange.api_key_env)
        secret = os.getenv(self.exchange.api_secret_env)
        if not key or not secret:
            raise ConfigError(
                f"API-Credentials nicht gesetzt. Bitte {self.exchange.api_key_env} und "
                f"{self.exchange.api_secret_env} im Environment setzen."
            )
        return key, secret

    def validate(self) -> bool:
        if self.risk.max_position_size_pct >= self.risk.max_total_exposure_pct:
            raise ConfigError(
                "max_position_size_pct sollte kleiner als max_total_exposure_pct sein"
            )

        self.backtest.data_dir.mkdir(parents=True, exist_ok=True)
        self.backtest.results_dir.mkdir(parents=True, exist_ok=True)

        if not self.exchange.testnet:
            print("⚠️  WARNUNG: Testnet ist deaktiviert – Live-Trading möglich!")

        return True


def load_config(path: Optional[Path] = None) -> PeakTradeConfig:
    cfg = PeakTradeConfig(path)
    cfg.validate()
    return cfg


if __name__ == "__main__":
    try:
        cfg = load_config()
        print("Konfiguration erfolgreich geladen.")
        print(f"Python {sys.version_info.major}.{sys.version_info.minor}, TOML-Parser: {toml_mod.__name__}")

        print("\nRisk Settings:")
        print(f"  Max Position: {cfg.risk.max_position_size_pct}%")
        print(f"  Max Drawdown: {cfg.risk.max_drawdown_pct}%");

        print("\nBacktest:")
        print(f"  Initial Cash: {cfg.backtest.initial_cash:,.0f}")
        print(f"  Commission: {cfg.backtest.commission_pct}%");

        print("\nExchange:")
        print(f"  Name: {cfg.exchange.name}")
        print(f"  Testnet: {cfg.exchange.testnet}")

        print("\nStrategien:", list(cfg.strategies.keys()))

        try:
            key, _ = cfg.get_exchange_credentials()
            print(f"\nCredentials gefunden (Key beginnt mit: {key[:8]}...)")
        except ConfigError:
            print("\nKeine Credentials gesetzt (ok für Backtest).");

    except ConfigError as e:
        print(f"Konfigurationsfehler: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unerwarteter Fehler: {e}")
        sys.exit(1)
```

---

## 6. `src/core/__init__.py`

```python
"""
Core-Package für Peak_Trade
Stellt zentrale Funktionen und Typen zur Verfügung.
"""

from .config import (
    PeakTradeConfig,
    RiskConfig,
    BacktestConfig,
    ExchangeConfig,
    StrategyConfig,
    ConfigError,
    load_config,
)

__all__ = [
    "PeakTradeConfig",
    "RiskConfig",
    "BacktestConfig",
    "ExchangeConfig",
    "StrategyConfig",
    "ConfigError",
    "load_config",
]

__version__ = "0.1.0"
```

---

## 7. Historical sample only — `src&#47;data&#47;kraken.py` is ABSENT <!-- pt:ref-target-ignore -->

The following code dump is a **historical sample**. It is **not** a current adapter, setup path, or operative venue client. Do not copy it as current guidance. Do not retarget it to OKX credentials.

```python
# HISTORICAL SAMPLE ONLY — MODULE ABSENT
import time
from typing import Optional

import ccxt
import pandas as pd

from src.core import load_config, ConfigError


def get_kraken_client() -> ccxt.kraken:
    """Erstellt einen konfigurierten Kraken-Client (inkl. Testnet-Option)."""
    cfg = load_config()

    options = {
        "enableRateLimit": True,
        "rateLimit": cfg.exchange.rate_limit_ms,
        "options": {"defaultType": "spot"},
    }

    try:
        api_key, api_secret = cfg.get_exchange_credentials()
        options["apiKey"] = api_key
        options["secret"] = api_secret
    except ConfigError:
        pass

    exchange = ccxt.kraken(options)

    if cfg.exchange.testnet and hasattr(exchange, "set_sandbox_mode"):
        exchange.set_sandbox_mode(True)

    return exchange


def fetch_ohlcv_df(
    symbol: str,
    timeframe: str = "1h",
    limit: int = 720,
    since_ms: Optional[int] = None,
) -> pd.DataFrame:
    """Holt OHLCV-Daten von Kraken und gibt sie als DataFrame zurück."""
    exchange = get_kraken_client()

    try:
        ohlcv = exchange.fetch_ohlcv(
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
            since=since_ms,
        )
    except ccxt.BaseError as e:
        raise RuntimeError(f"Fehler beim Abrufen von OHLCV für {symbol}: {e}") from e

    if not ohlcv:
        raise RuntimeError(f"Keine OHLCV-Daten für {symbol} erhalten")

    df = pd.DataFrame(
        ohlcv,
        columns=["timestamp", "open", "high", "low", "close", "volume"],
    )

    df["datetime"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
    df.set_index("datetime", inplace=True)
    df.drop(columns=["timestamp"], inplace=True)
    df.sort_index(inplace=True)

    return df


if __name__ == "__main__":
    import sys

    symbol = "BTC/EUR"
    timeframe = "1h"

    if len(sys.argv) > 1:
        symbol = sys.argv[1]
    if len(sys.argv) > 2:
        timeframe = sys.argv[2]

    print(f"📥 Hole OHLCV von Kraken: {symbol} @ {timeframe}")
    df = fetch_ohlcv_df(symbol, timeframe, limit=168)
    print(f"✅ {len(df)} Kerzen – von {df.index[0]} bis {df.index[-1]}")
    print(df.tail().round(2))
```

Aufruf aus dem Terminal:

```bash
cd ~/Peak_Trade
source .venv/bin/activate

# Konfiguration testen
python -m src.core.config

# Historical command only — module absent:
# python -m src.data.kraken BTC/EUR 1h
```

---

## 8. API-Keys per Environment-Variable

Do **not** export `KRAKEN_API_KEY` / `KRAKEN_API_SECRET` as current operative setup.
Those names are not live-readiness signals and must not be copied as current guidance.
This note does not prescribe OKX live credentials.

```bash
# HISTORICAL NAMES ONLY — not a current setup path
# export KRAKEN_API_KEY="dein_key"
# export KRAKEN_API_SECRET="dein_secret"
```

---

## 9. Verwendung in einem neuen Chat

In einem neuen Chat kannst du z.B. schreiben:

> Hier ist mein aktuelles Projekt *Peak_Trade* (Struktur + Code). Hilf mir, auf Basis davon den Backtest-Layer zu entwerfen.

Dann diese `.md` Datei (oder die relevanten Abschnitte) einfügen.
