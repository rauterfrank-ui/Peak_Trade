# Bounded Pilot Live Order Execution — Decision Package

status: DRAFT
last_updated: 2026-03-14
owner: Peak_Trade
purpose: Structure the governance decision for live_order_execution in the bounded pilot context
docs_token: DOCS_TOKEN_BOUNDED_PILOT_LIVE_ORDER_EXECUTION_DECISION_PACKAGE

---

## 1. Summary

This document structures the **governance decision** for enabling `live_order_execution` in the context of the **bounded real-money pilot** only. It does **not** make the decision; it provides the package for decision-makers.

**Reference:** `docs/GO_NO_GO_2026_LIVE_ALERTS_CLUSTER_82_85.md` §4 — Live-Order-Execution requires a separate Go/No-Go process.

**Scope:** Bounded pilot = one strictly operator-supervised session, bounded by caps, kill switch explicit, NO_TRADE on ambiguity. **Not** general live trading.

---

## 2. Current State

| Element | Status |
|---------|--------|
| `live_order_execution` | `locked` (src/governance/go_no_go.py) |
| `live_alerts_cluster_82_85` | `approved_2026` |
| Bounded pilot gate wrapper | Implemented (run_bounded_pilot_session.py) |
| First live session start | Not implemented (blockers B1–B6) |

**B2 (Governance)** is the central prerequisite: without approval of `live_order_execution` for bounded pilot, the technical chain remains blocked.

---

## 3. Inputs

| # | Input | Source |
|---|-------|--------|
| I1 | Entry Contract (Pre-Entry, Abort) | `docs/ops/specs/BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md` |
| I2 | Gap Note (Blockers B1–B6) | `docs/ops/specs/BOUNDED_PILOT_LIVE_ENTRY_GAP_NOTE.md` |
| I3 | Gate Wrapper | `scripts/ops/run_bounded_pilot_session.py` |
| I4 | Pilot Go/No-Go Checklist | `docs/ops/specs/PILOT_GO_NO_GO_OPERATIONAL_SLICE.md` |
| I5 | Treasury Separation | `docs/ops/specs/TREASURY_BALANCE_SEPARATION_SPEC.md` |
| I6 | Incident Runbooks | `RUNBOOK_PILOT_INCIDENT_*` |
| I7 | GO_NO_GO_2026 | `docs/GO_NO_GO_2026_LIVE_ALERTS_CLUSTER_82_85.md` |
| I8 | Audit GO_NO_GO | `docs/audit/GO_NO_GO.md` |

---

## 4. Criteria (from Entry Contract)

**Entry Posture (§2):**
- operator-supervised posture explicit
- dry validation completed
- pilot go/no-go acceptable
- bounded caps explicit
- treasury separation explicit
- ambiguity posture NO_TRADE
- incident / abort posture explicit

**Pre-Entry Prerequisites (§3):**
1. Dry Validation (Drills, Go/No-Go, Session Dry-Run)
2. Go/No-Go = GO_FOR_NEXT_PHASE_ONLY
3. human_supervision_state.status == operator_supervised
4. Policy/Operator/Incident Surfaces acceptable
5. exposure_state.caps_configured present
6. guard_state.treasury_separation == enforced

**Abort Criteria (§5):**
- go/no-go != GO_FOR_NEXT_PHASE_ONLY
- kill switch active
- policy blocked
- stale state unresolved
- session-end mismatch
- transfer ambiguity
- evidence/dependency degraded
- operator cannot determine posture
- any ambiguity about trading

---

## 5. Options

### Option A: New Feature-Key `live_order_execution_bounded_pilot`

| Aspect | Description |
|--------|-------------|
| Change | `_FEATURE_STATUS_MAP["live_order_execution_bounded_pilot"] = "approved_2026"` |
| `live_order_execution` | Remains `locked` |
| Pro | Clear separation from general live |
| Con | ExecutionPipeline must check new key |

### Option B: New Status `approved_bounded_pilot_2026`

| Aspect | Description |
|--------|-------------|
| Change | Extend GovernanceStatus; `live_order_execution = "approved_bounded_pilot_2026"` |
| Pro | Single key, specific status |
| Con | `is_feature_approved_for_year` semantics to define |

### Option C: `live_order_execution` → `approved_2026`

| Aspect | Description |
|--------|-------------|
| Change | `_FEATURE_STATUS_MAP["live_order_execution"] = "approved_2026"` |
| Pro | Minimal code change |
| Con | General approval; scope only via Entry Contract + gates |
| Risk | Misinterpretation: "live approved" vs "bounded pilot only" |

---

## 6. Recommendation (from Review)

**Option A** preferred for clear separation. `live_order_execution` stays locked; bounded pilot uses a dedicated key.

---

## 7. After Decision — Technical Dependencies

| # | Dependency | Blocker | Priority |
|---|--------------|---------|----------|
| 1 | Governance status changed | B2 | P0 |
| 2 | LiveSessionRunner mode=bounded_pilot | B1 | P1 |
| 3 | run_execution_session --mode bounded_pilot | B3 | P1 |
| 4 | EnvironmentConfig for bounded pilot | B4 | P1 |
| 5 | Kraken Live Client in flow | B5 | P2 |
| 6 | run_bounded_pilot_session invokes session starter | B6 | P1 |

**Order:** Governance (1) → Runner/Mode (2–4) → Wrapper invocation (6). B5 can be parallel or later.

---

## 8. Exit Condition

When does the approval lapse? (To be defined by decision-makers; examples:)
- Violation of bounded caps
- Incident requiring escalation
- Operator revokes supervision
- Audit finding

---

## 9. Relationship

- Companion to: `GO_NO_GO_2026_LIVE_ALERTS_CLUSTER_82_85`
- Companion to: `BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT`
- Companion to: `BOUNDED_PILOT_LIVE_ENTRY_GAP_NOTE`
- Source: `bounded_pilot_live_governance_decision_package_review`

---

## 10. Non-Goals

- This document does not make the governance decision
- No code change
- No bypass of gates
