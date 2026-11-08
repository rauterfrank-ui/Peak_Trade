"""Current original budget-owner veto after submit; no new financial admission."""

from dataclasses import dataclass, field
from pathlib import Path

from .external_effect_permit_v1 import ExternalEffectPermitV1, assert_permit_matches_envelope_v1
from .external_effect_permit_durable_consume_v1 import (
    OriginalPermitTransportAttemptV1,
    load_external_effect_durable_consume_v1,
)
from .final_order_envelope_v1 import FinalOrderEnvelopeV1, assert_envelope_unmodified_v1
from .full_core_exchange_reconciliation_v1 import (
    FullCoreExchangeReconciliationIdentityV1,
    PortfolioExecutionReconciliationIdentityV2,
    parse_exchange_reconciliation_identity_v1,
)


class CurrentPostBudgetAdmissionError(ValueError):
    pass


@dataclass(frozen=True)
class CurrentPostBudgetAdmissionContextV1:
    owner: object = field(repr=False)
    reservation_id: str
    envelope: FinalOrderEnvelopeV1
    identity: object
    permit: ExternalEffectPermitV1
    transport_attempt: OriginalPermitTransportAttemptV1

    def inspect_v1(self, *, envelope, stage):
        from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
            PortfolioCapitalReservationBudgetOwnerV1,
        )

        try:
            if (
                type(self.owner) is not PortfolioCapitalReservationBudgetOwnerV1
                or type(self.transport_attempt) is not OriginalPermitTransportAttemptV1
                or type(self.permit) is not ExternalEffectPermitV1
                or type(self.identity)
                not in {
                    FullCoreExchangeReconciliationIdentityV1,
                    PortfolioExecutionReconciliationIdentityV2,
                }
                or not isinstance(self.reservation_id, str)
                or not self.reservation_id
                or self.envelope != envelope
            ):
                raise ValueError("ORIGINAL_CONTEXT_REQUIRED")
            assert_envelope_unmodified_v1(envelope)
            assert_permit_matches_envelope_v1(self.permit, envelope)
            self.transport_attempt.inspect_v1(
                permit_id=self.permit.permit_id,
                envelope_id=envelope.envelope_id,
                envelope_digest=envelope.envelope_digest,
            )
            record = load_external_effect_durable_consume_v1(
                store_root=self.transport_attempt.store_root
            )["record"]
            if record["authority_ref"] != self.permit.authority_ref:
                raise ValueError("ORIGINAL_PERMIT_AUTHORITY_MISMATCH")
            modern = type(self.identity) is PortfolioExecutionReconciliationIdentityV2
            if modern and not (
                record.get("execution_identity") == self.identity.to_dict()
                and record.get("execution_identity_digest") == self.identity.identity_digest()
            ):
                raise ValueError("ORIGINAL_DUAL_BARRIER_IDENTITY_REQUIRED")
            if not modern and "execution_identity" in record:
                raise ValueError("ORIGINAL_IDENTITY_VERSION_MISMATCH")
            link = self.owner.execution_links_v1().get(self.reservation_id)
            if modern and (
                link is None
                or link.get("transport_store_root")
                != str(Path(self.transport_attempt.store_root).resolve())
            ):
                raise ValueError("ORIGINAL_TRANSPORT_ROOT_MISMATCH")
            # This is the actual original owner's existing locked reader, not
            # an admitted flag copied earlier or a new risk model.
            actual = self.owner.inspect_started_execution_attempt_v1(
                self.reservation_id, envelope, self.identity, self.permit
            )
            if actual != self.identity.to_dict():
                raise ValueError("ORIGINAL_CURRENT_READBACK_MISMATCH")
            self.owner.inspect_current_entry_budget_policy_v1(self.reservation_id, envelope)
            return {
                "scope": "CURRENT_ORIGINAL_BUDGET_EXECUTION_ADMISSION_ONLY",
                "account": self.identity.account_identity,
                "reservation_id": self.reservation_id,
                "execution_identity_digest": self.identity.identity_digest(),
                "execution_identity_contract": self.identity.to_dict()["contract_id"],
                "permit_id": self.permit.permit_id,
                "envelope_digest": envelope.envelope_digest,
            }
        except Exception as exc:
            raise CurrentPostBudgetAdmissionError(f"POST_BUDGET_DENIED:{stage}:{exc}") from exc


def capture_current_post_budget_admission_v1(
    *, owner, reservation_id, envelope, identity, permit, transport_attempt
):
    """Bind the actual original owner and the identity already committed by it."""
    try:
        record = load_external_effect_durable_consume_v1(store_root=transport_attempt.store_root)[
            "record"
        ]
        if "execution_identity" in record:
            actual = parse_exchange_reconciliation_identity_v1(record["execution_identity"])
            if type(actual) is not PortfolioExecutionReconciliationIdentityV2 or (
                identity is not None and identity != actual
            ):
                raise ValueError("ORIGINAL_DUAL_BARRIER_IDENTITY_REQUIRED")
            identity = actual
        elif owner is None and not reservation_id and identity is None:
            # Existing wholly unbound legacy path: absence is not current
            # capital admission and cannot discharge a V2 reference.
            return None
        return CurrentPostBudgetAdmissionContextV1(
            owner, reservation_id, envelope, identity, permit, transport_attempt
        )
    except Exception as exc:
        raise CurrentPostBudgetAdmissionError(f"POST_BUDGET_SOURCE_UNPROVEN:{exc}") from exc


def inspect_current_post_budget_admission_v1(context, *, envelope, transport_attempt, stage):
    try:
        if context is None:
            record = load_external_effect_durable_consume_v1(
                store_root=transport_attempt.store_root
            )["record"]
            if "execution_identity" in record:
                raise ValueError("ORIGINAL_V2_OWNER_REFERENCE_REQUIRED")
            return {"scope": "LEGACY_ORIGINAL_BUDGET_NOT_ASSESSED"}
        if (
            type(context) is not CurrentPostBudgetAdmissionContextV1
            or context.transport_attempt != transport_attempt
        ):
            raise ValueError("ORIGINAL_CONTEXT_REQUIRED")
        return context.inspect_v1(envelope=envelope, stage=stage)
    except CurrentPostBudgetAdmissionError:
        raise
    except Exception as exc:
        raise CurrentPostBudgetAdmissionError(f"POST_BUDGET_DENIED:{stage}:{exc}") from exc
