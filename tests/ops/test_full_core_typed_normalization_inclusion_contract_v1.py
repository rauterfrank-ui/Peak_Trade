"""Typed normalization/inclusion adjudication contract. No mapping. No producer."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from src.ops.capability_11_1_execution_domain_and_order_lifecycle_contracts_v1.execution_ports_v1 import (
    ExecutionPortConstructionForbiddenError,
    bind_simulated_execution_port_v1,
    construct_live_execution_port_v1,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    DIVERGENCE_POLICY_CREATED,
    EQUITY_DIMENSION_BOUND,
    FIELD_TO_DIMENSION_MAPPING_PRESENT,
    FIELD_TO_DIMENSION_MAPPING_SCHEMA_PRESENT,
    GOVERNED_PRODUCER_CREATED,
    GOVERNED_PRODUCTIVE_SOURCE_PRESENT,
    INCLUSION_PROVEN,
    INTERNAL_RECONSTRUCTION_CREATED,
    LIVE_ACCOUNT_BOUND_JOIN_PRESENT,
    LIVE_ARMED,
    LIVE_ENABLED,
    MAPPED_TO_RUNNING_ACCOUNT_EQUITY_AVAILABLE_FOR_SIZING,
    MAPPING_PROVEN,
    NORMALIZATION_AUTHORITY_EFFECT,
    NORMALIZATION_CONTRACT_MISSING_CLOSED,
    NORMALIZATION_RUNTIME_INSTANCE_PRESENT,
    NORMALIZATION_SCHEMA_PRESENT,
    RAW_TO_WITNESS_PROVEN,
    RECONCILIATION_CONTRACT_CREATED,
    RUNTIME_VALUE_BINDING_PRESENT,
    SEMANTIC_MAPPING_PROVEN,
    SOURCE_OBJECT_PRESENT,
    SOURCE_SELECTED,
    VENUE_WITNESS_RUNTIME_INSTANCE_PRESENT,
    VENUE_WITNESS_SCHEMA_PRESENT,
    VENUE_WITNESS_SELECTED,
    WIRE_SEND_PERMITTED,
)
from src.ops.full_core_live_path_composition_root_v1.live_admission_gap_dag_v1 import (
    EARLIEST_DECOMPOSED_CONTRACT_GAP,
    EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY,
    live_admission_gap_dag_v1,
)
from src.ops.full_core_live_path_composition_root_v1.step_29p_capital_risk_admissibility_v1 import (
    evaluate_step_29p_capital_risk_admissibility_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.normalization_inclusion_adjudication_v1 import (
    AMBIGUITY_NONE,
    AMBIGUITY_UNRESOLVED,
    COMPATIBILITY_COMPATIBLE,
    COMPATIBILITY_INCOMPATIBLE,
    COMPATIBILITY_UNPROVEN,
    CONTRADICTION_NONE,
    CONTRADICTION_PRESENT,
    DIMENSION_ID,
    EXCLUSION_ABSENT_PROVENANCE,
    EXCLUSION_CONTRADICTION,
    EXCLUSION_EMPTY_VALUE,
    EXCLUSION_INCOMPATIBLE_ACCOUNT_SCOPE,
    EXCLUSION_INCOMPATIBLE_CURRENCY_DOMAIN,
    EXCLUSION_INSUFFICIENT_EVIDENCE,
    EXCLUSION_MALFORMED_VALUE,
    EXCLUSION_MISSING_VALUE,
    EXCLUSION_STALE_OR_UNPROVEN_FRESHNESS,
    EXCLUSION_UNSUPPORTED_RAW_FIELD_MAPPING,
    EXCLUSION_UNRESOLVED_AMBIGUITY,
    FRESHNESS_STALE,
    FRESHNESS_WITNESS_TIMESTAMPS_NOT_TTL_POLICY,
    INCLUSION_STATUS_EXCLUDED,
    INCLUSION_STATUS_INCLUDED,
    INCLUSION_STATUS_UNPROVEN,
    MAPPING_STATUS_UNBOUND,
    NORMALIZABLE_STATUS_NORMALIZABLE,
    NORMALIZABLE_STATUS_NOT_NORMALIZABLE,
    NormalizationInclusionAdjudicationContractError,
    NormalizationInclusionAdjudicationV1,
    OBSERVATION_PARTICIPATION_STATE_OBSERVED,
    OBSERVATION_VS_AUTHORITY_CLASS_AUTHORITY,
    PROVENANCE_ABSENT,
    PROVENANCE_PRESENT,
    SEMANTIC_MAPPING_STATUS_MAPPED,
    SOURCE_SELECTION_STATUS_NOT_SELECTED,
    SOURCE_SELECTION_STATUS_SELECTED,
    attach_normalization_inclusion_provenance_digest_v1,
    build_normalization_inclusion_adjudication_v1,
    encode_exclusion_reason_codes_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.venue_witness_observation_v1 import (
    OBSERVATION_SEMANTIC_CLASS,
    PRESENCE_EMPTY,
    PRESENCE_MALFORMED,
    PRESENCE_MISSING,
    PRESENCE_NONZERO,
    PRESENCE_ZERO,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.simulated_execution_port_v1 import (
    SimulatedExecutionPortV1,
)
from tests.ops.test_full_core_step_29p_risk_admissibility_pre_construction_v1 import (
    _capital,
    _complete_claim,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
SPEC_PATH = REPO_ROOT / "docs/ops/specs/FULL_CORE_TYPED_NORMALIZATION_INCLUSION_CONTRACT_V1.md"
SCHEMA_PATH = (
    REPO_ROOT
    / "src/ops/governed_productive_account_equity_authority_producer_v1"
    / "normalization_inclusion_adjudication_v1.py"
)
X_HEADING = "11.2.1.X FULL_CORE_TYPED_VENUE_WITNESS_OBSERVATION_CONTRACT"
Y_HEADING = "11.2.1.Y FULL_CORE_TYPED_NORMALIZATION_INCLUSION_CONTRACT"
Z_HEADING = "11.2.1.Z FULL_CORE_TYPED_INTERNAL_RECONSTRUCTION_CONTRACT"
_FORBIDDEN_FALLBACK = "totalEq|eq|adjEq|availEq"


def _default_exclusion_codes(
    *,
    presence: str = PRESENCE_NONZERO,
    account_scope: str = COMPATIBILITY_COMPATIBLE,
    currency_status: str = COMPATIBILITY_COMPATIBLE,
    unit_status: str = COMPATIBILITY_UNPROVEN,
    freshness: str = FRESHNESS_WITNESS_TIMESTAMPS_NOT_TTL_POLICY,
    provenance: str = PROVENANCE_PRESENT,
    ambiguity: str = AMBIGUITY_NONE,
    contradiction: str = CONTRADICTION_NONE,
) -> tuple[str, ...]:
    codes: list[str] = []
    if presence == PRESENCE_MISSING:
        codes.append(EXCLUSION_MISSING_VALUE)
    if presence == PRESENCE_EMPTY:
        codes.append(EXCLUSION_EMPTY_VALUE)
    if presence == PRESENCE_MALFORMED:
        codes.append(EXCLUSION_MALFORMED_VALUE)
    if account_scope == COMPATIBILITY_INCOMPATIBLE:
        codes.append(EXCLUSION_INCOMPATIBLE_ACCOUNT_SCOPE)
    if currency_status == COMPATIBILITY_INCOMPATIBLE:
        codes.append(EXCLUSION_INCOMPATIBLE_CURRENCY_DOMAIN)
    if freshness in {FRESHNESS_WITNESS_TIMESTAMPS_NOT_TTL_POLICY, FRESHNESS_STALE}:
        codes.append(EXCLUSION_STALE_OR_UNPROVEN_FRESHNESS)
    if provenance == PROVENANCE_ABSENT:
        codes.append(EXCLUSION_ABSENT_PROVENANCE)
    if ambiguity == AMBIGUITY_UNRESOLVED:
        codes.append(EXCLUSION_UNRESOLVED_AMBIGUITY)
    if contradiction == CONTRADICTION_PRESENT:
        codes.append(EXCLUSION_CONTRADICTION)
    codes.append(EXCLUSION_UNSUPPORTED_RAW_FIELD_MAPPING)
    if (
        account_scope == COMPATIBILITY_UNPROVEN
        or currency_status == COMPATIBILITY_UNPROVEN
        or unit_status == COMPATIBILITY_UNPROVEN
    ):
        codes.append(EXCLUSION_INSUFFICIENT_EVIDENCE)
    return tuple(sorted(set(codes)))


def _synthetic_fields(
    *, presence: str = PRESENCE_NONZERO, **overrides: object
) -> dict[str, object]:
    raw_value = "1.25"
    normalizable = NORMALIZABLE_STATUS_NORMALIZABLE
    if presence == PRESENCE_MISSING or presence == PRESENCE_EMPTY:
        raw_value = ""
        normalizable = NORMALIZABLE_STATUS_NOT_NORMALIZABLE
    elif presence == PRESENCE_ZERO:
        raw_value = "0"
    elif presence == PRESENCE_MALFORMED:
        raw_value = "not-a-decimal"
        normalizable = NORMALIZABLE_STATUS_NOT_NORMALIZABLE
    account_scope = str(
        overrides.get("account_scope_compatibility_status", COMPATIBILITY_COMPATIBLE)
    )
    currency_status = str(
        overrides.get("currency_domain_compatibility_status", COMPATIBILITY_COMPATIBLE)
    )
    unit_status = str(overrides.get("unit_compatibility_status", COMPATIBILITY_UNPROVEN))
    freshness = str(
        overrides.get("freshness_evidence_status", FRESHNESS_WITNESS_TIMESTAMPS_NOT_TTL_POLICY)
    )
    provenance = str(overrides.get("provenance_status", PROVENANCE_PRESENT))
    ambiguity = str(overrides.get("ambiguity_status", AMBIGUITY_NONE))
    contradiction = str(overrides.get("contradiction_status", CONTRADICTION_NONE))
    codes = _default_exclusion_codes(
        presence=presence,
        account_scope=account_scope,
        currency_status=currency_status,
        unit_status=unit_status,
        freshness=freshness,
        provenance=provenance,
        ambiguity=ambiguity,
        contradiction=contradiction,
    )
    fields: dict[str, object] = {
        "adjudication_id": "SYNTHETIC_NORMALIZATION_ADJUDICATION_ID",
        "source_witness_id": "SYNTHETIC_WITNESS_ID",
        "bound_account_identity": "SYNTHETIC_BOUND_ACCOUNT",
        "bound_venue_identity": "OKX_EEA",
        "rest_host": "eea.okx.com",
        "bound_td_mode": "cross",
        "account_mode": "UNPROVEN",
        "currency_domain": "USDC",
        "decision_epoch": "synthetic-decision-epoch",
        "raw_field_path": "details.availEq",
        "observation_semantic_class": OBSERVATION_SEMANTIC_CLASS,
        "raw_value_representation": raw_value,
        "presence_state": presence,
        "requested_target_dimension_id": DIMENSION_ID,
        "field_to_dimension_mapping_status": MAPPING_STATUS_UNBOUND,
        "observation_participation_state": OBSERVATION_PARTICIPATION_STATE_OBSERVED,
        "normalizable_status": normalizable,
        "semantic_mapping_status": MAPPING_STATUS_UNBOUND,
        "inclusion_status": INCLUSION_STATUS_EXCLUDED,
        "source_selection_status": SOURCE_SELECTION_STATUS_NOT_SELECTED,
        "observation_vs_authority_class": "OBSERVATION",
        "normalization_authority_effect": "NONE",
        "exclusion_reason_codes": encode_exclusion_reason_codes_v1(codes),
        "account_scope_compatibility_status": COMPATIBILITY_COMPATIBLE,
        "currency_domain_compatibility_status": COMPATIBILITY_COMPATIBLE,
        "unit_compatibility_status": COMPATIBILITY_UNPROVEN,
        "freshness_evidence_status": FRESHNESS_WITNESS_TIMESTAMPS_NOT_TTL_POLICY,
        "freshness_evidence_ref": "SYNTHETIC_WITNESS_FRESHNESS_EVIDENCE",
        "provenance_status": PROVENANCE_PRESENT,
        "ambiguity_status": AMBIGUITY_NONE,
        "contradiction_status": CONTRADICTION_NONE,
        "semantic_mapping_proven_status": "UNPROVEN",
        "inclusion_proven_status": "UNPROVEN",
        "source_selected_status": SOURCE_SELECTION_STATUS_NOT_SELECTED,
    }
    fields.update(overrides)
    return attach_normalization_inclusion_provenance_digest_v1(fields)


def _y_section() -> str:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    y_start = runbook.index(Y_HEADING)
    return runbook[y_start : runbook.index(Z_HEADING, y_start)]


def test_valid_synthetic_adjudication_can_be_constructed() -> None:
    adjudication = build_normalization_inclusion_adjudication_v1(**_synthetic_fields())
    assert isinstance(adjudication, NormalizationInclusionAdjudicationV1)
    assert adjudication.source_witness_id == "SYNTHETIC_WITNESS_ID"
    assert adjudication.bound_account_identity == "SYNTHETIC_BOUND_ACCOUNT"
    assert adjudication.raw_field_path == "details.availEq"
    assert adjudication.requested_target_dimension_id == DIMENSION_ID
    assert adjudication.semantic_mapping_status != adjudication.requested_target_dimension_id
    assert adjudication.field_to_dimension_mapping_status == MAPPING_STATUS_UNBOUND
    assert NORMALIZATION_SCHEMA_PRESENT is True
    assert NORMALIZATION_RUNTIME_INSTANCE_PRESENT is False


def test_object_is_immutable() -> None:
    adjudication = build_normalization_inclusion_adjudication_v1(**_synthetic_fields())
    with pytest.raises(FrozenInstanceError):
        adjudication.inclusion_status = INCLUSION_STATUS_INCLUDED  # type: ignore[misc]


def test_digest_is_deterministic() -> None:
    first = build_normalization_inclusion_adjudication_v1(**_synthetic_fields())
    second = build_normalization_inclusion_adjudication_v1(**_synthetic_fields())
    assert first.provenance_digest == second.provenance_digest
    assert first.provenance_digest == first.to_canonical_dict()["provenance_digest"]


def test_witness_reference_required() -> None:
    fields = _synthetic_fields()
    fields["source_witness_id"] = ""
    with pytest.raises(NormalizationInclusionAdjudicationContractError) as raised:
        build_normalization_inclusion_adjudication_v1(**fields)
    assert "source_witness_id" in str(raised.value)


def test_account_identity_preserved() -> None:
    adjudication = build_normalization_inclusion_adjudication_v1(**_synthetic_fields())
    assert adjudication.bound_account_identity == "SYNTHETIC_BOUND_ACCOUNT"
    fields = _synthetic_fields()
    fields["bound_account_identity"] = ""
    with pytest.raises(NormalizationInclusionAdjudicationContractError) as raised:
        build_normalization_inclusion_adjudication_v1(**fields)
    assert "bound_account_identity" in str(raised.value)


def test_raw_field_path_preserved_exactly() -> None:
    adjudication = build_normalization_inclusion_adjudication_v1(
        **_synthetic_fields(raw_field_path="details.availEq")
    )
    assert adjudication.raw_field_path == "details.availEq"
    assert adjudication.observation_semantic_class == OBSERVATION_SEMANTIC_CLASS
    assert adjudication.requested_target_dimension_id == DIMENSION_ID
    assert adjudication.raw_field_path != adjudication.requested_target_dimension_id


def test_requested_target_dimension_is_not_proven_mapping() -> None:
    adjudication = build_normalization_inclusion_adjudication_v1(**_synthetic_fields())
    assert adjudication.requested_target_dimension_id == DIMENSION_ID
    assert adjudication.semantic_mapping_status == MAPPING_STATUS_UNBOUND
    assert adjudication.semantic_mapping_proven_status == "UNPROVEN"
    assert SEMANTIC_MAPPING_PROVEN is False
    assert FIELD_TO_DIMENSION_MAPPING_SCHEMA_PRESENT is True
    assert FIELD_TO_DIMENSION_MAPPING_PRESENT is False
    assert MAPPED_TO_RUNNING_ACCOUNT_EQUITY_AVAILABLE_FOR_SIZING is False


def test_observed_is_not_normalizable() -> None:
    missing = build_normalization_inclusion_adjudication_v1(
        **_synthetic_fields(presence=PRESENCE_MISSING)
    )
    assert missing.observation_participation_state == OBSERVATION_PARTICIPATION_STATE_OBSERVED
    assert missing.normalizable_status == NORMALIZABLE_STATUS_NOT_NORMALIZABLE
    assert missing.observation_participation_state != missing.normalizable_status
    fields = _synthetic_fields(presence=PRESENCE_MISSING)
    fields["normalizable_status"] = NORMALIZABLE_STATUS_NORMALIZABLE
    with pytest.raises(NormalizationInclusionAdjudicationContractError) as raised:
        build_normalization_inclusion_adjudication_v1(
            **attach_normalization_inclusion_provenance_digest_v1(fields)
        )
    assert "MISSING_EMPTY_MALFORMED_NOT_NORMALIZABLE" in str(raised.value)


def test_normalizable_is_not_semantically_mapped() -> None:
    adjudication = build_normalization_inclusion_adjudication_v1(
        **_synthetic_fields(presence=PRESENCE_ZERO)
    )
    assert adjudication.normalizable_status == NORMALIZABLE_STATUS_NORMALIZABLE
    assert adjudication.semantic_mapping_status == MAPPING_STATUS_UNBOUND
    assert adjudication.normalizable_status != adjudication.semantic_mapping_status
    fields = _synthetic_fields()
    fields["semantic_mapping_status"] = SEMANTIC_MAPPING_STATUS_MAPPED
    with pytest.raises(NormalizationInclusionAdjudicationContractError) as raised:
        build_normalization_inclusion_adjudication_v1(
            **attach_normalization_inclusion_provenance_digest_v1(fields)
        )
    assert "SEMANTICALLY_MAPPED_FORBIDDEN" in str(raised.value)


def test_semantically_mapped_is_not_included() -> None:
    adjudication = build_normalization_inclusion_adjudication_v1(**_synthetic_fields())
    assert adjudication.semantic_mapping_status != INCLUSION_STATUS_INCLUDED
    assert adjudication.inclusion_status != INCLUSION_STATUS_INCLUDED
    fields = _synthetic_fields()
    fields["inclusion_status"] = INCLUSION_STATUS_INCLUDED
    with pytest.raises(NormalizationInclusionAdjudicationContractError) as raised:
        build_normalization_inclusion_adjudication_v1(
            **attach_normalization_inclusion_provenance_digest_v1(fields)
        )
    assert "INCLUDED_FORBIDDEN" in str(raised.value)


def test_included_is_not_selected() -> None:
    adjudication = build_normalization_inclusion_adjudication_v1(**_synthetic_fields())
    assert adjudication.inclusion_status != SOURCE_SELECTION_STATUS_SELECTED
    assert adjudication.source_selection_status == SOURCE_SELECTION_STATUS_NOT_SELECTED
    fields = _synthetic_fields()
    fields["source_selection_status"] = SOURCE_SELECTION_STATUS_SELECTED
    with pytest.raises(NormalizationInclusionAdjudicationContractError) as raised:
        build_normalization_inclusion_adjudication_v1(
            **attach_normalization_inclusion_provenance_digest_v1(fields)
        )
    assert "SELECTED_FORBIDDEN" in str(raised.value)


def test_selected_is_not_authoritative() -> None:
    adjudication = build_normalization_inclusion_adjudication_v1(**_synthetic_fields())
    assert adjudication.source_selection_status != "AUTHORITY"
    assert adjudication.observation_vs_authority_class == "OBSERVATION"
    assert adjudication.normalization_authority_effect == "NONE"
    fields = _synthetic_fields()
    fields["observation_vs_authority_class"] = OBSERVATION_VS_AUTHORITY_CLASS_AUTHORITY
    with pytest.raises(NormalizationInclusionAdjudicationContractError) as raised:
        build_normalization_inclusion_adjudication_v1(
            **attach_normalization_inclusion_provenance_digest_v1(fields)
        )
    assert "AUTHORITY_CLASS_FORBIDDEN" in str(raised.value)


def test_missing_is_excluded_and_not_present_zero() -> None:
    missing = build_normalization_inclusion_adjudication_v1(
        **_synthetic_fields(presence=PRESENCE_MISSING)
    )
    zero = build_normalization_inclusion_adjudication_v1(
        **_synthetic_fields(presence=PRESENCE_ZERO)
    )
    assert missing.presence_state == PRESENCE_MISSING
    assert zero.presence_state == PRESENCE_ZERO
    assert missing.inclusion_status == INCLUSION_STATUS_EXCLUDED
    assert EXCLUSION_MISSING_VALUE in missing.exclusion_reason_codes
    assert EXCLUSION_MISSING_VALUE not in zero.exclusion_reason_codes
    assert missing.presence_state != zero.presence_state


def test_empty_is_excluded_and_not_present_zero() -> None:
    empty = build_normalization_inclusion_adjudication_v1(
        **_synthetic_fields(presence=PRESENCE_EMPTY)
    )
    zero = build_normalization_inclusion_adjudication_v1(
        **_synthetic_fields(presence=PRESENCE_ZERO)
    )
    assert empty.presence_state == PRESENCE_EMPTY
    assert EXCLUSION_EMPTY_VALUE in empty.exclusion_reason_codes
    assert EXCLUSION_EMPTY_VALUE not in zero.exclusion_reason_codes
    assert empty.presence_state != zero.presence_state


def test_malformed_is_excluded_and_not_present_zero() -> None:
    malformed = build_normalization_inclusion_adjudication_v1(
        **_synthetic_fields(presence=PRESENCE_MALFORMED)
    )
    zero = build_normalization_inclusion_adjudication_v1(
        **_synthetic_fields(presence=PRESENCE_ZERO)
    )
    assert malformed.presence_state == PRESENCE_MALFORMED
    assert EXCLUSION_MALFORMED_VALUE in malformed.exclusion_reason_codes
    assert EXCLUSION_MALFORMED_VALUE not in zero.exclusion_reason_codes
    assert malformed.presence_state != zero.presence_state


def test_present_zero_is_not_auto_excluded_because_zero() -> None:
    zero = build_normalization_inclusion_adjudication_v1(
        **_synthetic_fields(presence=PRESENCE_ZERO)
    )
    assert zero.presence_state == PRESENCE_ZERO
    assert zero.raw_value_representation == "0"
    assert zero.normalizable_status == NORMALIZABLE_STATUS_NORMALIZABLE
    assert EXCLUSION_MISSING_VALUE not in zero.exclusion_reason_codes
    assert EXCLUSION_EMPTY_VALUE not in zero.exclusion_reason_codes
    assert EXCLUSION_MALFORMED_VALUE not in zero.exclusion_reason_codes
    fields = _synthetic_fields(presence=PRESENCE_ZERO)
    codes = _default_exclusion_codes(presence=PRESENCE_ZERO) + (EXCLUSION_MISSING_VALUE,)
    fields["exclusion_reason_codes"] = encode_exclusion_reason_codes_v1(tuple(sorted(set(codes))))
    with pytest.raises(NormalizationInclusionAdjudicationContractError) as raised:
        build_normalization_inclusion_adjudication_v1(
            **attach_normalization_inclusion_provenance_digest_v1(fields)
        )
    assert "PRESENT_VALUE_MUST_NOT_COLLAPSE_TO_MISSING_EMPTY_MALFORMED" in str(raised.value)


def test_present_nonzero_does_not_imply_inclusion() -> None:
    nonzero = build_normalization_inclusion_adjudication_v1(
        **_synthetic_fields(presence=PRESENCE_NONZERO)
    )
    assert nonzero.presence_state == PRESENCE_NONZERO
    assert nonzero.normalizable_status == NORMALIZABLE_STATUS_NORMALIZABLE
    assert nonzero.inclusion_status == INCLUSION_STATUS_EXCLUDED
    assert nonzero.inclusion_proven_status == "UNPROVEN"
    assert INCLUSION_PROVEN is False


def test_incompatible_currency_domain_fails_closed() -> None:
    fields = _synthetic_fields(
        currency_domain="USD",
        currency_domain_compatibility_status=COMPATIBILITY_INCOMPATIBLE,
    )
    adjudication = build_normalization_inclusion_adjudication_v1(**fields)
    assert adjudication.currency_domain == "USD"
    assert adjudication.currency_domain != "USDC"
    assert EXCLUSION_INCOMPATIBLE_CURRENCY_DOMAIN in adjudication.exclusion_reason_codes
    assert adjudication.inclusion_status == INCLUSION_STATUS_EXCLUDED
    compatible = _synthetic_fields(currency_domain="USD")
    fields_bad = dict(compatible)
    fields_bad["currency_domain_compatibility_status"] = COMPATIBILITY_COMPATIBLE
    with pytest.raises(NormalizationInclusionAdjudicationContractError) as raised:
        build_normalization_inclusion_adjudication_v1(
            **attach_normalization_inclusion_provenance_digest_v1(fields_bad)
        )
    assert "NON_USDC_CANNOT_BE_CURRENCY_COMPATIBLE" in str(raised.value)


def test_incompatible_account_scope_fails_closed() -> None:
    adjudication = build_normalization_inclusion_adjudication_v1(
        **_synthetic_fields(account_scope_compatibility_status=COMPATIBILITY_INCOMPATIBLE)
    )
    assert adjudication.account_scope_compatibility_status == COMPATIBILITY_INCOMPATIBLE
    assert EXCLUSION_INCOMPATIBLE_ACCOUNT_SCOPE in adjudication.exclusion_reason_codes
    assert adjudication.inclusion_status == INCLUSION_STATUS_EXCLUDED


def test_unresolved_ambiguity_fails_closed() -> None:
    adjudication = build_normalization_inclusion_adjudication_v1(
        **_synthetic_fields(ambiguity_status=AMBIGUITY_UNRESOLVED)
    )
    assert EXCLUSION_UNRESOLVED_AMBIGUITY in adjudication.exclusion_reason_codes
    assert adjudication.inclusion_status == INCLUSION_STATUS_EXCLUDED


def test_contradiction_fails_closed() -> None:
    adjudication = build_normalization_inclusion_adjudication_v1(
        **_synthetic_fields(contradiction_status=CONTRADICTION_PRESENT)
    )
    assert EXCLUSION_CONTRADICTION in adjudication.exclusion_reason_codes
    assert adjudication.inclusion_status == INCLUSION_STATUS_EXCLUDED


def test_missing_provenance_fails_closed() -> None:
    adjudication = build_normalization_inclusion_adjudication_v1(
        **_synthetic_fields(provenance_status=PROVENANCE_ABSENT)
    )
    assert EXCLUSION_ABSENT_PROVENANCE in adjudication.exclusion_reason_codes
    assert adjudication.inclusion_status == INCLUSION_STATUS_EXCLUDED


def test_unproven_freshness_fails_closed() -> None:
    adjudication = build_normalization_inclusion_adjudication_v1(**_synthetic_fields())
    assert adjudication.freshness_evidence_status == FRESHNESS_WITNESS_TIMESTAMPS_NOT_TTL_POLICY
    assert EXCLUSION_STALE_OR_UNPROVEN_FRESHNESS in adjudication.exclusion_reason_codes
    stale = build_normalization_inclusion_adjudication_v1(
        **_synthetic_fields(freshness_evidence_status=FRESHNESS_STALE)
    )
    assert EXCLUSION_STALE_OR_UNPROVEN_FRESHNESS in stale.exclusion_reason_codes
    fields = _synthetic_fields()
    fields["inclusion_status"] = INCLUSION_STATUS_UNPROVEN
    with pytest.raises(NormalizationInclusionAdjudicationContractError) as raised:
        build_normalization_inclusion_adjudication_v1(
            **attach_normalization_inclusion_provenance_digest_v1(fields)
        )
    assert "EXCLUSION_REASONS_REQUIRE_EXCLUDED" in str(raised.value)


def test_forbidden_optimistic_fallback_chain_does_not_exist() -> None:
    fields = _synthetic_fields()
    fields["raw_field_path"] = _FORBIDDEN_FALLBACK
    with pytest.raises(NormalizationInclusionAdjudicationContractError) as raised:
        build_normalization_inclusion_adjudication_v1(
            **attach_normalization_inclusion_provenance_digest_v1(fields)
        )
    assert "FALLBACK_CHAIN_FORBIDDEN" in str(raised.value)
    inspect_source = SCHEMA_PATH.read_text(encoding="utf-8")
    assert "totalEq or eq or adjEq" not in inspect_source
    assert 'row.get("totalEq") or row.get("eq")' not in inspect_source
    assert "availEq or eq" not in inspect_source


def test_schema_creation_does_not_select_source_or_mapping_or_producer() -> None:
    build_normalization_inclusion_adjudication_v1(**_synthetic_fields())
    assert SOURCE_SELECTED is False
    assert MAPPING_PROVEN is False
    assert SOURCE_OBJECT_PRESENT is False
    assert GOVERNED_PRODUCER_CREATED is False
    assert GOVERNED_PRODUCTIVE_SOURCE_PRESENT is False
    assert RUNTIME_VALUE_BINDING_PRESENT is False
    assert LIVE_ACCOUNT_BOUND_JOIN_PRESENT is False
    assert RAW_TO_WITNESS_PROVEN is False
    assert SEMANTIC_MAPPING_PROVEN is False
    assert INCLUSION_PROVEN is False
    assert INTERNAL_RECONSTRUCTION_CREATED is False
    assert RECONCILIATION_CONTRACT_CREATED is False
    assert DIVERGENCE_POLICY_CREATED is False
    dag = live_admission_gap_dag_v1()
    assert dag["SOURCE_SELECTED"] is False
    assert dag["MAPPING_PROVEN"] is False
    assert dag["VENUE_WITNESS_SCHEMA_PRESENT"] is True
    assert dag["VENUE_WITNESS_RUNTIME_INSTANCE_PRESENT"] is False
    assert dag["VENUE_WITNESS_SELECTED"] is False
    assert dag["NORMALIZATION_SCHEMA_PRESENT"] is True
    assert dag["NORMALIZATION_RUNTIME_INSTANCE_PRESENT"] is False
    assert dag["NORMALIZATION_CONTRACT_MISSING_CLOSED"] is True
    assert dag["FIELD_TO_DIMENSION_MAPPING_SCHEMA_PRESENT"] is True
    assert dag["FIELD_TO_DIMENSION_MAPPING_PRESENT"] is False
    assert dag["SEMANTIC_MAPPING_PROVEN"] is False
    assert dag["INCLUSION_PROVEN"] is False
    assert dag["INTERNAL_RECONSTRUCTION_CREATED"] is False
    assert dag["EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY"] == (
        "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING"
    )
    assert EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY == (
        "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING"
    )
    assert dag["EARLIEST_DECOMPOSED_CONTRACT_GAP"] == (
        "U04_PENDING_ORDER_RESERVATION_INCLUSION_UNRESOLVED"
    )
    assert EARLIEST_DECOMPOSED_CONTRACT_GAP == "U04_PENDING_ORDER_RESERVATION_INCLUSION_UNRESOLVED"


def test_step_29p_remains_inadmissible_and_live_gates_remain_false() -> None:
    capital = _capital()
    result = evaluate_step_29p_capital_risk_admissibility_v1(
        capital=capital,
        claim=_complete_claim(typed_account_equity_source_field="availEq"),
    )
    assert result.risk_admissible is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert WIRE_SEND_PERMITTED is False
    assert EQUITY_DIMENSION_BOUND is False
    with pytest.raises(ExecutionPortConstructionForbiddenError) as raised:
        construct_live_execution_port_v1()
    assert "LIVE_EXECUTION_PORT_CONSTRUCTION_FORBIDDEN_IN_CAPABILITY_11_1" in str(raised.value)
    port = bind_simulated_execution_port_v1()
    assert isinstance(port, SimulatedExecutionPortV1)


def test_runbook_y_consumes_go_without_rewriting_x() -> None:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    spec = SPEC_PATH.read_text(encoding="utf-8")
    x_start = runbook.index(X_HEADING)
    y_section = _y_section()
    x_section = runbook[x_start : runbook.index(Y_HEADING, x_start)]
    assert "VENUE_WITNESS_SCHEMA_PRESENT=true" in x_section
    assert "THIS_SLICE=11.2.1.Y" not in x_section
    assert "EARLIEST_DECOMPOSED_CONTRACT_GAP=NORMALIZATION_CONTRACT_MISSING" in x_section
    assert (
        "OWNER_GO=OWNER_GO_PEAK_TRADE_FULL_CORE_TYPED_NORMALIZATION_INCLUSION_CONTRACT_V1"
        in y_section
    )
    assert "OWNER_GO_STATUS=CONSUMED" in y_section
    assert "NORMALIZATION_SCHEMA_PRESENT=true" in y_section
    assert "NORMALIZATION_RUNTIME_INSTANCE_PRESENT=false" in y_section
    assert "NORMALIZATION_CONTRACT_MISSING_CLOSED=true" in y_section
    assert "NORMALIZATION_AUTHORITY_EFFECT=NONE" in y_section
    assert "FIELD_TO_DIMENSION_MAPPING_SCHEMA_PRESENT=true" in y_section
    assert "FIELD_TO_DIMENSION_MAPPING_PRESENT=false" in y_section
    assert "SEMANTIC_MAPPING_PROVEN=false" in y_section
    assert "INCLUSION_PROVEN=false" in y_section
    assert "SOURCE_OBJECT_PRESENT=false" in y_section
    assert "SOURCE_SELECTED=false" in y_section
    assert "MAPPING_PROVEN=false" in y_section
    assert "GOVERNED_PRODUCER_CREATED=false" in y_section
    assert "RUNTIME_VALUE_BINDING_PRESENT=false" in y_section
    assert "LIVE_ACCOUNT_BOUND_JOIN_PRESENT=false" in y_section
    assert "STEP_29P_RISK_ADMISSIBLE=false" in y_section
    assert "LIVE_ENABLED=false" in y_section
    assert "LIVE_ARMED=false" in y_section
    assert "WIRE_SEND_PERMITTED=false" in y_section
    assert "INTERNAL_RECONSTRUCTION_CREATED=false" in y_section
    assert "RECONCILIATION_CONTRACT_CREATED=false" in y_section
    assert "DIVERGENCE_POLICY_CREATED=false" in y_section
    assert (
        "EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY="
        "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING" in y_section
    )
    assert "EARLIEST_DECOMPOSED_CONTRACT_GAP=INTERNAL_RECONSTRUCTION_CONTRACT_MISSING" in y_section
    assert "DOCS_TOKEN_FULL_CORE_TYPED_NORMALIZATION_INCLUSION_CONTRACT_V1" in spec
    assert "NORMALIZATION_SCHEMA_PRESENT=true" in spec
    assert "SOURCE_SELECTED=false" in spec
    assert "MAPPING_PROVEN=false" in spec
    assert "GOVERNED_PRODUCER_CREATED=false" in spec
    assert NORMALIZATION_AUTHORITY_EFFECT == "NONE"
    assert NORMALIZATION_CONTRACT_MISSING_CLOSED is True
    assert VENUE_WITNESS_SCHEMA_PRESENT is True
    assert VENUE_WITNESS_RUNTIME_INSTANCE_PRESENT is False
    assert VENUE_WITNESS_SELECTED is False
