# RUNBOOK — Pilot Incident: Exchange Degraded

status: DRAFT
last_updated: 2026-04-20
owner: Peak_Trade
purpose: Operator response for degraded exchange/broker behavior during bounded pilot activity
docs_token: DOCS_TOKEN_RUNBOOK_PILOT_INCIDENT_EXCHANGE_DEGRADED

## 1) Purpose, scope, and non-goals

**Purpose:** Give operators a **repeatable** sequence for recognizing exchange/broker degradation during the **first strictly bounded real-money pilot** and for adopting a **conservative safe posture** (`NO_TRADE` / safe stop) until truth sources reconcile or governance directs otherwise **outside** this document.

**Scope:** Bounded-pilot execution only. This runbook addresses **unreliable or degraded** exchange/broker truth (latency, errors, rate limits, ambiguous order/ack state). It does **not** define product behavior, policy rules, or kill-switch implementation.

**Non-goals (explicit):**

- This runbook **does not** authorize live trading, close any gate, or claim that the pilot is safe to continue.
- It **does not** assert that an incident is “resolved” generically; it only describes **operator posture**, **blocking conditions**, and **external evidence** discipline.
- It **does not** substitute [`BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md`](../specs/BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md), governance decisions, or external sign-off.

**Canonical anchors (read-only):**

