# Peak_Trade — Doubleplay Core Recovery Memo

Stand: 2026-04-16
Status: Read-only Zielbild- und Forensik-Memo
Zweck: Dieses Dokument soll Cursor eine eindeutige, belastbare Orientierung geben, **welches Kernsystem fachlich gemeint ist**, **welche Teile heute im Repo sichtbar sind**, **welche Teile nur als Sollbild dokumentiert sind**, und **welche Annahmen vor jeglichem Umbau ausdrücklich verboten sind**.

---

## 1. Executive Summary

Das gewünschte Kernsystem von Peak_Trade ist **nicht** einfach „Regime Detection + Strategy Switching + Execution“.
Das gemeinte Zielsystem ist eine **mehrschichtige Futures-Trading-Architektur** mit:

1. **Universe-Selektion / Marktauswahl**
2. **Richtungslogik via Doubleplay**
3. **Strategie-Einbettung in die Richtungslogik**
4. **Scope-/Budget-/Capital-Envelope**
5. **Kapital- und Exposure-Kappung**
6. **harte Safety-/Kill-Switches**
7. **gestufte Freigabe bis Execution**

Die bisherigen read-only Forensik-Schritte zeigen:

- **Doubleplay** ist im Repo aktuell vor allem als **Roadmap-/Sollbild** klar sichtbar.
- **Regime Detection / Strategy Switching** ist im Repo als **anderes Konzept** sichtbar und darf **nicht** automatisch mit Doubleplay gleichgesetzt werden.
- **Risk / Safety / Live-Gates / staged release** sind deutlich im Repo materialisiert.
- **Universe-/Selection-Logik** ist wahrscheinlich nicht verloren, sondern lebt verteilt weiter, insbesondere über:
  - `scripts&#47;scan_markets.py`
  - `run_market_scan.py`
  - `src&#47;experiments&#47;topn_promotion.py`
  - `config&#47;risk_liquidity_gate_paper.toml`
- Die **innere Mitte** des ursprünglichen Zielsystems — also **Doubleplay + Strategy embedding + Scope/Capital Envelope** — ist **nicht als klarer, durchgehender Ist-Pfad** sichtbar.

Dieses Memo ist deshalb **kein Umbauplan**, sondern eine **kanonische fachliche Klarstellung**, wohin die Reise gehen soll.

---

## 2. Das gewünschte Kernsystem

### 2.1 Nicht das Ziel

Nicht gemeint ist ein System, das nur:

- Regime-Labels erzeugt,
- Strategien umschaltet,
- dann direkt in bestehende Execution-/Policy-/Gates läuft.

Das ist nützlich, aber **nicht identisch** mit dem gewünschten Kernsystem.

### 2.2 Das eigentliche Zielbild

Das gemeinte System ist ein **mehrstufiger Entscheidungs- und Einsatzrahmen**:

```text
Universe Selection
    -> Doubleplay
        -> Strategy Embedding
            -> Scope / Capital Envelope
                -> Risk / Exposure Caps
                    -> Safety / Kill-Switches
                        -> staged Execution Enablement
```

Dabei gilt:

- **Doubleplay** ist die fachliche Mitte.
- **Strategien** sind nicht automatisch Ersatz für Doubleplay, sondern sollen in die Richtungslogik eingebettet werden.
- **Scope** ist nicht nur „Risk am Rand“, sondern ein eigener Kernbaustein.
- **Safety / Gates / Enablement** bleiben fail-closed und nachgelagert.

---

## 3. Fachliche Zielarchitektur

## 3.1 Universe-Selektion / Marktauswahl

### Zweck
Vor der Richtungsentscheidung wird eine begrenzte Menge handelbarer Futures ausgewählt.

### Gewünschte Funktion
Beispielhaft:

- die 20 stärksten bzw. geeignetsten Futures auswählen
- Ranking / Filter nach z. B.:
  - Liquidität
  - Volumen
  - Open Interest
  - Trendstärke
  - Volatilität
  - Marktqualität
  - Stabilität / Datenqualität

