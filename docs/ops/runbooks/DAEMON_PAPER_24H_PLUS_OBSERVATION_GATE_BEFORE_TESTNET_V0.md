# Daemon Paper 24h+ Observation Gate Before Testnet (v0)

**Status:** ACTIVE
**Scope:** Planning and gate documentation only
**Risk:** LOW — **non-runtime**, **non-authorizing**, **no executable commands** in this document

## 1. Purpose

This runbook defines **operator gates and expectations** for a **future** multi-hour (minimum 24h) **Daemon Paper-Observation** (also referred to as a **Daemon 24h+ Paper-Test** in operator language) that may be considered **before** any later Testnet execution is even reviewed for authorization.

**Daemon Paper-Observation** here means: a **long-window paper observation** that is expected to be **attended or carried** by the repo’s **scheduler/daemon-style** operational pattern (continuous or bounded long run), as documented for operators in read-only references such as `docs/SCHEDULER_DAEMON.md` — **not** a “demo” stack, **not** Testnet, and **not** a start instruction in this file.

It exists to:

- Separate **planning and review** from **execution**
- Preserve **no-active-run** discipline between milestones
- Document what must be true **before** a separate execution handoff is allowed for a **daemon-attended** paper observation

This document **does not** start anything, **does not** authorize Testnet, and **does not** authorize a **daemon**, **scheduler**, or **paper** **run**.

## 2. Non-Authorization Statement

Following or satisfying this runbook:

- Does **not** set `testnet_authorized`, `live_authorized`, or any execution authority
- Does **not** authorize scheduler, runtime daemon, paper runtime, paper-validation, Testnet, Live, broker, or exchange paths
- Does **not** authorize orders, credential validation, network calls to trading venues, or secret handling
- Does **not** replace **separate** operator approval for any future executable artifact or start action

All flags remain **false** until explicitly changed by a **future**, **scoped** operator decision outside this document.

## 3. Current Parked Preconditions

Before using this runbook as a planning reference, the operator should treat the following as the **minimum narrative preconditions** (confirm against current evidence on disk):

- A **no-active-run** or **pre-execution parked** closeout exists for the trading stack (example milestone: Testnet pre-execution parking closeout under operator-controlled paths such as `/tmp/...`).
- **Runtime process inventory** for scheduler or timeout runners shows no unexpected matches (or any matches are classified and handled under the orphan-scheduler runbook, not this document).
- Any **prior** long **Daemon Paper-Observation** (or equivalent paper lane) is **closed** with evidence PASS and cleanup recorded, or the operator explicitly scopes a **new** observation as a separate initiative.
- **Git** context for any **future** doc or code work is explicit (branch, clean working tree policy) — this runbook does not require a particular branch for **reading** it.

If these are not true, resolve parking and classification first; do not treat this runbook as permission to plan an overlapping live window.

## 4. Required Operator Inputs Before Any Future 24h+ Daemon Paper-Observation

Before **any future** observation **start** is even scheduled, the operator must record (in writing, outside this file if needed):

- **Objective** of the Daemon Paper-Observation (what signal is being validated; success vs failure meaning)
- **Allowed mode**: **paper only**, **daemon-attended** in the operational sense above; default remains **no Live**, **no Testnet**
- **Minimum duration**: exactly 24h vs longer; rationale for longer
- **Symbol or universe scope** (non-secret descriptors only in shared docs)
- **Risk and abort posture**: what “stop early” means for this observation class, including how **scheduler/daemon orphans** will be classified if a timeout or disconnect occurs
- **Evidence layout**: which directories, manifests, or reviewer steps will prove PASS/FAIL
- **Explicit statement** that Testnet and Live remain **out of scope** for this observation unless a **different** gate package exists

Missing any of the above means the observation is **not ready to be scheduled**, regardless of tooling readiness.

## 5. Required No-Active-Run Verification Before Any Future Start

Immediately before a **future** authorized start (handoff document, not this runbook), the operator must verify:

- No stray scheduler or runtime processes for the intended stack (repeat the same **read-only** process inventory discipline used in prior closeouts).
- **Git** state matches the agreed starting point (e.g. clean `main` or named release branch per policy).
- **OUTROOT / LOGROOT** (or equivalent) for the future run are **fresh, empty, and agreed**, if the execution package uses such paths.
- Prior closeouts and parking documents are **not contradicted** by the new run’s intent.

