# R&D Operator-Flow – Experimente einsehen & analysieren

**Zielgruppe:** Operators, Researcher, Quants  
**Basis:** Phase 76 (R&D Hub) + Phase 77 (Detail & Report Viewer) + Phase 78 (Multi-Run Comparison)  
**Stand:** 2025-12-09

---

## 1. Was ist der R&D-Hub und wann nutze ich ihn?

Der **R&D-Hub** ist ein Web-Dashboard zur Sichtung aller R&D-Experimente.

**Nutze den R&D-Hub, wenn du:**

- Einen Überblick über alle gelaufenen R&D-Experimente brauchst
- Einzelne Runs nach Preset, Strategy, Tag oder Status filtern willst
- Metriken (Return, Sharpe, MaxDD, WinRate) schnell vergleichen möchtest
- Zugehörige Reports (HTML, Markdown, Charts) direkt öffnen willst
- Das Roh-JSON eines Runs inspizieren musst (Debugging)

**Der R&D-Hub ist nicht für:**

- Live-/Testnet-Sessions → dafür: Live-Track Dashboard (`/`)
- Starten neuer Experimente → dafür: CLI / Research-Scripts
- Editieren von Konfigurationen → dafür: TOML-Dateien / IDE

> **Safety:** R&D-Strategien sind **nicht live-freigegeben**. Sie dienen ausschließlich Offline-Backtests, Research-Pipelines und akademischen Analysen.

---

## 2. Voraussetzungen

Bevor du den R&D-Hub nutzen kannst, muss mindestens ein Experiment gelaufen sein.

### 2.1 Experiment starten (CLI)

```bash
cd /path/to/Peak_Trade
source .venv/bin/activate

# Beispiel: Ehlers-Preset ausführen
python scripts/research_cli.py run-experiment \
  --preset ehlers_super_smoother_v1 \
  --symbol BTC/USDT \
  --timeframe 1h
```

Alternativ für Batch-Läufe:

```bash
python scripts/research_cli.py run-batch \
  --presets config/r_and_d_presets.toml \
  --tag "wave_v2_test"
```

### 2.2 Report-Verzeichnis prüfen

Experimente landen in:

```
reports/r_and_d_experiments/
├── exp_rnd_w2_ehlers_v1_20251208_233107.json
├── exp_rnd_w2_armstrong_v1_20251208_234512.json
└── ...
```

### 2.3 Web-Dashboard starten

```bash
python scripts/operator_dashboard.py
```

Standardmäßig erreichbar unter `http://127.0.0.1:8000`.

---

## 3. Schritt-für-Schritt: R&D Experiment einsehen

### Schritt 1 – R&D-Hub öffnen

- Browser: `http://127.0.0.1:8000/r_and_d`
- Oder im Dashboard: Navigation → **R&D**

Du siehst: Übersichtstabelle aller R&D-Experimente.

### Schritt 2 – Experiment suchen (Filter / Sort)

**Filteroptionen:**

| Filter       | Beispiel                     |
|--------------|------------------------------|
| Preset       | `ehlers_super_smoother_v1`   |
| Strategy     | `ehlers_cycle_filter`        |
| Tag-Substring| `wave_v2`                    |
| Mit Trades   | Nur Runs mit `trades > 0`    |
| Datum        | Von/Bis Zeitraum             |

**Sortieroptionen:** Klick auf Spaltenheader (Sharpe, Return, Timestamp, etc.)

### Schritt 3 – Zeile anklicken → Detail-View

Jede Zeile ist klickbar. Alternativ: Pfeil-Icon (→) in der Details-Spalte.

**Ziel-URL:** `/r_and_d/experiment/{run_id}`

### Schritt 4 – Detail-View verstehen

Die Detail-Ansicht zeigt:

| Bereich           | Inhalt                                                |
|-------------------|-------------------------------------------------------|
| **Meta-Panel**    | Preset, Strategy, Symbol, Timeframe                   |
| **Timing**        | Timestamp, Von/Bis-Datum, Laufzeit (duration_human)   |
| **Config-Badges** | Status-Badge, Run-Type-Badge, Tier-Badge              |
| **Metriken-Grid** | Return, Sharpe, MaxDD, Trades, WinRate, Profit Factor |
| **Report-Links**  | HTML-Report, Markdown, Charts (PNG)                   |
| **Raw JSON**      | Einklappbares Panel mit vollem Experiment-JSON        |

### Schritt 5 – Reports öffnen

Im Bereich **Reports** findest du (falls vorhanden):