### Zielrolle im Stack
Die Universe-Selektion ist **vorgelagert**.
Doubleplay und Strategien arbeiten nicht auf dem ganzen Marktuniversum, sondern auf einer qualifizierten Vorauswahl.

### Aktuelle Repo-Evidenz (read-only, noch nicht final)
Wahrscheinlich relevante Reste / Nachfolger:

- `scripts&#47;scan_markets.py`
- `run_market_scan.py`
- `src&#47;experiments&#47;topn_promotion.py`
- `config&#47;risk_liquidity_gate_paper.toml`
- `scripts&#47;run_portfolio_robustness.py`

### Wichtige Klarstellung
`Crawler` war vermutlich entweder:
- der frühere umgangssprachliche Name dieses Blocks, oder
- ein naher Spezialpfad.

Aktuell ist am wahrscheinlichsten, dass die Funktion heute eher unter **scan / market scan / topn / liquidity gate / promotion** weiterlebt.

---

## 3.2 Doubleplay als fachliche Mitte

### Zweck
Doubleplay trifft pro ausgewähltem Markt eine **Richtungsentscheidung**:

- LONG
- SHORT
- FLAT

### Gewünschte Struktur
Doubleplay ist **nicht** bloß ein einzelnes Signal, sondern ein Meta-Layer mit zwei Richtungsspezialisten:

- **Bull / Long Specialist**
- **Bear / Short Specialist**

Darüber liegt ein **Switch-Gate / Meta-Controller**, der den Endzustand bestimmt.

### Erwartete Eigenschaften
- Hysterese
- Cooldown
- Min-Hold
- Sideways-Band / Konfliktbehandlung
- fail-closed Verhalten
- klare Zustandsübergänge

### Soll-Semantik
Sinngemäß:

- Bull-/Long-Specialist bewertet Aufwärtskontext
- Bear-/Short-Specialist bewertet Abwärtskontext
- Switch-Gate entscheidet LONG / SHORT / FLAT

### Aktueller read-only Befund
Diese Logik ist als **Sollbild** insbesondere in den LevelUp-Roadmaps sichtbar, aber **nicht als sauberer Ist-Codepfad belegt**.

Wahrscheinlich wichtigste Soll-Dokumente:

- `docs&#47;roadmap&#47;PeakTrade_LevelUp_Roadmap_Evidence.md`
- `docs&#47;roadmap&#47;PeakTrade_LevelUp_Roadmap_Evidence_20260211_doubleplay_leverage50.md` <!-- pt:ref-target-ignore -->

### Wichtige Negativabgrenzung
Die heute sichtbare Regime-Schicht ist **nicht automatisch** die Doubleplay-Implementierung.

---

## 3.3 Strategie-Einbettung

### Grundentscheidung
Die favorisierte Zielrichtung ist aktuell **Variante B**:

> Strategien liegen innerhalb der jeweiligen Richtungs-Spezialisten.

Also:

- Bull-Specialist verarbeitet long-/bull-fokussierte Strategien
- Bear-Specialist verarbeitet short-/bear-fokussierte Strategien

### Warum B bevorzugt wird
B wirkt fachlich ausgeklügelter und näher an der ursprünglichen Intention:

- Strategien als „Motoren“ je Seite
- Doubleplay als Hülle / Meta-Entscheider
- keine bloße additive Signalmischung ohne Richtungszuständigkeit

### Nicht gemeint
Nicht gewünscht ist, dass „Strategie-Switching“ das Doubleplay einfach ersetzt.

### Read-only Repo-Befund
Heute sichtbar:

- Regime Detection
- Strategy Switching
- Strategy Mapping

Wahrscheinliche Dateien:

- `docs&#47;REGIME_DETECTION_AND_STRATEGY_SWITCHING_PHASE_28.md`
- `tests&#47;test_regime_integration.py`
- `src&#47;backtest&#47;engine.py`
- `src&#47;execution&#47;pipeline.py`

### Kritische Klarstellung
Regime-/Strategy-Switching kann ein **Teilbaustein** sein, aber ist derzeit fachlich **nicht dasselbe** wie:

- Bull-Specialist
- Bear-Specialist
- Doubleplay Meta-Gate

