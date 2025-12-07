# Phase 79: Real-Market Data Coverage & QC für Strategy-Smokes (Kraken-Cache)

**Status:** Implementiert
**Datum:** 2025-12-07
**Basis:** Phase 78 (Real-Market Strategy-Smokes)

---

## Überblick

Phase 79 erweitert die Real-Market-Smoke-Tests um:
1. **Konfigurierbare Data-Coverage** (mehr Märkte/Timeframes, Basis-Pfad, Lookback)
2. **Data-QC Layer** (Existenz, Min-Bars, Zeitraum, Plausibilitätschecks)
3. **Explizite Health-Felder** in den Smoke-Resultaten
4. **CLI-Modus** für Data-QC ohne Strategie-Run

### Safety-Constraints (unverändert)

- **Offline-only**: Keine Netzwerk-Calls, nur lokale Parquet-Dateien
- Keine neuen Live-/Testnet-Abhängigkeiten
- CI-Verhalten unverändert (Default = `synthetic`)

---

## Neue Config: `[real_market_smokes]`

In `config/config.toml`:

```toml
[real_market_smokes]
# Basis-Pfad für Kraken-Cache-Files (Produktiv)
base_path = "data/cache"

# Override-Base für Tests (in pytest über Fixture gesetzt)
test_base_path = "tests/data/kraken_smoke"

# Default-Parameter für Real-Market-Smokes
default_market = "BTC/EUR"
default_timeframe = "1h"
default_lookback_days = 30

# Data-Quality-Control Thresholds
min_bars = 500

# Liste konfigurierter Real-Market-Szenarien
markets = ["BTC/EUR"]
timeframes = ["1h"]
```

---

## Neue Komponenten

### 1. Kraken-Cache-Loader mit Data-QC

**Modul:** `src/data/kraken_cache_loader.py`

```python
from src.data.kraken_cache_loader import (
    KrakenDataHealth,
    load_kraken_cache_window,
    check_data_health_only,
    get_real_market_smokes_config,
    list_available_cache_files,
)
```

#### `KrakenDataHealth` Dataclass

```python
@dataclass
class KrakenDataHealth:
    status: str        # "ok", "missing_file", "too_few_bars", "empty", "other"
    num_bars: int = 0
    start_ts: Optional[pd.Timestamp] = None
    end_ts: Optional[pd.Timestamp] = None
    notes: Optional[str] = None
    file_path: Optional[str] = None
    lookback_days_actual: Optional[float] = None
```

#### `load_kraken_cache_window()`

```python
df, health = load_kraken_cache_window(
    base_path=Path("data/cache"),
    market="BTC/EUR",
    timeframe="1h",
    lookback_days=30,
    min_bars=500,
)

if health.is_ok:
    # Daten verwenden
    ...
else:
    print(f"Data-Problem: {health.status} - {health.notes}")
```

### 2. Erweiterte `StrategySmokeResult`

Neue Felder (Phase 79):

```python
@dataclass
class StrategySmokeResult:
    # ... bestehende Felder ...

    # Phase 79: Data-QC Fields
    data_health: Optional[str] = None  # "ok", "missing_file", "too_few_bars", "empty", "other"
    data_notes: Optional[str] = None   # Freitext, z.B. "only 120 bars < min_bars=500"
```

### 3. CLI-Erweiterungen

#### Neue Flags

```bash
# Data-QC-Only Modus (ohne Strategie-Tests)
python scripts/strategy_smoke_check.py --check-data-only --data-source kraken_cache

# Eigener Min-Bars-Threshold
python scripts/strategy_smoke_check.py --min-bars 1000 --data-source kraken_cache
```

#### Beispiel: Data-QC-Only

```bash
$ python scripts/strategy_smoke_check.py \
    --check-data-only \
    --data-source kraken_cache \
    --market "BTC/EUR" \
    --timeframe "1h"

================================================================================
Peak_Trade – Strategy Smoke-Check (Phase 76)
================================================================================

HINWEIS: Rein Research/Backtest – KEIN Live-Trading!

--------------------------------------------------------------------------------
DATA-QC ONLY MODE (Phase 79)
--------------------------------------------------------------------------------

Config: config/config.toml
Base-Path: tests/data/kraken_smoke
Market: BTC/EUR
Timeframe: 1h
Min-Bars: 500

Verfuegbare Cache-Dateien:
  - BTC_EUR_1h.parquet: 20.3 KB, modified: 2025-12-07T21:20:00

Data-QC fuer BTC/EUR / 1h...

--------------------------------------------------------------------------------
DATA-QC ERGEBNIS
--------------------------------------------------------------------------------

  Status:      ok
  Num-Bars:    720
  Start-TS:    2025-10-01 00:00:00+00:00
  End-TS:      2025-10-31 23:00:00+00:00
  Lookback:    30.0 Tage
  File-Path:   tests/data/kraken_smoke/BTC_EUR_1h.parquet

Data-QC: OK
```

