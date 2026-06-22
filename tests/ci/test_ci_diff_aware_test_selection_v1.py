"""Contract tests for diff-aware required test selection (ci.yml v1)."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

CI_YML = Path(".github/workflows/ci.yml")
SELECTOR = Path("scripts/ops/ci_test_selection_v1.py")
MAPPING = Path("config/ci/file_category_mapping.yaml")


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


def test_changes_job_exports_test_selection_outputs() -> None:
    text = _ci_text()
    for key in (
        "test_selection_mode",
        "test_selection_reason",
        "tests_execute_full",
        "tests_execute_focused",
        "tests_execute_no_op",
        "focused_pytest_targets",
        "focused_module_imports",
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
    assert "Run full test suite" in text
    assert "Run focused tests (matrix)" in text
    assert "Run tests with coverage (FULL only)" in text


def test_tests_job_focused_runs_on_all_matrix_versions() -> None:
    text = _ci_text()
    focused_step = text.split("name: Run focused tests (matrix)", 1)[1].split("\n      - name:", 1)[
        0
    ]
    assert "matrix.python-version == '3.11'" not in focused_step
    assert "tests_execute_focused == 'true'" in focused_step


def test_tests_job_focused_module_import_smoke_step() -> None:
    assert "Focused module import smoke" in _ci_text()
    assert "focused_module_imports" in _ci_text()
    assert "--import-smoke-modules" in _ci_text()


def test_selector_docs_only_no_op() -> None:
    sel = _run_selector("docs/TECH_DEBT_BACKLOG.md", "README.md")
    assert sel["test_selection_mode"] == "NO_OP"
    assert sel["tests_execute_no_op"] == "true"


def test_selector_workflow_only_no_op() -> None:
    sel = _run_selector(".github/workflows/ci.yml")
    assert sel["test_selection_mode"] == "NO_OP"


def test_selector_central_src_full() -> None:
    sel = _run_selector("src/strategies/__init__.py")
    assert sel["test_selection_mode"] == "FULL"
    assert sel["tests_execute_full"] == "true"


def test_selector_registry_init_full() -> None:
    sel = _run_selector(
        "src/strategies/__init__.py",
        "tests/test_strategy_vol_regime_filter.py",
    )
    assert sel["test_selection_mode"] == "FULL"


def test_selector_composite_full() -> None:
    sel = _run_selector(
        "src/strategies/composite.py",
        "tests/test_strategy_composite.py",
    )
    assert sel["test_selection_mode"] == "FULL"


def test_selector_dependencies_full() -> None:
    sel = _run_selector("requirements.txt")
    assert sel["test_selection_mode"] == "FULL"


def test_selector_global_test_infra_full() -> None:
    sel = _run_selector("tests/conftest.py")
    assert sel["test_selection_mode"] == "FULL"


def test_selector_scripts_focused() -> None:
    sel = _run_selector("scripts/demo_strategy_research.py")
    assert sel["test_selection_mode"] == "FOCUSED"
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
    assert sel["test_selection_mode"] == "FOCUSED"
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
    assert sel["test_selection_mode"] == "FOCUSED"
    assert sel["test_selection_reason"] == "strategy_regime_owner_focused"
    assert "tests/test_strategies_phase27.py" in _targets(sel)
    assert _modules(sel) == ["src.strategies.vol_breakout"]


def test_selector_strategy_vol_regime_filter_owner_focused() -> None:
    sel = _run_selector(
        "src/strategies/vol_regime_filter.py",
        "tests/test_strategy_vol_regime_filter.py",
    )
    assert sel["test_selection_mode"] == "FOCUSED"
    assert "tests/test_strategy_vol_regime_filter.py" in _targets(sel)
    assert _modules(sel) == ["src.strategies.vol_regime_filter"]


def test_selector_regime_detectors_owner_focused() -> None:
    sel = _run_selector(
        "src/regime/detectors.py",
        "tests/test_regime_detection.py",
    )
    assert sel["test_selection_mode"] == "FOCUSED"
    assert "tests/test_regime_detection.py" in _targets(sel)
    assert _modules(sel) == ["src.regime.detectors"]


def test_selector_el_karoui_vol_model_owner_focused() -> None:
    sel = _run_selector(
        "src/strategies/el_karoui/vol_model.py",
        "tests/strategies/el_karoui/test_vol_model.py",
    )
    assert sel["test_selection_mode"] == "FOCUSED"
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
    assert sel["test_selection_mode"] == "FULL"
    assert sel["test_selection_reason"] == "strategy_regime_owner_incomplete_or_ambiguous"


def test_selector_two_prod_files_full() -> None:
    sel = _run_selector(
        "src/strategies/vol_breakout.py",
        "src/strategies/vol_regime_filter.py",
        "tests/test_strategies_phase27.py",
    )
    assert sel["test_selection_mode"] == "FULL"


def test_selector_strategy_plus_foreign_test_owner_full() -> None:
    sel = _run_selector(
        "src/strategies/vol_breakout.py",
        "tests/test_strategy_vol_regime_filter.py",
    )
    assert sel["test_selection_mode"] == "FULL"


def test_selector_strategy_plus_conftest_full() -> None:
    sel = _run_selector(
        "src/strategies/vol_breakout.py",
        "tests/test_strategies_phase27.py",
        "tests/conftest.py",
    )
    assert sel["test_selection_mode"] == "FULL"


def test_selector_strategy_plus_dependency_full() -> None:
    sel = _run_selector(
        "src/strategies/vol_breakout.py",
        "tests/test_strategies_phase27.py",
        "requirements.txt",
    )
    assert sel["test_selection_mode"] == "FULL"


def test_selector_strategy_plus_pyproject_full() -> None:
    sel = _run_selector(
        "src/strategies/vol_breakout.py",
        "tests/test_strategies_phase27.py",
        "pyproject.toml",
    )
    assert sel["test_selection_mode"] == "FULL"


def test_selector_strategy_plus_workflow_full() -> None:
    sel = _run_selector(
        "src/strategies/vol_breakout.py",
        "tests/test_strategies_phase27.py",
        ".github/workflows/lint.yml",
    )
    assert sel["test_selection_mode"] == "FULL"


def test_selector_ci_bootstrap_selector_only_focused() -> None:
    sel = _run_selector("scripts/ops/ci_test_selection_v1.py")
    assert sel["test_selection_mode"] == "FOCUSED"
    assert sel["test_selection_reason"] == "ci_bootstrap_focused"
    assert "tests/ci/test_ci_diff_aware_test_selection_v1.py" in _targets(sel)
    assert sel["tests_execute_full"] == "false"


def test_selector_ci_bootstrap_selector_plus_contract_focused() -> None:
    sel = _run_selector(
        "scripts/ops/ci_test_selection_v1.py",
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
    )
    assert sel["test_selection_mode"] == "FOCUSED"
    assert sel["test_selection_reason"] == "ci_bootstrap_focused"
    assert _targets(sel) == ["tests/ci/test_ci_diff_aware_test_selection_v1.py"]
    assert sel["tests_execute_full"] == "false"


def test_selector_ci_bootstrap_plus_workflow_full() -> None:
    sel = _run_selector(
        "scripts/ops/ci_test_selection_v1.py",
        ".github/workflows/ci.yml",
    )
    assert sel["test_selection_mode"] == "FULL"
    assert sel["test_selection_reason"] == "ci_bootstrap_mixed_diff_requires_full"


def test_selector_ci_bootstrap_plus_dependency_full() -> None:
    sel = _run_selector(
        "scripts/ops/ci_test_selection_v1.py",
        "requirements.txt",
    )
    assert sel["test_selection_mode"] == "FULL"
    assert sel["test_selection_reason"] == "ci_bootstrap_mixed_diff_requires_full"


def test_selector_ci_bootstrap_plus_central_src_full() -> None:
    sel = _run_selector(
        "scripts/ops/ci_test_selection_v1.py",
        "src/core/foo.py",
    )
    assert sel["test_selection_mode"] == "FULL"
    assert sel["test_selection_reason"] == "ci_bootstrap_mixed_diff_requires_full"


def test_selector_ci_bootstrap_plus_unknown_full() -> None:
    sel = _run_selector(
        "scripts/ops/ci_test_selection_v1.py",
        "misc/unclassified.bin",
    )
    assert sel["test_selection_mode"] == "FULL"
    assert sel["test_selection_reason"] == "ci_bootstrap_mixed_diff_requires_full"


def test_selector_ci_bootstrap_contract_test_only_focused() -> None:
    sel = _run_selector("tests/ci/test_ci_diff_aware_test_selection_v1.py")
    assert sel["test_selection_mode"] == "FOCUSED"
    assert sel["test_selection_reason"] == "ci_bootstrap_focused"


def test_selector_ci_bootstrap_deterministic_regardless_of_file_order() -> None:
    files_a = (
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
        "scripts/ops/ci_test_selection_v1.py",
    )
    files_b = tuple(reversed(files_a))
    sel_a = _run_selector(*files_a)
    sel_b = _run_selector(*files_b)
    assert sel_a == sel_b
    assert sel_a["test_selection_mode"] == "FOCUSED"


def test_selector_ci_mapping_only_full() -> None:
    sel = _run_selector("config/ci/file_category_mapping.yaml")
    assert sel["test_selection_mode"] == "FULL"
    assert sel["test_selection_reason"] == "ci_mapping_or_workflow_selector_change_requires_full"


def test_selector_ci_workflow_change_self_full() -> None:
    sel = _run_selector(
        ".github/workflows/ci.yml",
        "scripts/ops/ci_test_selection_v1.py",
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
    )
    assert sel["test_selection_mode"] == "FULL"
    assert sel["test_selection_reason"] == "ci_bootstrap_mixed_diff_requires_full"


def test_selector_strategy_plus_core_full() -> None:
    sel = _run_selector(
        "src/strategies/vol_breakout.py",
        "tests/test_strategies_phase27.py",
        "src/core/foo.py",
    )
    assert sel["test_selection_mode"] == "FULL"


def test_selector_multiple_test_owners_full() -> None:
    sel = _run_selector(
        "src/strategies/vol_breakout.py",
        "tests/test_strategies_phase27.py",
        "tests/test_strategy_vol_regime_filter.py",
    )
    assert sel["test_selection_mode"] == "FULL"


def test_selector_unknown_fail_closed_full() -> None:
    sel = _run_selector("misc/unclassified.bin")
    assert sel["test_selection_mode"] == "FULL"


def test_selector_empty_diff_fail_closed_full() -> None:
    sel = _run_selector()
    assert sel["test_selection_mode"] == "FULL"
    assert sel["test_selection_reason"] == "empty_diff_fail_closed"


def test_selector_force_full() -> None:
    sel = _run_selector("docs/foo.md", force_full=True)
    assert sel["test_selection_mode"] == "FULL"


def test_selector_push_event_full() -> None:
    sel = _run_selector("docs/foo.md", event_name="push")
    assert sel["test_selection_mode"] == "FULL"


def test_selector_merge_group_event_full() -> None:
    sel = _run_selector(
        "src/strategies/vol_breakout.py",
        "tests/test_strategies_phase27.py",
        event_name="merge_group",
    )
    assert sel["test_selection_mode"] == "FULL"


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
    assert sel["test_selection_mode"] == "FOCUSED"
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
    assert sel["test_selection_mode"] == "FOCUSED"
    assert sel["test_selection_reason"] == "market_dashboard_focused"
    assert "tests/ci/test_ci_diff_aware_test_selection_v1.py" in _targets(sel)
    assert sel["tests_execute_full"] == "false"


def test_selector_market_dashboard_plus_central_src_full() -> None:
    sel = _run_selector(
        "src/webui/market_surface.py",
        "src/execution/live/orchestrator.py",
    )
    assert sel["test_selection_mode"] == "FULL"


def test_selector_market_dashboard_tests_only_focused() -> None:
    sel = _run_selector("tests/webui/test_market_dashboard_no_bitcoin_futures_v1.py")
    assert sel["test_selection_mode"] == "FOCUSED"
    assert sel["test_selection_reason"] == "market_dashboard_focused"


def test_workflow_only_does_not_run_full_pytest_step_unconditionally() -> None:
    text = _ci_text()
    full_step = text.split("name: Run full test suite", 1)[1].split("\n      - name:", 1)[0]
    assert "tests_execute_full == 'true'" in full_step
    assert "workflow_only == 'true'" not in full_step


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
    assert sel["test_selection_mode"] == "FOCUSED"
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
        "tests/ops/test_bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0.py",
    )
    assert sel["test_selection_mode"] == "FOCUSED"
    assert sel["test_selection_reason"] == "durable_completion_focused"
    targets = _targets(sel)
    assert targets == ["tests/ops/test_durable_completion_validation_graph_v1.py"]
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
    assert sel["test_selection_mode"] == "FOCUSED"
    assert sel["test_selection_reason"] == "durable_completion_focused"
    targets = _targets(sel)
    assert targets == ["tests/ops/test_durable_completion_validation_graph_v1.py"]
    assert sel["tests_execute_full"] == "false"
    assert sel["tests_execute_no_op"] == "false"


def test_selector_pe55_fill_rebinding_import_modules_bounded() -> None:
    sel = _run_selector(*PE55_DURABLE_COMPLETION_FILL_REBINDING_FILES)
    modules = _modules(sel)
    assert modules == ["src.ops.durable_completion_validation"]
    assert (
        "src.ops.bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0"
        not in modules
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
    assert sel["test_selection_mode"] == "FOCUSED"
    assert sel["test_selection_reason"] == "durable_completion_focused"
    targets = _targets(sel)
    assert targets == ["tests/ops/test_durable_completion_validation_graph_v1.py"]
    assert (
        "tests/ops/test_bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0.py"
        not in targets
    )
    assert "tests/ci/test_ci_diff_aware_test_selection_v1.py" not in targets


PE60_DURABLE_COMPLETION_DELEGATION_FILES = (
    "src/ops/bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0.py",
    "src/ops/durable_completion_validation/graph.py",
    "src/ops/durable_completion_validation/validators/completion_chain.py",
    "tests/ops/test_durable_completion_validation_graph_v1.py",
)


def test_selector_pe60_completion_chain_delegation_rebinding_bounded_focused_targets() -> None:
    sel = _run_selector(*PE60_DURABLE_COMPLETION_DELEGATION_FILES)
    assert sel["test_selection_mode"] == "FOCUSED"
    assert sel["test_selection_reason"] == "durable_completion_focused"
    targets = _targets(sel)
    assert targets == ["tests/ops/test_durable_completion_validation_graph_v1.py"]
    assert (
        "tests/ops/test_bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0.py"
        not in targets
    )
    assert sel["tests_execute_full"] == "false"
    assert sel["tests_execute_no_op"] == "false"


def test_fast_lane_skips_full_static_sweep_when_focused() -> None:
    text = _ci_text()
    static_if = text.split("name: Static contract tests", 1)[1].split("run:", 1)[0]
    assert "tests_execute_focused != 'true'" in static_if
    assert "OPS_SHARD_COUNT=8" in text


def test_selector_durable_completion_graph_core_plus_test_owners_focused() -> None:
    sel = _run_selector(
        "src/ops/durable_completion_validation/graph.py",
        "src/ops/durable_completion_validation/models.py",
        "tests/ops/test_durable_completion_validation_graph_v1.py",
        "tests/ops/test_bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0.py",
    )
    assert sel["test_selection_mode"] == "FOCUSED"
    assert sel["test_selection_reason"] == "durable_completion_focused"


def test_selector_pe55_full_diff_with_ci_workflow_rebundle_stays_focused() -> None:
    sel = _run_selector(
        *PE55_DURABLE_COMPLETION_FILL_REBINDING_FILES,
        ".github/workflows/ci.yml",
        "scripts/ops/ci_test_selection_v1.py",
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
    )
    assert sel["test_selection_mode"] == "FOCUSED"
    assert sel["test_selection_reason"] == "durable_completion_focused"
    targets = _targets(sel)
    assert "tests/ops/test_durable_completion_validation_graph_v1.py" in targets
    assert "tests/ci/test_ci_diff_aware_test_selection_v1.py" in targets
    assert (
        "tests/ops/test_bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0.py"
        not in targets
    )
    assert sel["tests_execute_full"] == "false"


def test_selector_durable_completion_facade_plus_graph_focused() -> None:
    sel = _run_selector(
        "src/ops/bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0.py",
        "src/ops/durable_completion_validation/graph.py",
        "src/ops/durable_completion_validation/validators/recovery.py",
        "tests/ops/test_durable_completion_validation_graph_v1.py",
        "tests/ops/test_bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0.py",
    )
    assert sel["test_selection_mode"] == "FOCUSED"
    assert sel["test_selection_reason"] == "durable_completion_focused"


def test_selector_durable_completion_rebundle_with_ci_policy_focused() -> None:
    sel = _run_selector(
        *PR4451_DURABLE_COMPLETION_FILES,
        "scripts/ops/ci_test_selection_v1.py",
        "config/ci/file_category_mapping.yaml",
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
    )
    assert sel["test_selection_mode"] == "FOCUSED"
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
    assert sel["test_selection_mode"] == "FULL"


def test_selector_durable_completion_identity_plus_foreign_src_full() -> None:
    sel = _run_selector(
        "src/ops/durable_completion_validation/identity.py",
        "src/risk/killswitch.py",
        "tests/ops/test_durable_completion_validation_graph_v1.py",
        "tests/ops/test_bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0.py",
    )
    assert sel["test_selection_mode"] == "FULL"


def test_selector_durable_completion_packaging_escalates_full() -> None:
    sel = _run_selector(
        "src/ops/durable_completion_validation/graph.py",
        "pyproject.toml",
        "tests/ops/test_durable_completion_validation_graph_v1.py",
        "tests/ops/test_bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0.py",
    )
    assert sel["test_selection_mode"] == "FULL"


def test_selector_durable_completion_execution_touch_escalates_full() -> None:
    sel = _run_selector(
        "src/ops/durable_completion_validation/validators/traceability.py",
        "src/execution/live/orchestrator.py",
        "tests/ops/test_durable_completion_validation_graph_v1.py",
        "tests/ops/test_bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0.py",
    )
    assert sel["test_selection_mode"] == "FULL"


def test_selector_durable_completion_unknown_file_escalates_full() -> None:
    sel = _run_selector(
        "src/ops/durable_completion_validation/graph.py",
        "misc/unclassified.bin",
        "tests/ops/test_durable_completion_validation_graph_v1.py",
        "tests/ops/test_bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0.py",
    )
    assert sel["test_selection_mode"] == "FULL"


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
    assert sel["test_selection_mode"] == "FULL"


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
    assert sel["test_selection_mode"] == "FOCUSED"
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
    assert sel["test_selection_mode"] == "FOCUSED"
    assert sel["test_selection_reason"] == "preflight_assembly_focused"


def test_selector_unknown_productive_src_ops_never_no_op() -> None:
    sel = _run_selector("src/ops/unknown_unmapped_contract_v0.py")
    assert sel["test_selection_mode"] == "FULL"
    assert sel["test_selection_reason"] == "productive_src_no_op_blocked_fail_closed"
    assert sel["tests_execute_no_op"] == "false"


def test_selector_productive_src_without_test_owner_escalates_full() -> None:
    sel = _run_selector(
        "src/ops/bounded_futures_testnet_preflight_packet_contract_v0.py",
    )
    assert sel["test_selection_mode"] == "FULL"
    assert sel["tests_execute_full"] == "true"


def test_selector_preflight_assembly_rebundle_with_ci_policy_focused() -> None:
    sel = _run_selector(
        *PE52_PREFLIGHT_ASSEMBLY_FILES,
        "scripts/ops/ci_test_selection_v1.py",
        "config/ci/file_category_mapping.yaml",
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
    )
    assert sel["test_selection_mode"] == "FOCUSED"
    assert sel["test_selection_reason"] == "preflight_assembly_focused"
    assert "tests/ci/test_ci_diff_aware_test_selection_v1.py" in _targets(sel)


def test_selector_preflight_assembly_plus_foreign_src_full() -> None:
    sel = _run_selector(
        *PE52_PREFLIGHT_ASSEMBLY_FILES,
        "src/execution/live/orchestrator.py",
    )
    assert sel["test_selection_mode"] == "FULL"


def test_selector_preflight_assembly_execution_touch_escalates_full() -> None:
    sel = _run_selector(
        PE52_PREFLIGHT_ASSEMBLY_FILES[0],
        "src/risk/killswitch.py",
        PE52_PREFLIGHT_ASSEMBLY_FILES[1],
    )
    assert sel["test_selection_mode"] == "FULL"


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
    assert sel["test_selection_mode"] == "FULL"


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


PE53_RISK_KILLSWITCH_FILES = (
    "src/ops/bounded_futures_testnet_risk_killswitch_lifecycle_integration_contract_v0.py",
    "tests/ops/test_bounded_futures_testnet_risk_killswitch_lifecycle_integration_contract_v0.py",
)


def test_selector_pe53_risk_killswitch_fileset_focused() -> None:
    sel = _run_selector(*PE53_RISK_KILLSWITCH_FILES)
    assert sel["test_selection_mode"] == "FOCUSED"
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
    assert sel["test_selection_mode"] == "FOCUSED"
    assert sel["test_selection_reason"] == "risk_killswitch_focused"


def test_selector_pe53_owner_without_test_owner_escalates_full() -> None:
    sel = _run_selector(PE53_RISK_KILLSWITCH_FILES[0])
    assert sel["test_selection_mode"] == "FULL"
    assert sel["test_selection_reason"] == "risk_killswitch_incomplete_or_missing_test_owner"


def test_selector_pe53_plus_unknown_ops_src_escalates_full() -> None:
    sel = _run_selector(
        *PE53_RISK_KILLSWITCH_FILES,
        "src/ops/bounded_futures_testnet_preflight_packet_contract_v0.py",
    )
    assert sel["test_selection_mode"] == "FULL"


def test_selector_pe53_plus_unknown_src_escalates_full() -> None:
    sel = _run_selector(
        *PE53_RISK_KILLSWITCH_FILES,
        "src/execution/live/orchestrator.py",
    )
    assert sel["test_selection_mode"] == "FULL"


def test_selector_pe53_risk_killswitch_outside_owner_escalates_full() -> None:
    sel = _run_selector(
        *PE53_RISK_KILLSWITCH_FILES,
        "src/risk/killswitch.py",
    )
    assert sel["test_selection_mode"] == "FULL"


def test_selector_pe53_runtime_touch_escalates_full() -> None:
    sel = _run_selector(
        PE53_RISK_KILLSWITCH_FILES[0],
        "src/runtime/scheduler.py",
        PE53_RISK_KILLSWITCH_FILES[1],
    )
    assert sel["test_selection_mode"] == "FULL"


def test_selector_pe53_trading_strategy_master_v2_touch_escalates_full() -> None:
    sel = _run_selector(
        PE53_RISK_KILLSWITCH_FILES[0],
        "src/strategies/vol_breakout.py",
        PE53_RISK_KILLSWITCH_FILES[1],
    )
    assert sel["test_selection_mode"] == "FULL"


def test_selector_pe53_packaging_change_escalates_full() -> None:
    sel = _run_selector(
        *PE53_RISK_KILLSWITCH_FILES,
        "pyproject.toml",
    )
    assert sel["test_selection_mode"] == "FULL"


def test_selector_pe53_rebundle_with_ci_policy_focused() -> None:
    sel = _run_selector(
        *PE53_RISK_KILLSWITCH_FILES,
        "scripts/ops/ci_test_selection_v1.py",
        "config/ci/file_category_mapping.yaml",
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
    )
    assert sel["test_selection_mode"] == "FOCUSED"
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


PE54_TINY_ORDER_FILES = (
    "src/ops/bounded_futures_testnet_tiny_order_lifecycle_integration_contract_v0.py",
    "tests/ops/test_bounded_futures_testnet_tiny_order_lifecycle_integration_contract_v0.py",
)


def test_selector_pe54_tiny_order_prod_owner_only_focused() -> None:
    sel = _run_selector(PE54_TINY_ORDER_FILES[0])
    assert sel["test_selection_mode"] == "FULL"
    assert sel["test_selection_reason"] == "tiny_order_incomplete_or_missing_test_owner"


def test_selector_pe54_tiny_order_test_owner_only_focused() -> None:
    sel = _run_selector(PE54_TINY_ORDER_FILES[1])
    assert sel["test_selection_mode"] == "FOCUSED"
    assert sel["test_selection_reason"] == "tiny_order_focused"
    targets = _targets(sel)
    assert PE54_TINY_ORDER_FILES[1] in targets
    assert "tests/ops/test_order_capability_killswitch_abort_binding_contract_v1.py" in targets
    assert "tests/ops/test_order_capability_cancel_cleanup_failclosed_contract_v1.py" in targets
    assert sel["tests_execute_full"] == "false"
    assert sel["tests_execute_no_op"] == "false"


def test_selector_pe54_tiny_order_fileset_focused() -> None:
    sel = _run_selector(*PE54_TINY_ORDER_FILES)
    assert sel["test_selection_mode"] == "FOCUSED"
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
    assert sel["test_selection_mode"] == "FULL"


def test_selector_pe54_tiny_order_plus_unknown_src_escalates_full() -> None:
    sel = _run_selector(
        *PE54_TINY_ORDER_FILES,
        "src/execution/live/orchestrator.py",
    )
    assert sel["test_selection_mode"] == "FULL"


def test_selector_pe54_tiny_order_outside_owner_escalates_full() -> None:
    sel = _run_selector(
        *PE54_TINY_ORDER_FILES,
        "src/risk/killswitch.py",
    )
    assert sel["test_selection_mode"] == "FULL"


def test_selector_pe54_tiny_order_runtime_touch_escalates_full() -> None:
    sel = _run_selector(
        PE54_TINY_ORDER_FILES[0],
        "src/runtime/scheduler.py",
        PE54_TINY_ORDER_FILES[1],
    )
    assert sel["test_selection_mode"] == "FULL"


def test_selector_pe54_tiny_order_trading_strategy_master_v2_touch_escalates_full() -> None:
    sel = _run_selector(
        PE54_TINY_ORDER_FILES[0],
        "src/strategies/vol_breakout.py",
        PE54_TINY_ORDER_FILES[1],
    )
    assert sel["test_selection_mode"] == "FULL"


def test_selector_pe54_tiny_order_packaging_change_escalates_full() -> None:
    sel = _run_selector(
        *PE54_TINY_ORDER_FILES,
        "pyproject.toml",
    )
    assert sel["test_selection_mode"] == "FULL"


def test_selector_pe54_tiny_order_rebundle_with_ci_policy_focused() -> None:
    sel = _run_selector(
        *PE54_TINY_ORDER_FILES,
        "scripts/ops/ci_test_selection_v1.py",
        "config/ci/file_category_mapping.yaml",
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
    )
    assert sel["test_selection_mode"] == "FOCUSED"
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
    assert sel["test_selection_mode"] == "FULL"


def test_mapping_file_includes_tiny_order_focused() -> None:
    text = MAPPING.read_text(encoding="utf-8")
    assert "tiny_order_focused:" in text


PE21_RECONCILIATION_PRIMARY_EVIDENCE_FILES = (
    "src/ops/bounded_futures_testnet_position_order_reconciliation_primary_evidence_integration_contract_v0.py",
    "tests/ops/test_bounded_futures_testnet_position_order_reconciliation_primary_evidence_integration_contract_v0.py",
)


def test_selector_pe21_reconciliation_primary_evidence_fileset_focused() -> None:
    sel = _run_selector(*PE21_RECONCILIATION_PRIMARY_EVIDENCE_FILES)
    assert sel["test_selection_mode"] == "FOCUSED"
    assert sel["test_selection_reason"] == "reconciliation_primary_evidence_focused"
    targets = _targets(sel)
    assert PE21_RECONCILIATION_PRIMARY_EVIDENCE_FILES[1] in targets
    assert "tests/ci/test_ci_diff_aware_test_selection_v1.py" in targets
    assert sel["tests_execute_full"] == "false"
    assert "productive_src_no_op_blocked_fail_closed" not in sel["test_selection_reason"]


def test_selector_pe21_prod_owner_without_test_owner_escalates_full() -> None:
    sel = _run_selector(PE21_RECONCILIATION_PRIMARY_EVIDENCE_FILES[0])
    assert sel["test_selection_mode"] == "FULL"
    assert (
        sel["test_selection_reason"]
        == "reconciliation_primary_evidence_incomplete_or_missing_test_owner"
    )


def test_selector_pe21_plus_unknown_src_escalates_full() -> None:
    sel = _run_selector(
        *PE21_RECONCILIATION_PRIMARY_EVIDENCE_FILES,
        "src/execution/live/orchestrator.py",
    )
    assert sel["test_selection_mode"] == "FULL"


def test_selector_pe21_rebundle_with_ci_policy_focused() -> None:
    sel = _run_selector(
        *PE21_RECONCILIATION_PRIMARY_EVIDENCE_FILES,
        "scripts/ops/ci_test_selection_v1.py",
        "config/ci/file_category_mapping.yaml",
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
    )
    assert sel["test_selection_mode"] == "FOCUSED"
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
    assert sel["test_selection_mode"] == "FOCUSED"
    assert sel["test_selection_reason"] == "wallclock_focused"
    assert sel["tests_execute_full"] == "false"
    assert sel["tests_execute_focused"] == "true"
    targets = _targets(sel)
    assert "tests/ops/test_run_shadow_bounded_observation_adapter_v0.py" in targets
    assert "tests/ops/test_shadow_wallclock_duration_evidence_contract_v0.py" in targets
    assert "tests/ops/test_shadow_247_futures_start_wrapper_skeleton_v0.py" in targets


def test_selector_case_pr4491_ci_bootstrap_diff_focused() -> None:
    sel = _run_selector(*PR4491_CI_BOOTSTRAP_FILES)
    assert sel["test_selection_mode"] == "FOCUSED"
    assert sel["test_selection_reason"] == "ci_infra_focused"
    assert sel["tests_execute_full"] == "false"
    assert "tests/ci/test_ci_diff_aware_test_selection_v1.py" in _targets(sel)
    assert "tests/ci/test_workflows_no_pull_request_target_contract_v0.py" in _targets(sel)
    assert "tests/ci/test_ci_testowner_runtime_budget_reporting_contract_v0.py" in _targets(sel)


def test_selector_case_ci_selector_change_full() -> None:
    sel = _run_selector(
        "scripts/ops/ci_test_selection_v1.py",
        "config/ci/file_category_mapping.yaml",
    )
    assert sel["test_selection_mode"] == "FULL"


def test_selector_case_dependency_change_full() -> None:
    sel = _run_selector("pyproject.toml")
    assert sel["test_selection_mode"] == "FULL"
    assert sel["test_selection_reason"] == "category_dependencies_requires_full"


def test_selector_case_central_shared_src_change_full() -> None:
    sel = _run_selector("src/core/foo.py")
    assert sel["test_selection_mode"] == "FULL"
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
    assert sel["test_selection_mode"] == "FULL"


def test_selector_case_unknown_src_diff_full() -> None:
    sel = _run_selector("misc/unclassified.bin")
    assert sel["test_selection_mode"] == "FULL"


def test_selector_ci_workflow_change_self_focused_ci_infra() -> None:
    sel = _run_selector(
        ".github/workflows/ci.yml",
        "scripts/ops/ci_test_selection_v1.py",
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
        "tests/ci/test_workflows_no_pull_request_target_contract_v0.py",
        "tests/ci/test_ci_testowner_runtime_budget_reporting_contract_v0.py",
    )
    assert sel["test_selection_mode"] == "FOCUSED"
    assert sel["test_selection_reason"] == "ci_infra_focused"


PR4497_BOUNDED_NETWORK_PREFLIGHT_FILES: tuple[str, ...] = (
    "src/ops/bounded_network_testnet_preflight_contract_v0.py",
    "tests/ops/test_bounded_network_testnet_preflight_contract_v0.py",
)


def test_selector_pr4497_bounded_network_preflight_diff_focused() -> None:
    sel = _run_selector(*PR4497_BOUNDED_NETWORK_PREFLIGHT_FILES)
    assert sel["test_selection_mode"] == "FOCUSED"
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
    assert sel["test_selection_mode"] == "FULL"
    assert (
        sel["test_selection_reason"]
        == "bounded_network_testnet_preflight_incomplete_or_missing_test_owner"
    )


def test_selector_bounded_network_preflight_plus_foreign_src_full() -> None:
    sel = _run_selector(
        *PR4497_BOUNDED_NETWORK_PREFLIGHT_FILES,
        "src/execution/live/orchestrator.py",
    )
    assert sel["test_selection_mode"] == "FULL"
    assert (
        sel["test_selection_reason"]
        == "bounded_network_testnet_preflight_foreign_path_requires_full"
    )


def test_selector_bounded_network_preflight_plus_dependency_full() -> None:
    sel = _run_selector(*PR4497_BOUNDED_NETWORK_PREFLIGHT_FILES, "requirements.txt")
    assert sel["test_selection_mode"] == "FULL"
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
    assert sel["test_selection_mode"] == "FOCUSED"
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
    assert sel["test_selection_mode"] == "FOCUSED"
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
    assert sel["test_selection_mode"] == "FULL"
    assert (
        sel["test_selection_reason"]
        == "runtime_wallclock_evidence_emitter_incomplete_or_missing_test_owner"
    )


def test_selector_runtime_wallclock_evidence_emitter_plus_foreign_src_full() -> None:
    sel = _run_selector(
        *RUNTIME_WALLCLOCK_EVIDENCE_EMITTER_FILES,
        "src/execution/live/orchestrator.py",
    )
    assert sel["test_selection_mode"] == "FULL"
    assert (
        sel["test_selection_reason"]
        == "runtime_wallclock_evidence_emitter_foreign_path_requires_full"
    )


def test_selector_runtime_wallclock_evidence_emitter_plus_dependency_full() -> None:
    sel = _run_selector(*RUNTIME_WALLCLOCK_EVIDENCE_EMITTER_FILES, "requirements.txt")
    assert sel["test_selection_mode"] == "FULL"
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
    assert sel["test_selection_mode"] == "FOCUSED"
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


def test_selector_testnet_wallclock_duration_evidence_owner_pair_focused() -> None:
    sel = _run_selector(*TESTNET_WALLCLOCK_DURATION_EVIDENCE_FILES)
    assert sel["test_selection_mode"] == "FOCUSED"
    assert sel["test_selection_reason"] == "testnet_wallclock_duration_evidence_focused"
    assert sel["tests_execute_full"] == "false"
    assert sel["tests_execute_focused"] == "true"
    assert sel["tests_execute_no_op"] == "false"
    targets = _targets(sel)
    assert TESTNET_WALLCLOCK_DURATION_EVIDENCE_FILES[1] in targets
    assert "tests/ci/test_ci_diff_aware_test_selection_v1.py" not in targets


def test_selector_testnet_wallclock_duration_evidence_owner_without_test_owner_full() -> None:
    sel = _run_selector(TESTNET_WALLCLOCK_DURATION_EVIDENCE_FILES[0])
    assert sel["test_selection_mode"] == "FULL"
    assert (
        sel["test_selection_reason"]
        == "testnet_wallclock_duration_evidence_incomplete_or_missing_test_owner"
    )


def test_selector_testnet_wallclock_duration_evidence_plus_foreign_src_full() -> None:
    sel = _run_selector(
        *TESTNET_WALLCLOCK_DURATION_EVIDENCE_FILES,
        "src/execution/live/orchestrator.py",
    )
    assert sel["test_selection_mode"] == "FULL"
    assert (
        sel["test_selection_reason"]
        == "testnet_wallclock_duration_evidence_foreign_path_requires_full"
    )


def test_selector_testnet_wallclock_duration_evidence_plus_dependency_full() -> None:
    sel = _run_selector(*TESTNET_WALLCLOCK_DURATION_EVIDENCE_FILES, "requirements.txt")
    assert sel["test_selection_mode"] == "FULL"
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
    assert sel["test_selection_mode"] == "FOCUSED"
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
    assert sel["test_selection_mode"] == "FOCUSED"
    assert sel["test_selection_reason"] == "testnet_wallclock_duration_evidence_focused"


def test_selector_wallclock_field_name_paired_rewire_shadow_only_unchanged() -> None:
    sel = _run_selector(SHADOW_WALLCLOCK_DURATION_EVIDENCE_TEST_OWNER)
    assert sel["test_selection_mode"] == "FOCUSED"
    assert sel["test_selection_reason"] == "wallclock_focused"


def test_selector_wallclock_field_name_paired_rewire_plus_foreign_test_full() -> None:
    sel = _run_selector(
        *WALLCLOCK_FIELD_NAME_PAIRED_REWIRE_FILES,
        "tests/ops/test_bounded_network_testnet_preflight_contract_v0.py",
    )
    assert sel["test_selection_mode"] == "FULL"
    assert sel["tests_execute_full"] == "true"
    assert sel["test_selection_reason"] != "wallclock_field_name_paired_rewire_no_op"


def test_selector_wallclock_field_name_paired_rewire_plus_src_full() -> None:
    sel = _run_selector(
        *WALLCLOCK_FIELD_NAME_PAIRED_REWIRE_FILES,
        "src/ops/testnet_wallclock_duration_evidence_contract_v0.py",
    )
    assert sel["test_selection_mode"] == "FULL"
    assert (
        sel["test_selection_reason"]
        == "testnet_wallclock_duration_evidence_foreign_path_requires_full"
    )


def test_selector_wallclock_field_name_paired_rewire_plus_dependency_full() -> None:
    sel = _run_selector(*WALLCLOCK_FIELD_NAME_PAIRED_REWIRE_FILES, "requirements.txt")
    assert sel["test_selection_mode"] == "FULL"
    assert (
        sel["test_selection_reason"]
        == "testnet_wallclock_duration_evidence_foreign_path_requires_full"
    )


def test_selector_wallclock_field_name_paired_rewire_plus_third_wallclock_test_full() -> None:
    sel = _run_selector(
        *WALLCLOCK_FIELD_NAME_PAIRED_REWIRE_FILES,
        "tests/ops/test_runtime_wallclock_evidence_emitter_contract_v0.py",
    )
    assert sel["test_selection_mode"] == "FULL"
    assert sel["tests_execute_full"] == "true"
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
    assert sel["test_selection_mode"] == "FOCUSED"
    assert sel["test_selection_reason"] == "ci_bootstrap_focused"
    assert sel["tests_execute_full"] == "false"
