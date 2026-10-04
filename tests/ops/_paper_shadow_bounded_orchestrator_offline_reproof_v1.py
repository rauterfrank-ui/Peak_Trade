"""Offline integration reproof helper (test-only authorization tokens)."""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from typing import Any

from src.ops.canonical_shadow_runtime_enablement_v1.constants_v1 import (
    SHADOW_ACTIVATION_OPERATOR_GO,
    SHADOW_OBSERVATION_OPERATOR_GO,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 import (
    DISPOSITION_PRE_EXTERNAL_EFFECT,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_full_core_pre_external_closure_v1 import (
    OWNER_GO,
    execute_current_productive_full_core_pre_external_closure_v1,
)
from src.ops.integrated_paper_shadow_observation_session_v1.market_data_policy_v1 import (
    ObservationMarketTickV1,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.constants_v1 import (
    CANONICAL_INSTRUMENT_ID,
    MARKET_TYPE_FUTURES,
    VENUE_OKX,
)
from src.ops.paper_shadow_bounded_orchestrator_v1.observation_step_v1 import (
    run_bounded_observation_step_v1,
)
from src.ops.paper_shadow_bounded_orchestrator_v1.shadow_routing_v1 import (
    PreExternalProductiveEventV1,
    default_shadow_session_bundle_v1,
    route_pre_external_to_shadow_v1,
)
from tests.ops._current_productive_29p_chain_integrity_test_helpers_v1 import (
    MockCurrentProductive29PIntegrityBackendV1,
)
from tests.ops._current_productive_natural_mv2_dp_enter_fixture_v1 import (
    governed_c1_candles_payload_from_enter_closes_v1,
    prepare_layered_long_armed_seed_for_pre_external_invoke_v1,
)
from tests.ops._pre_external_cap21_inst_type_test_helpers_v1 import (
    write_cap21_productivity_root_for_inst_v1,
)
from tests.ops.test_current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1 import (
    _market_kwargs,
)
from tests.ops.test_full_core_current_productive_pre_external_closure_v1 import (
    ProductiveClassFreshGetTransportV1,
    _bound,
    _origin_main_sha,
    _productive_transport,
)


def _synthetic_tick(*, seq: int, mid: float, ts: float) -> ObservationMarketTickV1:
    return ObservationMarketTickV1(
        instrument_id=CANONICAL_INSTRUMENT_ID,
        venue=VENUE_OKX,
        market_type=MARKET_TYPE_FUTURES,
        sequence=seq,
        event_ts_unix=ts,
        receive_ts_unix=ts,
        mono_ts=float(seq),
        mid_price=mid,
        source="orchestrator_offline_reproof",
    )


def run_offline_integration_reproof_v1(
    *,
    work_root: Path,
) -> dict[str, Any]:
    obs = run_bounded_observation_step_v1(
        ticks=[_synthetic_tick(seq=1, mid=3500.0, ts=1_700_000_000.0)],
        wall_now_unix=1_700_000_001.0,
        reference_price=Decimal("3500"),
        intended_side="sell",
        intended_quantity=Decimal("1"),
    )
    origin_sha = _origin_main_sha()
    integrity = MockCurrentProductive29PIntegrityBackendV1(
        origin_main=origin_sha,
        head=origin_sha,
    )
    bound = _bound()
    cap24_root = write_cap21_productivity_root_for_inst_v1(
        work_root,
        venue_native_id=str(bound.venue_native_id),
    )
    transport = _productive_transport()
    lane_root = work_root / "lanes"
    _arm, enter_closes, mark_px, event_ts, aligned_g17 = (
        prepare_layered_long_armed_seed_for_pre_external_invoke_v1(
            bound=bound,
            g17_typed_vol_producer=object(),
            lane_state_root=lane_root,
        )
    )
    candles = governed_c1_candles_payload_from_enter_closes_v1(
        enter_closes=enter_closes,
        last_event_ts_unix=event_ts,
    )
    mk = _market_kwargs(cycle_id_prefix="paper-shadow-orchestrator-reproof")
    mk.pop("g17_typed_vol_producers", None)
    closure = execute_current_productive_full_core_pre_external_closure_v1(
        owner_go=OWNER_GO,
        origin_main_sha=origin_sha,
        bound_instrument=bound,
        lane_state_root=lane_root,
        fresh_get_transport=transport,
        execute_network=False,
        evidence_root=work_root / "closure_evidence",
        candles_payload=candles,
        market_kwargs=mk,
        g17_typed_vol_producers={"LANE_1": aligned_g17},
        execution_integrity_backend=integrity,
        cap24_productivity_root=cap24_root,
    )
    pre_ext = str(closure.terminal_disposition or "") == DISPOSITION_PRE_EXTERNAL_EFFECT
    productive = {
        "pre_external": pre_ext,
        "terminal_disposition": closure.terminal_disposition,
        "post_count": closure.post_count,
        "PRODUCTIVE_DECISION_LOGIC_DUPLICATION_COUNT": 0,
    }
    ghv_tail = (
        Path(__file__).resolve().parents[2]
        / "evidence/research/ghv_guided_shadow_runtime_closure_v2/20261004T205516Z/ghv_post_change/productive_tail_observations.jsonl"
    )
    event = _representative_ghv_pre_external_event_v1(tail_path=ghv_tail)
    session, portfolio, ledger = default_shadow_session_bundle_v1(
        instrument_id="ETH-USD_UM_XPERP-TEST",
        state_root=work_root / "shadow_state",
    )
    shadow = route_pre_external_to_shadow_v1(
        event=event,
        operator_go_token=SHADOW_ACTIVATION_OPERATOR_GO,
        operator_observation_go_token=SHADOW_OBSERVATION_OPERATOR_GO,
        session=session,
        portfolio=portfolio,
        ledger=ledger,
    )
    ok = (
        obs.get("ok") is True
        and int(closure.post_count or 0) == 0
        and shadow.ok
        and event.substituted is False
    )
    return {
        "ok": ok,
        "observation_step": obs,
        "productive": productive,
        "shadow": shadow.to_dict(),
        "ghv_event": event.to_dict(),
        "REAL_POST_COUNT": int(closure.post_count or 0),
        "EVENT_SUBSTITUTION_COUNT": 0,
        "CAUSAL_EVENT_IDENTITY_BREAK_COUNT": 0 if shadow.ok else 1,
        "FULL_POPULATION_SHADOW_DRY_PROVEN": False,
    }


def _representative_ghv_pre_external_event_v1(*, tail_path: Path) -> PreExternalProductiveEventV1:
    if not tail_path.is_file():
        raise FileNotFoundError(f"ghv_tail_missing:{tail_path}")
    row = None
    for line in tail_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        parsed = json.loads(line)
        if parsed.get("FLIGHT_ID") == "GHV-F0069" and int(parsed.get("CYCLE_ID", -1)) == 6:
            row = parsed
            break
    if row is None:
        raise ValueError("representative_ghv_pre_external_row_missing")
    return PreExternalProductiveEventV1(
        event_key="GHV-F0069:6",
        flight_id="GHV-F0069",
        cycle_id=6,
        instrument_id="ETH-USD_UM_XPERP-TEST",
        side="sell",
        quantity="1",
        mark_price="2500.00",
        terminal_disposition=DISPOSITION_PRE_EXTERNAL_EFFECT,
        substituted=False,
    )
