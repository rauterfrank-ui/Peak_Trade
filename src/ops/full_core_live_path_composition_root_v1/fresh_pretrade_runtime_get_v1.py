"""Typed Full-Core Fresh Pretrade Runtime GET seam. No POST. No wire. No arming.

Collects the Owner-adjudicated required pretrade GET set through an injectable
GET-only port. Canary HTTP clients remain non-Full-Core transport. Missing,
malformed, stale, contradictory, auth-failed, or public-failed required GETs
fail-closed. Trusted GET evidence does not admit Live and does not set
LIVE_ENABLED / LIVE_ARMED / WIRE_SEND_PERMITTED.

Freshness is FRESH_GET_PER_PRETRADE_DECISION (decision-bound). Not a TTL.
Injected test doubles cannot claim productive venue contact.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional, Protocol, Tuple
from urllib.parse import urlencode

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    LIVE_ARMED,
    LIVE_ENABLED,
    OFFLINE_BOUNDARY_ROLE,
    WIRE_SEND_PERMITTED,
)
from src.ops.full_core_live_path_composition_root_v1.execution_admission_contract_v1 import (
    ADMISSION_CONTEXT_LIVE,
    ExecutionAdmissionInputsV1,
    FreshPretradeGetStatusV1,
    PRETRADE_SOURCE_FRESH_GET,
    PRETRADE_SOURCE_FROZEN_OFFLINE,
    PretradeFreshnessStatusV1,
)
from src.ops.full_core_live_path_composition_root_v1.owner_one_shot_permit_v1 import (
    join_owner_one_shot_permit_into_admission_inputs_v1,
)

JOIN_SEAM_ID = "FULL_CORE_FRESH_PRETRADE_RUNTIME_GET_SEAM_V1"
FRESH_PRETRADE_GET_AUTHORITY = "VENUE_PRETRADE_GATES"
FRESHNESS_POLICY = "FRESH_GET_PER_PRETRADE_DECISION"
TRANSPORT_CLASS_INJECTED_TEST_DOUBLE = "INJECTED_TEST_DOUBLE"
TRANSPORT_CLASS_MISSING = "TRANSPORT_MISSING"
METHOD_GET = "GET"

ENDPOINT_PUBLIC_INSTRUMENTS = "/api/v5/public/instruments"
ENDPOINT_PUBLIC_PRICE_LIMIT = "/api/v5/public/price-limit"
ENDPOINT_ACCOUNT_MAX_SIZE = "/api/v5/account/max-size"
ENDPOINT_ACCOUNT_LEVERAGE_INFO = "/api/v5/account/leverage-info"
ENDPOINT_ACCOUNT_CONFIG = "/api/v5/account/config"
ENDPOINT_ACCOUNT_POSITIONS = "/api/v5/account/positions"
ENDPOINT_ACCOUNT_BALANCE = "/api/v5/account/balance"

_HISTORICAL_OR_FIXTURE_MARKERS = (
    "HISTORICAL",
    "FIXTURE",
    "REPLAY",
    "FROZEN_OFFLINE",
    "6148",
    "Z2AR",
    "Z2V",
)


@dataclass(frozen=True)
class FreshPretradeGetItemSpecV1:
    item_id: str
    endpoint_path: str
    auth_required: bool
    fetch_group: str


REQUIRED_GET_ITEM_SPECS: Tuple[FreshPretradeGetItemSpecV1, ...] = (
    FreshPretradeGetItemSpecV1(
        "INSTRUMENT_STATE", ENDPOINT_PUBLIC_INSTRUMENTS, False, "instruments"
    ),
    FreshPretradeGetItemSpecV1("MAX_SIZE", ENDPOINT_PUBLIC_INSTRUMENTS, False, "instruments"),
    FreshPretradeGetItemSpecV1("PRICE_BAND", ENDPOINT_PUBLIC_PRICE_LIMIT, False, "price_limit"),
    FreshPretradeGetItemSpecV1("MAX_AVAILABLE", ENDPOINT_ACCOUNT_MAX_SIZE, True, "max_size"),
    FreshPretradeGetItemSpecV1("LEVERAGE", ENDPOINT_ACCOUNT_LEVERAGE_INFO, True, "leverage"),
    FreshPretradeGetItemSpecV1("POS_MODE", ENDPOINT_ACCOUNT_CONFIG, True, "config"),
    FreshPretradeGetItemSpecV1("ACCOUNT_MODE", ENDPOINT_ACCOUNT_CONFIG, True, "config"),
    FreshPretradeGetItemSpecV1("MARGIN_MODE", ENDPOINT_ACCOUNT_POSITIONS, True, "positions"),
    FreshPretradeGetItemSpecV1("AVAILABLE_MARGIN", ENDPOINT_ACCOUNT_BALANCE, True, "balance"),
)

PUBLIC_GET_PATHS: frozenset[str] = frozenset(
    spec.endpoint_path for spec in REQUIRED_GET_ITEM_SPECS if not spec.auth_required
)
PRIVATE_GET_PATHS: frozenset[str] = frozenset(
    spec.endpoint_path for spec in REQUIRED_GET_ITEM_SPECS if spec.auth_required
)


@dataclass(frozen=True)
class FreshPretradeGetTransportResultV1:
    get_performed: bool
    method: str
    endpoint: str
    http_status: int
    payload: Any
    auth_header_sent: bool
    transport_class: str
    venue_live_contact: bool
    historical_reuse: bool
    error_class: str
    body_sha256: str = ""


class FullCoreFreshPretradeGetTransportV1(Protocol):
    """GET-only Full-Core port. Implementations must not POST or send wire."""

    def get(
        self,
        *,
        endpoint: str,
        auth_required: bool,
        pretrade_decision_id: str,
    ) -> FreshPretradeGetTransportResultV1:
        """Issue exactly one GET. Must not POST."""


@dataclass(frozen=True)
class FreshPretradeGetItemEvidenceV1:
    item_id: str
    endpoint_path: str
    auth_required: bool
    evidence_status: str
    reason_codes: Tuple[str, ...]
    get_performed: bool
    method: str
    http_status: int
    auth_header_sent: bool
    historical_reuse: bool
    transport_class: str
    venue_live_contact: bool
    observed_account_uids: Tuple[str, ...] = ()
    observed_inst_ids: Tuple[str, ...] = ()
    observed_td_modes: Tuple[str, ...] = ()
    identity_fields_malformed: bool = False


@dataclass(frozen=True)
class FreshPretradeRuntimeGetEvidenceV1:
    evidence_status: str
    pretrade_source_kind: str
    pretrade_freshness_status: str
    pretrade_decision_id: str
    items: Tuple[FreshPretradeGetItemEvidenceV1, ...]
    reason_codes: Tuple[str, ...]
    get_performed: bool
    venue_live_contact: bool
    live_enabled: bool
    live_armed: bool
    wire_send_permitted: bool
    post_attempted: bool
    join_seam_id: str = JOIN_SEAM_ID
    authority: str = FRESH_PRETRADE_GET_AUTHORITY
    freshness_policy: str = FRESHNESS_POLICY


def _endpoint_path_only(endpoint: str) -> str:
    return str(endpoint or "").strip().split("?", 1)[0]


def contains_fixture_or_historical_marker_v1(value: str) -> bool:
    text = str(value or "")
    folded = text.upper()
    return any(marker in folded for marker in _HISTORICAL_OR_FIXTURE_MARKERS)


_contains_fixture_or_historical_marker = contains_fixture_or_historical_marker_v1


def extract_identity_fields_from_payload_v1(
    payload: Any,
) -> tuple[Tuple[str, ...], Tuple[str, ...], Tuple[str, ...], bool]:
    """Extract typed identity fields. Non-string values are malformed, not truthy."""
    uids: list[str] = []
    inst_ids: list[str] = []
    td_modes: list[str] = []
    malformed = False
    if not isinstance(payload, Mapping):
        return (), (), (), False
    data = payload.get("data")
    if not isinstance(data, list):
        return (), (), (), False
    for row in data:
        if not isinstance(row, Mapping):
            continue
        if "uid" in row:
            uid = row.get("uid")
            if not isinstance(uid, str) or uid == "" or uid != uid.strip():
                malformed = True
            else:
                uids.append(uid)
        if "instId" in row:
            inst = row.get("instId")
            if not isinstance(inst, str) or inst == "" or inst != inst.strip():
                malformed = True
            else:
                inst_ids.append(inst)
        for key in ("tdMode", "mgnMode"):
            if key not in row:
                continue
            mode = row.get(key)
            if not isinstance(mode, str) or mode == "" or mode != mode.strip():
                malformed = True
            else:
                td_modes.append(mode)
    return tuple(uids), tuple(inst_ids), tuple(td_modes), malformed


def build_required_get_endpoint_v1(
    spec: FreshPretradeGetItemSpecV1,
    *,
    instrument_id: str,
    td_mode: str,
    limit_px: str,
    inst_type: str = "FUTURES",
) -> str:
    path = spec.endpoint_path
    inst = str(instrument_id or "").strip()
    mode = str(td_mode or "").strip()
    px = str(limit_px or "").strip()
    itype = str(inst_type or "").strip() or "FUTURES"
    if path == ENDPOINT_PUBLIC_INSTRUMENTS:
        return f"{path}?{urlencode({'instType': itype, 'instId': inst})}"
    if path == ENDPOINT_PUBLIC_PRICE_LIMIT:
        return f"{path}?{urlencode({'instId': inst})}"
    if path == ENDPOINT_ACCOUNT_MAX_SIZE:
        params = [("instId", inst), ("tdMode", mode)]
        if px:
            params.append(("px", px))
        return f"{path}?{urlencode(params)}"
    if path == ENDPOINT_ACCOUNT_LEVERAGE_INFO:
        return f"{path}?{urlencode({'instId': inst, 'mgnMode': mode})}"
    return path


def _item_status_and_reasons(
    *,
    spec: FreshPretradeGetItemSpecV1,
    result: FreshPretradeGetTransportResultV1 | None,
    pretrade_decision_id: str,
    requested_endpoint: str,
) -> Tuple[str, Tuple[str, ...]]:
    prefix = spec.item_id
    if result is None:
        return FreshPretradeGetStatusV1.MISSING.value, (f"{prefix}_GET_MISSING",)
    reasons: list[str] = []
    method = str(result.method or "")
    if method and method != METHOD_GET:
        return FreshPretradeGetStatusV1.CONTRADICTORY.value, (
            f"{prefix}_POST_OR_NON_GET_FORBIDDEN",
            "FRESH_PRETRADE_GET_POST_FORBIDDEN",
        )
    if result.historical_reuse is True:
        reasons.append(f"{prefix}_STALE_HISTORICAL_REUSE")
        reasons.append("FRESH_PRETRADE_GET_FIXTURE_REPLAY_NOT_PRODUCTIVE")
        return FreshPretradeGetStatusV1.STALE.value, tuple(reasons)
    if _contains_fixture_or_historical_marker(pretrade_decision_id) or (
        _contains_fixture_or_historical_marker(str(result.endpoint or ""))
    ):
        reasons.append(f"{prefix}_FIXTURE_OR_REPLAY_MARKER")
        reasons.append("FRESH_PRETRADE_GET_FIXTURE_REPLAY_NOT_PRODUCTIVE")
        return FreshPretradeGetStatusV1.STALE.value, tuple(reasons)
    transport_class = str(result.transport_class or "")
    if transport_class == TRANSPORT_CLASS_MISSING or result.get_performed is not True:
        return FreshPretradeGetStatusV1.MISSING.value, (f"{prefix}_GET_NOT_PERFORMED",)
    if transport_class != TRANSPORT_CLASS_INJECTED_TEST_DOUBLE:
        return FreshPretradeGetStatusV1.CONTRADICTORY.value, (
            f"{prefix}_TRANSPORT_CLASS_NOT_BOUND",
        )
    if result.venue_live_contact is True:
        return FreshPretradeGetStatusV1.CONTRADICTORY.value, (
            f"{prefix}_INJECTED_DOUBLE_CANNOT_CLAIM_VENUE_CONTACT",
        )
    path = _endpoint_path_only(result.endpoint or requested_endpoint)
    if path != spec.endpoint_path:
        return FreshPretradeGetStatusV1.CONTRADICTORY.value, (f"{prefix}_ENDPOINT_MISMATCH",)
    error_class = str(result.error_class or "")
    if error_class in {"AUTH_ERROR", "AUTH_FAILURE"} or int(result.http_status) in {
        401,
        403,
    }:
        if spec.auth_required:
            return FreshPretradeGetStatusV1.AUTH_FAILURE.value, (
                f"{prefix}_AUTH_FAILURE",
                "FRESH_PRETRADE_GET_AUTH_FAILURE",
            )
        return FreshPretradeGetStatusV1.PUBLIC_FAILURE.value, (
            f"{prefix}_PUBLIC_FAILURE",
            "FRESH_PRETRADE_GET_PUBLIC_FAILURE",
        )
    if spec.auth_required and result.auth_header_sent is not True:
        return FreshPretradeGetStatusV1.AUTH_FAILURE.value, (
            f"{prefix}_AUTH_HEADER_MISSING",
            "FRESH_PRETRADE_GET_AUTH_FAILURE",
        )
    if int(result.http_status) != 200:
        if spec.auth_required:
            return FreshPretradeGetStatusV1.AUTH_FAILURE.value, (
                f"{prefix}_PRIVATE_HTTP_FAILURE",
                "FRESH_PRETRADE_GET_AUTH_FAILURE",
            )
        return FreshPretradeGetStatusV1.PUBLIC_FAILURE.value, (
            f"{prefix}_PUBLIC_HTTP_FAILURE",
            "FRESH_PRETRADE_GET_PUBLIC_FAILURE",
        )
    payload = result.payload
    if not isinstance(payload, Mapping):
        return FreshPretradeGetStatusV1.MALFORMED.value, (f"{prefix}_PAYLOAD_NOT_MAPPING",)
    if "code" not in payload or "data" not in payload:
        return FreshPretradeGetStatusV1.MALFORMED.value, (f"{prefix}_PAYLOAD_FIELDS_MISSING",)
    code = payload.get("code")
    if code != "0":
        return FreshPretradeGetStatusV1.MALFORMED.value, (f"{prefix}_VENUE_CODE_NOT_EXACT_ZERO",)
    data = payload.get("data")
    if not isinstance(data, list) or not data:
        return FreshPretradeGetStatusV1.MALFORMED.value, (f"{prefix}_DATA_EMPTY_OR_NOT_LIST",)
    return FreshPretradeGetStatusV1.TRUSTED_PRESENT.value, (f"{prefix}_TRUSTED_PRESENT",)


_STATUS_RANK = {
    FreshPretradeGetStatusV1.CONTRADICTORY.value: 0,
    FreshPretradeGetStatusV1.AUTH_FAILURE.value: 1,
    FreshPretradeGetStatusV1.PUBLIC_FAILURE.value: 2,
    FreshPretradeGetStatusV1.MALFORMED.value: 3,
    FreshPretradeGetStatusV1.STALE.value: 4,
    FreshPretradeGetStatusV1.MISSING.value: 5,
    FreshPretradeGetStatusV1.NOT_REQUIRED_OFFLINE.value: 6,
    FreshPretradeGetStatusV1.TRUSTED_PRESENT.value: 7,
}


def _worst_status(statuses: Tuple[str, ...]) -> str:
    if not statuses:
        return FreshPretradeGetStatusV1.MISSING.value
    return min(statuses, key=lambda item: _STATUS_RANK.get(item, -1))


def collect_fresh_pretrade_runtime_get_v1(
    *,
    pretrade_decision_id: str,
    instrument_id: str,
    td_mode: str,
    limit_px: str = "",
    inst_type: str = "FUTURES",
    transport: FullCoreFreshPretradeGetTransportV1 | None,
    require_collection: bool,
) -> FreshPretradeRuntimeGetEvidenceV1:
    standing_true = LIVE_ENABLED is True or LIVE_ARMED is True or WIRE_SEND_PERMITTED is True
    extra: Tuple[str, ...] = ("STANDING_LIVE_GATE_TRUE",) if standing_true else ()
    decision = str(pretrade_decision_id or "")
    if require_collection is not True:
        return FreshPretradeRuntimeGetEvidenceV1(
            evidence_status=FreshPretradeGetStatusV1.NOT_REQUIRED_OFFLINE.value,
            pretrade_source_kind=PRETRADE_SOURCE_FROZEN_OFFLINE,
            pretrade_freshness_status=PretradeFreshnessStatusV1.FROZEN_OFFLINE.value,
            pretrade_decision_id=decision,
            items=(),
            reason_codes=("FRESH_PRETRADE_GET_NOT_REQUIRED_OFFLINE", JOIN_SEAM_ID, *extra),
            get_performed=False,
            venue_live_contact=False,
            live_enabled=False,
            live_armed=False,
            wire_send_permitted=False,
            post_attempted=False,
        )
    if not isinstance(decision, str) or decision == "" or decision != decision.strip():
        return FreshPretradeRuntimeGetEvidenceV1(
            evidence_status=FreshPretradeGetStatusV1.MALFORMED.value,
            pretrade_source_kind=PRETRADE_SOURCE_FRESH_GET,
            pretrade_freshness_status=PretradeFreshnessStatusV1.UNKNOWN.value,
            pretrade_decision_id=decision,
            items=(),
            reason_codes=("FRESH_PRETRADE_GET_DECISION_ID_MALFORMED", *extra),
            get_performed=False,
            venue_live_contact=False,
            live_enabled=False,
            live_armed=False,
            wire_send_permitted=False,
            post_attempted=False,
        )
    if not str(instrument_id or "").strip() or not str(td_mode or "").strip():
        return FreshPretradeRuntimeGetEvidenceV1(
            evidence_status=FreshPretradeGetStatusV1.MALFORMED.value,
            pretrade_source_kind=PRETRADE_SOURCE_FRESH_GET,
            pretrade_freshness_status=PretradeFreshnessStatusV1.UNKNOWN.value,
            pretrade_decision_id=decision,
            items=(),
            reason_codes=("FRESH_PRETRADE_GET_REQUEST_IDENTITY_MALFORMED", *extra),
            get_performed=False,
            venue_live_contact=False,
            live_enabled=False,
            live_armed=False,
            wire_send_permitted=False,
            post_attempted=False,
        )

    group_results: dict[str, FreshPretradeGetTransportResultV1 | None] = {}
    post_attempted = False
    for spec in REQUIRED_GET_ITEM_SPECS:
        if spec.fetch_group in group_results:
            continue
        requested = build_required_get_endpoint_v1(
            spec,
            instrument_id=instrument_id,
            td_mode=td_mode,
            limit_px=limit_px,
            inst_type=inst_type,
        )
        if transport is None:
            group_results[spec.fetch_group] = FreshPretradeGetTransportResultV1(
                get_performed=False,
                method=METHOD_GET,
                endpoint=requested,
                http_status=0,
                payload=None,
                auth_header_sent=False,
                transport_class=TRANSPORT_CLASS_MISSING,
                venue_live_contact=False,
                historical_reuse=False,
                error_class="TRANSPORT_MISSING",
            )
            continue
        result = transport.get(
            endpoint=requested,
            auth_required=spec.auth_required,
            pretrade_decision_id=decision,
        )
        if str(getattr(result, "method", METHOD_GET) or "") != METHOD_GET:
            post_attempted = True
        group_results[spec.fetch_group] = result

    items: list[FreshPretradeGetItemEvidenceV1] = []
    seen_payload_by_group: dict[str, str] = {}
    for spec in REQUIRED_GET_ITEM_SPECS:
        result = group_results.get(spec.fetch_group)
        requested = build_required_get_endpoint_v1(
            spec,
            instrument_id=instrument_id,
            td_mode=td_mode,
            limit_px=limit_px,
            inst_type=inst_type,
        )
        status, reasons = _item_status_and_reasons(
            spec=spec,
            result=result,
            pretrade_decision_id=decision,
            requested_endpoint=requested,
        )
        body_key = ""
        if result is not None:
            body_key = str(result.body_sha256 or "") or repr(result.payload)
        prior = seen_payload_by_group.get(spec.fetch_group)
        if prior is not None and body_key != prior:
            status = FreshPretradeGetStatusV1.CONTRADICTORY.value
            reasons = reasons + (f"{spec.item_id}_DUPLICATE_AMBIGUOUS_PAYLOAD",)
        else:
            seen_payload_by_group[spec.fetch_group] = body_key
        payload = result.payload if result is not None else None
        uids, inst_ids, td_modes, identity_malformed = extract_identity_fields_from_payload_v1(
            payload
        )
        items.append(
            FreshPretradeGetItemEvidenceV1(
                item_id=spec.item_id,
                endpoint_path=spec.endpoint_path,
                auth_required=spec.auth_required,
                evidence_status=status,
                reason_codes=reasons,
                get_performed=bool(result.get_performed) if result is not None else False,
                method=str(result.method or "") if result is not None else "",
                http_status=int(result.http_status) if result is not None else 0,
                auth_header_sent=bool(result.auth_header_sent) if result is not None else False,
                historical_reuse=bool(result.historical_reuse) if result is not None else False,
                transport_class=str(result.transport_class or "") if result is not None else "",
                venue_live_contact=bool(result.venue_live_contact) if result is not None else False,
                observed_account_uids=uids,
                observed_inst_ids=inst_ids,
                observed_td_modes=td_modes,
                identity_fields_malformed=identity_malformed,
            )
        )

    present_ids = {item.item_id for item in items}
    required_ids = {spec.item_id for spec in REQUIRED_GET_ITEM_SPECS}
    aggregate_reasons: list[str] = []
    statuses = tuple(item.evidence_status for item in items)
    if present_ids != required_ids:
        statuses = statuses + (FreshPretradeGetStatusV1.MISSING.value,)
        aggregate_reasons.append("FRESH_PRETRADE_GET_REQUIRED_ITEM_MISSING")
    for item in items:
        aggregate_reasons.extend(item.reason_codes)
    if post_attempted:
        statuses = statuses + (FreshPretradeGetStatusV1.CONTRADICTORY.value,)
        aggregate_reasons.append("FRESH_PRETRADE_GET_POST_FORBIDDEN")
    aggregate = _worst_status(statuses)
    trusted = aggregate == FreshPretradeGetStatusV1.TRUSTED_PRESENT.value and all(
        item.evidence_status == FreshPretradeGetStatusV1.TRUSTED_PRESENT.value for item in items
    )
    if trusted:
        freshness = PretradeFreshnessStatusV1.LIVE_FRESH.value
        source = PRETRADE_SOURCE_FRESH_GET
        aggregate = FreshPretradeGetStatusV1.TRUSTED_PRESENT.value
        aggregate_reasons.append("FRESH_PRETRADE_GET_TRUSTED_PRESENT")
    else:
        source = PRETRADE_SOURCE_FRESH_GET
        if aggregate == FreshPretradeGetStatusV1.STALE.value:
            freshness = PretradeFreshnessStatusV1.STALE.value
        elif aggregate == FreshPretradeGetStatusV1.MISSING.value:
            freshness = PretradeFreshnessStatusV1.MISSING.value
        else:
            freshness = PretradeFreshnessStatusV1.UNKNOWN.value
    any_performed = any(item.get_performed for item in items)
    return FreshPretradeRuntimeGetEvidenceV1(
        evidence_status=aggregate,
        pretrade_source_kind=source,
        pretrade_freshness_status=freshness,
        pretrade_decision_id=decision,
        items=tuple(items),
        reason_codes=tuple(dict.fromkeys((*aggregate_reasons, JOIN_SEAM_ID, *extra))),
        get_performed=any_performed,
        venue_live_contact=False,
        live_enabled=False,
        live_armed=False,
        wire_send_permitted=False,
        post_attempted=post_attempted,
    )


def join_fresh_pretrade_runtime_get_into_admission_inputs_v1(
    *,
    plan_identity: str,
    venue_plan_identity: str,
    instrument_identity_ok: bool,
    pretrade_admissible: bool,
    pretrade_source_kind: str,
    pretrade_freshness_status: str,
    capital_risk_mode: str,
    owner_go: Any,
    admission_context: str,
    provenance_refs: Tuple[str, ...] = (),
    state_path: Optional[str] = None,
    transport: FullCoreFreshPretradeGetTransportV1 | None = None,
    pretrade_decision_id: str = "",
    instrument_id: str = "",
    td_mode: str = "",
    limit_px: str = "",
    inst_type: str = "FUTURES",
    precomputed_evidence: FreshPretradeRuntimeGetEvidenceV1 | None = None,
) -> ExecutionAdmissionInputsV1:
    live_context = admission_context == ADMISSION_CONTEXT_LIVE
    evidence = precomputed_evidence
    if evidence is None:
        evidence = collect_fresh_pretrade_runtime_get_v1(
            pretrade_decision_id=pretrade_decision_id or plan_identity,
            instrument_id=instrument_id,
            td_mode=td_mode,
            limit_px=limit_px,
            inst_type=inst_type,
            transport=transport,
            require_collection=live_context,
        )
    if live_context:
        source_kind = evidence.pretrade_source_kind
        freshness = evidence.pretrade_freshness_status
        get_status = evidence.evidence_status
        get_provenance = evidence.reason_codes
    else:
        source_kind = pretrade_source_kind
        freshness = pretrade_freshness_status
        get_status = FreshPretradeGetStatusV1.NOT_REQUIRED_OFFLINE.value
        get_provenance = evidence.reason_codes
    inputs = join_owner_one_shot_permit_into_admission_inputs_v1(
        plan_identity=plan_identity,
        venue_plan_identity=venue_plan_identity,
        instrument_identity_ok=instrument_identity_ok,
        pretrade_admissible=pretrade_admissible,
        pretrade_source_kind=source_kind,
        pretrade_freshness_status=freshness,
        capital_risk_mode=capital_risk_mode,
        owner_go=owner_go,
        admission_context=admission_context,
        provenance_refs=provenance_refs
        + (
            OFFLINE_BOUNDARY_ROLE,
            JOIN_SEAM_ID,
            FRESH_PRETRADE_GET_AUTHORITY,
            *get_provenance,
        ),
        state_path=state_path,
    )
    return ExecutionAdmissionInputsV1(
        plan_identity=inputs.plan_identity,
        venue_plan_identity=inputs.venue_plan_identity,
        instrument_identity_ok=inputs.instrument_identity_ok,
        pretrade_admissible=inputs.pretrade_admissible,
        pretrade_source_kind=inputs.pretrade_source_kind,
        pretrade_freshness_status=inputs.pretrade_freshness_status,
        capital_risk_mode=inputs.capital_risk_mode,
        durable_kill_switch_evidence_status=inputs.durable_kill_switch_evidence_status,
        durable_kill_switch_blocked=inputs.durable_kill_switch_blocked,
        live_enabled=False,
        live_armed=False,
        wire_send_permitted=False,
        owner_authorization_present=inputs.owner_authorization_present,
        owner_one_shot_permit_status=inputs.owner_one_shot_permit_status,
        admission_context=inputs.admission_context,
        fresh_pretrade_get_status=get_status,
        live_account_bound_status=inputs.live_account_bound_status,
        provenance_refs=inputs.provenance_refs,
    )
