# Trigger-Training & Offline-Paper-Reports – v0

## Meta

| Attribut | Wert |
|----------|------|
| **Status** | `EXPERIMENTAL / v0` |
| **Scope** | Offline-Paper-Trade, Offline-Realtime-Drills |
| **Owner** | Peak_Trade Reporting Team |
| **Created** | 2025-12-10 |
| **Phase** | Phase 16D Extension – Execution Training |

### Module

| Modul | Zweck |
|-------|-------|
| `src/reporting/offline_paper_trade_report.py` | HTML-Report für Offline-Paper-Trade-Sessions (Performance/Execution) |
| `src/reporting/trigger_training_report.py` | HTML-Report für Trigger-Training (Psychologie/Reaktion) |
| `src/reporting/offline_paper_trade_integration.py` | Zentraler Entry-Point für kombinierte Reports |
| `src/trigger_training/hooks.py` | Automatische Event-Generierung aus DataFrames |

### Reports Output

| Report-Typ | Pfad |
|------------|------|
| **Offline Paper Trade Report** | `reports/offline_paper_trade/<session_id>/offline_paper_trade_report.html` |
| **Trigger Training Report** | `reports/offline_paper_trade/<session_id>/trigger_training_report.html` |

---

## 1. Überblick / Motivation

### Warum zwei Perspektiven?

Bei Offline-Paper-Trading und Offline-Realtime-Drills sammeln wir zwei fundamental unterschiedliche Datenströme:

#### 1.1 Performance/Execution-Sicht (Offline-Paper-Report)

- **Fokus**: Quantitative Metriken (PnL, Fees, Trade-Count, Win-Rate, etc.)
- **Zweck**: Objektive Bewertung der Session-Performance
- **Frage**: "Wie profitabel war die Session?"

#### 1.2 Psychologische Sicht (Trigger-Training-Report)

- **Fokus**: Mensch-Signal-Interaktion (Reaktionszeit, Missed Opportunities, FOMO, Rule-Breaks)
- **Zweck**: Training von Trigger-Disziplin und Operator-Hygiene
- **Frage**: "Wie gut habe ich auf Signale reagiert?"

### Typische Einsatzfälle

| Use-Case | Beschreibung |
|----------|--------------|
| **Offline-Realtime-Drills** | Operator trainiert mit Live-Preisfeed (offline), Reports zeigen sofort Schwachstellen |
| **Operator-Training** | Neue Team-Mitglieder lernen Signal-Timing und Execution-Regeln |
| **Post-Session-Analysis** | Analyse von MISSED/LATE-Signalen mit hohem `pnl_after_bars` ("Pain Points") |
| **Rule-Compliance** | Identifikation von FOMO- und RULE_BREAK-Events zur Prozessverbesserung |

**v0-Scope**: Diese Reports sind für **Offline-Sessions** (Paper-Trade, Realtime-Drills) gedacht. Live-Sessions haben eigene Report-Pipelines (Phase 32, 57, 81).

---

## 2. Datenquellen & DataFrame-Schemata

### 2.1 `trades_df` (für Offline-Paper-Report)

**Zweck**: Quantitative Trade-Daten für Performance-Metriken.

| Spalte | Typ | Pflicht | Beschreibung |
|--------|-----|---------|--------------|
| `pnl` | `float` | ✅ Ja | Profit/Loss pro Trade |
| `fees` | `float` | ❌ Optional | Transaktionskosten (falls verfügbar) |

**Hinweis**: Das v0-Schema ist bewusst minimal. Weitere Spalten (z.B. `entry_price`, `exit_price`, `size`, `duration`) werden in v1+ unterstützt.

**Beispiel**:

```python
trades_df = pd.DataFrame({
    "pnl": [10.0, -5.0, 3.5, 8.2],
    "fees": [0.1, 0.2, 0.1, 0.15],
})
```

---

### 2.2 `signals_df` (für Trigger-Hooks)

**Zweck**: Alle Trading-Signale, die während der Session generiert wurden.

