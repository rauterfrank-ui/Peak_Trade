# Peak Trade — Map of Truth

```text
DOCUMENT_CLASS=CURRENT_RUNTIME_TRUTH
DOCUMENT_ROLE=NAVIGATION_ONLY_NO_SEMANTICS
```

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

**Aktuelle Runtime-Ist-Wahrheit (nicht Zielbild):** [`PEAK_TRADE_CANONICAL_RUNTIME_TRUTH_MAP_V1.md`](PEAK_TRADE_CANONICAL_RUNTIME_TRUTH_MAP_V1.md)

**Capability-Closure-Arbeitsrunbook:** [`Peak_Trade_Canonical_Capability_Closure_Runtime_Recovery_Trading_Path_Runbook_V1_2_Trading_First.md`](Peak_Trade_Canonical_Capability_Closure_Runtime_Recovery_Trading_Path_Runbook_V1_2_Trading_First.md)

---

## 1. Systemzweck

Peak Trade ist ein **futures-only** Handelssystem. Das **Zielprogramm** ist vollautonome Runtime-Closure; das ist **nicht** der aktuelle Runtime-Ist-Zustand.

Aktuell verbindlich (siehe Canonical Runtime Truth Map):

```text
CANONICAL_RUNTIME_ENTRYPOINT_STATUS=FULL_CANONICAL_STATEFUL_RUNTIME_ACTIVE
FULL_CANONICAL_STATEFUL_RUNTIME_ACTIVE=true
SIMULATED_EXECUTION_ACTIVE=true
PUBLIC_MD_RUNTIME_CAPABLE=true
PUBLIC_MD_NETWORK_SESSION_OBSERVED=false
LIVE_TRADING=FAIL_CLOSED
DASHBOARD=READ_ONLY_CONSUMER
PHASE_1_SELECTION=SINGLE_SELECTED_FUTURE
PHASE_1_MAX_POSITIONS=1
MULTI_FUTURE_RUNTIME_AUTHORIZED=false
```

Das Zielprogramm umfasst u. a.:

- deterministische, auditierbare Handelslogik,
- realistische Profitabilitätsvalidierung,
- unabhängige Safety Authority,
- gefencete Single-Writer-Runtime,
- vollständige Reconciliation und sichere Restart-/Recovery-Semantik,
- durchgängige Research → Validation → Promotion → Runtime → Feedback-Kette,
- Phase-1 Single-Future-Safety vor späterer Multi-Future-Portfolio-Runtime (nur nach separaten Gates).

Keine Anlageberatung. Keine Live-/Order-/Scheduler-Freigabe allein durch Lektüre.

---

## 2. Kanonische semantische Autorität (Master Runbook V2.3)

Ab sofort und bis zur vollständigen Systemautonomie ist die **einzige** aktuelle Architektur-, Governance- und Implementierungsautorität:

| Rolle | Pfad |
|-------|------|
| **Canonical Master Runbook (aktuell)** | [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) |
| **Historische Vorgängerautorität (SUPERSEDED)** | [`Peak_Trade_Kanonisches_Vollautonomie_Runbook_v4.4.12.md`](Peak_Trade_Kanonisches_Vollautonomie_Runbook_v4.4.12.md) |

```text
CANONICAL_MASTER_RUNBOOK_PATH=docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md
CANONICAL_WORKING_AUTHORITY=docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md
CURSOR_MUST_READ_CANONICAL_RUNBOOK_FIRST=true
NO_PARALLEL_SEMANTIC_MODEL=true
RUNTIME_AUTHORIZATION_EFFECT=NONE
LIVE_AUTHORIZED=false
TESTNET_AUTHORIZED=false
ORDERS_ALLOWED=false
```

Historische Vorgängerfelder (nicht aktuell; nur für bestehende Contract-/Progress-Marker und Supersession-Nachweis):

