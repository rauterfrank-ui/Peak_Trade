"""Contract tests for CAPABILITY_P4_L6_EXPLICIT_D_T_PROPOSAL_V1."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from src.ops.p4_l6_explicit_d_t_proposal_v1 import (
    AUTHORITY,
    CAPABILITY_ID,
    NO_DEFAULT,
    NO_FALLBACK,
    NO_FORMULA,
    NUMERIC_FORMULA_AUTHORITY,
    PRODUCTIVE_BINDING_AUTHORIZED,
    RUNTIME_AUTHORIZATION_EFFECT,
    ExplicitDtProposalV1,
    P4ExplicitDtProposalIdentityContextV1,
    proposal_missing_fail_closed_v1,
    validate_and_transport_explicit_dt_proposal_v1,
    validate_explicit_dt_proposal_v1,
)
from src.ops.p4_l6_explicit_d_t_proposal_v1.constants_v1 import (
    FORBIDDEN_RUNTIME_PRODUCER_IMPORTS,
    SCHEMA_VERSION,
)
from src.ops.p4_l6_explicit_d_t_proposal_v1.reason_codes_v1 import ExplicitDtProposalFailureCodeV1

_REPO_ROOT = Path(__file__).resolve().parents[2]
_PKG = _REPO_ROOT / "src" / "ops" / "p4_l6_explicit_d_t_proposal_v1"


def _context() -> P4ExplicitDtProposalIdentityContextV1:
    return P4ExplicitDtProposalIdentityContextV1(
        instrument_id="okx_eea:linear_perpetual:ETH:USDT:USDT:eth-usdt-swap",
        venue="OKX",
        venue_instrument_id="ETH-USDT-SWAP",
    )


def _valid_proposal(**overrides: object) -> ExplicitDtProposalV1:
    base = dict(
        value=42.5,
        producer_id="external-owner.example/v1",
        instrument_id="okx_eea:linear_perpetual:ETH:USDT:USDT:eth-usdt-swap",
        venue="OKX",
        venue_instrument_id="ETH-USDT-SWAP",
        observation_lineage_id="c1-lineage-abc",
        proposal_id="prop-001",
        schema_version=SCHEMA_VERSION,
        parameter_provenance={"provenance_kind": "owner_explicit_numeric"},
    )
    base.update(overrides)
    return ExplicitDtProposalV1(**base)  # type: ignore[arg-type]


def test_capability_authority_constants() -> None:
    assert CAPABILITY_ID == "CAPABILITY_P4_L6_EXPLICIT_D_T_PROPOSAL_V1"
    assert AUTHORITY == "PROPOSAL_CONTRACT_ONLY"
    assert NUMERIC_FORMULA_AUTHORITY == "NONE"
    assert PRODUCTIVE_BINDING_AUTHORIZED is False
    assert RUNTIME_AUTHORIZATION_EFFECT == "NONE"
    assert NO_DEFAULT is True
    assert NO_FORMULA is True
    assert NO_FALLBACK is True


def test_valid_exact_proposal_passes() -> None:
    proposal = _valid_proposal()
    result = validate_explicit_dt_proposal_v1(proposal, identity_context=_context())
    assert result.ok is True
    assert result.failure_codes == ()


@pytest.mark.parametrize(
    "value,code",
    [
        (0.0, ExplicitDtProposalFailureCodeV1.VALUE_NOT_POSITIVE.value),
        (-1.0, ExplicitDtProposalFailureCodeV1.VALUE_NOT_POSITIVE.value),
        (float("nan"), ExplicitDtProposalFailureCodeV1.VALUE_NOT_FINITE.value),
        (float("inf"), ExplicitDtProposalFailureCodeV1.VALUE_NOT_FINITE.value),
    ],
)
def test_invalid_numeric_values_reject(value: float, code: str) -> None:
    proposal = _valid_proposal(value=value)
    result = validate_explicit_dt_proposal_v1(proposal, identity_context=_context())
    assert result.ok is False
    assert code in result.failure_codes


def test_bool_value_rejects() -> None:
    proposal = _valid_proposal(value=True)  # type: ignore[arg-type]
    result = validate_explicit_dt_proposal_v1(proposal, identity_context=_context())
    assert result.ok is False
    assert ExplicitDtProposalFailureCodeV1.VALUE_TYPE_INVALID.value in result.failure_codes


def test_instrument_id_mismatch_rejects() -> None:
    proposal = _valid_proposal(instrument_id="other-id")
    result = validate_explicit_dt_proposal_v1(proposal, identity_context=_context())
    assert result.ok is False
    assert ExplicitDtProposalFailureCodeV1.INSTRUMENT_ID_MISMATCH.value in result.failure_codes


def test_venue_mismatch_rejects() -> None:
    proposal = _valid_proposal(venue="okx_eea")
    result = validate_explicit_dt_proposal_v1(proposal, identity_context=_context())
    assert result.ok is False
    assert (
        ExplicitDtProposalFailureCodeV1.VENUE_MISMATCH.value in result.failure_codes
        or ExplicitDtProposalFailureCodeV1.IDENTITY_FIELD_NORMALIZATION_FORBIDDEN.value
        in result.failure_codes
    )


def test_venue_native_mismatch_rejects() -> None:
    proposal = _valid_proposal(venue_instrument_id="BTC-USDT-SWAP")
    result = validate_explicit_dt_proposal_v1(proposal, identity_context=_context())
    assert result.ok is False
    assert (
        ExplicitDtProposalFailureCodeV1.VENUE_INSTRUMENT_ID_MISMATCH.value in result.failure_codes
    )


def test_missing_provenance_rejects() -> None:
    proposal = _valid_proposal(parameter_provenance={})
    result = validate_explicit_dt_proposal_v1(proposal, identity_context=_context())
    assert result.ok is False
    assert ExplicitDtProposalFailureCodeV1.PARAMETER_PROVENANCE_EMPTY.value in result.failure_codes


def test_unsupported_schema_rejects() -> None:
    proposal = _valid_proposal(schema_version="explicit_dt_proposal.v0")
    result = validate_explicit_dt_proposal_v1(proposal, identity_context=_context())
    assert result.ok is False
    assert ExplicitDtProposalFailureCodeV1.SCHEMA_VERSION_UNSUPPORTED.value in result.failure_codes


def test_whitespace_identity_forbidden() -> None:
    proposal = _valid_proposal(venue=" OKX")
    result = validate_explicit_dt_proposal_v1(proposal, identity_context=_context())
    assert result.ok is False
    assert (
        ExplicitDtProposalFailureCodeV1.IDENTITY_FIELD_NORMALIZATION_FORBIDDEN.value
        in result.failure_codes
    )


def test_adapter_preserves_value_exactly() -> None:
    proposal = _valid_proposal(value=123.456789)
    validation, transport, step = validate_and_transport_explicit_dt_proposal_v1(
        proposal,
        identity_context=_context(),
        mark_price_m_t=100.0,
    )
    assert validation.ok is True
    assert transport.ok is True
    assert transport.proposed_d_t == 123.456789
    assert step is not None
    assert step.proposed_d_t == 123.456789
    assert step.mark_price_m_t == 100.0


def test_none_proposal_fail_closed_no_default() -> None:
    missing = proposal_missing_fail_closed_v1()
    assert missing.ok is False
    validation, transport, step = validate_and_transport_explicit_dt_proposal_v1(
        None,
        identity_context=_context(),
        mark_price_m_t=100.0,
    )
    assert validation.ok is False
    assert transport.proposed_d_t is None
    assert step is None


def test_package_has_no_forbidden_imports() -> None:
    for path in _PKG.glob("*.py"):
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported.add(alias.name)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
        for forbidden in FORBIDDEN_RUNTIME_PRODUCER_IMPORTS:
            for name in imported:
                assert forbidden not in name, f"{path.name} imports forbidden {name}"


def test_package_source_has_no_formula_keywords() -> None:
    forbidden_snippets = (
        "CANONICAL_UP_DISTANCE",
        "compute_research_d_t_v1",
        "derive_scope_event_distances_v1",
        "RuntimeScopeState",
        "current_hysteresis_band",
    )
    for path in _PKG.glob("*.py"):
        if path.name == "constants_v1.py":
            continue  # guard list only; not runtime usage
        text = path.read_text(encoding="utf-8")
        for snippet in forbidden_snippets:
            assert snippet not in text, f"{path.name} must not reference {snippet}"


def test_spec_doc_exists() -> None:
    spec = _REPO_ROOT / "docs/ops/specs/CAPABILITY_P4_L6_EXPLICIT_D_T_PROPOSAL_V1.md"
    assert spec.is_file()
    body = spec.read_text(encoding="utf-8")
    assert "PRODUCTIVE_BINDING_AUTHORIZED=false" in body
    assert "NUMERIC_FORMULA_AUTHORITY=NONE" in body
