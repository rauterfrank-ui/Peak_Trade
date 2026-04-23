# RUNBOOK — Bounded Pilot Dry Validation

status: OPERATOR-READY
last_updated: 2026-04-23
owner: Peak_Trade
purpose: Canonical operator sequence for dry validation before any bounded real-money pilot session—chaining drills, go/no-go eval, and execution-session dry-run using existing scripts—without authorizing live trading, replacing live entry or candidate flow, or asserting L1 closure in enablement surfaces
docs_token: DOCS_TOKEN_RUNBOOK_BOUNDED_PILOT_DRY_VALIDATION

## Non-authorization (read first)

This runbook is an **operator aid** only. It does **not**:

- authorize a **real-funds** bounded pilot session, broad live trading, or any gate closure;
- replace [Live entry](RUNBOOK_BOUNDED_PILOT_LIVE_ENTRY.md), [Candidate flow](RUNBOOK_BOUNDED_REAL_MONEY_PILOT_CANDIDATE_FLOW.md), [Go/No-Go checklist](../specs/PILOT_GO_NO_GO_CHECKLIST.md) / eval semantics, incident runbooks, or org kill-switch procedures;
- prove safety from read-only CLI output or in-repo documentation alone;
- **imply** that **L1** or any enablement gate is **passed**, **unblocked**, or **verified** in [First-live gate status report surface](../specs/MASTER_V2_FIRST_LIVE_ENABLEMENT_GATE_STATUS_REPORT_SURFACE_V1.md) or elsewhere—interpretation and authority remain **outside** this document (see [Decision authority map](../specs/MASTER_V2_DECISION_AUTHORITY_MAP_V1.md) §4 / §7).

