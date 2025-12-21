# Offline-Realtime MA-Crossover Pipeline

## Überblick

Das Script `scripts/run_offline_realtime_ma_crossover.py` ermöglicht die Ausführung einer MA-Crossover-Strategie im `offline_realtime_pipeline`-Modus mit flexiblen CLI-Parametern.

## Features

- ✅ **Flexible CLI-Parameter** für Symbol, n-steps, n-regimes, MA-Fenster
- ✅ **Synth-Session** für synthetische Marktdaten mit Regime-Switching
- ✅ **OfflineRealtimeFeed** für realistische Daten-Wiedergabe
- ✅ **ExecutionPipeline** mit PaperOrderExecutor
- ✅ **HTML-Report-Generierung** mit Performance-Metriken
- ✅ **Symbol-Normalisierung** (z.B. `BTC/EUR` → `BTCEUR`)
- ✅ **Validierung** von Fast/Slow-Window-Parametern

## Workflow

```
1. CLI-Args parsen
2. Synth-Session bauen (n_steps, n_regimes)
3. OfflineRealtimeFeed aus Synth-Result erstellen
4. MACrossoverStrategy mit CLI-Parametern instanziieren
5. ExecutionPipeline aufsetzen
6. Pipeline ausführen
7. Report generieren
```

## Usage

### Basic Run mit Defaults

```bash
python scripts/run_offline_realtime_ma_crossover.py
```

### Custom Symbol und MA-Fenster

```bash
python scripts/run_offline_realtime_ma_crossover.py \
    --symbol BTC/EUR \
    --fast-window 10 \
    --slow-window 30
```

### Lange Simulation mit vielen Regimes

```bash
python scripts/run_offline_realtime_ma_crossover.py \
    --symbol ETH/USD \
    --n-steps 10000 \
    --n-regimes 10 \
    --fast-window 20 \
    --slow-window 50
```

### Mit Verbose-Logging

```bash
python scripts/run_offline_realtime_ma_crossover.py \
    --symbol BTC/EUR \
    --n-steps 1000 \
    --n-regimes 5 \
    --fast-window 10 \
    --slow-window 30 \
    --verbose
```

## CLI-Parameter

### Symbol

- `--symbol SYMBOL`: Trading-Symbol (z.B. `BTC/EUR`, `ETH/USD`)
- Default: `BTC/EUR`
- Wird intern normalisiert zu `BTCEUR`, `ETHUSD`, etc.

### Synth-Session-Parameter

- `--n-steps N_STEPS`: Anzahl der zu generierenden Ticks/Bars
  - Default: `1000`
  - Muss >= `slow-window` sein

- `--n-regimes N_REGIMES`: Anzahl der Regime-Wechsel
  - Default: `3`
  - Bestimmt, wie oft sich die Markt-Charakteristik ändert

- `--seed SEED`: Random-Seed für Reproduzierbarkeit
  - Default: `42`
  - Gleicher Seed → gleiche Ergebnisse

### MA-Crossover-Parameter

- `--fast-window FAST_WINDOW`: Fast-MA-Periode
  - Default: `20`
  - Muss < `slow-window` sein

- `--slow-window SLOW_WINDOW`: Slow-MA-Periode
  - Default: `50`
  - Muss > `fast-window` sein

### Feed-Parameter

- `--playback-mode {fast_forward,realtime}`: Playback-Modus
  - Default: `fast_forward`
  - `fast_forward`: Ohne Delays (für Backtests)
  - `realtime`: Mit Delays (für Live-Simulation)

- `--speed-factor SPEED_FACTOR`: Geschwindigkeitsfaktor für realtime-Modus
  - Default: `10.0`
  - Nur relevant bei `--playback-mode realtime`

### Output

- `--output-dir OUTPUT_DIR`: Output-Verzeichnis für Reports
  - Default: `reports/offline_realtime_pipeline/<run_id>`
  - Report wird als `summary.html` gespeichert

### Logging

- `--verbose`: Aktiviert verbose Logging (DEBUG-Level)
  - Default: INFO-Level

## Output

### Console-Output

