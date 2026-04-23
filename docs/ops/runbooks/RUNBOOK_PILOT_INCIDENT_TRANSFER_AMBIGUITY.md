# RUNBOOK — Pilot Incident: Transfer Ambiguity

status: OPERATOR-READY
last_updated: 2026-04-23
owner: Peak_Trade
purpose: Operator response when asset transfer status (withdraw, deposit, internal transfer) is unclear during the bounded pilot; unresolved ambiguity blocks dependent funding or risk steps
docs_token: DOCS_TOKEN_RUNBOOK_PILOT_INCIDENT_TRANSFER_AMBIGUITY

## Non-authorization (read first)

This runbook is an **operator aid** only. It does **not**:

- authorize live trading, resume a session, or close any gate;
- replace the [Entry Contract](../specs/BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md), governance decisions, or org kill-switch procedures;
- prove safety from read-only CLI output or in-repo documentation alone.

If there is **any** doubt whether trading is allowed, apply [Entry Contract §5](../specs/BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md#5-abort--rollback--no_trade-criteria): **ambiguity ⇒ `NO_TRADE` / safe stop**.

## A. Purpose and boundaries

**Use this runbook as the primary path when** the **dominant** uncertainty is **transfer state**: whether a **withdrawal, deposit, or internal transfer** has **completed**, **failed**, or **cannot be determined** from broker/exchange-trusted history within a bounded check, and **downstream** pilot steps depend on that truth.

**Prefer a different primary path when:**

- The problem is **broader ledger disagreement** (orders, fills, positions, balances **and** transfers in one systematic compare) → start with [Reconciliation mismatch](RUNBOOK_PILOT_INCIDENT_RECONCILIATION_MISMATCH.md); use this runbook if the scope **narrows** to **transfer status only**.
- **Closeout / session-end terminal state** is the main disagreement → [Session end mismatch](RUNBOOK_PILOT_INCIDENT_SESSION_END_MISMATCH.md).
- **Exposure or envelope** is the primary doubt without a crisp transfer narrative → [Unexpected exposure](RUNBOOK_PILOT_INCIDENT_UNEXPECTED_EXPOSURE.md).
- **Venue degradation** (timeouts, rejects) dominates before transfer history is readable → [Exchange degraded](RUNBOOK_PILOT_INCIDENT_EXCHANGE_DEGRADED.md); remain `NO_TRADE` while truth is unstable.
- **Symptom routing** → [Abort triage compass](RUNBOOK_BOUNDED_PILOT_INCIDENT_ABORT_TRIAGE_COMPASS.md).

**Treasury / execution boundary (repo-evident discipline)**

- **Operational keys used for trading** do **not** execute transfers in this architecture; transfers are **manual or external** to the bot path. This runbook covers **status tracking and posture** when transfers matter for pilot continuity — not implementation of transfers.

**Design context (non-authorizing)**

- [Reconciliation flow spec](../specs/RECONCILIATION_FLOW_SPEC.md) — Transfers.
- [Pilot execution edge case matrix](../specs/PILOT_EXECUTION_EDGE_CASE_MATRIX.md) — Transfer ambiguity.

## B. Triggers and entry conditions

**Observable triggers (any can suffice)**

- Transfer **initiated** but **completion** unknown after a bounded wait.
- Broker/exchange **transfer history** missing expected rows, **delayed**, or **contradictory**.
- **Internal** expectation (treasury note, operator intent) **disagrees** with broker-trusted transfer status.
- **Audit trail** for the transfer is **incomplete** or **cannot** be aligned to a single terminal state.

**Fail-closed rule**

- If dependent actions (size increases, session progression, reliance on posted collateral) **require** settled transfer truth and you **cannot** assert it, treat as **`ambiguous`**: **`NO_TRADE`** and **no** new dependent steps.

## C. Immediate actions (ordered)

1. **Stop new risk:** **`NO_TRADE`** and **no** deliberate positions or size increases that **depend** on unsettled transfer state. Use org **kill-switch / safe-stop** only per [Kill Switch runbook](../../risk/KILL_SWITCH_RUNBOOK.md); this runbook does not redefine that mechanism.
2. **Freeze the scene:** record **UTC time**, **session id** (if applicable), **operator**, transfer **type** (withdraw / deposit / internal), and **last known** broker vs internal expectation.
3. **Gather broker-trusted transfer history** through the same channels your pilot already treats as authoritative for funding movements; do not trust a single internal pane if it contradicts broker transfer records.
4. **Compare** intent vs observed terminals; **classify**: **`reconciled_explainable`** / **`partial`** / **`ambiguous`**.
5. If **`partial`** or **`ambiguous`**: **escalate** per §F; **do not** assume the transfer completed.

**Order matters:** **posture before** assuming funding is available or safe to build on.

## D. Verification and classification

**Definitions**

- **Reconciled explainable:** broker-trusted transfer state **matches** internal expectation, or discrepancy is **fully explained** by an operator-trusted, bounded cause (e.g. known processing window documented in your procedure) **without** residual ambiguity for dependent steps.
- **Partial:** some status fields **clear**, others **missing**, **delayed**, or **inconsistent** — **cannot** rely on collateral or funding assumptions.
- **Ambiguous:** **contradictory** terminals, **unknown** net funding effect, or **cannot** complete verification in bounded time.

**Suggested checks**

- Re-query transfer **history** and **transaction ids**; align **timestamps** in UTC.
- If registry/cockpit JSON is used, treat as **read-only hints**; read **disclaimers** (see [Compass §8](RUNBOOK_BOUNDED_PILOT_INCIDENT_ABORT_TRIAGE_COMPASS.md#8-read-only-cli--report-hints-scriptsreport_live_sessionspy)).

**Return toward normal (non-authorizing)**

- **No** “resume trading” from this runbook alone after **`partial`** / **`ambiguous`**. **Only** governance or explicit org disposition **outside** this repo can authorize continuation.
- If **`reconciled_explainable`**, posture still follows [Entry Contract §5](../specs/BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md#5-abort--rollback--no_trade-criteria) and org procedure; this runbook does not grant go-ahead.

## E. Evidence and pointers (L5 discipline)

Capture review material **outside** git per [L5 incident / safe-stop pointer contract](../specs/MASTER_V2_BOUNDED_PILOT_L5_INCIDENT_SAFE_STOP_EVIDENCE_POINTER_CONTRACT_V0.md): **metadata and opaque handles only** — no log dumps, secrets, or raw broker identifiers pasted into the repository.

**Minimum narrative to record externally (conceptual)**

- **Trigger** (transfer type, first symptom).
- **Truth sources** (broker transfer history paths consulted).
- **Summary** (expected vs observed; ids only as appropriate).
- **Classification** (`reconciled_explainable` / `partial` / `ambiguous`).
- **Final posture** and **escalation** reference if any.

## F. Escalation

Escalate when **any** holds:

- Classification remains **`partial`** or **`ambiguous`** after bounded checks.
- **Dependent** pilot steps would **require** assumed funding that is **not** broker-confirmed.
- **Policy / kill-switch** blocks progression while transfer truth is unresolved.

State **transfer class**, **UTC window**, **session id** if relevant, and whether funding impact is **known**, **partially known**, or **unknown**.

## G. Related runbooks

- [Reconciliation mismatch](RUNBOOK_PILOT_INCIDENT_RECONCILIATION_MISMATCH.md)
- [Session end mismatch](RUNBOOK_PILOT_INCIDENT_SESSION_END_MISMATCH.md)
- [Unexpected exposure](RUNBOOK_PILOT_INCIDENT_UNEXPECTED_EXPOSURE.md)
- [Exchange degraded](RUNBOOK_PILOT_INCIDENT_EXCHANGE_DEGRADED.md)
- [Abort triage compass](RUNBOOK_BOUNDED_PILOT_INCIDENT_ABORT_TRIAGE_COMPASS.md)
