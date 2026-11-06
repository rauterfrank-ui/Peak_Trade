# RUNBOOK — Pilot Incident: Restart Mid-Session

status: OPERATOR-READY
last_updated: 2026-04-23
owner: Peak_Trade
purpose: Operator response when a process or operator continuity break occurs mid-session such that local execution state is cold, empty, or no longer trusted while broker or venue truth may still reflect active orders or positions; disciplined rebuild and classification before any further risk-increasing action
docs_token: DOCS_TOKEN_RUNBOOK_PILOT_INCIDENT_RESTART_MID_SESSION

## Non-authorization (read first)

This runbook is an **operator aid** only. It does **not**:

- authorize live trading, resume a session, or close any gate;
- replace the [Entry Contract](../specs/BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md), governance decisions, or org kill-switch procedures;
- prove safety from read-only CLI output or in-repo documentation alone.

If there is **any** doubt whether trading is allowed, apply [Entry Contract §5](../specs/BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md#5-abort--rollback--no_trade-criteria): **ambiguity ⇒ `NO_TRADE` / safe stop**.

## A. Purpose and boundaries

**Use this runbook as the primary path when** a **mid-session restart or continuity break** is the **dominant** narrative: the execution/session process **restarted or crashed**, or the operator must **cold-start** trust in local runtime state, and **local ledgers or in-memory views are empty, reset, or inconsistent** on the new process while **venue truth may still hold open orders, positions, or recent fills**. Symptom routing for this class: [Abort triage compass §5.7](RUNBOOK_BOUNDED_PILOT_INCIDENT_ABORT_TRIAGE_COMPASS.md#57-mid-session-restart--continuity-break).

**Prefer a different primary path when:**

- **Systematic ledger disagreement** without a restart/cold-start story is the **first** job → [Reconciliation mismatch](RUNBOOK_PILOT_INCIDENT_RECONCILIATION_MISMATCH.md); you may **use that runbook’s steps** once venue and local trails are gathered — restart remains the **Compass §5.7** entry framing.
- **Closeout / session-end** terminal disagreement → [Session end mismatch](RUNBOOK_PILOT_INCIDENT_SESSION_END_MISMATCH.md).
- **Venue or broker API** instability (timeouts, rejects, rate limits) is the **main** failure mode → [Exchange degraded](RUNBOOK_PILOT_INCIDENT_EXCHANGE_DEGRADED.md); overlap is common — hold **`NO_TRADE`** until venue truth is **classifiable** alongside local rebuild.
- **Observability / evidence continuity** gaps without a restart narrative → [Telemetry degraded](RUNBOOK_PILOT_INCIDENT_TELEMETRY_DEGRADED.md).
- **Transfer / funding** state unknown → [Transfer ambiguity](RUNBOOK_PILOT_INCIDENT_TRANSFER_AMBIGUITY.md).
- **Exposure / envelope** doubt drives the incident → [Unexpected exposure](RUNBOOK_PILOT_INCIDENT_UNEXPECTED_EXPOSURE.md).
- **Symptom routing** → [Abort triage compass](RUNBOOK_BOUNDED_PILOT_INCIDENT_ABORT_TRIAGE_COMPASS.md).

## B. Triggers and entry conditions

**Observable triggers (any can suffice)**

- Process or session **restarted** or **crashed** during a window when **orders were active** or **positions were expected** open.
- **Local** OrderLedger / PositionLedger (or equivalent runtime views) are **empty**, **default**, or **clearly not warm-loaded** for the active session on process start.
- **Broker or exchange** surfaces still show **open orders**, **non-flat positions**, or **recent fills** that must be **reconciled** to any local trail.
- **Execution event** trails and operator logs **suggest prior activity** that is **not** reflected in the **current** warm local state — bounded-pilot evidence roots include session-scoped paths under `out&#47;ops&#47;execution_events&#47;` and (where applicable) `logs&#47;execution&#47;execution_events.jsonl`; see [Bounded pilot telemetry / evidence roots note](../specs/BOUNDED_PILOT_TELEMETRY_ROOT_EVIDENCE_GAP_NOTE.md).

**Fail-closed rule**

- If you **cannot** yet establish a coherent story of **venue truth vs local trail** after a restart, treat as **`ambiguous`**: **`NO_TRADE`** and **freeze** risk expansion until classification improves or governance directs otherwise **outside** this document.

## C. Immediate actions (ordered)

1. **Stop new risk:** **`NO_TRADE`** and **no** deliberate risk-increasing steps until rebuild and classification are complete. Use org **kill-switch / safe-stop** only per [Kill Switch runbook](../../risk/KILL_SWITCH_RUNBOOK.md); this runbook does not redefine that mechanism.
2. **Freeze the scene:** record **UTC time** of restart/detection, **session id**, **operator**, and whether local state **started cold** (ledgers empty / not loaded).
3. **Gather venue-trusted truth:** broker or exchange **orders, fills, positions, balances** via channels already used in your pilot; treat **venue** as authoritative for **what is live** vs a blank local pane.
4. **Gather local evidence (read-only):** execution event JSONL and related logs **without** pasting contents into git — use session-scoped paths under `out&#47;ops&#47;execution_events&#47;sessions&#47;<session_id>&#47;` when present, and/or `logs&#47;execution&#47;execution_events.jsonl` per org layout; confirm kill-switch **state** path for your deployment (commonly `data&#47;kill_switch&#47;state.json`).
5. **Reconcile:** compare **venue truth** to the **evidence trail** and any local snapshots; identify **orphan orders**, **stale positions**, **missing fills**, or **timeline gaps** introduced by the restart.
6. **Classify:** **`reconciled_explainable`** / **`partial`** / **`ambiguous`** (see §D).
7. If **`partial`** or **`ambiguous`**: **escalate** per §F; **do not** assume safe to proceed.

**Order matters:** **posture and venue truth** before any “resume” or “catch up” narrative.

## D. Verification and classification

**Definitions**

- **Reconciled explainable:** **venue-trusted** orders, positions, and balances **align** with a **complete, operator-trusted** explanation of the evidence trail and session window — **or** any discrepancy is **fully explained** by a known cause (e.g. documented lag, acknowledged duplicate terminal) **without** residual exposure doubt.
- **Partial:** some domains **match** but **orders, fills, or balances** remain **unsettled**, **missing**, or **only partially** replayed — **cannot** rely on full continuity for the next step.
- **Ambiguous:** contradictory terminals, **unknown** net exposure after restart, **cannot** complete comparison in bounded time, or **venue** truth itself is **unstable** — treat as **unsafe to extend risk**.

**Suggested checks**

- Re-pull **venue-trusted** views; compare **stable identifiers** (order id, client id, fill id), not only aggregates.
- If cockpit/registry JSON or report scripts are used, treat as **read-only hints**; read **disclaimers**; JSON is **not** proof of safety (see [Compass §8](RUNBOOK_BOUNDED_PILOT_INCIDENT_ABORT_TRIAGE_COMPASS.md#8-read-only-cli--report-hints-scriptsreport_live_sessionspy)).
- If **venue** symptoms dominate, pivot primary posture to [Exchange degraded](RUNBOOK_PILOT_INCIDENT_EXCHANGE_DEGRADED.md) while holding **`NO_TRADE`**.

**Return toward normal (non-authorizing)**

- **No** “resume trading” or “session OK” from this runbook alone after **`partial`** / **`ambiguous`**. **Only** governance or explicit org disposition **outside** this repo can authorize continuation.
- If **`reconciled_explainable`**, posture still follows [Entry Contract §5](../specs/BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md#5-abort--rollback--no_trade-criteria); this runbook does not grant go-ahead.

## E. Evidence and pointers (L5 discipline)

Capture review material **outside** git per [L5 incident / safe-stop pointer contract](../specs/MASTER_V2_BOUNDED_PILOT_L5_INCIDENT_SAFE_STOP_EVIDENCE_POINTER_CONTRACT_V0.md): **metadata and opaque handles only** — no log dumps, secrets, raw broker payloads, or full JSONL pasted into the repository.

**Minimum narrative to record externally (conceptual)**

- **Trigger** (restart / crash / cold start, first symptom).
- **Truth sources** (venue channels, evidence roots consulted — categories only).
- **Reconciliation summary** (orphan/stale/gap narrative, identifiers only as appropriate).
- **Classification** (`reconciled_explainable` / `partial` / `ambiguous`).
- **Final posture** and **escalation** reference if any.

## F. Escalation

Escalate when **any** holds:

- Classification remains **`partial`** or **`ambiguous`** after bounded checks.
- **Exposure or session** truth **cannot** be verified after restart.
- **Policy / kill-switch** blocks progression while rebuild is incomplete.

State **symptom class**, **UTC window**, **session id**, and whether exposure is **known**, **partially known**, or **unknown**.

## G. Related runbooks and design context

**Runbooks**

- [Reconciliation mismatch](RUNBOOK_PILOT_INCIDENT_RECONCILIATION_MISMATCH.md)
- [Session end mismatch](RUNBOOK_PILOT_INCIDENT_SESSION_END_MISMATCH.md)
- [Exchange degraded](RUNBOOK_PILOT_INCIDENT_EXCHANGE_DEGRADED.md)
- [Telemetry degraded](RUNBOOK_PILOT_INCIDENT_TELEMETRY_DEGRADED.md)
- [Transfer ambiguity](RUNBOOK_PILOT_INCIDENT_TRANSFER_AMBIGUITY.md)
- [Unexpected exposure](RUNBOOK_PILOT_INCIDENT_UNEXPECTED_EXPOSURE.md)
- [Abort triage compass](RUNBOOK_BOUNDED_PILOT_INCIDENT_ABORT_TRIAGE_COMPASS.md)

**Specs (design context; no extra authorization)**

- [Reconciliation flow spec](../specs/RECONCILIATION_FLOW_SPEC.md) — restart-during-active-session considerations.
- [Pilot execution edge case matrix](../specs/PILOT_EXECUTION_EDGE_CASE_MATRIX.md) — Session/Recovery: restart mid-session.
- [Go/No-Go operational slice](../specs/PILOT_GO_NO_GO_OPERATIONAL_SLICE.md) — checklist mapping including restart/replay row.
