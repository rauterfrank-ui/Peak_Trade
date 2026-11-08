"""Exact current native quantity sources at actual POST; no sizing or grant."""

from dataclasses import asdict, dataclass
import hashlib

from .current_productive_n1_venue_quantity_limit_admission_v1 import (
    VenueQuantitySourceV1,
    assess_native_order_venue_quantity_sources_v1,
    capture_venue_quantity_source_v1,
)
from .datasafety_gate_join_into_execution_admission_v1 import (
    evaluate_datasafety_admission_for_transport_result_v1,
)
from .execution_admission_contract_v1 import DataSafetyAdmissionStatusV1
from .final_order_envelope_v1 import FinalOrderEnvelopeV1, assert_envelope_unmodified_v1


class CurrentPostVenueQuantityError(ValueError):
    pass


@dataclass(frozen=True)
class CurrentPostVenueQuantityContextV1:
    envelope: FinalOrderEnvelopeV1
    acquisition_decision_id: str
    public_source: VenueQuantitySourceV1
    private_source: VenueQuantitySourceV1

    def inspect_v1(self, *, envelope, stage):
        try:
            assert_envelope_unmodified_v1(envelope)
            if self.envelope != envelope:
                raise ValueError("ENVELOPE_MISMATCH")
            if (
                not isinstance(self.acquisition_decision_id, str)
                or not self.acquisition_decision_id
                or self.acquisition_decision_id != self.acquisition_decision_id.strip()
                or envelope.quantity_unit.upper() not in {"CONTRACT", "CONTRACTS"}
                or envelope.reduce_only is not False
            ):
                raise ValueError("NATIVE_NEW_ENTRY_CONTEXT_REQUIRED")
            assessment = assess_native_order_venue_quantity_sources_v1(
                public_source=self.public_source,
                private_source=self.private_source,
                acquisition_decision_id=self.acquisition_decision_id,
                native=envelope.instrument_id,
                side=envelope.side,
                quantity=envelope.quantity,
                order_type=envelope.order_type,
                td_mode=envelope.td_mode,
                price=envelope.price,
            )
            if not assessment["allowed"]:
                raise ValueError(",".join(assessment["reason_codes"]))
            return {
                **assessment,
                "scope": "CURRENT_NATIVE_VENUE_QUANTITY_ONLY",
                "envelope_digest": envelope.envelope_digest,
                "acquisition_decision_id": self.acquisition_decision_id,
                "sources": {
                    label: {
                        **asdict(source),
                        "payload_sha256": hashlib.sha256(source.payload_json.encode()).hexdigest(),
                    }
                    for label, source in (
                        ("public", self.public_source),
                        ("private", self.private_source),
                    )
                },
            }
        except (ValueError, TypeError, AttributeError, KeyError) as exc:
            raise CurrentPostVenueQuantityError(f"POST_QUANTITY_DENIED:{stage}:{exc}") from exc


def capture_current_post_venue_quantity_v1(*, envelope, results, acquisition_decision_id):
    for group in ("instruments", "max_size"):
        if (
            evaluate_datasafety_admission_for_transport_result_v1(results.get(group))
            != DataSafetyAdmissionStatusV1.SATISFIED.value
        ):
            raise CurrentPostVenueQuantityError("POST_QUANTITY_DATASAFETY_UNPROVEN")
    try:
        return CurrentPostVenueQuantityContextV1(
            envelope=envelope,
            acquisition_decision_id=acquisition_decision_id,
            public_source=capture_venue_quantity_source_v1(
                results=results, item_id="MAX_SIZE", acquisition_decision_id=acquisition_decision_id
            ),
            private_source=capture_venue_quantity_source_v1(
                results=results,
                item_id="MAX_AVAILABLE",
                acquisition_decision_id=acquisition_decision_id,
            ),
        )
    except (ValueError, TypeError, AttributeError, KeyError) as exc:
        raise CurrentPostVenueQuantityError(f"POST_QUANTITY_SOURCE_UNPROVEN:{exc}") from exc


def inspect_current_post_venue_quantity_v1(context, *, envelope, stage):
    if type(context) is not CurrentPostVenueQuantityContextV1:
        raise CurrentPostVenueQuantityError(f"POST_QUANTITY_CONTEXT_REQUIRED:{stage}")
    return context.inspect_v1(envelope=envelope, stage=stage)
