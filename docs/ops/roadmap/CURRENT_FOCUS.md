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

Docs for **chat continuity** are on `main`: operators can use **this file** plus [PEAK_TRADE_CHAT_CONTINUITY_BOOTSTRAP](../runbooks/PEAK_TRADE_CHAT_CONTINUITY_BOOTSTRAP.md) so every session starts with the same canonical pointers (Workflow Officer vs GitHub PR flow, Finish Plan).

---

## Next three concrete steps

1. Edit this file when the **active goal** changes (weekly or on milestone).
2. Paste the **bootstrap block** from `PEAK_TRADE_CHAT_CONTINUITY_BOOTSTRAP.md` into new assistant chats.
3. Pick the next concrete item from [FINISH_PLAN](FINISH_PLAN.md) when ready to move beyond docs scaffolding.

---

## Blockers / risks

- None from **PR #2047** itself.

---

## Last verification (evidence-first)

| Date (UTC) | What was verified | Command or artifact |
|------------|---------------------|----------------------|
| 2026-03-26 | PR #2047 merged: `CURRENT_FOCUS.md`, `PEAK_TRADE_CHAT_CONTINUITY_BOOTSTRAP.md`, FINISH_PLAN cross-link | https://github.com/rauterfrank-ui/Peak_Trade/pull/2047 (merged 2026-03-26T18:40:04Z) |

---

## Branch / PR pointer (optional)

- Branch: **main**
- Relevant PR / commit: **PR #2047** merged on **2026-03-26T18:40:04Z**
- Topic: **docs chat continuity bootstrap**
- State: **CURRENT_FOCUS** + **chat bootstrap** docs landed on `main`

---

## How Workflow Officer and Update Officer fit

- **Workflow Officer** (`src/ops/workflow_officer.py`): runs profiled checks, emits `summary` with follow-up ranking, handoff, next-chat preview, operator/executive views, and **sequencing** metadata. Use it to see **repo gate state**, not to replace this file.
- **Update Officer** (`src/ops/update_officer.py` + `UPDATE_OFFICER_V*.md` runbooks): separate evolution of operator-facing consolidation and WebUI wiring.