If there is **any** doubt whether trading is allowed, apply [Entry Contract §5](../specs/BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md#5-abort--rollback--no_trade-criteria): **ambiguity ⇒ `NO_TRADE` / safe stop**.

## A. Purpose and boundaries

**Use this runbook as the primary path when** you must run the **documented dry-validation chain** before a bounded real-money pilot: **live dry-run drills** → **pilot go/no-go eval** → **`run_execution_session.py --dry-run`**, using existing repo scripts and **no** new orchestration.

**This runbook does not:**

- start a **live** bounded pilot session or call `run_execution_session` **without** `--dry-run` for validation purposes—that is [Live entry](RUNBOOK_BOUNDED_PILOT_LIVE_ENTRY.md) / [Candidate flow](RUNBOOK_BOUNDED_REAL_MONEY_PILOT_CANDIDATE_FLOW.md) after preconditions are met;
- redefine **Master V2** promotion or enablement semantics—it is **bounded-pilot dry procedure** only;
- substitute human judgment on ambiguous go/no-go or policy posture.

**Prefer specialized paths when:**

- **End-to-end live entry** (German Ist-stand, phases, real session start) → [Live entry](RUNBOOK_BOUNDED_PILOT_LIVE_ENTRY.md) (Phase A references this sequence).
- **First candidate session narrative** (post-dry) → [Candidate flow](RUNBOOK_BOUNDED_REAL_MONEY_PILOT_CANDIDATE_FLOW.md).
- **Incident or safe-stop** symptoms → [Abort triage compass](RUNBOOK_BOUNDED_PILOT_INCIDENT_ABORT_TRIAGE_COMPASS.md) and **`RUNBOOK_PILOT_INCIDENT_*.md`**.

**Scope:** docs-only. Uses existing scripts and gates; **no** new runtime orchestration in this slice.

## B. Triggers and entry conditions

**Typical triggers**

- Operator intends a **bounded real-money** pilot and must complete **dry validation** first.
- [Live pilot execution plan](live_pilot_execution_plan.md) and related plans expect **dry-run-first** discipline; this runbook defines the **ordered** check sequence.

**Preconditions (before Step 1)**

- Repo on `main` (or org-approved branch).
- Config loadable: e.g. `config/config.toml` (or `PEAK_TRADE_CONFIG_PATH` / `CONFIG_PATH` per your env).
- Ops Cockpit payload buildable: `build_ops_cockpit_payload()` succeeds (as required by go/no-go eval).

**Fail-closed rule**

- If **any** precondition is **unknown** or **not verified**, **do not** treat later steps as satisfied—**stop** and resolve **before** asserting dry validation complete.

## C. Operator sequence (ordered)

**Minimum required path:** complete **Steps 1–3** successfully before any real-funds pilot. **Steps 4–5** are **optional** pre-checks.

**Abort discipline:** any step **fails** or outcome is **unacceptable** → **stop**; do not proceed down the sequence; fix blockers or escalate **per org** (this document does not authorize retry or waiver).

1. **Live drills (Phase 73)** — validate gating and dry-run behavior.

   ```bash
   python3 scripts/run_live_dry_run_drills.py
   ```

   **Expected:** all scenarios pass; exit **0**; no config changes, no orders, no API calls.  
   **If any drill fails:** **stop**; fix gates/config before retry.

2. **Pilot go/no-go eval** — evaluate cockpit payload against [PILOT_GO_NO_GO_CHECKLIST](../specs/PILOT_GO_NO_GO_CHECKLIST.md).

   ```bash
   python3 scripts/ops/pilot_go_no_go_eval_v1.py
   ```

   **Expected:** `verdict=GO_FOR_NEXT_PHASE_ONLY` or `verdict=CONDITIONAL` (**no** `FAIL`).  
   **If `verdict=NO_GO`:** **stop**; inspect `--json`; fix blockers (caps, treasury separation, human supervision, etc.) before retry.  
   **Note:** [Live entry](RUNBOOK_BOUNDED_PILOT_LIVE_ENTRY.md) expects **`GO_FOR_NEXT_PHASE_ONLY`** for **real-funds entry**; if you hold `CONDITIONAL`, treat **real-funds** progression as **blocked** until disposition **outside** this runbook clarifies acceptable posture.

3. **Execution session dry-run** — validate session config and intended parameters **without** starting a live session.

   ```bash
   python3 scripts/run_execution_session.py --dry-run
   ```

   (Adjust `--mode`, `--config`, etc. per your env.)  
   **Expected:** config validated; intended session logged; exit **0**; no `LiveSessionRunner` created; no registry write.  
   **If dry-run fails:** **stop**; fix config before retry.

4. **Pilot session wrapper (optional)** — if you use `run_live_pilot_session.sh`, verify gates with dry-run enforced:

   ```bash
   PT_LIVE_ENABLED=YES PT_LIVE_ARMED=YES PT_LIVE_ALLOW_FLAGS=pilot_only \
   PT_LIVE_DRY_RUN=YES PT_CONFIRM_TOKEN_EXPECTED=TOKEN PT_CONFIRM_TOKEN=TOKEN \
   scripts/ops/run_live_pilot_session.sh
   ```

   **Note:** this wrapper invokes `orchestrate_testnet_runs.py`. For session config validation, **Step 3** remains the **primary** dry-run check.

5. **Bounded pilot entry gate (optional)** — pre-entry checks **without** session start:

   ```bash
   python3 scripts/ops/run_bounded_pilot_session.py --no-invoke
   ```

   **Expected:** exit **0**; gates green; **no** `run_execution_session` handoff.  
   **If exit non-zero:** **stop**; inspect `--json` and fix blockers.

   **Critical:** omitting `--no-invoke` can start the **bounded pilot** session (`run_execution_session.py --mode bounded_pilot`)—that path belongs to **[Live entry](RUNBOOK_BOUNDED_PILOT_LIVE_ENTRY.md)**, not to dry validation alone.

**Order matters:** do **not** skip **Step 1** or **Step 2** before **Step 3** unless your org documents a **narrower** exception **outside** this repository.

## D. Verification and stop conditions

**Dry validation chain complete (minimum)** when:

- **Steps 1–3** finished with exit **0**;
- go/no-go eval shows **no** `FAIL`;
- no unintended config mutations, orders, or API calls from these steps.

**Suggested checks**

- Re-read [Entry Contract §5](../specs/BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md#5-abort--rollback--no_trade-criteria) if posture or cockpit signals conflict.
- Treat read-only CLI/report output as **hints only**; JSON is **not** proof of safety.

**Return toward normal (non-authorizing)**

- Completing this sequence **does not** mean “L1 closed”, “pilot approved”, or “next phase authorized”—only **governance** or explicit org disposition **outside** this repo can mean that.
- **Next** operational moves (real session, candidate flow, expanded scope) require **[Live entry](RUNBOOK_BOUNDED_PILOT_LIVE_ENTRY.md)** / **[Candidate flow](RUNBOOK_BOUNDED_REAL_MONEY_PILOT_CANDIDATE_FLOW.md)** and applicable evidence discipline—**not** this document alone.

## E. Evidence and pointers (L1 discipline)

Retain **review-oriented** material **outside** git where possible; use **metadata and opaque handles** only per [L1 dry-validation evidence pointer contract](../specs/MASTER_V2_BOUNDED_PILOT_L1_EVIDENCE_POINTER_CONTRACT_V0.md)—**no** full cockpit dumps, secrets, or payloads in the repository.

**Minimum artifacts to associate with this chain (conceptual)**

- Step 1: drill output (text or JSON).  
- Step 2: `pilot_go_no_go_eval_v1.py` verdict and optional `--json`.  
- Step 3: `run_execution_session.py --dry-run` log.  
- Optional: repo head, timestamp, operator identity (org policy).

## F. Escalation

Escalate per **bounded-pilot governance** when:

- Repeated failures in drills, go/no-go, or dry-run with **unclear** root cause;
- `CONDITIONAL` verdict and **unclear** whether real-funds progression is allowed;
- Optional Steps 4–5 disagree with Steps 1–3 and disposition is **ambiguous**.

State **UTC window**, **step** that failed, and whether cockpit posture is **known** or **unknown**. This runbook **does not** grant waivers.

## G. Related runbooks and specs

- [Entry Contract](../specs/BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md); [Entry boundary note](../specs/BOUNDED_REAL_MONEY_PILOT_ENTRY_BOUNDARY_NOTE.md)
- [Live entry](RUNBOOK_BOUNDED_PILOT_LIVE_ENTRY.md); [Candidate flow](RUNBOOK_BOUNDED_REAL_MONEY_PILOT_CANDIDATE_FLOW.md)
- [Go/No-Go checklist](../specs/PILOT_GO_NO_GO_CHECKLIST.md); [Go/No-Go operational slice](../specs/PILOT_GO_NO_GO_OPERATIONAL_SLICE.md)
- [Live pilot execution plan](live_pilot_execution_plan.md)
- [Abort triage compass](RUNBOOK_BOUNDED_PILOT_INCIDENT_ABORT_TRIAGE_COMPASS.md)
- **Design context (non-authorizing):** [Failure taxonomy](../specs/MASTER_V2_FAILURE_TAXONOMY_SAFE_FALLBACKS_V1.md); [Decision authority map](../specs/MASTER_V2_DECISION_AUTHORITY_MAP_V1.md); [Readiness ladder](../specs/MASTER_V2_FIRST_LIVE_ENABLEMENT_READINESS_LADDER.md)

**Explicit non-goals (unchanged in intent)**

- no new runtime orchestration script in this slice;
- no new gates;
- no replacement for operator judgment;
- no claim of pilot readiness **beyond** documenting this dry-validation sequence.
