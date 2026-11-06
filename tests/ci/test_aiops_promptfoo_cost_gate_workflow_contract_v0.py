"""Static cost-gate contract for AI-Ops Promptfoo workflow.

Reads workflow YAML as UTF-8 text only. No subprocess, no network, no PyYAML
requirement beyond what the repo already uses elsewhere.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "aiops-promptfoo-evals.yml"


def test_aiops_promptfoo_workflow_defaults_paid_evals_off() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")

    assert "workflow_dispatch:" in text
    assert "run_paid_openai_evals:" in text
    assert "default: false" in text
    assert "vars.PEAK_TRADE_RUN_PAID_PROMPTFOO_EVALS == 'true'" in text
    assert "github.event.inputs.run_paid_openai_evals == 'true'" in text


def test_aiops_promptfoo_workflow_injects_openai_secret_only_behind_opt_in_if() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")

    assert text.count("OPENAI_API_KEY:") == 1
    assert text.count("${{ secrets.OPENAI_API_KEY }}") == 1

    key_idx = text.index("OPENAI_API_KEY:")
    prefix = text[max(0, key_idx - 1200) : key_idx]

    assert "Run paid Promptfoo Eval (OpenAI)" in prefix
    assert "github.event_name == 'workflow_dispatch'" in prefix
    assert "run_paid_openai_evals" in prefix
    assert "PEAK_TRADE_RUN_PAID_PROMPTFOO_EVALS" in prefix


def test_aiops_promptfoo_workflow_pr_push_skips_paid_path() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")

    assert "PR/Push — paid Promptfoo/OpenAI disabled (cost gate)" in text
    assert "pr_push_cost_gate.json" in text
    assert "github.event_name == 'pull_request'" in text
    assert "github.event_name == 'push'" in text
