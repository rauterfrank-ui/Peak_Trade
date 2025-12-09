# R&D-Experiment – Armstrong x El Karoui Kombi v1

**Version:** v1
**Status:** Spezifikation (Konzept & Scope festgelegt, Implementierung folgt)
**Betroffene R&D-Strategien:**

* `armstrong_cycle`
* `el_karoui_vol_model`

---

## 1. Ziel & Motivation

Dieses R&D-Experiment verknüpft zwei Research-Bausteine:

1. **Armstrong-Zyklenmodell (`armstrong_cycle`)**
   → Markiert zyklische „Turning Points" bzw. relevante Event-Fenster im Markt.

2. **El-Karoui-Volatilitäts-/Regime-Modell (`el_karoui_vol_model`)**
   → Klassifiziert das Volatilitätsumfeld in Regime (z.B. LOW / MEDIUM / HIGH).

**Ziel dieses Kombi-Experiments v1:**

* Einen reproduzierbaren Workflow definieren, der:

  * Armstrong-Events und El-Karoui-Regime **für denselben Markt & Zeitraum** zusammenführt,
  * deren gemeinsame Struktur analysiert (z.B. Häufung bestimmter Regime um Zyklus-Events),
  * und Hypothesen für spätere Trade-Strategien bzw. Meta-Filter ableitet.
* Noch **keine Live- oder Produktionslogik**, sondern:

  * reine R&D-Labels und Explorations-Analysen,
  * strikte Trennung von produktiven Strategien.

---

## 2. Scope & Rahmenbedingungen

### 2.1 Märkte & Timeframes

Für v1 wird der Scope bewusst eng gehalten:

* **Märkte (Beispiel):**

  * 1–2 liquide Krypto-Paare auf Kraken, z.B.:

    * `XBT/EUR` (oder `BTC/EUR`, abhängig von der internen Symbolkonvention)
    * optional: `ETH/EUR`
* **Timeframe:**

  * `1d` oder `4h` (je nach Standard im Projekt)
* **Zeitraum:**

  * z.B. letzte 3–5 Jahre (konfigurierbar über Experiment-Config)

Die konkrete Parametrisierung (Symbol, Timeframe, Start-/Enddatum) wird über die Experiment-Config gesteuert und in der Registry gespeichert.

### 2.2 Environments & Safety

* `tier = "r_and_d"`
* `is_live_ready = false`
* `allowed_environments = ["offline_backtest", "research"]`
* Keine Nutzung in:

  * Live-Track
  * Paper- oder Testnet-Flows
  * Auto-Promotion / produktiven Strategy-Gruppen

---

## 3. Eingänge & Parameter

### 3.1 Armstrong-Cycle-Strategie (`armstrong_cycle`)

Relevante Parameter (vereinfachtes Schema):

* `cycle_length_days`
* `event_window_days`
* `reference_date`

**Interpretation:**

* Aus `reference_date` und `cycle_length_days` werden zyklische Turning Points generiert.
* `event_window_days` definiert ein Fenster um jedes Event (z.B. ±N Tage).

### 3.2 El-Karoui-Vol-Modell (`el_karoui_vol_model`)

Relevante Parameter:

* `vol_window`
* `vol_threshold_low`
* `vol_threshold_high`
* `use_ewm` (bool)
* `annualization_factor`

**Interpretation:**

* Auf Basis von Rolling-/EWM-Volatilität werden Regime-Klassen gebildet:

  * `LOW`, `MEDIUM`, `HIGH` (konkrete Logik wird in der Strategie gekapselt).

---

## 4. Labels, Features & Kombi-States

### 4.1 Armstrong-Event-Label

Für jede Bar (t) im betrachteten Zeitraum:

* `armstrong_event_state_t` ∈ {`PRE_EVENT`, `EVENT`, `POST_EVENT`, `NONE`}

Beispielhafte Definition:

* `EVENT`: innerhalb von `event_window_days` um einen Zyklus-Turning-Point
* `PRE_EVENT`: Fenster vor dem Event (z.B. -2 × `event_window_days` bis -1 × `event_window_days`)
* `POST_EVENT`: Fenster nach dem Event (z.B. +1 × `event_window_days` bis +2 × `event_window_days`)
* `NONE`: außerhalb dieser Fenster

(v1 darf auch mit einem trivialeren Schema starten, z.B. nur `EVENT` vs. `NONE`)

### 4.2 El-Karoui-Regime-Label

Für jede Bar (t):

* `elkaroui_regime_t` ∈ {`LOW`, `MEDIUM`, `HIGH`}

Definition über die Strategieparameter:

* `LOW`: Volatilität < `vol_threshold_low`
* `HIGH`: Volatilität > `vol_threshold_high`
* `MEDIUM`: dazwischen

### 4.3 Kombinierter Label-State

Kombinierter State für jede Bar (t):

* `combo_state_t = (armstrong_event_state_t, elkaroui_regime_t)`

Interessante Kombis (Beispiele):

* `("EVENT", "HIGH")`
* `("EVENT", "MEDIUM")`
* `("EVENT", "LOW")`
* `("PRE_EVENT", "HIGH")`, `("POST_EVENT", "HIGH")`
* … plus Baseline `("NONE", regime)`.

Für Analysen können diese Kombis in Kategorien oder Buckets gruppiert werden, z.B.:

* `EVENT_HIGH_VOL`, `EVENT_MED_VOL`, `EVENT_LOW_VOL`
* `PRE_EVENT_HIGH_VOL`, etc.

---

## 5. Experiment-Design v1

### 5.1 Parameterstrategie (gegen Kombi-Explosion)

Um eine Parameterexplosion zu vermeiden, definieren wir für v1 einen **klar begrenzten Parameterraum**:

