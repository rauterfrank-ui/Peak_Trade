---
title: "Peak_Trade — chat continuity bootstrap (copy-paste)"
status: DRAFT
scope: docs-only (NO-LIVE)
last_updated: 2026-05-14
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

## Cursor Ask-Mode / Result Robustness Note v0

When using `cursor-agent --print --mode ask` for operator planning, treat the agent output as best-effort console output, not as a guaranteed file writer.

Recommended operator-side pattern:

- write the prompt and intended result path under `/tmp`;
- capture raw agent output to `CURSOR_AGENT_OUTPUT.txt`;
- extract a Markdown block or structured section into the intended result file deterministically;
- always create a fallback result if extraction fails;
- record timeout/error metadata under the same `/tmp` package;
- keep the repo working tree clean unless a later explicit patch is approved.

Timeout note for macOS operators:

- GNU `timeout` is not available on default macOS shells;
- use `gtimeout` only if GNU coreutils is installed;
- otherwise prefer a small Python wrapper around `subprocess.run(..., timeout=...)`;
- do not rely on a missing `timeout` command as a safety boundary.

This note is operator-workflow guidance only. It does not authorize runtime, scheduler, Paper, Testnet, Live, Broker, Kraken, exchange, order-submission, credential, or secret handling changes.