| Icon | Typ       | Beschreibung                     |
|------|-----------|----------------------------------|
| 📄   | HTML      | Vollständiger Backtest-Report    |
| 📝   | Markdown  | Textbasierter Report             |
| 📊   | PNG       | Equity-Curve / Drawdown-Chart    |
| 📈   | Stats-JSON| Detaillierte Statistiken         |

Klick öffnet den Report in einem neuen Tab.

### Schritt 6 – Zurück zur Übersicht

Button **← Zurück zum R&D Hub** oder Browser-Back.

---

## 3b. Schritt-für-Schritt: Multi-Run Comparison (Phase 78)

### Schritt 1 – Experimente auswählen

- In der R&D-Übersicht (`/r_and_d`) gibt es jetzt eine Checkbox-Spalte (⚖️)
- Klicke die Checkbox bei 2–4 Experimenten, die du vergleichen möchtest
- Die Compare-Leiste erscheint automatisch mit einem Counter

### Schritt 2 – Vergleich starten

- Klicke auf **⚖️ Vergleichen** in der Compare-Leiste
- Du wirst zu `/r_and_d/comparison?run_ids=...` weitergeleitet

### Schritt 3 – Vergleichstabelle analysieren

Die Comparison-View zeigt:

| Bereich           | Inhalt                                                |
|-------------------|-------------------------------------------------------|
| **Konfiguration** | Tag, Preset, Strategy, Symbol/TF, Timestamp           |
| **Performance**   | Return, Sharpe, MaxDD, Trades, WinRate, Profit Factor |
| **Best-Metric**   | ★-Symbol beim besten Wert pro Zeile                   |
| **Aktionen**      | Link zur Detail-Ansicht jedes Experiments             |

### Schritt 4 – Tiefere Analyse

- Klicke auf **Details →** bei interessanten Runs
- Oder kehre zur Übersicht zurück und wähle andere Experimente

### Tipps für effektive Vergleiche

- Vergleiche Runs mit **gleichem Symbol/Timeframe** für aussagekräftige Ergebnisse
- Nutze die **Preset-Filter** in der Übersicht, um ähnliche Runs zu finden
- Maximal **4 Runs** gleichzeitig vergleichen für Übersichtlichkeit

---

## 4. Debugging & Fehlerbilder

### 4.1 Ungültige oder unbekannte `run_id`

**Symptom:** Du rufst `/r_and_d/experiment/xyz_invalid_123` auf.

**Verhalten:**
- HTTP 404
- Anzeige von `error.html` mit Fehlercode und Nachricht
- Rück-Link zum R&D-Hub

**Lösung:** Prüfe die korrekte `run_id` in der Übersicht oder im Dateisystem.

### 4.2 Fehlende Reports

**Symptom:** Report-Links-Bereich zeigt „Keine Reports gefunden".

**Ursache:** Das Experiment hat keine zugehörigen Report-Dateien generiert.

**Lösung:**
1. Prüfe, ob der Run erfolgreich war (`status: success`)
2. Report-Generierung ggf. manuell nachziehen:
   ```bash
   python scripts/research_cli.py generate-report --run-id <run_id>
   ```

### 4.3 Status `failed` oder `no_trades`

**Status-Badges:**

| Badge       | Bedeutung                                      |
|-------------|------------------------------------------------|
| ✅ success  | Run erfolgreich abgeschlossen                  |
| ⏳ running  | Run läuft noch (selten im Dashboard sichtbar)  |
| ❌ failed   | Run mit Fehler abgebrochen                     |
| ⚪ no_trades| Kein Trade generiert (z.B. zu enge Filter)     |

**Bei `failed`:**
- Raw JSON aufklappen → `error`-Feld prüfen
- Logs unter `logs/` durchsuchen

**Bei `no_trades`:**
- Parameter prüfen (Timeframe, Symbol, Filter-Bedingungen)
- Ggf. längeren Backtest-Zeitraum wählen

---

## 5. Best Practices

### 5.1 Aussagekräftige Tags verwenden

```bash
--tag "ehlers_btc_1h_conservative_v2"
```

Gute Tags enthalten: **Preset-Kurzname**, **Symbol**, **Timeframe**, **Variante**.

### 5.2 Batch-Runs dokumentieren

Halte in einem Run-Log fest, welche Presets wann gelaufen sind:

- Siehe: [`PHASE_75_R_AND_D_WAVE_V2_EXPERIMENTS.md`](PHASE_75_R_AND_D_WAVE_V2_EXPERIMENTS.md) → Abschnitt 6.1