1. **Armstrong-Parameter-Sets:**

   * 1–2 sinnvolle Konfigurationen (z.B. zwei Zykluslängen / Fenstergrößen)
2. **El-Karoui-Parameter-Sets:**

   * 2–3 Konfigurationen (z.B. unterschiedliche `vol_window` / Thresholds)

Resultierende Kombi:

* z.B. **maximal 2 × 3 = 6 Parameter-Kombinationen** pro Markt & Timeframe.

Jede Kombination erzeugt ein eigenes Experiment / einen eigenen Run in der Registry.

### 5.2 Experiment-Schritte (konzeptionell)

Pro Markt/Timeframe:

1. **Daten laden**

   * Preiszeitreihe aus Data-Layer (Kraken-Loader etc.)
   * Zeitsynchronisierung sicherstellen (Index / Timezone bereits durch Strategien geprüft).

2. **Armstrong-Labeling**

   * `armstrong_cycle` auf die Zeitreihe anwenden (als Label-/Event-Generator, nicht als Trade-Strategie).
   * Für jede Bar: `armstrong_event_state_t`.

3. **El-Karoui-Regime-Labeling**

   * `el_karoui_vol_model` auf dieselbe Zeitreihe anwenden.
   * Für jede Bar: `elkaroui_regime_t`.

4. **Kombination**

   * Pro Bar `combo_state_t` bilden.
   * Zusätzliche Features berechnen:

     * künftige Returns: z.B. `ret_1d_fwd`, `ret_3d_fwd`, `ret_7d_fwd`
     * aktuelle Volatilität
     * ggf. Trend-Features (z.B. MA-Slope) für spätere Analysen.

5. **Auswertung (aggregiert)**

   * Häufigkeit der verschiedenen Kombi-States.
   * Durchschnittliche künftige Returns pro Kombi-State.
   * Verteilung starker Moves (z.B. |Return| > X%) über Kombi-States.
   * Optional: einfache Scoring-Metrik (z.B. Sharpe / T-Stat pro Kombi-State).

6. **Persistenz**

   * Speichern des Experiments in der Registry:

     * `run_id`
     * `run_type` (z.B. `"r_and_d_combi"`)
     * `tier = "r_and_d"`
     * Parameter beider Modelle
     * Markt, Timeframe, Zeitraum
   * Verlinkung zu einem Report (Markdown/HTML) mit:

     * Tabellen (Kombi-States × Kennzahlen)
     * optional Charts (z.B. Heatmaps).

---

## 6. Kennzahlen & Reporting

### 6.1 Kern-Metriken

Für jede relevante Kombi-Klasse (z.B. `EVENT_HIGH_VOL`, `EVENT_MED_VOL`, …):

* `count_bars` (Anzahl Bars in dieser Klasse)
* `avg_ret_1d_fwd`, `avg_ret_3d_fwd`, `avg_ret_7d_fwd`
* `std_ret_1d_fwd`, etc.
* Anteil großer Bewegungen:

  * `p(|ret_3d_fwd| > Schwelle)`
* Optional:

  * Sharpe-ähnliche Kennzahlen auf diesen bedingten Returns.

### 6.2 Reports

Pro Experiment/Run:

* **JSON/Registry:** alle Parameter + aggregierte Kennzahlen
* **Markdown/HTML-Report (optional v1, wünschenswert v2):**

  * Beschreibung von Setup & Parametern
  * Tabellen mit Kennzahlen pro Kombi-State
  * ggf. Heatmap:

    * x-Achse: Armstrong-State
    * y-Achse: El-Karoui-Regime
    * Farbe: z.B. avg_ret_3d_fwd oder Hit-Rate großer Moves.

Reports erscheinen über die bestehende R&D-API/Report-Gallery im Web-UI.

---

## 7. Integration in Peak_Trade

### 7.1 Registry & Run-Type

* Neuer `run_type` für dieses Experiment, z.B.:

  * `run_type = "armstrong_elkaroui_combi"`
* `tier = "r_and_d"`
* Kategorie, z.B.:

  * `experiment_category = "label_analysis"`

### 7.2 R&D-Dashboard & API

* Experimente erscheinen im **R&D Experiments Overview**:

  * Filterbar nach `run_type`, `tier`, `experiment_category`.
* Detail-View:

  * zeigt:

    * Markt, Zeitraum, Timeframe
    * Parameter Armstrong/El-Karoui
    * Kern-Kennzahlen
    * Links zu Reports (Markdown/HTML/PNG).

---

## 8. Safety & Governance

* Dieses Experiment erzeugt **nur Labels und Analysen**, keine Trade-Ausführung.
* Keine direkte Anbindung an Live-/Paper-/Testnet-Umgebungen.
* Jede spätere Nutzung der Ergebnisse als Filter/Signal in produktiven Strategien erfordert:

  * separate Spezifikation,
  * zusätzliche Tests,
  * explizite Freigabe in einer eigenen Phase.

---

## 9. Nächste Schritte (Implementierungs-Roadmap)

1. **Minimal-Implementierung v1:**

   * Experiment-Skeleton (Code) anlegen:

     * Daten laden,
     * beide Label-Engines ausführen (Armstrong & El-Karoui),
     * Kombi-States + einfache Statistik berechnen.
   * Registry-Anbindung (`run_type`, `tier`, `experiment_category`).

2. **Einfache Reporting-Fassung:**

   * Markdown-Report mit:

     * Setup,
     * Parameter-Tabellen,
     * Kennzahlen pro Kombi-State.

3. **v2+:**

   * Visualisierungen (Heatmaps, Regime-Verlauf über Zeit).
   * Vergleich mehrerer Märkte / Timeframes.
   * Ableitung konkreter Hypothesen für Meta-Filter-Logik.
