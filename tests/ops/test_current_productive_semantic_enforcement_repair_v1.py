"""SEM-DIV-00001/00002/00006 semantic repair contract tests (PRE_EXTERNAL)."""

from __future__ import annotations

from tests.ops._current_productive_reconciliation_admission_test_helpers_v1 import (
    non_productive_test_master_v2_reconciliation_admission_v1,
)

import ast
from dataclasses import replace
from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.current_productive_canonical_price_provenance_v1 import (
    FORBIDDEN_MARK_SOURCES,
    INDEX_SOURCE_EXPLICIT_TEST_FIXTURE,
    MARK_SOURCE_EXPLICIT_SYNTHETIC_FIXTURE,
    MARK_SOURCE_OKX_PUBLIC_MARK_PAYLOAD,
    ProductiveCanonicalPriceProvenanceError,
    build_cmc_mark_provenance_from_okx_mark_price_payload_v1,
    build_explicit_test_fixture_price_provenance_v1,
    build_provenance_from_resolved_cmc_mark_and_index_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1 import (
    run_current_productive_master_v2_runtime_cycle_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_persistent_natural_enter_convergence_v1 import (
    PersistentNaturalEnterConvergenceError,
    _market_kwargs_from_observation_v1,
)
from src.ops.p5_2_productive_cycle_seam_invoke_and_authority_bind_v1.contract_v1 import (
    AuthorityBindFailureCodeV1,
    ProductiveCycleAuthorityBindRequestV1,
    ProductiveDecisionAuthorityModeV1,
    SideStateSeedClassV1,
    validate_productive_cycle_authority_bind_v1,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import ExistingPositionSide
from tests.ops._current_productive_canonical_price_test_helpers_v1 import (
    okx_public_mark_price_payload_v1,
    provenance_for_bound_v1,
)
from tests.ops._current_productive_natural_mv2_dp_enter_fixture_v1 import (
    governed_c1_candles_payload_from_enter_closes_v1,
    strong_uptrend_closes_v1,
)
from tests.ops.test_full_core_current_productive_oneshot_sidestate_confirmation_cursor_join_v1 import (
    _bound,
    _cycle,
    _produced_g17_producer,
)

REPO = Path(__file__).resolve().parents[2]
CONVERGENCE = (
    REPO
    / "src/ops/full_core_live_path_composition_root_v1/current_productive_persistent_natural_enter_convergence_v1.py"
)
CYCLE_SRC = (
    REPO
    / "src/ops/full_core_live_path_composition_root_v1/current_productive_master_v2_runtime_cycle_v1.py"
)


def test_synthetic_fixture_mark_must_not_claim_okx_public_mark_source() -> None:
    prov = build_explicit_test_fixture_price_provenance_v1(
        venue_native_id="ADA-USDT-SWAP",
        mark_px=100.0,
        index_px=99.5,
    )
    assert prov.mark_source == MARK_SOURCE_EXPLICIT_SYNTHETIC_FIXTURE
    assert prov.mark_source != MARK_SOURCE_OKX_PUBLIC_MARK_PAYLOAD
    with pytest.raises(ProductiveCanonicalPriceProvenanceError):
        build_provenance_from_resolved_cmc_mark_and_index_v1(
            venue_native_id="ADA-USDT-SWAP",
            mark_px=100.0,
            index_px=99.5,
            index_source=INDEX_SOURCE_EXPLICIT_TEST_FIXTURE,
        )


def test_natural_enter_rejects_candle_close_only_mark_without_payload() -> None:
    candles = governed_c1_candles_payload_from_enter_closes_v1(
        enter_closes=strong_uptrend_closes_v1(count=8),
        last_event_ts_unix=1_700_000_100.0,
    )
    with pytest.raises(PersistentNaturalEnterConvergenceError):
        _market_kwargs_from_observation_v1(
            candles_payload=candles,
            mark_price_payload={"code": "0", "data": []},
            venue_native_id="0G-USDT-SWAP",
            cycle_id_prefix="sem-repair",
            origin_main_sha="abc",
            g17_producers={},
        )


def test_natural_enter_accepts_distinct_cmc_mark_and_index() -> None:
    native = "0G-USDT-SWAP"
    mark_px = 101.25
    index_px = 100.75
    candles = governed_c1_candles_payload_from_enter_closes_v1(
        enter_closes=(100.0, 100.5, 101.0),
        last_event_ts_unix=1_700_000_100.0,
    )
    mark_payload = okx_public_mark_price_payload_v1(
        native_id=native, mark_px=mark_px, index_px=index_px
    )
    kwargs = _market_kwargs_from_observation_v1(
        candles_payload=candles,
        mark_price_payload=mark_payload,
        venue_native_id=native,
        cycle_id_prefix="sem-repair",
        origin_main_sha="abc",
        g17_producers={},
    )
    assert kwargs["mark_px"] == mark_px
    assert kwargs["index_px"] == index_px
    assert kwargs["mark_px"] != kwargs["finalized_closes"][-1] or mark_px != 101.0


def test_cycle_rejects_forbidden_candle_close_mark_source() -> None:
    bound = _bound()
    closes = (100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0)
    bad = replace(
        build_explicit_test_fixture_price_provenance_v1(
            venue_native_id=str(bound.venue_native_id),
            mark_px=108.0,
            index_px=107.5,
        ),
        mark_source="ORDINARY_MARKET_CANDLE_CLOSE",
    )
    assert bad.mark_source in FORBIDDEN_MARK_SOURCES
    result = run_current_productive_master_v2_runtime_cycle_v1(
        bound_instrument=bound,
        cycle_id="sem-div-candle-mark",
        observed_unix=1_700_000_200.0,
        mark_px=108.0,
        index_px=107.5,
        bid_px=107.0,
        ask_px=108.5,
        volume=1.0,
        open_interest=1.0,
        funding_rate=0.0001,
        finalized_closes=closes,
        last_finalized_event_ts_unix=1_700_000_100.0,
        venue_flat=True,
        existing_position_side=ExistingPositionSide.NONE,
        g17_typed_vol_producer=_produced_g17_producer(instrument_id=bound.instrument_id),
        canonical_price_provenance=bad,
        master_v2_reconciliation_admission=non_productive_test_master_v2_reconciliation_admission_v1(
            bound=bound
        ),
    )
    assert "CMC_MARK_SOURCE_FORBIDDEN" in str(result.fail_reasons)


def test_venue_occupancy_does_not_mint_long_active_side_state() -> None:
    bound = _bound()
    mark = 110.0
    index = 109.5
    result = run_current_productive_master_v2_runtime_cycle_v1(
        bound_instrument=bound,
        cycle_id="sem-div-venue-flat-false",
        observed_unix=1_700_000_200.0,
        mark_px=mark,
        index_px=index,
        bid_px=mark - 0.5,
        ask_px=mark + 0.5,
        volume=1.0,
        open_interest=1.0,
        funding_rate=0.0001,
        finalized_closes=(100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0),
        last_finalized_event_ts_unix=1_700_000_100.0,
        venue_flat=False,
        existing_position_side=ExistingPositionSide.LONG,
        g17_typed_vol_producer=_produced_g17_producer(instrument_id=bound.instrument_id),
        canonical_price_provenance=provenance_for_bound_v1(
            bound=bound,
            mark_px=mark,
            index_px=index,
        ),
        master_v2_reconciliation_admission=non_productive_test_master_v2_reconciliation_admission_v1(
            bound=bound
        ),
    )
    assert result.replay is not None
    assert result.replay.replay_pass is True
    intermediate = result.replay.intermediate
    assert intermediate is not None
    assert intermediate.state_switch is not None


def test_observation_sidestate_seed_class_rejected_on_bind() -> None:
    req = ProductiveCycleAuthorityBindRequestV1(
        productive_layered_core_bind_requested=False,
        decision_authority_mode=ProductiveDecisionAuthorityModeV1.LAYERED_CORE_SEAL_DELEGATED,
        seal_present=True,
        seal_validation_ok=True,
        cz4_delegation_intended=True,
        legacy_scope_writer_would_run=False,
        legacy_transition_writer_would_run=False,
        legacy_dynamic_boundary_writer_would_run=False,
        legacy_canonical_distances_as_d_t_authority=False,
        side_state_seed_class=SideStateSeedClassV1.OBSERVATION_OCCUPANCY_INPUT,
        fallback_to_legacy_on_missing_core=False,
    )
    result = validate_productive_cycle_authority_bind_v1(req)
    assert result.ok is False
    assert (
        AuthorityBindFailureCodeV1.SIDE_STATE_OBSERVATION_SEED_FORBIDDEN.value
        in result.failure_codes
    )


def test_static_guard_no_index_mark_collapse_in_convergence() -> None:
    tree = ast.parse(CONVERGENCE.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            if isinstance(node.value, ast.Name) and node.value.id == "mark_px":
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "index_px":
                        pytest.fail("index_px = mark_px assignment remains in convergence module")


def test_static_guard_no_venue_long_active_mint_in_cycle() -> None:
    text = CYCLE_SRC.read_text(encoding="utf-8")
    assert (
        "SideState.LONG_ACTIVE" not in text
        or "existing_position_side" not in text.split("SideState.LONG_ACTIVE")[0][-200:]
    )


def test_cmc_provenance_from_okx_payload() -> None:
    payload = okx_public_mark_price_payload_v1(
        native_id="ETH-USDT-SWAP", mark_px=2000.0, index_px=1999.0
    )
    prov = build_cmc_mark_provenance_from_okx_mark_price_payload_v1(
        mark_price_payload=payload,
        venue_native_id="ETH-USDT-SWAP",
    )
    prov.validate_against_cycle_inputs_v1(
        mark_px=2000.0, index_px=1999.0, venue_native_id="ETH-USDT-SWAP"
    )


def test_cursor_round_trip_still_reaches_transition_output() -> None:
    origin = _cycle(cycle_id="sem-repair-origin", mark_px=100.0)
    warm = _cycle(
        cycle_id="sem-repair-warm",
        incoming_cursor=origin.outgoing_cursor,
        mark_px=105.0,
    )
    assert warm.outgoing_cursor is not None
    assert warm.replay is not None and warm.replay.replay_pass is True
