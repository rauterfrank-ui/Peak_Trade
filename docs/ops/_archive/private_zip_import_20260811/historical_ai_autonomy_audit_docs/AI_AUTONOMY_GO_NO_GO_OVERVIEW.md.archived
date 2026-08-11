# PT-GOV-AI-001 — AI Autonomy: Go / No-Go Overview (Audit-Stable)
## Best-Practice Leitplanke für AI-gestütztes DAY TRADING

**Status:** Controlled Document (Governance)  
**Owner:** System Owner (Constitution Authority)  
**Approver:** Governance / Risk Owner (falls getrennt)  
**Effective Date:** YYYY-MM-DD  
**Version:** 1.0.0  
**Review Cadence:** mindestens quarterly oder bei jeder Live-Policy-Änderung  
**Applies To:** Peak_Trade — alle Umgebungen (Shadow, Paper, Live)  
**Primary Goal:** DAY TRADING (hoch riskant, kurze Feedbackschleifen)

---

## 0. Normative Sprache

Die Schlüsselwörter **MUST**, **MUST NOT**, **SHOULD**, **MAY** sind normativ zu verstehen (Audit/Policy-Sprache).
Dieses Dokument ist eine **Governance-Leitplanke**. Es ist **keine** Implementierung und **keine** Live-Freischaltung.

---

## 1. Zweck

Dieses Dokument definiert **auf Governance-Ebene**, wann Peak_Trade **Live-Handeln** zulassen darf (GO) und wann es **verboten** ist (NO-GO), insbesondere im Kontext von **AI-Unterstützung** und **Autonomie**.

Es dient als:
- Entscheidungsrahmen für Go/No-Go
- Audit-Grundlage (prüfbare Kriterien + Evidence-Pflichten)
- Schutz gegen „Performance-First“-Fehlentscheidungen

---

## 2. Definitionen (Day-Trading-spezifisch)

### 2.1 Betriebsmodi
- **SHADOW:** Daten & Signale laufen, keine Orders.
- **PAPER:** Orders werden simuliert / Paper-Broker; keine realen Trades.
- **LIVE:** Orders gehen an Broker/Exchange und können Kapital bewegen.

### 2.2 Autonomie (operativ definiert)
Autonomie ist ein **zeitlich begrenztes Recht**, das das System erhält, innerhalb klarer Grenzen Entscheidungen **auszuführen**.

- **Autonomy Lease:** Freigabe mit Ablaufzeit (TTL), Scope (Instrumente/Session), Budget (Risiko/Exposure/Trade Count).
- **Autonomy Budget:** quantifizierte Grenzen (z.B. Daily Loss Limit, Max Exposure, Max Orders/Tag).

### 2.3 Day-Trading-Non-Negotiables (MUST)
Für LIVE (egal ob manual-only oder bounded-auto) gelten zwingend:
- **Daily Loss Limit** (harte Sperre)
- **Kill Switch / Emergency Stop** (sofort wirksam)
- **Flat-by-Time** (Positionsabbau bis definierter Zeit)
- **Max Trades/Tag** und **Max Exposure** (harte Limits)
- **Cooldown / Circuit Breaker** nach Störungen oder Limit-Ereignissen

---

## 3. Nicht verhandelbare Grundannahmen

- Day-Trading ist **hochgradig riskant**.
- AI kann Analysequalität erhöhen, erhöht aber **nicht automatisch** Sicherheit.
- **Governance steht über AI.**
- **Default ist immer NO-GO.**
- Autonomie ist ein **Recht auf Zeit**, kein Dauerzustand.

---

## 4. Rollenverständnis: Was AI ist – und was nicht

### 4.1 AI ist (Allowed Use)
AI kann eingesetzt werden als:
- Denk- und Analyseinstanz
- Erklär- und Auditinstanz (Narrative + Rekonstruktion)
- Entscheidungs-Vorbereiter (Recommendations, nicht final)
- Policy-/Autonomie-Wächter (Governor) im Sinne von **Prüfen, Flaggen, Blockieren** auf Basis von Policy

### 4.2 AI ist nicht (Forbidden Use)
AI **MUST NOT** sein:
- Order-Placer (direktes Order-Placement)
- Autor von Risk-Regeln im Live-Betrieb
- Ausnahme-Entscheider (Overrides/Exceptions)
- Live-Optimierer (Parameter-Tweaks on-the-fly im Live-Betrieb)

---

## 5. Verhältnis zu Peak_Trade Layern (Architektur-Invariante)

Die folgenden Invarianten **MUST** gelten:
- Strategy Layer bleibt **deterministisch** (reproduzierbare Outputs bei gleichen Inputs).
- Risk Layer bleibt **hart und final** (Risk kann blockieren; Risk gewinnt immer).
- Execution bleibt **dumm und schnell** (keine Modellabhängigkeit im Hot Path).
- AI sitzt **darüber**, nicht **dazwischen**.
- Go/No-Go ist die **oberste Instanz** (über Strategy/Risk/Execution).

**Audit-Kernregel:** Der Order-Path **MUST** auch ohne AI vollständig funktionieren.

---

## 6. Go/No-Go State Machine (Audit-Fundament)

### 6.1 Zustände
- **NO_GO:** Kein Live-Order-Placement. Shadow/Paper erlaubt.
- **PAPER_GO:** Paper-Execution erlaubt; Live verboten.
- **LIVE_MANUAL_ONLY:** Live ist erlaubt, aber jede Order wird manuell bestätigt.
- **LIVE_BOUNDED_AUTO:** Live ist erlaubt innerhalb Autonomy Lease + Autonomy Budget.
- **EMERGENCY_STOP:** Harte Sperre; nur Recovery-Runbook.

