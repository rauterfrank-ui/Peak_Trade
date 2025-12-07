# Peak_Trade – Governance & Safety Overview

> **Status:** Phase 25 – Governance & Safety-Dokumentation
> **Scope:** Rein dokumentarisch, keine Code-Änderungen
> **Ziel:** Organisatorischer & prozessualer Rahmen für Peak_Trade

---

## 1. Einleitung

### Was ist Governance in Peak_Trade?

Governance in Peak_Trade umfasst die **organisatorischen Regeln, Prozesse und Verantwortlichkeiten**, die sicherstellen, dass das System sicher, nachvollziehbar und kontrolliert betrieben wird.

Während die technische Architektur (Phasen 1–24) festlegt, **wie** das System funktioniert, definiert die Governance, **wer** was tun darf, **wann** Änderungen erlaubt sind und **wie** mit Risiken umgegangen wird.

### Bezug zum aktuellen Stand

Peak_Trade ist aktuell ein **Research-/Backtest-/Paper-/Shadow-System**:

- **Strategien & Research**: Playground mit `ma_crossover`, `trend_following`, `mean_reversion`, etc.
- **Analytics & Reporting**: Experiment Explorer, HTML-Reports, Regime-Analyse
- **Execution**: Paper-/Shadow-Execution (Phase 24), keine echten Orders
- **Safety-Status**: Live-/Testnet-Executors sind Stubs, alle echten Order-Pfade blockiert

Diese Governance-Dokumentation bereitet Peak_Trade auf **zukünftige Phasen** vor, in denen Testnet- oder Live-Trading relevant werden könnte.

---

## 2. Grundprinzipien

### 2.1 Safety-First, nicht "Schnell Live"

**Kein voreiliges Live-Trading.**

- Jeder Schritt Richtung Testnet/Live erfordert explizite **Phasen**, **Gates** und **Reviews**
- Lieber ein konservativer Backtest mehr als ein verfrühter Live-Test
- "Fail-safe > Fail-fast": Bei Unsicherheit blockieren, nicht ausführen

### 2.2 Transparenz & Nachvollziehbarkeit

**Jede Aktion muss rückverfolgbar sein.**

- Alle Runs werden in der Experiments-Registry geloggt
- Order-Flows sind dokumentiert mit Strategie, Parametern, Risk-Checks
- Änderungen an Limits/Configs werden versioniert und begründet

### 2.3 Trennung der Domänen

**Klare Grenzen zwischen den Bereichen:**

| Domäne | Beschreibung | Beispiele |
|--------|--------------|-----------|
| **Research** | Strategie-Entwicklung, Backtests, Sweeps | `run_backtest.py`, Sweeps, Regime-Analyse |
| **Execution** | Order-Generierung und -Routing | `ExecutionPipeline`, Shadow-Execution |
| **Testnet/Live** | Echte oder simulierte Exchange-Verbindungen | *Nicht aktiviert* |

Research-Code darf Live-Endpoints **niemals** versehentlich erreichen können.

### 2.4 Defense in Depth

**Mehrere Sicherheitsschichten:**

1. **Environment-Mode** (`paper`/`testnet`/`live`)
2. **Global Flags** (`enable_live_trading = false`)
3. **Risk-Limits** (`LiveRiskLimits`, `max_daily_loss`, etc.)
4. **SafetyGuard** (zusätzliche Prüfungen, Whitelists)
5. **Governance-Prozesse** (Reviews, Checklisten, Freigaben)

---

## 3. Rollen & Verantwortlichkeiten

### 3.1 Rollenübersicht

| Rolle | Kurzbeschreibung |
|-------|------------------|
| **Owner / Systemverantwortlicher** | Gesamtverantwortung, Phasen-Freigaben |
| **Developer / Quant** | Implementierung, Strategie-Entwicklung |
| **Reviewer / Risk Officer** | Review von Änderungen, Risk-Bewertung |
| **Operator** (zukünftig) | Betrieb, Monitoring, Incident-Response |

### 3.2 Owner / Systemverantwortlicher

**Aufgaben:**
- Freigabe von Phasen-Übergängen (z.B. Research → Shadow → Testnet)
- Genehmigung von Änderungen an globalen Safety-Einstellungen
- Finale Entscheidung bei Konflikten oder Unsicherheiten

**Rechte:**
- Darf `enable_live_trading` und andere kritische Flags ändern
- Darf neue Phasen aktivieren

**Pflichten:**
- Dokumentation aller Freigabe-Entscheidungen
- Sicherstellung, dass Checklisten eingehalten werden
- Verantwortung für Gesamt-Risk des Systems

### 3.3 Developer / Quant

**Aufgaben:**
- Implementierung neuer Strategien und Features
- Durchführung von Backtests, Sweeps, Regime-Analysen
- Dokumentation von Code-Änderungen

**Rechte:**
- Darf Code in Research-/Backtest-Layern ändern
- Darf neue Strategien in die Registry einfügen
- Darf Backtests und Shadow-Runs ausführen

**Pflichten:**
- Code-Review für kritische Änderungen einholen
- Tests für neue Funktionalität schreiben
- Keine Änderung an Safety-/Live-Pfaden ohne explizite Freigabe

### 3.4 Reviewer / Risk Officer

**Aufgaben:**
- Review von Änderungen an Risk-Settings und Limits
- Prüfung von Strategie-Performance vor Phasen-Übergängen
- Erstellung und Pflege von Risk-Reports

**Rechte:**
- Darf Phasen-Übergänge blockieren (Veto-Recht)
- Darf Risk-Limits empfehlen

