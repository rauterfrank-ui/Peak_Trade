"""Invariants for required-checks SSOT narrative surfaces."""

from __future__ import annotations

from pathlib import Path


def test_ci_workflow_does_not_claim_pr_gate_only_branch_protection() -> None:
    workflow_text = Path(".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert 'Branch protection: require only "PR Gate".' not in workflow_text
    assert "single required check for branch protection" not in workflow_text
    assert "required_contexts - ignored_contexts" in workflow_text


def test_ops_ci_doc_states_json_ssot_effective_required_contexts() -> None:
    doc_text = Path("docs/ops/CI.md").read_text(encoding="utf-8")
    assert "Required Checks SSOT" in doc_text
    assert "effective_required_contexts = required_contexts - ignored_contexts" in doc_text