---

## 3.4 Scope / Budget / Capital Envelope

### Zweck
Das System darf nicht automatisch das gesamte eingezahlte Kapital operationalisieren.

### Beispiel
Wenn 1000 EUR auf Kraken liegen, soll das System **nicht automatisch alles handeln dürfen**.
Es soll nur ein bewusst abgeleiteter Teil **deployable / tradable** sein, z. B. 300 EUR.

### Gewünschte Schichten
Aus Kontokapital wird schrittweise abgeleitet:

1. **Account Equity / Wallet Balance**
2. **tradable scope**
3. **deployable scope**
4. **pro Markt / pro Seite / pro Signal begrenzter Anteil**
5. **nur dann konkrete Positions- oder Order-Ideen**

### Das ist ein eigener Kernbaustein
Scope ist **nicht** bloß ein Parameter im Risk-Modul.
Scope ist eine eigene **Capital Envelope**, also eine vorgeschaltete Hülle, die festlegt, wie viel Kapital überhaupt in den aktiven Trading-Raum gelangen darf.

### Aktueller Repo-Befund
Die exakte frühere Scope-Semantik ist noch **nicht sauber wiedergefunden**.
Es gibt aber starke Hinweise, dass Teile heute in Risk-/Safety-/Limits-Schichten verteilt liegen.

Wahrscheinlich relevante Dateien:

- `src&#47;live&#47;risk_limits.py`
- `src&#47;live&#47;safety.py`
- `src&#47;live&#47;live_gates.py`
- `tests&#47;test_environment_and_safety.py`

### Status
- als **gewünschter Kernbaustein** eindeutig
- als **heutige explizite Repo-Schicht** noch unklar / fragmentarisch

---

## 3.5 Kapital- und Exposure-Kappung

### Zweck
Selbst innerhalb des deployable scope gelten harte Obergrenzen.

### Erwartete Cap-Arten
Beispielhaft:

- max notional
- max position
- leverage cap
- max order size
- session loss cap
- daily loss cap
- drawdown cap
- correlation cap
- per-market caps
- per-side caps
- portfolio caps

### Rolle im Stack
Dieser Block kommt **nach** Scope / Capital Envelope.
Risk Caps begrenzen also nicht das Gesamtkapital direkt, sondern den bereits freigegebenen operativen Teil.

### Aktueller Repo-Befund
Dieser Block ist im Repo am ehesten sichtbar und plausibel materialisiert.

Wahrscheinlich relevante Dateien:

- `src&#47;live&#47;risk_limits.py`
- `src&#47;live&#47;safety.py`
- `src&#47;live&#47;live_gates.py`
- `src&#47;execution&#47;pipeline.py`
- `docs&#47;risk&#47;KILL_SWITCH_RUNBOOK.md`

### Status
- **stark sichtbar**
- wahrscheinlich im Ist-System vorhanden
- aber nicht automatisch identisch mit der früheren Scope-/Envelope-Logik

---

## 3.6 Harte Safety-/Kill-Switches

### Zweck
Fail-closed Schutzschicht über allem, was Richtung Kapitalpfad geht.

### Erwartete Eigenschaften
- enabled / armed / confirm token
- deny-by-default
- stale data block
- kill-switch
- fail-closed bei Unsicherheit
- keine implizite Live-Freischaltung
- keine autonomen Overrides

### Aktueller Repo-Befund
Dieser Block ist klar sichtbar und wahrscheinlich gut materialisiert.

Wahrscheinlich relevante Dateien:

- `src&#47;live&#47;safety.py`
- `src&#47;live&#47;live_gates.py`
- `src&#47;live&#47;risk_limits.py`
- `docs&#47;risk&#47;KILL_SWITCH_RUNBOOK.md`
- `docs&#47;LIVE_OPERATIONAL_RUNBOOKS.md`
- `tests&#47;test_environment_and_safety.py`

### Status
- **stark vorhanden**
- operativ und konzeptionell zentral
- vermutlich besser materialisiert als Doubleplay selbst

---

## 3.7 Gestufte Freigabe bis Execution

