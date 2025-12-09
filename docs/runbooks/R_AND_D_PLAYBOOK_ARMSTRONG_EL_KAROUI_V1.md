# R&D-Playbook – Armstrong & El Karoui v1

**Version:** v1.1
**Stand:** Armstrong und El Karoui sind als vollständige R&D-Strategien implementiert
**Ziel:** Research-Workflow für Cycle- und Volatilitäts-basierte Analysen aufbauen.

---

## 1. Kontext & Ziele

Dieses Playbook beschreibt, wie die beiden R&D-Strategien

* `armstrong_cycle`
* `el_karoui_vol_model`

innerhalb von **Peak_Trade** für Research genutzt werden sollen.

Aktueller Stand:

* Strategien sind in der **Config** registriert (`config.toml` und `config/config.toml`)
* Tiering & Safety:

  * `tier = "r_and_d"`
  * `is_live_ready = false`
  * `allowed_environments = ["offline_backtest", "research"]`
* Zwei Sweeps sind registriert:

  * `armstrong_cycles_v1` (32 Runs)
  * `el_karoui_vol_sensitivity_v1` (144 Runs)
* Beide Strategien generieren echte Signale basierend auf Cycle-Phasen (Armstrong) bzw. Vol-Regime (El Karoui).

Dieses Playbook definiert:

1. Wie die Sweeps aktuell sinnvoll genutzt werden können (Integration & Wiring).
2. Wie ein späterer inhaltlicher Research-Loop aussehen soll, sobald echte Signallogik existiert.

---

## 2. Setup & Voraussetzungen

* Repo: `Peak_Trade` (Hauptrepo, nicht Worktree)

* venv aktiv:

  ```bash
  cd /Users/frnkhrz/Peak_Trade
  source .venv/bin/activate
  ```

* Kraken-Daten sind über die Data-Layer / Loader erreichbar (Netzwerkzugriff vorhanden).

* R&D-API + R&D-Dashboard sind verfügbar (Phase 76–78).

---

## Dokumentation

* [Armstrong Cycle Strategy – Status v1](../strategies/armstrong/ARMSTRONG_CYCLE_STATUS_V1.md)
* [El Karoui Volatility Strategy – Status v1](../strategies/el_karoui/EL_KAROUI_VOL_STATUS_V1.md)

---

## How to run – Armstrong Cycle (R&D)

**Zweck:** Research-/Backtest-Experimente auf Basis des Armstrong-Cycle-Modells.
**Tier:** `r_and_d` → keine Live-/Paper-/Testnet-/Shadow-Trades.

Beispiel-Backtest (an dein CLI anpassen):

```bash
python -m scripts.run_backtest \
  --strategy armstrong_cycle \
  --config config/strategies/armstrong_cycle_default.toml
```

Typische Run-Typen:

* `backtest`
* `research`
* `sweep` (Parameter-Sweeps über Phasen-Profile, Cycle-Länge, etc.)

Nicht erlaubt:

* `live_trade`
* `paper_trade`
* `testnet_trade`
* `shadow_live`

## How to run – El Karoui Volatility (R&D)

**Zweck:** Volatilitäts-/Regime-Experimente basierend auf dem El-Karoui-Volatilitätsmodell.
**Registry-Key:** `el_karoui_vol_model`
**Tier:** `r_and_d`

Beispiel-Backtest:

```bash
python -m scripts.run_backtest \
  --strategy el_karoui_vol_model \
  --config config/strategies/el_karoui_vol_default.toml
```

Typische Run-Typen:

* `backtest`
* `research`
* `sweep` (z.B. über Vol-Schwellen, Fenstergrößen, Regime-Mapping)

Nicht erlaubt:

* `live_trade`
* `paper_trade`
* `testnet_trade`
* `shadow_live`

---

## ⚠️ R&D Safety & Tier-Gating (Armstrong & El Karoui)

Beide Strategien sind als **R&D-Strategien** klassifiziert:

* **Tier:** `r_and_d`
* **Allow Live:** `false`
* **Exception:** `RnDLiveTradingBlockedError` (via `live_gates.py`)

**Blockierte Modi:**

* `live`
* `paper`
* `testnet`
* `shadow`

**Erlaubte Modi:**

* `offline_backtest`
* `research` (inkl. Sweeps/Experiments ohne Order-Routing)

Jeder Versuch, diese Strategien in einem geblockten Modus zu verwenden, führt zu einer **sofortigen Exception**.
Damit ist sichergestellt, dass R&D-Strategien niemals versehentlich Orders an Broker/Exchanges schicken.

---

## Checkliste vor jedem R&D-Run

