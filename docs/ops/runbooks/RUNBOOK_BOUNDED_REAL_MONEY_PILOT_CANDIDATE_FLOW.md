# RUNBOOK — Bounded Real-Money Pilot: Candidate Flow

status: OPERATOR-READY
last_updated: 2026-04-23
owner: Peak_Trade
purpose: Canonical operator sequence for the first strictly bounded real-money pilot candidate session—preconditions, bounded posture, ordered steps, abort discipline, and closeout orientation—without authorizing broad live trading or replacing dry validation, go/no-go, or incident procedures
docs_token: DOCS_TOKEN_RUNBOOK_BOUNDED_REAL_MONEY_PILOT_CANDIDATE_FLOW

## Non-authorization (read first)

This runbook is an **operator aid** only. It does **not**:

- authorize broad live trading, permanent rollout, or any gate closure;
- replace [Dry validation](RUNBOOK_BOUNDED_PILOT_DRY_VALIDATION.md), [Live entry](RUNBOOK_BOUNDED_PILOT_LIVE_ENTRY.md), [Go/No-Go checklist](../specs/PILOT_GO_NO_GO_CHECKLIST.md) / eval tooling, or org kill-switch procedures;
- prove safety from read-only CLI output or in-repo documentation alone.

If there is **any** doubt whether trading is allowed, apply [Entry Contract §5](../specs/BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md#5-abort--rollback--no_trade-criteria): **ambiguity ⇒ `NO_TRADE` / safe stop**.

## A. Purpose and boundaries

**Use this runbook as the primary path when** you are executing the **first strictly bounded real-money pilot candidate session** sequence: preconditions are met, posture is **operator-supervised** and **ambiguity-intolerant**, and you need a **single canonical step order** from final checks through start, observe, abort-if-needed, and closeout orientation.

**This runbook does not:**

- substitute **[Dry validation](RUNBOOK_BOUNDED_PILOT_DRY_VALIDATION.md)** — dry validation must already be **complete** per your procedure before this flow;
- redefine **Master V2** promotion or enablement semantics — it is **bounded-pilot operator procedure** only;
- **imply** L4/L1 or any gate is **passed** or **unblocked** in enablement report surfaces — visibility and docs alignment remain **non-authorizing** (see [Decision authority map](../specs/MASTER_V2_DECISION_AUTHORITY_MAP_V1.md) §4 / §7).

**Prefer specialized paths when:**

- **Incident or safe-stop** symptoms dominate → primary [Abort triage compass](RUNBOOK_BOUNDED_PILOT_INCIDENT_ABORT_TRIAGE_COMPASS.md) and the relevant **`RUNBOOK_PILOT_INCIDENT_*.md`** runbook.
- **End-to-end live entry mechanics** (commands, phases, German Ist-Stand detail) → [Live entry](RUNBOOK_BOUNDED_PILOT_LIVE_ENTRY.md).
- **Dry-run / validation sequence** → [Dry validation](RUNBOOK_BOUNDED_PILOT_DRY_VALIDATION.md) only — **not** this document.

## B. Triggers and entry conditions

**All of the following must already be true** before starting the candidate session sequence:

- **Dry validation completed** per [Dry validation](RUNBOOK_BOUNDED_PILOT_DRY_VALIDATION.md).
- **[Entry contract](../specs/BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md)** accepted and boundaries understood ([boundary note](../specs/BOUNDED_REAL_MONEY_PILOT_ENTRY_BOUNDARY_NOTE.md)).
- **Pilot go/no-go** verdict **acceptable** — e.g. `GO_FOR_NEXT_PHASE_ONLY` from `scripts/ops/pilot_go_no_go_eval_v1.py` per your procedure ([operational slice](../specs/PILOT_GO_NO_GO_OPERATIONAL_SLICE.md)).
- **Ops Cockpit** reviewed for at least: `policy_state`, `operator_state`, `run_state`, `incident_state`, `exposure_state`, `evidence_state`, `dependencies_state`, `stale_state`, `session_end_mismatch_state`, `human_supervision_state` (see [Entry Contract §6](../specs/BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md#6-where-to-look)).

**Fail-closed rule**

- If **any** precondition is **unknown** or **not verified**, **do not** start the candidate session — **`NO_TRADE` / safe stop** until clarified or governance directs otherwise **outside** this document.

## C. Operator sequence (ordered)

**Required posture throughout:** operator-supervised, **strictly** bounded by configured caps, **ambiguity-intolerant**, kill-switch aware, treasury-separated, evidence-first.

1. **Confirm entry preconditions:** dry validation **complete**; go/no-go verdict **`GO_FOR_NEXT_PHASE_ONLY`** (or your org’s equivalent **acceptable** verdict); `human_supervision_state.status == operator_supervised`; **no** unresolved `stale_state`; **no** unresolved session-end mismatch; **no** unresolved transfer ambiguity; kill switch **not** active; bounded caps **present**; treasury separation **explicit**.
2. **Confirm first-session bounds:** smallest acceptable pilot scope only; **no** broad-rollout interpretation; **no** informal cap widening; **no** relaxed operator posture; **no** hidden dependency on missing evidence.
3. **Start the first candidate session** only under **explicit** operator observation. **Concrete commands:** follow [Live entry](RUNBOOK_BOUNDED_PILOT_LIVE_ENTRY.md) — typically `python3 scripts/ops/run_bounded_pilot_session.py` after preconditions are verified, or `python3 scripts/run_execution_session.py --mode bounded_pilot` **only if** the **same** preconditions are already verified. During start: keep Ops Cockpit, **incident** posture, kill-switch posture, and bounded caps **visible**.
4. **Observe during session:** continuously watch `policy_state`, `operator_state`, `incident_state`, `dependencies_state`, `evidence_state`, `exposure_state`, `stale_state`. **Any** operator uncertainty → treat as **`NO_TRADE`**.
5. **Abort immediately** if **any** holds: kill switch active; policy blocked; dependency posture beyond acceptable bounded tolerance; unresolved stale state; [unexpected exposure](RUNBOOK_PILOT_INCIDENT_UNEXPECTED_EXPOSURE.md) path; [transfer ambiguity](RUNBOOK_PILOT_INCIDENT_TRANSFER_AMBIGUITY.md); [restart mid-session](RUNBOOK_PILOT_INCIDENT_RESTART_MID_SESSION.md) without coherent handling; [session-end mismatch](RUNBOOK_PILOT_INCIDENT_SESSION_END_MISMATCH.md) evident; operator **cannot** determine allowed posture. Use org **kill-switch / safe-stop** per [Kill Switch runbook](../../risk/KILL_SWITCH_RUNBOOK.md); this runbook does not redefine that mechanism.
6. **Close out and reconcile:** perform required closeout and reconciliation; resolve mismatches before **any** next session; **do not** treat one successful candidate session as **broad** live readiness.

**Order matters:** **preconditions and bounds** before **start**; **posture** before interpreting success.

## D. Verification and stop conditions

**Suggested checks**

- Re-read [Entry Contract §5](../specs/BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md#5-abort--rollback--no_trade-criteria) when posture slips or signals conflict.
- If using read-only report/CLI outputs (e.g. via [Compass §8](RUNBOOK_BOUNDED_PILOT_INCIDENT_ABORT_TRIAGE_COMPASS.md#8-read-only-cli--report-hints-scriptsreport_live_sessionspy)), treat as **hints only**; read **disclaimers**; JSON is **not** proof of safety.

**Return toward normal (non-authorizing)**

- **No** “broad live ready” or “next phase authorized” from this runbook alone. **Only** governance or explicit org disposition **outside** this repo can authorize expansion beyond this **first** bounded candidate session narrative.
- **No** second session or **risk-increasing** follow-on while [Entry Contract §5](../specs/BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md#5-abort--rollback--no_trade-criteria) blockers or unresolved closeout/reconciliation remain.

## E. Evidence and pointers (L4 discipline)

Retain **review-oriented** material **outside** git per [L4 session-flow evidence pointer contract](../specs/MASTER_V2_BOUNDED_PILOT_L4_SESSION_FLOW_EVIDENCE_POINTER_CONTRACT_V0.md): **metadata and opaque handles only** — no full cockpit dumps, secrets, or payloads in the repository.

**Minimum narrative to record externally (conceptual)**

- Go/no-go outcome and **timestamp**; Ops Cockpit snapshot **references** at session start; session notes; incident/mismatch pointers if any; closeout and reconciliation **summary**; **final posture**.

## F. Escalation

Escalate per your **bounded-pilot governance** channel when:

- Preconditions **cannot** be confirmed, or abort criteria **fire** and disposition is **unclear**;
- Closeout or reconciliation remains **partial** or **ambiguous** after bounded steps.

State **session id** (if any), **UTC window**, and whether posture is **known**, **partially known**, or **unknown**.

## G. Related runbooks and specs

- [Entry Contract](../specs/BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md); [Entry boundary note](../specs/BOUNDED_REAL_MONEY_PILOT_ENTRY_BOUNDARY_NOTE.md)
- [Live entry](RUNBOOK_BOUNDED_PILOT_LIVE_ENTRY.md); [Dry validation](RUNBOOK_BOUNDED_PILOT_DRY_VALIDATION.md)
- [Go/No-Go checklist](../specs/PILOT_GO_NO_GO_CHECKLIST.md); [Go/No-Go operational slice](../specs/PILOT_GO_NO_GO_OPERATIONAL_SLICE.md)
- [Abort triage compass](RUNBOOK_BOUNDED_PILOT_INCIDENT_ABORT_TRIAGE_COMPASS.md)
- [Restart mid-session](RUNBOOK_PILOT_INCIDENT_RESTART_MID_SESSION.md); [Session end mismatch](RUNBOOK_PILOT_INCIDENT_SESSION_END_MISMATCH.md); [Transfer ambiguity](RUNBOOK_PILOT_INCIDENT_TRANSFER_AMBIGUITY.md); [Reconciliation mismatch](RUNBOOK_PILOT_INCIDENT_RECONCILIATION_MISMATCH.md)

**Design context (non-authorizing):** [Failure taxonomy](../specs/MASTER_V2_FAILURE_TAXONOMY_SAFE_FALLBACKS_V1.md); [Decision authority map](../specs/MASTER_V2_DECISION_AUTHORITY_MAP_V1.md).
