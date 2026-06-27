"""Contract tests for diff-aware required test selection (ci.yml v1)."""

from __future__ import annotations

import ast
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

CI_YML = Path(".github/workflows/ci.yml")
SELECTOR = Path("scripts/ops/ci_test_selection_v1.py")
MAPPING = Path("config/ci/file_category_mapping.yaml")


def _glb019_canonical_baseline(repo_root: Path, path: str) -> str:
    from tests.ci._glb019_synthetic_patch_builder_v0 import glb019_a2b_canonical_baseline_text

    return glb019_a2b_canonical_baseline_text(repo_root, path)


@pytest.fixture(autouse=True)
def _glb019_archived_contract_baseline(
    monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest
) -> None:
    """Align GLB-019 contract evaluation with embedded pre-merge baselines."""
    if "glb019" not in request.node.name.lower():
        return
    import scripts.ops.durable_completion_integration_partitions_v0 as partitions

    original = partitions._base_file_text

    def _embedded_baseline(repo_root: Path, path: str) -> str:
        from tests.ci._glb019_synthetic_patch_builder_v0 import _canonical_baseline_by_path

        baselines = _canonical_baseline_by_path()
        if path in baselines:
            return baselines[path]
        return original(repo_root, path)

    monkeypatch.setattr(partitions, "_base_file_text", _embedded_baseline)


def _ci_text() -> str:
    return CI_YML.read_text(encoding="utf-8")


def _run_selector(
    *files: str, force_full: bool = False, event_name: str = "pull_request"
) -> dict[str, str]:
    cmd = [sys.executable, str(SELECTOR), "--event-name", event_name]
    if files:
        cmd.extend(["--files", *files])
    if force_full:
        cmd.append("--force-full")
    out = subprocess.check_output(cmd, text=True)
    result: dict[str, str] = {}
    for line in out.splitlines():
        key, _, value = line.partition("=")
        result[key] = value
    return result


def _targets(sel: dict[str, str]) -> list[str]:
    raw = sel.get("focused_pytest_targets", "")
    return sorted(raw.split()) if raw else []


def _modules(sel: dict[str, str]) -> list[str]:
    raw = sel.get("focused_module_imports", "")
    return sorted(raw.split()) if raw else []


def test_required_tests_job_has_no_job_level_if() -> None:
    text = _ci_text()
    tests_block = text.split("  tests:", 1)[1].split("  strategy-smoke:", 1)[0]
    assert "if:" not in tests_block.split("steps:")[0]


def test_tests_job_timeout_25_absolute_cap() -> None:
    assert re.search(
        r"^\s*tests:\n(?:.*\n)*?\s*timeout-minutes:\s*25\s*$", _ci_text(), re.MULTILINE
    )
    tests_block = _ci_text().split("  tests:", 1)[1].split("  strategy-smoke:", 1)[0]
    assert "timeout-minutes: 17" not in tests_block


def test_fast_lane_job_timeout_10_absolute_cap() -> None:
    assert re.search(
        r"^\s*fast-lane:\n(?:.*\n)*?\s*timeout-minutes:\s*10\s*$", _ci_text(), re.MULTILINE
    )
    assert (
        "timeout-minutes: 25" not in _ci_text().split("  fast-lane:", 1)[1].split("  tests:", 1)[0]
    )


def test_ci_workflow_job_timeouts_do_not_exceed_25_minute_hard_cap() -> None:
    for match in re.finditer(r"timeout-minutes:\s*(\d+)", _ci_text()):
        assert int(match.group(1)) <= 25, "CI job exceeds 25-minute hard cap"


def _job_checkout_step_block(job_name: str, *, next_job: str) -> str:
    text = _ci_text()
    job_block = text.split(f"  {job_name}:", 1)[1].split(f"  {next_job}:", 1)[0]
    return job_block.split("- name: Checkout", 1)[1].split("\n      - name:", 1)[0]


def test_changes_job_checkout_fetch_depth_zero_unchanged() -> None:
    assert "fetch-depth: 0" in _job_checkout_step_block(
        "changes", next_job="ci-required-contexts-contract"
    )


def test_fast_lane_checkout_fetch_depth_zero_unchanged() -> None:
    assert "fetch-depth: 0" in _job_checkout_step_block("fast-lane", next_job="tests")


def test_tests_job_matrix_checkout_fetch_depth_zero_for_live_patch_contract() -> None:
    assert "fetch-depth: 0" in _job_checkout_step_block("tests", next_job="strategy-smoke")


def test_changes_job_exports_test_selection_outputs() -> None:
    text = _ci_text()
    for key in (
        "test_selection_mode",
        "test_selection_reason",
        "tests_execute_full",
        "tests_execute_contract_focused",
        "tests_execute_focused",
        "tests_execute_pr_bounded_full",
        "tests_execute_exhaustive_full",
        "tests_execute_invalid",
        "pr_bounded_pytest_targets",
        "tests_execute_no_op",
        "focused_pytest_targets",
        "focused_module_imports",
        "fast_lane_contract_mode",
        "fast_lane_contract_pytest_targets",
        "matrix_contract_mode",
        "matrix_contract_reason",
        "matrix_contract_pytest_targets",
        "tests_execute_matrix_contract_focused",
    ):
        assert (
            f"{key}:"
            in text.split("  changes:", 1)[1].split("  ci-required-contexts-contract:", 1)[0]
        )


def test_tests_job_has_no_op_step() -> None:
    assert "NO_OP — skip full matrix tests (diff-aware)" in _ci_text()
    assert "tests_execute_no_op == 'true'" in _ci_text()


def test_tests_job_has_focused_and_full_steps() -> None:
    text = _ci_text()
    assert "Run EXHAUSTIVE_FULL test suite" in text
    assert "Run focused tests (matrix)" in text
    assert "Run tests with coverage (EXHAUSTIVE_FULL only)" in text
    assert "Run PR_BOUNDED_FULL tests (matrix)" in text


def test_tests_job_focused_runs_on_all_matrix_versions() -> None:
    text = _ci_text()
    focused_step = text.split("name: Run focused tests (matrix)", 1)[1].split("\n      - name:", 1)[
        0
    ]
    assert (
        "matrix_contract_mode != 'MATRIX_CONTRACT_FOCUSED' || matrix.python-version == '3.11'"
        in focused_step
    )
    assert "tests_execute_contract_focused == 'true'" in focused_step


def test_tests_job_matrix_contract_focused_non_canonical_version_ack_step() -> None:
    text = _ci_text()
    assert "MATRIX_CONTRACT_FOCUSED — non-canonical version ack (diff-aware)" in text
    assert (
        "matrix_contract_mode == 'MATRIX_CONTRACT_FOCUSED' && matrix.python-version != '3.11'"
        in text
    )


def test_tests_job_full_suite_excludes_matrix_contract_focused() -> None:
    full_block = (
        _ci_text()
        .split("name: Run EXHAUSTIVE_FULL test suite", 1)[1]
        .split("name: Run focused tests (matrix)", 1)[0]
    )
    assert "matrix_contract_mode != 'MATRIX_CONTRACT_FOCUSED'" in full_block


def _focused_matrix_step_block() -> str:
    return _ci_text().split("name: Run focused tests (matrix)", 1)[1].split("\n      - name:", 1)[0]


def test_tests_job_focused_matrix_integration_parallel_sharding_contract() -> None:
    block = _focused_matrix_step_block()
    assert "INTEGRATION_SHARD_COUNT=3" in block
    assert "PYTHONUNBUFFERED=1" in block
    assert "_launch_focused_lane" in block
    assert "integration_shard_" in block
    assert "SHARD_FAIL=0" in block
    assert "if (( ${#INTEGRATION_NODES[@]} == 0 )); then" in block
    assert 'pytest "${VALIDATED_TARGETS[@]}" "${PYTEST_ARGS[@]}"' in block
    assert 'wait "${PIDS[$idx]}"' in block
    assert "exit 1" in block
    assert "|| true" not in block


def test_tests_job_focused_matrix_parallel_sharding_does_not_affect_full_suite_step() -> None:
    text = _ci_text()
    full_block = text.split("name: Run EXHAUSTIVE_FULL test suite", 1)[1].split(
        "name: Run focused tests (matrix)", 1
    )[0]
    assert "INTEGRATION_SHARD_COUNT" not in full_block
    assert "pytest tests/ -v --tb=short" in full_block


def test_focused_matrix_integration_shard_round_robin_distribution() -> None:
    """45 integration nodes partition into three shards with no loss or duplication."""
    integration_owner = (
        "tests/ops/test_bounded_futures_testnet_durable_run_primary_evidence_"
        "completion_integration_contract_v0.py"
    )
    nodes = [f"{integration_owner}::test_node_{i}" for i in range(45)]
    shard_count = 3
    shards: list[list[str]] = [[] for _ in range(shard_count)]
    for idx, node in enumerate(nodes):
        shards[idx % shard_count].append(node)
    flattened = [node for shard in shards for node in shard]
    assert len(flattened) == 45
    assert len(flattened) == len(set(flattened))
    assert all(len(shard) in {15, 15, 15} for shard in shards)


def test_focused_matrix_glb019_a2b_target_groups_complete() -> None:
    from scripts.ops.durable_completion_integration_partitions_v0 import (
        CI_GLB019_SYNTHETIC_PATCH_BUILDER,
        GLB019_A2B_ADDITIVE_PARTITIONS,
        expand_partitions_to_pytest_targets,
    )
    from tests.ci._glb019_synthetic_patch_builder_v0 import (
        synthetic_glb019_a2b_positive_patch_text as patch_text,
    )

    expected_integration_nodes = sorted(
        expand_partitions_to_pytest_targets(GLB019_A2B_ADDITIVE_PARTITIONS)
    )
    glb019_files = (
        "scripts/ops/durable_completion_integration_partitions_v0.py",
        "src/ops/bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0.py",
        "src/ops/durable_completion_validation/graph.py",
        "src/ops/durable_completion_validation/validators/event_stream.py",
        CI_GLB019_SYNTHETIC_PATCH_BUILDER,
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
        "tests/ops/test_bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0.py",
        "tests/ops/test_durable_completion_validation_graph_v1.py",
    )
    sel = _run_selector_with_patch(patch_text(), *glb019_files)
    targets = _targets(sel)
    ci_owner = "tests/ci/test_ci_diff_aware_test_selection_v1.py"
    graph_owner = "tests/ops/test_durable_completion_validation_graph_v1.py"
    integration_nodes = sorted(t for t in targets if "::" in t)
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert sel["test_selection_reason"] == "glb019_a2b_additive_change_contract"
    assert ci_owner in targets
    assert graph_owner in targets
    assert integration_nodes == expected_integration_nodes
    assert len(targets) == 2 + len(expected_integration_nodes)


def test_tests_job_focused_module_import_smoke_step() -> None:
    assert "Focused module import smoke" in _ci_text()
    assert "focused_module_imports" in _ci_text()
    assert "--import-smoke-modules" in _ci_text()


def test_selector_ci_workflow_shard_bootstrap_focused() -> None:
    sel = _run_selector(
        ".github/workflows/ci.yml",
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
    )
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert sel["test_selection_reason"] == "ci_infra_focused"
    assert sel["tests_execute_full"] == "false"
    assert sel["tests_execute_focused"] == "true"


def test_selector_docs_only_no_op() -> None:
    sel = _run_selector("docs/TECH_DEBT_BACKLOG.md", "README.md")
    assert sel["test_selection_mode"] == "NO_OP"
    assert sel["tests_execute_no_op"] == "true"


def test_selector_workflow_only_no_op() -> None:
    sel = _run_selector(".github/workflows/ci.yml")
    assert sel["test_selection_mode"] == "NO_OP"


def test_selector_central_src_full() -> None:
    sel = _run_selector("src/strategies/__init__.py")
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert sel["tests_execute_pr_bounded_full"] == "true"
    assert sel["tests_execute_full"] == "false"


def test_selector_registry_init_full() -> None:
    sel = _run_selector(
        "src/strategies/__init__.py",
        "tests/test_strategy_vol_regime_filter.py",
    )
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"


def test_selector_composite_full() -> None:
    sel = _run_selector(
        "src/strategies/composite.py",
        "tests/test_strategy_composite.py",
    )
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"


def test_selector_dependencies_full() -> None:
    sel = _run_selector("requirements.txt")
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"


def test_selector_global_test_infra_full() -> None:
    sel = _run_selector("tests/conftest.py")
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"


def test_selector_scripts_focused() -> None:
    sel = _run_selector("scripts/demo_strategy_research.py")
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert (
        "tests/scripts/test_demo_strategy_research_load_strategy_v1.py"
        in sel["focused_pytest_targets"]
    )
    assert "tests/scripts/test_demo_strategy_research.py" not in sel["focused_pytest_targets"]


def test_selector_scripts_focused_omits_nonexistent_test_paths() -> None:
    sel = _run_selector(
        "scripts/run_momentum_realistic.py",
        "scripts/run_offline_realtime_ma_crossover.py",
    )
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    targets = _targets(sel)
    assert "tests/scripts/test_run_momentum_realistic_load_strategy_v1.py" in targets
    assert "tests/scripts/test_run_offline_realtime_ma_crossover_load_strategy_v1.py" in targets
    assert "tests/scripts/test_run_momentum_realistic.py" not in targets
    assert "tests/scripts/test_run_offline_realtime_ma_crossover.py" not in targets


def test_selector_strategy_vol_breakout_owner_focused() -> None:
    sel = _run_selector(
        "src/strategies/vol_breakout.py",
        "tests/test_strategies_phase27.py",
    )
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert sel["test_selection_reason"] == "strategy_regime_owner_focused"
    assert "tests/test_strategies_phase27.py" in _targets(sel)
    assert _modules(sel) == ["src.strategies.vol_breakout"]


def test_selector_strategy_vol_regime_filter_owner_focused() -> None:
    sel = _run_selector(
        "src/strategies/vol_regime_filter.py",
        "tests/test_strategy_vol_regime_filter.py",
    )
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert "tests/test_strategy_vol_regime_filter.py" in _targets(sel)
    assert _modules(sel) == ["src.strategies.vol_regime_filter"]


def test_selector_regime_detectors_owner_focused() -> None:
    sel = _run_selector(
        "src/regime/detectors.py",
        "tests/test_regime_detection.py",
    )
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert "tests/test_regime_detection.py" in _targets(sel)
    assert _modules(sel) == ["src.regime.detectors"]


def test_selector_el_karoui_vol_model_owner_focused() -> None:
    sel = _run_selector(
        "src/strategies/el_karoui/vol_model.py",
        "tests/strategies/el_karoui/test_vol_model.py",
    )
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert "tests/strategies/el_karoui/test_vol_model.py" in _targets(sel)
    assert _modules(sel) == ["src.strategies.el_karoui.vol_model"]


def test_selector_strategy_owner_includes_load_strategy_contract_tests() -> None:
    sel = _run_selector(
        "src/strategies/vol_breakout.py",
        "tests/test_strategies_phase27.py",
    )
    targets = _targets(sel)
    assert "tests/scripts/test_demo_strategy_research_load_strategy_v1.py" in targets


def test_selector_focused_targets_sorted_deterministically() -> None:
    sel = _run_selector(
        "src/strategies/vol_breakout.py",
        "tests/test_strategies_phase27.py",
    )
    assert _targets(sel) == sorted(_targets(sel))


def test_selector_prod_only_without_test_owner_full() -> None:
    sel = _run_selector("src/strategies/vol_breakout.py")
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert sel["test_selection_reason"] == "strategy_regime_owner_incomplete_or_ambiguous"


def test_selector_two_prod_files_full() -> None:
    sel = _run_selector(
        "src/strategies/vol_breakout.py",
        "src/strategies/vol_regime_filter.py",
        "tests/test_strategies_phase27.py",
    )
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"


def test_selector_strategy_plus_foreign_test_owner_full() -> None:
    sel = _run_selector(
        "src/strategies/vol_breakout.py",
        "tests/test_strategy_vol_regime_filter.py",
    )
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"


def test_selector_strategy_plus_conftest_full() -> None:
    sel = _run_selector(
        "src/strategies/vol_breakout.py",
        "tests/test_strategies_phase27.py",
        "tests/conftest.py",
    )
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"


def test_selector_strategy_plus_dependency_full() -> None:
    sel = _run_selector(
        "src/strategies/vol_breakout.py",
        "tests/test_strategies_phase27.py",
        "requirements.txt",
    )
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"


def test_selector_strategy_plus_pyproject_full() -> None:
    sel = _run_selector(
        "src/strategies/vol_breakout.py",
        "tests/test_strategies_phase27.py",
        "pyproject.toml",
    )
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"


def test_selector_strategy_plus_workflow_full() -> None:
    sel = _run_selector(
        "src/strategies/vol_breakout.py",
        "tests/test_strategies_phase27.py",
        ".github/workflows/lint.yml",
    )
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"


def test_selector_ci_bootstrap_selector_only_focused() -> None:
    sel = _run_selector("scripts/ops/ci_test_selection_v1.py")
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert sel["test_selection_reason"] == "ci_bootstrap_focused"
    assert "tests/ci/test_ci_diff_aware_test_selection_v1.py" in _targets(sel)
    assert sel["tests_execute_full"] == "false"


def test_selector_ci_bootstrap_selector_plus_contract_focused() -> None:
    sel = _run_selector(
        "scripts/ops/ci_test_selection_v1.py",
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
    )
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert sel["test_selection_reason"] == "ci_bootstrap_focused"
    assert _targets(sel) == ["tests/ci/test_ci_diff_aware_test_selection_v1.py"]
    assert sel["tests_execute_full"] == "false"


def test_selector_ci_bootstrap_plus_workflow_full() -> None:
    sel = _run_selector(
        "scripts/ops/ci_test_selection_v1.py",
        ".github/workflows/ci.yml",
    )
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert sel["test_selection_reason"] == "ci_bootstrap_mixed_diff_requires_full"


def test_selector_ci_bootstrap_plus_dependency_full() -> None:
    sel = _run_selector(
        "scripts/ops/ci_test_selection_v1.py",
        "requirements.txt",
    )
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert sel["test_selection_reason"] == "ci_bootstrap_mixed_diff_requires_full"


def test_selector_ci_bootstrap_plus_central_src_full() -> None:
    sel = _run_selector(
        "scripts/ops/ci_test_selection_v1.py",
        "src/core/foo.py",
    )
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert sel["test_selection_reason"] == "ci_bootstrap_mixed_diff_requires_full"


def test_selector_ci_bootstrap_plus_unknown_full() -> None:
    sel = _run_selector(
        "scripts/ops/ci_test_selection_v1.py",
        "misc/unclassified.bin",
    )
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert sel["test_selection_reason"] == "ci_bootstrap_mixed_diff_requires_full"


def test_selector_ci_bootstrap_contract_test_only_focused() -> None:
    sel = _run_selector("tests/ci/test_ci_diff_aware_test_selection_v1.py")
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert sel["test_selection_reason"] == "ci_bootstrap_focused"


GLB019_CI_BOOTSTRAP_PR_FILES = (
    "scripts/ops/ci_test_selection_v1.py",
    "scripts/ops/durable_completion_integration_partitions_v0.py",
    "tests/ci/test_ci_diff_aware_test_selection_v1.py",
    "tests/ci/_glb019_synthetic_patch_builder_v0.py",
)


def test_selector_glb019_ci_bootstrap_pr_four_file_diff_focused() -> None:
    sel = _run_selector(*GLB019_CI_BOOTSTRAP_PR_FILES)
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert sel["test_selection_reason"] == "ci_bootstrap_focused"
    assert _targets(sel) == ["tests/ci/test_ci_diff_aware_test_selection_v1.py"]
    assert sel["tests_execute_full"] == "false"


def test_selector_glb019_ci_bootstrap_pr_four_files_plus_unknown_ci_helper_full() -> None:
    sel = _run_selector(*GLB019_CI_BOOTSTRAP_PR_FILES, "tests/ci/test_unknown_helper_v0.py")
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert sel["test_selection_reason"] == "ci_bootstrap_mixed_diff_requires_full"


def test_selector_glb019_ci_bootstrap_pr_four_files_plus_workflow_ci_infra_focused() -> None:
    sel = _run_selector(*GLB019_CI_BOOTSTRAP_PR_FILES, ".github/workflows/ci.yml")
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert sel["test_selection_reason"] == "selector_self_change_bootstrap"
    assert sel["tests_execute_pr_bounded_full"] == "true"


GLB019_PARTITION_SELECTOR_BOOTSTRAP_FILES = (
    "scripts/ops/ci_test_selection_v1.py",
    "scripts/ops/durable_completion_integration_partitions_v0.py",
    "tests/ci/test_ci_diff_aware_test_selection_v1.py",
)
_PARTITIONS_HELPER = GLB019_PARTITION_SELECTOR_BOOTSTRAP_FILES[1]


def test_selector_glb019_partition_bootstrap_three_file_diff_focused() -> None:
    sel = _run_selector(*GLB019_PARTITION_SELECTOR_BOOTSTRAP_FILES)
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert sel["test_selection_reason"] == "ci_bootstrap_focused"
    assert _targets(sel) == ["tests/ci/test_ci_diff_aware_test_selection_v1.py"]
    assert sel["tests_execute_full"] == "false"
    assert (
        "tests/ops/test_bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0.py"
        not in _targets(sel)
    )


def test_selector_glb019_partition_bootstrap_selector_plus_helper_focused() -> None:
    sel = _run_selector(
        GLB019_PARTITION_SELECTOR_BOOTSTRAP_FILES[0],
        GLB019_PARTITION_SELECTOR_BOOTSTRAP_FILES[1],
    )
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert sel["test_selection_reason"] == "ci_bootstrap_focused"


def test_selector_glb019_partition_bootstrap_helper_plus_contract_focused() -> None:
    sel = _run_selector(
        GLB019_PARTITION_SELECTOR_BOOTSTRAP_FILES[1],
        GLB019_PARTITION_SELECTOR_BOOTSTRAP_FILES[2],
    )
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert sel["test_selection_reason"] == "ci_bootstrap_focused"


def test_selector_glb019_partition_bootstrap_helper_only_focused() -> None:
    sel = _run_selector(_PARTITIONS_HELPER)
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert sel["test_selection_reason"] == "ci_bootstrap_focused"


def test_selector_glb019_partition_bootstrap_plus_workflow_full() -> None:
    sel = _run_selector(
        *GLB019_PARTITION_SELECTOR_BOOTSTRAP_FILES,
        ".github/workflows/ci.yml",
    )
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert sel["test_selection_reason"] == "selector_self_change_bootstrap"


def test_selector_glb019_partition_bootstrap_plus_unknown_ci_script_full() -> None:
    sel = _run_selector(
        *GLB019_PARTITION_SELECTOR_BOOTSTRAP_FILES,
        "scripts/ops/ci_unknown_bootstrap_probe_v0.py",
    )
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert sel["test_selection_reason"] == "ci_bootstrap_mixed_diff_requires_full"


def test_selector_glb019_partition_bootstrap_plus_central_prod_full() -> None:
    sel = _run_selector(
        *GLB019_PARTITION_SELECTOR_BOOTSTRAP_FILES,
        "src/ops/bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0.py",
    )
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert sel["test_selection_reason"] == "durable_completion_foreign_path_requires_full"


_FACADE_PATH = "src/ops/bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0.py"
_SELECTOR_OWNER = "scripts/ops/ci_test_selection_v1.py"


def test_selector_glb019_a2b_selector_owner_plus_central_facade_selects_full() -> None:
    sel = _run_selector(_SELECTOR_OWNER, _FACADE_PATH)
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert sel["test_selection_reason"] == "durable_completion_foreign_path_requires_full"


_GLB019_SELECTOR_OWNER_FULL_REASONS = frozenset(
    {
        "durable_completion_foreign_path_requires_full",
        "durable_completion_incomplete_or_missing_test_owner",
    }
)


def test_selector_glb019_a2b_selector_owner_plus_facade_explicit_patch_still_full() -> None:
    patch = _synthetic_glb019_a2b_positive_patch_text()
    sel = _run_selector_with_patch(patch, _SELECTOR_OWNER, _FACADE_PATH, *GLB019_A2B_FILESET)
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert sel["test_selection_reason"] in _GLB019_SELECTOR_OWNER_FULL_REASONS


def test_selector_glb019_a2b_full_nine_file_pr_diff_focused() -> None:
    sel = _run_selector_with_patch(
        _synthetic_glb019_a2b_nine_file_patch_text(),
        *GLB019_A2B_FULL_PR_FILES,
    )
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert sel["test_selection_reason"] == "glb019_a2b_additive_change_contract"
    assert sel["tests_execute_full"] == "false"


def test_selector_glb019_a2b_full_nine_file_pr_explicit_git_diff_focused() -> None:
    sel = _run_selector_with_patch(
        _synthetic_glb019_a2b_nine_file_patch_text(),
        *GLB019_A2B_FULL_PR_FILES,
    )
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert sel["test_selection_reason"] == "glb019_a2b_additive_change_contract"
    assert sel["tests_execute_full"] == "false"
    targets = _targets(sel)
    assert "tests/ci/test_ci_diff_aware_test_selection_v1.py" in targets
    assert _GRAPH_OWNER in targets
    integration_nodes = [t for t in targets if t.startswith(f"{_INTEGRATION_OWNER}::test_")]
    assert len(integration_nodes) == 47


def test_selector_glb019_a2b_live_collect_patch_contract_focused() -> None:
    from pathlib import Path

    from scripts.ops.durable_completion_integration_partitions_v0 import (
        Glb019A2bChangeContractOutcome,
        GLB019_A2B_SELECTOR_OWNER,
        evaluate_glb019_a2b_change_contract,
        patch_includes_glb019_guarded_selector_owner_rewire,
    )

    files = list(GLB019_A2B_FULL_PR_FILES)
    patch = _synthetic_glb019_a2b_nine_file_patch_text()
    assert patch
    assert patch.strip()
    assert len(patch) > 0
    assert patch_includes_glb019_guarded_selector_owner_rewire(patch, changed_files=files)
    assert GLB019_A2B_SELECTOR_OWNER in patch
    contract = evaluate_glb019_a2b_change_contract(patch, repo_root=Path("."))
    assert contract.outcome == Glb019A2bChangeContractOutcome.PASS
    sel = _run_selector_with_patch(
        _synthetic_glb019_a2b_nine_file_patch_text(),
        *GLB019_A2B_FULL_PR_FILES,
    )
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert sel["test_selection_reason"] == "glb019_a2b_additive_change_contract"
    assert sel["tests_execute_full"] == "false"
    targets = _targets(sel)
    assert "tests/ci/test_ci_diff_aware_test_selection_v1.py" in targets
    assert _GRAPH_OWNER in targets
    integration_nodes = [t for t in targets if t.startswith(f"{_INTEGRATION_OWNER}::test_")]
    assert integration_nodes