| Spalte | Typ | Pflicht | Beschreibung |
|--------|-----|---------|--------------|
| `signal_id` | `int` | ❌ Optional | Eindeutige ID (wenn fehlt: wird aus Index erzeugt) |
| `timestamp` | `datetime64` | ✅ Ja | Zeitpunkt des Signals |
| `symbol` | `str` | ✅ Ja | Trading-Symbol (z.B. `BTCEUR`) |
| `signal_state` | `int` | ✅ Ja | Signal-Status (z.B. `-1` = Short, `0` = Neutral, `1` = Long) |
| `recommended_action` | `str` | ✅ Ja | Empfohlene Aktion (z.B. `ENTER_LONG`, `EXIT_LONG`, `ENTER_SHORT`) |

**Hinweis**: Wenn `signal_id` fehlt, wird v0 automatisch eine ID aus dem DataFrame-Index erzeugen.

**Beispiel**:

```python
signals_df = pd.DataFrame({
    "signal_id": [1, 2, 3],
    "timestamp": [
        pd.Timestamp("2025-01-01T10:00:00Z"),
        pd.Timestamp("2025-01-01T10:05:00Z"),
        pd.Timestamp("2025-01-01T10:10:00Z"),
    ],
    "symbol": ["BTCEUR", "BTCEUR", "BTCEUR"],
    "signal_state": [1, 0, -1],
    "recommended_action": ["ENTER_LONG", "EXIT_LONG", "ENTER_SHORT"],
})
```

---

### 2.3 `actions_df` (für Trigger-Hooks)

**Zweck**: User-Aktionen zu Signalen (Manual-Execution, Skipped, etc.).

| Spalte | Typ | Pflicht | Beschreibung |
|--------|-----|---------|--------------|
| `signal_id` | `int` | ✅ Ja | Referenz zu `signals_df.signal_id` |
| `timestamp` | `datetime64` | ✅ Ja | Zeitpunkt der User-Aktion |
| `user_action` | `str` | ✅ Ja | Freier String (z.B. `EXECUTED`, `SKIPPED`, `EXECUTED_FOMO`) |
| `note` | `str` | ❌ Optional | Zusätzliche Notiz (z.B. "Too slow, missed entry") |

**Hinweis**: Wenn mehrere Aktionen zu einem `signal_id` existieren, verwendet v0 die **erste Aktion** (sortiert nach `timestamp`).

**Beispiel**:

```python
actions_df = pd.DataFrame({
    "signal_id": [1, 3],
    "timestamp": [
        pd.Timestamp("2025-01-01T10:00:01Z"),  # 1s nach Signal
        pd.Timestamp("2025-01-01T10:10:03Z"),  # 3s nach Signal
    ],
    "user_action": ["EXECUTED", "EXECUTED"],
    "note": ["Quick reaction", "Slightly late"],
})
```

---

### 2.4 `prices_df` (für Trigger-Hooks)

**Zweck**: OHLCV-Daten zur PnL-Berechnung (Lookahead für `pnl_after_bars`).

| Spalte | Typ | Pflicht | Beschreibung |
|--------|-----|---------|--------------|
| `timestamp` | `datetime64` | ✅ Ja* | Zeitstempel (oder DatetimeIndex) |
| `close` | `float` | ✅ Ja | Close-Price |
| `symbol` | `str` | ❌ Optional | Symbol (für Multi-Symbol-Sessions) |

**\*Hinweis**: Wenn der DataFrame bereits einen `DatetimeIndex` hat, wird keine separate `timestamp`-Spalte benötigt.

**Beispiel**:

```python
prices_df = pd.DataFrame({
    "timestamp": pd.date_range("2025-01-01T10:00:00Z", periods=100, freq="1min"),
    "close": [50000.0, 50010.0, 50020.0, ...],
    "symbol": ["BTCEUR"] * 100,
})
```

---

## 3. Technische Module & Entry-Points

### 3.1 Offline-Paper-Trade-Report

#### Modul: `src/reporting/offline_paper_trade_report.py`

