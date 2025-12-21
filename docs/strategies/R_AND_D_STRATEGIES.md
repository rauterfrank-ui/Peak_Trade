# Research & Development Strategies (R&D-Only)

⚠️ **WICHTIG: Diese Strategien sind NICHT für Live-Trading freigegeben** ⚠️

Diese Dokumentation beschreibt die **Research-Only Strategien** in Peak_Trade.
Diese Strategien sind ausschließlich für:
- Offline-Backtests und historische Analysen
- Akademische Research und Experimente
- Proof-of-Concept Implementierungen
- Explorative Datenanalysen

**Sie dürfen NIEMALS im Live-Trading verwendet werden.**

---

## Übersicht: R&D-Strategien in Peak_Trade

Peak_Trade enthält folgende Research-Only Strategien:

| Strategy Key               | Status      | Zweck                                    | Datenanforderung         |
|----------------------------|-------------|------------------------------------------|--------------------------|
| `ehlers_cycle_filter`      | Stub/Flat   | DSP-basierte Cycle-Detection             | OHLCV, mind. 120 Bars    |
| `meta_labeling`            | Stub/Flat   | Meta-Layer für ML-basiertes Trading      | OHLCV, mind. 50 Bars     |
| `vol_regime_overlay`       | Skeleton    | Vol-Regime-basiertes Risk-Management     | OHLCV, mind. 100 Bars    |
| `bouchaud_microstructure`  | Skeleton    | Orderbuch-/Tick-basierte Microstructure  | **Tick/Orderbuch-Daten** |

**Legende:**
- **Stub/Flat**: Implementiert, gibt aber flat-Signal (0) zurück – keine echte Trading-Logik
- **Skeleton**: Platzhalter-Struktur, wirft `NotImplementedError` – strukturelle Basis für zukünftige Implementierung

---

## Gate-System: Wie R&D-Strategien geschützt sind

Peak_Trade verwendet ein **3-stufiges Gate-System** in `src/strategies/registry.py`, um sicherzustellen, dass Research-Only Strategien niemals versehentlich in Produktion oder Live-Trading gelangen:

### Gate A: Live-Mode Hard-Gate (HART-SCHUTZ)
```python
if env == "live" and strategy.IS_LIVE_READY == False:
    raise ValueError("Strategy cannot be used in LIVE mode")
```
**Alle** R&D-Strategien haben `IS_LIVE_READY = False` → Instanziierung in Live-Mode wird **IMMER** blockiert.

### Gate B: R&D-Tier-Gate (Opt-In erforderlich)
```python
if strategy.TIER == "r_and_d" and not allow_r_and_d_strategies:
    raise ValueError("R&D strategy disabled. Set research.allow_r_and_d_strategies=true")
```
**Alle** R&D-Strategien haben `TIER = "r_and_d"` → Benötigen explizites Flag in Config.

### Gate C: Allowed-Environments-Gate (Env-Validierung)
```python
if env not in strategy.ALLOWED_ENVIRONMENTS:
    raise ValueError(f"Strategy not allowed in env '{env}'")
```
**Alle** R&D-Strategien haben `ALLOWED_ENVIRONMENTS = ["offline_backtest", "research"]` → Blockieren unerwünschte Modi.

---

## Aktivierung: R&D-Strategien im Backtest verwenden

Um eine R&D-Strategie im **Offline-Backtest** zu nutzen:

### 1. Config-Flag setzen

In `config.toml` oder über Environment Variable:

```toml
[research]
allow_r_and_d_strategies = true

[environment]
mode = "offline_backtest"  # NICHT "live"!
```

### 2. Strategy in Config referenzieren

Beispiel für Ehlers Cycle Filter:

```toml
[strategy.ehlers_cycle_filter]
smoother_type = "super_smoother"
min_cycle_length = 6
max_cycle_length = 50
cycle_threshold = 0.5
bandpass_bandwidth = 0.3
lookback = 100
use_hilbert_transform = true
```

### 3. Registry verwenden

```python
from src.strategies.registry import create_strategy_from_config
from src.core.peak_config import load_config

cfg = load_config()
strategy = create_strategy_from_config("ehlers_cycle_filter", cfg)
```

**Wichtig:** Ohne `research.allow_r_and_d_strategies = true` → ValueError!

---

## Strategien im Detail

### 1. Ehlers Cycle Filter Strategy

**Key:** `ehlers_cycle_filter`
**Datei:** `src/strategies/ehlers/ehlers_cycle_filter_strategy.py`
**Status:** Stub (gibt flat-Signal zurück)

