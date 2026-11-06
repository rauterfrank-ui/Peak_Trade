"""WP3 isolation: imports, writes, and protected blobs stay inside the new package."""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

import pytest

from scripts.ops.mv2_outer_boundary_projector_v1.cli_v1 import main
from scripts.ops.mv2_outer_boundary_projector_v1.countercheck_v1 import (
    scan_package_imports_v1,
    scan_pinned_ghv_imports_v1,
    scan_reverse_importers_v1,
)
from scripts.ops.mv2_outer_boundary_projector_v1.input_contract_v1 import ProjectorRequestV1
from scripts.ops.mv2_outer_boundary_projector_v1.run_v1 import (
    run_mv2_outer_boundary_projector_v1,
)

REPO = Path(__file__).resolve().parents[2]
PACKAGE = REPO / "scripts" / "ops" / "mv2_outer_boundary_projector_v1"
PIN_COMMIT = "7628005ae495c115ff341d32fa932b7f4642f456"
PIN_TREE = "e652f8d7b86c469311a068c34b0fb3f708c87d73"
PROTECTED_WORKTREE = (
    "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py",
    "src/trading/master_v2/naked_mv2_double_play_core_authority_hardening_v1.py",
    "scripts/ops/ghv_forensic_whole_system_crosswalk_v1/edges_v1.py",
    "config/governance/current_system_census_graph_v1/source_v1.json",
    "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md",
    "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md",
)
PROTECTED_BLOBS = (
    "src/ops/ghosv_bounded_context_v1/pipeline_v1.py",
    "scripts/ops/ghv_forensic_whole_system_crosswalk_v1/traversal_v1.py",
    "scripts/ops/ghv_forensic_whole_system_causal_integration_v1/integrate_v1.py",
    "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py",
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _blob(path: str) -> str:
    completed = subprocess.run(
        ["git", "rev-parse", f"{PIN_COMMIT}:{path}"],
        cwd=REPO,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def test_package_imports_and_reverse_dependencies_stay_inside_the_boundary() -> None:
    imports = scan_package_imports_v1(PACKAGE)
    forbidden_tokens = ("trading", "execution", "risk", "ghosv_bounded_context_v1")
    assert all(token not in module for module in imports for token in forbidden_tokens)
    assert scan_reverse_importers_v1(REPO, PACKAGE) == []
    assert scan_pinned_ghv_imports_v1(REPO, PIN_COMMIT) == []


def test_run_does_not_write_protected_or_productive_files() -> None:
    before_files = {relative: _sha256(REPO / relative) for relative in PROTECTED_WORKTREE}
    before_blobs = {relative: _blob(relative) for relative in PROTECTED_BLOBS}
    report = run_mv2_outer_boundary_projector_v1(
        ProjectorRequestV1(commit=PIN_COMMIT, tree=PIN_TREE),
        repo_root=REPO,
    )
    after_files = {relative: _sha256(REPO / relative) for relative in PROTECTED_WORKTREE}
    after_blobs = {relative: _blob(relative) for relative in PROTECTED_BLOBS}
    assert before_files == after_files
    assert before_blobs == after_blobs
    countercheck = report["COUNTERCHECK_RESULTS"]
    assert countercheck["execution_ghosv_imported"] is False
    assert countercheck["execution_ghosv_modified"] is False
    assert countercheck["productive_modules_imported"] is False
    assert countercheck["worktree_sources_used_as_evidence"] is False
    assert countercheck["causal_integration_invoked"] is False
    assert countercheck["isolation"] == "WITHIN_AUTHORIZED_NEW_PACKAGE"
    assert countercheck["universe_ratification"] is False


def test_cli_wrong_tree_exits_fail_closed(capsys: pytest.CaptureFixture[str]) -> None:
    code = main(
        [
            "--commit",
            PIN_COMMIT,
            "--tree",
            "1111111111111111111111111111111111111111",
            "--repo-root",
            str(REPO),
        ]
    )
    captured = capsys.readouterr()
    assert code == 2
    assert "FAIL_CLOSED TREE_MISMATCH" in captured.err
    assert captured.out == ""


def test_package_sources_do_not_open_worktree_evidence_files() -> None:
    for path in PACKAGE.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "read_text(" not in text or path.name == "countercheck_v1.py"
        assert "source_v1.json" not in text or "git" in text or path.name == "constants_v1.py"
