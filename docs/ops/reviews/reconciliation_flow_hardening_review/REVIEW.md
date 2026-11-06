# RECONCILIATION FLOW HARDENING REVIEW

status: DRAFT
last_updated: 2026-03-20
owner: Peak_Trade
purpose: Docs-first review defining source-of-truth, mismatch taxonomy, operator-visible states, and safe handling under ambiguity
docs_token: DOCS_TOKEN_RECONCILIATION_FLOW_HARDENING_REVIEW

## Purpose
Review and consolidate reconciliation flow hardening definitions per the reconciliation_flow_hardening plan. This slice is docs-only; no runtime changes.

## Scope
- source-of-truth hierarchy
- mismatch categories
- operator-visible failure states
- safe behavior under ambiguity
- escalation / follow-up path

## Constraints
- no runtime mutation
- no paper/shadow/testnet disturbance
- no live-expansion work

---

## 1. Source-of-Truth Hierarchy

### Decision-Grade vs Informational
- **Decision-grade:** fields used to authorize or block trading, capacity, or exposure
- **Informational:** fields used for display, audit, or operator awareness only

### Hierarchy (highest to lowest)
1. **Reconciled local state** — after successful reconciliation, local ledger/position/balance state that matches external truth
2. **Broker/exchange order/fill/position state** — authoritative for what the venue reports
3. **Broker/exchange balance** — reported balance; not automatically decision-grade until reconciled
4. **Local evidence trail** — audit log, ledger entries; supports audit, not primary decision input
5. **Stale or unreconciled state** — never decision-grade; must not increase tradable capacity

### Balance-Specific
- Treasury balance ≠ available trading balance (per TREASURY_BALANCE_SEPARATION_SPEC_V2)
- Free balance vs reserved balance must not be collapsed
- Reported balance is not automatically reconciled; reconciliation logic defines which fields become decision-grade

---

## 2. Mismatch Taxonomy

### By Domain
| Domain | Mismatch Type | Example |
|--------|---------------|---------|
| Orders | order state divergence | local ACK vs exchange REJECTED |
| Fills | fill qty/price mismatch | local fill vs exchange fill history |
| Positions | position divergence | local position vs exchange position |
| Balances | balance divergence | local cash vs exchange reported balance |
| Transfers | transfer ambiguity | pending transfer state unclear |
| Session | session-end mismatch | closeout state inconsistent |

### By Severity
| Severity | Meaning | Posture |
|----------|---------|---------|
| **Informational** | divergence noted, no exposure impact | log; do not block if gates remain valid |
| **Operationally blocking** | exposure or capacity uncertain | NO_TRADE until resolved |
| **Ambiguous** | cannot determine truth | NO_TRADE; escalate |

### Classification
- **reconciled** — local and external state coherent; proceed only if gates valid
- **partially reconciled** — some domains OK, others uncertain; remain bounded; no new risk expansion
- **ambiguous** — truth unclear; NO_TRADE / safe stop
- **degraded dependency** — exchange/telemetry degraded; prefer NO_TRADE
- **operator escalation required** — block progression pending review

---

## 3. Operator-Visible Failure States

Operators must be able to see:

1. **Trigger** — what initiated reconciliation (order timeout, stale balance, session end, etc.)
2. **Truth sources consulted** — which broker/exchange/local sources were used
3. **Unresolved items** — what remains uncertain or divergent
4. **Current posture** — reconciled / partial / ambiguous / NO_TRADE
5. **Resume criteria** — what must be satisfied to resume

### Explicit States to Surface
- `RECONCILED` — all domains coherent; gates valid
- `PARTIAL` — some domains OK; bounded; no new risk
- `AMBIGUOUS` — NO_TRADE; escalation path
- `DEGRADED` — dependency degraded; prefer NO_TRADE
- `ESCALATION_REQUIRED` — blocked pending operator review

---

## 4. Safe Behavior Under Ambiguity

### Principles
- Fail toward safety under mismatch or ambiguity
- Do not increase usable capacity from uncertain data
- Preserve separation between treasury, free, reserved, and reconciled balances
- Make operator-visible states explicit

### Rules
- Unresolved ambiguity → NO_TRADE
- Stale critical state → NO_TRADE
- Degraded truth source with unknown exposure → NO_TRADE
- Missing evidence continuity → escalation and blocked progression
- When in doubt, reduce tradable capacity; never increase it from uncertain data

---

## 5. Escalation / Follow-Up Path

### Escalation Triggers
- ambiguous classification
- degraded dependency with unknown exposure
- evidence trail gap
- operator cannot answer: what triggered reconciliation, which truth sources, what remains unresolved, why posture is safe

### Follow-Up
- Record: trigger, observed divergence, truth sources, classification, operator escalation, final posture
- Resume only when: order/fill/position/balance coherent, no unresolved ambiguity, gates valid, evidence intact

### Recommended Next Slice
- treasury_balance_incident_runbook

---

## Relationship to Other Documents
- `docs/ops/specs/RECONCILIATION_FLOW_SPEC.md` — canonical flow
- `docs/ops/specs/TREASURY_BALANCE_SEPARATION_SPEC_V2.md` — balance boundaries
- `docs/ops/runbooks/RUNBOOK_PILOT_INCIDENT_RECONCILIATION_MISMATCH.md` — operator response
- `docs/ops/reviews/reconciliation_flow_hardening/PLAN.md` — hardening plan
