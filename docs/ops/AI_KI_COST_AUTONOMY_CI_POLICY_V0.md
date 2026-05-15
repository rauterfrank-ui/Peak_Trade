# AI/KI — CI cost & autonomy operator policy (v0)

Version: v0

Owner: Ops / AI governance alignment

Scope: **GitHub Actions and operator posture** for paid LLM usage and repo autonomy.
Out of scope: Trading logic, Master V2, Double Play, Risk, Kill Switch, execution/live enablement (see [`ai_activation_gate_v1.md`](governance/ai_activation_gate_v1.md)).

## Purpose

Peak_Trade keeps **kostenpflichtige AI/KI/LLM** usage **default-off** in CI and scheduled automation until the system is intentionally mature. This note records the **operator policy** after Promptfoo cost gating (PR #3461) and follow-up workflow reviews.

## Principles (operators)

1. **Paid AI/KI/LLM is default-off** in `pull_request`, `push`, and routine `schedule` paths.
2. **A present `OPENAI_API_KEY` GitHub Actions secret does not imply permission to spend.** Runtime and workflow gates still apply.
3. **No silent paid LLM** on ordinary PR/push or cron: prefer `--skip-llm`, `--skip-ai`, offline/no-op, replay, or placeholder outputs.
4. **Real (billable) LLM calls** are allowed only when an operator **explicitly opts in**, with **auditable** workflow inputs and/or repository variables plus existing **hard gates** (see model enablement runbooks).
5. **AI must not grant trading or live execution authority.** Advisory and orchestration remain bounded by governance; see [`AI_AUTONOMY_GO_NO_GO_OVERVIEW.md`](../governance/AI_AUTONOMY_GO_NO_GO_OVERVIEW.md).

## Workflow surfaces (expected posture)

| Surface | Current expected state | Paid / billable LLM allowed? | Notes |
|--------|-------------------------|--------------------------------|-------|
| **AI-Ops Promptfoo Evals** | Active; PR/push run cost-safe path | **Only** manual `workflow_dispatch` with `run_paid_openai_evals=true` **and** repo var `PEAK_TRADE_RUN_PAID_PROMPTFOO_EVALS=true` | After PR #3461; see also [`AI_EVALS_RUNBOOK.md`](../ai/AI_EVALS_RUNBOOK.md). |
| **InfoStream Automation** (`.github/workflows/infostream-automation.yml`) | Schedule + manual | **Schedule:** only if affirmative repo variables (e.g. `PT_AI_MODELS_ENABLED`, `PT_PAPERTRAIL_READY`) and runtime gates allow; keep vars **absent/false** unless owner-approved. | Treat scheduled model clients as **high sensitivity**. |
| **MarketSentinel – Daily Market Outlook** (`.github/workflows/market_outlook_automation.yml`) | Schedule + manual | **Schedule:** uses `--skip-llm` (placeholder path; no billable outbound LLM on cron). **Manual `workflow_dispatch`:** runs the script **without** `--skip-llm` today — **operator-initiated only**, not schedule-default, **not** autonomous spend; still **Principle 2** (secret ≠ spend permission) + **Principle 5** (no trading/live authority). No dedicated “paid LLM” workflow input yet. | Outputs are advisory/reporting; optional explicit paid opt-in inputs are a future guardrail slice. |
| **AIOps trend seed / ledger** | `workflow_run` / dispatch | **No** OpenAI secret in workflow (artifact chain) | Offline/deterministic chain. |
| **Cursor Auto-PR / Auto-merge** | Push / PR automation | **No LLM cost**; uses `GITHUB_TOKEN` | **Repo autonomy** (PRs, labels, merge) — separate governance from LLM cost. |
| **`ai-model-cards-validate`** | PR | **No** — local validation of docs | Safe. |
| **Audit workflow** | Various | Dummy `OPENAI_API_KEY` in CI only where documented | No live key dependency for audit path. |

## Market Outlook — manual `workflow_dispatch` (operator clarification)

This section restates repo-verified behavior from `.github/workflows/market_outlook_automation.yml` only; it does **not** grant authority.

- **Scheduled runs** always pass `--skip-llm` → placeholder path; routine automation does **not** turn on billable LLM by default.
- **Manual runs** follow the workflow `else` path **without** `--skip-llm`; any outbound LLM therefore requires a deliberate operator action in GitHub plus whatever keys/vars exist — **not** silent or autonomous CI spend.
- **Presence of `OPENAI_API_KEY`** (or other secrets) is **not** approval, **not** Freigabe, and **not** trading/live enablement; spending posture remains gated by operator intent, repo variables, and runtime/workflow rules elsewhere.
- **Documentation** and CI outputs **must not** be interpreted as order placement, risk override, or execution gates (see [`AI_AUTONOMY_GO_NO_GO_OVERVIEW.md`](../governance/AI_AUTONOMY_GO_NO_GO_OVERVIEW.md)).

## Repository variables (cost-relevant)

Keep **absent or non-affirmative** unless an owner explicitly arms automation:

- `PT_AI_MODELS_ENABLED`
- `PT_PAPERTRAIL_READY`
- `PT_AI_MODELS_ARMED`

Treat **`PEAK_TRADE_RUN_PAID_PROMPTFOO_EVALS`** as **false/absent** unless paid Promptfoo evals are intentionally required.

Also check **GitHub Environments** and **organization-level** variables if workflows bind to environments.

## Related documentation

- Promptfoo / local evals: [`docs/ai/AI_EVALS_RUNBOOK.md`](../ai/AI_EVALS_RUNBOOK.md)
- Live AI activation (execution boundary): [`docs/ops/governance/ai_activation_gate_v1.md`](governance/ai_activation_gate_v1.md)
- Model enablement operations: [`docs/ops/ai/ai_model_enablement_runbook_v1.md`](ai/ai_model_enablement_runbook_v1.md)
- Autonomy overview: [`docs/governance/AI_AUTONOMY_GO_NO_GO_OVERVIEW.md`](../governance/AI_AUTONOMY_GO_NO_GO_OVERVIEW.md)

## Next review points (no implementation commitment)

1. **Market Outlook** — manual `workflow_dispatch`: optional explicit “paid LLM” input + repo variable (align with Promptfoo pattern).
2. **InfoStream** — confirm repo variables and policy artifacts stay **disarmed** in GitHub UI when daily KI is not intended.
3. **Org/environment variables** — periodic audit that no environment inherits unintended affirmative AI flags.

## Non-goals

- Changing trading, risk, execution, or live gates.
- Mandating removal of `OPENAI_API_KEY`; controlling **when** workflows may use it is the goal.