**Pflichten:**
- Schriftliche Begründung für Freigaben/Blockaden
- Regelmäßige Risk-Reports erstellen
- Sicherstellung, dass Governance-Dokumente aktuell sind

### 3.5 Operator (zukünftig)

**Aufgaben:**
- Überwachung des laufenden Systems
- Ausführung von Runbooks bei Incidents
- Eskalation bei kritischen Ereignissen

**Rechte:**
- Darf System pausieren/stoppen (Kill-Switch)
- Darf Alerts bestätigen und dokumentieren

**Pflichten:**
- Protokollierung aller Eingriffe
- Sofortige Eskalation bei kritischen Incidents

---

## 4. Entscheidungsprozesse

### 4.1 Einführung neuer Strategien

**Prozess:**

1. **Entwicklung**: Developer implementiert Strategie mit Tests
2. **Backtest**: Mindestens 6 Monate historische Daten
3. **Review**: Code-Review durch zweiten Developer oder Reviewer
4. **Registry**: Eintrag in `strategies.available` nach Review
5. **Dokumentation**: Strategie in `docs/` dokumentieren

**Kriterien für Freigabe:**
- Alle Unit-Tests grün
- Backtest-Metriken dokumentiert
- Keine bekannten kritischen Bugs

### 4.2 Änderung von Risk-Limits

**Prozess:**

1. **Antrag**: Developer/Quant formuliert Änderungswunsch mit Begründung
2. **Risk-Analyse**: Reviewer prüft Auswirkungen
3. **Freigabe**: Owner genehmigt bei positiver Risk-Analyse
4. **Dokumentation**: Änderung in Changelog dokumentieren
5. **Umsetzung**: Änderung in `config.toml` mit Commit-Message

**Zwei-Augen-Prinzip:**
- Änderungen an `[live_risk]` erfordern **immer** Review
- Keine selbst-genehmigten Änderungen bei kritischen Limits

### 4.3 Phasen-Übergänge (Stufen-Wechsel)

**Prozess:**

1. **Checklist**: Relevante Checklist aus `LIVE_READINESS_CHECKLISTS.md` durcharbeiten
2. **Dokumentation**: Alle Punkte abhaken und dokumentieren
3. **Review**: Reviewer prüft Checklist-Ergebnis
4. **Freigabe**: Owner gibt Übergang frei
5. **Aktivierung**: Technische Umsetzung des Stufen-Wechsels

**Beispiel:** Research → Shadow (Stufe 0 → 1)
- Siehe `LIVE_READINESS_CHECKLISTS.md`, Abschnitt "Research → Shadow"

**Portfolio-basierte Promotions:**

Portfolio-Entscheidungen (Research → Testnet/Live) erfolgen entlang des in [`PLAYBOOK_RESEARCH_TO_LIVE_PORTFOLIOS.md`](PLAYBOOK_RESEARCH_TO_LIVE_PORTFOLIOS.md) beschriebenen Ablaufs (Phase 54). Dieses Playbook definiert klare Go/No-Go-Kriterien, Dokumentationsanforderungen und Governance-Freigaben für Portfolio-Promotions.

### 4.4 Notfall-Entscheidungen

**Bei kritischen Incidents:**

1. **Sofort-Stopp**: Operator/Owner darf System jederzeit pausieren
2. **Post-Mortem**: Innerhalb von 24h Incident-Analyse starten
3. **Dokumentation**: Alle Maßnahmen protokollieren
4. **Review**: Lessons Learned dokumentieren

---

## 5. Verhältnis zu technischen Phasen

### Bezug zu Phase 23 (Blueprint)

Phase 23 definiert die **technische Architektur** für Testnet/Live:
- Schichtenmodell (Strategies → Risk → SafetyGuard → Execution)
- 5-Stufen-Plan (Research → Shadow → Testnet → Shadow-Live → Live)
- Technische Safety-Schalter

→ Siehe: `docs/PHASE_23_LIVE_TESTNET_BLUEPRINT.md`

### Bezug zu Phase 24 (Shadow-Execution)

Phase 24 implementiert den **Shadow-/Dry-Run-Modus**:
- `ShadowOrderExecutor` für simulierte Orders
- Keine echten API-Calls
- Integration mit Experiments-Registry

→ Siehe: `docs/PHASE_24_SHADOW_EXECUTION.md`

### Phase 25 (dieses Dokument)

Phase 25 ergänzt den **organisatorischen Layer**:
- Rollen & Verantwortlichkeiten
- Entscheidungsprozesse
- Policies, Runbooks, Checklisten

---

## 6. Weiterführende Dokumente

| Dokument | Beschreibung |
|----------|--------------|
| `SAFETY_POLICY_TESTNET_AND_LIVE.md` | Konkrete Safety-Policies für Testnet/Live |
| `RUNBOOKS_AND_INCIDENT_HANDLING.md` | Runbooks und Incident-Prozesse |
| `LIVE_READINESS_CHECKLISTS.md` | Checklisten für Stufen-Übergänge |
| `PHASE_23_LIVE_TESTNET_BLUEPRINT.md` | Technischer Blueprint |
| `PHASE_24_SHADOW_EXECUTION.md` | Shadow-Execution-Dokumentation |

---

## 7. Changelog

- **Phase 25** (2025-12): Initial erstellt
  - Grundprinzipien definiert
  - Rollen & Verantwortlichkeiten beschrieben
  - Entscheidungsprozesse dokumentiert
  - Keine Code-Änderungen
