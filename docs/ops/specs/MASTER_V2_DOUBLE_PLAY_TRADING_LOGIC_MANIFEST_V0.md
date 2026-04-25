# Peak_Trade — Master V2 Double Play Trading Logic Manifest v0

## Repository safety note (canonical)

This document is **docs-only**. It is the **canonical trading-logic manifest** for the clarified **Master V2 / Double Play** target semantics. It does **not** change runtime behavior. It does **not** grant order placement, execution, or session permission. It does **not** authorize testnet or live operation. It does not permit or imply mutation of `out/`, evidence artifacts, S3, or application caches.

**Terminology (explicit, for reading this file):**

- **State-Switch Logic** is **normal** switching between the Long/Bull and Short/Bear side on the same selected instrument. It is **not** the same semantics as a generic “KillSwitch flips to the other side.”
- **Kill-All / Emergency Stop** is a **separate** hard stop; it is not routine side change.
- **Dynamic** does **not** mean arbitrary: dynamic **scope** rules are **pre-authorized** and **bounded** by static hard limits and governance; **Risk/Safety** is the pre-authorized **runtime envelope**, not a full recomputation on every switch tick.
- The **hot path** may update **lightweight runtime scope state** only. It must **not** run heavy **AI**, full **governance**, or full **risk** recomputation in the hot path.
- This manifest carries **no live authorization**; live remains blocked until separate governed steps.

## Related specifications (docs-only, non-authority)

- [MASTER_V2_DOUBLE_PLAY_ARITHMETIC_SEQUENCE_SURVIVAL_CONTRACT_V0.md](MASTER_V2_DOUBLE_PLAY_ARITHMETIC_SEQUENCE_SURVIVAL_CONTRACT_V0.md) — **Futures arithmetic** and **sequence survival** **envelope** for Double Play (complements this manifest; not an execution permit).
- [MASTER_V2_DOUBLE_PLAY_STRATEGY_SUITABILITY_PROJECTION_CONTRACT_V0.md](MASTER_V2_DOUBLE_PLAY_STRATEGY_SUITABILITY_PROJECTION_CONTRACT_V0.md) — **Strategy suitability projection** (metadata and side-compatibility only; not activation or execution authority).

---
**Status:** Konzept-/Architektur-Manifest, nicht Live-Freigabe  
**Scope:** Master V2 / Double Play Handelslogik für Futures/Perpetuals  
**Boundary:** Keine Orders, keine Sessions, kein Testnet, kein Live, keine Evidence-Claims

---

## 0. Executive Summary

Die Master V2 / Double Play Logik ist die zentrale Handelslogik für den späteren Futures-Einsatz in Peak_Trade.

Der Kern ist nicht „einfach Long- und Short-Strategien sortieren“, sondern:

> **Ein ausgewähltes Future wird von zwei gegengerichteten Strategie-Layern umfasst: Long/Bull auf der einen Seite und Short/Bear auf der anderen Seite. Die normale Umschaltung zwischen diesen Seiten erfolgt über eine schnelle, dynamische State-Switch-Logik.**

Diese Logik soll den Future „in die Zange nehmen“:

- Wenn der Markt in einen bestätigten Downscope kippt, wird die Long-Seite blockiert und die Short-Seite wird gemäß vorab freigegebenem Runtime Envelope armed/aktiv.
- Wenn der Markt in einen bestätigten Upscope kippt, wird die Short-Seite blockiert und die Long-Seite wird gemäß vorab freigegebenem Runtime Envelope armed/aktiv.
- Der normale Wechsel ist **State-Switch-Logik**, nicht KillSwitch-Logik.
- Kill-All / Emergency Stop ist separat und blockiert alles.
- Risk/Safety gibt die jeweiligen Strategie-Layer vorab frei, wird aber nicht als langsame Vollprüfung im Millisekunden-Switch neu berechnet.
- Dynamische Scope-Grenzen trailen/adaptieren mit dem Markt, aber nur innerhalb vorab begrenzter Formeln und Hard Limits.

