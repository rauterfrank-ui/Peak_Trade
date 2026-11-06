# RUNBOOK — Pilot Incident: Telemetry Degraded

status: OPERATOR-READY
last_updated: 2026-04-23
owner: Peak_Trade
purpose: Operator response when telemetry, evidence freshness, or observability continuity is degraded during the bounded pilot such that operator visibility into posture or audit trail is incomplete
docs_token: DOCS_TOKEN_RUNBOOK_PILOT_INCIDENT_TELEMETRY_DEGRADED

## Non-authorization (read first)

This runbook is an **operator aid** only. It does **not**:

- authorize live trading, resume a session, or close any gate;
- replace the [Entry Contract](../specs/BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md), governance decisions, or org kill-switch procedures;
- prove safety from read-only CLI output or in-repo documentation alone.

If there is **any** doubt whether trading is allowed, apply [Entry Contract §5](../specs/BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md#5-abort--rollback--no_trade-criteria): **ambiguity ⇒ `NO_TRADE` / safe stop**.

## A. Purpose and boundaries

**Use this runbook as the primary path when** the **dominant** problem is **observability / evidence continuity**: stale or missing telemetry segments, **gaps** in the operator-trusted **audit or evidence trail**, or dashboards that **look** healthy while **bounded-pilot evidence** (freshness, segments, or continuity) is **not** sufficient to support the next risk-increasing step.

**Prefer a different primary path when:**

- **Exchange or broker API** behavior (latency, rejects, rate limits, unstable order/ack state) is the **main** failure mode → [Exchange degraded](RUNBOOK_PILOT_INCIDENT_EXCHANGE_DEGRADED.md); **overlap is common** — if **venue** truth is unreliable, treat exchange path as **primary** and remain `NO_TRADE` while telemetry is also incomplete.
- **Ledger disagreement** (orders, fills, positions, balances, transfers) is the **first** job → [Reconciliation mismatch](RUNBOOK_PILOT_INCIDENT_RECONCILIATION_MISMATCH.md).
- **Closeout / session-end** terminal disagreement → [Session end mismatch](RUNBOOK_PILOT_INCIDENT_SESSION_END_MISMATCH.md).
- **Transfer status** unknown → [Transfer ambiguity](RUNBOOK_PILOT_INCIDENT_TRANSFER_AMBIGUITY.md).
- **Exposure / envelope** doubt without a crisp observability narrative → [Unexpected exposure](RUNBOOK_PILOT_INCIDENT_UNEXPECTED_EXPOSURE.md).
- **Symptom routing** → [Abort triage compass](RUNBOOK_BOUNDED_PILOT_INCIDENT_ABORT_TRIAGE_COMPASS.md).

## B. Triggers and entry conditions

**Observable triggers (any can suffice)**

- **Stale evidence freshness** or **missing** telemetry segments needed for pilot review or continuity.
- **System appears healthy** on coarse signals while **pilot-grade** observability (session/evidence/registry views) is **incomplete** or **discontinuous**.
- **Gaps** in timelines, logs, or exports that operators **expect** for the current session window.
- **Cannot** answer whether evidence continuity supports the **next** bounded action within a short, operator-defined check.

**Fail-closed rule**

- If **trust in visibility** is **unclear**, treat as **`ambiguous`**: **`NO_TRADE`** and **freeze** progression until classification improves or governance directs otherwise **outside** this document.

## C. Immediate actions (ordered)

1. **Stop new risk:** **`NO_TRADE`** and **no** deliberate risk-increasing steps that **depend** on complete observability you **do not** have. Use org **kill-switch / safe-stop** only per [Kill Switch runbook](../../risk/KILL_SWITCH_RUNBOOK.md); this runbook does not redefine that mechanism.
2. **Freeze the scene:** record **UTC interval** of the gap, **session id**, **operator**, and which **evidence classes** are missing or stale.
3. **Identify affected truth sources:** e.g. telemetry backends, export jobs, registry/cockpit read-models — **without** pasting secrets or payloads into git.
4. **Classify** observability posture: **`reconciled_explainable`** / **`partial`** / **`ambiguous`** (see §D).
5. If **`partial`** or **`ambiguous`**: **escalate** per §F; **do not** “trade through” missing evidence.

**Order matters:** **posture before** assuming dashboards reflect safe reality.

## D. Verification and classification

**Definitions**

- **Reconciled explainable:** gaps are **bounded and explained** (known delay, single missing segment with **no** impact on exposure truth for the next step per operator procedure) — **and** broker/exposure truth is **still** verifiable **independently** of the degraded telemetry path.
- **Partial:** some evidence streams **ok**, others **missing** or **stale** — **cannot** rely on full continuity for pilot decisions.
- **Ambiguous:** contradictory freshness signals, **unknown** coverage of the session window, or **cannot** complete verification in bounded time.

**Suggested checks**

- Re-pull **bounded-pilot** overview / lifecycle / closeout JSON **read-only** after posture is safe — see [Compass §8](RUNBOOK_BOUNDED_PILOT_INCIDENT_ABORT_TRIAGE_COMPASS.md#8-read-only-cli--report-hints-scriptsreport_live_sessionspy); read **disclaimers**; JSON is **not** proof of safety.
- If **venue** symptoms dominate, pivot posture to [Exchange degraded](RUNBOOK_PILOT_INCIDENT_EXCHANGE_DEGRADED.md) while holding `NO_TRADE`.

**Return toward normal (non-authorizing)**

- **No** “resume trading” from this runbook alone after **`partial`** / **`ambiguous`**. **Only** governance or explicit org disposition **outside** this repo can authorize continuation.
- If **`reconciled_explainable`**, posture still follows [Entry Contract §5](../specs/BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md#5-abort--rollback--no_trade-criteria); this runbook does not grant go-ahead.

## E. Evidence and pointers (L5 discipline)

Capture review material **outside** git per [L5 incident / safe-stop pointer contract](../specs/MASTER_V2_BOUNDED_PILOT_L5_INCIDENT_SAFE_STOP_EVIDENCE_POINTER_CONTRACT_V0.md): **metadata and opaque handles only** — no log dumps, secrets, or raw telemetry payloads in the repository.

**Minimum narrative to record externally (conceptual)**

- **Trigger** (gap type, first symptom).
- **Affected truth sources** (categories only).
- **Degraded interval** (UTC).
- **Classification** (`reconciled_explainable` / `partial` / `ambiguous`).
- **Final posture** and **escalation** reference if any.

## F. Escalation

Escalate when **any** holds:

- Classification remains **`partial`** or **`ambiguous`** after bounded checks.
- **Exposure or session** truth **cannot** be verified **without** the missing observability path.
- **Policy / kill-switch** blocks progression while evidence continuity is unresolved.

State **symptom class**, **UTC window**, **session id**, and whether visibility into exposure is **known**, **partially known**, or **unknown**.

## G. Related runbooks

- [Exchange degraded](RUNBOOK_PILOT_INCIDENT_EXCHANGE_DEGRADED.md)
- [Reconciliation mismatch](RUNBOOK_PILOT_INCIDENT_RECONCILIATION_MISMATCH.md)
- [Session end mismatch](RUNBOOK_PILOT_INCIDENT_SESSION_END_MISMATCH.md)
- [Transfer ambiguity](RUNBOOK_PILOT_INCIDENT_TRANSFER_AMBIGUITY.md)
- [Unexpected exposure](RUNBOOK_PILOT_INCIDENT_UNEXPECTED_EXPOSURE.md)
- [Abort triage compass](RUNBOOK_BOUNDED_PILOT_INCIDENT_ABORT_TRIAGE_COMPASS.md)
