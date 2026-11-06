"""Offline source adapter: applied simulated fills to the existing Exit owner.

Uses the original accounting engine to verify lineage/weighted entry. This is
simulated accounting provenance, never authentication of a venue position.
"""

from dataclasses import asdict, replace
from decimal import Decimal
import json
import math
import os
from pathlib import Path

from src.ops.exit_policy_producer_binding_v1.models_v1 import canonical_digest_v1
from src.ops.exit_policy_producer_binding_v1.position_episode_binding_v1 import (
    open_position_episode_binding_v1,
)
from src.ops.productive_futures_accounting_runtime_binding_v1.accounting_engine_v1 import (
    ProductiveFuturesAccountingSessionV1,
)
from src.ops.productive_futures_accounting_runtime_binding_v1.models_v1 import SimulatedFillInputV1

SCHEMA = "simulated_accounting_entry_source.v1"
FLAT_SCHEMA = "simulated_accounting_flat_source.v1"


def bind_simulated_accounting_episode_identity_v1(*, identity, opening_fill):
    """Deterministic episode key for this exact simulated opening, not a position ID."""
    identity.validate_v1()
    material = asdict(identity)
    material.pop("episode_id")
    material["opening_fill_digest"] = opening_fill.digest()
    return replace(identity, episode_id="simulated-accounting:" + canonical_digest_v1(material))


def _verify(*, identity, session, fills, closed=False):
    identity.validate_v1()
    if identity.account_scope.execution_environment != "INTERNAL_SIMULATED_EXECUTION":
        raise ValueError("SIMULATED_ENTRY_SOURCE_MODE_FORBIDDEN")
    if not isinstance(session, ProductiveFuturesAccountingSessionV1):
        raise ValueError("SIMULATED_ENTRY_ACCOUNTING_OWNER_REQUIRED")
    # Freeze through the owner's own strict checkpoint loader; never mutate caller state.
    checkpoint = session.to_durable_dict()
    frozen = ProductiveFuturesAccountingSessionV1.from_durable_dict(checkpoint)
    fills = tuple(fills)
    if frozen.contract.symbol != identity.venue_native_id:
        raise ValueError("SIMULATED_ENTRY_NATIVE_ID_MISMATCH")
    if frozen.funding_events or frozen.funding_pnl != 0:
        raise ValueError("SIMULATED_ENTRY_FUNDING_REPLAY_NOT_SUPPORTED")
    if not fills or any(not isinstance(f, SimulatedFillInputV1) for f in fills):
        raise ValueError("SIMULATED_ENTRY_FILL_INPUTS_REQUIRED")
    if [f.fill_id for f in fills] != frozen.fill_order:
        raise ValueError("SIMULATED_ENTRY_COMPLETE_FILL_ORDER_REQUIRED")
    replay = ProductiveFuturesAccountingSessionV1(
        contract=frozen.contract,
        initial_equity=frozen.initial_equity,
        writer_identity=frozen.writer_identity,
    )
    opening = None
    closed_opening = None
    closing_fill = None
    for fill in fills:
        time = fill.event_time_unix
        if time is not None and (
            type(time) not in (int, float) or not math.isfinite(time) or time <= 0
        ):
            raise ValueError("SIMULATED_ENTRY_INVALID_FILL_TIME")
        result = replay.apply_fill(fill)
        original = frozen.applied_fill_results[fill.fill_id]
        if (
            fill.digest() != original.fill_input_digest
            or result.accounting_output_digest != original.accounting_output_digest
            or result.action_code != original.action_code
        ):
            raise ValueError("SIMULATED_ENTRY_APPLIED_FILL_LINEAGE_MISMATCH")
        if result.action_code in {"LONG_OPEN", "SHORT_OPEN"}:
            opening = fill
        elif result.action_code in {"LONG_CLOSE", "SHORT_CLOSE"}:
            closed_opening = opening
            closing_fill = fill
            opening = None
    if frozen.last_mark is not None:
        replay.mark_to_market(frozen.last_mark)
    if (
        replay.portfolio_state().to_dict() != frozen.portfolio_state().to_dict()
        or replay.risk_state().to_dict() != frozen.risk_state().to_dict()
        or replay.last_fill_time != frozen.last_fill_time
    ):
        raise ValueError("SIMULATED_ENTRY_ACCOUNTING_REPLAY_MISMATCH")
    if closed:
        if replay.position is not None or closed_opening is None or closing_fill is None:
            raise ValueError("SIMULATED_ENTRY_CLOSED_EPISODE_REQUIRED")
        opening = closed_opening
    elif (
        opening is None
        or replay.position is None
        or replay.position.side.value.lower() != identity.position_side
    ):
        raise ValueError("SIMULATED_ENTRY_OPEN_EPISODE_REQUIRED")
    if identity != bind_simulated_accounting_episode_identity_v1(
        identity=identity, opening_fill=opening
    ):
        raise ValueError("SIMULATED_ENTRY_EPISODE_ID_MISMATCH")
    payload = {
        "schema": FLAT_SCHEMA if closed else SCHEMA,
        "identity": asdict(identity),
        "accounting_checkpoint": checkpoint,
        "fills": [f.to_dict() for f in fills],
    }
    if closed:
        return payload, {
            "entry_event_time": opening.event_time_unix,
            "close_event_time": closing_fill.event_time_unix,
        }
    anchors = {
        "entry_price": float(replay.position.entry_price),
        "entry_event_time": opening.event_time_unix,
        "entry_trading_epoch": None,
        "entry_price_basis": "CONFIRMED_POSITION_ENTRY_PRICE",
    }
    if not math.isfinite(anchors["entry_price"]) or anchors["entry_price"] <= 0:
        raise ValueError("SIMULATED_ENTRY_PRICE_NOT_REPRESENTABLE")
    return payload, anchors