---

## 1. Nicht-Autoritäts-Hinweis

Dieses Manifest ist eine konzeptionelle und technische Festlegung für die Zielarchitektur.

Es ist **keine** Live-Freigabe und keine Ausführungserlaubnis.

Es erlaubt nicht:

- Orders,
- Exchange Calls,
- Market-Data-Fetches,
- Backtests,
- Scanner-Ausführung,
- Paper/Shadow/Testnet/Live Sessions,
- Evidence Writes,
- Archive/S3 Writes,
- Risk-/KillSwitch-Toggles,
- Live Authorization.

Dieses Manifest beschreibt, wie die spätere Logik aussehen muss, damit sie konsistent, schnell und Master-V2-kompatibel ist.

---

## 2. Kernmodell: Ein Future, zwei Layer

Master V2 / Double Play wählt **ein Future-Instrument** aus.

Auf diesem Future sitzen zwei gegengerichtete Strategie-Layer:

```text
selected_future
  ├─ long_bull_layer
  ├─ short_bear_layer
  └─ state_switch_logic
```

### Long/Bull Layer

Der Long/Bull Layer enthält eine oder mehrere Strategien, die für steigende Kurse geeignet sind.

Beispiele für spätere Eignung:

- Trend-Following long,
- Breakout long,
- bullische Momentum-Strategien,
- Strategien, die auf Aufwärtsbewegung und ausreichend Liquidität ausgelegt sind.

### Short/Bear Layer

Der Short/Bear Layer enthält eine oder mehrere Strategien, die für fallende Kurse geeignet sind.

Beispiele für spätere Eignung:

- Breakdown short,
- bearische Momentum-Strategien,
- Trend-Following short,
- Strategien, die fallende Marktphasen nutzen.

### Zentrale Invariante

Für die Basislogik gilt:

```text
LONG_ACTIVE und SHORT_ACTIVE dürfen auf demselben Future nicht gleichzeitig aktiv sein.
```

Falls später Hedge Mode erlaubt werden soll, braucht das einen separaten, expliziten Governance-/Contract-Pfad. Für diese Master-V2-Double-Play-Logik gilt erstmal: **genau eine aktive Seite**.

---

## 3. State-Switch statt KillSwitch

Der normale Seitenwechsel heißt **State-Switch-Logik**.

Nicht:

```text
KillSwitch aktiviert automatisch die Gegenseite.
```

Sondern:

```text
Downscope erkannt
→ Long blocked
→ Short armed/active gemäß Runtime Envelope
```

und:

```text
Upscope erkannt
→ Short blocked
→ Long armed/active gemäß Runtime Envelope
```

### Trennung der Begriffe

| Begriff | Bedeutung |
|---|---|
| State-Switch-Logik | Normaler schneller Wechsel zwischen Long- und Short-Layer. |
| Long Blocked | Long darf keine neue Aktivierung ausführen. |
| Short Blocked | Short darf keine neue Aktivierung ausführen. |
| Armed | Seite ist vorbereitet, aber nur innerhalb vorab freigegebener Grenzen. |
| Active | Seite ist aktuell aktiv. |
| Kill-All / Emergency Stop | Harter Not-Aus. Keine Side darf aktivieren. |

Kill-All ist nicht normaler Side-Wechsel. Kill-All blockiert.

---

## 4. Ziel-State-Machine

Die spätere State-Machine sollte mindestens diese Zustände kennen:

```text
NEUTRAL_OBSERVE
LONG_ARMED
LONG_ACTIVE
LONG_BLOCKED
SHORT_ARMED
SHORT_ACTIVE
SHORT_BLOCKED
SWITCH_LONG_TO_SHORT_PENDING
SWITCH_SHORT_TO_LONG_PENDING
CHOP_GUARD_BLOCK
KILL_ALL
```

### Normale Downscope-Transition

```text
LONG_ACTIVE
  → SWITCH_LONG_TO_SHORT_PENDING
  → LONG_BLOCKED
  → SHORT_ARMED
  → SHORT_ACTIVE
```