### Zweck
Kein direkter Sprung in Live.
Stattdessen klar gestufte Umgebungen und Freigaben.

### Erwartete Pipeline
Zumindest sinngemäß:

- Research
- Backtest
- Shadow / Paper
- Testnet
- Live (nur bei expliziter, gegateter Freigabe)

### Aktueller Repo-Befund
Diese Schicht ist klar sichtbar.

Wahrscheinlich relevante Dateien:

- `src&#47;execution&#47;pipeline.py`
- `docs&#47;LIVE_OPERATIONAL_RUNBOOKS.md`
- `tests&#47;test_live_shadow_session.py`
- `tests&#47;test_live_session_registry.py`
- `src&#47;webui&#47;ops_cockpit.py`
- `tests&#47;webui&#47;test_ops_cockpit.py`

### Status
- **stark sichtbar**
- heute eher stärker als die alte Doubleplay-Mitte

---

## 4. Was heute im Repo wahrscheinlich vorhanden ist

## 4.1 Stark sichtbar / wahrscheinlich materialisiert

- Risk limits
- Safety / live gates
- Kill-switch-/fail-closed-Denke
- staged release / staged execution enablement
- operatorische / governance-nahe Schutzschichten

## 4.2 Teilweise sichtbar / semantisch verschoben

- Strategie-Einbettung
- Regime-Schichten
- Universe-/Selection-Logik
- Liquidity-/TopN-/Scan-Familie

## 4.3 Weiterhin schwach oder nur als Sollbild sichtbar

- Doubleplay als zusammenhängender Runtime-Kern
- Bull-/Bear-Specialists als explizite Produktionspfade
- Switch-Gate LONG / SHORT / FLAT als kanonischer Ist-Codepfad
- Scope / deployable capital als explizite First-Class-Envelope

---

## 5. Was ausdrücklich **nicht** angenommen werden darf

Vor jeglichem Coding sind folgende Annahmen verboten:

### 5.1 Verbotene Gleichsetzungen

Nicht annehmen, dass:

- `src&#47;regime` = Doubleplay <!-- pt:ref-target-ignore -->
- Strategy Switching = Bull/Bear Specialist Layer
- bestehende Execution Pipeline bereits zwei Richtungsmodelle routet
- Risk Limits automatisch die frühere Scope-/Capital-Envelope vollständig ersetzen
- „LevelUp im Repo“ bedeutet, dass die gesamte frühere Doubleplay-Architektur heute fertig implementiert ist

### 5.2 Verbotene Kurzschlüsse

Nicht einfach:

- `scan_markets.py` als kompletten Crawler-Kern interpretieren, ohne die Übergaben zu prüfen
- `risk_limits.py` als vollständige deployable-capital-Logik behandeln, ohne die Scope-Semantik zu verifizieren
- `Phase 28 Regime Detection` als finale Antwort auf die ursprüngliche Richtungslogik behandeln
- Roadmap-Sollpfade als Ist-Pfade ausgeben

---

## 6. Kanonische Arbeitsannahme für die nächsten Schritte

Bis zur weiteren Klärung gilt fachlich:

### 6.1 Gewünschtes Zielsystem

```text
Universe Selection
    -> Bull Specialist + Bear Specialist
        -> Doubleplay Switch-Gate (LONG / SHORT / FLAT)
            -> Strategy Embedding je Richtung
                -> Scope / Capital Envelope
                    -> Risk / Exposure Caps
                        -> Safety / Kill-Switches
                            -> staged Execution Enablement
```

### 6.2 Praktische Interpretation
- Universe-Selektion ist vorgelagert
- Doubleplay ist die Mitte
- Strategien sind in Doubleplay einzubetten, nicht umgekehrt
- Scope ist ein Kernbaustein
- Risk, Safety und Execution bleiben streng fail-closed

### 6.3 Status dieser Annahme
Das ist **das gewünschte Zielbild**, nicht die Behauptung, dass das Repo heute schon genau so verdrahtet ist.

---

## 7. Wichtigste bekannte Evidenzquellen