**Zweck**: Generiert HTML-Report mit Trade-Performance-Metriken.

**Hauptklassen**:

- `OfflinePaperTradeSessionMeta`: Dataclass für Session-Metadaten
- `build_offline_paper_trade_report(trades, meta, output_dir)`: Funktion zur Report-Erstellung

**Parameter**:

| Parameter | Typ | Beschreibung |
|-----------|-----|--------------|
| `trades` | `pd.DataFrame` | Trade-Daten (siehe Schema 2.1) |
| `meta` | `OfflinePaperTradeSessionMeta` | Session-Metadaten (ID, Symbol, Timeframe, Start/End) |
| `output_dir` | `Path` | Zielverzeichnis für HTML-Report |

**Output**: Pfad zur generierten HTML-Datei (`offline_paper_trade_report.html`)

---

### 3.2 Trigger-Training-Report

#### Modul: `src/reporting/trigger_training_report.py`

**Zweck**: Generiert HTML-Report mit Trigger-Disziplin-Metriken (Reaction-Time, Outcomes, Pain-Points).

**Hauptklassen**:

- `TriggerOutcome`: Enum (`HIT`, `MISSED`, `LATE`, `FOMO`, `RULE_BREAK`, `OTHER`)
- `TriggerTrainingEvent`: Dataclass für ein einzelnes Signal+Action-Event
- `build_trigger_training_report(events, output_dir, session_meta)`: Funktion zur Report-Erstellung

**Parameter**:

| Parameter | Typ | Beschreibung |
|-----------|-----|--------------|
| `events` | `List[TriggerTrainingEvent]` | Liste von Trigger-Events |
| `output_dir` | `Path` | Zielverzeichnis für HTML-Report |
| `session_meta` | `Mapping[str, Any]` | Optional: Session-Metadaten für Report-Header |

**Output**: Pfad zur generierten HTML-Datei (`trigger_training_report.html`)

---

### 3.3 Offline-Paper-Trade-Integration (Entry-Point)

#### Modul: `src/reporting/offline_paper_trade_integration.py`

**Zweck**: Zentraler Entry-Point, der **beide** Reports in einem Aufruf erzeugt.

**Hauptklassen**:

- `OfflinePaperTradeReportConfig`: Dataclass für Report-Konfiguration
- `generate_reports_for_offline_paper_trade(trades, report_config, trigger_events, session_meta_for_trigger)`: Zentrale Funktion

**Parameter**:

| Parameter | Typ | Beschreibung |
|-----------|-----|--------------|
| `trades` | `pd.DataFrame` | Trade-Daten |
| `report_config` | `OfflinePaperTradeReportConfig` | Konfig (Session-ID, Symbol, Timeframe, etc.) |
| `trigger_events` | `Optional[List[TriggerTrainingEvent]]` | Events (wenn vorhanden -> Trigger-Report wird erzeugt) |
| `session_meta_for_trigger` | `Optional[Mapping[str, Any]]` | Meta für Trigger-Report |

**Output**: Dictionary mit Pfaden:

```python
{
    "paper_report": Path("reports/.../offline_paper_trade_report.html"),
    "trigger_report": Path("reports/.../trigger_training_report.html"),  # optional
}
```

---

### 3.4 Trigger-Training-Hooks

#### Modul: `src/trigger_training/hooks.py`

**Zweck**: Automatische Event-Generierung aus DataFrames (`signals_df`, `actions_df`, `prices_df`).

**Hauptklassen**:

- `TriggerTrainingHookConfig`: Dataclass für Hook-Konfiguration
- `build_trigger_training_events_from_dfs(signals, actions, prices, config)`: Hauptfunktion

**Parameter (Config)**:

| Parameter | Typ | Default | Beschreibung |
|-----------|-----|---------|--------------|
| `lookahead_bars` | `int` | `20` | Anzahl Bars für PnL-Lookahead |
| `late_threshold_s` | `float` | `5.0` | Ab dieser Reaktionszeit gilt Signal als `LATE` |
| `pain_threshold` | `float` | `0.0` | Schwelle für "Pain Point"-Tagging (bei `pnl_after_bars > threshold`) |

