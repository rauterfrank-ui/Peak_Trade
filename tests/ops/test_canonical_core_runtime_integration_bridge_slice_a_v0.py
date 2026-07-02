"""Contract tests for Canonical Core Runtime Integration Bridge Slice A v0.

Offline, I/O-free proofs that zero-order harness inputs consume the canonical
``run_integrated_offline_trading_logic_replay_v1`` decision core without legacy
parallel authority or execution effects.
"""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

import pytest

from scripts.ops import archive_futures_testnet_harness_v0 as harness
from trading.master_v2.canonical_core_runtime_integration_bridge_v0 import (
    CANONICAL_CORE_RUNTIME_INTEGRATION_BRIDGE_OWNER,
    INTEGRATION_STATUS_BOUND_NOT_ACTIVATED,
    NEXT_REMEDIATION_SLICE,
    PACKAGE_MARKER,
    CanonicalCoreRuntimeIntegrationInputV0,
    build_integrated_offline_replay_input_from_harness_v0,
    map_harness_instrument_to_canonical_id,
    run_canonical_core_runtime_integration_bridge_v0,
    serialize_canonical_decision_evidence_for_parity,
)
from trading.master_v2.canonical_market_context_v1 import (
    BarFinalityStatus,
    WarmupStatus,
)
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_OWNER,
    run_integrated_offline_trading_logic_replay_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
BRIDGE_MODULE = (
    REPO_ROOT / "src" / "trading" / "master_v2" / "canonical_core_runtime_integration_bridge_v0.py"
)
HARNESS_SCRIPT = REPO_ROOT / "scripts" / "ops" / "archive_futures_testnet_harness_v0.py"
REPLAY_MODULE = (
    REPO_ROOT / "src" / "trading" / "master_v2" / "integrated_offline_trading_logic_replay_v1.py"
)

TEST_PACKAGE_MARKER = "CANONICAL_CORE_RUNTIME_INTEGRATION_SLICE_A_GUARD_V0=true"


def _default_integration_input(**overrides: object) -> CanonicalCoreRuntimeIntegrationInputV0:
    base = {
        "run_id": "slice-a-contract-fixture",
        "harness_instrument": "PF_ETHUSD",
        "market_type": "futures",
    }
    base.update(overrides)
    return CanonicalCoreRuntimeIntegrationInputV0(**base)


def test_package_marker_and_owner_present() -> None:
    assert TEST_PACKAGE_MARKER
    assert PACKAGE_MARKER in BRIDGE_MODULE.read_text(encoding="utf-8")
    assert CANONICAL_CORE_RUNTIME_INTEGRATION_BRIDGE_OWNER.endswith(
        "canonical_core_runtime_integration_bridge_v0"
    )


def test_bridge_consumes_canonical_decision_core_owner() -> None:
    result = run_canonical_core_runtime_integration_bridge_v0(_default_integration_input())
    assert result.canonical_core_consumed is True
    assert result.replay_owner == INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_OWNER
    assert result.replay_owner.endswith("integrated_offline_trading_logic_replay_v1")