```text
CANONICAL_VOLLAUTONOMIE_RUNBOOK_VERSION=v4.4.12
CANONICAL_VOLLAUTONOMIE_RUNBOOK_PATH=docs/governance/Peak_Trade_Kanonisches_Vollautonomie_Runbook_v4.4.12.md
CANONICAL_RUNBOOK_CONTENT_VERSION=4.4.12-full-canonical-system-parity-before-system-economic-evidence
HISTORICAL_ONLY=true
STATUS=SUPERSEDED
SUPERSEDED_BY=docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md
```

Ältere Runbook-Pfade (v4.4 / v4.4.1 / v4.4.10 Dateiname / v2.6 / v4.4.12) sind **historische Adoption-/Crosslink-Oberflächen**. Normative Semantik kommt ausschließlich aus dem Canonical Master Runbook über diese Map.

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
- [`docs/architecture/canonical/PEAK_TRADE_CANONICAL_END_STATE_WIRING_MAP.md`](../architecture/canonical/PEAK_TRADE_CANONICAL_END_STATE_WIRING_MAP.md) — derived end-state wiring map (non-SSOT; non-runtime-authorizing; forensic SHA-bound)
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
| [`PEAK_TRADE_CANONICAL_RUNTIME_TRUTH_MAP_V1.md`](PEAK_TRADE_CANONICAL_RUNTIME_TRUTH_MAP_V1.md) | Canonical Runtime Ist-Zustand (CURRENT_RUNTIME_TRUTH; non-authorizing) |
| [`PEAK_TRADE_DEFERRED_WORK_RECOVERY_REGISTER_V1.md`](PEAK_TRADE_DEFERRED_WORK_RECOVERY_REGISTER_V1.md) | Deferred-Work Recovery Register (Capability 0.4; Rotation-Policy Wiedervorlage; non-activating) |
| [`docs/ops/specs/REAL_MARKET_247_RUNTIME_ARCHITECTURE_V1.md`](../ops/specs/REAL_MARKET_247_RUNTIME_ARCHITECTURE_V1.md) | Runtime-Architektur |
| [`docs/runbooks/canonical/PEAK_TRADE_CANONICAL_RUNTIME_OPERATIONS_DASHBOARD_AND_PROCESS_SUPERVISION_RUNBOOK_V2_4.md`](../runbooks/canonical/PEAK_TRADE_CANONICAL_RUNTIME_OPERATIONS_DASHBOARD_AND_PROCESS_SUPERVISION_RUNBOOK_V2_4.md) | Canonical Runtime Operations / Dashboard / Process Supervision V2.4 (`DERIVED_DOMAIN_AUTHORITY_ONLY`; **nicht** SSOT; Master Runbook bleibt einzige SSOT mit absoluter Precedence; Manifest: [`…_V2_4_RATIFICATION.json`](../runbooks/canonical/PEAK_TRADE_CANONICAL_RUNTIME_OPERATIONS_DASHBOARD_AND_PROCESS_SUPERVISION_RUNBOOK_V2_4_RATIFICATION.json); **kein** Runtime-/Trading-/Testnet-/Live-/Order-/Credential-Authorization-Effekt) |
| [`docs/ops/runbooks/README.md`](../ops/runbooks/README.md) | Ops-Runbooks-Index |
| [`docs/ops/RUNBOOK_INDEX.md`](../ops/RUNBOOK_INDEX.md) | Runbook-Index |
| [`docs/ops/README.md`](../ops/README.md) | Ops Operator Center |
| [`docs/LIVE_OPERATIONAL_RUNBOOKS.md`](../LIVE_OPERATIONAL_RUNBOOKS.md) | Live-Ops-Übersicht (non-authorizing) |
| [`docs/architecture/TREND_FOLLOWING_V2_CANONICAL_WIRING.md`](../architecture/TREND_FOLLOWING_V2_CANONICAL_WIRING.md) | Canonical Wiring-Hinweis (keine zweite Trading-SSOT) |
| [`docs/architecture/canonical/PEAK_TRADE_CANONICAL_END_STATE_WIRING_MAP.md`](../architecture/canonical/PEAK_TRADE_CANONICAL_END_STATE_WIRING_MAP.md) | Canonical End-State Wiring Map (derived; `RUNTIME_AUTHORITY_EFFECT=NONE`; keine zweite Trading-SSOT) |

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

