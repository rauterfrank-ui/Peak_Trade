# R&D-Playbook – Armstrong & El Karoui v1

**Version:** v1
**Stand:** Strategien sind Research-Stubs (Flat-Signale, keine Trades)
**Ziel:** Technische Integration nutzen, um einen klaren Research-Workflow für spätere Signal-Logik aufzubauen.

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
* Sweeps laufen **100% durch**, Metriken sind aktuell 0/NaN, weil die Strategien Flat-Signale generieren.

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

Typische Parameter:

* `vol_window`
* `vol_threshold_low`
* `vol_threshold_high`
* `use_ewm`
* `annualization_factor`

Ziel später:

* Für jedes Bar / jede Periode einen Regime-State bestimmen:

  * z.B. `LOW`, `MEDIUM`, `HIGH`
* Später nutzbar als:

  * Filter: „nur handeln in LOW/MEDIUM"
  * Switch: Wahl unterschiedlicher Strategien je nach Regime

### 4.3 Aktuelle Nutzung (v1 – Flat-Stubs)

Aktuell (Flat):

* Keine Trades, daher keine PnL-Metriken
* Aber: Sweep-Setup, Parameterraum, Runtime können getestet/verstanden werden.

Später:

* Sweeps über `vol_window` + `thresholds` helfen zu verstehen, wie stabil Regime-Klassifikationen sind.
* Ziel: Parameter-Sets finden, bei denen Regime logisch und stabil wirken (z.B. Anteil HIGH-Vol-Tage im realistischen Bereich).

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

1. **Signallogik implementieren** – Strategien von Flat-Stubs zu echten Signalen erweitern
2. **Event-Studien** – Armstrong-Turning-Points gegen historische Marktbewegungen validieren
3. **Regime-Stabilität testen** – El Karoui Regime-Klassifikation auf Robustheit prüfen
4. **Kombinierte Experimente** – Armstrong × El Karoui Interaktionen analysieren

---

**Kurzfassung:**

Dieses Playbook dokumentiert den aktuellen Stand der R&D-Strategien Armstrong & El Karoui, deren technische Integration validiert ist (Sweeps laufen 100%), aber deren Signallogik noch Research-Stubs sind. Es definiert den Workflow für die aktuelle Nutzung und das Zielbild für spätere Research-Iterationen.