Das Script gibt am Ende eine Zusammenfassung aus:

```
================================================================================
✓ Pipeline erfolgreich abgeschlossen
================================================================================
Run-ID: synth_BTCEUR_20251210_100319_2459d4
Symbol: BTC/EUR (intern: BTCEUR)
Fast/Slow-Window: 10/30
Ticks: 1,000
Orders: 1
Trades: 1
Netto-PnL: -47.09 EUR
Duration: 0.02s
Report: /Users/frnkhrz/Peak_Trade/reports/offline_realtime_pipeline/synth_BTCEUR_20251210_100319_2459d4/summary.html
================================================================================
```

### HTML-Report

Der generierte HTML-Report (`summary.html`) enthält:

- **Run-Informationen**: Run-ID, Symbol, Strategie, Environment, Timestamps
- **Synth-Session-Einstellungen**: N-Steps, N-Regimes, Seed
- **Strategie-Parameter**: Fast-Window, Slow-Window
- **Performance-Metriken**:
  - Verarbeitete Ticks
  - Generierte Orders
  - Ausgeführte Trades
  - Brutto-PnL
  - Netto-PnL
  - Gezahlte Fees
  - Max-Drawdown

## Architektur

### Komponenten

1. **OfflineSynthSessionConfig**: Konfiguration für Synth-Session
   - `n_steps`: Anzahl der Ticks
   - `n_regimes`: Anzahl der Regime-Wechsel
   - `seed`: Random-Seed
   - `base_price`: Start-Preis
   - `volatility`: Volatilität

2. **OfflineSynthSessionResult**: Ergebnis der Synth-Session
   - `df`: DataFrame mit OHLCV-Daten
   - `config`: Verwendete Config
   - `symbol`: Trading-Symbol
   - `run_id`: Eindeutige Run-ID

3. **OfflineRealtimeFeedConfig**: Konfiguration für Feed
   - `symbol`: Trading-Symbol
   - `playback_mode`: "fast_forward" oder "realtime"
   - `speed_factor`: Geschwindigkeitsfaktor

4. **OfflineRealtimeFeed**: Feed für Offline-Realtime-Wiedergabe
   - Simuliert einen Live-Feed
   - Sequentielle Wiedergabe von vorab generierten Daten

5. **OfflineRealtimePipelineStats**: Performance-Statistiken
   - Run-Informationen
   - Synth-Settings
   - Strategy-Settings
   - Performance-Metriken
   - Timing-Informationen

### Datenfluss

```
CLI-Args → SynthConfig → run_offline_synth_session()
                                    ↓
                        OfflineSynthSessionResult (OHLCV-Daten)
                                    ↓
                        OfflineRealtimeFeed.from_synth_session_result()
                                    ↓
                        MACrossoverStrategy.generate_signals()
                                    ↓
                        ExecutionPipeline.execute_from_signals()
                                    ↓
                        OrderExecutionResults
                                    ↓
                        OfflineRealtimePipelineStats
                                    ↓
                        write_offline_realtime_report() → summary.html
```

## Symbol-Normalisierung

Das Script verwendet `normalize_symbol()` für die Konvertierung:

```python
def normalize_symbol(symbol: str) -> str:
    """Normalisiert ein Trading-Symbol für interne Verwendung."""
    return symbol.replace("/", "").upper()
```

Beispiele:
- `BTC/EUR` → `BTCEUR`
- `ETH/USD` → `ETHUSD`
- `btc/eur` → `BTCEUR`

## Validierung

Das Script validiert automatisch:

1. **Fast/Slow-Window**: `fast_window` muss < `slow_window` sein
   ```bash
   # Fehler:
   python scripts/run_offline_realtime_ma_crossover.py --fast-window 50 --slow-window 30
   # error: fast-window (50) muss < slow-window (30) sein
   ```

2. **N-Steps vs. Slow-Window**: `n_steps` muss >= `slow_window` sein
   ```bash
   # Fehler:
   python scripts/run_offline_realtime_ma_crossover.py --n-steps 40 --slow-window 50
   # error: n-steps (40) muss >= slow-window (50) sein
   ```

