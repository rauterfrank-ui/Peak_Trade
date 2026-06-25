---
title: "Master V2 Double Play Kill-All vs State-Switch Favorable Adverse Extreme Moves Acceptance v0"
status: "DRAFT"
owner: "ops"
last_updated: "2026-06-25"
docs_token: "DOCS_TOKEN_MASTER_V2_DOUBLE_PLAY_KILL_ALL_STATE_SWITCH_FAVORABLE_ADVERSE_EXTREME_MOVES_ACCEPTANCE_V0"
source_intake: "downloads/Peak_Trade_Kill_All_vs_State_Switch_Favorable_Adverse_Extreme_Moves_v1.md"
source_sha256: "8db9bdc5ea6980d37761b3ddfb6e5ad3b2889abf17a81e3a31589b6d7a8161af"
---

## Canonical acceptance and reconciliation basis

This document is the **canonical fachliche acceptance and reconciliation ground** for Kill-All vs State-Switch semantics under favorable/adverse extreme moves. It complements (does not replace) [MASTER_V2_DOUBLE_PLAY_TRADING_LOGIC_MANIFEST_V0.md](MASTER_V2_DOUBLE_PLAY_TRADING_LOGIC_MANIFEST_V0.md).

**Non-authority:** docs-only; `live_authorization=false`; `orders=0`; no runtime permission.

# Peak_Trade — Kill-All vs. State-Switch bei extremen Marktbewegungen

## Fachliche Abgrenzung für Master V2 / Double Play

**Dokumenttyp:** Fachliche Klarstellung und spätere Prüfgrundlage  
**Systemkontext:** Peak_Trade, Master V2 / Double Play  
**Geltungsbereich:** Modell-, Safety- und Governance-Semantik  
**Nicht enthalten:** Live-Autorisierung, Orderausführung, konkrete Exit-Implementierung, Anlageberatung  
**Sicherheitsstatus:** `live_authorization=false`, `orders=0`

---

# 1. Zweck dieses Dokuments

Dieses Dokument behandelt eine zentrale Sicherheitsfrage von Master V2 / Double Play:

> Wie muss das System zwischen einer starken günstigen Marktbewegung, einer starken ungünstigen Marktbewegung und einer echten systemischen Gefahr unterscheiden?

Die Kerngefahr besteht darin, extreme Marktbewegungen pauschal als Anomalie oder Sicherheitsverletzung zu behandeln.

Eine solche pauschale Regel wäre fachlich falsch:

- Ein starker Kursanstieg kann für einen aktiven Bull-/Long-Layer sehr günstig sein.
- Ein starker Kursverfall kann für einen aktiven Bear-/Short-Layer sehr günstig sein.
- Dieselben Bewegungen können für die jeweils entgegengesetzte Seite gefährlich sein.
- Unabhängig von der Richtung kann eine systemische Unsicherheit trotzdem einen globalen Sicherheitsstopp rechtfertigen.

Deshalb müssen **Richtung**, **aktive Exponierung**, **Marktqualität**, **Datenqualität**, **Ausführbarkeit** und **globale Sicherheitsinvarianten** getrennt bewertet werden.

---

# 2. Bull, Bear, State-Switch und Kill-All

## 2.1 Bull-/Long-Layer

Der Bull-Layer ist für steigende Märkte vorgesehen.

Vereinfacht:

```text
LONG_ACTIVE
+ Preis steigt
= günstige Richtungsbewegung
```

Der aktive Long-Layer profitiert grundsätzlich von steigenden Preisen.

---

## 2.2 Bear-/Short-Layer

Der Bear-Layer ist für fallende Märkte vorgesehen.

Vereinfacht:

```text
SHORT_ACTIVE
+ Preis fällt
= günstige Richtungsbewegung
```

Der aktive Short-Layer profitiert grundsätzlich von fallenden Preisen.

---

## 2.3 State-Switch

Der State-Switch ist der normale Mechanismus für den Wechsel zwischen Bull und Bear.

Beispiele:

```text
LONG_ACTIVE
→ bestätigter Downscope
→ SWITCH_LONG_TO_SHORT_PENDING
→ LONG_BLOCKED
→ SHORT_ARMED
→ SHORT_ACTIVE
```

```text
SHORT_ACTIVE
→ bestätigter Upscope
→ SWITCH_SHORT_TO_LONG_PENDING
→ SHORT_BLOCKED
→ LONG_ARMED
→ LONG_ACTIVE
```

Der State-Switch behandelt eine Richtungsänderung des Marktes.

Er ist **kein Not-Aus**.

---

## 2.4 Kill-All

Kill-All ist ein separater globaler Sicherheitszustand.

Seine Aufgabe ist nicht, normale Marktbewegungen zu klassifizieren, sondern das System bei einer schwerwiegenden Sicherheitsverletzung fail-closed zu blockieren.

Vereinfacht:

```text
KILL_ALL
→ Long blockiert
→ Short blockiert
→ keine neue Modellfreigabe
→ live_authorization=false
→ orders=0
```

Kill-All darf daher nicht mit dem normalen Bull↔Bear-Wechsel verwechselt werden.

---

# 3. Zentrale Invariante

## Große Bewegung ist nicht automatisch Gefahr

Eine starke Marktbewegung kann sein:

1. günstig für die aktive Seite,
2. ungünstig für die aktive Seite,
3. neutral für die Richtungslogik, aber operativ unsicher,
4. ein echter systemischer Sicherheitsbruch.

Daraus folgt:

```text
extreme_price_move != automatic_kill_all
```

Ein Kill-All allein aufgrund hoher absoluter Preisänderung wäre zu grob und könnte profitable Trends unnötig abschneiden.

---

# 4. Die drei fachlich getrennten Hauptklassen

## 4.1 FAVORABLE_DIRECTIONAL_MOVE

Eine starke Bewegung in Richtung der aktiven Seite.

### Long-Beispiel

```text
ACTIVE_SIDE=LONG
PRICE_MOVE=stark positiv
SIGNED_EFFECT=günstig
```

### Short-Beispiel

```text
ACTIVE_SIDE=SHORT
PRICE_MOVE=stark negativ
SIGNED_EFFECT=günstig
```

### Erwartete Reaktion

```text
→ aktive Seite nicht allein wegen der Stärke blockieren
→ Dynamic Boundaries nachziehen
→ Trailing Anchor aktualisieren
→ Downscope-/Upscope-Grenzen adaptieren
→ Hard Limits weiter respektieren
→ Safety- und Datenqualität separat prüfen
```

Die starke Bewegung ist zunächst ein Gewinnfall, kein Kill-All-Fall.

---

## 4.2 ADVERSE_DIRECTIONAL_MOVE

Eine Bewegung gegen die aktive Seite.

### Long-Beispiel

```text
ACTIVE_SIDE=LONG
PRICE_MOVE=stark negativ
SIGNED_EFFECT=ungünstig
```

### Short-Beispiel

```text
ACTIVE_SIDE=SHORT
PRICE_MOVE=stark positiv
SIGNED_EFFECT=ungünstig
```

### Erwartete Reaktion

```text
→ Scope-Event auswerten
→ Hysterese beachten
→ Confirmation beachten
→ Cooldown beachten
→ gegebenenfalls State-Switch einleiten
→ nicht automatisch Kill-All
```

Eine ungünstige Richtungsbewegung ist primär ein Fall für die State Machine und die Side-Switch-Logik.

---

## 4.3 SYSTEMIC_SAFETY_FAILURE

Ein Zustand, in dem das System Markt, Daten, Exponierung oder Ausführbarkeit nicht mehr zuverlässig kontrollieren kann.

Mögliche Beispiele:

- Marktdaten fehlen oder sind stale.
- Mark Price, Index Price und Last Price sind widersprüchlich.
- Preisfeeds divergieren außerhalb erlaubter Grenzen.
- Spread oder Liquidität kollabieren.
- Venue oder Netzwerk ist nicht zuverlässig erreichbar.
- Positionen oder Orders können nicht reconciled werden.
- Margin- oder Liquidationspuffer sind nicht mehr vertrauenswürdig.
- Die effektive Leverage verletzt Hard Limits.
- Beide Seiten erscheinen gleichzeitig aktiv.
- Governance- oder Evidence-Invarianten sind gebrochen.
- Der interne Zustand ist inkonsistent.
- Ein explizites `KILL_ALL_REQUIRED`-Signal liegt vor.

