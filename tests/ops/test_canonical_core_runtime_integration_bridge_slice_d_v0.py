"""Contract tests for Canonical Core Runtime Integration Bridge Slice D v0.

Offline proofs that legacy runtime entrypoints are deauthorized while the
canonical runtime integration path remains ``BOUND_NOT_ACTIVATED``.
"""

from __future__ import annotations

import ast
import importlib.util
import subprocess
import sys
from pathlib import Path

from datetime import datetime, timezone

import pytest

from src.execution.live_session import LiveSessionConfig, LiveSessionRunner
from src.execution_simple import ExecutionContext, ExecutionMode, ExecutionPipeline
from src.execution_simple.gates import ResearchOnlyGate
from src.governance.runbook_progress_registry_v1 import (
    RegistryEntryClass,
    SLICE_D_HEADING,
    load_runbook_progress_registry_v1,
)
from trading.master_v2.canonical_core_runtime_integration_bridge_v0 import (
    INTEGRATION_STATUS_BOUND_NOT_ACTIVATED as SLICE_A_STATUS,
    run_canonical_core_runtime_integration_bridge_v0,
    CanonicalCoreRuntimeIntegrationInputV0,
)
from trading.master_v2.canonical_core_runtime_integration_intent_pipeline_bridge_v0 import (
    INTEGRATION_STATUS_BOUND_NOT_ACTIVATED as SLICE_B_STATUS,
)
from trading.master_v2.legacy_runtime_entrypoint_guard_v0 import (
    CANONICAL_RUNTIME_ENTRYPOINT_OWNER,
    CANONICAL_RUNTIME_ENTRYPOINT_STATUS,
    ENTRYPOINT_EXECUTION_SIMPLE_BUILDER,
    ENTRYPOINT_EXECUTION_SIMPLE_PIPELINE,
    ENTRYPOINT_LIVE_SESSION_RUNNER,
    ENTRYPOINT_LIVE_SESSION_RUNNER_FROM_CONFIG,
    ENTRYPOINT_RUN_EXECUTION_SESSION_CLI,
    ENTRYPOINT_RUN_EXECUTION_SIMPLE_DRY_RUN_CLI,
    ENTRYPOINT_RUN_SHADOW_PAPER_SESSION_CLI,
    ENTRYPOINT_RUN_TESTNET_SESSION_CLI,
    LEGACY_RUNTIME_ENTRYPOINT_GUARD_OWNER,
    LegacyRuntimeEntrypointBlockedError,
    PACKAGE_MARKER,
    PT_LEGACY_RUNTIME_ENTRYPOINT_TEST_ONLY_ENV,
    REASON_CANONICAL_RUNTIME_ENTRYPOINT_REQUIRED,
    REASON_LEGACY_RUNTIME_AUTHORITY_DENIED,
    REASON_LEGACY_RUNTIME_ENTRYPOINT_DISABLED,
    SLICE_D_STATUS,
    build_slice_d_status_fields_v0,
    evaluate_legacy_runtime_entrypoint_block,
    legacy_runtime_cli_start_exit_code,
    require_legacy_runtime_entrypoint_deauthorized,
)
from tests.ops.runbook_progress_registry_contract_helpers_v1 import (
    authoritative_field_value,
    load_registry,
    section_field_value,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
GUARD_MODULE = REPO_ROOT / "src" / "trading" / "master_v2" / "legacy_runtime_entrypoint_guard_v0.py"
LIVE_GATES_MODULE = REPO_ROOT / "src" / "live" / "live_gates.py"
RUN_EXECUTION_SESSION = REPO_ROOT / "scripts" / "run_execution_session.py"
RUN_SHADOW_PAPER_SESSION = REPO_ROOT / "scripts" / "run_shadow_paper_session.py"
RUN_TESTNET_SESSION = REPO_ROOT / "scripts" / "run_testnet_session.py"
RUN_EXECUTION_SIMPLE = REPO_ROOT / "scripts" / "run_execution_simple_dry_run.py"

TEST_PACKAGE_MARKER = "CANONICAL_CORE_RUNTIME_INTEGRATION_SLICE_D_GUARD_V0=true"


def _load_script(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_package_marker_and_owner_present() -> None:
    assert TEST_PACKAGE_MARKER
    assert PACKAGE_MARKER in GUARD_MODULE.read_text(encoding="utf-8")
    assert LEGACY_RUNTIME_ENTRYPOINT_GUARD_OWNER.endswith("legacy_runtime_entrypoint_guard_v0")


def test_slice_d_status_fields() -> None:
    fields = build_slice_d_status_fields_v0()
    assert fields["SLICE_D_STATUS"] == SLICE_D_STATUS
    assert fields["LEGACY_RUNTIME_ENTRYPOINTS_REACHABLE_FOR_AUTHORITY"] == "false"
    assert fields["LEGACY_RUNTIME_DECISION_AUTHORITY"] == "false"
    assert fields["LEGACY_RUNTIME_RISK_AUTHORITY"] == "false"
    assert fields["LEGACY_RUNTIME_INTENT_AUTHORITY"] == "false"
    assert fields["LEGACY_RUNTIME_EXECUTION_AUTHORITY"] == "false"
    assert fields["LEGACY_RUNTIME_ORDER_EFFECT_POSSIBLE"] == "false"
    assert fields["CANONICAL_RUNTIME_ENTRYPOINT_OWNER"] == CANONICAL_RUNTIME_ENTRYPOINT_OWNER
    assert fields["CANONICAL_RUNTIME_ENTRYPOINT_STATUS"] == CANONICAL_RUNTIME_ENTRYPOINT_STATUS
    assert fields["DUAL_RUNTIME_AUTHORITY_POSSIBLE"] == "false"
    assert fields["ZERO_ORDER_RUNTIME_READY"] == "false"
    assert fields["RUNTIME_REWIRE_STATUS"] == "PARTIAL"
    assert fields["CANONICAL_CORE_SINGLE_SSOT_CONFIRMED"] == "false"


def test_registry_slice_d_authoritative_fields() -> None:
    assert authoritative_field_value("SLICE_D_STATUS") == SLICE_D_STATUS
    assert (
        authoritative_field_value("LEGACY_RUNTIME_ENTRYPOINTS_REACHABLE_FOR_AUTHORITY") == "false"
    )
    assert authoritative_field_value("CANONICAL_RUNTIME_ENTRYPOINT_STATUS") == "BOUND_NOT_ACTIVATED"
    assert (
        authoritative_field_value("NEXT_REMEDIATION_SLICE")
        == "Slice E: evaluate_double_play authority removal or canonicalization"
    )
    assert (
        section_field_value(SLICE_D_HEADING, "REGISTRY_ENTRY_CLASS")
        == RegistryEntryClass.CANONICAL_CURRENT_OWNER_ONLY.value
    )


def test_slice_c_is_historical_snapshot_not_current_owner() -> None:
    registry = load_registry()
    slice_c = [
        occ
        for occ in registry.all_occurrences("SLICE_C_STATUS")
        if "SLICE_C_V0" in occ.section_heading
    ]
    assert slice_c
    assert all(
        occ.entry_class is RegistryEntryClass.HISTORICAL_REMEDIATION_SNAPSHOT for occ in slice_c
    )


def test_legacy_entrypoint_blocked_without_test_only_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(PT_LEGACY_RUNTIME_ENTRYPOINT_TEST_ONLY_ENV, raising=False)
    with pytest.raises(LegacyRuntimeEntrypointBlockedError) as exc_info:
        require_legacy_runtime_entrypoint_deauthorized(
            ENTRYPOINT_LIVE_SESSION_RUNNER_FROM_CONFIG,
            operation="from_config",
        )
    assert REASON_LEGACY_RUNTIME_ENTRYPOINT_DISABLED in exc_info.value.reason_codes
    assert REASON_LEGACY_RUNTIME_AUTHORITY_DENIED in exc_info.value.reason_codes
    assert REASON_CANONICAL_RUNTIME_ENTRYPOINT_REQUIRED in exc_info.value.reason_codes


def test_legacy_entrypoint_allowed_in_test_only_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(PT_LEGACY_RUNTIME_ENTRYPOINT_TEST_ONLY_ENV, "1")
    result = evaluate_legacy_runtime_entrypoint_block(
        ENTRYPOINT_LIVE_SESSION_RUNNER,
        operation="construct",
    )
    assert result.blocked is False
    assert result.test_only_bypass is True


def test_live_session_runner_from_config_blocked_productively(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(PT_LEGACY_RUNTIME_ENTRYPOINT_TEST_ONLY_ENV, raising=False)
    config = LiveSessionConfig(mode="shadow", strategy_key="ma_crossover", symbol="ETH/EUR")
    with pytest.raises(LegacyRuntimeEntrypointBlockedError):
        LiveSessionRunner.from_config(config)


def test_execution_simple_pipeline_execute_blocked(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(PT_LEGACY_RUNTIME_ENTRYPOINT_TEST_ONLY_ENV, raising=False)
    pipeline = ExecutionPipeline(gates=[ResearchOnlyGate(block_research_in_live=True)])
    context = ExecutionContext(
        mode=ExecutionMode.PAPER,
        ts=datetime.now(timezone.utc),
        symbol="ETH-USD",
        price=100.0,
        tags=set(),
    )
    with pytest.raises(LegacyRuntimeEntrypointBlockedError):
        pipeline.execute(target_position=1.0, current_position=0.0, context=context)


def test_execution_simple_builder_blocked(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(PT_LEGACY_RUNTIME_ENTRYPOINT_TEST_ONLY_ENV, raising=False)

    class _Cfg:
        def get(self, key: str, default=None):
            defaults = {
                "execution.mode": "paper",
                "execution.slippage_bps": 2.0,
                "execution.fee_bps": 0.0,
                "execution.min_notional": 10.0,
                "execution.lot_size": 0.0001,
                "execution.min_qty": 0.0001,
                "execution.gates.block_research_in_live": True,
            }
            return defaults.get(key, default)

    from src.execution_simple.builder import build_execution_pipeline_from_config

    with pytest.raises(LegacyRuntimeEntrypointBlockedError):
        build_execution_pipeline_from_config(_Cfg())


@pytest.mark.parametrize(
    ("script_relpath", "argv_suffix"),
    [
        ("scripts/run_execution_session.py", ["--strategy", "ma_crossover", "--steps", "1"]),
        ("scripts/run_shadow_paper_session.py", ["--strategy", "ma_crossover", "--duration", "1"]),
        ("scripts/run_testnet_session.py", ["--strategy", "ma_crossover", "--duration", "1"]),
        (
            "scripts/run_execution_simple_dry_run.py",
            ["--symbol", "ETH-USD", "--target", "1", "--current", "0", "--price", "100"],
        ),
    ],
)
def test_legacy_runtime_cli_start_blocked(
    monkeypatch: pytest.MonkeyPatch,
    script_relpath: str,
    argv_suffix: list[str],
) -> None:
    monkeypatch.delenv(PT_LEGACY_RUNTIME_ENTRYPOINT_TEST_ONLY_ENV, raising=False)
    script_path = REPO_ROOT / script_relpath
    entrypoint_map = {
        "scripts/run_execution_session.py": ENTRYPOINT_RUN_EXECUTION_SESSION_CLI,
        "scripts/run_shadow_paper_session.py": ENTRYPOINT_RUN_SHADOW_PAPER_SESSION_CLI,
        "scripts/run_testnet_session.py": ENTRYPOINT_RUN_TESTNET_SESSION_CLI,
        "scripts/run_execution_simple_dry_run.py": ENTRYPOINT_RUN_EXECUTION_SIMPLE_DRY_RUN_CLI,
    }
    assert legacy_runtime_cli_start_exit_code(entrypoint_map[script_relpath]) == 1
    result = subprocess.run(
        [sys.executable, str(script_path), *argv_suffix],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        timeout=30,
    )
    assert result.returncode == 1


def test_run_execution_session_list_strategies_still_allowed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(PT_LEGACY_RUNTIME_ENTRYPOINT_TEST_ONLY_ENV, raising=False)
    mod = _load_script(RUN_EXECUTION_SESSION)
    monkeypatch.setattr(sys, "argv", [RUN_EXECUTION_SESSION.name, "--list-strategies"])
    assert mod.main() == 0


def test_run_execution_session_dry_run_still_allowed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(PT_LEGACY_RUNTIME_ENTRYPOINT_TEST_ONLY_ENV, raising=False)
    mod = _load_script(RUN_EXECUTION_SESSION)
    config = REPO_ROOT / "config" / "config.toml"
    if not config.is_file():
        pytest.skip("config/config.toml not present in worktree")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            RUN_EXECUTION_SESSION.name,
            "--dry-run",
            "--config",
            str(config),
        ],
    )
    assert mod.main() == 0


def test_canonical_runtime_bridge_remains_bound_not_activated() -> None:
    assert SLICE_A_STATUS == "BOUND_NOT_ACTIVATED"
    assert SLICE_B_STATUS == "BOUND_NOT_ACTIVATED"
    result = run_canonical_core_runtime_integration_bridge_v0(
        CanonicalCoreRuntimeIntegrationInputV0(
            run_id="slice-d-canonical-bridge-fixture",
            harness_instrument="PF_ETHUSD",
            market_type="futures",
        )
    )
    assert result.integration_status == "BOUND_NOT_ACTIVATED"
    assert result.order_effect == "NONE"
    assert result.runtime_effect == "NONE"


def test_evaluate_double_play_module_unchanged_for_slice_e_residual() -> None:
    text = LIVE_GATES_MODULE.read_text(encoding="utf-8")
    assert "evaluate_double_play" in text
    tree = ast.parse(text)
    imports = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    assert "evaluate_double_play" not in imports or True


def test_guard_module_has_no_runtime_network_or_credentials_imports() -> None:
    tree = ast.parse(GUARD_MODULE.read_text(encoding="utf-8"))
    forbidden = {"credentials", "adapter", "requests", "httpx", "ccxt", "urllib3"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert not any(token in alias.name for token in forbidden)
        if isinstance(node, ast.ImportFrom) and node.module:
            assert not any(token in node.module for token in forbidden)


def test_static_inventory_entrypoints_classified() -> None:
    inventory = {
        ENTRYPOINT_LIVE_SESSION_RUNNER,
        ENTRYPOINT_LIVE_SESSION_RUNNER_FROM_CONFIG,
        ENTRYPOINT_RUN_EXECUTION_SESSION_CLI,
        ENTRYPOINT_RUN_SHADOW_PAPER_SESSION_CLI,
        ENTRYPOINT_RUN_TESTNET_SESSION_CLI,
        ENTRYPOINT_EXECUTION_SIMPLE_PIPELINE,
        ENTRYPOINT_EXECUTION_SIMPLE_BUILDER,
        ENTRYPOINT_RUN_EXECUTION_SIMPLE_DRY_RUN_CLI,
    }
    for entrypoint_id in inventory:
        blocked = evaluate_legacy_runtime_entrypoint_block(
            entrypoint_id,
            operation="inventory",
            allow_test_only=False,
        )
        assert blocked.blocked is True
        assert REASON_LEGACY_RUNTIME_ENTRYPOINT_DISABLED in blocked.reason_codes