3. **Order-Quantity**: Strategie validiert automatisch MA-Perioden >= 2

## Performance-Berechnung

### PnL-Berechnung

- **Brutto-PnL**: Summe aller Trade-Gewinne/-Verluste ohne Fees
- **Netto-PnL**: Brutto-PnL minus gezahlte Fees
- **Fees**: Berechnet basierend auf `fee_bps` (Default: 10 bps = 0.1%)

### Drawdown-Berechnung

- **Max-Drawdown**: Größter Rückgang vom Peak zur Talsohle
- Berechnet über die komplette Equity-Curve

## Erweiterungsmöglichkeiten

Das Script ist bewusst modular aufgebaut und kann leicht erweitert werden:

1. **Weitere Strategien**:
   - Einfach `MACrossoverStrategy` durch andere Strategien ersetzen
   - Parameter über CLI übergeben

2. **Komplexere Synth-Session**:
   - Mehr Regime-Parameter
   - Verschiedene Markt-Charakteristiken
   - Volatilität-Clustering

3. **Erweiterte Reporting**:
   - Trade-Liste
   - Equity-Curve-Plot
   - Drawdown-Plot
   - Signal-Visualisierung

4. **Risk-Management**:
   - Position-Sizing
   - Stop-Loss
   - Take-Profit

5. **Multi-Symbol**:
   - Portfolio von mehreren Symbolen
   - Korrelations-Analyse

## Troubleshooting

### Import-Fehler

Wenn `ModuleNotFoundError: No module named 'src'`:

```bash
# Stelle sicher, dass du im Projekt-Root bist:
cd /path/to/Peak_Trade

# Oder setze PYTHONPATH:
export PYTHONPATH=/path/to/Peak_Trade:$PYTHONPATH
python scripts/run_offline_realtime_ma_crossover.py
```

### Keine Trades

Wenn keine Trades ausgeführt werden:

1. **MA-Fenster zu groß**: Verkleinere `slow-window`
2. **Zu wenig Daten**: Erhöhe `n-steps`
3. **Keine Signal-Wechsel**: Erhöhe `n-regimes` oder ändere `seed`

### Negative PnL

Negative PnL ist normal bei:

- Zu hohen Fees
- Schlechten Entry/Exit-Punkten
- Trendlosen Märkten

Optimierungsmöglichkeiten:

- Anpasse `fast-window` / `slow-window`
- Ändere `n-regimes` für andere Markt-Charakteristiken
- Verwende verschiedene `seed`-Werte

## Testing

Die zugrunde liegenden Komponenten werden durch bestehende Tests abgedeckt:

```bash
# Execution-Pipeline-Tests
pytest tests/test_execution_pipeline.py -v

# MA-Crossover-Strategy-Tests (wenn vorhanden)
pytest tests/ -k "ma_crossover" -v
```

## Siehe auch

### Runbooks & Dokumentation

- **[OFFLINE_REALTIME_PIPELINE_RUNBOOK_V1](runbooks/OFFLINE_REALTIME_PIPELINE_RUNBOOK_V1.md)** – Operator-Runbook mit typischen Workflows, Szenarien und Troubleshooting
- **[RUNBOOKS_LANDSCAPE_2026_READY](runbooks/RUNBOOKS_LANDSCAPE_2026_READY.md)** – Zentrale Übersicht aller Runbooks

### Code-Referenzen

- `src/strategies/ma_crossover.py` - MA-Crossover-Strategie
- `src/execution/pipeline.py` - Execution-Pipeline
- `src/orders/paper.py` - Paper-Order-Executor
- `src/core/environment.py` - Environment-Config

## Changelog

### 2025-12-10 - v1.0.0 (Initial Release)

- ✅ CLI-Parameter für Symbol, n-steps, n-regimes, MA-Fenster
- ✅ Synth-Session-Implementierung
- ✅ OfflineRealtimeFeed-Implementierung
- ✅ ExecutionPipeline-Integration
- ✅ HTML-Report-Generierung
- ✅ Symbol-Normalisierung
- ✅ Parameter-Validierung
- ✅ Verbose-Logging