def test_selector_glb019_a2b_live_patch_selector_owner_ast_validator_accepts() -> None:
    import ast
    from pathlib import Path

    from scripts.ops.durable_completion_integration_partitions_v0 import (
        GLB019_A2B_SELECTOR_OWNER,
        _apply_unified_hunks,
        _parse_unified_diff,
        _validate_selector_owner_glb019_rewire_ast,
    )

    files = list(GLB019_A2B_FULL_PR_FILES)
    patch = _synthetic_glb019_a2b_nine_file_patch_text()
    assert patch
    repo_root = Path(".")
    before = _glb019_canonical_baseline(repo_root, GLB019_A2B_SELECTOR_OWNER)
    after = _apply_unified_hunks(before, _parse_unified_diff(patch)[GLB019_A2B_SELECTOR_OWNER])
    assert _validate_selector_owner_glb019_rewire_ast(ast.parse(before), ast.parse(after))


def test_selector_glb019_a2b_missing_selector_owner_hunks_full() -> None:
    patch = _synthetic_glb019_a2b_positive_patch_text()
    sel = _run_selector_with_patch(patch, *GLB019_A2B_FULL_PR_FILES)
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert sel["test_selection_reason"] in _GLB019_SELECTOR_OWNER_FULL_REASONS


def test_selector_glb019_a2b_removed_binding_check_full() -> None:
    canonical = _selector_owner_canonical_after_text()
    needle = (
        "        if not patch_includes_glb019_guarded_selector_owner_rewire(\n"
        "            patch_text,\n"
        "            changed_files=files,\n"
        "        ):\n"
        "            return None\n"
    )
    assert needle in canonical
    mutated = canonical.replace(needle, "", 1)
    patch = _guarded_mixed_patch_with_selector_after(mutated)
    sel = _run_selector_with_patch(patch, *GLB019_A2B_FULL_PR_FILES)
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert sel["test_selection_reason"] in _GLB019_SELECTOR_OWNER_FULL_REASONS


def test_selector_glb019_a2b_removed_evaluate_call_full() -> None:
    canonical = _selector_owner_canonical_after_text()
    needle = (
        "        contract = evaluate_glb019_a2b_change_contract(patch_text, repo_root=_REPO_ROOT)\n"
        "        return _selection_result_for_glb019_a2b_change_contract(\n"
        "            files,\n"
        "            contract,\n"
        "            patch_text=patch_text,\n"
        "        )\n"
    )
    assert needle in canonical
    mutated = canonical.replace(needle, "        return None\n", 1)
    patch = _guarded_mixed_patch_with_selector_after(mutated)
    sel = _run_selector_with_patch(patch, *GLB019_A2B_FULL_PR_FILES)
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert sel["test_selection_reason"] in _GLB019_SELECTOR_OWNER_FULL_REASONS


def test_selector_glb019_a2b_classify_bypass_reintroduced_full() -> None:
    canonical = _selector_owner_canonical_after_text()
    needle = (
        "    if selector_owner_changed and guarded_mixed_candidate:\n"
        "        if not patch_text:\n"
        "            return None\n"
        "        if not patch_includes_glb019_guarded_selector_owner_rewire(\n"
        "            patch_text,\n"
        "            changed_files=files,\n"
        "        ):\n"
        "            return None\n"
        "        contract = evaluate_glb019_a2b_change_contract(patch_text, repo_root=_REPO_ROOT)\n"
        "        return _selection_result_for_glb019_a2b_change_contract(\n"
        "            files,\n"
        "            contract,\n"
        "            patch_text=patch_text,\n"
        "        )\n"
    )
    assert needle in canonical
    mutated = canonical.replace(needle, "", 1)
    patch = _guarded_mixed_patch_with_selector_after(mutated)
    sel = _run_selector_with_patch(patch, *GLB019_A2B_FULL_PR_FILES)
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert sel["test_selection_reason"] in _GLB019_SELECTOR_OWNER_FULL_REASONS


def test_selector_glb019_a2b_extra_import_full() -> None:
    canonical = _selector_owner_canonical_after_text()
    needle = "    patch_includes_glb019_guarded_selector_owner_rewire,\n)"
    assert needle in canonical
    mutated = canonical.replace(
        needle,
        "    patch_includes_glb019_guarded_selector_owner_rewire,\n"
        "    DURABLE_COMPLETION_FACADE_PATH,\n)",
        1,
    )
    patch = _guarded_mixed_patch_with_selector_after(mutated)
    sel = _run_selector_with_patch(patch, *GLB019_A2B_FULL_PR_FILES)
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert sel["test_selection_reason"] in _GLB019_SELECTOR_OWNER_FULL_REASONS


def test_selector_glb019_a2b_extra_module_level_assignment_full() -> None:
    canonical = _selector_owner_canonical_after_text()
    mutated = 'CI_GLB019_SYNTHETIC_PATCH_BUILDER = "evil_probe_path"\n' + canonical
    patch = _guarded_mixed_patch_with_selector_after(mutated)
    sel = _run_selector_with_patch(patch, *GLB019_A2B_FULL_PR_FILES)
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert sel["test_selection_reason"] in _GLB019_SELECTOR_OWNER_FULL_REASONS


def test_selector_glb019_a2b_extra_structural_wrapper_branch_full() -> None:
    canonical = _selector_owner_canonical_after_text()
    needle = "def _is_glb019_a2b_structural_contract_candidate(changed_files: list[str]) -> bool:\n"
    assert needle in canonical
    mutated = canonical.replace(
        needle,
        needle + "    if changed_files:\n        return False\n",
        1,
    )
    patch = _guarded_mixed_patch_with_selector_after(mutated)
    sel = _run_selector_with_patch(patch, *GLB019_A2B_FULL_PR_FILES)
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert sel["test_selection_reason"] in _GLB019_SELECTOR_OWNER_FULL_REASONS


def test_selector_glb019_a2b_other_resolver_mutation_full() -> None:
    canonical = _selector_owner_canonical_after_text()
    needle = "def _try_ci_bootstrap_focused(files: list[str]) -> SelectionResult | None:\n"
    assert needle in canonical
    mutated = canonical.replace(
        needle,
        needle + "    return None\n",
        1,
    )
    patch = _guarded_mixed_patch_with_selector_after(mutated)
    sel = _run_selector_with_patch(patch, *GLB019_A2B_FULL_PR_FILES)
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert sel["test_selection_reason"] in _GLB019_SELECTOR_OWNER_FULL_REASONS


def test_selector_glb019_a2b_eight_file_subset_without_selector_owner_still_focused() -> None:
    sel = _run_selector_with_patch(
        _synthetic_glb019_a2b_positive_patch_text(),
        *GLB019_A2B_FILESET,
    )
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert sel["test_selection_reason"] == "glb019_a2b_additive_change_contract"
    assert sel["tests_execute_full"] == "false"


def test_selector_glb019_a2b_selector_owner_resolve_selection_body_change_full() -> None:
    canonical = _selector_owner_canonical_after_text()
    needle = "    return is_glb019_a2b_structural_contract_candidate(changed_files)"
    assert needle in canonical
    mutated = canonical.replace(needle, "    return True", 1)
    patch = _guarded_mixed_patch_with_selector_after(mutated)
    sel = _run_selector_with_patch(patch, *GLB019_A2B_FULL_PR_FILES)
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert sel["test_selection_reason"] in _GLB019_SELECTOR_OWNER_FULL_REASONS


def test_selector_glb019_a2b_selector_owner_reason_string_change_full() -> None:
    canonical = _selector_owner_canonical_after_text()
    needle = '"glb019_a2b_additive_change_contract"'
    assert needle in canonical
    mutated = canonical.replace(needle, '"glb019_a2b_additive_change_contract_mutated"', 1)
    assert mutated != canonical
    patch = _guarded_mixed_patch_with_selector_after(mutated)
    sel = _run_selector_with_patch(patch, *GLB019_A2B_FULL_PR_FILES)
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert sel["test_selection_reason"] in _GLB019_SELECTOR_OWNER_FULL_REASONS


def test_selector_glb019_a2b_selector_owner_extra_ast_statement_full() -> None:
    canonical = _selector_owner_canonical_after_text()
    needle = "    if path == CI_GLB019_SYNTHETIC_PATCH_BUILDER:\n        return True"
    assert needle in canonical
    mutated = canonical.replace(
        needle,
        needle + '\n    if path == "evil_probe_path":\n        return True',
        1,
    )
    patch = _guarded_mixed_patch_with_selector_after(mutated)
    sel = _run_selector_with_patch(patch, *GLB019_A2B_FULL_PR_FILES)
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert sel["test_selection_reason"] in _GLB019_SELECTOR_OWNER_FULL_REASONS


def test_selector_glb019_a2b_selector_owner_missing_canonical_import_binding_full() -> None:
    canonical = _selector_owner_canonical_after_text()
    needle = "    CI_GLB019_SYNTHETIC_PATCH_BUILDER,\n"
    assert needle in canonical
    mutated = canonical.replace(needle, "", 1)
    patch = _guarded_mixed_patch_with_selector_after(mutated)
    sel = _run_selector_with_patch(patch, *GLB019_A2B_FULL_PR_FILES)
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert sel["test_selection_reason"] in _GLB019_SELECTOR_OWNER_FULL_REASONS


def test_selector_glb019_a2b_full_pr_plus_unknown_foreign_path_full() -> None:
    patch = _synthetic_glb019_a2b_nine_file_patch_text() + (
        "\ndiff --git a/src/ops/unknown_contract_v0.py b/src/ops/unknown_contract_v0.py\n"
        "+++ b/src/ops/unknown_contract_v0.py\n"
        "@@ -0,0 +1 @@\n"
        "+pass\n"
    )
    sel = _run_selector_with_patch(
        patch,
        *GLB019_A2B_FULL_PR_FILES,
        "src/ops/unknown_contract_v0.py",
    )
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert sel["test_selection_reason"] == "durable_completion_foreign_path_requires_full"


def test_selector_glb019_a2b_full_pr_plus_second_ci_file_full() -> None:
    sel = _run_selector(
        *GLB019_A2B_FULL_PR_FILES,
        "scripts/ops/ci_unknown_bootstrap_probe_v0.py",
    )
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert sel["test_selection_reason"] in {
        "ci_bootstrap_mixed_diff_requires_full",
        "durable_completion_foreign_path_requires_full",
    }


def test_selector_glb019_a2b_allowed_files_do_not_globally_allow_selector_owner() -> None:
    from scripts.ops.durable_completion_integration_partitions_v0 import (
        GLB019_A2B_ALLOWED_FILES,
        GLB019_A2B_SELECTOR_OWNER,
    )

    assert GLB019_A2B_SELECTOR_OWNER not in GLB019_A2B_ALLOWED_FILES
    assert not any(path.endswith("/") for path in GLB019_A2B_ALLOWED_FILES)


def test_selector_glb019_a2b_selector_partitions_helper_plus_central_facade_selects_full() -> None:
    sel = _run_selector(
        _SELECTOR_OWNER,
        _PARTITIONS_HELPER,
        _FACADE_PATH,
    )
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert sel["test_selection_reason"] == "durable_completion_foreign_path_requires_full"


def test_selector_glb019_a2b_central_facade_without_structural_contract_selects_full() -> None:
    sel = _run_selector(_FACADE_PATH)
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert sel["tests_execute_pr_bounded_full"] == "true"
    assert sel["tests_execute_full"] == "false"


def test_selector_glb019_a2b_eligible_fileset_structural_contract_failure_selects_full() -> None:
    patch = _synthetic_glb019_a2b_reject_patch_text()
    sel = _run_selector_with_patch(patch, *GLB019_A2B_FILESET)
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert sel["tests_execute_pr_bounded_full"] == "true"
    assert sel["tests_execute_full"] == "false"


def test_selector_ci_bootstrap_deterministic_regardless_of_file_order() -> None:
    files_a = (
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
        "scripts/ops/ci_test_selection_v1.py",
    )
    files_b = tuple(reversed(files_a))
    sel_a = _run_selector(*files_a)
    sel_b = _run_selector(*files_b)
    assert sel_a == sel_b
    assert sel_a["test_selection_mode"] == "CONTRACT_FOCUSED"


def test_selector_ci_mapping_only_full() -> None:
    sel = _run_selector("config/ci/file_category_mapping.yaml")
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert sel["test_selection_reason"] == "ci_mapping_or_workflow_selector_change_requires_full"


def test_selector_ci_workflow_change_self_full() -> None:
    sel = _run_selector(
        ".github/workflows/ci.yml",
        "scripts/ops/ci_test_selection_v1.py",
    )
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert sel["test_selection_reason"] == "ci_bootstrap_mixed_diff_requires_full"


def test_selector_gap_ci_017_full_pr_diff_ci_infra_focused() -> None:
    sel = _run_selector(
        ".github/workflows/ci.yml",
        "scripts/ops/ci_test_selection_v1.py",
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
    )
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert sel["test_selection_reason"] == "selector_self_change_bootstrap"
    assert sel["tests_execute_pr_bounded_full"] == "true"


def test_selector_gap_ci_017_ci_workflow_timeout_rebundle_ci_infra_focused() -> None:
    sel = _run_selector(
        ".github/workflows/ci.yml",
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
    )
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert sel["test_selection_reason"] == "ci_infra_focused"
    assert sel["tests_execute_full"] == "false"
    assert sel["tests_execute_focused"] == "true"
    targets = _targets(sel)
    assert "tests/ci/test_ci_diff_aware_test_selection_v1.py" in targets
    assert "tests/ci/test_workflows_no_pull_request_target_contract_v0.py" in targets
    assert "tests/ci/test_ci_testowner_runtime_budget_reporting_contract_v0.py" in targets


def test_selector_strategy_plus_core_full() -> None:
    sel = _run_selector(
        "src/strategies/vol_breakout.py",
        "tests/test_strategies_phase27.py",
        "src/core/foo.py",
    )
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"


def test_selector_multiple_test_owners_full() -> None:
    sel = _run_selector(
        "src/strategies/vol_breakout.py",
        "tests/test_strategies_phase27.py",
        "tests/test_strategy_vol_regime_filter.py",
    )
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"


def test_selector_unknown_fail_closed_full() -> None:
    sel = _run_selector("misc/unclassified.bin")
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"


def test_selector_empty_diff_fail_closed_full() -> None:
    sel = _run_selector()
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert sel["test_selection_reason"] == "empty_diff_fail_closed"


def test_selector_force_full() -> None:
    sel = _run_selector(event_name="workflow_dispatch", force_full=True)
    assert sel["test_selection_mode"] == "EXHAUSTIVE_FULL"


def test_selector_push_event_bounded_or_no_op() -> None:
    sel = _run_selector("docs/foo.md", event_name="push")
    assert sel["test_selection_mode"] == "NO_OP"


def test_selector_merge_group_event_bounded() -> None:
    sel = _run_selector(
        "src/strategies/vol_breakout.py",
        "tests/test_strategies_phase27.py",
        event_name="merge_group",
    )
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"


def test_selector_import_smoke_cli_ok() -> None:
    out = subprocess.check_output(
        [sys.executable, str(SELECTOR), "--import-smoke-modules", "src.strategies.vol_breakout"],
        text=True,
    )
    assert "import smoke ok: src.strategies.vol_breakout" in out