def _load_source(path, identity, *, include_payload=False, closed=False):
    record = json.loads(Path(path).read_text(encoding="utf-8"))
    if (
        not isinstance(record, dict)
        or set(record) != {"payload", "content_digest"}
        or not isinstance(record["payload"], dict)
        or record["content_digest"] != canonical_digest_v1(record["payload"])
    ):
        raise ValueError("SIMULATED_ENTRY_SOURCE_DIGEST_MISMATCH")
    payload = record["payload"]
    if (
        set(payload) != {"schema", "identity", "accounting_checkpoint", "fills"}
        or payload["schema"] != (FLAT_SCHEMA if closed else SCHEMA)
        or payload["identity"] != asdict(identity)
    ):
        raise ValueError("SIMULATED_ENTRY_SOURCE_IDENTITY_MISMATCH")
    session = ProductiveFuturesAccountingSessionV1.from_durable_dict(
        payload["accounting_checkpoint"]
    )
    fills = []
    for row in payload["fills"]:
        if not isinstance(row, dict) or set(row) != set(SimulatedFillInputV1.__dataclass_fields__):
            raise ValueError("SIMULATED_ENTRY_FILL_SCHEMA_MISMATCH")
        if type(row["reduce_only"]) is not bool:
            raise ValueError("SIMULATED_ENTRY_FILL_BOOLEAN_REQUIRED")
        fills.append(
            SimulatedFillInputV1(
                **{
                    k: Decimal(v)
                    if k
                    in {"quantity", "mark_price", "fill_price", "fee", "slippage_cost", "notional"}
                    else v
                    for k, v in row.items()
                }
            )
        )
    _verified, anchors = _verify(identity=identity, session=session, fills=fills, closed=closed)
    if include_payload:
        return record["content_digest"], anchors, payload
    return record["content_digest"], anchors


def _ref(path, digest):
    return f"{SCHEMA}:{digest}:{Path(path).resolve()}"


def _retain_payload_v1(*, payload, source_archive_root):
    root = Path(source_archive_root)
    if not root.is_absolute():
        raise ValueError("SIMULATED_ENTRY_EXPLICIT_ARCHIVE_ROOT_REQUIRED")
    digest = canonical_digest_v1(payload)
    path = root / (digest + ".json")
    body = (
        json.dumps({"payload": payload, "content_digest": digest}, sort_keys=True, allow_nan=False)
        + "\n"
    )
    root.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8") as stream:
            stream.write(body)
            stream.flush()
            os.fsync(stream.fileno())
    except FileExistsError:
        if path.read_text(encoding="utf-8") != body:
            raise ValueError("SIMULATED_ENTRY_SOURCE_ARCHIVE_CONFLICT")
    retained = json.loads(path.read_text())
    if retained != {"payload": payload, "content_digest": digest}:
        raise ValueError("SIMULATED_ENTRY_SOURCE_READBACK_MISMATCH")
    return path, digest


def _archive_verified_source_v1(*, payload, anchors, identity, source_archive_root, closed=False):
    path, digest = _retain_payload_v1(payload=payload, source_archive_root=source_archive_root)
    loaded_digest, loaded_anchors = _load_source(path, identity, closed=closed)
    if loaded_digest != digest or loaded_anchors != anchors:
        raise ValueError("SIMULATED_ENTRY_SOURCE_READBACK_MISMATCH")
    return path, digest


def create_position_episode_from_simulated_accounting_v1(
    *,
    identity,
    session,
    fills,
    source_archive_root,
    state_root,
    repository_sha,
    config_digest,
    writer_session_id,
):
    payload, anchors = _verify(identity=identity, session=session, fills=fills)
    path, digest = _archive_verified_source_v1(
        payload=payload,
        anchors=anchors,
        identity=identity,
        source_archive_root=source_archive_root,
    )
    return open_position_episode_binding_v1(
        identity=identity,
        state_root=state_root,
        mode="create",
        repository_sha=repository_sha,
        config_digest=config_digest,
        writer_session_id=writer_session_id,
        entry_source_ref=_ref(path, digest),
        **anchors,
    )


def recover_position_episode_from_simulated_accounting_v1(
    *,
    identity,
    source_path,
    state_root,
    repository_sha,
    config_digest,
    writer_session_id,
):
    identity.validate_v1()
    path = Path(source_path)
    if not path.is_absolute():
        raise ValueError("SIMULATED_ENTRY_EXPLICIT_SOURCE_PATH_REQUIRED")
    digest, anchors = _load_source(path, identity)
    context = open_position_episode_binding_v1(
        identity=identity,
        state_root=state_root,
        mode="recover",
        repository_sha=repository_sha,
        config_digest=config_digest,
        writer_session_id=writer_session_id,
        entry_source_ref=_ref(path, digest),
        entry_price_basis=anchors["entry_price_basis"],
    )
    if context.binding.simulated_accounting_progress is not None:
        from src.ops.exit_policy_producer_binding_v1.simulated_accounting_progress_v1 import (
            verify_simulated_accounting_progress_v1,
        )

        verify_simulated_accounting_progress_v1(context)
    elif any(
        getattr(context.binding, k) != anchors[k]
        for k in ("entry_price", "entry_event_time", "entry_trading_epoch")
    ):
        raise ValueError("SIMULATED_ENTRY_PERSISTED_ANCHOR_MISMATCH")
    return context
