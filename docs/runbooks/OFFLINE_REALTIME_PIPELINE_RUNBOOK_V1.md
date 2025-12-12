# OFFLINE_REALTIME_PIPELINE_RUNBOOK_V1

Offline-Realtime-Pipeline mit synthetischen Ticks (`is_synthetic=True`)

---

## 1. Zweck & Überblick

Die **Offline-Realtime-Pipeline** ist deine *Safety-Sandbox* für die Order-Execution-Pipeline:

* Datenquelle: **OfflineSynthSession** (synthetische Ticks)
* Feed: **OfflineRealtimeFeed v0** (realtime-ähnlicher Tick-Stream)
* Execution: normale **Order-Execution-Pipeline** (wie Live/Paper)
* Modus: **`offline_realtime_pipeline` + `paper`**, *niemals* Live/Testnet
* Safety: Jeder Tick trägt `is_synthetic=True`, Safety-Gates verhindern reale Orders

Ziel:
Strategie-Logik, Execution-Pfade, Fees-Handling, Positionstracking etc. testen – **ohne Risiko**, komplett entkoppelt vom echten Markt.

---

## 2. Voraussetzungen

* Projekt gebaut & Tests grün (insbesondere `tests/offline/`)
* Das Script existiert:

```bash
scripts/run_offline_realtime_ma_crossover.py
```

* Reporting-Modul vorhanden:

```bash
src/offline/offline_realtime_report.py
```

* Optional/empfohlen: Meta-Report-Modul

```bash
src/offline/offline_realtime_meta_report.py
scripts/offline_realtime_meta_report.py
```

---

## 3. Standard-Workflow: ein Run

### 3.1 Basic-Run (Default-Parameter)

Einfachster Start:

```bash
python scripts/run_offline_realtime_ma_crossover.py
```

Was passiert:

1. OfflineSynthSession erzeugt einen synthetischen Preisprozess
2. `OfflineRealtimeFeed` streamt diese Ticks
3. MA-Crossover-Strategie generiert Signale
4. Paper-Executor füllt Orders (Paper, niemals Live)
5. Run wird als `offline_realtime_pipeline` registriert
6. Report wird erzeugt unter:

```text
reports/offline_realtime_pipeline/<run_id>/
  ├── summary.json
  ├── summary.md
  └── summary.html
```

Im Terminal siehst du am Ende u.a.:

* Run-ID
* Symbol
* MA-Fenster
* Pfad zum HTML-Report

---

### 3.2 Typischer CLI-Run mit expliziten Parametern

Dein „Standard"-Beispiel:

```bash
python scripts/run_offline_realtime_ma_crossover.py \
  --symbol BTC/EUR \
  --n-steps 1000 \
  --n-regimes 5 \
  --fast-window 10 \
  --slow-window 30
```

#### CLI-Parameter-Referenz

| Parameter           | Default      | Beschreibung                                                      | Beispiele              |
|---------------------|--------------|-------------------------------------------------------------------|------------------------|
| `--symbol`          | `BTC/EUR`    | Handelssymbol (wird intern normalisiert zu `BTCEUR`)             | `BTC/EUR`, `ETH/USD`   |
| `--n-steps`         | `1000`       | Anzahl synthetischer Ticks/Zeitpunkte                             | `500`, `10000`, `20000`|
| `--n-regimes`       | `3`          | Anzahl Volatilitäts-Regimes (1=konstant, 5=sehr variabel)        | `3`, `5`, `10`         |
| `--fast-window`     | `20`         | Fenstergröße für schnelles Moving Average                         | `10`, `20`, `50`       |
| `--slow-window`     | `50`         | Fenstergröße für langsames Moving Average (muss > fast-window)    | `30`, `50`, `100`      |
| `--seed`            | `42`         | Random-Seed für Reproduzierbarkeit                                | `1`, `42`, `123`       |
| `--playback-mode`   | `fast_forward` | Playback-Modus: `fast_forward` (schnell) oder `realtime` (verzögert) | `fast_forward`, `realtime` |
| `--speed-factor`    | `10.0`       | Geschwindigkeitsfaktor für realtime-Modus (nur mit `--playback-mode realtime`) | `1.0`, `10.0`, `100.0` |
| `--verbose`         | `False`      | Aktiviert DEBUG-Logging                                           | `-`                    |

**Wichtige Constraints:**

* `fast-window` < `slow-window` (sonst Fehler)
* `n-steps` ≥ `slow-window` (sonst nicht genug Daten für MA-Berechnung)
* `n-regimes` ≥ 1

