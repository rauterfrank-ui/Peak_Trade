"""Pilot capital guard enforce + DW wiring for Enter-POST (offline-capable, fail-closed).

Requires explicit OWNER_GO_CURRENT_PILOT_CAPITAL_GUARD_POST_BIND_V1. No standing
authorization. Does not ratify owner caps or activate productive POST pins.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlencode

from src.ops.full_core_live_path_composition_root_v1.current_full_core_capital_guard_v1 import (
    FullCoreCapitalGuardConfigV1,
    load_full_core_capital_guard_config_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_dw_exchange_reconciliation_wiring_v1 import (
    DwExchangeReconciliationWiringConfigV1,
    DwExchangeReconciliationWiringModeV1,
)
from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
    FinalOrderEnvelopeV1,
    assert_envelope_unmodified_v1,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    ENDPOINT_ACCOUNT_BALANCE,
    ENDPOINT_ACCOUNT_CONFIG,
    ENDPOINT_ACCOUNT_LEVERAGE_INFO,
    ENDPOINT_ACCOUNT_POSITIONS,
    ENDPOINT_PUBLIC_INSTRUMENTS,
    FullCoreFreshPretradeGetTransportV1,
    FreshPretradeGetTransportResultV1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1 import (
    ENDPOINT_MARKET_INDEX_TICKERS,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_capital_guard_atomic_one_shot_v1 import (
    FullCoreAuthorizationBindingV1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_pre_post_capital_guard_binding_v1 import (
    FullCoreCapitalGuardBindingError,
    build_full_core_enter_post_capital_guard_join_binding_v1,
    extract_instrument_contract_metadata_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_pre_post_capital_guard_join_v1 import (
    FullCoreCapitalGuardJoinMode,
    FullCorePrePostCapitalGuardJoinError,
    FullCorePrePostCapitalGuardJoinResultV1,
    run_full_core_pre_post_capital_guard_join_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.cover_usdc_current_public_tier_mmr_productive_evidence_v1 import (
    POSITION_TIERS_ENDPOINT,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.current_live_canary_capital_guard_v1 import (
    CanaryCapitalGuardExposureEvidenceV1,
    CanaryCapitalGuardMarginEvidenceV1,
    IMR_SOURCE_PUBLIC_POSITION_TIERS_QTY_ONE,
    bind_imr_from_public_position_tiers_payload_v1,
    extract_avail_eq_usdc_from_balance_payload_v1,
    extract_leverage_from_leverage_payload_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pre_submit_state_v1 import (
    LiveCanaryPreSubmitStateError,
    evaluate_pre_submit_exchange_state_v1,
)

CONTRACT_ID = "CURRENT_PRODUCTIVE_PILOT_CAPITAL_GUARD_POST_BIND_V1"
OWNER_GO_CURRENT_PILOT_CAPITAL_GUARD_POST_BIND_V1 = (
    "OWNER_GO_CURRENT_PILOT_CAPITAL_GUARD_POST_BIND_V1"
)
PILOT_ENVIRONMENT = "PRODUCTIVE_READ_ONLY"
ORDERS_PENDING_ENDPOINT = "/api/v5/trade/orders-pending"
POST_COUNT = 0


class PilotCapitalGuardPostBindError(RuntimeError):
    """Fail-closed pilot guard / DW bind violation."""


@dataclass(frozen=True)
class PilotCapitalGuardAuthoritativeEvidenceV1:
    margin_evidence: CanaryCapitalGuardMarginEvidenceV1
    exposure_evidence: CanaryCapitalGuardExposureEvidenceV1
    observed_leverage: str
    existing_exposure_notional_usdc: str


@dataclass(frozen=True)
class PilotCapitalGuardPostBindResultV1:
    join_result: FullCorePrePostCapitalGuardJoinResultV1
    authorization_binding: FullCoreAuthorizationBindingV1
    dw_wiring_config: DwExchangeReconciliationWiringConfigV1
    blocked: bool
    reasons: tuple[str, ...]


def _require_get_v1(
    transport: FullCoreFreshPretradeGetTransportV1,
    *,
    endpoint: str,
    auth_required: bool,
    pretrade_decision_id: str,
) -> Mapping[str, Any]:
    result: FreshPretradeGetTransportResultV1 = transport.get(
        endpoint=endpoint,
        auth_required=auth_required,
        pretrade_decision_id=pretrade_decision_id,
    )
    if result.get_performed is not True or result.payload is None:
        raise PilotCapitalGuardPostBindError(f"GET_INCOMPLETE:{endpoint.split('?', 1)[0]}")
    payload = result.payload
    if not isinstance(payload, Mapping):
        raise PilotCapitalGuardPostBindError("GET_PAYLOAD_NOT_MAPPING")
    if str(payload.get("code") or "") != "0":
        raise PilotCapitalGuardPostBindError("GET_VENUE_CODE_NON_ZERO")
    return payload


def _reference_mark_px_for_market_order_v1(
    transport: FullCoreFreshPretradeGetTransportV1,
    *,
    native_instrument_id: str,
    pretrade_decision_id: str,
) -> str:
    endpoint = f"{ENDPOINT_MARKET_INDEX_TICKERS}?{urlencode({'instId': native_instrument_id})}"
    payload = _require_get_v1(
        transport,
        endpoint=endpoint,
        auth_required=False,
        pretrade_decision_id=pretrade_decision_id,
    )
    data = payload.get("data")
    if not isinstance(data, list) or not data or not isinstance(data[0], Mapping):
        raise PilotCapitalGuardPostBindError("REFERENCE_MARK_PX_MISSING")
    mark = data[0].get("idxPx") or data[0].get("markPx")
    if mark is None or not str(mark).strip():
        raise PilotCapitalGuardPostBindError("REFERENCE_MARK_PX_MISSING")
    return str(mark).strip()


def extract_account_uid_from_config_payload_v1(payload: Mapping[str, Any]) -> str:
    data = payload.get("data")
    if not isinstance(data, list) or not data or not isinstance(data[0], Mapping):
        raise PilotCapitalGuardPostBindError("ACCOUNT_CONFIG_UID_MISSING")
    uid = str(data[0].get("uid") or "").strip()
    if not uid:
        raise PilotCapitalGuardPostBindError("ACCOUNT_CONFIG_UID_MISSING")
    return uid


def _inst_family_from_instruments_v1(
    instruments_payload: Mapping[str, Any], *, native_instrument_id: str
) -> str:
    data = instruments_payload.get("data")
    if not isinstance(data, list):
        raise PilotCapitalGuardPostBindError("INSTRUMENTS_DATA_MISSING")
    for row in data:
        if isinstance(row, Mapping) and str(row.get("instId") or "") == native_instrument_id:
            family = str(row.get("instFamily") or "").strip()
            if family:
                return family
    raise PilotCapitalGuardPostBindError("INSTRUMENT_FAMILY_MISSING")


def _existing_exposure_notional_usdc_v1(
    *,
    positions_payload: Mapping[str, Any],
    native_instrument_id: str,
) -> str:
    data = positions_payload.get("data")
    if not isinstance(data, list):
        raise PilotCapitalGuardPostBindError("POSITIONS_DATA_MISSING")
    total = Decimal("0")
    saw_unknown = False
    for row in data:
        if not isinstance(row, Mapping):
            continue
        if str(row.get("instId") or "") != native_instrument_id:
            continue
        pos = str(row.get("pos") or "0").strip()
        try:
            if Decimal(pos) == 0:
                continue
        except InvalidOperation:
            saw_unknown = True
            continue
        notional = row.get("notionalUsd") or row.get("notionalUsdForMargin")
        if notional is None or str(notional).strip() == "":
            saw_unknown = True
            continue
        try:
            total += Decimal(str(notional).strip())
        except InvalidOperation:
            saw_unknown = True
    if saw_unknown and total == 0:
        raise PilotCapitalGuardPostBindError("EXISTING_EXPOSURE_UNKNOWN")
    return format(total, "f")


def collect_pilot_capital_guard_authoritative_evidence_v1(
    *,
    transport: FullCoreFreshPretradeGetTransportV1,
    pretrade_decision_id: str,
    native_instrument_id: str,
    inst_type: str = "SWAP",
    td_mode: str = "cross",
) -> PilotCapitalGuardAuthoritativeEvidenceV1:
    decision = str(pretrade_decision_id or "").strip()
    native = str(native_instrument_id or "").strip()
    if not decision or not native:
        raise PilotCapitalGuardPostBindError("PRETRADE_OR_NATIVE_INSTRUMENT_REQUIRED")

    instruments_ep = (
        f"{ENDPOINT_PUBLIC_INSTRUMENTS}?{urlencode({'instType': inst_type, 'instId': native})}"
    )
    instruments_payload = _require_get_v1(
        transport,
        endpoint=instruments_ep,
        auth_required=False,
        pretrade_decision_id=decision,
    )
    metadata = extract_instrument_contract_metadata_v1(
        instruments_payload,
        instrument_id=native,
    )
    inst_family = _inst_family_from_instruments_v1(
        instruments_payload,
        native_instrument_id=native,
    )

    balance_payload = _require_get_v1(
        transport,
        endpoint=ENDPOINT_ACCOUNT_BALANCE,
        auth_required=True,
        pretrade_decision_id=decision,
    )
    avail = extract_avail_eq_usdc_from_balance_payload_v1(balance_payload)
    if avail is None:
        raise PilotCapitalGuardPostBindError("AVAIL_EQ_USDC_MISSING")

    leverage_ep = (
        f"{ENDPOINT_ACCOUNT_LEVERAGE_INFO}?{urlencode({'instId': native, 'mgnMode': td_mode})}"
    )
    leverage_payload = _require_get_v1(
        transport,
        endpoint=leverage_ep,
        auth_required=True,
        pretrade_decision_id=decision,
    )
    observed_leverage = extract_leverage_from_leverage_payload_v1(
        leverage_payload=leverage_payload,
        instrument_id=native,
    )
    if observed_leverage is None:
        raise PilotCapitalGuardPostBindError("OBSERVED_LEVERAGE_MISSING")

    tiers_ep = (
        f"{POSITION_TIERS_ENDPOINT}?instType={inst_type}&tdMode={td_mode}"
        f"&instFamily={inst_family}&instId={native}"
    )
    tiers_payload = _require_get_v1(
        transport,
        endpoint=tiers_ep,
        auth_required=False,
        pretrade_decision_id=decision,
    )
    imr = bind_imr_from_public_position_tiers_payload_v1(
        position_tiers_payload=tiers_payload,
        expected_inst_family=inst_family,
    )

    pending_ep = f"{ORDERS_PENDING_ENDPOINT}?{urlencode({'instType': inst_type, 'instId': native})}"
    pending_payload = _require_get_v1(
        transport,
        endpoint=pending_ep,
        auth_required=True,
        pretrade_decision_id=decision,
    )

    positions_ep = (
        f"{ENDPOINT_ACCOUNT_POSITIONS}?{urlencode({'instType': inst_type, 'instId': native})}"
    )
    positions_payload = _require_get_v1(
        transport,
        endpoint=positions_ep,
        auth_required=True,
        pretrade_decision_id=decision,
    )

    try:
        pre_submit = evaluate_pre_submit_exchange_state_v1(
            positions_payload=positions_payload,
            pending_orders_payload=pending_payload,
            instrument_id=native,
        )
    except LiveCanaryPreSubmitStateError as exc:
        raise PilotCapitalGuardPostBindError(str(exc)) from exc

    existing_exposure = _existing_exposure_notional_usdc_v1(
        positions_payload=positions_payload,
        native_instrument_id=native,
    )

    margin = CanaryCapitalGuardMarginEvidenceV1(
        avail_eq_usdc=avail,
        imr_rate=imr,
        imr_source_class=IMR_SOURCE_PUBLIC_POSITION_TIERS_QTY_ONE,
        pretrade_decision_id=decision,
        expected_pretrade_decision_id=decision,
    )
    exposure = CanaryCapitalGuardExposureEvidenceV1(
        open_order_count=int(pre_submit.get("open_order_count") or 0),
        open_position_count=int(pre_submit.get("open_position_count") or 0),
        unknown_submit_active=False,
        recovery_state_clear=pre_submit.get("recovery_state_clear") is True,
        transport_retry_count=0,
    )
    return PilotCapitalGuardAuthoritativeEvidenceV1(
        margin_evidence=margin,
        exposure_evidence=exposure,
        observed_leverage=observed_leverage,
        existing_exposure_notional_usdc=existing_exposure,
    )


def _authorization_binding_from_join_v1(
    binding: Any,
    *,
    session_id: str,
) -> FullCoreAuthorizationBindingV1:
    return FullCoreAuthorizationBindingV1(
        owner_go=binding.owner_go,
        origin_main_sha=binding.origin_main_sha,
        account_scope=binding.account_identity,
        environment=binding.environment,
        execution_mode=binding.execution_mode,
        canonical_decision_id=binding.canonical_decision_id,
        instrument_id=binding.instrument_id,
        native_id=binding.native_id,
        selected_direction=binding.selected_direction,
        order_side=binding.order_side,
        final_quantity=binding.final_quantity,
        order_type=binding.order_type,
        order_price=binding.order_price,
        venue_plan_digest=binding.venue_plan_digest,
        envelope_digest=binding.envelope_digest,
        guard_config_digest=binding.guard_config_digest,
        session_id=session_id,
        clordid=binding.clordid,
    )


def build_pilot_dw_exchange_reconciliation_wiring_config_v1(
    *,
    authorization_binding: FullCoreAuthorizationBindingV1,
    envelope: FinalOrderEnvelopeV1,
    pretrade_decision_id: str,
    origin_main_sha: str,
    read_only_get_transport: FullCoreFreshPretradeGetTransportV1,
    venue_plan_identity: str,
    submit_attempt_id: str,
    private_get_go: str = "GRANTED_SCOPED_READ_ONLY",
) -> DwExchangeReconciliationWiringConfigV1:
    return DwExchangeReconciliationWiringConfigV1(
        binding=authorization_binding,
        decision_outcome="ENTER",
        venue_plan_identity=venue_plan_identity,
        envelope_identity=str(envelope.envelope_id),
        submit_attempt_id=submit_attempt_id,
        local_durable_state_version="v1",
        pretrade_decision_id=str(pretrade_decision_id),
        origin_main_sha=str(origin_main_sha).strip().lower(),
        read_only_get_transport=read_only_get_transport,
        private_get_go=private_get_go,
        apply_durable_atomic_state=False,
    )


def enforce_pilot_capital_guard_before_enter_post_v1(
    *,
    pilot_capital_guard_bind_go: str,
    envelope: FinalOrderEnvelopeV1,
    read_only_get_transport: FullCoreFreshPretradeGetTransportV1,
    pretrade_decision_id: str,
    native_instrument_id: str,
    canonical_decision_id: str,
    account_identity: str | None,
    origin_main_sha: str,
    guard_config: FullCoreCapitalGuardConfigV1 | None = None,
    atomic_state_dir: Path | None = None,
    master_v2_decision: str = "enter_long",
    pretrade_reference_mark_px: str | None = None,
    private_get_go: str = "GRANTED_SCOPED_READ_ONLY",
) -> PilotCapitalGuardPostBindResultV1:
    if (
        str(pilot_capital_guard_bind_go or "").strip()
        != OWNER_GO_CURRENT_PILOT_CAPITAL_GUARD_POST_BIND_V1
    ):
        raise PilotCapitalGuardPostBindError("PILOT_CAPITAL_GUARD_BIND_GO_DENIED")
    assert_envelope_unmodified_v1(envelope)
    transport = read_only_get_transport
    if transport is None:
        raise PilotCapitalGuardPostBindError("READ_TRANSPORT_REQUIRED")

    decision = str(pretrade_decision_id or "").strip()
    native = str(native_instrument_id or "").strip()
    if not native:
        raise PilotCapitalGuardPostBindError("NATIVE_INSTRUMENT_ID_REQUIRED")

    config_payload = _require_get_v1(
        transport,
        endpoint=ENDPOINT_ACCOUNT_CONFIG,
        auth_required=True,
        pretrade_decision_id=decision,
    )
    account_uid = extract_account_uid_from_config_payload_v1(config_payload)
    if account_identity is not None and str(account_identity).strip() != account_uid:
        raise PilotCapitalGuardPostBindError("ACCOUNT_IDENTITY_MISMATCH")
    account_scope = account_uid

    instruments_ep = (
        f"{ENDPOINT_PUBLIC_INSTRUMENTS}?{urlencode({'instType': 'SWAP', 'instId': native})}"
    )
    instruments_payload = _require_get_v1(
        transport,
        endpoint=instruments_ep,
        auth_required=False,
        pretrade_decision_id=decision,
    )
    try:
        metadata = extract_instrument_contract_metadata_v1(
            instruments_payload,
            instrument_id=native,
        )
    except FullCoreCapitalGuardBindingError as exc:
        raise PilotCapitalGuardPostBindError(str(exc)) from exc

    cfg = guard_config or load_full_core_capital_guard_config_v1()
    join_binding = build_full_core_enter_post_capital_guard_join_binding_v1(
        canonical_decision_id=canonical_decision_id or decision,
        native_instrument_id=native,
        envelope=envelope,
        master_v2_decision=master_v2_decision,
        account_identity=account_scope,
        environment=PILOT_ENVIRONMENT,
        origin_main_sha=origin_main_sha,
        guard_config_digest=cfg.config_digest,
        instrument_metadata=metadata,
    )

    evidence = collect_pilot_capital_guard_authoritative_evidence_v1(
        transport=transport,
        pretrade_decision_id=decision,
        native_instrument_id=native,
        td_mode=str(envelope.td_mode or "cross"),
    )

    ref_mark = pretrade_reference_mark_px
    if (
        not str(ref_mark or "").strip()
        and str(envelope.order_type or "").lower() == "market"
        and not str(envelope.price or "").strip()
    ):
        ref_mark = _reference_mark_px_for_market_order_v1(
            transport,
            native_instrument_id=native,
            pretrade_decision_id=decision,
        )

    session_id = f"pilot-enter-post:{envelope.envelope_id}"
    try:
        join_result = run_full_core_pre_post_capital_guard_join_v1(
            binding=join_binding,
            envelope=envelope,
            guard_config=cfg,
            margin_evidence=evidence.margin_evidence,
            exposure_evidence=evidence.exposure_evidence,
            observed_leverage=evidence.observed_leverage,
            existing_exposure_notional_usdc=evidence.existing_exposure_notional_usdc,
            join_mode=FullCoreCapitalGuardJoinMode.PRODUCTIVE_PILOT_ENFORCE,
            atomic_state_dir=atomic_state_dir,
            session_id=session_id,
            account_evidence_scope=account_scope,
            authoritative_environment=PILOT_ENVIRONMENT,
            authoritative_venue_plan_digest=join_binding.venue_plan_digest,
            pretrade_reference_mark_px=ref_mark,
            pilot_enforce_owner_go=pilot_capital_guard_bind_go,
        )
    except FullCorePrePostCapitalGuardJoinError as exc:
        raise PilotCapitalGuardPostBindError(str(exc)) from exc

    auth_binding = _authorization_binding_from_join_v1(join_binding, session_id=session_id)
    dw_config = build_pilot_dw_exchange_reconciliation_wiring_config_v1(
        authorization_binding=auth_binding,
        envelope=envelope,
        pretrade_decision_id=decision,
        origin_main_sha=origin_main_sha,
        read_only_get_transport=transport,
        venue_plan_identity=join_binding.venue_plan_digest,
        submit_attempt_id=f"enter-post:{envelope.client_order_id}",
        private_get_go=private_get_go,
    )
    blocked = join_result.guard_blocked is True or join_result.guard_allowed is not True
    return PilotCapitalGuardPostBindResultV1(
        join_result=join_result,
        authorization_binding=auth_binding,
        dw_wiring_config=dw_config,
        blocked=blocked,
        reasons=join_result.reasons,
    )


__all__ = [
    "CONTRACT_ID",
    "ORDERS_PENDING_ENDPOINT",
    "OWNER_GO_CURRENT_PILOT_CAPITAL_GUARD_POST_BIND_V1",
    "PILOT_ENVIRONMENT",
    "POST_COUNT",
    "PilotCapitalGuardAuthoritativeEvidenceV1",
    "PilotCapitalGuardPostBindError",
    "PilotCapitalGuardPostBindResultV1",
    "build_pilot_dw_exchange_reconciliation_wiring_config_v1",
    "collect_pilot_capital_guard_authoritative_evidence_v1",
    "enforce_pilot_capital_guard_before_enter_post_v1",
    "extract_account_uid_from_config_payload_v1",
]
