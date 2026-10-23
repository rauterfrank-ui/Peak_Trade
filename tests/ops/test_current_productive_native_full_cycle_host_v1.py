"""Native full-cycle host v1 — composition authority + end-to-end PRE_EXTERNAL."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 import (
    DISPOSITION_HOLD,
    DISPOSITION_PRE_EXTERNAL_EFFECT,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1 import (
    ENDPOINT_MARKET_TICKER,
    ENDPOINT_PUBLIC_FUNDING_RATE,
    ENDPOINT_PUBLIC_OPEN_INTEREST,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    ENDPOINT_PUBLIC_INSTRUMENTS,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_native_full_cycle_host_v1 import (
    APPLY_AUTHORITY,
    BINDING_DECISION_AUTHORITY,
    CAPITAL_AUTHORITY,
    EXTERNAL_EFFECT_AUTHORITY,
    OWNER_GO,
    RANKING_AUTHORITY,
    RISK_POLICY_AUTHORITY,
    SELECTION_AUTHORITY,
    TRADING_DECISION_AUTHORITY,
    CurrentProductiveNativeFullCycleHostError,
    bind_native_full_cycle_volume_oi_funding_v1,
    execute_current_productive_native_full_cycle_host_v1,
)
from tests.ops._current_productive_29p_chain_integrity_test_helpers_v1 import (
    MockCurrentProductive29PIntegrityBackendV1,
    TRUSTED_TEST_ORIGIN_MAIN_SHA,
)
from tests.ops.test_full_core_current_productive_eea_universe_inventory_to_cap24_and_29p_v1 import (
    _eligible_transport,
)
from tests.ops.test_full_core_current_productive_29p_common_epoch_handoff_v1 import (
    _identity_payloads,
)
from tests.ops.test_full_core_current_productive_pre_external_closure_v1 import (
    ProductiveClassFreshGetTransportV1,
    _productive_instruments_row_for_enter_metadata_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
HOST_SRC = (
    REPO_ROOT / "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "current_productive_native_full_cycle_host_v1.py"
)
AVAIL_EQ_10K = "10000.00"
_TEST_INST = "ADA-USDT-SWAP"


def attach_explicit_synthetic_market_fields_v1(payloads: dict, *, native_id: str) -> dict:
    """Explicit synthetic ticker, open interest, and funding. Not venue evidence."""
    payloads[ENDPOINT_MARKET_TICKER] = {
        "code": "0",
        "data": [{"instId": native_id, "vol24h": "1234.5", "bidPx": "1", "askPx": "2"}],
    }
    payloads[ENDPOINT_PUBLIC_OPEN_INTEREST] = {
        "code": "0",
        "data": [{"instId": native_id, "oi": "5678"}],
    }
    payloads[ENDPOINT_PUBLIC_FUNDING_RATE] = {
        "code": "0",
        "data": [{"instId": native_id, "fundingRate": "0.00015"}],
    }
    payloads["/api/v5/trade/orders-pending"] = {"code": "0", "data": []}
    return payloads


def _fresh_get_10k_transport() -> ProductiveClassFreshGetTransportV1:
    payloads = dict(_identity_payloads(instrument_id=_TEST_INST, avail_eq=AVAIL_EQ_10K))
    payloads[ENDPOINT_PUBLIC_INSTRUMENTS] = {
        "code": "0",
        "data": [_productive_instruments_row_for_enter_metadata_v1(instrument_id=_TEST_INST)],
    }
    attach_explicit_synthetic_market_fields_v1(payloads, native_id=_TEST_INST)
    return ProductiveClassFreshGetTransportV1(payloads=payloads)


def test_host_authority_pins_none() -> None:
    assert TRADING_DECISION_AUTHORITY == "NONE"
    assert RANKING_AUTHORITY == "NONE"
    assert SELECTION_AUTHORITY == "NONE"
    assert BINDING_DECISION_AUTHORITY == "NONE"
    assert RISK_POLICY_AUTHORITY == "NONE"
    assert CAPITAL_AUTHORITY == "NONE"
    assert APPLY_AUTHORITY == "NONE"
    assert EXTERNAL_EFFECT_AUTHORITY == "NONE"


def test_host_does_not_import_pre_armed_mv2_fixture() -> None:
    tree = ast.parse(HOST_SRC.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name)
    forbidden = (
        "tests.ops._current_productive_natural_mv2_dp_enter_fixture_v1",
        "prepare_layered_long_armed_seed_for_pre_external_invoke_v1",
    )
    src_text = HOST_SRC.read_text(encoding="utf-8")
    for token in forbidden:
        assert token not in src_text


def test_host_source_does_not_call_ranking_or_selection_owners() -> None:
    src = HOST_SRC.read_text(encoding="utf-8")
    assert "productive_futures_ranking_producer_v1" not in src
    assert "single_selected_future_policy_v1" not in src
    assert "rerank" not in src.lower()
    assert "reselect" not in src.lower()


def test_pre_external_result_does_not_imply_permit_or_post(tmp_path: Path) -> None:
    integrity = MockCurrentProductive29PIntegrityBackendV1(
        origin_main=TRUSTED_TEST_ORIGIN_MAIN_SHA,
        head=TRUSTED_TEST_ORIGIN_MAIN_SHA,
    )
    result = execute_current_productive_native_full_cycle_host_v1(
        owner_go=OWNER_GO,
        origin_main_sha=TRUSTED_TEST_ORIGIN_MAIN_SHA,
        evidence_root=tmp_path / "perm",
        acquisition_transport=_eligible_transport(),
        fresh_get_transport=_fresh_get_10k_transport(),
        pre_external_fresh_get_transport=_fresh_get_10k_transport(),
        producer_observed_at_unix=1_700_000_100.0,
        execution_integrity_backend=integrity,
    )
    pre = result.pre_external_result
    assert pre.permit_created is False
    assert pre.external_effect_occurred is False
    assert pre.post_count == 0


def test_market_fields_resolve_transport_query_keys_without_get() -> None:
    """Contract: stored bodies keyed like a transport GET are readable offline."""

    class _NoGet:
        def __init__(self, payloads: dict) -> None:
            self.payloads = payloads

        def get(self, **_kwargs: object) -> None:
            raise AssertionError("GET_FORBIDDEN")

    native = _TEST_INST
    transport = _NoGet(
        {
            f"{ENDPOINT_MARKET_TICKER}?instId={native}": {
                "code": "0",
                "data": [{"instId": native, "vol24h": "2500", "bidPx": "1", "askPx": "2"}],
            },
            f"{ENDPOINT_PUBLIC_OPEN_INTEREST}?instId={native}&instType=SWAP": {
                "code": "0",
                "data": [{"instId": native, "oi": "8800"}],
            },
            f"{ENDPOINT_PUBLIC_FUNDING_RATE}#instId={native}": {
                "code": "0",
                "data": [{"instId": native, "fundingRate": "0.0002"}],
            },
        }
    )
    volume, open_interest, funding_rate = bind_native_full_cycle_volume_oi_funding_v1(
        transport=transport,
        native_id=native,
    )
    assert volume == 2500.0
    assert open_interest == 8800.0
    assert funding_rate == pytest.approx(0.0002)


def test_market_fields_do_not_read_another_instrument_query() -> None:
    class _Store:
        payloads = {
            f"{ENDPOINT_MARKET_TICKER}?instId=BTC-USDT-SWAP": {
                "code": "0",
                "data": [{"instId": "BTC-USDT-SWAP", "vol24h": "9", "bidPx": "1", "askPx": "2"}],
            }
        }

    with pytest.raises(
        CurrentProductiveNativeFullCycleHostError,
        match="MARKET_FIELD_PROVENANCE_FAIL_CLOSED",
    ):
        bind_native_full_cycle_volume_oi_funding_v1(
            transport=_Store(),
            native_id=_TEST_INST,
        )


def test_market_fields_fail_closed_when_payloads_absent() -> None:
    transport = _fresh_get_10k_transport()
    transport.payloads.pop(ENDPOINT_PUBLIC_FUNDING_RATE, None)
    with pytest.raises(
        CurrentProductiveNativeFullCycleHostError,
        match="MARKET_FIELD_PROVENANCE_FAIL_CLOSED",
    ):
        bind_native_full_cycle_volume_oi_funding_v1(
            transport=transport,
            native_id=_TEST_INST,
        )


def test_owner_go_mismatch_raises() -> None:
    with pytest.raises(CurrentProductiveNativeFullCycleHostError, match="OWNER_GO"):
        execute_current_productive_native_full_cycle_host_v1(
            owner_go="WRONG",
            origin_main_sha=TRUSTED_TEST_ORIGIN_MAIN_SHA,
            acquisition_transport=_eligible_transport(),
            fresh_get_transport=_fresh_get_10k_transport(),
        )


def test_native_full_cycle_host_reaches_pre_external_or_hold_without_driver_slices(
    tmp_path: Path,
) -> None:
    integrity = MockCurrentProductive29PIntegrityBackendV1(
        origin_main=TRUSTED_TEST_ORIGIN_MAIN_SHA,
        head=TRUSTED_TEST_ORIGIN_MAIN_SHA,
    )
    result = execute_current_productive_native_full_cycle_host_v1(
        owner_go=OWNER_GO,
        origin_main_sha=TRUSTED_TEST_ORIGIN_MAIN_SHA,
        evidence_root=tmp_path / "native_cycle",
        acquisition_transport=_eligible_transport(),
        fresh_get_transport=_fresh_get_10k_transport(),
        pre_external_fresh_get_transport=_fresh_get_10k_transport(),
        execute_network=False,
        producer_observed_at_unix=1_700_000_100.0,
        execution_integrity_backend=integrity,
    )
    assert result.bound_instrument_handoff == "NATIVE_TYPED_FROM_EEA_RESULT"
    assert result.driver_bound_reload_required == "false"
    assert result.pre_armed_mv2_fixture_used == "false"
    assert result.eea_result.bound_instrument is not None
    assert result.eea_result.bound_instrument.venue_native_id == _TEST_INST
    assert str(result.eea_result.cap22_ranking_id).strip()
    assert str(result.eea_result.cap23_selection_decision_id).strip()
    assert result.eea_result.master_v2_reconciliation_admission is not None
    assert (
        result.eea_result.master_v2_reconciliation_admission.is_productive_upstream_provenance_v1()
        is True
    )
    assert result.pre_external_result.post_count == 0
    assert result.pre_external_result.permit_created is False
    assert result.pre_external_result.external_effect_occurred is False
    assert result.terminal_disposition == DISPOSITION_PRE_EXTERNAL_EFFECT
    assert result.pre_external_reached == "true"
    assert (
        result.pre_external_result.current_productive_decision_result
        == "EXECUTABLE_VENUE_PLAN_BOUND"
    )
    envelope = result.pre_external_result.fresh_executable_enter_final_order_envelope
    assert envelope is not None
    assert envelope.side == "buy"
    assert envelope.quantity == "609"
    assert result.pre_external_result.post_count == 0