---

## 4. Typische Szenarien & Parameter-Sets

### 4.1 „Smoke-Test" – schneller Check

Kurz, kleiner Run zum Checken, ob alles funktioniert:

```bash
python scripts/run_offline_realtime_ma_crossover.py \
  --symbol BTC/EUR \
  --n-steps 500 \
  --n-regimes 3 \
  --fast-window 10 \
  --slow-window 30
```

Zweck:
Schnell sehen, ob:

* Strategie Ticks verarbeitet
* Orders generiert werden
* Report erzeugt wird

---

### 4.2 „Stress-Test" – längere Session

Mehr Last auf Strategie + Pipeline:

```bash
python scripts/run_offline_realtime_ma_crossover.py \
  --symbol BTC/EUR \
  --n-steps 20000 \
  --n-regimes 3 \
  --fast-window 20 \
  --slow-window 50
```

Zweck:

* Performance & Latenz beobachten
* Log-Volumen & Speicherbelastung testen
* Verhalten über lange synthetische Pfade sehen

---

### 4.3 „Regime-Varianz" – mehr Regimes, wilderes Verhalten

```bash
python scripts/run_offline_realtime_ma_crossover.py \
  --symbol BTC/EUR \
  --n-steps 10000 \
  --n-regimes 5 \
  --fast-window 15 \
  --slow-window 45
```

Zweck:

* Strategie-Verhalten in wechselnden Vol-Regimes sehen
* Robustheit prüfen: zu früh/zu spät, Whipsaw etc.

---

### 4.4 Seed-Sweeps (wenn `--seed` vorhanden)

Mehrere Runs mit verschiedenen Seeds:

```bash
for s in 1 2 3 4 5; do
  python scripts/run_offline_realtime_ma_crossover.py \
    --symbol BTC/EUR \
    --n-steps 5000 \
    --n-regimes 3 \
    --fast-window 20 \
    --slow-window 50 \
    --seed $s
done
```

Zweck:

* Verteilung über viele Szenarien
* Erkennen von „Fragilität" – Performance nur gut für einzelne Seeds?

---

## 5. Reports im Detail

### 5.1 Einzel-Run Report

Pro Run:

```text
reports/offline_realtime_pipeline/<run_id>/
  ├── summary.json
  ├── summary.md
  └── summary.html
```

* **summary.json**
  Maschinenlesbare Stats:

  * `run_id`, `run_type`, `symbol`, `strategy_id`
  * `env_mode`, `is_synthetic`
  * `started_at`, `finished_at`, `duration_seconds`
  * `n_ticks`, `n_orders`, `n_trades`
  * `gross_pnl`, `net_pnl`, `fees_paid`, `max_drawdown`
  * `synth_n_steps`, `synth_n_regimes`, `synth_seed`

* **summary.md**
  Menschlich gut lesbarer Markdown-Report:

  * Meta
  * PnL & Risk
  * Synthese-Setup
  * Safety-Notizen

* **summary.html**
  Kleine HTML-Seite (Dark-Theme), ideal für Browser/GUIs.

---

### 5.2 Meta-Overview über mehrere Runs

Wenn du das Meta-Report-Skript implementiert hast:

```bash
python scripts/offline_realtime_meta_report.py \
  --limit 50
```

Standard-Ausgabe:

```text
reports/offline_realtime_pipeline/OVERVIEW.md
reports/offline_realtime_pipeline/OVERVIEW.html
```

Typische Inhalte:

* Tabelle mit Spalten wie:

  * Run ID
  * Startzeit
  * Symbol
  * Strategie
  * Env
  * Ticks
  * Trades
  * Net PnL
  * Max Drawdown
  * Seed

Nutzung:

* **OVERVIEW.md** → direkt im Repo ansehen / in Git diffbar
* **OVERVIEW.html** → im Browser als kleine „OfflineRealtime-Dashboard"-Ansicht

---

## 6. Safety & Guardrails

Ganz wichtige Punkte:

1. **Alle Ticks sind synthetisch**

   * `is_synthetic=True`
   * `source="offline_synth"` (oder äquivalent)
   * Wird im Tick-Modell & Feed gesetzt

2. **Environment-Modus**

   * Für diese Pipeline ist **`mode="paper"`** gesetzt
   * `allow_live_orders=False`

3. **Safety-Gates in der Pipeline**

   * If `tick.is_synthetic` **und** Environment ist nicht Paper/Backtest/Shadow → **RuntimeError**
   * Keine Code-Pfade, in denen synthetische Ticks echte Live-Executors erreichen