**Output**: `List[TriggerTrainingEvent]`

---

## 4. Trigger-Training-Logik (Heuristiken)

### 4.1 Outcome-Klassifikation

Die v0-Logik klassifiziert jedes Signal+Action-Paar in folgende Kategorien:

| Outcome | Bedingung | Beschreibung |
|---------|-----------|--------------|
| `HIT` | Aktion vorhanden, Reaktionszeit ≤ `late_threshold_s` | **Erfolg**: Signal wurde rechtzeitig ausgeführt |
| `MISSED` | Keine Aktion zu diesem Signal | **Fehler**: Signal wurde komplett ignoriert |
| `LATE` | Aktion vorhanden, Reaktionszeit > `late_threshold_s` | **Verzögert**: Zu langsame Reaktion |
| `FOMO` | `user_action` enthält String `"FOMO"` | **Psycho**: Emotion-getriebene Aktion |
| `RULE_BREAK` | `user_action` enthält `"RULE_BREAK"`, `"OVERSIZE"`, etc. | **Disziplin**: Regelverstoß (z.B. zu große Position) |
| `OTHER` | Keines der obigen | **Unbekannt**: Fallback-Kategorie |

**Reaktionszeit** = `(action_timestamp - signal_timestamp).total_seconds()`

---

### 4.2 PnL-Betrachtung (`pnl_after_bars`)

**Zweck**: Quantifiziert, wie viel PnL man "verpasst" hätte (bei MISSED/LATE) oder "gewonnen" hätte (bei HIT).

**Berechnung**:

1. Finde `close[t]` zum Signal-Zeitpunkt `t`
2. Finde `close[t + lookahead_bars]` nach N Bars
3. Berechne Delta: `(close[t + lookahead_bars] - close[t]) * direction`
   - `direction = +1.0` für `ENTER_LONG` / `OPEN_LONG`
   - `direction = -1.0` für `ENTER_SHORT` / `OPEN_SHORT`
   - `direction = 0.0` für Exits/Neutralität (v0: kein PnL)

**Hinweis**: Dies ist eine **vereinfachte v0-Heuristik**. Es wird keine Positionsgröße, kein Leverage, keine Fees berücksichtigt. Zweck ist rein qualitativ: "Wie groß war die Chance?"

---

### 4.3 Tagging

Events werden automatisch getaggt, um "Pain Points" hervorzuheben:

| Tag | Bedingung | Bedeutung |
|-----|-----------|-----------|
| `rule_follow` | `outcome == HIT` | Positive Bestätigung: Signal wurde korrekt ausgeführt |
| `missed_opportunity` | `outcome == MISSED` AND `pnl_after_bars > pain_threshold` | **Schmerzhaft**: Signal ignoriert, aber hätte Profit gebracht |
| `late_entry` | `outcome == LATE` AND `pnl_after_bars > pain_threshold` | **Schmerzhaft**: Zu langsam reagiert, Profit reduziert |

**Zweck**: Ermöglicht Filterung im Report (z.B. "Zeige mir nur die teuren Fehler").

---

## 5. How-To: Integration in Offline-Paper-Trade / Offline-Realtime

### 5.1 Workflow (6 Schritte)

1. **Offline-Run durchführen**  
   - Offline-Paper-Trade oder Offline-Realtime-Drill mit deiner Strategie/Profil
   - Am Ende: `trades_df`, `signals_df`, `actions_df`, `prices_df` befüllt

2. **Trigger-Hook-Config definieren**  
   - Lege fest: `lookahead_bars`, `late_threshold_s`, `pain_threshold`

3. **Events generieren**  
   - `build_trigger_training_events_from_dfs(signals, actions, prices, config)`

4. **Report-Config erstellen**  
   - `OfflinePaperTradeReportConfig` mit Session-ID, Symbol, Timeframe, etc.

5. **Reports generieren**  
   - `generate_reports_for_offline_paper_trade(trades, config, trigger_events, ...)`

