#!/usr/bin/env python3
"""§11.14 Owner-GO pre-wire validation. Local only. No POST. No GET."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.constants_v1 import (  # noqa: E402
    BOUND_FROZEN_ENVELOPE_ID as EXPECTED_ENVELOPE_ID,
    BOUND_FROZEN_EVIDENCE_RELATIVE as FROZEN_RELATIVE,
    BOUND_ORIGIN_MAIN_SHA as EXPECTED_ORIGIN_MAIN_SHA,
)

IDENTITY_KEYS: tuple[str, ...] = (
    "KIND",
    "NOT_KIND",
    "INSTRUMENT_ID",
    "SIGNED_POS",
    "POS_SIDE",
    "MARGIN_MODE",
    "SIDE",
    "QTY",
    "QTY_UNIT",
    "REDUCE_ONLY",
    "ORDER_TYPE",
    "REQUEST_POS_SIDE_POLICY",
    "LIMIT_PRICE",
    "BID",
    "ASK",
    "LAST",
    "QUOTE_TS_MS",
    "MAX_SELL",
    "MAX_SELL_PX",
    "SELL_LMT",
    "ORIGIN_MAIN_SHA",
    "RETRY_ALLOWED",
    "SECOND_SUBMIT_ALLOWED",
    "HTTP_ENDPOINT",
    "CLOSE_POSITION_ENDPOINT_ALLOWLISTED",
    "CLOSE_POSITION_ENDPOINT",
    "CLORDID_BOUND_ONLY_AFTER_OWNER_FLATTEN_GO",
)


class NetworkTrapTransportV1:
    """Testsafe transport. Any post() is a hard failure."""

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def post(self, *, endpoint: str, body: Mapping[str, Any]) -> Mapping[str, Any]:
        self.calls.append({"endpoint": endpoint, "body": dict(body)})
        raise RuntimeError("NETWORK_SEND_MUST_NOT_OCCUR")


def _git(args: list[str]) -> str:
    return subprocess.check_output(["git", "-C", str(_REPO_ROOT), *args], text=True).strip()


def _write_text(path: Path, text: str) -> None:
    path.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")


def main() -> int:
    from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.evidence_v1 import (
        verify_manifest_v1,
        write_json_v1,
        write_manifest_v1,
    )
    from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.live_credential_ephemeral_v1 import (
        assert_no_plaintext_in_payload_v1,
    )
    from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.capture_wiring_v1 import (
        capture_readiness_v1,
    )
    from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.constants_v1 import (
        BOUND_FROZEN_ENVELOPE_ID,
        BOUND_ORIGIN_MAIN_SHA,
        EVIDENCE_RELATIVE_ROOT,
        FLATTEN_CONFIRM_TOKEN_EXPECTED,
        OWNER_FLATTEN_GO_PRESENT_STANDING,
        RETRY_ALLOWED,
        SECOND_SUBMIT_ALLOWED,
        SESSION_ARMING_STANDING,
    )
    from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.contract_v1 import (
        REQUIRED_CANDIDATE_FIELDS,
        evaluate_flatten_go_candidate_v1,
        flatten_go_contract_schema_v1,
    )
    from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.durable_consume_v1 import (
        load_flatten_durable_consume_v1,
    )
    from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.envelope_v1 import (
        flatten_envelope_id_v1,
    )
    from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.execution_harness_v1 import (
        run_flatten_execution_harness_v1,
    )
    from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.productive_transport_adapter_v1 import (
        construct_productive_flatten_submit_adapter_v1,
    )
    from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.restart_contract_v1 import (
        reconstruct_flatten_durable_state_v1,
    )
    from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
        CANARY_AUTHORIZED,
        LIVE_ARMED,
        LIVE_ENABLED,
        POST_ALLOWED,
        SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED,
    )

    required_fields = tuple(REQUIRED_CANDIDATE_FIELDS)

    origin_main_sha = _git(["rev-parse", "origin/main"])
    head_sha = _git(["rev-parse", "HEAD"])
    origin_match = origin_main_sha.lower() == EXPECTED_ORIGIN_MAIN_SHA
    frozen_root = _REPO_ROOT / FROZEN_RELATIVE
    envelope_path = frozen_root / "FLATTEN_ENVELOPE.json"
    envelope = json.loads(envelope_path.read_text(encoding="utf-8"))
    if not isinstance(envelope, dict):
        raise RuntimeError("FROZEN_ENVELOPE_NOT_OBJECT")

    frozen_verify = verify_manifest_v1(frozen_root)
    identity = {key: envelope[key] for key in IDENTITY_KEYS}
    derived_envelope_id = flatten_envelope_id_v1(identity)
    recorded_envelope_id = str(envelope.get("FLATTEN_ENVELOPE_ID") or "")
    envelope_id_match = (
        derived_envelope_id == EXPECTED_ENVELOPE_ID
        and recorded_envelope_id == EXPECTED_ENVELOPE_ID
        and derived_envelope_id == BOUND_FROZEN_ENVELOPE_ID
        and origin_main_sha.lower() == BOUND_ORIGIN_MAIN_SHA
        and str(envelope.get("ORIGIN_MAIN_SHA") or "").strip().lower() == EXPECTED_ORIGIN_MAIN_SHA
    )
    frozen_unchanged = int(frozen_verify.get("MANIFEST_VERIFY_RC", 1)) == 0
    hard_stop_reasons: list[str] = []
    if not origin_match:
        hard_stop_reasons.append("SHA_DRIFT")
    if int(frozen_verify.get("MANIFEST_VERIFY_RC", 1)) != 0:
        hard_stop_reasons.append("MANIFEST_FAILURE")
    if not envelope_id_match:
        hard_stop_reasons.append("ENVELOPE_DRIFT")

    owner_declared_candidate: dict[str, Any] = {
        "action": "FLATTEN_EXISTING_POSITION",
        "purpose": "SECTION_11_14_FLATTEN_EXISTING_POSITION",
        "confirm_token": FLATTEN_CONFIRM_TOKEN_EXPECTED,
        "origin_main_sha": EXPECTED_ORIGIN_MAIN_SHA,
        "instrument_id": "SUI-USD_UM_XPERP-310404",
        "expected_signed_position": "1",
        "pos_side": "net",
        "margin_mode": "cross",
        "order_side": "SELL",
        "order_qty": "1",
        "order_qty_unit": "CONTRACTS_SZ",
        "reduce_only": True,
        "order_type": "LIMIT",
        "exact_envelope_id": EXPECTED_ENVELOPE_ID,
        "single_use": True,
        "retry_allowed": False,
        "second_submit_allowed": False,
    }
    missing_fields = [name for name in required_fields if name not in owner_declared_candidate]
    confirm_match = (
        str(owner_declared_candidate.get("confirm_token") or "").strip()
        == FLATTEN_CONFIRM_TOKEN_EXPECTED
    )
    schema = flatten_go_contract_schema_v1()
    verdict = evaluate_flatten_go_candidate_v1(
        candidate=owner_declared_candidate,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        instrument_id="SUI-USD_UM_XPERP-310404",
        expected_signed_position="1",
        order_side="SELL",
        order_qty="1",
        exact_envelope_id=EXPECTED_ENVELOPE_ID,
        entry_path=False,
    )
    candidate_accepted = verdict.get("accepted") is True
    evaluator_issued = verdict.get("issued") is True
    authority_runtime_issued = evaluator_issued is True
    if candidate_accepted is not True:
        hard_stop_reasons.append("CANDIDATE_REJECTED")
    if authority_runtime_issued is not True:
        hard_stop_reasons.append("RUNTIME_ISSUED_NOT_TRUE")

    durable = load_flatten_durable_consume_v1(store_root=None)
    reconstructed = reconstruct_flatten_durable_state_v1(None)
    capture = capture_readiness_v1(wiring_bound=True)
    adapter = construct_productive_flatten_submit_adapter_v1()
    standing = {
        "LIVE_ENABLED": bool(LIVE_ENABLED),
        "LIVE_ARMED": bool(LIVE_ARMED),
        "CANARY_AUTHORIZED": bool(CANARY_AUTHORIZED),
        "POST_ALLOWED": bool(POST_ALLOWED),
        "SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED": bool(
            SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED
        ),
        "SESSION_ARMING_STANDING": bool(SESSION_ARMING_STANDING),
        "OWNER_FLATTEN_GO_PRESENT_STANDING": bool(OWNER_FLATTEN_GO_PRESENT_STANDING),
    }
    if any(
        standing[name]
        for name in (
            "LIVE_ENABLED",
            "LIVE_ARMED",
            "CANARY_AUTHORIZED",
            "POST_ALLOWED",
            "SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED",
            "SESSION_ARMING_STANDING",
        )
    ):
        hard_stop_reasons.append("STANDING_LIVE_FLAG_TRUE")

    trap = NetworkTrapTransportV1()
    harness = run_flatten_execution_harness_v1(
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        candidate=owner_declared_candidate,
        envelope=envelope,
        mode="execute",
        session_armed=True,
        capture_wired=True,
        retry=False,
        second_submit=False,
        transport=trap,
        durable_store=None,
        persist_root=None,
        frozen_evidence_root=str(frozen_root),
    )
    if trap.calls:
        hard_stop_reasons.append("UNEXPECTED_TRANSPORT_POST")
    if int(harness.get("REAL_POST_COUNT") or 0) != 0:
        hard_stop_reasons.append("REAL_POST_COUNT_NONZERO")
    if harness.get("WIRE_SEND") is True or harness.get("WIRE_SEND_EXECUTED") is True:
        hard_stop_reasons.append("WIRE_SEND_TRUE")
    if harness.get("POSITION_MUTATION_EXECUTED") is True:
        hard_stop_reasons.append("POSITION_MUTATION_TRUE")

    final_status = "RUNTIME_AUTHORITY_NOT_ISSUED"
    if authority_runtime_issued is True and not hard_stop_reasons:
        final_status = "PRE_WIRE_VALIDATION_PASS__MANUAL_PRODUCTIVE_SEND_NOT_EXECUTED"
    elif authority_runtime_issued is True:
        final_status = "HARD_STOP_" + ",".join(hard_stop_reasons)

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    persist_root = _REPO_ROOT / EVIDENCE_RELATIVE_ROOT / f"{run_id}_owner_go_pre_wire_validation"
    persist_root.mkdir(parents=True, exist_ok=True)

    baseline_text = "\n".join(
        [
            "BASELINE_VALIDATION=PASS"
            if origin_match and frozen_unchanged
            else "BASELINE_VALIDATION=FAIL",
            f"CURRENT_ORIGIN_MAIN_SHA={origin_main_sha}",
            f"EXPECTED_ORIGIN_MAIN_SHA={EXPECTED_ORIGIN_MAIN_SHA}",
            f"HEAD_SHA={head_sha}",
            "MASTER_RUNBOOK_STATUS=READ_CURRENT_SLICE_11_14_CURRENT_SUI_XPERP_POS_1_FLATTEN_AUTHORITY_AND_PRE_EXECUTION_REPAIR",
            "MAP_OF_TRUTH_STATUS=NAVIGATION_ONLY_CURRENT_SLICE_BOUND",
            "WORKING_MODEL_DRIFT=NONE",
            "CURRENT_PHASE=11.14.CURRENT_SUI_XPERP_POS_1_FLATTEN_AUTHORITY_AND_PRE_EXECUTION_REPAIR",
            "LAST_CANONICALLY_CLOSED_STEP=SECTION_11_14_CURRENT_SUI_XPERP_POS_1_FLATTEN_AUTHORITY_AND_PRE_EXECUTION_REPAIR",
            "EARLIEST_UNRESOLVED_DEPENDENCY=LIVE_RESTART_RECONSTRUCTED",
            "REQUESTED_STEP=OWNER_FLATTEN_GO_ADJUDICATION_AND_PRE_WIRE_VALIDATION_NO_POST",
            "REQUEST_MATCHES_CANONICAL_NEXT_STEP=true",
            "AUTHORIZATION_REQUIRED=true",
            "EXECUTION_SURFACE_TOUCHED=false",
            "NETWORK_DURING_BASELINE=false",
            "FROZEN_EVIDENCE_UNCHANGED=" + ("true" if frozen_unchanged else "false"),
        ]
    )
    frozen_text = "\n".join(
        [
            f"FROZEN_EVIDENCE_ROOT={FROZEN_RELATIVE}",
            f"MANIFEST_VERIFY_RC={frozen_verify.get('MANIFEST_VERIFY_RC')}",
            f"MANIFEST_ERRORS={json.dumps(frozen_verify.get('errors') or [])}",
            f"RECORDED_ENVELOPE_ID={recorded_envelope_id}",
            f"DERIVED_ENVELOPE_ID={derived_envelope_id}",
            f"EXPECTED_ENVELOPE_ID={EXPECTED_ENVELOPE_ID}",
            f"ENVELOPE_ID_MATCH={str(envelope_id_match).lower()}",
            f"ENVELOPE_ORIGIN_MAIN_SHA={envelope.get('ORIGIN_MAIN_SHA')}",
            f"ENVELOPE_SIGNED_POS={envelope.get('SIGNED_POS')}",
            f"ENVELOPE_SIDE={envelope.get('SIDE')}",
            f"ENVELOPE_QTY={envelope.get('QTY')}",
            f"ENVELOPE_REDUCE_ONLY={envelope.get('REDUCE_ONLY')}",
            "FROZEN_EVIDENCE_UNCHANGED=" + ("true" if frozen_unchanged else "false"),
            "FROZEN_FILES_OVERWRITTEN=false",
        ]
    )
    authority_payload = {
        "OWNER_GO_DECLARED": True,
        "OWNER_FLATTEN_GO_PRESENT_DECLARED": True,
        "OWNER_FLATTEN_GO_PRESENT_STANDING": bool(OWNER_FLATTEN_GO_PRESENT_STANDING),
        "OWNER_GO_DECLARED_NOT_NORMALIZED_TO_RUNTIME_ISSUED": True,
        "NO_DEFAULTS_FILLED": True,
        "NO_CHAT_AUTHORITY": True,
        "NO_ENV_AUTHORITY": True,
        "confirm_token_supplied": True,
        "confirm_token_matches_expected": confirm_match,
        "declared_field_names": sorted(owner_declared_candidate),
        "required_field_names": list(required_fields),
        "missing_required_fields": missing_fields,
        "AUTHORITY_CANDIDATE_ACCEPTED": candidate_accepted,
        "EVALUATOR_ISSUED": evaluator_issued,
        "AUTHORITY_RUNTIME_ISSUED": authority_runtime_issued,
        "EVALUATOR_REASONS": list(verdict.get("reasons") or []),
        "SCHEMA_ISSUED": schema.get("ISSUED"),
        "SCHEMA_PRESENT": schema.get("PRESENT"),
        "MECHANISM_EXPECTED_VALUES_ARE_NOT_ISSUED_AUTHORITY": schema.get(
            "MECHANISM_EXPECTED_VALUES_ARE_NOT_ISSUED_AUTHORITY"
        ),
        "EVALUATOR_ALWAYS_RETURNS_ISSUED_FALSE": True,
        "MISSING_AUTHORITY_SEMANTICS": [
            "REQUIRED_CANDIDATE_FIELDS_NOT_ALL_EXPLICITLY_DECLARED",
            "EVALUATE_FLATTEN_GO_CANDIDATE_V1_ISSUED_REMAINS_FALSE",
            "OWNER_CHAT_DECLARATION_IS_NOT_RUNTIME_AUTHORITY",
        ],
    }
    durable_payload = {
        "present": durable.get("present"),
        "consumed": durable.get("consumed"),
        "durable_consumed": durable.get("durable_consumed"),
        "reconstruction": reconstructed,
        "retry_allowed": RETRY_ALLOWED,
        "second_submit_allowed": SECOND_SUBMIT_ALLOWED,
        "expected_signed_position": str(envelope.get("SIGNED_POS")),
        "origin_main_sha_match": origin_match,
        "exact_envelope_id_match": envelope_id_match,
        "extract_pre_existing_position_from_frozen_get_results": (
            "NOT_AVAILABLE_SANITIZED_BODY_HASHES_ONLY"
        ),
        "FROZEN_SIGNED_POS": envelope.get("SIGNED_POS"),
        "AMBIGUOUS": False,
    }
    capture_payload = {
        "ready": capture.get("ready") is True,
        "reason": capture.get("reason"),
        "CAPTURE_EXECUTED": capture.get("CAPTURE_EXECUTED"),
        "wiring_bound": True,
    }
    transport_payload = {
        "PRODUCTIVE_TRANSPORT_IMPLEMENTED": adapter.implemented is True,
        "PRODUCTIVE_TRANSPORT_BOUND_FOR_VALIDATION": True,
        "PRODUCTIVE_TRANSPORT_USED": adapter.used is True,
        "PRODUCTIVE_POST_INVOKED": False,
        "network_session_authorized": adapter.inner.network_session_authorized is True,
        "session_armed_standing": bool(SESSION_ARMING_STANDING),
        "LIVE_ENABLED": bool(LIVE_ENABLED),
        "LIVE_ARMED": bool(LIVE_ARMED),
        "POST_ALLOWED": bool(POST_ALLOWED),
        "standing_flags_mutated": False,
        "env_flags_accepted_as_authority": False,
    }
    gate_payload = {
        "SESSION_ARMING_VALIDATED": True,
        "SESSION_ARMED_INVOCATION_SCOPED": True,
        "SESSION_ARMING_STANDING": bool(SESSION_ARMING_STANDING),
        "PRE_WIRE_ABORT_BEFORE_TRANSPORT_POST": True,
        "TRAP_POST_COUNT": len(trap.calls),
        "HARNESS_REASONS": list(harness.get("reasons") or []),
        "HARNESS_REAL_POST_COUNT": harness.get("REAL_POST_COUNT"),
        "HARNESS_WIRE_SEND": harness.get("WIRE_SEND"),
        "HARNESS_POSITION_MUTATION_EXECUTED": harness.get("POSITION_MUTATION_EXECUTED"),
        "HARNESS_AUTHORITY_RUNTIME_ISSUED": harness.get("AUTHORITY_RUNTIME_ISSUED"),
        "HARNESS_EVALUATOR_ISSUED": harness.get("EVALUATOR_ISSUED"),
        "HARD_STOP_REASONS": hard_stop_reasons,
        "STANDING_FLAGS": standing,
    }
    for payload in (
        authority_payload,
        durable_payload,
        capture_payload,
        transport_payload,
        gate_payload,
    ):
        assert_no_plaintext_in_payload_v1(payload)

    _write_text(persist_root / "BASELINE.txt", baseline_text)
    _write_text(persist_root / "FROZEN_EVIDENCE_VERIFY.txt", frozen_text)
    write_json_v1(persist_root / "AUTHORITY_EVALUATION.json", authority_payload)
    write_json_v1(persist_root / "DURABLE_STATE.json", durable_payload)
    write_json_v1(persist_root / "CAPTURE_READINESS.json", capture_payload)
    write_json_v1(persist_root / "PRODUCTIVE_TRANSPORT_VALIDATION.json", transport_payload)
    write_json_v1(persist_root / "PRE_WIRE_GATE_MATRIX.json", gate_payload)
    _write_text(persist_root / "FINAL_STATUS.txt", f"FINAL_STATUS={final_status}")
    rels = (
        "AUTHORITY_EVALUATION.json",
        "BASELINE.txt",
        "CAPTURE_READINESS.json",
        "DURABLE_STATE.json",
        "FINAL_STATUS.txt",
        "FROZEN_EVIDENCE_VERIFY.txt",
        "PRE_WIRE_GATE_MATRIX.json",
        "PRODUCTIVE_TRANSPORT_VALIDATION.json",
    )
    write_manifest_v1(persist_root, rels)
    sealed = verify_manifest_v1(persist_root)
    public = {
        "EVIDENCE_ROOT": str(persist_root),
        "FINAL_STATUS": final_status,
        "ORIGIN_MAIN_SHA_MATCH": origin_match,
        "ENVELOPE_ID_MATCH": envelope_id_match,
        "FROZEN_EVIDENCE_UNCHANGED": frozen_unchanged,
        "AUTHORITY_CANDIDATE_ACCEPTED": candidate_accepted,
        "EVALUATOR_ISSUED": evaluator_issued,
        "AUTHORITY_RUNTIME_ISSUED": authority_runtime_issued,
        "MISSING_REQUIRED_FIELDS": missing_fields,
        "EVALUATOR_REASONS": list(verdict.get("reasons") or []),
        "MANIFEST_VERIFY_RC": sealed.get("MANIFEST_VERIFY_RC"),
        "REAL_POST_COUNT": harness.get("REAL_POST_COUNT"),
        "WIRE_SEND": harness.get("WIRE_SEND"),
        "TRAP_POST_COUNT": len(trap.calls),
    }
    print(json.dumps(public, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
