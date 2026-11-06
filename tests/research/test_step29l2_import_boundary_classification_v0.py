"""Contract tests for STEP29L.2 import boundary classification (AST/tokenize owner)."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from research.linear_evidence.import_boundary import (
    classify_import_boundary_scan,
    module_violates_forbidden_boundary,
    scan_file_import_boundary,
    scan_paths_import_boundary,
)
from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256
from scripts.research.classify_step29l2_offline_linear_evidence_status_after_pr5044_v0 import (
    run_classification,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CLASSIFY_SCRIPT = (
    REPO_ROOT
    / "scripts/research/classify_step29l2_offline_linear_evidence_status_after_pr5044_v0.py"
)
INIT_PATH = REPO_ROOT / "src/research/linear_evidence/__init__.py"


def _write_probe_file(tmp_path: Path, name: str, source: str) -> Path:
    path = tmp_path / name
    path.write_text(textwrap.dedent(source).strip() + "\n", encoding="utf-8")
    return path


def test_module_violates_forbidden_boundary_segments() -> None:
    assert module_violates_forbidden_boundary("src.scheduler.jobs")
    assert module_violates_forbidden_boundary("src.live.execution")
    assert module_violates_forbidden_boundary("src.runtime.bridge")
    assert module_violates_forbidden_boundary("src.order_adapter.submit")
    assert not module_violates_forbidden_boundary("research.linear_evidence.contracts")


def test_docstring_with_scheduler_is_ignored(tmp_path: Path) -> None:
    path = _write_probe_file(
        tmp_path,
        "docstring_probe.py",
        '''
        """Offline only; must not import scheduler paths."""
        x = 1
        ''',
    )
    hits = scan_file_import_boundary(path)
    assert hits == []
    _, probes = scan_paths_import_boundary([path], repo_root=tmp_path)
    classification = classify_import_boundary_scan(hits, docstring_comment_probes=probes)
    assert classification["IMPORT_BOUNDARY_STATUS"] == "PASS_DOCSTRING_FALSE_POSITIVE_IGNORED"
    assert classification["false_positive_docstring_ignored"] is True


def test_comment_with_runtime_order_adapter_is_ignored(tmp_path: Path) -> None:
    path = _write_probe_file(
        tmp_path,
        "comment_probe.py",
        """
        # runtime/order adapter imports are forbidden here
        value = 42
        """,
    )
    hits = scan_file_import_boundary(path)
    assert hits == []
    _, probes = scan_paths_import_boundary([path], repo_root=tmp_path)
    classification = classify_import_boundary_scan(hits, docstring_comment_probes=probes)
    assert classification["IMPORT_BOUNDARY_STATUS"] == "PASS_DOCSTRING_FALSE_POSITIVE_IGNORED"
    assert classification["false_positive_docstring_ignored"] is True


@pytest.mark.parametrize(
    ("source", "expected_module"),
    [
        ("import src.scheduler.jobs", "src.scheduler.jobs"),
        ("from src.live.execution import lane", "src.live.execution"),
    ],
)
def test_real_imports_are_blocked(
    tmp_path: Path,
    source: str,
    expected_module: str,
) -> None:
    path = _write_probe_file(tmp_path, "bad_import.py", source)
    hits = scan_file_import_boundary(path)
    assert len(hits) == 1
    assert hits[0].module == expected_module
    classification = classify_import_boundary_scan(hits)
    assert classification["IMPORT_BOUNDARY_STATUS"] == "REVIEW_REQUIRED"
    assert classification["BAD_IMPORT_BOUNDARY_HITS"] == 1


def test_linear_evidence_init_docstring_is_not_import_hit() -> None:
    hits = scan_file_import_boundary(INIT_PATH, repo_root=REPO_ROOT)
    assert hits == []


def test_classification_runner_emits_expected_artifacts(tmp_path: Path) -> None:
    rc = run_classification(output_dir=tmp_path, repo_root=REPO_ROOT)
    assert rc == 0

    boundary_text = (tmp_path / "import_boundary_classification.txt").read_text(encoding="utf-8")
    assert "IMPORT_BOUNDARY_STATUS=PASS_DOCSTRING_FALSE_POSITIVE_IGNORED" in boundary_text
    assert "false_positive_docstring_ignored=true" in boundary_text
    assert "STEP29L2_SURFACE_STATUS=COMPLETE" in (tmp_path / "classification.txt").read_text(
        encoding="utf-8"
    )
    assert "MISSING_SURFACE=NONE" in (tmp_path / "classification.txt").read_text(encoding="utf-8")
    assert "NEXT_GAP_CLASS=NONE" in (tmp_path / "final_report.txt").read_text(encoding="utf-8")

    ok, _msg = verify_manifest_sha256(tmp_path)
    assert ok
    assert (tmp_path / "final_report.txt").is_file()
    assert (tmp_path / "MANIFEST.sha256").is_file()


def test_classify_script_uses_ast_not_raw_grep() -> None:
    source = CLASSIFY_SCRIPT.read_text(encoding="utf-8")
    assert "grep" not in source
    assert "scan_paths_import_boundary" in source
    assert "import_boundary" in source


def test_import_boundary_module_uses_ast_walk_for_imports_only() -> None:
    module_path = REPO_ROOT / "src/research/linear_evidence/import_boundary.py"
    source = module_path.read_text(encoding="utf-8")
    assert "isinstance(node, ast.Import)" in source
    assert "isinstance(node, ast.ImportFrom)" in source
    assert "tokenize.tokenize" in source
