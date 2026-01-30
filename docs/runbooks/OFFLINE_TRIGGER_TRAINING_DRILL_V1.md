# Offline Trigger-Training Drill – v0

## Meta

| Attribut | Wert |
|----------|------|
| **Mode** | `OFFLINE_ONLY &#47; NO REAL ORDERS` |
| **Ziel** | Operator-Training, Reaktions-Analyse, Signal-Disziplin |
| **Reports** | `offline_paper_trade_report.html` + `trigger_training_report.html` |
| **Status** | `EXPERIMENTAL &#47; v0` |
| **Owner** | Peak_Trade Operator Training Team |
| **Created** | 2025-12-10 |

---

## 1. Ziel & Scope

### Was ist ein Offline-Trigger-Training-Drill?

Dieser Drill simuliert eine Trading-Session, in der:

1. **Signale generiert werden** (z.B. MA-Crossover auf BTCEUR/1m)
2. Der **Operator** (oder ein Simulations-Script) darauf **reagiert** (`EXECUTED`, `SKIPPED`, `EXECUTED_FOMO`, etc.)
3. Alle Daten in strukturierte DataFrames fließen:
   - `trades_df` – ausgeführte Trades mit PnL
   - `signals_df` – alle generierten Signale
   - `actions_df` – Operator-Aktionen zu Signalen
   - `prices_df` – OHLCV-Preisfeed
4. Am Ende werden **automatisch zwei Reports** erzeugt:
   - **Offline-Paper-Report**: Performance-Metriken (PnL, Fees, Equity-Kurve)
   - **Trigger-Training-Report**: Psychologie-Metriken (Reaktionszeit, Missed Opportunities, FOMO, Rule-Breaks)

### Zweck

- **Operator-Training**: Neue Team-Mitglieder lernen Signal-Timing und Execution-Regeln
- **Reaktions-Analyse**: Identifikation von Schwachstellen (zu langsam, zu emotional, Regel-Verstöße)
- **Pain-Point-Analyse**: Quantifizierung verpasster Chancen (`pnl_after_bars` bei MISSED/LATE)

---

> ⚠️ **WICHTIG: KEIN LIVE-MODE**
>
> Dieser Drill ist **ausschließlich für Offline-/Paper-Training**. Es werden **keine echten Orders** platziert.
> Live-Sessions haben eigene Pipelines (siehe `PHASE_32_LIVE_RUN_REPORT.md`, `PHASE_57_LIVE_STATUS_REPORT.md`).

---

## 2. Voraussetzungen (Preflight)

### 2.1 Code & Tests

Stelle sicher, dass alle relevanten Tests grün sind:

```bash
# Preflight: Reporting + Trigger-Training-Tests
python3 -m pytest tests/reporting/test_offline_paper_trade_report.py \
                  tests/reporting/test_trigger_training_report.py \
                  tests/reporting/test_offline_paper_trade_integration.py \
                  tests/trigger_training/test_trigger_training_hooks.py -v
```

**Erwartetes Ergebnis**: Alle 4+ Tests `PASSED` (ohne Failures).

---

### 2.2 Dependencies

- ✅ **Matplotlib** installiert (für PNG-Plots in Reports)
- ✅ **Pandas** >= 1.3
- ✅ **Python** >= 3.9

---

### 2.3 Drill-Konfiguration

Du benötigst:

1. **Offline-Profil** (z.B. MA-Crossover auf BTCEUR/1m)
2. **Offline-Runner-Script** (z.B. `scripts/run_offline_realtime_ma_crossover.py`)

> 📝 **Hinweis**: Die genauen Script-Pfade hängen von deinem Setup ab. Dieser Runbook verwendet **Beispiel-Pfade**, die du anpassen musst.

---

### 2.4 Preflight-Checklist

- [ ] Alle Tests grün
- [ ] Offline-Profil existiert (Config in `config&#47;offline_profiles&#47;...` oder ähnlich)
- [ ] Runner-Script vorhanden und ausführbar
- [ ] Kraken-Cache oder Offline-Preisfeed verfügbar (für BTCEUR/1m)

