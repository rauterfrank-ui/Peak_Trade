# ✅ R&D-Strategie: Armstrong Cycle Strategy – Status v1

| Aspekt | Details |
|--------|---------|
| **Modulpfad** | `src/strategies/armstrong/` |
| **Klassen** | `ArmstrongPhase`, `ArmstrongCycleConfig`, `ArmstrongCycleModel` (`cycle_model.py`), `ArmstrongCycleStrategy` (`armstrong_cycle_strategy.py`) |
| **Kategorie** | `cycles` |
| **Tier** | `r_and_d` (rein Research/Backtests, keine Live-Freigabe) |
| **Registry-Key** | `armstrong_cycle` |

---

## ⚠️ Tier-3 / R&D Only

> **Dieses Modell ist ausschließlich für Research und Offline-Backtests freigegeben.**
> Es existiert **kein** Live-Executor-Pfad, **kein** Order-Routing und **keine** Production-Safety-Gates.
> Jeder Versuch, Armstrong in einem Live-/Paper-/Testnet-Modus zu starten, wird mit einer `RnDLiveTradingBlockedError` blockiert.

---

## Funktionale Idee

- Implementiert das **Armstrong Economic Confidence Model (ECM)** als deterministisches Zyklus-Modell
- ECM-Grundzyklus: **8,6 Jahre = 3141 Tage ≈ π × 1000**
- Phasen: `CRISIS`, `PRE_CRISIS`, `POST_CRISIS`, `EXPANSION`, `CONTRACTION`
- Jede Phase hat einen **Risk-Multiplier** für Position-Sizing (0.3 – 1.0)
- Übersetzt aktive Phase in Positions-Entscheidungen via Phase→Position-Maps:
  - **Default**: EXPANSION/POST_CRISIS→long, CONTRACTION/PRE_CRISIS/CRISIS→flat
  - **Conservative**: nur EXPANSION→long, sonst flat
  - **Aggressive**: EXPANSION/POST_CRISIS→long, PRE_CRISIS/CRISIS→short

**Warnung:**
- Armstrong-Zyklen sind **NICHT wissenschaftlich validiert**
- Hindsight-Bias ist ein bekanntes Problem
- Nutze dieses Modell nur für **explorative Analysen**

---

## Kernkomponenten

### `cycle_model.py`

| Klasse/Enum | Beschreibung |
|-------------|--------------|
| `ArmstrongPhase` | Enum mit `CRISIS`, `EXPANSION`, `CONTRACTION`, `PRE_CRISIS`, `POST_CRISIS` |
| `ArmstrongCycleConfig` | Dataclass für Zyklus-Parameter (reference_peak_date, cycle_length_days, phase_distribution, risk_multipliers) |
| `ArmstrongCycleModel` | Hauptmodell für deterministische Phasenberechnung |

**Wichtige Methoden:**
- `phase_for_date(dt)` → Aktuelle Phase für ein Datum
- `risk_multiplier_for_date(dt)` → Risk-Multiplier (0.0–1.0)
- `get_cycle_info(dt)` → Umfassende Zyklus-Info (phase, position, days_to_turning_point, etc.)
- `from_default()` → Factory mit ECM 2015.75 als Referenz
- `from_config_dict(dict)` → Factory aus Config-Dict

### `armstrong_cycle_strategy.py`

| Klasse | Beschreibung |
|--------|--------------|
| `ArmstrongCycleStrategy` | Hauptstrategie mit Signal-Generierung basierend auf ECM-Phasen |

**Wichtige Methoden:**
- `generate_signals(data)` → Signal-Series (0/1/-1) basierend auf Zyklus-Phase
- `get_cycle_info(dt)` → Zyklus-Info für Datum
- `get_phase_for_date(dt)` → Aktuelle Phase
- `get_position_for_phase(phase)` → Position für gegebene Phase
- `get_strategy_info()` → Strategy-Metadaten inkl. Tier