### Erwartete Reaktion

```text
→ beide Seiten blockieren
→ keine neue Aktivierung
→ keine neue Modellfreigabe
→ fail-closed
→ definierte operative Sicherungsstrategie
```

Hier ist Kill-All fachlich gerechtfertigt, auch wenn die aktuelle Preisrichtung für die aktive Position günstig erscheint.

---

# 5. Richtungsabhängige Bewertung

Eine einfache Grundidee ist die Bewertung des signierten Bewegungseffekts:

```text
signed_move_effect =
    position_direction × price_move
```

Vereinfachte Interpretation:

| Aktive Seite | Marktbewegung | Grundwirkung |
|---|---|---|
| Long | Preis steigt | günstig |
| Long | Preis fällt | ungünstig |
| Short | Preis fällt | günstig |
| Short | Preis steigt | ungünstig |

Diese Klassifikation ist notwendig, aber nicht ausreichend.

Zusätzlich müssen mindestens folgende Dimensionen geprüft werden:

- Datenqualität
- Mark Price / Index Price / Last Price
- Spread
- Liquidität
- Slippage-Risiko
- Margin-Puffer
- Liquidationsnähe
- Leverage
- Venue-Verfügbarkeit
- Reconciliation-Zustand
- Governance- und Evidence-Kohärenz

---

# 6. Beispiel: Bull aktiv und Markt schießt nach oben

## Situation

```text
STATE=LONG_ACTIVE
MARKET_MOVE=extrem positiv
```

## Fachlich richtige Interpretation

Die Bewegung ist für den Long-Layer zunächst günstig.

Die gewünschte Reaktion ist:

```text
neues Hoch
→ Anchor nach oben aktualisieren
→ Downscope-Boundary nachziehen
→ Hysterese und Volatilitätsband adaptieren
→ Long weiter halten, solange Hard Limits und Safety intakt sind
```

Kill-All darf nicht allein deshalb auslösen, weil:

- die Bewegung ungewöhnlich groß ist,
- die kurzfristige Volatilität steigt,
- der Preis neue Extremwerte erreicht.

## Kill-All wäre nur gerechtfertigt, wenn zusätzlich

- Datenquellen widersprüchlich sind,
- Preisqualität nicht verlässlich ist,
- Venue oder Netzwerk ausfällt,
- Margin-/Leverage-Grenzen verletzt werden,
- interne Zustände inkonsistent werden,
- Reconciliation unmöglich ist,
- eine globale Safety-Invariante verletzt ist.

---

# 7. Beispiel: Bear aktiv und Markt fällt stark

## Situation

```text
STATE=SHORT_ACTIVE
MARKET_MOVE=extrem negativ
```

## Fachlich richtige Interpretation

Die Bewegung ist für den Short-Layer zunächst günstig.

Die gewünschte Reaktion ist:

```text
neues Tief
→ Anchor nach unten aktualisieren
→ Upscope-Boundary nachziehen
→ Bear weiter halten, solange Hard Limits und Safety intakt sind
```

Ein massiver Preisverfall ist nicht automatisch ein Kill-All-Grund.

## Operative Besonderheit

Trotz günstiger Richtung können Risiken entstehen:

- Orderbuch wird sehr dünn.
- Spread explodiert.
- Venue meldet inkonsistente Preise.
- Markt wird unterbrochen.
- Reconciliation ist nicht mehr möglich.
- Exit-Liquidität verschwindet.
- Funding-, Margin- oder Liquidationsmodelle sind nicht mehr vertrauenswürdig.

Dann kann ein globaler Safety-Block trotz positivem unrealized PnL korrekt sein.

---

# 8. Volatilitätsanstieg ist nicht gleich Kill-All

Volatilität muss in mindestens drei Bedeutungen unterschieden werden.

