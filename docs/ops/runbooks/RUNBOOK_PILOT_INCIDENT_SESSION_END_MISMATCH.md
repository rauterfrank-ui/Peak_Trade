# RUNBOOK — Pilot Incident: Session End Mismatch

status: OPERATOR-READY
last_updated: 2026-04-23
owner: Peak_Trade
purpose: Operator response when bounded-pilot session closeout or registry state disagrees with broker/exchange truth at or immediately after session end; fail-closed until classified, reconciled, or governance directs otherwise outside this document
docs_token: DOCS_TOKEN_RUNBOOK_PILOT_INCIDENT_SESSION_END_MISMATCH

## Non-authorization (read first)

This runbook is an **operator aid** only. It does **not**:

- authorize live trading, start the next session, close any gate, or waive Entry Contract §5;
- replace the [Entry Contract](../specs/BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md), governance decisions, or org kill-switch procedures;
- prove safety from read-only CLI output or in-repo documentation alone.

If there is **any** doubt whether trading is allowed, apply [Entry Contract §5](../specs/BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md#5-abort--rollback--no_trade-criteria): **ambiguity ⇒ `NO_TRADE` / safe stop**.

## A. Purpose and boundaries

**Use this runbook as the primary path when** the **dominant** problem is **closeout or session-boundary truth**: local or registry **session-end / closeout** views **do not align** with **broker/exchange** positions, balances, open orders, or fill history **at or right after** declared session end — including partial or conflicting terminal order/fill state **scoped to that boundary**. Symptom routing: [Abort triage compass §5.4](RUNBOOK_BOUNDED_PILOT_INCIDENT_ABORT_TRIAGE_COMPASS.md#54-session-end--closeout-disagreement).

**Prefer a different primary path when:**

- **Order/fill/position/balance disagreement** is the **first** job **during** the session **without** a narrow closeout-boundary story → [Reconciliation mismatch](RUNBOOK_PILOT_INCIDENT_RECONCILIATION_MISMATCH.md); **overlap is common** — if the **only** unresolved story is **terminal closeout vs broker**, keep **this** runbook as primary.
- **Venue path unhealthy** (timeouts, rejects, unstable acks) dominates **before** closeout can be read → [Exchange degraded](RUNBOOK_PILOT_INCIDENT_EXCHANGE_DEGRADED.md); hold **`NO_TRADE`** until venue reads are **classifiable** for closeout.
- **Observability / evidence continuity** gaps without a closeout-specific narrative → [Telemetry degraded](RUNBOOK_PILOT_INCIDENT_TELEMETRY_DEGRADED.md).
- **Cap or envelope surprise** is the main doubt → [Unexpected exposure](RUNBOOK_PILOT_INCIDENT_UNEXPECTED_EXPOSURE.md).
- **Transfer / funding** unknown → [Transfer ambiguity](RUNBOOK_PILOT_INCIDENT_TRANSFER_AMBIGUITY.md).
- **Process restart / cold local state** mid-session → [Restart mid-session](RUNBOOK_PILOT_INCIDENT_RESTART_MID_SESSION.md); closeout mismatch may **follow** once continuity is rebuilt.
- **Symptom routing** → [Abort triage compass](RUNBOOK_BOUNDED_PILOT_INCIDENT_ABORT_TRIAGE_COMPASS.md).

**Scope:** Bounded-pilot execution and **post-session closeout** only. This runbook does **not** define reconciliation algorithms, registry schema, or automated closeout behavior.

## B. Triggers and entry conditions

**Observable triggers (any can suffice)**

- **Local closeout or registry snapshot** (session summary, intended flat/risk-off posture) **disagrees** with **broker/exchange** positions, balances, or open orders **at session end**.
- **Reconciliation** at session end returns **partial** results, **timeouts**, or **conflicting** terminal states for orders or fills **at the boundary**.
- **Next bounded session** or **risk-increasing steps** would rely on closeout truth the operator **cannot** confirm.
- **Ambiguity** whether exposure is **flat**, **within envelope**, or **unknown** relative to the entry contract **after** closeout.

**Fail-closed rule**

- If closeout **cannot** be reconciled within a short, operator-defined window, treat as **`ambiguous`** (unresolved session-end mismatch per Entry Contract §5): **`NO_TRADE`** and **no** new bounded session until classification improves or governance directs otherwise **outside** this document.

## C. Immediate actions (ordered)

1. **Stop progression that assumes clean closeout:** **`NO_TRADE`** for **starting a new** bounded session or **new** risk-increasing actions on top of **unresolved** closeout. Use org **kill-switch / safe-stop** only per [Kill Switch runbook](../../risk/KILL_SWITCH_RUNBOOK.md); this runbook does not redefine that mechanism.
2. **Freeze the scene:** record **UTC interval**, **session id**, **operator**, and **mismatch domain** (positions vs registry, balances vs internal view, open orders vs expected flat, fill-history gaps — **category labels only** in external notes).
3. **Confirm bounded-pilot context:** re-anchor on [Entry Contract §1–2 and §4](../specs/BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md); do not exceed the first bounded real-money step intent.
4. **Gather broker-trusted truth:** use pilot-approved UI/API **read** paths; capture **non-secret** references (screenshot policy, ticket IDs) under change control — **no** raw dumps into the repository.
5. **Compare to local registry and closeout evidence trail:** align timestamps, session IDs, and order IDs **only** in external systems; if comparison **cannot** complete in bounded time, classify as **`ambiguous`**.
6. **Classify:** **`reconciled_explainable`** / **`partial`** / **`ambiguous`** (see §D).
7. If **`partial`** or **`ambiguous`**: **escalate** per §F; **do not** message “all clear” or “authorized to continue” from this runbook.

**Order matters:** **posture before** treating the session as complete for pilot purposes; **broker-trusted closeout** before **next session** narratives.

## D. Verification and classification

**Definitions**

- **Reconciled explainable:** a **single consistent** closeout story — broker-trusted positions, balances, and terminals **align** with registry/session-end views **or** any discrepancy is **fully explained** by a known, operator-trusted cause **without** residual exposure doubt — **still** no authorization from this document to start the next session.
- **Partial:** some legs or domains **confirmed**, others **missing**, **timeout**, or **unsettled** — **cannot** rely on full closeout for progression.
- **Ambiguous:** contradictory terminals, **unknown** flat/envelope state, or **cannot** complete verification in bounded time — **unsafe** to assume clean closeout.

**Suggested checks**

- Re-pull **broker-trusted** views; compare **stable identifiers** (order id, client id, fill id), not only aggregates.
- If cockpit/registry JSON or `scripts/report_live_sessions.py` outputs are used, treat as **read-only hints**; read **disclaimers**; JSON is **not** proof of safety (see [Compass §8](RUNBOOK_BOUNDED_PILOT_INCIDENT_ABORT_TRIAGE_COMPASS.md#8-read-only-cli--report-hints-scriptsreport_live_sessionspy)).
- If **venue** instability dominates, pivot triage context to [Exchange degraded](RUNBOOK_PILOT_INCIDENT_EXCHANGE_DEGRADED.md) while holding **`NO_TRADE`**.

**Return toward normal (non-authorizing)**

- **No** “next session OK” or “closeout resolved for governance” from this runbook alone after **`partial`** / **`ambiguous`**. **Only** governance or explicit org disposition **outside** this repo can authorize continuation.
- If **`reconciled_explainable`**, **next session** or **candidate** steps follow [Bounded real-money pilot candidate flow](RUNBOOK_BOUNDED_REAL_MONEY_PILOT_CANDIDATE_FLOW.md) and [Live entry](RUNBOOK_BOUNDED_PILOT_LIVE_ENTRY.md) only per **your** authorized procedures **outside** this document; posture still follows [Entry Contract §5](../specs/BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md#5-abort--rollback--no_trade-criteria) and [Failure taxonomy §6](../specs/MASTER_V2_FAILURE_TAXONOMY_SAFE_FALLBACKS_V1.md#6-ambiguity-confusion-and-interpretation-risk-map).

## E. Evidence and pointers (L5 discipline)

Capture review material **outside** git per [L5 incident / safe-stop pointer contract](../specs/MASTER_V2_BOUNDED_PILOT_L5_INCIDENT_SAFE_STOP_EVIDENCE_POINTER_CONTRACT_V0.md): **metadata and opaque handles only** — no full registry exports, complete fill logs, ticket bodies with live identifiers, or kill-switch dumps in the repository.

**Minimum narrative to record externally (conceptual)**

- **Trigger** (closeout symptom, first observation).
- **Mismatch domain** and **UTC window** at session boundary.
- **Broker-trusted vs local** summary (what aligned / what did not; identifiers only as appropriate).
- **Classification** (`reconciled_explainable` / `partial` / `ambiguous`).
- **Final posture** and **escalation** reference if any.

## F. Escalation

Escalate when **any** holds:

- Classification remains **`partial`** or **`ambiguous`** after bounded checks.
- **Session-end mismatch** remains **unresolved** per Entry Contract §5.
- **Policy / kill-switch** blocks progression while closeout is unsettled.

**Internal:** pilot owner / governance per bounded-pilot path; state **mismatch class**, **UTC window**, **session id**, and whether exposure is **known**, **partially known**, or **unknown**.

**External:** venue or broker support only per org rules; **no** secrets or unnecessary account identifiers in unsecured channels.

## G. Related runbooks

- [Reconciliation mismatch](RUNBOOK_PILOT_INCIDENT_RECONCILIATION_MISMATCH.md)
- [Exchange degraded](RUNBOOK_PILOT_INCIDENT_EXCHANGE_DEGRADED.md)
- [Telemetry degraded](RUNBOOK_PILOT_INCIDENT_TELEMETRY_DEGRADED.md)
- [Unexpected exposure](RUNBOOK_PILOT_INCIDENT_UNEXPECTED_EXPOSURE.md)
- [Transfer ambiguity](RUNBOOK_PILOT_INCIDENT_TRANSFER_AMBIGUITY.md)
- [Restart mid-session](RUNBOOK_PILOT_INCIDENT_RESTART_MID_SESSION.md)
- [Abort triage compass](RUNBOOK_BOUNDED_PILOT_INCIDENT_ABORT_TRIAGE_COMPASS.md)

**Design context (non-authorizing):** [Reconciliation flow spec](../specs/RECONCILIATION_FLOW_SPEC.md); [Pilot execution edge case matrix](../specs/PILOT_EXECUTION_EDGE_CASE_MATRIX.md); [Failure taxonomy](../specs/MASTER_V2_FAILURE_TAXONOMY_SAFE_FALLBACKS_V1.md) §4 / §6.
