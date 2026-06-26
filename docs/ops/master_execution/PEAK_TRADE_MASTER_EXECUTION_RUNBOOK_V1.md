---
CANONICAL_ACTIVE_REPO_RUNBOOK=true
RUNBOOK_ID=PEAK_TRADE_MASTER_EXECUTION_RUNBOOK_V1
RUNBOOK_VERSION=v1
OWNER=Frank Rauter
NON_AUTHORIZING=true
SOURCE_DURABLE_SNAPSHOT=/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/planning/peak_trade_master_execution_runbook_v1_20260626T233500Z
SOURCE_DURABLE_MANIFEST_VERIFY_RC=0
origin_main: 6b529f19c71c23967636fe398a320ed611285d96
---

# Peak_Trade Master Execution Runbook v1

Kanonischer **aktiver** Repo-Owner für Programm-Wiederaufnahme, Current State und Resume.

Maschinenlesbarer State: [`CURRENT_CHECKPOINT.env`](CURRENT_CHECKPOINT.env)  
Append-only Changelog: [`RUNBOOK_CHANGELOG.csv`](RUNBOOK_CHANGELOG.csv)

## Owner-Rollen (verbindlich)

| Rolle | Pfad / Artefakt |
|-------|-----------------|
| **CANONICAL_ACTIVE_RUNBOOK_OWNER** | Dieses Repo-Dokument + Checkpoint + Changelog unter `docs/ops/master_execution/` |
| **IMMUTABLE_VERIFIED_ORIGIN_SNAPSHOT** | Durable Bundle `peak_trade_master_execution_runbook_v1_20260626T233500Z` (`MANIFEST_VERIFY_RC=0`) — **unverändert** |
| **NON_CANONICAL_CONVENIENCE_COPY** | `/Users/frnkhrz/Desktop/Peak_Trade_Master_Execution_Runbook_V1.md` — Lesekopie, **nicht** kanonisch |

- Code, Contracts, Evidence-Bundles und PR-Closeouts bleiben **eigene fachliche Owner**.
- Dieses Runbook besitzt **keine** Trading-, Runtime-, Promotion- oder Live-Authority.
- `FUTURES_ONLY=true`, `BITCOIN_DIRECTION_ALLOWED=false`.

Ergänzende Runbook-Artefakte (State Machine, Resume Payloads, Safety Gates) verbleiben im **Durable Ursprungssnapshot** und im **Masterplan** — nicht duplizieren.

## 1. Langfristiges Ziel

Peak_Trade wird ein autonomes, selbstüberwachendes, adaptives, fail-closed, numerisch korrektes, auditierbares, kapitalbewusstes, reproduzierbares **Futures-only** Trading-System (Master V2 / Double Play als Integrationslogik).

Reifepipeline: Research → Offline Proof → Shadow → Paper → Testnet → streng gegated Live.

## 2. Aktueller Programmstand

| Feld | Wert |
|------|------|
| PROGRAM_PHASE | PACKAGE_C_IN_PROGRESS |
| CURRENT_MAJOR_PACKAGE | PACKAGE_C_DOUBLE_PLAY_DYNAMIC_SCOPE_AND_STATE (**IN_PROGRESS**) |
| CURRENT_STATUS | PACKAGE_C_C1_CLOSEOUT_COMPLETE |
| PACKAGE_A_STATUS | COMPLETE |
| PACKAGE_B_STATUS | COMPLETE |
| PACKAGE_B_FINAL_SELECTION_DECISION | PACKAGE_B_FINAL_SELECTED_WITH_BOUNDED_SCOPE_CORRECTION |
| PACKAGE_B_INCLUDED_INVENTORY_IDS | INV-022, INV-006 |
| PACKAGE_B_SLICE_B1_STATUS | MERGED_CLOSEOUT_COMPLETE |
| PACKAGE_B_SLICE_B2_STATUS | MERGED_CLOSEOUT_COMPLETE |
| PACKAGE_C_STARTED | true |
| PACKAGE_C_STATUS | IN_PROGRESS |
| C1_INV045_STATUS | COMPLETE |
| C2_INV046_STATUS | NOT_STARTED |
| PACKAGE_C_GO_GRANTED | false |
| GO_GRANTED | false |
| IMPLEMENTATION_STARTED | false |
| CURRENT_RUN_ACTIVE | false |
| NEXT_ALLOWED_ACTION | READ_ONLY_OPERATOR_REVIEW_FOR_PACKAGE_C_C2_INV046_SCOPE_NO_IMPLEMENTATION_NO_GO |