Normative Semantik: **nur** das Canonical Master Runbook (`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`). Historisch: v4.4.12 (SUPERSEDED).

Ergänzende Owner-/Wiring-Hinweise (keine parallele Trading-SSOT):

| Dokument | Rolle |
|----------|-------|
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) | Master-V2 / Double-Play / Scope / Entry-Exit-Reversal (aktuell) |
| [`Peak_Trade_Kanonisches_Vollautonomie_Runbook_v4.4.12.md`](Peak_Trade_Kanonisches_Vollautonomie_Runbook_v4.4.12.md) | Historische Vorgängerreferenz (SUPERSEDED) |
| [`Peak_Trade_Canonical_Chain_Wiring_Repair_Master_Runbook_v2.2.md`](Peak_Trade_Canonical_Chain_Wiring_Repair_Master_Runbook_v2.2.md) | Chain-Wiring-Repair-Vertrag |
| [`STRATEGY_SIGNAL_CANONICAL_ARCHITECTURE_RATIFICATION_CLOSEOUT_V1.md`](STRATEGY_SIGNAL_CANONICAL_ARCHITECTURE_RATIFICATION_CLOSEOUT_V1.md) | Negative Architecture Ratification |
| [`docs/ops/specs/MASTER_V2_DECISION_AUTHORITY_MAP_V1.md`](../ops/specs/MASTER_V2_DECISION_AUTHORITY_MAP_V1.md) | Decision-Authority-Map |

---

## 8.0 Phase 11 §11.12.8 bounded campaign evidence (navigation only)

| Pfad | Rolle |
|------|-------|
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.12.8.2 | SSOT forensic campaign-run status |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.12.8.3 | SSOT OKX EEA Demo path EXTERNAL_CAPABILITY_UNAVAILABLE closeout |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.12.8.4 | SSOT OKX Global Demo binding package (NO_ORDER; not activated) |
| [`docs/ops/specs/CAPABILITY_11_SECTION_11_12_8_OKX_GLOBAL_DEMO_VENUE_HOST_ACCOUNT_INSTRUMENT_BINDING_V1.md`](../ops/specs/CAPABILITY_11_SECTION_11_12_8_OKX_GLOBAL_DEMO_VENUE_HOST_ACCOUNT_INSTRUMENT_BINDING_V1.md) | Capability spec for Global Demo binding |
| [`evidence/ops/section_11_12_8_bounded_long_running_productive_testnet_campaign_now/20260808T181528Z/`](../../evidence/ops/section_11_12_8_bounded_long_running_productive_testnet_campaign_now/20260808T181528Z/) | Primary sealed run evidence (immutable) |
| [`…&#47;20260808T181528Z&#47;derived_forensic_closeout_v1&#47;`](../../evidence/ops/section_11_12_8_bounded_long_running_productive_testnet_campaign_now/20260808T181528Z/derived_forensic_closeout_v1/) | Derived HTTP-403 forensic closeout (non-SSOT) |
| [`evidence&#47;ops&#47;section_11_12_8_close_okx_eea_demo_path_external_capability_unavailable_and_evaluate_alternate_derivatives_testnet_no_order_v1&#47;20260810T143709Z&#47;`](../../evidence/ops/section_11_12_8_close_okx_eea_demo_path_external_capability_unavailable_and_evaluate_alternate_derivatives_testnet_no_order_v1/20260810T143709Z/) | OKX EEA Demo path closeout &#47; no-order alternate evaluation (non-activating) |
| [`evidence&#47;ops&#47;section_11_12_8_okx_global_demo_venue_host_account_instrument_binding_v1&#47;20260810T151323Z&#47;`](../../evidence/ops/section_11_12_8_okx_global_demo_venue_host_account_instrument_binding_v1/20260810T151323Z/) | OKX Global Demo binding package evidence (NO_ORDER) |

