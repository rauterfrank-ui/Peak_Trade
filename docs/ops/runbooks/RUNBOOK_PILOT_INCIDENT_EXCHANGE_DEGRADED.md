# RUNBOOK — Pilot Incident: Exchange Degraded

status: OPERATOR-READY
last_updated: 2026-04-23
owner: Peak_Trade
purpose: Operator response when exchange or broker API behavior is degraded during the bounded pilot—latency, errors, rate limits, or unstable order/ack/fill truth—such that venue trust is insufficient for risk-increasing steps until classified and reconciled or governance directs otherwise outside this document
docs_token: DOCS_TOKEN_RUNBOOK_PILOT_INCIDENT_EXCHANGE_DEGRADED

## Non-authorization (read first)

This runbook is an **operator aid** only. It does **not**:

- authorize live trading, resume a session, or close any gate;
- replace the [Entry Contract](../specs/BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md), governance decisions, or org kill-switch procedures;
- prove safety from read-only CLI output or in-repo documentation alone.

If there is **any** doubt whether trading is allowed, apply [Entry Contract §5](../specs/BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md#5-abort--rollback--no_trade-criteria): **ambiguity ⇒ `NO_TRADE` / safe stop**.

## A. Purpose and boundaries

**Use this runbook as the primary path when** the **dominant** problem is **degraded or unreliable exchange/broker API or venue truth**: elevated latency or timeouts, error/reject spikes, rate-limit or capacity signals, or **unstable** order/ack/fill state across refresh cycles—**before** you have a clean, systematic ledger story. Symptom routing: [Abort triage compass §5.1](RUNBOOK_BOUNDED_PILOT_INCIDENT_ABORT_TRIAGE_COMPASS.md#51-exchange--broker-path-unhealthy).

**Prefer a different primary path when:**

- **Systematic ledger comparison** (orders, fills, positions, balances, transfers) is the **first** job on **stable enough** venue reads → [Reconciliation mismatch](RUNBOOK_PILOT_INCIDENT_RECONCILIATION_MISMATCH.md); **overlap is common** — remain **`NO_TRADE`** while the venue is **also** too flaky to trust those reads, then **return** here as primary until venue class improves.
- **Observability / evidence continuity** is the main gap **without** a clear venue-outage pattern → [Telemetry degraded](RUNBOOK_PILOT_INCIDENT_TELEMETRY_DEGRADED.md); if **venue** symptoms dominate, treat **this** runbook as **primary** and hold `NO_TRADE` while telemetry is incomplete.
- **Closeout / session-end** terminal disagreement at the **session boundary** → [Session end mismatch](RUNBOOK_PILOT_INCIDENT_SESSION_END_MISMATCH.md).
- **Cap or envelope surprise** is the main doubt → [Unexpected exposure](RUNBOOK_PILOT_INCIDENT_UNEXPECTED_EXPOSURE.md); **overlap is common** — stabilize venue **and** hold `NO_TRADE` if exposure is unclear.
- **Transfer / funding** state unknown → [Transfer ambiguity](RUNBOOK_PILOT_INCIDENT_TRANSFER_AMBIGUITY.md).
- **Process restart / cold local state** mid-session → [Restart mid-session](RUNBOOK_PILOT_INCIDENT_RESTART_MID_SESSION.md); venue degradation may **co-occur** after restart.
- **Symptom routing** → [Abort triage compass](RUNBOOK_BOUNDED_PILOT_INCIDENT_ABORT_TRIAGE_COMPASS.md).

## B. Triggers and entry conditions

**Observable triggers (any can suffice)**

- **Latency or timeouts** on order, cancel, or query paths **materially** above your pilot baseline.
- **Error or reject rate** spikes (HTTP/API errors, venue error codes, sustained reject-class outcomes).
- **Rate-limit or capacity** signals (throttling, HTTP 429-class behavior, documented venue degradation).
- **Order / ack / fill** state **flickers** or **fails to reach** a terminal state you can verify within a short, operator-defined window.
- **Position or exposure** from the venue **cannot** be aligned with the operator’s session view in that same bounded window.

**Fail-closed rule**

- If you **cannot** classify venue health for the **next** bounded action, treat as **`ambiguous`**: **`NO_TRADE`** and **freeze** risk expansion until classification improves or governance directs otherwise **outside** this document.

## C. Immediate actions (ordered)

1. **Stop new risk:** **`NO_TRADE`** and **no** deliberate risk-increasing orders or size increases until classification completes. Use org **kill-switch / safe-stop** only per [Kill Switch runbook](../../risk/KILL_SWITCH_RUNBOOK.md); this runbook does not redefine that mechanism.
2. **Freeze the scene:** record **UTC interval**, **session id**, **operator**, and **symptom class** (timeouts / rejects / rate limit / state ambiguity).
3. **Confirm bounded-pilot context:** re-read [Entry Contract §1–2](../specs/BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md) mentally; do not exceed the documented bounded real-money step intent.
4. **Verify policy visibility:** if kill-switch, policy, or session posture is **not** visible per your procedure, treat as **blocked** per Entry Contract §5 (*operator cannot clearly determine the current bounded posture*).
5. **Reconcile venue-trusted truth:** compare orders, fills, cancels, and positions using **independent** checks your pilot already uses (e.g. venue UI vs registry vs internal summaries). Document **discrepancies** externally—**no** raw payloads or secrets in git.
6. **Classify:** **`reconciled_explainable`** / **`partial`** / **`ambiguous`** (see §D).
7. If **`partial`** or **`ambiguous`**: **escalate** per §F; **do not** “trade through” venue flakiness.

**Order matters:** **posture and venue-trusted terminals** before any “resume” narrative.

## D. Verification and classification

**Definitions**

- **Reconciled explainable:** degradation is **bounded** (known window, explainable lag or single-class errors) **and** **terminal** order/fill/position states are **establishable** via broker-trusted channels **without** residual exposure doubt for the pilot envelope — **still** no authorization from this document to resume.
- **Partial:** some checks succeed, others **timeout** or **conflict**; **incomplete** picture of terminals or net exposure.
- **Ambiguous:** contradictory venue snapshots, **unknown** terminals after bounded tries, or venue truth **unstable** — **unsafe** to extend risk.

**Suggested checks**

- Re-pull **venue-trusted** views; compare **stable identifiers** (order id, client id, fill id), not only aggregates.
- If cockpit/registry JSON or `scripts/report_live_sessions.py` outputs are used, treat as **read-only hints**; read **disclaimers**; JSON is **not** proof of safety (see [Compass §8](RUNBOOK_BOUNDED_PILOT_INCIDENT_ABORT_TRIAGE_COMPASS.md#8-read-only-cli--report-hints-scriptsreport_live_sessionspy)).
- If **observability** gaps dominate **without** a venue-primary story, pivot triage context to [Telemetry degraded](RUNBOOK_PILOT_INCIDENT_TELEMETRY_DEGRADED.md) while holding **`NO_TRADE`**.

**Return toward normal (non-authorizing)**

- **No** “resume trading” from this runbook alone after **`partial`** / **`ambiguous`**. **Only** governance or explicit org disposition **outside** this repo can authorize continuation.
- If **`reconciled_explainable`**, posture still follows [Entry Contract §5](../specs/BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md#5-abort--rollback--no_trade-criteria) and [Failure taxonomy §6](../specs/MASTER_V2_FAILURE_TAXONOMY_SAFE_FALLBACKS_V1.md#6-ambiguity-confusion-and-interpretation-risk-map); this runbook does not grant go-ahead. For **next session** or **candidate** steps, follow [Bounded real-money pilot candidate flow](RUNBOOK_BOUNDED_REAL_MONEY_PILOT_CANDIDATE_FLOW.md) and [Live entry](RUNBOOK_BOUNDED_PILOT_LIVE_ENTRY.md) only per **your** authorized procedures **outside** this document.

## E. Evidence and pointers (L5 discipline)

Capture review material **outside** git per [L5 incident / safe-stop pointer contract](../specs/MASTER_V2_BOUNDED_PILOT_L5_INCIDENT_SAFE_STOP_EVIDENCE_POINTER_CONTRACT_V0.md): **metadata and opaque handles only** — no log dumps, secrets, full API traces, or kill-switch dumps in the repository.

**Minimum narrative to record externally (conceptual)**

- **Trigger** (symptom class, first observation).
- **Venue / channel** (categories only) and **UTC window**.
- **Reconciliation summary** (what could / could not be verified; identifiers only as appropriate).
- **Classification** (`reconciled_explainable` / `partial` / `ambiguous`).
- **Final posture** and **escalation** reference if any.

## F. Escalation

Escalate when **any** holds:

- Classification remains **`partial`** or **`ambiguous`** after bounded checks.
- **Terminal** order or position state **cannot** be established via broker-trusted paths.
- **Policy / kill-switch** blocks progression while venue degradation is unresolved.

**Internal:** pilot owner / governance channel per your existing bounded-pilot path (this document does not define roster).

**External:** venue or broker support only per org rules; **do not** paste secrets or raw account identifiers without redaction policy.

State **symptom class**, **UTC window**, **session id**, and whether exposure is **known**, **partially known**, or **unknown**.

## G. Related runbooks

- [Reconciliation mismatch](RUNBOOK_PILOT_INCIDENT_RECONCILIATION_MISMATCH.md)
- [Telemetry degraded](RUNBOOK_PILOT_INCIDENT_TELEMETRY_DEGRADED.md)
- [Session end mismatch](RUNBOOK_PILOT_INCIDENT_SESSION_END_MISMATCH.md)
- [Unexpected exposure](RUNBOOK_PILOT_INCIDENT_UNEXPECTED_EXPOSURE.md)
- [Transfer ambiguity](RUNBOOK_PILOT_INCIDENT_TRANSFER_AMBIGUITY.md)
- [Restart mid-session](RUNBOOK_PILOT_INCIDENT_RESTART_MID_SESSION.md)
- [Abort triage compass](RUNBOOK_BOUNDED_PILOT_INCIDENT_ABORT_TRIAGE_COMPASS.md)

**Design context (non-authorizing):** [Failure taxonomy](../specs/MASTER_V2_FAILURE_TAXONOMY_SAFE_FALLBACKS_V1.md) §4 / §6; [Reconciliation flow spec](../specs/RECONCILIATION_FLOW_SPEC.md); [Pilot execution edge case matrix](../specs/PILOT_EXECUTION_EDGE_CASE_MATRIX.md) (broker/API degradation rows).