6. **Reports öffnen**  
   - HTML-Dateien in Browser öffnen und analysieren

---

### 5.2 Code-Beispiele

#### Beispiel A: Nur Offline-Paper-Report (ohne Trigger-Events)

```python
from pathlib import Path
import pandas as pd

from src.reporting.offline_paper_trade_integration import (
    OfflinePaperTradeReportConfig,
    generate_reports_for_offline_paper_trade,
)

# Trade-Daten aus deiner Session
trades_df = pd.DataFrame({
    "pnl": [12.5, -3.2, 8.0, -1.5, 15.0],
    "fees": [0.1, 0.1, 0.15, 0.1, 0.2],
})

# Report-Konfiguration
report_cfg = OfflinePaperTradeReportConfig(
    session_id="OFFLINE_BTCEUR_2025_01_01_SESSION_001",
    environment="offline_paper_trade",
    symbol="BTCEUR",
    timeframe="1m",
    start_ts=pd.Timestamp("2025-01-01T10:00:00Z"),
    end_ts=pd.Timestamp("2025-01-01T12:00:00Z"),
    extra_meta={"strategy": "MA_Crossover", "operator": "frank"},
)

# Reports generieren (nur Paper-Report, keine Trigger-Events)
result_paths = generate_reports_for_offline_paper_trade(
    trades=trades_df,
    report_config=report_cfg,
)

print(f"✅ Paper-Report: {result_paths['paper_report']}")
# Output: reports/offline_paper_trade/OFFLINE_BTCEUR_2025_01_01_SESSION_001/offline_paper_trade_report.html
```

---

#### Beispiel B: Offline-Paper-Report + Trigger-Training-Report

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

# 1. Trade-Daten
trades_df = pd.DataFrame({
    "pnl": [12.5, -3.2, 8.0],
    "fees": [0.1, 0.1, 0.15],
})

# 2. Signals-Daten
signals_df = pd.DataFrame({
    "signal_id": [1, 2, 3],
    "timestamp": [
        pd.Timestamp("2025-01-01T10:00:00Z"),
        pd.Timestamp("2025-01-01T10:15:00Z"),
        pd.Timestamp("2025-01-01T10:30:00Z"),
    ],
    "symbol": ["BTCEUR", "BTCEUR", "BTCEUR"],
    "signal_state": [1, -1, 1],
    "recommended_action": ["ENTER_LONG", "ENTER_SHORT", "ENTER_LONG"],
})

# 3. Actions-Daten (Signal 2 wurde verpasst!)
actions_df = pd.DataFrame({
    "signal_id": [1, 3],
    "timestamp": [
        pd.Timestamp("2025-01-01T10:00:02Z"),  # 2s Reaktionszeit
        pd.Timestamp("2025-01-01T10:30:01Z"),  # 1s Reaktionszeit
    ],
    "user_action": ["EXECUTED", "EXECUTED"],
    "note": ["Quick", "Very quick"],
})

# 4. Price-Daten
prices_df = pd.DataFrame({
    "timestamp": pd.date_range("2025-01-01T10:00:00Z", periods=60, freq="1min"),
    "close": [50000.0 + i * 10.0 for i in range(60)],  # Steigender Trend
    "symbol": ["BTCEUR"] * 60,
})

# 5. Hook-Config
hook_cfg = TriggerTrainingHookConfig(
    lookahead_bars=10,
    late_threshold_s=5.0,
    pain_threshold=50.0,  # Nur "teure" Fehler taggen
)

# 6. Events generieren
trigger_events = build_trigger_training_events_from_dfs(
    signals=signals_df,
    actions=actions_df,
    prices=prices_df,
    config=hook_cfg,
)

# 7. Report-Config
report_cfg = OfflinePaperTradeReportConfig(
    session_id="OFFLINE_BTCEUR_2025_01_01_SESSION_002",
    environment="offline_realtime_drill",
    symbol="BTCEUR",
    timeframe="1m",
    start_ts=pd.Timestamp("2025-01-01T10:00:00Z"),
    end_ts=pd.Timestamp("2025-01-01T11:00:00Z"),
    extra_meta={"strategy": "MA_Crossover", "operator": "frank"},
)

