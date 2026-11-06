# Runbook B — Shadow → (Validate/Testnet) → Mini-Live auf Kraken Spot (unattended-ready, safety-first)
Stand: 2026-02-07  
Scope: Kraken Spot REST Integration (api.kraken.com), Shadow bereits vorhanden.  
Ziel: Von “läuft irgendwie” zu einem **unattended**-fähigen Betrieb mit klaren Gates, Kill-Switch, Reconciliation und Audit-Trail.

---

## 0) In einfacher Sprache: was wir hier bauen
- **Shadow**: System tut so, als würde es traden, aber schickt **keine** Orders.
- **Validate/Testnet (bei euch)**: “Order-Validation / Dry-Run” (z.B. validate_only), gut für Formate/Checks, nicht für echte Fills.
- **Mini-Live**: echte Orders, aber sehr klein + harte Limits + enge Zeitfenster.

---

## 1) Sicherheitsregeln (unverhandelbar)
- Live ist **default OFF**.
- Live braucht **2 Stufen**:
  - `enabled=true` (Konfiguration erlaubt Live grundsätzlich)
  - `armed=true` (nur für ein Zeitfenster/Session)
- Zusätzlich: **Confirm-Token** für jede Live-Session (einmalig).
- Jeder Trade muss durch **L5 Risk Gate** (deterministisch) freigegeben werden.
- Kill-Switch muss jederzeit funktionieren:
  - Stop Trading + Cancel Open Orders + (optional) Reduce-only/flatten (wenn vorgesehen)

---

## 2) Was “Daytrading” technisch bedeutet (für Execution)
Du brauchst vor allem:
- saubere Daten (keine Lücken)
- saubere Zustände (Orders/Positions stimmen)
- schnelle Fehlerreaktion (Reconnect, retries, backoff)
- limitierte Frequenz (rate limits)

Euer aktueller Datenpfad ist OHLC/CCXT/REST – das reicht für Start, aber nicht für “HFT”.

---

## 3) Phasenübersicht (A bis Z)
### Phase B1 — Baseline: Shadow stabilisieren & vermessen
**Ziel**: Shadow 24/7 stabil, ohne “silent failure”.  
**Endpunkt**: 7–14 Tage stabiler Lauf (oder kürzer, wenn ihr schnell iteriert, aber mind. mehrere Stunden ohne Drift).

**Schritte**
1. Shadow starten (wie ihr es aktuell macht).
2. Health-Metriken:
   - Datenlücken (missing candles)
   - Latenz (poll durations)
   - Exceptions (count)
   - Decision count / minute
3. Audit:
   - Jede Entscheidung mit run_id, inputs-hash, gate-result, hypothetischer order

**Exit Criteria**
- Kein State-Corruption nach Restart
- Logs/Audit nachvollziehbar
- Out/ops Artefakte sauber

**Troubleshoot**
- Wenn Shadow “hängt”: watchdog + restart strategy, aber niemals “blind weitertraden”.

---

### Phase B2 — Execution-State Model & Reconciliation (muss vor Mini-Live sitzen)
**Ziel**: Bei jedem Start kann das System seinen Zustand wiederherstellen.  
**Endpunkt**: “cold start” führt zu konsistentem state.

**Was ihr braucht**
- Lokaler State Store (append-only + snapshot):
  - open orders (client_id ↔ exchange_id)
  - last seen balances
  - last decision timestamp
- Reconciliation routine:
  - QueryOrders (alle offenen IDs)
  - Balance check
  - Cancel unknown/stale orders (je nach policy)

**Exit Criteria**
- Nach Crash/Restart: keine “ghost orders”
- open orders im System = open orders bei Kraken

---

### Phase B3 — Risk Gate (L5) finalisieren (deterministisch)
**Ziel**: Vor jedem OrderIntent harte Checks.  
**Endpunkt**: Gate kann “NO” sagen und das wird respektiert.

**Mindestchecks (Start)**
- Max notional pro trade
- Max daily loss (realisiert + unrealisiert, je nach verfügbar)
- Max trades per day
- Cooldown nach Verlustserie
- Spread/Volatilität (wenn verfügbar) oder Candle range heuristics
- Datenqualität ok? (keine Lücken, keine stale candles)
- API health ok? (timeouts? retries?)
- Config gating ok? (enabled/armed/token)

