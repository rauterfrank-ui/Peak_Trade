import subprocess
import sys
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


def test_cli_fail_on_warn_inline_workflow_dispatch_list_exits_one(tmp_path: Path) -> None:
    wf = tmp_path / "inline_dispatch.yml"
    wf.write_text(
        "name: synthetic-inline-dispatch\n"
        "on: [workflow_dispatch]\n"
        "\n"
        "jobs:\n"
        "  t:\n"
        "    runs-on: ubuntu-latest\n"
        "    steps:\n"
        "      - run: echo ${{ github.event.inputs.only_warn_key }}\n",
        encoding="utf-8",
    )

    repo_root = Path(__file__).resolve().parents[2]
    script = repo_root / "scripts" / "ops" / "validate_workflow_dispatch_guards.py"
    proc = subprocess.run(
        [
            sys.executable,
            str(script),
            "--paths",
            str(wf),
            "--fail-on-warn",
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    assert proc.returncode == 1
    assert "WARN" in proc.stdout
    assert "inline 'on:' Form" in proc.stdout
    assert "only_warn_key" in proc.stdout
    assert "ERROR " not in proc.stdout