#### Zweck
Implementierung von John Ehlers' Digital Signal Processing (DSP) Techniken:
- **Super Smoother Filter**: Bessere Glättung als EMA/SMA mit weniger Lag
- **Cycle-Detection**: Identifikation dominanter Marktzyklen via Hilbert Transform
- **Bandpass-Filter**: Isolierung der Cycle-Komponente für bessere Signalqualität

#### Konzept
- Preis-Daten mit DSP-Filtern glätten (Noise-Reduktion)
- Dominante Zyklusperiode messen (typisch 6-50 Bars)
- Entries bei Zyklus-Tiefs, Exits bei Zyklus-Hochs

#### Datenanforderungen
- OHLCV-Daten (mindestens `close`-Spalte)
- Minimum 100-120 Bars für Lookback

#### Aktueller Status
⚠️ **Stub-Implementierung**: `generate_signals()` gibt aktuell nur `pd.Series(0)` zurück.

Geplante Implementierung (TODO):
1. Super Smoother Filter (2-Pole Butterworth)
2. Hilbert Transform für Cycle-Period-Messung
3. Bandpass Filter für Cycle-Isolierung
4. Phase-basierte Entry/Exit-Logik

#### Config-Parameter
```toml
[strategy.ehlers_cycle_filter]
smoother_type = "super_smoother"    # "super_smoother", "two_pole", "three_pole"
min_cycle_length = 6                # Minimale Zykluslänge in Bars
max_cycle_length = 50               # Maximale Zykluslänge in Bars
cycle_threshold = 0.5               # Signal-Schwelle (0.0 - 1.0)
bandpass_bandwidth = 0.3            # Bandpass-Bandbreite
lookback = 100                      # Benötigte Historie
use_hilbert_transform = true        # Hilbert-Transform verwenden
```

#### Referenzen
- John Ehlers: "Cybernetic Analysis for Stocks and Futures"
- John Ehlers: "Rocket Science for Traders"

---

### 2. Meta-Labeling Strategy (López de Prado)

**Key:** `meta_labeling`
**Datei:** `src/strategies/lopez_de_prado/meta_labeling_strategy.py`
**Status:** Stub (gibt flat-Signal zurück)

#### Zweck
Meta-Layer über bestehenden Strategien nach Marcos López de Prado:
- **Triple-Barrier-Labeling**: TP, SL, oder Time-Exit-basierte Labels
- **Meta-Model**: ML-Modell entscheidet, welche Basis-Signale gehandelt werden
- **Bet-Sizing**: Position-Sizing basierend auf Modell-Confidence

#### Konzept
1. **Basis-Strategie** generiert Richtungs-Signale (long/short)
2. **Triple-Barrier** definiert Outcome-Labels: +1 (TP hit), -1 (SL hit), 0 (time-out)
3. **Feature-Engineering**: Volatility, Momentum, Regime-Indikatoren
4. **Meta-Model** (Random Forest, XGBoost): Filtert Basis-Signale
5. **Output**: Nur Signale mit Confidence > `min_confidence` werden ausgeführt

#### Datenanforderungen
- OHLCV-Daten (mindestens `close`-Spalte)
- Minimum 50 Bars für Basis-Strategie + Triple-Barrier-Lookback

#### Aktueller Status
⚠️ **Stub-Implementierung**: `generate_signals()` gibt aktuell nur `pd.Series(0)` zurück.

Geplante Implementierung (TODO):
1. Triple-Barrier-Labeling-Funktion
2. Feature-Engineering-Pipeline (Fractional Differentiation, Vol-adjusted Returns)
3. ML-Modell-Training/Evaluation (Cross-Validation, Walk-Forward)
4. Bet-Sizing basierend auf Confidence

#### Config-Parameter
```toml
[strategy.meta_labeling]
base_strategy_id = "rsi_reversion"   # ID der Basis-Strategie
take_profit = 0.02                   # Take-Profit-Schwelle (2%)
stop_loss = 0.01                     # Stop-Loss-Schwelle (1%)
vertical_barrier_bars = 20           # Maximale Haltedauer in Bars
prediction_horizon_bars = 10         # Vorhersage-Horizont
use_triple_barrier = true            # Triple-Barrier verwenden
meta_model_type = "random_forest"    # ML-Modell-Typ (Platzhalter)
min_confidence = 0.5                 # Min. Confidence für Trade-Ausführung
```

#### Referenzen
- Marcos López de Prado: "Advances in Financial Machine Learning"
- Marcos López de Prado: "Machine Learning for Asset Managers"

---

### 3. Vol Regime Overlay Strategy (Gatheral & Cont)

**Key:** `vol_regime_overlay`
**Datei:** `src/strategies/gatheral_cont/vol_regime_overlay_strategy.py`
**Status:** Skeleton (wirft NotImplementedError)