**Klassen-Flags:**
- `KEY = "armstrong_cycle"`
- `IS_LIVE_READY = False`
- `ALLOWED_ENVIRONMENTS = ["offline_backtest", "research"]`
- `TIER = "r_and_d"`

---

## Safety / Gating

- R&D-Tier wird in `src/live/live_gates.py` explizit geprüft
- Exception: `RnDLiveTradingBlockedError`
- **Blockierte Modi**: `live`, `paper`, `testnet`, `shadow` → Exception
- **Erlaubte Modi**: `offline_backtest`, `research` → OK

**Gating-Funktionen:**
- `check_r_and_d_tier_for_mode("armstrong_cycle", mode)` → `True` wenn blockiert
- `assert_strategy_not_r_and_d_for_live("armstrong_cycle", mode)` → wirft Exception bei Blockierung
- `get_strategy_tier("armstrong_cycle")` → `"r_and_d"`
- `check_strategy_live_eligibility("armstrong_cycle")` → `LiveGateResult(is_eligible=False, ...)`

---

## Tests (74 Tests gesamt)

| Testdatei | Tests | Beschreibung |
|-----------|-------|--------------|
| `tests/strategies/armstrong/test_cycle_model.py` | 26 | ArmstrongPhase-Enum, ArmstrongCycleConfig-Validierung, Cycle-Position-Berechnung, Phase-Bestimmung, Risk-Multipliers, Convenience-Funktionen |
| `tests/strategies/armstrong/test_armstrong_cycle_strategy.py` | 48 | Instanziierung, Config-Override, R&D-Safety-Flags, Phase-Position-Mappings, Signal-Generierung, Metadaten, Helper-Methoden, Tier-Gating, Exception-Tests, Smoke-Tests |

**Abdeckung:**
- ✅ Cycle-Model-Logik (Phasen-Bestimmung, Zyklus-Position)
- ✅ Risk-Multiplier-Berechnung
- ✅ Strategy-Signal-Generierung
- ✅ Phase→Position-Mapping (Default, Conservative, Aggressive)
- ✅ R&D-Tier-Gating (alle blockierten Modi)
- ✅ Exception-Handling (RnDLiveTradingBlockedError)
- ✅ Smoke-Tests (End-to-End Backtest-Workflow)

---

## Registrierung

| Datei | Eintrag |
|-------|---------|
| `src/strategies/__init__.py` | `"armstrong_cycle": "armstrong.armstrong_cycle_strategy"` |
| `src/strategies/registry.py` | `_STRATEGY_REGISTRY["armstrong_cycle"]` mit `ArmstrongCycleStrategy` |
| `config/strategy_tiering.toml` | `[strategy.armstrong_cycle]` mit `tier = "r_and_d"`, `category = "cycles"` |

**Tiering-Config (Auszug):**
```toml
[strategy.armstrong_cycle]
tier = "r_and_d"
label = "Armstrong Cycle Model"
category = "cycles"
risk_profile = "experimental"
owner = "research"
tags = ["cycles", "ecm", "armstrong", "macro", "timing"]
recommended_config_id = "armstrong_cycle_v0_research"
allow_live = false
```

---

## Wichtige Parameter

| Parameter | Default | Beschreibung |
|-----------|---------|--------------|
| `cycle_length_days` | 3141 | ECM-Zyklus-Länge in Tagen (≈ 8.6 Jahre) |
| `event_window_days` | 90 | Fenster um Turning-Points (Tage) |
| `reference_date` | 2015-10-01 | Referenz-Turning-Point (ECM 2015.75) |
| `phase_position_map` | "default" | Mapping-Strategie ("default", "conservative", "aggressive") |
| `use_risk_scaling` | True | Ob Risk-Multiplier angewendet wird |
| `underlying` | "SPX" | Underlying-Symbol |

**Phasen-Verteilung im Zyklus (Default):**

