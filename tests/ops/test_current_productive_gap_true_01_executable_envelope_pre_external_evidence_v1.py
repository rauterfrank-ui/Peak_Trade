"""GAP-TRUE-01 EXECUTABLE→Envelope→PRE_EXTERNAL bounded evidence tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    POST_ALLOWED,
    REAL_VENUE_POST_ALLOWED,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_productive_http_post_transport_v1 import (
    FullCoreProductiveHttpPostError,
    FullCoreProductiveHttpTradeOrderTransportV1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    CURRENT_PRODUCTIVE_GAP_TRUE_01_EXECUTABLE_ENVELOPE_PRE_EXTERNAL_EVIDENCE_CREATED,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_gap_true_01_executable_envelope_pre_external_evidence_v1 import (
    OWNER_GO,
    THIS_SLICE,
    execute_current_productive_gap_true_01_executable_envelope_pre_external_evidence_v1,
)
from tests.ops._current_productive_29p_chain_integrity_test_helpers_v1 import (
    MockCurrentProductive29PIntegrityBackendV1,
)
from tests.ops._current_productive_natural_mv2_dp_enter_fixture_v1 import (
    governed_c1_candles_payload_from_enter_closes_v1,
    prepare_layered_long_armed_seed_for_pre_external_invoke_v1,
)
from tests.ops.test_full_core_current_productive_pre_external_closure_v1 import (
    _bound,
    _origin_main_sha,
    _productive_transport,
)
from tests.ops.test_full_core_current_productive_oneshot_sidestate_confirmation_cursor_join_v1 import (
    _produced_g17_producer,
)
from tests.ops.test_full_core_current_productive_envelope_bound_single_use_external_effect_send_seam_v1 import (
    _handle,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SPEC_PATH = (
    REPO_ROOT
    / "docs/ops/specs/FULL_CORE_CURRENT_PRODUCTIVE_GAP_TRUE_01_EXECUTABLE_ENVELOPE_PRE_EXTERNAL_EVIDENCE_V1.md"
)


def test_created_flag_and_spec() -> None:
    assert CURRENT_PRODUCTIVE_GAP_TRUE_01_EXECUTABLE_ENVELOPE_PRE_EXTERNAL_EVIDENCE_CREATED is True
    assert OWNER_GO.startswith("OWNER_GO_")
    assert "GAP-TRUE-01" in THIS_SLICE
    assert SPEC_PATH.is_file()


def test_gap_true_01_closes_with_executable_envelope_pre_external(tmp_path: Path) -> None:
    origin_sha = _origin_main_sha()
    integrity = MockCurrentProductive29PIntegrityBackendV1(
        origin_main=origin_sha,
        head=origin_sha,
    )
    bound = _bound()
    g17 = _produced_g17_producer(instrument_id=bound.instrument_id)
    lanes_root = tmp_path / "lanes"
    _arm, enter_closes, mark_px, event_ts = (
        prepare_layered_long_armed_seed_for_pre_external_invoke_v1(
            bound=bound,
            g17_typed_vol_producer=g17,
            lane_state_root=lanes_root,
        )
    )
    del _arm
    candles = governed_c1_candles_payload_from_enter_closes_v1(
        enter_closes=enter_closes,
        last_event_ts_unix=event_ts,
    )
    result = execute_current_productive_gap_true_01_executable_envelope_pre_external_evidence_v1(
        owner_go=OWNER_GO,
        origin_main_sha=origin_sha,
        bound_instrument=bound,
        fresh_get_transport=_productive_transport(),
        lane_state_root=lanes_root,
        candles_payload=candles,
        market_kwargs={
            "cycle_id_prefix": "gap-true-01-test",
            "mark_px": mark_px,
            "index_px": mark_px,
            "bid_px": mark_px - 0.5,
            "ask_px": mark_px + 0.5,
            "finalized_closes": enter_closes,
            "last_finalized_event_ts_unix": event_ts,
            "observed_unix": event_ts + 100.0,
            "venue_flat": True,
            "volume": 10.0,
            "open_interest": 20.0,
            "funding_rate": 0.0001,
        },
        g17_typed_vol_producers={"LANE_1": g17},
        evidence_root=tmp_path / "evidence",
        execution_integrity_backend=integrity,
    )
    assert result.gap_true_01_verdict == "CLOSED"
    assert result.productive_real_get_proven is False
    assert result.transport_bound_proof is True
    assert result.closure.envelope_readiness == "true"
    assert result.closure.capital_context_bound == "true"
    assert result.closure.current_productive_decision_result == "EXECUTABLE_VENUE_PLAN_BOUND"
    assert result.closure.post_count == 0

    summary = json.loads((Path(result.store_root) / "SUMMARY.json").read_text(encoding="utf-8"))
    assert summary["ENVELOPE_READINESS"] == "true"
    assert summary["PRE_EXTERNAL_EFFECT_BOUNDARY_REACHED"] == "true"
    assert summary["CAPITAL_CONTEXT_BOUND"] == "true"
    assert summary["DECISION_EXECUTION_ELIGIBLE"] == "true"
    assert summary["POST_COUNT"] == "0"
    assert summary["EXTERNAL_EFFECT_OCCURRED"] == "false"

    verdict = json.loads(
        (Path(result.store_root) / "gap_true_01_verdict.json").read_text(encoding="utf-8")
    )
    assert verdict["GAP_TRUE_01_VERDICT"] == "CLOSED"

    assert EXTERNAL_EFFECT_AUTHORIZED is False
    assert REAL_VENUE_POST_ALLOWED is False
    assert POST_ALLOWED is False
    transport = FullCoreProductiveHttpTradeOrderTransportV1(handle=_handle())
    with pytest.raises(FullCoreProductiveHttpPostError, match="REAL_VENUE_POST_FORBIDDEN"):
        transport.post_trade_order(
            payload={"instId": "MUST_NOT_POST"},
            permit_id="gap-true-01",
            envelope_id="env-gap",
            envelope_digest="0" * 64,
        )