def test_selector_import_smoke_cli_rejects_invalid_module() -> None:
    proc = subprocess.run(
        [sys.executable, str(SELECTOR), "--import-smoke-modules", "src;rm -rf /"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode != 0


def test_selector_emit_validated_pytest_targets_ok() -> None:
    out = subprocess.check_output(
        [
            sys.executable,
            str(SELECTOR),
            "--emit-validated-pytest-targets",
            "tests/ci/test_ci_diff_aware_test_selection_v1.py",
        ],
        text=True,
    )
    assert "tests/ci/test_ci_diff_aware_test_selection_v1.py" in out


def test_selector_emit_validated_pytest_targets_rejects_injection() -> None:
    proc = subprocess.run(
        [
            sys.executable,
            str(SELECTOR),
            "--emit-validated-pytest-targets",
            "tests/ci/foo.py; echo pwned",
        ],
        capture_output=True,
        text=True,
    )
    assert proc.returncode != 0


def test_mapping_file_exists() -> None:
    assert MAPPING.is_file()
    text = MAPPING.read_text(encoding="utf-8")
    assert "docs_only:" in text
    assert "strategy_regime_owner_focused:" in text
    assert "market_dashboard_focused:" in text


def test_selector_market_dashboard_eligibility_only_focused() -> None:
    sel = _run_selector("src/webui/market_instrument_eligibility_v0.py")
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert sel["test_selection_reason"] == "market_dashboard_focused"
    assert "tests/webui/test_market_dashboard_no_bitcoin_futures_v1.py" in _targets(sel)


def test_selector_market_dashboard_rebundle_diff_focused() -> None:
    files = (
        "src/webui/market_instrument_eligibility_v0.py",
        "src/webui/market_surface.py",
        "tests/webui/test_market_dashboard_no_bitcoin_futures_v1.py",
        "tests/test_market_surface_api.py",
        "scripts/ops/ci_test_selection_v1.py",
        "config/ci/file_category_mapping.yaml",
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
    )
    sel = _run_selector(*files)
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert sel["test_selection_reason"] == "market_dashboard_focused"
    assert "tests/ci/test_ci_diff_aware_test_selection_v1.py" in _targets(sel)
    assert sel["tests_execute_full"] == "false"


def test_selector_market_dashboard_plus_central_src_full() -> None:
    sel = _run_selector(
        "src/webui/market_surface.py",
        "src/execution/live/orchestrator.py",
    )
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"


def test_selector_market_dashboard_tests_only_focused() -> None:
    sel = _run_selector("tests/webui/test_market_dashboard_no_bitcoin_futures_v1.py")
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert sel["test_selection_reason"] == "market_dashboard_focused"


def test_workflow_only_does_not_run_full_pytest_step_unconditionally() -> None:
    text = _ci_text()
    exhaustive_step = text.split("name: Run EXHAUSTIVE_FULL test suite", 1)[1].split(
        "\n      - name:", 1
    )[0]
    assert "tests_execute_exhaustive_full == 'true'" in exhaustive_step
    assert "workflow_only == 'true'" not in exhaustive_step


PR4451_DURABLE_COMPLETION_FILES = (
    "src/ops/bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0.py",
    "src/ops/durable_completion_validation/__init__.py",
    "src/ops/durable_completion_validation/graph.py",
    "src/ops/durable_completion_validation/identity.py",
    "src/ops/durable_completion_validation/models.py",
    "src/ops/durable_completion_validation/validators/__init__.py",
    "src/ops/durable_completion_validation/validators/operator_closure.py",
    "src/ops/durable_completion_validation/validators/reconciliation.py",
    "src/ops/durable_completion_validation/validators/recovery.py",
    "src/ops/durable_completion_validation/validators/traceability.py",
    "tests/ops/test_durable_completion_validation_graph_v1.py",
)


def test_selector_pr4451_durable_completion_fileset_focused() -> None:
    sel = _run_selector(*PR4451_DURABLE_COMPLETION_FILES)
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert sel["test_selection_reason"] == "durable_completion_focused"
    targets = _targets(sel)
    assert "tests/ops/test_durable_completion_validation_graph_v1.py" in targets
    assert (
        "tests/ops/test_bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0.py"
        in targets
    )
    assert sel["tests_execute_full"] == "false"


def test_selector_durable_completion_internal_validator_only_focused() -> None:
    sel = _run_selector(
        "src/ops/durable_completion_validation/validators/reconciliation.py",
        "tests/ops/test_durable_completion_validation_graph_v1.py",
    )
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert sel["test_selection_reason"] == "durable_completion_validation_graph_focused"
    targets = _targets(sel)
    assert "tests/ops/test_durable_completion_validation_graph_v1.py" in targets
    assert "tests/ci/test_ci_diff_aware_test_selection_v1.py" in targets
    assert (
        "tests/ops/test_bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0.py"
        not in targets
    )


PE55_DURABLE_COMPLETION_FILL_REBINDING_FILES = (
    "src/ops/durable_completion_validation/validators/reconciliation.py",
    "tests/ops/test_bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0.py",
    "tests/ops/test_durable_completion_validation_graph_v1.py",
)


def test_selector_pe55_fill_rebinding_bounded_focused_targets() -> None:
    sel = _run_selector(*PE55_DURABLE_COMPLETION_FILL_REBINDING_FILES)
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert sel["test_selection_reason"] == "durable_completion_focused"
    targets = _targets(sel)
    assert any(t.startswith(f"{_GRAPH_OWNER}::") for t in targets)
    assert any(t.startswith(f"{_INTEGRATION_OWNER}::") for t in targets)
    assert _GRAPH_OWNER not in targets
    assert _INTEGRATION_OWNER not in targets
    assert sel["tests_execute_full"] == "false"
    assert sel["tests_execute_no_op"] == "false"


def test_selector_pe55_fill_rebinding_import_modules_bounded() -> None:
    sel = _run_selector(*PE55_DURABLE_COMPLETION_FILL_REBINDING_FILES)
    modules = _modules(sel)
    assert "src.ops.durable_completion_validation" in modules
    assert (
        "src.ops.bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0"
        in modules
    )


def test_fast_lane_focused_contract_check_runs_for_focused_prs() -> None:
    text = _ci_text()
    assert "Focused Fast-Lane contract check (diff-aware FOCUSED PRs)" in text
    focused_block = text.split("Focused Fast-Lane contract check", 1)[1].split(
        "Static contract tests", 1
    )[0]
    assert "tests_execute_focused == 'true'" in focused_block
    assert "focused_pytest_targets" in focused_block
    assert "tests/ci/test_ci_*contract*.py" in focused_block
    assert "OPS_SHARD_COUNT" not in focused_block


def test_fast_lane_focused_skips_matrix_targets_when_run_matrix_true() -> None:
    text = _ci_text()
    focused_block = text.split("Focused Fast-Lane contract check", 1)[1].split(
        "Static contract tests", 1
    )[0]
    assert 'run_matrix }}" = "true"' in focused_block
    matrix_branch = focused_block.split('run_matrix }}" = "true"', 1)[1].split("else", 1)[0]
    assert "VALIDATED_TARGETS" not in matrix_branch
    assert "VALIDATED_TARGETS" in focused_block


PE56_DURABLE_COMPLETION_GRAPH_WIRING_FILES = (
    "src/ops/durable_completion_validation/graph.py",
    "src/ops/durable_completion_validation/validators/reconciliation.py",
    "tests/ops/test_durable_completion_validation_graph_v1.py",
)


def test_selector_pe56_graph_wiring_rebinding_bounded_focused_targets() -> None:
    sel = _run_selector(*PE56_DURABLE_COMPLETION_GRAPH_WIRING_FILES)
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert sel["test_selection_reason"] == "durable_completion_focused"
    targets = _targets(sel)
    assert any(t.startswith(f"{_GRAPH_OWNER}::") for t in targets)
    assert any(t.startswith(f"{_INTEGRATION_OWNER}::") for t in targets)
    assert _GRAPH_OWNER not in targets
    assert _INTEGRATION_OWNER not in targets
    assert "tests/ci/test_ci_diff_aware_test_selection_v1.py" in targets


PE60_DURABLE_COMPLETION_DELEGATION_FILES = (
    "src/ops/bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0.py",
    "src/ops/durable_completion_validation/graph.py",
    "src/ops/durable_completion_validation/validators/completion_chain.py",
    "tests/ops/test_durable_completion_validation_graph_v1.py",
)


def test_selector_pe60_completion_chain_delegation_rebinding_bounded_focused_targets() -> None:
    sel = _run_selector(*PE60_DURABLE_COMPLETION_DELEGATION_FILES)
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert sel["test_selection_reason"] == "durable_completion_focused"
    targets = _targets(sel)
    assert _INTEGRATION_OWNER not in targets
    assert any(t.startswith(f"{_INTEGRATION_OWNER}::") for t in targets)
    assert "tests/ci/test_ci_diff_aware_test_selection_v1.py" in targets
    assert sel["tests_execute_full"] == "false"
    assert sel["tests_execute_no_op"] == "false"


GLB019_A1_FOUR_FILE_DIFF = (
    "src/ops/durable_completion_validation/models.py",
    "src/ops/durable_completion_validation/validators/__init__.py",
    "src/ops/durable_completion_validation/validators/event_stream.py",
    "tests/ops/test_durable_completion_validation_graph_v1.py",
)

_INTEGRATION_OWNER = "tests/ops/test_bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0.py"
_GRAPH_OWNER = "tests/ops/test_durable_completion_validation_graph_v1.py"
_CI_OWNER = "tests/ci/test_ci_diff_aware_test_selection_v1.py"


def test_selector_glb019_a1_four_file_diff_validation_graph_focused() -> None:
    sel = _run_selector(*GLB019_A1_FOUR_FILE_DIFF)
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert sel["test_selection_reason"] == "durable_completion_validation_graph_focused"
    targets = _targets(sel)
    assert _GRAPH_OWNER in targets
    assert _CI_OWNER in targets
    assert _INTEGRATION_OWNER not in targets
    assert _modules(sel) == ["src.ops.durable_completion_validation"]


def test_selector_glb019_validation_only_event_stream_validator_focused() -> None:
    sel = _run_selector(
        "src/ops/durable_completion_validation/validators/event_stream.py",
        _GRAPH_OWNER,
    )
    assert sel["test_selection_reason"] == "durable_completion_validation_graph_focused"
    assert _INTEGRATION_OWNER not in _targets(sel)


def test_selector_glb019_validation_only_models_context_field_focused() -> None:
    sel = _run_selector(
        "src/ops/durable_completion_validation/models.py",
        _GRAPH_OWNER,
    )
    assert sel["test_selection_reason"] == "durable_completion_validation_graph_focused"
    assert _INTEGRATION_OWNER not in _targets(sel)


def test_selector_glb019_completion_facade_still_selects_integration_owner() -> None:
    sel = _run_selector_with_patch(
        "",
        "src/ops/bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0.py",
        _GRAPH_OWNER,
    )
    assert sel["test_selection_reason"] == "durable_completion_focused"
    assert _INTEGRATION_OWNER in _targets(sel)


def test_selector_glb019_graph_wiring_still_selects_integration_owner() -> None:
    sel = _run_selector(
        "src/ops/durable_completion_validation/graph.py",
        "src/ops/durable_completion_validation/validators/reconciliation.py",
        _GRAPH_OWNER,
    )
    assert sel["test_selection_reason"] == "durable_completion_focused"
    targets = _targets(sel)
    assert any(t.startswith(f"{_INTEGRATION_OWNER}::") for t in targets)
    assert _INTEGRATION_OWNER not in targets


PR4553_GLB019_GRAPH_BINDING_FILES = (
    "src/ops/durable_completion_validation/graph.py",
    _GRAPH_OWNER,
)


def test_selector_pr4553_glb019_graph_binding_empty_partition_bounded_focused() -> None:
    sel = _run_selector(*PR4553_GLB019_GRAPH_BINDING_FILES)
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert sel["test_selection_reason"] == "durable_completion_focused"
    targets = _targets(sel)
    assert _GRAPH_OWNER in targets
    assert _CI_OWNER in targets
    assert _INTEGRATION_OWNER not in targets
    assert sel["tests_execute_full"] == "false"
    assert sel["fast_lane_contract_mode"] == "DURABLE_COMPLETION_BOUNDED"


def test_integration_partition_inventory_covers_all_nodes() -> None:
    from scripts.ops.durable_completion_integration_partitions_v0 import (
        ALL_PARTITIONS,
        classify_integration_node_id,
        collect_integration_owner_node_ids,
        integration_partition_inventory,
    )

    nodes = collect_integration_owner_node_ids()
    # 283 = explicit canonical inventory after 12 B2 PE31 durable-completion integration nodes.
    # Intentionally static (not derived from collect) so inventory drift fails visibly.
    assert len(nodes) == 283
    inventory = integration_partition_inventory()
    assert set(inventory) <= set(ALL_PARTITIONS)
    covered = [node for part in inventory.values() for node in part]
    assert len(covered) == len(nodes)
    assert len(set(covered)) == len(nodes)
    for node in nodes:
        assert classify_integration_node_id(node) in inventory


PR4550_CROSS_SLICE_DIFF = (
    "src/ops/bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0.py",
    "src/ops/durable_completion_validation/graph.py",
    "src/ops/durable_completion_validation/validators/__init__.py",
    "src/ops/durable_completion_validation/validators/completion_chain.py",
    "src/ops/durable_completion_validation/validators/cross_slice_coherence.py",
    "tests/ops/test_bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0.py",
    "tests/ops/test_durable_completion_validation_graph_v1.py",
)


def test_selector_pr4550_cross_slice_coherence_bounded_node_ids() -> None:
    sel = _run_selector(*PR4550_CROSS_SLICE_DIFF)
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert sel["test_selection_reason"] == "durable_completion_focused"
    assert sel["tests_execute_exhaustive_full"] == "false"
    targets = _targets(sel)
    assert _GRAPH_OWNER not in targets
    assert _CI_OWNER in targets
    assert _INTEGRATION_OWNER not in targets
    assert any(
        "::test_pe33_cross_slice_coherence_bound_in_completion_happy_path" in t for t in targets
    )
    assert any("::test_pe33_proof_digest_chain_drift_fails" in t for t in targets)
    pe33_targets = [t for t in targets if t.startswith(_INTEGRATION_OWNER + "::")]
    assert len(pe33_targets) == 5
    assert all("::test_pe33_" in t for t in pe33_targets)


def test_selector_pr4550_fast_lane_durable_completion_bounded() -> None:
    sel = _run_selector(*PR4550_CROSS_SLICE_DIFF)
    assert sel["fast_lane_contract_mode"] == "DURABLE_COMPLETION_BOUNDED"
    assert sel["fast_lane_contract_reason"] == "durable_completion_bounded_partition"
    fast_lane_targets = _fast_lane_targets(sel)
    pe33_targets = [t for t in fast_lane_targets if "::test_pe33_" in t]
    graph_targets = [t for t in fast_lane_targets if t.startswith(_GRAPH_OWNER + "::")]
    assert len(pe33_targets) == 5
    assert len(graph_targets) == 3
    assert _INTEGRATION_OWNER not in fast_lane_targets
    assert _GRAPH_OWNER not in fast_lane_targets
    assert len(fast_lane_targets) <= 10


PR4554_MASTER_V2_EVENT_STREAM_BINDING_FILES = (
    "src/ops/bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0.py",
    "src/ops/durable_completion_validation/validators/event_stream.py",
    "tests/ops/test_bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0.py",
)


def test_selector_pr4554_fast_lane_durable_completion_bounded_master_v2_event_stream() -> None:
    sel = _run_selector(*PR4554_MASTER_V2_EVENT_STREAM_BINDING_FILES)
    assert sel["fast_lane_contract_mode"] == "DURABLE_COMPLETION_BOUNDED"
    assert sel["fast_lane_contract_reason"] == "durable_completion_bounded_partition"
    fast_lane_targets = _fast_lane_targets(sel)
    graph_targets = [t for t in fast_lane_targets if t.startswith(_GRAPH_OWNER + "::")]
    master_v2_targets = [
        t
        for t in fast_lane_targets
        if "::test_master_v2_kill_all_event_stream_happy_path" in t
        or "::test_master_v2_state_switch_event_stream_happy_path_non_authorizing" in t
    ]
    assert len(graph_targets) == 3
    assert len(master_v2_targets) == 2
    assert not any(
        "::test_coherent_static_completion_happy_path_passes" in t for t in fast_lane_targets
    )
    assert _INTEGRATION_OWNER not in fast_lane_targets
    assert _GRAPH_OWNER not in fast_lane_targets
    assert len(fast_lane_targets) == 7


DURABLE_COMPLETION_EVENT_STREAM_VALIDATOR_BINDING_FILES = (
    "src/ops/bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0.py",
    "src/ops/durable_completion_validation/validators/event_stream.py",
    "tests/ops/test_bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0.py",
    "tests/ci/test_ci_diff_aware_test_selection_v1.py",
)

DURABLE_COMPLETION_MATRIX_MASTER_V2_EVENT_STREAM_BOUNDED_TARGETS = (
    f"{_INTEGRATION_OWNER}::test_master_v2_state_switch_event_stream_happy_path_non_authorizing",
    f"{_INTEGRATION_OWNER}::test_master_v2_kill_all_event_stream_happy_path",
    f"{_INTEGRATION_OWNER}::test_master_v2_missing_required_event_fail_closed",
    f"{_INTEGRATION_OWNER}::test_master_v2_kill_all_terminal_break_fail_closed",
    f"{_INTEGRATION_OWNER}::test_completion_proof_chain_pe38_digest_bound_positive",
    f"{_INTEGRATION_OWNER}::test_glb019_missing_proof_fail_closed",
    f"{_GRAPH_OWNER}::test_graph_explicit_order_matches_dependencies",
    "tests/ci/test_ci_diff_aware_test_selection_v1.py::test_selector_pr4554_fast_lane_durable_completion_bounded_master_v2_event_stream",
)


def test_selector_durable_completion_event_stream_validator_focused_matrix_eight_node_bounded() -> (
    None
):
    # Empty patch isolates bounded-matrix contract from live branch GLB019 auto-patch drift.
    sel = _run_selector_with_patch("", *DURABLE_COMPLETION_EVENT_STREAM_VALIDATOR_BINDING_FILES)
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert sel["test_selection_reason"] == "durable_completion_focused"
    targets = _targets(sel)
    assert targets == sorted(DURABLE_COMPLETION_MATRIX_MASTER_V2_EVENT_STREAM_BOUNDED_TARGETS)
    assert _INTEGRATION_OWNER not in targets
    assert _GRAPH_OWNER not in targets
    assert "tests/ci/test_ci_diff_aware_test_selection_v1.py" not in targets
    assert not any("::test_coherent_static_completion_happy_path_passes" in t for t in targets)
    assert not any("::test_global_safety_flags_remain_blocked" in t for t in targets)
    assert not any("::test_master_v2_dynamic_scope_digest_drift_fail_closed" in t for t in targets)


def test_selector_pr4550_matrix_contract_focused_not_exhaustive() -> None:
    sel = _run_selector(*PR4550_CROSS_SLICE_DIFF)
    assert sel["tests_execute_exhaustive_full"] == "false"
    assert sel["tests_execute_pr_bounded_full"] == "false"
    assert sel["tests_execute_contract_focused"] == "true"
    targets = _targets(sel)
    assert _INTEGRATION_OWNER not in targets
    assert sum(1 for t in targets if "::test_pe33_" in t) == 5


def test_selector_pe33_nodes_classified_in_inventory() -> None:
    from scripts.ops.durable_completion_integration_partitions_v0 import (
        PE33_PR_SMOKE_NODE_IDS,
        classify_integration_node_id,
        integration_partition_inventory,
    )

    inventory = integration_partition_inventory()
    for node in PE33_PR_SMOKE_NODE_IDS:
        assert classify_integration_node_id(node) == "pe33_pr_smoke"
        assert node in inventory["pe33_pr_smoke"]
    assert (
        classify_integration_node_id("test_pe33_invalid_proof_lifecycle_states_fail[stale]")
        == "pe33_cross_slice_exhaustive"
    )


B2_PE31_DURABLE_COMPLETION_BINDING_TEST_ONLY_DUAL_OWNER_FILES = (
    _INTEGRATION_OWNER,
    _GRAPH_OWNER,
)

B2_PE31_DURABLE_COMPLETION_BINDING_INTEGRATION_NODE_IDS = (
    "test_pe31_durable_completion_binding_package_marker_present",
    "test_pe31_durable_completion_canonical_binding_registry_complete",
    "test_pe31_durable_completion_registry_upstream_owner_matches_pe31_contract",
    "test_pe31_durable_completion_dependency_direction_is_downstream_only",
    "test_pe31_durable_completion_sole_canonical_upstream_module_in_completion_facade",
    "test_pe31_durable_completion_graph_validator_imports_canonical_pe31_owner_only",
    "test_pe31_durable_completion_binding_authority_neutral_on_happy_path",
    "test_pe31_source_revision_mismatch_with_completion_input_fails",
    "test_pe31_integration_input_digest_drift_fails",
    "test_pe31_integration_owner_mismatch_fails",
    "test_pe31_referenced_pe21_digest_drift_in_completion_chain_fails",
    "test_pe31_completion_binding_source_revision_consistent_on_happy_path",
)

B2_PE31_DURABLE_COMPLETION_BINDING_GRAPH_NODE_IDS = (
    "test_graph_pe31_canonical_binding_registry_aligns_with_integration_owner",
    "test_graph_reconciliation_validator_imports_canonical_pe31_owner_only",
    "test_graph_reconciliation_validator_is_canonical_pe31_binding_entrypoint",
    "test_graph_pe31_binding_authority_neutral_on_happy_path",
    "test_graph_pe31_source_revision_drift_fail_closed_via_reconciliation_validator",
    "test_graph_pe31_integration_input_digest_drift_fail_closed",
    "test_graph_pe31_referenced_pe21_digest_drift_in_completion_chain_fail_closed",
    "test_graph_pe31_completion_chain_digest_alignment_fail_closed",
)

B2_PE31_TARGET_COMBINED_UNIQUE_NODE_COUNT = 22
B2_PE31_B2_MANIFEST_NODE_COUNT = 20
B2_PE31_CI_META_NODE_COUNT = 2


def _node_targets(targets: list[str]) -> list[str]:
    return sorted(t for t in targets if "::" in t)


def test_selector_b2_pe31_durable_completion_binding_test_only_dual_owner_bounded() -> None:
    from scripts.ops.ci_test_selection_v1 import (
        DURABLE_COMPLETION_FAST_LANE_GRAPH_STRUCTURE_NODE_IDS,
        DURABLE_COMPLETION_FAST_LANE_SELECTOR_ANCHOR_NODE_IDS,
    )
    from scripts.ops.durable_completion_integration_partitions_v0 import (
        CORE_ALWAYS_PARTITIONS,
        expand_partitions_to_pytest_targets,
        partitions_for_changed_files,
    )

    sel = _run_selector(*B2_PE31_DURABLE_COMPLETION_BINDING_TEST_ONLY_DUAL_OWNER_FILES)
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert sel["test_selection_reason"] == "durable_completion_focused"
    assert sel["tests_execute_full"] == "false"
    assert sel["fast_lane_contract_mode"] == "DURABLE_COMPLETION_BOUNDED"
    partition_selection = partitions_for_changed_files(
        list(B2_PE31_DURABLE_COMPLETION_BINDING_TEST_ONLY_DUAL_OWNER_FILES)
    )
    assert partition_selection is not None
    assert "pe31_durable_completion_binding" in partition_selection
    targets = _targets(sel)
    assert _INTEGRATION_OWNER not in targets
    assert _GRAPH_OWNER not in targets
    assert "tests/ci/test_ci_diff_aware_test_selection_v1.py" in targets
    node_targets = _node_targets(targets)
    assert len(node_targets) == B2_PE31_TARGET_COMBINED_UNIQUE_NODE_COUNT
    integration_nodes = [t for t in node_targets if t.startswith(f"{_INTEGRATION_OWNER}::")]
    graph_nodes = [t for t in node_targets if t.startswith(f"{_GRAPH_OWNER}::")]
    assert len(integration_nodes) == len(B2_PE31_DURABLE_COMPLETION_BINDING_INTEGRATION_NODE_IDS)
    assert len(graph_nodes) == len(B2_PE31_DURABLE_COMPLETION_BINDING_GRAPH_NODE_IDS)
    assert len(integration_nodes) + len(graph_nodes) == B2_PE31_B2_MANIFEST_NODE_COUNT
    for node_id in B2_PE31_DURABLE_COMPLETION_BINDING_INTEGRATION_NODE_IDS:
        assert f"{_INTEGRATION_OWNER}::{node_id}" in node_targets
    for node_id in B2_PE31_DURABLE_COMPLETION_BINDING_GRAPH_NODE_IDS:
        assert f"{_GRAPH_OWNER}::{node_id}" in node_targets
    legacy_nodes = set(expand_partitions_to_pytest_targets(frozenset(CORE_ALWAYS_PARTITIONS)))
    assert not legacy_nodes.intersection(node_targets)
    assert not set(DURABLE_COMPLETION_FAST_LANE_GRAPH_STRUCTURE_NODE_IDS).intersection(node_targets)
    selector_anchor_nodes = set(DURABLE_COMPLETION_FAST_LANE_SELECTOR_ANCHOR_NODE_IDS)
    assert selector_anchor_nodes.issubset(node_targets)
    assert len(selector_anchor_nodes) == B2_PE31_CI_META_NODE_COUNT


def test_selector_b2_pe31_prod_scoped_durable_completion_preserves_legacy_core_always_coverage() -> (
    None
):
    from scripts.ops.durable_completion_integration_partitions_v0 import (
        CORE_ALWAYS_PARTITIONS,
        expand_partitions_to_pytest_targets,
    )

    sel = _run_selector(*PE55_DURABLE_COMPLETION_FILL_REBINDING_FILES)
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert sel["test_selection_reason"] == "durable_completion_focused"
    targets = set(_node_targets(_targets(sel)))
    legacy_nodes = set(expand_partitions_to_pytest_targets(frozenset(CORE_ALWAYS_PARTITIONS)))
    assert legacy_nodes.intersection(targets)


def test_selector_b2_pe31_prod_graph_facade_preserves_graph_structure_coverage() -> None:
    from scripts.ops.ci_test_selection_v1 import (
        DURABLE_COMPLETION_FAST_LANE_GRAPH_STRUCTURE_NODE_IDS,
    )

    sel = _run_selector(*PE56_DURABLE_COMPLETION_GRAPH_WIRING_FILES)
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert sel["test_selection_reason"] == "durable_completion_focused"
    targets = set(_node_targets(_targets(sel)))
    graph_structure_nodes = set(DURABLE_COMPLETION_FAST_LANE_GRAPH_STRUCTURE_NODE_IDS)
    assert graph_structure_nodes.issubset(targets)


def test_selector_b2_pe31_ci_hard_timeout_unchanged() -> None:
    text = _ci_text()
    tests_block = text.split("  tests:", 1)[1].split("  strategy-smoke:", 1)[0]
    assert "timeout-minutes: 25" in tests_block
    assert "timeout-minutes: 30" not in tests_block
    assert "timeout-minutes: 40" not in tests_block
    required_checks = Path("config/ci/required_status_checks.json").read_text(encoding="utf-8")
    assert '"tests (3.11)"' in required_checks
    assert '"strategy-smoke"' in required_checks


def test_fast_lane_b2_pe31_durable_completion_binding_bounded() -> None:
    sel = _run_selector(*B2_PE31_DURABLE_COMPLETION_BINDING_TEST_ONLY_DUAL_OWNER_FILES)
    assert sel["fast_lane_contract_mode"] == "DURABLE_COMPLETION_BOUNDED"
    assert sel["fast_lane_contract_reason"] == "durable_completion_bounded_partition"
    fast_lane_targets = _fast_lane_targets(sel)
    assert _INTEGRATION_OWNER not in fast_lane_targets
    assert _GRAPH_OWNER not in fast_lane_targets
    for node_id in B2_PE31_DURABLE_COMPLETION_BINDING_INTEGRATION_NODE_IDS:
        assert f"{_INTEGRATION_OWNER}::{node_id}" in fast_lane_targets
    for node_id in B2_PE31_DURABLE_COMPLETION_BINDING_GRAPH_NODE_IDS:
        assert f"{_GRAPH_OWNER}::{node_id}" in fast_lane_targets
    assert len(fast_lane_targets) <= 30


def test_selector_b2_file1_alone_stays_pr_bounded_full() -> None:
    sel = _run_selector(_INTEGRATION_OWNER)
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert sel["test_selection_reason"] == "durable_completion_incomplete_or_missing_test_owner"
    assert sel["fast_lane_contract_mode"] == "FULL_STATIC_CONTRACTS"


def test_selector_b2_file2_alone_stays_graph_focused() -> None:
    sel = _run_selector(_GRAPH_OWNER)
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert sel["test_selection_reason"] == "durable_completion_validation_graph_focused"
    assert sel["fast_lane_contract_mode"] == "DURABLE_COMPLETION_BOUNDED"


def test_selector_b2_unknown_dual_owner_combination_stays_fail_closed() -> None:
    sel = _run_selector(
        _INTEGRATION_OWNER,
        "tests/ops/test_bounded_futures_testnet_risk_killswitch_lifecycle_integration_contract_v0.py",
    )
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert sel["test_selection_reason"] == "durable_completion_foreign_path_requires_full"


def test_selector_pe31_durable_completion_binding_nodes_classified_in_manifest() -> None:
    from scripts.ops.durable_completion_integration_partitions_v0 import (
        PE31_DURABLE_COMPLETION_BINDING_INTEGRATION_NODE_IDS,
        classify_integration_node_id,
    )

    for node in PE31_DURABLE_COMPLETION_BINDING_INTEGRATION_NODE_IDS:
        assert classify_integration_node_id(node) == "pe31_durable_completion_binding"
    assert classify_integration_node_id("test_pe31_proof_mismatch_fails") == "pe31_review"


def test_selector_pe21_prod_owner_partitioned_integration_nodes() -> None:
    sel = _run_selector(
        "src/ops/bounded_futures_testnet_position_order_reconciliation_primary_evidence_integration_contract_v0.py",
        _GRAPH_OWNER,
    )
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert sel["test_selection_reason"] == "durable_completion_focused"
    targets = _targets(sel)
    assert any(t.startswith(f"{_GRAPH_OWNER}::") for t in targets)
    assert _GRAPH_OWNER not in targets
    assert _INTEGRATION_OWNER not in targets
    assert any(t.startswith(f"{_INTEGRATION_OWNER}::test_pe21") for t in targets)
    assert any("test_reconciliation_result_" in t for t in targets)


def test_selector_wallclock_prod_owner_partitioned() -> None:
    sel = _run_selector(
        "src/ops/testnet_wallclock_duration_evidence_contract_v0.py",
        _GRAPH_OWNER,
    )
    targets = _targets(sel)
    assert _INTEGRATION_OWNER not in targets
    assert any("wallclock" in t for t in targets)


def test_selector_glb019_a2b_probe_partition_union_bounded() -> None:
    from scripts.ops.durable_completion_integration_partitions_v0 import (
        estimate_partition_seconds,
        partitions_for_changed_files,
    )

    files = [
        "src/ops/durable_completion_validation/validators/event_stream.py",
        "src/ops/bounded_futures_testnet_preflight_execution_readiness_review_lifecycle_integration_contract_v0.py",
        _GRAPH_OWNER,
    ]
    partitions = partitions_for_changed_files(files)
    assert partitions is not None
    assert "pe38_readiness" in partitions
    assert estimate_partition_seconds(partitions) <= 840
    sel = _run_selector(*files)
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert _INTEGRATION_OWNER not in _targets(sel)


def test_selector_completion_facade_full_integration_owner() -> None:
    sel = _run_selector_with_patch(
        "",
        "src/ops/bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0.py",
        _GRAPH_OWNER,
    )
    assert _INTEGRATION_OWNER in _targets(sel)


def test_selector_glb019_mixed_validation_and_facade_selects_integration_owner() -> None:
    sel = _run_selector_with_patch(
        "",
        "src/ops/durable_completion_validation/validators/event_stream.py",
        "src/ops/bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0.py",
        _GRAPH_OWNER,
    )
    assert sel["test_selection_reason"] == "durable_completion_focused"
    targets = _targets(sel)
    assert any(t.startswith(f"{_INTEGRATION_OWNER}::") for t in targets)
    assert _INTEGRATION_OWNER not in targets


from scripts.ops.durable_completion_integration_partitions_v0 import (
    CI_GLB019_SYNTHETIC_PATCH_BUILDER,
)
from tests.ci._glb019_synthetic_patch_builder_v0 import (
    synthetic_glb019_a2b_nine_file_patch_text as _synthetic_glb019_a2b_nine_file_patch_text,
    synthetic_glb019_a2b_positive_patch_text as _synthetic_glb019_a2b_positive_patch_text,
    synthetic_glb019_a2b_reject_patch_text as _synthetic_glb019_a2b_reject_patch_text,
)

GLB019_A2B_FILESET = (
    "src/ops/bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0.py",
    "tests/ops/test_bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0.py",
    "src/ops/durable_completion_validation/graph.py",
    "src/ops/durable_completion_validation/validators/event_stream.py",
    "tests/ops/test_durable_completion_validation_graph_v1.py",
    "scripts/ops/durable_completion_integration_partitions_v0.py",
    "tests/ci/test_ci_diff_aware_test_selection_v1.py",
    CI_GLB019_SYNTHETIC_PATCH_BUILDER,
)

GLB019_A2B_FULL_PR_FILES = (_SELECTOR_OWNER, *GLB019_A2B_FILESET)


def _unified_patch_for_path(path: str, before: str, after: str) -> str:
    import difflib

    if before == after:
        return ""
    diff_lines = list(
        difflib.unified_diff(
            before.splitlines(keepends=True),
            after.splitlines(keepends=True),
            fromfile=f"a/{path}",
            tofile=f"b/{path}",
            n=3,
        )
    )
    if not diff_lines:
        return ""
    return f"diff --git a/{path} b/{path}\n" + "".join(diff_lines)


def _selector_owner_canonical_before_text() -> str:
    return _glb019_canonical_baseline(Path("."), _SELECTOR_OWNER)


def _selector_owner_canonical_after_text() -> str:
    from scripts.ops.durable_completion_integration_partitions_v0 import (
        _apply_unified_hunks,
        _parse_unified_diff,
    )

    patch = _synthetic_glb019_a2b_nine_file_patch_text()
    before = _selector_owner_canonical_before_text()
    return _apply_unified_hunks(before, _parse_unified_diff(patch)[_SELECTOR_OWNER])


def _guarded_mixed_patch_with_selector_after(mutated_after: str) -> str:
    before = _selector_owner_canonical_before_text()
    canonical_after = _selector_owner_canonical_after_text()
    assert canonical_after != before
    assert mutated_after != canonical_after
    selector_patch = _unified_patch_for_path(_SELECTOR_OWNER, before, mutated_after)
    assert selector_patch.strip(), "selector unified diff must not be empty"
    return _synthetic_glb019_a2b_positive_patch_text() + "\n" + selector_patch


def test_glb019_a2b_allowed_files_includes_synthetic_patch_builder() -> None:
    from scripts.ops.durable_completion_integration_partitions_v0 import (
        CI_GLB019_SYNTHETIC_PATCH_BUILDER,
        GLB019_A2B_ALLOWED_FILES,
    )

    assert CI_GLB019_SYNTHETIC_PATCH_BUILDER in GLB019_A2B_ALLOWED_FILES


def test_glb019_a2b_synthetic_patch_builder_has_registered_ast_validator() -> None:
    from scripts.ops.durable_completion_integration_partitions_v0 import (
        CI_GLB019_SYNTHETIC_PATCH_BUILDER,
        _FILE_AST_VALIDATORS,
    )

    assert CI_GLB019_SYNTHETIC_PATCH_BUILDER in _FILE_AST_VALIDATORS


def test_glb019_a2b_synthetic_patch_builder_ast_validator_accepts_canonical_helper() -> None:
    import ast
    from pathlib import Path

    from scripts.ops.durable_completion_integration_partitions_v0 import (
        CI_GLB019_SYNTHETIC_PATCH_BUILDER,
        _FILE_AST_VALIDATORS,
    )

    helper_path = Path(CI_GLB019_SYNTHETIC_PATCH_BUILDER)
    after_tree = ast.parse(helper_path.read_text(encoding="utf-8"))
    before_tree = ast.parse("")
    assert _FILE_AST_VALIDATORS[CI_GLB019_SYNTHETIC_PATCH_BUILDER](before_tree, after_tree)


def test_glb019_a2b_synthetic_patch_builder_ast_validator_rejects_missing_delegation() -> None:
    import ast

    from scripts.ops.durable_completion_integration_partitions_v0 import (
        CI_GLB019_SYNTHETIC_PATCH_BUILDER,
        _validate_synthetic_patch_builder_ast,
    )

    invalid = ast.parse(
        "def synthetic_glb019_a2b_positive_patch_text() -> str:\n"
        "    return ''\n"
        "def synthetic_glb019_a2b_reject_patch_text() -> str:\n"
        "    return synthetic_glb019_a2b_positive_patch_text()\n"
    )
    assert not _validate_synthetic_patch_builder_ast(ast.parse(""), invalid)


def test_glb019_a2b_synthetic_patch_builder_ast_validator_rejects_fragile_string_mutation() -> None:
    import ast

    from scripts.ops.durable_completion_integration_partitions_v0 import (
        _validate_synthetic_patch_builder_ast,
    )

    fragile = ast.parse(
        "from scripts.ops.durable_completion_integration_partitions_v0 import (\n"
        "    GLB019_A2B_ALLOWED_FILES,\n"
        "    collect_glb019_a2b_patch_text,\n"
        ")\n"
        "def synthetic_glb019_a2b_positive_patch_text() -> str:\n"
        "    patch = collect_glb019_a2b_patch_text(changed_files=sorted(GLB019_A2B_ALLOWED_FILES))\n"
        "    return patch\n"
        "def synthetic_glb019_a2b_reject_patch_text() -> str:\n"
        "    return synthetic_glb019_a2b_positive_patch_text().replace('glb019', 'pe21', 1)\n"
    )
    assert not _validate_synthetic_patch_builder_ast(ast.parse(""), fragile)


def test_selector_glb019_a2b_pr_fileset_focused_additive_contract() -> None:
    from scripts.ops.durable_completion_integration_partitions_v0 import (
        CI_GLB019_SYNTHETIC_PATCH_BUILDER,
    )

    pr_files = (
        "scripts/ops/durable_completion_integration_partitions_v0.py",
        "src/ops/bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0.py",
        "src/ops/durable_completion_validation/graph.py",
        "src/ops/durable_completion_validation/validators/event_stream.py",
        CI_GLB019_SYNTHETIC_PATCH_BUILDER,
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
        "tests/ops/test_bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0.py",
        "tests/ops/test_durable_completion_validation_graph_v1.py",
    )
    sel = _run_selector_with_patch(
        _synthetic_glb019_a2b_positive_patch_text(),
        *pr_files,
    )
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert sel["test_selection_reason"] == "glb019_a2b_additive_change_contract"
    assert sel["tests_execute_full"] == "false"


def _run_selector_with_patch(
    patch_text: str,
    *files: str,
    force_full: bool = False,
    event_name: str = "pull_request",
) -> dict[str, str]:
    import scripts.ops.durable_completion_integration_partitions_v0 as partitions

    glb019_scope = patch_text.strip() and (
        "glb019" in patch_text.lower() or "event_stream" in patch_text
    )
    original_base = partitions._base_file_text
    if glb019_scope:

        def _embedded_baseline(repo_root: Path, path: str) -> str:
            from tests.ci._glb019_synthetic_patch_builder_v0 import _canonical_baseline_by_path

            baselines = _canonical_baseline_by_path()
            if path in baselines:
                return baselines[path]
            return original_base(repo_root, path)

        partitions._base_file_text = _embedded_baseline

    try:
        from scripts.ops.ci_test_selection_v1 import (
            _finalize_selection_result,
            resolve_matrix_contract_selection,
            resolve_selection,
        )

        file_list = list(files)
        matrix_contract = resolve_matrix_contract_selection(file_list)
        result = resolve_selection(
            file_list,
            force_full=force_full,
            event_name=event_name,
            patch_text=patch_text or None,
        )
        if matrix_contract.mode == "MATRIX_CONTRACT_FOCUSED":
            from scripts.ops.ci_test_selection_v1 import SelectionResult

            result = SelectionResult(
                "FOCUSED",
                matrix_contract.reason,
                matrix_contract.pytest_targets,
            )
        result = _finalize_selection_result(
            result,
            file_list,
            event_name=event_name,
            force_exhaustive=force_full and event_name in {"schedule", "workflow_dispatch"},
        )
    finally:
        partitions._base_file_text = original_base

    sel: dict[str, str] = {}
    for line in result.github_output_lines():
        key, _, value = line.partition("=")
        sel[key] = value
    matrix_lines = matrix_contract.github_output_lines()
    for line in matrix_lines:
        key, _, value = line.partition("=")
        sel[key] = value
    return sel


def test_selector_glb019_a2b_frozen_patch_additive_contract_focused() -> None:
    patch = _synthetic_glb019_a2b_positive_patch_text()
    sel = _run_selector_with_patch(patch, *GLB019_A2B_FILESET)
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert sel["test_selection_reason"] == "glb019_a2b_additive_change_contract"
    assert sel["tests_execute_full"] == "false"
    targets = _targets(sel)
    assert _GRAPH_OWNER in targets
    assert "tests/ci/test_ci_diff_aware_test_selection_v1.py" in targets
    assert _INTEGRATION_OWNER not in targets
    assert any(t.startswith(f"{_INTEGRATION_OWNER}::test_") for t in targets)


def test_selector_glb019_a2b_change_contract_unknown_file_selects_full() -> None:
    patch = _synthetic_glb019_a2b_positive_patch_text() + (
        "\ndiff --git a/src/ops/unknown_contract_v0.py b/src/ops/unknown_contract_v0.py\n"
        "+++ b/src/ops/unknown_contract_v0.py\n"
        "@@ -0,0 +1 @@\n"
        "+pass\n"
    )
    sel = _run_selector_with_patch(patch, *GLB019_A2B_FILESET, "src/ops/unknown_contract_v0.py")
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert sel["test_selection_reason"] == "durable_completion_foreign_path_requires_full"


def _parse_function_body(body: str, *, name: str = "sample_fn") -> "ast.FunctionDef":
    import ast

    indented = "\n".join(f"    {line}" for line in body.strip().splitlines())
    module = ast.parse(f"def {name}():\n{indented}\n")
    fn = module.body[0]
    assert isinstance(fn, ast.FunctionDef)
    return fn


def test_glb019_statement_diff_additive_assignment_preserves_general_statements() -> None:
    from scripts.ops.durable_completion_integration_partitions_v0 import (
        function_statements_preserved_with_allowed_glb019,
    )

    before = _parse_function_body(
        "guard_a()\nevaluate_existing_chain()\nbuild_existing_context()\n",
    )
    after = _parse_function_body(
        "guard_a()\n"
        "glb019_result = evaluate_glb019_event_stream_validation(integration_input)\n"
        "evaluate_existing_chain()\n"
        "build_existing_context()\n",
    )
    assert function_statements_preserved_with_allowed_glb019(before, after)


def test_glb019_statement_diff_central_deletion_selects_full() -> None:
    from scripts.ops.durable_completion_integration_partitions_v0 import (
        function_statements_preserved_with_allowed_glb019,
    )

    before = _parse_function_body(
        "guard_a()\nevaluate_existing_chain()\nbuild_existing_context()\n",
    )
    after = _parse_function_body(
        "glb019_result = evaluate_glb019_event_stream_validation(integration_input)\n"
        "evaluate_existing_chain()\n"
        "build_existing_context()\n",
    )
    assert not function_statements_preserved_with_allowed_glb019(before, after)


def test_glb019_statement_diff_reorder_selects_full() -> None:
    from scripts.ops.durable_completion_integration_partitions_v0 import (
        function_statements_preserved_with_allowed_glb019,
    )

    before = _parse_function_body(
        "guard_a()\nfirst_existing()\nsecond_existing()\n",
    )
    after = _parse_function_body(
        "guard_a()\n"
        "glb019_result = evaluate_glb019_event_stream_validation(integration_input)\n"
        "second_existing()\n"
        "first_existing()\n",
    )
    assert not function_statements_preserved_with_allowed_glb019(before, after)


def test_glb019_statement_diff_call_argument_mutation_selects_full() -> None:
    from scripts.ops.durable_completion_integration_partitions_v0 import (
        function_statements_preserved_with_allowed_glb019,
    )

    before = _parse_function_body(
        "guard_a()\nevaluate_existing_chain(mode='baseline')\n",
    )
    after = _parse_function_body(
        "guard_a()\n"
        "glb019_result = evaluate_glb019_event_stream_validation(integration_input)\n"
        "evaluate_existing_chain(mode='mutated')\n",
    )
    assert not function_statements_preserved_with_allowed_glb019(before, after)


def test_glb019_statement_diff_validation_context_only_glb019_keyword_allowed() -> None:
    from scripts.ops.durable_completion_integration_partitions_v0 import (
        function_statements_preserved_with_allowed_glb019,
    )

    before = _parse_function_body(
        "context = ValidationContext(integration_input=integration_input)\nreturn context\n",
    )
    after = _parse_function_body(
        "glb019_result = evaluate_glb019_event_stream_validation(integration_input)\n"
        "context = ValidationContext(\n"
        "    integration_input=integration_input,\n"
        "    glb019_result=glb019_result,\n"
        ")\n"
        "return context\n",
    )
    assert function_statements_preserved_with_allowed_glb019(before, after)


def test_glb019_statement_diff_validation_context_keyword_mutation_selects_full() -> None:
    from scripts.ops.durable_completion_integration_partitions_v0 import (
        function_statements_preserved_with_allowed_glb019,
    )

    before = _parse_function_body(
        "context = ValidationContext(integration_input=integration_input)\nreturn context\n",
    )
    after = _parse_function_body(
        "glb019_result = evaluate_glb019_event_stream_validation(integration_input)\n"
        "context = ValidationContext(\n"
        "    integration_input=mutated_input,\n"
        "    glb019_result=glb019_result,\n"
        ")\n"
        "return context\n",
    )
    assert not function_statements_preserved_with_allowed_glb019(before, after)


def test_selector_glb019_a2b_change_contract_unparseable_patch_selects_full() -> None:
    sel = _run_selector_with_patch("not a unified diff", *GLB019_A2B_FILESET)
    assert _INTEGRATION_OWNER in _targets(sel)


def test_selector_glb019_a2b_change_contract_classify_unit() -> None:
    from scripts.ops.durable_completion_integration_partitions_v0 import (
        GLB019_A2B_ADDITIVE_PARTITIONS,
        classify_glb019_a2b_additive_patch,
    )

    patch = _synthetic_glb019_a2b_positive_patch_text()
    assert classify_glb019_a2b_additive_patch(patch) == GLB019_A2B_ADDITIVE_PARTITIONS
    assert classify_glb019_a2b_additive_patch("") is None
    assert classify_glb019_a2b_additive_patch("corrupt") is None


def test_collect_glb019_a2b_patch_text_uses_three_line_unified_context() -> None:
    from scripts.ops import durable_completion_integration_partitions_v0 as partitions

    source = Path(partitions.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    fn_node = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "collect_glb019_a2b_patch_text"
    )
    fn_source = ast.get_source_segment(source, fn_node) or ""
    assert fn_source
    assert '"--unified=3"' in fn_source or "'--unified=3'" in fn_source
    assert "--unified=0" not in fn_source
    assert "merge-base" in fn_source
    assert "...HEAD" in fn_source


def test_collect_glb019_a2b_patch_text_produces_parseable_additive_contract(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from scripts.ops.durable_completion_integration_partitions_v0 import (
        Glb019A2bChangeContractOutcome,
        collect_glb019_a2b_patch_text,
        evaluate_glb019_a2b_change_contract,
        expand_partitions_to_pytest_targets,
    )
    from scripts.ops.ci_test_selection_v1 import resolve_selection

    patch = _synthetic_glb019_a2b_positive_patch_text()
    git_calls: list[list[str]] = []

    def _fake_run(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        git_calls.append(cmd)
        if cmd[:2] == ["git", "merge-base"]:
            return subprocess.CompletedProcess(cmd, 0, "abc123def\n", "")
        if cmd[:2] == ["git", "diff"]:
            return subprocess.CompletedProcess(cmd, 0, patch, "")
        return subprocess.CompletedProcess(cmd, 1, "", "")

    with monkeypatch.context() as scoped:
        scoped.setattr(
            "scripts.ops.durable_completion_integration_partitions_v0.subprocess.run",
            _fake_run,
        )
        collected = collect_glb019_a2b_patch_text(
            changed_files=list(GLB019_A2B_FILESET),
            repo_root=Path("."),
        )

    assert collected
    assert collected == patch
    diff_cmd = next(cmd for cmd in git_calls if cmd[:2] == ["git", "diff"])
    assert "--unified=3" in diff_cmd
    assert "--unified=0" not in diff_cmd
    assert "abc123def...HEAD" in diff_cmd

    contract = evaluate_glb019_a2b_change_contract(collected, repo_root=Path("."))
    assert contract.outcome == Glb019A2bChangeContractOutcome.PASS
    assert contract.partitions is not None

    sel = resolve_selection(
        list(GLB019_A2B_FILESET),
        event_name="pull_request",
        patch_text=collected,
    )
    targets = _targets(
        {
            "focused_pytest_targets": " ".join(sel.focused_pytest_targets),
            "test_selection_mode": sel.mode,
            "test_selection_reason": sel.reason,
        }
    )
    integration_nodes = [t for t in targets if t.startswith(f"{_INTEGRATION_OWNER}::")]
    expected_nodes = expand_partitions_to_pytest_targets(contract.partitions)
    assert sel.mode == "FOCUSED"
    assert sel.reason == "glb019_a2b_additive_change_contract"
    assert _GRAPH_OWNER in targets
    assert "tests/ci/test_ci_diff_aware_test_selection_v1.py" in targets
    assert _INTEGRATION_OWNER not in targets
    assert integration_nodes
    assert all("::" in node for node in integration_nodes)
    assert set(integration_nodes) == set(expected_nodes)


PR4512_MASTER_V2_BINDING_CONTRACT_FILES = (
    "src/ops/bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0.py",
    "src/ops/durable_completion_validation/validators/completion_chain.py",
    "tests/ops/test_durable_completion_validation_graph_v1.py",
    "tests/ops/test_master_v2_decision_digest_completion_chain_binding_contract_v0.py",
)

_MASTER_V2_BINDING_OWNER = (
    "tests/ops/test_master_v2_decision_digest_completion_chain_binding_contract_v0.py"
)
_COMPLETION_OWNER = _INTEGRATION_OWNER


def test_selector_pr4512_master_v2_binding_contract_four_file_diff_focused() -> None:
    sel = _run_selector(*PR4512_MASTER_V2_BINDING_CONTRACT_FILES)
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert sel["test_selection_reason"] == "durable_completion_master_v2_binding_contract_focused"
    assert sel["tests_execute_full"] == "false"
    assert sel["tests_execute_focused"] == "true"
    assert sel["tests_execute_no_op"] == "false"
    targets = _targets(sel)
    assert all("::test_" in target for target in targets)
    assert _COMPLETION_OWNER not in targets
    assert _MASTER_V2_BINDING_OWNER not in targets
    assert _GRAPH_OWNER not in targets
    assert f"{_MASTER_V2_BINDING_OWNER}::test_six_node_validation_graph_unchanged" in targets
    assert f"{_GRAPH_OWNER}::test_graph_completion_chain_validator_composes_binding" in targets
    assert len(targets) >= 16
    modules = _modules(sel)
    assert (
        "src.ops.bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0"
        in modules
    )
    assert "src.ops.durable_completion_validation" in modules


def test_selector_master_v2_binding_contract_test_plus_production_owners_focused() -> None:
    sel = _run_selector(
        "src/ops/bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0.py",
        "src/ops/durable_completion_validation/validators/completion_chain.py",
        _MASTER_V2_BINDING_OWNER,
    )
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert sel["test_selection_reason"] == "durable_completion_master_v2_binding_contract_focused"
    assert any("::test_" in target for target in _targets(sel))


def test_selector_master_v2_binding_unknown_validator_escalates_full() -> None:
    sel = _run_selector(
        *PR4512_MASTER_V2_BINDING_CONTRACT_FILES,
        "src/ops/durable_completion_validation/validators/reconciliation.py",
    )
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert sel["test_selection_reason"] == "durable_completion_foreign_path_requires_full"


def test_selector_master_v2_binding_other_validator_only_escalates_full() -> None:
    sel = _run_selector(
        "src/ops/bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0.py",
        "src/ops/durable_completion_validation/validators/recovery.py",
        "tests/ops/test_durable_completion_validation_graph_v1.py",
        _MASTER_V2_BINDING_OWNER,
    )
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert sel["test_selection_reason"] == "durable_completion_foreign_path_requires_full"


def test_selector_master_v2_binding_missing_contract_test_owner_escalates_full() -> None:
    sel = _run_selector(
        "src/ops/bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0.py",
        "src/ops/durable_completion_validation/validators/completion_chain.py",
        "tests/ops/test_durable_completion_validation_graph_v1.py",
    )
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert sel["test_selection_reason"] == "durable_completion_focused"


def test_selector_master_v2_binding_selector_self_change_escalates_full() -> None:
    sel = _run_selector(
        *PR4512_MASTER_V2_BINDING_CONTRACT_FILES,
        "scripts/ops/ci_test_selection_v1.py",
    )
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert sel["test_selection_reason"] == "durable_completion_foreign_path_requires_full"


def test_selector_master_v2_binding_dependency_change_escalates_full() -> None:
    sel = _run_selector(*PR4512_MASTER_V2_BINDING_CONTRACT_FILES, "requirements.txt")
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert sel["test_selection_reason"] in {
        "category_dependencies_requires_full",
        "durable_completion_foreign_path_requires_full",
    }


def test_selector_master_v2_binding_execution_logic_escalates_full() -> None:
    sel = _run_selector(
        *PR4512_MASTER_V2_BINDING_CONTRACT_FILES,
        "src/ops/bounded_futures_testnet_risk_killswitch_lifecycle_integration_contract_v0.py",
    )
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert sel["test_selection_reason"] == "durable_completion_foreign_path_requires_full"


def test_selector_master_v2_binding_heterogeneous_foreign_src_escalates_full() -> None:
    sel = _run_selector(
        *PR4512_MASTER_V2_BINDING_CONTRACT_FILES,
        "src/ops/durable_completion_validation/graph.py",
    )
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert sel["test_selection_reason"] == "durable_completion_foreign_path_requires_full"


OFFLINE_MASTER_V2_DOUBLE_PLAY_SCENARIO_REPLAY_FILES = (
    "src/trading/master_v2/offline_double_play_scenario_replay_v0.py",
    "tests/trading/master_v2/test_offline_master_v2_double_play_scenario_replay_binding_contract_v0.py",
    "tests/ops/test_offline_master_v2_double_play_scenario_replay_completion_binding_contract_v0.py",
    "scripts/ops/ci_test_selection_v1.py",
    "tests/ci/test_ci_diff_aware_test_selection_v1.py",
)


def test_selector_offline_master_v2_double_play_scenario_replay_five_file_diff_focused() -> None:
    sel = _run_selector(*OFFLINE_MASTER_V2_DOUBLE_PLAY_SCENARIO_REPLAY_FILES)
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert sel["test_selection_reason"] == "offline_master_v2_double_play_scenario_replay_focused"
    assert sel["tests_execute_full"] == "false"
    assert sel["tests_execute_focused"] == "true"
    targets = _targets(sel)
    assert (
        "tests/trading/master_v2/test_offline_master_v2_double_play_scenario_replay_binding_contract_v0.py"
        in targets
    )
    assert (
        "tests/ops/test_offline_master_v2_double_play_scenario_replay_completion_binding_contract_v0.py"
        in targets
    )
    assert "tests/ci/test_ci_diff_aware_test_selection_v1.py" in targets


def test_selector_offline_master_v2_double_play_foreign_path_escalates_full() -> None:
    sel = _run_selector(
        *OFFLINE_MASTER_V2_DOUBLE_PLAY_SCENARIO_REPLAY_FILES,
        "src/trading/master_v2/double_play_state.py",
    )
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert sel["test_selection_reason"].endswith("requires_full")


MASTER_V2_REPLAY_DISPLAY_PROJECTION_DIGEST_COMPLETION_EVIDENCE_FILES = (
    "src/ops/bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0.py",
    "src/trading/master_v2/offline_double_play_scenario_replay_v0.py",
    "tests/ops/test_master_v2_decision_digest_completion_chain_binding_contract_v0.py",
    "tests/trading/master_v2/test_offline_master_v2_double_play_scenario_replay_binding_contract_v0.py",
    "tests/ops/test_offline_master_v2_double_play_scenario_replay_completion_binding_contract_v0.py",
)


def test_selector_master_v2_replay_display_projection_digest_completion_evidence_five_file_diff_focused() -> (
    None
):
    sel = _run_selector(*MASTER_V2_REPLAY_DISPLAY_PROJECTION_DIGEST_COMPLETION_EVIDENCE_FILES)
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert (
        sel["test_selection_reason"]
        == "master_v2_replay_display_projection_digest_completion_evidence_focused"
    )
    assert sel["tests_execute_full"] == "false"
    assert sel["tests_execute_focused"] == "true"
    targets = _targets(sel)
    assert (
        "tests/ops/test_master_v2_decision_digest_completion_chain_binding_contract_v0.py"
        in targets
    )
    assert (
        "tests/trading/master_v2/test_offline_master_v2_double_play_scenario_replay_binding_contract_v0.py"
        in targets
    )
    assert (
        "tests/ops/test_offline_master_v2_double_play_scenario_replay_completion_binding_contract_v0.py"
        in targets
    )
    assert "tests/ci/test_ci_diff_aware_test_selection_v1.py" not in targets


def test_selector_master_v2_replay_display_projection_digest_completion_evidence_with_ci_policy_focused() -> (
    None
):
    sel = _run_selector(
        *MASTER_V2_REPLAY_DISPLAY_PROJECTION_DIGEST_COMPLETION_EVIDENCE_FILES,
        "scripts/ops/ci_test_selection_v1.py",
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
    )
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert (
        sel["test_selection_reason"]
        == "master_v2_replay_display_projection_digest_completion_evidence_focused"
    )
    targets = _targets(sel)
    assert (
        "tests/ci/test_ci_diff_aware_test_selection_v1.py::test_selector_master_v2_replay_display_projection_digest_completion_evidence_five_file_diff_focused"
        in targets
    )
    assert (
        "tests/ci/test_ci_diff_aware_test_selection_v1.py::test_selector_master_v2_replay_display_projection_digest_completion_evidence_with_ci_policy_focused"
        in targets
    )
    assert (
        "tests/ci/test_ci_diff_aware_test_selection_v1.py::test_selector_master_v2_replay_display_projection_digest_completion_evidence_foreign_path_escalates_full"
        in targets
    )
    assert "tests/ci/test_ci_diff_aware_test_selection_v1.py" not in targets


def test_selector_master_v2_replay_display_projection_digest_completion_evidence_foreign_path_escalates_full() -> (
    None
):
    sel = _run_selector(
        *MASTER_V2_REPLAY_DISPLAY_PROJECTION_DIGEST_COMPLETION_EVIDENCE_FILES,
        "src/trading/master_v2/double_play_state.py",
    )
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert sel["test_selection_reason"].endswith("requires_full")


OFFLINE_MASTER_V2_REPLAY_SIX_NODE_VALIDATION_GRAPH_BINDING_FILES = (
    "src/ops/offline_master_v2_replay_six_node_validation_graph_binding_v0.py",
    "tests/ops/test_offline_master_v2_double_play_scenario_replay_completion_binding_contract_v0.py",
    "scripts/ops/ci_test_selection_v1.py",
    "tests/ci/test_ci_diff_aware_test_selection_v1.py",
)


def test_selector_offline_master_v2_replay_six_node_validation_graph_binding_four_file_diff_focused() -> (
    None
):
    sel = _run_selector(*OFFLINE_MASTER_V2_REPLAY_SIX_NODE_VALIDATION_GRAPH_BINDING_FILES)
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert (
        sel["test_selection_reason"]
        == "offline_master_v2_replay_six_node_validation_graph_binding_focused"
    )
    assert sel["tests_execute_full"] == "false"
    assert sel["tests_execute_focused"] == "true"
    targets = _targets(sel)
    assert (
        "tests/ops/test_offline_master_v2_double_play_scenario_replay_completion_binding_contract_v0.py"
        in targets
    )
    assert (
        "tests/trading/master_v2/test_offline_master_v2_double_play_scenario_replay_binding_contract_v0.py"
        in targets
    )
    assert "tests/ci/test_ci_diff_aware_test_selection_v1.py" in targets


def test_selector_offline_master_v2_replay_six_node_graph_binding_foreign_path_escalates_full() -> (
    None
):
    sel = _run_selector(
        *OFFLINE_MASTER_V2_REPLAY_SIX_NODE_VALIDATION_GRAPH_BINDING_FILES,
        "src/trading/master_v2/double_play_state.py",
    )
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert sel["test_selection_reason"].endswith("requires_full")


BOUNDED_MASTER_V2_TESTNET_COMPLETION_PATH_WIRING_FILES = (
    "src/ops/bounded_master_v2_testnet_completion_path_wiring_v0.py",
    "tests/ops/test_bounded_master_v2_testnet_completion_path_wiring_contract_v0.py",
    "scripts/ops/run_testnet_bounded_observation_adapter_v0.py",
    "scripts/ops/ci_test_selection_v1.py",
    "tests/ci/test_ci_diff_aware_test_selection_v1.py",
)


def test_selector_bounded_master_v2_testnet_completion_path_wiring_five_file_diff_focused() -> None:
    sel = _run_selector(*BOUNDED_MASTER_V2_TESTNET_COMPLETION_PATH_WIRING_FILES)
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert (
        sel["test_selection_reason"] == "bounded_master_v2_testnet_completion_path_wiring_focused"
    )
    assert sel["tests_execute_full"] == "false"
    assert sel["tests_execute_focused"] == "true"
    targets = _targets(sel)
    wiring_owner = "tests/ops/test_bounded_master_v2_testnet_completion_path_wiring_contract_v0.py"
    adapter_owner = "tests/ops/test_run_testnet_bounded_observation_adapter_v0.py"
    replay_owner = "tests/ops/test_offline_master_v2_double_play_scenario_replay_completion_binding_contract_v0.py"
    completion_owner = "tests/ops/test_bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0.py"
    assert wiring_owner not in targets
    wiring_nodes = [target for target in targets if target.startswith(f"{wiring_owner}::")]
    assert len(wiring_nodes) == 7
    assert all("::test_" in target for target in wiring_nodes)
    assert (
        f"{wiring_owner}::test_full_e2e_bound_classification_bound_with_valid_market_input"
        in targets
    )
    assert (
        f"{wiring_owner}::test_invalid_replay_proof_classification_fails_closed_in_evaluator"
        in targets
    )
    assert f"{wiring_owner}::test_partial_replay_proof_classification_fails_closed" in targets
    assert (
        f"{wiring_owner}::test_completion_path_happy_path_unchanged_with_retention" not in targets
    )
    assert adapter_owner not in targets
    assert replay_owner not in targets
    assert completion_owner not in targets
    assert all("::test_" in target for target in targets if target != wiring_owner)
    assert f"{adapter_owner}::test_plan_only_default_does_not_call_subprocess" in targets
    assert f"{replay_owner}::test_replay_sourced_six_node_validation_graph_passes" in targets
    assert f"{completion_owner}::test_valid_static_proof_remains_non_authorizing" in targets
    assert (
        "tests/ci/test_ci_diff_aware_test_selection_v1.py::test_selector_bounded_master_v2_testnet_completion_path_wiring_five_file_diff_focused"
        in targets
    )
    assert len(targets) >= 26


def test_selector_bounded_master_v2_testnet_wiring_foreign_path_escalates_full() -> None:
    sel = _run_selector(
        *BOUNDED_MASTER_V2_TESTNET_COMPLETION_PATH_WIRING_FILES,
        "src/trading/master_v2/double_play_state.py",
    )
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert sel["test_selection_reason"].endswith("requires_full")


PR4504_DURABLE_COMPLETION_WALLCLOCK_BINDING_FILES = (
    "src/ops/bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0.py",
    "tests/ops/test_bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0.py",
)


def test_selector_pr4504_wallclock_binding_diff_narrow_focused() -> None:
    sel = _run_selector_with_patch("", *PR4504_DURABLE_COMPLETION_WALLCLOCK_BINDING_FILES)
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert sel["test_selection_reason"] == "durable_completion_focused"
    assert sel["tests_execute_full"] == "false"
    targets = _targets(sel)
    assert any(t.startswith(f"{_COMPLETION_OWNER}::") for t in targets)
    assert any(t.startswith(f"{_GRAPH_OWNER}::") for t in targets)
    assert _COMPLETION_OWNER not in targets
    assert _GRAPH_OWNER not in targets
    assert "tests/ci/test_ci_diff_aware_test_selection_v1.py" not in targets
    assert len(targets) < 20
    assert len(targets) >= 9


def test_selector_pr4504_wallclock_binding_includes_wallclock_regression_nodes() -> None:
    sel = _run_selector_with_patch("", *PR4504_DURABLE_COMPLETION_WALLCLOCK_BINDING_FILES)
    targets = set(_targets(sel))
    assert f"{_COMPLETION_OWNER}::test_missing_wallclock_evidence_fails_closed" in targets
    assert (
        f"{_COMPLETION_OWNER}::test_completion_wallclock_semantic_binding_uses_canonical_evaluators"
        in targets
    )
    assert (
        f"{_GRAPH_OWNER}::test_graph_testnet_completion_includes_wallclock_required_path_binding"
        in targets
    )
    assert f"{_GRAPH_OWNER}::test_graph_seven_vs_eight_path_drift_fail_closed" in targets


def test_selector_pr4504_wallclock_binding_not_full_404_owner_files() -> None:
    sel = _run_selector_with_patch("", *PR4504_DURABLE_COMPLETION_WALLCLOCK_BINDING_FILES)
    targets = _targets(sel)
    assert _COMPLETION_OWNER not in targets
    assert "tests/ci/test_ci_diff_aware_test_selection_v1.py" not in targets
    assert len(targets) < 50


def test_selector_pr4504_wallclock_binding_import_modules_bounded() -> None:
    sel = _run_selector_with_patch("", *PR4504_DURABLE_COMPLETION_WALLCLOCK_BINDING_FILES)
    modules = _modules(sel)
    assert modules == [
        "src.ops.bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0"
    ]
    assert "src.ops.durable_completion_validation" not in modules


def test_selector_durable_completion_foreign_production_change_stays_broad() -> None:
    sel = _run_selector(
        "src/ops/durable_completion_validation/graph.py",
        "src/ops/durable_completion_validation/models.py",
        "tests/ops/test_durable_completion_validation_graph_v1.py",
        "tests/ops/test_bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0.py",
    )
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    targets = _targets(sel)
    assert any(t.startswith(f"{_COMPLETION_OWNER}::") for t in targets)
    assert any(t.startswith(f"{_GRAPH_OWNER}::") for t in targets)
    assert _COMPLETION_OWNER not in targets
    assert _GRAPH_OWNER not in targets


def test_selector_pr4504_wallclock_binding_plus_foreign_file_full() -> None:
    sel = _run_selector_with_patch(
        "",
        *PR4504_DURABLE_COMPLETION_WALLCLOCK_BINDING_FILES,
        "src/strategies/__init__.py",
    )
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"


def test_selector_pr4504_wallclock_binding_plus_dependency_full() -> None:
    sel = _run_selector_with_patch(
        "",
        *PR4504_DURABLE_COMPLETION_WALLCLOCK_BINDING_FILES,
        "pyproject.toml",
    )
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"


def test_selector_pr4504_wallclock_binding_plus_ci_policy_includes_ci_owner() -> None:
    sel = _run_selector_with_patch(
        "",
        *PR4504_DURABLE_COMPLETION_WALLCLOCK_BINDING_FILES,
        "scripts/ops/ci_test_selection_v1.py",
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
    )
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    targets = _targets(sel)
    assert "tests/ci/test_ci_diff_aware_test_selection_v1.py" in targets
    assert _COMPLETION_OWNER not in targets


def test_selector_durable_completion_validator_rebinding_rules_unchanged() -> None:
    sel = _run_selector(*PE55_DURABLE_COMPLETION_FILL_REBINDING_FILES)
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    targets = _targets(sel)
    assert any(t.startswith(f"{_GRAPH_OWNER}::") for t in targets)
    assert any(t.startswith(f"{_INTEGRATION_OWNER}::") for t in targets)
    assert _GRAPH_OWNER not in targets
    assert _INTEGRATION_OWNER not in targets


def test_fast_lane_skips_full_static_sweep_when_focused() -> None:
    text = _ci_text()
    static_if = text.split("name: Static contract tests", 1)[1].split("run:", 1)[0]
    assert "tests_execute_focused != 'true'" in static_if
    assert "fast_lane_contract_mode == 'FULL_STATIC_CONTRACTS'" in static_if
    assert "OPS_SHARD_COUNT=8" in text


def test_selector_durable_completion_graph_core_plus_test_owners_focused() -> None:
    sel = _run_selector(
        "src/ops/durable_completion_validation/graph.py",
        "src/ops/durable_completion_validation/models.py",
        "tests/ops/test_durable_completion_validation_graph_v1.py",
        "tests/ops/test_bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0.py",
    )
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert sel["test_selection_reason"] == "durable_completion_focused"


def test_selector_pe55_full_diff_with_ci_workflow_rebundle_stays_focused() -> None:
    sel = _run_selector(
        *PE55_DURABLE_COMPLETION_FILL_REBINDING_FILES,
        ".github/workflows/ci.yml",
        "scripts/ops/ci_test_selection_v1.py",
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
    )
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert sel["test_selection_reason"] == "selector_self_change_bootstrap"
    assert (
        "tests/ops/test_durable_completion_validation_graph_v1.py"
        in sel["pr_bounded_pytest_targets"]
    )


def test_selector_durable_completion_facade_plus_graph_focused() -> None:
    sel = _run_selector(
        "src/ops/bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0.py",
        "src/ops/durable_completion_validation/graph.py",
        "src/ops/durable_completion_validation/validators/recovery.py",
        "tests/ops/test_durable_completion_validation_graph_v1.py",
        "tests/ops/test_bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0.py",
    )
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert sel["test_selection_reason"] == "durable_completion_focused"


def test_selector_durable_completion_rebundle_with_ci_policy_focused() -> None:
    sel = _run_selector(
        *PR4451_DURABLE_COMPLETION_FILES,
        "scripts/ops/ci_test_selection_v1.py",
        "config/ci/file_category_mapping.yaml",
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
    )
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert sel["test_selection_reason"] == "durable_completion_focused"
    assert "tests/ci/test_ci_diff_aware_test_selection_v1.py" in _targets(sel)


def test_selector_durable_completion_public_api_init_escalates_full() -> None:
    sel = _run_selector(
        "src/ops/durable_completion_validation/__init__.py",
        "src/ops/durable_completion_validation/models.py",
        "src/strategies/__init__.py",
        "tests/ops/test_durable_completion_validation_graph_v1.py",
        "tests/ops/test_bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0.py",
    )
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"


def test_selector_durable_completion_identity_plus_foreign_src_full() -> None:
    sel = _run_selector(
        "src/ops/durable_completion_validation/identity.py",
        "src/risk/killswitch.py",
        "tests/ops/test_durable_completion_validation_graph_v1.py",
        "tests/ops/test_bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0.py",
    )
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"


def test_selector_durable_completion_packaging_escalates_full() -> None:
    sel = _run_selector(
        "src/ops/durable_completion_validation/graph.py",
        "pyproject.toml",
        "tests/ops/test_durable_completion_validation_graph_v1.py",
        "tests/ops/test_bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0.py",
    )
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"


def test_selector_durable_completion_execution_touch_escalates_full() -> None:
    sel = _run_selector(
        "src/ops/durable_completion_validation/validators/traceability.py",
        "src/execution/live/orchestrator.py",
        "tests/ops/test_durable_completion_validation_graph_v1.py",
        "tests/ops/test_bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0.py",
    )
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"


def test_selector_durable_completion_unknown_file_escalates_full() -> None:
    sel = _run_selector(
        "src/ops/durable_completion_validation/graph.py",
        "misc/unclassified.bin",
        "tests/ops/test_durable_completion_validation_graph_v1.py",
        "tests/ops/test_bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0.py",
    )
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"


def test_selector_durable_completion_missing_test_owner_escalates_full(monkeypatch) -> None:
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "ci_test_selection_v1_missing_owner",
        str(SELECTOR),
    )
    assert spec and spec.loader
    sel_mod = importlib.util.module_from_spec(spec)
    sys.modules["ci_test_selection_v1_missing_owner"] = sel_mod
    spec.loader.exec_module(sel_mod)

    original_exists = sel_mod._repo_path_exists

    def fake_exists(path: str) -> bool:
        if (
            path
            == "tests/ops/test_bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0.py"
        ):
            return False
        return original_exists(path)

    monkeypatch.setattr(sel_mod, "_repo_path_exists", fake_exists)
    result = sel_mod.resolve_selection(["src/ops/durable_completion_validation/graph.py"])
    assert result.mode == "FULL"


def test_selector_durable_completion_ci_policy_only_escalates_full() -> None:
    sel = _run_selector(
        "scripts/ops/ci_test_selection_v1.py",
        "config/ci/file_category_mapping.yaml",
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
    )
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"


def test_selector_durable_completion_import_modules() -> None:
    sel = _run_selector(*PR4451_DURABLE_COMPLETION_FILES)
    modules = _modules(sel)
    assert "src.ops.durable_completion_validation" in modules
    assert (
        "src.ops.bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0"
        in modules
    )


def test_mapping_file_includes_durable_completion_focused() -> None:
    text = MAPPING.read_text(encoding="utf-8")
    assert "durable_completion_focused:" in text


PE52_PREFLIGHT_ASSEMBLY_FILES = (
    "src/ops/bounded_futures_testnet_preflight_execution_readiness_assembly_lifecycle_integration_contract_v0.py",
    "tests/ops/test_bounded_futures_testnet_preflight_execution_readiness_assembly_lifecycle_integration_contract_v0.py",
)


def test_selector_pe52_preflight_assembly_fileset_focused() -> None:
    sel = _run_selector(*PE52_PREFLIGHT_ASSEMBLY_FILES)
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert sel["test_selection_reason"] == "preflight_assembly_focused"
    targets = _targets(sel)
    assert (
        "tests/ops/test_bounded_futures_testnet_preflight_execution_readiness_assembly_lifecycle_integration_contract_v0.py"
        in targets
    )
    assert (
        "tests/ops/test_bounded_futures_testnet_reconciliation_review_lifecycle_integration_contract_v0.py"
        in targets
    )
    assert sel["tests_execute_full"] == "false"
    assert sel["tests_execute_no_op"] == "false"


def test_selector_pe26_owner_plus_test_owner_only_focused() -> None:
    sel = _run_selector(*PE52_PREFLIGHT_ASSEMBLY_FILES)
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert sel["test_selection_reason"] == "preflight_assembly_focused"


def test_selector_unknown_productive_src_ops_never_no_op() -> None:
    sel = _run_selector("src/ops/unknown_unmapped_contract_v0.py")
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert sel["test_selection_reason"] == "productive_src_no_op_blocked_fail_closed"
    assert sel["tests_execute_no_op"] == "false"


def test_selector_productive_src_without_test_owner_escalates_full() -> None:
    sel = _run_selector(
        "src/ops/bounded_futures_testnet_preflight_packet_contract_v0.py",
    )
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert sel["tests_execute_pr_bounded_full"] == "true"
    assert sel["tests_execute_full"] == "false"


def test_selector_preflight_assembly_rebundle_with_ci_policy_focused() -> None:
    sel = _run_selector(
        *PE52_PREFLIGHT_ASSEMBLY_FILES,
        "scripts/ops/ci_test_selection_v1.py",
        "config/ci/file_category_mapping.yaml",
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
    )
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert sel["test_selection_reason"] == "preflight_assembly_focused"
    assert "tests/ci/test_ci_diff_aware_test_selection_v1.py" in _targets(sel)


def test_selector_preflight_assembly_plus_foreign_src_full() -> None:
    sel = _run_selector(
        *PE52_PREFLIGHT_ASSEMBLY_FILES,
        "src/execution/live/orchestrator.py",
    )
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"


def test_selector_preflight_assembly_execution_touch_escalates_full() -> None:
    sel = _run_selector(
        PE52_PREFLIGHT_ASSEMBLY_FILES[0],
        "src/risk/killswitch.py",
        PE52_PREFLIGHT_ASSEMBLY_FILES[1],
    )
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"


def test_selector_preflight_assembly_missing_test_owner_escalates_full(monkeypatch) -> None:
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "ci_test_selection_v1_pa_missing_owner",
        str(SELECTOR),
    )
    assert spec and spec.loader
    sel_mod = importlib.util.module_from_spec(spec)
    sys.modules["ci_test_selection_v1_pa_missing_owner"] = sel_mod
    spec.loader.exec_module(sel_mod)

    original_exists = sel_mod._repo_path_exists

    def fake_exists(path: str) -> bool:
        if (
            path
            == "tests/ops/test_bounded_futures_testnet_reconciliation_review_lifecycle_integration_contract_v0.py"
        ):
            return False
        return original_exists(path)

    monkeypatch.setattr(sel_mod, "_repo_path_exists", fake_exists)
    result = sel_mod.resolve_selection([PE52_PREFLIGHT_ASSEMBLY_FILES[0]])
    assert result.mode == "FULL"


def test_selector_preflight_assembly_ci_policy_only_escalates_full() -> None:
    sel = _run_selector(
        "scripts/ops/ci_test_selection_v1.py",
        "config/ci/file_category_mapping.yaml",
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
    )
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"


def test_selector_preflight_assembly_import_modules() -> None:
    sel = _run_selector(*PE52_PREFLIGHT_ASSEMBLY_FILES)
    modules = _modules(sel)
    assert (
        "src.ops.bounded_futures_testnet_preflight_execution_readiness_assembly_lifecycle_integration_contract_v0"
        in modules
    )


def test_mapping_file_includes_preflight_assembly_focused() -> None:
    text = MAPPING.read_text(encoding="utf-8")
    assert "preflight_assembly_focused:" in text


PR4585_BOUNDED_FUTURES_TESTNET_CONTRACT_FILES = (
    "src/ops/bounded_futures_testnet_contract_v0.py",
    "tests/ops/test_archive_futures_testnet_harness_v0.py",
    "tests/ops/test_bounded_futures_testnet_adapter_contract_v0.py",
    "tests/ops/test_bounded_futures_testnet_contract_v0.py",
    "tests/ops/test_order_capability_dry_validation_contract_v1.py",
    "tests/ops/test_run_order_capability_dry_validation_adapter_v1.py",
)

PR4585_REQUIRED_OPS_TESTOWNERS = (
    "tests/ops/test_bounded_futures_testnet_contract_v0.py",
    "tests/ops/test_bounded_futures_testnet_adapter_contract_v0.py",
    "tests/ops/test_order_capability_dry_validation_contract_v1.py",
    "tests/ops/test_archive_futures_testnet_harness_v0.py",
    "tests/ops/test_run_order_capability_dry_validation_adapter_v1.py",
)


def test_selector_pr4585_bounded_futures_testnet_contract_fileset_focused() -> None:
    sel = _run_selector(*PR4585_BOUNDED_FUTURES_TESTNET_CONTRACT_FILES)
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert sel["test_selection_reason"] == "bounded_futures_testnet_contract_focused"
    assert sel["tests_execute_focused"] == "true"
    assert sel["tests_execute_pr_bounded_full"] == "false"
    assert sel["fast_lane_contract_mode"] == "FULL_STATIC_CONTRACTS"
    targets = _targets(sel)
    for owner in PR4585_REQUIRED_OPS_TESTOWNERS:
        assert owner in targets
    assert "tests/ci/test_ci_diff_aware_test_selection_v1.py" in targets
    assert len([t for t in targets if t in PR4585_REQUIRED_OPS_TESTOWNERS]) == 5


def test_selector_pr4585_bounded_futures_testnet_contract_no_missing_testowners() -> None:
    sel = _run_selector(*PR4585_BOUNDED_FUTURES_TESTNET_CONTRACT_FILES)
    targets = _targets(sel)
    missing = [t for t in PR4585_REQUIRED_OPS_TESTOWNERS if t not in targets]
    assert missing == []


def test_selector_pr4585_bounded_futures_testnet_contract_not_pr_bounded_full() -> None:
    sel = _run_selector(*PR4585_BOUNDED_FUTURES_TESTNET_CONTRACT_FILES)
    assert sel["test_selection_mode"] != "PR_BOUNDED_FULL"
    assert sel["tests_execute_pr_bounded_full"] == "false"
    bounded = sel.get("pr_bounded_pytest_targets", "")
    assert bounded == ""


def test_selector_pr4585_owner_without_primary_test_owner_escalates_full() -> None:
    sel = _run_selector(PR4585_BOUNDED_FUTURES_TESTNET_CONTRACT_FILES[0])
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert (
        sel["test_selection_reason"]
        == "bounded_futures_testnet_contract_incomplete_or_missing_test_owner"
    )


def test_selector_pr4585_plus_unknown_ops_src_escalates_full() -> None:
    sel = _run_selector(
        *PR4585_BOUNDED_FUTURES_TESTNET_CONTRACT_FILES,
        "src/ops/bounded_futures_testnet_preflight_packet_contract_v0.py",
    )
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"


def test_selector_pr4585_plus_runtime_touch_escalates_full() -> None:
    sel = _run_selector(
        PR4585_BOUNDED_FUTURES_TESTNET_CONTRACT_FILES[0],
        "src/runtime/scheduler.py",
        *PR4585_BOUNDED_FUTURES_TESTNET_CONTRACT_FILES[1:],
    )
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"


def test_selector_pr4585_rebundle_with_ci_policy_focused() -> None:
    sel = _run_selector(
        *PR4585_BOUNDED_FUTURES_TESTNET_CONTRACT_FILES,
        "scripts/ops/ci_test_selection_v1.py",
        "config/ci/file_category_mapping.yaml",
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
    )
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert sel["test_selection_reason"] == "bounded_futures_testnet_contract_focused"


def test_selector_pr4585_import_modules() -> None:
    sel = _run_selector(*PR4585_BOUNDED_FUTURES_TESTNET_CONTRACT_FILES)
    modules = _modules(sel)
    assert "src.ops.bounded_futures_testnet_contract_v0" in modules


def test_mapping_file_includes_bounded_futures_testnet_contract_focused() -> None:
    text = MAPPING.read_text(encoding="utf-8")
    assert "bounded_futures_testnet_contract_focused:" in text


def test_selector_pr4585_focused_fast_lane_wired_not_full_static_only() -> None:
    text = _ci_text()
    static_if = text.split("Static contract tests", 1)[1].split("\n", 3)[0]
    assert "tests_execute_focused != 'true'" in text
    assert "Focused Fast-Lane contract check" in text


PE53_RISK_KILLSWITCH_FILES = (
    "src/ops/bounded_futures_testnet_risk_killswitch_lifecycle_integration_contract_v0.py",
    "tests/ops/test_bounded_futures_testnet_risk_killswitch_lifecycle_integration_contract_v0.py",
)


def test_selector_pe53_risk_killswitch_fileset_focused() -> None:
    sel = _run_selector(*PE53_RISK_KILLSWITCH_FILES)
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert sel["test_selection_reason"] == "risk_killswitch_focused"
    targets = _targets(sel)
    assert (
        "tests/ops/test_bounded_futures_testnet_risk_killswitch_lifecycle_integration_contract_v0.py"
        in targets
    )
    assert "tests/ops/test_order_capability_killswitch_abort_binding_contract_v1.py" in targets
    assert sel["tests_execute_full"] == "false"
    assert sel["tests_execute_no_op"] == "false"


def test_selector_pe53_owner_plus_test_owner_only_focused() -> None:
    sel = _run_selector(*PE53_RISK_KILLSWITCH_FILES)
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert sel["test_selection_reason"] == "risk_killswitch_focused"


def test_selector_pe53_owner_without_test_owner_escalates_full() -> None:
    sel = _run_selector(PE53_RISK_KILLSWITCH_FILES[0])
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert sel["test_selection_reason"] == "risk_killswitch_incomplete_or_missing_test_owner"


def test_selector_pe53_plus_unknown_ops_src_escalates_full() -> None:
    sel = _run_selector(
        *PE53_RISK_KILLSWITCH_FILES,
        "src/ops/bounded_futures_testnet_preflight_packet_contract_v0.py",
    )
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"


def test_selector_pe53_plus_unknown_src_escalates_full() -> None:
    sel = _run_selector(
        *PE53_RISK_KILLSWITCH_FILES,
        "src/execution/live/orchestrator.py",
    )
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"


def test_selector_pe53_risk_killswitch_outside_owner_escalates_full() -> None:
    sel = _run_selector(
        *PE53_RISK_KILLSWITCH_FILES,
        "src/risk/killswitch.py",
    )
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"


def test_selector_pe53_runtime_touch_escalates_full() -> None:
    sel = _run_selector(
        PE53_RISK_KILLSWITCH_FILES[0],
        "src/runtime/scheduler.py",
        PE53_RISK_KILLSWITCH_FILES[1],
    )
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"


def test_selector_pe53_trading_strategy_master_v2_touch_escalates_full() -> None:
    sel = _run_selector(
        PE53_RISK_KILLSWITCH_FILES[0],
        "src/strategies/vol_breakout.py",
        PE53_RISK_KILLSWITCH_FILES[1],
    )
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"


def test_selector_pe53_packaging_change_escalates_full() -> None:
    sel = _run_selector(
        *PE53_RISK_KILLSWITCH_FILES,
        "pyproject.toml",
    )
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"


def test_selector_pe53_rebundle_with_ci_policy_focused() -> None:
    sel = _run_selector(
        *PE53_RISK_KILLSWITCH_FILES,
        "scripts/ops/ci_test_selection_v1.py",
        "config/ci/file_category_mapping.yaml",
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
    )
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert sel["test_selection_reason"] == "risk_killswitch_focused"
    assert "tests/ci/test_ci_diff_aware_test_selection_v1.py" in _targets(sel)


def test_selector_pe53_missing_abort_test_owner_escalates_full(monkeypatch) -> None:
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "ci_test_selection_v1_rk_missing_owner",
        str(SELECTOR),
    )
    assert spec and spec.loader
    sel_mod = importlib.util.module_from_spec(spec)
    sys.modules["ci_test_selection_v1_rk_missing_owner"] = sel_mod
    spec.loader.exec_module(sel_mod)

    original_exists = sel_mod._repo_path_exists

    def fake_exists(path: str) -> bool:
        if path == "tests/ops/test_order_capability_killswitch_abort_binding_contract_v1.py":
            return False
        return original_exists(path)

    monkeypatch.setattr(sel_mod, "_repo_path_exists", fake_exists)
    result = sel_mod.resolve_selection(list(PE53_RISK_KILLSWITCH_FILES))
    assert result.mode == "FULL"
    assert result.reason == "risk_killswitch_incomplete_or_missing_test_owner"


def test_selector_pe53_import_modules() -> None:
    sel = _run_selector(*PE53_RISK_KILLSWITCH_FILES)
    modules = _modules(sel)
    assert (
        "src.ops.bounded_futures_testnet_risk_killswitch_lifecycle_integration_contract_v0"
        in modules
    )


def test_mapping_file_includes_risk_killswitch_focused() -> None:
    text = MAPPING.read_text(encoding="utf-8")
    assert "risk_killswitch_focused:" in text


SLICE2_OKX_EUROPE_ADAPTER_LIFECYCLE_FILES = (
    "src/ops/okx_europe_adapter_lifecycle_contract_v0.py",
    "tests/ops/test_okx_europe_adapter_lifecycle_contract_v0.py",
)


def test_selector_okx_europe_adapter_lifecycle_fileset_focused() -> None:
    sel = _run_selector(*SLICE2_OKX_EUROPE_ADAPTER_LIFECYCLE_FILES)
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert sel["test_selection_reason"] == "okx_europe_adapter_lifecycle_focused"
    targets = _targets(sel)
    assert SLICE2_OKX_EUROPE_ADAPTER_LIFECYCLE_FILES[1] in targets
    assert "tests/ops/test_bounded_futures_testnet_okx_eea_xperp_binding_contract_v0.py" in targets
    assert (
        "tests/ops/test_aws_shadow_paper_testnet_okx_europe_compatibility_contract_v0.py" in targets
    )
    assert sel["tests_execute_full"] == "false"
    assert sel["tests_execute_no_op"] == "false"


def test_selector_okx_europe_adapter_lifecycle_owner_plus_test_owner_only_focused() -> None:
    sel = _run_selector(*SLICE2_OKX_EUROPE_ADAPTER_LIFECYCLE_FILES)
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert sel["test_selection_reason"] == "okx_europe_adapter_lifecycle_focused"


def test_selector_okx_europe_adapter_lifecycle_rebundle_with_ci_policy_focused() -> None:
    sel = _run_selector(
        *SLICE2_OKX_EUROPE_ADAPTER_LIFECYCLE_FILES,
        "scripts/ops/ci_test_selection_v1.py",
        "config/ci/file_category_mapping.yaml",
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
    )
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert sel["test_selection_reason"] == "okx_europe_adapter_lifecycle_focused"
    assert "tests/ci/test_ci_diff_aware_test_selection_v1.py" in _targets(sel)


def test_selector_okx_europe_adapter_lifecycle_plus_foreign_src_full() -> None:
    sel = _run_selector(
        *SLICE2_OKX_EUROPE_ADAPTER_LIFECYCLE_FILES,
        "src/execution/live/orchestrator.py",
    )
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert sel["test_selection_reason"] == "okx_europe_adapter_lifecycle_foreign_path_requires_full"


def test_selector_okx_europe_adapter_lifecycle_owner_without_test_owner_escalates_full() -> None:
    sel = _run_selector(SLICE2_OKX_EUROPE_ADAPTER_LIFECYCLE_FILES[0])
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert (
        sel["test_selection_reason"]
        == "okx_europe_adapter_lifecycle_incomplete_or_missing_test_owner"
    )


def test_selector_okx_europe_adapter_lifecycle_import_modules() -> None:
    sel = _run_selector(*SLICE2_OKX_EUROPE_ADAPTER_LIFECYCLE_FILES)
    modules = _modules(sel)
    assert "src.ops.okx_europe_adapter_lifecycle_contract_v0" in modules


def test_mapping_file_includes_okx_europe_adapter_lifecycle_focused() -> None:
    text = MAPPING.read_text(encoding="utf-8")
    assert "okx_europe_adapter_lifecycle_focused:" in text


SLICE3_OKX_EUROPE_ADAPTER_CAPABILITY_DIGEST_FILES = (
    "src/ops/bounded_futures_testnet_adapter_capability_lifecycle_integration_contract_v0.py",
    "tests/ops/test_bounded_futures_testnet_adapter_capability_lifecycle_integration_contract_v0.py",
)


def test_selector_okx_europe_adapter_lifecycle_slice3_digest_hook_focused() -> None:
    sel = _run_selector(*SLICE3_OKX_EUROPE_ADAPTER_CAPABILITY_DIGEST_FILES)
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert sel["test_selection_reason"] == "okx_europe_adapter_lifecycle_focused"
    targets = _targets(sel)
    assert SLICE3_OKX_EUROPE_ADAPTER_CAPABILITY_DIGEST_FILES[1] in targets
    assert "tests/ops/test_okx_europe_adapter_lifecycle_contract_v0.py" in targets
    assert "tests/ops/test_bounded_futures_testnet_okx_eea_xperp_binding_contract_v0.py" in targets
    assert (
        "tests/ops/test_aws_shadow_paper_testnet_okx_europe_compatibility_contract_v0.py" in targets
    )


def test_selector_okx_europe_adapter_lifecycle_slice3_integration_owner_without_test_owner_full() -> (
    None
):
    sel = _run_selector(SLICE3_OKX_EUROPE_ADAPTER_CAPABILITY_DIGEST_FILES[0])
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert (
        sel["test_selection_reason"]
        == "okx_europe_adapter_lifecycle_incomplete_or_missing_test_owner"
    )


PE54_TINY_ORDER_FILES = (
    "src/ops/bounded_futures_testnet_tiny_order_lifecycle_integration_contract_v0.py",
    "tests/ops/test_bounded_futures_testnet_tiny_order_lifecycle_integration_contract_v0.py",
)


def test_selector_pe54_tiny_order_prod_owner_only_focused() -> None:
    sel = _run_selector(PE54_TINY_ORDER_FILES[0])
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert sel["test_selection_reason"] == "tiny_order_incomplete_or_missing_test_owner"


def test_selector_pe54_tiny_order_test_owner_only_focused() -> None:
    sel = _run_selector(PE54_TINY_ORDER_FILES[1])
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert sel["test_selection_reason"] == "tiny_order_focused"
    targets = _targets(sel)
    assert PE54_TINY_ORDER_FILES[1] in targets
    assert "tests/ops/test_order_capability_killswitch_abort_binding_contract_v1.py" in targets
    assert "tests/ops/test_order_capability_cancel_cleanup_failclosed_contract_v1.py" in targets
    assert sel["tests_execute_full"] == "false"
    assert sel["tests_execute_no_op"] == "false"


def test_selector_pe54_tiny_order_fileset_focused() -> None:
    sel = _run_selector(*PE54_TINY_ORDER_FILES)
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert sel["test_selection_reason"] == "tiny_order_focused"
    targets = _targets(sel)
    assert PE54_TINY_ORDER_FILES[1] in targets
    assert "tests/ops/test_order_capability_killswitch_abort_binding_contract_v1.py" in targets
    assert "tests/ops/test_order_capability_cancel_cleanup_failclosed_contract_v1.py" in targets
    assert "tests/ci/test_ci_diff_aware_test_selection_v1.py" in targets
    assert sel["tests_execute_full"] == "false"
    assert sel["tests_execute_no_op"] == "false"
    assert "productive_src_no_op_blocked_fail_closed" not in sel["test_selection_reason"]


def test_selector_pe54_tiny_order_plus_unknown_ops_src_escalates_full() -> None:
    sel = _run_selector(
        *PE54_TINY_ORDER_FILES,
        "src/ops/bounded_futures_testnet_preflight_packet_contract_v0.py",
    )
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"


def test_selector_pe54_tiny_order_plus_unknown_src_escalates_full() -> None:
    sel = _run_selector(
        *PE54_TINY_ORDER_FILES,
        "src/execution/live/orchestrator.py",
    )
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"


def test_selector_pe54_tiny_order_outside_owner_escalates_full() -> None:
    sel = _run_selector(
        *PE54_TINY_ORDER_FILES,
        "src/risk/killswitch.py",
    )
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"


def test_selector_pe54_tiny_order_runtime_touch_escalates_full() -> None:
    sel = _run_selector(
        PE54_TINY_ORDER_FILES[0],
        "src/runtime/scheduler.py",
        PE54_TINY_ORDER_FILES[1],
    )
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"


def test_selector_pe54_tiny_order_trading_strategy_master_v2_touch_escalates_full() -> None:
    sel = _run_selector(
        PE54_TINY_ORDER_FILES[0],
        "src/strategies/vol_breakout.py",
        PE54_TINY_ORDER_FILES[1],
    )
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"


def test_selector_pe54_tiny_order_packaging_change_escalates_full() -> None:
    sel = _run_selector(
        *PE54_TINY_ORDER_FILES,
        "pyproject.toml",
    )
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"


def test_selector_pe54_tiny_order_rebundle_with_ci_policy_focused() -> None:
    sel = _run_selector(
        *PE54_TINY_ORDER_FILES,
        "scripts/ops/ci_test_selection_v1.py",
        "config/ci/file_category_mapping.yaml",
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
    )
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert sel["test_selection_reason"] == "tiny_order_focused"
    assert "tests/ci/test_ci_diff_aware_test_selection_v1.py" in _targets(sel)


def test_selector_pe54_tiny_order_missing_abort_test_owner_escalates_full(monkeypatch) -> None:
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "ci_test_selection_v1_to_missing_abort",
        str(SELECTOR),
    )
    assert spec and spec.loader
    sel_mod = importlib.util.module_from_spec(spec)
    sys.modules["ci_test_selection_v1_to_missing_abort"] = sel_mod
    spec.loader.exec_module(sel_mod)

    original_exists = sel_mod._repo_path_exists

    def fake_exists(path: str) -> bool:
        if path == "tests/ops/test_order_capability_killswitch_abort_binding_contract_v1.py":
            return False
        return original_exists(path)

    monkeypatch.setattr(sel_mod, "_repo_path_exists", fake_exists)
    result = sel_mod.resolve_selection(list(PE54_TINY_ORDER_FILES))
    assert result.mode == "FULL"
    assert result.reason == "tiny_order_incomplete_or_missing_test_owner"


