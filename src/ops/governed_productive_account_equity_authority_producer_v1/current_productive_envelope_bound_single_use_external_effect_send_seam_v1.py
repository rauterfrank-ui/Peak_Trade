"""CURRENT_PRODUCTIVE envelope-bound single-use External-Effect send seam.

Consumes Owner-GO
OWNER_GO_CURRENT_PRODUCTIVE_ENVELOPE_BOUND_SINGLE_USE_EXTERNAL_EFFECT_SEND_SEAM_V1.

Ratifies FINAL_ORDER_ENVELOPE -> SINGLE_USE_EXTERNAL_EFFECT_PERMIT ->
durable consume / replay protection -> Full-Core HTTP POST seam.
Standing EXTERNAL_EFFECT_AUTHORIZED remains false. STEP-29Q remains
PLAN_ONLY. No real venue POST is performed.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from src.governance.canonical_order_intent_v1 import CanonicalOrderIntentV1
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    CAP_11_1_SEND_CAPABLE_ADAPTER_CONSTRUCTED,
    ENVELOPE_BOUND_SINGLE_USE_EXTERNAL_EFFECT_SEAM,
    EXACT_ENVELOPE_REQUIRED,
    EXTERNAL_EFFECT_AUTHORIZED,
    FOLLOW_ON_SUBMIT_ISOLATED,
    FULL_CORE_ACTUAL_HTTP_POST_SEAM_IMPLEMENTED,
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    LIVE_ENABLED,
    MAX_EXTERNAL_EFFECT_POST_COUNT,
    POST_ALLOWED,
    PRODUCTIVE_WIRE_SEND_REACHABLE,
    REAL_EXTERNAL_EFFECT_AUTHORIZED,
    REAL_VENUE_POST_ALLOWED,
    REPLAY_PROTECTION_DURABLE,
    REPLAY_PROTECTION_PRESENT,
    SINGLE_USE_EXTERNAL_EFFECT_PERMIT,
    STANDING_LIVE_AUTHORIZATION,
    SUBMISSION_AUTHORIZED,
    SUBMIT_UNLOCKED,
    SUBMIT_UNLOCKED_ALONE_IS_NOT_SEND_PERMISSION,
    WIRE_SEND_PERMITTED,
    current_productive_first_real_blocker_v1,
)
from src.ops.full_core_live_path_composition_root_v1.envelope_bound_external_effect_send_seam_v1 import (
    FullCoreEnvelopeBoundSendSeamError,
    attempt_envelope_bound_external_effect_send_v1,
    prove_follow_on_submit_isolated_v1,
)
from src.ops.full_core_live_path_composition_root_v1.execution_admission_contract_v1 import (
    DurableKillSwitchEvidenceStatusV1,
)
from src.ops.full_core_live_path_composition_root_v1.external_effect_gate_v1 import (
    evaluate_external_effect_v1,
)
from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_v1 import (
    FullCoreExternalEffectPermitError,
    issue_external_effect_permit_v1,
)
from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
    bind_final_order_envelope_from_venue_plan_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_productive_http_post_transport_v1 import (
    FullCoreNonNetworkingTestPostTransportV1,
    FullCoreProductiveHttpPostError,
    FullCoreProductiveHttpTradeOrderTransportV1,
)
from src.ops.full_core_live_path_composition_root_v1.gated_productive_wire_transport_v1 import (
    FullCoreSendCredentialHandleV1,
)
from src.ops.full_core_live_path_composition_root_v1.live_admission_gap_dag_v1 import (
    gap_node_v1,
)
from src.ops.full_core_live_path_composition_root_v1.models_v1 import VenuePlanCandidateV1
from src.ops.full_core_live_path_composition_root_v1.submission_authorized_v1 import (
    STEP_29Q_PLAN_ONLY,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    CURRENT_PRODUCTIVE_ENVELOPE_BOUND_SINGLE_USE_EXTERNAL_EFFECT_SEND_SEAM_CREATED,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_live_authorized_and_cap_11_1_send_capable_adapter_v1 import (
    CANONICAL_PACK_RELPATH as DH_PACK_RELPATH,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.d4_d5_genesis_runtime_orchestrator_v1 import (
    persist_manifest_sha256_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    verify_manifest_sha256_v1,
)

OWNER_GO = "OWNER_GO_CURRENT_PRODUCTIVE_ENVELOPE_BOUND_SINGLE_USE_EXTERNAL_EFFECT_SEND_SEAM_V1"
THIS_SLICE = (
    "11.2.1.DI.FULL_CORE_CURRENT_PRODUCTIVE_ENVELOPE_BOUND_SINGLE_USE_EXTERNAL_EFFECT_SEND_SEAM"
)
EXPECTED_ORIGIN_MAIN_SHA = "836a89b4d4ff1eace55ad320a2d7c24b5227d155"
CANONICAL_PACK_RELPATH = (
    "evidence/ops/full_core_current_productive_envelope_bound_single_use_external_effect_send_seam_v1/"
    "20260915T212000Z"
)
AUTHORITY_REF = OWNER_GO
FALSE_TOKEN = "false"
TRUE_TOKEN = "true"
NEXT_OWNER_GO = (
    "OWNER_GO_REQUIRED_FOR_ACTUAL_VENUE_POST_WITH_FRESH_ENVELOPE_BOUND_SINGLE_USE_PERMIT"
)
_SECRET_TOKENS = ("secret", "passphrase", "api_key", "apikey", "private_key")


class CurrentProductiveEnvelopeBoundSendSeamError(ValueError):
    """Fail-closed envelope-bound send-seam persist violation."""


@dataclass(frozen=True)
class CurrentProductiveEnvelopeBoundSendSeamResultV1:
    store_root: str
    live_enabled: str
    live_armed: str
    wire_send_permitted: str
    live_authorized: str
    submission_authorized: str
    productive_wire_send_reachable: str
    envelope_bound_single_use_external_effect_seam: str
    exact_envelope_required: str
    single_use: str
    max_post_count: str
    replay_protection_present: str
    replay_protection_durable: str
    follow_on_submit_isolated: str
    full_core_actual_http_post_seam_implemented: str
    submit_unlocked_semantics: str
    external_effect_authorized: str
    real_external_effect_authorized: str
    step_29q_status: str
    step_29p_risk_admissible: str
    cap24_bound_instrument_id: str
    mocked_post_count: str
    real_post_count: str
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
            raise CurrentProductiveEnvelopeBoundSendSeamError(f"SECRET_TOKEN_PRESENT:{token}")


def _load_json_object(*, path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise CurrentProductiveEnvelopeBoundSendSeamError(f"JSON_NOT_OBJECT:{path.name}")
    return payload


def _token(value: bool) -> str:
    return TRUE_TOKEN if value is True else FALSE_TOKEN


def _assert_standing_pins() -> None:
    if CURRENT_PRODUCTIVE_ENVELOPE_BOUND_SINGLE_USE_EXTERNAL_EFFECT_SEND_SEAM_CREATED is not True:
        raise CurrentProductiveEnvelopeBoundSendSeamError("SEAM_NOT_CREATED")
    if ENVELOPE_BOUND_SINGLE_USE_EXTERNAL_EFFECT_SEAM is not True:
        raise CurrentProductiveEnvelopeBoundSendSeamError("ENVELOPE_BOUND_SEAM_NOT_TRUE")
    if EXACT_ENVELOPE_REQUIRED is not True:
        raise CurrentProductiveEnvelopeBoundSendSeamError("EXACT_ENVELOPE_NOT_REQUIRED")
    if SINGLE_USE_EXTERNAL_EFFECT_PERMIT is not True:
        raise CurrentProductiveEnvelopeBoundSendSeamError("SINGLE_USE_NOT_TRUE")
    if int(MAX_EXTERNAL_EFFECT_POST_COUNT) != 1:
        raise CurrentProductiveEnvelopeBoundSendSeamError("MAX_POST_COUNT_NOT_ONE")
    if REPLAY_PROTECTION_PRESENT is not True:
        raise CurrentProductiveEnvelopeBoundSendSeamError("REPLAY_PROTECTION_MISSING")
    if REPLAY_PROTECTION_DURABLE is not True:
        raise CurrentProductiveEnvelopeBoundSendSeamError("REPLAY_PROTECTION_NOT_DURABLE")
    if FOLLOW_ON_SUBMIT_ISOLATED is not True:
        raise CurrentProductiveEnvelopeBoundSendSeamError("FOLLOW_ON_NOT_ISOLATED")
    if FULL_CORE_ACTUAL_HTTP_POST_SEAM_IMPLEMENTED is not True:
        raise CurrentProductiveEnvelopeBoundSendSeamError("HTTP_POST_SEAM_NOT_IMPLEMENTED")
    if SUBMIT_UNLOCKED is not False:
        raise CurrentProductiveEnvelopeBoundSendSeamError("SUBMIT_UNLOCKED_MUST_REMAIN_FALSE")
    if SUBMIT_UNLOCKED_ALONE_IS_NOT_SEND_PERMISSION is not True:
        raise CurrentProductiveEnvelopeBoundSendSeamError("SUBMIT_UNLOCKED_SEMANTICS_DRIFT")
    if EXTERNAL_EFFECT_AUTHORIZED is not False:
        raise CurrentProductiveEnvelopeBoundSendSeamError("STANDING_EXTERNAL_EFFECT_NOT_FALSE")
    if REAL_EXTERNAL_EFFECT_AUTHORIZED is not False:
        raise CurrentProductiveEnvelopeBoundSendSeamError("REAL_EXTERNAL_EFFECT_NOT_FALSE")
    if REAL_VENUE_POST_ALLOWED is not False:
        raise CurrentProductiveEnvelopeBoundSendSeamError("REAL_VENUE_POST_ALLOWED_NOT_FALSE")
    if POST_ALLOWED is not False:
        raise CurrentProductiveEnvelopeBoundSendSeamError("POST_ALLOWED_NOT_FALSE")
    if LIVE_ENABLED is not True:
        raise CurrentProductiveEnvelopeBoundSendSeamError("LIVE_ENABLED_NOT_TRUE")
    if LIVE_ARMED is not True:
        raise CurrentProductiveEnvelopeBoundSendSeamError("LIVE_ARMED_NOT_TRUE")
    if WIRE_SEND_PERMITTED is not True:
        raise CurrentProductiveEnvelopeBoundSendSeamError("WIRE_SEND_PERMITTED_NOT_TRUE")
    if SUBMISSION_AUTHORIZED is not True:
        raise CurrentProductiveEnvelopeBoundSendSeamError("SUBMISSION_AUTHORIZED_NOT_TRUE")
    if LIVE_AUTHORIZED is not True:
        raise CurrentProductiveEnvelopeBoundSendSeamError("LIVE_AUTHORIZED_NOT_TRUE")
    if PRODUCTIVE_WIRE_SEND_REACHABLE is not True:
        raise CurrentProductiveEnvelopeBoundSendSeamError("WIRE_SEND_NOT_REACHABLE")
    if CAP_11_1_SEND_CAPABLE_ADAPTER_CONSTRUCTED is not True:
        raise CurrentProductiveEnvelopeBoundSendSeamError("SEND_CAPABLE_NOT_TRUE")
    if STANDING_LIVE_AUTHORIZATION is not False:
        raise CurrentProductiveEnvelopeBoundSendSeamError("STANDING_LIVE_AUTHORIZATION_TRUE")
    if gap_node_v1("EXTERNAL_EFFECT").implementation_status != (
        "ENVELOPE_BOUND_SINGLE_USE_SEAM_IMPLEMENTED_STANDING_FALSE"
    ):
        raise CurrentProductiveEnvelopeBoundSendSeamError("EXTERNAL_EFFECT_DAG_STATUS_DRIFT")


def _bind_current_dh_epoch(*, repo_root: Path) -> dict[str, Any]:
    claims_path = repo_root / DH_PACK_RELPATH / "claims.json"
    if not claims_path.is_file():
        raise CurrentProductiveEnvelopeBoundSendSeamError("DH_CLAIMS_MISSING")
    claims = _load_json_object(path=claims_path)
    if str(claims.get("LIVE_AUTHORIZED") or "") != TRUE_TOKEN:
        raise CurrentProductiveEnvelopeBoundSendSeamError("DH_LIVE_AUTHORIZED_NOT_TRUE")
    if str(claims.get("SUBMISSION_AUTHORIZED") or "") != TRUE_TOKEN:
        raise CurrentProductiveEnvelopeBoundSendSeamError("DH_SUBMISSION_NOT_TRUE")
    if str(claims.get("PRODUCTIVE_WIRE_SEND_REACHABLE") or "") != TRUE_TOKEN:
        raise CurrentProductiveEnvelopeBoundSendSeamError("DH_REACHABLE_NOT_TRUE")
    if str(claims.get("EXTERNAL_EFFECT_AUTHORIZED") or "") != FALSE_TOKEN:
        raise CurrentProductiveEnvelopeBoundSendSeamError("DH_EXTERNAL_EFFECT_NOT_FALSE")
    if str(claims.get("STEP_29Q_STATUS") or "") != STEP_29Q_PLAN_ONLY:
        raise CurrentProductiveEnvelopeBoundSendSeamError("DH_STEP_29Q_NOT_PLAN_ONLY")
    if str(claims.get("POST_COUNT") or "") != "0":
        raise CurrentProductiveEnvelopeBoundSendSeamError("DH_POST_COUNT_NOT_ZERO")
    if str(claims.get("STEP_29P_RISK_ADMISSIBLE") or "") != TRUE_TOKEN:
        raise CurrentProductiveEnvelopeBoundSendSeamError("DH_STEP_29P_NOT_TRUE")
    instrument_id = str(claims.get("CAP24_BOUND_INSTRUMENT_ID") or "").strip()
    if not instrument_id:
        raise CurrentProductiveEnvelopeBoundSendSeamError("DH_CAP24_ID_MISSING")
    if str(claims.get("FIRST_REAL_BLOCKER") or "") != "EXTERNAL_EFFECT_NOT_AUTHORIZED":
        raise CurrentProductiveEnvelopeBoundSendSeamError("DH_HISTORICAL_BLOCKER_DRIFT")
    return claims


def _fixture_plan_v1(*, instrument_id: str) -> VenuePlanCandidateV1:
    return VenuePlanCandidateV1(
        instrument_id=instrument_id,
        side="buy",
        quantity="1",
        order_type="market",
        td_mode="cross",
        reduce_only=False,
        clordid="pt-fc-envelope-bound-seam-di-v1",
        venue_native_payload={
            "instId": instrument_id,
            "ordType": "market",
            "side": "buy",
            "sz": "1",
            "tdMode": "cross",
        },
        quantity_source="CURRENT_PRODUCTIVE_FIXTURE_NOT_LIVE_ENVELOPE",
        side_source="CURRENT_PRODUCTIVE_FIXTURE_NOT_LIVE_ENVELOPE",
        instrument_source="DH_CAP24_BOUND_INSTRUMENT_ID",
        path_kind="FULL_CORE_CURRENT_PRODUCTIVE",
    )


def _plan_only_intent_v1() -> CanonicalOrderIntentV1:
    from decimal import Decimal

    return CanonicalOrderIntentV1(
        intent_id="step-29q-plan-only",
        intent_version="v1",
        decision_id="step-29q-plan-only",
        instrument_id="fixture-not-live",
        trading_epoch="fixture",
        canonical_trading_logic_version="v1",
        capital_envelope_ref="fixture",
        pre_sizing_risk_ref="fixture",
        sizing_result_ref="fixture",
        post_sizing_risk_ref="fixture",
        policy_digest="fixture",
        config_digest="fixture",
        implementation_digest="fixture",
        provenance_digest="fixture",
        side="buy",
        intent_action="PLAN_ONLY",
        quantity=Decimal("1"),
        quantity_unit="CONTRACTS",
        quantity_provenance="fixture",
        reduce_only=False,
        position_effect="OPEN",
        order_type_policy="market",
        price_policy="none",
        time_in_force_policy="GTC",
        max_slippage_policy="none",
        expected_position_side="net",
        instrument_metadata_ref="fixture",
        execution_eligible=True,
        submission_authorized=False,
    )


def execute_current_productive_envelope_bound_single_use_external_effect_send_seam_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    evidence_root: Path | None = None,
    repo_root: Path | None = None,
) -> CurrentProductiveEnvelopeBoundSendSeamResultV1:
    if owner_go != OWNER_GO:
        raise CurrentProductiveEnvelopeBoundSendSeamError("OWNER_GO_MISMATCH")
    if origin_main_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise CurrentProductiveEnvelopeBoundSendSeamError("ORIGIN_MAIN_SHA_MISMATCH")
    _assert_standing_pins()
    root = repo_root or Path(__file__).resolve().parents[3]
    dh = _bind_current_dh_epoch(repo_root=root)
    standing = evaluate_external_effect_v1()
    if standing.external_effect_authorized is True:
        raise CurrentProductiveEnvelopeBoundSendSeamError("STANDING_EXTERNAL_EFFECT_MUST_DENY")
    instrument_id = str(dh["CAP24_BOUND_INSTRUMENT_ID"])
    envelope = bind_final_order_envelope_from_venue_plan_v1(
        _fixture_plan_v1(instrument_id=instrument_id),
        admission_ref="DH_CAP24_AND_STANDING_ADMISSION",
        provenance_ref="FULL_CORE_TRANSFORMED_VENUE_PLAN_FIXTURE",
        creation_epoch="2026-09-15T21:20:00Z",
    )
    permit = issue_external_effect_permit_v1(
        envelope,
        authority_ref=AUTHORITY_REF,
        kill_switch_blocked=False,
        durable_kill_switch_evidence_status=(
            DurableKillSwitchEvidenceStatusV1.TRUSTED_PRESENT.value
        ),
        filegate_denied=False,
        step_29q_status=STEP_29Q_PLAN_ONLY,
    )
    try:
        issue_external_effect_permit_v1(
            envelope,
            authority_ref=AUTHORITY_REF,
            submission_authorized=False,
        )
    except FullCoreExternalEffectPermitError as exc:
        if "SUBMISSION_AUTHORIZED_FALSE" not in str(exc):
            raise CurrentProductiveEnvelopeBoundSendSeamError("SUBMISSION_DENY_MISSING") from exc
    else:
        raise CurrentProductiveEnvelopeBoundSendSeamError("SUBMISSION_DENY_MUST_RAISE")
    handle = FullCoreSendCredentialHandleV1(handle_id="full-core-envelope-bound-handle", bound=True)
    transport = FullCoreNonNetworkingTestPostTransportV1()
    store = Path(evidence_root) if evidence_root is not None else root / CANONICAL_PACK_RELPATH
    store.mkdir(parents=True, exist_ok=True)
    result = attempt_envelope_bound_external_effect_send_v1(
        envelope=envelope,
        permit=permit,
        store_root=store,
        transport=transport,
        handle=handle,
    )
    if result.mocked_post_count != 1 or result.real_post_count != 0:
        raise CurrentProductiveEnvelopeBoundSendSeamError("MOCKED_POST_COUNT_DRIFT")
    if result.venue_live_contact is True:
        raise CurrentProductiveEnvelopeBoundSendSeamError("VENUE_LIVE_CONTACT")
    if transport.post_count != 1:
        raise CurrentProductiveEnvelopeBoundSendSeamError("TRANSPORT_POST_COUNT_DRIFT")
    isolated = prove_follow_on_submit_isolated_v1(
        envelope=envelope,
        permit=permit,
        store_root=store,
        transport=transport,
        handle=handle,
    )
    if isolated is not True:
        raise CurrentProductiveEnvelopeBoundSendSeamError("FOLLOW_ON_NOT_DENIED")
    if transport.post_count != 1:
        raise CurrentProductiveEnvelopeBoundSendSeamError("FOLLOW_ON_POSTED")
    try:
        attempt_envelope_bound_external_effect_send_v1(
            envelope=envelope,
            permit=None,
            store_root=store / "no-permit",
            transport=FullCoreNonNetworkingTestPostTransportV1(),
            handle=handle,
        )
    except FullCoreEnvelopeBoundSendSeamError as exc:
        if str(exc) != "NO_PERMIT":
            raise CurrentProductiveEnvelopeBoundSendSeamError("NO_PERMIT_DENY_MISSING") from exc
    else:
        raise CurrentProductiveEnvelopeBoundSendSeamError("NO_PERMIT_MUST_RAISE")
    try:
        attempt_envelope_bound_external_effect_send_v1(
            envelope=envelope,
            permit=permit,
            store_root=store / "direct-29q",
            transport=FullCoreNonNetworkingTestPostTransportV1(),
            handle=handle,
            canonical_intent=_plan_only_intent_v1(),
        )
    except FullCoreEnvelopeBoundSendSeamError as exc:
        if str(exc) != "DIRECT_STEP_29Q_SUBMISSION_FORBIDDEN":
            raise CurrentProductiveEnvelopeBoundSendSeamError("DIRECT_29Q_DENY_MISSING") from exc
    else:
        raise CurrentProductiveEnvelopeBoundSendSeamError("DIRECT_29Q_MUST_RAISE")
    http_transport = FullCoreProductiveHttpTradeOrderTransportV1(handle=handle)
    try:
        http_transport.post_trade_order(
            payload={"instId": instrument_id},
            permit_id=permit.permit_id,
            envelope_id=envelope.envelope_id,
            envelope_digest=envelope.envelope_digest,
        )
    except FullCoreProductiveHttpPostError as exc:
        if "REAL_VENUE_POST_FORBIDDEN_IN_THIS_SLICE" not in str(exc):
            raise CurrentProductiveEnvelopeBoundSendSeamError("HTTP_FORBIDDEN_MISSING") from exc
    else:
        raise CurrentProductiveEnvelopeBoundSendSeamError("HTTP_MUST_NOT_POST")
    if http_transport.post_count != 0:
        raise CurrentProductiveEnvelopeBoundSendSeamError("HTTP_TRANSPORT_SIDE_EFFECT")
    first_blocker = current_productive_first_real_blocker_v1()
    if first_blocker != NEXT_OWNER_GO:
        raise CurrentProductiveEnvelopeBoundSendSeamError(f"BLOCKER_DRIFT:{first_blocker}")
    blocker_class = "E"
    claims = {
        "THIS_SLICE": THIS_SLICE,
        "OWNER_GO": OWNER_GO,
        "EXPECTED_ORIGIN_MAIN": origin_main_sha,
        "ENVELOPE_BOUND_SINGLE_USE_EXTERNAL_EFFECT_SEAM": TRUE_TOKEN,
        "EXACT_ENVELOPE_REQUIRED": TRUE_TOKEN,
        "SINGLE_USE": TRUE_TOKEN,
        "MAX_POST_COUNT": "1",
        "REPLAY_PROTECTION_PRESENT": TRUE_TOKEN,
        "REPLAY_PROTECTION_DURABLE": TRUE_TOKEN,
        "FOLLOW_ON_SUBMIT_ISOLATED": TRUE_TOKEN,
        "FULL_CORE_ACTUAL_HTTP_POST_SEAM_IMPLEMENTED": TRUE_TOKEN,
        "SUBMIT_UNLOCKED": FALSE_TOKEN,
        "SUBMIT_UNLOCKED_ALONE_IS_NOT_SEND_PERMISSION": TRUE_TOKEN,
        "LIVE_ENABLED": _token(LIVE_ENABLED is True),
        "LIVE_ARMED": _token(LIVE_ARMED is True),
        "WIRE_SEND_PERMITTED": _token(WIRE_SEND_PERMITTED is True),
        "SUBMISSION_AUTHORIZED": _token(SUBMISSION_AUTHORIZED is True),
        "LIVE_AUTHORIZED": _token(LIVE_AUTHORIZED is True),
        "PRODUCTIVE_WIRE_SEND_REACHABLE": _token(PRODUCTIVE_WIRE_SEND_REACHABLE is True),
        "CAP_11_1_SEND_CAPABLE_ADAPTER_CONSTRUCTED": TRUE_TOKEN,
        "STANDING_LIVE_AUTHORIZATION": _token(STANDING_LIVE_AUTHORIZATION is True),
        "EXTERNAL_EFFECT_AUTHORIZED": _token(EXTERNAL_EFFECT_AUTHORIZED is True),
        "REAL_EXTERNAL_EFFECT_AUTHORIZED": FALSE_TOKEN,
        "REAL_VENUE_POST_ALLOWED": FALSE_TOKEN,
        "POST_ALLOWED": FALSE_TOKEN,
        "STEP_29Q_STATUS": STEP_29Q_PLAN_ONLY,
        "STEP_29Q_BLOCKS_POST": FALSE_TOKEN,
        "MOCKED_POST_COUNT": str(result.mocked_post_count),
        "REAL_POST_COUNT": "0",
        "POST_COUNT": "0",
        "ACTUAL_ORDER_SUBMIT_PERFORMED": FALSE_TOKEN,
        "VENUE_MUTATION_PERFORMED": FALSE_TOKEN,
        "AUTONOMOUS_FOLLOW_ON_EXECUTION_ALLOWED": FALSE_TOKEN,
        "STEP_29P_RISK_ADMISSIBLE": str(dh["STEP_29P_RISK_ADMISSIBLE"]),
        "CAP24_BOUND_INSTRUMENT_ID": instrument_id,
        "DH_PACK": DH_PACK_RELPATH,
        "FIRST_REAL_BLOCKER": first_blocker,
        "BLOCKER_CLASS": blocker_class,
        "NEXT_OWNER_GO_REQUIRED": NEXT_OWNER_GO,
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
        "DH_OWNER_GO": str(dh.get("OWNER_GO") or ""),
        "DH_FIRST_REAL_BLOCKER": str(dh.get("FIRST_REAL_BLOCKER") or ""),
        "CAP24_BOUND_INSTRUMENT_ID": instrument_id,
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
        "EXTERNAL_EFFECT_STANDING_UNCHANGED_FALSE": TRUE_TOKEN,
        "LIVE_ENABLED_UNCHANGED_TRUE": TRUE_TOKEN,
        "LIVE_ARMED_UNCHANGED_TRUE": TRUE_TOKEN,
        "WIRE_SEND_PERMITTED_UNCHANGED_TRUE": TRUE_TOKEN,
        "SUBMISSION_AUTHORIZED_UNCHANGED_TRUE": TRUE_TOKEN,
        "LIVE_AUTHORIZED_UNCHANGED_TRUE": TRUE_TOKEN,
    }
    summary = {
        "FIRST_REAL_BLOCKER": first_blocker,
        "BLOCKER_CLASS": blocker_class,
        "ENVELOPE_BOUND_SINGLE_USE_EXTERNAL_EFFECT_SEAM": TRUE_TOKEN,
        "SINGLE_USE": TRUE_TOKEN,
        "MAX_POST_COUNT": "1",
        "REPLAY_PROTECTION_DURABLE": TRUE_TOKEN,
        "FOLLOW_ON_SUBMIT_ISOLATED": TRUE_TOKEN,
        "FULL_CORE_ACTUAL_HTTP_POST_SEAM_IMPLEMENTED": TRUE_TOKEN,
        "EXTERNAL_EFFECT_AUTHORIZED": FALSE_TOKEN,
        "REAL_EXTERNAL_EFFECT_AUTHORIZED": FALSE_TOKEN,
        "STEP_29Q_STATUS": STEP_29Q_PLAN_ONLY,
        "MOCKED_POST_COUNT": str(result.mocked_post_count),
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
    return CurrentProductiveEnvelopeBoundSendSeamResultV1(
        store_root=str(store),
        live_enabled=_token(LIVE_ENABLED is True),
        live_armed=_token(LIVE_ARMED is True),
        wire_send_permitted=_token(WIRE_SEND_PERMITTED is True),
        live_authorized=_token(LIVE_AUTHORIZED is True),
        submission_authorized=_token(SUBMISSION_AUTHORIZED is True),
        productive_wire_send_reachable=_token(PRODUCTIVE_WIRE_SEND_REACHABLE is True),
        envelope_bound_single_use_external_effect_seam=TRUE_TOKEN,
        exact_envelope_required=TRUE_TOKEN,
        single_use=TRUE_TOKEN,
        max_post_count="1",
        replay_protection_present=TRUE_TOKEN,
        replay_protection_durable=TRUE_TOKEN,
        follow_on_submit_isolated=_token(isolated is True),
        full_core_actual_http_post_seam_implemented=TRUE_TOKEN,
        submit_unlocked_semantics="SUBMIT_UNLOCKED_ALONE_IS_NOT_SEND_PERMISSION",
        external_effect_authorized=FALSE_TOKEN,
        real_external_effect_authorized=FALSE_TOKEN,
        step_29q_status=STEP_29Q_PLAN_ONLY,
        step_29p_risk_admissible=str(dh["STEP_29P_RISK_ADMISSIBLE"]),
        cap24_bound_instrument_id=instrument_id,
        mocked_post_count=str(result.mocked_post_count),
        real_post_count="0",
        first_real_blocker=first_blocker,
        blocker_class=blocker_class,
        post_count="0",
        evidence_manifest=str(store / "MANIFEST.sha256"),
        manifest_verify_rc=manifest_rc,
    )
