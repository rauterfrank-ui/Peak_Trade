"""Map CURRENT_PRODUCTIVE common-epoch handoff to enter-live-29p carrier v1.

Values are taken only from the common-epoch compose result and the same
Full-Core fresh-pretrade transport payloads. No fixture defaults.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

from src.ops.full_core_live_path_composition_root_v1.pretrade_acquisition_v1 import (
    acquisition_age_seconds_v1,
    utc_now_iso_v1,
)

from src.ops.full_core_live_path_composition_root_v1.current_productive_enter_live_29p_join_v1 import (
    CurrentProductiveEnterLive29PInjectedGetV1,
)
from src.ops.full_core_live_path_composition_root_v1.execution_admission_contract_v1 import (
    FreshPretradeGetStatusV1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1 import (
    ENDPOINT_MARKET_INDEX_TICKERS,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    ENDPOINT_ACCOUNT_BALANCE,
    ENDPOINT_PUBLIC_INSTRUMENTS,
    MONETARY_NORMALIZATION_CONVERSION_PAIR_INSTRUMENTS_ITEM_ID,
    FullCoreFreshPretradeGetTransportV1,
    REQUIRED_GET_ITEM_SPECS,
    TRANSPORT_CLASS_INJECTED_TEST_DOUBLE,
    TRANSPORT_CLASS_PRODUCTIVE_READ_ONLY_GET,
    build_required_get_endpoint_v1,
)
from src.ops.governed_productive_monetary_normalization_v1.constants_v1 import (
    USDT_USDC_PAIR_NATIVE_ID,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_common_epoch_handoff_v1 import (
    CurrentProductive29PCommonEpochHandoffResultV1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_risk_capital_model_v1 import (
    REQUIRED_TD_MODE,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.available_margin_observation_v1 import (
    account_balance_query_path_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    REUSED_BINDING_ACCOUNT_SCOPE,
)

JOIN_SEAM_ID = "CURRENT_PRODUCTIVE_COMMON_EPOCH_TO_ENTER_LIVE_29P_HANDOFF_V1"


class CurrentProductiveCommonEpochToEnterLive29PHandoffError(RuntimeError):
    """Fail-closed common-epoch → enter-live-29p handoff violation."""


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _require_productive_transport_v1(transport: FullCoreFreshPretradeGetTransportV1) -> None:
    transport_class = str(getattr(transport, "transport_class", "") or "")
    if transport_class == TRANSPORT_CLASS_INJECTED_TEST_DOUBLE:
        raise CurrentProductiveCommonEpochToEnterLive29PHandoffError(
            "INJECTED_TEST_DOUBLE_NOT_PRODUCTIVE_CURRENT"
        )
    if transport_class != TRANSPORT_CLASS_PRODUCTIVE_READ_ONLY_GET:
        raise CurrentProductiveCommonEpochToEnterLive29PHandoffError(
            "TRANSPORT_CLASS_NOT_PRODUCTIVE"
        )
    if bool(getattr(transport, "venue_live_contact", False)) is not True:
        raise CurrentProductiveCommonEpochToEnterLive29PHandoffError(
            "VENUE_LIVE_CONTACT_REQUIRED_FOR_PRODUCTIVE_CURRENT"
        )


def _fresh_pretrade_item_spec_v1(*, item_id: str):
    for spec in REQUIRED_GET_ITEM_SPECS:
        if spec.item_id == item_id:
            return spec
    raise CurrentProductiveCommonEpochToEnterLive29PHandoffError("FRESH_PRETRADE_ITEM_SPEC_MISSING")


def _payload_from_decision_epoch_get_v1(
    *,
    handoff: CurrentProductive29PCommonEpochHandoffResultV1,
    endpoint: str,
    auth_required: bool,
    decision_epoch: str,
) -> Any:
    # Do not consult a path-only cache or issue another read after admission.
    for result in handoff.pretrade_results.values():
        if result.endpoint != endpoint or result.auth_header_sent is not auth_required:
            continue
        if result.pretrade_decision_id != handoff.get_evidence.pretrade_decision_id:
            break
        try:
            acquisition_age_seconds_v1(
                acquired_at_utc=result.acquired_at_utc, now_utc=utc_now_iso_v1()
            )
        except ValueError as exc:
            raise CurrentProductiveCommonEpochToEnterLive29PHandoffError(str(exc)) from exc
        return result.payload
    raise CurrentProductiveCommonEpochToEnterLive29PHandoffError(
        "FRESH_PRETRADE_SNAPSHOT_BINDING_MISSING"
    )


def _require_bound_instruments_payload_v1(
    *,
    payload: Any,
    bound_venue_native_id: str,
) -> Mapping[str, Any]:
    if not isinstance(payload, Mapping):
        raise CurrentProductiveCommonEpochToEnterLive29PHandoffError("INSTRUMENTS_PAYLOAD_MISSING")
    data = payload.get("data")
    if not isinstance(data, list):
        raise CurrentProductiveCommonEpochToEnterLive29PHandoffError(
            "INSTRUMENTS_PAYLOAD_MALFORMED"
        )
    bound_id = str(bound_venue_native_id or "").strip()
    has_bound = any(
        isinstance(row, Mapping) and str(row.get("instId") or "").strip() == bound_id
        for row in data
    )
    if not has_bound:
        raise CurrentProductiveCommonEpochToEnterLive29PHandoffError(
            "BOUND_INSTRUMENT_METADATA_MISSING"
        )
    return payload


def _require_conversion_pair_instruments_payload_v1(*, payload: Any) -> Mapping[str, Any]:
    if not isinstance(payload, Mapping):
        raise CurrentProductiveCommonEpochToEnterLive29PHandoffError(
            "CONVERSION_PAIR_INSTRUMENTS_PAYLOAD_MISSING"
        )
    data = payload.get("data")
    if not isinstance(data, list):
        raise CurrentProductiveCommonEpochToEnterLive29PHandoffError(
            "CONVERSION_PAIR_INSTRUMENTS_PAYLOAD_MALFORMED"
        )
    pair_rows = [
        row
        for row in data
        if isinstance(row, Mapping)
        and str(row.get("instId") or "").strip() == USDT_USDC_PAIR_NATIVE_ID
    ]
    if len(pair_rows) != 1:
        raise CurrentProductiveCommonEpochToEnterLive29PHandoffError(
            "CONVERSION_PAIR_INSTRUMENTS_ROW_MISSING"
        )
    return payload


def build_current_productive_enter_live_29p_injected_from_common_epoch_handoff_v1(
    *,
    handoff: CurrentProductive29PCommonEpochHandoffResultV1,
    transport: FullCoreFreshPretradeGetTransportV1,
    expected_account_identity: str = REUSED_BINDING_ACCOUNT_SCOPE,
) -> CurrentProductiveEnterLive29PInjectedGetV1:
    """Build enter-live-29p carrier from common-epoch outputs only."""
    _require_productive_transport_v1(transport)
    if transport is not handoff.source_transport:
        raise CurrentProductiveCommonEpochToEnterLive29PHandoffError(
            "FRESH_PRETRADE_SNAPSHOT_TRANSPORT_MISMATCH"
        )
    epoch = str(handoff.decision_epoch or "").strip()
    if not epoch:
        raise CurrentProductiveCommonEpochToEnterLive29PHandoffError("DECISION_EPOCH_MISSING")
    if handoff.get_status != FreshPretradeGetStatusV1.TRUSTED_PRESENT.value:
        raise CurrentProductiveCommonEpochToEnterLive29PHandoffError(
            "FRESH_PRETRADE_GET_NOT_TRUSTED_PRESENT"
        )
    if handoff.lab_trusted is not True:
        raise CurrentProductiveCommonEpochToEnterLive29PHandoffError(
            "LIVE_ACCOUNT_BOUND_NOT_TRUSTED"
        )
    groups = {spec.fetch_group for spec in REQUIRED_GET_ITEM_SPECS}
    if set(handoff.pretrade_results) != groups:
        raise CurrentProductiveCommonEpochToEnterLive29PHandoffError(
            "FRESH_PRETRADE_SNAPSHOT_BINDING_MISSING"
        )
    now_utc = utc_now_iso_v1()
    for result in handoff.pretrade_results.values():
        if result.pretrade_decision_id != handoff.get_evidence.pretrade_decision_id:
            raise CurrentProductiveCommonEpochToEnterLive29PHandoffError(
                "FRESH_PRETRADE_SNAPSHOT_DECISION_MISMATCH"
            )
        try:
            acquisition_age_seconds_v1(acquired_at_utc=result.acquired_at_utc, now_utc=now_utc)
        except ValueError as exc:
            raise CurrentProductiveCommonEpochToEnterLive29PHandoffError(str(exc)) from exc

    bound_venue_native_id = str(handoff.bound_instrument.venue_native_id or "").strip()
    if not bound_venue_native_id:
        raise CurrentProductiveCommonEpochToEnterLive29PHandoffError("BOUND_INSTRUMENT_ID_MISSING")

    public_inst_type = str(handoff.public_inst_type or "").strip().upper() or "FUTURES"

    balance_path = account_balance_query_path_v1()
    balance_payload = _payload_from_decision_epoch_get_v1(
        handoff=handoff,
        endpoint=balance_path,
        auth_required=True,
        decision_epoch=epoch,
    )
    if not isinstance(balance_payload, Mapping):
        raise CurrentProductiveCommonEpochToEnterLive29PHandoffError("BALANCE_PAYLOAD_MISSING")

    instrument_state_spec = _fresh_pretrade_item_spec_v1(item_id="INSTRUMENT_STATE")
    bound_instruments_endpoint = build_required_get_endpoint_v1(
        instrument_state_spec,
        instrument_id=bound_venue_native_id,
        td_mode=REQUIRED_TD_MODE,
        limit_px="",
        inst_type=public_inst_type,
    )
    instruments_payload = _payload_from_decision_epoch_get_v1(
        handoff=handoff,
        endpoint=bound_instruments_endpoint,
        auth_required=False,
        decision_epoch=epoch,
    )
    instruments_payload = _require_bound_instruments_payload_v1(
        payload=instruments_payload,
        bound_venue_native_id=bound_venue_native_id,
    )

    index_spec = _fresh_pretrade_item_spec_v1(item_id="MONETARY_NORMALIZATION_USDT_USDC_INDEX")
    index_tickers_endpoint = build_required_get_endpoint_v1(
        index_spec,
        instrument_id=bound_venue_native_id,
        td_mode=REQUIRED_TD_MODE,
        limit_px="",
        inst_type=public_inst_type,
    )
    index_tickers_payload = _payload_from_decision_epoch_get_v1(
        handoff=handoff,
        endpoint=index_tickers_endpoint,
        auth_required=False,
        decision_epoch=epoch,
    )
    if not isinstance(index_tickers_payload, Mapping):
        raise CurrentProductiveCommonEpochToEnterLive29PHandoffError(
            "MONETARY_NORMALIZATION_INDEX_TICKERS_MISSING"
        )

    conversion_pair_spec = _fresh_pretrade_item_spec_v1(
        item_id=MONETARY_NORMALIZATION_CONVERSION_PAIR_INSTRUMENTS_ITEM_ID
    )
    conversion_pair_endpoint = build_required_get_endpoint_v1(
        conversion_pair_spec,
        instrument_id=bound_venue_native_id,
        td_mode=REQUIRED_TD_MODE,
        limit_px="",
        inst_type=public_inst_type,
    )
    conversion_pair_payload = _payload_from_decision_epoch_get_v1(
        handoff=handoff,
        endpoint=conversion_pair_endpoint,
        auth_required=False,
        decision_epoch=epoch,
    )
    conversion_pair_payload = _require_conversion_pair_instruments_payload_v1(
        payload=conversion_pair_payload
    )

    if conversion_pair_payload is instruments_payload:
        raise CurrentProductiveCommonEpochToEnterLive29PHandoffError(
            "CONVERSION_PAIR_INSTRUMENTS_NOT_SEPARATE_FROM_BOUND"
        )

    body_sha256 = ""
    if handoff.observation is not None:
        body_sha256 = str(handoff.observation.provenance_digest or "").strip()
    if not body_sha256:
        body_sha256 = _sha256_text(_canonical_json(dict(balance_payload)))

    if handoff.observation is None:
        raise CurrentProductiveCommonEpochToEnterLive29PHandoffError(
            "ORIGINAL_MARGIN_OBSERVATION_MISSING"
        )
    observed_at = handoff.observation.observed_at_as_of

    try:
        age_seconds = acquisition_age_seconds_v1(
            acquired_at_utc=observed_at, now_utc=utc_now_iso_v1()
        )
    except ValueError as exc:
        raise CurrentProductiveCommonEpochToEnterLive29PHandoffError(str(exc)) from exc

    raw_acct_lv = str(handoff.adaptation.raw_token or "").strip()

    from src.ops.full_core_live_path_composition_root_v1.current_productive_n1_venue_quantity_limit_admission_v1 import (
        capture_n1_venue_quantity_limits_v1,
    )

    try:
        venue_quantity_limits = capture_n1_venue_quantity_limits_v1(
            results=handoff.pretrade_results,
            acquisition_decision_id=handoff.get_evidence.pretrade_decision_id,
            account_identity=handoff.bound_uid,
            bound_instrument=handoff.bound_instrument,
            decision_epoch=epoch,
            cycle_id=handoff.pretrade_cycle_id,
        )
    except (ValueError, TypeError) as exc:
        raise CurrentProductiveCommonEpochToEnterLive29PHandoffError(str(exc)) from exc

    return CurrentProductiveEnterLive29PInjectedGetV1(
        payload=dict(balance_payload),
        get_performed=True,
        http_status=200,
        error_class="",
        body_sha256=body_sha256,
        observed_at=observed_at,
        age_seconds=age_seconds,
        live_account_bound_status=str(handoff.lab_status),
        raw_acct_lv=raw_acct_lv,
        expected_account_identity=str(expected_account_identity or REUSED_BINDING_ACCOUNT_SCOPE),
        fresh_pretrade_get_status=str(handoff.get_status),
        instruments_payload=dict(instruments_payload),
        index_tickers_payload=dict(index_tickers_payload),
        conversion_pair_instruments_payload=dict(conversion_pair_payload),
        acquisition_decision_id=epoch,
        acquisition_cycle_id=handoff.pretrade_cycle_id,
        pretrade_acquired_at_utc=tuple(
            result.acquired_at_utc for result in handoff.pretrade_results.values()
        ),
        venue_quantity_limits=venue_quantity_limits,
    )


__all__ = [
    "JOIN_SEAM_ID",
    "CurrentProductiveCommonEpochToEnterLive29PHandoffError",
    "build_current_productive_enter_live_29p_injected_from_common_epoch_handoff_v1",
]
