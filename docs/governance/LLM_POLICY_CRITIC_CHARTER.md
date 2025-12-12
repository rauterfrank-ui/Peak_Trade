# Peak_Trade – LLM Policy Critic (LLM-PC)

**Zweck:** Der LLM Policy Critic ist ein *read-only Governance-Layer*, der vorgeschlagene Änderungen (Patches, Config-Edits, Runbook-Anpassungen, Auto-Promotions) gegen Sicherheits-, Risiko- und Betriebsrichtlinien prüft – und dabei **niemals** Hard-Gates ersetzt, sondern **ergänzt**.

## 1) Warum es Sinn ergibt (Symbiose)

Peak_Trade hat (zurecht) harte, deterministische Schutzschichten (Live-Locks, Risk-Limits, Env-Gates, Go/No-Go). Der LLM-PC ist die „semantische" Ergänzung:

* **Deterministik schützt** vor klar definierbaren Verstößen.
* **LLM-PC erkennt** „Graubereiche": implizite Bypass-Muster, riskante Nebenwirkungen, fehlende Testpläne, unklare Operator-Steps, fragile Annahmen, unzureichende Dokumentation.
* **Ergebnis:** weniger gefährliche Auto-Apply-Fehler, sauberere Promotion-Cycles, bessere Reports, stärkere Operator-Sicherheit – ohne Autonomie-Überhang.

> Leitprinzip: **LLM-PC darf bremsen, aber nicht beschleunigen.** (Er kann etwas als „Review erforderlich" markieren, aber nicht allein „freischalten".)

---

## 2) Einordnung im System

### 2.1 Upstream (liefert Input)

* bounded_auto / Promotion Proposal Cycle
* Patch-Generatoren (z.B. Fix-Vorschläge aus Sweep-Runs)
* Konfig-Änderungen (TOML/YAML)
* Docs/Runbooks-Änderungen (Operator-Sicherheit)

### 2.2 Downstream (nutzt Output)

* Auto-Apply Gate (entscheidet: Apply / Block / Manual)
* Operator (Review-Checkliste + konkrete Fragen)
* TestHealth Automation (Testplan-Hinweise, Mindesttests)
* InfoStream (Governance-IntelEvent / LearningSnippet)

---

## 3) Was der LLM Policy Critic **darf**

### 3.1 Read-only Analyse

* Diffs, Dateiliste, Konfig-Snippets, Runbook-Text, Commit-Message-Drafts analysieren
* Risiken klassifizieren (Security/Risk/Execution/Docs/Compliance)
* **Evidenz-basiert** argumentieren: *jede* Warnung/Blockade muss auf konkrete Diff-Stellen referenzieren

### 3.2 Entscheidungen empfehlen (nicht ausführen)

* `ALLOW` (unbedenklich)
* `REVIEW_REQUIRED` (manuelles Review nötig)
* `AUTO_APPLY_DENY` (Auto-Apply verboten; nur manueller Prozess möglich)

### 3.3 Konkrete, sichere Vorschläge liefern

* Minimaler Testplan („mindestens diese Tests laufen lassen")
* Runbook-Ergänzungen („Operator-Schritt fehlt", „Rollback fehlt")
* Sicherheits-Härtungen („Secrets redaction", „Config-Guard")
* „Fragen an den Autor" (z.B. „Warum Limit erhöht? Welche Daten? Welche Metrik?")

### 3.4 Logging/Transparenz

* Strukturierter Report (JSON) + kurze Human-Summary
* Optional: Emittiert **InfoStream-Events** (Kategorie: GOVERNANCE), damit Lern-/Audit-Spuren entstehen

---

## 4) Was der LLM Policy Critic **nicht darf** (harte Grenzen)

### 4.1 Keine autonomen Systemänderungen

* **Nie** Patches anwenden, Dateien verändern, Branches mergen, Releases triggern
* **Nie** Live-Trading aktivieren oder Gating/Locks entfernen/abschwächen
* **Nie** Risk-Limits hochsetzen oder Safety-Checks abschalten

### 4.2 Kein „Freischalten" von gefährlichen Aktionen

* Ein `ALLOW` des LLM-PC **ersetzt** keine deterministischen Gates.
* Kritische Änderungen bleiben an harte Policies gebunden (z.B. Live-Gates, Confirm-Token, Operator-Steps).

### 4.3 Keine Secrets / kein Datenabfluss

* Kein Speichern oder Wiedergeben von Secrets (Token/Keys).
* In Reports: **Redaction** statt Klartext.
* Keine „copy-paste"-Wiedergabe potenzieller Secrets.

### 4.4 Keine Ausführung / kein Netz

* Keine Codeausführung, keine Shell-Commands, kein externer Netzwerkzugriff als Bestandteil des Critic-Kerns.
* Er arbeitet nur mit dem bereitgestellten Kontext.

---

## 5) Invarianten (Systemvertrag)

Diese Invarianten sind „nicht verhandelbar" – jede Integration muss sie erzwingen:

1. **Least Privilege:** LLM-PC bekommt nur den Diff + Kontext, nicht mehr.
2. **Fail-Closed für Auto-Apply:** Wenn LLM-PC abstürzt/unavailable/unklar → `REVIEW_REQUIRED` oder `AUTO_APPLY_DENY`.
3. **Hard-Gates bleiben souverän:** LLM-PC kann *nie* Live-Gates überschreiben.
4. **Evidence First:** Keine Behauptung ohne konkrete Referenz (Datei/Pattern/Stelle).
5. **No Silent Pass:** Jede Entscheidung liefert eine kurze Begründung + Risiken.

---

## 6) Policy-Scope (was wird geprüft)

### 6.1 Security Policies

* Secrets im Diff / Testdaten / Logs
* gefährliche Dependencies/Imports (z.B. ungeprüfte HTTP calls in critical path)
* Injection-Risiken, Pfad-Traversal, unsichere Eval/Exec Muster

### 6.2 Live & Execution Policies

* Änderungen in `src/live/`, `src/execution/`, `src/exchange/`
* Alles, was Orders/Positions/Leverage/Exposure beeinflusst
* Jede Änderung, die „Live-Ready" impliziert

### 6.3 Risk & Governance Policies

* Risk-Limits / Drawdown / Leverage / Notional
* Disable/Relax von Risk-Checks
* Konfig-Switches (Strategy Switch / Allowed Strategies / R&D vs Live)

### 6.4 Ops & Runbook Policies

* Gibt es Rollback?
* Gibt es Monitoring/Alerting-Hinweise?
* Sind Operator-Schritte eindeutig, wiederholbar, testbar?

### 6.5 Test & Repro Policies

* Fehlt ein Testplan?
* Fehlen neue Tests bei sicherheitsrelevanten Änderungen?
* Reproduzierbarkeit (Seed, deterministische Outputs)

---

## 7) Ergebnis-Format (Output Contract)

Der LLM-PC liefert immer:

* `max_severity`: INFO | WARN | BLOCK
* `recommended_action`: ALLOW | REVIEW_REQUIRED | AUTO_APPLY_DENY
* `violations[]`:

  * `rule_id` (stabil, maschinenlesbar)
  * `severity`
  * `message`
  * `evidence[]` (z.B. Dateiname + kurzes Snippet/Pattern)
  * `suggested_fix` (optional)
* `minimum_test_plan[]` (optional)
* `operator_questions[]` (optional)
* `summary` (1–3 Sätze)

---

## 8) Zusammenspiel mit deterministischen Checks (entscheidend)

**Regel:** Auto-Apply darf nur passieren, wenn *beide* Schichten grün sind:

* Deterministische Rules: PASS
* LLM-PC: `ALLOW`

Wenn deterministisch PASS, aber LLM-PC `REVIEW_REQUIRED`:
→ Keine Auto-Apply. Manual Review & ggf. Testplan.

Wenn deterministisch FAIL:
→ LLM-PC wird zwar geloggt, kann aber nicht „retten".

---

## 9) Betriebsmodi (Empfehlung)

### Mode A – V0 „Deterministic-Only" (CI/Always-On)

* reine Pattern/Path/Rule Engine
* super stabil, keine LLM-Abhängigkeit
* setzt das Grundgerüst

### Mode B – V1 „LLM-Augmented" (Advisory)

* LLM ergänzt *nur* Begründung, Risikoanalyse, bessere Operator-Fragen
* darf in Richtung Sicherheit immer strenger sein
* niemals permissiver als Deterministik

### Mode C – „Strict Change Zones"

Für bestimmte Pfade/Änderungstypen gilt immer:

* `AUTO_APPLY_DENY` (z.B. Order-Routing, Live-Arming, Risk-Core)

---

## 10) Definition von „Symbiose" (konkret)

Der LLM-PC ist nicht „ein weiterer Bot", sondern ein *Verstärker*:

* **bounded_auto** produziert Vorschläge → LLM-PC zwingt Klarheit + Tests + Safety-Narrativ
* **TestHealth** prüft mechanisch → LLM-PC prüft semantisch („passt das zur Absicht?")
* **InfoStream** sammelt Intel → LLM-PC macht daraus Governance-Intel & Learning-Snippets
* **Operator** bekommt weniger Rauschen, mehr konkrete Fragen, bessere Runbooks

---

## 11) Nicht-Ziele (damit es sauber bleibt)

* Kein „Autopilot", kein autonomes Refactoring
* Keine Produktentscheidungen („wir sollten Strategie X live schalten")
* Kein Ersatz für Code-Review – eher „Pre-Review" + „Safety-Review"
* Keine Bewertung von Profitabilität/Alpha (das ist nicht Governance)

---

## 12) Kurzform (one-liner)

**Der LLM Policy Critic ist ein read-only, evidence-basiertes Governance-Korrektiv, das Auto-Apply nur bremsen darf, Hard-Gates nie ersetzt und die gesamte Promotion-/Learning-Loop-Symbiose über klare Reports, Testpläne und Operator-Sicherheit stärkt.**

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| v1.0 | 2025-12-12 | Initial charter created. Defined core principles, permissions, boundaries, invariants, policy scope, and integration points. |
