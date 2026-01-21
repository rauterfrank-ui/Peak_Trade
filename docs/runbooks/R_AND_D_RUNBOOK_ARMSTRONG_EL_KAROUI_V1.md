# R&D-Runbook – ArmstrongCycleStrategy & ElKarouiVolModelStrategy (v1)

**Scope:** R&D-/Research-Track für zyklus- und volatilitätsbasierte Strategien.  
**Status:** v1 – *nur* für `offline_backtest` & `research` (keine Live-Freigabe).  

**Strategien:**

- `ArmstrongCycleStrategy`  
  - Pfad: `src/strategies/armstrong/armstrong_cycle_strategy.py`
  - TIER: `r_and_d`
  - ALLOWED_ENVIRONMENTS: `["offline_backtest", "research"]`
  - IS_LIVE_READY: `False`

- `ElKarouiVolModelStrategy`  
  - Pfad: `src/strategies/el_karoui/el_karoui_vol_model_strategy.py`
  - TIER: `r_and_d`
  - ALLOWED_ENVIRONMENTS: `["offline_backtest", "research"]`
  - IS_LIVE_READY: `False`


---

## 1. Ziel & Kontext

Dieses Runbook beschreibt, wie die beiden R&D-Strategien

- `ArmstrongCycleStrategy` (Zyklus-/Cycle-basierter Ansatz, Armstrong-Style) und  
- `ElKarouiVolModelStrategy` (Vol-/Diffusions-/BSDE-inspirierter Ansatz)

im bestehenden Peak_Trade-Research-Stack betrieben werden:

- **Wie starten?** (CLI-Commands / R&D-Dashboard)  
- **Welche Standard-Experimente?** (Baseline, Sensitivitäten, Sweeps)  
- **Wie auswerten?** (R&D-API, Reports, Gallery & Comparison)  
- **Was ist verboten?** (kein Live, keine Orders, kein Auto-Promotion-Shortcut)


---

## 2. Safety-Gates & harte Grenzen

1. **Tier & Environment**
   - Beide Strategien sind klar als `TIER = "r_and_d"` markiert.
   - Erlaubte Environments:
     - `offline_backtest`
     - `research`
   - **Verboten:**
     - `paper_trade`
     - `testnet`
     - `live`

2. **Risk / Governance**
   - Keine Orders, keine Verbindung zu Live-Execution-Pipeline.
   - Ergebnisse dürfen **nicht** direkt in Live-Runs übernommen werden, sondern:
     1. Dokumentation in R&D-Reports.
     2. Review (Code & Statistik).
     3. Ggf. Migration in eine produktive Strategy-Klasse (neue Datei, neues TIER).

3. **Dok-Referenzen**
   - R&D-Track / Strategy-Library-Docs (Phasen 75–78).
   - Strategy-Tiering-Konfiguration (Tiers + erlaubte Environments).
   - Live-/Testnet-Governance-Dokumente für generelle Safety-Policies.


---

## 3. Gemeinsame Voraussetzungen

### 3.1 Environment & Projekt-Setup

```bash
cd ~/Peak_Trade
source .venv/bin/activate
```

Prüfen:

* `pytest` läuft durch (oder mindestens die relevanten Strategy-/R&D-Tests).
* Config-Dateien für die beiden Strategien existieren (z.B. in `config&#47;strategies&#47;` oder entsprechend deiner Struktur).

### 3.2 R&D-Experiment-Registry

Alle Runs werden idealerweise über die bestehende Experiment-Registry angelegt, damit:

* der R&D-Dashboard (Overview),
* der Detail-View & Report-Viewer und
* die Gallery & Comparison-Views

die Runs automatisch anzeigen können.

Typische Run-Types:

* `backtest`
* `sweep`
* `walkforward`
* `monte_carlo` (falls unterstützt)
* `research_experiment` (falls vorhanden)

---

## 4. Standard-Workflow: ArmstrongCycleStrategy

### 4.1 Baseline-Backtest

**Ziel:** Verstehen, wie der Zyklus-Ansatz auf einem Referenzmarkt performt.