4. **Im Zweifel: Fehler > Risiko**

   * Lieber ein Run bricht mit klarem `RuntimeError` ab,
   * als dass eine Fehlkonfiguration irgendwas Echtes angreift.

---

## 7. Typischer Operator-Flow (Kurzfassung)

1. **Smoke-Test laufen lassen**

   ```bash
   python scripts/run_offline_realtime_ma_crossover.py \
     --symbol BTC/EUR \
     --n-steps 500 \
     --n-regimes 3 \
     --fast-window 10 \
     --slow-window 30
   ```

2. **Report öffnen**

   * Im Terminal die Run-ID ablesen
   * `reports/offline_realtime_pipeline/<run_id>/summary.html` im Browser öffnen

3. **Mehrere Szenarien fahren**

   * verschieden Seeds (`--seed`)
   * verschiedene Fenster (`--fast-window`, `--slow-window`)
   * verschiedene Regimes (`--n-regimes`)

4. **Overview aktualisieren**

   ```bash
   python scripts/offline_realtime_meta_report.py --limit 50
   ```

   * `OVERVIEW.md` im Repo checken
   * `OVERVIEW.html` im Browser angucken

5. **Insights notieren**

   * Wo verhält sich die Strategie instabil?
   * Welche Settings sind robust über viele Seeds/Regimes?
   * Welche Patterns willst du später im echten Live-/Testnet-Flow überwachen?

---

## 8. Troubleshooting (Kurz)

* **Keine Reports?**

  * Checke Fehlermeldungen im Terminal
  * Prüfe, ob `reports/offline_realtime_pipeline/` existiert
  * Prüfe Schreibrechte

* **RuntimeError bzgl. Environment & is_synthetic**

  * Sicherstellen, dass das Environment für diesen Flow auf `paper`/`offline` steht
  * Configs/Run-Type prüfen

* **Meta-Report leer**

  * Keine `summary.json` gefunden:

    * Hast du schon Runs gefahren?
    * Sind die Pfade korrekt (`reports/offline_realtime_pipeline/<run_id>/summary.json`)?

---

## 9. Interpretation & Heuristiken für Offline-Realtime-Runs

Dieser Abschnitt hilft dir, einzelne Offline-Realtime-Runs **schnell zu beurteilen**, ohne jedes Mal tief in den Code zu tauchen. Die Werte findest du im jeweiligen `summary.md` / `summary.html`.

---

### 9.1 Quick-Check: 10-Sekunden-Bewertung

Nimm aus dem Report:

* `n_ticks`
* `n_trades`
* `net_pnl`
* `max_drawdown`
* `fees_paid`
* `synth_n_regimes`, `synth_seed`

**Fragen:**

1. **Ist überhaupt was passiert?**

   * `n_trades == 0` bei vielen Ticks (z.B. `n_ticks > 2000`)
     → *Strategie zu passiv / Parameter evtl. zu konservativ.*

2. **Ist das Ergebnis realistisch?**

   * `net_pnl` extrem hoch relativ zu Drawdown (z.B. 10% Gewinn bei max. 0.5% DD)
     → *Misstrauisch sein: evtl. Bug, unrealistische Path-Struktur oder Fee-Modell prüfen.*

3. **Frisst Fees alles auf?**

   * `fees_paid` ≈ `gross_pnl` oder `fees_paid > net_pnl`
     → *Strategie zu hyperaktiv / Trade-Frequenz im Verhältnis zur Edge zu hoch.*

---

### 9.2 Heuristiken für „gesundes" Verhalten

**A) Ticks vs. Trades**

* Grobe Faustregel (nur als Startpunkt):

  * < 0.1% der Ticks führen zu Trades → *sehr selektiv / evtl. zu passiv*
  * 0.1–2% der Ticks führen zu Trades → *oft ein sinnvoller Bereich*
  * > 5% der Ticks führen zu Trades → *High-Frequency-Verhalten, Fees & Slippage kritisch prüfen*

Rechnung:

```text
trade_rate = n_trades / n_ticks
```

---

**B) Drawdown vs. Ergebnis**

* Konvertiere `max_drawdown` in Prozent:

```text
max_dd_pct = max_drawdown * 100
```

Heuristiken:

* `max_dd_pct` im Bereich **-2% bis -15%** bei längeren Runs:

  * *für riskantere Strategien normal / tolerierbar*

* `max_dd_pct` < -20%:

  * *aggressiv, für Live/Real eher nur mit kleinem Kapital & starkem Risk-Framework*

