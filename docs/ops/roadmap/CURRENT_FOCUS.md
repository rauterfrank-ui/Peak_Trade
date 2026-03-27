---
title: "Current focus — operator-maintained (not auto-generated)"
status: DRAFT
scope: docs-only (NO-LIVE)
last_updated: 2026-03-27
---

# Current focus

**Purpose:** One short, **human-updated** place so chats and operators know **what we are doing now**.  
This is **not** produced by Workflow Officer or Update Officer; officers aggregate checks and summaries — they do not replace this note.

**Related:** [Finish Plan (MVP→v1.0)](FINISH_PLAN.md) · [Chat continuity bootstrap](../runbooks/PEAK_TRADE_CHAT_CONTINUITY_BOOTSTRAP.md)

---

## Active goal (one sentence)

**Finish Plan PR 6 (Live-Ops runbook pack, docs-only):** Cross-links between [Workflow Frontdoor](../../WORKFLOW_FRONTDOOR.md), [Live Operational Runbooks](../../LIVE_OPERATIONAL_RUNBOOKS.md), [Incident Simulation & Drills](../../INCIDENT_SIMULATION_AND_DRILLS.md), and [Safety Policy Testnet & Live](../../SAFETY_POLICY_TESTNET_AND_LIVE.md) — **NO unlocks**, navigation only (see [FINISH_PLAN PR 6](FINISH_PLAN.md#pr-6-live-ops-runbook-pack-docs-only)).

---

## Next three concrete steps

1. Merge the PR for **PR 6** when CI/docs gates are green; then point **Active goal** at [FINISH_PLAN](FINISH_PLAN.md) **PR 7** or refresh chat-continuity focus as needed.
2. Keep pasting the **bootstrap block** from [PEAK_TRADE_CHAT_CONTINUITY_BOOTSTRAP](../runbooks/PEAK_TRADE_CHAT_CONTINUITY_BOOTSTRAP.md) for new assistant chats.
3. Run `bash scripts/ops/pt_docs_gates_snapshot.sh --changed` before merge (changed-scope docs gates).

---

## Blockers / risks

- None from **PR #2047** itself.

---

## Last verification (evidence-first)

| Date (UTC) | What was verified | Command or artifact |
|------------|---------------------|----------------------|
| 2026-03-26 | PR #2047 merged: `CURRENT_FOCUS.md`, `PEAK_TRADE_CHAT_CONTINUITY_BOOTSTRAP.md`, FINISH_PLAN cross-link | https://github.com/rauterfrank-ui/Peak_Trade/pull/2047 (merged 2026-03-26T18:40:04Z) |
| 2026-03-27 | Finish Plan **PR 6** slice: Live-Ops pack cross-links in `WORKFLOW_FRONTDOOR`, `LIVE_OPERATIONAL_RUNBOOKS`, `INCIDENT_SIMULATION_AND_DRILLS`, `SAFETY_POLICY_*`, `FINISH_PLAN`, `CURRENT_FOCUS` | `bash scripts/ops/pt_docs_gates_snapshot.sh --changed` → PASS (pending merge) |

---

## Branch / PR pointer (optional)

- Branch: **feat/pr6-live-ops-runbook-pack-docs** (PR 6); merge → **main**
- Topic: **Finish Plan PR 6 — Live-Ops runbook pack (docs-only)**
- State: cross-links landed in **WORKFLOW_FRONTDOOR**, **LIVE_OPERATIONAL_RUNBOOKS**, **INCIDENT_SIMULATION_AND_DRILLS**, **SAFETY_POLICY_TESTNET_AND_LIVE**, **FINISH_PLAN**, **CURRENT_FOCUS**

---

## How Workflow Officer and Update Officer fit

- **Workflow Officer** (`src/ops/workflow_officer.py`): runs profiled checks, emits `summary` with follow-up ranking, handoff, next-chat preview, operator/executive views, and **sequencing** metadata. Use it to see **repo gate state**, not to replace this file.
- **Update Officer** (`src/ops/update_officer.py` + `UPDATE_OFFICER_V*.md` runbooks): separate evolution of operator-facing consolidation and WebUI wiring.