---

## 3. Drill-Ablauf (Schritt-für-Schritt)

### Schritt 1: Drill-Profil wählen

Definiere die Parameter für deinen Drill:

| Parameter | Beispiel-Wert |
|-----------|---------------|
| **Symbol** | `BTCEUR` |
| **Timeframe** | `1m` |
| **Strategy** | `ma_crossover` |
| **Mode** | `offline_paper_trade` oder `offline_realtime` |
| **Duration** | z.B. 60 Minuten |

---

### Schritt 2: Offline-Session starten

Starte den Offline-Runner (anpassen an dein Setup):

```bash
# Beispiel – an das echte Script anpassen:
python3 scripts/run_offline_realtime_ma_crossover.py \
  --profile offline_btceur_1m_ma_crossover \
  --mode offline_paper_trade \
  --duration 60
```

**Was passiert intern**:

1. Script lädt historische Preisdaten (z.B. aus Kraken-Cache)
2. Strategie (MA-Crossover) generiert Signale
3. Operator (oder Sim-Bot) reagiert auf Signale → Actions werden geloggt
4. Trades werden ausgeführt (Paper-Mode) → PnL berechnet
5. Am Ende:
   - `trades_df` ist befüllt
   - `signals_df` ist befüllt
   - `actions_df` ist befüllt
   - `prices_df` ist befüllt

> 📝 **Hinweis**: Der Runner **muss** diese DataFrames am Ende bereitstellen, damit die Report-Pipeline funktioniert (siehe Schritt 3–4).

---

### Schritt 3: Trigger-Events aus DataFrames bauen

Nach dem Run (oder innerhalb des Runner-Scripts) werden die Events generiert:

```python
from src.trigger_training.hooks import (
    TriggerTrainingHookConfig,
    build_trigger_training_events_from_dfs,
)

# Konfiguration für Event-Klassifikation
hook_cfg = TriggerTrainingHookConfig(
    lookahead_bars=20,        # PnL nach 20 Bars
    late_threshold_s=5.0,     # > 5s Reaktionszeit = LATE
    pain_threshold=0.0,       # Pain-Point-Schwelle (0 = alle)
)

# Events generieren
trigger_events = build_trigger_training_events_from_dfs(
    signals=signals_df,
    actions=actions_df,
    prices=prices_df,
    config=hook_cfg,
)

print(f"✅ {len(trigger_events)} Trigger-Events generiert")
```

**Output-Beispiel**:

```
✅ 12 Trigger-Events generiert
```

---

### Schritt 4: Reports generieren

Jetzt werden beide Reports (Paper + Trigger) in einem Aufruf erzeugt:

```python
from pathlib import Path
import pandas as pd

from src.reporting.offline_paper_trade_integration import (
    OfflinePaperTradeReportConfig,
    generate_reports_for_offline_paper_trade,
)

# Report-Konfiguration
report_cfg = OfflinePaperTradeReportConfig(
    session_id=f"OFFLINE_BTCEUR_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}",
    environment="offline_paper_trade",
    symbol="BTCEUR",
    timeframe="1m",
    start_ts=start_ts,  # pd.Timestamp aus dem Run
    end_ts=end_ts,      # pd.Timestamp aus dem Run
    extra_meta={
        "strategy": "ma_crossover",
        "operator": "frank",  # oder aus ENV/Config
    },
    # base_reports_dir bleibt Default: Path("reports/offline_paper_trade")
)

# Beide Reports generieren
result_paths = generate_reports_for_offline_paper_trade(
    trades=trades_df,
    report_config=report_cfg,
    trigger_events=trigger_events,
    session_meta_for_trigger={
        "session_id": report_cfg.session_id,
        "mode": "offline_training",
        "strategy": "ma_crossover",
        "operator": "frank",
    },
)

print(f"[REPORT] Offline-Paper-Report:   {result_paths['paper_report']}")
if "trigger_report" in result_paths:
    print(f"[REPORT] Trigger-Training-Report: {result_paths['trigger_report']}")
```