## 8.1 Richtungsstarker Trend

```text
hohe Volatilität
+ konsistente Richtung
+ gute Datenqualität
+ ausreichende Liquidität
= Trendfall
```

Reaktion:

```text
→ Dynamic Scope adaptieren
→ aktive Seite halten
→ Trailing Boundaries nachziehen
```

---

## 8.2 Choppy oder flappender Markt

```text
hohe Volatilität
+ schnelle Richtungswechsel
+ instabile Scope-Events
= Chop-/Flapping-Fall
```

Reaktion:

```text
→ Hysterese
→ Confirmation
→ Cooldown
→ CHOP_GUARD_BLOCK
```

Das ist nicht zwingend Kill-All.

---

## 8.3 Systemisch unsicherer Markt

```text
hohe Volatilität
+ schlechte Datenqualität
oder
+ kollabierende Liquidität
oder
+ Venue-/Reconciliation-Fehler
= Safety-Fall
```

Reaktion:

```text
→ Kill-All prüfen
→ beide Seiten fail-closed blockieren
```

---

# 9. Warum ein pauschaler Volatilitäts-Kill falsch wäre

Eine primitive Regel wie:

```text
if volatility > threshold:
    kill_all()
```

wäre fachlich problematisch.

Sie würde:

- profitable Trends zu früh abschneiden,
- Bull und Bear nicht richtungsabhängig unterscheiden,
- Trend und Chop vermischen,
- Preisbewegung und Datenqualität vermischen,
- normale Marktregimewechsel wie Systemfehler behandeln,
- die Dynamic-Scope-Logik teilweise wirkungslos machen.

Besser ist eine mehrdimensionale Klassifikation:

```text
price_direction
active_side
scope_state
trend_consistency
volatility_regime
liquidity_state
spread_state
data_freshness
price_source_coherence
margin_state
reconciliation_state
governance_state
```

---

# 10. Empfohlene semantische Triggerklassen

Für spätere Reconciliation und Tests sollten Trigger mindestens in folgende Klassen getrennt werden:

```text
FAVORABLE_DIRECTIONAL_MOVE
ADVERSE_DIRECTIONAL_MOVE
VOLATILITY_REGIME_CHANGE
CHOP_OR_FLAPPING
MARKET_DATA_ANOMALY
PRICE_SOURCE_DIVERGENCE
LIQUIDITY_COLLAPSE
SPREAD_EXPANSION
MARGIN_OR_LIQUIDATION_RISK
VENUE_OR_NETWORK_FAILURE
RECONCILIATION_FAILURE
GOVERNANCE_OR_EVIDENCE_BREACH
GLOBAL_SAFETY_BREACH
```

## Erwartete Zuordnung

| Triggerklasse | Primärer Mechanismus |
|---|---|
| Favorable directional move | Dynamic Scope / Hold |
| Adverse directional move | State-Switch |
| Volatility regime change | Dynamic Boundaries |
| Chop / Flapping | Chop Guard / Cooldown |
| Market data anomaly | Fail-closed Safety |
| Price source divergence | Safety / mögliche Kill-All-Eskalation |
| Liquidity collapse | Safety / Execution Guard |
| Margin risk | Risk / Kill-All |
| Venue failure | Safety / Kill-All |
| Reconciliation failure | Safety / Kill-All |
| Governance breach | Kill-All |
| Global safety breach | Kill-All |

---

# 11. State-Switch und Kill-All dürfen nicht dieselbe Rolle übernehmen

## State-Switch

Beantwortet:

> Welche Seite ist unter den aktuellen, gültigen Marktbedingungen die richtige Modellseite?

## Kill-All

Beantwortet:

> Ist das System überhaupt noch in einem Zustand, in dem irgendeine Seite sicher aktiv sein darf?

Diese Fragen sind verschieden.

```text
State-Switch = Richtungsentscheidung
Kill-All     = globale Zulässigkeitsentscheidung
```

Kill-All darf die State Machine nicht ersetzen.

Die State Machine darf Kill-All nicht überstimmen.

---

# 12. Fail-closed korrekt verstehen

„Fail-closed“ bedeutet:

Wenn eine sicherheitsrelevante Voraussetzung fehlt oder nicht beweisbar ist, darf das System keine neue riskante Aktivität freigeben.

Es bedeutet nicht:

> Bei jeder ungewöhnlichen Marktbewegung sofort alles beenden.

Korrekt:

```text
unknown_or_untrusted_safety_state
→ block
```

Nicht korrekt:

```text
large_price_move
→ block
```

Große Preisbewegung kann ein Indikator sein, aber kein ausreichender alleiniger Kill-All-Grund.

---

# 13. Aktueller Modellzustand vs. spätere Live-Semantik

Im aktuellen Master-V2-/Double-Play-Modell bedeutet Kill-All zunächst:

```text
Long nicht eligible
Short nicht eligible
keine neue Modellfreigabe
live_authorization=false
orders=0
cancels=0
fills=0
positions_opened=0
```

Das ist eine modellseitige Sperre.

Für einen späteren Live-Betrieb muss separat definiert werden, was mit bereits bestehenden realen Positionen und Orders geschieht.

Mögliche operative Reaktionen sind nicht gleichbedeutend:

- keine neuen Orders
- offene Orders stornieren
- Position nicht vergrößern
- Position kontrolliert reduzieren
- Position sofort glattstellen
- Venue-spezifische Emergency-Logik
- externe Operator-Eskalation

Ein blindes sofortiges Market-Close kann in einem illiquiden oder fehlerhaften Markt selbst gefährlich sein.

Daher muss die spätere Live-Semantik getrennt und explizit gouverniert werden.

---

# 14. Zielzustand für Peak_Trade

## Günstiger Extremtrend

```text
aktive Seite korrekt
+ Markt bewegt sich stark in diese Richtung
+ Daten und Venue vertrauenswürdig
+ Hard Limits eingehalten
→ aktive Seite halten
→ Dynamic Scope trailen
→ Gewinne nicht allein wegen Volatilität abschneiden
```

## Ungünstiger Extremtrend

```text
aktive Seite falsch
+ bestätigter Gegenmove
+ Daten und Venue vertrauenswürdig
→ State-Switch oder Side-Block
→ kein automatischer globaler Kill-All
```

## Systemische Unsicherheit

```text
Markt, Daten, Venue, Reconciliation oder Risk unzuverlässig
→ Kill-All
→ beide Seiten blockieren
→ fail-closed
```

---

# 15. Prüffragen für die spätere Master-V2-Gap-Reconciliation

Die folgende Prüfung sollte nach Abschluss der aktuellen GLB-/Completion-Arbeiten explizit durchgeführt werden.

## 15.1 Richtungssemantik

- Unterscheidet das System günstige und ungünstige Bewegungen relativ zur aktiven Seite?
- Wird ein starker positiver Move für Long korrekt als günstig behandelt?
- Wird ein starker negativer Move für Short korrekt als günstig behandelt?
- Gibt es irgendeine Regel, die nur auf absoluter Preisbewegung basiert?

## 15.2 Dynamic Scope

- Trailten die Boundaries bei starkem Trend korrekt mit?
- Bleiben sie innerhalb statischer Hard Limits?
- Wird Volatilität zur Bandanpassung genutzt, ohne automatische Kill-All-Eskalation?
- Bleibt die aktive Seite bei konsistentem Trend stabil?

## 15.3 State-Switch

- Werden Gegenbewegungen über Confirmation, Hysterese und Cooldown verarbeitet?
- Wird ein Richtungswechsel sauber von einem Systemfehler getrennt?
- Kann der Switch Gate die State Machine nicht ersetzen?
- Bleiben Long und Short exklusiv?

## 15.4 Chop Guard

- Wird Flapping als Chop behandelt?
- Wird Chop von echtem Kill-All getrennt?
- Verhindert Cooldown unnötige Seitenwechsel?

## 15.5 Kill-All

- Welche exakten Trigger führen zu Kill-All?
- Sind diese Trigger systemisch statt rein richtungsbezogen?
- Gibt es explizite Datenqualitäts-, Venue-, Margin-, Reconciliation- und Governance-Trigger?
- Blockiert Kill-All beide Seiten?
- Kann keine Seite Kill-All überstimmen?
- Bleibt der Zustand fail-closed?

