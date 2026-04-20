# RUNBOOK — Pilot Incident: Session End Mismatch

status: DRAFT
last_updated: 2026-04-20
owner: Peak_Trade
purpose: Operator response when bounded-pilot session closeout state disagrees with broker/exchange truth at or after session end; fail-closed until reconciled or governance directs otherwise outside this document
docs_token: DOCS_TOKEN_RUNBOOK_PILOT_INCIDENT_SESSION_END_MISMATCH

## 1) Purpose, scope, and non-goals

**Purpose:** Provide a **repeatable** sequence for detecting and handling **session end / closeout mismatches** during the **first strictly bounded real-money pilot**: local or in-process closeout views that **do not align** with broker/exchange positions, balances, or fill history at the boundary of a session.

**Scope:** Bounded-pilot execution and **post-session closeout** only. This runbook does **not** define reconciliation algorithms, registry schema, or automated closeout behavior.

**Non-goals (explicit):**

- This runbook **does not** authorize the next session, live trading, or progression past entry prerequisites.
- It **does not** claim generic “incident resolved” or that closeout is **proven** correct — only **operator posture**, **classification**, and **external evidence** discipline.
- It **does not** substitute [`BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md`](../specs/BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md), governance decisions, or external sign-off.

**Canonical anchors (read-only):**