**Output-Beispiel**:

```
[REPORT] Offline-Paper-Report:   reports/offline_paper_trade/OFFLINE_BTCEUR_20250110_103045/offline_paper_trade_report.html
[REPORT] Trigger-Training-Report: reports/offline_paper_trade/OFFLINE_BTCEUR_20250110_103045/trigger_training_report.html
```

---

### Schritt 5: Reports öffnen

Die Reports liegen in:

```
reports/offline_paper_trade/<session_id>/
  ├── offline_paper_trade_report.html
  └── trigger_training_report.html
```

**Im Browser öffnen**:

```bash
# macOS
open reports/offline_paper_trade/OFFLINE_BTCEUR_20250110_103045/offline_paper_trade_report.html

# Linux
xdg-open reports/offline_paper_trade/OFFLINE_BTCEUR_20250110_103045/offline_paper_trade_report.html
```

---

## 4. Erwartete Artefakte & Checks

### 4.1 Erwartete Artefakte

| Artefakt | Pfad | Inhalt |
|----------|------|--------|
| **Offline-Paper-Report** | `offline_paper_trade_report.html` | PnL, Fees, Equity-Kurve, Trade-Liste, Win-Rate |
| **Trigger-Training-Report** | `trigger_training_report.html` | Outcome-Verteilung (HIT/MISSED/LATE/FOMO/RULE_BREAK), Reaktionszeiten, Pain-Points, Tag-Analyse |

---

### 4.2 Operator-Checklist

Nach dem Drill prüfe:

- [ ] **Report-Dateien existieren** (beide HTML-Dateien)
- [ ] **Offline-Paper-Report** zeigt sinnvolle PnL-Werte (nicht nur 0.0)
- [ ] **Trigger-Report** zeigt Outcome-Verteilung (mindestens eine Kategorie > 0)
- [ ] **Pain-Points** werden angezeigt (wenn es verpasste Chancen gab)
- [ ] **Tags** wie `missed_opportunity`, `late_entry`, `rule_follow` sind vorhanden
- [ ] **Reaktionszeiten** sind plausibel (z.B. 0.5s–10s, nicht 0.0s für alle)

---

### 4.3 Report-Inhalt im Detail

#### Offline-Paper-Report

| Abschnitt | Inhalt |
|-----------|--------|
| **Session Meta** | Session-ID, Symbol, Timeframe, Start/End |
| **Summary** | Total PnL, Fees, Trade-Count |
| **Equity Curve** | PNG-Plot der kumulativen PnL |
| **Trade Details** | Tabelle mit einzelnen Trades |

#### Trigger-Training-Report

| Abschnitt | Inhalt |
|-----------|--------|
| **Session Meta** | Session-ID, Mode, Operator |
| **Outcome Summary** | Anzahl HIT/MISSED/LATE/FOMO/RULE_BREAK/OTHER |
| **Reaction Time Stats** | Mean, Median, P95 Reaktionszeit |
| **Pain Points** | Events mit hohem `pnl_after_bars` (verpasste Chancen) |
| **Tag Analysis** | Häufigkeit von `missed_opportunity`, `late_entry`, etc. |
| **Event Table** | Alle Events mit Timestamp, Symbol, Action, Outcome, PnL |

---

## 5. Troubleshooting

### Problem 1: Kein Trigger-Report erzeugt

**Symptom**: `result_paths` enthält nur `paper_report`, kein `trigger_report`.

**Ursache**: `trigger_events` war leer oder `None`.

**Lösung**:

1. Prüfe, ob `signals_df` und `actions_df` wirklich befüllt werden:

   ```python
   print(f"Signals: {len(signals_df)} rows")
   print(f"Actions: {len(actions_df)} rows")
   ```

2. Falls `signals_df` leer ist: Runner erzeugt keine Signale → Strategie-Config prüfen.
3. Falls `actions_df` leer ist: Operator/Sim-Bot reagiert nicht → Action-Logik prüfen.

---

### Problem 2: `pnl_after_bars` = 0 für alle Events

