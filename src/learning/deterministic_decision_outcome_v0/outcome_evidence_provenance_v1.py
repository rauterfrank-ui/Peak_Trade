"""Canonical outcome/evidence provenance v1 — orthogonal dimensions, no universal realm enum.

Preserves distributed CURRENT semantics (environment, execution mode, outcome class).
Does not confer trading, promotion, or optimization authority.
"""

from __future__ import annotations

import hashlib
import json
from enum import Enum
from types import MappingProxyType
from typing import Any, Final, Mapping

from src.learning.deterministic_decision_outcome_v0.common_v0 import (
    optional_string_or_unknown,
    reject_unknown_fields,
    require_enum,
    require_event_time_utc,
    require_mapping,
    require_non_empty_string_or_unknown,
    require_record_id,
    require_sha256_or_unknown,
)
from src.learning.deterministic_decision_outcome_v0.enums_v0 import UNKNOWN
from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoValidationError

SCHEMA_NAME: Final[str] = "outcome_evidence_provenance"
SCHEMA_VERSION: Final[str] = "outcome_evidence_provenance_v1"
PROVENANCE_CONTRACT_VERSION: Final[str] = "1"

PRODUCTIVE_TRUTH_LABELS: Final[frozenset[str]] = frozenset(
    {
        "OBSERVED_PRODUCTIVE_PRE_EXTERNAL",
        "REALIZED_PRODUCTIVE",
    }
)


class DdoLedgerEnvironmentV1(str, Enum):
    DEV = "dev"
    SHADOW = "shadow"
    TESTNET = "testnet"
    PROD = "prod"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    UNKNOWN = "UNKNOWN"
    AMBIGUOUS = "AMBIGUOUS"


class MarketObservationSourceV1(str, Enum):
    INJECTED_C1 = "INJECTED_C1"
    PUBLIC_MD = "PUBLIC_MD"
    TESTNET_BOUNDED = "TESTNET_BOUNDED"
    CALLER_SUPPLIED = "CALLER_SUPPLIED"
    REPLAY_HISTORICAL = "REPLAY_HISTORICAL"
    SYNTHETIC_OFFLINE = "SYNTHETIC_OFFLINE"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    UNKNOWN = "UNKNOWN"
    AMBIGUOUS = "AMBIGUOUS"


class DecisionSourceV1(str, Enum):
    PRODUCTIVE_MV2_DP_PRE_EXTERNAL = "PRODUCTIVE_MV2_DP_PRE_EXTERNAL"
    INTERNAL_SIM_BRIDGE = "INTERNAL_SIM_BRIDGE"
    I67_PAPER_SIM = "I67_PAPER_SIM"
    I17_SHADOW_OBS = "I17_SHADOW_OBS"
    REPLAY_SEMANTIC = "REPLAY_SEMANTIC"
    REPLAY_PACK_I79 = "REPLAY_PACK_I79"
    TESTNET_COMPLETION = "TESTNET_COMPLETION"
    CANARY_EVIDENCE = "CANARY_EVIDENCE"
    DDO_OBSERVATION = "DDO_OBSERVATION"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    UNKNOWN = "UNKNOWN"
    AMBIGUOUS = "AMBIGUOUS"


class ExecutionModeLabelV1(str, Enum):
    SIMULATED = "SIMULATED"
    TESTNET = "TESTNET"
    LIVE = "LIVE"
    INTERNAL_SIMULATED_EXECUTION = "INTERNAL_SIMULATED_EXECUTION"
    NO_EXECUTION = "NO_EXECUTION"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    UNKNOWN = "UNKNOWN"
    AMBIGUOUS = "AMBIGUOUS"


class FillSourceTypeV1(str, Enum):
    NO_FILL = "NO_FILL"
    SIMULATED = "SIMULATED"
    VENUE_TESTNET = "VENUE_TESTNET"
    VENUE_LIVE = "VENUE_LIVE"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    UNKNOWN = "UNKNOWN"
    AMBIGUOUS = "AMBIGUOUS"


class OutcomeSemanticClassV1(str, Enum):
    OBSERVED_PRODUCTIVE_PRE_EXTERNAL = "OBSERVED_PRODUCTIVE_PRE_EXTERNAL"
    INTERNAL_SIMULATED_OUTCOME = "INTERNAL_SIMULATED_OUTCOME"
    I67_PAPER_SIM_OUTCOME = "I67_PAPER_SIM_OUTCOME"
    SHADOW_COUNTERFACTUAL = "SHADOW_COUNTERFACTUAL"
    TESTNET_VENUE_EVIDENCE = "TESTNET_VENUE_EVIDENCE"
    REPLAY_HISTORICAL = "REPLAY_HISTORICAL"
    DDO_OBSERVATION_ONLY = "DDO_OBSERVATION_ONLY"
    CANARY_EVIDENCE = "CANARY_EVIDENCE"
    UNKNOWN = "UNKNOWN"
    AMBIGUOUS = "AMBIGUOUS"


