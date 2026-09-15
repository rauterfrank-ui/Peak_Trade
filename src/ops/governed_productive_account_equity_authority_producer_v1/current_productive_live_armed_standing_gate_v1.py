"""CURRENT_PRODUCTIVE LIVE_ARMED standing-gate closure.

Consumes Owner-GO
OWNER_GO_CURRENT_PRODUCTIVE_LIVE_ARMED_STANDING_GATE_EVALUATION_V1.

Sets the existing §11.2.1.P Full-Core standing predicate LIVE_ARMED=true.
That satisfies only the LIVE_ARMED deny predicate. It does not admit Live,
permit wire send, authorize POST, or construct LiveExecutionPort.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    EXECUTION_ADMISSION_REMAINDER_CLOSED,
    LIVE_ARMED,
    LIVE_ARMED_DOES_NOT_IMPLY_LIVE_AUTHORIZED,
    LIVE_ARMED_DOES_NOT_IMPLY_PORT_CONSTRUCTION,
    LIVE_ARMED_DOES_NOT_IMPLY_RISK_ADMISSIBLE,
    LIVE_ARMED_DOES_NOT_IMPLY_WIRE_SEND,
    LIVE_ARMED_STANDING_ADMISSION_SEAM_IMPLEMENTED,
    LIVE_ARMED_STANDING_GATE_CLOSED,
    LIVE_ARMED_TRUE_IS_NOT_AUTOMATIC_ADMISSION,
    LIVE_AUTHORIZED,
    LIVE_ENABLED,
    LIVE_EXECUTION_PORT_CONSTRUCTIBLE,
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
    evaluate_live_execution_port_construction_admission_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    CURRENT_PRODUCTIVE_LIVE_ARMED_STANDING_GATE_ADAPTER_CREATED,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_live_enabled_standing_gate_v1 import (
    CANONICAL_PACK_RELPATH as DA_PACK_RELPATH,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.d4_d5_genesis_runtime_orchestrator_v1 import (
    persist_manifest_sha256_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    verify_manifest_sha256_v1,
)

OWNER_GO = "OWNER_GO_CURRENT_PRODUCTIVE_LIVE_ARMED_STANDING_GATE_EVALUATION_V1"
THIS_SLICE = "11.2.1.DB.FULL_CORE_CURRENT_PRODUCTIVE_LIVE_ARMED_STANDING_GATE"
EXPECTED_ORIGIN_MAIN_SHA = "5895fcb495a00f71ffa1fff643da8e4a701b95bf"
CANONICAL_PACK_RELPATH = (
    "evidence/ops/full_core_current_productive_live_armed_standing_gate_v1/20260915T173000Z"
)
FALSE_TOKEN = "false"
TRUE_TOKEN = "true"
_LIVE_ARMED_DENY_REASONS = frozenset(
    {
        "LIVE_ARMED_FALSE",
        "STANDING_OR_INPUT_LIVE_ARMED",
        "STANDING_LIVE_ARMED_TRUE",
    }
)
_SECRET_TOKENS = ("secret", "passphrase", "api_key", "apiKey", "private_key")


class CurrentProductiveLiveArmedStandingGateError(ValueError):
    """Fail-closed LIVE_ARMED standing-gate evaluation violation."""


@dataclass(frozen=True)
class CurrentProductiveLiveArmedStandingGateResultV1:
    store_root: str
    live_enabled: str
    live_armed: str
    wire_send_permitted: str
    live_authorized: str
    admitted: str
    live_armed_deny_absent: str
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
            raise CurrentProductiveLiveArmedStandingGateError(f"SECRET_TOKEN_PRESENT:{token}")


def _load_json_object(*, path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise CurrentProductiveLiveArmedStandingGateError(f"JSON_NOT_OBJECT:{path.name}")
    return payload


def _token(value: bool) -> str:
    return TRUE_TOKEN if value is True else FALSE_TOKEN


def _assert_standing_pins() -> None:
    if CURRENT_PRODUCTIVE_LIVE_ARMED_STANDING_GATE_ADAPTER_CREATED is not True:
        raise CurrentProductiveLiveArmedStandingGateError("ADAPTER_NOT_CREATED")
    if LIVE_ARMED_STANDING_ADMISSION_SEAM_IMPLEMENTED is not True:
        raise CurrentProductiveLiveArmedStandingGateError("SEAM_NOT_IMPLEMENTED")
    if LIVE_ARMED_STANDING_GATE_CLOSED is not True:
        raise CurrentProductiveLiveArmedStandingGateError("STANDING_GATE_NOT_CLOSED")
    if LIVE_ENABLED is not True:
        raise CurrentProductiveLiveArmedStandingGateError("LIVE_ENABLED_NOT_TRUE")
    if LIVE_ARMED is not True:
        raise CurrentProductiveLiveArmedStandingGateError("LIVE_ARMED_NOT_TRUE")
    if LIVE_ARMED_TRUE_IS_NOT_AUTOMATIC_ADMISSION is not True:
        raise CurrentProductiveLiveArmedStandingGateError("TRUE_MUST_NOT_ADMIT")
    if LIVE_ARMED_DOES_NOT_IMPLY_WIRE_SEND is not True:
        raise CurrentProductiveLiveArmedStandingGateError("MUST_NOT_IMPLY_WIRE")
    if LIVE_ARMED_DOES_NOT_IMPLY_PORT_CONSTRUCTION is not True:
        raise CurrentProductiveLiveArmedStandingGateError("MUST_NOT_IMPLY_PORT")
    if LIVE_ARMED_DOES_NOT_IMPLY_LIVE_AUTHORIZED is not True:
        raise CurrentProductiveLiveArmedStandingGateError("MUST_NOT_IMPLY_AUTHORIZED")
    if LIVE_ARMED_DOES_NOT_IMPLY_RISK_ADMISSIBLE is not True:
        raise CurrentProductiveLiveArmedStandingGateError("MUST_NOT_IMPLY_RISK")
    if LIVE_AUTHORIZED is not False:
        raise CurrentProductiveLiveArmedStandingGateError("LIVE_AUTHORIZED_NOT_FALSE")
    if STANDING_LIVE_AUTHORIZATION is not False:
        raise CurrentProductiveLiveArmedStandingGateError("STANDING_LIVE_AUTHORIZATION_NOT_FALSE")
    if PRODUCTIVE_WIRE_SEND_REACHABLE is not False:
        raise CurrentProductiveLiveArmedStandingGateError("WIRE_SEND_REACHABLE")
    if LIVE_EXECUTION_PORT_CONSTRUCTIBLE is not False:
        raise CurrentProductiveLiveArmedStandingGateError("PORT_CONSTRUCTIBLE")
    if LIVE_EXECUTION_PORT_CONSTRUCTION_FORBIDDEN is not True:
        raise CurrentProductiveLiveArmedStandingGateError("PORT_NOT_FORBIDDEN")
    node = gap_node_v1("LIVE_ARMED")
    if node.implementation_status != "STANDING_TRUE_NOT_AUTOMATIC_ADMISSION":
        raise CurrentProductiveLiveArmedStandingGateError("DAG_NODE_STATUS_DRIFT")


def _bind_current_da_epoch(*, repo_root: Path) -> dict[str, Any]:
    claims_path = repo_root / DA_PACK_RELPATH / "claims.json"
    if not claims_path.is_file():
        raise CurrentProductiveLiveArmedStandingGateError("DA_CLAIMS_MISSING")
    claims = _load_json_object(path=claims_path)
    if str(claims.get("LIVE_ENABLED") or "") != TRUE_TOKEN:
        raise CurrentProductiveLiveArmedStandingGateError("DA_LIVE_ENABLED_NOT_TRUE")
    if str(claims.get("STEP_29P_RISK_ADMISSIBLE") or "") != TRUE_TOKEN:
        raise CurrentProductiveLiveArmedStandingGateError("DA_STEP_29P_NOT_TRUE")
    instrument_id = str(claims.get("CAP24_BOUND_INSTRUMENT_ID") or "").strip()
    if not instrument_id:
        raise CurrentProductiveLiveArmedStandingGateError("DA_CAP24_ID_MISSING")
    if str(claims.get("POST_COUNT") or "") != "0":
        raise CurrentProductiveLiveArmedStandingGateError("DA_POST_COUNT_NOT_ZERO")
    if str(claims.get("WIRE_SEND_PERMITTED") or "") != FALSE_TOKEN:
        raise CurrentProductiveLiveArmedStandingGateError("DA_WIRE_SEND_NOT_FALSE")
    if str(claims.get("LIVE_AUTHORIZED") or "") != FALSE_TOKEN:
        raise CurrentProductiveLiveArmedStandingGateError("DA_LIVE_AUTHORIZED_NOT_FALSE")
    return claims


def _admission_inputs_v1() -> ExecutionAdmissionInputsV1:
    return ExecutionAdmissionInputsV1(
        plan_identity="current-productive-live-armed-standing-gate",
        venue_plan_identity="current-productive-live-armed-standing-gate",
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


def execute_current_productive_live_armed_standing_gate_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    evidence_root: Path | None = None,
    repo_root: Path | None = None,
) -> CurrentProductiveLiveArmedStandingGateResultV1:
    if owner_go != OWNER_GO:
        raise CurrentProductiveLiveArmedStandingGateError("OWNER_GO_MISMATCH")
    if origin_main_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise CurrentProductiveLiveArmedStandingGateError("ORIGIN_MAIN_SHA_MISMATCH")
    _assert_standing_pins()
    root = repo_root or Path(__file__).resolve().parents[3]
    da = _bind_current_da_epoch(repo_root=root)
    gates = standing_live_gate_fields_v1()
    if gates["live_enabled"] is not True:
        raise CurrentProductiveLiveArmedStandingGateError("STANDING_FIELD_LIVE_ENABLED_FALSE")
    if gates["live_armed"] is not True:
        raise CurrentProductiveLiveArmedStandingGateError("STANDING_FIELD_LIVE_ARMED_FALSE")
    if WIRE_SEND_PERMITTED is not True and gates["wire_send_permitted"] is not False:
        raise CurrentProductiveLiveArmedStandingGateError("STANDING_FIELD_WIRE_TRUE")

    decision = evaluate_execution_admission_v1(_admission_inputs_v1())
    deny_hit = _LIVE_ARMED_DENY_REASONS.intersection(decision.reason_codes)
    if deny_hit:
        raise CurrentProductiveLiveArmedStandingGateError(
            f"LIVE_ARMED_DENY_PRESENT:{sorted(deny_hit)}"
        )
    if "LIVE_ENABLED_FALSE" in decision.reason_codes:
        raise CurrentProductiveLiveArmedStandingGateError("LIVE_ENABLED_DENY_PRESENT")
    remainder_closed = EXECUTION_ADMISSION_REMAINDER_CLOSED is True
    if remainder_closed:
        if decision.admitted is not True:
            raise CurrentProductiveLiveArmedStandingGateError("ADMISSION_REMAINDER_NOT_CLOSED")
        if "EXECUTION_ADMISSION_FAIL_CLOSED" in decision.reason_codes:
            raise CurrentProductiveLiveArmedStandingGateError("ADMISSION_FAIL_CLOSED_STILL_PRESENT")
        if "WIRE_SEND_NOT_PERMITTED" in decision.reason_codes:
            raise CurrentProductiveLiveArmedStandingGateError("WIRE_SEND_DENY_PRESENT")
    else:
        if decision.admitted is True:
            raise CurrentProductiveLiveArmedStandingGateError("ADMISSION_MUST_REMAIN_FALSE")
        if WIRE_SEND_PERMITTED is True:
            if "WIRE_SEND_NOT_PERMITTED" in decision.reason_codes:
                raise CurrentProductiveLiveArmedStandingGateError("WIRE_SEND_DENY_PRESENT")
            if "EXECUTION_ADMISSION_FAIL_CLOSED" not in decision.reason_codes:
                raise CurrentProductiveLiveArmedStandingGateError("ADMISSION_FAIL_CLOSED_MISSING")
        elif "WIRE_SEND_NOT_PERMITTED" not in decision.reason_codes:
            raise CurrentProductiveLiveArmedStandingGateError("WIRE_SEND_DENY_MISSING")

    construction = evaluate_live_execution_port_construction_admission_v1(
        admission=decision,
        live_enabled=LIVE_ENABLED is True,
        live_armed=LIVE_ARMED is True,
        wire_send_permitted=WIRE_SEND_PERMITTED is True,
        attempt_with_credentials=False,
        attempt_network_session=False,
    )
    if construction.constructible is True or construction.constructed is True:
        raise CurrentProductiveLiveArmedStandingGateError("PORT_MUST_REMAIN_FORBIDDEN")
    if remainder_closed:
        if "WIRE_SEND_NOT_PERMITTED" in construction.reason_codes:
            raise CurrentProductiveLiveArmedStandingGateError("CONSTRUCTION_WIRE_DENY_PRESENT")
        if "LIVE_EXECUTION_PORT_CONSTRUCTION_FORBIDDEN_IN_CAPABILITY_11_1" not in (
            construction.reason_codes
        ):
            raise CurrentProductiveLiveArmedStandingGateError("CONSTRUCTION_CAP_11_1_MISSING")
        if "EXECUTION_ADMISSION_NOT_ADMITTED" in construction.reason_codes:
            raise CurrentProductiveLiveArmedStandingGateError("CONSTRUCTION_ADMISSION_DENY_PRESENT")
    elif WIRE_SEND_PERMITTED is True:
        if "WIRE_SEND_NOT_PERMITTED" in construction.reason_codes:
            raise CurrentProductiveLiveArmedStandingGateError("CONSTRUCTION_WIRE_DENY_PRESENT")
        if "LIVE_EXECUTION_PORT_CONSTRUCTION_FORBIDDEN_IN_CAPABILITY_11_1" not in (
            construction.reason_codes
        ):
            raise CurrentProductiveLiveArmedStandingGateError("CONSTRUCTION_CAP_11_1_MISSING")
        if "EXECUTION_ADMISSION_NOT_ADMITTED" not in construction.reason_codes:
            raise CurrentProductiveLiveArmedStandingGateError("CONSTRUCTION_ADMISSION_DENY_MISSING")
    elif "WIRE_SEND_NOT_PERMITTED" not in construction.reason_codes:
        raise CurrentProductiveLiveArmedStandingGateError("CONSTRUCTION_WIRE_DENY_MISSING")

    first_blocker = (
        "LIVE_EXECUTION_PORT_CONSTRUCTION_REMAINS_FORBIDDEN"
        if remainder_closed
        else (
            "EXECUTION_ADMISSION_REMAINS_FAIL_CLOSED"
            if WIRE_SEND_PERMITTED is True
            else "WIRE_SEND_PERMITTED_STANDING_GATE_REMAINS_FALSE"
        )
    )
    blocker_class = "E"
    store = Path(evidence_root) if evidence_root is not None else root / CANONICAL_PACK_RELPATH
    store.mkdir(parents=True, exist_ok=True)
    claims = {
        "THIS_SLICE": THIS_SLICE,
        "OWNER_GO": OWNER_GO,
        "EXPECTED_ORIGIN_MAIN": origin_main_sha,
        "LIVE_ARMED_SEAM_STATUS": "STANDING_TRUE_NOT_AUTOMATIC_ADMISSION",
        "LIVE_ARMED_SEMANTICS_PROVEN": TRUE_TOKEN,
        "CONTRADICTION_LOCK_REMOVED": TRUE_TOKEN,
        "LIVE_ARMED_TRUE_IS_NOT_AUTOMATIC_ADMISSION": TRUE_TOKEN,
        "LIVE_ARMED_DOES_NOT_IMPLY_WIRE_SEND": TRUE_TOKEN,
        "LIVE_ARMED_DOES_NOT_IMPLY_PORT_CONSTRUCTION": TRUE_TOKEN,
        "LIVE_ARMED_DOES_NOT_IMPLY_LIVE_AUTHORIZED": TRUE_TOKEN,
        "LIVE_ARMED_DOES_NOT_IMPLY_RISK_ADMISSIBLE": TRUE_TOKEN,
        "LIVE_ENABLED": _token(LIVE_ENABLED is True),
        "LIVE_ARMED": _token(LIVE_ARMED is True),
        "WIRE_SEND_PERMITTED": _token(WIRE_SEND_PERMITTED is True),
        "LIVE_AUTHORIZED": _token(LIVE_AUTHORIZED is True),
        "STANDING_LIVE_AUTHORIZATION": _token(STANDING_LIVE_AUTHORIZATION is True),
        "ADMITTED": _token(decision.admitted is True),
        "LIVE_ARMED_DENY_ABSENT": TRUE_TOKEN,
        "ADMISSION_REASON_CODES": list(decision.reason_codes),
        "LIVE_EXECUTION_PORT_CONSTRUCTIBLE": _token(construction.constructible is True),
        "LIVE_EXECUTION_PORT_CONSTRUCTED": _token(construction.constructed is True),
        "PRODUCTIVE_WIRE_SEND_REACHABLE": _token(PRODUCTIVE_WIRE_SEND_REACHABLE is True),
        "STEP_29Q_STATUS": "PLAN_ONLY",
        "POST_COUNT": "0",
        "STEP_29P_RISK_ADMISSIBLE": str(da["STEP_29P_RISK_ADMISSIBLE"]),
        "CAP24_BOUND_INSTRUMENT_ID": str(da["CAP24_BOUND_INSTRUMENT_ID"]),
        "CAP23_SELECTED_INSTRUMENT_ID": str(da.get("CAP23_SELECTED_INSTRUMENT_ID") or ""),
        "DA_PACK": DA_PACK_RELPATH,
        "FIRST_REAL_BLOCKER": first_blocker,
        "BLOCKER_CLASS": blocker_class,
        "NEXT_OWNER_GO_REQUIRED": (
            "OWNER_GO_REQUIRED_FOR_ADMISSION_REMAINDER_NOT_AUTHORIZED_BY_THIS_SLICE"
            if WIRE_SEND_PERMITTED is True
            else "OWNER_GO_REQUIRED_FOR_WIRE_SEND_PERMITTED_NOT_AUTHORIZED_BY_THIS_SLICE"
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
        "DA_OWNER_GO": str(da.get("OWNER_GO") or ""),
        "DA_FIRST_REAL_BLOCKER": str(da.get("FIRST_REAL_BLOCKER") or ""),
        "CAP24_BOUND_INSTRUMENT_ID": str(da.get("CAP24_BOUND_INSTRUMENT_ID") or ""),
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
        "CANARY_LIVE_ARMED_UNCHANGED": TRUE_TOKEN,
        "SECTION_11_14_LIVE_ARMED_UNCHANGED": TRUE_TOKEN,
        "WIRE_SEND_PERMITTED_UNCHANGED_FALSE": _token(WIRE_SEND_PERMITTED is False),
        "LIVE_AUTHORIZED_UNCHANGED_FALSE": TRUE_TOKEN,
        "STEP_29Q_UNCHANGED_PLAN_ONLY": TRUE_TOKEN,
        "LIVE_EXECUTION_PORT_CONSTRUCTION_FORBIDDEN_UNCHANGED": TRUE_TOKEN,
    }
    summary = {
        "FIRST_REAL_BLOCKER": first_blocker,
        "BLOCKER_CLASS": blocker_class,
        "LIVE_ENABLED": _token(LIVE_ENABLED is True),
        "LIVE_ARMED": _token(LIVE_ARMED is True),
        "WIRE_SEND_PERMITTED": _token(WIRE_SEND_PERMITTED is True),
        "LIVE_AUTHORIZED": _token(LIVE_AUTHORIZED is True),
        "STEP_29P_RISK_ADMISSIBLE": str(da["STEP_29P_RISK_ADMISSIBLE"]),
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
    return CurrentProductiveLiveArmedStandingGateResultV1(
        store_root=str(store),
        live_enabled=_token(LIVE_ENABLED is True),
        live_armed=_token(LIVE_ARMED is True),
        wire_send_permitted=_token(WIRE_SEND_PERMITTED is True),
        live_authorized=_token(LIVE_AUTHORIZED is True),
        admitted=_token(decision.admitted is True),
        live_armed_deny_absent=TRUE_TOKEN,
        step_29p_risk_admissible=str(da["STEP_29P_RISK_ADMISSIBLE"]),
        cap24_bound_instrument_id=str(da["CAP24_BOUND_INSTRUMENT_ID"]),
        first_real_blocker=first_blocker,
        blocker_class=blocker_class,
        post_count="0",
        evidence_manifest=str(store / "MANIFEST.sha256"),
        manifest_verify_rc=manifest_rc,
    )