def test_selector_pe54_tiny_order_missing_cleanup_test_owner_escalates_full(monkeypatch) -> None:
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "ci_test_selection_v1_to_missing_cleanup",
        str(SELECTOR),
    )
    assert spec and spec.loader
    sel_mod = importlib.util.module_from_spec(spec)
    sys.modules["ci_test_selection_v1_to_missing_cleanup"] = sel_mod
    spec.loader.exec_module(sel_mod)

    original_exists = sel_mod._repo_path_exists

    def fake_exists(path: str) -> bool:
        if path == "tests/ops/test_order_capability_cancel_cleanup_failclosed_contract_v1.py":
            return False
        return original_exists(path)

    monkeypatch.setattr(sel_mod, "_repo_path_exists", fake_exists)
    result = sel_mod.resolve_selection(list(PE54_TINY_ORDER_FILES))
    assert result.mode == "FULL"
    assert result.reason == "tiny_order_incomplete_or_missing_test_owner"


def test_selector_pe54_tiny_order_import_modules() -> None:
    sel = _run_selector(*PE54_TINY_ORDER_FILES)
    modules = _modules(sel)
    assert "src.ops.bounded_futures_testnet_tiny_order_lifecycle_integration_contract_v0" in modules


def test_selector_pe54_tiny_order_ci_policy_only_escalates_full() -> None:
    sel = _run_selector(
        "scripts/ops/ci_test_selection_v1.py",
        "config/ci/file_category_mapping.yaml",
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
    )
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"


