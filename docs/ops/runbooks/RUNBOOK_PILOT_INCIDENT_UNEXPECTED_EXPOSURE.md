# RUNBOOK — Pilot Incident: Unexpected Exposure

status: DRAFT
last_updated: 2026-04-20
owner: Peak_Trade
purpose: Operator response when position or notional exposure is outside the intended bounded pilot envelope, or when exposure relative to caps cannot be established
docs_token: DOCS_TOKEN_RUNBOOK_PILOT_INCIDENT_UNEXPECTED_EXPOSURE

## Non-authorization (read first)

This runbook is an **operator aid** only. It does **not**:

- authorize live trading, resume a session, or close any gate;
- replace the [Entry Contract](../specs/BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md), governance decisions, or org kill-switch procedures;
- prove safety from read-only CLI output or in-repo documentation alone.

If there is **any** doubt whether trading is allowed, apply [Entry Contract §5](../specs/BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md#5-abort--rollback--no_trade-criteria): **ambiguity ⇒ `NO_TRADE` / safe stop**.

## A. Purpose and boundaries

**In this context, “unexpected exposure” means:** observed or inferred **position / notional / risk** sits **outside** the **intended bounded pilot envelope**, **grows** without an operator-trusted explanation, or **cannot be reconciled** to configured caps quickly enough to justify continued risk-taking.

**Use this runbook when** cap or envelope surprise is the **primary** problem (you know or strongly suspect “too much / wrong shape / unknown size,” not merely that one feed is slow).

**Prefer a different primary path when:**

- **Local vs broker truth disagrees** and the first job is systematic comparison of orders, fills, positions, or balances → start with [Reconciliation mismatch](RUNBOOK_PILOT_INCIDENT_RECONCILIATION_MISMATCH.md); return here if exposure **remains** unexplained after partial reconciliation.
- **Disagreement is narrowly at session end / closeout boundary** → [Session end mismatch](RUNBOOK_PILOT_INCIDENT_SESSION_END_MISMATCH.md).
- **Funding / transfer status** is the unknown → [Transfer ambiguity](RUNBOOK_PILOT_INCIDENT_TRANSFER_AMBIGUITY.md).
- **Venue path unhealthy** (timeouts, rejects, unreliable acks) without a cap surprise yet → [Exchange degraded](RUNBOOK_PILOT_INCIDENT_EXCHANGE_DEGRADED.md); **overlap is common** — stabilize venue **and** hold `NO_TRADE` if exposure is unclear.
- **Kill switch already active** as the org-wide control → follow [Kill Switch runbook](../../risk/KILL_SWITCH_RUNBOOK.md) and remain `NO_TRADE`; use this runbook **additionally** if you must **characterize** unexpected exposure for evidence and escalation.

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

## C. Immediate actions (fail-closed order)

1. **Stop new risk immediately:** **`NO_TRADE`** and **no deliberate new positions** or size increases. If org procedure requires an explicit **kill-switch / safe-stop** posture, apply it per [Kill Switch runbook](../../risk/KILL_SWITCH_RUNBOOK.md) — this runbook does not redefine that mechanism.
2. **Freeze the scene:** note **time**, **session id**, **operator**, and **what changed** (last known good envelope vs now). Do **not** “trade through” to fix.
3. **Snapshot visibility (read-only):** pull bounded-pilot **overview / closeout / lifecycle** JSON **after** posture is safe, not instead of stopping risk — see §E for commands. Read embedded **disclaimers**; JSON is **not** proof of safety.
4. **Establish broker-trusted truth:** use the **same broker/exchange channels** your reconciliation discipline already relies on; do **not** trust a single local pane if it disagrees with broker authority for size.
5. **Classify:** `reconciled_explainable` / `partial` / **`ambiguous`**. If **partial** or **ambiguous**, **remain** `NO_TRADE` and **escalate** — see §G.
6. **Record external evidence** per [L5 incident / safe-stop pointer contract](../specs/MASTER_V2_BOUNDED_PILOT_L5_INCIDENT_SAFE_STOP_EVIDENCE_POINTER_CONTRACT_V0.md) (handles **outside** git; **no** log dumps in-repo).

Order matters: **posture before investigation**, **broker truth before “we’re fine”**, **external pointers for review bundles**.

## D. Verification (signal → suspicion → confirmation)

**Definitions**

- **Signal:** UI, alert, metric, or JSON hint that something may be wrong.
- **Suspicion:** operator judgment that exposure may be **out of envelope** or **unknown**.
- **Confirmation:** **consistent** story across **cockpit / registry / broker-trusted** views (as applicable) that exposure is **within** envelope **or** **bounded and explained**; or a **governance-accepted** disposition recorded **outside** this repo.

**Suggested order**

1. Confirm **kill-switch / policy** posture: if **blocked**, you still must **understand exposure** for escalation, but **do not** bypass org controls.
2. Compare **intended caps** (configured caps, pilot plan) to **broker-trusted** position / notional / margin.
3. Use **read-only** session reports to **correlate** session id, registry row, and closeout/lifecycle hints — not to **override** broker truth.
4. If **reconciliation** explains the delta **without** cap violation, **hand off** to [Reconciliation mismatch](RUNBOOK_PILOT_INCIDENT_RECONCILIATION_MISMATCH.md) as primary narrative; **do not** resume trading while [Entry Contract §5](../specs/BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md#5-abort--rollback--no_trade-criteria) blocks.
5. If **after** checks exposure is **still** unclear or **out of envelope**, treat as **unresolved** — §G.

## E. Evidence and artifact sources (repo-established only)

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

## F. Safe retreat, containment, and rollback posture

- **Default containment:** **`NO_TRADE`** and **no new risk** until exposure is **explained** or **governance-accepted** disposition exists **outside** this repository.
- **Do not** “roll forward” by widening caps or interpreting JSON hints as approval.
- **Do not** delete or rewrite registry rows to **match** a desired story; if registry and truth disagree, that is **reconciliation / integrity** territory — involve [Reconciliation mismatch](RUNBOOK_PILOT_INCIDENT_RECONCILIATION_MISMATCH.md) and escalation.
- **Broker‑protective actions** (flatten, hedge, cancel working orders) follow **org trading policy** and kill-switch playbooks — this runbook **does not** prescribe specific market actions.

## G. Exit criteria (when to stand down vs stop)

**May treat as stabilized for *this incident slice* only** when **all** hold:

- Broker-trusted exposure is **within** the **intended pilot envelope**, **or** exposure is **fully explained** and **accepted** under **external** governance (record via **L5** pointers, not free-form logs in git).
- **No** remaining [Entry Contract §5](../specs/BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md#5-abort--rollback--no_trade-criteria) blockers you are aware of.
- Operator of record can **state** the **final classification** and **posture** without contradiction across cockpit, broker, and registry snapshots used in the investigation.

**Escalate and remain `NO_TRADE` when:**

- Exposure is **still unknown**, **out of envelope**, or **classification is partial** after initial checks.
- **Policy / kill-switch / evidence** posture is degraded such that you cannot **verify** caps.

**Do not continue pilot activity when:**

- You would need to **assume** away ambiguity to resume.
- Read-only JSON or gate-index snippets **look green** but **contradict** broker-trusted exposure — visibility is **not** authorization ([Decision authority map §4 / §7](../specs/MASTER_V2_DECISION_AUTHORITY_MAP_V1.md); [Gate index G8](../specs/MASTER_V2_FIRST_LIVE_GATE_STATUS_INDEX_V1.md) is **not** a substitute for exposure truth).

## H. Cross-links

- [§5 Abort triage compass](RUNBOOK_BOUNDED_PILOT_INCIDENT_ABORT_TRIAGE_COMPASS.md) — symptom routing, CLI table, escalation defaults
- [Entry Contract §5](../specs/BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md#5-abort--rollback--no_trade-criteria) — abort / `NO_TRADE` criteria
- [Reconciliation mismatch](RUNBOOK_PILOT_INCIDENT_RECONCILIATION_MISMATCH.md), [Session end mismatch](RUNBOOK_PILOT_INCIDENT_SESSION_END_MISMATCH.md), [Exchange degraded](RUNBOOK_PILOT_INCIDENT_EXCHANGE_DEGRADED.md), [Transfer ambiguity](RUNBOOK_PILOT_INCIDENT_TRANSFER_AMBIGUITY.md)
- [Kill Switch runbook](../../risk/KILL_SWITCH_RUNBOOK.md)
- [L5 incident / safe-stop evidence pointers](../specs/MASTER_V2_BOUNDED_PILOT_L5_INCIDENT_SAFE_STOP_EVIDENCE_POINTER_CONTRACT_V0.md)
- [Failure taxonomy (non-authorizing)](../specs/MASTER_V2_FAILURE_TAXONOMY_SAFE_FALLBACKS_V1.md#4-failure-taxonomy-table)

## Evidence checklist (external record)

Capture via **L5** classes only (metadata + external handles): **trigger**, **intended cap / envelope**, **broker-trusted numbers**, **cockpit/registry snapshot references**, **classification** (`reconciled_explainable` / `partial` / `ambiguous`), **final posture**, **escalation id / owner**.