Target Architecture ist im Masterplan abgeschlossen (`MANIFEST_VERIFY_RC=0`). **Package A (INV-021 + INV-048) ist vollständig abgeschlossen**. **Package B (INV-022 + INV-006) ist vollständig abgeschlossen**. **Package C (INV-045 + INV-046) ist gestartet — C1 abgeschlossen, C2 nicht gestartet**; statische Contract-Formalisation only; **kein C2-GO, keine Runtime**.

## 3. Capability Trains (12)

| Train | Mission (Kurz) | Inventory-IDs | Schutz |
|-------|------------------|---------------|--------|
| TRAIN_1_NUMERICAL_TRUST | Decimal kernel, PnL SSOT, P1/P2 | INV-001,002,003,021,048 | Foundation |
| TRAIN_2_RECONCILIATION | Dual engines, PE-31/42 | INV-006,022,041 | Hard prereq TRAIN_8 |
| TRAIN_3_DOUBLE_PLAY | **Dynamic Scope + State Switch** | INV-045,046 | **MUST_HAVE** |
| TRAIN_4_CAPITAL | **Capital Ratchet** | INV-007 | **Strategic core** |
| TRAIN_5_RISK_KILLSWITCH | PE-22/43 operative | INV-008,033,037 | Safety |
| TRAIN_6_DURABLE_EVIDENCE | Six-node, completion | INV-004,015,016,017,023,030,034-040 | Hard prereq TRAIN_7,8 |
| TRAIN_7_BAYESIAN | Read-only confidence | INV-043 | **PARKED, no authority** |
| TRAIN_8_RUNTIME | Shadow/Paper/Testnet | INV-005,009,010,019,028 | After PACKAGE_A |
| TRAIN_9_OPERATOR_VISIBILITY | Cockpit, diagnostics | INV-011,025,026,027,042 | Read-only |
| TRAIN_10_CYBERSECURITY | Recovery visibility | INV-032,044 | No major package |
| TRAIN_11_CI | Selector, sharding | INV-012,029,047 | Cross-cut |
| TRAIN_12_STRATEGY_AUTONOMY | Go-live blockers, harness | INV-018,020,024,031 | Far downstream |

**Excluded by policy:** INV-013, INV-014. **48 Inventory-Positionen** abgedeckt (Masterplan `INTENT_TRUTH_INVENTORY.csv`).

## 4. Major Packages (11)

