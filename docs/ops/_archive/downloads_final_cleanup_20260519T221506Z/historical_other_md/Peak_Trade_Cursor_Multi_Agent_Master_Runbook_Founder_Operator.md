# Peak_Trade – Cursor Multi-Agent Master-Runbook (Founder / Operator)

Stand: 2026-03-21
Modus: `paper_stability_guard`
Ziel: Peak_Trade von heute bis zu einem späteren, streng kontrollierten, potenziell autonomen Trading-System weiterentwickeln – ohne Paper-, Shadow- oder Evidence-Bestände zu beschädigen.

---

## 1. Zweck dieses Runbooks

Dieses Runbook ist die operative Kurzfassung für die tägliche Arbeit mit Cursor Multi-Agent. Es ist nicht die Produktvision, sondern der praktische Führungsrahmen für die nächsten Themenblöcke.

Es gilt für alle Arbeiten, die auf `main` vorbereitet und anschließend in genau **einem klar abgegrenzten PR pro Thema** umgesetzt werden.

---

## 2. Nicht verhandelbare Regeln

### 2.1 Harte Schutzregeln

1. **Paper- und Shadow-Daten nicht anfassen.**
2. **Evidence-Artefakte nicht überschreiben, nicht löschen, nicht umbenennen.**
3. **Keine Live-Freischaltung.**
4. **Keine Secrets / Keys / Klartext-Zugangsdaten in Docs, Code oder Prompts.**
5. **Jedes Thema genau ein PR.**
6. **Wenn Scope unklar ist: docs-first, operator-first, safety-first.**
7. **Bei Unsicherheit: read-only Inventur vor jeder Mutation.**

### 2.2 Was ausdrücklich nicht passieren darf

- kein „kurz mal“ Testdaten bereinigen
- kein Shadow-/Paper-Reset ohne expliziten Anlass
- keine Runtime-Änderung, wenn das Thema eigentlich nur Doku / Mapping / Plan betrifft
- keine Misch-PRs aus mehreren Themen
- keine Live-Execution-Autorisierung per Nebenwirkung

---

## 3. Ausgangslage

Peak_Trade ist heute ein **Research-/Backtest-/Paper-/Shadow-System**. Testnet ist vorbereitet, Live bleibt governance-gesperrt. Execution ist deterministisch und gated; LLM-Schichten sind advisory oder supervisory, aber nicht finale Ausführungsinstanz. Der weitere Weg zur Autonomie ist explizit von zusätzlicher Evidence, Controls und Review abhängig.

---

## 4. Operative Arbeitsweise in Cursor

### 4.1 Standard-Reihenfolge pro Thema

1. **Topic wählen**
2. **Read-only Inventur** auf `main`
3. **einen klaren Slice definieren**
4. **Feature-Branch anlegen**
5. **genau einen Themenblock umsetzen**
6. **lokal prüfen**
7. **genau einen PR öffnen**
8. **Checks abwarten / fixen**
9. **merge + closeout**
10. **Block stabil halten**

### 4.2 Git-Kontext immer explizit

Jeder Cursor-Block muss immer voranstellen:

- `GIT_CONTEXT=main` oder `main_to_feature_branch` oder `feature-branch`
- `BRANCH=<branch-name>`
- `MODE=paper_stability_guard`
- `TOPIC=<genau_ein_thema>`
- `GOAL=<genau_ein_ziel>`

### 4.3 Scope-Kontrolle

Vor jedem PR muss klar sein:

- Was ist das eine Thema?
- Was ist explizit **nicht** Teil des PR?
- Ist es docs-only, review-only, mapping-only oder runtime?
- Gefährdet es Paper/Shadow/Evidence?

Wenn die Antwort unscharf ist, ist der Scope zu groß.

---

## 5. Entry Points – von wo aus wir arbeiten

### 5.1 Strategische Entry Points

Diese Dokumente sind die erste Schicht für neue Themen:

- das aktuelle Autonomous-Trading-Handout
- AI-/Governance-/Policy-Dokumente
- Risk-/Execution-/Observability-Runbooks
- aktuelle Reviews und Closeouts zu stabilisierten Blöcken

### 5.2 Operative Entry Points

Für neue Themen zuerst prüfen:

- `docs&#47;ops&#47;reviews&#47;`
- `docs&#47;ops&#47;runbooks&#47;`
- `docs&#47;ops&#47;specs&#47;`
- `docs&#47;execution&#47;`
- `docs&#47;risk&#47;`
- `src&#47;`
- `tests&#47;`
- `scripts&#47;`

### 5.3 Stabilisierte Blöcke nicht unnötig neu öffnen

Diese Themen nur wieder anfassen, wenn es einen **konkreten neuen Anlass** gibt:

- balance semantics guardrail
- incident-state read model
- kill-switch adapter plan/review/map/matrix
- observability operator-summary consistency
- execution telemetry runbook consistency
- live broker boundary review

---

## 6. Welche Arten von Themen zuerst sinnvoll sind

### Priorität A – sicher und wertvoll

- docs-only Konsistenzslices
- operator-facing Runbooks
- mapping / contract / review / gap-matrix Themen
- observability / evidence / governance Alignment

### Priorität B – vorsichtig, aber machbar

- read-model Implementierungen in operator surfaces
- ops cockpit visibility / mapping
- risk- oder execution-adjacent read-models

### Priorität C – nur mit expliziter Entscheidung

- runtime mutation in risk / execution
- testnet-bezogene Änderungen
- anything touching live boundaries
- proposer/critic runtime changes

---

## 7. Roadmap-Logik bis „finished“

### Phase 0 – Stabilisierte Foundation

Ziel:
- vorhandene Governance-, Risk-, Evidence- und Ops-Struktur erhalten
- stabilisierte Blöcke nicht wieder aufbrechen
- nur kleine, klare, saubere PRs

### Phase 1 – Unknown Reduction

Ziel:
- alle unklaren AI-, Runtime-, Governance- und Operator-Grenzen dokumentieren
- offene Bindings, Contracts, Consumer-Maps, Gap-Matrizen schließen

Lieferobjekte:
- Reviews
- Plans
- Contracts
- Gap-Matrices
- Runbook-Härtungen

### Phase 2 – Operator / Observability Maturity

Ziel:
- operatorische Interpretierbarkeit erhöhen
- Incident-, Telemetry-, Ops-Cockpit- und Evidence-Pfade konsistent machen
- keine Runtime-Autorisierung, aber maximale Sichtbarkeit

### Phase 3 – Testnet Readiness (nur mit expliziter Freigabe)

Ziel:
- Sandbox- und Recon-Fähigkeit
- Incident Drills
- Kill-Switch / Risk / Entry / Operator-Pfade in Testnet belastbar

### Phase 4 – Controlled Live Readiness (nicht automatisch)

Ziel:
- keine echte Freigabe, sondern Nachweis der Freigabefähigkeit
- harte Limits
- Go/No-Go-Packs
- mehrstufige Reviews

### Phase 5 – Potenziell autonomeres System

Nur möglich, wenn vorher belegt ist:
- Risk dominiert weiterhin deterministisch
- proposer/critic runtime-evidenziert
- control stack vollständig auditierbar
- online learning nicht nur konzipiert, sondern kontrolliert und governance-fähig

### Phase 6 – „Finished“ aus Produktsicht

Praktisch bedeutet „finished“ nicht „alles kann alles“, sondern:

- stabiler, dokumentierter, verkaufbarer Systemkern
- klare Governance-Story
- klare Operator-Story
- klarer Risk-/Execution-Boundary-Stack
- dokumentierte Roadmap für spätere Autonomie
- kein Marketing-Fake über Fähigkeiten, die nicht belegt sind

---

## 8. Was bis auf Weiteres nicht autonom werden darf

