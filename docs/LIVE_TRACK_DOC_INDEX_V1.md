# Live-Track Doc Index v1.1

Dieser Index ist die **zentrale Anlaufstelle** für alle Dokumente rund um den Live-Track-Stack von Peak_Trade – von der Strategy-to-Execution-Bridge über Live-Session-Registry und Web-Dashboard bis hin zu Playbooks, Safety-Policies und Demo-Scripts.

**Zielgruppe:** Operatoren, Quant-Research, Stakeholder für Demo-Setups  
**Fokus:** Shadow-/Testnet-Demo-Stack (kein echter Live-Handel, Safety-Gates bleiben aktiv)

---

## Inhaltsübersicht

| Abschnitt | Inhalt |
|-----------|--------|
| **1. Überblick & Releases** | Status-Overview, Roadmap, Release-Notes v1.1 |
| **2. Kern-Stack** | Strategy-to-Execution Bridge (Phase 80), Live-Session-Registry (Phase 81) |
| **3. Operator Workflow & Dashboard** | Phase-83-Workflow, Runbooks, Web-Dashboard v1.1 (Phase 82/85) |
| **4. Demo- & Onboarding** | Phase-84-Walkthrough, 2-Min-Demo-Script, 3-Min-How-To |
| **5. Playbooks & Checklisten** | Deployment-Playbook, Readiness-Checklisten, Research-to-Live |
| **6. Safety & Risk** | Safety-Policies, Gating, Live-Risk-Limits |
| **7. Ergänzende Phasen (71–75)** | Pre-Live-Design, Operator-Console, Dry-Run-Drills, Audit-Export |
| **8. Monitoring & Alerts (48–51)** | Portfolio-Monitoring, Alerts, Webhooks, Ops-CLI |
| **9. Quick-Links für Demos** | Schnellzugriff-Tabelle für häufigste Demo-Dokumente |

---

## 1. Überblick & Releases

### 1.1 Status & Roadmap

| Dokument | Beschreibung |
|----------|--------------|
| [PEAK_TRADE_STATUS_OVERVIEW.md](./PEAK_TRADE_STATUS_OVERVIEW.md) | Gesamtstatus des Projekts mit Release-Eintrag v1.1 – Live-Track Web-Dashboard & Demo-Pack. |
| [PEAK_TRADE_MINI_ROADMAP_V1_RESEARCH_LIVE_BETA.md](./PEAK_TRADE_MINI_ROADMAP_V1_RESEARCH_LIVE_BETA.md) | Kompakte Roadmap mit allen Phasen rund um Live-/Shadow-/Testnet-Betrieb und Web-Dashboard. |
| [PEAK_TRADE_V1_OVERVIEW_FULL.md](./PEAK_TRADE_V1_OVERVIEW_FULL.md) | Vollständige v1-Übersicht inkl. Abschnitte 4.10/4.11 zum Web-Dashboard v1.1. |

### 1.2 Release-Notes

| Dokument | Beschreibung |
|----------|--------------|
| [RELEASE_NOTES_V1_1_LIVE_TRACK_DASHBOARD.md](./RELEASE_NOTES_V1_1_LIVE_TRACK_DASHBOARD.md) | **Release v1.1** – Live-Track Web-Dashboard, Phase-84-Walkthrough, Demo-Script, Playbook-How-To. |
| [PEAK_TRADE_V1_RELEASE_NOTES.md](./PEAK_TRADE_V1_RELEASE_NOTES.md) | Allgemeine v1-Release-Notes mit Changelog-Historie. |

---

## 2. Kern-Stack (Phasen 80–81)

### 2.1 Strategy-to-Execution Bridge (Phase 80)

| Dokument | Beschreibung |
|----------|--------------|
| [PHASE_80_STRATEGY_TO_EXECUTION_BRIDGE.md](./PHASE_80_STRATEGY_TO_EXECUTION_BRIDGE.md) | ExecutionPipeline-Integration, SafetyGuard/LiveRiskLimits Hooks, CLI-Recipes für den Live-/Shadow-/Testnet-Flow. |
| [PHASE_80_TIERED_PORTFOLIO_PRESETS.md](./PHASE_80_TIERED_PORTFOLIO_PRESETS.md) | Tiered Portfolio Presets für verschiedene Risiko-/Kapital-Stufen. |

