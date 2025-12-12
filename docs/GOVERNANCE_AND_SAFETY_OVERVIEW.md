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

### 4.4 Incident-Drills

Neben formaler Governance (Freigaben, Checklisten) werden regelmäßig **Incident-Drills** nach [`INCIDENT_SIMULATION_AND_DRILLS.md`](INCIDENT_SIMULATION_AND_DRILLS.md) durchgeführt (Phase 56), um Runbooks, Tooling und Alerts praktisch zu validieren.

**Zweck:**
- Runbooks in kontrollierter Umgebung üben
- Alert-System & Monitoring-Tools testen
- Incident-Handling-Prozesse validieren
- Kontinuierliche Verbesserung der Incident-Response

**Empfohlene Frequenz:**
- **Monatlich**: Mindestens 1 Drill (abwechselnd Szenarien)
- **Quartalsweise**: Kompletter Zyklus durch alle Szenarien

**Dokumentation:**
- Alle Drills werden in [`INCIDENT_DRILL_LOG.md`](INCIDENT_DRILL_LOG.md) protokolliert
- Erkenntnisse werden in Runbooks & Governance-Doku eingearbeitet

### 4.5 Live Status Reports

Regelmäßige Status-Reports (z.B. daily/weekly) sind Teil der operativen Governance und Monitoring-Strategie. Reports werden mit [`generate_live_status_report.py`](../scripts/generate_live_status_report.py) generiert und dokumentieren den aktuellen Systemzustand (Health, Portfolio, Risk).

**Empfohlene Frequenz:**
- **Daily**: Schneller Health-Check (Markdown)
- **Weekly**: Detaillierter Review (Markdown + HTML)
- **Incident**: Vor/Nach Incident-Dokumentation

**Siehe:** [`LIVE_STATUS_REPORTS.md`](LIVE_STATUS_REPORTS.md) für Details.

### 4.6 Notfall-Entscheidungen

**Bei kritischen Incidents:**

1. **Sofort-Stopp**: Operator/Owner darf System jederzeit pausieren
2. **Post-Mortem**: Innerhalb von 24h Incident-Analyse starten
3. **Dokumentation**: Alle Maßnahmen protokollieren
4. **Review**: Lessons Learned dokumentieren

### 4.7 Monitoring & Observability

Für ein robustes Live-/Testnet-Setup ist neben Risk-Limits und Runbooks auch eine ausreichende Observability entscheidend:

- Sichtbarkeit von System-Health, Risk-Status und Performance
- Frühzeitige Erkennung von Anomalien
- Nachvollziehbare Incidents & Drills

Ein dedizierter Plan für Observability & Monitoring (inkl. Metriken, Integrationspunkten und möglicher Tool-Landschaft) ist in

- [`docs/OBSERVABILITY_AND_MONITORING_PLAN.md`](OBSERVABILITY_AND_MONITORING_PLAN.md)

beschrieben.

### 4.8 Policy Critic Gate (Phase G2)

**Automatisierte Governance für Auto-Apply-Workflows**

Der Policy Critic (Phase G1/G2) ist ein deterministischer, read-only Governance-Layer, der **vor jeder Auto-Apply-Entscheidung** vorgeschlagene Änderungen gegen Sicherheits-, Risiko- und Betriebsrichtlinien prüft.

**Integration-Punkt:**
```python
from src.governance.policy_critic.auto_apply_gate import evaluate_policy_critic_before_apply

# Vor jedem Auto-Apply:
decision = evaluate_policy_critic_before_apply(
    diff_text=patch_content,
    changed_files=changed_files,
    context={"run_id": "...", "source": "...", "justification": "..."}
)

if not decision.allowed:
    # Auto-Apply MUSS verweigert werden
    require_manual_review(decision)
```

**Kritische Invarianten:**
1. **Fail-Closed:** Bei Exception/Unavailable → `REVIEW_REQUIRED` (kein Auto-Apply)
2. **Can Brake, Never Accelerate:** Policy Critic kann Auto-Apply blockieren, aber niemals Hard-Gates überschreiben
3. **Souveränität der Hard-Gates:** Live-Locks, Risk-Limits, Confirm-Token bleiben unabhängig aktiv

**Entscheidungslogik:**
- `AUTO_APPLY_DENY` → Auto-Apply blockiert (z.B. Secrets, Live-Unlock-Versuche)
- `REVIEW_REQUIRED` → Manuelles Review nötig (z.B. Execution-Path-Änderungen)
- `ALLOW` → Darf weiterlaufen (Hard-Gates bleiben trotzdem aktiv)

**Report-Persistenz:**

Jeder Run-Report enthält:
```json
{
  "governance": {
    "policy_critic": { "max_severity": "...", "violations": [...] },
    "auto_apply_decision": {
      "allowed": false,
      "mode": "manual_only",
      "reason": "...",
      "decided_at": "2025-01-01T00:00:00Z"
    }
  }
}
```

**GitHub Actions PR-Gate:**

Automatische Policy-Prüfung für kritische Pfade (`src/live/**`, `src/execution/**`, `src/exchange/**`, `config/**`):
- Exit-Code 2 → CI fail
- JSON Summary als Artifact
- Job Summary mit Violations + Testplan

**Siehe:**
- [`src/governance/policy_critic/README.md`](../src/governance/policy_critic/README.md) - Vollständige Dokumentation
- [`docs/governance/LLM_POLICY_CRITIC_CHARTER.md`](governance/LLM_POLICY_CRITIC_CHARTER.md) - Governance-Charter
- [`src/governance/policy_critic/auto_apply_gate.py`](../src/governance/policy_critic/auto_apply_gate.py) - Integration-API

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
| [`governance/LLM_POLICY_CRITIC_CHARTER.md`](governance/LLM_POLICY_CRITIC_CHARTER.md) | LLM Policy Critic: Read-only Governance-Layer für automatisierte Safety-Reviews |

---

## 7. Changelog

- **Phase 25** (2025-12): Initial erstellt
  - Grundprinzipien definiert
  - Rollen & Verantwortlichkeiten beschrieben
  - Entscheidungsprozesse dokumentiert
  - Keine Code-Änderungen