- Abort / rollback / `NO_TRADE`: [Entry contract §5](../specs/BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md#5-abort--rollback--no_trade-criteria).
- Failure / safe-fallback framing: [Failure taxonomy](../specs/MASTER_V2_FAILURE_TAXONOMY_SAFE_FALLBACKS_V1.md) (safety-boundary and operator-visibility rows in §4).
- External **L5** pointer vocabulary (no payloads in git): [L5 incident / safe-stop pointer contract v0](../specs/MASTER_V2_BOUNDED_PILOT_L5_INCIDENT_SAFE_STOP_EVIDENCE_POINTER_CONTRACT_V0.md).

## 2) Trigger / symptoms

Treat the situation as **exchange degraded** when **one or more** of the following are observed during pilot activity (examples, not an exhaustive product spec):

- **Latency or timeouts** increase materially on order, cancel, or query paths compared to normal pilot baseline.
- **Error or reject rate** spikes (HTTP/API errors, exchange error codes, sustained `reject`-class outcomes).
- **Rate-limit or capacity** signals indicate throttling or degraded service from the venue.
- **Order / ack / fill state** becomes **unstable or inconsistent** across refresh cycles (state “flicker,” missing acks, delayed fills without clear terminal state).
- **Position or exposure truth** from the exchange or broker **cannot be reconciled** with the operator’s internal session view within a short, operator-defined verification window.

If the operator **cannot** determine whether the venue is healthy enough for bounded pilot activity, treat that as **ambiguity** and apply §5.

## 3) Immediate safe posture

Until the situation is **clearly** classified as **degraded-but-reconcilable** with **stable** truth (§7), default posture is:

- **`NO_TRADE` / safe stop:** do **not** open new risk-increasing positions; do **not** rely on automation to “work through” venue flakiness without explicit human confirmation aligned with entry contract §5.
- **Do not expand risk** (size, leverage, new symbols) while exchange truth is unreliable.
- **Prefer fail-closed:** when in doubt, remain blocked; see [Failure taxonomy §6](../specs/MASTER_V2_FAILURE_TAXONOMY_SAFE_FALLBACKS_V1.md#6-ambiguity-confusion-and-interpretation-risk-map) (fail-closed vs strategic no-trade distinction remains governance-visible, not rewritten here).

## 4) Step-by-step operator actions

Execute in order unless a later step proves impossible without new risk; if so, stop and escalate (§6).

1. **Confirm bounded-pilot context**  
   Re-read [Entry contract §1–2](../specs/BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md) mentally; do not exceed the documented first bounded real-money step intent.

2. **Freeze new risk-increasing actions**  
   Stop placing new orders that increase exposure or widen ambiguity until classification completes.

3. **Verify safety and policy visibility**  
   Confirm kill-switch / policy / session posture is **visible** to the operator per your **operative** cockpit or procedure (this runbook does not invoke tooling). If posture is **not** visible, treat as **blocked** per entry contract §5 (*operator cannot clearly determine the current bounded posture*).

4. **Capture a minimal timestamped operator note (outside git)**  
   One line: symptom class (timeouts / rejects / rate limit / state ambiguity), UTC time, and “bounded pilot — exchange degraded path” — **no** secrets, API keys, or full log paste.

5. **Reconcile truth sources**  
   Compare order, fill, cancel, and position views using **independent** checks where your process allows (for example venue UI vs session registry vs internal summaries). Document **discrepancies**, not raw payloads, in change control.

6. **Classify**

   - **Degraded but reconcilable:** stable explanation, terminal order states known, exposure matches intended bounded envelope — **still** no new risk until governance/operator policy outside this doc allows continuation.  
   - **Ambiguous / irreconcilable:** exposure or order state **unclear** — remain **`NO_TRADE` / blocked** until reconciled; do **not** claim “all clear” from this runbook alone.

7. **Session and handoff**  
   If another operator takes over, hand off **classification**, **current posture**, and **open discrepancies** via your standard channel; see §8.

## 5) Abort / `NO_TRADE` / remain-blocked conditions

Remain in **blocked / `NO_TRADE`** posture (and escalate per §6) if **any** of the following hold:

- Kill switch active, policy blocked, or entry contract §5 abort criteria apply.
- Order or position **terminal state** cannot be established.
- **Ambiguity** remains about whether trading is allowed (entry contract §5: **ambiguity => `NO_TRADE` / safe stop**).
- **Evidence or dependency posture** is degraded beyond acceptable pilot tolerance (entry contract §5 bullet; operator judgment + governance outside this repo).

This runbook **does not** downgrade or override §5; it operationalizes a conservative reading for venue degradation.

## 6) Escalation / communication

- **Internal:** Notify pilot owner / governance channel per your **existing** bounded-pilot escalation path (this document does not define roster or tooling).
- **External:** Broker or venue support only as appropriate to your **operational** rules; **do not** paste secrets, keys, or full account identifiers into shared tickets without your org’s redaction policy.
- **What to communicate:** symptom category, time window (UTC), whether exposure is **known** or **unknown**, and current **`NO_TRADE` / blocked** posture — not a claim that the system is “safe” or “authorized.”

## 7) Evidence handling (pointers only)

Retain material **outside** this repository under change control. Use the **L5 pointer contract** classes and fields ([§3–4](../specs/MASTER_V2_BOUNDED_PILOT_L5_INCIDENT_SAFE_STOP_EVIDENCE_POINTER_CONTRACT_V0.md#3-allowed-pointer-classes-l5)) — for example `L5_INCIDENT_SAFE_STOP_SUMMARY_CAPTURE` and, when applicable, `L5_INCIDENT_RESPONSE_SUPPORTING_BUNDLE` — with **opaque** `retrieval_reference` values.

**Do not** commit incident logs, ticket exports, full API traces, or kill-switch dumps into git as “evidence of compliance.”

## 8) Exit, handoff, and unresolved conditions

**This runbook does not declare incident closure.**

- **Handoff:** Next operator receives classification, posture, reconciliation status, and external pointer handles (titles/IDs only in chat — not secret values in-repo).
- **Unresolved:** If reconciliation fails or ambiguity persists, maintain **`NO_TRADE` / blocked** and record **external** pointers only; revisit when venue truth and governance allow.
- **Degraded-but-reconcilable:** Even with a stable explanation, **resuming** risk-increasing activity is **not** implied here; follow [candidate flow](../runbooks/RUNBOOK_BOUNDED_REAL_MONEY_PILOT_CANDIDATE_FLOW.md) and [live entry](../runbooks/RUNBOOK_BOUNDED_PILOT_LIVE_ENTRY.md) only per **your** authorized procedures — this runbook stays a **degradation** path only.

## 9) Non-authorization reminder

Following this runbook **does not** mean:

- any gate (including `G8`) is closed, passed, or `Verified`;
- the bounded pilot is live-authorized or eligible for the next phase;
- exchange degradation is fully mitigated or will not recur.

It is a **draft** operator aid for **safe posture and review discipline** only.