### 2.2 Live-Session-Registry (Phase 81)

| Dokument | Beschreibung |
|----------|--------------|
| [PHASE_81_LIVE_SESSION_REGISTRY.md](./PHASE_81_LIVE_SESSION_REGISTRY.md) | Live-Session-Registry, Report-CLI, Ablage und Inspection von Session-Metadaten. |

---

## 3. Operator Workflow & Dashboard (Phasen 82–85)

### 3.1 Web-Dashboard (Phase 82)

| Dokument | Beschreibung |
|----------|--------------|
| [PHASE_82_LIVE_TRACK_DASHBOARD.md](./PHASE_82_LIVE_TRACK_DASHBOARD.md) | Live-Track Web-Dashboard v1.1 – Operator View mit Session-Tabelle, Status-Kacheln und Safety-Header. |
| [PHASE_82_RESEARCH_QA_AND_SCENARIOS.md](./PHASE_82_RESEARCH_QA_AND_SCENARIOS.md) | Research-QA und Szenarien für Dashboard-Validierung. |

### 3.2 Operator Workflow & Gating (Phase 83)

| Dokument | Beschreibung |
|----------|--------------|
| [PHASE_83_LIVE_TRACK_OPERATOR_WORKFLOW.md](./PHASE_83_LIVE_TRACK_OPERATOR_WORKFLOW.md) | Operator-Workflow: Shadow-/Testnet-Sessions starten, Readiness prüfen, Dashboard-Monitoring. |
| [PHASE_83_LIVE_GATING_AND_RISK_POLICIES.md](./PHASE_83_LIVE_GATING_AND_RISK_POLICIES.md) | Live-Gating-Mechanismen und Risk-Policies für den Übergang zu echtem Live-Handel. |

### 3.3 Operator Dashboard & Session Explorer (Phase 84/85)

| Dokument | Beschreibung |
|----------|--------------|
| [PHASE_84_OPERATOR_DASHBOARD.md](./PHASE_84_OPERATOR_DASHBOARD.md) | Operator-Dashboard-Spezifikation und UI-Komponenten. |
| [PHASE_85_LIVE_TRACK_SESSION_EXPLORER.md](./PHASE_85_LIVE_TRACK_SESSION_EXPLORER.md) | Session Explorer im Dashboard v1.1 – Detailansicht einzelner Sessions. |
| [PHASE_85_LIVE_BETA_DRILL.md](./PHASE_85_LIVE_BETA_DRILL.md) | Live-Beta-Drill-Szenarien für Operatoren. |

### 3.4 Runbooks

| Dokument | Beschreibung |
|----------|--------------|
| [LIVE_OPERATIONAL_RUNBOOKS.md](./LIVE_OPERATIONAL_RUNBOOKS.md) | Operative Runbooks für Live-/Shadow-/Testnet-Flows und Post-Session-Checks. |
| [RUNBOOKS_AND_INCIDENT_HANDLING.md](./RUNBOOKS_AND_INCIDENT_HANDLING.md) | Incident-Response, Troubleshooting und Eskalationspfade. |

---

## 4. Demo- & Onboarding

### 4.1 Demo-Walkthrough (Phase 84)

| Dokument | Beschreibung |
|----------|--------------|
| [PHASE_84_LIVE_TRACK_DEMO_WALKTHROUGH.md](./PHASE_84_LIVE_TRACK_DEMO_WALKTHROUGH.md) | End-to-End-Demo-Flow: System-Check → Session starten → Registry/Report → Dashboard-Verifikation. Inkl. Storyboard für Stakeholder-Demos. |

### 4.2 Demo-Scripts & How-Tos

| Dokument | Beschreibung |
|----------|--------------|
| [DEMO_SCRIPT_DASHBOARD_V11.md](./DEMO_SCRIPT_DASHBOARD_V11.md) | **2-Minuten-Demo-Script** inkl. Cheat-Sheet für schnelle Dashboard-Demos. |
| [HOW_TO_LIVE_TRACK_V11_IN_3_MIN.md](./HOW_TO_LIVE_TRACK_V11_IN_3_MIN.md) | **3-Minuten-Schnellstart** – CLI → Readiness → Dashboard → Demo in kompakter Form. |