| Package | Train | Status / Hinweis |
|---------|-------|------------------|
| PACKAGE_A_NUMERICAL_TRUST_FOUNDATION | TRAIN_1 | **COMPLETE** — INV-021+048 gemergt; keine Produktions-Verdrahtung |
| PACKAGE_B_RECONCILIATION_CANONICALIZATION | TRAIN_2 | **COMPLETE** — INV-022+INV-006 gemergt; kein Package-C-GO |
| PACKAGE_C_DOUBLE_PLAY_DYNAMIC_SCOPE_AND_STATE | TRAIN_3 | **IN_PROGRESS** — C1 (INV-045) gemergt; C2 (INV-046) NOT_STARTED |
| PACKAGE_D_CAPITAL_SLOT_RATCHET | TRAIN_4 | Strategic core — INV-007 |
| PACKAGE_E_RISK_KILLSWITCH_OPERATIVE_COMPLETION | TRAIN_5 | INV-033/008 |
| PACKAGE_F_DURABLE_RUNTIME_EVIDENCE | TRAIN_6 | INV-016/005 |
| PACKAGE_G_BAYESIAN_EVIDENCE_READONLY_LAYER | TRAIN_7 | **PARKED** — INV-043 |
| PACKAGE_H_OPERATOR_VISIBILITY | TRAIN_9 | INV-011,042,044 |
| PACKAGE_I_RUNTIME_PROMOTION_AND_RECOVERY | TRAIN_8 | INV-005 after PACKAGE_A |
| PACKAGE_J_CI_SCALE_AND_RELIABILITY | TRAIN_11 | INV-012,047 |
| PACKAGE_K_AUTONOMY_GOVERNANCE | TRAIN_12 | INV-018,020 |

Wave-Reihenfolge: 1=A → 2=B → 3=A ext (INV-003 GO) → 4=C → 5=D → 6=E,F → 7+=G,K

### PACKAGE_A (final ausgewählt — vollständig abgeschlossen)

- **Entscheidung:** `PACKAGE_A_FINAL_SELECTED` (Operator-Review Bundle `package_a_numerical_trust_foundation_final_operator_review_v0_20260625T230158Z`, `MANIFEST_VERIFY_RC=0`)
- **Enthalten:** INV-021 (PnL-Owner-Design/Contract) + INV-048 (P1-3/P1-4/P1-5 Contract-Tests)
- **Slice-Status:**
  - **A1 (INV-021):** **MERGED** — PR #4566, Merge `f570e857`; kanonische Futures-PnL-Ownership-/Boundary-Contracts (test-only); keine Produktionsänderung
  - **A2 (INV-048):** **MERGED** — PR #4568, Merge `5495c8fb`; P1-3 flip, P1-4 quantize, P1-5 equity identity (test-only); keine Produktionsänderung
- **Explizit ausgeschlossen:** INV-003 wiring, INV-005 testnet, Authority-Lift, Runtime, produktive Arithmetic-Verdrahtung
- **GO_GRANTED:** false | **IMPLEMENTATION_STARTED:** false | **Package A abgeschlossen — kein Runtime-Proof**

### PACKAGE_B (final ausgewählt — vollständig abgeschlossen)

- **Entscheidung:** `PACKAGE_B_FINAL_SELECTED_WITH_BOUNDED_SCOPE_CORRECTION` (Operator-Review Bundle `package_b_reconciliation_canonicalization_final_operator_review_v0_20260626T000500Z`, `MANIFEST_VERIFY_RC=0`)
- **Titel:** Reconciliation Canonicalization
- **Enthalten:** INV-022 (Reconciliation Owner/Authority/Import-Grenzen) + INV-006 (PE-31 ↔ Durable-Completion-Binding)
- **Explizit ausgeschlossen:** INV-041 (absorbiert), Engine-Vereinheitlichung, produktives Reconciliation-Wiring, Runtime, Repair-Authority, Trading-/Promotion-Authority
- **Slice-Reihenfolge (verbindlich):**
  - **B1 (INV-022):** **MERGED** — PR #4571, Merge `ba4fa64e`; kanonische Reconciliation-Owner-Rollen, Authority- und Import-Grenzen via PR-#4561-Contract-Erweiterung (test-only); keine Produktionsänderung
  - **B2 (INV-006):** **MERGED** — PR #4575, Merge `c757c2af`; PE-31 ↔ Durable-Completion-Binding als statischer Canonical-Contract (test-only); CI: CONTRACT_FOCUSED / `durable_completion_focused`; 20 Manifest-Nodes, 22 CI-Targets; keine Produktionsänderung
- **Reuse-before-new:** bestehende Contract-Owner erweitert; keine parallele Reconciliation-SSOT
- **PACKAGE_B_STATUS:** COMPLETE | **PACKAGE_B_GO_GRANTED:** false | **kein Wiring, keine Runtime, keine Repair-Authority**