### Normale Upscope-Transition

```text
SHORT_ACTIVE
  → SWITCH_SHORT_TO_LONG_PENDING
  → SHORT_BLOCKED
  → LONG_ARMED
  → LONG_ACTIVE
```

### Neutraler Start

```text
NEUTRAL_OBSERVE
  → LONG_ARMED → LONG_ACTIVE
  oder
  → SHORT_ARMED → SHORT_ACTIVE
```

### Harte Blockade

```text
any_state → KILL_ALL
```

### Chop-Schutz

```text
any_switch_candidate → CHOP_GUARD_BLOCK
```

---

## 5. Scope-Erkennung: Up- und Downscope

Die State-Switch-Logik reagiert nicht auf jeden Tick, sondern auf bestätigte Scope-Events.

Ziel-Events:

| Event | Bedeutung |
|---|---|
| DOWNSCOPE_CANDIDATE | Möglicher Downscope, noch nicht bestätigt. |
| DOWNSCOPE_CONFIRMED | Bestätigter Downscope, Seitenwechsel zulässig. |
| UPSCOPE_CANDIDATE | Möglicher Upscope, noch nicht bestätigt. |
| UPSCOPE_CONFIRMED | Bestätigter Upscope, Seitenwechsel zulässig. |
| CHOP_DETECTED | Markt ist zu noisy / flip-flop-gefährdet. |
| SCOPE_UNKNOWN | Scope kann nicht verlässlich bestimmt werden. |
| KILL_ALL_REQUIRED | Harte Stop-Bedingung. |

### Wichtig

Scope-Erkennung muss schnell sein, aber nicht naiv.

Sie darf nicht bei minimalem Tick-Rauschen ständig wechseln. Sie braucht:

- Hysterese,
- Cooldown,
- Confirmation Window,
- Chop Guard,
- dynamische/trailing Scope-Grenzen.

---

## 6. Dynamische Scope-Grenzen statt fixer Schwellen

Ein zentraler Punkt: **statische Preisgrenzen reichen nicht.**

Wenn ein Future stark nach oben läuft, darf das System nicht fälschlich „out of scope“ werden, nur weil der Markt von einer vorher fixen Grenze weggelaufen ist.

Daher:

```text
Dynamische Scope-Grenzen trailen/adaptieren mit dem Markt.
```

Aber:

```text
Dynamisch heißt nicht beliebig.
```

Die Dynamik selbst muss vorab begrenzt und freigegeben sein.

### Schlechtes Modell

```text
downscope_threshold = fixer Preis
upscope_threshold = fixer Preis
```

Problem:

```text
Long aktiv
Future steigt stark
fixe Grenze bleibt zurück
System interpretiert irgendwann falschen Out-of-Scope
```

### Gewünschtes Modell

```text
Long aktiv
Preis macht neue Hochs
Trailing Anchor zieht nach oben
Downscope Boundary zieht kontrolliert nach
Long bleibt aktiv, solange Trendstruktur intakt bleibt
Short wird erst bei bestätigtem Bruch der dynamischen Boundary aktiv
```

Analog für Short:

```text
Short aktiv
Preis macht neue Tiefs
Trailing Anchor zieht nach unten
Upscope Boundary zieht kontrolliert nach unten
Short bleibt aktiv, solange Downtrend-Struktur intakt bleibt
Long wird erst bei bestätigtem Bruch über die dynamische Boundary aktiv
```

---

## 7. Dynamic Runtime Envelope

Der Runtime Envelope besteht aus zwei Ebenen:

```text
1. Static Hard Limits
2. Dynamic Scope Rules
```

### 7.1 Static Hard Limits

Diese Werte dürfen dynamisch niemals erweitert werden:

```yaml
static_hard_limits:
  max_notional: number
  max_leverage: number
  max_position_size: number
  max_switches_per_window: integer
  min_band_width: number
  max_band_width: number
  kill_all_conditions: list
  live_authorization: false
```