#### Zweck
**Meta-Risk-/Regime-Layer** (KEIN eigenständiger Signal-Generator):
- **Regime-Detection**: Low-Vol, Normal, High-Vol Regimes identifizieren
- **Position-Sizing-Scaler**: Dynamisches Sizing basierend auf Vol-Regime
- **Vol-Budget-Management**: Tägliches Volatilitäts-Budget und Drawdown-Limits

#### Konzept (Gatheral & Cont)
- **Jim Gatheral**: Stochastic Volatility Models, Rough Volatility (H ≈ 0.1), Vol-Surface-Dynamik
- **Rama Cont**: Stilisierte Fakten, Fat Tails, Volatility Clustering, Regime-Switching

#### Anwendung als Meta-Layer
⚠️ **Dies ist KEIN eigenständiger Signal-Generator!**

Geplante Nutzung:
```python
# Nicht als standalone Strategy
strategy = VolRegimeOverlayStrategy(...)
# strategy.generate_signals(data)  # → Wirft NotImplementedError!

# Stattdessen: Meta-Layer-Methoden
regime = strategy.get_regime_state(data)      # "low_vol" | "normal" | "high_vol"
scalar = strategy.get_position_scalar(data)   # 0.0 - 1.0 für Sizing
should_reduce = strategy.should_reduce_exposure(data)  # DD-Check
```

#### Datenanforderungen
- OHLCV-Daten
- Minimum 100 Bars für Regime-Lookback

#### Aktueller Status
⚠️ **Skeleton/Platzhalter**: `generate_signals()` wirft `NotImplementedError`.

Geplante Implementierung (TODO):
1. Realized-Volatility-Schätzer (Parkinson, Garman-Klass)
2. Regime-Detection (HMM, Rolling-Percentile)
3. Optional: Rough-Vol-Schätzer (Hurst-Exponent H ≈ 0.1)
4. Integration mit Peak_Trade Position-Sizing-Modul

#### Config-Parameter
```toml
[strategy.vol_regime_overlay]
day_vol_budget = 0.02               # Tägliches Vol-Budget (2%)
max_intraday_dd = 0.01              # Max. Intraday-Drawdown (1%)
regime_lookback_bars = 100          # Lookback für Regime-Bestimmung
high_vol_threshold = 0.75           # High-Vol-Regime Percentile
low_vol_threshold = 0.25            # Low-Vol-Regime Percentile
use_rough_vol = false               # Rough-Vol-Schätzer (rechenintensiv)
hurst_lookback = 252                # Lookback für Hurst-Exponent
vol_target_scaling = true           # Vol-Target-Scaling aktivieren
```

#### Referenzen
- Jim Gatheral: "The Volatility Surface"
- Gatheral et al.: "Volatility is Rough"
- Rama Cont: "Empirical Properties of Asset Returns"

#### Wichtiger Hinweis
**VolRegimeOverlay sollte perspektivisch als Overlay/Sizer im Risk-Management-Layer integriert werden, NICHT als normale Signal-Strategie.**

---

### 4. Bouchaud Microstructure Strategy

**Key:** `bouchaud_microstructure`
**Datei:** `src/strategies/bouchaud/bouchaud_microstructure_strategy.py`
**Status:** Skeleton (wirft NotImplementedError)

#### Zweck
Markt-Mikrostruktur-Strategie basierend auf Jean-Philippe Bouchauds Arbeiten:
- **Orderbuch-Imbalance**: Bid/Ask-Volume-Ratio als Preisdruck-Indikator
- **Trade-Signs**: Kauf-/Verkaufssignal-Autokorrelation (Metaorder-Detection)
- **Propagator-Modelle**: Wie Trades den Preis beeinflussen
- **Price-Impact**: Institutionelle Orderflows identifizieren

#### Datenanforderungen
⚠️ **ACHTUNG: Diese Strategie benötigt Tick- oder Orderbuch-Daten, die in Peak_Trade NICHT verfügbar sind!**

Erforderliche Daten:
- **Tick-Daten**: Trade Prints (Timestamp, Price, Size, Side)
- **Orderbuch-Snapshots**: L2/L3 Depth (Bid/Ask Prices & Volumes)

**OHLCV-Daten (1m/1h/1d) sind NICHT ausreichend für Microstructure-Analysen!**

#### Aktueller Status
⚠️ **Skeleton/Platzhalter**: `generate_signals()` wirft `NotImplementedError`.

Geplante Implementierung (TODO – wenn Tick-Daten verfügbar):
1. Orderbuch-Imbalance-Berechnung: `(bid_vol - ask_vol) / (bid_vol + ask_vol)`
2. Trade-Sign-Extraktion (Lee-Ready-Algorithmus)
3. Propagator-basierte Preisvorhersage
4. Signal-Generierung bei signifikanter Imbalance

