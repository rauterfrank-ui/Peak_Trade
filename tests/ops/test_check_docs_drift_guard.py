"""Tests for docs drift evaluation (ops.truth) — deterministic mapping logic."""

from __future__ import annotations

from pathlib import Path

from ops.truth import TruthStatus, evaluate_docs_drift

_FIXTURE_MAP: dict = {
    "version": 1,
    "rules": [
        {
            "id": "execution-layer",
            "sensitive": ["src/execution/"],
            "required_docs": [
                "docs/GOVERNANCE_AND_SAFETY_OVERVIEW.md",
                "docs/PEAK_TRADE_V1_KNOWN_LIMITATIONS.md",
            ],
        },
        {
            "id": "governance-doc",
            "sensitive": ["docs/GOVERNANCE_AND_SAFETY_OVERVIEW.md"],
            "required_docs": ["docs/ops/registry/DOCS_TRUTH_MAP.md"],
        },
    ],
}


def test_no_sensitive_change_ok() -> None:
    changed = ["README.md", "src/foo.py"]
    r = evaluate_docs_drift(changed, _FIXTURE_MAP)
    assert r.status is TruthStatus.PASS
    assert not r.violations


def test_execution_change_with_governance_doc_ok() -> None:
    changed = [
        "src/execution/pipeline.py",
        "docs/GOVERNANCE_AND_SAFETY_OVERVIEW.md",
        "docs/ops/registry/DOCS_TRUTH_MAP.md",
    ]
    r = evaluate_docs_drift(changed, _FIXTURE_MAP)
    assert r.status is TruthStatus.PASS


def test_execution_change_without_doc_fails() -> None:
    changed = ["src/execution/pipeline.py"]
    r = evaluate_docs_drift(changed, _FIXTURE_MAP)
    assert r.status is TruthStatus.FAIL
    assert len(r.violations) == 1
    assert r.violations[0].rule_id == "execution-layer"
    assert "src/execution/pipeline.py" in r.violations[0].triggered_paths


def test_governance_doc_change_requires_truth_map() -> None:
    changed = ["docs/GOVERNANCE_AND_SAFETY_OVERVIEW.md"]
    r = evaluate_docs_drift(changed, _FIXTURE_MAP)
    assert r.status is TruthStatus.FAIL
    assert len(r.violations) == 1
    assert r.violations[0].rule_id == "governance-doc"


def test_governance_plus_truth_map_ok() -> None:
    changed = [
        "docs/GOVERNANCE_AND_SAFETY_OVERVIEW.md",
        "docs/ops/registry/DOCS_TRUTH_MAP.md",
    ]
    r = evaluate_docs_drift(changed, _FIXTURE_MAP)
    assert not any(v.rule_id == "governance-doc" for v in r.violations)


def test_script_exists() -> None:
    root = Path(__file__).resolve().parents[2]
    script = root / "scripts" / "ops" / "check_docs_drift_guard.py"
    assert script.is_file()


def test_cli_reports_git_diff_failure_for_missing_base_ref(tmp_path: Path) -> None:
    import subprocess

    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)
    (repo / "docs").mkdir()
    (repo / "src").mkdir()
    (repo / "docs" / "README.md").write_text("# Probe\n", encoding="utf-8")
    (repo / "src" / "probe.py").write_text('print("probe")\n', encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=repo, check=True)

    result = subprocess.run(
        [
            "uv",
            "run",
            "python",
            "scripts/ops/check_docs_drift_guard.py",
            "--base",
            "definitely_missing_base_ref_for_contract_probe",
            "--repo-root",
            str(repo),
            "--config",
            "config/ops/docs_truth_map.yaml",
        ],
        cwd=Path(__file__).resolve().parents[2],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert "ERR: git diff failed (exit 128)." in result.stderr
    assert "definitely_missing_base_ref_for_contract_probe...HEAD" in result.stderr
    assert "Hint: ensure the base ref exists" in result.stderr