**Symptom**: Trigger-Report zeigt überall `pnl_after_bars = 0.0`.

**Ursache**: `prices_df` fehlt `close`-Spalte, falscher Index oder Symbol-Filter.

**Lösung**:

1. Prüfe Schema von `prices_df`:

   ```python
   print(prices_df.columns)  # muss 'close' enthalten
   print(prices_df.index)    # DatetimeIndex ODER 'timestamp'-Spalte
   ```

2. Falls `symbol`-Spalte vorhanden: prüfe, ob Symbol übereinstimmt (`BTCEUR` vs. `BTC&#47;EUR`).
3. Fallback: In `TriggerTrainingHookConfig` `lookahead_bars=0` setzen (deaktiviert PnL-Calc).

---

### Problem 3: Reports ohne Equity-Kurve / Plots

**Symptom**: HTML-Reports enthalten keine PNG-Bilder.

**Ursache 1**: Matplotlib fehlt oder nicht korrekt installiert.

**Lösung**: `python3 -m pip install matplotlib`

**Ursache 2**: `trades_df` hat keine `pnl`-Spalte.

**Lösung**: PnL-Berechnung im Runner ergänzen oder (v0) akzeptieren, dass Plots fehlen.

---

### Problem 4: Alle Outcomes = `MISSED`

**Symptom**: Trigger-Report zeigt 100% `MISSED`, keine `HIT`.

**Ursache**: `actions_df` hat keine passenden `signal_id`-Referenzen.

**Lösung**:

1. Prüfe `signal_id`-Spalte in beiden DataFrames:

   ```python
   print(signals_df["signal_id"].unique())
   print(actions_df["signal_id"].unique())
   ```

2. Falls keine Übereinstimmung: Runner-Logik für Signal-Action-Mapping prüfen.

---

### Problem 5: Outcome-Klassifikation falsch

**Symptom**: Events mit 1s Reaktionszeit werden als `LATE` klassifiziert.

**Ursache**: `late_threshold_s` ist zu niedrig (z.B. 0.5s).

**Lösung**:

```python
hook_cfg = TriggerTrainingHookConfig(
    late_threshold_s=5.0,  # auf 5s erhöhen
)
```

---

## 6. Quick-Commands (Cheat Sheet)

### Preflight

```bash
# Tests ausführen
python3 -m pytest tests/reporting/test_offline_paper_trade_report.py \
                  tests/reporting/test_trigger_training_report.py \
                  tests/reporting/test_offline_paper_trade_integration.py \
                  tests/trigger_training/test_trigger_training_hooks.py -v
```

---

### Drill starten (Beispiel – anpassen!)

```bash
# Offline-Realtime-Drill (Beispiel-Pfad)
python3 scripts/run_offline_realtime_ma_crossover.py \
  --profile offline_btceur_1m_ma_crossover \
  --mode offline_paper_trade \
  --duration 60

# Alternativ: Python-Script mit direktem Report-Call
# Alternativ: Trigger-Training Drill Example Script (Repo vorhanden; benötigt Session-Daten-Anbindung)
python3 scripts/run_offline_trigger_training_drill_example.py
```

---

### Quick Python-Snippets

#### Import-Block (Copy-Paste)

```python
from pathlib import Path
import pandas as pd

from src.trigger_training.hooks import (
    TriggerTrainingHookConfig,
    build_trigger_training_events_from_dfs,
)
from src.reporting.offline_paper_trade_integration import (
    OfflinePaperTradeReportConfig,
    generate_reports_for_offline_paper_trade,
)
```

---

#### Minimal-Setup (nur Paper-Report)

```python
cfg = OfflinePaperTradeReportConfig(
    session_id="MY_SESSION",
    environment="offline_paper_trade",
    symbol="BTCEUR",
    timeframe="1m",
    start_ts=pd.Timestamp("2025-01-01T10:00:00Z"),
    end_ts=pd.Timestamp("2025-01-01T11:00:00Z"),
)

result = generate_reports_for_offline_paper_trade(trades_df, cfg)
print(result["paper_report"])
```

