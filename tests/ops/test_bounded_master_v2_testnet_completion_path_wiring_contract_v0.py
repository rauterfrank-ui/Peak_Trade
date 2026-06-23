"""Static contract: bounded Master V2 testnet completion path wiring v0."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

from src.ops.bounded_master_v2_testnet_completion_path_wiring_v0 import (
    BOUNDED_MASTER_V2_TESTNET_COMPLETION_PATH_WIRING_OWNER,
    CANONICAL_MASTER_V2_REPLAY_OWNER,
    CANONICAL_RETENTION_OWNER,
    CANONICAL_SIX_NODE_GRAPH_OWNER,
    CANONICAL_TESTNET_COMPLETION_OWNER,
    CANONICAL_TESTNET_RUNNER,
    TestnetCompletionPathMarketInputV0,
    assert_forbidden_testnet_execution_claims_absent,
    build_testnet_bounded_adapter_completion_path_wiring_section,
    evaluate_bounded_master_v2_testnet_completion_path_wiring,
    validate_testnet_completion_path_market_input,
)
from trading.master_v2.double_play_state import ScopeEvent
from trading.master_v2.offline_double_play_scenario_replay_v0 import (
    OfflineDoublePlayScenarioTickV0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
ADAPTER_SCRIPT = REPO_ROOT / "scripts" / "ops" / "run_testnet_bounded_observation_adapter_v0.py"
WIRING_OWNER = REPO_ROOT / "src" / "ops" / "bounded_master_v2_testnet_completion_path_wiring_v0.py"
OFFLINE_REPLAY_OPS_TEST = (
    REPO_ROOT
    / "tests"
    / "ops"
    / "test_offline_master_v2_double_play_scenario_replay_completion_binding_contract_v0.py"
)
COMPLETION_INTEGRATION_TEST = (
    REPO_ROOT
    / "tests"
    / "ops"
    / "test_bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0.py"
)
ADAPTER_TEST = REPO_ROOT / "tests" / "ops" / "test_run_testnet_bounded_observation_adapter_v0.py"


def _load_adapter():
    spec = importlib.util.spec_from_file_location(
        "run_testnet_bounded_observation_adapter_v0", ADAPTER_SCRIPT
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_canonical_owner_paths_present() -> None:
    assert WIRING_OWNER.is_file()
    assert Path(REPO_ROOT / CANONICAL_TESTNET_RUNNER).is_file()
    assert Path(REPO_ROOT / CANONICAL_TESTNET_COMPLETION_OWNER).is_file()
    assert Path(REPO_ROOT / CANONICAL_MASTER_V2_REPLAY_OWNER).is_file()
    assert Path(REPO_ROOT / CANONICAL_SIX_NODE_GRAPH_OWNER).is_file()
    assert Path(REPO_ROOT / CANONICAL_RETENTION_OWNER).is_file()


def test_static_wiring_flags_present_without_market_input() -> None:
    result = evaluate_bounded_master_v2_testnet_completion_path_wiring(None)
    machine = result.to_machine_lines()
    assert result.admission_pass is False
    assert result.wiring_pass is False
    assert result.missing_testnet_market_input_fails_closed is True
    assert machine["BOUNDED_TESTNET_COMPLETION_PATH_MASTER_V2_WIRING_PRESENT"] is True
    assert machine["BOUNDED_TESTNET_COMPLETION_PATH_SIX_NODE_GRAPH_WIRING_PRESENT"] is True
    assert machine["BOUNDED_TESTNET_COMPLETION_PATH_DECISION_DIGEST_WIRING_PRESENT"] is True
    assert machine["BOUNDED_TESTNET_COMPLETION_PATH_RETENTION_WIRING_PRESENT"] is True
    assert machine["BOUNDED_TESTNET_ZERO_ORDER_ADMISSION_BOUNDARY_PRESENT"] is True
    assert machine["MISSING_TESTNET_MARKET_INPUT_FAILS_CLOSED"] is True
    assert machine["TESTNET_RUNNER_REUSES_CANONICAL_COMPLETION_PATH"] is True
    assert machine["TESTNET_EXECUTES_CANONICAL_MASTER_V2"] is False
    assert machine["TESTNET_SIX_NODE_VALIDATION_GRAPH_PROVEN"] is False


def test_synthetic_offline_fixture_rejected() -> None:
    market_input = TestnetCompletionPathMarketInputV0(
        selected_future_id="ETH-PERP",
        ticks=(
            OfflineDoublePlayScenarioTickV0(
                tick_index=0,
                timestamp_ms=1_700_000_000_000,
                price=100.0,
                scope_event=ScopeEvent.NOOP,
            ),
        ),
        source_run_id="fixture-run",
        synthetic_offline_fixture=True,
    )
    reasons = validate_testnet_completion_path_market_input(market_input)
    assert reasons
    result = evaluate_bounded_master_v2_testnet_completion_path_wiring(market_input)
    assert result.admission_pass is False


def test_btc_instrument_rejected() -> None:
    market_input = TestnetCompletionPathMarketInputV0(
        selected_future_id="XBT-PERP",
        ticks=(
            OfflineDoublePlayScenarioTickV0(
                tick_index=0,
                timestamp_ms=1_700_000_000_000,
                price=100.0,
                scope_event=ScopeEvent.NOOP,
            ),
        ),
        source_run_id="run-1",
    )
    reasons = validate_testnet_completion_path_market_input(market_input)
    assert reasons
    result = evaluate_bounded_master_v2_testnet_completion_path_wiring(market_input)
    assert result.admission_pass is False


def test_adapter_plan_includes_completion_path_wiring_section() -> None:
    mod = _load_adapter()
    plan = mod.build_plan(
        mode="plan-only",
        staging_root=Path("/tmp/peak_trade_testnet_wiring_plan"),
        archive_root=Path(
            "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
        ),
        repo_root=REPO_ROOT,
        duration_minutes=10,
        max_steps=120,
        step_interval_seconds=0.0,
        run_id="wiring_plan_test",
    )
    payload = plan.to_dict()
    wiring = payload["completion_path_wiring"]
    assert wiring["owner"] == BOUNDED_MASTER_V2_TESTNET_COMPLETION_PATH_WIRING_OWNER
    assert wiring["admission_pass"] is False
    assert wiring["machine_summary"]["TESTNET_EXECUTES_CANONICAL_MASTER_V2"] is False


def test_adapter_plan_json_emits_wiring_metadata(tmp_path: Path) -> None:
    mod = _load_adapter()
    staging = Path("/tmp") / f"peak_trade_testnet_wiring_json_{tmp_path.name}"
    argv = [
        "--staging-root",
        str(staging),
        "--archive-root",
        "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z",
        "--repo-root",
        str(REPO_ROOT),
        "--run-id",
        "wiring_json_test",
        "--json",
    ]
    rc = mod.main(argv)
    assert rc == 0


def test_build_section_matches_evaluator() -> None:
    section = build_testnet_bounded_adapter_completion_path_wiring_section(
        run_id="section-test",
        mode="plan-only",
    )
    assert section["canonical_testnet_runner"] == CANONICAL_TESTNET_RUNNER
    assert section["machine_summary"]["MISSING_TESTNET_MARKET_INPUT_FAILS_CLOSED"] is True


def test_forbidden_testnet_execution_claims_guard() -> None:
    violations = assert_forbidden_testnet_execution_claims_absent(
        {"TESTNET_EXECUTES_CANONICAL_MASTER_V2": True}
    )
    assert violations


@pytest.mark.parametrize(
    "owner_path",
    [
        OFFLINE_REPLAY_OPS_TEST,
        COMPLETION_INTEGRATION_TEST,
        ADAPTER_TEST,
    ],
)
def test_required_existing_test_owners_present(owner_path: Path) -> None:
    assert owner_path.is_file()


def test_wiring_owner_references_completion_chain_symbols() -> None:
    text = WIRING_OWNER.read_text(encoding="utf-8")
    assert "prove_offline_replay_six_node_validation_graph_binding_v0" in text
    assert "evaluate_durable_run_primary_evidence_completion_integration" in text
    assert "verify_manifest_sha256" in text
    assert "build_default_bull_bear_bull_scenario_ticks" not in text