def test_mapping_file_includes_tiny_order_focused() -> None:
    text = MAPPING.read_text(encoding="utf-8")
    assert "tiny_order_focused:" in text


PE21_RECONCILIATION_PRIMARY_EVIDENCE_FILES = (
    "src/ops/bounded_futures_testnet_position_order_reconciliation_primary_evidence_integration_contract_v0.py",
    "tests/ops/test_bounded_futures_testnet_position_order_reconciliation_primary_evidence_integration_contract_v0.py",
)


def test_selector_pe21_reconciliation_primary_evidence_fileset_focused() -> None:
    sel = _run_selector(*PE21_RECONCILIATION_PRIMARY_EVIDENCE_FILES)
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert sel["test_selection_reason"] == "reconciliation_primary_evidence_focused"
    targets = _targets(sel)
    assert PE21_RECONCILIATION_PRIMARY_EVIDENCE_FILES[1] in targets
    assert "tests/ci/test_ci_diff_aware_test_selection_v1.py" in targets
    assert sel["tests_execute_full"] == "false"
    assert "productive_src_no_op_blocked_fail_closed" not in sel["test_selection_reason"]


def test_selector_pe21_prod_owner_without_test_owner_escalates_full() -> None:
    sel = _run_selector(PE21_RECONCILIATION_PRIMARY_EVIDENCE_FILES[0])
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert (
        sel["test_selection_reason"]
        == "reconciliation_primary_evidence_incomplete_or_missing_test_owner"
    )


