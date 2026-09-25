"""PRODUCTIVE Full-Core pre-external closure v1 tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 import (
    DISPOSITION_HOLD,
    DISPOSITION_PRE_EXTERNAL_EFFECT,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    ENDPOINT_PUBLIC_INSTRUMENTS,
    TRANSPORT_CLASS_PRODUCTIVE_READ_ONLY_GET,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    CURRENT_PRODUCTIVE_FULL_CORE_PRE_EXTERNAL_CLOSURE_CREATED,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_common_epoch_handoff_v1 import (
    compose_current_productive_29p_common_epoch_handoff_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_common_epoch_to_enter_live_29p_handoff_v1 import (
    CurrentProductiveCommonEpochToEnterLive29PHandoffError,
    build_current_productive_enter_live_29p_injected_from_common_epoch_handoff_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_full_core_pre_external_closure_v1 import (
    ALLOWED_OWNER_GOS,
    EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
    OWNER_GO,
    THIS_SLICE,
    CurrentProductiveFullCorePreExternalClosureError,
    execute_current_productive_full_core_pre_external_closure_v1,
)
from src.ops.single_selected_future_runtime_binding_v1.constants_v1 import (
    MAX_POSITIONS_EFFECTIVE,
    STATE_SELECTED_ACTIVE,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1
from tests.ops._current_productive_29p_chain_integrity_test_helpers_v1 import (
    MockCurrentProductive29PIntegrityBackendV1,
)
from tests.ops.test_full_core_current_productive_29p_common_epoch_handoff_v1 import (
    CountingInjectedFreshGetTransportV1,
    _EPOCH,
    _identity_payloads,
    _transport,
)
from tests.ops.test_current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1 import (
    _lane_g17,
    _market_kwargs,
    _mv2_aligned_candles,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SPEC_PATH = (
    REPO_ROOT / "docs/ops/specs/FULL_CORE_CURRENT_PRODUCTIVE_FULL_CORE_PRE_EXTERNAL_CLOSURE_V1.md"
)
_TEST_INST = "ADA-USDT-SWAP"


class ProductiveClassFreshGetTransportV1(CountingInjectedFreshGetTransportV1):
    """Injected payloads with productive transport classification (test double)."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.transport_class = TRANSPORT_CLASS_PRODUCTIVE_READ_ONLY_GET
        self.venue_live_contact = True


def _bound() -> BoundInstrumentV1:
    return BoundInstrumentV1(
        instrument_id=f"cap24-{_TEST_INST}",
        venue_native_id=_TEST_INST,
        ranking_snapshot_id="rank-pre-ext-1",
        ranking_integrity_digest="rank-digest-pre-ext-1",
        universe_snapshot_id="uni-pre-ext-1",
        selection_id="sel-pre-ext-1",
        selection_integrity_digest="sel-digest-pre-ext-1",
        selection_state=STATE_SELECTED_ACTIVE,
        selected_future_count=1,
        max_positions_effective=MAX_POSITIONS_EFFECTIVE,
    )


def _productive_instruments_row_for_enter_metadata_v1(
    *, instrument_id: str = _TEST_INST
) -> dict[str, object]:
    """CRS-required OKX instruments fields for natural ENTER → PRE_EXTERNAL join."""
    return {
        "instId": instrument_id,
        "instType": "SWAP",
        "state": "live",
        "ctVal": "0.01",
        "ctValCcy": "ADA",
        "lotSz": "1",
        "minSz": "1",
        "tickSz": "0.01",
        "tdMode": "cross",
        "mgnMode": "cross",
    }


def _productive_transport(**kwargs) -> ProductiveClassFreshGetTransportV1:
    payloads = dict(_identity_payloads(instrument_id=_TEST_INST, **kwargs))
    payloads[ENDPOINT_PUBLIC_INSTRUMENTS] = {
        "code": "0",
        "data": [_productive_instruments_row_for_enter_metadata_v1()],
    }
    return ProductiveClassFreshGetTransportV1(payloads=payloads)


def _origin_main_sha() -> str:
    import subprocess

    return subprocess.check_output(
        ["git", "rev-parse", "origin/main"], cwd=REPO_ROOT, text=True
    ).strip()


def test_standing_pins_and_owner_go() -> None:
    assert CURRENT_PRODUCTIVE_FULL_CORE_PRE_EXTERNAL_CLOSURE_CREATED is True
    assert OWNER_GO in ALLOWED_OWNER_GOS
    assert len(EXPECTED_BASELINE_ORIGIN_MAIN_SHA) == 40
    assert THIS_SLICE.startswith("11.2.1.FC.")
    assert SPEC_PATH.is_file()