---

## 5. Playbooks & Checklisten

### 5.1 Deployment & Operations

| Dokument | Beschreibung |
|----------|--------------|
| [LIVE_DEPLOYMENT_PLAYBOOK.md](./LIVE_DEPLOYMENT_PLAYBOOK.md) | Stufenplan Research → Shadow → Testnet → Live. Enthält Abschnitt **12.5**: Kurz-How-To für Dashboard-Demo. |
| [PLAYBOOK_RESEARCH_TO_LIVE_PORTFOLIOS.md](./PLAYBOOK_RESEARCH_TO_LIVE_PORTFOLIOS.md) | Playbook für den Weg von Research-Ergebnissen zu Live-Portfolios. |

### 5.2 Readiness & Checklisten

| Dokument | Beschreibung |
|----------|--------------|
| [LIVE_READINESS_CHECKLISTS.md](./LIVE_READINESS_CHECKLISTS.md) | Detaillierte Checklisten für Stufen-Übergänge (Shadow, Testnet, Live). |
| [LIVE_WORKFLOWS.md](./LIVE_WORKFLOWS.md) | Workflow-Definitionen für Live-Operationen. |

### 5.3 Status & Tracking

| Dokument | Beschreibung |
|----------|--------------|
| [LIVE_STATUS_REPORTS.md](./LIVE_STATUS_REPORTS.md) | Templates und Beispiele für Live-Status-Reports. |
| [LIVE_TESTNET_TRACK_STATUS.md](./LIVE_TESTNET_TRACK_STATUS.md) | Aktueller Tracking-Status für Testnet-Operationen. |
| [LIVE_TESTNET_PREPARATION.md](./LIVE_TESTNET_PREPARATION.md) | Vorbereitungs-Checkliste für Testnet-Betrieb. |

---

## 6. Safety & Risk

### 6.1 Policies & Governance

| Dokument | Beschreibung |
|----------|--------------|
| [SAFETY_POLICY_TESTNET_AND_LIVE.md](./SAFETY_POLICY_TESTNET_AND_LIVE.md) | Safety-Policies für Testnet- und Live-Betrieb, inkl. Gating-Regeln. |
| [GOVERNANCE_AND_SAFETY_OVERVIEW.md](./GOVERNANCE_AND_SAFETY_OVERVIEW.md) | Überblick über Governance-Struktur und Safety-Mechanismen. |

### 6.2 Risk-Limits & Dev-Guides

| Dokument | Beschreibung |
|----------|--------------|
| [LIVE_RISK_LIMITS.md](./LIVE_RISK_LIMITS.md) | Dokumentation der Live-Risk-Limits und deren Konfiguration. |
| [DEV_GUIDE_ADD_LIVE_RISK_LIMIT.md](./DEV_GUIDE_ADD_LIVE_RISK_LIMIT.md) | Entwickler-Anleitung zum Hinzufügen neuer Live-Risk-Limits. |

---

## 7. Ergänzende Phasen (71–75)

Diese Phasen bilden die Grundlage für den Live-Track-Stack und decken Pre-Live-Design, Operator-Tools und Audit-Funktionen ab.

| Phase | Dokument | Beschreibung |
|-------|----------|--------------|
| 71 | [PHASE_71_LIVE_EXECUTION_DESIGN_AND_GATING.md](./PHASE_71_LIVE_EXECUTION_DESIGN_AND_GATING.md) | Live-Execution-Design & Gating-Architektur. |
| 72 | [PHASE_72_LIVE_OPERATOR_CONSOLE.md](./PHASE_72_LIVE_OPERATOR_CONSOLE.md) | CLI-basierte Operator-Console für Live-Monitoring. |
| 73 | [PHASE_73_LIVE_DRY_RUN_DRILLS.md](./PHASE_73_LIVE_DRY_RUN_DRILLS.md) | Dry-Run-Drills zum Testen von Live-Abläufen ohne echte Orders. |
| 74 | [PHASE_74_LIVE_AUDIT_EXPORT.md](./PHASE_74_LIVE_AUDIT_EXPORT.md) | Audit-Export für Compliance und Nachvollziehbarkeit. |
| 75 | [PHASE_75_STRATEGY_LIBRARY_V1_1.md](./PHASE_75_STRATEGY_LIBRARY_V1_1.md) | Strategy-Library v1.1 mit erweiterten Strategien. |

