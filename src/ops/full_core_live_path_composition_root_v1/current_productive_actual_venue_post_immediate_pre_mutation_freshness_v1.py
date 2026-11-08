"""Immediate pre-mutation freshness for direct actual-venue POST entry.

Reuses collect_fresh_pretrade_runtime_get_v1 and bound-instrument position
observations. UNKNOWN != FLAT. Fresh position data and new-entry eligibility
are distinct predicates. A valid position proof is not complete account/order,
risk, safety, permit or later-send admission; original account context remains
a separate integration boundary.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
import hashlib
import json
from typing import Any, Mapping
from urllib.parse import urlencode

from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    ENDPOINT_ACCOUNT_POSITIONS,
    GET_CACHE_POLICY_DECISION_BOUND_SNAPSHOT,
    REQUIRED_GET_ITEM_SPECS,
    FreshPretradeGetTransportResultV1,
    _item_status_and_reasons,
)
from src.ops.full_core_live_path_composition_root_v1.execution_admission_contract_v1 import (
    DataSafetyAdmissionStatusV1,
    FreshPretradeGetStatusV1,
    LiveAccountBoundStatusV1,
)
from src.ops.full_core_live_path_composition_root_v1.envelope_bound_external_effect_send_seam_v1 import (
    FullCoreEnvelopeBoundSendSeamError,
    inspect_original_portfolio_execution_context_v1,
)
from src.ops.full_core_live_path_composition_root_v1.live_account_bound_v1 import (
    evaluate_live_account_bound_v1,
)
from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
    FinalOrderEnvelopeV1,
    assert_envelope_unmodified_v1,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    FullCoreFreshPretradeGetTransportV1,
    collect_fresh_pretrade_runtime_get_v1,
)
from src.ops.single_selected_future_runtime_binding_v1.constants_v1 import (
    MAX_POSITIONS_EFFECTIVE,
)
from src.ops.full_core_live_path_composition_root_v1.pretrade_acquisition_v1 import (
    acquisition_age_seconds_v1,
    utc_now_iso_v1,
)
from src.ops.full_core_live_path_composition_root_v1.datasafety_gate_join_into_execution_admission_v1 import (
    evaluate_datasafety_admission_for_transport_result_v1,
)
from .current_productive_post_venue_quantity_v1 import (
    CurrentPostVenueQuantityContextV1,
    capture_current_post_venue_quantity_v1,
    inspect_current_post_venue_quantity_v1,
)


class CurrentProductiveActualVenuePostPreMutationFreshnessError(RuntimeError):
    """Fail-closed pre-mutation freshness violation."""


@dataclass(frozen=True)
class ActualVenuePostPreMutationFreshnessProofV1:
    account_state_fresh: bool
    position_state_fresh: bool
    full_pretrade_conjunction_pass: bool
    all_required_pre_post_gates_pass: bool
    pretrade_evidence_status: str
    position_truth: str
    reason_codes: tuple[str, ...]
    position_observations_consistent: bool = False
    new_entry_position_admissible: bool = False
    position_source_binding: Mapping[str, Any] = field(default_factory=dict)
    scope: str = "PREPOST_FRESHNESS_POSITION_AND_VENUE_QUANTITY_ONLY"
    account_identity_binding_status: str = "NOT_ASSESSED"
    account_source_binding: Mapping[str, Any] = field(default_factory=dict)
    venue_quantity_limits_admissible: bool = False
    venue_quantity_assessment: Mapping[str, Any] = field(default_factory=dict)
    venue_quantity_context: CurrentPostVenueQuantityContextV1 | None = None


def _position_rows_v1(payload: Any, *, scoped_native: str = "") -> dict[tuple, Decimal]:
    """Keep native signed counts and hedge legs; never net opposite legs away."""
    if (
        not isinstance(payload, Mapping)
        or payload.get("code") != "0"
        or not isinstance(payload.get("data"), list)
    ):
        raise ValueError("POSITION_RESPONSE_MALFORMED")
    positions, seen = {}, set()
    for row in payload["data"]:
        if not isinstance(row, Mapping):
            raise ValueError("POSITION_ROW_MALFORMED")
        native, side, mode, ccy = (row.get(k) for k in ("instId", "posSide", "mgnMode", "ccy"))
        if not isinstance(native, str) or not native or native != native.strip():
            raise ValueError("POSITION_INSTRUMENT_MISSING")
        if scoped_native and native != scoped_native:
            raise ValueError("POSITION_SCOPED_INSTRUMENT_MISMATCH")
        if side not in {"net", "long", "short"} or mode not in {"cross", "isolated"}:
            raise ValueError("POSITION_SIDE_OR_MARGIN_MODE_MALFORMED")
        if ccy is not None and not isinstance(ccy, str):
            raise ValueError("POSITION_CURRENCY_MALFORMED")
        raw = row.get("pos")
        if not isinstance(raw, str) or not raw or raw != raw.strip():
            raise ValueError("POSITION_QUANTITY_MALFORMED")
        try:
            quantity = Decimal(raw)
        except InvalidOperation as exc:
            raise ValueError("POSITION_QUANTITY_MALFORMED") from exc
        if not quantity.is_finite() or (side != "net" and quantity < 0):
            raise ValueError("POSITION_QUANTITY_MALFORMED")
        key = (native, side, mode, ccy or "")
        if key in seen:
            raise ValueError("POSITION_DUPLICATE_IDENTITY")
        seen.add(key)
        if quantity != 0:
            positions[key] = quantity
    return positions


def _validate_position_result_v1(result, *, endpoint, decision_id, now):
    if not isinstance(result, FreshPretradeGetTransportResultV1):
        raise ValueError("POSITION_RESULT_MISSING")
    spec = next(s for s in REQUIRED_GET_ITEM_SPECS if s.item_id == "MARGIN_MODE")
    status, _ = _item_status_and_reasons(
        spec=spec, result=result, pretrade_decision_id=decision_id, requested_endpoint=endpoint
    )
    if (
        status != FreshPretradeGetStatusV1.TRUSTED_PRESENT.value
        or result.method != "GET"
        or result.error_class
    ):
        raise ValueError("POSITION_RESULT_NOT_TRUSTED")
    if result.endpoint != endpoint or result.pretrade_decision_id != decision_id:
        raise ValueError("POSITION_ACQUISITION_OR_ENDPOINT_MISMATCH")
    acquisition_age_seconds_v1(acquired_at_utc=result.acquired_at_utc, now_utc=now)
    if (
        evaluate_datasafety_admission_for_transport_result_v1(result)
        != DataSafetyAdmissionStatusV1.SATISFIED.value
    ):
        raise ValueError("POSITION_DATASAFETY_NOT_SATISFIED")


def _position_source_v1(result):
    payload = json.dumps(result.payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return {
        "endpoint": result.endpoint,
        "acquisition_decision_id": result.pretrade_decision_id,
        "acquired_at_utc": result.acquired_at_utc,
        "response_body_sha256": result.body_sha256,
        "payload_sha256": hashlib.sha256(payload.encode()).hexdigest(),
    }


def _inst_type_for_envelope_v1(envelope: FinalOrderEnvelopeV1) -> str:
    inst = str(envelope.instrument_id or "").strip()
    if inst.endswith("-SWAP"):
        return "SWAP"
    return "FUTURES"


def prove_immediate_pre_mutation_freshness_for_actual_venue_post_v1(
    *,
    envelope: FinalOrderEnvelopeV1,
    read_only_get_transport: FullCoreFreshPretradeGetTransportV1 | None,
    pretrade_decision_id: str,
    portfolio_budget_owner=None,
    portfolio_reservation_id: str = "",
    execution_identity=None,
    execution_plan_context=None,
) -> ActualVenuePostPreMutationFreshnessProofV1:
    assert_envelope_unmodified_v1(envelope)
    context_args = dict(
        envelope=envelope,
        portfolio_budget_owner=portfolio_budget_owner,
        portfolio_reservation_id=portfolio_reservation_id,
        execution_identity=execution_identity,
        execution_plan_context=execution_plan_context,
        required_execution_environment="LIVE",
    )
    try:
        original_context = inspect_original_portfolio_execution_context_v1(**context_args)
    except FullCoreEnvelopeBoundSendSeamError as exc:
        raise CurrentProductiveActualVenuePostPreMutationFreshnessError(str(exc)) from exc
    if read_only_get_transport is None:
        raise CurrentProductiveActualVenuePostPreMutationFreshnessError(
            "PRE_MUTATION_READ_TRANSPORT_REQUIRED"
        )
    if int(MAX_POSITIONS_EFFECTIVE) != 1:
        raise CurrentProductiveActualVenuePostPreMutationFreshnessError(
            "MAX_POSITIONS_EFFECTIVE_MUST_REMAIN_ONE"
        )
    decision_id = str(pretrade_decision_id or "").strip()
    if not decision_id:
        raise CurrentProductiveActualVenuePostPreMutationFreshnessError(
            "PRETRADE_DECISION_ID_REQUIRED"
        )
    inst_type = _inst_type_for_envelope_v1(envelope)
    results: dict[str, FreshPretradeGetTransportResultV1] = {}
    evidence = collect_fresh_pretrade_runtime_get_v1(
        pretrade_decision_id=decision_id,
        instrument_id=envelope.instrument_id,
        td_mode=envelope.td_mode,
        limit_px=envelope.price,
        inst_type=inst_type,
        transport=read_only_get_transport,
        require_collection=True,
        collected_results=results,
    )
    pretrade_ok = evidence.evidence_status == FreshPretradeGetStatusV1.TRUSTED_PRESENT.value
    reasons: list[str] = list(evidence.reason_codes)
    if not pretrade_ok:
        reasons.append("FULL_PRETRADE_CONJUNCTION_NOT_TRUSTED_PRESENT")

    pos_endpoint = (
        f"{ENDPOINT_ACCOUNT_POSITIONS}?"
        f"{urlencode({'instType': inst_type, 'instId': envelope.instrument_id})}"
    )
    pos_result = read_only_get_transport.get(
        endpoint=pos_endpoint,
        auth_required=True,
        pretrade_decision_id=decision_id,
        get_cache_policy=GET_CACHE_POLICY_DECISION_BOUND_SNAPSHOT,
    )
    source_binding = {}
    position_fresh, consistent, entry_admissible = False, False, False
    truth = "UNKNOWN"
    account_fresh = pretrade_ok
    account_status = "NOT_ASSESSED" if original_context is None else "MISSING"
    account_binding = {}
    quantity_context, quantity_assessment = None, {}
    try:
        now = utc_now_iso_v1()
        # The tenth read must not extend the lifetime of the original nine.
        for result in results.values():
            acquisition_age_seconds_v1(acquired_at_utc=result.acquired_at_utc, now_utc=now)
        if evidence.data_safety_admission_status != DataSafetyAdmissionStatusV1.SATISFIED.value:
            account_fresh = False
            pretrade_ok = False
            raise ValueError("COMMON_DATASAFETY_NOT_SATISFIED")
        if original_context is not None:
            # Recheck the original owner after acquisition; no cached owner proof.
            current_context = inspect_original_portfolio_execution_context_v1(**context_args)
            if current_context != original_context:
                raise ValueError("ORIGINAL_PORTFOLIO_CONTEXT_CHANGED")
            config = results.get("config")
            data = config.payload.get("data") if config is not None else None
            if not (
                isinstance(data, list)
                and len(data) == 1
                and isinstance(data[0], Mapping)
                and isinstance(data[0].get("uid"), str)
                and data[0]["uid"]
                and data[0]["uid"] == data[0]["uid"].strip()
            ):
                account_status = LiveAccountBoundStatusV1.MALFORMED.value
                raise ValueError("PREPOST_ACCOUNT_CONFIG_IDENTITY_MALFORMED")
            account = evaluate_live_account_bound_v1(
                get_evidence=evidence,
                expected_account_identity=original_context["account"],
                expected_instrument_id=envelope.instrument_id,
                expected_td_mode=envelope.td_mode,
            )
            account_status = account.evidence_status
            if account_status != LiveAccountBoundStatusV1.TRUSTED_PRESENT.value:
                reasons.extend(account.reason_codes)
                raise ValueError("PREPOST_ORIGINAL_ACCOUNT_BINDING_NOT_TRUSTED")
            account_binding = {
                "config": _position_source_v1(config),
                "original_owner_scope_sha256": hashlib.sha256(
                    json.dumps(
                        {k: original_context[k] for k in ("root", "account")},
                        sort_keys=True,
                        separators=(",", ":"),
                    ).encode()
                ).hexdigest(),
                "reservation_id": original_context["reservation_id"],
                "envelope_digest": original_context["envelope_digest"],
                **{
                    k: original_context[k]
                    for k in (
                        "execution_identity_digest",
                        "plan_origin_digest",
                        "order_environment",
                        "context_kind",
                    )
                    if k in original_context
                },
            }
        global_result = results.get("positions")
        _validate_position_result_v1(
            global_result, endpoint=ENDPOINT_ACCOUNT_POSITIONS, decision_id=decision_id, now=now
        )
        _validate_position_result_v1(
            pos_result, endpoint=pos_endpoint, decision_id=decision_id, now=now
        )
        global_positions = _position_rows_v1(global_result.payload)
        scoped_positions = _position_rows_v1(
            pos_result.payload, scoped_native=envelope.instrument_id
        )
        source_binding = {
            "account_wide": _position_source_v1(global_result),
            "bound_instrument": _position_source_v1(pos_result),
            "envelope_digest": envelope.envelope_digest,
        }
        position_fresh = True
        bound_positions = {
            key: value
            for key, value in global_positions.items()
            if key[0] == envelope.instrument_id
        }
        consistent = bound_positions == scoped_positions
        if not consistent:
            reasons.append("POSITION_OBSERVATIONS_CHANGED_OR_CONFLICTING")
        elif any(key[0] != envelope.instrument_id for key in global_positions):
            truth = "FOREIGN_OPEN_POSITION_MAX_POSITIONS_1"
            reasons.append("FOREIGN_OPEN_POSITION_MAX_POSITIONS_ONE")
        elif bound_positions:
            truth = "BOUND_INSTRUMENT_OPEN"
            reasons.append("NEW_ENTRY_REQUIRES_ACCOUNT_FLAT")
        else:
            truth = "FLAT"
            entry_admissible = envelope.reduce_only is False
        if envelope.reduce_only is True:
            reasons.append("CLOSE_REQUIRES_ORIGINAL_POSITION_ADMISSION")
        quantity_context = capture_current_post_venue_quantity_v1(
            envelope=envelope, results=results, acquisition_decision_id=decision_id
        )
        quantity_assessment = inspect_current_post_venue_quantity_v1(
            quantity_context, envelope=envelope, stage="BEFORE_POST_GO"
        )
    except (
        ValueError,
        TypeError,
        AttributeError,
        KeyError,
        FullCoreEnvelopeBoundSendSeamError,
    ) as exc:
        reasons.append(str(exc))
        # Fresh account acquisition is a clock claim, not UID/order admission.
        if str(exc).startswith("ACQUISITION_"):
            account_fresh = False
            pretrade_ok = False
    account_bound = (
        original_context is None or account_status == LiveAccountBoundStatusV1.TRUSTED_PRESENT.value
    )
    all_pass = (
        pretrade_ok
        and account_fresh
        and account_bound
        and position_fresh
        and consistent
        and entry_admissible
        and bool(quantity_assessment)
    )
    if not all_pass:
        reasons.append("PREPOST_GATE_CONJUNCTION_FAIL_CLOSED")
    return ActualVenuePostPreMutationFreshnessProofV1(
        account_state_fresh=account_fresh,
        position_state_fresh=position_fresh,
        full_pretrade_conjunction_pass=pretrade_ok,
        all_required_pre_post_gates_pass=all_pass,
        pretrade_evidence_status=str(evidence.evidence_status),
        position_truth=str(truth),
        reason_codes=tuple(dict.fromkeys(reasons)),
        position_observations_consistent=consistent,
        new_entry_position_admissible=entry_admissible,
        position_source_binding=source_binding,
        account_identity_binding_status=account_status,
        account_source_binding=account_binding,
        venue_quantity_limits_admissible=bool(quantity_assessment),
        venue_quantity_assessment=quantity_assessment,
        venue_quantity_context=quantity_context if quantity_assessment else None,
        scope="PREPOST_ORIGINAL_BUDGET_ACCOUNT_POSITION_AND_VENUE_QUANTITY_ONLY"
        if original_context is not None
        else "PREPOST_FRESHNESS_POSITION_AND_VENUE_QUANTITY_ONLY",
    )


__all__ = [
    "ActualVenuePostPreMutationFreshnessProofV1",
    "CurrentProductiveActualVenuePostPreMutationFreshnessError",
    "prove_immediate_pre_mutation_freshness_for_actual_venue_post_v1",
]
