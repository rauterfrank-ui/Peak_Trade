"""CURRENT_PRODUCTIVE Cap-7.2 host-join to LiveExecutionPort.

Consumes Owner-GO
OWNER_GO_CURRENT_PRODUCTIVE_CAP_7_2_HOST_JOIN_TO_LIVE_EXECUTION_PORT_V1.

Joins the productive Cap-7.2 host to the already constructible fail-closed
LiveExecutionPort. Host-join is not LIVE_AUTHORIZED, STEP-29Q, POST,
submission, execution_eligible, or productive wire send.

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
    CAP_7_2_HOST_JOINED_IS_NOT_EXECUTION_ELIGIBLE,
    CAP_7_2_HOST_JOINED_IS_NOT_LIVE_AUTHORIZED,
    CAP_7_2_HOST_JOINED_IS_NOT_POST,
    CAP_7_2_HOST_JOINED_IS_NOT_STEP_29Q,
    CAP_7_2_HOST_JOINED_IS_NOT_SUBMISSION_AUTHORIZED,
    CAP_7_2_HOST_JOINED_IS_NOT_WIRE_SEND,
    CAP_7_2_HOST_JOIN_TO_LIVE_EXECUTION_PORT,
    CAP_7_2_HOST_JOIN_TO_LIVE_EXECUTION_PORT_IMPLEMENTED,
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    LIVE_ENABLED,
    LIVE_EXECUTION_PORT_CONSTRUCTED_IS_NOT_LIVE_AUTHORIZED,
    LIVE_EXECUTION_PORT_CONSTRUCTED_IS_NOT_POST,
    LIVE_EXECUTION_PORT_CONSTRUCTED_IS_NOT_STEP_29Q,
    LIVE_EXECUTION_PORT_CONSTRUCTED_IS_NOT_SUBMISSION_AUTHORIZED,
    LIVE_EXECUTION_PORT_CONSTRUCTED_IS_NOT_WIRE_SEND,
    LIVE_EXECUTION_PORT_CONSTRUCTIBLE,
    LIVE_EXECUTION_PORT_CONSTRUCTION_REMAINDER_CLOSED,
    PRODUCTIVE_WIRE_SEND_REACHABLE,
    STANDING_LIVE_AUTHORIZATION,
    WIRE_SEND_PERMITTED,
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
    LIVE_EXECUTION_PORT_CONSTRUCTION_FORBIDDEN,
    gap_node_v1,
)
from src.ops.full_core_live_path_composition_root_v1.live_execution_port_construction_admission_v1 import (
    CAP_11_1_CONSTRUCTION_FORBIDDEN_REASON,
    evaluate_live_execution_port_construction_admission_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    CURRENT_PRODUCTIVE_CAP72_HOST_JOIN_TO_LIVE_EXECUTION_PORT_ADAPTER_CREATED,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_live_execution_port_construction_v1 import (
    CANONICAL_PACK_RELPATH as DE_PACK_RELPATH,
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

OWNER_GO = "OWNER_GO_CURRENT_PRODUCTIVE_CAP_7_2_HOST_JOIN_TO_LIVE_EXECUTION_PORT_V1"
THIS_SLICE = "11.2.1.DF.FULL_CORE_CURRENT_PRODUCTIVE_CAP_7_2_HOST_JOIN_TO_LIVE_EXECUTION_PORT"
EXPECTED_ORIGIN_MAIN_SHA = "f573538d0ff561c752f3e123b9f66b8a3938b064"
CANONICAL_PACK_RELPATH = (
    "evidence/ops/full_core_current_productive_cap72_host_join_to_live_execution_port_v1/"
    "20260915T192200Z"
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


class CurrentProductiveCap72HostJoinToLiveExecutionPortError(ValueError):
    """Fail-closed Cap-7.2 host-join remainder violation."""


@dataclass(frozen=True)
class CurrentProductiveCap72HostJoinToLiveExecutionPortResultV1:
    store_root: str
    live_enabled: str
    live_armed: str
    wire_send_permitted: str
    live_authorized: str
    admitted: str
    admission_deny_absent: str
    port_constructible: str
    port_constructed: str
    port_construction_side_effect_free: str
    host_joined: str
    host_join_side_effect_free: str
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
            raise CurrentProductiveCap72HostJoinToLiveExecutionPortError(
                f"SECRET_TOKEN_PRESENT:{token}"
            )


def _load_json_object(*, path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise CurrentProductiveCap72HostJoinToLiveExecutionPortError(f"JSON_NOT_OBJECT:{path.name}")
    return payload


def _token(value: bool) -> str:
    return TRUE_TOKEN if value is True else FALSE_TOKEN


def _assert_standing_pins() -> None:
    if CURRENT_PRODUCTIVE_CAP72_HOST_JOIN_TO_LIVE_EXECUTION_PORT_ADAPTER_CREATED is not True:
        raise CurrentProductiveCap72HostJoinToLiveExecutionPortError("ADAPTER_NOT_CREATED")
    if LIVE_EXECUTION_PORT_CONSTRUCTION_REMAINDER_CLOSED is not True:
        raise CurrentProductiveCap72HostJoinToLiveExecutionPortError("CONSTRUCTION_REMAINDER_OPEN")
    if CAP_7_2_HOST_JOIN_TO_LIVE_EXECUTION_PORT_IMPLEMENTED is not True:
        raise CurrentProductiveCap72HostJoinToLiveExecutionPortError("HOST_JOIN_NOT_IMPLEMENTED")
    if LIVE_ENABLED is not True:
        raise CurrentProductiveCap72HostJoinToLiveExecutionPortError("LIVE_ENABLED_NOT_TRUE")
    if LIVE_ARMED is not True:
        raise CurrentProductiveCap72HostJoinToLiveExecutionPortError("LIVE_ARMED_NOT_TRUE")
    if WIRE_SEND_PERMITTED is not True:
        raise CurrentProductiveCap72HostJoinToLiveExecutionPortError("WIRE_SEND_PERMITTED_NOT_TRUE")
    if LIVE_EXECUTION_PORT_CONSTRUCTED_IS_NOT_SUBMISSION_AUTHORIZED is not True:
        raise CurrentProductiveCap72HostJoinToLiveExecutionPortError("MUST_NOT_AUTHORIZE_SUBMIT")
    if LIVE_EXECUTION_PORT_CONSTRUCTED_IS_NOT_WIRE_SEND is not True:
        raise CurrentProductiveCap72HostJoinToLiveExecutionPortError("MUST_NOT_SEND")
    if LIVE_EXECUTION_PORT_CONSTRUCTED_IS_NOT_LIVE_AUTHORIZED is not True:
        raise CurrentProductiveCap72HostJoinToLiveExecutionPortError("MUST_NOT_LIVE_AUTHORIZED")
    if LIVE_EXECUTION_PORT_CONSTRUCTED_IS_NOT_STEP_29Q is not True:
        raise CurrentProductiveCap72HostJoinToLiveExecutionPortError("MUST_NOT_STEP_29Q")
    if LIVE_EXECUTION_PORT_CONSTRUCTED_IS_NOT_POST is not True:
        raise CurrentProductiveCap72HostJoinToLiveExecutionPortError("MUST_NOT_POST")
    if CAP_7_2_HOST_JOINED_IS_NOT_SUBMISSION_AUTHORIZED is not True:
        raise CurrentProductiveCap72HostJoinToLiveExecutionPortError("JOIN_MUST_NOT_SUBMIT")
    if CAP_7_2_HOST_JOINED_IS_NOT_WIRE_SEND is not True:
        raise CurrentProductiveCap72HostJoinToLiveExecutionPortError("JOIN_MUST_NOT_SEND")
    if CAP_7_2_HOST_JOINED_IS_NOT_LIVE_AUTHORIZED is not True:
        raise CurrentProductiveCap72HostJoinToLiveExecutionPortError(
            "JOIN_MUST_NOT_LIVE_AUTHORIZED"
        )
    if CAP_7_2_HOST_JOINED_IS_NOT_STEP_29Q is not True:
        raise CurrentProductiveCap72HostJoinToLiveExecutionPortError("JOIN_MUST_NOT_STEP_29Q")
    if CAP_7_2_HOST_JOINED_IS_NOT_POST is not True:
        raise CurrentProductiveCap72HostJoinToLiveExecutionPortError("JOIN_MUST_NOT_POST")
    if CAP_7_2_HOST_JOINED_IS_NOT_EXECUTION_ELIGIBLE is not True:
        raise CurrentProductiveCap72HostJoinToLiveExecutionPortError(
            "JOIN_MUST_NOT_EXECUTION_ELIGIBLE"
        )
    if LIVE_AUTHORIZED is not False:
        raise CurrentProductiveCap72HostJoinToLiveExecutionPortError("LIVE_AUTHORIZED_NOT_FALSE")
    if STANDING_LIVE_AUTHORIZATION is not False:
        raise CurrentProductiveCap72HostJoinToLiveExecutionPortError(
            "STANDING_LIVE_AUTHORIZATION_NOT_FALSE"
        )
    if PRODUCTIVE_WIRE_SEND_REACHABLE is not False:
        raise CurrentProductiveCap72HostJoinToLiveExecutionPortError("WIRE_SEND_REACHABLE")
    if CAP_7_2_HOST_JOIN_TO_LIVE_EXECUTION_PORT is not True:
        raise CurrentProductiveCap72HostJoinToLiveExecutionPortError("HOST_JOIN_NOT_TRUE")
    if LIVE_EXECUTION_PORT_CONSTRUCTIBLE is not True:
        raise CurrentProductiveCap72HostJoinToLiveExecutionPortError("PORT_NOT_CONSTRUCTIBLE")
    if LIVE_EXECUTION_PORT_CONSTRUCTION_FORBIDDEN is not False:
        raise CurrentProductiveCap72HostJoinToLiveExecutionPortError("PORT_STILL_FORBIDDEN")
    node = gap_node_v1("LiveExecutionPort")
    if node.implementation_status != "HOST_JOINED_NOT_SUBMISSION_AUTHORIZED_NOT_WIRE":
        raise CurrentProductiveCap72HostJoinToLiveExecutionPortError("DAG_NODE_STATUS_DRIFT")


def _bind_current_de_epoch(*, repo_root: Path) -> dict[str, Any]:
    claims_path = repo_root / DE_PACK_RELPATH / "claims.json"
    if not claims_path.is_file():
        raise CurrentProductiveCap72HostJoinToLiveExecutionPortError("DE_CLAIMS_MISSING")
    claims = _load_json_object(path=claims_path)
    if str(claims.get("LIVE_ENABLED") or "") != TRUE_TOKEN:
        raise CurrentProductiveCap72HostJoinToLiveExecutionPortError("DE_LIVE_ENABLED_NOT_TRUE")
    if str(claims.get("LIVE_ARMED") or "") != TRUE_TOKEN:
        raise CurrentProductiveCap72HostJoinToLiveExecutionPortError("DE_LIVE_ARMED_NOT_TRUE")
    if str(claims.get("WIRE_SEND_PERMITTED") or "") != TRUE_TOKEN:
        raise CurrentProductiveCap72HostJoinToLiveExecutionPortError("DE_WIRE_SEND_NOT_TRUE")
    if str(claims.get("ADMITTED") or "") != TRUE_TOKEN:
        raise CurrentProductiveCap72HostJoinToLiveExecutionPortError("DE_ADMITTED_NOT_TRUE")
    if str(claims.get("LIVE_EXECUTION_PORT_CONSTRUCTED") or "") != TRUE_TOKEN:
        raise CurrentProductiveCap72HostJoinToLiveExecutionPortError("DE_PORT_NOT_CONSTRUCTED")
    if str(claims.get("STEP_29P_RISK_ADMISSIBLE") or "") != TRUE_TOKEN:
        raise CurrentProductiveCap72HostJoinToLiveExecutionPortError("DE_STEP_29P_NOT_TRUE")
    instrument_id = str(claims.get("CAP24_BOUND_INSTRUMENT_ID") or "").strip()
    if not instrument_id:
        raise CurrentProductiveCap72HostJoinToLiveExecutionPortError("DE_CAP24_ID_MISSING")
    if str(claims.get("POST_COUNT") or "") != "0":
        raise CurrentProductiveCap72HostJoinToLiveExecutionPortError("DE_POST_COUNT_NOT_ZERO")
    if str(claims.get("LIVE_AUTHORIZED") or "") != FALSE_TOKEN:
        raise CurrentProductiveCap72HostJoinToLiveExecutionPortError("DE_LIVE_AUTHORIZED_NOT_FALSE")
    if str(claims.get("CAP_7_2_HOST_JOIN_TO_LIVE_EXECUTION_PORT") or "") != FALSE_TOKEN:
        raise CurrentProductiveCap72HostJoinToLiveExecutionPortError("DE_HOST_JOIN_NOT_FALSE")
    if str(claims.get("FIRST_REAL_BLOCKER") or "") != (
        "CAP_7_2_HOST_JOIN_TO_LIVE_EXECUTION_PORT_REMAINS_FALSE"
    ):
        raise CurrentProductiveCap72HostJoinToLiveExecutionPortError("DE_BLOCKER_DRIFT")
    return claims


def _admission_inputs_v1() -> ExecutionAdmissionInputsV1:
    return ExecutionAdmissionInputsV1(
        plan_identity="current-productive-cap72-host-join",
        venue_plan_identity="current-productive-cap72-host-join",
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


def execute_current_productive_cap72_host_join_to_live_execution_port_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    evidence_root: Path | None = None,
    repo_root: Path | None = None,
) -> CurrentProductiveCap72HostJoinToLiveExecutionPortResultV1:
    if owner_go != OWNER_GO:
        raise CurrentProductiveCap72HostJoinToLiveExecutionPortError("OWNER_GO_MISMATCH")
    if origin_main_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise CurrentProductiveCap72HostJoinToLiveExecutionPortError("ORIGIN_MAIN_SHA_MISMATCH")
    _assert_standing_pins()
    root = repo_root or Path(__file__).resolve().parents[3]
    de = _bind_current_de_epoch(repo_root=root)
    gates = standing_live_gate_fields_v1()
    if gates["live_enabled"] is not True:
        raise CurrentProductiveCap72HostJoinToLiveExecutionPortError(
            "STANDING_FIELD_LIVE_ENABLED_FALSE"
        )
    if gates["live_armed"] is not True:
        raise CurrentProductiveCap72HostJoinToLiveExecutionPortError(
            "STANDING_FIELD_LIVE_ARMED_FALSE"
        )
    if gates["wire_send_permitted"] is not True:
        raise CurrentProductiveCap72HostJoinToLiveExecutionPortError("STANDING_FIELD_WIRE_FALSE")

    decision = evaluate_execution_admission_v1(_admission_inputs_v1())
    if decision.admitted is not True:
        raise CurrentProductiveCap72HostJoinToLiveExecutionPortError("ADMISSION_NOT_ADMITTED")
    deny_hit = _ADMISSION_DENY_REASONS.intersection(decision.reason_codes)
    if deny_hit:
        raise CurrentProductiveCap72HostJoinToLiveExecutionPortError(
            f"ADMISSION_DENY_PRESENT:{sorted(deny_hit)}"
        )
    if decision.reason_codes:
        raise CurrentProductiveCap72HostJoinToLiveExecutionPortError(
            f"UNEXPECTED_ADMISSION_REASONS:{list(decision.reason_codes)}"
        )

    missing_host = HostActivationBindingV1()
    missing_join = join_cap72_host_to_live_execution_port_v1(host=missing_host)
    if missing_join.host_joined is True:
        raise CurrentProductiveCap72HostJoinToLiveExecutionPortError("MISSING_PREREQ_MUST_FAIL")
    if "CONSTRUCTION_ADMISSION_NOT_CONSTRUCTIBLE" not in missing_join.reason_codes:
        raise CurrentProductiveCap72HostJoinToLiveExecutionPortError("MISSING_CONSTRUCTION_DENY")
    if isinstance(missing_host.execution_port, SimulatedExecutionPortV1) is not True:
        raise CurrentProductiveCap72HostJoinToLiveExecutionPortError(
            "MISSING_SIMULATED_NOT_RETAINED"
        )
    if missing_host.live_execution_port is not None:
        raise CurrentProductiveCap72HostJoinToLiveExecutionPortError("MISSING_LIVE_PORT_ATTACHED")

    productive = evaluate_live_execution_port_construction_admission_v1(
        admission=decision,
        live_enabled=True,
        live_armed=True,
        wire_send_permitted=True,
        attempt_with_credentials=True,
        attempt_network_session=True,
    )
    productive_join = join_cap72_host_to_live_execution_port_v1(
        host=HostActivationBindingV1(),
        construction_admission=productive,
    )
    if productive_join.host_joined is True:
        raise CurrentProductiveCap72HostJoinToLiveExecutionPortError(
            "PRODUCTIVE_RESOURCES_MUST_FAIL"
        )
    if "PRODUCTIVE_CONSTRUCTION_RESOURCES_FORBIDDEN" not in productive_join.reason_codes:
        raise CurrentProductiveCap72HostJoinToLiveExecutionPortError(
            "PRODUCTIVE_RESOURCES_DENY_MISSING"
        )

    construction = evaluate_live_execution_port_construction_admission_v1(
        admission=decision,
        live_enabled=LIVE_ENABLED is True,
        live_armed=LIVE_ARMED is True,
        wire_send_permitted=WIRE_SEND_PERMITTED is True,
        attempt_with_credentials=False,
        attempt_network_session=False,
    )
    if construction.constructible is not True:
        raise CurrentProductiveCap72HostJoinToLiveExecutionPortError("PORT_NOT_CONSTRUCTIBLE")
    if construction.constructed is True:
        raise CurrentProductiveCap72HostJoinToLiveExecutionPortError("EVALUATE_MUST_NOT_CONSTRUCT")
    if CAP_11_1_CONSTRUCTION_FORBIDDEN_REASON in construction.reason_codes:
        raise CurrentProductiveCap72HostJoinToLiveExecutionPortError(
            "CONSTRUCTION_CAP_11_1_STILL_PRESENT"
        )
    try:
        construct_live_execution_port_v1()
    except ExecutionPortConstructionForbiddenError as exc:
        if CAP_11_1_CONSTRUCTION_FORBIDDEN_REASON not in str(exc):
            raise CurrentProductiveCap72HostJoinToLiveExecutionPortError(
                "BARE_CONSTRUCT_REASON_DRIFT"
            )
    else:
        raise CurrentProductiveCap72HostJoinToLiveExecutionPortError("BARE_CONSTRUCT_MUST_FAIL")
    port = construct_live_execution_port_v1(construction_admission=construction)
    host = HostActivationBindingV1()
    submit_join = join_cap72_host_to_live_execution_port_v1(
        host=HostActivationBindingV1(),
        construction_admission=construction,
        live_port=port,
        attempt_submit=True,
    )
    if submit_join.host_joined is True:
        raise CurrentProductiveCap72HostJoinToLiveExecutionPortError("SUBMIT_JOIN_MUST_FAIL")
    if "SUBMIT_FROM_HOST_JOIN_FORBIDDEN" not in submit_join.reason_codes:
        raise CurrentProductiveCap72HostJoinToLiveExecutionPortError("SUBMIT_DENY_MISSING")
    wire_join = join_cap72_host_to_live_execution_port_v1(
        host=HostActivationBindingV1(),
        construction_admission=construction,
        live_port=port,
        attempt_wire_send=True,
    )
    if wire_join.host_joined is True:
        raise CurrentProductiveCap72HostJoinToLiveExecutionPortError("WIRE_JOIN_MUST_FAIL")
    if "WIRE_FROM_HOST_JOIN_FORBIDDEN" not in wire_join.reason_codes:
        raise CurrentProductiveCap72HostJoinToLiveExecutionPortError("WIRE_DENY_MISSING")
    join = join_cap72_host_to_live_execution_port_v1(
        host=host,
        construction_admission=construction,
        live_port=port,
    )
    if join.host_joined is not True:
        raise CurrentProductiveCap72HostJoinToLiveExecutionPortError(
            f"HOST_JOIN_FAILED:{list(join.reason_codes)}"
        )
    if join.side_effect_free is not True:
        raise CurrentProductiveCap72HostJoinToLiveExecutionPortError(
            "HOST_JOIN_NOT_SIDE_EFFECT_FREE"
        )
    if join.submission_authorized is True:
        raise CurrentProductiveCap72HostJoinToLiveExecutionPortError("SUBMISSION_AUTHORIZED")
    if join.execution_eligible is True:
        raise CurrentProductiveCap72HostJoinToLiveExecutionPortError("EXECUTION_ELIGIBLE")
    if join.wire_send_occurred is True:
        raise CurrentProductiveCap72HostJoinToLiveExecutionPortError("WIRE_SIDE_EFFECT")
    if join.post_count != 0:
        raise CurrentProductiveCap72HostJoinToLiveExecutionPortError("POST_COUNT_NOT_ZERO")
    if not isinstance(host.execution_port, SimulatedExecutionPortV1):
        raise CurrentProductiveCap72HostJoinToLiveExecutionPortError("SIMULATED_PORT_LOST")
    if host.live_execution_port is not port:
        raise CurrentProductiveCap72HostJoinToLiveExecutionPortError("LIVE_PORT_NOT_OWNED")
    if host.live_execution_port is host.execution_port:
        raise CurrentProductiveCap72HostJoinToLiveExecutionPortError("LIVE_PORT_REPLACED_SIMULATED")
    if getattr(port, "EXCHANGE_ORDER_SUBMIT_REACHABLE", True) is not False:
        raise CurrentProductiveCap72HostJoinToLiveExecutionPortError("SUBMIT_REACHABLE")
    if getattr(port, "SUBMISSION_AUTHORIZED", True) is not False:
        raise CurrentProductiveCap72HostJoinToLiveExecutionPortError("PORT_SUBMISSION_AUTHORIZED")

    first_blocker = "SUBMISSION_AUTHORIZED_REMAINS_FALSE"
    blocker_class = "E"
    store = Path(evidence_root) if evidence_root is not None else root / CANONICAL_PACK_RELPATH
    store.mkdir(parents=True, exist_ok=True)
    claims = {
        "THIS_SLICE": THIS_SLICE,
        "OWNER_GO": OWNER_GO,
        "EXPECTED_ORIGIN_MAIN": origin_main_sha,
        "LIVE_EXECUTION_PORT_CONSTRUCTION_REMAINDER_CLOSED": TRUE_TOKEN,
        "LIVE_EXECUTION_PORT_CONSTRUCTIBLE": _token(construction.constructible is True),
        "LIVE_EXECUTION_PORT_CONSTRUCTED": TRUE_TOKEN,
        "PORT_CONSTRUCTION_SIDE_EFFECT_FREE": TRUE_TOKEN,
        "CAP_7_2_HOST_JOIN_TO_LIVE_EXECUTION_PORT": _token(
            CAP_7_2_HOST_JOIN_TO_LIVE_EXECUTION_PORT is True
        ),
        "CAP_7_2_HOST_JOIN_TO_LIVE_EXECUTION_PORT_IMPLEMENTED": TRUE_TOKEN,
        "HOST_JOINED": _token(join.host_joined is True),
        "HOST_JOIN_SIDE_EFFECT_FREE": _token(join.side_effect_free is True),
        "CAP_7_2_HOST_JOINED_IS_NOT_SUBMISSION_AUTHORIZED": TRUE_TOKEN,
        "CAP_7_2_HOST_JOINED_IS_NOT_WIRE_SEND": TRUE_TOKEN,
        "CAP_7_2_HOST_JOINED_IS_NOT_LIVE_AUTHORIZED": TRUE_TOKEN,
        "CAP_7_2_HOST_JOINED_IS_NOT_STEP_29Q": TRUE_TOKEN,
        "CAP_7_2_HOST_JOINED_IS_NOT_POST": TRUE_TOKEN,
        "CAP_7_2_HOST_JOINED_IS_NOT_EXECUTION_ELIGIBLE": TRUE_TOKEN,
        "SIMULATED_EXECUTION_PORT_RETAINED": TRUE_TOKEN,
        "SIMULATED_EXECUTION_PORT_SOLE_REACHABLE": TRUE_TOKEN,
        "LIVE_ENABLED": _token(LIVE_ENABLED is True),
        "LIVE_ARMED": _token(LIVE_ARMED is True),
        "WIRE_SEND_PERMITTED": _token(WIRE_SEND_PERMITTED is True),
        "LIVE_AUTHORIZED": _token(LIVE_AUTHORIZED is True),
        "STANDING_LIVE_AUTHORIZATION": _token(STANDING_LIVE_AUTHORIZATION is True),
        "ADMITTED": _token(decision.admitted is True),
        "ADMISSION_DENY_ABSENT": TRUE_TOKEN,
        "ADMISSION_REASON_CODES": list(decision.reason_codes),
        "CONSTRUCTION_REASON_CODES": list(construction.reason_codes),
        "HOST_JOIN_REASON_CODES": list(join.reason_codes),
        "PRODUCTIVE_WIRE_SEND_REACHABLE": _token(PRODUCTIVE_WIRE_SEND_REACHABLE is True),
        "STEP_29Q_STATUS": "PLAN_ONLY",
        "SUBMISSION_AUTHORIZED": FALSE_TOKEN,
        "POST_COUNT": "0",
        "STEP_29P_RISK_ADMISSIBLE": str(de["STEP_29P_RISK_ADMISSIBLE"]),
        "CAP24_BOUND_INSTRUMENT_ID": str(de["CAP24_BOUND_INSTRUMENT_ID"]),
        "CAP23_SELECTED_INSTRUMENT_ID": str(de.get("CAP23_SELECTED_INSTRUMENT_ID") or ""),
        "DE_PACK": DE_PACK_RELPATH,
        "FIRST_REAL_BLOCKER": first_blocker,
        "BLOCKER_CLASS": blocker_class,
        "NEXT_OWNER_GO_REQUIRED": (
            "OWNER_GO_REQUIRED_FOR_SUBMISSION_AUTHORIZED_NOT_AUTHORIZED_BY_THIS_SLICE"
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
        "DE_OWNER_GO": str(de.get("OWNER_GO") or ""),
        "DE_FIRST_REAL_BLOCKER": str(de.get("FIRST_REAL_BLOCKER") or ""),
        "CAP24_BOUND_INSTRUMENT_ID": str(de.get("CAP24_BOUND_INSTRUMENT_ID") or ""),
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
        "SUBMISSION_AUTHORIZED_UNCHANGED_FALSE": TRUE_TOKEN,
        "LIVE_ENABLED_UNCHANGED_TRUE": TRUE_TOKEN,
        "LIVE_ARMED_UNCHANGED_TRUE": TRUE_TOKEN,
        "WIRE_SEND_PERMITTED_UNCHANGED_TRUE": TRUE_TOKEN,
        "ADMISSION_UNCHANGED_TRUE": TRUE_TOKEN,
        "PORT_CONSTRUCTED_UNCHANGED_TRUE": TRUE_TOKEN,
    }
    summary = {
        "FIRST_REAL_BLOCKER": first_blocker,
        "BLOCKER_CLASS": blocker_class,
        "LIVE_ENABLED": _token(LIVE_ENABLED is True),
        "LIVE_ARMED": _token(LIVE_ARMED is True),
        "WIRE_SEND_PERMITTED": _token(WIRE_SEND_PERMITTED is True),
        "LIVE_AUTHORIZED": _token(LIVE_AUTHORIZED is True),
        "ADMITTED": _token(decision.admitted is True),
        "LIVE_EXECUTION_PORT_CONSTRUCTIBLE": TRUE_TOKEN,
        "LIVE_EXECUTION_PORT_CONSTRUCTED": TRUE_TOKEN,
        "PORT_CONSTRUCTION_SIDE_EFFECT_FREE": TRUE_TOKEN,
        "HOST_JOINED": TRUE_TOKEN,
        "HOST_JOIN_SIDE_EFFECT_FREE": TRUE_TOKEN,
        "CAP_7_2_HOST_JOIN_TO_LIVE_EXECUTION_PORT": TRUE_TOKEN,
        "STEP_29P_RISK_ADMISSIBLE": str(de["STEP_29P_RISK_ADMISSIBLE"]),
        "SUBMISSION_AUTHORIZED": FALSE_TOKEN,
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
    return CurrentProductiveCap72HostJoinToLiveExecutionPortResultV1(
        store_root=str(store),
        live_enabled=_token(LIVE_ENABLED is True),
        live_armed=_token(LIVE_ARMED is True),
        wire_send_permitted=_token(WIRE_SEND_PERMITTED is True),
        live_authorized=_token(LIVE_AUTHORIZED is True),
        admitted=_token(decision.admitted is True),
        admission_deny_absent=TRUE_TOKEN,
        port_constructible=_token(construction.constructible is True),
        port_constructed=TRUE_TOKEN,
        port_construction_side_effect_free=TRUE_TOKEN,
        host_joined=_token(join.host_joined is True),
        host_join_side_effect_free=_token(join.side_effect_free is True),
        step_29p_risk_admissible=str(de["STEP_29P_RISK_ADMISSIBLE"]),
        cap24_bound_instrument_id=str(de["CAP24_BOUND_INSTRUMENT_ID"]),
        first_real_blocker=first_blocker,
        blocker_class=blocker_class,
        post_count="0",
        evidence_manifest=str(store / "MANIFEST.sha256"),
        manifest_verify_rc=manifest_rc,
    )