---

## 8. Monitoring & Alerts (Phasen 48–51)

Diese Phasen decken Portfolio-Monitoring, Alert-Systeme und Operator-CLI ab.

| Phase | Dokument | Beschreibung |
|-------|----------|--------------|
| 48 | [PHASE_48_LIVE_PORTFOLIO_MONITORING_AND_RISK_BRIDGE.md](./PHASE_48_LIVE_PORTFOLIO_MONITORING_AND_RISK_BRIDGE.md) | Live-Portfolio-Monitoring und Risk-Bridge-Integration. |
| 49 | [PHASE_49_LIVE_ALERTS_AND_NOTIFICATIONS.md](./PHASE_49_LIVE_ALERTS_AND_NOTIFICATIONS.md) | Alert-System und Notification-Konfiguration. |
| 50 | [PHASE_50_LIVE_ALERT_WEBHOOKS_AND_SLACK.md](./PHASE_50_LIVE_ALERT_WEBHOOKS_AND_SLACK.md) | Webhooks und Slack-Integration für Live-Alerts. |
| 51 | [PHASE_51_LIVE_OPS_CLI.md](./PHASE_51_LIVE_OPS_CLI.md) | Operator-CLI für Live-Operations und Monitoring. |

---

## 9. Quick-Links für Demos

Schnellzugriff auf die wichtigsten Dokumente für Demos und Onboarding:

| Use-Case | Zeitbedarf | Dokument |
|----------|------------|----------|
| **Schnellster Einstieg** | 3 Min | [HOW_TO_LIVE_TRACK_V11_IN_3_MIN.md](./HOW_TO_LIVE_TRACK_V11_IN_3_MIN.md) |
| **Dashboard-Demo** | 2 Min | [DEMO_SCRIPT_DASHBOARD_V11.md](./DEMO_SCRIPT_DASHBOARD_V11.md) |
| **Vollständiger Walkthrough** | 10–15 Min | [PHASE_84_LIVE_TRACK_DEMO_WALKTHROUGH.md](./PHASE_84_LIVE_TRACK_DEMO_WALKTHROUGH.md) |
| **Playbook-How-To** | 5 Min | [LIVE_DEPLOYMENT_PLAYBOOK.md](./LIVE_DEPLOYMENT_PLAYBOOK.md) → Abschnitt 12.5 |
| **Safety-Review** | 10 Min | [SAFETY_POLICY_TESTNET_AND_LIVE.md](./SAFETY_POLICY_TESTNET_AND_LIVE.md) |
| **Operator-Workflow** | 10 Min | [PHASE_83_LIVE_TRACK_OPERATOR_WORKFLOW.md](./PHASE_83_LIVE_TRACK_OPERATOR_WORKFLOW.md) |
| **Release-Notes v1.1** | 2 Min | [RELEASE_NOTES_V1_1_LIVE_TRACK_DASHBOARD.md](./RELEASE_NOTES_V1_1_LIVE_TRACK_DASHBOARD.md) |

---

## Weitere Ressourcen

| Dokument | Beschreibung |
|----------|--------------|
| [PHASE_86_RESEARCH_V1_FREEZE.md](./PHASE_86_RESEARCH_V1_FREEZE.md) | Research-Freeze für v1-Release. |
| [PHASE_33_LIVE_MONITORING_AND_CLI_DASHBOARDS.md](./PHASE_33_LIVE_MONITORING_AND_CLI_DASHBOARDS.md) | Früheres CLI-Dashboard-Design (Phase 33). |
| [PHASE_23_LIVE_TESTNET_BLUEPRINT.md](./PHASE_23_LIVE_TESTNET_BLUEPRINT.md) | Original-Blueprint für Testnet-Architektur. |

---

## Changelog

| Version | Datum | Änderung |
|---------|-------|----------|
| v1.1 | 2025-12-08 | Vollständige Überarbeitung mit erweiterter Struktur, Tabellen und Quick-Links |
| v1.0 | 2025-12-08 | Initiale Version des Live-Track Doc-Index |
