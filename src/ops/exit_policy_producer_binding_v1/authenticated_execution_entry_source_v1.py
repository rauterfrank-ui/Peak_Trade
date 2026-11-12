"""Open or recover the original exit-state episode from an owned venue entry."""

from decimal import Decimal, InvalidOperation
import math
from pathlib import Path
from urllib.parse import urlsplit

from src.ops.execution_reconciliation_proof_store_v1 import (
    AuthenticatedExecutionReconciliationSourceV1,
    read_authenticated_execution_reconciliation_source_v1,
)
from src.ops.exit_policy_producer_binding_v1.models_v1 import canonical_digest_v1
from src.ops.exit_policy_producer_binding_v1.position_episode_binding_v1 import (
    PositionEpisodeBindingV1,
    PositionEpisodeIdentityV1,
    PositionEpisodeScopeV1,
    open_position_episode_binding_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_v1 import (
    EvidenceLayer,
    OUTCOME_CONFIRMED_FILLED,
    OUTCOME_CONFIRMED_PARTIALLY_FILLED,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1


def _venue_number(value: object) -> Decimal:
    try:
        number = Decimal(value) if isinstance(value, str) else Decimal("NaN")
    except InvalidOperation as exc:
        raise ValueError("VENUE_ENTRY_NUMBER_INVALID") from exc
    if not number.is_finite():
        raise ValueError("VENUE_ENTRY_NUMBER_INVALID")
    return number


def _venue_positive_int(value: object) -> int:
    if not isinstance(value, str) or not value.isascii() or not value.isdecimal():
        raise ValueError("VENUE_ENTRY_INTEGER_INVALID")
    number = int(value)
    if number <= 0:
        raise ValueError("VENUE_ENTRY_INTEGER_INVALID")
    return number


def _entry_anchors_v1(
    source: AuthenticatedExecutionReconciliationSourceV1, *, side: str
) -> tuple[Decimal, int, str]:
    result = source.reconciliation
    decision = result["decision"]
    if (
        result["matched"] is not True
        or result["reservation_released"] is not False
        or decision["reconciliation_complete"] is not True
        or decision["exposure_retained"] is not True
        or decision["outcome"] not in {OUTCOME_CONFIRMED_FILLED, OUTCOME_CONFIRMED_PARTIALLY_FILLED}
        or not decision["venue_ord_id"]
    ):
        raise ValueError("VENUE_ENTRY_TERMINAL_FILL_UNPROVEN")

    snapshot = source.snapshot
    pending = snapshot.pending_orders_observation or {}
    positions = snapshot.positions_observation or {}
    position_response = positions.get("response") or {}
    rows = position_response.get("data")
    if (
        pending.get("freshness_proven") is not True
        or (pending.get("response") or {}).get("code") != "0"
        or (pending.get("response") or {}).get("data") != []
        or positions.get("freshness_proven") is not True
        or position_response.get("code") != "0"
        or not isinstance(rows, list)
        or len(rows) != 1
    ):
        raise ValueError("VENUE_ENTRY_POSITION_READBACK_UNPROVEN")

    identity = source.identity
    quantity = _venue_number(decision["cumulative_filled_qty"])
    position = rows[0]
    order_side = "buy" if side == "long" else "sell"
    if (
        quantity <= 0
        or position.get("posSide") != "net"
        or position.get("instId") != identity.native_id
        or _venue_number(position.get("pos")) != (quantity if side == "long" else -quantity)
    ):
        raise ValueError("VENUE_ENTRY_POSITION_READBACK_UNPROVEN")

    fills: dict[int, tuple[int, Decimal, Decimal]] = {}
    for item in snapshot.evidence_items:
        if item.layer is not EvidenceLayer.EXCHANGE_FILL_STATE:
            continue
        row = item.payload
        if (
            row.get("instId") != identity.native_id
            or row.get("clOrdId") != identity.clordid
            or row.get("ordId") != decision["venue_ord_id"]
            or row.get("side") != order_side
            or row.get("posSide") != "net"
        ):
            raise ValueError("VENUE_ENTRY_FILL_IDENTITY_UNPROVEN")
        trade_id = _venue_positive_int(row.get("tradeId"))
        fill = (
            _venue_positive_int(row.get("fillTime")),
            _venue_number(row.get("fillSz")),
            _venue_number(row.get("fillPx")),
        )
        if fill[1] <= 0 or fill[2] <= 0 or fills.setdefault(trade_id, fill) != fill:
            raise ValueError("VENUE_ENTRY_FILL_UNPROVEN")

    position_time = _venue_positive_int(position.get("uTime"))
    position_get = next(
        read
        for read in source.proof.gets
        if urlsplit(read.endpoint).path == "/api/v5/account/positions"
    )
    if (
        not fills
        or sum(fill[1] for fill in fills.values()) != quantity
        or _venue_positive_int(position.get("tradeId")) != max(fills)
        or max(fill[0] for fill in fills.values()) > position_time
        or position_time > int(position_get.acquired_at.timestamp() * 1000)
    ):
        raise ValueError("VENUE_ENTRY_FILL_POSITION_LINK_UNPROVEN")
    price = _venue_number(position.get("avgPx"))
    if price <= 0:
        raise ValueError("VENUE_ENTRY_PRICE_UNPROVEN")
    anchors_digest = canonical_digest_v1(
        {
            "order": decision["venue_ord_id"],
            "entry_price": str(price.normalize()),
            "fills": [
                [trade_id, time_ms, str(qty.normalize()), str(fill_price.normalize())]
                for trade_id, (time_ms, qty, fill_price) in sorted(fills.items())
            ],
        }
    )
    return price, min(fill[0] for fill in fills.values()), anchors_digest


def open_position_episode_from_authenticated_execution_v1(
    *,
    bound: BoundInstrumentV1,
    lane_id: str,
    account_scope: PositionEpisodeScopeV1,
    proof_root: Path,
    budget_owner_root: Path,
    source_session_id: str,
    reservation_id: str,
    revision_ref: tuple[int, str],
    state_root: Path,
    mode: str,
    repository_sha: str,
    config_digest: str,
    writer_session_id: str,
) -> PositionEpisodeBindingV1:
    """Bind historical entry anchors. Current position admission is a separate read."""
    account_scope.validate_v1()
    source = read_authenticated_execution_reconciliation_source_v1(
        root=proof_root,
        budget_owner_root=budget_owner_root,
        account=account_scope.account_identity,
        session_id=source_session_id,
        reservation_id=reservation_id,
        revision_ref=revision_ref,
    )
    attempt = source.identity
    side = {"LONG": "long", "SHORT": "short"}.get(attempt.selected_side.upper())
    if (
        side is None
        or attempt.decision_outcome.upper() != f"ENTER_{side.upper()}"
        or attempt.execution_environment != account_scope.execution_environment
        or (attempt.slot_id, attempt.instrument_id, attempt.native_id)
        != (lane_id, bound.instrument_id, bound.venue_native_id)
        or source.lane_binding.get("bound") != bound.to_dict()
    ):
        raise ValueError("VENUE_ENTRY_BOUND_SCOPE_MISMATCH")

    price, fill_time_ms, anchors_digest = _entry_anchors_v1(source, side=side)
    episode = PositionEpisodeIdentityV1(
        lane_id=lane_id,
        instrument_id=bound.instrument_id,
        venue_native_id=bound.venue_native_id,
        episode_id=attempt.identity_digest(),
        position_side=side,
        account_scope=account_scope,
    )
    source_ref = "authenticated_execution_entry.v1:" + canonical_digest_v1(
        {"attempt": episode.episode_id, "anchors": anchors_digest}
    )
    legacy_source_ref = "authenticated_execution_entry.v1:" + canonical_digest_v1(
        {
            "attempt": episode.episode_id,
            "revision": list(revision_ref),
            "snapshot": source.proof.snapshot_digest,
        }
    )
    entry_price = float(price)
    entry_event_time = fill_time_ms / 1000
    if not math.isfinite(entry_price) or entry_price <= 0:
        raise ValueError("VENUE_ENTRY_PRICE_UNPROVEN")
    binding = open_position_episode_binding_v1(
        identity=episode,
        state_root=state_root,
        mode=mode,
        repository_sha=repository_sha,
        config_digest=config_digest,
        writer_session_id=writer_session_id,
        entry_source_ref=source_ref if mode == "create" else None,
        entry_price_basis="CONFIRMED_POSITION_ENTRY_PRICE",
        entry_price=entry_price if mode == "create" else None,
        entry_event_time=entry_event_time if mode == "create" else None,
    )
    if binding.entry_source_ref not in {source_ref, legacy_source_ref}:
        raise ValueError("VENUE_ENTRY_SOURCE_READBACK_MISMATCH")
    if (binding.binding.entry_price, binding.binding.entry_event_time) != (
        entry_price,
        entry_event_time,
    ):
        raise ValueError("VENUE_ENTRY_ANCHOR_READBACK_MISMATCH")
    return binding