**Empfohlene Parameter (logisch, nicht technisch):**

* 1–2 Kern-Märkte (z.B. BTCUSD, ETHUSD, ggf. ein FX- oder Index-Future).
* Timeframe: z.B. 1D oder 4H (was im Setup vorgesehen ist).
* Historie: mindestens mehrere volle Zyklus-Längen.

**Schritte:**

1. Experiment starten (Beispiel-Command, ggf. an deine CLI anpassen):

   ```bash
   python scripts/research_cli.py strategy-profile \
       --strategy ArmstrongCycleStrategy \
       --symbol BTCUSD \
       --run-label "armstrong_baseline_btcusd"
   ```

2. Run-ID notieren (wird von der Registry generiert).

3. Im R&D-Dashboard:

   * Overview öffnen (R&D Hub).
   * Run in der Tabelle prüfen (Status, Laufzeit, Run-Type).
   * Detail-View öffnen:

     * Metriken (Sharpe, MaxDD, WinRate, Trades, PF).
     * Reports (HTML / Markdown / PNG) im Report-Viewer checken.

### 4.2 Parameter-Sensitivität

**Ziel:** Check, ob das Modell robust ist oder nur „spiky sweet spots" hat.

Typische Variationen:

* Zyklus-Länge(n) / Phasenverschiebungen.
* Stärke von Filtern (z.B. Trend-/Vol-Filter).
* Risiko-Skalierung (fixed vs. vol-basiert).

**Schritte (konzeptionell):**

1. Sweep-Config definieren (z.B. in einer Config-Datei oder direkt in der CLI).
2. R&D-Sweep über `research_cli.py` oder ein Sweep-Script starten.
3. Alle Runs landen in der Registry → im R&D-Dashboard:

   * Gallery & Comparison-View nutzen:

     * Beste Sharpe,
     * Beste Return,
     * Niedrigste MaxDD,
     * Stabilität über Märkte.

### 4.3 Stress-Szenarien

**Ziel:** Armstrong-Logik in schwierigen Marktphasen testen.

* Krisenphasen, Flash-Crashes, Sideways-Märkte.
* Ggf. spezielle Data-Slices oder Szenario-Files.

Workflow wie oben, aber mit expliziter Marktauswahl / speziellen Testperioden.

---

## 5. Standard-Workflow: ElKarouiVolModelStrategy

### 5.1 Baseline-Backtest

**Ziel:** Grundverständnis, wie das El-Karoui-inspirierte Vol-Modell in „normaler" Marktumgebung performt.

**Empfohlene Setup-Idee:**

* 1–3 liquide Underlyings (BTCUSD, ETHUSD, großer Index).
* Timeframe passend zur Implementierung (z.B. 1H oder 4H für Vol-Strukturen).
* Ausreichend lange Historie für robuste Vol-Schätzung.

**Schritte:**

```bash
python scripts/research_cli.py strategy-profile \
    --strategy ElKarouiVolModelStrategy \
    --symbol BTCUSD \
    --run-label "el_karoui_baseline_btcusd"
```

Dann analog zu Armstrong:

* Run-ID notieren,
* R&D-Hub öffnen,
* Details & Reports checken.

### 5.2 Volatility-Parameter-Variationen

**Ziel:** Sensitivität des Modells gegenüber Vol-Schätzfenster, Glättung, ggf. BSDE/HJB-bezogenen Hyperparametern.

Beispiele (konzeptionell):

* Kürzere vs. längere Vol-Fenster.
* Verschiedene „Regime-Schwellen" (Low/Medium/High Vol).
* Alternative Normalisierungen (z.B. log-Returns vs. einfache Returns).

Diese Variation möglichst über einen Sweep laufen lassen, sodass:

* die Runs in der R&D-Gallery visualisiert werden können,
* Comparison-View die „besten" Konfigurationen nach Metriken hervorhebt.

### 5.3 Tail- & Crash-Szenarien

ElKaroui/Vol-Modelle zeigen ihre Schwächen oft in extremen Tails. Daher:

* Spezielle Perioden mit starken Gaps und Vol-Spikes testen.
* Check:

  * Wird Exposure sauber reduziert?
  * Gibt es pathologische Over-Leverage-Situationen?
  * Wie viele Trades gehen in hoch-volatilen Phasen durch?

---

## 6. Auswertung & Reporting

### 6.1 Metriken

Mindestens:

* Annualized Return / Sharpe
* Max Drawdown / Max Daily Loss
* Win-Rate & Profit-Factor
* Anzahl Trades, Turnover
* ggf. Tail-Metriken (Worst k-Tage, CVaR, etc.)

### 6.2 R&D-Dashboard-Flows

1. **Overview (R&D Hub)**

   * Täglich: Check „Heute fertig" / „Aktuell laufend"-Kacheln.
   * Filter nach `run_type`, `tier = "r_and_d"`, ggf. nach Strategy-Name.

2. **Detail-View**

   * Für einzelne Run-IDs: Metriken, Status, Duration, Reports.
   * Konsistenz-Check:

     * stimmen Config, Symbol, Zeitraum mit der Experiment-Notiz überein?

3. **Gallery & Comparison**

   * Mehrere Run-IDs markieren.
   * Vergleichs-View nutzen, um:

     * klaren Sieger pro Kennzahl zu sehen,
     * aber v.a. **Stabilität** über Parameter / Märkte zu prüfen.

### 6.3 Dokumentation

Für relevante Experimente:

* Kurz-Report (Markdown) mit:

  * Ziel,
  * Setup (Strategie, Märkte, Perioden, Parameter),
  * wichtigsten Metriken,
  * Interpretation,
  * „Next Steps"-Entscheidung (verwerfen, weiter untersuchen, Richtung für Refactoring).

---

## 7. Promotion-Pfad (von R&D → produktiv)

**WICHTIG:** Dieses Runbook ist *kein* Freifahrtschein für Live-Gang.

Eine mögliche Pipeline:

1. **R&D-Phase**

   * Mehrere Zyklen von Baseline + Sweeps + Stress-Tests.
   * Saubere Doku im R&D-Track.

2. **Review-Phase**

   * Code-Review (Architektur, Test-Coverage, Edge Cases).
   * Metriken-Review (Robustheit, Overfitting-Risiko).

3. **Refactoring**

   * Ggf. neue produktive Strategy-Klasse ableiten.
   * TIER von `r_and_d` → `experimental` oder direkt `core_candidate`.
   * Tests und Doku für produktiven Track anpassen.

4. **Shadow-/Paper-Track**

   * Bevor *irgendetwas* in Testnet/Live landet:

     * Shadow-/Paper-Runs mit strengen Limits,
     * Monitoring & Alerts konfigurieren.

5. **Entscheidung**

   * Erst nach dokumentierter Shadow-/Paper-Phase kann ein Live-Gang diskutiert werden – außerhalb dieses Runbooks und nur über die regulären Governance-Prozesse.

---

## 8. Offene TODOs & Erweiterungen

* Detaillierte Parameter-Tabellen für beide Strategien ergänzen (sobald stabil).
* Konkrete Sweep-Konfigurationen (z.B. eigene TOML/JSON-Files) dokumentieren.
* Beispiele für „gute" und „schlechte" Runs inkl. Links zu Report-Files (HTML/PNG).
* Checkliste für „Promotion-Readiness" (z.B. minimale Anzahl unabhängiger Märkte, minimale Historiendauer, maximale akzeptierte Drawdowns etc.).

---

**Kurzfassung:**

Dieses Runbook beschreibt, wie die R&D-Strategien `ArmstrongCycleStrategy` und `ElKarouiVolModelStrategy` sicher, reproduzierbar und gut dokumentiert im Research-Stack betrieben werden – mit klaren Safety-Gates (kein Live), Standard-Workflows (Baseline, Sweeps, Stress) und einem strukturierten Pfad für mögliche Promotionen in den produktiven Strategy-Layer.
