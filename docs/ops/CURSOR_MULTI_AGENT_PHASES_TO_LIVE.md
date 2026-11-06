# Cursor Multi-Agent Runbook: Phases to Live

Purpose: Operator-facing phased runbook to progress from offline research to governed live trading using Cursor Multi-Agent workflows.

Scope:
- Operational process, evidence, and governance gates.
- Multi-agent collaboration protocol (A1/A2/A3) aligned with Peak_Trade ops.

Non-goals:
- No automatic live activation.
- No bypassing of governance or risk controls.

Related docs:
- Frontdoor: `docs/ops/CURSOR_MULTI_AGENT_RUNBOOK_FRONTDOOR.md`
- Canonical workflow: `docs/ops/CURSOR_MULTI_AGENT_WORKFLOW.md`
- Readiness tracker: `docs/ops/LIVE_READINESS_PHASE_TRACKER.md`

---

## Roles and Responsibilities

- Operator: owns final decisions, merges, releases, and production safety.
- A1 (Implementer): code changes + tests.
- A2 (Reviewer): risk, correctness, CI gates, failure-mode analysis.
- A3 (Docs/Ops): runbooks, navigation, operator UX, auditability.

RACI (default):
- Build/Implement: A1 (R), Operator (A)
- Review/Gates: A2 (R), Operator (A)
- Docs/Runbooks: A3 (R), Operator (A)

---

## Global Guardrails

- All changes must be reviewable and auditable (PR-based).
- CI must be green on required gates before merge.
- Avoid repo-relative file paths for targets that might not exist (docs-reference-targets-gate).
- Prefer discovery instructions (`rg`, `fd`) when referring to evolving locations.

---

## Phase Model (P0–P10)

Each phase has:
- Goal
- Inputs
- Tasks (A1/A2/A3)
- Evidence / DoD (Definition of Done)
- Gate / Exit criteria
- Failure modes / Recovery

### P0 — Offline Research Validated
Goal:
- Validate research outputs deterministically.

Inputs:
- Research configuration and datasets.

Tasks:
- A1: ensure deterministic run + stable outputs.
- A2: verify methodology, edge cases, reproducibility.
- A3: document operator steps + evidence locations.

Evidence / DoD:
- Repeatable runs (same inputs → same outputs).
- Tests pass relevant scope.
- Clear operator instructions to reproduce.

Gate:
- Operator confirms reproducibility and review completion.

Recovery:
- If nondeterministic: enforce stable seeds, stable sorting, stable markers.

---

### P1 — Shadow Mode Stability
Goal:
- Validate data pipeline and monitoring under shadow constraints.

Tasks:
- A1: implement/adjust shadow pipeline tooling.
- A2: verify guardrails and that "live" pathways remain blocked.
- A3: ensure runbooks include outputs and troubleshooting.

Evidence / DoD:
- Multiple shadow runs without regressions.
- Monitoring/reporting artifacts produced consistently.
- No policy violations.

Gate:
- Operator signs off stability over defined window.

---

### P2 — Paper / Simulation Trading (if applicable)
Goal:
- Validate end-to-end execution logic without market impact.

Tasks:
- A1: simulation harness improvements.
- A2: validate fills, slippage assumptions, reconciliation.
- A3: operator workflows for run/stop/rollback.

Evidence / DoD:
- Consistent reconciliation and audit logs.
- Risk policies enforced as expected.

Gate:
- Operator signs off execution correctness under simulated conditions.

---

### P3 — Live Readiness Review (Governed)
Goal:
- Confirm governance requirements satisfied before any live exposure.

Tasks:
- A1: ensure runtime gating controls are explicit and test-covered.
- A2: validate failure modes, kill-switch behavior, and guardrails.
- A3: update readiness tracker and operator playbook references.

Evidence / DoD:
- Go/No-Go criteria met and recorded.
- Required runbooks exist and are discoverable from ops index.
- CI + policy gates all green.

Gate:
- Operator governance sign-off recorded.

---

### P4 — Controlled Live (Manual-Only)
Goal:
- Minimal live exposure under strict manual control.

Tasks:
- A1: ensure manual-only controls cannot be bypassed.
- A2: verify risk caps and audit logging.
- A3: operator checklist for start/stop and incident handling.

Evidence / DoD:
- Bounded exposure, all actions audited.
- Incident drill performed (start/stop/rollback).

Gate:
- Operator signs off controlled-live stability.

---

### P5 — Expanded Live (Still Governed)
Goal:
- Gradually expand exposure and automation within pre-approved bounds.

Tasks:
- A1: incremental improvements under governance constraints.
- A2: validate metrics, alerts, regression risk.
- A3: keep runbooks current; ensure ops index remains accurate.

Evidence / DoD:
- Stability over defined time window.
- No unmitigated incidents; postmortems filed where needed.
- All gates remain green for changes.

Gate:
- Operator approval for next expansion step.

---

### P6 — Monitoring & Incident Readiness Hardening
Goal:
- Ensure operators can detect, diagnose, and respond quickly.

Evidence / DoD:
- Runbooks include clear incident response procedures.
- Alerts and diagnostics are operator-actionable.

---

### P7 — Weekly Health Discipline
Goal:
- Institutionalize predictable health checks and reviews.

Evidence / DoD:
- Weekly checks run, recorded, and reviewed.

---

### P8 — Strategy Switch Sanity Checks (Governance)
Goal:
- Validate strategy-switch configuration is safe and consistent.

Evidence / DoD:
- Sanity check tooling exists and is run as part of readiness.

---

### P9 — Bounded Automation (Optional / Governance-Approved)
Goal:
- Limited automation within strict bounds.

Evidence / DoD:
- Automated actions cannot exceed approved limits.
- Auditability and rollback are proven.

---

### P10 — Mature Live Operations
Goal:
- Stable operations with continuous governance and evidence-based iteration.

Evidence / DoD:
- Sustained stability and disciplined change management.

---

## Operator Checklist (Per Change / Per Phase Transition)

- Working tree clean.
- PR scope minimal and reviewable.
- Required CI gates green.
- Docs links are valid (docs-reference-targets-gate).
- Evidence recorded (reports/logs/decision notes).
- Rollback plan is clear and tested where relevant.

---

## Cursor Multi-Agent Execution Recipe

1) Define scope and target phase.
2) Assign A1/A2/A3 tasks with explicit DoD.
3) Run local verification.
4) Prepare PR with evidence-oriented description.
5) Merge only after gates are green and operator sign-off is recorded.

Discovery helpers:
- Find relevant docs: `rg -n "Cursor Multi-Agent|Live Readiness|Runbook" docs -S`
- Find relevant code: `rg -n "risk|go/no-go|kill|gating" src -S`