| Phase | Zyklus-Anteil | Risk-Multiplier |
|-------|---------------|-----------------|
| POST_CRISIS | 0–15% | 0.5 |
| EXPANSION | 15–45% | 1.0 |
| PRE_CRISIS_MID | 45–50% | 0.7 |
| CONTRACTION | 50–85% | 0.6 |
| PRE_CRISIS | 85–95% | 0.4 |
| CRISIS | 95–100% | 0.3 |

---

## Kanonische R&D-Experimente

> **⚠️ Tier-3 / R&D Only – Keine Live-/Testnet-Ausführung**
>
> Die folgenden Experimente sind ausschließlich für Research und Offline-Backtests freigegeben.
> Live-Gates blockieren automatisch jeden Versuch, Armstrong in `live`, `paper`, `testnet` oder `shadow`
> Modus auszuführen (`RnDLiveTradingBlockedError`).

### Übersicht

| Name | Zweck | Command (Kurz) | Output-Pfad (Schema) |
|------|-------|----------------|----------------------|
| `armstrong_cycle_tier3_lasttest_v1` | Pipeline-/Last-Test mit synthetischen Daten (5000 Bars) | `run_backtest.py --strategy armstrong_cycle --bars 5000` | `reports&#47;r_and_d&#47;armstrong_cycle&#47;lasttest_v1&#47;` |
| `armstrong_cycle_tier3_realdata_v1` | Cycle-Analyse mit echten OHLCV-Daten | `run_backtest.py --strategy armstrong_cycle --data-file ...` | `reports&#47;r_and_d&#47;armstrong_cycle&#47;realdata_v1&#47;` |

---

### 1) `armstrong_cycle_tier3_lasttest_v1`

**Zweck:**
- Pipeline-Performance- und Stabilitätstest unter höherer Last
- Fokus auf Durchsatz und Fehlerfreiheit, nicht Markt-Realismus
- Synthetische Dummy-Daten (Random-Walk mit Trend-Overlay)

**Wann benutzen?**
- Bei Code-Änderungen an der Pipeline oder Strategie
- Vor größeren R&D-Kampagnen als Smoke-Check
- Wenn schnelle Iteration wichtiger ist als Markt-Validierung

**Parameter:**

| Parameter | Wert | Beschreibung |
|-----------|------|--------------|
| `strategy` | `armstrong_cycle` | Armstrong ECM-Zyklus-Strategie |
| `bars` | `5000` | Anzahl synthetischer Bars |
| `config` | `config/config.toml` | Standard-Config (nutzt Default-Parameter) |
| `tag` | `rnd_armstrong_lasttest_v1` | Registry-Tag für Tracking |

**CLI-Command:**

```bash
python3 scripts/run_backtest.py \
  --strategy armstrong_cycle \
  --config config/config.toml \
  --bars 5000 \
  --tag rnd_armstrong_lasttest_v1 \
  --save-report reports/r_and_d/armstrong_cycle/lasttest_v1/report.html \
  --verbose
```

**Erwartete Outputs:**

```
reports/r_and_d/armstrong_cycle/lasttest_v1/
├── report.html                 # Interaktiver HTML-Report
├── backtest_armstrong_cycle_equity.png      # Equity-Kurve
├── backtest_armstrong_cycle_drawdown.png    # Drawdown-Plot
└── backtest_armstrong_cycle_stats.json      # Kennzahlen
```

**Erwartete Kennzahlen (Richtwerte):**
- Total Return: variabel (Random-Walk)
- Sharpe Ratio: typisch 0.3–1.0
- Max Drawdown: typisch -10% bis -30%
- Trades: variabel je nach Phase-Mapping

---

### 2) `armstrong_cycle_tier3_realdata_v1`

**Zweck:**
- Armstrong-Zyklus-Verhalten mit echten Marktdaten analysieren
- „Gefühl" für Metriken und Phasen-Verteilung entwickeln
- Explorative Analyse – keine Produktions-Validierung