### 7.2 Dynamic Scope Rules

Diese Regeln dürfen dynamisch arbeiten, aber nur innerhalb der Hard Limits:

```yaml
dynamic_scope_rules:
  trailing_enabled: true
  anchor_update_mode: trend_extreme
  volatility_model: atr_or_realized_volatility
  downscope_band_multiplier: number
  upscope_band_multiplier: number
  min_band_width: number
  max_band_width: number
  hysteresis_multiplier: number
  boundary_update_rate_limit: number
  min_scope_hold_ms: integer
  min_switch_cooldown_ms: integer
  confirmation_ticks: integer
  freeze_conditions: list
  chop_guard_conditions: list
```

### 7.3 Runtime Dynamic Scope State

Der Hot Path darf nur leichten Runtime-State aktualisieren:

```yaml
runtime_dynamic_scope_state:
  active_side: LONG | SHORT | NEUTRAL
  anchor_price: number
  current_upscope_boundary: number
  current_downscope_boundary: number
  current_hysteresis_band: number
  current_volatility_estimate: number
  last_switch_utc: timestamp
  switch_count_window: integer
  freshness_state: fresh | stale | unknown
  chop_score: number
  boundary_frozen: boolean
```

---

## 8. Bandbreiten-Formeln und ATR / Realized Volatility

Die dynamische Bandbreite darf nicht willkürlich entstehen.

Beispielhafte Formel:

```text
dynamic_band_width = clamp(
  atr_or_realized_volatility * multiplier,
  min_band_width,
  max_band_width
)
```

Oder:

```text
dynamic_band_width = clamp(
  realized_volatility_window * price * multiplier,
  min_band_width,
  max_band_width
)
```

Welche Volatilitätsmessung genutzt wird, muss vorab definiert werden:

- ATR,
- Realized Volatility,
- Rolling Range,
- Intraday Volatility Profile,
- ggf. mark/index-price-basierte Volatilität.

Diese Parameter kommen idealerweise aus dem Universe Selector / Instrument Intelligence Layer.

---

## 9. Universe Selector als Wissensquelle

Der Futures Universe Selector ist nicht nur ein Top20-Ranking-Tool. Er liefert die Instrument Intelligence, die später die dynamischen Scope-Regeln prägt.

### Universe Selector soll liefern

```text
- realized volatility
- ATR / rolling range
- intraday volatility profile
- volume / quote volume
- liquidity profile
- spread profile
- open interest, falls verfügbar
- funding profile
- mark/index/last availability
- data freshness
- trendiness / chop score
- volatility regime: low / normal / high / extreme
- F1 metadata completeness
- F2 provenance completeness
```

Diese Werte sind Inputs für:

```text
- Scope-Bandbreite
- Boundary-Trailing-Geschwindigkeit
- Hysterese-Stärke
- Confirmation Window
- Cooldown
- Chop Guard
- Funding-/Spread-/Liquidity-Blocks
```

### Wichtig

Der Selector liefert Kontext. Er handelt nicht. Er aktiviert keine Strategie. Er autorisiert kein Testnet/Live.

---

## 10. AI-Layer und Strategy Suitability

Der AI-/Analysis-Layer darf Instrument Intelligence verdichten und erklären.

Er darf z. B. sagen:

```text
- Future ist stark intraday-volatil.
- Liquidität ist ausreichend.
- Spread ist eng.
- Funding ist neutral/auffällig.
- Aktuelle Struktur ist eher Trend / Breakout / Chop.
- Long-Strategien wirken geeigneter als Range-Strategien.
```

Aber:

```text
AI ist Kontext, nicht Autorität.
```

### Strategy Suitability

Strategien sollen später als Suitability-Kandidaten klassifiziert werden:

```text
long_only_candidate
short_only_candidate
both_sides_candidate
neutral_range_candidate
disabled_for_candidate
unknown_suitability
```

### Fail-Closed

Bei `unknown_suitability` darf keine automatische Strategie-Aktivierung erfolgen.

