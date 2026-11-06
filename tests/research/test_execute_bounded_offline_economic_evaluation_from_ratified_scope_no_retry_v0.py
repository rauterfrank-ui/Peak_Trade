from __future__ import annotations

import ast
from pathlib import Path


RUNNER = Path(
    "scripts/research/"
    "execute_bounded_offline_economic_evaluation_from_ratified_scope_no_retry_v0.py"
)
PREFERRED_OWNER = Path(
    "scripts/ops/materialize_final_research_fleet_offline_economic_evaluation_execution_v0.py"
)


def test_dedicated_execute_runner_exists() -> None:
    assert RUNNER.is_file()


def test_preferred_existing_owner_exists() -> None:
    assert PREFERRED_OWNER.is_file()


def test_runner_is_parseable_and_binds_single_preferred_owner() -> None:
    tree = ast.parse(RUNNER.read_text(encoding="utf-8"))
    assignments = {
        node.targets[0].id: ast.literal_eval(node.value)
        for node in tree.body
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id == "PREFERRED_OWNER_RELATIVE_PATH"
    }
    assert assignments == {
        "PREFERRED_OWNER_RELATIVE_PATH": str(PREFERRED_OWNER),
    }


def test_runner_fail_closed_without_durable_evidence_root() -> None:
    text = RUNNER.read_text(encoding="utf-8")
    assert "missing required durable evidence root" in text
    assert "raise SystemExit" in text


def test_runner_delegates_materializer_cli_contract() -> None:
    text = RUNNER.read_text(encoding="utf-8")
    assert "--confirm-go-token" in text
    assert "--binding-completion-path" in text
    assert "--durable-evidence-root" in text
    assert "runpy.run_path" in text


def test_runner_inserts_repo_root_on_sys_path_before_delegation() -> None:
    text = RUNNER.read_text(encoding="utf-8")
    assert "repo_root_str = str(repo_root)" in text
    assert "sys.path.insert(0, repo_root_str)" in text
