"""Typed Full-Core LIVE_ACCOUNT_BOUND seam. No POST. No wire. No arming.

Derives capital_risk_mode=LIVE_ACCOUNT_BOUND from explicit typed binding
evidence over Fresh Pretrade GET identity extracts. Fresh GET success alone
does not prove bound. String passthrough of LIVE_ACCOUNT_BOUND is not
authority. Missing, malformed, mismatch, contradictory, or stale evidence
fails closed. Fixture/replay/historical markers cannot prove bound.

Does not set LIVE_ENABLED / LIVE_ARMED / WIRE_SEND_PERMITTED.
Does not replace STEP-29P OFFLINE_ALGEBRA sizing. Does not POST.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional, Tuple

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    LIVE_ARMED,
    LIVE_ENABLED,
    OFFLINE_BOUNDARY_ROLE,
    WIRE_SEND_PERMITTED,
)
from src.ops.full_core_live_path_composition_root_v1.execution_admission_contract_v1 import (
    ADMISSION_CONTEXT_LIVE,
    CAPITAL_RISK_MODE_LIVE_ACCOUNT_BOUND,
    CAPITAL_RISK_MODE_OFFLINE_ALGEBRA,
    ExecutionAdmissionInputsV1,
    FreshPretradeGetStatusV1,
    LiveAccountBoundStatusV1,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    FRESH_PRETRADE_GET_AUTHORITY,
    JOIN_SEAM_ID as FRESH_GET_JOIN_SEAM_ID,
    FullCoreFreshPretradeGetTransportV1,
    FreshPretradeGetItemEvidenceV1,
    FreshPretradeRuntimeGetEvidenceV1,
    collect_fresh_pretrade_runtime_get_v1,
    contains_fixture_or_historical_marker_v1,
    join_fresh_pretrade_runtime_get_into_admission_inputs_v1,
)

JOIN_SEAM_ID = "FULL_CORE_LIVE_ACCOUNT_BOUND_SEAM_V1"
LIVE_ACCOUNT_BOUND_AUTHORITY = "capital_risk_sizing_v1/STEP_29P"
BINDING_SEMANTIC_CLASS = "TYPED_ACCOUNT_INSTRUMENT_IDENTITY_RELATION"
INSTRUMENT_BEARING_ITEM_IDS: frozenset[str] = frozenset(
    {
        "INSTRUMENT_STATE",
        "MAX_SIZE",
        "PRICE_BAND",
        "MAX_AVAILABLE",
        "LEVERAGE",
    }
)
ACCOUNT_UID_ITEM_IDS: frozenset[str] = frozenset({"POS_MODE", "ACCOUNT_MODE"})


@dataclass(frozen=True)
class LiveAccountBoundExpectedV1:
    expected_account_identity: str
    expected_instrument_id: str
    expected_td_mode: str


@dataclass(frozen=True)
class LiveAccountBoundEvidenceV1:
    evidence_status: str
    capital_risk_mode: str
    expected_account_identity: str
    observed_account_identity: str
    expected_instrument_id: str
    observed_inst_ids: Tuple[str, ...]
    expected_td_mode: str
    observed_td_modes: Tuple[str, ...]
    reason_codes: Tuple[str, ...]
    live_enabled: bool
    live_armed: bool
    wire_send_permitted: bool
    join_seam_id: str = JOIN_SEAM_ID
    authority: str = LIVE_ACCOUNT_BOUND_AUTHORITY
    semantic_class: str = BINDING_SEMANTIC_CLASS


def _denied(
    *,
    status: str,
    expected: LiveAccountBoundExpectedV1,
    observed_account_identity: str = "",
    observed_inst_ids: Tuple[str, ...] = (),
    observed_td_modes: Tuple[str, ...] = (),
    reasons: Tuple[str, ...],
) -> LiveAccountBoundEvidenceV1:
    return LiveAccountBoundEvidenceV1(
        evidence_status=status,
        capital_risk_mode=CAPITAL_RISK_MODE_OFFLINE_ALGEBRA,
        expected_account_identity=expected.expected_account_identity,
        observed_account_identity=observed_account_identity,
        expected_instrument_id=expected.expected_instrument_id,
        observed_inst_ids=observed_inst_ids,
        expected_td_mode=expected.expected_td_mode,
        observed_td_modes=observed_td_modes,
        reason_codes=tuple(dict.fromkeys((*reasons, JOIN_SEAM_ID))),
        live_enabled=LIVE_ENABLED is True,
        live_armed=LIVE_ARMED is True,
        wire_send_permitted=WIRE_SEND_PERMITTED is True,
    )


def _unique_nonempty(values: Tuple[str, ...]) -> Tuple[str, ...]:
    return tuple(dict.fromkeys(item for item in values if item))


def _collect_item_identities(
    items: Tuple[FreshPretradeGetItemEvidenceV1, ...],
) -> tuple[Tuple[str, ...], Tuple[str, ...], Tuple[str, ...], bool]:
    uids: list[str] = []
    inst_ids: list[str] = []
    td_modes: list[str] = []
    malformed = False
    for item in items:
        if item.identity_fields_malformed is True:
            malformed = True
        uids.extend(item.observed_account_uids)
        inst_ids.extend(item.observed_inst_ids)
        td_modes.extend(item.observed_td_modes)
    return (
        _unique_nonempty(tuple(uids)),
        _unique_nonempty(tuple(inst_ids)),
        _unique_nonempty(tuple(td_modes)),
        malformed,
    )


def _get_status_to_bound_status(get_status: str) -> str:
    if get_status == FreshPretradeGetStatusV1.STALE.value:
        return LiveAccountBoundStatusV1.STALE.value
    if get_status == FreshPretradeGetStatusV1.MALFORMED.value:
        return LiveAccountBoundStatusV1.MALFORMED.value
    if get_status == FreshPretradeGetStatusV1.CONTRADICTORY.value:
        return LiveAccountBoundStatusV1.CONTRADICTORY.value
    if get_status in {
        FreshPretradeGetStatusV1.AUTH_FAILURE.value,
        FreshPretradeGetStatusV1.PUBLIC_FAILURE.value,
        FreshPretradeGetStatusV1.MISSING.value,
        FreshPretradeGetStatusV1.NOT_REQUIRED_OFFLINE.value,
        "",
    }:
        return LiveAccountBoundStatusV1.MISSING.value
    return LiveAccountBoundStatusV1.MISSING.value


def evaluate_live_account_bound_v1(
    *,
    get_evidence: FreshPretradeRuntimeGetEvidenceV1,
    expected_account_identity: Any,
    expected_instrument_id: Any,
    expected_td_mode: Any,
) -> LiveAccountBoundEvidenceV1:
    expected = LiveAccountBoundExpectedV1(
        expected_account_identity=str(expected_account_identity)
        if isinstance(expected_account_identity, str)
        else "",
        expected_instrument_id=str(expected_instrument_id)
        if isinstance(expected_instrument_id, str)
        else "",
        expected_td_mode=str(expected_td_mode) if isinstance(expected_td_mode, str) else "",
    )
    uids, inst_ids, td_modes, extracts_malformed = _collect_item_identities(get_evidence.items)
    observed_uid = uids[0] if len(uids) == 1 else ""

    if (
        not isinstance(expected_account_identity, str)
        or not isinstance(expected_instrument_id, str)
        or not isinstance(expected_td_mode, str)
    ):
        return _denied(
            status=LiveAccountBoundStatusV1.MALFORMED.value,
            expected=expected,
            observed_account_identity=observed_uid,
            observed_inst_ids=inst_ids,
            observed_td_modes=td_modes,
            reasons=("LIVE_ACCOUNT_BOUND_MALFORMED", "LIVE_ACCOUNT_BOUND_EXPECTED_NOT_STRING"),
        )
    if (
        expected_account_identity != expected_account_identity.strip()
        or (expected_instrument_id != expected_instrument_id.strip())
        or expected_td_mode != expected_td_mode.strip()
    ):
        return _denied(
            status=LiveAccountBoundStatusV1.MALFORMED.value,
            expected=expected,
            observed_account_identity=observed_uid,
            observed_inst_ids=inst_ids,
            observed_td_modes=td_modes,
            reasons=("LIVE_ACCOUNT_BOUND_MALFORMED", "LIVE_ACCOUNT_BOUND_EXPECTED_WHITESPACE"),
        )
    if contains_fixture_or_historical_marker_v1(expected_account_identity) or (
        contains_fixture_or_historical_marker_v1(get_evidence.pretrade_decision_id)
    ):
        return _denied(
            status=LiveAccountBoundStatusV1.STALE.value,
            expected=expected,
            observed_account_identity=observed_uid,
            observed_inst_ids=inst_ids,
            observed_td_modes=td_modes,
            reasons=(
                "LIVE_ACCOUNT_BOUND_STALE",
                "LIVE_ACCOUNT_BOUND_FIXTURE_REPLAY_NOT_PRODUCTIVE",
            ),
        )

    get_status = str(get_evidence.evidence_status or "")
    get_trusted = get_status == FreshPretradeGetStatusV1.TRUSTED_PRESENT.value
    if get_trusted is not True:
        mapped = _get_status_to_bound_status(get_status)
        reasons = [
            "LIVE_ACCOUNT_BOUND_REQUIRES_TRUSTED_FRESH_GET",
            "FRESH_GET_ALONE_NOT_ACCOUNT_BOUND",
        ]
        if mapped == LiveAccountBoundStatusV1.STALE.value:
            reasons.extend(
                (
                    "LIVE_ACCOUNT_BOUND_STALE",
                    "LIVE_ACCOUNT_BOUND_FIXTURE_REPLAY_NOT_PRODUCTIVE",
                )
            )
        elif mapped == LiveAccountBoundStatusV1.MALFORMED.value:
            reasons.append("LIVE_ACCOUNT_BOUND_MALFORMED")
        elif mapped == LiveAccountBoundStatusV1.CONTRADICTORY.value:
            reasons.append("LIVE_ACCOUNT_BOUND_CONTRADICTORY")
        else:
            reasons.append("LIVE_ACCOUNT_BOUND_MISSING")
        return _denied(
            status=mapped,
            expected=expected,
            observed_account_identity=observed_uid,
            observed_inst_ids=inst_ids,
            observed_td_modes=td_modes,
            reasons=tuple(reasons),
        )

    if expected_account_identity == "" or expected_instrument_id == "" or (expected_td_mode == ""):
        return _denied(
            status=LiveAccountBoundStatusV1.MISSING.value,
            expected=expected,
            observed_account_identity=observed_uid,
            observed_inst_ids=inst_ids,
            observed_td_modes=td_modes,
            reasons=(
                "LIVE_ACCOUNT_BOUND_MISSING",
                "LIVE_ACCOUNT_BOUND_EXPECTED_IDENTITY_MISSING",
                "FRESH_GET_ALONE_NOT_ACCOUNT_BOUND",
            ),
        )

    if extracts_malformed is True:
        return _denied(
            status=LiveAccountBoundStatusV1.MALFORMED.value,
            expected=expected,
            observed_account_identity=observed_uid,
            observed_inst_ids=inst_ids,
            observed_td_modes=td_modes,
            reasons=(
                "LIVE_ACCOUNT_BOUND_MALFORMED",
                "LIVE_ACCOUNT_BOUND_IDENTITY_FIELD_NOT_EXACT_STRING",
            ),
        )

    uid_items = tuple(item for item in get_evidence.items if item.item_id in ACCOUNT_UID_ITEM_IDS)
    config_uids = _unique_nonempty(
        tuple(uid for item in uid_items for uid in item.observed_account_uids)
    )
    all_uids = uids
    if not config_uids:
        return _denied(
            status=LiveAccountBoundStatusV1.MISSING.value,
            expected=expected,
            observed_account_identity="",
            observed_inst_ids=inst_ids,
            observed_td_modes=td_modes,
            reasons=(
                "LIVE_ACCOUNT_BOUND_MISSING",
                "LIVE_ACCOUNT_BOUND_ACCOUNT_UID_MISSING",
                "FRESH_GET_ALONE_NOT_ACCOUNT_BOUND",
            ),
        )
    if len(all_uids) > 1 or len(config_uids) > 1:
        return _denied(
            status=LiveAccountBoundStatusV1.CONTRADICTORY.value,
            expected=expected,
            observed_account_identity="",
            observed_inst_ids=inst_ids,
            observed_td_modes=td_modes,
            reasons=(
                "LIVE_ACCOUNT_BOUND_CONTRADICTORY",
                "LIVE_ACCOUNT_BOUND_DUPLICATE_AMBIGUOUS_ACCOUNT",
            ),
        )
    observed_uid = config_uids[0]
    if observed_uid != expected_account_identity:
        return _denied(
            status=LiveAccountBoundStatusV1.MISMATCH.value,
            expected=expected,
            observed_account_identity=observed_uid,
            observed_inst_ids=inst_ids,
            observed_td_modes=td_modes,
            reasons=(
                "LIVE_ACCOUNT_BOUND_MISMATCH",
                "LIVE_ACCOUNT_BOUND_WRONG_ACCOUNT",
            ),
        )

    instrument_items = tuple(
        item for item in get_evidence.items if item.item_id in INSTRUMENT_BEARING_ITEM_IDS
    )
    if not instrument_items:
        return _denied(
            status=LiveAccountBoundStatusV1.MISSING.value,
            expected=expected,
            observed_account_identity=observed_uid,
            observed_inst_ids=inst_ids,
            observed_td_modes=td_modes,
            reasons=(
                "LIVE_ACCOUNT_BOUND_MISSING",
                "LIVE_ACCOUNT_BOUND_INSTRUMENT_RELATION_MISSING",
            ),
        )
    instrument_inst_ids = _unique_nonempty(
        tuple(inst for item in instrument_items for inst in item.observed_inst_ids)
    )
    missing_inst = [item.item_id for item in instrument_items if not item.observed_inst_ids]
    if missing_inst:
        return _denied(
            status=LiveAccountBoundStatusV1.MISSING.value,
            expected=expected,
            observed_account_identity=observed_uid,
            observed_inst_ids=inst_ids,
            observed_td_modes=td_modes,
            reasons=(
                "LIVE_ACCOUNT_BOUND_MISSING",
                "LIVE_ACCOUNT_BOUND_INSTRUMENT_RELATION_MISSING",
                "FRESH_GET_ALONE_NOT_ACCOUNT_BOUND",
            ),
        )
    if instrument_inst_ids != (expected_instrument_id,):
        return _denied(
            status=LiveAccountBoundStatusV1.MISMATCH.value,
            expected=expected,
            observed_account_identity=observed_uid,
            observed_inst_ids=instrument_inst_ids,
            observed_td_modes=td_modes,
            reasons=(
                "LIVE_ACCOUNT_BOUND_MISMATCH",
                "LIVE_ACCOUNT_BOUND_WRONG_INSTRUMENT",
            ),
        )
    if td_modes and instrument_inst_ids:
        unexpected_td = tuple(mode for mode in td_modes if mode != expected_td_mode)
        if unexpected_td:
            return _denied(
                status=LiveAccountBoundStatusV1.MISMATCH.value,
                expected=expected,
                observed_account_identity=observed_uid,
                observed_inst_ids=instrument_inst_ids,
                observed_td_modes=td_modes,
                reasons=(
                    "LIVE_ACCOUNT_BOUND_MISMATCH",
                    "LIVE_ACCOUNT_BOUND_WRONG_CONTEXT",
                ),
            )

    return LiveAccountBoundEvidenceV1(
        evidence_status=LiveAccountBoundStatusV1.TRUSTED_PRESENT.value,
        capital_risk_mode=CAPITAL_RISK_MODE_LIVE_ACCOUNT_BOUND,
        expected_account_identity=expected_account_identity,
        observed_account_identity=observed_uid,
        expected_instrument_id=expected_instrument_id,
        observed_inst_ids=instrument_inst_ids,
        expected_td_mode=expected_td_mode,
        observed_td_modes=td_modes,
        reason_codes=tuple(
            dict.fromkeys(
                (
                    "LIVE_ACCOUNT_BOUND_TRUSTED_PRESENT",
                    JOIN_SEAM_ID,
                    LIVE_ACCOUNT_BOUND_AUTHORITY,
                )
            )
        ),
        live_enabled=LIVE_ENABLED is True,
        live_armed=LIVE_ARMED is True,
        wire_send_permitted=WIRE_SEND_PERMITTED is True,
    )


def join_live_account_bound_into_admission_inputs_v1(
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
    expected_account_identity: Any = "",
) -> ExecutionAdmissionInputsV1:
    live_context = admission_context == ADMISSION_CONTEXT_LIVE
    get_evidence = collect_fresh_pretrade_runtime_get_v1(
        pretrade_decision_id=pretrade_decision_id or plan_identity,
        instrument_id=instrument_id,
        td_mode=td_mode,
        limit_px=limit_px,
        inst_type=inst_type,
        transport=transport,
        require_collection=live_context,
    )
    bound = evaluate_live_account_bound_v1(
        get_evidence=get_evidence,
        expected_account_identity=expected_account_identity,
        expected_instrument_id=instrument_id,
        expected_td_mode=td_mode,
    )
    bound_trusted = bound.evidence_status == LiveAccountBoundStatusV1.TRUSTED_PRESENT.value
    resolved_mode = (
        CAPITAL_RISK_MODE_LIVE_ACCOUNT_BOUND if bound_trusted else CAPITAL_RISK_MODE_OFFLINE_ALGEBRA
    )
    if (
        str(capital_risk_mode or "").strip() == CAPITAL_RISK_MODE_LIVE_ACCOUNT_BOUND
        and bound_trusted is not True
    ):
        bound = _denied(
            status=LiveAccountBoundStatusV1.CONTRADICTORY.value,
            expected=LiveAccountBoundExpectedV1(
                expected_account_identity=bound.expected_account_identity,
                expected_instrument_id=bound.expected_instrument_id,
                expected_td_mode=bound.expected_td_mode,
            ),
            observed_account_identity=bound.observed_account_identity,
            observed_inst_ids=bound.observed_inst_ids,
            observed_td_modes=bound.observed_td_modes,
            reasons=bound.reason_codes
            + (
                "LIVE_ACCOUNT_BOUND_CONTRADICTORY",
                "LIVE_ACCOUNT_BOUND_STRING_PASSTHROUGH_NOT_AUTHORITY",
            ),
        )
        resolved_mode = CAPITAL_RISK_MODE_OFFLINE_ALGEBRA
    inputs = join_fresh_pretrade_runtime_get_into_admission_inputs_v1(
        plan_identity=plan_identity,
        venue_plan_identity=venue_plan_identity,
        instrument_identity_ok=instrument_identity_ok,
        pretrade_admissible=pretrade_admissible,
        pretrade_source_kind=pretrade_source_kind,
        pretrade_freshness_status=pretrade_freshness_status,
        capital_risk_mode=resolved_mode,
        owner_go=owner_go,
        admission_context=admission_context,
        provenance_refs=provenance_refs
        + (
            OFFLINE_BOUNDARY_ROLE,
            JOIN_SEAM_ID,
            LIVE_ACCOUNT_BOUND_AUTHORITY,
            FRESH_PRETRADE_GET_AUTHORITY,
            FRESH_GET_JOIN_SEAM_ID,
            *bound.reason_codes,
        ),
        state_path=state_path,
        transport=transport,
        pretrade_decision_id=pretrade_decision_id,
        instrument_id=instrument_id,
        td_mode=td_mode,
        limit_px=limit_px,
        inst_type=inst_type,
        precomputed_evidence=get_evidence,
    )
    return ExecutionAdmissionInputsV1(
        plan_identity=inputs.plan_identity,
        venue_plan_identity=inputs.venue_plan_identity,
        instrument_identity_ok=inputs.instrument_identity_ok,
        pretrade_admissible=inputs.pretrade_admissible,
        pretrade_source_kind=inputs.pretrade_source_kind,
        pretrade_freshness_status=inputs.pretrade_freshness_status,
        capital_risk_mode=resolved_mode,
        durable_kill_switch_evidence_status=inputs.durable_kill_switch_evidence_status,
        durable_kill_switch_blocked=inputs.durable_kill_switch_blocked,
        live_enabled=LIVE_ENABLED is True,
        live_armed=LIVE_ARMED is True,
        wire_send_permitted=WIRE_SEND_PERMITTED is True,
        owner_authorization_present=inputs.owner_authorization_present,
        owner_one_shot_permit_status=inputs.owner_one_shot_permit_status,
        admission_context=inputs.admission_context,
        fresh_pretrade_get_status=inputs.fresh_pretrade_get_status,
        live_account_bound_status=bound.evidence_status,
        provenance_refs=inputs.provenance_refs,
    )
