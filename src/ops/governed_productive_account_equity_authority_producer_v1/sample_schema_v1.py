"""Typed GOVERNED_RUNNING_ACCOUNT_EQUITY_SAMPLE_V1 schema.

Schema definition only. Not a producer. Not a source mapping.
Not a runtime value binding. Not a LIVE_ACCOUNT_BOUND join.
Construction of a schema instance is not source selection.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping, Tuple

from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    GOVERNED_PRODUCER_CREATED,
    GOVERNED_RUNNING_ACCOUNT_EQUITY_SAMPLE_SCHEMA_PRESENT,
    NUMERIC_EQUITY_TTL_SECONDS,
    OWNER,
    SAMPLE_PROVENANCE_REQUIRED_FIELDS,
    SOURCE_OBJECT_PRESENT,
)

SCHEMA_CLASS = "GOVERNED_RUNNING_ACCOUNT_EQUITY_SAMPLE_V1"
DIMENSION_ID = "RUNNING_ACCOUNT_EQUITY_AVAILABLE_FOR_SIZING"
REQUIRED_SETTLEMENT_CURRENCY = "USDC"
OBSERVATION_VS_AUTHORITY_CLASS_OBSERVATION = "OBSERVATION"
OBSERVATION_VS_AUTHORITY_CLASS_AUTHORITY = "AUTHORITY"
CANONICAL_OBSERVED_AT_AS_OF = "observed_at/as_of"
PYTHON_OBSERVED_AT_AS_OF = "observed_at_as_of"

CANONICAL_TO_PYTHON_FIELD: Mapping[str, str] = {
    CANONICAL_OBSERVED_AT_AS_OF: PYTHON_OBSERVED_AT_AS_OF,
}

_FORBIDDEN_VENUE_FIELD_MARKERS: Tuple[str, ...] = (
    "details.availeq",
    "availeq",
    "totaleq",
    "adjeq",
    "availbal",
    "cashbal",
    "frozenbal",
    "isoeq",
    "ordfrozen",
    "mgnratio",
)
_BARE_FORBIDDEN_TOKENS: Tuple[str, ...] = ("eq", "upl")
_FORBIDDEN_OBJECT_TOKENS: Tuple[str, ...] = (
    "balance.total",
    "ledgersnapshot.equitybyccy",
    "accountingportfoliostatev1.equity",
    "fundingaccountbalanceobservationv1",
    "freshavailablemarginobservationv1",
    "simulatedportfoliostatev1.equity",
    "startbalance",
    "defaultaccountequity",
    "injectedrunningaccountequity",
    "typedaccountequityraw",
    "c01qgetpackdetailsavaileq",
    "c02forbiddenrawvenueeqfields",
    "c03capitaladmissionenvelope",
    "c04crsaccountequityconsumer",
    "c05offlinereplaydefault10000",
    "c06injectedrunningaccountequity",
    "c07fundingaccountbalanceobservation",
    "c08treasuryobservedorreconciledcapital",
    "c09cap113fixtureprivateaccountstate",
    "c10ledgersnapshotequitybyccy",
    "c11cap31productivefuturesaccounting",
    "c12s1114liveaccountingreconstructed",
    "c13backteststatefileaccountequity",
    "c14startbalance",
    "c15liveaccountboundidentity",
    "c16restartreconstructionaccounting",
    "c17freshavailablemarginobservation",
    "c18simulatedportfoliostate",
    "c19exchangebasebalance",
    "c20reconbalancesnapshot",
    "c21dryrunorderplaneqfallback",
)
_IDENTITY_SEMANTICS_FIELDS: Tuple[str, ...] = (
    "producer_identity",
    "authority_contract_ref",
    "value_semantics",
    "observation_vs_authority_class",
    "component_provenance",
    "inclusion_vector",
    "component_term_vector",
    "component_completeness",
    "double_count_guards",
    "currency_conversion_status",
    "witness_reconciliation_status",
    "restart_reconciliation_status",
    "freshness_policy_status",
)


class GovernedRunningAccountEquitySampleSchemaError(ValueError):
    """Fail-closed governed running-account-equity sample schema violation."""


def _fold(value: str) -> str:
    return str(value or "").strip().lower().replace("_", "").replace("-", "")


def _python_field_name(canonical: str) -> str:
    return CANONICAL_TO_PYTHON_FIELD.get(canonical, canonical)


def _token_is_forbidden_venue_field(name: str) -> bool:
    folded = _fold(name)
    if not folded:
        return False
    if folded in _BARE_FORBIDDEN_TOKENS:
        return True
    return any(marker in folded for marker in _FORBIDDEN_VENUE_FIELD_MARKERS)


def _token_is_forbidden_object(name: str) -> bool:
    folded = _fold(name)
    if not folded:
        return False
    return any(token in folded for token in _FORBIDDEN_OBJECT_TOKENS)


def _require_non_empty_str(*, field: str, raw: Any) -> str:
    if raw is None:
        raise GovernedRunningAccountEquitySampleSchemaError(
            f"GOVERNED_RUNNING_ACCOUNT_EQUITY_SAMPLE_FIELD_MISSING:{field}"
        )
    if not isinstance(raw, str):
        raise GovernedRunningAccountEquitySampleSchemaError(
            f"GOVERNED_RUNNING_ACCOUNT_EQUITY_SAMPLE_FIELD_NOT_STRING:{field}"
        )
    text = raw.strip()
    if text == "" or text != raw:
        raise GovernedRunningAccountEquitySampleSchemaError(
            f"GOVERNED_RUNNING_ACCOUNT_EQUITY_SAMPLE_FIELD_MISSING:{field}"
        )
    return text


def _require_finite_decimal(*, field: str, raw: Any) -> Decimal:
    if raw is None:
        raise GovernedRunningAccountEquitySampleSchemaError(
            f"GOVERNED_RUNNING_ACCOUNT_EQUITY_SAMPLE_FIELD_MISSING:{field}"
        )
    if isinstance(raw, bool):
        raise GovernedRunningAccountEquitySampleSchemaError(
            f"GOVERNED_RUNNING_ACCOUNT_EQUITY_SAMPLE_VALUE_NOT_DECIMAL:{field}"
        )
    if isinstance(raw, Decimal):
        value = raw
    else:
        text = str(raw).strip()
        if text == "" or text != str(raw).strip():
            raise GovernedRunningAccountEquitySampleSchemaError(
                f"GOVERNED_RUNNING_ACCOUNT_EQUITY_SAMPLE_FIELD_MISSING:{field}"
            )
        try:
            value = Decimal(text)
        except (InvalidOperation, ValueError) as exc:
            raise GovernedRunningAccountEquitySampleSchemaError(
                f"GOVERNED_RUNNING_ACCOUNT_EQUITY_SAMPLE_VALUE_NOT_DECIMAL:{field}"
            ) from exc
    if not value.is_finite():
        raise GovernedRunningAccountEquitySampleSchemaError(
            f"GOVERNED_RUNNING_ACCOUNT_EQUITY_SAMPLE_VALUE_NOT_FINITE:{field}"
        )
    return value


def _reject_forbidden_authority_token(*, field: str, raw: str) -> None:
    if _token_is_forbidden_venue_field(raw) or _token_is_forbidden_object(raw):
        raise GovernedRunningAccountEquitySampleSchemaError(
            f"GOVERNED_RUNNING_ACCOUNT_EQUITY_SAMPLE_FORBIDDEN_AUTHORITY_FIELD:{field}"
        )


@dataclass(frozen=True)
class GovernedRunningAccountEquitySampleV1:
    """Typed immutable governed sample schema. Not a producer mint."""

    dimension_id: str
    bound_account_identity: str
    bound_venue_identity: str
    bound_td_mode: str
    settlement_currency: str
    value: Decimal
    value_semantics: str
    producer_identity: str
    authority_contract_ref: str
    source_revision_or_digest: str
    input_set_digest: str
    decision_epoch: str
    observed_at_as_of: str
    freshness_max_age: str
    freshness_policy_status: str
    restart_reconciliation_status: str
    component_completeness: str
    component_provenance: str
    inclusion_vector: str
    component_term_vector: str
    double_count_guards: str
    currency_conversion_status: str
    witness_reconciliation_status: str
    policy_version: str
    semantic_digest: str
    sample_id: str
    observation_vs_authority_class: str

    def __post_init__(self) -> None:
        _validate_governed_running_account_equity_sample_v1(self)

    def to_canonical_dict(self) -> dict[str, str]:
        values = {
            "dimension_id": self.dimension_id,
            "bound_account_identity": self.bound_account_identity,
            "bound_venue_identity": self.bound_venue_identity,
            "bound_td_mode": self.bound_td_mode,
            "settlement_currency": self.settlement_currency,
            "value": str(self.value),
            "value_semantics": self.value_semantics,
            "producer_identity": self.producer_identity,
            "authority_contract_ref": self.authority_contract_ref,
            "source_revision_or_digest": self.source_revision_or_digest,
            "input_set_digest": self.input_set_digest,
            "decision_epoch": self.decision_epoch,
            CANONICAL_OBSERVED_AT_AS_OF: self.observed_at_as_of,
            "freshness_max_age": self.freshness_max_age,
            "freshness_policy_status": self.freshness_policy_status,
            "restart_reconciliation_status": self.restart_reconciliation_status,
            "component_completeness": self.component_completeness,
            "component_provenance": self.component_provenance,
            "inclusion_vector": self.inclusion_vector,
            "component_term_vector": self.component_term_vector,
            "double_count_guards": self.double_count_guards,
            "currency_conversion_status": self.currency_conversion_status,
            "witness_reconciliation_status": self.witness_reconciliation_status,
            "policy_version": self.policy_version,
            "semantic_digest": self.semantic_digest,
            "sample_id": self.sample_id,
            "observation_vs_authority_class": self.observation_vs_authority_class,
        }
        return {key: values[key] for key in SAMPLE_PROVENANCE_REQUIRED_FIELDS}


def _validate_governed_running_account_equity_sample_v1(
    sample: GovernedRunningAccountEquitySampleV1,
) -> None:
    if GOVERNED_RUNNING_ACCOUNT_EQUITY_SAMPLE_SCHEMA_PRESENT is not True:
        raise GovernedRunningAccountEquitySampleSchemaError(
            "GOVERNED_RUNNING_ACCOUNT_EQUITY_SAMPLE_SCHEMA_PRESENT_REQUIRED"
        )
    if SOURCE_OBJECT_PRESENT is True:
        raise GovernedRunningAccountEquitySampleSchemaError(
            "GOVERNED_RUNNING_ACCOUNT_EQUITY_SAMPLE_RUNTIME_SOURCE_OBJECT_FORBIDDEN"
        )
    if GOVERNED_PRODUCER_CREATED is True:
        raise GovernedRunningAccountEquitySampleSchemaError(
            "GOVERNED_RUNNING_ACCOUNT_EQUITY_SAMPLE_PRODUCER_MUST_REMAIN_ABSENT"
        )

    missing = [
        canonical
        for canonical in SAMPLE_PROVENANCE_REQUIRED_FIELDS
        if getattr(sample, _python_field_name(canonical), None) in (None, "")
    ]
    if missing:
        raise GovernedRunningAccountEquitySampleSchemaError(
            "GOVERNED_RUNNING_ACCOUNT_EQUITY_SAMPLE_FIELD_MISSING:" + ",".join(missing)
        )

    dimension = _require_non_empty_str(field="dimension_id", raw=sample.dimension_id)
    if dimension != DIMENSION_ID:
        raise GovernedRunningAccountEquitySampleSchemaError(
            f"GOVERNED_RUNNING_ACCOUNT_EQUITY_SAMPLE_DIMENSION_MISMATCH:{dimension}"
        )
    _require_non_empty_str(field="bound_account_identity", raw=sample.bound_account_identity)
    _require_non_empty_str(field="bound_venue_identity", raw=sample.bound_venue_identity)
    _require_non_empty_str(field="bound_td_mode", raw=sample.bound_td_mode)
    currency = _require_non_empty_str(field="settlement_currency", raw=sample.settlement_currency)
    if currency != REQUIRED_SETTLEMENT_CURRENCY:
        raise GovernedRunningAccountEquitySampleSchemaError(
            f"GOVERNED_RUNNING_ACCOUNT_EQUITY_SAMPLE_CURRENCY_NOT_USDC:{currency}"
        )
    _require_finite_decimal(field="value", raw=sample.value)
    _require_non_empty_str(field="value_semantics", raw=sample.value_semantics)
    producer = _require_non_empty_str(field="producer_identity", raw=sample.producer_identity)
    _reject_forbidden_authority_token(field="producer_identity", raw=producer)
    if producer != OWNER:
        raise GovernedRunningAccountEquitySampleSchemaError(
            f"GOVERNED_RUNNING_ACCOUNT_EQUITY_SAMPLE_PRODUCER_IDENTITY_MISMATCH:{producer}"
        )
    _require_non_empty_str(field="authority_contract_ref", raw=sample.authority_contract_ref)
    _require_non_empty_str(field="source_revision_or_digest", raw=sample.source_revision_or_digest)
    _require_non_empty_str(field="input_set_digest", raw=sample.input_set_digest)
    _require_non_empty_str(field="decision_epoch", raw=sample.decision_epoch)
    _require_non_empty_str(field=CANONICAL_OBSERVED_AT_AS_OF, raw=sample.observed_at_as_of)
    age_raw = _require_non_empty_str(field="freshness_max_age", raw=sample.freshness_max_age)
    try:
        age = int(age_raw)
    except ValueError as exc:
        raise GovernedRunningAccountEquitySampleSchemaError(
            "GOVERNED_RUNNING_ACCOUNT_EQUITY_SAMPLE_FRESHNESS_MAX_AGE_NOT_INTEGER"
        ) from exc
    if str(age) != age_raw:
        raise GovernedRunningAccountEquitySampleSchemaError(
            "GOVERNED_RUNNING_ACCOUNT_EQUITY_SAMPLE_FRESHNESS_MAX_AGE_NOT_INTEGER"
        )
    if age < 0 or age > NUMERIC_EQUITY_TTL_SECONDS:
        raise GovernedRunningAccountEquitySampleSchemaError(
            "GOVERNED_RUNNING_ACCOUNT_EQUITY_SAMPLE_FRESHNESS_MAX_AGE_OUT_OF_POLICY"
        )
    _require_non_empty_str(field="freshness_policy_status", raw=sample.freshness_policy_status)
    _require_non_empty_str(
        field="restart_reconciliation_status", raw=sample.restart_reconciliation_status
    )
    _require_non_empty_str(field="component_completeness", raw=sample.component_completeness)
    _require_non_empty_str(field="component_provenance", raw=sample.component_provenance)
    _require_non_empty_str(field="inclusion_vector", raw=sample.inclusion_vector)
    _require_non_empty_str(field="component_term_vector", raw=sample.component_term_vector)
    _require_non_empty_str(field="double_count_guards", raw=sample.double_count_guards)
    _require_non_empty_str(
        field="currency_conversion_status", raw=sample.currency_conversion_status
    )
    _require_non_empty_str(
        field="witness_reconciliation_status", raw=sample.witness_reconciliation_status
    )
    _require_non_empty_str(field="policy_version", raw=sample.policy_version)
    _require_non_empty_str(field="semantic_digest", raw=sample.semantic_digest)
    _require_non_empty_str(field="sample_id", raw=sample.sample_id)
    authority_class = _require_non_empty_str(
        field="observation_vs_authority_class",
        raw=sample.observation_vs_authority_class,
    )
    if authority_class == OBSERVATION_VS_AUTHORITY_CLASS_AUTHORITY:
        raise GovernedRunningAccountEquitySampleSchemaError(
            "GOVERNED_RUNNING_ACCOUNT_EQUITY_SAMPLE_AUTHORITY_CLASS_FORBIDDEN_UNTIL_PRODUCER_MINT"
        )
    if authority_class != OBSERVATION_VS_AUTHORITY_CLASS_OBSERVATION:
        raise GovernedRunningAccountEquitySampleSchemaError(
            "GOVERNED_RUNNING_ACCOUNT_EQUITY_SAMPLE_OBSERVATION_VS_AUTHORITY_CLASS_UNKNOWN"
        )

    for field in _IDENTITY_SEMANTICS_FIELDS:
        _reject_forbidden_authority_token(field=field, raw=str(getattr(sample, field)))


def build_governed_running_account_equity_sample_v1(
    **fields: Any,
) -> GovernedRunningAccountEquitySampleV1:
    """Fail-closed schema constructor. Explicit fields only. Not a mint."""

    normalized: dict[str, Any] = {}
    for canonical in SAMPLE_PROVENANCE_REQUIRED_FIELDS:
        python_name = _python_field_name(canonical)
        if canonical in fields:
            raw = fields[canonical]
        elif python_name in fields:
            raw = fields[python_name]
        else:
            raise GovernedRunningAccountEquitySampleSchemaError(
                f"GOVERNED_RUNNING_ACCOUNT_EQUITY_SAMPLE_FIELD_MISSING:{canonical}"
            )
        if canonical == "value":
            normalized[python_name] = _require_finite_decimal(field="value", raw=raw)
        else:
            normalized[python_name] = raw
    unexpected = (
        set(fields)
        - set(SAMPLE_PROVENANCE_REQUIRED_FIELDS)
        - set(CANONICAL_TO_PYTHON_FIELD.values())
    )
    if unexpected:
        raise GovernedRunningAccountEquitySampleSchemaError(
            "GOVERNED_RUNNING_ACCOUNT_EQUITY_SAMPLE_UNEXPECTED_FIELD:"
            + ",".join(sorted(unexpected))
        )
    return GovernedRunningAccountEquitySampleV1(**normalized)
