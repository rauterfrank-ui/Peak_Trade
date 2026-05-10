# Orphan Scheduler after run_with_timeout v0

**Status:** ACTIVE  
**Scope:** Diagnostic and **cleanup decision guide** only (no commands in this document perform cleanup)  
**Risk:** LOW — documentation only; **non-runtime** and **non-authorizing**

## Purpose and boundaries

After a bounded scheduler Paper observation driven by `scripts/ops/run_with_timeout.py`, **evidence review** may report **PASS** (including `timeout_observed=true`) while a **child** `run_scheduler.py` process still appears in `ps` for a time, or remains **re-parented** (e.g. parent PID 1). That is a **process hygiene** topic, not a contradiction of the evidence review by itself.

This runbook separates:

1. **Evidence closeout** — file-based, using `scripts/ops/review_scheduler_paper_runtime_evidence.py` (offline, read-only).
2. **Process classification** — whether a lingering PID is idle, orphaned, or requires operator follow-up.

**This document does not authorize** Scheduler, runtime daemon, Paper runtime, Paper-validation, Testnet, Live, broker, exchange, or order submission. **It does not instruct you to kill processes**; any signal is **only** after explicit operator approval outside this file.

## Situation

- `run_with_timeout` enforces wall-clock bound; when the bound is hit, wrapper stderr typically contains a line matching  
  `run_with_timeout: exceeded --timeout-seconds=<n>; ...`  
  (see `review_scheduler_paper_runtime_evidence.py` for the exact pattern).
- The **review tool** treats matching timeout semantics in `scheduler_stderr.log` as `timeout_observed=true`.
- A **child** scheduler process might still show in process listings briefly, or appear **orphaned** (e.g. PPID 1) if the wrapper exited and the child did not reap immediately.
- **PASS** on evidence review means the **artifact set** satisfies the review contract; it does **not** mean “zero processes on the host.” Operators must not confuse the two.

## Required evidence before any cleanup decision

All of the following should be satisfied before considering *any* process signal (and only then under explicit operator approval):

| Gate | Meaning |
|------|--------|
| Review `verdict` | `PASS` from `review_scheduler_paper_runtime_evidence` |
| `timeout_observed` | `true` at the configured `--expected-timeout-seconds` |
| Manifest / hashes | `manifest_references_computed_hashes` true |
| `issues` | Empty list |
| No growth | Scheduler logs and `OUTROOT` evidence files show **no** meaningful growth across **two** spaced observations (e.g. log byte counts and mtimes stable) |
| Orphan signal | PPID 1 (or equivalent re-parenting) **if** claiming “orphan idle” — verify with `ps`, not assumptions |

If review is not **PASS**, fix evidence review first; **do not** use process cleanup to “fix” bad artifacts.

## Diagnostic steps (read-only)

Use **your** plan directory and paths (often under a private temp tree — **do not** paste secret material into tickets).

1. **Plan-path process match** — `ps` filtered by the **stable plan directory** string or job config path you used for the observation (grep-style match on command line).
2. **`lsof`** — For a candidate PID, list open files and confirm handles only point at **that** observation’s log and config roots (diagnostic only).
3. **Log sizes** — Record `scheduler_stdout.log` / `scheduler_stderr.log` sizes; wait; re-record; confirm **no growth** if claiming idle orphan.
4. **OUTROOT mtimes** — `account.json`, `fills.json`, `evidence_manifest.json` stable if claiming no new writes.
5. **Review JSON recap** — Re-run or retain `review_scheduler_paper_runtime_evidence.py --json` with the same `--outroot`, `--logroot`, `--expected-timeout-seconds` and confirm `PASS`, `issues=[]`, and metrics.

Canonical tools: `scripts/ops/review_scheduler_paper_runtime_evidence.py`, `scripts/ops/run_with_timeout.py` (reference only).

## Cleanup decision ladder

Operate **outside** this document; order is illustrative only.

1. **No action** — If no PID matches the plan path, or PID disappeared after earlier **SIGTERM**, evidence **PASS** is sufficient for **evidence** closeout; record “process gone” in operator closeout notes.
2. **SIGTERM** — Only after **explicit operator approval**, scoped to **one** verified PID, command line still matching the **same** observation plan path, and **idle** pattern (no log or OUTROOT growth across checks). Prefer documented operator scripts, not ad-hoc copy-paste.
3. **Post-TERM delay** — Wait; re-check `ps` and growth; if PID persists, treat as **manual review** (not automatic escalation).
4. **SIGKILL** — **Never** automatic from this runbook. Requires **separate** manual risk review; many sites forbid without runbook addendum.

## Safety boundaries

- **Do not** start a new scheduler, runtime daemon, Paper runtime, Paper-validation, Testnet, Live, or connect to broker or exchange for this workflow.
- **Do not** delete or rewrite evidence files or logs used for the **PASS** review unless a *new* legal/retention decision applies (out of scope here).
- **Do not** mutate repo config or trading logic to “clean up” a host process.
- **Do not** treat this runbook as approval to run anything — it is **classification and documentation** only.

## Relation to closeout

- **Evidence closeout** should cite **PASS** JSON from `review_scheduler_paper_runtime_evidence` and artifact paths (without secrets).
- **Process closeout** may be a **separate** subsection: orphan classification, optional **SIGTERM** approval reference, post-TERM “PID gone” confirmation.
- Keeping both in the written record avoids future operators assuming PASS implies no stray PID.

## Stop line

**No** Scheduler, runtime daemon, Paper runtime, Paper-validation, Testnet, Live, broker, exchange, order-submission, **kill**, or filesystem cleanup is **authorized by this runbook text**. All actions remain **operator decisions** under local policy.
