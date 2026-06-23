"""Static contract: bounded Master V2 testnet completion path wiring v0."""

from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

import pytest

from src.ops.bounded_master_v2_testnet_completion_path_wiring_v0 import (
    BOUNDED_MASTER_V2_TESTNET_COMPLETION_PATH_WIRING_OWNER,
    CANONICAL_MASTER_V2_REPLAY_OWNER,
    CANONICAL_RETENTION_OWNER,
    CANONICAL_RETENTION_VERIFY_OWNER,
    CANONICAL_SIX_NODE_GRAPH_OWNER,
    CANONICAL_TESTNET_COMPLETION_OWNER,
    CANONICAL_TESTNET_RUNNER,
    TestnetCompletionPathMarketInputV0,
    TestnetCompletionPathRetentionVerificationResultV0,
    assert_forbidden_testnet_execution_claims_absent,
    build_testnet_bounded_adapter_completion_path_wiring_section,
    evaluate_bounded_master_v2_testnet_completion_path_wiring,
    run_canonical_retention_manifest_verification,
    validate_testnet_completion_path_market_input,
    verify_dashboard_display_projection_digest_wiring,
    verify_testnet_completion_path_retention_wiring,
)
from scripts.ops.primary_evidence_retention_v0 import write_manifest_sha256
from src.ops.offline_master_v2_replay_six_node_validation_graph_binding_v0 import (
    OfflineReplaySixNodeValidationGraphBindingResultV0,
    build_completion_integration_input_from_offline_replay_result,
    prove_offline_replay_six_node_validation_graph_binding_v0,
)
from trading.master_v2.double_play_state import ScopeEvent
from trading.master_v2.offline_double_play_scenario_replay_v0 import (
    SYNTHETIC_FUTURES_INSTRUMENT,
    OfflineDoublePlayScenarioReplayInputV0,
    OfflineDoublePlayScenarioReplayResultV0,
    OfflineDoublePlayScenarioTickV0,
    build_default_bull_bear_bull_scenario_ticks,
    run_offline_double_play_scenario_replay_v0,
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


def _valid_market_input() -> TestnetCompletionPathMarketInputV0:
    return TestnetCompletionPathMarketInputV0(
        selected_future_id=SYNTHETIC_FUTURES_INSTRUMENT,
        ticks=build_default_bull_bear_bull_scenario_ticks(),
        source_run_id="gap004-digest-wiring",
    )


def _valid_retention_verification(
    tmp_path: Path,
) -> TestnetCompletionPathRetentionVerificationResultV0:
    archive = tmp_path / "archive"
    archive.mkdir()
    (archive / "RUN_METADATA.json").write_text("{}", encoding="utf-8")
    write_manifest_sha256(archive)
    return run_canonical_retention_manifest_verification(archive)


@pytest.fixture(scope="module", name="replay_result")
def _replay_result() -> OfflineDoublePlayScenarioReplayResultV0:
    replay = run_offline_double_play_scenario_replay_v0(
        OfflineDoublePlayScenarioReplayInputV0(
            selected_future_id=SYNTHETIC_FUTURES_INSTRUMENT,
            ticks=build_default_bull_bear_bull_scenario_ticks(),
            source_revision="gap004-testnet-wiring-v0",
        )
    )
    assert replay.replay_pass, replay.fail_reasons
    return replay


@pytest.fixture(scope="module", name="six_node_binding")
def _six_node_binding() -> OfflineReplaySixNodeValidationGraphBindingResultV0:
    binding = prove_offline_replay_six_node_validation_graph_binding_v0()
    assert binding.binding_pass, binding.fail_reasons
    return binding


@pytest.fixture(scope="module", name="integration_input")
def _integration_input(replay_result: OfflineDoublePlayScenarioReplayResultV0):
    return build_completion_integration_input_from_offline_replay_result(replay_result)


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
    assert machine["BOUNDED_TESTNET_COMPLETION_PATH_RETENTION_WIRING_PRESENT"] is False
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
    assert "verify_dashboard_display_projection_digest_wiring" in text
    assert "six_node_binding" in text
    assert "build_default_bull_bear_bull_scenario_ticks" not in text


def test_wiring_exposes_canonical_dashboard_display_projection_digest(
    replay_result: OfflineDoublePlayScenarioReplayResultV0,
) -> None:
    result = evaluate_bounded_master_v2_testnet_completion_path_wiring(_valid_market_input())
    assert result.dashboard_display_projection_digest is not None
    assert len(result.dashboard_display_projection_digest) == 64
    assert (
        result.dashboard_display_projection_digest
        == replay_result.dashboard_display_projection_digest
    )
    binding = replay_result.master_v2_decision_state_digest_binding
    assert binding is not None
    assert result.dashboard_display_projection_digest == binding.dashboard_display_projection_digest


def test_machine_lines_contains_dashboard_display_projection_digest() -> None:
    result = evaluate_bounded_master_v2_testnet_completion_path_wiring(_valid_market_input())
    machine = result.to_machine_lines()
    assert (
        machine["DASHBOARD_DISPLAY_PROJECTION_DIGEST"] == result.dashboard_display_projection_digest
    )
    assert machine["DASHBOARD_DISPLAY_PROJECTION_DIGEST"] != ""


def test_adapter_section_contains_dashboard_display_projection_digest() -> None:
    section = build_testnet_bounded_adapter_completion_path_wiring_section(
        run_id="digest-section-test",
        mode="plan-only",
        market_input=_valid_market_input(),
    )
    assert section["dashboard_display_projection_digest"] is not None
    assert (
        section["machine_summary"]["DASHBOARD_DISPLAY_PROJECTION_DIGEST"]
        == section["dashboard_display_projection_digest"]
    )


def test_missing_dashboard_display_projection_digest_fails_closed(
    replay_result: OfflineDoublePlayScenarioReplayResultV0,
    integration_input,
    six_node_binding: OfflineReplaySixNodeValidationGraphBindingResultV0,
) -> None:
    bad_replay = replace(replay_result, dashboard_display_projection_digest=None)
    digest, reasons = verify_dashboard_display_projection_digest_wiring(
        bad_replay,
        integration_input,
        six_node_binding,
    )
    assert digest is None
    assert any("dashboard_display_projection_digest missing" in reason for reason in reasons)


def test_dashboard_display_projection_digest_drift_fails_closed(
    replay_result: OfflineDoublePlayScenarioReplayResultV0,
    integration_input,
    six_node_binding: OfflineReplaySixNodeValidationGraphBindingResultV0,
) -> None:
    bad_chain = replace(
        integration_input.completion_proof_chain,
        completion_referenced_dashboard_display_projection_digest="0" * 64,
    )
    bad_input = replace(integration_input, completion_proof_chain=bad_chain)
    digest, reasons = verify_dashboard_display_projection_digest_wiring(
        replay_result,
        bad_input,
        six_node_binding,
    )
    assert digest is not None
    assert any("dashboard_display_projection_digest" in reason for reason in reasons)


def test_dashboard_display_projection_digest_mismatch_fails_closed(
    replay_result: OfflineDoublePlayScenarioReplayResultV0,
    integration_input,
    six_node_binding: OfflineReplaySixNodeValidationGraphBindingResultV0,
) -> None:
    binding = replay_result.master_v2_decision_state_digest_binding
    assert binding is not None
    bad_binding = replace(binding, dashboard_display_projection_digest="1" * 64)
    bad_replay = replace(
        replay_result,
        master_v2_decision_state_digest_binding=bad_binding,
    )
    digest, reasons = verify_dashboard_display_projection_digest_wiring(
        bad_replay,
        integration_input,
        six_node_binding,
    )
    assert digest is not None
    assert any("drift: replay vs decision state binding" in reason for reason in reasons)


def test_evaluator_fails_closed_on_display_projection_digest_drift(
    integration_input,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bad_chain = replace(
        integration_input.completion_proof_chain,
        completion_referenced_dashboard_display_projection_digest="0" * 64,
    )
    bad_input = replace(integration_input, completion_proof_chain=bad_chain)

    def _bad_builder(replay_result: OfflineDoublePlayScenarioReplayResultV0):
        return bad_input

    monkeypatch.setattr(
        "src.ops.bounded_master_v2_testnet_completion_path_wiring_v0."
        "build_completion_integration_input_from_offline_replay_result",
        _bad_builder,
    )
    result = evaluate_bounded_master_v2_testnet_completion_path_wiring(_valid_market_input())
    assert result.wiring_pass is False
    assert any("dashboard_display_projection_digest" in reason for reason in result.fail_reasons)


def test_zero_order_and_no_execution_authority_with_valid_market_input() -> None:
    result = evaluate_bounded_master_v2_testnet_completion_path_wiring(_valid_market_input())
    machine = result.to_machine_lines()
    assert result.orders_total == 0
    assert result.cancels_total == 0
    assert result.fills_total == 0
    assert result.positions_opened_total == 0
    assert machine["TESTNET_EXECUTES_CANONICAL_MASTER_V2"] is False
    assert machine["ORDERS_TOTAL"] == 0


def test_six_node_digest_crosscheck_accepts_valid_binding(
    replay_result: OfflineDoublePlayScenarioReplayResultV0,
    integration_input,
    six_node_binding: OfflineReplaySixNodeValidationGraphBindingResultV0,
) -> None:
    digest, reasons = verify_dashboard_display_projection_digest_wiring(
        replay_result,
        integration_input,
        six_node_binding,
    )
    assert digest == replay_result.dashboard_display_projection_digest
    assert reasons == []


def test_six_node_digest_matches_replay_in_wiring_verifier(
    replay_result: OfflineDoublePlayScenarioReplayResultV0,
    six_node_binding: OfflineReplaySixNodeValidationGraphBindingResultV0,
) -> None:
    assert (
        six_node_binding.dashboard_display_projection_digest
        == replay_result.dashboard_display_projection_digest
    )


def test_six_node_digest_matches_decision_state_in_wiring_verifier(
    replay_result: OfflineDoublePlayScenarioReplayResultV0,
    six_node_binding: OfflineReplaySixNodeValidationGraphBindingResultV0,
) -> None:
    binding = replay_result.master_v2_decision_state_digest_binding
    assert binding is not None
    assert (
        six_node_binding.dashboard_display_projection_digest
        == binding.dashboard_display_projection_digest
    )


def test_six_node_digest_matches_completion_proof_in_wiring_verifier(
    integration_input,
    six_node_binding: OfflineReplaySixNodeValidationGraphBindingResultV0,
) -> None:
    chain = integration_input.completion_proof_chain
    assert chain is not None
    assert (
        six_node_binding.dashboard_display_projection_digest
        == chain.completion_referenced_dashboard_display_projection_digest
    )


def test_six_node_digest_matches_testnet_completion_in_wiring_verifier(
    six_node_binding: OfflineReplaySixNodeValidationGraphBindingResultV0,
) -> None:
    result = evaluate_bounded_master_v2_testnet_completion_path_wiring(_valid_market_input())
    assert (
        result.dashboard_display_projection_digest
        == six_node_binding.dashboard_display_projection_digest
    )


def test_missing_six_node_digest_fails_closed_in_wiring_verifier(
    replay_result: OfflineDoublePlayScenarioReplayResultV0,
    integration_input,
    six_node_binding: OfflineReplaySixNodeValidationGraphBindingResultV0,
) -> None:
    bad_six_node = replace(
        six_node_binding,
        dashboard_display_projection_digest=None,
    )
    digest, reasons = verify_dashboard_display_projection_digest_wiring(
        replay_result,
        integration_input,
        bad_six_node,
    )
    assert digest is not None
    assert any("missing from six-node binding result" in reason for reason in reasons)


def test_six_node_digest_mismatch_fails_closed_in_wiring_verifier(
    replay_result: OfflineDoublePlayScenarioReplayResultV0,
    integration_input,
    six_node_binding: OfflineReplaySixNodeValidationGraphBindingResultV0,
) -> None:
    bad_six_node = replace(
        six_node_binding,
        dashboard_display_projection_digest="2" * 64,
    )
    digest, reasons = verify_dashboard_display_projection_digest_wiring(
        replay_result,
        integration_input,
        bad_six_node,
    )
    assert digest is not None
    assert any("drift: replay vs six-node binding result" in reason for reason in reasons)


def test_six_node_only_digest_drift_fails_closed_in_wiring_verifier(
    replay_result: OfflineDoublePlayScenarioReplayResultV0,
    integration_input,
    six_node_binding: OfflineReplaySixNodeValidationGraphBindingResultV0,
) -> None:
    bad_six_node = replace(
        six_node_binding,
        dashboard_display_projection_digest="3" * 64,
    )
    digest, reasons = verify_dashboard_display_projection_digest_wiring(
        replay_result,
        integration_input,
        bad_six_node,
    )
    assert digest is not None
    assert any("replay vs six-node binding result" in reason for reason in reasons)
    assert any("six-node binding result vs decision state binding" in reason for reason in reasons)


def test_evaluator_fails_closed_on_six_node_digest_drift(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    real_prove = prove_offline_replay_six_node_validation_graph_binding_v0

    def _bad_prove(*args, **kwargs):
        binding = real_prove(*args, **kwargs)
        return replace(binding, dashboard_display_projection_digest="4" * 64)

    monkeypatch.setattr(
        "src.ops.bounded_master_v2_testnet_completion_path_wiring_v0."
        "prove_offline_replay_six_node_validation_graph_binding_v0",
        _bad_prove,
    )
    result = evaluate_bounded_master_v2_testnet_completion_path_wiring(_valid_market_input())
    assert result.wiring_pass is False
    assert any("six-node binding result" in reason for reason in result.fail_reasons)


def test_wiring_verifier_does_not_recompute_six_node_digest() -> None:
    text = WIRING_OWNER.read_text(encoding="utf-8")
    assert "dashboard_display_projection_digest" in text
    assert "hashlib" not in text
    assert "hashlib.sha256" not in text


def test_identical_input_yields_identical_crosscheck_result() -> None:
    first = evaluate_bounded_master_v2_testnet_completion_path_wiring(_valid_market_input())
    second = evaluate_bounded_master_v2_testnet_completion_path_wiring(_valid_market_input())
    assert first.dashboard_display_projection_digest == second.dashboard_display_projection_digest
    assert first.wiring_pass == second.wiring_pass
    assert first.fail_reasons == second.fail_reasons


def test_hasattr_only_does_not_satisfy_retention_wiring_without_executed_result() -> None:
    result = evaluate_bounded_master_v2_testnet_completion_path_wiring(_valid_market_input())
    assert result.bounded_testnet_completion_path_retention_wiring_present is False
    assert any("retention verification result required" in reason for reason in result.fail_reasons)


def test_valid_executed_retention_verification_accepted(tmp_path: Path) -> None:
    retention = _valid_retention_verification(tmp_path)
    result = evaluate_bounded_master_v2_testnet_completion_path_wiring(
        _valid_market_input(),
        retention_verification=retention,
        expected_archive_root=retention.archive_root,
    )
    assert result.bounded_testnet_completion_path_retention_wiring_present is True
    assert result.wiring_pass is True
    assert retention.verify_owner == CANONICAL_RETENTION_VERIFY_OWNER


def test_missing_retention_result_fails_closed() -> None:
    reasons = verify_testnet_completion_path_retention_wiring(None)
    assert reasons == ["retention verification result required"]
    result = evaluate_bounded_master_v2_testnet_completion_path_wiring(_valid_market_input())
    assert result.wiring_pass is False
    assert any("retention verification result required" in reason for reason in result.fail_reasons)


def test_failed_retention_result_fails_closed() -> None:
    failed = TestnetCompletionPathRetentionVerificationResultV0(
        verify_pass=False,
        verify_message="MANIFEST.sha256 missing",
        verify_owner=CANONICAL_RETENTION_VERIFY_OWNER,
    )
    reasons = verify_testnet_completion_path_retention_wiring(failed)
    assert any("retention verification failed" in reason for reason in reasons)
    result = evaluate_bounded_master_v2_testnet_completion_path_wiring(
        _valid_market_input(),
        retention_verification=failed,
    )
    assert result.wiring_pass is False
    assert result.bounded_testnet_completion_path_retention_wiring_present is False


def test_retention_owner_drift_fails_closed() -> None:
    drifted = TestnetCompletionPathRetentionVerificationResultV0(
        verify_pass=True,
        verify_message="",
        verify_owner="parallel.retention.owner",
    )
    reasons = verify_testnet_completion_path_retention_wiring(drifted)
    assert any("retention verify owner drift" in reason for reason in reasons)


def test_retention_archive_root_mismatch_fails_closed(tmp_path: Path) -> None:
    retention = _valid_retention_verification(tmp_path)
    reasons = verify_testnet_completion_path_retention_wiring(
        retention,
        expected_archive_root=str(tmp_path / "other"),
    )
    assert any("archive_root mismatch" in reason for reason in reasons)


def test_adapter_section_binds_retention_verification_result(tmp_path: Path) -> None:
    retention = _valid_retention_verification(tmp_path)
    section = build_testnet_bounded_adapter_completion_path_wiring_section(
        run_id="retention-section-test",
        mode="plan-only",
        market_input=_valid_market_input(),
        retention_verification=retention,
        expected_archive_root=retention.archive_root,
    )
    assert section["retention_verify_owner"] == CANONICAL_RETENTION_VERIFY_OWNER
    assert section["retention_verification"]["verify_pass"] is True
    assert section["machine_summary"]["BOUNDED_TESTNET_COMPLETION_PATH_RETENTION_WIRING_PRESENT"]


def test_wiring_owner_uses_canonical_retention_verifier_not_hasattr() -> None:
    text = WIRING_OWNER.read_text(encoding="utf-8")
    assert "hasattr(primary_evidence_retention_v0" not in text
    assert "verify_testnet_completion_path_retention_wiring" in text
    assert "run_canonical_retention_manifest_verification" in text


def test_wiring_verifier_does_not_recompute_retention_digest() -> None:
    text = WIRING_OWNER.read_text(encoding="utf-8")
    assert "verify_manifest_sha256" in text
    assert "hashlib" not in text
    assert "hashlib.sha256" not in text
