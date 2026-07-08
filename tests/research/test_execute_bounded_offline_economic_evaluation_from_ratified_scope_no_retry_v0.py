from __future__ import annotations

import ast
from pathlib import Path


RUNNER = Path(
    "scripts/research/"
    "execute_bounded_offline_economic_evaluation_from_ratified_scope_no_retry_v0.py"
)
PREFERRED_OWNER = Path(
    "src/research/final_research_fleet_offline_economic_evaluation_execution_v0.py"
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


def test_runner_preserves_no_runtime_authority_boundary() -> None:
    text = RUNNER.read_text(encoding="utf-8")
    required_false_bindings = [
        "LIVE_AUTHORIZED = False",
        "READY_FOR_OPERATOR_ARMING = False",
        "ORDERS_ALLOWED = False",
        "SCHEDULER_RUNTIME_ALLOWED = False",
        "SHADOW_AUTHORIZED = False",
        "PAPER_AUTHORIZED = False",
        "TESTNET_AUTHORIZED = False",
        "CANARY_AUTHORIZED = False",
        "UNMODIFIED_BINDING_RETRY_ALLOWED = False",
    ]
    for binding in required_false_bindings:
        assert binding in text
    assert 'RETRY_MODE = "NO_RETRY"' in text


def test_runner_fail_closed_verdict_for_resolution_error() -> None:
    text = RUNNER.read_text(encoding="utf-8")
    assert "BLOCKED_RUNNER_RESOLUTION_NOT_EXACTLY_ONE" in text
    assert "resolved_count" in text
    assert "runpy.run_path" in text


def test_runner_inserts_repo_root_on_sys_path_before_delegation() -> None:
    text = RUNNER.read_text(encoding="utf-8")
    assert "repo_root_str = str(repo_root)" in text
    assert "sys.path.insert(0, repo_root_str)" in text