* `net_pnl` deutlich positiv, aber `max_dd_pct` > -30%:

  * *klassisches „High-Return, High-Pain"-Profil – nur bewusst einsetzen.*

---

**C) Fees als Qualitätssignal**

```text
fee_ratio = fees_paid / max(1e-9, gross_pnl)
```

Daumenregel:

* `fee_ratio < 0.1` → Fees sind relativ unkritisch
* `0.1 <= fee_ratio <= 0.3` → Fees sind spürbar, aber ok
* `fee_ratio > 0.3` → Fees fressen einen großen Teil der Brutto-Edge
* `fee_ratio > 1.0` → du zahlst mehr Fees als du brutto verdienst → *Strategie zu „zappelig".*

---

### 9.3 Vergleich über Seeds & Regimes

Wenn du mehrere Runs mit unterschiedlichem `synth_seed` / `n_regimes` fährst:

* **Stabilität**:

  * `net_pnl` schwankt moderat um einen Bereich, aber ist nicht komplett „+100%, -100%, +200% …"
  * `n_trades` bleibt in derselben Größenordnung

* **Fragilität**:

  * ein Seed mit „Monster-PnL", die meisten Seeds leicht negativ/flat
    → *Verdacht auf Overfitting / instabiles Setup.*

Empfehlung:

* Für eine Strategie-Konfiguration mind. **5–10 Seeds** testen.
* Wenn 7/10 Seeds „ok" aussehen und 3/10 schlecht → eher robust als umgekehrt.

---

### 9.4 Wann ein Run „kritisch" ist

Markiere einen Offline-Realtime-Run intern als **kritisch / rot**, wenn z.B.:

* `max_dd_pct <= -30%` UND `net_pnl` ≈ 0 oder negativ
* `fee_ratio > 0.5` (Fees fressen mind. die Hälfte des Brutto-PnL)
* `n_trades` extrem hoch trotz moderater `n_ticks` (z.B. > 20% der Ticks führen zu Trades)
* massive Unterschiede zwischen Seeds bei ansonsten gleichen Parametern

Solche Runs eignen sich gut als:

* Negativ-Beispiele für weitere R&D
* Testfälle für zukünftige Risk-Engines / Stop-Logiken

---

### 9.5 Notizen für zukünftige Erweiterungen

In weiteren Versionen kannst du auf diesen Abschnitt aufbauen:

* Sharpe-ähnliche Metrik (Paper-Version) ergänzen
* Bucket-Analysen pro Regime (PnL nach Regime-Zugehörigkeit)
* Integration in ein zentrales HTML-Dashboard:

  * Ampel-Status pro Run (grün/gelb/rot)
  * Filterbar nach Symbol, Seed, Parametern

Bis dahin reicht diese Heuristik-Sektion als praktischer „Mental-Check", um Offline-Realtime-Runs schnell in **ok / interessant / kritisch** einzusortieren.

---

## 10. Weiterführende Dokumentation

### Verwandte Runbooks

- **[RUNBOOKS_LANDSCAPE_2026_READY](RUNBOOKS_LANDSCAPE_2026_READY.md)** – Zentrale Übersicht aller Runbooks
- **[EXECUTION_PIPELINE_GOVERNANCE_RISK_RUNBOOK_V1](EXECUTION_PIPELINE_GOVERNANCE_RISK_RUNBOOK_V1.md)** – Governance & Risk für Execution-Pipeline

### Script-Dokumentation

- **[SCRIPT_OFFLINE_REALTIME_MA_CROSSOVER](../SCRIPT_OFFLINE_REALTIME_MA_CROSSOVER.md)** – Detaillierte Script-Dokumentation mit Architektur & Datenfluss
- **[CHANGELOG_OFFLINE_REALTIME_MA_CROSSOVER](../CHANGELOG_OFFLINE_REALTIME_MA_CROSSOVER.md)** – Changelog des Scripts

### Code-Referenzen

- `scripts/run_offline_realtime_ma_crossover.py` – Das Haupt-Script
- `src/execution/pipeline.py` – Execution-Pipeline
- `src/orders/paper.py` – Paper-Order-Executor
- `src/offline/offline_realtime_report.py` – Report-Modul
- `src/offline/offline_realtime_meta_report.py` – Meta-Report-Modul (optional)

---

Damit hast du einen klaren Operator-Workflow für deine **OfflineRealtime Safety Sandbox** – ready für tägliche Nutzung & zukünftige Auswertung (Dashboards, Vergleiche mit Backtests, Testnet, Live).









