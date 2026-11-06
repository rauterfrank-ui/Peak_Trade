"""CI invariant: paper-tests-audit-evidence workflow must not reference fallback-policy-json."""

from pathlib import Path


def test_paper_tests_audit_evidence_workflow_has_no_fallback_policy_json_flag() -> None:
    workflows = Path(".github/workflows")
    assert workflows.exists()
    ymls = sorted(list(workflows.glob("*.yml")) + list(workflows.glob("*.yaml")))
    assert ymls, "no workflows found"

    needle = "fallback-policy-json"
    offenders = []
    for p in ymls:
        txt = p.read_text(encoding="utf-8", errors="replace")
        if needle in txt:
            offenders.append(p.as_posix())

    assert not offenders, f"workflow(s) still reference {needle}: {offenders}"
