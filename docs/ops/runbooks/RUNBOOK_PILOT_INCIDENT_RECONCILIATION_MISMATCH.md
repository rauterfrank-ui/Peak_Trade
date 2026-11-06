# RUNBOOK — Pilot Incident: Reconciliation Mismatch

status: OPERATOR-READY
last_updated: 2026-04-23
owner: Peak_Trade
purpose: Operator response when local or internal state disagrees with broker/exchange-trusted orders, fills, positions, balances, or transfers during the bounded pilot
docs_token: DOCS_TOKEN_RUNBOOK_PILOT_INCIDENT_RECONCILIATION_MISMATCH

## Non-authorization (read first)

This runbook is an **operator aid** only. It does **not**:

- authorize live trading, resume a session, or close any gate;
- replace the [Entry Contract](../specs/BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md), governance decisions, or org kill-switch procedures;
- prove safety from read-only CLI output or in-repo documentation alone.

If there is **any** doubt whether trading is allowed, apply [Entry Contract §5](../specs/BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md#5-abort--rollback--no_trade-criteria): **ambiguity ⇒ `NO_TRADE` / safe stop**.

## A. Purpose and boundaries

**Use this runbook as the primary path when** the first job is **systematic comparison** of **orders, fills, positions, balances, or transfers**: internal or tool-reported state **disagrees** with **broker/exchange-trusted** truth, or reconciliation **stalls** (partial rows, timeouts, conflicting terminals).

**Prefer a different primary path when:**

- **Exposure / envelope** is the main doubt (too large, unknown size, caps vs broker disagree on *risk*, not only on row timing) → [Unexpected exposure](RUNBOOK_PILOT_INCIDENT_UNEXPECTED_EXPOSURE.md); you may return here if the mismatch **narrows** to concrete ledger rows.
- **Disagreement is narrowly at session end / closeout boundary** → [Session end mismatch](RUNBOOK_PILOT_INCIDENT_SESSION_END_MISMATCH.md).
- **Funding / transfer landed vs internal** is the unknown → [Transfer ambiguity](RUNBOOK_PILOT_INCIDENT_TRANSFER_AMBIGUITY.md).
- **Venue unhealthy** (timeouts, rejects) without a settled ledger story yet → [Exchange degraded](RUNBOOK_PILOT_INCIDENT_EXCHANGE_DEGRADED.md); hold `NO_TRADE` until reconciliation is **classifiable**.
- **Orientation across symptoms** → [Abort triage compass](RUNBOOK_BOUNDED_PILOT_INCIDENT_ABORT_TRIAGE_COMPASS.md).

## B. Triggers and entry conditions

**Observable triggers (any can suffice)**

- **Order / fill mismatch:** IDs, statuses, or counts differ between internal records and broker UI/API.
- **Stale position or balance:** internal or cockpit view lags broker-trusted position or cash/margin after known activity.
- **Session-end mismatch** *as a reconciliation problem* (terminal orders/fills/positions disagree), not only a lifecycle row label — if scope is only closeout wording, prefer session-end runbook.
- **Transfer ambiguity** *as it appears in reconciliation* (internal expects transfer, broker ledger unclear) — if transfer *state* is the sole unknown, prefer transfer runbook.

**Fail-closed rule**

- If you **cannot** yet name which domain is wrong (orders vs fills vs positions vs balances vs transfers), treat as **`ambiguous`** for posture: **`NO_TRADE`** until bounded.

## C. Immediate actions (ordered)

1. **Stop new risk:** **`NO_TRADE`** and no deliberate size increases. Use org **kill-switch / safe-stop** only per [Kill Switch runbook](../../risk/KILL_SWITCH_RUNBOOK.md); this runbook does not redefine that mechanism.
2. **Freeze the scene:** record **UTC time**, **session id**, **operator**, last known **trusted** snapshot vs current symptom.
3. **Choose broker-trusted channels** already used in your pilot for **authoritative** orders/fills/positions/balances; do not treat a single local pane as truth when it disagrees with broker authority for size.
4. **Compare in one domain at a time** (orders → fills → positions → balances → transfers) to avoid mixing causes.
5. **Classify** outcome of the comparison: **`reconciled_explainable`** / **`partial`** / **`ambiguous`**.
6. If **`partial`** or **`ambiguous`**: remain **`NO_TRADE`** and **escalate** per §G.

**Order matters:** safe posture and broker-trusted truth **before** “resume” narratives.

## D. Verification and classification

**Definitions**

- **Reconciled explainable:** broker-trusted and internal views **align** after bounded checks, or discrepancy is **fully explained** by a known, operator-trusted cause (e.g. acknowledged lag window documented in your procedure) **without** residual exposure doubt.
- **Partial:** some legs or rows **match**, others **missing**, **timeout**, or **conflicting** — exposure or session story **not** fully known.
- **Ambiguous:** contradictory terminals, **unknown** net, or **cannot** complete comparison in bounded time — treat as **unsafe to extend risk**.

**Suggested checks**

- Re-pull **broker-trusted** exports or API views; compare stable identifiers (order id, client id, fill id) not only aggregates.
- If cockpit/registry JSON is used, treat as **read-only hints**; read **disclaimers**; JSON is **not** proof of safety (see [Compass §8](RUNBOOK_BOUNDED_PILOT_INCIDENT_ABORT_TRIAGE_COMPASS.md#8-read-only-cli--report-hints-scriptsreport_live_sessionspy)).

**Resume / return toward normal (non-authorizing)**

- **No** “resume trading” from this runbook alone. **Only** governance or an **explicit** org disposition **outside** this repo can authorize continuation after **`partial`** / **`ambiguous`**.
- If **`reconciled_explainable`**, posture still follows org procedure and [Entry Contract §5](../specs/BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md#5-abort--rollback--no_trade-criteria); this runbook does not grant go-ahead.

## E. Evidence and pointers (L5 discipline)

Capture review material **outside** git per [L5 incident / safe-stop pointer contract](../specs/MASTER_V2_BOUNDED_PILOT_L5_INCIDENT_SAFE_STOP_EVIDENCE_POINTER_CONTRACT_V0.md): **metadata and opaque handles only** — no log dumps, secrets, or broker identifiers pasted into the repository.

**Minimum narrative to record externally (conceptual)**

- **Trigger** (which domain, first symptom).
- **Truth sources** (broker vs internal paths consulted).
- **Mismatch summary** (what differs, identifiers only as appropriate).
- **Classification** (`reconciled_explainable` / `partial` / `ambiguous`).
- **Final posture** (`NO_TRADE` / escalation / governance disposition reference).

## F. Escalation (when to stop local triage)

Escalate when **any** holds:

- Classification stays **`partial`** or **`ambiguous`** after initial bounded steps.
- **Exposure** cannot be bounded or contradicts pilot envelope while mismatch is open.
- **Kill-switch / policy** blocks you while mismatch is unresolved and you lack org guidance.

State **symptom class**, **UTC window**, **session id**, and whether exposure is **known**, **partially known**, or **unknown**.

## G. Related runbooks

- [Unexpected exposure](RUNBOOK_PILOT_INCIDENT_UNEXPECTED_EXPOSURE.md)
- [Session end mismatch](RUNBOOK_PILOT_INCIDENT_SESSION_END_MISMATCH.md)
- [Transfer ambiguity](RUNBOOK_PILOT_INCIDENT_TRANSFER_AMBIGUITY.md)
- [Exchange degraded](RUNBOOK_PILOT_INCIDENT_EXCHANGE_DEGRADED.md)
- [Abort triage compass](RUNBOOK_BOUNDED_PILOT_INCIDENT_ABORT_TRIAGE_COMPASS.md)
