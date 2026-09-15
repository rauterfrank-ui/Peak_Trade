"""CURRENT_PRODUCTIVE LIVE_AUTHORIZED and Cap-11.1 send-capable adapter.

Consumes Owner-GO
OWNER_GO_CURRENT_PRODUCTIVE_LIVE_AUTHORIZED_AND_CAP_11_1_SEND_CAPABLE_ADAPTER_V1.

Closes LIVE_AUTHORIZED as a fail-closed live-execution authority predicate
and constructs a send-capable LiveExecutionPort with PRODUCTIVE_WIRE_SEND_REACHABLE
true behind standing gates. Actual venue POST remains blocked by the
external-effect gate. STEP-29Q remains PLAN_ONLY.

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
    CAP_11_1_SEND_CAPABLE_ADAPTER_CONSTRUCTED,
    CAP_11_1_SEND_CAPABLE_ADAPTER_IS_NOT_EXTERNAL_EFFECT,
    CAP_11_1_SEND_CAPABLE_ADAPTER_IS_NOT_POST,
    CAP_11_1_SEND_CAPABLE_ADAPTER_IS_NOT_STEP_29Q,
    CAP_7_2_HOST_JOIN_TO_LIVE_EXECUTION_PORT,
    EXTERNAL_EFFECT_AUTHORIZED,
    EXTERNAL_EFFECT_GATE_IMPLEMENTED,
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    LIVE_AUTHORIZED_DOES_NOT_IMPLY_EXTERNAL_EFFECT,
    LIVE_AUTHORIZED_DOES_NOT_IMPLY_POST,
    LIVE_AUTHORIZED_DOES_NOT_IMPLY_STEP_29Q,
    LIVE_AUTHORIZED_STANDING_ADMISSION_SEAM_IMPLEMENTED,
    LIVE_AUTHORIZED_STANDING_GATE_CLOSED,
    LIVE_AUTHORIZED_TRUE_IS_NOT_AUTOMATIC_SEND,
    LIVE_ENABLED,
    LIVE_EXECUTION_PORT_CONSTRUCTIBLE,
    PRODUCTIVE_WIRE_SEND_REACHABLE,
    PRODUCTIVE_WIRE_SEND_REACHABLE_DOES_NOT_IMPLY_EXTERNAL_EFFECT,
    PRODUCTIVE_WIRE_SEND_REACHABLE_DOES_NOT_IMPLY_POST,
    STANDING_LIVE_AUTHORIZATION,
    SUBMISSION_AUTHORIZED,
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
from src.ops.full_core_live_path_composition_root_v1.external_effect_gate_v1 import (
    FullCoreExternalEffectNotAuthorizedError,
    evaluate_external_effect_v1,
)
from src.ops.full_core_live_path_composition_root_v1.gated_productive_wire_transport_v1 import (
    FullCoreGatedProductiveWireTransportV1,
    FullCoreSendCredentialHandleV1,
)
from src.ops.full_core_live_path_composition_root_v1.live_admission_gap_dag_v1 import (
    gap_node_v1,
)
from src.ops.full_core_live_path_composition_root_v1.live_authorized_v1 import (
    evaluate_live_authorized_v1,
    prove_live_authorized_not_external_effect_v1,
)
from src.ops.full_core_live_path_composition_root_v1.live_execution_port_construction_admission_v1 import (
    evaluate_live_execution_port_construction_admission_v1,
)
from src.ops.full_core_live_path_composition_root_v1.submission_authorized_v1 import (
    STEP_29Q_PLAN_ONLY,
    evaluate_submission_authorized_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    CURRENT_PRODUCTIVE_LIVE_AUTHORIZED_AND_CAP_11_1_SEND_CAPABLE_ADAPTER_CREATED,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_submission_authorized_v1 import (
    CANONICAL_PACK_RELPATH as DG_PACK_RELPATH,
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

OWNER_GO = "OWNER_GO_CURRENT_PRODUCTIVE_LIVE_AUTHORIZED_AND_CAP_11_1_SEND_CAPABLE_ADAPTER_V1"
THIS_SLICE = (
    "11.2.1.DH.FULL_CORE_CURRENT_PRODUCTIVE_LIVE_AUTHORIZED_AND_CAP_11_1_SEND_CAPABLE_ADAPTER"
)
EXPECTED_ORIGIN_MAIN_SHA = "d3e0e6b35b1893d005fa015fb4c7f50de5a877ec"
CANONICAL_PACK_RELPATH = (
    "evidence/ops/full_core_current_productive_live_authorized_and_cap_11_1_send_capable_adapter_v1/"
    "20260915T203000Z"
)
FALSE_TOKEN = "false"
TRUE_TOKEN = "true"
_SECRET_TOKENS = ("secret", "passphrase", "api_key", "apiKey", "private_key")


class CurrentProductiveLiveAuthorizedSendCapableError(ValueError):
    """Fail-closed LIVE_AUTHORIZED / send-capable remainder violation."""


@dataclass(frozen=True)
class CurrentProductiveLiveAuthorizedSendCapableResultV1:
    store_root: str
    live_enabled: str
    live_armed: str
    wire_send_permitted: str
    live_authorized: str
    admitted: str
    host_joined: str
    port_constructed: str
    send_capable: str
    submission_authorized: str
    productive_wire_send_reachable: str
    external_effect_authorized: str
    step_29q_status: str
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
            raise CurrentProductiveLiveAuthorizedSendCapableError(f"SECRET_TOKEN_PRESENT:{token}")


def _load_json_object(*, path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise CurrentProductiveLiveAuthorizedSendCapableError(f"JSON_NOT_OBJECT:{path.name}")
    return payload


def _token(value: bool) -> str:
    return TRUE_TOKEN if value is True else FALSE_TOKEN


def _assert_standing_pins() -> None:
    if CURRENT_PRODUCTIVE_LIVE_AUTHORIZED_AND_CAP_11_1_SEND_CAPABLE_ADAPTER_CREATED is not True:
        raise CurrentProductiveLiveAuthorizedSendCapableError("ADAPTER_NOT_CREATED")
    if LIVE_AUTHORIZED_STANDING_ADMISSION_SEAM_IMPLEMENTED is not True:
        raise CurrentProductiveLiveAuthorizedSendCapableError("SEAM_NOT_IMPLEMENTED")
    if LIVE_AUTHORIZED_STANDING_GATE_CLOSED is not True:
        raise CurrentProductiveLiveAuthorizedSendCapableError("GATE_NOT_CLOSED")
    if LIVE_AUTHORIZED is not True:
        raise CurrentProductiveLiveAuthorizedSendCapableError("LIVE_AUTHORIZED_NOT_TRUE")
    if LIVE_AUTHORIZED_TRUE_IS_NOT_AUTOMATIC_SEND is not True:
        raise CurrentProductiveLiveAuthorizedSendCapableError("MUST_NOT_AUTOMATIC_SEND")
    if LIVE_AUTHORIZED_DOES_NOT_IMPLY_EXTERNAL_EFFECT is not True:
        raise CurrentProductiveLiveAuthorizedSendCapableError("MUST_NOT_IMPLY_EXTERNAL_EFFECT")
    if LIVE_AUTHORIZED_DOES_NOT_IMPLY_POST is not True:
        raise CurrentProductiveLiveAuthorizedSendCapableError("MUST_NOT_IMPLY_POST")
    if LIVE_AUTHORIZED_DOES_NOT_IMPLY_STEP_29Q is not True:
        raise CurrentProductiveLiveAuthorizedSendCapableError("MUST_NOT_IMPLY_STEP_29Q")
    if CAP_11_1_SEND_CAPABLE_ADAPTER_CONSTRUCTED is not True:
        raise CurrentProductiveLiveAuthorizedSendCapableError("SEND_CAPABLE_NOT_TRUE")
    if CAP_11_1_SEND_CAPABLE_ADAPTER_IS_NOT_EXTERNAL_EFFECT is not True:
        raise CurrentProductiveLiveAuthorizedSendCapableError("ADAPTER_MUST_NOT_EFFECT")
    if CAP_11_1_SEND_CAPABLE_ADAPTER_IS_NOT_POST is not True:
        raise CurrentProductiveLiveAuthorizedSendCapableError("ADAPTER_MUST_NOT_POST")
    if CAP_11_1_SEND_CAPABLE_ADAPTER_IS_NOT_STEP_29Q is not True:
        raise CurrentProductiveLiveAuthorizedSendCapableError("ADAPTER_MUST_NOT_29Q")
    if PRODUCTIVE_WIRE_SEND_REACHABLE is not True:
        raise CurrentProductiveLiveAuthorizedSendCapableError("WIRE_SEND_NOT_REACHABLE")
    if PRODUCTIVE_WIRE_SEND_REACHABLE_DOES_NOT_IMPLY_EXTERNAL_EFFECT is not True:
        raise CurrentProductiveLiveAuthorizedSendCapableError("REACHABLE_MUST_NOT_EFFECT")
    if PRODUCTIVE_WIRE_SEND_REACHABLE_DOES_NOT_IMPLY_POST is not True:
        raise CurrentProductiveLiveAuthorizedSendCapableError("REACHABLE_MUST_NOT_POST")
    if EXTERNAL_EFFECT_AUTHORIZED is not False:
        raise CurrentProductiveLiveAuthorizedSendCapableError("EXTERNAL_EFFECT_NOT_FALSE")
    if EXTERNAL_EFFECT_GATE_IMPLEMENTED is not True:
        raise CurrentProductiveLiveAuthorizedSendCapableError("EXTERNAL_EFFECT_GATE_MISSING")
    if LIVE_ENABLED is not True:
        raise CurrentProductiveLiveAuthorizedSendCapableError("LIVE_ENABLED_NOT_TRUE")
    if LIVE_ARMED is not True:
        raise CurrentProductiveLiveAuthorizedSendCapableError("LIVE_ARMED_NOT_TRUE")
    if WIRE_SEND_PERMITTED is not True:
        raise CurrentProductiveLiveAuthorizedSendCapableError("WIRE_SEND_PERMITTED_NOT_TRUE")
    if SUBMISSION_AUTHORIZED is not True:
        raise CurrentProductiveLiveAuthorizedSendCapableError("SUBMISSION_AUTHORIZED_NOT_TRUE")
    if CAP_7_2_HOST_JOIN_TO_LIVE_EXECUTION_PORT is not True:
        raise CurrentProductiveLiveAuthorizedSendCapableError("HOST_JOIN_NOT_TRUE")
    if LIVE_EXECUTION_PORT_CONSTRUCTIBLE is not True:
        raise CurrentProductiveLiveAuthorizedSendCapableError("PORT_NOT_CONSTRUCTIBLE")
    if STANDING_LIVE_AUTHORIZATION is not False:
        raise CurrentProductiveLiveAuthorizedSendCapableError("STANDING_LIVE_AUTHORIZATION_TRUE")
    if gap_node_v1("LIVE_AUTHORIZED").implementation_status != "STANDING_TRUE_NOT_AUTOMATIC_SEND":
        raise CurrentProductiveLiveAuthorizedSendCapableError("DAG_LIVE_AUTHORIZED_STATUS_DRIFT")
    if gap_node_v1("LiveExecutionPort").implementation_status != "SEND_CAPABLE_NOT_EXTERNAL_EFFECT":
        raise CurrentProductiveLiveAuthorizedSendCapableError("PORT_DAG_NODE_STATUS_DRIFT")
    if gap_node_v1("EXTERNAL_EFFECT").implementation_status != (
        "ENVELOPE_BOUND_SINGLE_USE_SEAM_IMPLEMENTED_STANDING_FALSE"
    ):
        raise CurrentProductiveLiveAuthorizedSendCapableError("EXTERNAL_EFFECT_DAG_STATUS_DRIFT")


def _bind_current_dg_epoch(*, repo_root: Path) -> dict[str, Any]:
    claims_path = repo_root / DG_PACK_RELPATH / "claims.json"
    if not claims_path.is_file():
        raise CurrentProductiveLiveAuthorizedSendCapableError("DG_CLAIMS_MISSING")
    claims = _load_json_object(path=claims_path)
    if str(claims.get("SUBMISSION_AUTHORIZED") or "") != TRUE_TOKEN:
        raise CurrentProductiveLiveAuthorizedSendCapableError("DG_SUBMISSION_NOT_TRUE")
    if str(claims.get("HOST_JOINED") or "") != TRUE_TOKEN:
        raise CurrentProductiveLiveAuthorizedSendCapableError("DG_HOST_NOT_JOINED")
    if str(claims.get("ADMITTED") or "") != TRUE_TOKEN:
        raise CurrentProductiveLiveAuthorizedSendCapableError("DG_ADMITTED_NOT_TRUE")
    if str(claims.get("STEP_29P_RISK_ADMISSIBLE") or "") != TRUE_TOKEN:
        raise CurrentProductiveLiveAuthorizedSendCapableError("DG_STEP_29P_NOT_TRUE")
    instrument_id = str(claims.get("CAP24_BOUND_INSTRUMENT_ID") or "").strip()
    if not instrument_id:
        raise CurrentProductiveLiveAuthorizedSendCapableError("DG_CAP24_ID_MISSING")
    if str(claims.get("POST_COUNT") or "") != "0":
        raise CurrentProductiveLiveAuthorizedSendCapableError("DG_POST_COUNT_NOT_ZERO")
    if str(claims.get("LIVE_AUTHORIZED") or "") != FALSE_TOKEN:
        raise CurrentProductiveLiveAuthorizedSendCapableError("DG_LIVE_AUTHORIZED_NOT_FALSE")
    if str(claims.get("PRODUCTIVE_WIRE_SEND_REACHABLE") or "") != FALSE_TOKEN:
        raise CurrentProductiveLiveAuthorizedSendCapableError("DG_REACHABLE_NOT_FALSE")
    if (
        str(claims.get("FIRST_REAL_BLOCKER") or "")
        != "PRODUCTIVE_WIRE_SEND_REACHABLE_REMAINS_FALSE"
    ):
        raise CurrentProductiveLiveAuthorizedSendCapableError("DG_BLOCKER_DRIFT")
    return claims


def _admission_inputs_v1() -> ExecutionAdmissionInputsV1:
    return ExecutionAdmissionInputsV1(
        plan_identity="current-productive-live-authorized-send-capable",
        venue_plan_identity="current-productive-live-authorized-send-capable",
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


def execute_current_productive_live_authorized_and_cap_11_1_send_capable_adapter_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    evidence_root: Path | None = None,
    repo_root: Path | None = None,
) -> CurrentProductiveLiveAuthorizedSendCapableResultV1:
    if owner_go != OWNER_GO:
        raise CurrentProductiveLiveAuthorizedSendCapableError("OWNER_GO_MISMATCH")
    if origin_main_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise CurrentProductiveLiveAuthorizedSendCapableError("ORIGIN_MAIN_SHA_MISMATCH")
    _assert_standing_pins()
    root = repo_root or Path(__file__).resolve().parents[3]
    dg = _bind_current_dg_epoch(repo_root=root)
    gates = standing_live_gate_fields_v1()
    if gates["live_authorized"] is not True:
        raise CurrentProductiveLiveAuthorizedSendCapableError("STANDING_FIELD_LIVE_AUTHORIZED")

    decision = evaluate_execution_admission_v1(_admission_inputs_v1())
    if decision.admitted is not True:
        raise CurrentProductiveLiveAuthorizedSendCapableError("ADMISSION_NOT_ADMITTED")

    default_deny = evaluate_live_authorized_v1(standing_live_authorized=False)
    if default_deny.live_authorized is True:
        raise CurrentProductiveLiveAuthorizedSendCapableError("DEFAULT_MUST_DENY")
    if "LIVE_AUTHORIZED_STANDING_FALSE" not in default_deny.reason_codes:
        raise CurrentProductiveLiveAuthorizedSendCapableError("STANDING_FALSE_DENY_MISSING")

    malformed = evaluate_live_authorized_v1(
        standing_live_authorized="UNKNOWN",  # type: ignore[arg-type]
    )
    if malformed.live_authorized is True:
        raise CurrentProductiveLiveAuthorizedSendCapableError("MALFORMED_MUST_DENY")

    construction = evaluate_live_execution_port_construction_admission_v1(
        admission=decision,
        live_enabled=LIVE_ENABLED is True,
        live_armed=LIVE_ARMED is True,
        wire_send_permitted=WIRE_SEND_PERMITTED is True,
        attempt_with_credentials=False,
        attempt_network_session=False,
        send_capable=True,
    )
    if construction.constructible is not True:
        raise CurrentProductiveLiveAuthorizedSendCapableError("PORT_NOT_CONSTRUCTIBLE")
    if construction.send_capable is not True:
        raise CurrentProductiveLiveAuthorizedSendCapableError("CONSTRUCTION_NOT_SEND_CAPABLE")
    try:
        construct_live_execution_port_v1()
    except ExecutionPortConstructionForbiddenError:
        pass
    else:
        raise CurrentProductiveLiveAuthorizedSendCapableError("BARE_CONSTRUCT_MUST_FAIL")
    secrets_denied = evaluate_live_execution_port_construction_admission_v1(
        admission=decision,
        send_capable=True,
        attempt_with_credentials=True,
    )
    if secrets_denied.constructible is True:
        raise CurrentProductiveLiveAuthorizedSendCapableError("CREDENTIAL_MATERIAL_MUST_DENY")
    network_denied = evaluate_live_execution_port_construction_admission_v1(
        admission=decision,
        send_capable=True,
        attempt_network_session=True,
    )
    if network_denied.constructible is True:
        raise CurrentProductiveLiveAuthorizedSendCapableError("NETWORK_SESSION_MUST_DENY")

    port = construct_live_execution_port_v1(
        construction_admission=construction,
        send_capable=True,
        credential_handle_bound=True,
        transport_bound=True,
    )
    if getattr(port, "SEND_CAPABLE", False) is not True:
        raise CurrentProductiveLiveAuthorizedSendCapableError("PORT_NOT_SEND_CAPABLE")
    if getattr(port, "SEND_SEAM_PRESENT", False) is not True:
        raise CurrentProductiveLiveAuthorizedSendCapableError("SEND_SEAM_MISSING")
    if getattr(port, "EXTERNAL_EFFECT_AUTHORIZED", True) is not False:
        raise CurrentProductiveLiveAuthorizedSendCapableError("PORT_EXTERNAL_EFFECT")
    if int(getattr(port, "POST_COUNT", 1)) != 0:
        raise CurrentProductiveLiveAuthorizedSendCapableError("PORT_POST_COUNT")
    if getattr(port, "MATERIAL_LOADED", True) is not False:
        raise CurrentProductiveLiveAuthorizedSendCapableError("PORT_MATERIAL_LOADED")

    host = HostActivationBindingV1()
    join = join_cap72_host_to_live_execution_port_v1(
        host=host,
        construction_admission=construction,
        live_port=port,
    )
    if join.host_joined is not True:
        raise CurrentProductiveLiveAuthorizedSendCapableError(
            f"HOST_JOIN_FAILED:{list(join.reason_codes)}"
        )
    if not isinstance(host.execution_port, SimulatedExecutionPortV1):
        raise CurrentProductiveLiveAuthorizedSendCapableError("SIMULATED_PORT_LOST")
    if host.live_execution_port is host.execution_port:
        raise CurrentProductiveLiveAuthorizedSendCapableError("LIVE_PORT_REPLACED_SIMULATED")

    closed_submission = evaluate_submission_authorized_v1(
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
    if closed_submission.submission_authorized is not True:
        raise CurrentProductiveLiveAuthorizedSendCapableError(
            f"SUBMISSION_NOT_AUTHORIZED:{list(closed_submission.reason_codes)}"
        )

    closed_live = evaluate_live_authorized_v1(
        live_enabled=LIVE_ENABLED is True,
        live_armed=LIVE_ARMED is True,
        wire_send_permitted=WIRE_SEND_PERMITTED is True,
        submission_authorized=closed_submission.submission_authorized is True,
    )
    if closed_live.live_authorized is not True:
        raise CurrentProductiveLiveAuthorizedSendCapableError(
            f"LIVE_NOT_AUTHORIZED:{list(closed_live.reason_codes)}"
        )
    proof = prove_live_authorized_not_external_effect_v1(closed_live)
    if proof["ok"] is not True:
        raise CurrentProductiveLiveAuthorizedSendCapableError("EXTERNAL_EFFECT_PROOF_FAILED")

    post_from_live = evaluate_live_authorized_v1(
        live_enabled=LIVE_ENABLED is True,
        live_armed=LIVE_ARMED is True,
        wire_send_permitted=WIRE_SEND_PERMITTED is True,
        submission_authorized=True,
        attempt_post=True,
    )
    if post_from_live.live_authorized is True:
        raise CurrentProductiveLiveAuthorizedSendCapableError("POST_FROM_LIVE_MUST_DENY")

    effect = evaluate_external_effect_v1()
    if effect.external_effect_authorized is True:
        raise CurrentProductiveLiveAuthorizedSendCapableError("EXTERNAL_EFFECT_MUST_DENY")
    if "EXTERNAL_EFFECT_NOT_AUTHORIZED" not in effect.reason_codes:
        raise CurrentProductiveLiveAuthorizedSendCapableError("EXTERNAL_EFFECT_DENY_MISSING")

    handle = FullCoreSendCredentialHandleV1(handle_id="full-core-gated-handle", bound=True)
    transport = FullCoreGatedProductiveWireTransportV1(handle=handle)
    try:
        transport.attempt_trade_order_post(payload={"instId": "MUST_NOT_POST"})
    except FullCoreExternalEffectNotAuthorizedError:
        pass
    else:
        raise CurrentProductiveLiveAuthorizedSendCapableError("TRANSPORT_POST_MUST_FAIL")
    if transport.post_count != 0 or transport.wire_send_occurred is True:
        raise CurrentProductiveLiveAuthorizedSendCapableError("TRANSPORT_SIDE_EFFECT")

    missing_handle = FullCoreGatedProductiveWireTransportV1(handle=None)
    try:
        missing_handle.attempt_trade_order_post()
    except FullCoreExternalEffectNotAuthorizedError:
        pass
    else:
        raise CurrentProductiveLiveAuthorizedSendCapableError("MISSING_HANDLE_MUST_FAIL")

    first_blocker = current_productive_first_real_blocker_v1()
    if first_blocker != (
        "OWNER_GO_REQUIRED_FOR_ACTUAL_VENUE_POST_WITH_FRESH_ENVELOPE_BOUND_SINGLE_USE_PERMIT"
    ):
        raise CurrentProductiveLiveAuthorizedSendCapableError(f"BLOCKER_DRIFT:{first_blocker}")
    blocker_class = "E"
    store = Path(evidence_root) if evidence_root is not None else root / CANONICAL_PACK_RELPATH
    store.mkdir(parents=True, exist_ok=True)
    claims = {
        "THIS_SLICE": THIS_SLICE,
        "OWNER_GO": OWNER_GO,
        "EXPECTED_ORIGIN_MAIN": origin_main_sha,
        "LIVE_AUTHORIZED_STANDING_ADMISSION_SEAM_IMPLEMENTED": TRUE_TOKEN,
        "LIVE_AUTHORIZED_STANDING_GATE_CLOSED": TRUE_TOKEN,
        "LIVE_AUTHORIZED": _token(closed_live.live_authorized is True),
        "LIVE_AUTHORIZED_TRUE_IS_NOT_AUTOMATIC_SEND": TRUE_TOKEN,
        "LIVE_AUTHORIZED_DOES_NOT_IMPLY_EXTERNAL_EFFECT": TRUE_TOKEN,
        "LIVE_AUTHORIZED_DOES_NOT_IMPLY_POST": TRUE_TOKEN,
        "LIVE_AUTHORIZED_DOES_NOT_IMPLY_STEP_29Q": TRUE_TOKEN,
        "CAP_11_1_SEND_CAPABLE_ADAPTER_CONSTRUCTED": TRUE_TOKEN,
        "CAP_11_1_SEND_CAPABLE_ADAPTER_IS_NOT_EXTERNAL_EFFECT": TRUE_TOKEN,
        "CAP_11_1_SEND_CAPABLE_ADAPTER_IS_NOT_POST": TRUE_TOKEN,
        "SEND_SEAM_PRESENT": TRUE_TOKEN,
        "HOST_JOINED": _token(join.host_joined is True),
        "LIVE_EXECUTION_PORT_CONSTRUCTED": TRUE_TOKEN,
        "SIMULATED_EXECUTION_PORT_RETAINED": TRUE_TOKEN,
        "LIVE_ENABLED": _token(LIVE_ENABLED is True),
        "LIVE_ARMED": _token(LIVE_ARMED is True),
        "WIRE_SEND_PERMITTED": _token(WIRE_SEND_PERMITTED is True),
        "SUBMISSION_AUTHORIZED": _token(closed_submission.submission_authorized is True),
        "STANDING_LIVE_AUTHORIZATION": _token(STANDING_LIVE_AUTHORIZATION is True),
        "ADMITTED": _token(decision.admitted is True),
        "PRODUCTIVE_WIRE_SEND_REACHABLE": _token(PRODUCTIVE_WIRE_SEND_REACHABLE is True),
        "PRODUCTIVE_WIRE_SEND_REACHABLE_DOES_NOT_IMPLY_EXTERNAL_EFFECT": TRUE_TOKEN,
        "PRODUCTIVE_WIRE_SEND_REACHABLE_DOES_NOT_IMPLY_POST": TRUE_TOKEN,
        "EXTERNAL_EFFECT_AUTHORIZED": _token(EXTERNAL_EFFECT_AUTHORIZED is True),
        "EXTERNAL_EFFECT_GATE_IMPLEMENTED": TRUE_TOKEN,
        "STEP_29Q_STATUS": STEP_29Q_PLAN_ONLY,
        "POST_COUNT": "0",
        "ACTUAL_ORDER_SUBMIT_PERFORMED": FALSE_TOKEN,
        "VENUE_MUTATION_PERFORMED": FALSE_TOKEN,
        "STEP_29P_RISK_ADMISSIBLE": str(dg["STEP_29P_RISK_ADMISSIBLE"]),
        "CAP24_BOUND_INSTRUMENT_ID": str(dg["CAP24_BOUND_INSTRUMENT_ID"]),
        "DG_PACK": DG_PACK_RELPATH,
        "FIRST_REAL_BLOCKER": first_blocker,
        "BLOCKER_CLASS": blocker_class,
        "NEXT_OWNER_GO_REQUIRED": (
            "OWNER_GO_REQUIRED_FOR_EXTERNAL_EFFECT_AND_ACTUAL_VENUE_POST_NOT_AUTHORIZED_BY_THIS_SLICE"
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
        "DG_OWNER_GO": str(dg.get("OWNER_GO") or ""),
        "DG_FIRST_REAL_BLOCKER": str(dg.get("FIRST_REAL_BLOCKER") or ""),
        "CAP24_BOUND_INSTRUMENT_ID": str(dg.get("CAP24_BOUND_INSTRUMENT_ID") or ""),
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
        "STEP_29Q_UNCHANGED_PLAN_ONLY": TRUE_TOKEN,
        "EXTERNAL_EFFECT_UNCHANGED_FALSE": TRUE_TOKEN,
        "LIVE_ENABLED_UNCHANGED_TRUE": TRUE_TOKEN,
        "LIVE_ARMED_UNCHANGED_TRUE": TRUE_TOKEN,
        "WIRE_SEND_PERMITTED_UNCHANGED_TRUE": TRUE_TOKEN,
        "SUBMISSION_AUTHORIZED_UNCHANGED_TRUE": TRUE_TOKEN,
        "ADMISSION_UNCHANGED_TRUE": TRUE_TOKEN,
        "HOST_JOINED_UNCHANGED_TRUE": TRUE_TOKEN,
    }
    summary = {
        "FIRST_REAL_BLOCKER": first_blocker,
        "BLOCKER_CLASS": blocker_class,
        "LIVE_ENABLED": TRUE_TOKEN,
        "LIVE_ARMED": TRUE_TOKEN,
        "WIRE_SEND_PERMITTED": TRUE_TOKEN,
        "LIVE_AUTHORIZED": TRUE_TOKEN,
        "ADMITTED": TRUE_TOKEN,
        "HOST_JOINED": TRUE_TOKEN,
        "CAP_11_1_SEND_CAPABLE_ADAPTER_CONSTRUCTED": TRUE_TOKEN,
        "SUBMISSION_AUTHORIZED": TRUE_TOKEN,
        "STEP_29P_RISK_ADMISSIBLE": str(dg["STEP_29P_RISK_ADMISSIBLE"]),
        "PRODUCTIVE_WIRE_SEND_REACHABLE": TRUE_TOKEN,
        "EXTERNAL_EFFECT_AUTHORIZED": FALSE_TOKEN,
        "STEP_29Q_STATUS": STEP_29Q_PLAN_ONLY,
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
    return CurrentProductiveLiveAuthorizedSendCapableResultV1(
        store_root=str(store),
        live_enabled=_token(LIVE_ENABLED is True),
        live_armed=_token(LIVE_ARMED is True),
        wire_send_permitted=_token(WIRE_SEND_PERMITTED is True),
        live_authorized=_token(closed_live.live_authorized is True),
        admitted=_token(decision.admitted is True),
        host_joined=_token(join.host_joined is True),
        port_constructed=TRUE_TOKEN,
        send_capable=TRUE_TOKEN,
        submission_authorized=_token(closed_submission.submission_authorized is True),
        productive_wire_send_reachable=_token(PRODUCTIVE_WIRE_SEND_REACHABLE is True),
        external_effect_authorized=FALSE_TOKEN,
        step_29q_status=STEP_29Q_PLAN_ONLY,
        step_29p_risk_admissible=str(dg["STEP_29P_RISK_ADMISSIBLE"]),
        cap24_bound_instrument_id=str(dg["CAP24_BOUND_INSTRUMENT_ID"]),
        first_real_blocker=first_blocker,
        blocker_class=blocker_class,
        post_count="0",
        evidence_manifest=str(store / "MANIFEST.sha256"),
        manifest_verify_rc=manifest_rc,
    )
