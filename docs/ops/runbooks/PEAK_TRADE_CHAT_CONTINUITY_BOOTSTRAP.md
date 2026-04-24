---
title: "Peak_Trade — chat continuity bootstrap (copy-paste)"
status: DRAFT
scope: docs-only (NO-LIVE)
last_updated: 2026-04-24
---

# Peak_Trade — chat continuity bootstrap

**Purpose:** Paste the block below at the **start of any** assistant chat (Cursor, CLI, etc.) so the model knows **where Peak_Trade stands** and **which docs are canonical**. Update [Current focus](../roadmap/CURRENT_FOCUS.md) when priorities change.

**Guardrails:** NO-LIVE; no live trading; no secrets in chats.

---

## Copy-paste block (session bootstrap)

```markdown
## Peak_Trade — session bootstrap

**Repository:** Peak_Trade. **Governance:** NO-LIVE (no live trading, no credential exposure).

**Canonical roadmap:** `docs/ops/roadmap/FINISH_PLAN.md`  
**Human “where we are now” (edit weekly):** `docs/ops/roadmap/CURRENT_FOCUS.md`  
**MVP finish runbook:** `docs/ops/runbooks/RUNBOOK_FINISH_A_MVP.md`

**Bounded-Pilot / First-Live navigation:** `docs/CLI_CHEATSHEET.md` (Bounded Pilot / First-Live Navigation); `docs/GETTING_STARTED.md` points to the same operator-navigation-only entry; `docs/ops/roadmap/CURRENT_FOCUS.md` (Recently landed) records the #2857–#2861 docs-only sequence. Navigation-only: no live authorization, gate bypass, or runtime, trading, evidence, approval, or live-entry semantics change.

**Workflow Officer** (check orchestration, read-only summaries):
- Implementation: `src/ops/workflow_officer.py`, `src/ops/workflow_officer_markdown.py`
- Runbook: `docs/ops/runbooks/WORKFLOW_OFFICER_V1_IMPLEMENTATION_RUNBOOK.md`
- Outputs include: `followup_topic_ranking`, `handoff_context`, `next_chat_preview`, `operator_report`, `executive_summary`, and **sequencing** fields (`build_now` | `stabilize_only` | `defer_until_prerequisites`).
- **Do not claim:** Workflow Officer is a full product roadmap or “autonomous self-learning system”; it reflects **checks and heuristics** over the repo.

**Update Officer** (separate track; WebUI / consolidation / operator flows):
- Code: `src/ops/update_officer.py`
- Runbooks: `docs/ops/runbooks/UPDATE_OFFICER_V*.md`

**This session’s question:**  
[Replace with 1–3 sentences.]

**Last known state (fill in):**  
- Branch: …  
- Relevant PR / commit: …  
- Blockers: …
```

---

## Why this exists

Chat sessions have **no persistent repo memory**. Without explicit pointers, assistants guess. This bootstrap + **CURRENT_FOCUS.md** reduce drift.

---

## Optional: refresh Workflow Officer locally

```bash
cd ~/Peak_Trade
python3 src/ops/workflow_officer.py --mode audit --profile docs_only_pr
```

Latest outputs: each run directory under the Workflow Officer output root contains `report.json` and `summary.md` (see `--output-root` on the CLI).