---

## 11. Master V2 / Double Play Authority Chain

Die Ziel-Autoritätskette lautet:

```text
Futures Universe Selector
  → Instrument Intelligence
  → AI Context Summary
  → Strategy Suitability Router
  → Dynamic Scope Envelope Builder
  → Double Play State-Switch Logic
  → Risk / Safety / Kill-All Boundary
  → Candidate Evidence / Governance
  → Execution only in later governed slice
```

### Klare Rollen

| Layer | Rolle | Autorität? |
|---|---|---:|
| Futures Universe Selector | Kandidaten finden und erklären | Nein |
| Instrument Intelligence | Marktprofil liefern | Nein |
| AI Context | Kontext verdichten | Nein |
| Strategy Suitability | Strategien vor-klassifizieren | Nein |
| Dynamic Scope Envelope Builder | Vorab Regeln/Bounds erzeugen | Nur innerhalb Governance |
| State-Switch Runtime | Schnell zwischen Seiten wechseln | Nur innerhalb Envelope |
| Risk/Safety/Kill-All | Blockieren / Not-Aus | Ja, blockierend |
| Master V2 / Double Play | Entscheidungs-/Governance-Schicht | Ja |
| Execution | Späterer Ausführungspfad | Nicht jetzt |

---

## 12. Risk/Safety Layer-Freigabe

Risk/Safety soll die jeweilige Strategie-Seite grundsätzlich freigeben, aber nicht als langsame Vollprüfung im Side-Switch-Moment.

### Zweistufiges Modell

```text
1. Pre-Arm / Runtime Envelope Freigabe
   Vor dem Hot Path:
   - Future erlaubt?
   - Long Layer erlaubt?
   - Short Layer erlaubt?
   - Double-Play-Paar zulässig?
   - max Notional?
   - max Leverage?
   - max Position Size?
   - Scope-Regeln?
   - Funding/Spread/Liquidity Blocks?
   - Kill-All-Bedingungen?

2. Hot-Path State-Switch
   Während der Markt läuft:
   - Scope lesen
   - Boundary-State updaten
   - Side wechseln
   - keine schwere neue Risk-/Safety-Governance
```

### Merksatz

```text
Risk/Safety ist nicht aus dem Hot Path raus.
Risk/Safety wird in den Hot Path vorkompiliert.
```

---

## 13. Hot Path: Was erlaubt ist

Im Hot Path erlaubt:

```text
- aktuellen Preis / Mark Price lesen
- Active Side lesen
- Anchor Price aktualisieren
- Dynamic Boundaries aktualisieren
- leichte Volatility Estimate aktualisieren
- Switch Counter aktualisieren
- Cooldown State aktualisieren
- Freshness State lesen
- Chop Score aktualisieren
- State Transition ausführen
```

Alles muss auf vorab genehmigten Formeln und Runtime Inputs beruhen.

---

## 14. Hot Path: Was verboten ist

Im Hot Path verboten:

```text
- AI aufrufen
- Universe Selector neu laufen lassen
- Strategy neu auswählen
- Dashboard abfragen
- Exchange APIs aufrufen
- Market Data extern fetchen
- Cache schreiben
- Evidence schreiben
- Archive/S3 schreiben
- Backtests laufen lassen
- schwere Risk/Safety-Recomputations
- Governance neu entscheiden
- Configs ändern
- Workflows dispatchen
- Live autorisieren
```

Der Hot Path muss schnell und deterministisch sein.

---

## 15. Hysterese, Cooldown, Confirmation, Chop Guard

Damit das System nicht wegen jedem Tick flippt, braucht es harte Anti-Ping-Pong-Regeln.

### Hysterese

Up- und Downscope dürfen nicht dieselbe Schwelle verwenden.

```text
Downscope boundary != Upscope boundary
```

Es braucht ein Band dazwischen.

### Cooldown

Nach einem Switch muss eine Mindestzeit vergehen, bevor zurück gewechselt werden darf.

