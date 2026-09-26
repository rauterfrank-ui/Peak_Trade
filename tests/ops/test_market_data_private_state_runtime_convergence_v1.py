"""Deterministic tests for MARKET_DATA_PRIVATE_STATE_RUNTIME_CONVERGENCE_V1 (WP-C)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

import pytest

from src.ops.economic_md_input_producer_v1.constants_v1 import (
    MINIMUM_FINALIZED_PT1M_MARKS,
    PT1M_STEP_MS,
)
from src.ops.market_data_private_state_runtime_convergence_v1.consumer_census_v1 import (
    CONSUMER_CENSUS_V1,
    census_entry_by_id_v1,
    competing_productive_runtime_truths_v1,
)
from src.ops.market_data_private_state_runtime_convergence_v1.convergence_orchestrator_v1 import (
    run_wp_c_dual_plane_convergence_cycle_v1,
)
from src.ops.market_data_private_state_runtime_convergence_v1.effective_authorization_readmodel_v1 import (
    ObservationCapabilitySignalsV1,
    build_effective_authorization_readmodel_v1,
)
from src.ops.market_data_private_state_runtime_convergence_v1.private_handoff_v1 import (
    PrivateConvergenceError,
    assert_baseline_before_delta_trusted_v1,
    stale_gap_fail_closed_v1,
)
from src.ops.market_data_private_state_runtime_convergence_v1.public_handoff_v1 import (
    PublicConvergenceError,
    assert_cap23_selection_owner_unchanged_v1,
    converged_public_surfaces_v1,
    forbid_direct_transport_as_consumer_truth_v1,
)
from src.ops.market_data_private_state_runtime_convergence_v1.restart_reconciliation_closure_v1 import (
    run_private_restart_reconciliation_closure_v1,
    run_public_restart_reconciliation_closure_v1,
)
from src.ops.market_data_private_state_runtime_convergence_v1.safety_boundary_v1 import (
    wp_c_safety_attestation_v1,
)
from src.ops.peak_trade_public_market_data_runtime_v1.runtime_orchestrator_v1 import (
    PublicMarketDataRuntimeV1,
)

REPO = Path(__file__).resolve().parents[2]
BASE_TS = 1_757_631_540_000


def _fixture_private_rest(path: str, _params: Mapping[str, str]) -> dict[str, Any]:
    if path == "/api/v5/account/config":
        return {"code": "0", "data": [{"acctLv": "2", "posMode": "net_mode"}]}
    if path == "/api/v5/account/balance":
        return {
            "code": "0",
            "data": [{"totalEq": "100", "details": [{"ccy": "USDT", "availEq": "90"}]}],
        }
    if path == "/api/v5/account/positions":
        return {
            "code": "0",
            "data": [{"instId": "ETH-USDT-SWAP", "pos": "1", "posSide": "net", "avgPx": "100"}],
        }
    if path.endswith("orders-pending") or path.endswith("orders-history"):
        return {"code": "0", "data": []}
    if path.endswith("fills"):
        return {"code": "0", "data": []}
    if path.endswith("leverage-info") or path.endswith("max-size"):
        return {"code": "0", "data": [{}]}
    raise AssertionError(path)


def _public_rest(_path: str, _params: Mapping[str, str]) -> dict[str, Any]:
    return {"code": "0", "data": [{"instId": "ETH-USDT-SWAP", "markPx": "1"}]}


def test_o4_n_bars_learning_caller_closure_evidence() -> None:
    from src.ops.market_data_private_state_runtime_convergence_v1.o4_n_bars_learning_caller_closure_v1 import (
        build_o4_n_bars_learning_caller_closure_v1,
    )

    closure = build_o4_n_bars_learning_caller_closure_v1()
    assert closure["productive_ddo_o4_source_is_wp_a_wp_c_canonical"] is True
    assert closure["competing_productive_o4_truth"] is False


def test_census_covers_minimum_consumer_surfaces() -> None:
    required = {
        "landscape_dashboard",
        "ranking_b05_cap22",
        "selection_cap23_boundary",
        "o4_n_bars_learning",
        "research_backtest",
        "optimizer",
        "fresh_pretrade_runtime_get",
        "execution_state_handoff",
    }
    ids = {e.consumer_id for e in CONSUMER_CENSUS_V1}
    assert required <= ids
    assert competing_productive_runtime_truths_v1() == ()


def test_no_competing_transport_truth_when_converged() -> None:
    with pytest.raises(PublicConvergenceError):
        forbid_direct_transport_as_consumer_truth_v1(
            consumer_id="ranking_b05_cap22", transport_session_as_truth=True
        )


def test_cap23_selection_owner_unchanged() -> None:
    boundary = assert_cap23_selection_owner_unchanged_v1()
    assert boundary["cap_2_3_selection_owner_status"] == "UNCHANGED"
    assert boundary["wp_a_may_select"] is False


def test_public_ranking_convergence_preserves_b05_semantics(tmp_path: Path) -> None:
    runtime = PublicMarketDataRuntimeV1(
        store_root=tmp_path,
        venue_native_id="ETH-USDT-SWAP",
        canonical_instrument_id="inst-eth",
        rest_fetch_json=_public_rest,
    )
    runtime.bootstrap(captured_at="2026-09-26T00:00:00Z")
    for i in range(MINIMUM_FINALIZED_PT1M_MARKS):
        runtime.persist_finalized_mark_fact(
            {
                "fact_kind": "FinalizedPt1mMarkFactV1",
                "interval_start_ms": BASE_TS + i * PT1M_STEP_MS,
                "mark_px": str(100 + i),
                "confirm": "1",
                "instrument": {"venue_native_id": "ETH-USDT-SWAP"},
            }
        )
    surfaces = runtime.publish_consumer_surfaces(
        mark_age_seconds=1.0, bba_age_seconds=1.0, captured_at="2026-09-26T00:00:00Z"
    )
    converged = converged_public_surfaces_v1(surfaces)
    assert converged["ranking_b05"]["competing_transport_truth"] is False
    assert converged["ranking_b05"]["ranking_safe"] is True
    assert converged["ranking_b05"]["payload"]["ohlcv_substitution"] is False


def test_private_baseline_before_delta_invariant() -> None:
    with pytest.raises(PrivateConvergenceError):
        assert_baseline_before_delta_trusted_v1(baseline_established=False, ws_delta_applied=True)
    with pytest.raises(PrivateConvergenceError):
        stale_gap_fail_closed_v1(trusted_current=True, quality_state="stale")


def test_private_restart_reconciliation_closure(tmp_path: Path) -> None:
    result = run_private_restart_reconciliation_closure_v1(
        store_root=tmp_path / "private",
        rest_fetch_json=_fixture_private_rest,
        captured_at="2026-09-26T00:00:00Z",
    )
    assert result["baseline_established"] is True
    assert "surfaces" in result


def test_public_restart_without_ws_consumer_truth(tmp_path: Path) -> None:
    result = run_public_restart_reconciliation_closure_v1(
        store_root=tmp_path / "public",
        venue_native_id="ETH-USDT-SWAP",
        canonical_instrument_id="inst-eth",
        rest_fetch_json=_public_rest,
        captured_at="2026-09-26T00:00:00Z",
    )
    assert result["historical_live_ws_required"] is False


def test_effective_authorization_observation_does_not_imply_send() -> None:
    rm = build_effective_authorization_readmodel_v1(
        observation=ObservationCapabilitySignalsV1(
            private_ws_logged_in=True,
            rest_get_success=True,
            credential_sign_capable=True,
            authenticated_connectivity=True,
        )
    )
    assert rm["observation_capability"]["implies_send_authority"] is False
    assert rm["private_send_pins"]["PRIVATE_WS_ORDER_SEND_AUTHORIZED"] is False
    assert rm["external_effect_authorization"]["effective_external_effect_authorized"] is False
    assert rm["standing_admission_seams"]["standing_admission_implies_post"] is False


def test_wp_c_safety_attestation_pins() -> None:
    att = wp_c_safety_attestation_v1()
    assert att["PUBLIC_MARKET_DATA_SELECTION_AUTHORITY"] == "NONE"
    assert att["PRIVATE_WS_ORDER_SEND_AUTHORIZED"] is False
    assert att["MULTI_FUTURE_RUNTIME_AUTHORIZED"] is False
    assert att["MAX_POSITIONS_EFFECTIVE"] == 1
    assert att["K2_STATUS"] == "ABSENT"
    assert att["ACCOUNT_EQUITY_SIZING_AUTHORITY_NOT_ACQUIRED_BY_WP_C"] is True


def test_dual_plane_convergence_cycle(tmp_path: Path) -> None:
    cycle = run_wp_c_dual_plane_convergence_cycle_v1(
        public_store_root=tmp_path / "pub",
        private_store_root=tmp_path / "priv",
        venue_native_id="ETH-USDT-SWAP",
        canonical_instrument_id="inst-eth",
        public_rest_fetch=_public_rest,
        private_rest_fetch=_fixture_private_rest,
        captured_at="2026-09-26T00:00:00Z",
        observation=ObservationCapabilitySignalsV1(rest_get_success=True),
    )
    assert cycle["competing_productive_runtime_truths"] == ()
    assert cycle["safety_attestation"]["wp_c_may_rerank"] is False
    assert "converged_public" in cycle
    assert "converged_private" in cycle


def test_policy_config_present() -> None:
    cfg = json.loads(
        (
            REPO
            / "config/governance/market_data_private_state_runtime_convergence_v1_policy_v1.json"
        ).read_text()
    )
    assert cfg["baseline_sha"] == "0daf4c4119293416bdda8cf84e834b06f16ccf08"
    assert cfg["private_ws_order_send_authorized"] is False
    assert cfg["max_positions_effective"] == 1


def test_census_entry_ranking_documents_bounded_legacy_batch() -> None:
    entry = census_entry_by_id_v1("ranking_b05_cap22")
    assert "economic_md_input_producer_v1" in entry.legacy_parallel_runtime_truth
    assert entry.competing_productive_transport_truth is False