**Wann benutzen?**
- Nach erfolgreichem `lasttest_v1`
- Wenn echte Marktdynamik relevant ist
- Für Phasen-Performance-Analyse (EXPANSION vs. CONTRACTION etc.)

**Voraussetzung:**
- OHLCV-CSV-Datei mit Daily-Daten (z.B. `data&#47;ohlcv&#47;btcusdt_1d.csv`)
- Wenn keine Datei vorhanden: Pfad als Platzhalter verwenden und eigene Daten bereitstellen

**Parameter:**

| Parameter | Wert | Beschreibung |
|-----------|------|--------------|
| `strategy` | `armstrong_cycle` | Armstrong ECM-Zyklus-Strategie |
| `data-file` | `data&#47;ohlcv&#47;btcusdt_1d.csv` | Pfad zur OHLCV-CSV (**⚠️ Platzhalter – eigene Daten bereitstellen**) |
| `start-date` | `2019-01-01` | Startdatum (volatiler Crypto-Winter-Zeitraum) |
| `end-date` | `2019-12-31` | Enddatum (1 Jahr für Cycle-Analyse) |
| `config` | `config/config.toml` | Standard-Config |
| `tag` | `rnd_armstrong_realdata_v1` | Registry-Tag für Tracking |

**CLI-Command:**

```bash
python3 scripts/run_backtest.py \
  --strategy armstrong_cycle \
  --config config/config.toml \
  --data-file data/ohlcv/btcusdt_1d.csv \
  --start-date 2019-01-01 \
  --end-date 2019-12-31 \
  --tag rnd_armstrong_realdata_v1 \
  --save-report reports/r_and_d/armstrong_cycle/realdata_v1/report.html \
  --verbose
```

**⚠️ Hinweis zu Daten:**
Falls `data&#47;ohlcv&#47;btcusdt_1d.csv` nicht existiert:
1. Erstelle das Verzeichnis: `mkdir -p data&#47;ohlcv`
2. Lade Daily-OHLCV-Daten herunter (z.B. von Binance, Kraken, CoinGecko)
3. Format: CSV mit Spalten `timestamp,open,high,low,close,volume`

**Erwartete Outputs:**

```
reports/r_and_d/armstrong_cycle/realdata_v1/
├── report.html                 # Interaktiver HTML-Report
├── backtest_armstrong_cycle_equity.png      # Equity-Kurve
├── backtest_armstrong_cycle_drawdown.png    # Drawdown-Plot
└── backtest_armstrong_cycle_stats.json      # Kennzahlen
```

**Erwartete Kennzahlen (Richtwerte für BTC 2019):**
- Total Return: abhängig von Marktphase
- Sharpe Ratio: typisch 0.5–1.5
- Max Drawdown: typisch -15% bis -35%
- Trades: wenige (Cycle-basierte Signale sind langfristig)

---

### Output-Struktur

Alle Armstrong-R&D-Experimente folgen diesem Schema:

```
reports/r_and_d/armstrong_cycle/
├── lasttest_v1/
│   ├── report.html
│   ├── backtest_armstrong_cycle_equity.png
│   ├── backtest_armstrong_cycle_drawdown.png
│   └── backtest_armstrong_cycle_stats.json
├── realdata_v1/
│   ├── report.html
│   ├── backtest_armstrong_cycle_equity.png
│   ├── backtest_armstrong_cycle_drawdown.png
│   └── backtest_armstrong_cycle_stats.json
└── ... (zukünftige Experimente)
```

Registry-Einträge werden automatisch in `reports/experiments/experiments.csv` geloggt.

---

### Safety-Hinweise

**Automatische Blockierung:**
Die folgenden Live-Gates verhindern Armstrong-Ausführung in Production-Modi:

| Funktion | Verhalten |
|----------|-----------|
| `check_strategy_live_eligibility("armstrong_cycle")` | `is_eligible=False`, Grund: R&D-Tier |
| `check_r_and_d_tier_for_mode("armstrong_cycle", "live")` | `True` (blockiert) |
| `assert_strategy_not_r_and_d_for_live("armstrong_cycle", "testnet")` | wirft `RnDLiveTradingBlockedError` |