**Exit Criteria**
- Gate-Tests grün
- Jede Gate-Entscheidung geloggt

---

### Phase B4 — Validate/Testnet-Flow nutzen (bei euch: “validate_only”)
**Ziel**: Order-Building ist korrekt, ohne Live-Risiko.  
**Endpunkt**: Für jede hypothetische Order existiert ein validierter Payload.

**Schritte**
1. Shadow erzeugt OrderIntent.
2. Validate-Client prüft:
   - symbol format
   - size rounding
   - price precision
   - side/type
3. Ergebnis wird als Event + Capsule gespeichert.

**Exit Criteria**
- 100+ Validations ohne Formatfehler

---

### Phase B5 — Mini-Live (echte Orders, klein & eng begrenzt)
**Ziel**: Unattended-ready in “klein”.  
**Endpunkt**: Mehrere Sessions ohne Incidents, mit sauberem Reconcile.

**Konkrete Limits (Start – Beispiel)**
- 1 Symbol
- max 1 offene Position
- max 1 offene Order
- max 3 Trades/Tag
- max Verlust/Tag sehr klein (z.B. 0.2–0.5% vom eingesetzten Budget)
- only limit orders (wenn eure Strategie das erlaubt)
- time window: z.B. 60–120 Minuten pro Session

**Session Ablauf**
1. `enabled=true`
2. `armed=true` + confirm token setzen (einmalig)
3. Start live session (mit logging)
4. Nach time window: auto-disarm
5. EOD: Reconcile + Report + disable

**Exit Criteria**
- Keine ungeklärten Orders
- Kill-switch getestet (mind. 1x in Mini-Live)
- Daily loss cap nie überschritten

---

## 4) Integration mit Runbook A (Incoming → Envelopes → Learning)
Ja, das läuft parallel und ist sogar gewünscht:

- In B1/B4/B5 produziert Shadow/Validate/Mini-Live Events
- Runbook A normalisiert und erzeugt FeatureViews/Envelopes/Capsules
- Behavior/Process Critic erstellt ProcessScore pro Session/Trade

**Wichtig**
- ProcessScore beeinflusst nicht automatisch die Ordergröße.
- ProcessScore ist Label + Feedback für später.

---

## 5) Wieder-Einstiegspunkte (Quick Resume)
### Resume S1: “Shadow läuft, ich will nur Health sehen”
- Check: letzte Events/metrics vorhanden
- Check: keine data gaps
- Check: exceptions = 0 in window

### Resume S2: “Ich will Reconciliation testen”
- Simuliere Crash/Restart
- Run reconcile
- Verify: open orders match

### Resume S3: “Mini-Live Session starten”
- Verify gates: enabled/armed/token
- Verify risk limits small
- Run session in time window
- End: disarm + reconcile + report

---

## 6) Incident Playbook (Kurz)
### A) Datenlücken / Stale Data
- Stop trading (disarm)
- Mark session as degraded
- Reconnect/retry
- Resume only when data gap recovered

### B) Kraken API timeouts / rate limits
- Exponential backoff
- Stop placing new orders
- Reconcile after recovery

### C) Unklare Order (unknown state)
- Cancel if possible
- QueryOrders repeatedly
- If still unknown: hard stop and manual review

---

## 7) Definition of Done (Finish)
- [ ] Shadow stabil 24/7 (B1)
- [ ] Reconciliation robust (B2)
- [ ] Risk Gate vollständig & geloggt (B3)
- [ ] Validate/Testnet Flow korrekt (B4)
- [ ] Mini-Live mehrfach erfolgreich (B5)
- [ ] Full audit trail + learning capsules (Runbook A integriert)
- [ ] Kill-switch zuverlässig
- [ ] Rollback plan dokumentiert

---

## 8) “Was kommt danach?”
- Optional: WebSocket Market Data für bessere Daytrading-Reaktivität
- Optional: Mehr Symbole / höhere Frequenz nur nach Benchmarks
- Optional: Automatischer Session Scheduler (aber erst nach Stabilität)
