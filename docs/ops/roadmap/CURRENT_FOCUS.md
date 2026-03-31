---
title: "Current focus — operator-maintained (not auto-generated)"
status: DRAFT
scope: docs-only (NO-LIVE)
last_updated: 2026-03-31
---

# Current focus

**Purpose:** One short, **human-updated** place so chats and operators know **what we are doing now**.  
This is **not** produced by Workflow Officer or Update Officer; officers aggregate checks and summaries — they do not replace this note.

**Related:** [Finish Plan (MVP→v1.0)](FINISH_PLAN.md) · [Workflow Frontdoor](../../WORKFLOW_FRONTDOOR.md) · [Release docs (index)](../release/README.md) · [Chat continuity bootstrap](../runbooks/PEAK_TRADE_CHAT_CONTINUITY_BOOTSTRAP.md)

---

## Active goal (one sentence)

**Finish Plan PRs 6–8 are merged on `main` (docs-only / snapshot-only):** [PR 6 — Live-Ops runbook pack](FINISH_PLAN.md#pr-6-live-ops-runbook-pack-docs-only) · [PR 7 — Observability / status reports](FINISH_PLAN.md#pr-7-observabilitystatus-report-hardening-code-docs) · [PR 8 — Release checklist / Go–No-Go](FINISH_PLAN.md#pr-8-release-checklist-gono-go-rubric-docs-only) — use [Workflow Frontdoor](../../WORKFLOW_FRONTDOOR.md) and [Release docs](../release/README.md) for navigation; **NO** live unlocks.

---

## Next three concrete steps

1. For **new work**, start from [FINISH_PLAN](FINISH_PLAN.md) and the Frontdoor; edit **this file** when the active goal or branch context changes.
2. Keep pasting the **bootstrap block** from [PEAK_TRADE_CHAT_CONTINUITY_BOOTSTRAP](../runbooks/PEAK_TRADE_CHAT_CONTINUITY_BOOTSTRAP.md) for new assistant chats.
3. After docs edits, run `bash scripts/ops/pt_docs_gates_snapshot.sh --changed` (changed-scope docs gates).

---

## Blockers / risks

- None known for **main** at last verification below; reopen if required CI/docs gates regress.

---

## Parked (bewusst nicht aktiv)

- **F3 — Learning/Promotion Roadmap v2** (optional): Wunschliste in `docs&#47;LEARNING_PROMOTION_LOOP_V1_ARCHITECTURE.md` §12; Runbook-Stufe F und Tag **DOC** in [RUNBOOK_UNIMPLEMENTED_FEATURES_ORDERED.md](../runbooks/RUNBOOK_UNIMPLEMENTED_FEATURES_ORDERED.md). Kein Lieferzwang bis Priorisierung.

---

## Last verification (evidence-first)

| Date (UTC) | What was verified | Command or artifact |
|------------|---------------------|----------------------|
| 2026-03-26 | PR #2047 merged: `CURRENT_FOCUS.md`, `PEAK_TRADE_CHAT_CONTINUITY_BOOTSTRAP.md`, FINISH_PLAN cross-link | https://github.com/rauterfrank-ui/Peak_Trade/pull/2047 (merged 2026-03-26T18:40:04Z) |
| 2026-03-27 | Finish Plan **PR 6** slice: Live-Ops pack cross-links (Frontdoor, runbooks, safety) | https://github.com/rauterfrank-ui/Peak_Trade/pull/2059 |
| 2026-03-27 | Finish Plan **PR 7** slice: observability / status report navigation | https://github.com/rauterfrank-ui/Peak_Trade/pull/2060 |
| 2026-03-27 | Finish Plan **PR 8** slice: release checklist + Go/No-Go rubric (`docs/ops/release/`) | https://github.com/rauterfrank-ui/Peak_Trade/pull/2061 |
| 2026-03-27 | `CURRENT_FOCUS` refresh post PR 6–8 (this file) | https://github.com/rauterfrank-ui/Peak_Trade/pull/2062 |
| 2026-03-27 | `CURRENT_FOCUS` post-merge finalize (table + branch pointer on `main`) | https://github.com/rauterfrank-ui/Peak_Trade/pull/2063 |

---

## Branch / PR pointer (optional)

- Branch: **`main`** — **CURRENT_FOCUS** post PR 6–8: refresh **#2062**, finalize **#2063**
- Topic: **Roadmap PR 6–8 landed — operator navigation + release rubric**
- State: Frontdoor links to **Live-Ops pack**, **Observability / status reports**, **Release checklist / Go–No-Go**; evidence-first posture unchanged (**NO-LIVE** default)

---

## How Workflow Officer and Update Officer fit

- **Workflow Officer** (`src/ops/workflow_officer.py`): runs profiled checks, emits `summary` with follow-up ranking, handoff, next-chat preview, operator/executive views, and **sequencing** metadata. Use it to see **repo gate state**, not to replace this file.
- **Update Officer** (`src/ops/update_officer.py` + `UPDATE_OFFICER_V*.md` runbooks): separate evolution of operator-facing consolidation and WebUI wiring.
