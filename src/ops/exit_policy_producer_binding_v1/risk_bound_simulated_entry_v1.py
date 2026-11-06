"""Attribute an already-applied explicit simulated fill to its original entry.

No fill application, order/permit creation or new numerical position owner.
Legacy episode ports remain separate and are not certified by this adapter.
"""

from dataclasses import asdict
from decimal import Decimal
import json
from pathlib import Path

from src.ops.portfolio_capital_reservation_budget_v1.durable_store_v1 import digest
from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
    assert_envelope_unmodified_v1,
)
from .simulated_accounting_entry_source_v1 import (
    _verify,
    _archive_verified_source_v1,
    _ref,
    create_position_episode_from_simulated_accounting_v1,
    recover_position_episode_from_simulated_accounting_v1,
)


def _entry_binding(*, owner, reservation_id, envelope, identity, session, fills):
    assert_envelope_unmodified_v1(envelope)
    identity.validate_v1()
    binding = owner.reservation_risk_binding_v1(reservation_id)
    request = binding.request
    record = owner.lookup_v1(
        slot_id=request.slot_id,
        decision_id=request.decision_id,
        cycle_id=request.cycle_id,
        observation_id=json.loads(binding.owner_snapshot_json)["state"]["observation_id"],
    )
    if (
        record is None
        or not record.counts_against_budget
        or str(record.reservation_id) != str(reservation_id)
    ):
        raise ValueError("SIMULATED_ENTRY_ORIGINAL_ACTIVE_RESERVATION_REQUIRED")
    link = owner.execution_links_v1().get(str(reservation_id))
    if link is None or link["envelope"] != envelope.to_runtime_json_v1():
        raise ValueError("SIMULATED_ENTRY_ORIGINAL_EXECUTION_PLAN_REQUIRED")
    binding.validate_envelope_v1(envelope)
    if identity.account_scope.execution_environment != "INTERNAL_SIMULATED_EXECUTION" or (
        identity.account_scope.account_identity,
        identity.lane_id,
        identity.instrument_id,
        identity.venue_native_id,
        identity.position_side,
    ) != (
        request.data.account,
        request.slot_id,
        request.canonical_id,
        request.native_id,
        request.side.lower(),
    ):
        raise ValueError("SIMULATED_ENTRY_RISK_EPISODE_IDENTITY_MISMATCH")
    if len(fills) != 1:
        raise ValueError("SIMULATED_ENTRY_FULL_OPENING_FILL_ONLY")
    fill = fills[0]
    item = next(i for i in request.data.instruments if i.canonical_id == request.canonical_id)
    sizing_metadata = owner.risk_snapshot_v1()["state"]["sizing_bindings"][str(reservation_id)][
        "applied_input"
    ]["instrument"]
    if (
        fill.fill_id != "offline-envelope:" + envelope.envelope_digest
        or fill.instrument_id != request.native_id
        or fill.side.upper() != envelope.side.upper()
        or fill.quantity != Decimal(envelope.quantity)
        or fill.reduce_only is not False
        or fill.event_time_unix is None
        or fill.event_time_unix * 1000 < request.data.as_of_ms
        or session.contract.symbol != request.native_id
        or session.contract.contract_size != item.contract_multiplier
        or session.contract.quote_currency != item.quote_currency
        or sizing_metadata["tick_size"] is None
        or session.contract.tick_size != Decimal(sizing_metadata["tick_size"])
        or session.contract.min_qty != Decimal(sizing_metadata["minimum_quantity"])
    ):
        raise ValueError("SIMULATED_ENTRY_FILL_ENVELOPE_OR_CONTRACT_MISMATCH")
    payload, anchors = _verify(identity=identity, session=session, fills=fills)
    return (
        {
            "risk_binding_digest": digest(binding.to_dict_v1()),
            "reservation_id": str(reservation_id),
            "envelope": envelope.to_runtime_json_v1(),
            "opening_fill_digest": fill.digest(),
            "identity": asdict(identity),
            "declaration": "EXPLICIT_INTERNAL_SIMULATION_NO_VENUE_FILL_CLAIM",
        },
        payload,
        anchors,
    )