def test_no_legacy_double_play_or_generate_signals_imports_in_bridge() -> None:
    tree = ast.parse(BRIDGE_MODULE.read_text(encoding="utf-8"))
    forbidden_modules = {
        "live_gates",
        "live_session",
        "generate_signals",
        "evaluate_double_play",
        "create_strategy_from_config",
        "execution",
        "adapter",
        "credentials",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert not any(f in alias.name for f in forbidden_modules)
        if isinstance(node, ast.ImportFrom) and node.module:
            assert not any(f in node.module for f in forbidden_modules)


def test_identical_canonical_input_produces_same_decision_digest_as_offline_replay() -> None:
    integration_input = _default_integration_input()
    bridge_replay_input, errors = build_integrated_offline_replay_input_from_harness_v0(
        integration_input
    )
    assert errors == ()
    assert bridge_replay_input is not None

    bridge_result = run_canonical_core_runtime_integration_bridge_v0(integration_input)
    direct_result = run_integrated_offline_trading_logic_replay_v1(bridge_replay_input)

    assert bridge_result.decision_semantic_digest == direct_result.evidence.semantic_digest
    assert serialize_canonical_decision_evidence_for_parity(direct_result) == json.dumps(
        json.loads(serialize_canonical_decision_evidence_for_parity(direct_result)),
        sort_keys=True,
        separators=(",", ":"),
    )
    assert (
        hashlib.sha256(
            serialize_canonical_decision_evidence_for_parity(direct_result).encode("utf-8")
        ).hexdigest()
        == hashlib.sha256(
            json.dumps(
                json.loads(serialize_canonical_decision_evidence_for_parity(direct_result)),
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
    )


def test_no_duplicated_bull_bear_scope_double_play_evaluation_in_bridge() -> None:
    """Bridge delegates to replay orchestrator; no local directional/composition evaluators."""
    source = BRIDGE_MODULE.read_text(encoding="utf-8")
    assert "evaluate_directional_assessment_v1" not in source
    assert "evaluate_double_play_composition_matrix_v1" not in source
    assert "evaluate_double_play_entry_exit_policy_v0" not in source
    assert "generate_deterministic_scope_event" not in source
    assert "run_integrated_offline_trading_logic_replay_v1" in source


@pytest.mark.parametrize(
    "kwargs,expected_reason_fragment",
    [
        ({"run_id": ""}, "run_id_missing"),
        ({"market_type": "spot"}, "market_type_not_futures"),
        ({"harness_instrument": "BTCUSDT"}, "instrument_kind_forbidden"),
        ({"harness_instrument": "PF_XBTUSD"}, "instrument_kind_forbidden"),
        ({"harness_instrument": "ETH/EUR"}, "harness_instrument_unmapped"),
        (
            {"bar_finality_status": BarFinalityStatus.UNFINALIZED},
            "trading_epoch_unfinalized",
        ),
        ({"warmup_status": WarmupStatus.WARMUP_REQUIRED}, "warmup_incomplete"),
    ],
)
def test_fail_closed_on_invalid_runtime_inputs(kwargs, expected_reason_fragment) -> None:
    result = run_canonical_core_runtime_integration_bridge_v0(_default_integration_input(**kwargs))
    assert result.integration_pass is False
    assert result.canonical_core_consumed is False
    assert any(expected_reason_fragment in reason for reason in result.fail_reasons)


def test_futures_only_enforced() -> None:
    result = run_canonical_core_runtime_integration_bridge_v0(
        _default_integration_input(market_type="synthetic_spot")
    )
    assert result.integration_pass is False
    assert "market_type_not_futures" in result.fail_reasons


def test_bitcoin_instruments_blocked() -> None:
    for instrument in ("BTCUSDT", "PF_XBTUSD", "XBTUSD", "bitcoin-perp"):
        assert map_harness_instrument_to_canonical_id(instrument) is None
        result = run_canonical_core_runtime_integration_bridge_v0(
            _default_integration_input(harness_instrument=instrument)
        )
        assert result.integration_pass is False


def test_spot_instruments_blocked() -> None:
    result = run_canonical_core_runtime_integration_bridge_v0(
        _default_integration_input(harness_instrument="ETH/EUR", market_type="spot")
    )
    assert result.integration_pass is False


def test_execution_eligible_remains_false() -> None:
    result = run_canonical_core_runtime_integration_bridge_v0(_default_integration_input())
    assert result.execution_eligible is False


def test_no_order_runtime_adapter_credential_effects() -> None:
    result = run_canonical_core_runtime_integration_bridge_v0(_default_integration_input())
    assert result.authority_effect == "NONE"
    assert result.runtime_effect == "NONE"
    assert result.order_effect == "NONE"
    assert result.adapter_submission is False
    assert result.credentials_required is False
    assert result.private_endpoint_required is False


def test_legacy_and_canonical_core_do_not_share_decision_authority() -> None:
    result = run_canonical_core_runtime_integration_bridge_v0(_default_integration_input())
    assert result.legacy_decision_authority_active is False
    assert result.dual_authority_possible is False
    assert result.authority_effect == "NONE"


def test_integration_status_bound_not_activated() -> None:
    result = run_canonical_core_runtime_integration_bridge_v0(_default_integration_input())
    assert result.integration_status == INTEGRATION_STATUS_BOUND_NOT_ACTIVATED


def test_next_remediation_slice_points_to_slice_b() -> None:
    assert "Slice B" in NEXT_REMEDIATION_SLICE
    fields = harness.run_zero_order_canonical_core_integration(
        run_id="slice-a",
        instrument="PF_ETHUSD",
        market_type="futures",
    )
    assert fields["next_remediation_slice"] == NEXT_REMEDIATION_SLICE
    assert fields["runtime_rewire_status"] == "FAIL"


def test_harness_wires_canonical_core_consumption_into_evidence_payload() -> None:
    timing = harness.HarnessTiming(
        monotonic_start=0.0,
        monotonic_end=1.0,
        wall_clock_start_utc="2026-07-02T00:00:00Z",
        wall_clock_end_utc="2026-07-02T00:00:01Z",
    )
    integration_fields = harness.run_zero_order_canonical_core_integration(
        run_id="harness-evidence",
        instrument="PF_ETHUSD",
        market_type="futures",
    )
    evidence = harness.build_zero_order_evidence_payload(
        timing=timing,
        endpoints_called=[],
        request_count=0,
        network_host="https://demo-futures.kraken.com",
        run_id="harness-evidence",
        pe8_pass=False,
        canonical_integration_fields=integration_fields,
    )
    assert evidence["canonical_core_decision_consumed"] is True
    assert evidence["master_v2_double_play_authority_used"] is False
    assert evidence["legacy_generate_signals_invoked"] is False
    assert evidence["legacy_evaluate_double_play_invoked"] is False
    assert evidence["zero_order_runtime_ready"] is False
    assert evidence["zero_order_runtime_execution_suspended"] is True
    assert evidence["canonical_core_runtime_integration_status"] == (
        INTEGRATION_STATUS_BOUND_NOT_ACTIVATED
    )
    digest = evidence["canonical_trading_decision_semantic_digest"]
    assert isinstance(digest, str) and len(digest) == 64


def test_harness_script_imports_bridge_not_legacy_decision_paths() -> None:
    tree = ast.parse(HARNESS_SCRIPT.read_text(encoding="utf-8"))
    imported_modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported_modules.append(node.module)
    assert any("canonical_core_runtime_integration_bridge_v0" in m for m in imported_modules)
    forbidden = {"live_gates", "live_session", "strategies.registry"}
    assert not any(any(f in m for f in forbidden) for m in imported_modules)


def test_integrated_offline_replay_owner_unchanged() -> None:
    assert "run_integrated_offline_trading_logic_replay_v1" in REPLAY_MODULE.read_text(
        encoding="utf-8"
    )