class OutcomeRealizationKindV1(str, Enum):
    REALIZED = "REALIZED"
    SIMULATED = "SIMULATED"
    COUNTERFACTUAL = "COUNTERFACTUAL"
    REPLAYED = "REPLAYED"
    OBSERVATION_ONLY = "OBSERVATION_ONLY"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    UNKNOWN = "UNKNOWN"
    AMBIGUOUS = "AMBIGUOUS"


class ExternalCapitalFlowClassV1(str, Enum):
    NONE = "NONE"
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"
    INTERNAL_TRANSFER = "INTERNAL_TRANSFER"
    UNKNOWN = "UNKNOWN"
    AMBIGUOUS = "AMBIGUOUS"


PROVENANCE_ALLOWED_FIELDS: Final[frozenset[str]] = frozenset(
    {
        "schema_name",
        "schema_version",
        "provenance_version",
        "instrument_id",
        "venue_native_id",
        "decision_event_ref",
        "cycle_id",
        "trading_epoch",
        "producer_id",
        "producer_version",
        "market_observation_source",
        "ddo_ledger_environment",
        "order_environment_label",
        "decision_source",
        "execution_mode_label",
        "fill_source_type",
        "position_truth_source",
        "reconciliation_source",
        "accounting_source",
        "outcome_source",
        "outcome_semantic_class",
        "outcome_realization_kind",
        "outcome_scalar_kind",
        "external_capital_flow_class",
        "market_timestamp_utc",
        "decision_timestamp_utc",
        "evaluation_timestamp_utc",
        "evaluation_horizon",
        "lineage_digest",
        "provenance_status",
        "provenance_digest",
    }
)

_FAIL_CLOSED_STATUSES: Final[frozenset[str]] = frozenset({"UNKNOWN", "AMBIGUOUS"})