def create_risk_bound_simulated_episode_v1(
    *,
    owner,
    reservation_id,
    envelope,
    identity,
    session,
    fills,
    source_archive_root,
    state_root,
    repository_sha,
    config_digest,
    writer_session_id,
):
    from src.ops.bounded_peaktrade_system_composition_v1.manifest_v1 import (
        canonical_absolute_path_v1,
    )

    canonical_absolute_path_v1(str(source_archive_root))
    canonical_absolute_path_v1(str(state_root))
    evidence, payload, anchors = _entry_binding(
        owner=owner,
        reservation_id=reservation_id,
        envelope=envelope,
        identity=identity,
        session=session,
        fills=fills,
    )
    path, checksum = _archive_verified_source_v1(
        payload=payload, anchors=anchors, identity=identity, source_archive_root=source_archive_root
    )
    body = json.loads(
        json.dumps(
            {
                "schema": "risk_bound_simulated_episode_entry.v1",
                **evidence,
                "source_ref": _ref(path, checksum),
                "exit_state_root": str(Path(state_root).resolve()),
                "repository_sha": repository_sha,
                "config_digest": config_digest,
            },
            allow_nan=False,
        )
    )
    receipt = {**body, "digest": digest(body)}
    receipt_path = Path(source_archive_root) / ("risk_entry_receipt_" + receipt["digest"] + ".json")
    from src.ops.bounded_peaktrade_system_composition_v1.session_v1 import _write

    if receipt_path.exists():
        if json.loads(receipt_path.read_text()) != receipt:
            raise ValueError("SIMULATED_ENTRY_BINDING_RECEIPT_CONFLICT")
    else:
        _write(receipt_path, receipt)
    context = create_position_episode_from_simulated_accounting_v1(
        identity=identity,
        session=session,
        fills=fills,
        source_archive_root=source_archive_root,
        state_root=state_root,
        repository_sha=repository_sha,
        config_digest=config_digest,
        writer_session_id=writer_session_id,
    )
    if context.entry_source_ref != receipt["source_ref"]:
        raise ValueError("SIMULATED_ENTRY_SOURCE_BINDING_READBACK_MISMATCH")
    return context, receipt_path


def recover_risk_bound_simulated_episode_v1(
    *, receipt_path, owner, envelope, identity, repository_sha, config_digest, writer_session_id
):
    from src.ops.productive_futures_accounting_runtime_binding_v1.accounting_engine_v1 import (
        ProductiveFuturesAccountingSessionV1,
    )
    from src.ops.productive_futures_accounting_runtime_binding_v1.models_v1 import (
        SimulatedFillInputV1,
    )
    from .simulated_accounting_entry_source_v1 import _load_source

    receipt = json.loads(Path(receipt_path).read_text())
    if not isinstance(receipt, dict) or set(receipt) != {
        "schema",
        "risk_binding_digest",
        "reservation_id",
        "envelope",
        "opening_fill_digest",
        "identity",
        "declaration",
        "source_ref",
        "exit_state_root",
        "repository_sha",
        "config_digest",
        "digest",
    }:
        raise ValueError("SIMULATED_ENTRY_BINDING_RECEIPT_INVALID")
    body = {k: v for k, v in receipt.items() if k != "digest"}
    if (
        receipt.get("digest") != digest(body)
        or receipt.get("schema") != "risk_bound_simulated_episode_entry.v1"
        or receipt.get("repository_sha") != repository_sha
        or receipt.get("config_digest") != config_digest
    ):
        raise ValueError("SIMULATED_ENTRY_BINDING_RECEIPT_INVALID")
    parts = receipt["source_ref"].split(":", 2)
    from .simulated_accounting_entry_source_v1 import SCHEMA
    from src.ops.bounded_peaktrade_system_composition_v1.manifest_v1 import (
        canonical_absolute_path_v1,
    )

    if len(parts) != 3 or parts[0] != SCHEMA:
        raise ValueError("SIMULATED_ENTRY_SOURCE_DIGEST_MISMATCH")
    canonical_absolute_path_v1(parts[2])
    canonical_absolute_path_v1(receipt["exit_state_root"])
    checksum, _, payload = _load_source(Path(parts[2]), identity, include_payload=True)
    if checksum != parts[1] or _ref(Path(parts[2]), checksum) != receipt["source_ref"]:
        raise ValueError("SIMULATED_ENTRY_SOURCE_DIGEST_MISMATCH")
    session = ProductiveFuturesAccountingSessionV1.from_durable_dict(
        payload["accounting_checkpoint"]
    )
    numeric = {"quantity", "mark_price", "fill_price", "fee", "slippage_cost", "notional"}
    fills = tuple(
        SimulatedFillInputV1(**{k: Decimal(v) if k in numeric else v for k, v in row.items()})
        for row in payload["fills"]
    )
    expected, _, _ = _entry_binding(
        owner=owner,
        reservation_id=receipt["reservation_id"],
        envelope=envelope,
        identity=identity,
        session=session,
        fills=fills,
    )
    if any(receipt.get(k) != json.loads(json.dumps(v)) for k, v in expected.items()):
        raise ValueError("SIMULATED_ENTRY_BOUND_ORIGINALS_CHANGED")
    return recover_position_episode_from_simulated_accounting_v1(
        identity=identity,
        source_path=Path(parts[2]),
        state_root=Path(receipt["exit_state_root"]),
        repository_sha=repository_sha,
        config_digest=config_digest,
        writer_session_id=writer_session_id,
    )