### 5.3 Reports immer generieren lassen

Aktiviere Report-Generierung im Preset oder per Flag:

```bash
--generate-reports
```

So sind HTML-Reports und Charts später im Dashboard verfügbar.

### 5.4 Raw JSON nur bei Bedarf

Das Raw-JSON-Panel ist standardmäßig eingeklappt. Nutze es für:

- Debugging bei unerwarteten Ergebnissen
- Prüfung von Parametern, die nicht im Meta-Panel erscheinen
- Export / Copy-Paste für weitere Analyse

### 5.5 Regelmäßige Cleanup-Runden

Alte oder fehlgeschlagene Experimente ggf. archivieren:

```bash
mv reports/r_and_d_experiments/exp_old_*.json archive/r_and_d/
```

---

## 6. Verwandte Dokumente & Links

| Thema                          | Dokument / Pfad                                                |
|--------------------------------|----------------------------------------------------------------|
| R&D-Runbook Armstrong/ElKaroui | [`R_AND_D_RUNBOOK_ARMSTRONG_EL_KAROUI_V1.md`](runbooks/R_AND_D_RUNBOOK_ARMSTRONG_EL_KAROUI_V1.md) – beschreibt Standard-Workflows, Safety-Gates und Promotion-Pfade für `ArmstrongCycleStrategy` & `ElKarouiVolModelStrategy`. |
| R&D-Playbook Armstrong/ElKaroui | [`R_AND_D_PLAYBOOK_ARMSTRONG_EL_KAROUI_V1.md`](runbooks/R_AND_D_PLAYBOOK_ARMSTRONG_EL_KAROUI_V1.md) – Research-Workflow, Sweeps, zukünftige Hypothesen für `armstrong_cycle` & `el_karoui_vol_model`. |
| Phase 76 Design-Spezifikation  | [`PHASE_76_R_AND_D_DASHBOARD_V0_DESIGN.md`](PHASE_76_R_AND_D_DASHBOARD_V0_DESIGN.md) |
| Phase 77 Detail Viewer         | [`PHASE_77_R_AND_D_EXPERIMENT_DETAIL_VIEWER.md`](PHASE_77_R_AND_D_EXPERIMENT_DETAIL_VIEWER.md) |
| Phase 78 Multi-Run Comparison  | [`PHASE_78_R_AND_D_REPORT_GALLERY_AND_COMPARISON_V1.md`](PHASE_78_R_AND_D_REPORT_GALLERY_AND_COMPARISON_V1.md) |
| Status-Übersicht (Phase 76-78) | [`PEAK_TRADE_STATUS_OVERVIEW.md`](PEAK_TRADE_STATUS_OVERVIEW.md) → Abschnitt R&D |
| R&D Presets                    | `config/r_and_d_presets.toml`                                  |
| R&D API Implementierung        | `src/webui/r_and_d_api.py` (v1.3)                              |
| Detail-View Template           | `templates/peak_trade_dashboard/r_and_d_experiment_detail.html`|
| Comparison-View Template       | `templates/peak_trade_dashboard/r_and_d_experiment_comparison.html` |
| CLI Experiments Viewer         | `scripts/view_r_and_d_experiments.py`                          |
| Notebook-Template              | `notebooks/r_and_d_experiment_analysis_template.py`            |

---

## 7. Checkliste: Bin ich bereit für das R&D-Dashboard?

- [ ] **Mindestens ein Experiment gelaufen** (`reports/r_and_d_experiments/*.json` vorhanden)
- [ ] **Web-Dashboard gestartet** (`python scripts/operator_dashboard.py`)
- [ ] **Browser auf** `http://127.0.0.1:8000/r_and_d`
- [ ] **Ich weiß, wonach ich suche** (Preset, Tag, Strategy, Zeitraum)
- [ ] **Ich verstehe die Metriken** (Return, Sharpe, MaxDD, WinRate, PF)
- [ ] **Ich kenne den Unterschied** zwischen R&D-Hub (Research) und Live-Track (Execution)

✅ Alle Punkte erfüllt? → Du bist ready für den R&D Operator-Flow!

---

## 8. Änderungshistorie

| Datum      | Änderung                                      |
|------------|-----------------------------------------------|
| 2025-12-09 | Initiale Version (Phase 76/77)                |
| 2025-12-09 | Multi-Run Comparison hinzugefügt (Phase 78)   |

---

**Built for Research – R&D Operator Flow v1.1**