def test_selector_pe21_plus_unknown_src_escalates_full() -> None:
    sel = _run_selector(
        *PE21_RECONCILIATION_PRIMARY_EVIDENCE_FILES,
        "src/execution/live/orchestrator.py",
    )
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"


def test_selector_pe21_rebundle_with_ci_policy_focused() -> None:
    sel = _run_selector(
        *PE21_RECONCILIATION_PRIMARY_EVIDENCE_FILES,
        "scripts/ops/ci_test_selection_v1.py",
        "config/ci/file_category_mapping.yaml",
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
    )
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert sel["test_selection_reason"] == "reconciliation_primary_evidence_focused"


def test_mapping_file_includes_reconciliation_primary_evidence_focused() -> None:
    text = MAPPING.read_text(encoding="utf-8")
    assert "reconciliation_primary_evidence_focused:" in text


PR4489_WALLCLOCK_FILES: tuple[str, ...] = (
    "src/ops/wallclock_session_evidence_v0.py",
    "scripts/ops/shadow_247_futures_start_wrapper_skeleton_v0.py",
    "scripts/ops/run_shadow_bounded_observation_adapter_v0.py",
    "tests/ops/test_run_shadow_bounded_observation_adapter_v0.py",
    "tests/ops/test_shadow_wallclock_duration_evidence_contract_v0.py",
    "tests/ops/test_shadow_247_futures_start_wrapper_skeleton_v0.py",
)

PR4491_CI_BOOTSTRAP_FILES: tuple[str, ...] = (
    ".github/workflows/ci-export-pack-download-verify.yml",
    ".github/workflows/ci-scheduled-paper-and-export-smoke.yml",
    ".github/workflows/ci.yml",
    ".github/workflows/full_audit_weekly.yml",
    ".github/workflows/offline_suites.yml",
    ".github/workflows/paper_session_audit_evidence.yml",
    ".github/workflows/paper_tests_audit_evidence.yml",
    ".github/workflows/prbj-testnet-exec-events.yml",
    ".github/workflows/test-health-automation.yml",
    "scripts/ops/ci_test_selection_v1.py",
    "tests/ci/test_ci_diff_aware_test_selection_v1.py",
    "tests/ci/test_ci_scheduled_paper_export_smoke_workflow_contract_v0.py",
    "tests/ci/test_class_a_shadow_paper_scheduled_probe_workflow_contract_v0.py",
    "tests/ci/test_paper_session_audit_evidence_workflow_contract_v0.py",
    "tests/ci/test_paper_tests_audit_evidence_workflow_contract_v0.py",
    "tests/ci/test_prj_scheduled_shadow_paper_features_smoke_workflow_contract_v0.py",
    "tests/ci/test_shadow_paper_smoke_workflow_contract_v0.py",
    "tests/ci/test_workflows_no_pull_request_target_contract_v0.py",
)


def test_selector_case_pr4489_wallclock_diff_focused() -> None:
    sel = _run_selector(*PR4489_WALLCLOCK_FILES)
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert sel["test_selection_reason"] == "wallclock_focused"
    assert sel["tests_execute_full"] == "false"
    assert sel["tests_execute_focused"] == "true"
    targets = _targets(sel)
    assert "tests/ops/test_run_shadow_bounded_observation_adapter_v0.py" in targets
    assert "tests/ops/test_shadow_wallclock_duration_evidence_contract_v0.py" in targets
    assert "tests/ops/test_shadow_247_futures_start_wrapper_skeleton_v0.py" in targets


def test_selector_case_pr4491_ci_bootstrap_diff_focused() -> None:
    sel = _run_selector(*PR4491_CI_BOOTSTRAP_FILES)
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert sel["test_selection_reason"] == "selector_self_change_bootstrap"
    assert sel["tests_execute_pr_bounded_full"] == "true"
    assert "tests/ci/test_ci_diff_aware_test_selection_v1.py" in sel["pr_bounded_pytest_targets"]


def test_selector_case_ci_selector_change_full() -> None:
    sel = _run_selector(
        "scripts/ops/ci_test_selection_v1.py",
        "config/ci/file_category_mapping.yaml",
    )
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"


def test_selector_case_dependency_change_full() -> None:
    sel = _run_selector("pyproject.toml")
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert sel["test_selection_reason"] == "category_dependencies_requires_full"


def test_selector_case_central_shared_src_change_full() -> None:
    sel = _run_selector("src/core/foo.py")
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert sel["test_selection_reason"] == "category_central_src_requires_full"


def test_selector_case_docs_only_safe_no_op() -> None:
    sel = _run_selector("docs/foo.md")
    assert sel["test_selection_mode"] == "NO_OP"


def test_selector_case_unknown_workflow_diff_full() -> None:
    sel = _run_selector(
        "scripts/ops/ci_test_selection_v1.py",
        ".github/workflows/unknown-workflow.yml",
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
    )
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"


def test_selector_case_unknown_src_diff_full() -> None:
    sel = _run_selector("misc/unclassified.bin")
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"


def test_selector_ci_workflow_change_self_focused_ci_infra() -> None:
    sel = _run_selector(
        ".github/workflows/ci.yml",
        "scripts/ops/ci_test_selection_v1.py",
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
        "tests/ci/test_workflows_no_pull_request_target_contract_v0.py",
        "tests/ci/test_ci_testowner_runtime_budget_reporting_contract_v0.py",
    )
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert sel["test_selection_reason"] == "selector_self_change_bootstrap"


PR4497_BOUNDED_NETWORK_PREFLIGHT_FILES: tuple[str, ...] = (
    "src/ops/bounded_network_testnet_preflight_contract_v0.py",
    "tests/ops/test_bounded_network_testnet_preflight_contract_v0.py",
)


def test_selector_pr4497_bounded_network_preflight_diff_focused() -> None:
    sel = _run_selector(*PR4497_BOUNDED_NETWORK_PREFLIGHT_FILES)
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert sel["test_selection_reason"] == "bounded_network_testnet_preflight_focused"
    assert sel["tests_execute_full"] == "false"
    assert sel["tests_execute_focused"] == "true"
    assert sel["tests_execute_no_op"] == "false"
    targets = _targets(sel)
    assert targets == [
        "tests/ops/test_bounded_network_testnet_preflight_contract_v0.py",
    ]
    assert "tests/ci/test_ci_diff_aware_test_selection_v1.py" not in targets


def test_selector_bounded_network_preflight_owner_without_test_owner_full() -> None:
    sel = _run_selector("src/ops/bounded_network_testnet_preflight_contract_v0.py")
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert (
        sel["test_selection_reason"]
        == "bounded_network_testnet_preflight_incomplete_or_missing_test_owner"
    )


def test_selector_bounded_network_preflight_plus_foreign_src_full() -> None:
    sel = _run_selector(
        *PR4497_BOUNDED_NETWORK_PREFLIGHT_FILES,
        "src/execution/live/orchestrator.py",
    )
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert (
        sel["test_selection_reason"]
        == "bounded_network_testnet_preflight_foreign_path_requires_full"
    )


def test_selector_bounded_network_preflight_plus_dependency_full() -> None:
    sel = _run_selector(*PR4497_BOUNDED_NETWORK_PREFLIGHT_FILES, "requirements.txt")
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert (
        sel["test_selection_reason"]
        == "bounded_network_testnet_preflight_foreign_path_requires_full"
    )


def test_selector_bounded_network_preflight_rebundle_with_ci_policy_focused() -> None:
    sel = _run_selector(
        *PR4497_BOUNDED_NETWORK_PREFLIGHT_FILES,
        "scripts/ops/ci_test_selection_v1.py",
        "config/ci/file_category_mapping.yaml",
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
    )
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert sel["test_selection_reason"] == "bounded_network_testnet_preflight_focused"
    targets = _targets(sel)
    assert targets == [
        "tests/ops/test_bounded_network_testnet_preflight_contract_v0.py",
    ]
    assert "tests/ci/test_ci_diff_aware_test_selection_v1.py" not in targets


def test_selector_bounded_network_preflight_import_modules() -> None:
    sel = _run_selector(*PR4497_BOUNDED_NETWORK_PREFLIGHT_FILES)
    modules = sel.get("focused_module_imports", "").split()
    assert modules == ["src.ops.bounded_network_testnet_preflight_contract_v0"]


RUNTIME_WALLCLOCK_EVIDENCE_EMITTER_FILES: tuple[str, ...] = (
    "src/ops/runtime_wallclock_evidence_emitter_contract_v0.py",
    "tests/ops/test_runtime_wallclock_evidence_emitter_contract_v0.py",
)


def test_selector_runtime_wallclock_evidence_emitter_owner_pair_focused() -> None:
    sel = _run_selector(*RUNTIME_WALLCLOCK_EVIDENCE_EMITTER_FILES)
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert sel["test_selection_reason"] == "runtime_wallclock_evidence_emitter_focused"
    assert sel["tests_execute_full"] == "false"
    assert sel["tests_execute_focused"] == "true"
    assert sel["tests_execute_no_op"] == "false"
    targets = _targets(sel)
    assert RUNTIME_WALLCLOCK_EVIDENCE_EMITTER_FILES[1] in targets
    assert "tests/ops/test_testnet_wallclock_duration_evidence_contract_v0.py" in targets
    assert "tests/ci/test_ci_diff_aware_test_selection_v1.py" not in targets


def test_selector_runtime_wallclock_evidence_emitter_owner_without_test_owner_full() -> None:
    sel = _run_selector(RUNTIME_WALLCLOCK_EVIDENCE_EMITTER_FILES[0])
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert (
        sel["test_selection_reason"]
        == "runtime_wallclock_evidence_emitter_incomplete_or_missing_test_owner"
    )


def test_selector_runtime_wallclock_evidence_emitter_plus_foreign_src_full() -> None:
    sel = _run_selector(
        *RUNTIME_WALLCLOCK_EVIDENCE_EMITTER_FILES,
        "src/execution/live/orchestrator.py",
    )
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert (
        sel["test_selection_reason"]
        == "runtime_wallclock_evidence_emitter_foreign_path_requires_full"
    )


def test_selector_runtime_wallclock_evidence_emitter_plus_dependency_full() -> None:
    sel = _run_selector(*RUNTIME_WALLCLOCK_EVIDENCE_EMITTER_FILES, "requirements.txt")
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert (
        sel["test_selection_reason"]
        == "runtime_wallclock_evidence_emitter_foreign_path_requires_full"
    )


def test_selector_runtime_wallclock_evidence_emitter_four_file_bundle_focused() -> None:
    sel = _run_selector(
        *RUNTIME_WALLCLOCK_EVIDENCE_EMITTER_FILES,
        "scripts/ops/ci_test_selection_v1.py",
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
    )
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert sel["test_selection_reason"] == "runtime_wallclock_evidence_emitter_focused"
    targets = _targets(sel)
    assert RUNTIME_WALLCLOCK_EVIDENCE_EMITTER_FILES[1] in targets
    assert "tests/ops/test_testnet_wallclock_duration_evidence_contract_v0.py" in targets
    assert "tests/ci/test_ci_diff_aware_test_selection_v1.py" not in targets


def test_selector_runtime_wallclock_evidence_emitter_ci_policy_only_not_owner_focused() -> None:
    sel = _run_selector(
        "scripts/ops/ci_test_selection_v1.py",
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
    )
    assert sel["test_selection_reason"] != "runtime_wallclock_evidence_emitter_focused"


def test_selector_runtime_wallclock_evidence_emitter_import_modules() -> None:
    sel = _run_selector(*RUNTIME_WALLCLOCK_EVIDENCE_EMITTER_FILES)
    modules = _modules(sel)
    assert modules == ["src.ops.runtime_wallclock_evidence_emitter_contract_v0"]


def test_selector_bounded_network_preflight_rules_unchanged() -> None:
    sel = _run_selector(*PR4497_BOUNDED_NETWORK_PREFLIGHT_FILES)
    assert sel["test_selection_reason"] == "bounded_network_testnet_preflight_focused"


TESTNET_WALLCLOCK_DURATION_EVIDENCE_FILES: tuple[str, ...] = (
    "src/ops/testnet_wallclock_duration_evidence_contract_v0.py",
    "tests/ops/test_testnet_wallclock_duration_evidence_contract_v0.py",
)


MASTER_V2_ARITHMETIC_KERNEL_SEAM_FAIL_CLOSED_CONTRACT_TEST_OWNER = (
    "tests/ops/test_master_v2_arithmetic_kernel_seam_fail_closed_contract_v0.py"
)


def test_selector_master_v2_arithmetic_kernel_seam_fail_closed_contract_test_only_focused() -> None:
    sel = _run_selector(MASTER_V2_ARITHMETIC_KERNEL_SEAM_FAIL_CLOSED_CONTRACT_TEST_OWNER)
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert (
        sel["test_selection_reason"]
        == "master_v2_arithmetic_kernel_seam_fail_closed_contract_focused"
    )
    assert sel["tests_execute_full"] == "false"
    assert sel["tests_execute_focused"] == "true"
    assert sel["tests_execute_no_op"] == "false"
    targets = _targets(sel)
    assert len([t for t in targets if "::test_" in t]) == 6
    assert (
        f"{MASTER_V2_ARITHMETIC_KERNEL_SEAM_FAIL_CLOSED_CONTRACT_TEST_OWNER}::test_canonical_futures_accounting_kernel_identity_and_decimal_semantics"
        in targets
    )
    assert (
        f"{MASTER_V2_ARITHMETIC_KERNEL_SEAM_FAIL_CLOSED_CONTRACT_TEST_OWNER}::test_future_seam_must_reuse_decimal_kernel_without_formula_duplication"
        in targets
    )
    assert "tests/ci/test_ci_diff_aware_test_selection_v1.py" not in targets


def test_selector_master_v2_arithmetic_kernel_seam_fail_closed_contract_selector_rebundle_focused() -> (
    None
):
    sel = _run_selector(
        MASTER_V2_ARITHMETIC_KERNEL_SEAM_FAIL_CLOSED_CONTRACT_TEST_OWNER,
        "scripts/ops/ci_test_selection_v1.py",
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
    )
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert (
        sel["test_selection_reason"]
        == "master_v2_arithmetic_kernel_seam_fail_closed_contract_focused"
    )
    targets = _targets(sel)
    assert len([t for t in targets if "::test_" in t]) == 8
    assert (
        "tests/ci/test_ci_diff_aware_test_selection_v1.py::test_selector_master_v2_arithmetic_kernel_seam_fail_closed_contract_test_only_focused"
        in targets
    )


def test_selector_master_v2_arithmetic_kernel_seam_fail_closed_contract_foreign_path_escalates_full() -> (
    None
):
    sel = _run_selector(
        MASTER_V2_ARITHMETIC_KERNEL_SEAM_FAIL_CLOSED_CONTRACT_TEST_OWNER,
        "src/trading/master_v2/double_play_state.py",
    )
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert (
        sel["test_selection_reason"]
        == "master_v2_arithmetic_kernel_seam_fail_closed_contract_foreign_path_requires_full"
    )


DUPLICATE_PNL_OWNER_BOUNDARY_CONTRACT_TEST_OWNER = (
    "tests/ops/test_duplicate_pnl_owner_boundary_contract_v0.py"
)


def test_selector_duplicate_pnl_owner_boundary_contract_test_only_focused() -> None:
    sel = _run_selector(DUPLICATE_PNL_OWNER_BOUNDARY_CONTRACT_TEST_OWNER)
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert sel["test_selection_reason"] == "duplicate_pnl_owner_boundary_contract_focused"
    assert sel["tests_execute_full"] == "false"
    assert sel["tests_execute_focused"] == "true"
    assert sel["tests_execute_no_op"] == "false"
    targets = _targets(sel)
    assert len([t for t in targets if "::test_" in t]) == 6
    assert (
        f"{DUPLICATE_PNL_OWNER_BOUNDARY_CONTRACT_TEST_OWNER}::test_exactly_one_futures_arithmetic_kernel_candidate"
        in targets
    )
    assert (
        f"{DUPLICATE_PNL_OWNER_BOUNDARY_CONTRACT_TEST_OWNER}::test_contract_is_non_authorizing"
        in targets
    )
    assert "tests/ci/test_ci_diff_aware_test_selection_v1.py" not in targets


def test_selector_duplicate_pnl_owner_boundary_contract_selector_rebundle_focused() -> None:
    sel = _run_selector(
        DUPLICATE_PNL_OWNER_BOUNDARY_CONTRACT_TEST_OWNER,
        "scripts/ops/ci_test_selection_v1.py",
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
    )
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert sel["test_selection_reason"] == "duplicate_pnl_owner_boundary_contract_focused"
    targets = _targets(sel)
    assert len([t for t in targets if "::test_" in t]) == 8
    assert (
        "tests/ci/test_ci_diff_aware_test_selection_v1.py::test_selector_duplicate_pnl_owner_boundary_contract_test_only_focused"
        in targets
    )


def test_selector_duplicate_pnl_owner_boundary_contract_foreign_path_escalates_full() -> None:
    sel = _run_selector(
        DUPLICATE_PNL_OWNER_BOUNDARY_CONTRACT_TEST_OWNER,
        "src/execution/position_ledger.py",
    )
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert (
        sel["test_selection_reason"]
        == "duplicate_pnl_owner_boundary_contract_foreign_path_requires_full"
    )


RECONCILIATION_DECIMAL_FLOAT_OWNER_BOUNDARY_CONTRACT_TEST_OWNER = (
    "tests/ops/test_reconciliation_decimal_float_owner_boundary_contract_v0.py"
)