**Erlaubte Modi:**
- `offline_backtest` ✅
- `research` ✅

**Blockierte Modi:**
- `live` ❌
- `paper` ❌
- `testnet` ❌
- `shadow` ❌

---

## Risiken & Grenzen

### Konzeptionelle Risiken

| Risiko | Beschreibung |
|--------|--------------|
| **Keine wissenschaftliche Validierung** | Das ECM ist nicht akademisch peer-reviewed oder empirisch robust validiert |
| **Hindsight-Bias** | Armstrong-Zyklen wurden retrospektiv auf historische Daten angepasst |
| **Determinismus** | Das Modell ist rein deterministisch – keine Adaption an Marktbedingungen |
| **Parameter-Sensitivität** | Kleine Änderungen an `reference_date` oder `cycle_length_days` können Ergebnisse stark verändern |

### Technische Limitierungen

| Limitierung | Beschreibung |
|-------------|--------------|
| **Keine Live-Integration** | Kein Order-Router, kein Execution-Hook, keine Broker-Anbindung |
| **Keine Production-Safety-Gates** | Circuit-Breaker, Max-Position-Limits etc. nicht implementiert |
| **Kein Risk-Management** | Kein Stop-Loss, kein Trailing-Stop, kein Drawdown-Limit |
| **Keine Slippage/Fee-Simulation** | Transaktionskosten nicht modelliert |

### Klarer Hinweis

> **Dieses Modell ist aktuell NICHT für Live-, Paper- oder Testnet-Orders freigegeben.**
> Es dient ausschließlich der explorativen Analyse und dem Verständnis von Cycle-basierten Timing-Konzepten.

---

## Next Steps / TODO-Liste

1. **Weitere Sweep-Experimente**
   - Parameter-Sweeps über `cycle_length_days` (z.B. 2000–4000 Tage)
   - Sweeps über `reference_date` (verschiedene historische Peaks)

2. **Robustheits-Checks**
   - Out-of-Sample-Tests auf verschiedenen Zeiträumen
   - Regime-Splits (Bull/Bear/Sideways-Märkte)
   - Cross-Asset-Tests (BTC, ETH, SPX, Gold)

3. **Kombinierte Experimente**
   - Armstrong × El Karoui: Cycle-Phasen als Vol-Regime-Filter
   - Armstrong als Meta-Signal für andere Strategien

4. **Metriken erweitern**
   - Phasen-spezifische Performance-Auswertung
   - Turning-Point-Treffer-Rate (Event-Studien)
   - Cycle-Phase-Verteilung über Zeit

5. **Visualisierungen**
   - Cycle-Position-Plot über Backtest-Zeitraum
   - Phasen-Heatmap mit Performance-Overlay
   - Turning-Point-Marker auf Preis-Charts

6. **Dokumentation**
   - Detaillierte ECM-Theorie-Referenz
   - Interpretation der Phasen für verschiedene Asset-Klassen

7. **Optionale spätere Live-Anbindung**
   - Strenge Bedingungen: Shadow-Mode zuerst
   - Nur als Overlay/Filter, nicht als Standalone-Signal
   - Requires: Full Risk-Management-Suite, Production-Gates, Audit-Trail

8. **Zusätzliche Tests**
   - Edge-Cases: Sehr kurze/lange Zeiträume
   - Boundary-Tests: Exakt auf Turning-Points
   - Performance-Tests: Große Datenmengen (>10k Bars)

---

## Verwandte Dokumente

- [R&D-Playbook Armstrong & El Karoui](../../runbooks/R_AND_D_PLAYBOOK_ARMSTRONG_EL_KAROUI_V1.md)
- [El Karoui Volatility Strategy – Status v1](../el_karoui/EL_KAROUI_VOL_STATUS_V1.md)
