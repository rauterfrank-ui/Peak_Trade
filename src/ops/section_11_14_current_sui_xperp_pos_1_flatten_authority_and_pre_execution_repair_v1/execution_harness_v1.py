"""§11.14 flatten operator harness. Default dry-run. No Owner-GO mint.

Orchestrates the existing wrapper, capture wiring, durable consume, and
position-recon classifier. Does not mutate standing Live flags. Does not GET.
Does not POST unless a caller binds a fake transport and session_armed=True.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.capture_wiring_v1 import (
    capture_readiness_v1,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.constants_v1 import (
    BOUND_FROZEN_ENVELOPE_ID,
    EXPECTED_VENUE_NATIVE_BODY,
    FLATTEN_ACTION,
    INSTRUMENT_ID,
    SESSION_ARMING_STANDING,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.contract_v1 import (
    REQUIRED_CANDIDATE_FIELDS,
    evaluate_flatten_go_candidate_v1,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.durable_consume_v1 import (
    FlattenDurableConsumeError,
    load_flatten_durable_consume_v1,
    persist_flatten_durable_consume_v1,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.persist_v1 import (
    persist_flatten_harness_evidence_v1,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.position_recon_v1 import (
    POSITION_RECON_NOT_EXECUTED,
    evaluate_flatten_position_recon_v1,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.productive_transport_adapter_v1 import (
    ConstructiveProductiveFlattenSubmitAdapterV1,
    construct_productive_flatten_submit_adapter_v1,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.wrapper_v1 import (
    FlattenSubmitTransportV1,
    RecordingFakeFlattenSubmitTransportV1,
    evaluate_current_sha_flatten_wrapper_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    CANARY_AUTHORIZED,
    LIVE_ARMED,
    LIVE_ENABLED,
    POST_ALLOWED,
    SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED,
)


class FlattenExecutionHarnessError(RuntimeError):
    """Fail-closed flatten execution-harness violation."""


def _standing_flags() -> dict[str, bool]:
    flags = {
        "LIVE_ENABLED": bool(LIVE_ENABLED),
        "LIVE_ARMED": bool(LIVE_ARMED),
        "CANARY_AUTHORIZED": bool(CANARY_AUTHORIZED),
        "POST_ALLOWED": bool(POST_ALLOWED),
        "SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED": bool(
            SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED
        ),
    }
    if any(flags.values()):
        raised = ",".join(name for name, value in flags.items() if value)
        raise FlattenExecutionHarnessError(f"STANDING_LIVE_FLAG_MUST_REMAIN_FALSE:{raised}")
    return flags


def assert_candidate_required_fields_v1(candidate: Mapping[str, Any] | None) -> list[str]:
    if candidate is None:
        return ["FLATTEN_GO_CANDIDATE_MISSING"]
    missing = [name for name in REQUIRED_CANDIDATE_FIELDS if name not in candidate]
    if missing:
        return ["FLATTEN_GO_FIELDS_MISSING:" + ",".join(missing)]
    return []


def assert_frozen_preview_if_bound_v1(envelope: Mapping[str, Any]) -> list[str]:
    preview = dict(envelope.get("VENUE_NATIVE_BODY_PREVIEW") or {})
    reasons: list[str] = []
    if "posSide" in preview:
        reasons.append("POS_SIDE_MUST_REMAIN_OMITTED")
    if "clOrdId" in preview:
        reasons.append("CLORDID_MUST_REMAIN_UNBOUND")
    if preview.get("reduceOnly") is not True:
        reasons.append("REDUCE_ONLY_NOT_TRUE")
    eid = str(envelope.get("FLATTEN_ENVELOPE_ID") or "")
    if eid == BOUND_FROZEN_ENVELOPE_ID and preview != EXPECTED_VENUE_NATIVE_BODY:
        reasons.append("FROZEN_VENUE_BODY_MISMATCH")
    return reasons


def _deny(
    *,
    reasons: list[str],
    flags: Mapping[str, bool],
    capture: Mapping[str, Any],
    durable: Mapping[str, Any],
    verdict: Mapping[str, Any] | None,
    productive_implemented: bool,
    mode: str,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "accepted": False,
        "reasons": list(reasons),
        "DRY_RUN": mode != "execute",
        "POST_COUNT": 0,
        "FAKE_POST_COUNT": 0,
        "REAL_POST_COUNT": 0,
        "POST_PERFORMED": False,
        "WIRE_SEND": False,
        "WIRE_SEND_EXECUTED": False,
        "POSITION_MUTATION_EXECUTED": False,
        "OWNER_TOKEN_CONSUMED": bool(durable.get("durable_consumed")),
        "AUTHORITY_CANDIDATE_ACCEPTED": bool((verdict or {}).get("accepted") is True),
        "AUTHORITY_RUNTIME_ISSUED": bool((verdict or {}).get("issued") is True)
        and durable.get("durable_consumed") is not True,
        "EVALUATOR_ISSUED": bool((verdict or {}).get("issued") is True)
        and durable.get("durable_consumed") is not True,
        "EVALUATOR_IS_NOT_ISSUER": True,
        "CAPTURE_READY": capture.get("ready") is True,
        "SESSION_ARMED": False,
        "SESSION_ARMING_REQUIRED": True,
        "SESSION_ARMING_STANDING": SESSION_ARMING_STANDING,
        "PRODUCTIVE_TRANSPORT_IMPLEMENTED": productive_implemented,
        "PRODUCTIVE_TRANSPORT_USED": False,
        "DURABLE_SINGLE_USE_IMPLEMENTED": True,
        "POST_SUBMIT_RECON_IMPLEMENTED": True,
        "STANDING_FLAGS": dict(flags),
        "WRAPPER": None,
        "POSITION_RECON": {
            "outcome": POSITION_RECON_NOT_EXECUTED,
            "GET_PERFORMED": False,
        },
    }
    if extra:
        payload.update(dict(extra))
    return payload


def run_flatten_execution_harness_v1(
    *,
    origin_main_sha: str,
    candidate: Mapping[str, Any] | None,
    envelope: Mapping[str, Any] | None,
    mode: str = "dry-run",
    session_armed: bool = False,
    capture_wired: bool = True,
    retry: bool = False,
    second_submit: bool = False,
    transport: FlattenSubmitTransportV1 | None = None,
    durable_store: Path | str | None = None,
    persist_root: Path | str | None = None,
    positions_payload: Mapping[str, Any] | None = None,
    positions_get_performed: bool = False,
    frozen_evidence_root: str = "",
    issuance: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Orchestrate flatten execution gates. Default dry-run produces zero POSTs."""
    flags = _standing_flags()
    mode_n = str(mode or "dry-run").strip().lower()
    if mode_n not in {"dry-run", "execute"}:
        raise FlattenExecutionHarnessError(f"MODE_FORBIDDEN:{mode}")
    dry_run = mode_n != "execute"
    if dry_run:
        session_armed = False
        transport = None
        positions_get_performed = False
        positions_payload = None
    if session_armed is True and SESSION_ARMING_STANDING is True:
        raise FlattenExecutionHarnessError("STANDING_SESSION_ARMING_MUST_REMAIN_FALSE")
    adapter = construct_productive_flatten_submit_adapter_v1()
    productive_implemented = adapter.implemented is True
    if isinstance(transport, ConstructiveProductiveFlattenSubmitAdapterV1):
        raise FlattenExecutionHarnessError("PRODUCTIVE_ADAPTER_MUST_NOT_BE_USED_TO_SEND")

    durable = load_flatten_durable_consume_v1(store_root=durable_store)
    capture = capture_readiness_v1(wiring_bound=capture_wired)
    consumed_authority_id = ""
    if durable.get("durable_consumed") is True:
        consumed_authority_id = str(
            durable.get("authority_id") or (durable.get("record") or {}).get("authority_id") or ""
        )

    field_reasons = assert_candidate_required_fields_v1(candidate)
    preview_reasons: list[str] = []
    envelope_id = ""
    signed_pos = ""
    side = ""
    qty = ""
    instrument = INSTRUMENT_ID
    if envelope is None:
        preview_reasons.append("CURRENT_SELL_ENVELOPE_MISSING")
    else:
        preview_reasons.extend(assert_frozen_preview_if_bound_v1(envelope))
        envelope_id = str(envelope.get("FLATTEN_ENVELOPE_ID") or "")
        signed_pos = str(envelope.get("SIGNED_POS") or "")
        side = str(envelope.get("SIDE") or "")
        qty = str(envelope.get("QTY") or "")
        instrument = str(envelope.get("INSTRUMENT_ID") or "") or INSTRUMENT_ID

    verdict = evaluate_flatten_go_candidate_v1(
        candidate=candidate,
        origin_main_sha=origin_main_sha,
        instrument_id=instrument,
        expected_signed_position=signed_pos or "1",
        order_side=side or "SELL",
        order_qty=qty or "1",
        exact_envelope_id=envelope_id,
        entry_path=False,
        issuance=issuance,
        durable_consumed_authority_id=consumed_authority_id,
    )

    gate_reasons: list[str] = []
    gate_reasons.extend(field_reasons)
    gate_reasons.extend(preview_reasons)
    if retry is True:
        gate_reasons.append("RETRY_FORBIDDEN")
    if second_submit is True:
        gate_reasons.append("SECOND_SUBMIT_FORBIDDEN")
    if durable.get("durable_consumed") is True:
        gate_reasons.append("CONSUMED_STATE_CANNOT_RESUBMIT")
        if bool((durable.get("record") or {}).get("consumed")) is True:
            gate_reasons.append("CONSUMED_GO_CANNOT_BE_REUSED")
    if capture.get("ready") is not True:
        gate_reasons.append("CAPTURE_NOT_READY")
    if session_armed is not True:
        gate_reasons.append("SESSION_NOT_ARMED")
    if verdict.get("accepted") is not True:
        gate_reasons.extend(str(item) for item in (verdict.get("reasons") or []))

    def _persist_and_return(result: dict[str, Any]) -> dict[str, Any]:
        result["EVALUATOR"] = {
            "accepted": verdict.get("accepted"),
            "reasons": verdict.get("reasons"),
            "issued": verdict.get("issued"),
            "EVALUATOR_IS_NOT_ISSUER": True,
            "authority_id": verdict.get("authority_id"),
        }
        result["EVALUATOR_IS_NOT_ISSUER"] = True
        result["AUTHORITY_RUNTIME_ISSUED"] = (
            verdict.get("issued") is True and durable.get("durable_consumed") is not True
        )
        result["NETWORK_SESSION_AUTHORIZED"] = adapter.inner.network_session_authorized is True
        result["DURABLE"] = {
            "present": durable.get("present"),
            "consumed": durable.get("consumed"),
            "durable_consumed": durable.get("durable_consumed"),
            "reconstruction": durable.get("reconstruction"),
        }
        result["CAPTURE"] = {
            "ready": capture.get("ready"),
            "reason": capture.get("reason"),
            "CAPTURE_EXECUTED": capture.get("CAPTURE_EXECUTED"),
        }
        result["PRE_SUBMIT_CAPTURE_READY"] = capture.get("ready") is True
        result["AUTHORITY_ACCEPTED"] = verdict.get("accepted") is True
        result["ACTION"] = FLATTEN_ACTION
        if persist_root is not None:
            summary = {
                "SCHEMA": "section_11_14_current_flatten_execution_harness.v1",
                "DRY_RUN": result.get("DRY_RUN"),
                "POST_COUNT": result.get("POST_COUNT"),
                "WIRE_SEND": result.get("WIRE_SEND"),
                "AUTHORITY_CANDIDATE_ACCEPTED": result.get("AUTHORITY_CANDIDATE_ACCEPTED"),
                "CAPTURE_READY": result.get("CAPTURE_READY"),
                "SESSION_ARMED": result.get("SESSION_ARMED"),
                "PRODUCTIVE_TRANSPORT_IMPLEMENTED": result.get("PRODUCTIVE_TRANSPORT_IMPLEMENTED"),
                "PRODUCTIVE_TRANSPORT_USED": result.get("PRODUCTIVE_TRANSPORT_USED"),
                "FINAL_ACTION": (
                    "FLATTEN_EXECUTION_HARNESS_DRY_RUN"
                    if result.get("DRY_RUN")
                    else "FLATTEN_EXECUTION_HARNESS_GATED"
                ),
            }
            persist_meta = persist_flatten_harness_evidence_v1(
                persist_root=persist_root,
                summary=summary,
                claims={
                    "GET_ONLY_RUNNER_IS_NOT_SUBMIT_ENTRY": True,
                    "STANDING_LIVE_FLAGS_UNCHANGED": True,
                    "NO_AUTHORITY_FROM_ENV": True,
                    "NO_FORCE_SWITCH": True,
                },
                adjudication={
                    "FLATTEN_AUTHORIZED": False,
                    "OWNER_EXECUTION_AUTHORIZED": False,
                    "AUTHORITY_RUNTIME_ISSUED": result.get("AUTHORITY_RUNTIME_ISSUED") is True,
                },
                lineage={
                    "origin_main_sha": str(origin_main_sha).strip().lower(),
                    "frozen_envelope_id": envelope_id,
                    "frozen_evidence_root": str(frozen_evidence_root or ""),
                    "historical_reuse": False,
                },
                non_execution={
                    "POST_PERFORMED": False,
                    "WIRE_SEND_EXECUTED": False,
                    "POSITION_MUTATION_EXECUTED": False,
                    "SESSION_ARMING": False,
                    "REAL_POST_COUNT": 0,
                },
                harness={k: result[k] for k in result if k != "WRAPPER"},
                candidate=dict(candidate) if candidate is not None else None,
                frozen_ref={
                    "FLATTEN_ENVELOPE_ID": envelope_id,
                    "frozen_evidence_root": str(frozen_evidence_root or ""),
                },
            )
            result["PERSIST"] = persist_meta
            result["MANIFEST_VERIFY_RC"] = persist_meta.get("MANIFEST_VERIFY_RC")
        return result

    if dry_run:
        deny = _deny(
            reasons=gate_reasons,
            flags=flags,
            capture=capture,
            durable=durable,
            verdict=verdict,
            productive_implemented=productive_implemented,
            mode=mode_n,
            extra={
                "NOTE": "DRY_RUN_STOPS_BEFORE_WRAPPER_TRANSPORT",
                "SESSION_ARMED": False,
            },
        )
        # Dry-run reports structural authority even while session remains unarmed.
        deny["AUTHORITY_CANDIDATE_ACCEPTED"] = verdict.get("accepted") is True
        deny["accepted"] = False
        return _persist_and_return(deny)

    if gate_reasons:
        return _persist_and_return(
            _deny(
                reasons=gate_reasons,
                flags=flags,
                capture=capture,
                durable=durable,
                verdict=verdict,
                productive_implemented=productive_implemented,
                mode=mode_n,
            )
        )

    if transport is None:
        return _persist_and_return(
            _deny(
                reasons=["PRODUCTIVE_TRANSPORT_NOT_BOUND"],
                flags=flags,
                capture=capture,
                durable=durable,
                verdict=verdict,
                productive_implemented=productive_implemented,
                mode=mode_n,
                extra={"SESSION_ARMED": True},
            )
        )

    fake = isinstance(transport, RecordingFakeFlattenSubmitTransportV1)
    if not fake:
        return _persist_and_return(
            _deny(
                reasons=["NON_FAKE_TRANSPORT_FORBIDDEN_IN_THIS_HARNESS"],
                flags=flags,
                capture=capture,
                durable=durable,
                verdict=verdict,
                productive_implemented=productive_implemented,
                mode=mode_n,
                extra={"SESSION_ARMED": True},
            )
        )

    try:
        wrapper = evaluate_current_sha_flatten_wrapper_v1(
            origin_main_sha=origin_main_sha,
            flatten_go_candidate=candidate,
            envelope=envelope,
            session_armed=True,
            capture_wired=True,
            retry=False,
            second_submit=False,
            durable_consumed=False,
            transport=transport,
            issuance=issuance,
            durable_consumed_authority_id=consumed_authority_id,
        )
    except Exception as exc:  # noqa: BLE001
        if durable_store is not None:
            try:
                persist_flatten_durable_consume_v1(
                    store_root=durable_store,
                    envelope_id=envelope_id,
                    origin_main_sha=origin_main_sha,
                    durable_state="INCOMPLETE",
                    post_count=0,
                    outcome="AMBIGUOUS_TRANSPORT_EXCEPTION",
                    authority_id=str(verdict.get("authority_id") or ""),
                )
            except FlattenDurableConsumeError:
                pass
            durable = load_flatten_durable_consume_v1(store_root=durable_store)
        return _persist_and_return(
            _deny(
                reasons=["AMBIGUOUS_TRANSPORT_FAIL_CLOSED", str(exc)],
                flags=flags,
                capture=capture,
                durable=durable,
                verdict=verdict,
                productive_implemented=productive_implemented,
                mode=mode_n,
                extra={"SESSION_ARMED": True, "AMBIGUOUS_TRANSPORT": True},
            )
        )

    post_count = int(wrapper.get("POST_COUNT") or 0)
    fake_calls = getattr(transport, "calls", [])
    fake_post_count = len(fake_calls) if fake else 0
    outcome = "FAKE_POST_OK"
    durable_state = "COMPLETED"
    if post_count != 1 or wrapper.get("accepted") is not True:
        outcome = "AMBIGUOUS_OR_DENIED_SUBMIT"
        durable_state = "INCOMPLETE"
    if durable_store is not None and post_count:
        persist_flatten_durable_consume_v1(
            store_root=durable_store,
            envelope_id=envelope_id,
            origin_main_sha=origin_main_sha,
            durable_state=durable_state,
            post_count=post_count,
            outcome=outcome,
            raw_response={"code": "0"} if durable_state == "COMPLETED" else {"code": ""},
            authority_id=str(verdict.get("authority_id") or ""),
        )
        durable = load_flatten_durable_consume_v1(store_root=durable_store)

    recon = evaluate_flatten_position_recon_v1(
        payload=positions_payload,
        instrument_id=instrument,
        get_performed=positions_get_performed is True,
    )
    return _persist_and_return(
        {
            "accepted": wrapper.get("accepted") is True and durable_state == "COMPLETED",
            "reasons": list(wrapper.get("reasons") or []),
            "DRY_RUN": False,
            "POST_COUNT": post_count,
            "FAKE_POST_COUNT": fake_post_count,
            "REAL_POST_COUNT": 0,
            "POST_PERFORMED": fake_post_count == 1,
            "WIRE_SEND": False,
            "WIRE_SEND_EXECUTED": False,
            "POSITION_MUTATION_EXECUTED": False,
            "OWNER_TOKEN_CONSUMED": durable.get("durable_consumed") is True,
            "AUTHORITY_CANDIDATE_ACCEPTED": verdict.get("accepted") is True,
            "AUTHORITY_RUNTIME_ISSUED": False,
            "EVALUATOR_ISSUED": False,
            "EVALUATOR_IS_NOT_ISSUER": True,
            "NETWORK_SESSION_AUTHORIZED": adapter.inner.network_session_authorized is True,
            "CAPTURE_READY": True,
            "SESSION_ARMED": True,
            "SESSION_ARMING_REQUIRED": True,
            "SESSION_ARMING_STANDING": SESSION_ARMING_STANDING,
            "PRODUCTIVE_TRANSPORT_IMPLEMENTED": productive_implemented,
            "PRODUCTIVE_TRANSPORT_USED": False,
            "DURABLE_SINGLE_USE_IMPLEMENTED": True,
            "POST_SUBMIT_RECON_IMPLEMENTED": True,
            "STANDING_FLAGS": dict(flags),
            "WRAPPER": wrapper,
            "POSITION_RECON": recon,
            "FAKE_TRANSPORT_ONLY": True,
        }
    )
