# RUNBOOK — Pilot Incident: Unexpected Exposure

status: OPERATOR-READY
last_updated: 2026-04-23
owner: Peak_Trade
purpose: Operator response when position or notional exposure is outside the intended bounded pilot envelope, when exposure grows without an operator-trusted explanation, or when exposure relative to caps cannot be established; fail-closed until classified or governance directs otherwise outside this document
docs_token: DOCS_TOKEN_RUNBOOK_PILOT_INCIDENT_UNEXPECTED_EXPOSURE

## Non-authorization (read first)

This runbook is an **operator aid** only. It does **not**:

- authorize live trading, resume a session, or close any gate;
- replace the [Entry Contract](../specs/BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md), governance decisions, or org kill-switch procedures;
- prove safety from read-only CLI output or in-repo documentation alone.

If there is **any** doubt whether trading is allowed, apply [Entry Contract §5](../specs/BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md#5-abort--rollback--no_trade-criteria): **ambiguity ⇒ `NO_TRADE` / safe stop**.

## A. Purpose and boundaries

**Use this runbook as the primary path when** cap or envelope surprise is the **dominant** problem: you know or strongly suspect **“too much / wrong shape / unknown size”** relative to the **intended bounded pilot envelope**, not merely that one feed is slow. Symptom routing: [Abort triage compass §5.2](RUNBOOK_BOUNDED_PILOT_INCIDENT_ABORT_TRIAGE_COMPASS.md#52-exposure-or-cap-surprise).

**In this context, “unexpected exposure” means:** observed or inferred **position / notional / risk** sits **outside** that envelope, **grows** without an operator-trusted explanation, or **cannot be reconciled** to configured caps quickly enough to justify continued risk-taking.

**Prefer a different primary path when:**

- **Local vs broker truth disagrees** and the first job is systematic comparison of orders, fills, positions, or balances → start with [Reconciliation mismatch](RUNBOOK_PILOT_INCIDENT_RECONCILIATION_MISMATCH.md); return here if exposure **remains** unexplained after partial reconciliation.
- **Disagreement is narrowly at session end / closeout boundary** → [Session end mismatch](RUNBOOK_PILOT_INCIDENT_SESSION_END_MISMATCH.md).
- **Funding / transfer status** is the unknown → [Transfer ambiguity](RUNBOOK_PILOT_INCIDENT_TRANSFER_AMBIGUITY.md).
- **Venue path unhealthy** (timeouts, rejects, unreliable acks) without a cap surprise yet → [Exchange degraded](RUNBOOK_PILOT_INCIDENT_EXCHANGE_DEGRADED.md); **overlap is common** — stabilize venue **and** hold `NO_TRADE` if exposure is unclear.
- **Observability / evidence continuity** is the main gap **without** a crisp cap/envelope narrative → [Telemetry degraded](RUNBOOK_PILOT_INCIDENT_TELEMETRY_DEGRADED.md); if **exposure** doubt dominates, keep **this** runbook primary.
- **Process restart / cold local state** mid-session → [Restart mid-session](RUNBOOK_PILOT_INCIDENT_RESTART_MID_SESSION.md); return here if **envelope** truth remains the open question after continuity rebuild.
- **Kill switch already active** as the org-wide control → follow [Kill Switch runbook](../../risk/KILL_SWITCH_RUNBOOK.md) and remain `NO_TRADE`; use this runbook **additionally** if you must **characterize** unexpected exposure for evidence and escalation.
- **Symptom routing** → [Abort triage compass](RUNBOOK_BOUNDED_PILOT_INCIDENT_ABORT_TRIAGE_COMPASS.md).

## B. Triggers and entry conditions

**Observable triggers and symptoms**

- Reported or displayed **position / notional / margin** **exceeds** intended pilot cap or **violates** the **bounded** envelope you expect for this session.
- **Exposure grows** (fills, deltas, or risk measures) **without** an operator-understood cause, or **faster** than the planned pilot scope allows.
- **Configured caps** (`exposure_state.caps_configured` and related cockpit fields) **do not match** what risk limits **should** be, or caps **cannot be read** while trading is still possible.
- **Operator cannot answer** “are we within the pilot envelope?” within a short, bounded check — treat as exposure uncertainty (see [Entry Contract §5](../specs/BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md#5-abort--rollback--no_trade-criteria)).

**Read-models / hints that should raise suspicion (not proof)**

- `abort_triage_hints` or closeout/lifecycle JSON from `scripts/report_live_sessions.py` pointing at **exposure**, **reconciliation**, or **bounded-posture** ambiguity — **read-only navigation**; not authorization (see [Compass §8](RUNBOOK_BOUNDED_PILOT_INCIDENT_ABORT_TRIAGE_COMPASS.md#8-read-only-cli--report-hints-scriptsreport_live_sessionspy)).
- **Stale or inconsistent** `stale_state`, `run_state`, or `exposure_state` relative to broker-trusted snapshots.

**Typical mis-shapes that belong here**

- “We are **larger** / **different instruments** than the pilot allows.”
- “**Unknown** net after a burst of activity or a tooling glitch.”
- “**Caps say X**, **broker says Y**, and **Y is worse** for the pilot envelope.”

**Typical mis-shapes that do *not* belong here alone**

- Pure **session-end closeout row** disagreement with no mid-session cap surprise → session-end runbook first.
- **Transfer not landed** → transfer runbook first.
- **Only** connectivity / rate-limit noise **without** exposure doubt → exchange degraded first (still `NO_TRADE` if ambiguity exists).

**Fail-closed rule**

- If **envelope or cap truth** is **unclear** after a bounded check, treat as **`ambiguous`**: **`NO_TRADE`** and **freeze** risk expansion until classification improves or governance directs otherwise **outside** this document.

## C. Immediate actions (ordered)

1. **Stop new risk immediately:** **`NO_TRADE`** and **no deliberate new positions** or size increases. If org procedure requires an explicit **kill-switch / safe-stop** posture, apply it per [Kill Switch runbook](../../risk/KILL_SWITCH_RUNBOOK.md) — this runbook does not redefine that mechanism.
2. **Freeze the scene:** note **UTC time**, **session id**, **operator**, and **what changed** (last known good envelope vs now). Do **not** “trade through” to fix.
3. **Snapshot visibility (read-only):** pull bounded-pilot **overview / closeout / lifecycle** JSON **after** posture is safe, not instead of stopping risk — see §E and [Compass §8](RUNBOOK_BOUNDED_PILOT_INCIDENT_ABORT_TRIAGE_COMPASS.md#8-read-only-cli--report-hints-scriptsreport_live_sessionspy). Read embedded **disclaimers**; JSON is **not** proof of safety.
4. **Establish broker-trusted truth:** use the **same broker/exchange channels** your reconciliation discipline already relies on; do **not** trust a single local pane if it disagrees with broker authority for size.
5. **Classify:** **`reconciled_explainable`** / **`partial`** / **`ambiguous`** (see §D). If **`partial`** or **`ambiguous`**, **remain** `NO_TRADE` and **escalate** per §F.
6. **Record external evidence** per [L5 incident / safe-stop pointer contract](../specs/MASTER_V2_BOUNDED_PILOT_L5_INCIDENT_SAFE_STOP_EVIDENCE_POINTER_CONTRACT_V0.md) (handles **outside** git; **no** log dumps in-repo).

**Order matters:** **posture before investigation**, **broker truth before “we’re fine”**, **external pointers for review bundles**.

**Containment reminders:** Do **not** “roll forward” by widening caps or interpreting JSON hints as approval. Do **not** delete or rewrite registry rows to **match** a desired story; if registry and truth disagree, involve [Reconciliation mismatch](RUNBOOK_PILOT_INCIDENT_RECONCILIATION_MISMATCH.md) and escalation. **Broker‑protective actions** (flatten, hedge, cancel working orders) follow **org trading policy** and kill-switch playbooks — this runbook **does not** prescribe specific market actions.

## D. Verification and classification

**Signal → suspicion → confirmation (lens)**

- **Signal:** UI, alert, metric, or JSON hint that something may be wrong.
- **Suspicion:** operator judgment that exposure may be **out of envelope** or **unknown**.
- **Confirmation:** **consistent** story across **cockpit / registry / broker-trusted** views (as applicable) that exposure is **within** envelope **or** **bounded and explained**; or a **governance-accepted** disposition recorded **outside** this repo.

**Classification (operational)**

- **Reconciled explainable:** broker-trusted exposure is **within** the intended pilot envelope **or** the **delta** is **fully explained** by a known, operator-trusted cause **without** residual cap doubt — **still** no authorization from this document to resume.
- **Partial:** some checks align, but caps, notionals, or margin story **not** fully settled — **cannot** justify the next risk-increasing step.
- **Ambiguous:** contradictory views, **unknown** net vs envelope, or **cannot** complete verification in bounded time — **unsafe** to extend risk.

**Suggested order**

1. Confirm **kill-switch / policy** posture: if **blocked**, you still must **understand exposure** for escalation, but **do not** bypass org controls.
2. Compare **intended caps** (configured caps, pilot plan) to **broker-trusted** position / notional / margin.
3. Use **read-only** session reports to **correlate** session id, registry row, and closeout/lifecycle hints — not to **override** broker truth.
4. If **reconciliation** explains the delta **without** cap violation, **hand off** to [Reconciliation mismatch](RUNBOOK_PILOT_INCIDENT_RECONCILIATION_MISMATCH.md) as primary narrative; **do not** resume trading while [Entry Contract §5](../specs/BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md#5-abort--rollback--no_trade-criteria) blocks.
5. If **after** checks exposure is **still** unclear or **out of envelope**, treat as **unresolved** — §F.

**Suggested checks**

- Re-pull **bounded-pilot** overview / lifecycle / closeout JSON **read-only** after posture is safe — see [Compass §8](RUNBOOK_BOUNDED_PILOT_INCIDENT_ABORT_TRIAGE_COMPASS.md#8-read-only-cli--report-hints-scriptsreport_live_sessionspy); read **disclaimers**; JSON is **not** proof of safety.
- If **observability** alone is the gap, pivot triage context to [Telemetry degraded](RUNBOOK_PILOT_INCIDENT_TELEMETRY_DEGRADED.md) while holding **`NO_TRADE`** if exposure is unclear.

**Return toward normal (non-authorizing)**

- **No** “resume trading” from this runbook alone after **`partial`** / **`ambiguous`**. **Only** governance or explicit org disposition **outside** this repo can authorize continuation.
- **May treat as stabilized for *this incident slice* only** when **all** hold: broker-trusted exposure is **within** envelope **or** **fully explained** and **accepted** under **external** governance (record via **L5** pointers); **no** remaining Entry Contract §5 blockers you are aware of; operator of record can **state** **final classification** and **posture** without contradiction across cockpit, broker, and registry snapshots used.
- If **`reconciled_explainable`**, posture still follows [Entry Contract §5](../specs/BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md#5-abort--rollback--no_trade-criteria) and [Failure taxonomy §6](../specs/MASTER_V2_FAILURE_TAXONOMY_SAFE_FALLBACKS_V1.md#6-ambiguity-confusion-and-interpretation-risk-map); this runbook does not grant go-ahead.
- **Do not continue** when you would need to **assume** away ambiguity, or when read-only JSON or gate-index snippets **look green** but **contradict** broker-trusted exposure — visibility is **not** authorization ([Decision authority map §4 / §7](../specs/MASTER_V2_DECISION_AUTHORITY_MAP_V1.md); [Gate index G8](../specs/MASTER_V2_FIRST_LIVE_GATE_STATUS_INDEX_V1.md) is **not** a substitute for exposure truth).

## E. Evidence and pointers (L5 discipline)

Use **existing** operator surfaces; do **not** invent new artifact types in git.

| Source | Role |
|--------|------|
| Ops Cockpit / supervision payloads | Authoritative **operator** state: `exposure_state` (including caps), `run_state`, `stale_state`, `session_end_mismatch_state`, `policy_state`, `operator_state`, `incident_state`, `human_supervision_state` — see [Entry Contract §6](../specs/BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md#6-where-to-look) |
| Broker / exchange consoles & statements | **Broker-trusted** size, fills, positions, margin |
| `python scripts/report_live_sessions.py` | **Read-only** bounded-pilot snapshots; prefer `--json` and read `disclaimer` fields |
| `python scripts/report_live_sessions.py --bounded-pilot-operator-overview [--json]` | Combined operator snapshot |
| `python scripts/report_live_sessions.py --bounded-pilot-closeout-status-summary [--json]` | Closeout signals and `abort_triage_hints` |
| `python scripts/report_live_sessions.py --bounded-pilot-lifecycle-consistency [--json]` | Lifecycle consistency and `abort_triage_hints` |
| `python scripts/report_live_sessions.py --open-sessions [--bounded-pilot-only] [--json]` | Registry `started` rows |
| `python scripts/ops/check_bounded_pilot_readiness.py` | Canonical **read-only** preflight bundle (does **not** replace incident verification) |
| [L5 pointer contract](../specs/MASTER_V2_BOUNDED_PILOT_L5_INCIDENT_SAFE_STOP_EVIDENCE_POINTER_CONTRACT_V0.md) | **External** evidence handles after stabilization |

Capture review material **outside** git per the L5 contract: **metadata and opaque handles only** — no log dumps, secrets, or raw payloads in the repository.

**Minimum narrative to record externally (conceptual)**

- **Trigger** (cap/envelope symptom, first observation).
- **Intended cap / envelope** vs **broker-trusted numbers** (categories only as appropriate).
- **Cockpit/registry snapshot references** (handles only).
- **Classification** (`reconciled_explainable` / `partial` / `ambiguous`).
- **Final posture** and **escalation id / owner** if any.

## F. Escalation

Escalate when **any** holds:

- Exposure is **still unknown**, **out of envelope**, or **classification is partial** after initial checks.
- **Policy / kill-switch / evidence** posture is degraded such that you cannot **verify** caps.

**Internal:** pilot owner / governance per bounded-pilot path; state **symptom class**, **UTC window**, **session id**, and whether exposure is **known**, **partially known**, or **unknown**.

**External:** only per org rules; **no** secrets or unnecessary identifiers in unsecured channels.

## G. Related runbooks

- [Reconciliation mismatch](RUNBOOK_PILOT_INCIDENT_RECONCILIATION_MISMATCH.md)
- [Session end mismatch](RUNBOOK_PILOT_INCIDENT_SESSION_END_MISMATCH.md)
- [Exchange degraded](RUNBOOK_PILOT_INCIDENT_EXCHANGE_DEGRADED.md)
- [Telemetry degraded](RUNBOOK_PILOT_INCIDENT_TELEMETRY_DEGRADED.md)
- [Transfer ambiguity](RUNBOOK_PILOT_INCIDENT_TRANSFER_AMBIGUITY.md)
- [Restart mid-session](RUNBOOK_PILOT_INCIDENT_RESTART_MID_SESSION.md)
- [Abort triage compass](RUNBOOK_BOUNDED_PILOT_INCIDENT_ABORT_TRIAGE_COMPASS.md)
- [Kill Switch runbook](../../risk/KILL_SWITCH_RUNBOOK.md)

**Design context (non-authorizing):** [Entry Contract §5](../specs/BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md#5-abort--rollback--no_trade-criteria); [L5 incident / safe-stop evidence pointers](../specs/MASTER_V2_BOUNDED_PILOT_L5_INCIDENT_SAFE_STOP_EVIDENCE_POINTER_CONTRACT_V0.md); [Failure taxonomy](../specs/MASTER_V2_FAILURE_TAXONOMY_SAFE_FALLBACKS_V1.md#4-failure-taxonomy-table).