# 8. Beide Reports generieren
result_paths = generate_reports_for_offline_paper_trade(
    trades=trades_df,
    report_config=report_cfg,
    trigger_events=trigger_events,
    session_meta_for_trigger={
        "session_id": report_cfg.session_id,
        "mode": "offline_training",
        "operator": "frank",
    },
)

print(f"✅ Paper-Report:   {result_paths['paper_report']}")
print(f"✅ Trigger-Report: {result_paths['trigger_report']}")

# Output:
# ✅ Paper-Report:   reports/offline_paper_trade/.../offline_paper_trade_report.html
# ✅ Trigger-Report: reports/offline_paper_trade/.../trigger_training_report.html
```

---

## 6. Limitierungen & Roadmap (v1+)

### 6.1 Bekannte Limitierungen (v0)

| Limitation | Beschreibung | Workaround |
|------------|--------------|------------|
| **PnL-Heuristik** | Keine Positionsgrößen, Fees, Leverage, Partial Fills | Für v0 nur qualitative Aussage: "Richtung war richtig/falsch" |
| **`user_action` Format** | Freier String, keine Konventionen | Team muss sich auf Keywords einigen (z.B. `EXECUTED`, `SKIPPED`, `EXECUTED_FOMO`) |
| **Multi-Action-Support** | Nur erste Aktion pro `signal_id` wird verwendet | v0: In `actions_df` nur relevanteste Aktion eintragen |
| **Preisfeed-Matching** | Simples Index-Matching, keine Interpolation | Sicherstellen, dass `prices_df` dense/vollständig ist |
| **Outcome-Klassifikation** | String-basierte Heuristiken (FOMO, RULE_BREAK) | Keywords in `user_action` standardisieren |
| **Symbol-Filtering** | Optional, aber nicht gut getestet bei Multi-Symbol-Sessions | v0: Ein Symbol pro Session |

---

### 6.2 Roadmap (v1+)

#### v1: PnL-Verbesserungen

- [ ] **Positionsgrößen-Modell**: `pnl_after_bars` berücksichtigt `size`, `leverage`
- [ ] **Fees-Integration**: Realistische PnL inkl. Maker/Taker-Fees
- [ ] **Partial Fills**: Multi-Action-Support für gestückelte Entries/Exits

#### v2: Outcome-Erweiterungen

- [ ] **Mehr Outcomes**: `EARLY_EXIT`, `STOP_LOSS_HIT`, `TAKE_PROFIT_HIT`
- [ ] **Regelwerk-Integration**: Automatische `RULE_BREAK`-Detektion (z.B. `size > max_size`)
- [ ] **Custom Tags**: User-definierte Tags im DataFrame (z.B. `emotion=fear`, `fatigue=high`)

#### v3: Multi-Session-Analysis

- [ ] **Aggregierte Reports**: Mehrere Sessions vergleichen (z.B. "Woche 1 vs. Woche 2")
- [ ] **Progress-Tracking**: "Deine MISSED-Rate hat sich um 30% verbessert"
- [ ] **Leaderboard**: Team-weite Trigger-Disziplin-Scores

#### v4: Live-Integration

- [ ] **Live-Trigger-Reports**: Auch für Live-Sessions (nicht nur Offline)
- [ ] **Real-Time-Alerts**: Slack/Discord-Notification bei RULE_BREAK/FOMO
- [ ] **Feedback-Loop**: Trigger-Training-Report → Live-Operator-Console

---

## 7. Quick-Ref (Copy-Paste Snippets)

### 7.1 Minimal-Setup (nur Paper-Report)

```python
from src.reporting.offline_paper_trade_integration import (
    OfflinePaperTradeReportConfig,
    generate_reports_for_offline_paper_trade,
)
import pandas as pd