### 6.2 Transition-Regeln (MUST)
- Jede Transition in einen „stärkeren“ Zustand (z.B. PAPER_GO → LIVE_MANUAL_ONLY) **MUST** ein Evidence Pack haben (siehe Abschnitt 10).
- Jede GO-Freigabe **MUST** als Autonomy Lease mit TTL erteilt werden.
- Jede GO-Freigabe **MUST** jederzeit widerrufbar sein; Widerruf **MUST** sofort wirksam sein (vor nächstem Order-Submit).
- Jede Transition **MUST** geloggt werden (wer, wann, warum, welche Evidence, welche Versionen).

---

## 7. Zentrale Frage (entscheidungsleitend)

Die zentrale Frage ist:

> **Ist dieses System aktuell in der Lage, Verantwortung für eigenes Handeln zu tragen?**

Nicht:
- „Ist das Modell gut?“
- „Ist die Performance hoch?“

Sondern:
- Erklärbarkeit
- Kontrollierbarkeit
- Risikodominanz
- Auditierbarkeit

---

## 8. Harte NO-GO Gründe (MUST → NO_GO oder EMERGENCY_STOP)

Die folgenden Bedingungen **MUST** zu NO_GO führen (oder bei akuter Gefahr zu EMERGENCY_STOP):

1) **AI nicht vollständig integriert** (unklarer Einfluss, „KI nicht drauf“, unklare Pipeline).  
2) **Entscheidungen nicht rekonstruierbar** (fehlende Logs/Inputs/Outputs/IDs/Versionen).  
3) Kein klares „Warum nicht handeln“ / kein Hold-Reasoning.  
4) **Risk kann nicht blockieren** (Risk-Override fehlt / technisch unwirksam).  
5) Lernen beeinflusst Live-Verhalten (ungeprüfte Online-Learning-Änderungen).  
6) Autonomie-Entzug ist nicht sofort wirksam.  
7) Order-Path hängt an Modellverfügbarkeit (Modell-Ausfall = Trading-Ausfall).  
8) Kill Switch / Daily Loss Limit / Flat-by-Time nicht aktiv oder nicht getestet.

---

## 9. Rolle des Owners (Constitution Authority)

Der Owner ist:
- Verfassungsinstanz
- darf Autonomie entziehen
- darf Live stoppen
- verantwortet die Dokumente/Policies/Sign-offs

Der Owner ist nicht:
- Trade-Entscheider im operativen Sinne
- Ausnahme-Genehmiger außerhalb des Change-Prozesses
- Parameter-Tweaker im Live-Betrieb

**Grundsatz:** Owner darf das System **abschalten**, aber nicht „live steuern“.

---

## 10. Evidence & Audit (MUST)

### 10.1 Evidence Pack Pflicht
Jede GO-Freigabe (PAPER_GO, LIVE_MANUAL_ONLY, LIVE_BOUNDED_AUTO) **MUST** ein Evidence Pack haben, gespeichert im Repo (versioniert), mit eindeutigem Identifier.

Empfohlenes Pfadschema:
- `docs/governance/evidence/EVP_YYYYMMDD_<session>_<env>.md`

### 10.2 Mindest-Evidence (Checkliste)
Ein Evidence Pack **MUST** mindestens enthalten:

**A) System-Identität**
- Commit SHA / Tag / Release-ID
- Config Snapshot (redacted secrets)
- Env (Shadow/Paper/Live), Instrument-Universum, Session-Zeiten

**B) Governance & Policy**
- Aktive Go/No-Go Policy Version
- Autonomy Lease (TTL, Scope, Budget)
- Rollenmatrix-Referenz (AI_Roles_Matrix)

**C) Risiko & Safety**
- Nachweis: Risk kann blockieren (Test/Drill-Output)
- Daily Loss Limit, Kill Switch, Flat-by-Time: aktiv + getestet
- Incident/Recovery Runbook Links

**D) Rekonstruktion**
- Event IDs / Correlation IDs
- Logs: Inputs/Outputs/Decisions (inkl. Hold-Reasons)
- Modell-/Prompt-/Policy-Versionen (falls AI beteiligt)

**E) Monitoring**
- Live Health Signals (Data feed, execution health, latency, error budget)
- Alerting (wer bekommt Alerts, wie schnell, Eskalationspfad)

**F) Sign-off**
- Owner Sign-off (Name/Datum)
- Risk/Compliance Sign-off (falls getrennt)
- Gültigkeitsdauer (TTL) + Review Trigger

---

## 11. Modell-Platzierung & Deep Research (Governance-Regel)

### 11.1 Grundregel
**Deep Research (web-/syntheseorientiert)** ist **MUST NOT** im Trading-Hot-Path.
Deep Research ist erlaubt für:
- Pre-market / Post-market Research
- Regime-/News-Synthese für Strategiewahl auf Governance-Ebene
- Dokumentations-/Policy-Synthese

### 11.2 Model Routing Dokument
Die konkrete Modellzuordnung (welches Modell für welche Aufgabe) wird separat gepflegt:
- `docs/governance/MODEL_PLACEMENT_AND_ROUTING.md`

---

## 12. Change Control (Audit-Stabilität)

Änderungen an:
- Go/No-Go Kriterien
- Rollenabgrenzung
- Autonomy Budget/Lease Defaultwerte
- Risk/Execution invariants

**MUST** über einen dokumentierten Change-Prozess laufen:
- PR mit Review
- Evidence (Tests/Drills)
- Version bump dieses Dokuments (SemVer oder Date-Version)
- Aktualisierung des Evidence Pack Templates (falls nötig)

---

## 13. Abschluss (Prinzip)

Ein gutes Day-Trading-System scheitert selten an fehlender Intelligenz,
sondern an fehlender Selbstbegrenzung.

Dieses Dokument existiert, um genau das zu verhindern.
