"""CURRENT productive native full-cycle host v1 (composition only).

Single invocation: EEA universe→Cap24→29P, MV2 state advance, Full-Core PRE_EXTERNAL.
No trading, ranking, selection, risk, capital, apply, or external-effect authority.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from src.ops.current_productive_eea_universe_inventory_acquisition_v1.transport_v1 import (
    EeaPublicUniverseGetPortV1,
)
from src.ops.current_productive_eea_universe_inventory_acquisition_v1.acquire_v1 import (
    EeaUniverseAcquisitionResultV1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_controlled_external_market_observation_v1 import (
    governed_c1_candles_payload_from_closes_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 import (
    DISPOSITION_PRE_EXTERNAL_EFFECT,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_layered_long_mv2_state_advance_for_pre_external_v1 import (
    LayeredLongMv2StateAdvanceError,
    advance_layered_long_mv2_state_for_pre_external_v1,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    FullCoreFreshPretradeGetTransportV1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_chain_baseline_contract_v1 import (
    CurrentProductive29PRuntimeIntegrityBackendV1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_eea_universe_inventory_to_cap24_and_29p_v1 import (
    OWNER_GO as EEA_SLICE_OWNER_GO,
    CurrentProductiveEeaUniverseTo29PError,
    CurrentProductiveEeaUniverseTo29PResultV1,
    execute_current_productive_eea_universe_inventory_to_cap24_and_29p_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_full_core_pre_external_closure_v1 import (
    OWNER_GO as PRE_EXTERNAL_SLICE_OWNER_GO,
    CurrentProductiveFullCorePreExternalClosureError,
    CurrentProductiveFullCorePreExternalClosureResultV1,
    execute_current_productive_full_core_pre_external_closure_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_fresh_cap23_cap24_decision_and_one_shot_real_post_readiness_v1 import (
    _assert_no_secrets,
    _persist_json,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.d4_d5_genesis_runtime_orchestrator_v1 import (
    persist_manifest_sha256_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    verify_manifest_sha256_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_canonical_price_provenance_v1 import (
    INDEX_SOURCE_EXPLICIT_TEST_FIXTURE,
    build_provenance_from_resolved_cmc_mark_and_index_v1,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1
from trading.master_v2.double_play_entry_exit_policy_v0 import ExistingPositionSide

OWNER_GO = "OWNER_GO_CURRENT_PRODUCTIVE_NATIVE_FULL_CYCLE_HOST_V1"
ALLOWED_OWNER_GOS = frozenset({OWNER_GO, f"OWNER_GO_{OWNER_GO}"})
THIS_SLICE = "11.2.1.FC.CURRENT_PRODUCTIVE_NATIVE_FULL_CYCLE_HOST_V1"
EVIDENCE_DIRNAME = "current_productive_native_full_cycle_host_v1"
FALSE_TOKEN = "false"
TRUE_TOKEN = "true"
_REPO_ROOT = Path(__file__).resolve().parents[3]

# Composition host: explicit authority pins (must remain NONE / false).
TRADING_DECISION_AUTHORITY = "NONE"
RANKING_AUTHORITY = "NONE"
SELECTION_AUTHORITY = "NONE"
BINDING_DECISION_AUTHORITY = "NONE"
RISK_POLICY_AUTHORITY = "NONE"
CAPITAL_AUTHORITY = "NONE"
APPLY_AUTHORITY = "NONE"
EXTERNAL_EFFECT_AUTHORITY = "NONE"


class CurrentProductiveNativeFullCycleHostError(RuntimeError):
    """Fail-closed native full-cycle host violation."""


@dataclass(frozen=True)
class CurrentProductiveNativeFullCycleHostResultV1:
    store_root: str
    session_id: str
    origin_main_sha: str
    eea_result: CurrentProductiveEeaUniverseTo29PResultV1
    bound_instrument_handoff: str
    mv2_advance_arm_side_state: str
    mv2_advance_arm_decision: str
    pre_external_result: CurrentProductiveFullCorePreExternalClosureResultV1
    terminal_disposition: str
    pre_external_reached: str
    bound_instrument_native_typed: str
    driver_bound_reload_required: str
    pre_armed_mv2_fixture_used: str
    manifest_verify_rc: int


def _utc_now_iso_v1() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _session_id_v1() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def execute_current_productive_native_full_cycle_host_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    evidence_root: Path | None = None,
    lane_state_root: Path | None = None,
    acquisition_transport: EeaPublicUniverseGetPortV1 | None = None,
    acquisition_result: EeaUniverseAcquisitionResultV1 | None = None,
    fresh_get_transport: FullCoreFreshPretradeGetTransportV1 | None = None,
    pre_external_fresh_get_transport: FullCoreFreshPretradeGetTransportV1 | None = None,
    execute_network: bool = False,
    vault_file: Path | str | None = None,
    producer_observed_at_unix: float | None = None,
    execution_integrity_backend: CurrentProductive29PRuntimeIntegrityBackendV1 | None = None,
) -> CurrentProductiveNativeFullCycleHostResultV1:
    """One-shot composition: EEA→Cap24 typed bound→MV2 advance→PRE_EXTERNAL."""
    if owner_go not in ALLOWED_OWNER_GOS:
        raise CurrentProductiveNativeFullCycleHostError("OWNER_GO_MISMATCH")
    base_sha = str(origin_main_sha or "").strip().lower()
    if not base_sha:
        raise CurrentProductiveNativeFullCycleHostError("ORIGIN_MAIN_SHA_MISSING")
    if fresh_get_transport is None and execute_network is not True:
        raise CurrentProductiveNativeFullCycleHostError(
            "FRESH_GET_TRANSPORT_OR_EXECUTE_NETWORK_REQUIRED"
        )

    session_id = _session_id_v1()
    store = (
        Path(evidence_root)
        if evidence_root is not None
        else _REPO_ROOT / "evidence" / "ops" / EVIDENCE_DIRNAME / session_id
    )
    store.mkdir(parents=True, exist_ok=True)
    lanes = Path(lane_state_root) if lane_state_root is not None else store / "lane_state"
    lanes.mkdir(parents=True, exist_ok=True)
    phase_eea = store / "phase_eea"
    phase_preext = store / "phase_pre_external"

    try:
        eea = execute_current_productive_eea_universe_inventory_to_cap24_and_29p_v1(
            owner_go=EEA_SLICE_OWNER_GO,
            origin_main_sha=base_sha,
            evidence_root=phase_eea,
            acquisition_transport=acquisition_transport,
            acquisition_result=acquisition_result,
            fresh_get_transport=fresh_get_transport,
            execute_network=execute_network,
            vault_file=vault_file,
            producer_observed_at_unix=producer_observed_at_unix,
            execution_integrity_backend=execution_integrity_backend,
        )
    except CurrentProductiveEeaUniverseTo29PError as exc:
        raise CurrentProductiveNativeFullCycleHostError(str(exc)) from exc

    bound = eea.bound_instrument
    handoff = "MISSING"
    if bound is not None and isinstance(bound, BoundInstrumentV1):
        handoff = "NATIVE_TYPED_FROM_EEA_RESULT"
    else:
        raise CurrentProductiveNativeFullCycleHostError("BOUND_INSTRUMENT_TYPED_HANDOFF_MISSING")

    try:
        mv2_advance = advance_layered_long_mv2_state_for_pre_external_v1(
            bound=bound,
            lane_state_root=lanes,
            origin_main_sha=base_sha,
            g17_evidence_root=store / "g17_controlled",
        )
    except LayeredLongMv2StateAdvanceError as exc:
        raise CurrentProductiveNativeFullCycleHostError(str(exc)) from exc

    candles = governed_c1_candles_payload_from_closes_v1(
        closes=mv2_advance.enter_closes,
        last_event_ts_unix=mv2_advance.enter_event_ts_unix,
    )
    mark_px = float(mv2_advance.enter_mark_px)
    market_kwargs: Mapping[str, Any] = {
        "cycle_id_prefix": "native-full-cycle-enter",
        "mark_px": mark_px,
        "index_px": mark_px * 0.995,
        "bid_px": mark_px - 0.5,
        "ask_px": mark_px + 0.5,
        "finalized_closes": mv2_advance.enter_closes,
        "last_finalized_event_ts_unix": mv2_advance.enter_event_ts_unix,
        "observed_unix": mv2_advance.enter_event_ts_unix + 100.0,
        "venue_flat": True,
        "existing_position_side": ExistingPositionSide.NONE,
        "volume": 10.0,
        "open_interest": 20.0,
        "funding_rate": 0.0001,
        "canonical_price_provenance": build_provenance_from_resolved_cmc_mark_and_index_v1(
            venue_native_id=str(bound.venue_native_id),
            mark_px=mark_px,
            index_px=mark_px * 0.995,
            index_source=INDEX_SOURCE_EXPLICIT_TEST_FIXTURE,
        ),
    }

    preext_transport = pre_external_fresh_get_transport or fresh_get_transport
    if preext_transport is None:
        raise CurrentProductiveNativeFullCycleHostError("PRE_EXTERNAL_FRESH_GET_TRANSPORT_REQUIRED")

    try:
        preext = execute_current_productive_full_core_pre_external_closure_v1(
            owner_go=PRE_EXTERNAL_SLICE_OWNER_GO,
            origin_main_sha=base_sha,
            bound_instrument=bound,
            lane_state_root=lanes,
            fresh_get_transport=preext_transport,
            execute_network=execute_network,
            vault_file=vault_file,
            evidence_root=phase_preext,
            candles_payload=candles,
            cap24_productivity_root=phase_eea,
            market_kwargs=market_kwargs,
            g17_typed_vol_producers={"LANE_1": mv2_advance.invoke_g17_producer},
            execution_integrity_backend=execution_integrity_backend,
        )
    except CurrentProductiveFullCorePreExternalClosureError as exc:
        raise CurrentProductiveNativeFullCycleHostError(str(exc)) from exc

    pre_reached = (
        TRUE_TOKEN
        if preext.terminal_disposition == DISPOSITION_PRE_EXTERNAL_EFFECT
        or preext.pre_external_effect_boundary_reached == TRUE_TOKEN
        else FALSE_TOKEN
    )
    claims = {
        "OWNER_GO": owner_go,
        "THIS_SLICE": THIS_SLICE,
        "SESSION_ID": session_id,
        "ORIGIN_MAIN_SHA": base_sha,
        "BOUND_INSTRUMENT_HANDOFF": handoff,
        "DRIVER_BOUND_RELOAD_REQUIRED": FALSE_TOKEN,
        "PRE_ARMED_MV2_FIXTURE_USED": FALSE_TOKEN,
        "TRADING_DECISION_AUTHORITY": TRADING_DECISION_AUTHORITY,
        "RANKING_AUTHORITY": RANKING_AUTHORITY,
        "SELECTION_AUTHORITY": SELECTION_AUTHORITY,
        "TERMINAL_DISPOSITION": preext.terminal_disposition,
        "PRE_EXTERNAL_REACHED": pre_reached,
        "POST_COUNT": str(preext.post_count),
        "PERMIT_CREATED": FALSE_TOKEN,
        "EXTERNAL_EFFECT_OCCURRED": FALSE_TOKEN,
    }
    _assert_no_secrets(claims)
    _persist_json(path=store / "NATIVE_FULL_CYCLE_CLAIMS.json", payload=claims)
    _persist_json(
        path=store / "SUMMARY.json",
        payload={
            "SESSION_ID": session_id,
            "TERMINAL_DISPOSITION": preext.terminal_disposition,
            "PRE_EXTERNAL_REACHED": pre_reached,
            "BOUND_HANDOFF": handoff,
        },
    )
    persist_manifest_sha256_v1(store_root=store)
    manifest_rc = verify_manifest_sha256_v1(store_root=store)

    return CurrentProductiveNativeFullCycleHostResultV1(
        store_root=str(store),
        session_id=session_id,
        origin_main_sha=base_sha,
        eea_result=eea,
        bound_instrument_handoff=handoff,
        mv2_advance_arm_side_state=mv2_advance.arm_side_state,
        mv2_advance_arm_decision=mv2_advance.arm_decision_outcome,
        pre_external_result=preext,
        terminal_disposition=preext.terminal_disposition,
        pre_external_reached=pre_reached,
        bound_instrument_native_typed=TRUE_TOKEN,
        driver_bound_reload_required=FALSE_TOKEN,
        pre_armed_mv2_fixture_used=FALSE_TOKEN,
        manifest_verify_rc=manifest_rc,
    )