```text
THIS_SECTION_DEFINES_NO_SEMANTICS=true
SECTION_11_12_8_CLOSED=false
SECTION_11_13_STARTED=false
LIVE_AUTHORIZED=false
PRE_LIVE_CYBERSECURITY_GATE=NOT_PASSED
OKX_EEA_DEMO_PRODUCTIVE_ORDER_PATH_STATUS=CLOSED_EXTERNAL_CAPABILITY_UNAVAILABLE
OKX_GLOBAL_DEMO_BINDING_PACKAGE_STATUS=PREPARED_NO_ORDER_NOT_ACTIVATED
NEXT_CANONICAL_STEP_POINTER=OWNER_GO_EXECUTE_BOUNDED_NO_ORDER_PREFLIGHT_ON_OKX_GLOBAL_DEMO_BTC_USDT_SWAP
PREDECESSOR_GET_PROOF_IS_NOT_TARGETED_TRADE_PROOF=true
PREDECESSOR_ORDERLESS_GET_PROOF_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_12_8_autonomous_okx_eea_demo_credential_ip_resolve_v1&#47;20260808T203507Z&#47;
ALTERNATE_EVALUATION_IS_NOT_VENUE_ACTIVATION=true
BINDING_PACKAGE_IS_NOT_VENUE_ACTIVATION=true
```

---

## 8. Wichtigste Research- / Economic-Evidence-Dokumente

| Dokument | Rolle |
|----------|-------|
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) | Economic Validity / evidence gates (aktuell) |
| [`Peak_Trade_Kanonisches_Vollautonomie_Runbook_v4.4.12.md`](Peak_Trade_Kanonisches_Vollautonomie_Runbook_v4.4.12.md) | Historische PART-III-Vorgängerreferenz (SUPERSEDED) |
| [`docs/ops/runbooks/INTEGRATED_PAPER_SHADOW_ECONOMIC_VALIDITY_PIPELINE_V1.md`](../ops/runbooks/INTEGRATED_PAPER_SHADOW_ECONOMIC_VALIDITY_PIPELINE_V1.md) | Gate-Split: Paper-Shadow Observation Readiness vs integriertes Economic Evidence Bundle vs ECONOMIC_VALIDITY_PASS |
| [`docs/ops/runbooks/INTEGRATED_PAPER_SHADOW_OBSERVATION_SESSION_CAPABILITY_V1.md`](../ops/runbooks/INTEGRATED_PAPER_SHADOW_OBSERVATION_SESSION_CAPABILITY_V1.md) | Kanonischer Observation-Pfad (Entrypoint/Model/Readiness/Evidence) ohne Default-Autorisierung |
| [`docs/ops/runbooks/PAPER_SHADOW_OBSERVATION_OPERATOR_GO_AND_SESSION_PREREGISTRATION_CAPABILITY_V1.md`](../ops/runbooks/PAPER_SHADOW_OBSERVATION_OPERATOR_GO_AND_SESSION_PREREGISTRATION_CAPABILITY_V1.md) | Session-Preregistration + scoped Operator-GO / Authorization-Readiness (keine Session-Ausführung) |
| [`docs/ops/runbooks/INTEGRATED_PAPER_SHADOW_OBSERVATION_WALLCLOCK_SESSION_EXECUTION_CAPABILITY_V1.md`](../ops/runbooks/INTEGRATED_PAPER_SHADOW_OBSERVATION_WALLCLOCK_SESSION_EXECUTION_CAPABILITY_V1.md) | Wallclock OKX-EEA public MD Observation (technisch; keine produktive Default-Autorisierung) |
| [`docs/ops/runbooks/INTEGRATED_PAPER_SHADOW_PRODUCTIVE_AUTHORIZATION_ISSUANCE_AND_REAL_NETWORK_EXECUTION_CAPABILITY_V1.md`](../ops/runbooks/INTEGRATED_PAPER_SHADOW_PRODUCTIVE_AUTHORIZATION_ISSUANCE_AND_REAL_NETWORK_EXECUTION_CAPABILITY_V1.md) | Produktive Issuance + realer Public-MD-Run (Merge autorisiert keine Session) |
| [`ECONOMIC_DIAGNOSTIC_OPTIMIZATION_BOUNDARY_AND_CANONICAL_TRADING_LOGIC_IMMUTABILITY_CONTRACT_V0.md`](ECONOMIC_DIAGNOSTIC_OPTIMIZATION_BOUNDARY_AND_CANONICAL_TRADING_LOGIC_IMMUTABILITY_CONTRACT_V0.md) | Optimierungsgrenze |
| [`docs/STRATEGY_RESEARCH_PLAYBOOK.md`](../STRATEGY_RESEARCH_PLAYBOOK.md) | Research-Workflow |
| [`docs/PLAYBOOK_RESEARCH_TO_LIVE_PORTFOLIOS.md`](../PLAYBOOK_RESEARCH_TO_LIVE_PORTFOLIOS.md) | Research → Portfolio-Pfad |
| [`docs/audit/EVIDENCE_INDEX.md`](../audit/EVIDENCE_INDEX.md) | Evidence-Index |

