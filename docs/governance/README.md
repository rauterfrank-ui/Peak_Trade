# Governance & AI Autonomy

Governance-Dokumentation für AI-Autonomie, Policy Enforcement und Compliance im Peak_Trade Repository.

---

## Canonical Vocabulary / Authority / Provenance v0

- Canonical Spec (verbindlich): [docs/ops/specs/CANONICAL_VOCAB_AUTHORITY_PROVENANCE_V0.md](../ops/specs/CANONICAL_VOCAB_AUTHORITY_PROVENANCE_V0.md)
- **Primärnorm** für Begriffsdisziplin, Authority-/Veto-Precedence und Claim-/Provenance-Disziplin (Veto-Kette und Grenzen in der Spec).
- Claim-Disziplin: Claims in den Klassen `repo-evidenced`, `documented`, `unverified`, `not-claimed` formulieren (Abschnitt 6); `unverified` und `not-claimed` nicht als verifizierte Fakten ausgeben; `operator-stated` explizit markieren, wo zutreffend; keine impliziten E2E-/Runtime-Behauptungen.

---

## 📋 Core Governance

- **[Map of Truth (Navigations-Einstieg)](PEAK_TRADE_MAP_OF_TRUTH.md)** — Zentraler Einstieg; **keine** Semantik; verweist auf kanonische Owner; SSOT = Vollautonomie-Runbook v4.4.12
- **[Feature State Map v1](feature_state_map_v1.md)** — Kanonische Feature-Klassifikation A–D und NON-OPERATIONAL-Regel (read-only map)
- **[Drift Cleanup Plan v1](drift_cleanup_plan_v1.md)** — Safe documentation fixes und flagged structural/authority items
- **[Runbook Execution Governance v1](PEAK_TRADE_RUNBOOK_EXECUTION_GOVERNANCE_V1.md)** — Verbindliche strategische SSOT-Steuerung, Package-Sequenzierung und Ranking-Ausnahmeregel (non-authorizing)
- **[Autonomy Runbook Progress Registry v1](PEAK_TRADE_AUTONOMY_RUNBOOK_PROGRESS_V1.md)** — Kanonische Progress-Registry: Runbook-Soll ↔ Repo-Ist (non-authorizing)
- **[Vollautonomie-Runbook v4.4.12 (aktuelle SSOT)](Peak_Trade_Kanonisches_Vollautonomie_Runbook_v4.4.12.md)** — Kanonische Governance- und Implementierungs-SSOT (via Map of Truth; non-authorizing)
- **[Vollautonomie-Runbook v4.4.10 (Vollfassung)](Peak_Trade_Kanonisches_Vollautonomie_Runbook_v4.4.10_IMPLEMENTATION_CONTRACT.md)** — Historische Adoption-/Crosslink-Oberfläche (Pfad für bestehende Contracts; normative Semantik: Map of Truth → v4.4.12; Cursor muss die kanonische Vollfassung zuerst lesen)
- **[Implementation Contract (Kurzfassung)](PEAK_TRADE_IMPLEMENTATION_CONTRACT.md)** — Navigations- und Ausführungsleitfaden ohne eigene SSOT-Authority (`THIS_DOCUMENT_IS_NOT_A_SECOND_SSOT=true`)
- **[Canonical Chain Wiring Repair Master Runbook v2.2](Peak_Trade_Canonical_Chain_Wiring_Repair_Master_Runbook_v2.2.md)** — Kanonischer Governance-/Implementierungsvertrag für Chain-Wiring-Repair (Slice 1 complete; Slice 2 blocked; non-authorizing; `MISSION_COMPLETE=false`)
- **[Strategy Signal Architecture Ratification Closeout v1](STRATEGY_SIGNAL_CANONICAL_ARCHITECTURE_RATIFICATION_CLOSEOUT_V1.md)** — Negative Architecture Ratification (Selection D); `SLICE_2_IMPLEMENTATION_BLOCKED=true`; `NEXT_AUTOMATIC_IMPLEMENTATION_SCOPE=NONE`
- **[Strategy Signal Canonical Consumer Architecture Authorization v1](STRATEGY_SIGNAL_CANONICAL_CONSUMER_ARCHITECTURE_AUTHORIZATION_V1.md)** — Separate architecture authorization under GO; Decision **C** (`NO_SAFE_ARCHITECTURE_AUTHORIZABLE`); `SLICE_2_IMPLEMENTATION_AUTHORIZED=false`
- **[Economic/Diagnostic Optimization Boundary v0](ECONOMIC_DIAGNOSTIC_OPTIMIZATION_BOUNDARY_AND_CANONICAL_TRADING_LOGIC_IMMUTABILITY_CONTRACT_V0.md)** — Verbindliche zulässige Optimierungsflächen vs. unveränderliche kanonische Trading-/Safety-/Authority-Semantik (additive Governance-Erweiterung; non-authorizing)
- **[Promotion Owner and Gate Inventory SSOT v1](PROMOTION_OWNER_AND_GATE_INVENTORY_SSOT_V1.md)** — Repo-weite Inventur: kanonischer Gate-Owner = `promotion_economic_gate_v1`; Adapter/Consumer/Reporting/Legacy klassifiziert; non-authorizing (`PRODUCTIVE_PROMOTION_DECISION_OWNER_COUNT=1`)
- **[Runbook v4.4.1 Multi-Future Target Model Clarification](Peak_Trade_Kanonisches_Vollautonomie_Runbook_v4.4.1_multi_future_target_model_clarification.md)** — Governance-Clarification: Phase-1 Single-Future bleibt; Multi-Future nur Zielmodell nach separaten Gates (non-authorizing; historische Clarification — maßgeblich: [Map of Truth](PEAK_TRADE_MAP_OF_TRUTH.md) → v4.4.12)
- **[AI Autonomy Go/No-Go Overview](AI_AUTONOMY_GO_NO_GO_OVERVIEW.md)** — Governance-first guardrails für Cursor Agent (keine Live-Autonomie)
- **[AI Autonomy Evidence Pack Template](templates/AI_AUTONOMY_EVIDENCE_PACK_TEMPLATE.md)** — Strukturiertes Template für Autonomie-Evidenz
- **[Untracked Local Reports Policy](UNTRACKED_LOCAL_REPORTS_POLICY.md)** — Umgang mit lokalen unversionierten Analyse-/Audit-Reports