## 7.1 Für das Sollbild / die frühere Fachlogik
- `docs&#47;roadmap&#47;PeakTrade_LevelUp_Roadmap_Evidence.md`
- `docs&#47;roadmap&#47;PeakTrade_LevelUp_Roadmap_Evidence_20260211_doubleplay_leverage50.md` <!-- pt:ref-target-ignore -->

## 7.2 Für Selection / Universe / Crawler-Nachfolger
- `scripts&#47;scan_markets.py`
- `run_market_scan.py`
- `src&#47;experiments&#47;topn_promotion.py`
- `config&#47;risk_liquidity_gate_paper.toml`
- `scripts&#47;run_portfolio_robustness.py`

## 7.3 Für Regime / Strategy Switching
- `docs&#47;REGIME_DETECTION_AND_STRATEGY_SWITCHING_PHASE_28.md`
- `tests&#47;test_regime_integration.py`
- `src&#47;backtest&#47;engine.py`

## 7.4 Für Risk / Safety / staged release
- `src&#47;live&#47;risk_limits.py`
- `src&#47;live&#47;safety.py`
- `src&#47;live&#47;live_gates.py`
- `src&#47;execution&#47;pipeline.py`
- `docs&#47;risk&#47;KILL_SWITCH_RUNBOOK.md`
- `docs&#47;LIVE_OPERATIONAL_RUNBOOKS.md`
- `tests&#47;test_environment_and_safety.py`
- `tests&#47;test_live_shadow_session.py`
- `tests&#47;test_live_session_registry.py`

---

## 8. Reihenfolge für weitere read-only Klärung

Keine Mutation. Keine Architektur erfinden. Kein „schneller Umbau“.

### Phase A — Selection / Crawler
Ziel:
- verifizieren, was `scan_markets.py` und verwandte Dateien fachlich genau tun
- prüfen, ob Top-N / Liquidity / Ranking / Promotion wirklich den früheren Universe-Block abbilden

### Phase B — Scope / Capital Envelope
Ziel:
- in `risk_limits.py`, `safety.py`, `live_gates.py` prüfen, ob deployable capital / usable capital / scope / wallet semantics explizit oder implizit existieren

### Phase C — Strategy Embedding vs. Regime
Ziel:
- klären, ob bestehendes Regime-/Strategy-Switching als Baustein in Bull/Bear-Specialists taugt oder semantisch separat bleiben muss

### Phase D — Doubleplay Recovery Gap
Ziel:
- exakt auflisten, welche Teile von Doubleplay heute nur Roadmap-Soll sind
- und welche Übergabepunkte an bestehende Repo-Bausteine realistisch erscheinen

---

## 9. Was Cursor bei Folgearbeit beachten muss

### Harte Guardrails
- **read-only, bis ausdrücklich anders entschieden**
- nichts an Paper-/Shadow-/Evidence-Daten ändern
- keine Live-Freischaltung
- keine impliziten Runtime-Umbauten
- keine Gleichsetzung von Soll-Doku mit Ist-Code
- keine Vermischung mehrerer Konzepte ohne explizite Trennung

### Bewertungsdisziplin
Für jeden Fund ist explizit zu markieren:
- **Ist**
- **Teilweise**
- **Soll**
- **Fehlt**
- **unklar**

---

## 10. Schlussformel

Peak_Trade soll **nicht** in ein unscharfes Sammelsystem aus Regime, Strategy Switching und Safety Gates zerfallen.
Das gewünschte Ziel ist ein **klar lesbares Kernsystem** mit:

- Marktauswahl,
- richtungsspezifischer Doubleplay-Entscheidung,
- Strategien als eingebettete Spezialisten,
- bewusst begrenztem Capital Envelope,
- harten Risk-/Safety-Grenzen,
- und streng gegateter Execution.

Die read-only Forensik deutet darauf hin, dass:
- die **vordere Schicht** (Selection) teilweise noch lebt,
- die **äußere Schutzschicht** (Risk / Safety / staged execution) deutlich lebt,
- aber die **innere Doubleplay-Mitte** heute nicht mehr als sauberer End-to-End-Pfad sichtbar ist.

Genau diese Mitte ist der Kern der weiteren fachlichen Klärung.
