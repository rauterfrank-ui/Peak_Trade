# Phase 78: Real-Market Strategy-Smokes mit Kraken-Cache

**Status:** Fertig
**Datum:** 2025-12-07

## Zusammenfassung

Phase 78 erweitert die Strategy-Smoke-Infrastruktur (Phase 76/77) um die Möglichkeit, **echte historische Marktdaten aus dem lokalen Kraken-Cache** als Datenquelle zu nutzen – weiterhin **komplett offline und ohne Live-API-Aufrufe**.

## Features

### 1. Konfigurierbare Datenquelle

Die Funktion `run_strategy_smoke_tests(...)` unterstützt jetzt einen `data_source`-Parameter:

- `"synthetic"` (Default): Generiert synthetische OHLCV-Daten (bisheriges Verhalten)
- `"kraken_cache"`: Lädt echte Marktdaten aus dem lokalen Parquet-Cache

### 2. Erweiterte Metadata in `StrategySmokeResult`

Neue Felder für vollständige Daten-Transparenz:

```python
@dataclass
class StrategySmokeResult:
    name: str
    status: Literal["ok", "fail"]
    data_source: str = "synthetic"  # NEU
    symbol: Optional[str] = None     # NEU
    timeframe: Optional[str] = None  # NEU
    num_bars: Optional[int] = None   # NEU
    start_ts: Optional[pd.Timestamp] = None  # NEU
    end_ts: Optional[pd.Timestamp] = None    # NEU
    return_pct: Optional[float] = None
    sharpe: Optional[float] = None
    max_drawdown_pct: Optional[float] = None
    num_trades: Optional[int] = None
    error: Optional[str] = None
    duration_ms: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
```

### 3. CLI-Erweiterung

Neues `--data-source` Argument:

```bash
# Default: synthetische Daten
python scripts/strategy_smoke_check.py

# Explizit synthetisch
python scripts/strategy_smoke_check.py --data-source synthetic

# Real-Market-Smoke mit Kraken-Cache
python scripts/strategy_smoke_check.py \
  --data-source kraken_cache \
  --market BTC/EUR \
  --timeframe 1h \
  --lookback-days 30
```

### 4. Strukturierte Reports

JSON- und Markdown-Reports enthalten jetzt:
- Datenquelle (`data_source`)
- Market und Timeframe
- Anzahl der Bars
- Zeitraum (`start_ts` bis `end_ts`)

## API-Änderungen

### `run_strategy_smoke_tests(...)`

```python
def run_strategy_smoke_tests(
    strategy_names: Optional[List[str]] = None,
    config_path: str = "config/config.toml",
    market: str = "BTC/EUR",      # Geändert von "BTCUSDT"
    timeframe: str = "1h",        # Jetzt mit Default-Wert
    lookback_days: int = 30,
    n_bars: Optional[int] = None,
    data_source: str = "synthetic",  # NEU
) -> List[StrategySmokeResult]:
```

### Neue Funktionen

```python
def load_kraken_cache_ohlcv(
    symbol: str = "BTC/EUR",
    timeframe: str = "1h",
    lookback_days: int = 30,
    n_bars: Optional[int] = None,
    config_path: str = "config/config.toml",
) -> pd.DataFrame:
    """Lädt OHLCV-Daten aus dem lokalen Kraken-Cache."""

def _load_ohlcv_for_smoke(
    data_source: str,
    market: str,
    timeframe: str,
    lookback_days: int,
    n_bars: Optional[int],
    config_path: str,
) -> pd.DataFrame:
    """Dispatch-Funktion für Datenquellen."""
```

## Verfügbare Cache-Dateien

Aktuell im `data/cache/` Verzeichnis:

| Datei | Symbol | Timeframe |
|-------|--------|-----------|
| BTC_EUR_1h.parquet | BTC/EUR | 1h |
| BTC_USD_1d.parquet | BTC/USD | 1d |
| BTC_USD_1h_limit200.parquet | BTC/USD | 1h |
| BTC_USD_1h_limit500.parquet | BTC/USD | 1h |

## Beispiel-CLI-Aufrufe

```bash
# Synthetisch (Default, CI-kompatibel)
python scripts/strategy_smoke_check.py \
  --strategies ma_crossover,rsi_reversion \
  --n-bars 200

# Kraken-Cache mit BTC/EUR 1h
python scripts/strategy_smoke_check.py \
  --data-source kraken_cache \
  --market BTC/EUR \
  --timeframe 1h \
  --strategies ma_crossover,rsi_reversion,breakout \
  --n-bars 500 \
  --output-json test_results/strategy_smoke/smoke_kraken.json \
  --output-md test_results/strategy_smoke/smoke_kraken.md
```

## Tests

33 Tests in `tests/test_strategy_smoke_cli.py`:
- 23 bestehende Tests (Phase 76)
- 10 neue Tests für Phase 78 (Kraken-Cache)

```bash
pytest tests/test_strategy_smoke_cli.py -v
# 33 passed in 2.63s
```

## CI-Kompatibilität

- Default-Verhalten (`data_source="synthetic"`) bleibt identisch zu Phase 76/77
- Keine Änderungen an `.github/workflows/ci.yml` erforderlich
- CI nutzt weiterhin den synthetischen Pfad

## Safety

- **Keine Netzwerk-Aufrufe**: Kraken-Cache-Modus liest nur lokale Parquet-Dateien
- **Keine Live-/Testnet-Order-Flows**: Rein Research/Backtest
- **Keine Secrets benötigt**: Offline-Only
- **Keine Änderungen an Live-Komponenten**: `src/live/*` und `src/execution/*` unverändert

## Geänderte/Neue Dateien

### Geändert
- `src/strategies/diagnostics.py` - Erweiterte API mit DataSource-Unterstützung
- `scripts/strategy_smoke_check.py` - CLI mit `--data-source` Flag
- `tests/test_strategy_smoke_cli.py` - 10 neue Tests für Kraken-Cache

### Neu
- `docs/PHASE_78_REAL_MARKET_STRATEGY_SMOKES.md` - Diese Dokumentation
- `tests/data/kraken_smoke/BTC_EUR_1h.parquet` - Test-Fixture

## Nächste Schritte

- Weitere Timeframes/Symbole zum Cache hinzufügen
- Integration in Research-Playground für interaktive Analyse
- Sweep-Optimierung mit echten Marktdaten