### PACKAGE_C (gestartet — C1 abgeschlossen, C2 nicht gestartet)

- **Operator-Review:** `package_c_double_play_dynamic_scope_state_operator_review_inv045_inv046_v0_20260626T040925Z`, `MANIFEST_VERIFY_RC=0`
- **Titel:** Double Play Dynamic Scope and State
- **Enthalten:** INV-045 (Dynamic Scope Owner/Authority/Import-Grenzen) + INV-046 (Bull/Bear State-Switch Owner/Authority/Import-Grenzen)
- **Explizit ausgeschlossen:** produktive Dynamic-Scope-/State-Switch-Verdrahtung, Runtime, Trading-/Promotion-Authority, parallele SSOTs
- **Slice-Reihenfolge (verbindlich):**
  - **C1 (INV-045):** **MERGED** — PR #4577, Squash `6b529f19`; kanonische Dynamic-Scope-Owner-/Authority-/Import-Boundary-Contracts (contract-only); CI: CONTRACT_FOCUSED / `dynamic_scope_owner_boundary_contract_focused`; keine Produktionsänderung; keine Runtime
  - **C2 (INV-046):** **NOT_STARTED** — nicht autorisiert; separates read-only Operator-Review erforderlich
- **Reuse-before-new:** bestehende Contract-Owner erweitert; keine parallele Dynamic-Scope-SSOT
- **PACKAGE_C_STATUS:** IN_PROGRESS | **C1_INV045_STATUS:** COMPLETE | **C2_INV046_STATUS:** NOT_STARTED | **PACKAGE_C_GO_GRANTED:** false | **kein C2-GO, keine Runtime**

## 5. State Machine (26 Zustände)

Fail-closed Guards — vollständige Definition im Durable Snapshot `PROGRAM_STATE_MACHINE.md`.

Verbotene Sprünge u.a.:
- DESIGN_COMPLETE → IMPLEMENTATION_IN_PROGRESS
- MERGED_CLOSEOUT_REQUIRED → nächstes Package
- Runtime ohne separates Runtime-GO

## 6. Global Entry / Exit Gates

Siehe Durable Snapshot: `GLOBAL_ENTRY_EXIT_GATES.md`, `SAFETY_AND_AUTHORITY_BOUNDARIES.md`.

`CI_HARD_TIMEOUT_MINUTES=25` (Diagnose-Trigger); operatives CI-Budget: 17 min (fast-lane/tests).

## 7. Resume Protocol

R1 Identität → R2 Checkpoint → R3 Drift → R4 Safe Continuation → R5 Update — siehe Durable Snapshot `RESUME_PROTOCOL.md`.

Handoff-Payloads: `NEW_CHAT_RESUME_PAYLOAD.md`, `CURSOR_RESUME_PAYLOAD.md` (Durable Snapshot).

## 8. Operator Checklist (aktuell)

### Nach Package-C-C1-Abschluss (aktuell)

- [x] Package A (INV-021 + INV-048) vollständig abgeschlossen
- [x] Package B (INV-022 + INV-006) vollständig abgeschlossen
- [x] Separates read-only Operator-Review für Package C abgeschlossen (`package_c_double_play_dynamic_scope_state_operator_review_inv045_inv046_v0_20260626T040925Z`)
- [x] Package-C-Slice C1 (INV-045) gemergt — PR #4577, Squash `6b529f19`; contract-only Dynamic-Scope-Owner-/Authority-/Import-Boundary
- [x] Fachliches C1-Closeout-Bundle mit `MANIFEST_VERIFY_RC=0`
- [x] Docs-Closeout-Checkpoint für C1 vorbereitet
- [ ] Separates read-only Operator-Review für Package-C-Slice C2 (INV-046) — **nicht gestartet**
- [ ] C2 (INV-046) — **nicht autorisiert**
- [ ] INV-003 wiring, INV-005 testnet, Authority-Lift, Runtime, Engine-Vereinheitlichung, Reconciliation-Wiring weiterhin ausgeschlossen

