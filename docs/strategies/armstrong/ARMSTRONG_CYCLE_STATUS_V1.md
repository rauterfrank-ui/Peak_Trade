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

## R&D-Varianten (Tier-3)

Armstrong hat zwei „würzige" R&D-Varianten für unterschiedliche Test-Szenarien.
Beide sind strikt **Tier-3 / R&D** – kein Live-, Paper- oder Testnet-Flow.

### A) Armstrong Last-Test (Dummy-Daten, mehr Last)

**Zweck:** Pipeline-Performance- und Last-Tests mit synthetischen Daten

**Wann benutzen?**
- Wenn du prüfen willst, ob die Pipeline unter höherer Last stabil läuft
- Wenn synthetische Dummy-Daten ausreichen und Markt-Realismus nicht wichtig ist

**Command:**
```bash
python scripts/run_backtest.py \
  --strategy armstrong_cycle \
  --config config.toml \
  --tag rnd_armstrong_spicy_5k_bars \
  --bars 5000 \
  --save-report reports/r_and_d/armstrong_spicy_5k_bars.html \
  --verbose
```

**Erwartete Outputs:**
- HTML-Report: `reports/r_and_d/armstrong_spicy_5k_bars.html`
- Registry-Eintrag mit Tag `rnd_armstrong_spicy_5k_bars`
- Terminal-Output mit Kennzahlen (Total Return, Sharpe, Trades)

---

### B) Armstrong Real-Data (echte Daten, engeres Zeitfenster)

**Zweck:** Armstrong mit echten OHLCV-Daten in einem volatilen Zeitfenster testen

**Voraussetzung:** Eigene OHLCV-CSV-Datei unter `data/ohlcv/` (z.B. `btcusdt_1d.csv`)

**Wann benutzen?**
- Wenn der Basis-Smoke-Test stabil läuft
- Wenn du Armstrong mit echten Daily-Daten sehen willst

**Command:**
```bash
python scripts/run_backtest.py \
  --strategy armstrong_cycle \
  --config config.toml \
  --tag rnd_armstrong_trend_spice \
  --data-file data/ohlcv/btcusdt_1d.csv \
  --start-date 2019-01-01 \
  --end-date 2019-06-30 \
  --save-report reports/r_and_d/armstrong_trend_spice.html \
  --verbose
```

**Erwartete Outputs:**
- HTML-Report: `reports/r_and_d/armstrong_trend_spice.html`
- Equity-Plot: `reports/r_and_d/armstrong_trend_spice_equity.png`
- Stats-JSON: `reports/r_and_d/armstrong_trend_spice_stats.json`
- Registry-Eintrag mit Tag `rnd_armstrong_trend_spice`
- Plots mit echten Trends/Drawdowns und Cycle-Phasen-Verteilung

---

## Experiment Templates

### Template 1: `armstrong_cycle_tier3_lasttest_v1`

**Zweck:** Pipeline-Stabilität unter Last mit synthetischen Daten

| Aspekt | Wert |
|--------|------|
| Strategy | `armstrong_cycle` |
| Bars | 5000 |
| Config | `config.toml` |
| Tag | `rnd_armstrong_lasttest_v1` |
| Output | `reports/r_and_d/armstrong_lasttest_v1.html` |

```bash
python scripts/run_backtest.py \
  --strategy armstrong_cycle \
  --config config.toml \
  --tag rnd_armstrong_lasttest_v1 \
  --bars 5000 \
  --save-report reports/r_and_d/armstrong_lasttest_v1.html \
  --verbose
```

---

### Template 2: `armstrong_cycle_tier3_realdata_v1`

**Zweck:** Cycle-Phasen-Verhalten mit echten Marktdaten analysieren

| Aspekt | Wert |
|--------|------|
| Strategy | `armstrong_cycle` |
| Data | `data/ohlcv/btcusdt_1d.csv` |
| Date-Range | 2019-01-01 bis 2019-06-30 |
| Config | `config.toml` |
| Tag | `rnd_armstrong_realdata_v1` |
| Output | `reports/r_and_d/armstrong_realdata_v1.html` |

```bash
python scripts/run_backtest.py \
  --strategy armstrong_cycle \
  --config config.toml \
  --tag rnd_armstrong_realdata_v1 \
  --data-file data/ohlcv/btcusdt_1d.csv \
  --start-date 2019-01-01 \
  --end-date 2019-06-30 \
  --save-report reports/r_and_d/armstrong_realdata_v1.html \
  --verbose
```

**Output-Struktur:**
```
reports/r_and_d/
├── armstrong_realdata_v1.html
├── armstrong_realdata_v1_equity.png
├── armstrong_realdata_v1_stats.json
└── ...

reports/experiments/
└── experiments.csv  (neue Zeile mit run_id, strategy_key, Stats)
```

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