```text
min_switch_cooldown_ms
```

### Confirmation Window

Ein Scope muss kurz stabil sein, bevor er bestätigt wird.

```text
min_scope_hold_ms
confirmation_ticks
```

### Chop Guard

Wenn zu viele Switch-Kandidaten oder ungültige Bewegungen in kurzer Zeit auftreten:

```text
CHOP_GUARD_BLOCK
```

Dann keine neue Side-Aktivierung.

---

## 16. Freeze Conditions

Dynamische Boundary Updates müssen einfrieren oder blockieren, wenn Daten unzuverlässig sind.

Freeze Conditions:

```text
- stale data
- toxic spread
- funding abnormal
- market data degraded
- contradictory runtime state
- volatility extreme beyond assumptions
- boundary update would violate hard limits
- mark/index/last unavailable when required
```

Bei Freeze:

```text
- keine neue Side-Aktivierung
- ggf. CHOP_GUARD_BLOCK
- ggf. KILL_ALL je nach Envelope
```

---

## 17. Output / Handoff Schema

Ein späteres Objekt könnte so aussehen:

```yaml
master_v2_double_play_context:
  candidate_id: string
  instrument_id: string
  selected_future: string

  instrument_intelligence:
    volatility_profile: string
    liquidity_profile: string
    spread_profile: string
    open_interest_profile: string
    funding_profile: string
    freshness_profile: string
    trend_profile: string
    chop_profile: string
    risk_warnings: list
    missing_data_warnings: list

  strategy_layers:
    long_bull_layer:
      strategy_family: string
      suitability_class: long_only_candidate
      pre_authorized: boolean
    short_bear_layer:
      strategy_family: string
      suitability_class: short_only_candidate
      pre_authorized: boolean

  dynamic_scope_envelope:
    static_hard_limits:
      max_notional: number
      max_leverage: number
      max_position_size: number
      max_switches_per_window: integer
      live_authorization: false
    dynamic_scope_rules:
      trailing_enabled: true
      volatility_model: atr_or_realized_volatility
      downscope_band_multiplier: number
      upscope_band_multiplier: number
      min_band_width: number
      max_band_width: number
      hysteresis_multiplier: number
      boundary_update_rate_limit: number
      min_scope_hold_ms: integer
      min_switch_cooldown_ms: integer
      confirmation_ticks: integer

  runtime_state:
    active_side: LONG | SHORT | NEUTRAL
    anchor_price: number
    current_upscope_boundary: number
    current_downscope_boundary: number
    chop_score: number
    boundary_frozen: boolean

  authority:
    selector_is_signal: false
    ai_is_authority: false
    strategy_suitability_is_permission: false
    master_v2_required: true
    risk_safety_required: true
    live_authorization: false
```

---

## 18. Dashboard-Rolle

Das Dashboard darf diese Logik später anzeigen, aber nicht steuern.

Dashboard darf anzeigen:

```text
- selected future
- active side
- Long/Bull Layer status
- Short/Bear Layer status
- current boundaries
- trailing anchor
- hysteresis band
- cooldown state
- chop guard state
- boundary frozen state
- no-live banner
```

Dashboard darf nicht:

```text
- State wechseln
- Side aktivieren
- Side blockieren
- Risk/Safety togglen
- Kill-All togglen
- Orders platzieren
- Sessions starten
- Market Data fetchen
- Evidence schreiben
- Live autorisieren
```

---

## 19. Test-/Validierungsanforderungen für später

Spätere Tests müssen beweisen:

```text
1. LONG_ACTIVE und SHORT_ACTIVE können nicht gleichzeitig true sein.
2. Downscope blockiert Long, bevor Short aktiv wird.
3. Upscope blockiert Short, bevor Long aktiv wird.
4. Hysterese verhindert Same-Threshold-Flip-Flop.
5. Cooldown verhindert Ping-Pong.
6. Confirmation verhindert One-Tick-Switching.
7. Chop Guard blockiert noisy Switching.
8. Dynamic Boundaries trailen in Trends korrekt.
9. Dynamic Band Width ist clamp-beschränkt.
10. Hard Limits werden dynamisch nie erweitert.
11. Stale Data friert/blockiert Boundary Updates.
12. Hot Path ruft keine AI/Selector/Dashboard/Exchange/Evidence/Archive auf.
13. Missing Envelope failt closed.
14. Kill-All überschreibt normalen State-Switch.
15. Keine State-Switch-Logik autorisiert Live.
```