def test_selector_reconciliation_decimal_float_owner_boundary_contract_test_only_focused() -> None:
    sel = _run_selector(RECONCILIATION_DECIMAL_FLOAT_OWNER_BOUNDARY_CONTRACT_TEST_OWNER)
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert (
        sel["test_selection_reason"]
        == "reconciliation_decimal_float_owner_boundary_contract_focused"
    )
    assert sel["tests_execute_full"] == "false"
    assert sel["tests_execute_focused"] == "true"
    assert sel["tests_execute_no_op"] == "false"
    targets = _targets(sel)
    assert len([t for t in targets if "::test_" in t]) == 7
    assert (
        f"{RECONCILIATION_DECIMAL_FLOAT_OWNER_BOUNDARY_CONTRACT_TEST_OWNER}::test_exactly_one_execution_decimal_reconciliation_candidate"
        in targets
    )
    assert (
        f"{RECONCILIATION_DECIMAL_FLOAT_OWNER_BOUNDARY_CONTRACT_TEST_OWNER}::test_contract_defines_no_reconciliation_formulas_and_is_non_authorizing"
        in targets
    )
    assert "tests/ci/test_ci_diff_aware_test_selection_v1.py" not in targets


def test_selector_reconciliation_decimal_float_owner_boundary_contract_selector_rebundle_focused() -> (
    None
):
    sel = _run_selector(
        RECONCILIATION_DECIMAL_FLOAT_OWNER_BOUNDARY_CONTRACT_TEST_OWNER,
        "scripts/ops/ci_test_selection_v1.py",
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
    )
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert (
        sel["test_selection_reason"]
        == "reconciliation_decimal_float_owner_boundary_contract_focused"
    )
    targets = _targets(sel)
    assert len([t for t in targets if "::test_" in t]) == 9
    assert (
        "tests/ci/test_ci_diff_aware_test_selection_v1.py::test_selector_reconciliation_decimal_float_owner_boundary_contract_test_only_focused"
        in targets
    )


def test_selector_reconciliation_decimal_float_owner_boundary_contract_foreign_path_escalates_full() -> (
    None
):
    sel = _run_selector(
        RECONCILIATION_DECIMAL_FLOAT_OWNER_BOUNDARY_CONTRACT_TEST_OWNER,
        "src/execution/reconciliation.py",
    )
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert (
        sel["test_selection_reason"]
        == "reconciliation_decimal_float_owner_boundary_contract_foreign_path_requires_full"
    )


DYNAMIC_SCOPE_OWNER_BOUNDARY_CONTRACT_TEST_OWNER = (
    "tests/ops/test_master_v2_dynamic_scope_owner_boundary_contract_v0.py"
)


def test_selector_dynamic_scope_owner_boundary_contract_test_only_focused() -> None:
    sel = _run_selector(DYNAMIC_SCOPE_OWNER_BOUNDARY_CONTRACT_TEST_OWNER)
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert sel["test_selection_reason"] == "dynamic_scope_owner_boundary_contract_focused"
    assert sel["tests_execute_full"] == "false"
    assert sel["tests_execute_focused"] == "true"
    assert sel["tests_execute_no_op"] == "false"
    targets = _targets(sel)
    assert len([t for t in targets if "::test_" in t]) == 7
    assert (
        f"{DYNAMIC_SCOPE_OWNER_BOUNDARY_CONTRACT_TEST_OWNER}::test_exactly_one_dynamic_scope_pure_model_candidate"
        in targets
    )
    assert (
        f"{DYNAMIC_SCOPE_OWNER_BOUNDARY_CONTRACT_TEST_OWNER}::test_forbidden_authority_and_repair_claim_keys_absent"
        in targets
    )
    assert "tests/ci/test_ci_diff_aware_test_selection_v1.py" not in targets


def test_selector_dynamic_scope_owner_boundary_contract_selector_rebundle_focused() -> None:
    sel = _run_selector(
        DYNAMIC_SCOPE_OWNER_BOUNDARY_CONTRACT_TEST_OWNER,
        "scripts/ops/ci_test_selection_v1.py",
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
    )
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert sel["test_selection_reason"] == "dynamic_scope_owner_boundary_contract_focused"
    targets = _targets(sel)
    assert len([t for t in targets if "::test_" in t]) == 9
    assert (
        "tests/ci/test_ci_diff_aware_test_selection_v1.py::test_selector_dynamic_scope_owner_boundary_contract_test_only_focused"
        in targets
    )


def test_selector_dynamic_scope_owner_boundary_contract_foreign_path_escalates_full() -> None:
    sel = _run_selector(
        DYNAMIC_SCOPE_OWNER_BOUNDARY_CONTRACT_TEST_OWNER,
        "src/trading/master_v2/double_play_state.py",
    )
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert (
        sel["test_selection_reason"]
        == "dynamic_scope_owner_boundary_contract_foreign_path_requires_full"
    )


STATE_SWITCH_OWNER_BOUNDARY_CONTRACT_TEST_OWNER = (
    "tests/ops/test_master_v2_state_switch_owner_boundary_contract_v0.py"
)


def test_selector_state_switch_owner_boundary_contract_test_only_focused() -> None:
    sel = _run_selector(STATE_SWITCH_OWNER_BOUNDARY_CONTRACT_TEST_OWNER)
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert sel["test_selection_reason"] == "state_switch_owner_boundary_contract_focused"
    assert sel["tests_execute_full"] == "false"
    assert sel["tests_execute_focused"] == "true"
    assert sel["tests_execute_no_op"] == "false"
    targets = _targets(sel)
    assert len([t for t in targets if "::test_" in t]) == 7
    assert (
        f"{STATE_SWITCH_OWNER_BOUNDARY_CONTRACT_TEST_OWNER}::test_exactly_one_state_switch_pure_model_candidate"
        in targets
    )
    assert (
        f"{STATE_SWITCH_OWNER_BOUNDARY_CONTRACT_TEST_OWNER}::test_forbidden_authority_and_side_switch_claim_keys_absent"
        in targets
    )
    assert "tests/ci/test_ci_diff_aware_test_selection_v1.py" not in targets


def test_selector_state_switch_owner_boundary_contract_selector_rebundle_focused() -> None:
    sel = _run_selector(
        STATE_SWITCH_OWNER_BOUNDARY_CONTRACT_TEST_OWNER,
        "scripts/ops/ci_test_selection_v1.py",
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
    )
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert sel["test_selection_reason"] == "state_switch_owner_boundary_contract_focused"
    targets = _targets(sel)
    assert len([t for t in targets if "::test_" in t]) == 9
    assert (
        "tests/ci/test_ci_diff_aware_test_selection_v1.py::test_selector_state_switch_owner_boundary_contract_test_only_focused"
        in targets
    )


def test_selector_state_switch_owner_boundary_contract_foreign_path_escalates_full() -> None:
    sel = _run_selector(
        STATE_SWITCH_OWNER_BOUNDARY_CONTRACT_TEST_OWNER,
        "src/trading/master_v2/double_play_state.py",
    )
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert (
        sel["test_selection_reason"]
        == "state_switch_owner_boundary_contract_foreign_path_requires_full"
    )


CAPITAL_SLOT_OWNER_BOUNDARY_CONTRACT_TEST_OWNER = (
    "tests/ops/test_master_v2_capital_slot_owner_boundary_contract_v0.py"
)


def test_selector_capital_slot_owner_boundary_contract_test_only_focused() -> None:
    sel = _run_selector(CAPITAL_SLOT_OWNER_BOUNDARY_CONTRACT_TEST_OWNER)
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert sel["test_selection_reason"] == "capital_slot_owner_boundary_contract_focused"
    assert sel["tests_execute_full"] == "false"
    assert sel["tests_execute_focused"] == "true"
    assert sel["tests_execute_no_op"] == "false"
    targets = _targets(sel)
    assert len([t for t in targets if "::test_" in t]) == 7
    assert (
        f"{CAPITAL_SLOT_OWNER_BOUNDARY_CONTRACT_TEST_OWNER}::test_exactly_one_capital_slot_pure_model_candidate"
        in targets
    )
    assert (
        f"{CAPITAL_SLOT_OWNER_BOUNDARY_CONTRACT_TEST_OWNER}::test_forbidden_authority_and_ratchet_claim_keys_absent"
        in targets
    )
    assert "tests/ci/test_ci_diff_aware_test_selection_v1.py" not in targets


def test_selector_capital_slot_owner_boundary_contract_selector_rebundle_focused() -> None:
    sel = _run_selector(
        CAPITAL_SLOT_OWNER_BOUNDARY_CONTRACT_TEST_OWNER,
        "scripts/ops/ci_test_selection_v1.py",
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
    )
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert sel["test_selection_reason"] == "capital_slot_owner_boundary_contract_focused"
    targets = _targets(sel)
    assert len([t for t in targets if "::test_" in t]) == 9
    assert (
        "tests/ci/test_ci_diff_aware_test_selection_v1.py::test_selector_capital_slot_owner_boundary_contract_test_only_focused"
        in targets
    )


def test_selector_capital_slot_owner_boundary_contract_foreign_path_escalates_full() -> None:
    sel = _run_selector(
        CAPITAL_SLOT_OWNER_BOUNDARY_CONTRACT_TEST_OWNER,
        "src/trading/master_v2/double_play_capital_slot.py",
    )
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert (
        sel["test_selection_reason"]
        == "capital_slot_owner_boundary_contract_foreign_path_requires_full"
    )


PE22_DURABLE_COMPLETION_BINDING_CONTRACT_TEST_OWNER = (
    "tests/ops/test_pe22_durable_completion_binding_contract_v0.py"
)

PE22_DURABLE_COMPLETION_BINDING_NODE_IDS = (
    "test_pe22_durable_completion_binding_package_marker_present",
    "test_pe22_durable_completion_canonical_binding_registry_complete",
    "test_pe22_durable_completion_registry_upstream_owner_matches_pe22_contract",
    "test_pe22_durable_completion_dependency_direction_is_downstream_only",
    "test_pe22_durable_completion_sole_canonical_upstream_module_in_completion_facade",
    "test_pe22_durable_completion_completion_chain_validator_imports_canonical_pe22_owner_only",
    "test_pe22_durable_completion_binding_authority_neutral_on_happy_path",
    "test_pe22_source_revision_mismatch_with_completion_input_fails",
    "test_pe22_integration_input_digest_drift_fails",
    "test_pe22_integration_owner_mismatch_fails",
    "test_pe22_referenced_upstream_digest_drift_in_completion_chain_fails",
    "test_pe22_completion_binding_source_revision_consistent_on_happy_path",
    "test_graph_pe22_canonical_binding_registry_aligns_with_integration_owner",
    "test_graph_completion_chain_validator_imports_canonical_pe22_owner_only",
    "test_graph_completion_chain_validator_is_canonical_pe22_binding_entrypoint",
    "test_graph_pe22_binding_authority_neutral_on_happy_path",
    "test_graph_pe22_source_revision_drift_fail_closed_via_completion_chain_validator",
    "test_graph_pe22_integration_input_digest_drift_fail_closed",
    "test_graph_pe22_referenced_proof_digest_drift_in_completion_chain_fail_closed",
    "test_graph_pe22_completion_chain_digest_alignment_fail_closed",
)


def test_selector_pe22_durable_completion_binding_contract_test_only_focused() -> None:
    sel = _run_selector(PE22_DURABLE_COMPLETION_BINDING_CONTRACT_TEST_OWNER)
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert sel["test_selection_reason"] == "pe22_durable_completion_binding_focused"
    assert sel["tests_execute_full"] == "false"
    assert sel["tests_execute_focused"] == "true"
    assert sel["tests_execute_no_op"] == "false"
    assert "pe31_durable_completion_binding" not in sel["test_selection_reason"]
    targets = _targets(sel)
    assert len([t for t in targets if "::test_" in t]) == 20
    for node_id in PE22_DURABLE_COMPLETION_BINDING_NODE_IDS:
        assert any(t.endswith(f"::{node_id}") for t in targets), node_id
    assert (
        f"{PE22_DURABLE_COMPLETION_BINDING_CONTRACT_TEST_OWNER}::test_pe22_durable_completion_binding_authority_neutral_on_happy_path"
        in targets
    )
    assert "tests/ci/test_ci_diff_aware_test_selection_v1.py" not in targets


def test_selector_pe22_durable_completion_binding_contract_foreign_path_escalates_full() -> None:
    sel = _run_selector(
        PE22_DURABLE_COMPLETION_BINDING_CONTRACT_TEST_OWNER,
        "src/ops/bounded_futures_testnet_pilot_envelope_lifecycle_integration_contract_v0.py",
    )
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert (
        sel["test_selection_reason"] == "pe22_durable_completion_binding_foreign_path_requires_full"
    )
    assert "pe31_durable_completion_binding" not in sel["test_selection_reason"]


INV016_DURABLE_COMPLETION_BINDING_CONTRACT_TEST_OWNER = (
    "tests/ops/test_inv016_durable_completion_binding_contract_v0.py"
)

INV016_DURABLE_COMPLETION_BINDING_NODE_IDS = (
    "test_inv016_durable_completion_binding_package_marker_present",
    "test_inv016_durable_completion_canonical_binding_registry_complete",
    "test_inv016_durable_completion_registry_upstream_owner_matches_inv016_contract",
    "test_inv016_durable_completion_dependency_direction_is_downstream_only",
    "test_inv016_durable_completion_sole_canonical_completion_facade_import_in_wiring_owner",
    "test_inv016_durable_completion_completion_chain_validator_references_inv016_digest_fields",
    "test_inv016_durable_completion_binding_authority_neutral_on_happy_path",
    "test_inv016_missing_market_input_fails_closed",
    "test_inv016_dashboard_display_projection_digest_drift_fails_closed",
    "test_inv016_replay_proof_classification_not_full_e2e_fails_closed",
    "test_inv016_canonical_completion_owner_reference_consistent_on_happy_path",
    "test_graph_inv016_canonical_binding_registry_aligns_with_wiring_owner",
    "test_graph_completion_chain_validator_imports_master_v2_digest_binding_only",
    "test_graph_completion_chain_validator_is_canonical_inv016_binding_entrypoint",
    "test_graph_inv016_binding_authority_neutral_on_happy_path",
    "test_graph_inv016_dashboard_display_projection_digest_drift_fail_closed",
    "test_graph_inv016_completion_chain_master_v2_digest_alignment_fail_closed",
    "test_inv016_f1_contract_only_scope_without_package_f_complete",
    "test_inv016_f2_inv017_and_inv005_runtime_parking_unchanged",
    "test_inv016_no_runtime_network_credential_or_trading_readiness_claimed",
)


def test_selector_inv016_durable_completion_binding_contract_test_only_focused() -> None:
    sel = _run_selector(INV016_DURABLE_COMPLETION_BINDING_CONTRACT_TEST_OWNER)
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert sel["test_selection_reason"] == "inv016_durable_completion_binding_focused"
    assert sel["tests_execute_full"] == "false"
    assert sel["tests_execute_focused"] == "true"
    assert sel["tests_execute_no_op"] == "false"
    assert "pe22_durable_completion_binding" not in sel["test_selection_reason"]
    assert "pe31_durable_completion_binding" not in sel["test_selection_reason"]
    targets = _targets(sel)
    assert len([t for t in targets if "::test_" in t]) == 20
    for node_id in INV016_DURABLE_COMPLETION_BINDING_NODE_IDS:
        assert any(t.endswith(f"::{node_id}") for t in targets), node_id
    assert (
        f"{INV016_DURABLE_COMPLETION_BINDING_CONTRACT_TEST_OWNER}::test_inv016_durable_completion_binding_authority_neutral_on_happy_path"
        in targets
    )
    assert "tests/ci/test_ci_diff_aware_test_selection_v1.py" not in targets


def test_selector_inv016_durable_completion_binding_contract_foreign_path_escalates_full() -> None:
    sel = _run_selector(
        INV016_DURABLE_COMPLETION_BINDING_CONTRACT_TEST_OWNER,
        "src/ops/bounded_futures_testnet_pilot_envelope_lifecycle_integration_contract_v0.py",
    )
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert (
        sel["test_selection_reason"]
        == "inv016_durable_completion_binding_foreign_path_requires_full"
    )
    assert "pe22_durable_completion_binding" not in sel["test_selection_reason"]


MASTER_V2_ARITHMETIC_DECIMAL_FLOAT_CONVERSION_BOUNDARY_CONTRACT_TEST_OWNER = (
    "tests/ops/test_master_v2_arithmetic_decimal_float_conversion_boundary_contract_v0.py"
)


def test_selector_master_v2_arithmetic_decimal_float_conversion_boundary_contract_test_only_focused() -> (
    None
):
    sel = _run_selector(MASTER_V2_ARITHMETIC_DECIMAL_FLOAT_CONVERSION_BOUNDARY_CONTRACT_TEST_OWNER)
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert (
        sel["test_selection_reason"]
        == "master_v2_arithmetic_decimal_float_conversion_boundary_contract_focused"
    )
    assert sel["tests_execute_full"] == "false"
    assert sel["tests_execute_focused"] == "true"
    assert sel["tests_execute_no_op"] == "false"
    targets = _targets(sel)
    assert len([t for t in targets if "::test_" in t]) == 8
    assert (
        f"{MASTER_V2_ARITHMETIC_DECIMAL_FLOAT_CONVERSION_BOUNDARY_CONTRACT_TEST_OWNER}::test_to_decimal_exists_but_is_not_complete_master_v2_seam_contract"
        in targets
    )
    assert (
        f"{MASTER_V2_ARITHMETIC_DECIMAL_FLOAT_CONVERSION_BOUNDARY_CONTRACT_TEST_OWNER}::test_no_current_kernel_binding_and_contract_is_non_authorizing"
        in targets
    )
    assert "tests/ci/test_ci_diff_aware_test_selection_v1.py" not in targets


def test_selector_master_v2_arithmetic_decimal_float_conversion_boundary_contract_selector_rebundle_focused() -> (
    None
):
    sel = _run_selector(
        MASTER_V2_ARITHMETIC_DECIMAL_FLOAT_CONVERSION_BOUNDARY_CONTRACT_TEST_OWNER,
        "scripts/ops/ci_test_selection_v1.py",
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
    )
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert (
        sel["test_selection_reason"]
        == "master_v2_arithmetic_decimal_float_conversion_boundary_contract_focused"
    )
    targets = _targets(sel)
    assert len([t for t in targets if "::test_" in t]) == 10
    assert (
        "tests/ci/test_ci_diff_aware_test_selection_v1.py::test_selector_master_v2_arithmetic_decimal_float_conversion_boundary_contract_test_only_focused"
        in targets
    )


def test_selector_master_v2_arithmetic_decimal_float_conversion_boundary_contract_foreign_path_escalates_full() -> (
    None
):
    sel = _run_selector(
        MASTER_V2_ARITHMETIC_DECIMAL_FLOAT_CONVERSION_BOUNDARY_CONTRACT_TEST_OWNER,
        "src/execution/paper/futures_accounting.py",
    )
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert (
        sel["test_selection_reason"]
        == "master_v2_arithmetic_decimal_float_conversion_boundary_contract_foreign_path_requires_full"
    )


MASTER_V2_ARITHMETIC_DECIMAL_FLOAT_CONVERSION_IMPLEMENTATION_PRODUCTION_PATH = (
    "src/trading/master_v2/arithmetic_decimal_float_conversion_v0.py"
)
MASTER_V2_ARITHMETIC_DECIMAL_FLOAT_CONVERSION_IMPLEMENTATION_TEST_OWNER = (
    "tests/ops/test_master_v2_arithmetic_decimal_float_conversion_implementation_v0.py"
)


def test_selector_master_v2_arithmetic_decimal_float_conversion_implementation_test_only_focused() -> (
    None
):
    sel = _run_selector(MASTER_V2_ARITHMETIC_DECIMAL_FLOAT_CONVERSION_IMPLEMENTATION_TEST_OWNER)
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert (
        sel["test_selection_reason"]
        == "master_v2_arithmetic_decimal_float_conversion_implementation_focused"
    )
    assert sel["tests_execute_full"] == "false"
    assert sel["tests_execute_focused"] == "true"
    assert sel["tests_execute_no_op"] == "false"
    targets = _targets(sel)
    assert len([t for t in targets if "::test_" in t]) == 26
    assert (
        f"{MASTER_V2_ARITHMETIC_DECIMAL_FLOAT_CONVERSION_IMPLEMENTATION_TEST_OWNER}::test_deterministic_decimal_no_float_leakage"
        in targets
    )
    assert (
        f"{MASTER_V2_ARITHMETIC_DECIMAL_FLOAT_CONVERSION_IMPLEMENTATION_TEST_OWNER}::test_immutable_non_authorizing_no_wiring"
        in targets
    )
    assert "tests/ci/test_ci_diff_aware_test_selection_v1.py" not in targets


def test_selector_master_v2_arithmetic_decimal_float_conversion_implementation_selector_rebundle_focused() -> (
    None
):
    sel = _run_selector(
        MASTER_V2_ARITHMETIC_DECIMAL_FLOAT_CONVERSION_IMPLEMENTATION_PRODUCTION_PATH,
        MASTER_V2_ARITHMETIC_DECIMAL_FLOAT_CONVERSION_IMPLEMENTATION_TEST_OWNER,
        "scripts/ops/ci_test_selection_v1.py",
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
    )
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert (
        sel["test_selection_reason"]
        == "master_v2_arithmetic_decimal_float_conversion_implementation_focused"
    )
    targets = _targets(sel)
    assert len([t for t in targets if "::test_" in t]) == 28
    assert (
        "tests/ci/test_ci_diff_aware_test_selection_v1.py::test_selector_master_v2_arithmetic_decimal_float_conversion_implementation_test_only_focused"
        in targets
    )


def test_selector_master_v2_arithmetic_decimal_float_conversion_implementation_foreign_path_escalates_full() -> (
    None
):
    sel = _run_selector(
        MASTER_V2_ARITHMETIC_DECIMAL_FLOAT_CONVERSION_IMPLEMENTATION_PRODUCTION_PATH,
        "src/execution/paper/futures_accounting.py",
    )
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert (
        sel["test_selection_reason"]
        == "master_v2_arithmetic_decimal_float_conversion_implementation_foreign_path_requires_full"
    )


def test_selector_testnet_wallclock_duration_evidence_owner_pair_focused() -> None:
    sel = _run_selector(*TESTNET_WALLCLOCK_DURATION_EVIDENCE_FILES)
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert sel["test_selection_reason"] == "testnet_wallclock_duration_evidence_focused"
    assert sel["tests_execute_full"] == "false"
    assert sel["tests_execute_focused"] == "true"
    assert sel["tests_execute_no_op"] == "false"
    targets = _targets(sel)
    assert TESTNET_WALLCLOCK_DURATION_EVIDENCE_FILES[1] in targets
    assert "tests/ci/test_ci_diff_aware_test_selection_v1.py" not in targets


def test_selector_testnet_wallclock_duration_evidence_owner_without_test_owner_full() -> None:
    sel = _run_selector(TESTNET_WALLCLOCK_DURATION_EVIDENCE_FILES[0])
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert (
        sel["test_selection_reason"]
        == "testnet_wallclock_duration_evidence_incomplete_or_missing_test_owner"
    )


def test_selector_testnet_wallclock_duration_evidence_plus_foreign_src_full() -> None:
    sel = _run_selector(
        *TESTNET_WALLCLOCK_DURATION_EVIDENCE_FILES,
        "src/execution/live/orchestrator.py",
    )
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert (
        sel["test_selection_reason"]
        == "testnet_wallclock_duration_evidence_foreign_path_requires_full"
    )


def test_selector_testnet_wallclock_duration_evidence_plus_dependency_full() -> None:
    sel = _run_selector(*TESTNET_WALLCLOCK_DURATION_EVIDENCE_FILES, "requirements.txt")
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert (
        sel["test_selection_reason"]
        == "testnet_wallclock_duration_evidence_foreign_path_requires_full"
    )


def test_selector_testnet_wallclock_duration_evidence_four_file_bundle_focused() -> None:
    sel = _run_selector(
        *TESTNET_WALLCLOCK_DURATION_EVIDENCE_FILES,
        "scripts/ops/ci_test_selection_v1.py",
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
    )
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert sel["test_selection_reason"] == "testnet_wallclock_duration_evidence_focused"
    targets = _targets(sel)
    assert TESTNET_WALLCLOCK_DURATION_EVIDENCE_FILES[1] in targets
    assert "tests/ci/test_ci_diff_aware_test_selection_v1.py" not in targets


def test_selector_testnet_wallclock_duration_evidence_ci_policy_only_not_owner_focused() -> None:
    sel = _run_selector(
        "scripts/ops/ci_test_selection_v1.py",
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
    )
    assert sel["test_selection_reason"] != "testnet_wallclock_duration_evidence_focused"


def test_selector_testnet_wallclock_duration_evidence_import_modules() -> None:
    sel = _run_selector(*TESTNET_WALLCLOCK_DURATION_EVIDENCE_FILES)
    modules = _modules(sel)
    assert modules == ["src.ops.testnet_wallclock_duration_evidence_contract_v0"]


def test_selector_runtime_wallclock_evidence_emitter_rules_unchanged() -> None:
    sel = _run_selector(*RUNTIME_WALLCLOCK_EVIDENCE_EMITTER_FILES)
    assert sel["test_selection_reason"] == "runtime_wallclock_evidence_emitter_focused"


WALLCLOCK_FIELD_NAME_PAIRED_REWIRE_FILES: tuple[str, ...] = (
    "tests/ops/test_testnet_wallclock_duration_evidence_contract_v0.py",
    "tests/ops/test_shadow_wallclock_duration_evidence_contract_v0.py",
)

SHADOW_WALLCLOCK_DURATION_EVIDENCE_TEST_OWNER = (
    "tests/ops/test_shadow_wallclock_duration_evidence_contract_v0.py"
)


def test_selector_wallclock_field_name_paired_rewire_exact_pair_no_op() -> None:
    sel = _run_selector(*WALLCLOCK_FIELD_NAME_PAIRED_REWIRE_FILES)
    assert sel["test_selection_mode"] == "NO_OP"
    assert sel["test_selection_reason"] == "wallclock_field_name_paired_rewire_no_op"
    assert sel["tests_execute_full"] == "false"
    assert sel["tests_execute_focused"] == "false"
    assert sel["tests_execute_no_op"] == "true"
    assert _targets(sel) == []


def test_selector_wallclock_field_name_paired_rewire_not_broad_tests_ops_selection() -> None:
    sel = _run_selector(*WALLCLOCK_FIELD_NAME_PAIRED_REWIRE_FILES)
    assert sel["test_selection_reason"] != "focused_script_or_test_diff"
    assert "tests/ops/test_run_shadow_bounded_observation_adapter_v0.py" not in _targets(sel)


def test_selector_wallclock_field_name_paired_rewire_testnet_only_unchanged() -> None:
    sel = _run_selector(WALLCLOCK_FIELD_NAME_PAIRED_REWIRE_FILES[0])
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert sel["test_selection_reason"] == "testnet_wallclock_duration_evidence_focused"


