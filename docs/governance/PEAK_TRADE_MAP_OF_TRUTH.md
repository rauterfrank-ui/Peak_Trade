# Peak Trade — Map of Truth

**Rolle:** Zentraler Navigations-Einstieg (Discovery-Only).  
**Authority:** Keine. Dieses Dokument definiert keine Semantik.

```text
THIS_DOCUMENT_DEFINES_NO_SEMANTICS=true
THIS_DOCUMENT_POINTS_ONLY_TO_CANONICAL_OWNERS=true
THIS_DOCUMENT_IS_NOT_A_SECOND_RUNBOOK=true
THIS_DOCUMENT_IS_NOT_A_SECOND_SSOT=true
PARALLEL_SSOT_CREATED=false
LIVE_AUTHORIZED=false
ORDERS_ALLOWED=false
SCHEDULER_RUNTIME_ALLOWED=false
```

**Dieses Dokument definiert keine Semantik. Es verweist ausschließlich auf die kanonischen Owner.**

---

## 1. Systemzweck

Peak Trade ist ein futures-only, vollautonomes Handelssystem mit:

- deterministischer, auditierbarer Handelslogik,
- realistischer Profitabilitätsvalidierung,
- unabhängiger Safety Authority,
- gefenceter Single-Writer-Runtime,
- vollständiger Reconciliation und sicherer Restart-/Recovery-Semantik,
- durchgängiger Research → Validation → Promotion → Runtime → Feedback-Kette,
- Phase-1 Single-Future-Safety vor späterer Multi-Future-Portfolio-Runtime (nur nach separaten Gates).

Keine Anlageberatung. Keine Live-/Order-/Scheduler-Freigabe allein durch Lektüre.

---

## 2. Kanonische SSOT (Vollautonomie-Runbook v4.4.12)

Ab sofort und bis zur vollständigen Systemautonomie ist die **einzige** Architektur-, Governance- und Implementierungs-SSOT:

| Rolle | Pfad |
|-------|------|
| **Kanonische SSOT (v4.4.12)** | [`Peak_Trade_Kanonisches_Vollautonomie_Runbook_v4.4.12.md`](Peak_Trade_Kanonisches_Vollautonomie_Runbook_v4.4.12.md) |

```text
CANONICAL_VOLLAUTONOMIE_RUNBOOK_VERSION=v4.4.12
CANONICAL_VOLLAUTONOMIE_RUNBOOK_PATH=docs/governance/Peak_Trade_Kanonisches_Vollautonomie_Runbook_v4.4.12.md
CANONICAL_RUNBOOK_CONTENT_VERSION=4.4.12-full-canonical-system-parity-before-system-economic-evidence
CURSOR_MUST_READ_CANONICAL_RUNBOOK_FIRST=true
```

Ältere Runbook-Pfade (v4.4 / v4.4.1 / v4.4.10 Dateiname / v2.6) sind **historische Adoption-/Crosslink-Oberflächen**. Normative Semantik kommt ausschließlich aus v4.4.12 über diese Map.

Kurz-Navigationsvertrag (keine zweite SSOT): [`PEAK_TRADE_IMPLEMENTATION_CONTRACT.md`](PEAK_TRADE_IMPLEMENTATION_CONTRACT.md).

Ops-Drift-Registry (kein Navigations-Ersatz): [`docs/ops/registry/DOCS_TRUTH_MAP.md`](../ops/registry/DOCS_TRUTH_MAP.md).

---

## 3. Wichtigste Architektur-Domänen

Aus der kanonischen SSOT (Authority-Grenzen dort, nicht hier):

| Domäne | Kurzbeschreibung |
|--------|------------------|
| `TRADING_DECISION_CORE` | Market Context → Scope → Assessment → Survival/Suitability → Double Play → Decision |
| `CAPITAL_RISK_AND_SIZING_CORE` | Envelope → Pre-/Post-Sizing Risk → Position Sizing → Order Intent |
| `ECONOMIC_VALIDATION_CORE` | Backtest/Kosten/OLS-Diagnostik → Walk-Forward/MC/Stress → Viability Evidence |
| `SAFETY_EXECUTION_RUNTIME_CORE` | Safety Kernel → Eligibility → Lease → Submission → Reconciliation → Recovery |
| `LEARNING_PROMOTION_CORE` | Admissible Evidence → Candidate → Validation → Promotion → Deploy Inactive |

Weitere Architektur-Landkarten (deep dives, keine parallele Trading-SSOT):

