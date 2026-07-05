# Governance & AI Autonomy

Governance-Dokumentation für AI-Autonomie, Policy Enforcement und Compliance im Peak_Trade Repository.

---

## Canonical Vocabulary / Authority / Provenance v0

- Canonical Spec (verbindlich): [docs/ops/specs/CANONICAL_VOCAB_AUTHORITY_PROVENANCE_V0.md](../ops/specs/CANONICAL_VOCAB_AUTHORITY_PROVENANCE_V0.md)
- **Primärnorm** für Begriffsdisziplin, Authority-/Veto-Precedence und Claim-/Provenance-Disziplin (Veto-Kette und Grenzen in der Spec).
- Claim-Disziplin: Claims in den Klassen `repo-evidenced`, `documented`, `unverified`, `not-claimed` formulieren (Abschnitt 6); `unverified` und `not-claimed` nicht als verifizierte Fakten ausgeben; `operator-stated` explizit markieren, wo zutreffend; keine impliziten E2E-/Runtime-Behauptungen.

---

## 📋 Core Governance

- **[Feature State Map v1](feature_state_map_v1.md)** — Kanonische Feature-Klassifikation A–D und NON-OPERATIONAL-Regel (read-only map)
- **[Drift Cleanup Plan v1](drift_cleanup_plan_v1.md)** — Safe documentation fixes und flagged structural/authority items
- **[Runbook Execution Governance v1](PEAK_TRADE_RUNBOOK_EXECUTION_GOVERNANCE_V1.md)** — Verbindliche strategische SSOT-Steuerung, Package-Sequenzierung und Ranking-Ausnahmeregel (non-authorizing)
- **[Autonomy Runbook Progress Registry v1](PEAK_TRADE_AUTONOMY_RUNBOOK_PROGRESS_V1.md)** — Kanonische Progress-Registry: Runbook-Soll ↔ Repo-Ist (non-authorizing)
- **[Runbook v4.4.1 Multi-Future Target Model Clarification](Peak_Trade_Kanonisches_Vollautonomie_Runbook_v4.4.1_multi_future_target_model_clarification.md)** — Governance-Clarification: Phase-1 Single-Future bleibt; Multi-Future nur Zielmodell nach separaten Gates (non-authorizing)
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