OLS / Offline Linear Evidence ist Economic-Validation-**Support**, keine Runtime-, Trading-, Promotion- oder Sizing-Authority.
`ECONOMIC_VALIDITY_OFFLINE_GATE_PASS` ist Legacy-Offline-Sub-Evidence only; System-`ECONOMIC_VALIDITY_PASS` erfordert `INTEGRATED_ECONOMIC_EVIDENCE_BUNDLE_VERIFIED`.
Paper Shadow ist Evidence-Generator only; `PAPER_SHADOW_OBSERVATION_AUTHORIZED=false` ohne verifiziertes, scoped Operator-GO-Artefakt.
Readiness ist nicht Authorization; Authorization ist nicht Execution.

---

## 8.1 Local verification minimum / CI dedup (navigation only)

| Dokument | Rolle |
|----------|-------|
| [`docs/ops/specs/GOVERNANCE_VERIFICATION_MINIMUM_LOCAL_CI_DEDUP_V1.md`](../ops/specs/GOVERNANCE_VERIFICATION_MINIMUM_LOCAL_CI_DEDUP_V1.md) | Governance verification minimum &#47; local CI dedup (navigation pointer; Semantik im Master Runbook §15.3 + JSON-Owner) |
| [`docs/ops/specs/GOVERNANCE_VERIFICATION_MINIMUM_LOCAL_CI_DEDUP_V1.json`](../ops/specs/GOVERNANCE_VERIFICATION_MINIMUM_LOCAL_CI_DEDUP_V1.json) | Machine-readable policy owner |

```text
THIS_SECTION_DEFINES_NO_SEMANTICS=true
CANONICAL_SEMANTICS=docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md#15.3
```

---

## 9. Wichtigste Runbooks