- [`docs/architecture/PEAK_TRADE_CANONICAL_UNIFIED_TRADING_SYSTEM_RUNBOOK_V2_6.md`](../architecture/PEAK_TRADE_CANONICAL_UNIFIED_TRADING_SYSTEM_RUNBOOK_V2_6.md) — historisches strategisches Zielbild v2.6
- [`docs/ARCHITECTURE_OVERVIEW.md`](../ARCHITECTURE_OVERVIEW.md)
- [`docs/PEAK_TRADE_OVERVIEW.md`](../PEAK_TRADE_OVERVIEW.md)

---

## 4. Wichtigste Governance-Dokumente

| Dokument | Rolle |
|----------|-------|
| [`README.md`](README.md) | Governance-Index |
| [`PEAK_TRADE_RUNBOOK_EXECUTION_GOVERNANCE_V1.md`](PEAK_TRADE_RUNBOOK_EXECUTION_GOVERNANCE_V1.md) | Ausführungssteuerung / Package-Sequenz |
| [`PEAK_TRADE_AUTONOMY_RUNBOOK_PROGRESS_V1.md`](PEAK_TRADE_AUTONOMY_RUNBOOK_PROGRESS_V1.md) | Progress-Registry (Soll ↔ Ist) |
| [`PEAK_TRADE_IMPLEMENTATION_CONTRACT.md`](PEAK_TRADE_IMPLEMENTATION_CONTRACT.md) | Cursor-Kurzvertrag (navigation only) |
| [`ECONOMIC_DIAGNOSTIC_OPTIMIZATION_BOUNDARY_AND_CANONICAL_TRADING_LOGIC_IMMUTABILITY_CONTRACT_V0.md`](ECONOMIC_DIAGNOSTIC_OPTIMIZATION_BOUNDARY_AND_CANONICAL_TRADING_LOGIC_IMMUTABILITY_CONTRACT_V0.md) | Zulässige Optimierungsflächen vs. unveränderliche Semantik |
| [`AI_AUTONOMY_GO_NO_GO_OVERVIEW.md`](AI_AUTONOMY_GO_NO_GO_OVERVIEW.md) | AI-Autonomie Guardrails |
| [`feature_state_map_v1.md`](feature_state_map_v1.md) | Feature-Klassifikation A–D |

---

## 5. Wichtigste Runtime-Dokumente

| Dokument | Rolle |
|----------|-------|
| [`docs/ops/specs/REAL_MARKET_247_RUNTIME_ARCHITECTURE_V1.md`](../ops/specs/REAL_MARKET_247_RUNTIME_ARCHITECTURE_V1.md) | Runtime-Architektur |
| [`docs/ops/runbooks/README.md`](../ops/runbooks/README.md) | Ops-Runbooks-Index |
| [`docs/ops/RUNBOOK_INDEX.md`](../ops/RUNBOOK_INDEX.md) | Runbook-Index |
| [`docs/ops/README.md`](../ops/README.md) | Ops Operator Center |
| [`docs/LIVE_OPERATIONAL_RUNBOOKS.md`](../LIVE_OPERATIONAL_RUNBOOKS.md) | Live-Ops-Übersicht (non-authorizing) |
| [`docs/architecture/TREND_FOLLOWING_V2_CANONICAL_WIRING.md`](../architecture/TREND_FOLLOWING_V2_CANONICAL_WIRING.md) | Canonical Wiring-Hinweis (keine zweite Trading-SSOT) |

---

## 6. Wichtigste Safety-Dokumente

| Dokument | Rolle |
|----------|-------|
| [`docs/GOVERNANCE_AND_SAFETY_OVERVIEW.md`](../GOVERNANCE_AND_SAFETY_OVERVIEW.md) | Safety-/Governance-Übersicht |
| [`docs/SAFETY_POLICY_TESTNET_AND_LIVE.md`](../SAFETY_POLICY_TESTNET_AND_LIVE.md) | Testnet-/Live-Safety-Policy |
| [`docs/risk/KILL_SWITCH_ARCHITECTURE.md`](../risk/KILL_SWITCH_ARCHITECTURE.md) | Kill-Switch-Architektur |
| [`docs/ops/KILL_SWITCH_RUNBOOK.md`](../ops/KILL_SWITCH_RUNBOOK.md) | Kill-Switch-Betrieb |
| [`docs/ops/runbooks/CANARY_LIVE_ENTRY_CRITERIA.md`](../ops/runbooks/CANARY_LIVE_ENTRY_CRITERIA.md) | Canary-Entry-Kriterien (non-authorizing) |
| [`docs/PEAK_TRADE_V1_KNOWN_LIMITATIONS.md`](../PEAK_TRADE_V1_KNOWN_LIMITATIONS.md) | Bekannte Grenzen |

---

## 7. Wichtigste Trading-Logik-Dokumente

Normative Semantik: **nur** die kanonische SSOT v4.4.12 (PART II).

Ergänzende Owner-/Wiring-Hinweise (keine parallele Trading-SSOT):