trades = pd.DataFrame({"pnl": [10, -5, 8], "fees": [0.1, 0.1, 0.1]})
cfg = OfflinePaperTradeReportConfig(
    session_id="MY_SESSION",
    environment="offline_paper_trade",
    symbol="BTCEUR",
    timeframe="1m",
    start_ts=pd.Timestamp("2025-01-01T10:00:00Z"),
    end_ts=pd.Timestamp("2025-01-01T11:00:00Z"),
)
result = generate_reports_for_offline_paper_trade(trades, cfg)
print(result["paper_report"])
```

---

### 7.2 Full-Setup (Paper + Trigger)

```python
from src.trigger_training.hooks import (
    TriggerTrainingHookConfig,
    build_trigger_training_events_from_dfs,
)
from src.reporting.offline_paper_trade_integration import (
    OfflinePaperTradeReportConfig,
    generate_reports_for_offline_paper_trade,
)
import pandas as pd

# DataFrames (siehe Abschnitt 2 für Schema)
trades_df = pd.DataFrame({"pnl": [10, -5, 8], "fees": [0.1, 0.1, 0.1]})
signals_df = pd.DataFrame({...})  # siehe Beispiel B
actions_df = pd.DataFrame({...})
prices_df = pd.DataFrame({...})

# Events generieren
hook_cfg = TriggerTrainingHookConfig(lookahead_bars=20, late_threshold_s=5.0)
events = build_trigger_training_events_from_dfs(signals_df, actions_df, prices_df, hook_cfg)

# Reports generieren
cfg = OfflinePaperTradeReportConfig(...)  # siehe 7.1
result = generate_reports_for_offline_paper_trade(trades_df, cfg, trigger_events=events)
print(result["paper_report"])
print(result["trigger_report"])
```

---

### 7.3 DataFrame-Schema (Copy-Paste-Template)

```python
import pandas as pd

# Trades
trades_df = pd.DataFrame({
    "pnl": [...],
    "fees": [...],
})

# Signals
signals_df = pd.DataFrame({
    "signal_id": [...],
    "timestamp": [...],  # pd.Timestamp
    "symbol": [...],
    "signal_state": [...],  # -1, 0, 1
    "recommended_action": [...],  # "ENTER_LONG", "EXIT_LONG", ...
})

# Actions
actions_df = pd.DataFrame({
    "signal_id": [...],
    "timestamp": [...],  # pd.Timestamp
    "user_action": [...],  # "EXECUTED", "SKIPPED", "EXECUTED_FOMO", ...
    "note": [...],  # optional
})

# Prices
prices_df = pd.DataFrame({
    "timestamp": [...],  # pd.Timestamp
    "close": [...],
    "symbol": [...],  # optional
})
```

---

## 8. Anhang

### 8.1 Verwandte Dokumentation

| Dokument | Relevanz |
|----------|----------|
| `PHASE_16A_EXECUTION_PIPELINE_V2.md` | Execution-Pipeline-Context |
| `PHASE_16D_EXECUTION_REPORTS.md` | Execution-Stats-Basis |
| `PHASE_32_LIVE_RUN_REPORT.md` | Live-Session-Reports (unterschiedlich zu Offline) |
| `PHASE_57_LIVE_STATUS_REPORT.md` | Live-Status-Reporting |
| `OFFLINE_REALTIME_PIPELINE_RUNBOOK_V1.md` | Offline-Realtime-Drill-Workflow |

### 8.2 Test-Locations

- **Reports**: `tests/reporting/test_offline_paper_trade_report.py`
- **Reports**: `tests/reporting/test_trigger_training_report.py`
- **Integration**: `tests/reporting/test_offline_paper_trade_integration.py`
- **Hooks**: `tests/trigger_training/test_trigger_training_hooks.py`

### 8.3 Kontakt & Support

Bei Fragen oder Feature-Requests:

- **Slack**: `#peak-trade-reporting` (oder `#ops-training`)
- **Issues**: GitHub Issues mit Label `reporting` + `trigger-training`

---

**Version**: v0 (2025-12-10)  
**Next Review**: Nach 10 Offline-Realtime-Sessions mit Operator-Feedback