## 15.6 Positive Extrembewegungen

- Gibt es einen Test für Long plus starken Kursanstieg?
- Gibt es einen Test für Short plus starken Kursverfall?
- Beweisen diese Tests, dass kein Kill-All allein wegen der Bewegungsstärke entsteht?
- Beweisen sie das korrekte Trailing der Boundaries?

## 15.7 Safety trotz günstiger Richtung

- Gibt es einen Test für günstige Richtung plus stale Daten?
- Gibt es einen Test für günstige Richtung plus Price-Source-Divergenz?
- Gibt es einen Test für günstige Richtung plus Venue-Ausfall?
- Gibt es einen Test für günstige Richtung plus Margin-/Liquidationsverletzung?
- Führt die zusätzliche Safety-Verletzung dann korrekt zu Kill-All?

---

# 16. Empfohlene Testszenarien

## Szenario A — Long, starker positiver Trend

```text
Start: LONG_ACTIVE
Markt: stark steigend
Daten: valide
Liquidität: valide
Risk: innerhalb Limits

Erwartung:
- kein Kill-All
- Long bleibt aktiv
- Anchor steigt
- Downscope-Boundary trailt
- Long/Short exklusiv
```

---

## Szenario B — Short, starker negativer Trend

```text
Start: SHORT_ACTIVE
Markt: stark fallend
Daten: valide
Liquidität: valide
Risk: innerhalb Limits

Erwartung:
- kein Kill-All
- Short bleibt aktiv
- Anchor fällt
- Upscope-Boundary trailt
- Long/Short exklusiv
```

---

## Szenario C — Long, starker negativer Gegenmove

```text
Start: LONG_ACTIVE
Markt: stark fallend
Daten: valide
Risk: kontrollierbar

Erwartung:
- kein pauschaler Kill-All
- Downscope-Candidate
- Confirmation/Hysterese/Cooldown
- kontrollierter Long→Short-State-Switch
```

---

## Szenario D — Short, starker positiver Gegenmove

```text
Start: SHORT_ACTIVE
Markt: stark steigend
Daten: valide
Risk: kontrollierbar

Erwartung:
- kein pauschaler Kill-All
- Upscope-Candidate
- kontrollierter Short→Long-State-Switch
```

---

## Szenario E — Long gewinnt, aber Daten sind stale

```text
Start: LONG_ACTIVE
Markt: scheinbar stark steigend
Daten: stale oder widersprüchlich

Erwartung:
- Richtungsvorteil reicht nicht
- Safety fail-closed
- Kill-All oder globaler Block
```

---

## Szenario F — Short gewinnt, aber Venue fällt aus

```text
Start: SHORT_ACTIVE
Markt: scheinbar stark fallend
Venue: nicht erreichbar
Reconciliation: unmöglich

Erwartung:
- positiver PnL verhindert Safety-Block nicht
- Kill-All oder definierter globaler Block
```

---

## Szenario G — Hohe Volatilität ohne Richtungsbruch

```text
Start: LONG_ACTIVE oder SHORT_ACTIVE
Markt: stark, aber konsistent in aktiver Richtung
Daten: valide

Erwartung:
- Dynamic Scope adaptiert
- kein Kill-All allein wegen Volatilität
```

---

## Szenario H — Hohe Volatilität mit Flapping

```text
Markt: schnelle Richtungswechsel
Daten: valide

Erwartung:
- Chop Guard
- Cooldown
- kein unkontrolliertes Bull/Bear-Flipping
- Kill-All nur bei zusätzlicher globaler Safety-Verletzung
```

---

# 17. Mögliche fachliche Gap-Klassifikation

Falls die spätere Reconciliation zeigt, dass extreme Bewegungen pauschal behandelt werden, wäre dies wahrscheinlich ein oder mehrere Gaps aus folgenden Klassen:

```text
DYNAMIC_SCOPE_GAP
STATE_TRANSITION_BINDING_GAP
SPEC_CODE_CONFORMANCE_GAP
CONTRACT_TEST_GAP
INTEGRATION_TEST_GAP
ZERO_ORDER_PROOF_GAP
RISK_KILL_ALL_SEPARATION_GAP
FAVORABLE_EXTREME_MOVE_CLASSIFICATION_GAP
```

Der Fix müsste minimal innerhalb bestehender kanonischer Owner erfolgen.

Nicht zulässig wären:

- neue parallele State Machine
- neuer separater Kill-All-Owner ohne Notwendigkeit
- neue unabhängige Volatilitätslogik
- Live- oder Order-Autorisierung
- neue Trading-Semantik ohne belegten Gap

---

# 18. Kompakte Entscheidungslogik

```text
INPUT:
- active_side
- price_move
- scope_event
- volatility_state
- data_quality
- liquidity_state
- margin_state
- venue_state
- reconciliation_state
- governance_state

IF global_safety_breach:
    KILL_ALL

ELSE IF favorable_directional_move:
    HOLD_ACTIVE_SIDE
    UPDATE_TRAILING_BOUNDARIES

ELSE IF adverse_directional_move:
    PROCESS_STATE_SWITCH_WITH_CONFIRMATION_HYSTERESIS_COOLDOWN

ELSE IF chop_or_flapping:
    CHOP_GUARD_BLOCK

ELSE:
    OBSERVE_FAIL_CLOSED
```

Diese Reihenfolge ist konzeptionell, nicht als fertige Implementierung zu verstehen.

---

# 19. Kernaussagen

1. Bull bedeutet vereinfacht Long und steigende Märkte.
2. Bear bedeutet vereinfacht Short und fallende Märkte.
3. Ein starker Anstieg ist für Long nicht automatisch gefährlich.
4. Ein starker Verfall ist für Short nicht automatisch gefährlich.
5. Große absolute Preisbewegung darf allein keinen Kill-All auslösen.
6. Gegenbewegungen gehören primär in die State-Switch-Logik.
7. Flapping gehört primär in Hysterese, Cooldown und Chop Guard.
8. Kill-All ist für systemische Sicherheitsverletzungen vorgesehen.
9. Kill-All kann trotz günstiger Richtung korrekt sein, wenn Daten, Venue, Margin oder Reconciliation nicht vertrauenswürdig sind.
10. State-Switch und Kill-All müssen strikt getrennt bleiben.
11. Dynamic Boundaries sollen profitable Trends begleiten, nicht abschneiden.
12. Fail-closed bedeutet fehlende Sicherheit blockiert; nicht jede ungewöhnliche Bewegung blockiert.
13. Die aktuelle Modelllogik ist Zero-Order und nicht live-autorisierend.
14. Eine spätere Live-Exit-Semantik muss separat gouverniert und bewiesen werden.
15. Die abschließende Master-V2-Reconciliation sollte diese Unterscheidungen explizit testen.

---

# 20. Abschlussstatus

```text
DOCUMENT_SCOPE=MASTER_V2_DOUBLE_PLAY_KILL_ALL_STATE_SWITCH_SEMANTIC_CLARIFICATION
FAVORABLE_EXTREME_MOVE_AUTOMATIC_KILL_ALL=false
ADVERSE_MOVE_PRIMARY_HANDLER=STATE_SWITCH
CHOP_PRIMARY_HANDLER=CHOP_GUARD
SYSTEMIC_SAFETY_FAILURE_PRIMARY_HANDLER=KILL_ALL
LONG_SHORT_EXCLUSIVITY_REQUIRED=true
DYNAMIC_SCOPE_TRAILING_REQUIRED=true
FAIL_CLOSED_REQUIRED=true
LIVE_AUTHORIZATION=false
ORDERS_CREATED=0
```

---

## Referenz

Grundlage dieses Dokuments ist das kanonische Master-V2-/Double-Play-Alignment-Runbook und dessen eingebettete Fachquelle zur Bull-/Bear-State-Machine, Dynamic-Scope-Logik, Survival-, Capital-, Suitability-, Composition- und Kill-All-Abgrenzung.
