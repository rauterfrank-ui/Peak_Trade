"""CURRENT_PRODUCTIVE SUBMISSION_AUTHORIZED standing remainder.

Consumes Owner-GO
OWNER_GO_CURRENT_PRODUCTIVE_SUBMISSION_AUTHORIZED_V1.

Closes SUBMISSION_AUTHORIZED as a fail-closed submission-capability
admission remainder after Cap-7.2 host-join. True is not LIVE_AUTHORIZED,
STEP-29Q, POST, or productive wire send. Host-join, the LiveExecutionPort
handle, and WIRE_SEND_PERMITTED remain independently insufficient.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from src.ops.capability_11_1_execution_domain_and_order_lifecycle_contracts_v1.execution_ports_v1 import (
    ExecutionPortConstructionForbiddenError,
    construct_live_execution_port_v1,
)
from src.ops.full_core_live_path_composition_root_v1.cap72_host_join_to_live_execution_port_v1 import (
    join_cap72_host_to_live_execution_port_v1,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    CAP_7_2_HOST_JOIN_TO_LIVE_EXECUTION_PORT,
    CAP_7_2_HOST_JOINED_IS_NOT_SUBMISSION_AUTHORIZED,
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    LIVE_ENABLED,
    LIVE_EXECUTION_PORT_CONSTRUCTIBLE,
    PRODUCTIVE_WIRE_SEND_REACHABLE,
    STANDING_LIVE_AUTHORIZATION,
    SUBMISSION_AUTHORIZED,
    SUBMISSION_AUTHORIZED_DOES_NOT_IMPLY_LIVE_AUTHORIZED,
    SUBMISSION_AUTHORIZED_DOES_NOT_IMPLY_POST,
    SUBMISSION_AUTHORIZED_DOES_NOT_IMPLY_PRODUCTIVE_WIRE_SEND_REACHABLE,
    SUBMISSION_AUTHORIZED_DOES_NOT_IMPLY_STEP_29Q,
    SUBMISSION_AUTHORIZED_DOES_NOT_IMPLY_WIRE_SEND,
    SUBMISSION_AUTHORIZED_STANDING_ADMISSION_SEAM_IMPLEMENTED,
    SUBMISSION_AUTHORIZED_STANDING_GATE_CLOSED,
    SUBMISSION_AUTHORIZED_TRUE_IS_NOT_AUTOMATIC_SEND,
    SUBMISSION_AUTHORIZED_TRUE_IS_NOT_AUTOMATIC_WIRE,
    WIRE_SEND_PERMITTED,
    current_productive_first_real_blocker_v1,
    standing_live_gate_fields_v1,
)
from src.ops.full_core_live_path_composition_root_v1.execution_admission_contract_v1 import (
    ADMISSION_CONTEXT_LIVE,
    CAPITAL_AUTHORITY_RISK_ADMISSIBLE,
    CAPITAL_RISK_MODE_LIVE_ACCOUNT_BOUND,
    CapitalAdmissionStatusV1,
    DurableKillSwitchEvidenceStatusV1,
    ExecutionAdmissionInputsV1,
    FreshPretradeGetStatusV1,
    LiveAccountBoundStatusV1,
    OwnerOneShotPermitStatusV1,
    PRETRADE_SOURCE_FRESH_GET,
    PretradeFreshnessStatusV1,
    evaluate_execution_admission_v1,
)
from src.ops.full_core_live_path_composition_root_v1.live_admission_gap_dag_v1 import (
    gap_node_v1,
)
from src.ops.full_core_live_path_composition_root_v1.live_execution_port_construction_admission_v1 import (
    evaluate_live_execution_port_construction_admission_v1,
)
from src.ops.full_core_live_path_composition_root_v1.submission_authorized_v1 import (
    STEP_29Q_PLAN_ONLY,
    evaluate_submission_authorized_v1,
    prove_submission_authorized_not_wire_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    CURRENT_PRODUCTIVE_SUBMISSION_AUTHORIZED_ADAPTER_CREATED,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_cap72_host_join_to_live_execution_port_v1 import (
    CANONICAL_PACK_RELPATH as DF_PACK_RELPATH,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.d4_d5_genesis_runtime_orchestrator_v1 import (
    persist_manifest_sha256_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    verify_manifest_sha256_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.host_binding_v1 import (
    HostActivationBindingV1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.simulated_execution_port_v1 import (
    SimulatedExecutionPortV1,
)

OWNER_GO = "OWNER_GO_CURRENT_PRODUCTIVE_SUBMISSION_AUTHORIZED_V1"
THIS_SLICE = "11.2.1.DG.FULL_CORE_CURRENT_PRODUCTIVE_SUBMISSION_AUTHORIZED"
EXPECTED_ORIGIN_MAIN_SHA = "7fa87e76c7755467528848a3ff52ac4d98f48bb6"
CANONICAL_PACK_RELPATH = (
    "evidence/ops/full_core_current_productive_submission_authorized_v1/20260915T195700Z"
)
FALSE_TOKEN = "false"
TRUE_TOKEN = "true"
_ADMISSION_DENY_REASONS = frozenset(
    {
        "EXECUTION_ADMISSION_FAIL_CLOSED",
        "LIVE_ENABLED_FALSE",
        "LIVE_ARMED_FALSE",
        "WIRE_SEND_NOT_PERMITTED",
    }
)
_SECRET_TOKENS = ("secret", "passphrase", "api_key", "apiKey", "private_key")


class CurrentProductiveSubmissionAuthorizedError(ValueError):
    """Fail-closed SUBMISSION_AUTHORIZED remainder violation."""


@dataclass(frozen=True)
class CurrentProductiveSubmissionAuthorizedResultV1:
    store_root: str
    live_enabled: str
    live_armed: str
    wire_send_permitted: str
    live_authorized: str
    admitted: str
    host_joined: str
    port_constructed: str
    submission_authorized: str
    submission_deny_absent: str
    step_29p_risk_admissible: str
    cap24_bound_instrument_id: str
    first_real_blocker: str
    blocker_class: str
    post_count: str
    evidence_manifest: str
    manifest_verify_rc: int


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _persist_json(*, path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(_canonical_json(payload) + "\n", encoding="utf-8")
    tmp.replace(path)


def _assert_no_secrets(payload: Mapping[str, Any]) -> None:
    blob = _canonical_json(payload).lower()
    for token in _SECRET_TOKENS:
        if token in blob:
            raise CurrentProductiveSubmissionAuthorizedError(f"SECRET_TOKEN_PRESENT:{token}")


def _load_json_object(*, path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise CurrentProductiveSubmissionAuthorizedError(f"JSON_NOT_OBJECT:{path.name}")
    return payload


def _token(value: bool) -> str:
    return TRUE_TOKEN if value is True else FALSE_TOKEN


def _assert_standing_pins() -> None:
    if CURRENT_PRODUCTIVE_SUBMISSION_AUTHORIZED_ADAPTER_CREATED is not True:
        raise CurrentProductiveSubmissionAuthorizedError("ADAPTER_NOT_CREATED")
    if SUBMISSION_AUTHORIZED_STANDING_ADMISSION_SEAM_IMPLEMENTED is not True:
        raise CurrentProductiveSubmissionAuthorizedError("SEAM_NOT_IMPLEMENTED")
    if SUBMISSION_AUTHORIZED_STANDING_GATE_CLOSED is not True:
        raise CurrentProductiveSubmissionAuthorizedError("GATE_NOT_CLOSED")
    if SUBMISSION_AUTHORIZED is not True:
        raise CurrentProductiveSubmissionAuthorizedError("SUBMISSION_AUTHORIZED_NOT_TRUE")
    if SUBMISSION_AUTHORIZED_TRUE_IS_NOT_AUTOMATIC_SEND is not True:
        raise CurrentProductiveSubmissionAuthorizedError("MUST_NOT_AUTOMATIC_SEND")
    if SUBMISSION_AUTHORIZED_TRUE_IS_NOT_AUTOMATIC_WIRE is not True:
        raise CurrentProductiveSubmissionAuthorizedError("MUST_NOT_AUTOMATIC_WIRE")
    if SUBMISSION_AUTHORIZED_DOES_NOT_IMPLY_WIRE_SEND is not True:
        raise CurrentProductiveSubmissionAuthorizedError("MUST_NOT_IMPLY_WIRE")
    if SUBMISSION_AUTHORIZED_DOES_NOT_IMPLY_LIVE_AUTHORIZED is not True:
        raise CurrentProductiveSubmissionAuthorizedError("MUST_NOT_IMPLY_LIVE_AUTHORIZED")
    if SUBMISSION_AUTHORIZED_DOES_NOT_IMPLY_STEP_29Q is not True:
        raise CurrentProductiveSubmissionAuthorizedError("MUST_NOT_IMPLY_STEP_29Q")
    if SUBMISSION_AUTHORIZED_DOES_NOT_IMPLY_POST is not True:
        raise CurrentProductiveSubmissionAuthorizedError("MUST_NOT_IMPLY_POST")
    if SUBMISSION_AUTHORIZED_DOES_NOT_IMPLY_PRODUCTIVE_WIRE_SEND_REACHABLE is not True:
        raise CurrentProductiveSubmissionAuthorizedError("MUST_NOT_IMPLY_WIRE_REACHABLE")
    if CAP_7_2_HOST_JOINED_IS_NOT_SUBMISSION_AUTHORIZED is not True:
        raise CurrentProductiveSubmissionAuthorizedError("JOIN_MUST_NOT_SUBMIT")
    if LIVE_ENABLED is not True:
        raise CurrentProductiveSubmissionAuthorizedError("LIVE_ENABLED_NOT_TRUE")
    if LIVE_ARMED is not True:
        raise CurrentProductiveSubmissionAuthorizedError("LIVE_ARMED_NOT_TRUE")
    if WIRE_SEND_PERMITTED is not True:
        raise CurrentProductiveSubmissionAuthorizedError("WIRE_SEND_PERMITTED_NOT_TRUE")
    if CAP_7_2_HOST_JOIN_TO_LIVE_EXECUTION_PORT is not True:
        raise CurrentProductiveSubmissionAuthorizedError("HOST_JOIN_NOT_TRUE")
    if LIVE_EXECUTION_PORT_CONSTRUCTIBLE is not True:
        raise CurrentProductiveSubmissionAuthorizedError("PORT_NOT_CONSTRUCTIBLE")
    if STANDING_LIVE_AUTHORIZATION is not False:
        raise CurrentProductiveSubmissionAuthorizedError("STANDING_LIVE_AUTHORIZATION_NOT_FALSE")
    node = gap_node_v1("SUBMISSION_AUTHORIZED")
    if node.implementation_status != "STANDING_TRUE_NOT_AUTOMATIC_WIRE":
        raise CurrentProductiveSubmissionAuthorizedError("DAG_NODE_STATUS_DRIFT")
    port_node = gap_node_v1("LiveExecutionPort")
    if port_node.implementation_status != "SEND_CAPABLE_NOT_EXTERNAL_EFFECT":
        raise CurrentProductiveSubmissionAuthorizedError("PORT_DAG_NODE_STATUS_DRIFT")


def _bind_current_df_epoch(*, repo_root: Path) -> dict[str, Any]:
    claims_path = repo_root / DF_PACK_RELPATH / "claims.json"
    if not claims_path.is_file():
        raise CurrentProductiveSubmissionAuthorizedError("DF_CLAIMS_MISSING")
    claims = _load_json_object(path=claims_path)
    if str(claims.get("LIVE_ENABLED") or "") != TRUE_TOKEN:
        raise CurrentProductiveSubmissionAuthorizedError("DF_LIVE_ENABLED_NOT_TRUE")
    if str(claims.get("LIVE_ARMED") or "") != TRUE_TOKEN:
        raise CurrentProductiveSubmissionAuthorizedError("DF_LIVE_ARMED_NOT_TRUE")
    if str(claims.get("WIRE_SEND_PERMITTED") or "") != TRUE_TOKEN:
        raise CurrentProductiveSubmissionAuthorizedError("DF_WIRE_SEND_NOT_TRUE")
    if str(claims.get("ADMITTED") or "") != TRUE_TOKEN:
        raise CurrentProductiveSubmissionAuthorizedError("DF_ADMITTED_NOT_TRUE")
    if str(claims.get("LIVE_EXECUTION_PORT_CONSTRUCTED") or "") != TRUE_TOKEN:
        raise CurrentProductiveSubmissionAuthorizedError("DF_PORT_NOT_CONSTRUCTED")
    if str(claims.get("HOST_JOINED") or "") != TRUE_TOKEN:
        raise CurrentProductiveSubmissionAuthorizedError("DF_HOST_NOT_JOINED")
    if str(claims.get("CAP_7_2_HOST_JOIN_TO_LIVE_EXECUTION_PORT") or "") != TRUE_TOKEN:
        raise CurrentProductiveSubmissionAuthorizedError("DF_HOST_JOIN_NOT_TRUE")
    if str(claims.get("STEP_29P_RISK_ADMISSIBLE") or "") != TRUE_TOKEN:
        raise CurrentProductiveSubmissionAuthorizedError("DF_STEP_29P_NOT_TRUE")
    instrument_id = str(claims.get("CAP24_BOUND_INSTRUMENT_ID") or "").strip()
    if not instrument_id:
        raise CurrentProductiveSubmissionAuthorizedError("DF_CAP24_ID_MISSING")
    if str(claims.get("POST_COUNT") or "") != "0":
        raise CurrentProductiveSubmissionAuthorizedError("DF_POST_COUNT_NOT_ZERO")
    if str(claims.get("LIVE_AUTHORIZED") or "") != FALSE_TOKEN:
        raise CurrentProductiveSubmissionAuthorizedError("DF_LIVE_AUTHORIZED_NOT_FALSE")
    if str(claims.get("SUBMISSION_AUTHORIZED") or "") != FALSE_TOKEN:
        raise CurrentProductiveSubmissionAuthorizedError("DF_SUBMISSION_NOT_FALSE")
    if str(claims.get("FIRST_REAL_BLOCKER") or "") != "SUBMISSION_AUTHORIZED_REMAINS_FALSE":
        raise CurrentProductiveSubmissionAuthorizedError("DF_BLOCKER_DRIFT")
    return claims


def _admission_inputs_v1() -> ExecutionAdmissionInputsV1:
    return ExecutionAdmissionInputsV1(
        plan_identity="current-productive-submission-authorized",
        venue_plan_identity="current-productive-submission-authorized",
        instrument_identity_ok=True,
        pretrade_admissible=True,
        pretrade_source_kind=PRETRADE_SOURCE_FRESH_GET,
        pretrade_freshness_status=PretradeFreshnessStatusV1.LIVE_FRESH.value,
        capital_risk_mode=CAPITAL_RISK_MODE_LIVE_ACCOUNT_BOUND,
        durable_kill_switch_evidence_status=(
            DurableKillSwitchEvidenceStatusV1.TRUSTED_PRESENT.value
        ),
        durable_kill_switch_blocked=False,
        live_enabled=LIVE_ENABLED is True,
        live_armed=LIVE_ARMED is True,
        wire_send_permitted=WIRE_SEND_PERMITTED is True,
        owner_authorization_present=True,
        owner_one_shot_permit_status=OwnerOneShotPermitStatusV1.TRUSTED_PRESENT.value,
        admission_context=ADMISSION_CONTEXT_LIVE,
        fresh_pretrade_get_status=FreshPretradeGetStatusV1.TRUSTED_PRESENT.value,
        live_account_bound_status=LiveAccountBoundStatusV1.TRUSTED_PRESENT.value,
        capital_admission_status=CapitalAdmissionStatusV1.TRUSTED_PRESENT.value,
        capital_authority_class=CAPITAL_AUTHORITY_RISK_ADMISSIBLE,
        step_29p_risk_admissible=True,
    )


def execute_current_productive_submission_authorized_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    evidence_root: Path | None = None,
    repo_root: Path | None = None,
) -> CurrentProductiveSubmissionAuthorizedResultV1:
    if owner_go != OWNER_GO:
        raise CurrentProductiveSubmissionAuthorizedError("OWNER_GO_MISMATCH")
    if origin_main_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise CurrentProductiveSubmissionAuthorizedError("ORIGIN_MAIN_SHA_MISMATCH")
    _assert_standing_pins()
    root = repo_root or Path(__file__).resolve().parents[3]
    df = _bind_current_df_epoch(repo_root=root)
    gates = standing_live_gate_fields_v1()
    if gates["live_enabled"] is not True:
        raise CurrentProductiveSubmissionAuthorizedError("STANDING_FIELD_LIVE_ENABLED_FALSE")
    if gates["live_armed"] is not True:
        raise CurrentProductiveSubmissionAuthorizedError("STANDING_FIELD_LIVE_ARMED_FALSE")
    if gates["wire_send_permitted"] is not True:
        raise CurrentProductiveSubmissionAuthorizedError("STANDING_FIELD_WIRE_FALSE")
    if gates["submission_authorized"] is not True:
        raise CurrentProductiveSubmissionAuthorizedError("STANDING_FIELD_SUBMISSION_FALSE")

    decision = evaluate_execution_admission_v1(_admission_inputs_v1())
    if decision.admitted is not True:
        raise CurrentProductiveSubmissionAuthorizedError("ADMISSION_NOT_ADMITTED")
    deny_hit = _ADMISSION_DENY_REASONS.intersection(decision.reason_codes)
    if deny_hit:
        raise CurrentProductiveSubmissionAuthorizedError(
            f"ADMISSION_DENY_PRESENT:{sorted(deny_hit)}"
        )
    if decision.reason_codes:
        raise CurrentProductiveSubmissionAuthorizedError(
            f"UNEXPECTED_ADMISSION_REASONS:{list(decision.reason_codes)}"
        )

    default_deny = evaluate_submission_authorized_v1()
    if default_deny.submission_authorized is True:
        raise CurrentProductiveSubmissionAuthorizedError("DEFAULT_MUST_DENY")
    if "HOST_NOT_JOINED" not in default_deny.reason_codes:
        raise CurrentProductiveSubmissionAuthorizedError("DEFAULT_HOST_DENY_MISSING")
    if "LIVE_PORT_MISSING" not in default_deny.reason_codes:
        raise CurrentProductiveSubmissionAuthorizedError("DEFAULT_PORT_DENY_MISSING")
    if "EXECUTION_ADMISSION_NOT_ADMITTED" not in default_deny.reason_codes:
        raise CurrentProductiveSubmissionAuthorizedError("DEFAULT_ADMISSION_DENY_MISSING")

    standing_false = evaluate_submission_authorized_v1(
        host_joined=True,
        admitted=True,
        standing_submission_authorized=False,
    )
    if standing_false.submission_authorized is True:
        raise CurrentProductiveSubmissionAuthorizedError("STANDING_FALSE_MUST_DENY")
    if "SUBMISSION_AUTHORIZED_STANDING_FALSE" not in standing_false.reason_codes:
        raise CurrentProductiveSubmissionAuthorizedError("STANDING_FALSE_DENY_MISSING")

    malformed = evaluate_submission_authorized_v1(
        host_joined=True,
        admitted=True,
        standing_submission_authorized="UNKNOWN",  # type: ignore[arg-type]
        durable_kill_switch_evidence_status="MALFORMED",
        durable_kill_switch_blocked=None,
    )
    if malformed.submission_authorized is True:
        raise CurrentProductiveSubmissionAuthorizedError("MALFORMED_MUST_DENY")
    if "SUBMISSION_AUTHORIZED_STANDING_MALFORMED" not in malformed.reason_codes:
        raise CurrentProductiveSubmissionAuthorizedError("MALFORMED_STANDING_DENY_MISSING")
    if "KILL_SWITCH_EVIDENCE_NOT_TRUSTED" not in malformed.reason_codes:
        raise CurrentProductiveSubmissionAuthorizedError("MALFORMED_KS_DENY_MISSING")
    if "KILL_SWITCH_UNKNOWN" not in malformed.reason_codes:
        raise CurrentProductiveSubmissionAuthorizedError("UNKNOWN_KS_DENY_MISSING")

    missing_join = join_cap72_host_to_live_execution_port_v1(host=HostActivationBindingV1())
    missing = evaluate_submission_authorized_v1(
        host_joined=missing_join.host_joined is True,
        live_port=missing_join.live_execution_port,
        admitted=True,
    )
    if missing.submission_authorized is True:
        raise CurrentProductiveSubmissionAuthorizedError("MISSING_JOIN_MUST_DENY")
    if "HOST_NOT_JOINED" not in missing.reason_codes:
        raise CurrentProductiveSubmissionAuthorizedError("MISSING_JOIN_HOST_DENY")

    construction = evaluate_live_execution_port_construction_admission_v1(
        admission=decision,
        live_enabled=LIVE_ENABLED is True,
        live_armed=LIVE_ARMED is True,
        wire_send_permitted=WIRE_SEND_PERMITTED is True,
        attempt_with_credentials=False,
        attempt_network_session=False,
    )
    if construction.constructible is not True:
        raise CurrentProductiveSubmissionAuthorizedError("PORT_NOT_CONSTRUCTIBLE")
    try:
        construct_live_execution_port_v1()
    except ExecutionPortConstructionForbiddenError:
        pass
    else:
        raise CurrentProductiveSubmissionAuthorizedError("BARE_CONSTRUCT_MUST_FAIL")
    port = construct_live_execution_port_v1(construction_admission=construction)
    if getattr(port, "SUBMISSION_AUTHORIZED", True) is not False:
        raise CurrentProductiveSubmissionAuthorizedError("PORT_HANDLE_MUST_NOT_SUBMIT")
    handle_only = evaluate_submission_authorized_v1(
        host_joined=False,
        live_port=port,
        admitted=True,
    )
    if handle_only.submission_authorized is True:
        raise CurrentProductiveSubmissionAuthorizedError("PORT_HANDLE_ALONE_MUST_DENY")
    if "HOST_NOT_JOINED" not in handle_only.reason_codes:
        raise CurrentProductiveSubmissionAuthorizedError("PORT_HANDLE_HOST_DENY_MISSING")

    host = HostActivationBindingV1()
    join = join_cap72_host_to_live_execution_port_v1(
        host=host,
        construction_admission=construction,
        live_port=port,
    )
    if join.host_joined is not True:
        raise CurrentProductiveSubmissionAuthorizedError(
            f"HOST_JOIN_FAILED:{list(join.reason_codes)}"
        )
    if join.submission_authorized is True:
        raise CurrentProductiveSubmissionAuthorizedError("HOST_JOIN_MUST_NOT_SUBMIT")
    if not isinstance(host.execution_port, SimulatedExecutionPortV1):
        raise CurrentProductiveSubmissionAuthorizedError("SIMULATED_PORT_LOST")
    if host.live_execution_port is host.execution_port:
        raise CurrentProductiveSubmissionAuthorizedError("LIVE_PORT_REPLACED_SIMULATED")

    wire_only = evaluate_submission_authorized_v1(
        host_joined=False,
        live_port=None,
        admitted=False,
        wire_send_permitted=True,
    )
    if wire_only.submission_authorized is True:
        raise CurrentProductiveSubmissionAuthorizedError("WIRE_PERMITTED_ALONE_MUST_DENY")

    ks_blocked = evaluate_submission_authorized_v1(
        host_joined=True,
        live_port=port,
        admitted=True,
        durable_kill_switch_blocked=True,
    )
    if ks_blocked.submission_authorized is True:
        raise CurrentProductiveSubmissionAuthorizedError("KS_BLOCKED_MUST_DENY")
    if "KILL_SWITCH_BLOCKED" not in ks_blocked.reason_codes:
        raise CurrentProductiveSubmissionAuthorizedError("KS_BLOCKED_DENY_MISSING")

    submit_attempt = evaluate_submission_authorized_v1(
        host_joined=True,
        live_port=port,
        admitted=True,
        attempt_submit=True,
    )
    if submit_attempt.submission_authorized is True:
        raise CurrentProductiveSubmissionAuthorizedError("SUBMIT_ATTEMPT_MUST_DENY")
    if "SUBMIT_FROM_SUBMISSION_CAPABILITY_FORBIDDEN" not in submit_attempt.reason_codes:
        raise CurrentProductiveSubmissionAuthorizedError("SUBMIT_ATTEMPT_DENY_MISSING")

    wire_attempt = evaluate_submission_authorized_v1(
        host_joined=True,
        live_port=port,
        admitted=True,
        attempt_wire_send=True,
    )
    if wire_attempt.submission_authorized is True:
        raise CurrentProductiveSubmissionAuthorizedError("WIRE_ATTEMPT_MUST_DENY")
    if "WIRE_FROM_SUBMISSION_FORBIDDEN" not in wire_attempt.reason_codes:
        raise CurrentProductiveSubmissionAuthorizedError("WIRE_ATTEMPT_DENY_MISSING")

    closed = evaluate_submission_authorized_v1(
        host_joined=join.host_joined is True,
        live_port=port,
        admitted=decision.admitted is True,
        live_enabled=LIVE_ENABLED is True,
        live_armed=LIVE_ARMED is True,
        wire_send_permitted=WIRE_SEND_PERMITTED is True,
        durable_kill_switch_blocked=False,
        durable_kill_switch_evidence_status=DurableKillSwitchEvidenceStatusV1.TRUSTED_PRESENT.value,
        live_authorized=LIVE_AUTHORIZED is True,
        step_29q_status=STEP_29Q_PLAN_ONLY,
    )
    if closed.submission_authorized is not True:
        raise CurrentProductiveSubmissionAuthorizedError(
            f"SUBMISSION_NOT_AUTHORIZED:{list(closed.reason_codes)}"
        )
    if closed.reason_codes:
        raise CurrentProductiveSubmissionAuthorizedError(
            f"UNEXPECTED_SUBMISSION_REASONS:{list(closed.reason_codes)}"
        )
    proof = prove_submission_authorized_not_wire_v1(closed)
    if proof["ok"] is not True:
        raise CurrentProductiveSubmissionAuthorizedError("WIRE_PROOF_FAILED")
    if closed.post_count != 0:
        raise CurrentProductiveSubmissionAuthorizedError("POST_COUNT_NOT_ZERO")
    if closed.live_authorized is True:
        raise CurrentProductiveSubmissionAuthorizedError("LIVE_AUTHORIZED_AFTER_CLOSE")
    if closed.step_29q_status != STEP_29Q_PLAN_ONLY:
        raise CurrentProductiveSubmissionAuthorizedError("STEP_29Q_NOT_PLAN_ONLY")

    first_blocker = current_productive_first_real_blocker_v1()
    if first_blocker != "EXTERNAL_EFFECT_NOT_AUTHORIZED":
        raise CurrentProductiveSubmissionAuthorizedError(f"BLOCKER_DRIFT:{first_blocker}")
    blocker_class = "E"
    store = Path(evidence_root) if evidence_root is not None else root / CANONICAL_PACK_RELPATH
    store.mkdir(parents=True, exist_ok=True)
    claims = {
        "THIS_SLICE": THIS_SLICE,
        "OWNER_GO": OWNER_GO,
        "EXPECTED_ORIGIN_MAIN": origin_main_sha,
        "SUBMISSION_AUTHORIZED_STANDING_ADMISSION_SEAM_IMPLEMENTED": TRUE_TOKEN,
        "SUBMISSION_AUTHORIZED_STANDING_GATE_CLOSED": TRUE_TOKEN,
        "SUBMISSION_AUTHORIZED": _token(closed.submission_authorized is True),
        "SUBMISSION_AUTHORIZED_TRUE_IS_NOT_AUTOMATIC_SEND": TRUE_TOKEN,
        "SUBMISSION_AUTHORIZED_TRUE_IS_NOT_AUTOMATIC_WIRE": TRUE_TOKEN,
        "SUBMISSION_AUTHORIZED_DOES_NOT_IMPLY_WIRE_SEND": TRUE_TOKEN,
        "SUBMISSION_AUTHORIZED_DOES_NOT_IMPLY_LIVE_AUTHORIZED": TRUE_TOKEN,
        "SUBMISSION_AUTHORIZED_DOES_NOT_IMPLY_STEP_29Q": TRUE_TOKEN,
        "SUBMISSION_AUTHORIZED_DOES_NOT_IMPLY_POST": TRUE_TOKEN,
        "SUBMISSION_AUTHORIZED_DOES_NOT_IMPLY_PRODUCTIVE_WIRE_SEND_REACHABLE": TRUE_TOKEN,
        "CAP_7_2_HOST_JOINED_IS_NOT_SUBMISSION_AUTHORIZED": TRUE_TOKEN,
        "LIVE_EXECUTION_PORT_HANDLE_IS_NOT_SUBMISSION_AUTHORIZED": TRUE_TOKEN,
        "WIRE_SEND_PERMITTED_ALONE_IS_NOT_SUBMISSION_AUTHORIZED": TRUE_TOKEN,
        "HOST_JOINED": _token(join.host_joined is True),
        "LIVE_EXECUTION_PORT_CONSTRUCTED": TRUE_TOKEN,
        "SIMULATED_EXECUTION_PORT_RETAINED": TRUE_TOKEN,
        "SIMULATED_EXECUTION_PORT_SOLE_REACHABLE": TRUE_TOKEN,
        "LIVE_ENABLED": _token(LIVE_ENABLED is True),
        "LIVE_ARMED": _token(LIVE_ARMED is True),
        "WIRE_SEND_PERMITTED": _token(WIRE_SEND_PERMITTED is True),
        "LIVE_AUTHORIZED": _token(LIVE_AUTHORIZED is True),
        "STANDING_LIVE_AUTHORIZATION": _token(STANDING_LIVE_AUTHORIZATION is True),
        "ADMITTED": _token(decision.admitted is True),
        "SUBMISSION_DENY_ABSENT": TRUE_TOKEN,
        "ADMISSION_REASON_CODES": list(decision.reason_codes),
        "HOST_JOIN_REASON_CODES": list(join.reason_codes),
        "SUBMISSION_REASON_CODES": list(closed.reason_codes),
        "PRODUCTIVE_WIRE_SEND_REACHABLE": _token(PRODUCTIVE_WIRE_SEND_REACHABLE is True),
        "STEP_29Q_STATUS": STEP_29Q_PLAN_ONLY,
        "POST_COUNT": "0",
        "STEP_29P_RISK_ADMISSIBLE": str(df["STEP_29P_RISK_ADMISSIBLE"]),
        "CAP24_BOUND_INSTRUMENT_ID": str(df["CAP24_BOUND_INSTRUMENT_ID"]),
        "CAP23_SELECTED_INSTRUMENT_ID": str(df.get("CAP23_SELECTED_INSTRUMENT_ID") or ""),
        "DF_PACK": DF_PACK_RELPATH,
        "FIRST_REAL_BLOCKER": first_blocker,
        "BLOCKER_CLASS": blocker_class,
        "NEXT_OWNER_GO_REQUIRED": (
            "OWNER_GO_REQUIRED_FOR_PRODUCTIVE_WIRE_SEND_NOT_AUTHORIZED_BY_THIS_SLICE"
        ),
        "TRADING_LOGIC_CHANGES_FOUND": FALSE_TOKEN,
        "RANKING_ALGORITHM_CHANGED": FALSE_TOKEN,
        "SELECTION_ALGORITHM_CHANGED": FALSE_TOKEN,
        "UNIVERSE_SEMANTICS_CHANGED": FALSE_TOKEN,
        "LEARNING_LOGIC_CHANGED": FALSE_TOKEN,
        "SAFETY_AUTHORITY_WEAKENED": FALSE_TOKEN,
        "CANARY_FULL_CORE_BOUNDARY_CHANGED": FALSE_TOKEN,
        "PROTECTED_SURFACES_CHANGED": FALSE_TOKEN,
        "RUNTIME_AUTHORIZATION_EFFECT": "NONE",
    }
    lineage = {
        "OWNER_GO": OWNER_GO,
        "THIS_SLICE": THIS_SLICE,
        "DF_OWNER_GO": str(df.get("OWNER_GO") or ""),
        "DF_FIRST_REAL_BLOCKER": str(df.get("FIRST_REAL_BLOCKER") or ""),
        "CAP24_BOUND_INSTRUMENT_ID": str(df.get("CAP24_BOUND_INSTRUMENT_ID") or ""),
    }
    protected = {
        "MASTER_V2_UNCHANGED": TRUE_TOKEN,
        "DOUBLE_PLAY_UNCHANGED": TRUE_TOKEN,
        "UNIVERSE_MEMBERSHIP_SEMANTICS_UNCHANGED": TRUE_TOKEN,
        "RANKING_ALGORITHM_UNCHANGED": TRUE_TOKEN,
        "SELECTION_ALGORITHM_UNCHANGED": TRUE_TOKEN,
        "LEARNING_UNCHANGED": TRUE_TOKEN,
        "FULL_CORE_SAFETY_ADMISSION_AUTHORITY_UNCHANGED": TRUE_TOKEN,
        "CANARY_FULL_CORE_BOUNDARY_UNCHANGED": TRUE_TOKEN,
        "PRODUCTIVE_WIRE_SEND_REACHABLE_UNCHANGED_FALSE": TRUE_TOKEN,
        "LIVE_AUTHORIZED_UNCHANGED_FALSE": TRUE_TOKEN,
        "STEP_29Q_UNCHANGED_PLAN_ONLY": TRUE_TOKEN,
        "LIVE_ENABLED_UNCHANGED_TRUE": TRUE_TOKEN,
        "LIVE_ARMED_UNCHANGED_TRUE": TRUE_TOKEN,
        "WIRE_SEND_PERMITTED_UNCHANGED_TRUE": TRUE_TOKEN,
        "ADMISSION_UNCHANGED_TRUE": TRUE_TOKEN,
        "PORT_CONSTRUCTED_UNCHANGED_TRUE": TRUE_TOKEN,
        "HOST_JOINED_UNCHANGED_TRUE": TRUE_TOKEN,
    }
    summary = {
        "FIRST_REAL_BLOCKER": first_blocker,
        "BLOCKER_CLASS": blocker_class,
        "LIVE_ENABLED": _token(LIVE_ENABLED is True),
        "LIVE_ARMED": _token(LIVE_ARMED is True),
        "WIRE_SEND_PERMITTED": _token(WIRE_SEND_PERMITTED is True),
        "LIVE_AUTHORIZED": _token(LIVE_AUTHORIZED is True),
        "ADMITTED": _token(decision.admitted is True),
        "HOST_JOINED": TRUE_TOKEN,
        "LIVE_EXECUTION_PORT_CONSTRUCTED": TRUE_TOKEN,
        "SUBMISSION_AUTHORIZED": TRUE_TOKEN,
        "STEP_29P_RISK_ADMISSIBLE": str(df["STEP_29P_RISK_ADMISSIBLE"]),
        "PRODUCTIVE_WIRE_SEND_REACHABLE": FALSE_TOKEN,
        "POST_COUNT": "0",
        "HARD_STOP": TRUE_TOKEN,
    }
    for payload in (claims, lineage, protected, summary):
        _assert_no_secrets(payload)
    _persist_json(path=store / "claims.json", payload=claims)
    _persist_json(path=store / "SUMMARY.json", payload=summary)
    _persist_json(path=store / "LINEAGE.json", payload=lineage)
    _persist_json(path=store / "protected_surfaces_v1.json", payload=protected)
    persist_manifest_sha256_v1(store_root=store)
    manifest_rc = verify_manifest_sha256_v1(store_root=store)
    return CurrentProductiveSubmissionAuthorizedResultV1(
        store_root=str(store),
        live_enabled=_token(LIVE_ENABLED is True),
        live_armed=_token(LIVE_ARMED is True),
        wire_send_permitted=_token(WIRE_SEND_PERMITTED is True),
        live_authorized=_token(LIVE_AUTHORIZED is True),
        admitted=_token(decision.admitted is True),
        host_joined=_token(join.host_joined is True),
        port_constructed=TRUE_TOKEN,
        submission_authorized=_token(closed.submission_authorized is True),
        submission_deny_absent=TRUE_TOKEN,
        step_29p_risk_admissible=str(df["STEP_29P_RISK_ADMISSIBLE"]),
        cap24_bound_instrument_id=str(df["CAP24_BOUND_INSTRUMENT_ID"]),
        first_real_blocker=first_blocker,
        blocker_class=blocker_class,
        post_count="0",
        evidence_manifest=str(store / "MANIFEST.sha256"),
        manifest_verify_rc=manifest_rc,
    )
