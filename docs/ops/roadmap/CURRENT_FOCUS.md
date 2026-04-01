---
title: "Current focus — operator-maintained (not auto-generated)"
status: DRAFT
scope: docs-only (NO-LIVE)
last_updated: 2026-04-01
---

# Current focus

**Purpose:** One short, **human-updated** place so chats and operators know **what we are doing now**.  
This is **not** produced by Workflow Officer or Update Officer; officers aggregate checks and summaries — they do not replace this note.

**Related:** [Finish Plan (MVP→v1.0)](FINISH_PLAN.md) · [Truth Core](../registry/TRUTH_CORE.md) · [Workflow Frontdoor](../../WORKFLOW_FRONTDOOR.md) · [Release docs (index)](../release/README.md) · [Chat continuity bootstrap](../runbooks/PEAK_TRADE_CHAT_CONTINUITY_BOOTSTRAP.md)

---

## Active goal (one sentence)

**Finish Plan PRs 6–8 remain the navigation spine on `main` (docs-only / snapshot-only):** [PR 6 — Live-Ops runbook pack](FINISH_PLAN.md#pr-6-live-ops-runbook-pack-docs-only) · [PR 7 — Observability / status reports](FINISH_PLAN.md#pr-7-observabilitystatus-report-hardening-code-docs) · [PR 8 — Release checklist / Go–No-Go](FINISH_PLAN.md#pr-8-release-checklist-gono-go-rubric-docs-only) — use [Workflow Frontdoor](../../WORKFLOW_FRONTDOOR.md) and [Release docs](../release/README.md); **NO** live unlocks. **Truth/docs governance, PR truth gates, officer truth integration, bounded-pilot / canary-live-entry docs, J1 forward-pipeline slices, and the J2 Optuna demo-runner slice are landed** — see **Recently landed** below.

---

## Recently landed (truth, docs governance, officers)

- **Unified Truth Core** (`src/ops/truth/`): shared loaders + deterministic evaluators for docs drift and repo truth claims — [TRUTH_CORE.md](../registry/TRUTH_CORE.md).
- **CI:** workflow [.github/workflows/truth_gates_pr.yml](../../../.github/workflows/truth_gates_pr.yml) defines jobs **`docs-drift-guard`** and **`repo-truth-claims`** (PR / merge queue / manual dispatch).
- **Officers:** [Workflow Officer](#how-workflow-officer-and-update-officer-fit) and [Update Officer](#how-workflow-officer-and-update-officer-fit) include **`summary.unified_truth_status`** (read-only diagnostics from the same core).
- **Forward / ops context:** J1 forward-pipeline slices and bounded-pilot / canary-live-entry runbooks merged per prior PRs; posture unchanged (**NO-LIVE** default unless a governed runbook explicitly says otherwise).
- **J2 (Optuna placeholder slice, PR #2168):** `scripts/run_study_optuna_placeholder.py` — CLI, dry-run default, optional in-memory toy study (`--no-dry-run`); no market/live execution. Full strategy optimization remains `scripts/run_optuna_study.py` (incl. GridSampler / CI alignment with Optuna 3.6).

**GitHub (operators with admin):** If **Required status checks** for `docs-drift-guard` and `repo-truth-claims` are not yet enabled on **`main`**, configure them under **Repo Settings → Branches → Branch protection rule → Required status checks** (names must match the workflow job `name:` fields). The workflow file above is the source of truth for those names.

---

## Next three concrete steps

1. For **new work**, start from [FINISH_PLAN](FINISH_PLAN.md) and the Frontdoor; edit **this file** when the active goal or branch context changes.
2. Keep pasting the **bootstrap block** from [PEAK_TRADE_CHAT_CONTINUITY_BOOTSTRAP](../runbooks/PEAK_TRADE_CHAT_CONTINUITY_BOOTSTRAP.md) for new assistant chats.
3. After docs edits, run `bash scripts/ops/pt_docs_gates_snapshot.sh --changed` (changed-scope docs gates).

---

## Next small focus (suggestion)

- **Optional:** next **small** slice — e.g. [J3 placeholder-inventory tool](../runbooks/RUNBOOK_UNIMPLEMENTED_FEATURES_ORDERED.md#stufe-j--scripts--demo-daten-operativ-niedrig-priorisiert) (`generate_placeholder_reports.py`), [J1 stub follow-up](../runbooks/RUNBOOK_UNIMPLEMENTED_FEATURES_ORDERED.md#stufe-j--scripts--demo-daten-operativ-niedrig-priorisiert) (still **STUB** / no live), or a **chat-led** gap pass per [RUNBOOK_CHAT_LED_OPEN_FEATURES.md](../runbooks/RUNBOOK_CHAT_LED_OPEN_FEATURES.md). Keep scope **narrow**; no new product or live unlock.

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
| 2026-04-01 | Post–truth-layer / gates / officers: `CURRENT_FOCUS` human anchor updated (this file); docs gates snapshot PASS locally | `bash scripts/ops/pt_docs_gates_snapshot.sh --changed` |
| 2026-04-01 | Post–J2 (PR #2168): `CURRENT_FOCUS` refresh — J2 landed, pointer cleaned | PR #2168 merge; `bash scripts/ops/pt_docs_gates_snapshot.sh --changed` |

---

## Branch / PR pointer (optional)

- **Merged:** [PR #2168](https://github.com/rauterfrank-ui/Peak_Trade/pull/2168) — J2 Optuna placeholder / minimal study runner + related CI fixes on `main`.
- **Doc edits to this file:** short-lived `feat&#47;*` branch as usual; Finish Plan **PR 6–8** spine unchanged; **NO-LIVE** default.

---

## How Workflow Officer and Update Officer fit

- **Workflow Officer** (`src/ops/workflow_officer.py`): runs profiled checks, emits `summary` with follow-up ranking, handoff, next-chat preview, operator/executive views, **sequencing** metadata, and **`unified_truth_status`** (docs drift + repo truth claims via `ops.truth`). Use it to see **repo gate state**, not to replace this file.
- **Update Officer** (`src/ops/update_officer.py` + `UPDATE_OFFICER_V*.md` runbooks): separate evolution of operator-facing consolidation and WebUI wiring; **`summary.unified_truth_status`** uses the same truth integration layer.
