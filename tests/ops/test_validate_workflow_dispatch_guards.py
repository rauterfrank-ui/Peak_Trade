from pathlib import Path

from scripts.ops.validate_workflow_dispatch_guards import validate_file


def test_good_workflow_has_no_findings() -> None:
    p = Path("tests/fixtures/workflows_dispatch_guard/good_workflow.yml")
    findings = validate_file(p)
    assert findings == []


def test_bad_workflow_has_errors() -> None:
    p = Path("tests/fixtures/workflows_dispatch_guard/bad_workflow.yml")
    findings = validate_file(p)
    # Expect at least 2 errors:
    # - missing github.event.inputs.missing_key not declared
    # - inputs.mode misuse
    levels = [f.level for f in findings]
    assert "ERROR" in levels
    # Ensure we catch both categories
    msgs = " | ".join(f.message for f in findings)
    assert "missing_key" in msgs
    assert "inputs.mode" in msgs or "inputs." in msgs
