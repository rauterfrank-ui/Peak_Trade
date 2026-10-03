"""GHV E2E productive PRE_EXTERNAL tail bind (harness integration, not productive runtime).

Branches productive Closure from the naturally reached pre-decision cursor on the
same GHV evidence cycle. Evidence MV2 Natural ENTER remains qualification-only;
S7/MV2 inside Closure owns the productive ENTER decision.

Forensic replay of the incorrect post-ENTER → second-MV2 topology:
``GHV_E2E_FORENSIC_LEGACY_POST_ENTER_CLOSURE_ENTRY=1`` (research only).
"""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from src.ops.full_core_live_path_composition_root_v1.current_productive_canonical_price_provenance_v1 import (
    build_provenance_from_governed_synthetic_close_mark_and_index_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 import (
    DISPOSITION_PRE_EXTERNAL_EFFECT,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    ENDPOINT_PUBLIC_INSTRUMENTS,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_full_core_pre_external_closure_v1 import (
    OWNER_GO,
    CurrentProductiveFullCorePreExternalClosureResultV1,
    execute_current_productive_full_core_pre_external_closure_v1,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1
from tests.ops._current_productive_29p_chain_integrity_test_helpers_v1 import (
    MockCurrentProductive29PIntegrityBackendV1,
)
from tests.ops._current_productive_natural_mv2_dp_enter_fixture_v1 import (
    governed_c1_candles_payload_from_enter_closes_v1,
    governed_productive_c1_event_ts_unix_v1,
)
from tests.ops._pre_external_cap21_inst_type_test_helpers_v1 import (
    write_cap21_productivity_root_for_inst_v1,
)
from tests.ops.test_full_core_current_productive_29p_common_epoch_handoff_v1 import (
    _identity_payloads,
)
from tests.ops.test_full_core_current_productive_pre_external_closure_v1 import (
    ProductiveClassFreshGetTransportV1,
    _productive_instruments_row_for_enter_metadata_v1,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import ExistingPositionSide

FORENSIC_LEGACY_POST_ENTER_ENV = "GHV_E2E_FORENSIC_LEGACY_POST_ENTER_CLOSURE_ENTRY"


def ghv_e2e_forensic_legacy_post_enter_closure_entry_v1() -> bool:
    return str(os.environ.get(FORENSIC_LEGACY_POST_ENTER_ENV, "0")).strip().lower() in (
        "1",
        "true",
        "yes",
    )


def resolve_ghv_e2e_closure_lane_entry_cursor_v1(
    *,
    pre_decision_incoming_cursor: object | None,
    post_enter_outgoing_cursor: object | None,
) -> object | None:
    """Canonical: pre-decision incoming cursor. Legacy forensic: post-ENTER outgoing."""
    if ghv_e2e_forensic_legacy_post_enter_closure_entry_v1():
        return post_enter_outgoing_cursor
    return pre_decision_incoming_cursor


def ghv_e2e_flight_id_from_cycle_id_v1(cycle_id: str) -> str:
    text = str(cycle_id or "").strip()
    if "-c" in text:
        return text.rsplit("-c", 1)[0]
    return text


def ghv_e2e_closure_lane_store_root_v1(
    *, lane_state_root: Path, bound_instrument: BoundInstrumentV1
) -> Path:
    from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_full_core_pre_external_closure_v1 import (
        _lane_pair_v1,
    )

    pair = _lane_pair_v1(lane_state_root=lane_state_root, bound=bound_instrument)
    store = Path(pair[0].lane_state_root)
    store.mkdir(parents=True, exist_ok=True)
    return store


def _copy_lane_store_tree_v1(*, source_lane_store: Path, target_lane_store: Path) -> None:
    target_lane_store.mkdir(parents=True, exist_ok=True)
    for item in source_lane_store.iterdir():
        dest = target_lane_store / item.name
        if item.is_dir():
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(item, dest)
        elif item.is_file():
            shutil.copy2(item, dest)


def bind_ghv_e2e_pre_decision_state_to_closure_lane_root_v1(
    *,
    lane_state_root: Path,
    bound_instrument: BoundInstrumentV1,
    closure_entry_cursor: object | None,
    mark_px: float,
    finalized_closes: tuple[float, ...],
    last_finalized_event_ts_unix: float,
) -> Path:
    from src.ops.full_core_live_path_composition_root_v1.current_productive_sidestate_confirmation_cursor_v1 import (
        persist_current_productive_sidestate_confirmation_cursor_v1,
    )
    from src.ops.p5_10_productive_activation_and_binding_v1.productive_cycle_bind_seam_v1 import (
        ensure_productive_layered_core_episode_store_v1,
    )

    if closure_entry_cursor is None:
        raise ValueError("ghv_e2e_closure_entry_cursor_required")
    store = ghv_e2e_closure_lane_store_root_v1(
        lane_state_root=lane_state_root, bound_instrument=bound_instrument
    )
    persist_current_productive_sidestate_confirmation_cursor_v1(
        closure_entry_cursor,
        store_root=store,
    )
    failures = ensure_productive_layered_core_episode_store_v1(
        store_root=store,
        bound_instrument=bound_instrument,
        mark_price_m_t=float(mark_px),
        finalized_closes=finalized_closes,
        last_finalized_event_ts_unix=float(last_finalized_event_ts_unix),
        outgoing_cursor=closure_entry_cursor,
    )
    if failures:
        raise ValueError(f"ghv_e2e_episode_store_bootstrap_failures:{','.join(failures)}")
    return store


def build_ghv_e2e_closure_c1_candles_payload_v1(
    *,
    enter_closes: tuple[float, ...],
    mv2_last_finalized_event_ts_unix: float,
) -> Mapping[str, Any]:
    last_ts = governed_productive_c1_event_ts_unix_v1()
    return governed_c1_candles_payload_from_enter_closes_v1(
        enter_closes=enter_closes,
        last_event_ts_unix=last_ts,
    )


@dataclass
class GhvE2EProductivePreExternalTailContextV1:
    cap24_roots: dict[str, Path] = field(default_factory=dict)
    integrity_backend: MockCurrentProductive29PIntegrityBackendV1 | None = None
    lane_roots_base: Path | None = None
    closure_evidence_base: Path | None = None


def build_ghv_e2e_productive_pre_external_tail_context_v1(
    *,
    origin_main_sha: str,
    store_root: Path,
) -> GhvE2EProductivePreExternalTailContextV1:
    store_root.mkdir(parents=True, exist_ok=True)
    return GhvE2EProductivePreExternalTailContextV1(
        integrity_backend=MockCurrentProductive29PIntegrityBackendV1(
            origin_main=origin_main_sha,
            head=origin_main_sha,
        ),
        lane_roots_base=store_root / "ghv_e2e_lane_roots",
        closure_evidence_base=store_root / "ghv_e2e_closure_evidence",
    )


def _cap24_root_for_native_v1(
    ctx: GhvE2EProductivePreExternalTailContextV1, *, venue_native_id: str
) -> Path:
    assert ctx.closure_evidence_base is not None
    if venue_native_id not in ctx.cap24_roots:
        prod_parent = ctx.closure_evidence_base / "cap24" / venue_native_id
        prod_parent.mkdir(parents=True, exist_ok=True)
        ctx.cap24_roots[venue_native_id] = write_cap21_productivity_root_for_inst_v1(
            prod_parent,
            venue_native_id=venue_native_id,
        )
    return ctx.cap24_roots[venue_native_id]


def _transport_for_native_v1(*, venue_native_id: str) -> ProductiveClassFreshGetTransportV1:
    payloads = dict(_identity_payloads(instrument_id=venue_native_id))
    payloads[ENDPOINT_PUBLIC_INSTRUMENTS] = {
        "code": "0",
        "data": [_productive_instruments_row_for_enter_metadata_v1(instrument_id=venue_native_id)],
    }
    return ProductiveClassFreshGetTransportV1(payloads=payloads)


def invoke_ghv_e2e_productive_pre_external_closure_v1(
    *,
    ctx: GhvE2EProductivePreExternalTailContextV1,
    origin_main_sha: str,
    bound_instrument: BoundInstrumentV1,
    g17_typed_vol_producer: object,
    cycle_id: str,
    mark_px: float,
    index_px: float,
    bid_px: float,
    ask_px: float,
    volume: float,
    open_interest: float,
    funding_rate: float,
    finalized_closes: tuple[float, ...],
    last_finalized_event_ts_unix: float,
    observed_unix: float,
    ghv_pre_decision_incoming_cursor: object | None,
    ghv_post_enter_outgoing_cursor: object | None = None,
) -> CurrentProductiveFullCorePreExternalClosureResultV1:
    """Invoke canonical productive Closure from GHV cycle pre-decision state."""
    assert ctx.lane_roots_base is not None and ctx.closure_evidence_base is not None
    assert ctx.integrity_backend is not None
    native = str(bound_instrument.venue_native_id or "").strip()
    if not native:
        raise ValueError("venue_native_id_required")
    cap24 = _cap24_root_for_native_v1(ctx, venue_native_id=native)
    transport = _transport_for_native_v1(venue_native_id=native)
    c1_last_event_ts_unix = governed_productive_c1_event_ts_unix_v1()
    candles = governed_c1_candles_payload_from_enter_closes_v1(
        enter_closes=finalized_closes,
        last_event_ts_unix=c1_last_event_ts_unix,
    )
    closure_lane_entry_cursor = resolve_ghv_e2e_closure_lane_entry_cursor_v1(
        pre_decision_incoming_cursor=ghv_pre_decision_incoming_cursor,
        post_enter_outgoing_cursor=ghv_post_enter_outgoing_cursor,
    )
    lane_root = ctx.lane_roots_base / "closure" / cycle_id.replace("/", "_")
    lane_root.mkdir(parents=True, exist_ok=True)
    flight_root = (
        ctx.lane_roots_base
        / "flight_mv2"
        / ghv_e2e_flight_id_from_cycle_id_v1(cycle_id).replace("/", "_")
    )
    flight_root.mkdir(parents=True, exist_ok=True)
    bind_ghv_e2e_pre_decision_state_to_closure_lane_root_v1(
        lane_state_root=flight_root,
        bound_instrument=bound_instrument,
        closure_entry_cursor=closure_lane_entry_cursor,
        mark_px=float(mark_px),
        finalized_closes=finalized_closes,
        last_finalized_event_ts_unix=float(last_finalized_event_ts_unix),
    )
    flight_store = ghv_e2e_closure_lane_store_root_v1(
        lane_state_root=flight_root, bound_instrument=bound_instrument
    )
    closure_store = ghv_e2e_closure_lane_store_root_v1(
        lane_state_root=lane_root, bound_instrument=bound_instrument
    )
    _copy_lane_store_tree_v1(source_lane_store=flight_store, target_lane_store=closure_store)
    evidence_root = ctx.closure_evidence_base / cycle_id.replace("/", "_")
    evidence_root.mkdir(parents=True, exist_ok=True)
    market_kwargs = {
        "origin_main_sha": origin_main_sha,
        "cycle_id_prefix": f"ghv-e2e-{cycle_id}",
        "observed_unix": float(observed_unix),
        "mark_px": float(mark_px),
        "index_px": float(index_px),
        "bid_px": float(bid_px),
        "ask_px": float(ask_px),
        "volume": float(volume),
        "open_interest": float(open_interest),
        "funding_rate": float(funding_rate),
        "finalized_closes": finalized_closes,
        "last_finalized_event_ts_unix": float(c1_last_event_ts_unix),
        "venue_flat": True,
        "existing_position_side": ExistingPositionSide.NONE,
        "canonical_price_provenance": build_provenance_from_governed_synthetic_close_mark_and_index_v1(
            venue_native_id=native,
            mark_px=float(mark_px),
            index_px=float(index_px),
        ),
    }
    return execute_current_productive_full_core_pre_external_closure_v1(
        owner_go=OWNER_GO,
        origin_main_sha=origin_main_sha,
        bound_instrument=bound_instrument,
        lane_state_root=lane_root,
        fresh_get_transport=transport,
        execute_network=False,
        evidence_root=evidence_root,
        candles_payload=candles,
        market_kwargs=market_kwargs,
        g17_typed_vol_producers={"LANE_1": g17_typed_vol_producer},
        execution_integrity_backend=ctx.integrity_backend,
        cap24_productivity_root=cap24,
    )


def classify_ghv_e2e_productive_pre_external_tail_metrics_v1(
    result: CurrentProductiveFullCorePreExternalClosureResultV1,
) -> Mapping[str, Any]:
    wp1_pass = str(result.wp1_status or "") == "PASS"
    wp2_started = str(result.wp2_status or "") not in ("", "NOT_STARTED")
    rebind = str(result.mv2_capital_context_rebind_status or "")
    live_29p_join_reached = rebind != "NOT_REACHED"
    live_29p_pass = rebind == "PASS"
    live_29p_block = live_29p_join_reached and not live_29p_pass
    venue = str(result.venue_plan_status or "")
    venue_attempt = venue != "NOT_REACHED"
    venue_pass = venue == "PASS"
    pre_ext = str(result.terminal_disposition or "") == DISPOSITION_PRE_EXTERNAL_EFFECT
    step_29p_pass = wp1_pass and str(result.admissibility_29p_status or "").lower() == "true"
    return {
        "wp1_pass": wp1_pass,
        "step_29p_admission_pass": step_29p_pass,
        "wp2_started": wp2_started,
        "live_29p_join_reached": live_29p_join_reached,
        "live_29p_pass": live_29p_pass,
        "live_29p_block": live_29p_block,
        "venue_plan_bind_attempt": venue_attempt,
        "venue_plan_pass": venue_pass,
        "pre_external": pre_ext,
        "earliest_blocker": str(result.earliest_remaining_blocker or ""),
        "terminal_disposition": str(result.terminal_disposition or ""),
    }


__all__ = [
    "FORENSIC_LEGACY_POST_ENTER_ENV",
    "GhvE2EProductivePreExternalTailContextV1",
    "bind_ghv_e2e_pre_decision_state_to_closure_lane_root_v1",
    "build_ghv_e2e_closure_c1_candles_payload_v1",
    "build_ghv_e2e_productive_pre_external_tail_context_v1",
    "classify_ghv_e2e_productive_pre_external_tail_metrics_v1",
    "ghv_e2e_forensic_legacy_post_enter_closure_entry_v1",
    "invoke_ghv_e2e_productive_pre_external_closure_v1",
    "resolve_ghv_e2e_closure_lane_entry_cursor_v1",
]
