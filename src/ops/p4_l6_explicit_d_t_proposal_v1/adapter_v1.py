"""Transport adapter: validated ExplicitDtProposalV1 -> MechanicalStepSpecV1.proposed_d_t."""

from __future__ import annotations

from src.ops.p4_l6_explicit_d_t_proposal_v1.models_v1 import (
    ExplicitDtProposalTransportResultV1,
    ExplicitDtProposalV1,
    ExplicitDtProposalValidationResultV1,
    P4ExplicitDtProposalIdentityContextV1,
)
from src.ops.p4_l6_explicit_d_t_proposal_v1.reason_codes_v1 import ExplicitDtProposalFailureCodeV1
from src.ops.p4_l6_explicit_d_t_proposal_v1.validator_v1 import validate_explicit_dt_proposal_v1
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.orchestrator_v1 import (
    MechanicalStepSpecV1,
)


def transport_validated_explicit_dt_proposal_v1(
    proposal: ExplicitDtProposalV1,
    *,
    validation: ExplicitDtProposalValidationResultV1,
) -> ExplicitDtProposalTransportResultV1:
    """Copy proposal.value into MechanicalStepSpecV1.proposed_d_t only when validated."""
    if not validation.ok:
        return ExplicitDtProposalTransportResultV1(
            ok=False,
            proposed_d_t=None,
            failure_codes=validation.failure_codes,
        )
    # Copy-only: no arithmetic, no defaults, no legacy/research imports.
    return ExplicitDtProposalTransportResultV1(
        ok=True,
        proposed_d_t=float(proposal.value),
        failure_codes=(),
    )


def validate_and_transport_explicit_dt_proposal_v1(
    proposal: ExplicitDtProposalV1 | None,
    *,
    identity_context: P4ExplicitDtProposalIdentityContextV1,
    mark_price_m_t: float,
) -> tuple[
    ExplicitDtProposalValidationResultV1,
    ExplicitDtProposalTransportResultV1,
    MechanicalStepSpecV1 | None,
]:
    """Validate then transport. None proposal => fail-closed without inventing a value."""
    if proposal is None:
        missing = ExplicitDtProposalValidationResultV1(
            ok=False,
            failure_codes=(ExplicitDtProposalFailureCodeV1.VALUE_MISSING.value,),
        )
        transport = ExplicitDtProposalTransportResultV1(
            ok=False,
            proposed_d_t=None,
            failure_codes=missing.failure_codes,
        )
        return missing, transport, None

    validation = validate_explicit_dt_proposal_v1(proposal, identity_context=identity_context)
    transport = transport_validated_explicit_dt_proposal_v1(proposal, validation=validation)
    if not transport.ok:
        return validation, transport, None
    step = MechanicalStepSpecV1(
        mark_price_m_t=float(mark_price_m_t),
        proposed_d_t=transport.proposed_d_t,
    )
    return validation, transport, step
