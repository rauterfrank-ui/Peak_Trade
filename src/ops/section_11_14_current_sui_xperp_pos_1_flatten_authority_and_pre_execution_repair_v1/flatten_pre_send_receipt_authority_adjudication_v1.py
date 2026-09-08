"""§11.14 flatten pre-send receipt authority adjudication.

Offline census only. Does not mint an attachable receipt. Does not GET.
Does not HMAC. Does not reprice. Does not consume. Does not HTTP POST.
Does not invent an Owner receipt-issuance schema. Does not close open
gate-order points.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.authenticated_productive_transport_v1 import (
    AuthenticatedGatedProductiveFlattenTransportV1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.evidence_v1 import (
    verify_manifest_v1,
    write_json_v1,
    write_manifest_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.live_credential_ephemeral_v1 import (
    assert_no_plaintext_in_payload_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_limit_price_contract_v1 import (
    FlattenPriceInputV1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_pre_send_gate_v1 import (
    FlattenPreSendGateInputV1,
    FlattenPreSendGateReceiptV1,
    evaluate_flatten_pre_send_gate_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_productive_transport_v1 import (
    LiveCanaryFlattenProductiveTransportError,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.constants_v1 import (
    BOUND_ORIGIN_MAIN_SHA,
    PRE_SUBMIT_FRESH_GET_REQUIRED,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.productive_wire_send_orchestrator_v1 import (
    OPEN_GATE_ORDER_POINTS,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    CANARY_AUTHORIZED,
    LIVE_ARMED,
    LIVE_ENABLED,
    POST_ALLOWED,
)

THIS_SLICE = "11.14.FLATTEN_PRE_SEND_RECEIPT_AUTHORITY_AND_BINDING"
PREDECESSOR_SLICE = "11.14.PRODUCTIVE_INNER_SEND_FAIL_CLOSED_RECEIPT_BOUNDARY"
OWNER_GO = "OWNER_FLATTEN_PRE_SEND_RECEIPT_GO"
RECEIPT_TYPE = "FlattenPreSendGateReceiptV1"
RECEIPT_PRODUCER = "evaluate_flatten_pre_send_gate_v1"
RECEIPT_CONSUMER = "AuthenticatedGatedProductiveFlattenTransportV1.send"
RECEIPT_ATTACH_SEAM = "AuthenticatedGatedProductiveFlattenTransportV1.attach_pre_send_receipt"
RECEIPT_AUTHORITY_SCHEMA_STATUS = "DEFINED"
RECEIPT_AUTHORITY_OR_GO_NAME = "OWNER_FLATTEN_PRE_SEND_RECEIPT_GO"
RECEIPT_OWNER_ISSUANCE_SCHEMA_INVENTED = False
RECEIPT_MINTED = False
RECEIPT_BOUND = False
RECEIPT_ATTACHED = False
RECEIPT_WORK_BLOCKED_BY_OPEN_GATE_ORDER = True
OPEN_GATE_ORDER_BLOCKER = "FRESH_PRE_SUBMIT_GET"
OPEN_GATE_ORDER_BLOCKER_SECONDARY = "ENVELOPE_REPRICE_OR_FRESHNESS_AT_SEND"
CURRENT_CANONICAL_BOUNDARY = "RECEIPT_MISSING"
EARLIEST_UNRESOLVED_RUNTIME_GATE = "FLATTEN_PRE_SEND_GATE_RECEIPT"
NEXT_OWNER_AUTHORITY_REQUIRED = "FRESH_PRE_SUBMIT_GET"
FIRST_DENY_AFTER_RECEIPT = "NOT_REACHED"
EXPECTED_ORIGIN_MAIN_SHA = "376fe84088dae800fdc1ac25436162fe25e1620a"
RECEIPT_BIND_FIELDS: tuple[str, ...] = (
    "allowed",
    "approved_request_identity",
    "request_body",
    "approved_method",
    "approved_host",
    "approved_endpoint",
    "approved_url",
    "approved_body_text",
    "send_lease",
)
RECEIPT_SCHEMA_CANDIDATES: tuple[str, ...] = (
    "FlattenPreSendGateReceiptV1",
    "FlattenReceiptSendLeaseV1",
    "FlattenPreSendGateInputV1",
)
PRODUCER_CENSUS_IS_NOT_ATTACHABLE_MINT = True


class FlattenPreSendReceiptAuthorityError(RuntimeError):
    """Fail-closed receipt-authority adjudication violation."""


def _require_standing_live_flags_false() -> None:
    if LIVE_ENABLED or LIVE_ARMED or CANARY_AUTHORIZED or POST_ALLOWED:
        raise FlattenPreSendReceiptAuthorityError("STANDING_LIVE_FLAG_MUST_REMAIN_FALSE")


def census_denied_producer_receipt_v1() -> FlattenPreSendGateReceiptV1:
    """Call the named producer with no GET/reprice snapshots.

    Returns a typed receipt. allowed is expected False. This is producer
    census, not an attachable mint, and not a binding to the frozen envelope.
    """
    _require_standing_live_flags_false()
    return evaluate_flatten_pre_send_gate_v1(
        FlattenPreSendGateInputV1(
            live_authorized=False,
            live_enabled=False,
            live_armed=False,
            flatten_live_wire_enabled=False,
            allow_productive_wire_send=False,
            flatten_execute_token=None,
            flatten_execute_purpose=None,
            flatten_execute_owner_go=None,
            positions_payload={},
            pending_orders_payload=None,
            price_input=FlattenPriceInputV1(),
            owner_go="",
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        )
    )


def prove_denied_receipt_cannot_attach_v1(receipt: FlattenPreSendGateReceiptV1) -> str:
    """Attach of a non-allowed receipt must deny before HMAC/urllib."""
    _require_standing_live_flags_false()
    transport = AuthenticatedGatedProductiveFlattenTransportV1()
    try:
        transport.attach_pre_send_receipt(receipt)
    except LiveCanaryFlattenProductiveTransportError as exc:
        deny = str(exc)
        if transport._receipt is not None:
            raise FlattenPreSendReceiptAuthorityError("DENIED_RECEIPT_MUST_NOT_ATTACH") from exc
        return deny
    raise FlattenPreSendReceiptAuthorityError("DENIED_RECEIPT_ATTACHED")


def adjudicate_flatten_pre_send_receipt_authority_v1() -> dict[str, Any]:
    """Offline authority/schema census. Does not mint, GET, HMAC, or POST."""
    _require_standing_live_flags_false()
    producer_receipt = census_denied_producer_receipt_v1()
    attach_deny = prove_denied_receipt_cannot_attach_v1(producer_receipt)
    producer_consumer_match = (
        isinstance(producer_receipt, FlattenPreSendGateReceiptV1)
        and callable(evaluate_flatten_pre_send_gate_v1)
        and callable(AuthenticatedGatedProductiveFlattenTransportV1.send)
        and callable(AuthenticatedGatedProductiveFlattenTransportV1.attach_pre_send_receipt)
    )
    return {
        "THIS_SLICE": THIS_SLICE,
        "PREDECESSOR_SLICE": PREDECESSOR_SLICE,
        "OWNER_GO": OWNER_GO,
        "RECEIPT_AUTHORITY_SCHEMA_STATUS": RECEIPT_AUTHORITY_SCHEMA_STATUS,
        "RECEIPT_TYPE": RECEIPT_TYPE,
        "RECEIPT_PRODUCER": RECEIPT_PRODUCER,
        "RECEIPT_CONSUMER": RECEIPT_CONSUMER,
        "RECEIPT_ATTACH_SEAM": RECEIPT_ATTACH_SEAM,
        "RECEIPT_AUTHORITY_OR_GO_NAME": RECEIPT_AUTHORITY_OR_GO_NAME,
        "RECEIPT_OWNER_ISSUANCE_SCHEMA_INVENTED": RECEIPT_OWNER_ISSUANCE_SCHEMA_INVENTED,
        "RECEIPT_PRODUCER_ADJUDICATED": True,
        "RECEIPT_CONSUMER_ADJUDICATED": True,
        "PRODUCER_CONSUMER_SCHEMA_MATCH": producer_consumer_match,
        "RECEIPT_SCHEMA_CANDIDATE_COUNT": len(RECEIPT_SCHEMA_CANDIDATES),
        "RECEIPT_BIND_FIELDS": list(RECEIPT_BIND_FIELDS),
        "RECEIPT_MINTED": RECEIPT_MINTED,
        "RECEIPT_BOUND": RECEIPT_BOUND,
        "RECEIPT_ATTACHED": RECEIPT_ATTACHED,
        "PRODUCER_CENSUS_TYPED_OBJECT": True,
        "PRODUCER_CENSUS_ALLOWED": bool(producer_receipt.allowed),
        "PRODUCER_CENSUS_IS_NOT_ATTACHABLE_MINT": PRODUCER_CENSUS_IS_NOT_ATTACHABLE_MINT,
        "PRODUCER_CENSUS_GATE_DIGEST": producer_receipt.gate_digest,
        "DENIED_ATTACH_FIRST_DENY": attach_deny,
        "PRE_SUBMIT_FRESH_GET_REQUIRED": PRE_SUBMIT_FRESH_GET_REQUIRED is True,
        "BOUND_ENVELOPE_ORIGIN_MAIN_SHA": BOUND_ORIGIN_MAIN_SHA,
        "EXPECTED_ORIGIN_MAIN_SHA": EXPECTED_ORIGIN_MAIN_SHA,
        "BOUND_ENVELOPE_SHA_EQUALS_CURRENT_ORIGIN_MAIN": (
            str(BOUND_ORIGIN_MAIN_SHA).strip().lower() == EXPECTED_ORIGIN_MAIN_SHA
        ),
        "RECEIPT_WORK_BLOCKED_BY_OPEN_GATE_ORDER": RECEIPT_WORK_BLOCKED_BY_OPEN_GATE_ORDER,
        "OPEN_GATE_ORDER_BLOCKER": OPEN_GATE_ORDER_BLOCKER,
        "OPEN_GATE_ORDER_BLOCKER_SECONDARY": OPEN_GATE_ORDER_BLOCKER_SECONDARY,
        "OPEN_GATE_ORDER_POINTS": list(OPEN_GATE_ORDER_POINTS),
        "OPEN_GATE_ORDER_POINTS_UNCHANGED": True,
        "CURRENT_CANONICAL_BOUNDARY": CURRENT_CANONICAL_BOUNDARY,
        "EARLIEST_UNRESOLVED_RUNTIME_GATE": EARLIEST_UNRESOLVED_RUNTIME_GATE,
        "NEXT_OWNER_AUTHORITY_REQUIRED": NEXT_OWNER_AUTHORITY_REQUIRED,
        "FIRST_DENY_AFTER_RECEIPT": FIRST_DENY_AFTER_RECEIPT,
        "GET_PERFORMED": False,
        "REPRICE_EXECUTED": False,
        "HMAC_EXECUTED": False,
        "LEASE_CONSUMED": False,
        "POST_PERFORMED": False,
        "WIRE_SEND_EXECUTED": False,
        "DURABLE_CONSUMED": False,
        "POSITION_MUTATION_EXECUTED": False,
        "HMAC_VALIDATION_REACHED": False,
        "LIVE_ENABLED": False,
        "LIVE_ARMED": False,
        "CANARY_AUTHORIZED": False,
        "POST_ALLOWED": False,
        "SECTION_11_14_AUTHORIZED": False,
        "SECTION_11_14_COMPLETE": False,
        "NEXT_SLICE_AUTHORIZED": False,
    }


def persist_flatten_pre_send_receipt_authority_evidence_v1(
    *,
    persist_root: Path | str,
    adjudication: Mapping[str, Any],
) -> dict[str, Any]:
    """Persist offline receipt-authority evidence. No GET. No POST."""
    _require_standing_live_flags_false()
    root = Path(persist_root)
    root.mkdir(parents=True, exist_ok=True)
    summary = {
        "THIS_SLICE": THIS_SLICE,
        "RECEIPT_AUTHORITY_SCHEMA_STATUS": RECEIPT_AUTHORITY_SCHEMA_STATUS,
        "RECEIPT_MINTED": False,
        "RECEIPT_BOUND": False,
        "RECEIPT_ATTACHED": False,
        "RECEIPT_WORK_BLOCKED_BY_OPEN_GATE_ORDER": True,
        "OPEN_GATE_ORDER_BLOCKER": OPEN_GATE_ORDER_BLOCKER,
        "CURRENT_CANONICAL_BOUNDARY": CURRENT_CANONICAL_BOUNDARY,
        "EARLIEST_UNRESOLVED_RUNTIME_GATE": EARLIEST_UNRESOLVED_RUNTIME_GATE,
        "NEXT_OWNER_AUTHORITY_REQUIRED": NEXT_OWNER_AUTHORITY_REQUIRED,
        "GET_PERFORMED": False,
        "REPRICE_EXECUTED": False,
        "HMAC_EXECUTED": False,
        "POST_PERFORMED": False,
        "WIRE_SEND_EXECUTED": False,
        "DURABLE_CONSUMED": False,
        "POSITION_MUTATION_EXECUTED": False,
    }
    claims = {
        "RECEIPT_AUTHORITY_ADJUDICATED": True,
        "RECEIPT_MINTED": False,
        "RECEIPT_ATTACHED": False,
        "OPEN_GATE_ORDER_POINTS_UNCHANGED": True,
    }
    lineage = {
        "PREDECESSOR_SLICE": PREDECESSOR_SLICE,
        "THIS_SLICE": THIS_SLICE,
        "OWNER_GO": OWNER_GO,
        "EXPECTED_ORIGIN_MAIN_SHA": EXPECTED_ORIGIN_MAIN_SHA,
        "BOUND_ENVELOPE_ORIGIN_MAIN_SHA": BOUND_ORIGIN_MAIN_SHA,
    }
    non_execution = {
        "GET_PERFORMED": False,
        "REPRICE_EXECUTED": False,
        "HMAC_EXECUTED": False,
        "LEASE_CONSUMED": False,
        "POST_PERFORMED": False,
        "WIRE_SEND_EXECUTED": False,
        "DURABLE_CONSUMED": False,
        "POSITION_MUTATION_EXECUTED": False,
        "RECEIPT_MINTED": False,
        "RECEIPT_ATTACHED": False,
    }
    files: dict[str, Mapping[str, Any]] = {
        "SUMMARY.json": summary,
        "claims.json": claims,
        "ADJUDICATION.json": dict(adjudication),
        "CENSUS.json": {
            "RECEIPT_SCHEMA_CANDIDATES": list(RECEIPT_SCHEMA_CANDIDATES),
            "RECEIPT_PRODUCER": RECEIPT_PRODUCER,
            "RECEIPT_CONSUMER": RECEIPT_CONSUMER,
            "RECEIPT_BIND_FIELDS": list(RECEIPT_BIND_FIELDS),
        },
        "LINEAGE.json": lineage,
        "NON_EXECUTION.json": non_execution,
    }
    for name, payload in files.items():
        assert_no_plaintext_in_payload_v1(payload)
        write_json_v1(root / name, payload)
    rels = tuple(sorted(files))
    write_manifest_v1(root, rels)
    verified = verify_manifest_v1(root)
    if int(verified.get("MANIFEST_VERIFY_RC", 1)) != 0:
        raise FlattenPreSendReceiptAuthorityError("MANIFEST_VERIFY_FAILED")
    return {
        "persist_root": str(root),
        "MANIFEST_VERIFY_RC": 0,
        "files": list(rels),
    }
