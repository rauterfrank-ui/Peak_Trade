"""Reject-only venue limits at the original N1 final-plan consumer.

Uses the original decision-bound GET results. No GET, sizing, reservation,
permit, POST or authority. A planning assessment is not a later send admission.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from decimal import Decimal, InvalidOperation
import hashlib
import json
from typing import Any, Mapping
from urllib.parse import parse_qs, urlsplit

from src.ops.full_core_live_path_composition_root_v1.execution_admission_contract_v1 import (
    FreshPretradeGetStatusV1,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    FreshPretradeGetTransportResultV1,
    REQUIRED_GET_ITEM_SPECS,
    _item_status_and_reasons,
)
from src.ops.full_core_live_path_composition_root_v1.models_v1 import VenuePlanCandidateV1
from src.ops.full_core_live_path_composition_root_v1.pretrade_acquisition_v1 import (
    acquisition_age_seconds_v1,
    utc_now_iso_v1,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1

CONTRACT_ID = "CURRENT_PRODUCTIVE_N1_VENUE_QUANTITY_LIMIT_ADMISSION_V1"


def _json(value: Any) -> str:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    )


def _digest(value: Any) -> str:
    return hashlib.sha256(_json(value).encode()).hexdigest()


@dataclass(frozen=True)
class VenueQuantitySourceV1:
    endpoint: str
    acquired_at_utc: str
    acquisition_decision_id: str
    response_body_sha256: str
    payload_json: str


@dataclass(frozen=True)
class N1VenueQuantityLimitsObservationV1:
    account_identity: str
    bound_instrument_json: str
    decision_epoch: str
    cycle_id: str
    acquisition_decision_id: str
    public_source: VenueQuantitySourceV1
    private_source: VenueQuantitySourceV1
    integrity_digest: str = ""

    def digest_v1(self) -> str:
        material = asdict(self)
        material.pop("integrity_digest")
        return _digest(material)


@dataclass(frozen=True)
class N1VenueQuantityLimitAssessmentV1:
    allowed: bool
    reason_codes: tuple[str, ...]
    observation_digest: str = ""
    plan_digest: str = ""
    final_native_quantity: str = ""
    selected_private_field: str = ""
    private_maximum: str = ""
    selected_public_field: str = ""
    public_maximum: str = ""
    source_binding: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract_id": CONTRACT_ID,
            **asdict(self),
            "scope": "N1_FINAL_PLAN_ONLY",
            "runtime_authorization_effect": "NONE",
        }


def capture_n1_venue_quantity_limits_v1(
    *,
    results: Mapping[str, FreshPretradeGetTransportResultV1],
    acquisition_decision_id: str,
    account_identity: str,
    bound_instrument: BoundInstrumentV1,
    decision_epoch: str,
    cycle_id: str,
) -> N1VenueQuantityLimitsObservationV1:
    """Detach the two original response bodies; never consult a path cache."""

    def capture(item_id: str) -> VenueQuantitySourceV1:
        spec = next(item for item in REQUIRED_GET_ITEM_SPECS if item.item_id == item_id)
        result = results.get(spec.fetch_group)
        if not isinstance(result, FreshPretradeGetTransportResultV1):
            raise ValueError("VENUE_QUANTITY_SOURCE_MISSING")
        status, _ = _item_status_and_reasons(
            spec=spec,
            result=result,
            pretrade_decision_id=acquisition_decision_id,
            requested_endpoint=result.endpoint,
        )
        if status != FreshPretradeGetStatusV1.TRUSTED_PRESENT.value:
            raise ValueError("VENUE_QUANTITY_SOURCE_NOT_TRUSTED")
        if result.pretrade_decision_id != acquisition_decision_id:
            raise ValueError("VENUE_QUANTITY_ACQUISITION_MISMATCH")
        return VenueQuantitySourceV1(
            endpoint=result.endpoint,
            acquired_at_utc=result.acquired_at_utc,
            acquisition_decision_id=result.pretrade_decision_id,
            response_body_sha256=result.body_sha256,
            payload_json=_json(result.payload),
        )

    observation = N1VenueQuantityLimitsObservationV1(
        account_identity=account_identity,
        bound_instrument_json=_json(bound_instrument.to_dict()),
        decision_epoch=decision_epoch,
        cycle_id=cycle_id,
        acquisition_decision_id=acquisition_decision_id,
        public_source=capture("MAX_SIZE"),
        private_source=capture("MAX_AVAILABLE"),
    )
    return replace(observation, integrity_digest=observation.digest_v1())


def _row(source: VenueQuantitySourceV1, *, native: str) -> Mapping[str, Any]:
    payload = json.loads(source.payload_json)
    if (
        not isinstance(payload, dict)
        or payload.get("code") != "0"
        or not isinstance(payload.get("data"), list)
    ):
        raise ValueError("VENUE_QUANTITY_RESPONSE_MALFORMED")
    if any(not isinstance(row, dict) for row in payload["data"]):
        raise ValueError("VENUE_QUANTITY_RESPONSE_MALFORMED")
    rows = [row for row in payload["data"] if row.get("instId") == native]
    if len(rows) != 1:
        raise ValueError("VENUE_QUANTITY_INSTRUMENT_ROW_NOT_UNIQUE")
    return rows[0]


def _decimal(value: Any, *, positive: bool, reason: str) -> Decimal:
    if not isinstance(value, str) or not value or value != value.strip():
        raise ValueError(reason)
    try:
        result = Decimal(value)
        if not result.is_finite() or result < 0 or (positive and result == 0):
            raise ValueError(reason)
        return result
    except InvalidOperation as exc:
        raise ValueError(reason) from exc


def _query(source: VenueQuantitySourceV1, *, path: str) -> dict[str, list[str]]:
    parsed = urlsplit(source.endpoint)
    if parsed.scheme or parsed.netloc or parsed.fragment or parsed.path != path:
        raise ValueError("VENUE_QUANTITY_ENDPOINT_SCOPE_MISMATCH")
    return parse_qs(parsed.query, keep_blank_values=True)


def assess_n1_final_plan_venue_quantity_v1(
    *,
    observation: N1VenueQuantityLimitsObservationV1 | None,
    plan: VenuePlanCandidateV1,
    bound_instrument: BoundInstrumentV1,
    account_identity: str,
    decision_epoch: str,
    cycle_id: str,
    evaluated_at_utc: str | None = None,
) -> N1VenueQuantityLimitAssessmentV1:
    """Compare the unchanged final native count after sizing, before commit.

    Source freshness uses the original acquisition owner policy. No common plan
    expiry or future send right is created. Close-only has a different owner.
    """
    source_binding: dict[str, str] = {}
    try:
        if not isinstance(observation, N1VenueQuantityLimitsObservationV1):
            raise ValueError("VENUE_QUANTITY_OBSERVATION_MISSING")
        if observation.integrity_digest != observation.digest_v1():
            raise ValueError("VENUE_QUANTITY_OBSERVATION_CHANGED")
        source_binding = {
            "account_identity_digest": _digest(observation.account_identity),
            "bound_instrument_digest": hashlib.sha256(
                observation.bound_instrument_json.encode()
            ).hexdigest(),
            "decision_epoch": observation.decision_epoch,
            "cycle_id": observation.cycle_id,
            "acquisition_decision_id": observation.acquisition_decision_id,
        }
        for label, source in (
            ("public", observation.public_source),
            ("private", observation.private_source),
        ):
            source_binding.update(
                {
                    label + "_endpoint": source.endpoint,
                    label + "_acquired_at_utc": source.acquired_at_utc,
                    label + "_response_body_sha256": source.response_body_sha256,
                    label + "_payload_sha256": hashlib.sha256(
                        source.payload_json.encode()
                    ).hexdigest(),
                }
            )
        if (
            not account_identity
            or observation.account_identity != account_identity
            or observation.bound_instrument_json != _json(bound_instrument.to_dict())
            or observation.decision_epoch != decision_epoch
            or observation.cycle_id != cycle_id
        ):
            raise ValueError("VENUE_QUANTITY_CONTEXT_MISMATCH")
        expected_acquisition = (
            _json({"decision_epoch": decision_epoch, "cycle_id": cycle_id})
            if cycle_id
            else decision_epoch
        )
        if observation.acquisition_decision_id != expected_acquisition:
            raise ValueError("VENUE_QUANTITY_ACQUISITION_MISMATCH")
        now = evaluated_at_utc or utc_now_iso_v1()
        for source in (observation.public_source, observation.private_source):
            if source.acquisition_decision_id != expected_acquisition:
                raise ValueError("VENUE_QUANTITY_ACQUISITION_MISMATCH")
            acquisition_age_seconds_v1(acquired_at_utc=source.acquired_at_utc, now_utc=now)
        native = bound_instrument.venue_native_id
        if not isinstance(plan, VenuePlanCandidateV1) or plan.instrument_id != native:
            raise ValueError("VENUE_QUANTITY_PLAN_INSTRUMENT_MISMATCH")
        if (
            plan.reduce_only is not False
            or plan.side not in {"buy", "sell"}
            or plan.order_type not in {"market", "limit"}
        ):
            raise ValueError("VENUE_QUANTITY_NEW_RISK_PLAN_REQUIRED")
        wire = plan.venue_native_payload
        if (
            not isinstance(wire, Mapping)
            or any(
                wire.get(key) != value
                for key, value in (
                    ("instId", native),
                    ("side", plan.side),
                    ("ordType", plan.order_type),
                    ("sz", plan.quantity),
                    ("tdMode", plan.td_mode),
                )
            )
            or wire.get("reduceOnly", False) is not False
        ):
            raise ValueError("VENUE_QUANTITY_WIRE_PLAN_MISMATCH")
        public_query = _query(observation.public_source, path="/api/v5/public/instruments")
        if (
            set(public_query) != {"instId", "instType"}
            or public_query["instId"] != [native]
            or public_query["instType"] not in [["SWAP"], ["FUTURES"]]
        ):
            raise ValueError("VENUE_QUANTITY_PUBLIC_SCOPE_MISMATCH")
        private_query = _query(observation.private_source, path="/api/v5/account/max-size")
        if (
            set(private_query) - {"instId", "tdMode", "px"}
            or private_query.get("instId") != [native]
            or private_query.get("tdMode") != [plan.td_mode]
        ):
            raise ValueError("VENUE_QUANTITY_PRIVATE_SCOPE_MISMATCH")
        price = wire.get("px", "")
        if (plan.order_type == "limit" and (not price or private_query.get("px") != [price])) or (
            plan.order_type == "market" and ("px" in private_query or price)
        ):
            raise ValueError("VENUE_QUANTITY_PRICE_SCOPE_MISMATCH")
        public = _row(observation.public_source, native=native)
        if public.get("instType") != public_query["instType"][0]:
            raise ValueError("VENUE_QUANTITY_INSTRUMENT_TYPE_MISMATCH")
        private = _row(observation.private_source, native=native)
        private_limits = {
            key: _decimal(
                private.get(key), positive=False, reason="VENUE_QUANTITY_PRIVATE_MAXIMUM_MALFORMED"
            )
            for key in ("maxBuy", "maxSell")
        }
        private_field = "maxBuy" if plan.side == "buy" else "maxSell"
        public_field = "maxMktSz" if plan.order_type == "market" else "maxLmtSz"
        public_maximum = _decimal(
            public.get(public_field),
            positive=False,
            reason="VENUE_QUANTITY_PUBLIC_MAXIMUM_MALFORMED",
        )
        quantity = _decimal(
            plan.quantity, positive=True, reason="VENUE_QUANTITY_FINAL_COUNT_MALFORMED"
        )
        reasons = []
        if quantity > private_limits[private_field]:
            reasons.append("VENUE_QUANTITY_EXCEEDS_" + private_field.upper())
        if quantity > public_maximum:
            reasons.append("VENUE_QUANTITY_EXCEEDS_" + public_field.upper())
        return N1VenueQuantityLimitAssessmentV1(
            allowed=not reasons,
            reason_codes=tuple(reasons) or ("VENUE_QUANTITY_LIMITS_PASS",),
            observation_digest=observation.digest_v1(),
            plan_digest=_digest(asdict(plan)),
            final_native_quantity=plan.quantity,
            selected_private_field=private_field,
            private_maximum=str(private_limits[private_field]),
            selected_public_field=public_field,
            public_maximum=str(public_maximum),
            source_binding=source_binding,
        )
    except (ValueError, TypeError, AttributeError, KeyError) as exc:
        return N1VenueQuantityLimitAssessmentV1(
            allowed=False, reason_codes=(str(exc),), source_binding=source_binding
        )
