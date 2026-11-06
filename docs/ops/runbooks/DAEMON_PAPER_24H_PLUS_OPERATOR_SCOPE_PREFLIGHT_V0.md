# Daemon Paper 24h+ Operator Scope Preflight (v0)

**Status:** ACTIVE
**Scope:** Operator decision template and preflight checklist (documentation only)
**Risk:** LOW — **non-runtime**, **non-authorizing**, **no executable content** in this document

## 1. Purpose

This note is a **workspace for operator decisions** before any **future** **Daemon Paper-Observation** or **Daemon 24h+ Paper-Test** is even considered for a separate execution handoff.

It collects what must be decided, recorded, and verified in a **no-active-run** posture. It is **not** an execution plan and **not** a substitute for the gate runbook that precedes Testnet review.

## 2. Non-Authorization Statement

Using or completing this preflight note:

- Does **not** authorize a scheduler start, runtime daemon, paper runtime, paper-validation, Testnet, Live, broker, or exchange path
- Does **not** authorize orders, credential validation, venue connectivity checks, or network calls
- Does **not** set `paper_run_authorized`, `testnet_authorized`, `live_authorized`, or any execution flag
- Does **not** replace the **separate** external approval and executable handoff required before any future start

All execution-related flags remain **false** until explicitly changed elsewhere under governance.

## 3. Relationship To Existing Gate Runbook

The canonical **gate** narrative for a future long Daemon Paper-Observation before Testnet **review** remains:

- `docs/ops/runbooks/DAEMON_PAPER_24H_PLUS_OBSERVATION_GATE_BEFORE_TESTNET_V0.md`

This **preflight** note is a **companion**: it is a place to **draft and track operator answers** (decisions, inputs, duration choice, evidence expectations) **before** any future handoff document exists. If a conflict arises, the **gate runbook** wins for gate semantics; this note wins only as a **scratch / scope worksheet** until promoted by a formal doc change.

## 4. Current Parked State

Treat the stack as **parked** unless a separate closeout or inventory says otherwise:

- **Git** on `main` (or an explicitly named branch) should be clean when **recording** decisions that might later feed a PR or handoff
- **No-active-run** should be confirmed when this note is used for serious scheduling discussion (narrative confirmation against prior closeouts and process inventory, not a command in this file)
- **Testnet** and **Live** remain **out of scope** for this workstream unless a different gate package applies

## 5. Required Operator Decisions

Before any future start is **discussed seriously**, decide and record:

- **Whether** a new Daemon Paper-Observation is **in scope at all** for this program phase, or whether parking continues
- **Primary objective** of the observation (what hypothesis or stability claim is being exercised)
- **Duration class**: 24h vs 48h vs 72h or longer — with a one-line rationale
- **Daemon-attended meaning** for this initiative (long-window paper under scheduler or bounded timeout discipline per `docs/SCHEDULER_DAEMON.md` and orphan classification runbook)
- **PASS vs FAIL** meaning at a high level (what outcomes close the observation successfully or unsuccessfully)

## 6. Required Operator Inputs

Record **non-secret** inputs only in shared documentation:

- Symbol or universe description (no account numbers, keys, or secrets)
- Expected evidence roots or naming pattern for a **future** run (conceptual only until authorized)
- Reviewer identity or role (who signs off on evidence PASS)
- Dependencies on prior closeouts (paths to parking or merge closeout artifacts under operator control)
- Explicit statement that **credential validation** and **venue connectivity** are **not** part of this preflight

## 7. Duration Options: 24h / 48h / 72h+

- **24h** — Minimum label for a full calendar-day Daemon Paper-Observation; baseline for comparing to prior long paper evidence
- **48h** — Use when two full cycles, weekend/day boundaries, or repeated scheduler windows matter for stability narrative
- **72h+** — Use only with **written** justification (sustained load, rare regime coverage, extended drift watch). Longer windows increase operational burden and orphan-handling probability; they do **not** relax Testnet or Live gates

## 8. Evidence Requirements

Expect **future** evidence (only after a separate authorized run) to be reviewable **without secrets**:

- Time-bounded observation window recorded with UTC bounds
- Manifests or summaries that prove the daemon-attended paper path behaved within declared scope
- Runtime or scheduler inventory snapshots taken under the same read-only discipline as prior operator closeouts
- PASS/FAIL narrative tied to section 5 decisions
- Confirmation that forbidden paths (Testnet, Live, orders, credential probes) were not entered

This note does not prescribe filenames or tooling.

## 9. No-Active-Run Preflight Requirements

Before any **future** authorized start, a separate preflight (handoff package, not this note) must confirm:

- No unclassified scheduler, timeout-runner, or paper-runtime matches for the intended scope
- Prior parking and merge closeouts are consistent with starting a **new** initiative
- Git revision and branch policy for that future run are explicit
- Output and log roots for that future run are agreed to be **fresh** and **empty** at start (conceptual requirement)

## 10. STOP / Abort Conditions

Stop filling this note or abort progression toward scheduling if:

- Intent mixes **Testnet** or **Live** into a Daemon Paper-Observation without a separate gate
- Anyone requires **network proof**, **credential checks**, or **orders** to “validate” this preflight
- **No-active-run** cannot be honestly asserted
- Evidence plans would place secrets in git or public channels
- This note is mistaken for **authorization** or treated as containing **start** steps

## 11. Cleanup And Orphan-Process Boundaries

- **While editing this note only** — no cleanup obligation; no process actions
- **After a future authorized run** — cleanup, orphan classification, and scoped termination follow `docs/ops/runbooks/ORPHAN_SCHEDULER_AFTER_RUN_WITH_TIMEOUT_V0.md` and incident-stop runbooks, not this document

## 12. Relationship To Future Testnet Review

Completing this preflight **does not** advance Testnet readiness. Testnet remains gated by prerequisite declarations, external operator records, and execution policy **elsewhere**. A successful future Daemon Paper-Observation might inform **confidence**, but it is **not** a Testnet approval vector.

## 13. Explicitly Forbidden By This Note

- Executable instructions, shell fragments, or copy-paste command lists
- Scheduler, daemon, paper-runtime, or validation **starts**
- Testnet, Live, broker, exchange, order, or connectivity paths
- Credential or secret handling
- Changes to Master V2, Double Play, Risk/KillSwitch, Scope/Capital, or Execution/Live gate **implementations** (this file is documentation only)

## 14. Future Handoff Checklist

Before any **separate** execution handoff is accepted (outside this note):

- [ ] Sections 5–8 are **filled** and agreed among operators
- [ ] Duration choice (section 7) matches written rationale
- [ ] No-active-run narrative (section 9) is satisfied for the target environment story
- [ ] STOP conditions (section 10) are explicitly acknowledged
- [ ] Testnet and Live remain **unauthorized** unless another package overrides
- [ ] Executable handoff, if any, **does not** cite this note as the start trigger

## References (read-only pointers)

- `docs/ops/runbooks/DAEMON_PAPER_24H_PLUS_OBSERVATION_GATE_BEFORE_TESTNET_V0.md`
- `docs/SCHEDULER_DAEMON.md`
- `docs/ops/runbooks/ORPHAN_SCHEDULER_AFTER_RUN_WITH_TIMEOUT_V0.md`

---

**Last Updated:** 2026-05-11
**Maintainer:** ops
