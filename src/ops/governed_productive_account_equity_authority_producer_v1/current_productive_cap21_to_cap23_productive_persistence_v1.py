"""Shared CURRENT_PRODUCTIVE Cap-2.1→2.3 persistence (no Cap-2.4, no network).

Single reuse surface for EEA inventory, fresh Cap-23/24 slices, and the
Cap-24 selection-state canonical writer. No ranking/selection logic here —
only orchestrates existing producers in order.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from src.ops.current_productive_eea_universe_inventory_acquisition_v1.acquire_v1 import (
    EeaUniverseAcquisitionResultV1,
)
from src.ops.current_productive_eea_universe_inventory_acquisition_v1.constants_v1 import (
    SOURCE_KIND,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    CANARY_DEFAULT_INSTRUMENT_ID,
)
from src.ops.governed_futures_universe_producer_v1.producer_v1 import (
    run_governed_futures_universe_producer_v1,
)
from src.ops.productive_futures_ranking_producer_v1.producer_v1 import (
    run_productive_futures_ranking_producer_v1,
)
from src.ops.single_selected_future_policy_v1.constants_v1 import (
    SELECTION_FILENAME,
    STATE_SELECTED_ACTIVE,
)
from src.ops.single_selected_future_policy_v1.models_v1 import (
    SingleSelectedFutureSelectionV1,
)
from src.ops.single_selected_future_policy_v1.producer_v1 import (
    run_single_selected_future_policy_v1,
)


class CurrentProductiveCap21ToCap23PersistenceError(RuntimeError):
    """Fail-closed Cap-2.1→2.3 persistence violation."""


@dataclass(frozen=True)
class CurrentProductiveCap21ToCap23PersistResultV1:
    ok: bool
    status: str
    cap21_snapshot_id: str
    cap21_event_time: str
    cap21_universe_size: str
    cap22_ranking_id: str
    cap22_ranking_epoch: str
    cap23_selection_decision_id: str
    cap23_selected_instrument_id: str
    cap23_valid_from: str
    cap23_valid_until: str
    selection: SingleSelectedFutureSelectionV1 | None
    universe_state_root: Path
    ranking_state_root: Path
    selection_state_root: Path
    recon_state_root: Path


def eea_mark_price_payload_to_map_by_native_id_v1(
    payload: Mapping[str, Any],
) -> dict[str, str]:
    """Transform OKX EEA public mark-price payload → instId → markPx map."""

    out: dict[str, str] = {}
    data = payload.get("data")
    if not isinstance(data, list):
        return out
    for row in data:
        if not isinstance(row, Mapping):
            continue
        inst = str(row.get("instId") or "").strip()
        px = str(row.get("markPx") or "").strip()
        if inst and px:
            out[inst] = px
    return out


def build_cap24_mark_prices_sidecar_from_acquisition_v1(
    *,
    mark_price_payload: Mapping[str, Any],
    venue_native_id: str,
) -> dict[str, str]:
    """Derive handoff sidecar from EEA acquisition only (selected instId)."""

    native_id = str(venue_native_id or "").strip()
    if not native_id:
        raise CurrentProductiveCap21ToCap23PersistenceError(
            "CAP23_VENUE_NATIVE_ID_MISSING_FOR_MARK_SIDECAR"
        )
    marks = eea_mark_price_payload_to_map_by_native_id_v1(mark_price_payload)
    px = marks.get(native_id)
    if not px or not str(px).strip():
        raise CurrentProductiveCap21ToCap23PersistenceError(
            "MARK_PRICE_MISSING_FOR_SELECTED_VENUE_NATIVE_ID"
        )
    return {native_id: str(px)}


def run_cap21_to_cap23_persist_productive_v1(
    *,
    acquisition: EeaUniverseAcquisitionResultV1,
    store: Path,
    repository_sha: str,
    observed_unix: float,
    session_id_prefix: str,
) -> CurrentProductiveCap21ToCap23PersistResultV1:
    """Run Cap-2.1→2.3 producers into ``store/runtime_state/*`` (persisted)."""

    uni_root = store / "runtime_state" / "universe"
    rank_root = store / "runtime_state" / "ranking"
    sel_root = store / "runtime_state" / "selection"
    recon_root = store / "runtime_state" / "recon"
    for path in (uni_root, rank_root, sel_root, recon_root):
        path.mkdir(parents=True, exist_ok=True)
    empty_fields = {
        "cap21_snapshot_id": "",
        "cap21_event_time": "",
        "cap21_universe_size": "",
        "cap22_ranking_id": "",
        "cap22_ranking_epoch": "",
        "cap23_selection_decision_id": "",
        "cap23_selected_instrument_id": "",
        "cap23_valid_from": "",
        "cap23_valid_until": "",
    }

    def _result(*, ok: bool, status: str, selection: SingleSelectedFutureSelectionV1 | None):
        return CurrentProductiveCap21ToCap23PersistResultV1(
            ok=ok,
            status=status,
            selection=selection,
            universe_state_root=uni_root,
            ranking_state_root=rank_root,
            selection_state_root=sel_root,
            recon_state_root=recon_root,
            **empty_fields,
        )

    uni = run_governed_futures_universe_producer_v1(
        state_root=uni_root,
        source_payload=acquisition.instruments_payload,
        mark_price_payload=acquisition.mark_price_payload,
        repository_sha=repository_sha,
        producer_observed_at_unix=observed_unix,
        source_event_time=acquisition.source_event_time,
        source_kind=SOURCE_KIND,
        session_id=f"{session_id_prefix}-universe",
    )
    if uni.get("ok") is not True:
        return _result(ok=False, status="CAP21_CURRENT_UNIVERSE_FAIL_CLOSED", selection=None)
    uni_snap = uni.get("snapshot") or {}
    empty_fields["cap21_snapshot_id"] = str(uni_snap.get("snapshot_id") or "")
    empty_fields["cap21_event_time"] = str(uni_snap.get("generated_at_event_time") or "")
    empty_fields["cap21_universe_size"] = str(uni_snap.get("eligible_instrument_count") or "")

    ranking = run_productive_futures_ranking_producer_v1(
        state_root=rank_root,
        universe_state_root=uni_root,
        repository_sha=repository_sha,
        producer_observed_at_unix=observed_unix,
        session_id=f"{session_id_prefix}-ranking",
    )
    if ranking.get("ok") is not True:
        return _result(ok=False, status="CAP22_CURRENT_RANKING_FAIL_CLOSED", selection=None)
    rank_snap = ranking.get("snapshot") or {}
    empty_fields["cap22_ranking_id"] = str(rank_snap.get("ranking_snapshot_id") or "")
    empty_fields["cap22_ranking_epoch"] = str(rank_snap.get("event_time") or "")

    selection_run = run_single_selected_future_policy_v1(
        state_root=sel_root,
        ranking_state_root=rank_root,
        repository_sha=repository_sha,
        producer_observed_at_unix=observed_unix,
        session_id=f"{session_id_prefix}-selection",
        previous_selection=None,
        load_previous_from_state=False,
        open_position_instrument_id=None,
        dashboard_payload=None,
        allowlist_payload=None,
        manual_override_payload=None,
    )
    selection_path = sel_root / SELECTION_FILENAME
    selection = None
    if selection_path.is_file():
        selection = SingleSelectedFutureSelectionV1.from_dict(
            json.loads(selection_path.read_text(encoding="utf-8"))
        )
    if (
        selection_run.get("ok") is not True
        or selection is None
        or selection.state != STATE_SELECTED_ACTIVE
        or not str(selection.venue_native_id or "").strip()
    ):
        return _result(ok=False, status="CAP23_CURRENT_SELECTION_FAIL_CLOSED", selection=selection)
    if str(selection.venue_native_id) == CANARY_DEFAULT_INSTRUMENT_ID:
        raise CurrentProductiveCap21ToCap23PersistenceError("CANARY_INSTRUMENT_AUTHORITY_IMPORTED")
    empty_fields["cap23_selection_decision_id"] = selection.selection_id
    empty_fields["cap23_selected_instrument_id"] = str(selection.venue_native_id)
    empty_fields["cap23_valid_from"] = selection.valid_from
    empty_fields["cap23_valid_until"] = selection.valid_until
    return CurrentProductiveCap21ToCap23PersistResultV1(
        ok=True,
        status="PASS",
        selection=selection,
        universe_state_root=uni_root,
        ranking_state_root=rank_root,
        selection_state_root=sel_root,
        recon_state_root=recon_root,
        **empty_fields,
    )