## 9. Evidence Index

| Bundle | Rolle |
|--------|-------|
| Masterplan `intent_preserving_target_architecture_capability_train_masterplan_v0_20260625T222345Z` | Target Architecture |
| Inventory `six_month_prepared_partial_unactivated_work_inventory_v0_20260625T214514Z` | 48 Items |
| PR-4563 Closeout | Arithmetic conversion implementation |
| PR-4564 Closeout | Kanonischer Runbook-Owner in Repo |
| Operator-Review `package_a_numerical_trust_foundation_final_operator_review_v0_20260625T230158Z` | Finale Package-A-Auswahl |
| A1 Implementation `package_a_slice_a1_inv021_pnl_owner_contract_formalisation_v0_20260625T232429Z` | INV-021 Contract-Formalisation |
| A2 Implementation `package_a_slice_a2_inv048_p1_arithmetic_contracts_v0_20260625T234736Z` | INV-048 P1 Contract-Closure |
| PR-4566 Closeout | Package A Slice A1 merge |
| PR-4568 / A2 Professor Merge Closeout | Package A Slice A2 merge |
| PR-4569 Closeout | Package A complete checkpoint |
| Operator-Review `package_b_reconciliation_canonicalization_final_operator_review_v0_20260626T000500Z` | Finale Package-B-Auswahl |
| B1 Implementation `package_b_slice_b1_inv022_reconciliation_owner_boundaries_implementation_v0_20260626T002429Z` | INV-022 Contract-Formalisation |
| PR-4571 Merge | Package B Slice B1 merge |
| B2 Implementation `package_b_slice_b2_inv006_pe31_durable_completion_canonical_binding_v2_20260626T024158Z` | INV-006 PE-31 Binding |
| PR-4575 Closeout `pr4575_package_b_b2_inv006_pe31_durable_completion_closeout_v0_20260626T034210Z` | Package B Slice B2 merge closeout |
| PR-4575 Merge | Package B Slice B2 merge |
| Operator-Review `package_c_double_play_dynamic_scope_state_operator_review_inv045_inv046_v0_20260626T040925Z` | Finale Package-C-Auswahl |
| C1 Implementation `package_c_slice_c1_inv045_dynamic_scope_owner_boundaries_v0_20260626T061200Z` | INV-045 Contract-Formalisation |
| PR-4577 Closeout `pr4577_package_c_c1_inv045_merge_closeout_v0_20260626T062800Z` | Package C Slice C1 merge closeout |
| PR-4577 Merge | Package C Slice C1 merge |
| Runbook Durable Snapshot `peak_trade_master_execution_runbook_v1_20260626T233500Z` | Unveränderlicher Ursprung |

## 10. DO_NOT_DO (aktuell)

- C2 (INV-046) ohne separates read-only Operator-Review und explizites GO
- GO erteilen oder inferieren (insbesondere C2-GO oder Package-C-GO)
- Engine-Vereinheitlichung, produktives Reconciliation-Wiring, Repair-Authority
- Runtime, Testnet, Paper, Shadow, Live starten
- Primären dirty Worktree mutieren
- INV-003 wiring / INV-005 testnet ohne separates GO
- Parallele Runbook-/Checkpoint-SSOTs erzeugen

## 11. Upstream-Referenzen

- Masterplan: `/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/planning/intent_preserving_target_architecture_capability_train_masterplan_v0_20260625T222345Z`
- Durable Runbook Snapshot: `/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/planning/peak_trade_master_execution_runbook_v1_20260626T233500Z`
- Runbooks-Index: [`docs/ops/RUNBOOK_INDEX.md`](../RUNBOOK_INDEX.md)