def test_handoff_rejects_injected_test_double_transport() -> None:
    handoff, _transport_obj = _compose_handoff()
    with pytest.raises(CurrentProductiveCommonEpochToEnterLive29PHandoffError, match="INJECTED"):
        build_current_productive_enter_live_29p_injected_from_common_epoch_handoff_v1(
            handoff=handoff,
            transport=_transport(),
        )


def _compose_handoff():
    bound = _bound()
    transport = _productive_transport()
    handoff = compose_current_productive_29p_common_epoch_handoff_v1(
        decision_epoch=_EPOCH,
        bound_instrument=bound,
        fresh_get_transport=transport,
    )
    return handoff, transport


def test_handoff_builds_productive_carrier_from_common_epoch() -> None:
    handoff, transport = _compose_handoff()
    injected = build_current_productive_enter_live_29p_injected_from_common_epoch_handoff_v1(
        handoff=handoff,
        transport=transport,
    )
    assert injected.get_performed is True
    assert injected.instruments_payload is not None
    assert injected.fresh_pretrade_get_status == "TRUSTED_PRESENT"
    assert injected.raw_acct_lv == "2"


def test_execute_wp1_and_wp2_terminates_without_post(tmp_path: Path) -> None:
    origin_sha = _origin_main_sha()
    integrity = MockCurrentProductive29PIntegrityBackendV1(
        origin_main=origin_sha,
        head=origin_sha,
    )
    bound = _bound()
    transport = _productive_transport()
    pairs_lane_root = tmp_path / "lanes"
    candles = _mv2_aligned_candles(last_ts_ms=1_700_000_000_000, mark_px=100.0)
    mk = _market_kwargs(cycle_id_prefix="pre-ext-closure")
    slot = _dummy_slot(tmp_path)
    mk.pop("g17_typed_vol_producers", None)
    result = execute_current_productive_full_core_pre_external_closure_v1(
        owner_go=OWNER_GO,
        origin_main_sha=origin_sha,
        bound_instrument=bound,
        lane_state_root=pairs_lane_root,
        fresh_get_transport=transport,
        execute_network=False,
        evidence_root=tmp_path / "evidence",
        candles_payload=candles,
        market_kwargs=mk,
        g17_typed_vol_producers=_lane_g17({"LANE_1": (slot, bound)}),
        execution_integrity_backend=integrity,
    )
    assert result.wp1_status == "PASS"
    assert result.post_count == 0
    assert result.permit_created is False
    assert result.external_effect_occurred is False
    assert result.manual_injection_contamination is False
    assert result.runtime_owner_gos_consumed
    assert result.terminal_disposition in {
        DISPOSITION_PRE_EXTERNAL_EFFECT,
        DISPOSITION_HOLD,
        "FAIL_CLOSED",
    }


def _dummy_slot(tmp_path: Path):
    from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.constants_v1 import (
        OCCUPANCY_OCCUPIED,
    )
    from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.topology_v1 import (
        IsolatedLaneSlotV1,
    )

    bound = _bound()
    return IsolatedLaneSlotV1(
        lane_id="LANE_1",
        occupancy=OCCUPANCY_OCCUPIED,
        canonical_instrument_id=bound.instrument_id,
        lane_state_root=str(tmp_path / "lane1"),
        universe_snapshot_id=bound.universe_snapshot_id,
        ranking_snapshot_id=bound.ranking_snapshot_id,
        ranking_integrity_digest=bound.ranking_integrity_digest,
    )


def test_execute_network_without_vault_fail_closed(tmp_path: Path) -> None:
    origin_sha = _origin_main_sha()
    integrity = MockCurrentProductive29PIntegrityBackendV1(
        origin_main=origin_sha,
        head=origin_sha,
    )
    bound = _bound()
    result = execute_current_productive_full_core_pre_external_closure_v1(
        owner_go=OWNER_GO,
        origin_main_sha=origin_sha,
        execution_integrity_backend=integrity,
        bound_instrument=bound,
        lane_state_root=tmp_path / "lanes",
        execute_network=True,
        vault_file=None,
        evidence_root=tmp_path / "evidence",
    )
    assert result.wp1_status == "BLOCKED"
    assert result.earliest_remaining_blocker == "CREDENTIAL_HANDLE_FAIL_CLOSED"


def test_owner_go_mismatch_raises() -> None:
    with pytest.raises(CurrentProductiveFullCorePreExternalClosureError, match="OWNER_GO"):
        execute_current_productive_full_core_pre_external_closure_v1(
            owner_go="WRONG_GO",
            origin_main_sha=_origin_main_sha(),
            bound_instrument=_bound(),
            lane_state_root=Path("/tmp/unused"),
            fresh_get_transport=_productive_transport(),
            evidence_root=Path("/tmp/unused-ev"),
            candles_payload={"code": "0", "data": []},
        )
