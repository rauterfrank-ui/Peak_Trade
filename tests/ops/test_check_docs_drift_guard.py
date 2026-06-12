"""Tests for docs drift evaluation (ops.truth) — deterministic mapping logic."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys

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
            sys.executable,
            str(
                Path(__file__).resolve().parents[2]
                / "scripts"
                / "ops"
                / "check_docs_drift_guard.py"
            ),
            "--base",
            "definitely_missing_base_ref_for_contract_probe",
            "--repo-root",
            str(repo),
            "--config",
            str(Path(__file__).resolve().parents[2] / "config" / "ops" / "docs_truth_map.yaml"),
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


REPO_ROOT = Path(__file__).resolve().parents[2]
CI_AUDIT = REPO_ROOT / "docs" / "ops" / "CI_AUDIT_KNOWN_ISSUES.md"
DOCS_TRUTH_MAP = REPO_ROOT / "docs" / "ops" / "registry" / "DOCS_TRUTH_MAP.md"
DOCS_TRUTH_MAP_CONFIG = REPO_ROOT / "config" / "ops" / "docs_truth_map.yaml"
DOCS_DRIFT_GUARD_SCRIPT = REPO_ROOT / "scripts" / "ops" / "check_docs_drift_guard.py"
CV3_POINTER_INTEGRITY_HEADING = "### Docs drift / pointer integrity crosslink guard v0 (SLICE-CV-3)"
CV3_POINTER_INTEGRITY_BLOCK_ANCHOR = (
    "SLICE_CV3_DOCS_DRIFT_POINTER_INTEGRITY_CROSSLINK_GUARD_V0=true"
)
CV3_HISTOGRAM_GUARD_MODULE = (
    "tests/ci/test_cybersecurity_visibility_repo_static_histogram_"
    "artifact_retention_or_evidence_gap_crosslink_v0.py"
)


def test_docs_drift_guard_cv3_pointer_integrity_crosslink_v0() -> None:
    audit_text = CI_AUDIT.read_text(encoding="utf-8")
    truth_map = DOCS_TRUTH_MAP.read_text(encoding="utf-8")

    assert CV3_POINTER_INTEGRITY_HEADING in audit_text
    assert CV3_POINTER_INTEGRITY_BLOCK_ANCHOR in audit_text
    assert CV3_HISTOGRAM_GUARD_MODULE in audit_text
    assert str(DOCS_DRIFT_GUARD_SCRIPT.relative_to(REPO_ROOT)).replace("\\", "/") in audit_text
    assert str(DOCS_TRUTH_MAP_CONFIG.relative_to(REPO_ROOT)).replace("\\", "/") in audit_text
    assert Path(__file__).name in audit_text
    assert "DOCS_DRIFT_OR_POINTER_INTEGRITY_DEFERRED=true" in audit_text
    assert "DOCS_DRIFT_OR_POINTER_INTEGRITY_COMPLETE=false" in audit_text
    assert "docs_drift_or_pointer_integrity" in audit_text.lower()

    assert DOCS_TRUTH_MAP_CONFIG.is_file()
    assert DOCS_DRIFT_GUARD_SCRIPT.is_file()
    assert "check_docs_drift_guard.py" in truth_map
    assert "docs_truth_map.yaml" in truth_map
    assert "SLICE-CV-3" in truth_map
    assert "DOCS_DRIFT_OR_POINTER_INTEGRITY_DEFERRED=true" in truth_map