| Dokument | Rolle |
|----------|-------|
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) | Canonical Master Runbook (aktuelle semantische Autorität) |
| [`docs/runbooks/canonical/PEAK_TRADE_CANONICAL_RUNTIME_OPERATIONS_DASHBOARD_AND_PROCESS_SUPERVISION_RUNBOOK_V2_4.md`](../runbooks/canonical/PEAK_TRADE_CANONICAL_RUNTIME_OPERATIONS_DASHBOARD_AND_PROCESS_SUPERVISION_RUNBOOK_V2_4.md) | Canonical Runtime Operations V2.4 (`AUTHORITY_CLASSIFICATION=DERIVED_DOMAIN_AUTHORITY_ONLY`; `RUNTIME_OPERATIONS_RUNBOOK_IS_SSOT=false`; Master Runbook bleibt einzige SSOT mit absoluter Precedence; Manifest [`…_V2_4_RATIFICATION.json`](../runbooks/canonical/PEAK_TRADE_CANONICAL_RUNTIME_OPERATIONS_DASHBOARD_AND_PROCESS_SUPERVISION_RUNBOOK_V2_4_RATIFICATION.json); **kein** Runtime-/Trading-/Testnet-/Live-/Order-/Credential-Authorization-Effekt) |
| [`docs/runbooks/canonical/PEAK_TRADE_CANONICAL_CYBERSECURITY_RUNBOOK_V2_1.md`](../runbooks/canonical/PEAK_TRADE_CANONICAL_CYBERSECURITY_RUNBOOK_V2_1.md) | Canonical Cybersecurity Runbook V2.1 phase-aware / **mandatory** Pre-Live Security Gate (`AUTHORITY_CLASSIFICATION=DERIVED_DOMAIN_AUTHORITY_ONLY`; `CYBERSECURITY_RUNBOOK_IS_SSOT=false`; Master §4.8 / §4.8.1 / §11.12.9; Manifest [`…_V2_1_RATIFICATION.json`](../runbooks/canonical/PEAK_TRADE_CANONICAL_CYBERSECURITY_RUNBOOK_V2_1_RATIFICATION.json); `PRE_LIVE_CYBERSECURITY_GATE_CONTRACT=MANDATORY`; `PRE_LIVE_CYBERSECURITY_GATE=NOT_PASSED`; `FUTURE_IMPLEMENTATION_BOUND_TO_CANONICAL_SECURITY_INVARIANTS=true`; **kein** Runtime-/Trading-/Testnet-/Live-/Order-/Credential-Authorization-Effekt) |
| [`Peak_Trade_Kanonisches_Vollautonomie_Runbook_v4.4.12.md`](Peak_Trade_Kanonisches_Vollautonomie_Runbook_v4.4.12.md) | Historische Vollautonomie-Vorgängerreferenz (SUPERSEDED) |
| [`docs/ops/market_dashboard/PEAK_TRADE_MARKET_DASHBOARD_LANDSCAPE_MASTER_RUNBOOK_V2.md`](../ops/market_dashboard/PEAK_TRADE_MARKET_DASHBOARD_LANDSCAPE_MASTER_RUNBOOK_V2.md) | Market Dashboard Landscape V2 (canonical read-only consumer planning SSOT; non-authorizing; Documentation Anchor = documentary index only; `OPERATOR_PRODUCT_GATE=true`; `INTRABAR_CAPABILITY=PASS`; `REGIME_BULL_BEAR_SWITCH_BINDING=COMPLETE`; `NEXT_CANONICAL_ACTION=STOP_IDLE`; `WORKSTREAM_STATE=FINAL_CLOSEOUT_COMPLETE_STOP_IDLE`) |
| [`docs/ops/runbooks/README.md`](../ops/runbooks/README.md) | Operative Runbooks |
| [`docs/ops/RUNBOOK_INDEX.md`](../ops/RUNBOOK_INDEX.md) | Index |
| [`docs/DISASTER_RECOVERY_RUNBOOK.md`](../DISASTER_RECOVERY_RUNBOOK.md) | DR |
| [`docs/LIVE_DEPLOYMENT_PLAYBOOK.md`](../LIVE_DEPLOYMENT_PLAYBOOK.md) | Deployment (non-authorizing) |

---

## 10. Reihenfolge der Implementierung

Maßgeblich ausschließlich im Canonical Master Runbook und dessen Capability-Reihenfolge. Historische STEP-29-Übersicht bleibt in der SUPERSEDED-Datei v4.4.12 nachlesbar.

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

1. **Immer hier starten** — dann `docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md` vollständig lesen (`CURSOR_MUST_READ_CANONICAL_RUNBOOK_FIRST=true`).
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