| Dokument | Rolle |
|----------|-------|
| [`Peak_Trade_Kanonisches_Vollautonomie_Runbook_v4.4.12.md`](Peak_Trade_Kanonisches_Vollautonomie_Runbook_v4.4.12.md) | Master-V2 / Double-Play / Scope / Entry-Exit-Reversal |
| [`Peak_Trade_Canonical_Chain_Wiring_Repair_Master_Runbook_v2.2.md`](Peak_Trade_Canonical_Chain_Wiring_Repair_Master_Runbook_v2.2.md) | Chain-Wiring-Repair-Vertrag |
| [`STRATEGY_SIGNAL_CANONICAL_ARCHITECTURE_RATIFICATION_CLOSEOUT_V1.md`](STRATEGY_SIGNAL_CANONICAL_ARCHITECTURE_RATIFICATION_CLOSEOUT_V1.md) | Negative Architecture Ratification |
| [`docs/ops/specs/MASTER_V2_DECISION_AUTHORITY_MAP_V1.md`](../ops/specs/MASTER_V2_DECISION_AUTHORITY_MAP_V1.md) | Decision-Authority-Map |

---

## 8. Wichtigste Research- / Economic-Evidence-Dokumente

| Dokument | Rolle |
|----------|-------|
| [`Peak_Trade_Kanonisches_Vollautonomie_Runbook_v4.4.12.md`](Peak_Trade_Kanonisches_Vollautonomie_Runbook_v4.4.12.md) | PART III Economic Validity + OLS als Diagnose-Support |
| [`docs/ops/runbooks/INTEGRATED_PAPER_SHADOW_ECONOMIC_VALIDITY_PIPELINE_V1.md`](../ops/runbooks/INTEGRATED_PAPER_SHADOW_ECONOMIC_VALIDITY_PIPELINE_V1.md) | Gate-Split: Paper-Shadow Observation Readiness vs integriertes Economic Evidence Bundle vs ECONOMIC_VALIDITY_PASS |
| [`docs/ops/runbooks/INTEGRATED_PAPER_SHADOW_OBSERVATION_SESSION_CAPABILITY_V1.md`](../ops/runbooks/INTEGRATED_PAPER_SHADOW_OBSERVATION_SESSION_CAPABILITY_V1.md) | Kanonischer Observation-Pfad (Entrypoint/Model/Readiness/Evidence) ohne Default-Autorisierung |
| [`docs/ops/runbooks/PAPER_SHADOW_OBSERVATION_OPERATOR_GO_AND_SESSION_PREREGISTRATION_CAPABILITY_V1.md`](../ops/runbooks/PAPER_SHADOW_OBSERVATION_OPERATOR_GO_AND_SESSION_PREREGISTRATION_CAPABILITY_V1.md) | Session-Preregistration + scoped Operator-GO / Authorization-Readiness (keine Session-Ausführung) |
| [`ECONOMIC_DIAGNOSTIC_OPTIMIZATION_BOUNDARY_AND_CANONICAL_TRADING_LOGIC_IMMUTABILITY_CONTRACT_V0.md`](ECONOMIC_DIAGNOSTIC_OPTIMIZATION_BOUNDARY_AND_CANONICAL_TRADING_LOGIC_IMMUTABILITY_CONTRACT_V0.md) | Optimierungsgrenze |
| [`docs/STRATEGY_RESEARCH_PLAYBOOK.md`](../STRATEGY_RESEARCH_PLAYBOOK.md) | Research-Workflow |
| [`docs/PLAYBOOK_RESEARCH_TO_LIVE_PORTFOLIOS.md`](../PLAYBOOK_RESEARCH_TO_LIVE_PORTFOLIOS.md) | Research → Portfolio-Pfad |
| [`docs/audit/EVIDENCE_INDEX.md`](../audit/EVIDENCE_INDEX.md) | Evidence-Index |

OLS / Offline Linear Evidence ist Economic-Validation-**Support**, keine Runtime-, Trading-, Promotion- oder Sizing-Authority.
`ECONOMIC_VALIDITY_OFFLINE_GATE_PASS` ist Legacy-Offline-Sub-Evidence only; System-`ECONOMIC_VALIDITY_PASS` erfordert `INTEGRATED_ECONOMIC_EVIDENCE_BUNDLE_VERIFIED`.
Paper Shadow ist Evidence-Generator only; `PAPER_SHADOW_OBSERVATION_AUTHORIZED=false` ohne verifiziertes, scoped Operator-GO-Artefakt.
Readiness ist nicht Authorization; Authorization ist nicht Execution.

---

## 9. Wichtigste Runbooks