def test_selector_wallclock_field_name_paired_rewire_shadow_only_unchanged() -> None:
    sel = _run_selector(SHADOW_WALLCLOCK_DURATION_EVIDENCE_TEST_OWNER)
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert sel["test_selection_reason"] == "wallclock_focused"


def test_selector_wallclock_field_name_paired_rewire_plus_foreign_test_full() -> None:
    sel = _run_selector(
        *WALLCLOCK_FIELD_NAME_PAIRED_REWIRE_FILES,
        "tests/ops/test_bounded_network_testnet_preflight_contract_v0.py",
    )
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert sel["tests_execute_pr_bounded_full"] == "true"
    assert sel["tests_execute_full"] == "false"
    assert sel["test_selection_reason"] != "wallclock_field_name_paired_rewire_no_op"


def test_selector_wallclock_field_name_paired_rewire_plus_src_full() -> None:
    sel = _run_selector(
        *WALLCLOCK_FIELD_NAME_PAIRED_REWIRE_FILES,
        "src/ops/testnet_wallclock_duration_evidence_contract_v0.py",
    )
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert (
        sel["test_selection_reason"]
        == "testnet_wallclock_duration_evidence_foreign_path_requires_full"
    )


def test_selector_wallclock_field_name_paired_rewire_plus_dependency_full() -> None:
    sel = _run_selector(*WALLCLOCK_FIELD_NAME_PAIRED_REWIRE_FILES, "requirements.txt")
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert (
        sel["test_selection_reason"]
        == "testnet_wallclock_duration_evidence_foreign_path_requires_full"
    )


def test_selector_wallclock_field_name_paired_rewire_plus_third_wallclock_test_full() -> None:
    sel = _run_selector(
        *WALLCLOCK_FIELD_NAME_PAIRED_REWIRE_FILES,
        "tests/ops/test_runtime_wallclock_evidence_emitter_contract_v0.py",
    )
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert sel["tests_execute_pr_bounded_full"] == "true"
    assert sel["tests_execute_full"] == "false"
    assert sel["test_selection_reason"] != "wallclock_field_name_paired_rewire_no_op"


def test_selector_wallclock_field_name_paired_rewire_testnet_wallclock_rules_unchanged() -> None:
    sel = _run_selector(*TESTNET_WALLCLOCK_DURATION_EVIDENCE_FILES)
    assert sel["test_selection_reason"] == "testnet_wallclock_duration_evidence_focused"


def test_selector_wallclock_field_name_paired_rewire_shadow_wallclock_rules_unchanged() -> None:
    sel = _run_selector(*PR4489_WALLCLOCK_FILES)
    assert sel["test_selection_reason"] == "wallclock_focused"


def test_selector_ci_fix_diff_ci_bootstrap_focused() -> None:
    sel = _run_selector(
        "scripts/ops/ci_test_selection_v1.py",
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
    )
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert sel["test_selection_reason"] == "ci_bootstrap_focused"
    assert sel["tests_execute_full"] == "false"


_CURSOR_AUTO_PR_WORKFLOW = ".github/workflows/cursor_auto_pr.yml"
_LIVENESS_WORKFLOW = ".github/workflows/pr-head-sha-required-checks-liveness-guard.yml"
_CURSOR_AUTO_PR_TEST = "tests/ci/test_cursor_auto_pr_pre_pr_validation_enforcement_contract_v0.py"
_LIVENESS_TEST = "tests/ci/test_pr_head_sha_required_checks_liveness_guard.py"
_PR4548_WORKFLOW_CONTRACT_FILES = (
    _CURSOR_AUTO_PR_WORKFLOW,
    _LIVENESS_WORKFLOW,
    _CURSOR_AUTO_PR_TEST,
    _LIVENESS_TEST,
)


def _fast_lane_targets(sel: dict[str, str]) -> list[str]:
    raw = sel.get("fast_lane_contract_pytest_targets", "")
    return sorted(raw.split()) if raw else []


def test_fast_lane_contract_pr4548_workflow_diff_contract_focused() -> None:
    sel = _run_selector(*_PR4548_WORKFLOW_CONTRACT_FILES)
    assert sel["fast_lane_contract_mode"] == "CONTRACT_FOCUSED"
    assert sel["fast_lane_contract_reason"] == "workflow_contract_owner_map_complete"
    assert _fast_lane_targets(sel) == sorted([_CURSOR_AUTO_PR_TEST, _LIVENESS_TEST])


def test_fast_lane_contract_pr4548_rebundle_with_wiring_contract_focused() -> None:
    sel = _run_selector(
        *_PR4548_WORKFLOW_CONTRACT_FILES,
        ".github/workflows/ci.yml",
        "scripts/ops/ci_test_selection_v1.py",
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
    )
    assert sel["fast_lane_contract_mode"] == "CONTRACT_FOCUSED"
    assert _fast_lane_targets(sel) == sorted([_CURSOR_AUTO_PR_TEST, _LIVENESS_TEST])


def test_fast_lane_contract_cursor_auto_pr_only_contract_focused() -> None:
    sel = _run_selector(_CURSOR_AUTO_PR_WORKFLOW, _CURSOR_AUTO_PR_TEST)
    assert sel["fast_lane_contract_mode"] == "CONTRACT_FOCUSED"
    assert _fast_lane_targets(sel) == [_CURSOR_AUTO_PR_TEST]


def test_fast_lane_contract_liveness_only_contract_focused() -> None:
    sel = _run_selector(_LIVENESS_WORKFLOW, _LIVENESS_TEST)
    assert sel["fast_lane_contract_mode"] == "CONTRACT_FOCUSED"
    assert _fast_lane_targets(sel) == [_LIVENESS_TEST]


def test_fast_lane_contract_unknown_workflow_fail_closed_full() -> None:
    sel = _run_selector(".github/workflows/unknown_workflow.yml")
    assert sel["fast_lane_contract_mode"] == "FULL_STATIC_CONTRACTS"


def test_fast_lane_contract_selector_only_fail_closed_full() -> None:
    sel = _run_selector("scripts/ops/ci_test_selection_v1.py")
    assert sel["fast_lane_contract_mode"] == "FULL_STATIC_CONTRACTS"


def test_fast_lane_contract_ci_yml_only_fail_closed_full() -> None:
    sel = _run_selector(".github/workflows/ci.yml")
    assert sel["fast_lane_contract_mode"] == "FULL_STATIC_CONTRACTS"


def test_fast_lane_contract_mixed_workflow_and_src_fail_closed_full() -> None:
    sel = _run_selector(_CURSOR_AUTO_PR_WORKFLOW, "src/ops/example.py")
    assert sel["fast_lane_contract_mode"] == "FULL_STATIC_CONTRACTS"


def test_fast_lane_contract_docs_only_no_op() -> None:
    sel = _run_selector("docs/README.md")
    assert sel["fast_lane_contract_mode"] == "NO_OP"


def test_fast_lane_contract_selection_order_independent() -> None:
    files = list(_PR4548_WORKFLOW_CONTRACT_FILES)
    sel_a = _run_selector(*files)
    sel_b = _run_selector(*reversed(files))
    assert sel_a["fast_lane_contract_mode"] == sel_b["fast_lane_contract_mode"]
    assert _fast_lane_targets(sel_a) == _fast_lane_targets(sel_b)


def _matrix_targets(sel: dict[str, str]) -> list[str]:
    raw = sel.get("matrix_contract_pytest_targets", "")
    return sorted(raw.split()) if raw else []


_PR4548_MATRIX_REBUNDLE_FILES = (
    ".github/workflows/ci.yml",
    ".github/workflows/cursor_auto_pr.yml",
    ".github/workflows/pr-head-sha-required-checks-liveness-guard.yml",
    "scripts/ops/ci_test_selection_v1.py",
    "tests/ci/test_ci_diff_aware_test_selection_v1.py",
    _CURSOR_AUTO_PR_TEST,
    _LIVENESS_TEST,
)

_PR4548_MATRIX_EXPECTED_TARGETS = sorted(
    [
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
        _CURSOR_AUTO_PR_TEST,
        _LIVENESS_TEST,
    ]
)


def test_matrix_contract_pr4548_full_rebundle_contract_focused() -> None:
    sel = _run_selector(*_PR4548_MATRIX_REBUNDLE_FILES)
    assert sel["matrix_contract_mode"] == "MATRIX_CONTRACT_FOCUSED"
    assert sel["matrix_contract_reason"] == "matrix_contract_rebundle_complete"
    assert sel["matrix_contract_rebundle_id"] == "ci_workflow_selector_contract_rebundle_v1"
    assert sel["tests_execute_matrix_contract_focused"] == "true"
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert sel["tests_execute_pr_bounded_full"] == "true"
    assert _matrix_targets(sel) == _PR4548_MATRIX_EXPECTED_TARGETS


def test_matrix_contract_cursor_auto_pr_only_contract_focused() -> None:
    sel = _run_selector(_CURSOR_AUTO_PR_WORKFLOW, _CURSOR_AUTO_PR_TEST)
    assert sel["matrix_contract_mode"] == "MATRIX_CONTRACT_FOCUSED"
    assert _matrix_targets(sel) == [_CURSOR_AUTO_PR_TEST]


def test_matrix_contract_liveness_only_contract_focused() -> None:
    sel = _run_selector(_LIVENESS_WORKFLOW, _LIVENESS_TEST)
    assert sel["matrix_contract_mode"] == "MATRIX_CONTRACT_FOCUSED"
    assert _matrix_targets(sel) == [_LIVENESS_TEST]


def test_matrix_contract_both_workflow_groups_contract_focused() -> None:
    sel = _run_selector(*_PR4548_WORKFLOW_CONTRACT_FILES)
    assert sel["matrix_contract_mode"] == "MATRIX_CONTRACT_FOCUSED"
    assert _matrix_targets(sel) == sorted([_CURSOR_AUTO_PR_TEST, _LIVENESS_TEST])


def test_matrix_contract_unknown_extra_path_full() -> None:
    sel = _run_selector(*_PR4548_MATRIX_REBUNDLE_FILES, "misc/unmapped.bin")
    assert sel["matrix_contract_mode"] == "MATRIX_UNMAPPED"
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"


def test_matrix_contract_production_path_full() -> None:
    sel = _run_selector(*_PR4548_MATRIX_REBUNDLE_FILES, "src/core/foo.py")
    assert sel["matrix_contract_mode"] == "MATRIX_UNMAPPED"
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"


def test_matrix_contract_dependency_path_full() -> None:
    sel = _run_selector(*_PR4548_MATRIX_REBUNDLE_FILES, "requirements.txt")
    assert sel["matrix_contract_mode"] == "MATRIX_UNMAPPED"
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"


def test_matrix_contract_shared_fixture_path_full() -> None:
    sel = _run_selector(*_PR4548_MATRIX_REBUNDLE_FILES, "tests/fixtures/example.json")
    assert sel["matrix_contract_mode"] == "MATRIX_UNMAPPED"
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"


def test_matrix_contract_selector_without_selector_test_full() -> None:
    sel = _run_selector(
        "scripts/ops/ci_test_selection_v1.py",
        ".github/workflows/ci.yml",
    )
    assert sel["matrix_contract_mode"] == "MATRIX_UNMAPPED"
    assert sel["matrix_contract_reason"] == "matrix_contract_central_wiring_defer_to_ci_infra"
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"


def test_matrix_contract_ci_yml_without_selector_test_unmapped() -> None:
    sel = _run_selector(".github/workflows/ci.yml")
    assert sel["matrix_contract_mode"] == "MATRIX_UNMAPPED"
    assert sel["matrix_contract_reason"] == "matrix_contract_central_wiring_defer_to_ci_infra"


def test_matrix_contract_ci_infra_subset_not_overridden() -> None:
    sel = _run_selector(
        ".github/workflows/ci.yml",
        "scripts/ops/ci_test_selection_v1.py",
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
    )
    assert sel["matrix_contract_mode"] == "MATRIX_UNMAPPED"
    assert sel["test_selection_reason"] == "selector_self_change_bootstrap"
    assert "tests/ci/test_ci_diff_aware_test_selection_v1.py" in sel["pr_bounded_pytest_targets"]


def test_matrix_contract_workflow_without_test_owner_full() -> None:
    sel = _run_selector(_CURSOR_AUTO_PR_WORKFLOW)
    assert sel["matrix_contract_mode"] == "MATRIX_FULL"
    assert sel["matrix_contract_reason"] == "matrix_contract_incomplete_rebundle_mapping"


def test_matrix_contract_selector_self_change_full() -> None:
    sel = _run_selector(
        "scripts/ops/ci_test_selection_v1.py",
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
    )
    assert sel["matrix_contract_mode"] == "MATRIX_FULL"
    assert sel["matrix_contract_reason"] == "matrix_contract_selector_self_change_requires_full"
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert sel["test_selection_reason"] == "ci_bootstrap_focused"


def test_matrix_contract_arbitrary_selector_change_outside_rebundle_full() -> None:
    sel = _run_selector(
        "scripts/ops/ci_test_selection_v1.py",
        "scripts/ops/durable_completion_integration_partitions_v0.py",
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
    )
    assert sel["matrix_contract_mode"] == "MATRIX_UNMAPPED"
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"


def test_matrix_contract_selection_order_independent() -> None:
    files = list(_PR4548_MATRIX_REBUNDLE_FILES)
    sel_a = _run_selector(*files)
    sel_b = _run_selector(*reversed(files))
    assert sel_a["matrix_contract_mode"] == sel_b["matrix_contract_mode"]
    assert _matrix_targets(sel_a) == _matrix_targets(sel_b)


def test_matrix_contract_duplicate_paths_no_duplicate_targets() -> None:
    sel = _run_selector(*_PR4548_MATRIX_REBUNDLE_FILES, *_PR4548_MATRIX_REBUNDLE_FILES)
    assert sel["matrix_contract_mode"] == "MATRIX_CONTRACT_FOCUSED"
    assert _matrix_targets(sel) == _PR4548_MATRIX_EXPECTED_TARGETS


def test_matrix_contract_docs_only_matrix_no_op() -> None:
    sel = _run_selector("docs/README.md")
    assert sel["matrix_contract_mode"] == "MATRIX_NO_OP"
    assert sel["test_selection_mode"] == "NO_OP"


def test_fast_lane_contract_focused_step_wired_in_ci_yml() -> None:
    text = _ci_text()
    assert "Workflow contract tests (diff-aware CONTRACT_FOCUSED)" in text
    assert "fast_lane_contract_mode == 'CONTRACT_FOCUSED'" in text
    assert "fast_lane_contract_pytest_targets" in text


def test_selector_schedule_exhaustive_full() -> None:
    sel = _run_selector(event_name="schedule")
    assert sel["test_selection_mode"] == "EXHAUSTIVE_FULL"
    assert sel["tests_execute_exhaustive_full"] == "true"
    assert sel["tests_execute_pr_bounded_full"] == "false"


def test_selector_pull_request_never_exhaustive_full() -> None:
    sel = _run_selector("src/strategies/__init__.py", event_name="pull_request")
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert sel["tests_execute_exhaustive_full"] == "false"


def test_selector_workflow_dispatch_without_exhaustive_not_exhaustive() -> None:
    sel = _run_selector("src/strategies/__init__.py", event_name="workflow_dispatch")
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert sel["tests_execute_exhaustive_full"] == "false"


def test_selector_workflow_dispatch_explicit_exhaustive() -> None:
    sel = _run_selector(event_name="workflow_dispatch", force_full=True)
    assert sel["test_selection_mode"] == "EXHAUSTIVE_FULL"
    assert sel["tests_execute_exhaustive_full"] == "true"


def test_selector_bootstrap_self_change_pr_bounded_full() -> None:
    sel = _run_selector(
        "scripts/ops/ci_test_selection_v1.py",
        ".github/workflows/ci.yml",
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
    )
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert sel["test_selection_reason"] == "selector_self_change_bootstrap"
    assert sel["tests_execute_pr_bounded_full"] == "true"
    assert sel["pr_bounded_pytest_targets"]


def test_pr_bounded_full_targets_nonempty() -> None:
    sel = _run_selector("misc/unknown.bin")
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert sel["pr_bounded_pytest_targets"]


def test_tests_job_has_pr_bounded_full_step() -> None:
    text = _ci_text()
    assert "Run PR_BOUNDED_FULL tests (matrix)" in text
    bounded_block = text.split("Run PR_BOUNDED_FULL tests (matrix)", 1)[1].split(
        "Run EXHAUSTIVE_FULL test suite", 1
    )[0]
    assert 'pytest tests/"' not in bounded_block
    assert "pytest tests/ -v" not in bounded_block


VAR_SUITE_ADAPTER_PRODUCTION = "src/risk/validation/var_suite_adapter.py"
VAR_SUITE_ADAPTER_TESTOWNER = "tests/risk/validation/test_var_suite_adapter_v0.py"


def _bounded_targets(sel: dict[str, str]) -> list[str]:
    raw = sel.get("pr_bounded_pytest_targets", "")
    return sorted(raw.split()) if raw else []


def _resolve_finalized_with_adapter_testowner_present(monkeypatch: pytest.MonkeyPatch, *files: str):
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "ci_test_selection_v1_var_suite_adapter",
        str(SELECTOR),
    )
    assert spec and spec.loader
    sel_mod = importlib.util.module_from_spec(spec)
    sys.modules["ci_test_selection_v1_var_suite_adapter"] = sel_mod
    spec.loader.exec_module(sel_mod)

    original_exists = sel_mod._repo_path_exists

    def fake_exists(path: str) -> bool:
        if path == VAR_SUITE_ADAPTER_TESTOWNER:
            return True
        return original_exists(path)

    monkeypatch.setattr(sel_mod, "_repo_path_exists", fake_exists)
    raw = sel_mod.resolve_selection(list(files))
    return sel_mod._finalize_selection_result(
        raw,
        list(files),
        event_name="pull_request",
        force_exhaustive=False,
    )


def test_selector_var_suite_adapter_production_path_pr_bounded_full_includes_testowner(
    monkeypatch,
) -> None:
    result = _resolve_finalized_with_adapter_testowner_present(
        monkeypatch, VAR_SUITE_ADAPTER_PRODUCTION
    )
    assert result.mode == "PR_BOUNDED_FULL"
    assert result.reason == "category_central_src_requires_full"
    assert VAR_SUITE_ADAPTER_TESTOWNER in result.pr_bounded_pytest_targets
    assert result.pr_bounded_pytest_targets.count(VAR_SUITE_ADAPTER_TESTOWNER) == 1


def test_selector_var_suite_adapter_testowner_path_focused_includes_testowner(
    monkeypatch,
) -> None:
    result = _resolve_finalized_with_adapter_testowner_present(
        monkeypatch, VAR_SUITE_ADAPTER_TESTOWNER
    )
    assert result.mode == "CONTRACT_FOCUSED"
    assert VAR_SUITE_ADAPTER_TESTOWNER in result.focused_pytest_targets


def test_selector_var_suite_adapter_combined_diff_pr_bounded_full_includes_testowner_once(
    monkeypatch,
) -> None:
    result = _resolve_finalized_with_adapter_testowner_present(
        monkeypatch,
        VAR_SUITE_ADAPTER_PRODUCTION,
        VAR_SUITE_ADAPTER_TESTOWNER,
    )
    assert result.mode == "PR_BOUNDED_FULL"
    assert result.reason == "category_central_src_requires_full"
    assert result.pr_bounded_pytest_targets.count(VAR_SUITE_ADAPTER_TESTOWNER) == 1
    assert "tests/ci/test_ci_diff_aware_test_selection_v1.py" in result.pr_bounded_pytest_targets


def test_selector_var_suite_adapter_combined_diff_preserves_existing_pr_bounded_targets(
    monkeypatch,
) -> None:
    result = _resolve_finalized_with_adapter_testowner_present(
        monkeypatch,
        VAR_SUITE_ADAPTER_PRODUCTION,
        VAR_SUITE_ADAPTER_TESTOWNER,
    )
    baseline = _run_selector(VAR_SUITE_ADAPTER_PRODUCTION)
    for path in _bounded_targets(baseline):
        assert path in result.pr_bounded_pytest_targets


def test_selector_central_src_without_adapter_path_excludes_adapter_testowner() -> None:
    sel = _run_selector("src/core/foo.py")
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert VAR_SUITE_ADAPTER_TESTOWNER not in _bounded_targets(sel)


def test_selector_var_suite_adapter_empty_diff_does_not_add_adapter_testowner() -> None:
    sel = _run_selector()
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    assert VAR_SUITE_ADAPTER_TESTOWNER not in _bounded_targets(sel)


PACKAGE_A_META_PRODUCTION = "src/meta/learning_loop/contract_safety_v1.py"
PACKAGE_A_META_PRODUCTION_CONFIG = "src/meta/learning_loop/config_patch_manifest_v1.py"
PACKAGE_A_GOVERNANCE_PRODUCTION = "src/governance/promotion_loop/candidate_lineage_manifest_v1.py"
PACKAGE_A_CONTRACT_SAFETY_TESTOWNER = "tests/meta/test_contract_safety_v1.py"
PACKAGE_A_CONFIG_PATCH_MANIFEST_TESTOWNER = "tests/meta/test_config_patch_manifest_v1_contract.py"
PACKAGE_A_CANDIDATE_LINEAGE_TESTOWNER = (
    "tests/governance/promotion_loop/test_candidate_lineage_manifest_v1_contract.py"
)
PACKAGE_A_ALL_PRODUCTION = (
    PACKAGE_A_META_PRODUCTION,
    PACKAGE_A_META_PRODUCTION_CONFIG,
    PACKAGE_A_GOVERNANCE_PRODUCTION,
)
PACKAGE_A_ALL_TESTOWNERS = (
    PACKAGE_A_CONTRACT_SAFETY_TESTOWNER,
    PACKAGE_A_CONFIG_PATCH_MANIFEST_TESTOWNER,
    PACKAGE_A_CANDIDATE_LINEAGE_TESTOWNER,
)
PACKAGE_B_PROMOTION_INPUT_SCRIPT = "scripts/run_promotion_proposal_cycle.py"
PACKAGE_B_PROMOTION_INPUT_LOADER_TESTOWNER = (
    "tests/meta/test_config_patch_manifest_v1_promotion_input_loader_v1.py"
)
PACKAGE_B_PROMOTION_INPUT_REWIRE_TESTOWNER = (
    "tests/scripts/test_run_promotion_proposal_cycle_manifest_input_v1.py"
)
PACKAGE_B_PROMOTION_INPUT_LINEAGE_FK_TESTOWNER = (
    "tests/scripts/test_run_promotion_proposal_cycle_manifest_lineage_fk_v1.py"
)
PACKAGE_B_PROPOSAL_INPUT_REFS_TESTOWNER = (
    "tests/governance/promotion_loop/test_proposal_input_refs_v1.py"
)
PACKAGE_B_ALL_PRODUCTION = (
    PACKAGE_A_META_PRODUCTION_CONFIG,
    PACKAGE_B_PROMOTION_INPUT_SCRIPT,
    "src/governance/promotion_loop/proposal_input_refs_v1.py",
)
PACKAGE_B_ALL_TESTOWNERS = (
    PACKAGE_A_CONTRACT_SAFETY_TESTOWNER,
    PACKAGE_A_CONFIG_PATCH_MANIFEST_TESTOWNER,
    PACKAGE_B_PROMOTION_INPUT_LOADER_TESTOWNER,
    PACKAGE_B_PROMOTION_INPUT_REWIRE_TESTOWNER,
    PACKAGE_B_PROMOTION_INPUT_LINEAGE_FK_TESTOWNER,
    PACKAGE_B_PROPOSAL_INPUT_REFS_TESTOWNER,
)


def test_selector_package_a_meta_production_pr_bounded_full_includes_meta_testowners() -> None:
    sel = _run_selector(PACKAGE_A_META_PRODUCTION)
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    bounded = _bounded_targets(sel)
    assert PACKAGE_A_CONTRACT_SAFETY_TESTOWNER in bounded
    assert PACKAGE_A_CONFIG_PATCH_MANIFEST_TESTOWNER in bounded
    assert PACKAGE_A_CANDIDATE_LINEAGE_TESTOWNER not in bounded


def test_selector_package_a_governance_production_pr_bounded_full_includes_lineage_testowner() -> (
    None
):
    sel = _run_selector(PACKAGE_A_GOVERNANCE_PRODUCTION)
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    bounded = _bounded_targets(sel)
    assert PACKAGE_A_CANDIDATE_LINEAGE_TESTOWNER in bounded
    assert PACKAGE_A_CONTRACT_SAFETY_TESTOWNER not in bounded
    assert PACKAGE_A_CONFIG_PATCH_MANIFEST_TESTOWNER not in bounded


def test_selector_package_a_combined_diff_pr_bounded_full_includes_all_testowners_once() -> None:
    sel = _run_selector(*PACKAGE_A_ALL_PRODUCTION, *PACKAGE_A_ALL_TESTOWNERS)
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    bounded = _bounded_targets(sel)
    for path in PACKAGE_A_ALL_TESTOWNERS:
        assert path in bounded
        assert bounded.count(path) == 1


def test_selector_central_src_without_package_a_path_excludes_package_a_testowners() -> None:
    sel = _run_selector("src/core/foo.py")
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    bounded = _bounded_targets(sel)
    for path in PACKAGE_A_ALL_TESTOWNERS:
        assert path not in bounded


def test_selector_package_b_promotion_script_contract_focused_includes_loader_and_rewire_testowners() -> (
    None
):
    sel = _run_selector(PACKAGE_B_PROMOTION_INPUT_SCRIPT)
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    targets = _targets(sel)
    assert PACKAGE_B_PROMOTION_INPUT_LOADER_TESTOWNER in targets
    assert PACKAGE_B_PROMOTION_INPUT_REWIRE_TESTOWNER in targets
    assert PACKAGE_B_PROMOTION_INPUT_LINEAGE_FK_TESTOWNER in targets
    assert PACKAGE_B_PROPOSAL_INPUT_REFS_TESTOWNER in targets


def test_selector_package_b_combined_diff_pr_bounded_full_includes_required_testowners_once() -> (
    None
):
    sel = _run_selector(
        *PACKAGE_B_ALL_PRODUCTION,
        "scripts/ops/ci_test_selection_v1.py",
        *PACKAGE_B_ALL_TESTOWNERS,
    )
    assert sel["test_selection_mode"] == "PR_BOUNDED_FULL"
    bounded = _bounded_targets(sel)
    for path in PACKAGE_B_ALL_TESTOWNERS:
        assert path in bounded
        assert bounded.count(path) == 1
    assert PACKAGE_A_CANDIDATE_LINEAGE_TESTOWNER not in bounded