- finale Execution Authority
- Risk-Limit-Override
- Kill-Switch-Override
- geheime Config-Änderungen
- Self-Learning direkt am Kapitalpfad
- Key-/Secret-Handling
- ungeprüfte Model-Binding-Wechsel

---

## 9. Standard-Template für jedes neue Thema

### Vor dem Branch

- Thema benennen
- prüfen, ob es wirklich neu ist
- prüfen, ob es einen stabilisierten Block unnötig wieder öffnet

### Read-only Inventur

Fragen:
- Welche Docs existieren schon?
- Welche Runbooks / Specs / Reviews gibt es?
- Welche Runtime- oder Test-Touchpoints existieren?
- Ist das Thema docs-only lösbar?

### Branch-Erstellung

- Branch von `main`
- Name: präzise, thematisch, kurz

### Umsetzung

- nur dieses eine Thema
- keine Seiteneffekte
- keine Scope-Ausweitung während der Arbeit

### PR

Der PR muss sagen:
- genau dieses Thema
- genau diese Dateien
- docs-only oder runtime+tests
- keine Paper-/Shadow-Störung

### Closeout

Jeder Block endet mit:
- Sync auf `main`
- Closeout-Datei
- explizite Aussage: Block jetzt stabil halten

---

## 10. Standard-Entscheidungslogik: Was als Nächstes?

Wenn kein Thema klar ist, dann gilt:

1. **Docs-first**
2. **Operator-first**
3. **Observability-first**
4. **Governance-before-runtime**
5. **Risk-before-autonomy**

Praktisch heißt das:
- erst Reviews, Contracts, Plans, Runbooks, Gap-Matrices
- dann Mappings / read-model visibility
- erst später Runtime-Integration

---

## 11. Was Cursor Multi-Agent konkret leisten soll

### Planner
- Thema sauber schneiden
- Scope klein halten
- Risiken nennen

### Research / Reader
- Docs, Specs, Runbooks, Reviews inventarisieren
- Entry Points finden

### Implementer
- genau den einen Slice umsetzen
- nichts seitlich anfassen

### Critic
- Scope creep stoppen
- unstabile Themen erkennen
- Evidence-/Safety-Verletzungen markieren

### Verifier
- Tests / Lint / Docs-Gates prüfen
- keine falschen Closeouts produzieren

### Publisher
- PR-Text, Closeout, Handoff
- sauberer Abschluss, kein Churn danach

---

## 12. Operational Master Rule

Peak_Trade wird nicht dadurch „fertig“, dass wir möglichst schnell Live oder Autonomie anschalten. Peak_Trade wird dadurch fertig, dass wir Schicht für Schicht einen Stack bauen, der:

- technisch tragfähig,
- governance-fähig,
- operatorisch lesbar,
- evidenzbasiert,
- und verkaufbar ist.

Die oberste Regel bleibt:

> **Kein Fortschritt auf Kosten von Safety, Evidence, Paper oder Shadow.**

---

## 13. Praktischer Abschlusszustand pro Block

Ein Block ist fertig, wenn:

- das Thema präzise bearbeitet wurde
- genau ein PR verwendet wurde
- `main` sauber ist
- ein Closeout existiert
- klar dokumentiert ist, warum der Block jetzt stabil bleibt

Wenn das nicht erfüllt ist, ist der Block nicht fertig.

---

## 14. Empfohlene Nutzung im Alltag

Für jeden neuen Chat oder Cursor-Lauf:

1. `main`-Status prüfen
2. stabilisierte Blöcke nicht erneut aufreißen
3. genau ein neues Thema wählen
4. read-only Inventur
5. Branch
6. ein PR
7. merge
8. closeout
9. stabil halten

---

## 15. Schlussformel

Peak_Trade wird von **research-getriebenem, stark kontrolliertem Trading-Framework** zu einem potenziell später autonomen System nur dann sauber wachsen, wenn jede Stufe:

- nachvollziehbar,
- evidenzpflichtig,
- deterministisch gerahmt,
- und operatorisch kontrollierbar bleibt.

Dieses Runbook ist genau dafür der Führungsrahmen.