---

## 20. Empfohlene Repo-Manifeste / Contracts

Die folgenden Contracts sollten diese Logik im Repo manifestieren:

```text
FUTURES_UNIVERSE_SELECTOR_CONTRACT_V0.md
FUTURES_DYNAMIC_SCOPE_ENVELOPE_CONTRACT_V0.md
FUTURES_DOUBLE_PLAY_STATE_SWITCH_CONTRACT_V0.md
FUTURES_STRATEGY_SUITABILITY_AND_DOUBLE_PLAY_HANDOFF_CONTRACT_V0.md
```

Logische Reihenfolge:

```text
1. Universe Selector Contract
2. Dynamic Scope Envelope Contract
3. Double Play State-Switch Contract
4. Strategy Suitability / Double Play Handoff Contract
```

Der Dynamic Scope Envelope muss vor oder zusammen mit dem State-Switch Contract sauber definiert werden, weil statische Schwellen die Handelslogik verfälschen würden.

---

## 21. Endgültige Zielbeschreibung

Die finale Master V2 / Double Play Handelslogik ist:

> Peak_Trade wählt ein geeignetes Futures-Instrument aus einer futures-spezifischen Universe-/Top20-Pipeline. Für dieses eine Future werden ein Long/Bull-Layer und ein Short/Bear-Layer vorbereitet. Instrument Intelligence, AI-Kontext und Strategy Suitability liefern nur Kontext und Eignungsprofile. Risk/Safety gibt die Layer und Grenzen vorab als Dynamic Runtime Envelope frei. Während der Markt läuft, aktualisiert der Hot Path nur leichte dynamische Scope-Zustände und wechselt über eine State-Switch-Logik zwischen Long und Short. Dynamische, trailing Scope-Grenzen folgen starken Trends innerhalb harter Grenzen. Hysterese, Cooldown, Confirmation und Chop Guard verhindern Flip-Flop. Kill-All bleibt separat als Not-Aus. Kein Selector, keine AI, kein Dashboard und keine Strategie-Registry darf Trading-Autorität übernehmen. Live bleibt bis zu separater Governance blockiert.

---

## 22. Offene Punkte für nächste Schritte

Noch zu klären / zu implementieren:

```text
1. Welche vorhandenen Repo-Dateien können als Ausgangspunkt für Universe Selector dienen?
2. Wie sieht das konkrete Top50 → Top20 Output-Schema aus?
3. Welche Volatilitätsmetrik wird primär genutzt: ATR, realized volatility, rolling range?
4. Wie wird Funding in der Suitability gewichtet?
5. Wie wird Open Interest integriert, falls Exchange es liefert?
6. Welche Strategy Families existieren bereits für Long/Bull und Short/Bear?
7. Wo wird der Dynamic Runtime Envelope später materialisiert?
8. Wie wird State-Switch später getestet, ohne Exchange/Live?
9. Wie wird F5 Dashboard später read-only angeschlossen?
10. Wie wird verhindert, dass Label wie kraken_futures_testnet als Adapter-Proof missverstanden werden?
```

---

## 23. Safety Boundary

Bis explizit anders governed:

```text
no orders
no exchange calls
no market-data fetches
no scanner execution
no backtests
no sessions
no Paper
no Shadow
no Testnet
no Live
no out/evidence/S3/cache mutation
no Live authorization
```

Dieses Manifest ist ein Schutz gegen Verlust der konzeptionellen Handelslogik und eine Grundlage für die nächsten Cursor-Multi-Agent-Slices.
