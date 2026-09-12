"""GOVERNED_ACCOUNT_EQUITY_SOURCE_CANDIDATE_V1.

Non-authoritative C17+ candidate record. Candidate is not source
authority. Source is not mapping proven. AUTHORITY_EFFECT=NONE.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any, Mapping, Tuple

from src.ops.governed_productive_account_equity_authority_producer_v1.source_promotion_state_machine_v1 import (
    PR1_FORBIDDEN_STATES,
    assert_pr1_candidate_status_allowed_v1,
    candidate_cannot_self_authorize_v1,
)

SCHEMA_CLASS = "GOVERNED_ACCOUNT_EQUITY_SOURCE_CANDIDATE_V1"
CONTRACT_VERSION = "v1"
AUTHORITY_EFFECT = "NONE"
NEW_CANDIDATE_NAMESPACE_START = "C17"
C01_C16_REVIVAL_ALLOWED = False
OBSERVATION_VS_AUTHORITY_CLASS_ALLOWED: Tuple[str, ...] = (
    "OBSERVATION",
    "NON_AUTHORITATIVE_CANDIDATE",
)
C01_C16_IDS: Tuple[str, ...] = (
    "C01_Q_GET_PACK_DETAILS_AVAILEQ",
    "C02_FORBIDDEN_RAW_VENUE_EQ_FIELDS",
    "C03_CAPITAL_ADMISSION_ENVELOPE",
    "C04_CRS_ACCOUNT_EQUITY_CONSUMER",
    "C05_OFFLINE_REPLAY_DEFAULT_10000",
    "C06_INJECTED_RUNNING_ACCOUNT_EQUITY",
    "C07_FUNDING_ACCOUNT_BALANCE_OBSERVATION",
    "C08_TREASURY_OBSERVED_OR_RECONCILED_CAPITAL",
    "C09_CAP11_3_FIXTURE_PRIVATE_ACCOUNT_STATE",
    "C10_LEDGER_SNAPSHOT_EQUITY_BY_CCY",
    "C11_CAP31_PRODUCTIVE_FUTURES_ACCOUNTING",
    "C12_S1114_LIVE_ACCOUNTING_RECONSTRUCTED",
    "C13_BACKTEST_STATE_FILE_ACCOUNT_EQUITY",
    "C14_START_BALANCE",
    "C15_LIVE_ACCOUNT_BOUND_IDENTITY",
    "C16_RESTART_RECONSTRUCTION_ACCOUNTING",
)
REQUIRED_FIELDS: Tuple[str, ...] = (
    "candidate_id",
    "generation_class",
    "source_object_class",
    "producer_identity_claim",
    "account_scope",
    "venue_scope",
    "currency",
    "unit_class",
    "observation_authority_class",
    "authority_contract_ref",
    "source_revision_or_digest",
    "input_set_digest",
    "freshness_contract_ref",
    "reconciliation_contract_ref",
    "restart_reconstructability_class",
    "step_29p_compatibility_class",
    "evidence_refs",
    "candidate_status",
    "reason_codes",
)
_SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")
_C17_PLUS = re.compile(r"^C(1[7-9]|[2-9]\d|\d{3,})$")


class GovernedAccountEquitySourceCandidateError(ValueError):
    """Fail-closed C17+ source-candidate contract violation."""


@dataclass(frozen=True)
class GovernedAccountEquitySourceCandidateV1:
    candidate_id: str
    generation_class: str
    source_object_class: str
    producer_identity_claim: str
    account_scope: str
    venue_scope: str
    currency: str
    unit_class: str
    observation_authority_class: str
    authority_contract_ref: str
    source_revision_or_digest: str
    input_set_digest: str
    freshness_contract_ref: str
    reconciliation_contract_ref: str
    restart_reconstructability_class: str
    step_29p_compatibility_class: str
    evidence_refs: str
    candidate_status: str
    reason_codes: str
    authority_effect: str
    owner_ratified: str
    mapping_proven: str
    producer_authorized: str
    runtime_binding_authorized: str
    provenance_digest: str


def _require_non_empty_str(*, field: str, raw: Any) -> str:
    if raw is None:
        raise GovernedAccountEquitySourceCandidateError(f"CANDIDATE_FIELD_MISSING:{field}")
    if isinstance(raw, bool) or not isinstance(raw, str):
        raise GovernedAccountEquitySourceCandidateError(f"CANDIDATE_FIELD_NOT_STRING:{field}")
    text = raw.strip()
    if text == "" or text != raw:
        raise GovernedAccountEquitySourceCandidateError(f"CANDIDATE_FIELD_MISSING:{field}")
    return text


def _canonical_json(payload: Mapping[str, str]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def compute_source_candidate_digest_v1(canonical: Mapping[str, str]) -> str:
    return hashlib.sha256(_canonical_json(canonical).encode("utf-8")).hexdigest()


def _assert_c17_plus_id(candidate_id: str) -> None:
    if candidate_id in C01_C16_IDS:
        raise GovernedAccountEquitySourceCandidateError(f"C01_C16_REVIVAL_FORBIDDEN:{candidate_id}")
    prefix = candidate_id.split("_", 1)[0]
    if prefix in {item.split("_", 1)[0] for item in C01_C16_IDS}:
        raise GovernedAccountEquitySourceCandidateError(f"C01_C16_REVIVAL_FORBIDDEN:{candidate_id}")
    if not _C17_PLUS.match(prefix):
        raise GovernedAccountEquitySourceCandidateError(
            f"CANDIDATE_NAMESPACE_NOT_C17_PLUS:{candidate_id}"
        )


def build_governed_account_equity_source_candidate_v1(
    *,
    candidate_id: str,
    generation_class: str,
    source_object_class: str,
    producer_identity_claim: str,
    account_scope: str,
    venue_scope: str,
    currency: str,
    unit_class: str,
    observation_authority_class: str,
    authority_contract_ref: str,
    source_revision_or_digest: str,
    input_set_digest: str,
    freshness_contract_ref: str,
    reconciliation_contract_ref: str,
    restart_reconstructability_class: str,
    step_29p_compatibility_class: str,
    evidence_refs: str,
    candidate_status: str,
    reason_codes: str,
    revival_equivalent: bool = False,
) -> GovernedAccountEquitySourceCandidateV1:
    payload = {
        "candidate_id": _require_non_empty_str(field="candidate_id", raw=candidate_id),
        "generation_class": _require_non_empty_str(field="generation_class", raw=generation_class),
        "source_object_class": _require_non_empty_str(
            field="source_object_class", raw=source_object_class
        ),
        "producer_identity_claim": _require_non_empty_str(
            field="producer_identity_claim", raw=producer_identity_claim
        ),
        "account_scope": _require_non_empty_str(field="account_scope", raw=account_scope),
        "venue_scope": _require_non_empty_str(field="venue_scope", raw=venue_scope),
        "currency": _require_non_empty_str(field="currency", raw=currency),
        "unit_class": _require_non_empty_str(field="unit_class", raw=unit_class),
        "observation_authority_class": _require_non_empty_str(
            field="observation_authority_class", raw=observation_authority_class
        ),
        "authority_contract_ref": _require_non_empty_str(
            field="authority_contract_ref", raw=authority_contract_ref
        ),
        "source_revision_or_digest": _require_non_empty_str(
            field="source_revision_or_digest", raw=source_revision_or_digest
        ),
        "input_set_digest": _require_non_empty_str(field="input_set_digest", raw=input_set_digest),
        "freshness_contract_ref": _require_non_empty_str(
            field="freshness_contract_ref", raw=freshness_contract_ref
        ),
        "reconciliation_contract_ref": _require_non_empty_str(
            field="reconciliation_contract_ref", raw=reconciliation_contract_ref
        ),
        "restart_reconstructability_class": _require_non_empty_str(
            field="restart_reconstructability_class",
            raw=restart_reconstructability_class,
        ),
        "step_29p_compatibility_class": _require_non_empty_str(
            field="step_29p_compatibility_class", raw=step_29p_compatibility_class
        ),
        "evidence_refs": _require_non_empty_str(field="evidence_refs", raw=evidence_refs),
        "candidate_status": _require_non_empty_str(field="candidate_status", raw=candidate_status),
        "reason_codes": _require_non_empty_str(field="reason_codes", raw=reason_codes),
    }
    _assert_c17_plus_id(payload["candidate_id"])
    if revival_equivalent or payload["generation_class"] == "C01_C16_REVIVAL":
        raise GovernedAccountEquitySourceCandidateError(
            f"C01_C16_REVIVAL_FORBIDDEN:{payload['candidate_id']}"
        )
    if payload["generation_class"] != "NEW_SOURCE_GENERATION":
        raise GovernedAccountEquitySourceCandidateError(
            f"GENERATION_CLASS_NOT_NEW:{payload['generation_class']}"
        )
    if payload["observation_authority_class"] not in OBSERVATION_VS_AUTHORITY_CLASS_ALLOWED:
        raise GovernedAccountEquitySourceCandidateError("OBSERVATION_CANNOT_MINT_AUTHORITY")
    if payload["observation_authority_class"] == "AUTHORITY":
        raise GovernedAccountEquitySourceCandidateError("OBSERVATION_CANNOT_MINT_AUTHORITY")
    if not _SHA256_HEX.match(payload["source_revision_or_digest"]):
        raise GovernedAccountEquitySourceCandidateError("SOURCE_REVISION_OR_DIGEST_NOT_SHA256")
    if not _SHA256_HEX.match(payload["input_set_digest"]):
        raise GovernedAccountEquitySourceCandidateError("INPUT_SET_DIGEST_NOT_SHA256")
    status = assert_pr1_candidate_status_allowed_v1(payload["candidate_status"])
    candidate_cannot_self_authorize_v1(claimed_status=status)
    if status in PR1_FORBIDDEN_STATES:
        raise GovernedAccountEquitySourceCandidateError(f"PR1_FORBIDDEN_CANDIDATE_STATUS:{status}")
    digest_payload = dict(payload)
    digest_payload["authority_effect"] = AUTHORITY_EFFECT
    digest_payload["owner_ratified"] = "false"
    digest_payload["mapping_proven"] = "false"
    digest_payload["producer_authorized"] = "false"
    digest_payload["runtime_binding_authorized"] = "false"
    digest = compute_source_candidate_digest_v1(digest_payload)
    return GovernedAccountEquitySourceCandidateV1(
        **payload,
        authority_effect=AUTHORITY_EFFECT,
        owner_ratified="false",
        mapping_proven="false",
        producer_authorized="false",
        runtime_binding_authorized="false",
        provenance_digest=digest,
    )