- Abort / rollback / `NO_TRADE`, including **session-end mismatch**: [Entry contract §5](../specs/BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md#5-abort--rollback--no_trade-criteria).
- Failure / safe-fallback framing: [Failure taxonomy](../specs/MASTER_V2_FAILURE_TAXONOMY_SAFE_FALLBACKS_V1.md) (evidence/provenance gap and operator-visibility rows in §4; ambiguity notes in §6).
- External **L5** pointer vocabulary (no payloads in git): [L5 incident / safe-stop pointer contract v0](../specs/MASTER_V2_BOUNDED_PILOT_L5_INCIDENT_SAFE_STOP_EVIDENCE_POINTER_CONTRACT_V0.md).

**Related material (supplementary, non-authorizing):**

- Broader reconciliation incidents: [Reconciliation mismatch runbook](RUNBOOK_PILOT_INCIDENT_RECONCILIATION_MISMATCH.md).
- Design context only: [Reconciliation flow spec](../specs/RECONCILIATION_FLOW_SPEC.md), [Pilot execution edge case matrix](../specs/PILOT_EXECUTION_EDGE_CASE_MATRIX.md).

## 2) Trigger / symptoms

Treat the situation as **session end mismatch** when **one or more** of the following hold at or immediately after **declared session end / closeout** (examples, not an exhaustive product spec):

- **Local closeout or registry snapshot** (session summary, intended flat/risk-off posture) **disagrees** with **broker/exchange** positions, balances, or open orders.
- **Reconciliation** at session end returns **partial** results, **timeouts**, or **conflicting** terminal states for orders or fills.
- **Next bounded session** or **risk-increasing steps** would rely on closeout truth that the operator **cannot** confirm.
- **Ambiguity** remains whether exposure is **flat**, **within envelope**, or **unknown** relative to the entry contract.

If the operator **cannot** reconcile closeout within a short, operator-defined verification window, treat as **unresolved mismatch** and apply §5.

## 3) Immediate safe posture

Default posture until mismatch is **clearly classified** and **externally recorded** (§7):

- **`NO_TRADE` / blocked:** do **not** start a **new** bounded session or take **new** risk-increasing actions on top of unresolved closeout (entry contract §5: *session-end mismatch is unresolved*).
- **Freeze risk expansion:** no additional symbols, size, or leverage until closeout truth is aligned or governance explicitly directs a controlled wind-down **outside** this document.
- **Prefer fail-closed:** when in doubt, remain blocked; see [Failure taxonomy §6](../specs/MASTER_V2_FAILURE_TAXONOMY_SAFE_FALLBACKS_V1.md#6-ambiguity-confusion-and-interpretation-risk-map).

## 4) Step-by-step operator actions

Execute in order unless a step is unsafe without new risk; if so, stop and escalate (§6).

1. **Confirm bounded-pilot context**  
   Re-anchor on [Entry contract §1–2 and §4](../specs/BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md); do not exceed the first bounded real-money step intent.

2. **Halt progression that assumes clean closeout**  
   Do not treat the session as “complete for pilot purposes” until mismatch is classified.

3. **Identify mismatch domain**  
   Positions vs registry, balances/cash vs internal view, open orders vs expected flat, fill history gaps — record **category labels** only in external notes, not full payloads in git.

4. **Gather broker/exchange truth**  
   Use your **operative** procedures (UI, API read paths approved for the pilot) to capture **non-secret** references to truth checks (screenshot policy, ticket IDs) under change control — **not** raw dumps into the repository.

5. **Compare to local session registry and closeout evidence trail**  
   Align timestamps, session IDs, and order IDs **only** in external systems; if comparison cannot be completed, classify as **ambiguous**.

6. **Classify**

   - **Reconciled:** single consistent story; exposure and session end state match broker truth — **still** record external pointers (§7); **resuming** any activity follows [candidate flow](RUNBOOK_BOUNDED_REAL_MONEY_PILOT_CANDIDATE_FLOW.md) / [live entry](RUNBOOK_BOUNDED_PILOT_LIVE_ENTRY.md) only per **your** authorized procedures, not by this runbook alone.  
   - **Partial:** some legs confirmed, others not — remain **`NO_TRADE` / blocked** for progression.  
   - **Ambiguous:** irreconcilable or contradictory — remain **`NO_TRADE` / blocked**; escalate (§6).

7. **Handoff**  
   If another operator continues, pass classification, open questions, and external pointer handles (§8).

## 5) Abort / `NO_TRADE` / remain-blocked conditions

Remain **blocked** and treat entry contract §5 as applicable if **any** of the following hold:

- **Session-end mismatch is unresolved** (explicit contract bullet).
- Kill switch active, policy blocked, or other §5 abort criteria apply.
- **Ambiguity** about whether trading is allowed (*ambiguity => `NO_TRADE` / safe stop*).
- **Evidence or dependency posture** is degraded beyond acceptable pilot tolerance (§5; operator judgment + governance outside this repo).

This runbook **does not** narrow §5; it operationalizes a conservative reading for **closeout disagreement**.

## 6) Escalation / communication

- **Internal:** Notify pilot owner / governance per your bounded-pilot escalation path; state **mismatch class**, **UTC window**, and whether exposure is **known**, **partially known**, or **unknown**.
- **External:** Venue or broker support only per org rules; **no** secrets, API keys, or unnecessary account identifiers in unsecured channels.
- **Do not** message “all clear” or “authorized to continue” from this runbook — only **posture** and **classification**.

## 7) Evidence handling (pointers only)

Retain material **outside** this repository. Use [L5 pointer contract §3–4](../specs/MASTER_V2_BOUNDED_PILOT_L5_INCIDENT_SAFE_STOP_EVIDENCE_POINTER_CONTRACT_V0.md#3-allowed-pointer-classes-l5) — e.g. `L5_INCIDENT_SAFE_STOP_SUMMARY_CAPTURE` and, when applicable, `L5_INCIDENT_RESPONSE_SUPPORTING_BUNDLE` — with opaque `retrieval_reference` values.

**Forbidden in git:** full registry exports, complete fill logs, ticket bodies with live identifiers, kill-switch dumps.

## 8) Exit, handoff, and unresolved conditions

**This runbook does not declare incident closure or gate completion.**

- **Reconciled classification:** External pointers recorded; **next session** is **not** implied — follow authorized procedures only.  
- **Unresolved / ambiguous:** Maintain **`NO_TRADE` / blocked** until reconciliation succeeds or governance approves a documented exception **outside** this repo.  
- **Handoff:** Transfer classification, broker-truth checklist status, and change-control anchor IDs (not secret values in-repo).

## 9) Non-authorization reminder

Using this runbook **does not** mean:

- any gate (including `G8`) is closed, passed, or `Verified`;
- the bounded pilot may proceed to the next phase;
- closeout will not recur or that broker truth is permanently trustworthy.

It remains a **draft** operator aid for **safe posture and review discipline** only.