---

#### Full-Setup (Paper + Trigger)

```python
# 1. Events generieren
hook_cfg = TriggerTrainingHookConfig(lookahead_bars=20, late_threshold_s=5.0)
events = build_trigger_training_events_from_dfs(signals_df, actions_df, prices_df, hook_cfg)

# 2. Reports generieren
cfg = OfflinePaperTradeReportConfig(...)  # siehe oben
result = generate_reports_for_offline_paper_trade(
    trades_df, cfg, trigger_events=events
)

print(result["paper_report"])
print(result["trigger_report"])
```

---

## 7. Verwandte Runbooks & Dokumentation

| Dokument | Relevanz |
|----------|----------|
| `TRIGGER_TRAINING_REPORTS_V1.md` | Technische Details zu Reports & Hooks |
| `OFFLINE_REALTIME_PIPELINE_RUNBOOK_V1.md` | Offline-Realtime-Pipeline (Preisfeed, Simulation) |
| `PHASE_16A_EXECUTION_PIPELINE_V2.md` | Execution-Pipeline-Context |
| `PHASE_32_LIVE_RUN_REPORT.md` | Live-Session-Reports (unterschiedlich zu Offline) |
| `R_AND_D_PLAYBOOK_ARMSTRONG_EL_KAROUI_V1.md` | Strategie-Entwicklung & Backtesting |

---

## 8. Anhang: DataFrame-Schema (Quick-Ref)

### `trades_df`

```python
trades_df = pd.DataFrame({
    "pnl": [10.0, -5.0, 8.0],       # Pflicht
    "fees": [0.1, 0.1, 0.15],       # Optional
})
```

### `signals_df`

```python
signals_df = pd.DataFrame({
    "signal_id": [1, 2, 3],                           # Optional (wird auto-generiert)
    "timestamp": [ts1, ts2, ts3],                     # Pflicht (pd.Timestamp)
    "symbol": ["BTCEUR", "BTCEUR", "BTCEUR"],         # Pflicht
    "signal_state": [1, -1, 0],                       # Pflicht (-1/0/1)
    "recommended_action": ["ENTER_LONG", "ENTER_SHORT", "EXIT_LONG"],  # Pflicht
})
```

### `actions_df`

```python
actions_df = pd.DataFrame({
    "signal_id": [1, 3],                              # Pflicht (Referenz zu signals_df)
    "timestamp": [ts1_action, ts3_action],            # Pflicht (pd.Timestamp)
    "user_action": ["EXECUTED", "EXECUTED"],          # Pflicht
    "note": ["Quick reaction", ""],                   # Optional
})
```

### `prices_df`

```python
prices_df = pd.DataFrame({
    "timestamp": pd.date_range("2025-01-01T10:00:00Z", periods=60, freq="1min"),
    "close": [50000.0, 50010.0, ...],                 # Pflicht
    "symbol": ["BTCEUR"] * 60,                        # Optional (für Multi-Symbol)
})
```

---

## 9. Operator-Feedback & Iteration

Nach jedem Drill:

1. **Reports analysieren** (5–10 Minuten)
2. **Pain-Points identifizieren** (MISSED/LATE mit hohem `pnl_after_bars`)
3. **Feedback dokumentieren** (z.B. in Slack `#ops-training`)
4. **Next-Drill planen** (fokussiert auf Schwachstellen)

**Ziel**: Nach 5–10 Drills sollte sich die MISSED-Rate um 30%+ reduzieren und die durchschnittliche Reaktionszeit auf <3s sinken.

---

**Version**: v0 (2025-12-10)  
**Next Review**: Nach 10 Operator-Drills mit strukturiertem Feedback

---

## 10. Kontakt & Support

Bei Fragen oder Problemen:

- **Slack**: `#peak-trade-reporting` oder `#ops-training`
- **Issues**: GitHub Issues mit Label `runbook` + `trigger-training`
- **Docs**: `docs/trigger_training/TRIGGER_TRAINING_REPORTS_V1.md` (technische Details)
