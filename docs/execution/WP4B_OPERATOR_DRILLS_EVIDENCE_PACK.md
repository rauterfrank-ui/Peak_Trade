# WP4B — Operator Drills & Evidence Pack (Manual-Only)

## Purpose
WP4B defines a repeatable set of operator drills and a structured evidence pack to validate:
- governance lock behavior,
- execution pipeline safety defaults,
- failure-mode handling,
- reconciliation / audit readiness,
- operator runbook ergonomics.

This work package is documentation-only and does not enable live trading.

## Scope
In scope:
- Drill catalog (D1–D8) with objectives, preconditions, procedure, expected results, evidence artifacts, pass/fail criteria.
- Evidence pack structure and templates.
- Operator sign-off semantics.
- Minimal verification commands (discovery-based).

Out of scope:
- Any configuration that enables live trading.
- Automated strategy switching.
- Exchange credential handling.

## Dependencies
- WP4A: docs/execution/WP4A_LIVE_READINESS_GOVERNANCE_LOCK_PACKET.md

## Definitions
- Drill: A controlled, rtable procedure validating a safety or operability invariant.
- Evidence Pack: A structured collection of outputs proving drill execution and results.
- Manual-Only: Operator-triggered execution; no unattended enablement.

## Evidence Pack Structure
Recommended operator-managed folder naming (may be untracked):
- artifacts/wp4b/YYYY-MM-DD/<DRILL_ID>/...

Recommended evidence items:
- Command transcript (copy/paste output)
- Context snapshot (sanitized)
- Audit/recon summaries
- Decision log (pass/fail + rationale)
- Sign-off block (two-person if available)

---

## Drill Catalog

### D1 — Governance Lock / Default Blocked
Objective: Confirm the system defaults to a blocked posture (e.g., ExecutionMode.LIVE_BLOCKED semantics) and requires explicit governance for any mode transition.

Preconditions:
- Repo at intended commit/branch.
- No secrets present; no external exchange actions.

Procedure (discovery-first):
1) Locate governance/no-go entry points:
   - rg -n "go_no_go|go/no-go|GONOGO|GO_NO_GO" -S src/ocs/
2) Locate execution-mode enums/flags:
   - rg -n "ExecutionMode|LIVE_BLOCKED|LIVE" -S src/
3) Confirm docs describe default-blocked posture without enablement statements.

Expected:
- Clear reference to a default blocked mode (e.g., LIVE_BLOCKED) or equivalent.
- No "enable by default" phrasing.

Evidence:
- Output of the rg commands (top matches).
- Short operator note: where default-blocked posture is defined.

Pass/Fail:
- PASS if default-blocked posture is evident and policy-safe.
- FAIL if enable-by-default phrasing appears.

---

### D2 — Dry-Run Order Lifecycle (No External Effects)
Objective: Validate pipeline stage sequencing and idempotency behavior in a dry-run/simulated mode.

Procedure (discovery-first):
1) Locate orchestrator / pipeline stages:
   - rg -n "orchestrator|Pipeline|stage|Intent Intake" -S src/execution docs/
2) Identify any existing dry-run runner scripts:
   - rg -n "dry.?run|simulat|replay|drill" -S scripts/ src/
3) If a runner exists, execute it exactly as documented (doot invent flags).

Expected:
- Stage sequencing visible in logs/output.
- Duplicate idempotency key handled deterministically.

Evidence:
- Command + output excerpt showing stage progression.
- Idempotency behavior capture (duplicate handled as expected).

Pass/Fail:
- PASS if sequencing and idempotency are demonstrated without external side effects.
- FAIL otherwise.

---

### D3 — Risk Gate Reject Path
Objective: Demonstrate that a risk gate refusal prevents downstream execution and yields consistent reason codes.

Procedure:
- Discover risk gate components and reason code enums:
  - rg -n "Risk|risk gate|ReasonCode|REJECT" -S src/ docs/

Expected:
- Reject flow exists; downstream stages do not proceed after reject.

Evidence:
- References to risk gate + reason codes.
- If a test/runner exists: excerpt showing reject path.

---

### D4 — Kill Switch / Emergency Stop (Operator Action)
Objective: Validate operator emergency stop semantics and audit trail references.

Procedure (discovery-first):
- rg -nll.?switch|emergency|stop trading|halt" -S src/ docs/

Expected:
- Clear operator-facing stop action exists.
- Audit/event log reference present.

Evidence:
- Locations of stop semantics + expected log artifacts.

---

### D5 — Reconciliation / Audit Gate Readiness
Objective: Confirm reconciliation/audit gates can be executed and produce summary output suitable for go/no-go processes.

Procedure:
- Discover recon/audit scripts and docs:
  - rg -n "recon|reconciliation|audit gate|ReconDiff" -S scripts/ docs/ src/

Expected:
- A summary mode exists (text or json) OR docs specify required outputs.

Evidence:
- Entry points and expected output notes.

---

### D6 — Failure Injection: Feed/Transport Outage
Objective: Validate safe degradation (no uncontrolled execution) when inputs degrade.

Procedure:
- Discover offline feed / fallback behaviors:
  - rg -n "OfflineRealtimeFeed|fallback|degrade|circuit" -S src/ docs/

Expected:
- Safe stop / bounded behavior described.

Evidence:
- References and operator no

---

### D7 — Duplicate Event Handling / Replay Safety
Objective: Validate deterministic handling of duplicated acks/fills and replay semantics.

Procedure:
- Discover idempotency enforcement:
  - rg -n "idempotency|dedup|replay|correlation_id" -S src/ docs/

Expected:
- Explicit idempotency key / correlation ID usage documented or implemented.

Evidence:
- Code/doc references; test or runner evidence if present.

---

### D8 — Operator Runbook Ergonomics & Sign-Off
Objective: Ensure drills are executable with clear evidence expectations and sign-off fields.

Procedure:
- Validate each drill includes: objective, procedure, expected, evidence, pass/fail.
- Confirm evidence template exists: docs/execution/WP4B_EVIDENCE_PACK_TEMPLATE.md

Expected:
- Template is complete and usable.
- Minimal unknowns; discovery commands present.

Evidence:
- Filled example block (one drill) OR template review notes.

---

## Acceptance Criteria
- AC1: WP4B doc exists with D1–D8 drills.
- AC2: Every drill has objective,dure, expected, evidence, pass/fail.
- AC3: Evidence template exists and is referenced.
- AC4: Policy-safe wording (no enablement-by-default).
- AC5: Optional index/roadmap updates only if targets exist (avoid broken links).

## Notes (Policy-Safe)
This document describes validation steps and evidence capture. It does not enable live trading and must not be interpreted as operational authorization.