def _canonical_dumps(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def compute_provenance_digest_v1(provenance_body: Mapping[str, Any]) -> str:
    body = {k: v for k, v in provenance_body.items() if k != "provenance_digest"}
    return hashlib.sha256(_canonical_dumps(body).encode("utf-8")).hexdigest()


def provenance_implies_productive_truth_v1(provenance: Mapping[str, Any]) -> bool:
    status = str(provenance.get("provenance_status") or UNKNOWN)
    if status in _FAIL_CLOSED_STATUSES:
        return False
    oclass = str(provenance.get("outcome_semantic_class") or UNKNOWN)
    if oclass in _FAIL_CLOSED_STATUSES:
        return False
    if oclass in {
        OutcomeSemanticClassV1.OBSERVED_PRODUCTIVE_PRE_EXTERNAL.value,
    }:
        return True
    return False


def validate_outcome_evidence_provenance_v1(
    payload: Mapping[str, Any],
) -> MappingProxyType[str, Any]:
    raw = require_mapping(payload, "outcome_evidence_provenance")
    reject_unknown_fields(raw, PROVENANCE_ALLOWED_FIELDS)
    if raw.get("schema_name") != SCHEMA_NAME:
        raise DdoValidationError(f"PROVENANCE_SCHEMA_NAME_MISMATCH:{raw.get('schema_name')!r}")
    if raw.get("schema_version") != SCHEMA_VERSION:
        raise DdoValidationError(
            f"PROVENANCE_SCHEMA_VERSION_UNSUPPORTED:{raw.get('schema_version')!r}"
        )
    status = require_enum(
        raw.get("provenance_status"),
        "provenance_status",
        frozenset({"KNOWN", "UNKNOWN", "AMBIGUOUS"}),
    )
    canonical: dict[str, Any] = {
        "schema_name": SCHEMA_NAME,
        "schema_version": SCHEMA_VERSION,
        "provenance_version": require_non_empty_string_or_unknown(
            raw.get("provenance_version"), "provenance_version"
        ),
        "instrument_id": optional_string_or_unknown(raw.get("instrument_id"), "instrument_id"),
        "venue_native_id": optional_string_or_unknown(
            raw.get("venue_native_id"), "venue_native_id"
        ),
        "decision_event_ref": optional_string_or_unknown(
            raw.get("decision_event_ref"), "decision_event_ref"
        ),
        "cycle_id": None
        if raw.get("cycle_id") is None
        else require_record_id(raw.get("cycle_id"), "cycle_id"),
        "trading_epoch": optional_string_or_unknown(raw.get("trading_epoch"), "trading_epoch"),
        "producer_id": require_non_empty_string_or_unknown(raw.get("producer_id"), "producer_id"),
        "producer_version": optional_string_or_unknown(
            raw.get("producer_version"), "producer_version"
        ),
        "market_observation_source": require_enum(
            raw.get("market_observation_source"),
            "market_observation_source",
            frozenset(m.value for m in MarketObservationSourceV1),
        ),
        "ddo_ledger_environment": require_enum(
            raw.get("ddo_ledger_environment"),
            "ddo_ledger_environment",
            frozenset(m.value for m in DdoLedgerEnvironmentV1),
        ),
        "order_environment_label": optional_string_or_unknown(
            raw.get("order_environment_label"), "order_environment_label"
        ),
        "decision_source": require_enum(
            raw.get("decision_source"),
            "decision_source",
            frozenset(m.value for m in DecisionSourceV1),
        ),
        "execution_mode_label": require_enum(
            raw.get("execution_mode_label"),
            "execution_mode_label",
            frozenset(m.value for m in ExecutionModeLabelV1),
        ),
        "fill_source_type": require_enum(
            raw.get("fill_source_type"),
            "fill_source_type",
            frozenset(m.value for m in FillSourceTypeV1),
        ),
        "position_truth_source": optional_string_or_unknown(
            raw.get("position_truth_source"), "position_truth_source"
        ),
        "reconciliation_source": optional_string_or_unknown(
            raw.get("reconciliation_source"), "reconciliation_source"
        ),
        "accounting_source": optional_string_or_unknown(
            raw.get("accounting_source"), "accounting_source"
        ),
        "outcome_source": optional_string_or_unknown(raw.get("outcome_source"), "outcome_source"),
        "outcome_semantic_class": require_enum(
            raw.get("outcome_semantic_class"),
            "outcome_semantic_class",
            frozenset(m.value for m in OutcomeSemanticClassV1),
        ),
        "outcome_realization_kind": require_enum(
            raw.get("outcome_realization_kind"),
            "outcome_realization_kind",
            frozenset(m.value for m in OutcomeRealizationKindV1),
        ),
        "outcome_scalar_kind": optional_string_or_unknown(
            raw.get("outcome_scalar_kind"), "outcome_scalar_kind"
        ),
        "external_capital_flow_class": require_enum(
            raw.get("external_capital_flow_class"),
            "external_capital_flow_class",
            frozenset(m.value for m in ExternalCapitalFlowClassV1),
        ),
        "market_timestamp_utc": None
        if raw.get("market_timestamp_utc") is None
        else require_event_time_utc(raw.get("market_timestamp_utc"), "market_timestamp_utc"),
        "decision_timestamp_utc": None
        if raw.get("decision_timestamp_utc") is None
        else require_event_time_utc(raw.get("decision_timestamp_utc"), "decision_timestamp_utc"),
        "evaluation_timestamp_utc": None
        if raw.get("evaluation_timestamp_utc") is None
        else require_event_time_utc(
            raw.get("evaluation_timestamp_utc"), "evaluation_timestamp_utc"
        ),
        "evaluation_horizon": optional_string_or_unknown(
            raw.get("evaluation_horizon"), "evaluation_horizon"
        ),
        "lineage_digest": require_sha256_or_unknown(raw.get("lineage_digest"), "lineage_digest"),
        "provenance_status": status,
    }
    digest = compute_provenance_digest_v1(canonical)
    if raw.get("provenance_digest") is not None and raw["provenance_digest"] != digest:
        raise DdoValidationError("PROVENANCE_DIGEST_MISMATCH")
    canonical["provenance_digest"] = digest
    return MappingProxyType(canonical)


def build_outcome_evidence_provenance_v1(payload: Mapping[str, Any]) -> MappingProxyType[str, Any]:
    body = dict(payload)
    body.setdefault("schema_name", SCHEMA_NAME)
    body.setdefault("schema_version", SCHEMA_VERSION)
    body.setdefault("provenance_version", PROVENANCE_CONTRACT_VERSION)
    if "provenance_status" not in body:
        body["provenance_status"] = "KNOWN"
    return validate_outcome_evidence_provenance_v1(body)


def extract_outcome_provenance_from_record_v1(
    outcome_record: Mapping[str, Any],
) -> MappingProxyType[str, Any] | None:
    block = outcome_record.get("outcome_evidence_provenance")
    if block is None:
        return None
    return validate_outcome_evidence_provenance_v1(block)