This section describes **checks**, not commands: operators perform verification using their approved **non-secret** procedures and record results in evidence.

## 6. Duration Decision: 24h vs Longer Than 24h

- **24h** is the **default minimum** label for “short continuous Daemon Paper-Observation” when comparing against prior long paper evidence.
- **Longer than 24h** requires **explicit justification**: e.g. calendar effects, weekend coverage, rare regime capture, or stability under sustained daemon-attended load — described in prose only.
- Extending duration **does not** relax **no-order**, **no-Testnet**, or **no-Live** boundaries unless a **separate** authorization package says otherwise.

## 7. Evidence Requirements

Future evidence for this observation class should be **reviewable without secrets** in the repo:

- Time-bounded **runs** (started only after separate approval) should emit **manifests**, logs, and summaries under operator-chosen roots that are cited in closeout text.
- **PASS** requires explicit checklist completion plus artifact completeness per reviewer rules in effect at run time.
- **FAIL** requires recorded reason, scope of impact, and confirmation that **no** unauthorized execution path was entered.

This runbook does not define tooling invocations.

## 8. Abort / STOP Conditions

Abort planning or **do not** proceed toward scheduling if:

- Operator intent is ambiguous or **Testnet/Live** is mixed into a **Daemon Paper-Observation** without a separate gate
- Credential validation or venue connectivity is **required** to “prove” readiness for a step that should remain doc-only
- **No-active-run** is not satisfied or process inventory shows **unclassified** runtime matches
- Evidence expectations would require **secrets in git** or public channels
- Any party requests **executable** output from **this** planning slice (this runbook stays non-executable)

During a **future** observation (after separate authorization), STOP per incident-stop and bounded-pilot runbooks if limits, drift, or policy triggers fire; those procedures are **not** duplicated here.

## 9. Cleanup Boundaries

- **Planning phase** (this runbook): no mandatory cleanup; operators may keep **markdown and /tmp** planning artifacts only.
- **After a future run** (authorized elsewhere): cleanup is governed by the execution package and incident/orphan runbooks; scheduler orphans are **not** auto-terminated by this document.

## 10. Relationship To Testnet Authorization

- **Testnet authorization** remains a **downstream** decision: this observation gate is a **possible** predecessor milestone, not a Testnet checklist.
- Completing a future 24h+ Daemon Paper-Observation with evidence PASS **does not** imply `TESTNET_AUTHORIZED=true`.
- Operators must still satisfy **Testnet prerequisite** and **external gate** documentation (for example `TESTNET_CHECKER_PREREQUISITES_V0.md` and related readiness reporters) **before** Testnet execution is reviewed.

## 11. Explicitly Forbidden In This Runbook

- Executable **shell** or **Python** blocks as “copy-paste starts”
- Scheduler, **daemon**, or runtime **start** instructions
- Paper-validation or Testnet **launch** procedures
- Broker, exchange, order, or **network connectivity** tests
- Credential **validation** workflows or secret material
- Changes to **Master V2**, Double Play, Risk/KillSwitch, Scope/Capital, or Execution/Live gate implementations (this file is **docs-only**)
- Framing this lane as a **“demo”** observation — use **Daemon Paper-Observation** / **Daemon 24h+ Paper-Test** consistently

## 12. Future Execution Handoff Checklist

Before any **separate** execution document may be honored, confirm:

- [ ] All sections 4–7 inputs are **written** and agreed
- [ ] No-active-run verification (section 5) is **passed** for the target environment narrative
- [ ] Duration and STOP posture (sections 6–8) are **explicit**
- [ ] Evidence layout (section 7) matches reviewer expectations
- [ ] Testnet and Live remain **explicitly unauthorized** unless a **different** signed-off package overrides
- [ ] **Executable** artifact, if any, has its **own** operator approval and **does not** reference this file as a start trigger

## References (read-only pointers)

- `docs/SCHEDULER_DAEMON.md` — scheduler/daemon vocabulary and boundaries (read-only context for “daemon-attended” paper planning)
- `docs/ops/runbooks/TESTNET_CHECKER_PREREQUISITES_V0.md` — read-only Testnet prerequisite declaration (non-authorizing)
- `docs/ops/runbooks/ORPHAN_SCHEDULER_AFTER_RUN_WITH_TIMEOUT_V0.md` — orphan scheduler handling after bounded timeout (classification discipline)

---

**Last Updated:** 2026-05-11
**Maintainer:** ops