#### Config-Parameter
```toml
[strategy.bouchaud_microstructure]
use_orderbook_imbalance = true      # Orderbuch-Imbalance verwenden
use_trade_signs = true              # Trade-Sign-Korrelationen verwenden
lookback_ticks = 100                # Anzahl historischer Ticks
min_liquidity_filter = 1000.0       # Min. Liquidität (Bid+Ask Volume)
imbalance_threshold = 0.3           # Schwelle für Imbalance-Signal
propagator_decay = 0.5              # Decay-Parameter für Propagator
```

#### Referenzen
- J.P. Bouchaud et al.: "Trades, Quotes and Prices"
- J.P. Bouchaud, M. Potters: "Theory of Financial Risk and Derivative Pricing"

#### Wichtiger Hinweis
**Diese Strategie ergibt nur Sinn mit Hochfrequenz-/Tick-Daten. Implementierung erfordert erheblichen Research-Aufwand und Dateninfrastruktur-Änderungen.**

---

## Tests: Gate-Absicherung verifizieren

Die Gating-Logik ist durch Tests in `tests/test_r_and_d_strategy_gating.py` abgesichert:

### Test-Szenarien
1. **Ohne R&D-Flag**: `create_strategy_from_config()` → `ValueError`
2. **Mit R&D-Flag + offline_backtest**: Instanziierung erfolgreich
3. **Mit R&D-Flag + live mode**: `ValueError` (IS_LIVE_READY=False)
4. **Stub-Verhalten**: Flat-Signal (Ehlers, Meta-Labeling) oder NotImplementedError (VolRegime, Bouchaud)

Tests ausführen:
```bash
python -m pytest tests/test_r_and_d_strategy_gating.py -v
```

---

## Best Practices: R&D-Strategien nutzen

### ✅ DO:
- R&D-Strategien nur in `offline_backtest` oder `research` Mode nutzen
- Config-Flag `research.allow_r_and_d_strategies = true` explizit setzen
- Stub-/Skeleton-Status in Code-Kommentaren und Doku beachten
- Erwartungshaltung: Stub = Flat-Signal, Skeleton = NotImplementedError

### ❌ DON'T:
- **NIEMALS** R&D-Strategien in Live-Trading verwenden
- **NIEMALS** `IS_LIVE_READY = False` in Produktion überschreiben
- **NIEMALS** Gate-Logik in `registry.py` umgehen oder deaktivieren
- Nicht erwarten, dass Skeleton-Strategien Trading-Signale liefern

---

## Next Steps: Implementierungs-Roadmap

### 1. VolRegimeOverlay als echtes Overlay/Sizer
**Ziel**: Integration in Position-Sizing/Risk-Management-Layer

Schritte:
- Trennung von Signal-Generation und Risk-Management
- `get_regime_state()` und `get_position_scalar()` implementieren
- Integration mit `src/execution/position_sizing.py`

### 2. Ehlers DSP Filter-Bibliothek
**Ziel**: Robuste, lookahead-freie DSP-Filter für Intraday-Signale

Schritte:
- Super Smoother (2-Pole Butterworth + 2-Bar SMA)
- Hilbert Transform (Cycle-Period + Phase)
- Bandpass Filter (Isolierung Cycle-Komponente)
- Backtests auf 1m/5m Intraday-Daten (BTC, ETH, SPY)

### 3. Meta-Labeling: Triple-Barrier + Feature-Pipeline
**Ziel**: ML-basierte Signal-Filterung über RSI/MA-Crossover

Schritte:
- Triple-Barrier-Labeling-Funktion (TP, SL, Time-Exit)
- Feature-Engineering (Fractional Diff, Vol-adjusted Returns, Regime-Indikatoren)
- ML-Modell (Random Forest / XGBoost)
- Walk-Forward-Validation + Cross-Validation
- Bet-Sizing basierend auf Model-Confidence

### 4. Bouchaud Microstructure (Langfristig)
**Ziel**: Tick-/Orderbuch-basierte Strategie (falls Dateninfrastruktur verfügbar)

Voraussetzungen:
- Tick-Daten-Infrastruktur aufbauen (Binance/FTX Tick Replay)
- Orderbuch-Snapshots (L2/L3)
- Niedrige Latenz für Microstructure-Signale

---

## Support & Fragen

Bei Fragen zu R&D-Strategien:
1. Prüfe diese Dokumentation
2. Prüfe Code-Kommentare in Strategy-Dateien
3. Prüfe Tests in `tests/test_r_and_d_strategy_gating.py`
4. Öffne Issue in Peak_Trade Repository mit Tag `[R&D]`

---

**Dokument-Version:** 1.0.0
**Letzte Aktualisierung:** 2025-12-18
**Autor:** Peak_Trade Research Team
