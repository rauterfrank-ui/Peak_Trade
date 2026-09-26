"""REST/WS reconciliation and restart trust boundary."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from src.ops.okx_eea_private_account_state_runtime_v1.constants_v1 import (
    REST_WS_DISAGREEMENT,
    SAFE_ADOPT_EXCHANGE_TRUTH,
    QUALITY_CURRENT,
    QUALITY_RECONCILIATION_REQUIRED,
)
from src.ops.okx_eea_private_account_state_runtime_v1.rest_baseline_v1 import RestBaselineSnapshotV1
from src.ops.okx_eea_private_account_state_runtime_v1.state_contracts_v1 import (
    OrderSnapshotV1,
    PositionStateV1,
    PrivateStateQualityV1,
    ReconciliationSnapshotV1,
)
from src.ops.okx_eea_private_account_state_runtime_v1.quality_v1 import (
    restored_state_quality_before_reconcile_v1,
)


class ReconciliationError(RuntimeError):
    pass


@dataclass(frozen=True)
class ReconciliationResultV1:
    snapshot: ReconciliationSnapshotV1
    trusted: bool


def compare_rest_ws_positions_v1(
    rest_positions: Sequence[PositionStateV1],
    ws_positions: Sequence[Mapping[str, str]],
) -> bool:
    rest_map = {p.inst_id: p.pos for p in rest_positions}
    for row in ws_positions:
        inst = str(row.get("instId") or "")
        if not inst:
            continue
        ws_pos = str(row.get("pos") or "0")
        if inst in rest_map and rest_map[inst] != ws_pos:
            return False
    return True


def compare_rest_ws_orders_v1(
    rest_orders: Sequence[OrderSnapshotV1],
    ws_orders: Sequence[Mapping[str, str]],
) -> bool:
    rest_map = {(o.ord_id or "", o.cl_ord_id or ""): o.state for o in rest_orders}
    for row in ws_orders:
        key = (str(row.get("ordId") or ""), str(row.get("clOrdId") or ""))
        if key in rest_map and rest_map[key] != str(row.get("state") or ""):
            return False
    return True


def reconcile_rest_baseline_v1(
    *,
    reconciliation_id: str,
    rest_baseline: RestBaselineSnapshotV1,
    ws_positions: Sequence[Mapping[str, str]] | None = None,
    ws_orders: Sequence[Mapping[str, str]] | None = None,
    restored_from_durable: bool = False,
) -> ReconciliationResultV1:
    notes: list[str] = []
    if restored_from_durable:
        notes.append("RESTORED_STATE_NOT_TRUSTED_UNTIL_BASELINE")
    disagreement = False
    if ws_positions is not None and not compare_rest_ws_positions_v1(
        rest_baseline.positions, ws_positions
    ):
        disagreement = True
        notes.append("REST_WS_POSITION_DISAGREEMENT")
    if ws_orders is not None and not compare_rest_ws_orders_v1(rest_baseline.orders, ws_orders):
        disagreement = True
        notes.append("REST_WS_ORDER_DISAGREEMENT")

    if disagreement:
        if SAFE_ADOPT_EXCHANGE_TRUTH:
            raise ReconciliationError("SAFE_ADOPT_NOT_GOVERNED")
        quality = PrivateStateQualityV1(
            state=QUALITY_RECONCILIATION_REQUIRED,
            reconciliation_required=True,
            stale_reason=REST_WS_DISAGREEMENT,
        )
        trusted = False
    elif restored_from_durable:
        quality = PrivateStateQualityV1(
            state=restored_state_quality_before_reconcile_v1(),
            reconciliation_required=True,
        )
        trusted = False
    else:
        quality = PrivateStateQualityV1(state=QUALITY_CURRENT, reconciliation_required=False)
        trusted = True

    snap = ReconciliationSnapshotV1(
        reconciliation_id=reconciliation_id,
        rest_ws_disagreement=REST_WS_DISAGREEMENT if disagreement else "NONE",
        safe_adopt_exchange_truth=SAFE_ADOPT_EXCHANGE_TRUTH,
        trusted_boundary_established=trusted,
        notes=tuple(notes),
        quality=quality,
    )
    return ReconciliationResultV1(snapshot=snap, trusted=trusted)
