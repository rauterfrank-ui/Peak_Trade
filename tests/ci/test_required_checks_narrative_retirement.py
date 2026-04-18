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
    assert "pull_request" in doc_text
    assert "merge_group" in doc_text


def test_secondary_ops_docs_do_not_reintroduce_pr_gate_only_narrative() -> None:
    target_paths = [
        Path("docs/ops/ci_pragmatic_flow_pr_body.md"),
        Path("docs/ops/ci_pragmatic_flow_meta_gate.md"),
        Path("docs/ops/ci_pragmatic_flow_inventory.md"),
        Path("docs/ops/ci/trigger_runbook.md"),
    ]
    banned_fragments = [
        "Einziger required check",
        'required_contexts: ["PR Gate"]',
        'nur "PR Gate" als required',
        "single required check",
    ]
    required_anchor = "config/ci/required_status_checks.json"

    for path in target_paths:
        text = path.read_text(encoding="utf-8")
        for banned in banned_fragments:
            assert banned not in text, f"{path} reintroduced legacy narrative: {banned}"
        assert required_anchor in text, f"{path} must reference JSON SSOT config"


def test_ops_required_checks_drift_guard_uses_json_ssot_as_source() -> None:
    script_text = Path("scripts/ops/verify_required_checks_drift.sh").read_text(encoding="utf-8")
    assert "config/ci/required_status_checks.json" in script_text
    assert "scripts/ci/required_checks_drift_detector.py" in script_text


def test_required_checks_docs_do_not_reintroduce_doc_as_source_narrative() -> None:
    branch_protection_doc = Path("docs/ops/BRANCH_PROTECTION_REQUIRED_CHECKS.md").read_text(
        encoding="utf-8"
    )
    drift_guard_notes = Path("docs/ops/REQUIRED_CHECKS_DRIFT_GUARD_v1_OPERATOR_NOTES.md").read_text(
        encoding="utf-8"
    )
    trigger_runbook = Path("docs/ops/ci/trigger_runbook.md").read_text(encoding="utf-8")

    assert "Historical snapshot only (not canonical SSOT)." in branch_protection_doc
    assert "config/ci/required_status_checks.json" in branch_protection_doc
    assert "doc vs live" not in drift_guard_notes
    assert (
        "Extracts checks from `docs/ops/BRANCH_PROTECTION_REQUIRED_CHECKS.md`"
        not in drift_guard_notes
    )
    assert "config/ci/required_status_checks.json" in drift_guard_notes
    assert "docs/ops/BRANCH_PROTECTION_REQUIRED_CHECKS.md" not in trigger_runbook


def test_secondary_drift_guard_docs_remain_json_ssot_only() -> None:
    target_paths = [
        Path("docs/ops/DRIFT_GUARD_QUICK_START.md"),
        Path("docs/ops/REQUIRED_CHECKS_DRIFT_GUARD_PR_WORKFLOW.md"),
    ]
    banned_fragments = [
        "doc vs live",
        "Doc matches live",
        "Doc == Live",
        "dokumentierte Required Checks",
    ]
    required_anchors = [
        "config/ci/required_status_checks.json",
        "JSON SSOT",
    ]

    for path in target_paths:
        text = path.read_text(encoding="utf-8")
        for banned in banned_fragments:
            assert banned not in text, f"{path} reintroduced legacy drift narrative: {banned}"
        for anchor in required_anchors:
            assert anchor in text, f"{path} must include JSON-SSOT anchor: {anchor}"


def test_secondary_ops_helper_does_not_reintroduce_legacy_drift_flags() -> None:
    helper_script = Path("scripts/ops/create_required_checks_drift_guard_pr.sh").read_text(
        encoding="utf-8"
    )
    assert "--live" not in helper_script
    assert "--offline" not in helper_script
