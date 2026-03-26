---
title: "Current focus — operator-maintained (not auto-generated)"
status: DRAFT
scope: docs-only (NO-LIVE)
last_updated: 2026-03-26
---

# Current focus

**Purpose:** One short, **human-updated** place so chats and operators know **what we are doing now**.  
This is **not** produced by Workflow Officer or Update Officer; officers aggregate checks and summaries — they do not replace this note.

**Related:** [Finish Plan (MVP→v1.0)](FINISH_PLAN.md) · [Chat continuity bootstrap](../runbooks/PEAK_TRADE_CHAT_CONTINUITY_BOOTSTRAP.md)

---

## Active goal (one sentence)

<!-- Edit weekly or when direction changes. Example: "Close Finish Level A MVP DoD for docs gates + minimal backtest verify." -->

_TBD — fill in._

---

## Next three concrete steps

1. _TBD_
2. _TBD_
3. _TBD_

---

## Blockers / risks

- _None / list_

---

## Last verification (evidence-first)

| Date (UTC) | What was verified | Command or artifact |
|------------|---------------------|----------------------|
| _TBD_ | _e.g. docs gates snapshot_ | _paste path or command_ |

---

## Branch / PR pointer (optional)

- Branch: _e.g. main_
- Last merged PR touching this focus: _TBD_

---

## How Workflow Officer and Update Officer fit

- **Workflow Officer** (`src/ops/workflow_officer.py`): runs profiled checks, emits `summary` with follow-up ranking, handoff, next-chat preview, operator/executive views, and **sequencing** metadata. Use it to see **repo gate state**, not to replace this file.
- **Update Officer** (`src/ops/update_officer.py` + `UPDATE_OFFICER_V*.md` runbooks): separate evolution of operator-facing consolidation and WebUI wiring.