| Dokument | Rolle |
|----------|-------|
| [`Peak_Trade_Kanonisches_Vollautonomie_Runbook_v4.4.12.md`](Peak_Trade_Kanonisches_Vollautonomie_Runbook_v4.4.12.md) | Kanonische Vollautonomie-SSOT |
| [`docs/ops/market_dashboard/PEAK_TRADE_MARKET_DASHBOARD_LANDSCAPE_MASTER_RUNBOOK_V2.md`](../ops/market_dashboard/PEAK_TRADE_MARKET_DASHBOARD_LANDSCAPE_MASTER_RUNBOOK_V2.md) | Market Dashboard Landscape V2 (canonical read-only consumer planning SSOT; non-authorizing; Documentation Anchor = documentary index only; `OPERATOR_PRODUCT_GATE=true`; `INTRABAR_CAPABILITY=PASS`; `REGIME_BULL_BEAR_SWITCH_BINDING=COMPLETE`; `NEXT_CANONICAL_ACTION=STOP_IDLE`; `WORKSTREAM_STATE=FINAL_CLOSEOUT_COMPLETE_STOP_IDLE`) |
| [`docs/ops/runbooks/README.md`](../ops/runbooks/README.md) | Operative Runbooks |
| [`docs/ops/RUNBOOK_INDEX.md`](../ops/RUNBOOK_INDEX.md) | Index |
| [`docs/DISASTER_RECOVERY_RUNBOOK.md`](../DISASTER_RECOVERY_RUNBOOK.md) | DR |
| [`docs/LIVE_DEPLOYMENT_PLAYBOOK.md`](../LIVE_DEPLOYMENT_PLAYBOOK.md) | Deployment (non-authorizing) |

---

## 10. Reihenfolge der Implementierung

Maßgeblich ausschließlich in der kanonischen SSOT, Abschnitt **§34 Korrigierte kanonische Implementierungsreihenfolge** (`STEP 29A` … `STEP 29Z`).

Kurzüberblick (keine lokale Semantik):

```text
29A Constitutional Freeze
→ 29B Market Context
→ 29C Scope Init
→ 29D Scope Event Generator
→ 29E Bull/Bear
→ 29F Survival/Suitability
→ 29G Double Play
→ 29H Entry/Exit Policy
→ 29I Offline Trading Logic Replay
→ 29J Backtest Economic Realism
→ 29K Strategy Registry
→ 29L / 29L.1 / 29L.2 MV2 Wiring + Parity + OLS Scaffolding
→ 29M Economic Viability Evidence
→ 29N Promotion Gate Binding
→ 29O–29Q Intent / Risk / Order Intent
→ 29R–29T Runtime Rewire / Fenced Writer / Zero-Order
→ 29U–29Z Shadow → Paper → Testnet → SLO → Canary → Production
```

Aktueller Progress-Ist: [`PEAK_TRADE_AUTONOMY_RUNBOOK_PROGRESS_V1.md`](PEAK_TRADE_AUTONOMY_RUNBOOK_PROGRESS_V1.md) (non-authorizing).

---

## 11. Hinweise für neue Entwickler

1. **Immer hier starten** — dann die kanonische SSOT v4.4.12 lesen (`CURSOR_MUST_READ_CANONICAL_RUNBOOK_FIRST=true`).
2. **Keine Vermutung über Owner** — read-only inventarisieren; Unbekanntheit = fail-closed, keine Mutation.
3. **Reuse-before-new** — bestehende Owner erweitern; keine parallele SSOT, kein zweites Runbook, keine parallele Pipeline.
4. **Docs-only vs. Runtime** — diese Map und reine Doku-PRs autorisieren nichts Live-/Order-/Scheduler-seitig.
5. **Frontdoor** für allgemeine Produktdoku: [`docs/README.md`](../README.md).
6. **Onboarding**: [`docs/GETTING_STARTED.md`](../GETTING_STARTED.md), [`docs/DEV_SETUP.md`](../DEV_SETUP.md).
7. **CI / Docs Gates**: Token Policy und Reference Targets vor Push lokal prüfen; Ops-Drift-Registry bei Canonical-Doku-Änderungen mitziehen.

---

## 12. Explizite Nicht-Authority

```text
NO_SEMANTICS_IN_THIS_DOCUMENT=true
NO_TRADING_LOGIC_DEFINED_HERE=true
NO_SAFETY_OVERRIDE_DEFINED_HERE=true
NO_PROMOTION_AUTHORITY_DEFINED_HERE=true
NO_RUNTIME_ACTIVATION_BY_READING=true
NO_LIVE_FROM_DOCS_ALONE=true
```

Bei Widerspruch zwischen dieser Map und einem kanonischen Owner gewinnt der Owner. Diese Map wird dann navigativ korrigiert — nicht die Owner-Semantik.
