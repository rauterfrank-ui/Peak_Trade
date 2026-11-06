"""Pure fail-closed validator for ExplicitDtProposalV1 (no numeric derivation)."""

from __future__ import annotations

import math
from typing import Any, Mapping

from src.ops.p4_l6_explicit_d_t_proposal_v1.constants_v1 import SUPPORTED_SCHEMA_VERSIONS
from src.ops.p4_l6_explicit_d_t_proposal_v1.models_v1 import (
    ExplicitDtProposalV1,
    ExplicitDtProposalValidationResultV1,
    P4ExplicitDtProposalIdentityContextV1,
)
from src.ops.p4_l6_explicit_d_t_proposal_v1.reason_codes_v1 import ExplicitDtProposalFailureCodeV1


def _exact_identity_field(
    value: object, *, code: ExplicitDtProposalFailureCodeV1
) -> tuple[str | None, str | None]:
    if not isinstance(value, str):
        return None, code.value
    if not value:
        return None, code.value
    if value != value.strip():
        return None, ExplicitDtProposalFailureCodeV1.IDENTITY_FIELD_NORMALIZATION_FORBIDDEN.value
    return value, None


def _require_exact_match(
    left: str, right: str, *, code: ExplicitDtProposalFailureCodeV1
) -> str | None:
    if left != right:
        if left.casefold() == right.casefold():
            return ExplicitDtProposalFailureCodeV1.IDENTITY_FIELD_NORMALIZATION_FORBIDDEN.value
        return code.value
    return None


def validate_explicit_dt_proposal_v1(
    proposal: ExplicitDtProposalV1,
    *,
    identity_context: P4ExplicitDtProposalIdentityContextV1,
) -> ExplicitDtProposalValidationResultV1:
    """Validate proposal against P4 identity context. Deterministic fail-closed."""
    failures: list[str] = []

    ctx_inst, err = _exact_identity_field(
        identity_context.instrument_id,
        code=ExplicitDtProposalFailureCodeV1.CONTEXT_INSTRUMENT_ID_MISSING,
    )
    if err:
        failures.append(err)
    ctx_venue, err = _exact_identity_field(
        identity_context.venue, code=ExplicitDtProposalFailureCodeV1.CONTEXT_VENUE_MISSING
    )
    if err:
        failures.append(err)
    ctx_native, err = _exact_identity_field(
        identity_context.venue_instrument_id,
        code=ExplicitDtProposalFailureCodeV1.CONTEXT_VENUE_INSTRUMENT_ID_MISSING,
    )
    if err:
        failures.append(err)

    raw_value = proposal.value
    if isinstance(raw_value, bool) or not isinstance(raw_value, (int, float)):
        failures.append(ExplicitDtProposalFailureCodeV1.VALUE_TYPE_INVALID.value)
    else:
        value = float(raw_value)
        if not math.isfinite(value):
            failures.append(ExplicitDtProposalFailureCodeV1.VALUE_NOT_FINITE.value)
        elif value <= 0.0:
            failures.append(ExplicitDtProposalFailureCodeV1.VALUE_NOT_POSITIVE.value)

    for field_value, missing_code in (
        (proposal.producer_id, ExplicitDtProposalFailureCodeV1.PRODUCER_ID_MISSING),
        (proposal.proposal_id, ExplicitDtProposalFailureCodeV1.PROPOSAL_ID_MISSING),
        (
            proposal.observation_lineage_id,
            ExplicitDtProposalFailureCodeV1.OBSERVATION_LINEAGE_ID_MISSING,
        ),
    ):
        _, err = _exact_identity_field(field_value, code=missing_code)
        if err:
            failures.append(err)

    schema = proposal.schema_version
    if not isinstance(schema, str) or schema not in SUPPORTED_SCHEMA_VERSIONS:
        failures.append(ExplicitDtProposalFailureCodeV1.SCHEMA_VERSION_UNSUPPORTED.value)

    prov = proposal.parameter_provenance
    if prov is None:
        failures.append(ExplicitDtProposalFailureCodeV1.PARAMETER_PROVENANCE_MISSING.value)
    elif not isinstance(prov, Mapping):
        failures.append(ExplicitDtProposalFailureCodeV1.PARAMETER_PROVENANCE_MISSING.value)
    elif len(prov) == 0:
        failures.append(ExplicitDtProposalFailureCodeV1.PARAMETER_PROVENANCE_EMPTY.value)

    inst, err = _exact_identity_field(
        proposal.instrument_id, code=ExplicitDtProposalFailureCodeV1.INSTRUMENT_ID_MISSING
    )
    if err:
        failures.append(err)
    venue, err = _exact_identity_field(
        proposal.venue, code=ExplicitDtProposalFailureCodeV1.VENUE_MISSING
    )
    if err:
        failures.append(err)
    native, err = _exact_identity_field(
        proposal.venue_instrument_id,
        code=ExplicitDtProposalFailureCodeV1.VENUE_INSTRUMENT_ID_MISSING,
    )
    if err:
        failures.append(err)

    if ctx_inst is not None and inst is not None:
        mismatch = _require_exact_match(
            inst,
            ctx_inst,
            code=ExplicitDtProposalFailureCodeV1.INSTRUMENT_ID_MISMATCH,
        )
        if mismatch:
            failures.append(mismatch)
    if ctx_venue is not None and venue is not None:
        mismatch = _require_exact_match(
            venue, ctx_venue, code=ExplicitDtProposalFailureCodeV1.VENUE_MISMATCH
        )
        if mismatch:
            failures.append(mismatch)
    if ctx_native is not None and native is not None:
        mismatch = _require_exact_match(
            native,
            ctx_native,
            code=ExplicitDtProposalFailureCodeV1.VENUE_INSTRUMENT_ID_MISMATCH,
        )
        if mismatch:
            failures.append(mismatch)

    if failures:
        return ExplicitDtProposalValidationResultV1(
            ok=False,
            failure_codes=tuple(sorted(set(failures))),
        )
    return ExplicitDtProposalValidationResultV1(ok=True, failure_codes=())


def proposal_missing_fail_closed_v1() -> ExplicitDtProposalValidationResultV1:
    """Explicit absence of proposal — runtime must not default a numeric value."""
    return ExplicitDtProposalValidationResultV1(
        ok=False,
        failure_codes=(ExplicitDtProposalFailureCodeV1.VALUE_MISSING.value,),
    )