---

## Data-QC Flow

```
1. Config laden ([real_market_smokes])
   |
2. Cache-Pfad bauen (BTC/EUR -> BTC_EUR_1h.parquet)
   |
3. Existenzcheck
   |-- Nicht gefunden → status="missing_file"
   |
4. Parquet laden
   |-- Ladefehler → status="invalid_format"
   |
5. Leer-Check
   |-- len(df)==0 → status="empty"
   |
6. Spalten-Check (open, high, low, close, volume)
   |-- Fehlend → status="invalid_format"
   |
7. Min-Bars-Check
   |-- len(df) < min_bars → status="too_few_bars"
   |
8. Alles OK → status="ok"
```

---

## Tests

### Neue Test-Datei

`tests/test_kraken_cache_loader.py`:

- Happy-Path-Tests (gültige Daten)
- Missing-File-Tests
- Too-Few-Bars-Tests
- Empty-File-Tests
- Config-Tests
- Integration-Tests

### Erweiterte CLI-Tests

`tests/test_strategy_smoke_cli.py`:

- `TestPhase79DataHealthFields`
- `TestPhase79CLIDataQCOnly`
- `TestPhase79ReportsWithDataHealth`

### Test ausführen

```bash
# Nur neue Phase-79-Tests
pytest tests/test_kraken_cache_loader.py -v
pytest tests/test_strategy_smoke_cli.py::TestPhase79DataHealthFields -v
pytest tests/test_strategy_smoke_cli.py::TestPhase79CLIDataQCOnly -v
pytest tests/test_strategy_smoke_cli.py::TestPhase79ReportsWithDataHealth -v

# Alle Strategy-/Smoke-Tests
pytest tests/test_strategy*.py -v
```

---

## JSON/MD-Reports

### JSON-Report mit Data-Health

```json
{
  "timestamp": "2025-12-07T21:30:00",
  "data_source": "kraken_cache",
  "market": "BTC/EUR",
  "timeframe": "1h",
  "results": [
    {
      "name": "ma_crossover",
      "status": "ok",
      "data_health": "ok",
      "data_notes": null,
      "return_pct": 5.23,
      ...
    }
  ]
}
```

### Markdown-Report mit Data-Health-Spalte

```markdown
| Strategy | Status | Return | Sharpe | MaxDD | Trades | Data-Health |
|----------|--------|--------|--------|-------|--------|-------------|
| ma_crossover | OK | +5.23% | 1.45 | 8.12% | 42 | ok |
```

---

## Dateien (Phase 79)

| Datei | Beschreibung |
|-------|--------------|
| `config/config.toml` | `[real_market_smokes]` Block hinzugefügt |
| `src/data/kraken_cache_loader.py` | **NEU** - Loader mit Data-QC |
| `src/data/__init__.py` | Exports erweitert |
| `src/strategies/diagnostics.py` | `data_health`, `data_notes` Felder |
| `scripts/strategy_smoke_check.py` | `--check-data-only`, `--min-bars` Flags |
| `tests/test_kraken_cache_loader.py` | **NEU** - Loader-Tests |
| `tests/test_strategy_smoke_cli.py` | Phase 79 Tests hinzugefügt |
| `docs/PHASE_79_REAL_MARKET_DATA_QC.md` | Diese Dokumentation |

---

## Bekannte Limitierungen

1. **Nur BTC/EUR 1h** im Test-Cache (`tests/data/kraken_smoke/`)
2. Produktiv-Cache unter `data/cache/` muss manuell befüllt werden
3. Keine automatische Cache-Aktualisierung (Offline-only)

---

## Nächste Schritte (Future Phases)

- [ ] Weitere Märkte/Timeframes im Test-Cache
- [ ] Automatischer Cache-Refresh (optional, mit Rate-Limits)
- [ ] Data-Coverage-Dashboard (Übersicht aller verfügbaren Caches)
- [ ] Freshness-Check (Daten älter als N Tage = Warnung)

---

*Generiert: 2025-12-07 | Peak_Trade Phase 79*
