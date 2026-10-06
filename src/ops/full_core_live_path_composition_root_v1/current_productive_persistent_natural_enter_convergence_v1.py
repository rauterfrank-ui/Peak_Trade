"""CURRENT productive persistent Natural-ENTER convergence (S8→S6→S7→PRE_EXTERNAL).

Sequencing/ops authority only. Reuses occupied-lane N1 consumer join, S6 continuous
orchestrator, and S7 durable MV2+DP cursor persist. Does not POST, mint permits,
invoke Cap21→23 writers per cycle, or reinvoke Cap24 canonical writers per cycle.

RUNTIME_AUTHORIZATION_EFFECT=NONE (offline harness / preflight only unless explicitly
authorized productive continuous policy elsewhere — this module keeps
CONTINUOUS_RUN_AUTHORIZED=false and fails closed on productive execution).
"""

from __future__ import annotations

import inspect
import json
import os
import re
import tempfile
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from src.ops.current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1.invoke_join_v1 import (
    _align_lane_s7_closes_to_injected_c1_v1,
    _cursor_floor_or_zero,
    _t2_from_s7,
    non_v5_eg_dispatch_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_continuous_cycle_orchestrator_v1 import (
    DISPOSITION_FAIL_CLOSED as CONTINUOUS_DISPOSITION_FAIL_CLOSED,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 import (
    run_current_productive_governed_cycle_v1,
)
from src.ops.current_mf_n5_full_autonomy_occupied_lane_mv2_dp_decision_state_addressing_join_v1.addressing_join_v1 import (
    compose_occupied_lane_mv2_dp_durable_cycle_v1,
)
from src.ops.current_mf_n5_full_autonomy_occupied_lane_mv2_dp_decision_state_addressing_join_v1.addressing_join_v1 import (
    bind_occupied_lane_governed_cycle_store_roots_v1,
)
from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.constants_v1 import (
    LANE_IDS,
    OCCUPANCY_OCCUPIED,
)
from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.topology_v1 import (
    IsolatedLaneSlotV1,
    lane_state_root_for,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_actual_venue_post_owner_go_durable_consume_v1 import (
    POST_OWNER_GO,
    load_durable_post_owner_go_consume_v1,
)
from src.governance.current_continuous_run_runtime_binding_v1 import (
    ContinuousRunRuntimeBindingError,
    PolicyGovernedContinuousRunResultV1,
    run_policy_governed_current_productive_continuous_cycle_run_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_bounded_continuous_run_owner_go_wiring_v1 import (
    assert_module_pins_unchanged_v1,
    persist_bounded_continuous_run_owner_go_consume_v1,
    validate_bounded_continuous_run_owner_go_decision_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_continuous_observation_budget_v1 import (
    ABSOLUTE_MAX_CYCLES_PER_RUN,
    ABSOLUTE_MAX_RUN_DURATION_SECONDS,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_continuous_cycle_orchestrator_v1 import (
    CONTINUOUS_RUN_AUTHORIZED,
    DISPOSITION_PRE_EXTERNAL_EFFECT,
    CurrentProductiveGovernedContinuousCycleRunAuthorizationV1,
    CurrentProductiveGovernedContinuousCycleRunResultV1,
    ContinuousObservationSourceV1,
    InjectedContinuousObservationV1,
    RUNTIME_OWNER_GO as S6_RUNTIME_OWNER_GO,
    ScriptedContinuousObservationSourceV1,
    mint_continuous_run_id_v1,
    run_current_productive_governed_continuous_cycle_run_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 import (
    CurrentProductiveGovernedCycleAuthorizationV1,
    CurrentProductiveGovernedCycleResultV1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_canonical_price_provenance_v1 import (
    ProductiveCanonicalPriceProvenanceError,
    build_cmc_mark_provenance_from_okx_mark_price_payload_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1 import (
    extract_finalized_candle_closes_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_sidestate_confirmation_cursor_v1 import (
    CURSOR_FILENAME,
    load_current_productive_sidestate_confirmation_cursor_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_cap24_bound_instrument_provenance_handoff_v1 import (
    acquire_current_productive_29p_cap24_bound_instrument_provenance_handoff_v1,
)
from src.ops.single_selected_future_runtime_binding_v1.constants_v1 import (
    MAX_POSITIONS_EFFECTIVE,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1
from trading.master_v2.double_play_entry_exit_policy_v0 import ExistingPositionSide

OWNER = "full_core_live_path_composition_root_v1.current_productive_persistent_natural_enter_convergence_v1"
OFFLINE_HARNESS_OWNER_GO = (
    "OWNER_GO_CURRENT_PRODUCTIVE_PERSISTENT_NATURAL_ENTER_CONVERGENCE_OFFLINE_HARNESS_V1"
)
LANE_ID = "LANE_1"
MAX_CYCLES_PER_RUN_CAP = ABSOLUTE_MAX_CYCLES_PER_RUN
MAX_RUN_DURATION_CAP = ABSOLUTE_MAX_RUN_DURATION_SECONDS

RECONCILIATION_SAME_INSTRUMENT_CONTINUATION = "SAME_INSTRUMENT_CONTINUATION"
RECONCILIATION_SELECTION_ROTATION_FRESH_LANE = "SELECTION_ROTATION_FRESH_LANE"
RECONCILIATION_NO_PERSISTED_CURSOR = "NO_PERSISTED_CURSOR"
SUPERSEDED_CURSOR_FILENAME_PREFIX = (
    "current_productive_sidestate_confirmation_cursor_v1.superseded_selection_rotation_"
)


class PersistentNaturalEnterConvergenceError(ValueError):
    """Fail-closed persistent convergence violation."""

    def __init__(self, reason_code: str, detail: str = "") -> None:
        self.reason_code = reason_code
        self.detail = detail
        super().__init__(f"{reason_code}:{detail}" if detail else reason_code)


@dataclass(frozen=True)
class SelectionRotationCursorReconciliationV1:
    action: str
    persisted_native_id: str
    selected_native_id: str
    archived_cursor_path: str = ""


@dataclass(frozen=True)
class PersistentNaturalEnterPreflightV1:
    ok: bool
    reason_code: str
    bound_instrument: BoundInstrumentV1 | None
    native_id: str
    lane_state_root: str
    cursor_store_root: str
    selection_id: str
    cap24_reselection_performed: bool
    cursor_reconciliation_action: str = ""
    cursor_reconciliation_archived_path: str = ""


@dataclass(frozen=True)
class OwnerGoReuseAdjudicationV1:
    status: str
    authority: str
    post_owner_go_present: bool
    post_owner_go_consumed: bool
    post_consumer_reachable_from_runner: bool


def assert_productive_execution_forbidden_v1() -> None:
    if CONTINUOUS_RUN_AUTHORIZED is True:
        raise PersistentNaturalEnterConvergenceError(
            "CONTINUOUS_RUN_AUTHORIZED_MODULE_PIN_FORBIDDEN_TRUE"
        )


def assert_post_path_unreachable_from_runner_source_v1() -> bool:
    """Static proof: this runner module must not import POST execute entrypoints."""
    source = inspect.getsource(run_offline_persistent_natural_enter_convergence_v1)
    forbidden = (
        "execute_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1",
        "perform_real_venue_post=True",
        "FullCoreProductiveHttpPost",
    )
    return not any(token in source for token in forbidden)


def adjudicate_existing_owner_go_reuse_read_only_v1(
    *,
    post_durable_store_root: Path | None,
) -> OwnerGoReuseAdjudicationV1:
    loaded = load_durable_post_owner_go_consume_v1(store_root=post_durable_store_root)
    consumed = bool(loaded.get("consumed"))
    present = bool(loaded.get("present"))
    if not present:
        status = "VALID_UNTIL_CONSUMED"
    elif consumed:
        status = "NEW_ENVELOPE_REQUIRES_NEW_OWNER_GO"
    else:
        status = "VALID_UNTIL_CONSUMED"
    return OwnerGoReuseAdjudicationV1(
        status=status,
        authority=POST_OWNER_GO,
        post_owner_go_present=present,
        post_owner_go_consumed=consumed,
        post_consumer_reachable_from_runner=not assert_post_path_unreachable_from_runner_source_v1(),
    )


def persisted_cursor_venue_native_id_v1(cursor_payload: Mapping[str, Any]) -> str:
    """Canonical native id for continuous C1 lineage checks (top-level cursor field first)."""
    native = str(cursor_payload.get("venue_native_id") or "").strip()
    if native:
        return native
    cap61 = cursor_payload.get("cap61_confirmation_state")
    if isinstance(cap61, Mapping):
        oas = cap61.get("observation_acceptance_state")
        if isinstance(oas, Mapping):
            for key in ("bound_instrument_key", "instrument_key"):
                ikey = oas.get(key)
                if isinstance(ikey, Mapping):
                    vid = str(ikey.get("venue_instrument_id") or "").strip()
                    if vid:
                        return vid
    return ""


def _superseded_cursor_archive_path_v1(*, cursor_store_root: Path, old_native_id: str) -> Path:
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", old_native_id.strip()) or "unknown"
    base = cursor_store_root / f"{SUPERSEDED_CURSOR_FILENAME_PREFIX}{safe}.json"
    if not base.is_file():
        return base
    for index in range(1, 1000):
        candidate = cursor_store_root / (f"{SUPERSEDED_CURSOR_FILENAME_PREFIX}{safe}.{index}.json")
        if not candidate.is_file():
            return candidate
    raise PersistentNaturalEnterConvergenceError("SUPERSEDED_CURSOR_ARCHIVE_EXHAUSTED")


def _atomic_write_json_file_v1(*, path: Path, payload: Mapping[str, Any]) -> None:
    text = json.dumps(dict(payload), indent=2, sort_keys=True) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        prefix=".superseded_cursor_",
        suffix=".tmp",
        dir=str(path.parent),
    )
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, path)
    except OSError as exc:
        try:
            tmp_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise PersistentNaturalEnterConvergenceError(
            "CURSOR_ARCHIVE_WRITE_FAIL_CLOSED",
            str(exc),
        ) from exc
    if not path.is_file():
        raise PersistentNaturalEnterConvergenceError("CURSOR_ARCHIVE_WRITE_FAIL_CLOSED")
    try:
        json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PersistentNaturalEnterConvergenceError(
            "CURSOR_ARCHIVE_VERIFY_FAIL_CLOSED",
            str(exc),
        ) from exc


def reconcile_selection_rotation_with_persisted_cursor_v1(
    *,
    cursor_store_root: Path,
    bound: BoundInstrumentV1,
) -> SelectionRotationCursorReconciliationV1:
    """Align singleton lane cursor with Cap24-bound selection without cross-instrument carry."""
    selected = str(bound.venue_native_id or "").strip()
    if not selected:
        raise PersistentNaturalEnterConvergenceError("NATIVE_ID_MISSING")
    root = Path(cursor_store_root)
    active = root / CURSOR_FILENAME
    if not active.is_file():
        return SelectionRotationCursorReconciliationV1(
            action=RECONCILIATION_NO_PERSISTED_CURSOR,
            persisted_native_id="",
            selected_native_id=selected,
        )
    payload = load_current_productive_sidestate_confirmation_cursor_v1(root)
    if payload is None or not isinstance(payload, Mapping):
        raise PersistentNaturalEnterConvergenceError("CURSOR_LOAD_FAIL_CLOSED")
    persisted = persisted_cursor_venue_native_id_v1(payload)
    if not persisted:
        raise PersistentNaturalEnterConvergenceError("CURSOR_NATIVE_ID_UNREADABLE")
    if persisted == selected:
        return SelectionRotationCursorReconciliationV1(
            action=RECONCILIATION_SAME_INSTRUMENT_CONTINUATION,
            persisted_native_id=persisted,
            selected_native_id=selected,
        )
    archive_path = _superseded_cursor_archive_path_v1(
        cursor_store_root=root,
        old_native_id=persisted,
    )
    _atomic_write_json_file_v1(path=archive_path, payload=payload)
    try:
        active.unlink()
    except OSError as exc:
        raise PersistentNaturalEnterConvergenceError(
            "CURSOR_ACTIVE_REMOVAL_FAIL_CLOSED",
            str(exc),
        ) from exc
    if active.is_file():
        raise PersistentNaturalEnterConvergenceError("CURSOR_ACTIVE_REMOVAL_FAIL_CLOSED")
    return SelectionRotationCursorReconciliationV1(
        action=RECONCILIATION_SELECTION_ROTATION_FRESH_LANE,
        persisted_native_id=persisted,
        selected_native_id=selected,
        archived_cursor_path=str(archive_path),
    )


def build_s8_occupied_lane_pairs_v1(
    *,
    lane_state_root: Path,
    bound: BoundInstrumentV1,
) -> dict[str, tuple[IsolatedLaneSlotV1, BoundInstrumentV1]]:
    root = lane_state_root_for(
        topology_state_root_base=Path(lane_state_root),
        lane_id=LANE_ID,
    )
    slot = IsolatedLaneSlotV1(
        lane_id=LANE_ID,
        occupancy=OCCUPANCY_OCCUPIED,
        canonical_instrument_id=str(bound.instrument_id),
        lane_state_root=root,
        universe_snapshot_id=str(bound.universe_snapshot_id),
        ranking_snapshot_id=str(bound.ranking_snapshot_id),
        ranking_integrity_digest=str(bound.ranking_integrity_digest),
    )
    return {LANE_ID: (slot, bound)}


def preflight_current_productive_persistent_natural_enter_v1(
    *,
    productivity_root: Path,
    lane_state_root: Path,
    repository_sha: str,
    binding_epoch: str,
    authorization_native_id: str,
) -> PersistentNaturalEnterPreflightV1:
    handoff = acquire_current_productive_29p_cap24_bound_instrument_provenance_handoff_v1(
        productivity_root=Path(productivity_root),
        repository_sha=str(repository_sha),
        binding_epoch=str(binding_epoch),
    )
    bound = handoff.bound_instrument
    native_id = str(bound.venue_native_id or "").strip()
    if not native_id:
        return PersistentNaturalEnterPreflightV1(
            ok=False,
            reason_code="NATIVE_ID_MISSING",
            bound_instrument=None,
            native_id="",
            lane_state_root="",
            cursor_store_root="",
            selection_id="",
            cap24_reselection_performed=handoff.reselection_performed,
        )
    if native_id != str(authorization_native_id or "").strip():
        return PersistentNaturalEnterPreflightV1(
            ok=False,
            reason_code="AUTHORIZATION_NATIVE_ID_MISMATCH",
            bound_instrument=bound,
            native_id=native_id,
            lane_state_root="",
            cursor_store_root="",
            selection_id=handoff.selection_id,
            cap24_reselection_performed=handoff.reselection_performed,
        )
    pairs = build_s8_occupied_lane_pairs_v1(
        lane_state_root=Path(lane_state_root),
        bound=bound,
    )
    addressed = bind_occupied_lane_governed_cycle_store_roots_v1(pairs)
    roots = addressed.get(LANE_ID)
    if roots is None:
        return PersistentNaturalEnterPreflightV1(
            ok=False,
            reason_code="S8_ROOTS_MISSING",
            bound_instrument=bound,
            native_id=native_id,
            lane_state_root="",
            cursor_store_root="",
            selection_id=handoff.selection_id,
            cap24_reselection_performed=handoff.reselection_performed,
        )
    cursor_store_root, _lock_root, _evidence_root = roots
    lane_root = str(pairs[LANE_ID][0].lane_state_root)
    if Path(cursor_store_root).resolve() != Path(lane_root).resolve():
        return PersistentNaturalEnterPreflightV1(
            ok=False,
            reason_code="CURSOR_STORE_ROOT_MISMATCH",
            bound_instrument=bound,
            native_id=native_id,
            lane_state_root=lane_root,
            cursor_store_root=str(cursor_store_root),
            selection_id=handoff.selection_id,
            cap24_reselection_performed=handoff.reselection_performed,
        )
    try:
        reconciliation = reconcile_selection_rotation_with_persisted_cursor_v1(
            cursor_store_root=Path(cursor_store_root),
            bound=bound,
        )
    except PersistentNaturalEnterConvergenceError as exc:
        return PersistentNaturalEnterPreflightV1(
            ok=False,
            reason_code=exc.reason_code,
            bound_instrument=bound,
            native_id=native_id,
            lane_state_root=lane_root,
            cursor_store_root=str(cursor_store_root),
            selection_id=handoff.selection_id,
            cap24_reselection_performed=handoff.reselection_performed,
        )
    return PersistentNaturalEnterPreflightV1(
        ok=True,
        reason_code="",
        bound_instrument=bound,
        native_id=native_id,
        lane_state_root=lane_root,
        cursor_store_root=str(cursor_store_root),
        selection_id=handoff.selection_id,
        cap24_reselection_performed=handoff.reselection_performed,
        cursor_reconciliation_action=reconciliation.action,
        cursor_reconciliation_archived_path=reconciliation.archived_cursor_path,
    )


def _bid_ask_from_finalized_candles_v1(
    candles_payload: Mapping[str, Any], *, mark_px: float
) -> tuple[float, float]:
    """Use last finalized 1m bar low/high so sub-dollar marks stay valid for MV2 context."""
    data = candles_payload.get("data")
    if not isinstance(data, list):
        spread = max(mark_px * 0.001, 1e-6)
        return mark_px - spread, mark_px + spread
    finalized_rows: list[tuple[float, float, float, float]] = []
    for row in data:
        if not isinstance(row, (list, tuple)) or len(row) < 9:
            continue
        if str(row[8] or "").strip() != "1":
            continue
        try:
            ts = float(row[0]) / 1000.0
            high = float(row[2])
            low = float(row[3])
            close = float(row[4])
        except (TypeError, ValueError):
            continue
        if high <= 0 or low <= 0 or close <= 0 or low > high:
            continue
        finalized_rows.append((ts, low, high, close))
    if not finalized_rows:
        spread = max(mark_px * 0.001, 1e-6)
        return mark_px - spread, mark_px + spread
    finalized_rows.sort(key=lambda item: item[0])
    _ts, low, high, _close = finalized_rows[-1]
    if low < high:
        return low, high
    spread = max(mark_px * 0.001, 1e-6)
    return mark_px - spread, mark_px + spread


def _market_kwargs_from_observation_v1(
    *,
    candles_payload: Mapping[str, Any],
    mark_price_payload: Mapping[str, Any],
    venue_native_id: str,
    index_tickers_payload: Mapping[str, Any] | None = None,
    cycle_id_prefix: str,
    origin_main_sha: str,
    g17_producers: Mapping[str, object],
) -> dict[str, Any]:
    extracted, last_ts = extract_finalized_candle_closes_v1(candles_payload)
    if not extracted or last_ts is None:
        raise PersistentNaturalEnterConvergenceError("C1_CLOSES_EXTRACT_FAIL_CLOSED")
    try:
        provenance = build_cmc_mark_provenance_from_okx_mark_price_payload_v1(
            mark_price_payload=mark_price_payload,
            venue_native_id=venue_native_id,
            index_from_index_tickers=index_tickers_payload,
        )
    except ProductiveCanonicalPriceProvenanceError as exc:
        raise PersistentNaturalEnterConvergenceError(
            "CMC_MARK_OR_INDEX_PROVENANCE_FAIL_CLOSED", str(exc)
        ) from exc
    mark_px = float(provenance.mark_px)
    index_px = float(provenance.index_px)
    event_ts = float(last_ts)
    bid_px, ask_px = _bid_ask_from_finalized_candles_v1(candles_payload, mark_px=mark_px)
    return {
        "origin_main_sha": origin_main_sha,
        "cycle_id_prefix": cycle_id_prefix,
        "observed_unix": event_ts + 1.0,
        "mark_px": mark_px,
        "index_px": index_px,
        "bid_px": bid_px,
        "ask_px": ask_px,
        "volume": 10.0,
        "open_interest": 20.0,
        "funding_rate": 0.0001,
        "finalized_closes": extracted,
        "last_finalized_event_ts_unix": event_ts,
        "venue_flat": True,
        "existing_position_side": ExistingPositionSide.NONE,
        "g17_typed_vol_producers": dict(g17_producers),
        "canonical_price_provenance": provenance,
    }


def resolve_live_29p_injected_for_productive_s5_cycle_v1(
    *,
    bound: BoundInstrumentV1,
    fresh_pretrade_get_transport: Any | None,
    productivity_root: Path | None,
    decision_epoch: str,
) -> Any | None:
    """Build enter-live-29p injected carrier from shared fresh-pretrade GET transport.

    Uses the same common-epoch compose + handoff path as pre-external closure.
    Returns None when transport is absent or handoff/injection fail-closed (ENTER
    then fails at LIVE_29P join with GET_MISSING). Does not POST or activate credentials.
    """
    if fresh_pretrade_get_transport is None:
        return None
    from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_common_epoch_handoff_v1 import (
        CurrentProductive29PCommonEpochHandoffError,
        compose_current_productive_29p_common_epoch_handoff_v1,
        _resolve_public_inst_type_for_bound_instrument_v1,
    )
    from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_common_epoch_to_enter_live_29p_handoff_v1 import (
        CurrentProductiveCommonEpochToEnterLive29PHandoffError,
        build_current_productive_enter_live_29p_injected_from_common_epoch_handoff_v1,
    )

    epoch = str(decision_epoch or "").strip()
    if not epoch:
        return None
    prod_root = Path(productivity_root) if productivity_root is not None else None
    try:
        inst_type = _resolve_public_inst_type_for_bound_instrument_v1(
            bound=bound,
            productivity_root=prod_root,
            cap21_public_inst_type=None,
        )
        handoff = compose_current_productive_29p_common_epoch_handoff_v1(
            decision_epoch=epoch,
            bound_instrument=bound,
            fresh_get_transport=fresh_pretrade_get_transport,
            inst_type=inst_type,
        )
        if handoff.evaluator_29p is not True:
            return None
        return build_current_productive_enter_live_29p_injected_from_common_epoch_handoff_v1(
            handoff=handoff,
            transport=fresh_pretrade_get_transport,
        )
    except (
        CurrentProductive29PCommonEpochHandoffError,
        CurrentProductiveCommonEpochToEnterLive29PHandoffError,
    ):
        return None
    except Exception as exc:
        from src.ops.full_core_live_path_composition_root_v1.productive_read_only_get_transport_v1 import (
            FullCoreProductiveReadOnlyGetError,
        )

        if isinstance(exc, FullCoreProductiveReadOnlyGetError):
            return None
        raise


def make_n1_occupied_lane_s5_runner_v1(
    *,
    composed_pairs: Mapping[str, tuple[IsolatedLaneSlotV1, BoundInstrumentV1]],
    g17_producers: Mapping[str, object],
    cycle_id_prefix_base: str,
    forensic_observability_enabled: bool = False,
    synthetic_enter_forensic_enabled: bool = False,
    fresh_pretrade_get_transport: Any | None = None,
    cap24_productivity_root: Path | None = None,
) -> Callable[..., CurrentProductiveGovernedCycleResultV1]:
    """Adapt S6 S5 slot to occupied-lane N1 consumer (S7 T2 durable compose)."""

    def _runner(
        *,
        authorization: CurrentProductiveGovernedCycleAuthorizationV1,
        origin_main_sha: str,
        cursor_store_root: Path,
        lock_root: Path,
        evidence_root: Path,
        candles_payload: Mapping[str, Any],
        occupancy_payloads: Mapping[str, Any] | None = None,
        execute_network: bool = False,
        perform_get: bool = False,
        eg_cycle_dispatch: Callable[..., Any] | None = None,
        t2_cycle_dispatch: Callable[..., Any] | None = None,
        mark_price_payload: Mapping[str, Any] | None = None,
        index_tickers_payload: Mapping[str, Any] | None = None,
        **_: Any,
    ) -> CurrentProductiveGovernedCycleResultV1:
        if execute_network or perform_get:
            raise PersistentNaturalEnterConvergenceError("NETWORK_FORBIDDEN_THIS_RUNNER")
        addressed = bind_occupied_lane_governed_cycle_store_roots_v1(composed_pairs)
        lane_roots = addressed.get(LANE_ID)
        if lane_roots is None:
            raise PersistentNaturalEnterConvergenceError("S8_ROOTS_MISSING")
        expected_cursor_root = str(lane_roots[0])
        if Path(cursor_store_root).resolve() != Path(expected_cursor_root).resolve():
            raise PersistentNaturalEnterConvergenceError(
                "CURSOR_STORE_ROOT_DRIFT",
                f"expected={expected_cursor_root} actual={cursor_store_root}",
            )
        prefix = f"{cycle_id_prefix_base}:{Path(evidence_root).name}"
        native_id = str(authorization.native_id or "").strip()
        if mark_price_payload is None or not native_id:
            raise PersistentNaturalEnterConvergenceError("CMC_MARK_PRICE_PAYLOAD_REQUIRED")
        if forensic_observability_enabled:
            from src.ops.full_core_live_path_composition_root_v1.productive_golden_happy_vector_forensic_observability_v1 import (
                active_forensic_observability_session_v1,
            )

            obs_session = active_forensic_observability_session_v1()
            if obs_session is not None:
                obs_session.with_cycle_from_s5_evidence_root_v1(
                    s5_evidence_root=Path(evidence_root),
                )
        from src.ops.full_core_live_path_composition_root_v1.ghv_pre_external_runtime_flight_recorder_v1 import (
            sync_flight_recorder_cycle_from_s5_evidence_root_v1,
        )

        sync_flight_recorder_cycle_from_s5_evidence_root_v1(
            s5_evidence_root=Path(evidence_root),
        )
        mk = _market_kwargs_from_observation_v1(
            candles_payload=candles_payload,
            mark_price_payload=mark_price_payload,
            venue_native_id=native_id,
            index_tickers_payload=index_tickers_payload,
            cycle_id_prefix=prefix,
            origin_main_sha=origin_main_sha,
            g17_producers=g17_producers,
        )
        lane_pairs = {LANE_ID: composed_pairs[LANE_ID]}
        s7_base = {
            key: value
            for key, value in mk.items()
            if key not in {"origin_main_sha", "g17_typed_vol_producers"}
        }
        s7_base["g17_typed_vol_producers"] = {LANE_ID: g17_producers[LANE_ID]}
        if synthetic_enter_forensic_enabled:
            s7_base["cycle_evidence_root"] = str(Path(evidence_root).resolve())
        _bound = composed_pairs[LANE_ID][1]
        decision_epoch = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        live_29p_injected = resolve_live_29p_injected_for_productive_s5_cycle_v1(
            bound=_bound,
            fresh_pretrade_get_transport=fresh_pretrade_get_transport,
            productivity_root=cap24_productivity_root,
            decision_epoch=decision_epoch,
        )
        t2_dispatch = _t2_from_s7(
            lane_pairs=lane_pairs,
            native_id=native_id,
            lane_id=LANE_ID,
            s7_base={**s7_base, "cycle_id_prefix": f"{prefix}:{LANE_ID}"},
            live_29p_injected=live_29p_injected,
            candles_payload=dict(candles_payload),
            portfolio_budget_owner=None,
            common_epoch_decision_epoch=decision_epoch,
        )
        return run_current_productive_governed_cycle_v1(
            authorization=authorization,
            origin_main_sha=origin_main_sha,
            cursor_store_root=Path(cursor_store_root),
            lock_root=Path(lock_root),
            evidence_root=Path(evidence_root),
            candles_payload=dict(candles_payload),
            occupancy_payloads=occupancy_payloads,
            execute_network=False,
            perform_get=False,
            eg_cycle_dispatch=eg_cycle_dispatch or non_v5_eg_dispatch_v1,
            t2_cycle_dispatch=t2_dispatch,
        )

    return _runner


def _read_trading_epoch_v1(cursor_store_root: Path) -> int | None:
    path = Path(cursor_store_root) / CURSOR_FILENAME
    if not path.is_file():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    try:
        return int(payload["trading_epoch"])
    except (KeyError, TypeError, ValueError):
        return None


def _read_bull_confirmation_count_v1(cursor_store_root: Path) -> int | None:
    path = Path(cursor_store_root) / CURSOR_FILENAME
    if not path.is_file():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    try:
        cap61 = payload["cap61_confirmation_state"]
        return int(cap61["bull_confirmation_state"]["distinct_confirmation_observation_count"])
    except (KeyError, TypeError, ValueError):
        return None


def bootstrap_s8_lane_via_s7_compose_v1(
    *,
    composed_pairs: Mapping[str, tuple[IsolatedLaneSlotV1, BoundInstrumentV1]],
    origin_main_sha: str,
    g17_producers: Mapping[str, object],
    candles_payload: Mapping[str, Any],
    mark_price_payload: Mapping[str, Any],
    venue_native_id: str,
    index_tickers_payload: Mapping[str, Any] | None = None,
    cycle_id_prefix: str = "persistent-natural-enter-bootstrap",
) -> None:
    """Cold-lane S7 compose only (cursor persist) without S5 governed-cycle ledger."""
    _ = origin_main_sha
    lane_pairs = {LANE_ID: composed_pairs[LANE_ID]}
    mk = _market_kwargs_from_observation_v1(
        candles_payload=candles_payload,
        mark_price_payload=mark_price_payload,
        venue_native_id=venue_native_id,
        index_tickers_payload=index_tickers_payload,
        cycle_id_prefix=cycle_id_prefix,
        origin_main_sha=origin_main_sha,
        g17_producers=g17_producers,
    )
    s7 = {
        key: value
        for key, value in mk.items()
        if key not in {"origin_main_sha", "g17_typed_vol_producers"}
    }
    if LANE_ID not in g17_producers:
        raise PersistentNaturalEnterConvergenceError("G17_PRODUCER_MISSING", LANE_ID)
    s7["g17_typed_vol_producers"] = {LANE_ID: g17_producers[LANE_ID]}
    s7 = _align_lane_s7_closes_to_injected_c1_v1(s7, dict(candles_payload))
    compose_occupied_lane_mv2_dp_durable_cycle_v1(lane_pairs, **s7)


def run_offline_persistent_natural_enter_convergence_v1(
    *,
    authorization: CurrentProductiveGovernedContinuousCycleRunAuthorizationV1,
    origin_main_sha: str,
    lane_state_root: Path,
    bound: BoundInstrumentV1,
    g17_producers: Mapping[str, object],
    observation_source: ContinuousObservationSourceV1,
    evidence_root: Path,
    bootstrap_observation: InjectedContinuousObservationV1 | None = None,
    lock_root: Path | None = None,
    cycle_id_prefix_base: str = "persistent-natural-enter",
    time_fn: Callable[[], float] | None = None,
    sleep_fn: Callable[[float], None] | None = None,
) -> CurrentProductiveGovernedContinuousCycleRunResultV1:
    """Bounded offline S6 run with fixed S8 lane + S7 persist (no POST, no network)."""
    assert_productive_execution_forbidden_v1()
    if int(authorization.max_cycles_per_run) > MAX_CYCLES_PER_RUN_CAP:
        raise PersistentNaturalEnterConvergenceError("MAX_CYCLES_EXCEEDS_HARD_CAP")
    if float(authorization.max_run_duration_seconds) > MAX_RUN_DURATION_CAP:
        raise PersistentNaturalEnterConvergenceError("MAX_DURATION_EXCEEDS_HARD_CAP")
    if authorization.continuous_owner_go != S6_RUNTIME_OWNER_GO:
        raise PersistentNaturalEnterConvergenceError("S6_RUNTIME_OWNER_GO_MISMATCH")
    pairs = build_s8_occupied_lane_pairs_v1(
        lane_state_root=Path(lane_state_root),
        bound=bound,
    )
    addressed = bind_occupied_lane_governed_cycle_store_roots_v1(pairs)
    cursor_store_root = Path(addressed[LANE_ID][0])
    if cursor_store_root.resolve() != Path(pairs[LANE_ID][0].lane_state_root).resolve():
        raise PersistentNaturalEnterConvergenceError("FIXED_LANE_ROOT_VIOLATION")
    if not (cursor_store_root / CURSOR_FILENAME).is_file():
        first_obs = bootstrap_observation
        if first_obs is None:
            first_obs = observation_source.poll()
        if first_obs is None:
            raise PersistentNaturalEnterConvergenceError(
                "BOOTSTRAP_OBSERVATION_REQUIRED",
                "cold lane requires first injected C1 before S6",
            )
        if first_obs.mark_price_payload is None:
            raise PersistentNaturalEnterConvergenceError("BOOTSTRAP_CMC_MARK_PAYLOAD_REQUIRED")
        bootstrap_s8_lane_via_s7_compose_v1(
            composed_pairs=pairs,
            origin_main_sha=origin_main_sha,
            g17_producers=g17_producers,
            candles_payload=first_obs.candles_payload,
            mark_price_payload=first_obs.mark_price_payload,
            venue_native_id=str(bound.venue_native_id or "").strip(),
            index_tickers_payload=first_obs.index_tickers_payload,
        )
    runner = make_n1_occupied_lane_s5_runner_v1(
        composed_pairs=pairs,
        g17_producers=g17_producers,
        cycle_id_prefix_base=cycle_id_prefix_base,
    )
    lock = lock_root or (Path(evidence_root) / "continuous_lock")
    return run_current_productive_governed_continuous_cycle_run_v1(
        authorization=authorization,
        origin_main_sha=origin_main_sha,
        cursor_store_root=cursor_store_root,
        lock_root=Path(lock),
        evidence_root=Path(evidence_root),
        observation_source=observation_source,
        execute_network=False,
        perform_get=False,
        s5_runner=runner,
        time_fn=time_fn,
        sleep_fn=sleep_fn,
    )


def run_policy_governed_persistent_natural_enter_live_c1_continuous_run_v1(
    *,
    authorization: CurrentProductiveGovernedContinuousCycleRunAuthorizationV1,
    origin_main_sha: str,
    lane_state_root: Path,
    bound: BoundInstrumentV1,
    g17_producers: Mapping[str, object],
    observation_source: ContinuousObservationSourceV1,
    evidence_root: Path,
    f1_m9_cycle_evaluator: Callable[[int], Any],
    repo_root: Path | None = None,
    bootstrap_observation: InjectedContinuousObservationV1 | None = None,
    lock_root: Path | None = None,
    cycle_id_prefix_base: str = "persistent-natural-enter-live-c1",
    time_fn: Callable[[], float] | None = None,
    sleep_fn: Callable[[float], None] | None = None,
    enable_golden_happy_vector_forensic_observability_v1: bool = False,
    enable_ghv_pre_external_runtime_flight_recorder_v1: bool = False,
    enable_ghv_system_wide_canary_surface_discovery_v1: bool = False,
    enable_synthetic_enter_forensic_v1: bool = False,
    synthetic_enter_forensic_side: str = "enter_short",
    synthetic_enter_forensic_cycle_index: int = 1,
    enable_forensic_executable_quantity_override_v1: bool = False,
    forensic_executable_quantity: str = "",
    enable_real_carrier_passive_capture_v1: bool = False,
    real_carrier_passive_capture_root: Path | None = None,
    selection_id: str = "",
    binding_epoch: str = "",
    cap24_reselection_performed: bool = False,
    fresh_pretrade_get_transport: Any | None = None,
    cap24_productivity_root: Path | None = None,
) -> PolicyGovernedContinuousRunResultV1:
    """S8→policy binding→S6 (live or test observation source)→N1/S5/S7→PRE_EXTERNAL."""
    assert_module_pins_unchanged_v1()
    if CONTINUOUS_RUN_AUTHORIZED is True:
        raise PersistentNaturalEnterConvergenceError(
            "CONTINUOUS_RUN_AUTHORIZED_MODULE_PIN_FORBIDDEN_TRUE"
        )
    ok, reasons = validate_bounded_continuous_run_owner_go_decision_v1(
        repo_root=repo_root,
        baseline_origin_main_sha=origin_main_sha,
    )
    if not ok:
        raise PersistentNaturalEnterConvergenceError("OWNER_GO_DECISION_DENIED", ",".join(reasons))
    if authorization.continuous_owner_go != S6_RUNTIME_OWNER_GO:
        raise PersistentNaturalEnterConvergenceError("S6_RUNTIME_OWNER_GO_MISMATCH")
    if int(authorization.max_cycles_per_run) > MAX_CYCLES_PER_RUN_CAP:
        raise PersistentNaturalEnterConvergenceError("MAX_CYCLES_EXCEEDS_HARD_CAP")
    if float(authorization.max_run_duration_seconds) > MAX_RUN_DURATION_CAP:
        raise PersistentNaturalEnterConvergenceError("MAX_DURATION_EXCEEDS_HARD_CAP")
    if f1_m9_cycle_evaluator is None:
        raise PersistentNaturalEnterConvergenceError("F1_M9_CYCLE_EVALUATOR_REQUIRED")

    forensic_session_reset = None
    flight_recorder_session_reset = None
    canary_session_reset = None
    synthetic_session_reset = None
    forensic_quantity_override_session_reset = None
    real_carrier_capture_session_reset = None
    pairs = build_s8_occupied_lane_pairs_v1(
        lane_state_root=Path(lane_state_root),
        bound=bound,
    )
    addressed = bind_occupied_lane_governed_cycle_store_roots_v1(pairs)
    cursor_store_root = Path(addressed[LANE_ID][0])
    if cursor_store_root.resolve() != Path(pairs[LANE_ID][0].lane_state_root).resolve():
        raise PersistentNaturalEnterConvergenceError("FIXED_LANE_ROOT_VIOLATION")

    reconciliation = reconcile_selection_rotation_with_persisted_cursor_v1(
        cursor_store_root=cursor_store_root,
        bound=bound,
    )

    run_id = mint_continuous_run_id_v1(authorization)
    if enable_synthetic_enter_forensic_v1:
        from src.ops.full_core_live_path_composition_root_v1.current_productive_synthetic_enter_forensic_v1 import (
            bind_synthetic_enter_forensic_session_v1,
            build_synthetic_enter_forensic_session_v1,
        )

        synthetic_session = build_synthetic_enter_forensic_session_v1(
            enabled=True,
            synthetic_side=synthetic_enter_forensic_side,
            inject_cycle_index=synthetic_enter_forensic_cycle_index,
            product_evidence_root=Path(evidence_root),
            continuous_run_id=run_id,
        )
        synthetic_session_reset = bind_synthetic_enter_forensic_session_v1(synthetic_session)
    if enable_forensic_executable_quantity_override_v1:
        from src.ops.full_core_live_path_composition_root_v1.current_productive_forensic_executable_quantity_override_v1 import (
            bind_forensic_executable_quantity_override_session_v1,
            build_forensic_executable_quantity_override_session_v1,
        )

        fq_session = build_forensic_executable_quantity_override_session_v1(
            enabled=True,
            explicit_forensic_quantity=forensic_executable_quantity or None,
            product_evidence_root=Path(evidence_root),
            continuous_run_id=run_id,
            require_ghv_pre_external_runtime_flight_recorder_v1=(
                enable_ghv_pre_external_runtime_flight_recorder_v1
            ),
        )
        forensic_quantity_override_session_reset = (
            bind_forensic_executable_quantity_override_session_v1(fq_session)
        )
    if enable_golden_happy_vector_forensic_observability_v1:
        from src.ops.full_core_live_path_composition_root_v1.productive_golden_happy_vector_forensic_observability_v1 import (
            GoldenHappyVectorForensicObservabilitySessionV1,
            bind_golden_happy_vector_forensic_observability_session_v1,
            persist_continuous_run_entry_state_snapshot_v1,
        )

        forensic_session = GoldenHappyVectorForensicObservabilitySessionV1(
            enabled=True,
            product_evidence_root=Path(evidence_root),
            run_id=run_id,
            continuous_run_id=run_id,
            repository_sha=str(origin_main_sha),
        )
        forensic_session_reset = bind_golden_happy_vector_forensic_observability_session_v1(
            forensic_session
        )
    if enable_real_carrier_passive_capture_v1:
        if real_carrier_passive_capture_root is None:
            raise PersistentNaturalEnterConvergenceError(
                "REAL_CARRIER_PASSIVE_CAPTURE_ROOT_REQUIRED"
            )
        from src.ops.full_core_live_path_composition_root_v1.productive_real_carrier_passive_capture_v1 import (
            RealCarrierPassiveCaptureSessionV1,
            bind_real_carrier_passive_capture_session_v1,
        )

        capture_root = Path(real_carrier_passive_capture_root).expanduser().resolve()
        real_carrier_session = RealCarrierPassiveCaptureSessionV1(
            enabled=True,
            capture_armed=True,
            capture_root=capture_root,
            run_id=run_id,
            continuous_run_id=run_id,
        )
        real_carrier_capture_session_reset = bind_real_carrier_passive_capture_session_v1(
            real_carrier_session
        )
    if enable_ghv_pre_external_runtime_flight_recorder_v1:
        from src.ops.full_core_live_path_composition_root_v1.ghv_pre_external_runtime_flight_recorder_v1 import (
            GhvPreExternalRuntimeFlightRecorderSessionV1,
            bind_ghv_pre_external_runtime_flight_recorder_session_v1,
        )

        flight_session = GhvPreExternalRuntimeFlightRecorderSessionV1(
            enabled=True,
            product_evidence_root=Path(evidence_root),
            run_id=run_id,
            continuous_run_id=run_id,
            repository_sha=str(origin_main_sha),
        )
        flight_recorder_session_reset = bind_ghv_pre_external_runtime_flight_recorder_session_v1(
            flight_session
        )
    if enable_ghv_system_wide_canary_surface_discovery_v1:
        from src.ops.full_core_live_path_composition_root_v1.ghv_system_wide_canary_surface_discovery_v1 import (
            GhvSystemWideCanarySessionV1,
            bind_ghv_system_wide_canary_session_v1,
        )

        canary_session = GhvSystemWideCanarySessionV1(
            enabled=True,
            ghv_canary_trace_id=GhvSystemWideCanarySessionV1.new_trace_id(
                run_id=run_id,
                cycle_index=synthetic_enter_forensic_cycle_index,
            ),
            cycle_index=synthetic_enter_forensic_cycle_index,
        )
        canary_session_reset = bind_ghv_system_wide_canary_session_v1(canary_session)
    if enable_golden_happy_vector_forensic_observability_v1:
        cursor_floor_pre_obs = _cursor_floor_or_zero(cursor_store_root)
        persist_continuous_run_entry_state_snapshot_v1(
            session=forensic_session,
            bound=bound,
            reconciliation=reconciliation,
            cursor_store_root=cursor_store_root,
            expected_cursor_floor=float(cursor_floor_pre_obs),
            selection_id=selection_id,
            binding_epoch=binding_epoch,
            cap24_reselection_performed=cap24_reselection_performed,
        )
    persist_bounded_continuous_run_owner_go_consume_v1(
        evidence_root=Path(evidence_root),
        run_id=run_id,
        baseline_origin_main_sha=origin_main_sha,
        binding_digest=run_id,
    )

    if not (cursor_store_root / CURSOR_FILENAME).is_file():
        first_obs = bootstrap_observation
        if first_obs is None:
            first_obs = observation_source.poll()
        if first_obs is None:
            raise PersistentNaturalEnterConvergenceError(
                "BOOTSTRAP_OBSERVATION_REQUIRED",
                "cold lane requires first C1 before S6",
            )
        if first_obs.mark_price_payload is None:
            raise PersistentNaturalEnterConvergenceError("BOOTSTRAP_CMC_MARK_PAYLOAD_REQUIRED")
        bootstrap_s8_lane_via_s7_compose_v1(
            composed_pairs=pairs,
            origin_main_sha=origin_main_sha,
            g17_producers=g17_producers,
            candles_payload=first_obs.candles_payload,
            mark_price_payload=first_obs.mark_price_payload,
            venue_native_id=str(bound.venue_native_id or "").strip(),
            index_tickers_payload=first_obs.index_tickers_payload,
        )

    cursor_floor = _cursor_floor_or_zero(cursor_store_root)
    if float(authorization.expected_cursor_floor) != float(cursor_floor):
        authorization = replace(
            authorization,
            expected_cursor_floor=float(cursor_floor),
        )

    runner = make_n1_occupied_lane_s5_runner_v1(
        composed_pairs=pairs,
        g17_producers=g17_producers,
        cycle_id_prefix_base=cycle_id_prefix_base,
        forensic_observability_enabled=enable_golden_happy_vector_forensic_observability_v1,
        synthetic_enter_forensic_enabled=enable_synthetic_enter_forensic_v1,
        fresh_pretrade_get_transport=fresh_pretrade_get_transport,
        cap24_productivity_root=cap24_productivity_root,
    )
    lock = lock_root or (Path(evidence_root) / "continuous_lock")
    root = repo_root or Path(__file__).resolve().parents[3]
    try:
        result = run_policy_governed_current_productive_continuous_cycle_run_v1(
            authorization=authorization,
            origin_main_sha=origin_main_sha,
            cursor_store_root=cursor_store_root,
            lock_root=Path(lock),
            evidence_root=Path(evidence_root),
            observation_source=observation_source,
            repo_root=root,
            f1_m9_cycle_evaluator=f1_m9_cycle_evaluator,
            require_f1_m9_each_cycle=True,
            s5_runner=runner,
            time_fn=time_fn,
            sleep_fn=sleep_fn,
        )
    except ContinuousRunRuntimeBindingError as exc:
        raise PersistentNaturalEnterConvergenceError(exc.reason_code, exc.detail) from exc
    finally:
        if synthetic_session_reset is not None:
            from src.ops.full_core_live_path_composition_root_v1.current_productive_synthetic_enter_forensic_v1 import (
                reset_synthetic_enter_forensic_session_v1,
            )

            reset_synthetic_enter_forensic_session_v1(synthetic_session_reset)
        if forensic_quantity_override_session_reset is not None:
            from src.ops.full_core_live_path_composition_root_v1.current_productive_forensic_executable_quantity_override_v1 import (
                reset_forensic_executable_quantity_override_session_v1,
            )

            reset_forensic_executable_quantity_override_session_v1(
                forensic_quantity_override_session_reset
            )
        if forensic_session_reset is not None:
            from src.ops.full_core_live_path_composition_root_v1.productive_golden_happy_vector_forensic_observability_v1 import (
                reset_golden_happy_vector_forensic_observability_session_v1,
            )

            reset_golden_happy_vector_forensic_observability_session_v1(forensic_session_reset)
        if flight_recorder_session_reset is not None:
            from src.ops.full_core_live_path_composition_root_v1.ghv_pre_external_runtime_flight_recorder_v1 import (
                reset_ghv_pre_external_runtime_flight_recorder_session_v1,
            )

            reset_ghv_pre_external_runtime_flight_recorder_session_v1(flight_recorder_session_reset)
        if canary_session_reset is not None:
            from src.ops.full_core_live_path_composition_root_v1.ghv_system_wide_canary_surface_discovery_v1 import (
                reset_ghv_system_wide_canary_session_v1,
            )

            reset_ghv_system_wide_canary_session_v1(canary_session_reset)
        if real_carrier_capture_session_reset is not None:
            from src.ops.full_core_live_path_composition_root_v1.productive_real_carrier_passive_capture_v1 import (
                reset_real_carrier_passive_capture_session_v1,
            )

            reset_real_carrier_passive_capture_session_v1(real_carrier_capture_session_reset)

    orch = result.orchestrator_result
    if orch.post_count != 0 or orch.permit_created or orch.external_effect_count != 0:
        raise PersistentNaturalEnterConvergenceError("EXTERNAL_EFFECT_LEAK")
    if orch.disposition not in {
        DISPOSITION_PRE_EXTERNAL_EFFECT,
        "MAX_CYCLES_BOUND_STOP",
        "MAX_DURATION_BOUND_STOP",
        "STALL_BOUND_STOP",
        "WAIT_BOUND",
        "HOLD_CONTINUE_CLOSED",
        CONTINUOUS_DISPOSITION_FAIL_CLOSED,
    }:
        raise PersistentNaturalEnterConvergenceError(
            "UNEXPECTED_TERMINAL_DISPOSITION", str(orch.disposition)
        )
    return result


def read_sidestate_continuity_snapshot_v1(cursor_store_root: Path) -> dict[str, int | None]:
    return {
        "trading_epoch": _read_trading_epoch_v1(cursor_store_root),
        "bull_distinct_confirmation_count": _read_bull_confirmation_count_v1(cursor_store_root),
    }


__all__ = [
    "LANE_ID",
    "MAX_CYCLES_PER_RUN_CAP",
    "MAX_POSITIONS_EFFECTIVE",
    "MULTI_FUTURE_RUNTIME_AUTHORIZED",
    "OFFLINE_HARNESS_OWNER_GO",
    "OWNER",
    "OwnerGoReuseAdjudicationV1",
    "PersistentNaturalEnterConvergenceError",
    "PersistentNaturalEnterPreflightV1",
    "adjudicate_existing_owner_go_reuse_read_only_v1",
    "assert_post_path_unreachable_from_runner_source_v1",
    "assert_productive_execution_forbidden_v1",
    "bootstrap_s8_lane_via_s7_compose_v1",
    "build_s8_occupied_lane_pairs_v1",
    "make_n1_occupied_lane_s5_runner_v1",
    "resolve_live_29p_injected_for_productive_s5_cycle_v1",
    "preflight_current_productive_persistent_natural_enter_v1",
    "persisted_cursor_venue_native_id_v1",
    "reconcile_selection_rotation_with_persisted_cursor_v1",
    "read_sidestate_continuity_snapshot_v1",
    "RECONCILIATION_NO_PERSISTED_CURSOR",
    "RECONCILIATION_SAME_INSTRUMENT_CONTINUATION",
    "RECONCILIATION_SELECTION_ROTATION_FRESH_LANE",
    "SelectionRotationCursorReconciliationV1",
    "run_offline_persistent_natural_enter_convergence_v1",
    "run_policy_governed_persistent_natural_enter_live_c1_continuous_run_v1",
]
