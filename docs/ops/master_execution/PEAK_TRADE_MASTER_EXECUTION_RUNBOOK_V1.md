---
CANONICAL_ACTIVE_REPO_RUNBOOK=true
RUNBOOK_ID=PEAK_TRADE_MASTER_EXECUTION_RUNBOOK_V1
RUNBOOK_VERSION=v1
OWNER=Frank Rauter
NON_AUTHORIZING=true
SOURCE_DURABLE_SNAPSHOT=/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/planning/peak_trade_master_execution_runbook_v1_20260626T233500Z
SOURCE_DURABLE_MANIFEST_VERIFY_RC=0
origin_main: 6c1c4855241d3e0acf0af7f5448c0b24b30c9397
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
| PROGRAM_PHASE | TARGET_ARCHITECTURE_COMPLETE_OPERATOR_REVIEW |
| CURRENT_MAJOR_PACKAGE | PACKAGE_A_NUMERICAL_TRUST_FOUNDATION (provisorisch) |
| CURRENT_STATUS | OPERATOR_REVIEW_REQUIRED |
| GO_GRANTED | false |
| IMPLEMENTATION_STARTED | false |
| CURRENT_RUN_ACTIVE | false |
| NEXT_ALLOWED_ACTION | COMPLETE_OPERATOR_REVIEW_AND_FINAL_SELECTION_OF_PACKAGE_A_NUMERICAL_TRUST_FOUNDATION |

Target Architecture ist im Masterplan abgeschlossen (`MANIFEST_VERIFY_RC=0`). Package A ist **provisorisch** — finales Operator-Review-Bundle fehlt.

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
| PACKAGE_A_NUMERICAL_TRUST_FOUNDATION | TRAIN_1 | **ACTIVE PROVISIONAL** — OPERATOR_REVIEW_REQUIRED |
| PACKAGE_B_RECONCILIATION_CANONICALIZATION | TRAIN_2 | Nach PACKAGE_A |
| PACKAGE_C_DOUBLE_PLAY_DYNAMIC_SCOPE_AND_STATE | TRAIN_3 | MUST_HAVE — INV-045/046 |
| PACKAGE_D_CAPITAL_SLOT_RATCHET | TRAIN_4 | Strategic core — INV-007 |
| PACKAGE_E_RISK_KILLSWITCH_OPERATIVE_COMPLETION | TRAIN_5 | INV-033/008 |
| PACKAGE_F_DURABLE_RUNTIME_EVIDENCE | TRAIN_6 | INV-016/005 |
| PACKAGE_G_BAYESIAN_EVIDENCE_READONLY_LAYER | TRAIN_7 | **PARKED** — INV-043 |
| PACKAGE_H_OPERATOR_VISIBILITY | TRAIN_9 | INV-011,042,044 |
| PACKAGE_I_RUNTIME_PROMOTION_AND_RECOVERY | TRAIN_8 | INV-005 after PACKAGE_A |
| PACKAGE_J_CI_SCALE_AND_RELIABILITY | TRAIN_11 | INV-012,047 |
| PACKAGE_K_AUTONOMY_GOVERNANCE | TRAIN_12 | INV-018,020 |

Wave-Reihenfolge: 1=A → 2=B → 3=A ext (INV-003 GO) → 4=C → 5=D → 6=E,F → 7+=G,K

### PACKAGE_A (provisorisch — nicht final)

- **Scope wenn final:** INV-021 + INV-048 (contracts/PnL owner/P1-P2 only)
- **Explizit ausgeschlossen:** INV-003 wiring, INV-005 testnet, Authority-Lift
- **GO_GRANTED:** false | **IMPLEMENTATION_STARTED:** false

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

### Vor Operator-Review Package A

- [ ] Masterplan Bundle gelesen (`MANIFEST_VERIFY_RC=0`)
- [ ] 12 Trains + 11 Packages verstanden
- [ ] Dynamic Scope, Capital Ratchet, Bayesian parked bestätigt
- [ ] Scope Package A: nur INV-021 + INV-048 (contracts)
- [ ] INV-003 wiring, INV-005 testnet, Authority-Lift ausgeschlossen
- [ ] Ops-Cockpit-Package-A (20260603) nicht verwechseln
- [ ] Kein GO erteilen in Review-Chat
- [ ] Durable Review-Bundle mit Operator-Entscheid planen

## 9. Evidence Index

| Bundle | Rolle |
|--------|-------|
| Masterplan `intent_preserving_target_architecture_capability_train_masterplan_v0_20260625T222345Z` | Target Architecture |
| Inventory `six_month_prepared_partial_unactivated_work_inventory_v0_20260625T214514Z` | 48 Items |
| PR-4563 Closeout | Letzter Merge-Nachweis |
| Runbook Durable Snapshot `peak_trade_master_execution_runbook_v1_20260626T233500Z` | Unveränderlicher Ursprung |

## 10. DO_NOT_DO (aktuell)

- Implementierung, PR, CI, Run starten
- GO erteilen oder inferieren
- Primären dirty Worktree mutieren
- INV-003 wiring / INV-005 testnet ohne separates GO
- Provisorisches Package A als final behandeln
- Parallele Runbook-/Checkpoint-SSOTs erzeugen

## 11. Upstream-Referenzen

- Masterplan: `/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/planning/intent_preserving_target_architecture_capability_train_masterplan_v0_20260625T222345Z`
- Durable Runbook Snapshot: `/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/planning/peak_trade_master_execution_runbook_v1_20260626T233500Z`
- Runbooks-Index: [`docs/ops/RUNBOOK_INDEX.md`](../RUNBOOK_INDEX.md)
