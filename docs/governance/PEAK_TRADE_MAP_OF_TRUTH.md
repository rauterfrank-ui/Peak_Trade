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
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.12.8.3 | SSOT OKX EEA Demo BTC-USDT-SWAP productive-order path closeout (`CLOSED_DEPRECATED_HISTORICAL_EVIDENCE_ONLY`) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.12.8.4 | SSOT historical OKX Global Demo binding package (NO_ORDER; not activated; superseded by §11.12.8.5) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.12.8.5 | SSOT active OKX EEA Demo XPerp binding package (NO_ORDER package default; write path in §11.12.8.6) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.12.8.6 | SSOT OKX EEA Demo XPerp ephemeral campaign private-write path (armable; no auto-execute) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.12.8.7 | SSOT OKX EEA Demo XPerp bounded campaign forensic closeout package (no section close; superseded next-step by §11.12.8.8) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.12.8.8 | SSOT OKX EEA Demo XPerp clOrdId alphanumeric fix + bounded ACK proof (no section close; superseded next-step by §11.12.8.9) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.12.8.9 | SSOT OKX EEA Demo XPerp cancel-instId fix + bounded clean closeout proof (closeout recommended; superseded next-step by §11.12.8.10) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.12.8.10 | SSOT OKX EEA Demo XPerp §11.12.8 Owner closeout package (`SECTION_11_12_8_CLOSED=true`; Cap 11.12 Testnet progression program not closed) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.12.9 | SSOT Pre-Live Cybersecurity Acceptance Gate contract (mandatory; gate `NOT_PASSED`) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.12.9.1 | SSOT evidence-bound Pre-Live gate evaluation (`SECTION_11_12_9_EVALUATION_COMPLETED=true`; gate remains `NOT_PASSED`) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.12.9.2 | SSOT Cap 11.12 Testnet progression program nomenclature reconcile (docs-only; legacy tokens aliased&#47;retired) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.12.9.3 | SSOT Cap 11.12 Testnet progression residual proof §11.12.1 (fixture bind; no order&#47;network) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.12.9.4 | SSOT Cap 11.12 Testnet progression residual proof §11.12.2 (fixture dry-run bind; no order&#47;network) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.12.9.5 | SSOT Cap 11.12 Testnet progression residual proof §11.12.3 (fixture lifecycle bind; no order&#47;network) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.12.9.6 | SSOT Cap 11.12 Testnet progression residual proof §11.12.4 (fixture lifecycle bind; no order&#47;network) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.12.9.7 | SSOT Cap 11.12 Testnet progression residual proof §11.12.5 (fixture recovery bind; no order&#47;network) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.12.9.8 | SSOT Cap 11.12 Testnet progression residual proof §11.12.6 (fixture restart bind; no order&#47;network) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.12.9.9 | SSOT Cap 11.12 Testnet progression residual proof §11.12.7 (fixture kill-switch bind; no order&#47;network) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.12.9.10 | SSOT Cap 11.12 Testnet progression residual proof §11.12.8 (fixture campaign-evidence bind; no order&#47;network) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.12.9.11 | SSOT Cap 11.12 OPEN_TESTNET_PROVEN_FIELDS reporting reconcile residual (no proven-field closure; no order&#47;network) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.12.9.12 | SSOT Cap 11.12 productive `TESTNET_ORDER_LIFECYCLE_PROVEN` (bounded Demo XPerp lifecycle; hard stop) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.12.9.13 | SSOT Cap 11.12 productive `TESTNET_RECONCILIATION_PROVEN` (Demo XPerp account&#47;order snapshot vs local; `ORDER_EFFECT=NONE`; hard stop) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.12.9.14 | SSOT Cap 11.12 productive `TESTNET_RESTART_PROVEN` (Demo XPerp restart with open order + open position; hard stop) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.12.9.15 | SSOT Cap 11.12 productive `TESTNET_UNKNOWN_SUBMIT_RECOVERY_PROVEN` (Demo XPerp unknown-submit query-before-retry + reconnect; hard stop) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.12.9.16 | SSOT Cap 11.12 productive `TESTNET_DUPLICATE_ORDER_PREVENTION_PROVEN` (Demo XPerp duplicate&#47;replay&#47;retry client_order_id prevention; hard stop) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.12.9.17 | SSOT Cap 11.12 productive `TESTNET_KILL_SWITCH_PROVEN` (Demo XPerp kill-switch&#47;emergency-control trip&#47;halt&#47;cancel-all; hard stop) |
| [`docs/ops/specs/CAPABILITY_11_SECTION_11_12_8_OKX_EEA_DEMO_XPERP_VENUE_HOST_ACCOUNT_INSTRUMENT_BINDING_V1.md`](../ops/specs/CAPABILITY_11_SECTION_11_12_8_OKX_EEA_DEMO_XPERP_VENUE_HOST_ACCOUNT_INSTRUMENT_BINDING_V1.md) | Capability spec for active EEA Demo XPerp binding |
| [`docs/ops/specs/CAPABILITY_11_SECTION_11_12_8_OKX_EEA_DEMO_XPERP_CAMPAIGN_PRIVATE_WRITE_GATE_V1.md`](../ops/specs/CAPABILITY_11_SECTION_11_12_8_OKX_EEA_DEMO_XPERP_CAMPAIGN_PRIVATE_WRITE_GATE_V1.md) | Capability spec for ephemeral XPerp campaign private-write gate |
| [`docs/ops/specs/CAPABILITY_11_SECTION_11_12_8_OKX_GLOBAL_DEMO_VENUE_HOST_ACCOUNT_INSTRUMENT_BINDING_V1.md`](../ops/specs/CAPABILITY_11_SECTION_11_12_8_OKX_GLOBAL_DEMO_VENUE_HOST_ACCOUNT_INSTRUMENT_BINDING_V1.md) | Historical Global Demo binding capability (not active) |
| [`evidence/ops/section_11_12_8_bounded_long_running_productive_testnet_campaign_now/20260808T181528Z/`](../../evidence/ops/section_11_12_8_bounded_long_running_productive_testnet_campaign_now/20260808T181528Z/) | Historical primary sealed run evidence (immutable; HTTP 403 era) |
| [`…&#47;20260808T181528Z&#47;derived_forensic_closeout_v1&#47;`](../../evidence/ops/section_11_12_8_bounded_long_running_productive_testnet_campaign_now/20260808T181528Z/derived_forensic_closeout_v1/) | Derived HTTP-403 forensic closeout (non-SSOT) |
| [`evidence&#47;ops&#47;section_11_12_8_bounded_okx_eea_demo_xperp_campaign_execute_v1&#47;20260810T181703Z&#47;`](../../evidence/ops/section_11_12_8_bounded_okx_eea_demo_xperp_campaign_execute_v1/20260810T181703Z/) | Primary sealed OKX EEA Demo XPerp bounded campaign evidence (immutable) |
| [`…&#47;20260810T181703Z&#47;derived_forensic_closeout_v1&#47;`](../../evidence/ops/section_11_12_8_bounded_okx_eea_demo_xperp_campaign_execute_v1/20260810T181703Z/derived_forensic_closeout_v1/) | Derived XPerp campaign forensic closeout (clOrdId 51000; non-SSOT) |
| [`evidence&#47;ops&#47;section_11_12_8_retry_bounded_okx_eea_demo_xperp_ack_proof_after_clordid_fix_v1&#47;20260810T194806Z&#47;`](../../evidence/ops/section_11_12_8_retry_bounded_okx_eea_demo_xperp_ack_proof_after_clordid_fix_v1/20260810T194806Z/) | Bounded XPerp ACK proof after alphanumeric clOrdId fix (immutable evidence; non-SSOT) |
| [`evidence&#47;ops&#47;section_11_12_8_retry_bounded_okx_eea_demo_xperp_clean_closeout_after_cancel_instid_fix_v1&#47;20260810T200151Z&#47;`](../../evidence/ops/section_11_12_8_retry_bounded_okx_eea_demo_xperp_clean_closeout_after_cancel_instid_fix_v1/20260810T200151Z/) | Bounded XPerp clean closeout after cancel-instId fix (immutable evidence; non-SSOT) |
| [`evidence&#47;ops&#47;section_11_12_8_closeout_package_v1&#47;20260810T201332Z&#47;`](../../evidence/ops/section_11_12_8_closeout_package_v1/20260810T201332Z/) | Owner §11.12.8 closeout package (derived; non-SSOT; section closed) |
| [`evidence&#47;ops&#47;section_11_12_9_pre_live_cybersecurity_acceptance_gate_evidence_bound_evaluation_v1&#47;20260810T202800Z&#47;`](../../evidence/ops/section_11_12_9_pre_live_cybersecurity_acceptance_gate_evidence_bound_evaluation_v1/20260810T202800Z/) | Owner §11.12.9.1 Pre-Live Cybersecurity Acceptance Gate evidence-bound evaluation (derived; non-SSOT; gate remains `NOT_PASSED`) |
| [`evidence&#47;ops&#47;section_11_12_8_close_okx_eea_demo_path_external_capability_unavailable_and_evaluate_alternate_derivatives_testnet_no_order_v1&#47;20260810T143709Z&#47;`](../../evidence/ops/section_11_12_8_close_okx_eea_demo_path_external_capability_unavailable_and_evaluate_alternate_derivatives_testnet_no_order_v1/20260810T143709Z/) | OKX EEA Demo path closeout &#47; no-order alternate evaluation (non-activating) |
| [`evidence&#47;ops&#47;section_11_12_8_okx_global_demo_venue_host_account_instrument_binding_v1&#47;20260810T151323Z&#47;`](../../evidence/ops/section_11_12_8_okx_global_demo_venue_host_account_instrument_binding_v1/20260810T151323Z/) | Historical OKX Global Demo binding package evidence (NO_ORDER; not active) |
| [`evidence&#47;ops&#47;section_11_12_8_retry_okx_eea_private_ro_xperp_verify_no_order_v1&#47;20260810T165847Z&#47;`](../../evidence/ops/section_11_12_8_retry_okx_eea_private_ro_xperp_verify_no_order_v1/20260810T165847Z/) | Bound private READ-only XPerp capability proof (NO_ORDER) |
| [`evidence&#47;ops&#47;section_11_12_8_okx_eea_demo_xperp_venue_host_account_instrument_binding_v1&#47;20260810T171225Z&#47;`](../../evidence/ops/section_11_12_8_okx_eea_demo_xperp_venue_host_account_instrument_binding_v1/20260810T171225Z/) | Active OKX EEA Demo XPerp binding package evidence (NO_ORDER) |

```text
THIS_SECTION_DEFINES_NO_SEMANTICS=true
SECTION_11_12_8_CLOSED=true
SECTION_11_13_STARTED=false
LIVE_AUTHORIZED=false
PRE_LIVE_CYBERSECURITY_GATE=NOT_PASSED
SECTION_11_12_9_EVALUATION_COMPLETED=true
SECTION_11_12_9_GATE_PASS=false
ELIGIBLE_FOR_LIVE_READINESS_EVALUATION=false
OKX_EEA_DEMO_PRODUCTIVE_ORDER_PATH_STATUS=CLOSED_EXTERNAL_CAPABILITY_UNAVAILABLE
OKX_GLOBAL_DEMO_BINDING_PACKAGE_STATUS=PREPARED_NO_ORDER_NOT_ACTIVATED_SUPERSEDED_BY_SECTION_11_12_8_5
OKX_EEA_DEMO_XPERP_BINDING_PACKAGE_STATUS=PREPARED_NO_ORDER_ACTIVE_BINDING
SECTION_11_12_8_STATUS=CLOSED_OKX_EEA_DEMO_XPERP_BOUNDED_CAMPAIGN_AND_CLEAN_CLOSEOUT_PROVEN
CANONICAL_ACTIVE_VENUE_BINDING=OKX_EEA_DEMO
CANONICAL_ACTIVE_HOST_BINDING=https://eea.okx.com
CANONICAL_ACTIVE_INSTRUMENT=BTC-USD_UM_XPERP-310328
CANONICAL_ACTIVE_INSTRUMENT_TYPE=FUTURES
CANONICAL_ACTIVE_RULE_TYPE=xperp
BTC_USDT_SWAP_PATH_STATUS=CLOSED_DEPRECATED_HISTORICAL_EVIDENCE_ONLY
BTC-USD_UM_XPERP-310328=ONLY_ACTIVE_SECTION_11_12_8_DERIVATIVES_CAMPAIGN_PATH
ACTIVE_SECTION_11_12_8_DERIVATIVES_CAMPAIGN_PATH=OKX_EEA_DEMO_XPERP
LEGACY_BTC_USDT_SWAP_ACTIVE_BINDING_REMOVED=true
OKX_GLOBAL_DEMO_ACTIVE_BINDING=false
PACKAGE_DEFAULT_ORDER_POST_AUTHORIZED=false
SWAP_RUNTIME_FALLBACK=false
SWAP_WRITE_AUTHORIZATION=false
XPERP_ONLY_ACTIVE_WRITE_SCOPE=true
CAMPAIGN_EXECUTION_PASS=true
CLORDID_HYPHEN_DEFECT_CLOSED=true
CANCEL_INSTID_DEFECT_CLOSED=true
ORDER_ACK_PROVEN=true
CLEAN_CLOSEOUT_PROOF_PASS=true
SECTION_11_12_8_CLOSEOUT_RECOMMENDED=false
ORDER_LIFECYCLE_PROOF_PASS=true
CAP_11_12_TESTNET_PROGRAM_CLOSED=false
TESTNET_ORDER_LIFECYCLE_PROVEN=true
TESTNET_RECONCILIATION_PROVEN=true
TESTNET_RESTART_PROVEN=true
TESTNET_UNKNOWN_SUBMIT_RECOVERY_PROVEN=true
TESTNET_DUPLICATE_ORDER_PREVENTION_PROVEN=true
TESTNET_KILL_SWITCH_PROVEN=true
LONG_RUNNING_TESTNET_PROVEN=false
SECTION_11_12_1_RESIDUAL_PROOF_PASS=true
SECTION_11_12_1_RESIDUAL_BOUND=true
SECTION_11_12_2_RESIDUAL_PROOF_PASS=true
SECTION_11_12_2_RESIDUAL_BOUND=true
SECTION_11_12_3_RESIDUAL_PROOF_PASS=true
SECTION_11_12_3_RESIDUAL_BOUND=true
SECTION_11_12_4_RESIDUAL_PROOF_PASS=true
SECTION_11_12_4_RESIDUAL_BOUND=true
SECTION_11_12_5_RESIDUAL_PROOF_PASS=true
SECTION_11_12_5_RESIDUAL_BOUND=true
SECTION_11_12_6_RESIDUAL_PROOF_PASS=true
SECTION_11_12_6_RESIDUAL_BOUND=true
SECTION_11_12_7_RESIDUAL_PROOF_PASS=true
SECTION_11_12_7_RESIDUAL_BOUND=true
SECTION_11_12_8_RESIDUAL_PROOF_PASS=true
SECTION_11_12_8_RESIDUAL_BOUND=true
SECTION_11_12_9_11_RESIDUAL_PROOF_PASS=true
SECTION_11_12_9_11_RESIDUAL_BOUND=true
SECTION_11_12_9_12_PROOF_PASS=true
SECTION_11_12_9_12_PROOF_BOUND=true
SECTION_11_12_9_13_PROOF_PASS=true
SECTION_11_12_9_13_PROOF_BOUND=true
SECTION_11_12_9_14_PROOF_PASS=true
SECTION_11_12_9_14_PROOF_BOUND=true
SECTION_11_12_9_15_PROOF_PASS=true
SECTION_11_12_9_15_PROOF_BOUND=true
SECTION_11_12_9_16_PROOF_PASS=true
SECTION_11_12_9_16_PROOF_BOUND=true
SECTION_11_12_9_17_PROOF_PASS=true
SECTION_11_12_9_17_PROOF_BOUND=true
PREVIOUS_REPORTING_INCONSISTENCY_RECONCILED=true
OPEN_LIST_MEMBERSHIP_IMPLIES_PROVEN=false
TESTNET_EVIDENCE_VERIFIED=false
EARLIEST_OPEN_TESTNET_PROVEN_FIELD=TESTNET_AUTONOMOUS_RECOVERY_PROVEN
EARLIEST_UNRESOLVED_DEPENDENCY=CAP_11_12_TESTNET_PROGRESSION_PROGRAM_OPEN_TESTNET_PROVEN_FIELDS
EARLIEST_UNRESOLVED_SECTION_POINTER=OPEN_TESTNET_PROVEN_FIELDS
NEXT_CANONICAL_STEP_POINTER=OWNER_GO_PRODUCTIVE_TESTNET_AUTONOMOUS_RECOVERY_PROVEN_REQUIRED
XPERP_BOUNDED_CAMPAIGN_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_12_8_bounded_okx_eea_demo_xperp_campaign_execute_v1&#47;20260810T181703Z&#47;
XPERP_BOUNDED_CAMPAIGN_FORENSIC_POINTER=evidence&#47;ops&#47;section_11_12_8_bounded_okx_eea_demo_xperp_campaign_execute_v1&#47;20260810T181703Z&#47;derived_forensic_closeout_v1&#47;
XPERP_BOUNDED_ACK_PROOF_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_12_8_retry_bounded_okx_eea_demo_xperp_ack_proof_after_clordid_fix_v1&#47;20260810T194806Z&#47;
XPERP_BOUNDED_CLEAN_CLOSEOUT_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_12_8_retry_bounded_okx_eea_demo_xperp_clean_closeout_after_cancel_instid_fix_v1&#47;20260810T200151Z&#47;
XPERP_SECTION_11_12_8_CLOSEOUT_PACKAGE_POINTER=evidence&#47;ops&#47;section_11_12_8_closeout_package_v1&#47;20260810T201332Z&#47;
SECTION_11_12_9_EVALUATION_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_12_9_pre_live_cybersecurity_acceptance_gate_evidence_bound_evaluation_v1&#47;20260810T202800Z&#47;
SECTION_11_12_9_2_NOMENCLATURE_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_12_9_2_cap_11_12_testnet_program_nomenclature_reconcile_v1&#47;20260810T205051Z&#47;
SECTION_11_12_1_RESIDUAL_PROOF_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_12_1_cap_11_12_testnet_progression_residual_proof_v1&#47;20260810T211204Z&#47;
SECTION_11_12_2_RESIDUAL_PROOF_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_12_2_cap_11_12_testnet_progression_residual_proof_v1&#47;20260810T211449Z&#47;
SECTION_11_12_3_RESIDUAL_PROOF_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_12_3_cap_11_12_testnet_progression_residual_proof_v1&#47;20260810T211709Z&#47;
SECTION_11_12_4_RESIDUAL_PROOF_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_12_4_cap_11_12_testnet_progression_residual_proof_v1&#47;20260810T211915Z&#47;
SECTION_11_12_5_RESIDUAL_PROOF_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_12_5_cap_11_12_testnet_progression_residual_proof_v1&#47;20260810T212119Z&#47;
SECTION_11_12_6_RESIDUAL_PROOF_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_12_6_cap_11_12_testnet_progression_residual_proof_v1&#47;20260810T212326Z&#47;
SECTION_11_12_7_RESIDUAL_PROOF_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_12_7_cap_11_12_testnet_progression_residual_proof_v1&#47;20260810T212535Z&#47;
SECTION_11_12_8_RESIDUAL_PROOF_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_12_8_cap_11_12_testnet_progression_residual_proof_v1&#47;20260810T212942Z&#47;
SECTION_11_12_9_11_RESIDUAL_PROOF_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_12_9_11_open_testnet_proven_fields_reporting_reconcile_residual_proof_v1&#47;20260810T213441Z&#47;
SECTION_11_12_9_12_PROOF_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_12_testnet_order_lifecycle_proven_v1&#47;20260810T215942Z&#47;
SECTION_11_12_9_13_PROOF_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_12_testnet_reconciliation_proven_v1&#47;20260810T221902Z&#47;
SECTION_11_12_9_14_PROOF_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_12_testnet_restart_proven_v1&#47;20260810T223606Z&#47;
SECTION_11_12_9_15_PROOF_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_12_testnet_unknown_submit_recovery_proven_v1&#47;20260810T224947Z&#47;
SECTION_11_12_9_16_PROOF_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_12_testnet_duplicate_order_prevention_proven_v1&#47;20260810T230257Z&#47;
SECTION_11_12_9_17_PROOF_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_12_testnet_kill_switch_proven_v1&#47;20260810T232151Z&#47;
PREDECESSOR_GET_PROOF_IS_NOT_TARGETED_TRADE_PROOF=true
PREDECESSOR_ORDERLESS_GET_PROOF_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_12_8_autonomous_okx_eea_demo_credential_ip_resolve_v1&#47;20260808T203507Z&#47;
XPERP_PRIVATE_RO_PROOF_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_12_8_retry_okx_eea_private_ro_xperp_verify_no_order_v1&#47;20260810T165847Z&#47;
ALTERNATE_EVALUATION_IS_NOT_VENUE_ACTIVATION=true
BINDING_PACKAGE_IS_NOT_VENUE_ACTIVATION=true
WRITE_PATH_WIRED_IS_NOT_CAMPAIGN_STARTED=true
CAMPAIGN_EXECUTION_PASS_IS_NOT_SECTION_CLOSE=true
HISTORICAL_GLOBAL_OR_SWAP_EVIDENCE_IS_NOT_ACTIVE_BINDING=true
NO_PARALLEL_ACTIVE_SWAP_NAVIGATION=true
FURTHER_OKX_EEA_DEMO_ORDER_POSTS_AUTHORIZED_SWAP_PATH_ONLY=true
SECTION_11_12_9_EVALUATION_COMPLETED_IS_NOT_GATE_PASS=true
SECTION_11_12_1_RESIDUAL_PROOF_PASS_IS_NOT_TESTNET_ORDER_LIFECYCLE_PROVEN=true
SECTION_11_12_1_RESIDUAL_BOUND_IS_NOT_CAP_11_12_TESTNET_PROGRAM_CLOSED=true
SECTION_11_12_2_RESIDUAL_PROOF_PASS_IS_NOT_TESTNET_ORDER_LIFECYCLE_PROVEN=true
SECTION_11_12_2_RESIDUAL_BOUND_IS_NOT_CAP_11_12_TESTNET_PROGRAM_CLOSED=true
SECTION_11_12_3_RESIDUAL_PROOF_PASS_IS_NOT_TESTNET_ORDER_LIFECYCLE_PROVEN=true
SECTION_11_12_3_RESIDUAL_BOUND_IS_NOT_CAP_11_12_TESTNET_PROGRAM_CLOSED=true
SECTION_11_12_4_RESIDUAL_PROOF_PASS_IS_NOT_TESTNET_ORDER_LIFECYCLE_PROVEN=true
SECTION_11_12_4_RESIDUAL_BOUND_IS_NOT_CAP_11_12_TESTNET_PROGRAM_CLOSED=true
SECTION_11_12_5_RESIDUAL_PROOF_PASS_IS_NOT_TESTNET_UNKNOWN_SUBMIT_RECOVERY_PROVEN=true
SECTION_11_12_5_RESIDUAL_BOUND_IS_NOT_CAP_11_12_TESTNET_PROGRAM_CLOSED=true
SECTION_11_12_6_RESIDUAL_PROOF_PASS_IS_NOT_TESTNET_RESTART_PROVEN=true
SECTION_11_12_6_RESIDUAL_BOUND_IS_NOT_CAP_11_12_TESTNET_PROGRAM_CLOSED=true
SECTION_11_12_7_RESIDUAL_PROOF_PASS_IS_NOT_TESTNET_KILL_SWITCH_PROVEN=true
SECTION_11_12_7_RESIDUAL_BOUND_IS_NOT_CAP_11_12_TESTNET_PROGRAM_CLOSED=true
SECTION_11_12_8_RESIDUAL_PROOF_PASS_IS_NOT_TESTNET_EVIDENCE_VERIFIED=true
SECTION_11_12_8_RESIDUAL_BOUND_IS_NOT_CAP_11_12_TESTNET_PROGRAM_CLOSED=true
OPEN_TESTNET_PROVEN_FIELDS_MEMBERSHIP_IS_NOT_PROVEN=true
TESTNET_EVIDENCE_VERIFIED_IN_OPEN_LIST_IS_NOT_TESTNET_EVIDENCE_VERIFIED_TRUE=true
SECTION_11_12_9_11_RESIDUAL_PROOF_PASS_IS_NOT_TESTNET_ORDER_LIFECYCLE_PROVEN=true
SECTION_11_12_9_11_RESIDUAL_BOUND_IS_NOT_CAP_11_12_TESTNET_PROGRAM_CLOSED=true
SECTION_11_12_9_12_PROOF_PASS_IS_NOT_TESTNET_RECONCILIATION_PROVEN=true
SECTION_11_12_9_12_PROOF_BOUND_IS_NOT_CAP_11_12_TESTNET_PROGRAM_CLOSED=true
SECTION_11_12_9_13_PROOF_PASS_IS_NOT_TESTNET_RESTART_PROVEN=true
SECTION_11_12_9_13_PROOF_BOUND_IS_NOT_CAP_11_12_TESTNET_PROGRAM_CLOSED=true
SECTION_11_12_9_14_PROOF_PASS_IS_NOT_TESTNET_UNKNOWN_SUBMIT_RECOVERY_PROVEN=true
SECTION_11_12_9_14_PROOF_BOUND_IS_NOT_CAP_11_12_TESTNET_PROGRAM_CLOSED=true
SECTION_11_12_9_15_PROOF_PASS_IS_NOT_TESTNET_DUPLICATE_ORDER_PREVENTION_PROVEN=true
SECTION_11_12_9_15_PROOF_BOUND_IS_NOT_CAP_11_12_TESTNET_PROGRAM_CLOSED=true
SECTION_11_12_9_16_PROOF_PASS_IS_NOT_TESTNET_KILL_SWITCH_PROVEN=true
SECTION_11_12_9_16_PROOF_BOUND_IS_NOT_CAP_11_12_TESTNET_PROGRAM_CLOSED=true
SECTION_11_12_9_17_PROOF_PASS_IS_NOT_TESTNET_AUTONOMOUS_RECOVERY_PROVEN=true
SECTION_11_12_9_17_PROOF_BOUND_IS_NOT_CAP_11_12_TESTNET_PROGRAM_CLOSED=true
OPEN_RESIDUAL_LATENT_OKX_BOUND_CLIENT_SIGN_REQUEST_PATH_OMITS_QUERY_STRING=true
OPEN_RESIDUAL_PERMANENT_BOUND_CLIENT_QUERY_SIGN_FIX_IN_THIS_BINDING=false
OPEN_RESIDUAL_DOES_NOT_BLOCK_TESTNET_RECONCILIATION_PROVEN=true
OPEN_RESIDUAL_DOES_NOT_BLOCK_TESTNET_RESTART_PROVEN=true
OPEN_RESIDUAL_DOES_NOT_BLOCK_TESTNET_UNKNOWN_SUBMIT_RECOVERY_PROVEN=true
OPEN_RESIDUAL_DOES_NOT_BLOCK_TESTNET_DUPLICATE_ORDER_PREVENTION_PROVEN=true
OPEN_RESIDUAL_DOES_NOT_BLOCK_TESTNET_KILL_SWITCH_PROVEN=true
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