* [ ] Sicherstellen, dass der **Run-Typ** rein Research/Backtest ist
  (kein Live-, Paper-, Testnet- oder Shadow-Modus).
* [ ] Prüfen, dass das **Tier** der Strategie `r_and_d` ist und `allow_live = false`.
* [ ] Konfigurationsdatei kurz checken:

  * [ ] Märkte / Symbole
  * [ ] Zeitraum
  * [ ] Startkapital / Fees
* [ ] Output-/Log-Pfade klar:

  * [ ] Reports / Plots
  * [ ] Logs
  * [ ] Experiment-/Run-Registry-Eintrag (falls vorhanden)
* [ ] Bei Sweeps:

  * [ ] Parameterbereiche sind sinnvoll (keine extremen Werte, die Laufzeiten oder Speicher sprengen).
  * [ ] Anzahl der Varianten ist handhabbar.

---

## Checkliste nach jedem R&D-Run

* [ ] Ergebnis-Kennzahlen prüfen (z.B. Drawdown, Sharpe, Hit-Rate – je nach vorhandener Metrik-Pipeline).
* [ ] Logs und Reports kurz auf Errors/Warnings scannen.
* [ ] Interessante Ergebnisse markieren:

  * [ ] Run-ID / Experiment-ID im Registry-System speichern.
  * [ ] Kurznotiz zu Erkenntnissen (z.B. in „Research Notes" oder eigener Doku-Datei).
* [ ] Klar trennen:

  * [ ] Ergebnisse sind **R&D-only** – keine direkten Live-Handelsempfehlungen.
  * [ ] Für evtl. spätere Produktion sind zusätzliche Phasen nötig (Robustheitstests, Out-of-Sample, Risk-Review etc.).

---

## Runbook – Häufige Fehler & Troubleshooting

### 1. Run bricht sofort mit „Strategy not found" ab

**Ursache:** Der Registry-Key ist falsch geschrieben oder die Strategie ist nicht registriert.

**Was tun?**
* Prüfe den exakten Registry-Key: `armstrong_cycle` bzw. `el_karoui_vol_model`.
* Checke `config/config.toml` → `[strategies]`-Sektion: Ist die Strategie dort aufgeführt?
* Falls du einen Sweep nutzt: Ist der Sweep-Name korrekt (z.B. `armstrong_cycles_v1`)?

### 2. Config-Datei nicht gefunden / Pfad-Fehler

**Ursache:** Der Config-Pfad ist relativ zum Working Directory – wenn du aus einem Unterordner startest, stimmt der Pfad nicht.

**Was tun?**
* Starte Runs immer aus dem Repo-Root (`/Users/frnkhrz/Peak_Trade`).
* Verwende absolute Pfade oder prüfe den relativen Pfad: `config/strategies/armstrong_cycle_default.toml`.
* Quick-Check: `ls config/strategies/` – existiert die Datei?

### 3. Run-Typ wird als „live" oder „paper" interpretiert

**Ursache:** Die Execution-Pipeline oder ein anderes Script versucht, die Strategie in einem Live-Modus zu starten.

**Was tun?**
* Für R&D-Strategien nur `run_backtest.py` oder `research_cli.py` verwenden – diese sind für Offline-Backtests ausgelegt.
* Prüfe, dass du nicht versehentlich `run_shadow_paper_session.py` oder `run_execution_session.py` aufrufst.
* Das Tier-Gating in `live_gates.py` blockiert R&D-Strategien automatisch in Live-Modi.

### 4. RnDLiveTradingBlockedError – Strategie blockiert

**Ursache:** Du versuchst, eine R&D-Strategie in einem blockierten Modus (live/paper/testnet/shadow) zu starten.

**Was tun?**
* Das ist **erwartetes Verhalten** – R&D-Strategien dürfen nicht live traden.
* Wechsle zu `offline_backtest` oder `research` als Run-Modus.
* Falls du wirklich Live testen willst: Das geht nur mit produktionsreifen Strategien (Tier ≠ `r_and_d`).

### 5. Leere Metriken / NaN-Werte im Report

**Ursache:** Die Strategie hat keine Trades generiert oder die Daten-Range enthält keine verwertbaren Daten.

**Was tun?**
* Prüfe die Date-Range: Ist der Zeitraum sinnvoll und sind Daten verfügbar?
* Checke die Strategie-Parameter: Sind Schwellenwerte so gewählt, dass überhaupt Signale entstehen?
* Starte einen Dry-Run mit kurzer Date-Range (z.B. 30 Tage), um schnell Feedback zu bekommen.

### 6. Output-Ordner existiert nicht / Permission denied

**Ursache:** Der Output-Pfad wurde nicht angelegt oder du hast keine Schreibrechte.

**Was tun?**
* Standard-Output-Verzeichnisse werden automatisch angelegt (`reports/`, `reports/experiments/`, `reports/r_and_d_experiments/`).
* Falls `--save-report` genutzt wird: Prüfe, ob der Parent-Ordner existiert.
* Bei R&D-Experiments: `mkdir -p reports/r_and_d_experiments` falls nötig.
* Prüfe Schreibrechte im Projekt-Ordner.

### 7. Sweep läuft ewig / Memory-Probleme

**Ursache:** Der Parameterraum ist zu groß oder die Date-Range zu lang für die Anzahl der Runs.

**Was tun?**
* Reduziere die Anzahl der Parameter-Kombinationen (weniger Sweep-Dimensionen).
* Verkürze die Date-Range für erste Experimente.
* Nutze `--dry-run` (falls implementiert), um die Anzahl der Runs vorab zu sehen.
* Bei Memory-Issues: Runs nacheinander statt parallel ausführen.

### 8. Registry-Eintrag fehlt nach dem Run

**Ursache:** Der Run wurde nicht sauber abgeschlossen oder die Registry-Integration ist nicht aktiv.

**Was tun?**
* Prüfe die Logs auf Fehler am Run-Ende.
* Checke, ob die R&D-API läuft (`uvicorn` auf Port 8000).
* Manuell im R&D-Dashboard nachschauen: Ist der Run mit Status `failed` gelistet?

---

## Example R&D Session – Armstrong & El Karoui

> ⚠️ **Wichtig:** Alle folgenden Beispiele sind **R&D-only** (`tier = "r_and_d"`).
> Es werden **keine echten Orders** an Broker/Exchanges geschickt.

### Beispiel-Run: Armstrong Cycle (R&D)

**CLI-Command (Backtest):**

```bash
cd /Users/frnkhrz/Peak_Trade
source .venv/bin/activate

# Einfacher Backtest mit Tag (historisch abgeschlossenes Fenster)
python scripts/run_backtest.py \
  --strategy armstrong_cycle \
  --config config.toml \
  --tag armstrong_btc_2018_2020 \
  --start-date 2018-01-01 \
  --end-date 2020-12-31 \
  --verbose

# Mit Report-Export
python scripts/run_backtest.py \
  --strategy armstrong_cycle \
  --config config.toml \
  --tag armstrong_btc_2018_2020 \
  --save-report reports/r_and_d/armstrong_cycle_btc_2018_2020.html
```

**Erwartete Outputs:**

| Was | Wo |
|-----|-----|
| Registry-Eintrag | `reports/experiments/experiments.csv` (neue Zeile mit `run_id`, `strategy_key`, Stats) |
| HTML-Report (wenn `--save-report`) | z.B. `reports/r_and_d/armstrong_cycle_btc_2018_2020.html` |
| Equity-Plot (wenn `--save-report`) | z.B. `reports/r_and_d/armstrong_cycle_btc_2018_2020_equity.png` |
| Stats-JSON (wenn `--save-report`) | z.B. `reports/r_and_d/armstrong_cycle_btc_2018_2020_stats.json` |
| R&D-Dashboard | Web-UI → Experiments Overview → Filter: `armstrong_cycle` |

**Was schaue ich mir nach dem Run als erstes an?**

1. **Status im R&D-Dashboard:** Run-Status sollte `success` sein, nicht `failed` oder `no_trades`.
2. **Cycle-Phasen-Verteilung:** Wie oft war die Strategie in welcher Phase (ACCUMULATION, MARKUP, DISTRIBUTION, MARKDOWN)?
3. **Signal-Frequenz:** Wie viele Signale wurden generiert? Zu viele = Noise, zu wenige = kein Exposure.
4. **Turning-Point-Treffer:** Falls Event-Studien aktiv: Wie gut korrelieren Turning Points mit Marktbewegungen?
5. **Parameter-Sensitivität:** Bei Sweeps: Welche `cycle_length_days` / `event_window_days` performen am stabilsten?

---

### Beispiel-Run: El Karoui Volatility (R&D)

**CLI-Command (Backtest):**

```bash
cd /Users/frnkhrz/Peak_Trade
source .venv/bin/activate

# Einfacher Backtest mit Tag (historisch abgeschlossenes Fenster)
python scripts/run_backtest.py \
  --strategy el_karoui_vol_model \
  --config config.toml \
  --tag el_karoui_vol_regime_test \
  --start-date 2018-01-01 \
  --end-date 2020-12-31 \
  --verbose

# Mit Report-Export
python scripts/run_backtest.py \
  --strategy el_karoui_vol_model \
  --config config.toml \
  --tag el_karoui_vol_regime_test \
  --save-report reports/r_and_d/el_karoui_vol_btc_regime_test.html
```

**Erwartete Outputs:**

| Was | Wo |
|-----|-----|
| Registry-Eintrag | `reports/experiments/experiments.csv` (neue Zeile mit `run_id`, `strategy_key`, Stats) |
| HTML-Report (wenn `--save-report`) | z.B. `reports/r_and_d/el_karoui_vol_btc_regime_test.html` |
| Equity-Plot (wenn `--save-report`) | z.B. `reports/r_and_d/el_karoui_vol_btc_regime_test_equity.png` |
| Stats-JSON (wenn `--save-report`) | z.B. `reports/r_and_d/el_karoui_vol_btc_regime_test_stats.json` |
| R&D-Dashboard | Web-UI → Experiments Overview → Filter: `el_karoui_vol_model` |

**Was schaue ich mir nach dem Run als erstes an?**

1. **Regime-Verteilung:** Wie viel Zeit verbrachte der Markt in LOW/MEDIUM/HIGH? (Erwartung: nicht 99% in einem Regime.)
2. **Regime-Wechsel-Frequenz:** Wie oft wechselt das Regime? Zu häufig = Parameter zu sensitiv.
3. **Vol-Scaling-Effekt:** Falls `use_vol_scaling = true`: Wie stark variiert der Exposure-Faktor?
4. **Threshold-Sensitivität:** Bei Sweeps: Welche `low_threshold` / `high_threshold` Kombinationen liefern stabile Regime-Klassifikationen?
5. **Registry-Eintrag prüfen:** Run-ID notieren, Parameter und Duration im Dashboard checken.

---

### Quick-Validation nach jedem R&D-Run

```bash
# Letzte Einträge in der Experiment-Registry anzeigen
tail -5 reports/experiments/experiments.csv

# Stats aus JSON-Report lesen (falls --save-report genutzt)
cat reports/r_and_d/*_stats.json | jq '.total_return, .sharpe, .max_drawdown'

# Alle R&D-Experiment-JSONs auflisten
ls -lt reports/r_and_d_experiments/*.json | head -10
```

> **Tipp:** Falls `jq` nicht installiert ist, kannst du die Stats auch im Terminal-Output des Backtests oder im R&D-Dashboard ansehen.

---

## Goldene R&D-Commands (Copy & Paste)

> ⚠️ Die folgenden Commands sind für **R&D-Runs** (`tier = "r_and_d"`) konzipiert.
> Keine echten Orders – nur Offline-Backtests mit lokalen/Dummy-Daten.

**Zweck dieser Smoke-Tests:**
- **Stabile Basis-Tests** für Setup, Pipeline und Reporting
- Historisch abgeschlossenes Datenfenster (2018–2020) für reproduzierbare Ergebnisse
- Keine Live/Paper-Trades – rein R&D/Tier-3
- Crash-resistent durch bewusst konservative Parameter

### Armstrong Cycle – Smoke-Test

```bash
cd /Users/frnkhrz/Peak_Trade
source .venv/bin/activate

python scripts/run_backtest.py \
  --strategy armstrong_cycle \
  --config config.toml \
  --tag rnd_armstrong_smoke \
  --start-date 2018-01-01 \
  --end-date 2020-12-31 \
  --save-report reports/r_and_d/armstrong_smoke_test.html \
  --verbose
```

**Was erwarte ich nach dem Run?**

* ✅ Neuer Eintrag in `reports/experiments/experiments.csv` mit `strategy_key = armstrong_cycle`
* ✅ Terminal-Output mit Kennzahlen (Total Return, Sharpe, Max Drawdown, Trade-Statistiken)
* ✅ HTML-Report: `reports/r_and_d/armstrong_smoke_test.html`
* ✅ Equity-Plot: `reports/r_and_d/armstrong_smoke_test_equity.png`
* ✅ Stats-JSON: `reports/r_and_d/armstrong_smoke_test_stats.json`
* ✅ Optional: JSON in `reports/r_and_d_experiments/` (abhängig von Pipeline-Integration)

---

### El Karoui Volatility – Smoke-Test

```bash
cd /Users/frnkhrz/Peak_Trade
source .venv/bin/activate

python scripts/run_backtest.py \
  --strategy el_karoui_vol_model \
  --config config.toml \
  --tag rnd_elkaroui_smoke \
  --start-date 2018-01-01 \
  --end-date 2020-12-31 \
  --save-report reports/r_and_d/elkaroui_smoke_test.html \
  --verbose
```

**Was erwarte ich nach dem Run?**

* ✅ Neuer Eintrag in `reports/experiments/experiments.csv` mit `strategy_key = el_karoui_vol_model`
* ✅ Terminal-Output mit Kennzahlen (Total Return, Sharpe, Max Drawdown, Trade-Statistiken)
* ✅ HTML-Report: `reports/r_and_d/elkaroui_smoke_test.html`
* ✅ Equity-Plot: `reports/r_and_d/elkaroui_smoke_test_equity.png`
* ✅ Stats-JSON: `reports/r_and_d/elkaroui_smoke_test_stats.json`
* ✅ Optional: JSON in `reports/r_and_d_experiments/` (abhängig von Pipeline-Integration)

---

### Quick-Validation (Bash-Snippets)

Nach dem Run kannst du mit diesen Kommandos prüfen, ob alles geklappt hat:

```bash
# 1. Registry-Check: Letzte 3 Einträge in der Experiment-CSV
tail -3 reports/experiments/experiments.csv

# 2. Report-Check: Wurden HTML-Reports erstellt?
ls -la reports/r_and_d/*.html 2>/dev/null | tail -5

# 3. Stats-Check: Wurden Stats-JSONs erstellt?
ls -la reports/r_and_d/*_stats.json 2>/dev/null | tail -5

# 4. R&D-Experiments-Check: Gibt es neue JSONs?
ls -lt reports/r_and_d_experiments/*.json 2>/dev/null | head -5
```

**Optional (falls `jq` installiert):**

```bash
# Stats aus dem letzten Report lesen
cat reports/r_and_d/armstrong_smoke_test_stats.json | jq '{total_return, sharpe, max_drawdown, total_trades}'

# Oder für El Karoui
cat reports/r_and_d/elkaroui_smoke_test_stats.json | jq '{total_return, sharpe, max_drawdown, total_trades}'
```

> **Hinweis:** Falls `jq` nicht installiert ist, kannst du die JSON-Dateien auch direkt öffnen oder den HTML-Report im Browser ansehen.

---

## Würzige R&D-Varianten (immer noch Tier-3)

> Die Basis-Smoke-Tests oben sind bewusst konservativ und crash-resistent.
> Dieser Abschnitt zeigt **„würzigere" R&D-Varianten** mit mehr Last / anderen Datenquellen.
> Es bleibt trotzdem **R&D/Tier-3** – keine echten Orders, kein Live/Paper-Modus.

### Würzige Armstrong-Varianten (Tier-3 / R&D)

Der Armstrong-Block hat zwei „würzige" Unter-Varianten:

#### A) Armstrong Last-Test (Dummy-Daten, mehr Last)

* **Zweck:** Pipeline-Performance- und Last-Tests mit synthetischen Daten
* **Status:** Bestehende `--bars 5000`-Variante bleibt unverändert erhalten
* **Wann benutzen?**
  * Wenn du nur prüfen willst, ob die Pipeline unter höherer Last stabil läuft
  * Wenn dir synthetische Dummy-Daten reichen und es nicht um Markt-Realismus geht

> **Hinweis:** Der konkrete Command bleibt identisch zur bestehenden Armstrong-Smoke-/Load-Variante, nur mit erhöhtem `--bars`-Wert (`--bars 5000`).

**Command:**

```bash
cd /Users/frnkhrz/Peak_Trade
source .venv/bin/activate

python scripts/run_backtest.py \
  --strategy armstrong_cycle \
  --config config.toml \
  --tag rnd_armstrong_spicy_5k_bars \
  --bars 5000 \
  --save-report reports/r_and_d/armstrong_spicy_5k_bars.html \
  --verbose
```

**Was erwarte ich?**
- Größerer Report, mehr Trades/Bars im Output.
- Längere Laufzeit, aber weiterhin reine R&D-Umgebung.

---

#### B) Armstrong Real-Data (echte Daten, engeres Zeitfenster)

Diese Variante verwendet echte OHLCV-Daten in einem volatilen Fenster und erzeugt einen „echten" R&D-Report.

> **Voraussetzung:** Du benötigst eine eigene OHLCV-CSV-Datei (z.B. Daily-Daten).
> Lege diese z.B. unter `data/ohlcv/` ab. Beispiel-Dateiname: `btcusdt_1d.csv`

**Command:**

```bash
cd /Users/frnkhrz/Peak_Trade
source .venv/bin/activate

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

**Kurz-Check:**

* **Wann benutzen?**
  * Wenn der Basis-Smoke-Test stabil läuft
  * Wenn du Armstrong mit **echten Daily-Daten** in einem volatilen Zeitfenster sehen willst
* **Was ist anders?**
  * Echte OHLCV-Datei via `--data-file`
  * Kürzeres Zeitfenster (~6 Monate) mit realen Marktbewegungen
* **Was erwarte ich?**
  * HTML-Report unter `reports/r_and_d/…`
  * Registry-Eintrag mit Tag `rnd_armstrong_trend_spice`
  * Plots mit echten Trends/Drawdowns und einer Cycle-Phasen-Verteilung

---

#### Safety / Tier-Hinweis (Armstrong)

* Beide Varianten sind strikt **Tier-3 / R&D**
* Kein Live-, kein Paper-, kein Testnet-Flow
* Nur für **Offline-Backtests** und R&D-Auswertungen gedacht

> **Symmetrie:** Armstrong und El Karoui haben jetzt beide eine „würzige" Real-Data-Variante im gleichen Abschnitt.

---

### Würzige El-Karoui-Variante (reale Daten, engeres Zeitfenster)

> **Voraussetzung:** Du benötigst eine eigene OHLCV-CSV-Datei (z.B. 1h oder 4h Frequenz).
> Lege diese z.B. unter `data/ohlcv/` ab. Beispiel-Dateiname: `btcusdt_1h.csv`

```bash
cd /Users/frnkhrz/Peak_Trade
source .venv/bin/activate

# Pfad anpassen an deine tatsächliche CSV-Datei!
python scripts/run_backtest.py \
  --strategy el_karoui_vol_model \
  --config config.toml \
  --tag rnd_elkaroui_intraday_spice \
  --data-file data/ohlcv/btcusdt_1h.csv \
  --start-date 2019-01-01 \
  --end-date 2019-06-30 \
  --save-report reports/r_and_d/elkaroui_intraday_spice.html \
  --verbose
```

**Wann benutzen?**
- Wenn der Basis-Smoke läuft und du das Vol-Modell auf Intraday-/feinere Daten loslassen willst.
- Zum Testen von Regime-Wechseln in volatileren Marktphasen.

**Was ist anders?**
- Echte OHLCV-Datei über `--data-file` (nicht synthetische Dummy-Daten).
- Kürzeres, volatileres Zeitfenster (6 Monate).
- Höhere Frequenz (z.B. 1h statt Daily).

**Was erwarte ich?**
- Reports/Plots, die stärkere Volatilität/Regimewechsel zeigen.
- Höhere Last auf Modell & Reporting durch mehr Datenpunkte.

---

### Weitere Varianten (Kurzreferenz)

**Schneller Mini-Smoke (nur 200 Bars):**

```bash
python scripts/run_backtest.py \
  --strategy el_karoui_vol_model \
  --config config.toml \
  --tag rnd_elkaroui_quick \
  --bars 200 \
  --verbose
```

**Ohne Report-Export (nur Registry + Terminal-Output):**

```bash
python scripts/run_backtest.py \
  --strategy armstrong_cycle \
  --config config.toml \
  --tag rnd_armstrong_minimal \
  --verbose
```

> **Hinweis:** Die Quick-Validation-Snippets weiter unten kannst du auch nach diesen würzigen Läufen nutzen.

---

### ⚠️ Safety-Hinweis für alle Würzigen Varianten

- Alle oben genannten Varianten sind weiterhin **Tier-3/R&D**.
- Verwende ausschließlich `scripts/run_backtest.py` – **niemals** Live- oder Paper-Skripte.
- Das Tier-Gating in `live_gates.py` blockiert R&D-Strategien automatisch in Live-Modi.

---

## 3. Armstrong-Cycle – Research-Ansatz

### 3.1 Grundidee (Zielbild)

Der Armstrong-Ansatz soll zyklische „Turning Points" im Markt markieren, z.B.:

* Lang-/Mittelfrist-Zyklen (z.B. 8.6 Jahre / Subzyklen)
* Ereignisfenster um bestimmte Referenzdaten
* Später: „Event-Score" oder „Cycle-Phase", die als **Filter oder Trigger** in anderen Strategien dient.

### 3.2 Relevante Parameter (aktuelle Strategie-API)

Typische Parameter (vereinfacht):

* `cycle_length_days`
* `event_window_days`
* `reference_date`

Ziel später:

* Für gegebene Märkte (z.B. `BTC/EUR` auf Kraken) Zeiträume finden, in denen:

  * Häufung von starken Bewegungen um Cycle-Dates
  * bestimmte Volatilitäts-/Trend-Muster rund um diese Events auftreten

### 3.3 Aktuelle Nutzung (v1 – Flat-Stubs)

Auch ohne echte Trades sind die Sweeps nützlich für:

1. **Validierung der technischen Integration**

   * Strategy-Loading aus Config
   * Sweep-Handling (`StrategySweepConfig`)
   * Registry-Einträge / Run-IDs
   * R&D-Dashboard & API-Views

2. **Laufzeit-/Skalierungs-Checks**

   * Wie viele Runs sind für die gewählte Parametrisierung performant?
   * Gibt es Timeouts / Memory-Issues bei größeren Parameterräumen?

3. **Metadaten-Validierung**

   * `run_type`, `tier`, `experiment_category`
   * Status (`success`, `no_trades`, …)
   * Dauer (`duration_info` in der R&D-API)

### 3.4 Zielbild für spätere Iterationen

Sobald Signallogik existiert, sollen Armstrong-Sweeps helfen bei:

* Hypothese H1: **Cycle-Turning-Points korrelieren mit lokalen Extrema / Volatilitäts-Clustern**

  * Messen: Return-/Volatility-Profile vor/nach Turning Points.
* Hypothese H2: **Bestimmte Cycle-Phasen sind „no-trade" Zonen**

  * Messen: Performance von Strategien, wenn nur in bestimmten Phasen gehandelt wird.
* Hypothese H3: **Armstrong als Meta-Filter**

  * Nur dann Trades anderer Strategien zulassen, wenn bestimmte Cycle-Kriterien erfüllt sind.

---

## 4. El-Karoui-Vol-Modell – Research-Ansatz

### 4.1 Grundidee (Zielbild)

Der El-Karoui-inspirierte Ansatz soll **Volatilitäts-Regime** erkennen:

* „Low-Vol"-Phasen: eher trendig / carry-freundlich
* „High-Vol"-Phasen: eher mean-reverting / risk-off
* Zwischenregime: neutral / Übergangsphasen

### 4.2 Relevante Parameter (aktuelle Strategie-API)

Die El Karoui Volatility Strategy (`ElKarouiVolatilityStrategy`) verwendet:

* `vol_window`: Fenster für Realized-Vol-Berechnung (default: 20)
* `lookback_window`: Fenster für Perzentil-Berechnung (default: 252)
* `low_threshold`: Perzentil-Schwelle für LOW-Regime (default: 0.30)
* `high_threshold`: Perzentil-Schwelle für HIGH-Regime (default: 0.70)
* `vol_target`: Ziel-Volatilität p.a. für Scaling (default: 0.10)
* `use_ewm`: Exponentiell gewichtete Volatilität
* `use_vol_scaling`: Ob Vol-Target-Scaling angewendet wird
* `regime_position_map`: Mapping-Strategie ("default", "conservative", "aggressive")

Das zugrunde liegende `ElKarouiVolModel` klassifiziert drei Regimes:

* `VolRegime.LOW`: Volatilität im unteren Bereich
* `VolRegime.MEDIUM`: Volatilität im mittleren Bereich
* `VolRegime.HIGH`: Volatilität im oberen Bereich

### 4.3 Signal-Logik (v1.1 – Implementiert)

Die Strategie generiert Signale basierend auf Vol-Regime:

**Default-Mapping:**
* LOW-Vol → long (1) – Risk-On, geringe Marktrisiken
* MEDIUM-Vol → long (1) – mit reduziertem Exposure via Scaling
* HIGH-Vol → flat (0) – Risk-Off, erhöhte Marktrisiken

**Conservative-Mapping:**
* Nur in LOW-Vol long, sonst flat

**Aggressive-Mapping:**
* In allen Regimes long, nur Scaling unterschiedlich

### 4.4 Aktuelle Nutzung

Sweeps über `vol_window` + `thresholds` helfen zu verstehen:
* Wie stabil Regime-Klassifikationen sind
* Welche Parameter-Sets robuste Ergebnisse liefern
* Optimale Balance zwischen Reaktionsgeschwindigkeit und Noise

---

## 5. Kombinierte Analysen – Armstrong x El Karoui (Zielbild)

Sobald beide Strategien echte Signale/Labels liefern, entsteht ein interessanter Kombi-Research:

1. **Cycle-Turning-Points vs. Volatilitätsregime**

   * Fragestellung:

     * „In welchen Vol-Regimen treten die Armstrong-Turning-Points überwiegend auf?"
     * „Sind bestimmte Zyklen nur unter bestimmten Regimen relevant?"

2. **Regime-Filter für Zyklen**

   * Armstrong erzeugt potenzielle Event-Zeiträume.
   * El Karoui klassifiziert das Umfeld (LOW/MED/HIGH).
   * Mögliche Regeln:

     * Nur Armstrong-Events in `MEDIUM`-Regimen handeln.
     * Armstrong-Events in `HIGH`-Regimen als Warnsignal / Hedge-Signal benutzen.

3. **Bridging zu produktiven Strategien**

   * Armstrong/El Karoui bleiben `r_and_d`, aber:

     * können Meta-Signale/Labels liefern,
     * die dann von robusten Kernstrategien genutzt werden (z.B. MA-Trend, Reversal, Breakout).

---

## 6. Praktischer Workflow (jetzt, mit v1-Stubs)

### 6.1 Standard-Loop für Sweeps

1. **Sweep starten** (Armstrong / El Karoui)
2. **R&D-Dashboard öffnen** (Experiments Overview)
3. Runs filtern:

   * nach `run_type`, `tier = r_and_d`
   * nach Sweep-Name (`armstrong_cycles_v1`, `el_karoui_vol_sensitivity_v1`)
4. **Detail-View** eines Runs öffnen:

   * Status prüfen (sollte `success` sein)
   * `run_type`, `parameters`, `duration_info`
   * aktuell noch: PnL-Metriken = 0/NaN → ignorieren
5. **Technik-Doku ergänzen**:

   * Sweep-Namen + Parametrisierung notieren
   * Laufzeit / Stabilität kurz kommentieren
   * Grundlage für spätere „echte" Research-Runs schaffen

### 6.2 Iterations-Haken für die Zukunft

Sobald Signale implementiert sind, wird dieser Loop erweitert um:

* Metrik-Analyse:

  * Sharpe, Return, MaxDD, Hit-Rate, etc.
* Verhaltensanalyse:

  * Wann funktionieren bestimmte Parameter gut/schlecht?
* Cross-Strategie-Auswertung:

  * Armstrong/El Karoui als Label-Erzeuger,
  * andere Strategien als Trade-Executor.

---

## 7. Nächste Schritte

1. ✅ **Signallogik implementiert** – Beide Strategien generieren echte Signale
2. **Event-Studien** – Armstrong-Turning-Points gegen historische Marktbewegungen validieren
3. **Regime-Stabilität testen** – El Karoui Regime-Klassifikation auf Robustheit prüfen
4. **Kombinierte Experimente** – Armstrong × El Karoui Interaktionen analysieren
5. **Backtests mit realen Daten** – Performance-Metriken erheben und analysieren

---

## 8. Modulstruktur

### 8.1 Armstrong (`src/strategies/armstrong/`)

> 📄 **Status-Dokument:** [ARMSTRONG_CYCLE_STATUS_V1.md](../strategies/armstrong/ARMSTRONG_CYCLE_STATUS_V1.md)

```
armstrong/
├── __init__.py
├── cycle_model.py      # ArmstrongPhase, ArmstrongCycleConfig, ArmstrongCycleModel
└── armstrong_cycle_strategy.py  # ArmstrongCycleStrategy
```

### 8.2 El Karoui (`src/strategies/el_karoui/`)

```
el_karoui/
├── __init__.py
├── vol_model.py        # VolRegime, ElKarouiVolConfig, ElKarouiVolModel
└── el_karoui_vol_model_strategy.py  # ElKarouiVolatilityStrategy
```

### 8.3 Tests (`tests/strategies/`)

```
tests/strategies/
├── armstrong/
│   ├── __init__.py
│   ├── test_cycle_model.py              # 26 Tests (Phase, Config, Model)
│   └── test_armstrong_cycle_strategy.py # 48 Tests (Strategy, Gating, Smoke)
├── el_karoui/
│   ├── test_vol_model.py                # Vol-Model Tests
│   └── test_el_karoui_volatility_strategy.py  # Strategy Tests
└── test_r_and_d_armstrong_el_karoui_safety.py  # 6 Safety-Flag Tests
```

### 8.4 R&D Tier-Gating (`src/live/live_gates.py`)

Das Tier-Gating für R&D-Strategien ist zentral in `live_gates.py` implementiert:

```python
# Exception für blockierte R&D-Strategien
class RnDLiveTradingBlockedError(Exception):
    """Wird geworfen wenn R&D-Strategie in Live/Paper/Testnet läuft."""

# Prüfung ob Strategie für Modus blockiert ist
def check_r_and_d_tier_for_mode(strategy_id: str, mode: str) -> bool

# Assertion mit Exception
def assert_strategy_not_r_and_d_for_live(strategy_id: str, mode: str) -> None

# Blockierte Modi: live, paper, testnet, shadow
# Erlaubte Modi: offline_backtest, research
```

---

**Kurzfassung:**

Dieses Playbook dokumentiert den aktuellen Stand der R&D-Strategien Armstrong & El Karoui. Beide Strategien sind vollständig implementiert mit echter Signallogik:
- **Armstrong** generiert Signale basierend auf ECM-Zyklusphasen
- **El Karoui** generiert Signale basierend auf Volatilitäts-Regime-Klassifikation

Beide sind als `tier = "r_and_d"` klassifiziert und ausschließlich für Research/Backtests freigegeben. Live/Paper/Testnet ist durch Tier-Gating blockiert.