---

## 🛡️ Policy Critic

- **[Policy Critic Charter](LLM_POLICY_CRITIC_CHARTER.md)** — Charter und Mandate
- **[Policy Critic Status](POLICY_CRITIC_STATUS.md)** — Aktueller Status
- **[Policy Critic Roadmap](POLICY_CRITIC_ROADMAP.md)** — Entwicklungs-Roadmap
- **[Policy Critic Telemetry (G4)](POLICY_CRITIC_TELEMETRY_G4.md)** — Telemetrie-System
- **[Policy Critic G4 Telemetry Workflow](POLICY_CRITIC_G4_TELEMETRY_WORKFLOW.md)** — Workflow-Dokumentation
- **[Policy Critic Real Cycles (G3.5)](POLICY_CRITIC_REAL_CYCLES_G3_5.md)** — Real-World-Zyklen
- **[Policy Pack Tuning Log](POLICY_PACK_TUNING_LOG.md)** — Tuning-Historie

---

## 📦 Evidence & Gates

- **[WP0C Gate Evidence](evidence/WP0C_GATE_EVIDENCE.md)** — Work Package 0C Gate-Evidenz

---

## 🔗 Related Documentation

- **Feature Drift & State:** [audit/feature_drift_reconciliation_report_v1.md](../audit/feature_drift_reconciliation_report_v1.md), [audit/drift_safe_docs_patch_v1.md](../audit/drift_safe_docs_patch_v1.md)
- **Audit Runbooks**: `docs/audit/`
- **Ops Runbooks**: `docs/ops/`
- **Risk Governance**: `docs/risk/`
