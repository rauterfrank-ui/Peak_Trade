from __future__ import annotations

from pathlib import Path


RUNNER = Path(
    "scripts/research/execute_bounded_offline_economic_evaluation_from_ratified_scope_no_retry_v0.py"
)
MATERIALIZER = (
    "scripts/ops/materialize_final_research_fleet_offline_economic_evaluation_execution_v0.py"
)
LIBRARY_DELEGATE = "src/research/final_research_fleet_offline_economic_evaluation_execution_v0.py"


def test_execute_runner_delegates_to_materializing_owner() -> None:
    text = RUNNER.read_text()
    assert MATERIALIZER in text
    assert LIBRARY_DELEGATE not in text


def test_execute_runner_preserves_repo_root_sys_path_guard() -> None:
    text = RUNNER.read_text()
    assert "repo_root_str = str(repo_root)" in text
    assert "sys.path.insert(0, repo_root_str)" in text
