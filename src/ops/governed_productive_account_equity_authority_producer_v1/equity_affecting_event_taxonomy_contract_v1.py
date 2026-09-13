"""EQUITY_STOCK affecting event taxonomy contract.

UNKNOWN and UNCLASSIFIED are explicitly representable and are
execution/reconstruction-invalid. They must not map to zero or no-op.
No venue event kinds are invented. CLASSIFIED kinds remain unratified.
Not event acquisition. Not a reconstruction engine. AUTHORITY_EFFECT=NONE.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any, Mapping, Tuple

from src.ops.governed_productive_account_equity_authority_producer_v1.bound_account_identity_contract_v1 import (
    require_bound_account_identity_ref_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    DIMENSION_EQUITY_STOCK,
    UNCLASSIFIED_EVENT_FAIL_CLOSED,
)

SCHEMA_CLASS = "EQUITY_AFFECTING_EVENT_TAXONOMY_CONTRACT_V1"
CONTRACT_VERSION = "v1"
AUTHORITY_EFFECT = "NONE"
CLASSIFICATION_STATUS_UNKNOWN = "UNKNOWN"
CLASSIFICATION_STATUS_UNCLASSIFIED = "UNCLASSIFIED"
CLASSIFICATION_STATUS_CLASSIFIED = "CLASSIFIED"
CLASSIFICATION_STATUSES: Tuple[str, ...] = (
    CLASSIFICATION_STATUS_UNKNOWN,
    CLASSIFICATION_STATUS_UNCLASSIFIED,
    CLASSIFICATION_STATUS_CLASSIFIED,
)
RECONSTRUCTION_INVALID_STATUSES: Tuple[str, ...] = (
    CLASSIFICATION_STATUS_UNKNOWN,
    CLASSIFICATION_STATUS_UNCLASSIFIED,
)
RATIFIED_CLASSIFIED_KIND_SET: Tuple[str, ...] = ()
RATIFIED_CLASSIFIED_KIND_SET_RESOLVED = False
EVENT_ACQUISITION_PRESENT = False
REQUIRED_FIELDS: Tuple[str, ...] = (
    "event_record_id",
    "classification_status",
    "event_semantic_class",
    "target_dimension_id",
    "ordering_key",
    "event_digest",
    "mapped_numeric_effect",
    "bound_account_identity_ref",
    "bound_account_identity_digest",
    "reconstruction_eligibility",
    "execution_eligibility",
)
_SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")
_SILENT_ZERO_MARKERS: Tuple[str, ...] = (
    "0",
    "0.0",
    "zero",
    "no-op",
    "noop",
    "ignore",
    "omit",
)


class EquityAffectingEventTaxonomyContractError(ValueError):
    """Fail-closed event-taxonomy contract violation."""


@dataclass(frozen=True)
class EquityAffectingEventTaxonomyRecordV1:
    event_record_id: str
    classification_status: str
    event_semantic_class: str
    target_dimension_id: str
    ordering_key: str
    event_digest: str
    mapped_numeric_effect: str
    bound_account_identity_ref: str
    bound_account_identity_digest: str
    reconstruction_eligibility: str
    execution_eligibility: str
    authority_effect: str
    provenance_digest: str


def _require_non_empty_str(*, field: str, raw: Any) -> str:
    if raw is None:
        raise EquityAffectingEventTaxonomyContractError(f"EVENT_FIELD_MISSING:{field}")
    if isinstance(raw, bool) or not isinstance(raw, str):
        raise EquityAffectingEventTaxonomyContractError(f"EVENT_FIELD_NOT_STRING:{field}")
    text = raw.strip()
    if text == "" or text != raw:
        raise EquityAffectingEventTaxonomyContractError(f"EVENT_FIELD_MISSING:{field}")
    return text


def _canonical_json(payload: Mapping[str, str]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def compute_event_taxonomy_digest_v1(canonical: Mapping[str, str]) -> str:
    return hashlib.sha256(_canonical_json(canonical).encode("utf-8")).hexdigest()


def assert_unclassified_event_fail_closed_v1(
    *,
    classification_status: str,
    mapped_numeric_effect: str,
) -> None:
    if UNCLASSIFIED_EVENT_FAIL_CLOSED is not True:
        raise EquityAffectingEventTaxonomyContractError("UNCLASSIFIED_EVENT_FAIL_CLOSED_NOT_TRUE")
    if classification_status not in RECONSTRUCTION_INVALID_STATUSES:
        return
    effect = mapped_numeric_effect.strip().lower()
    if effect in _SILENT_ZERO_MARKERS or effect == "":
        raise EquityAffectingEventTaxonomyContractError(
            "UNCLASSIFIED_EVENT_CANNOT_MAP_TO_ZERO_OR_NOOP"
        )


def evaluate_event_reconstruction_eligibility_v1(
    *,
    classification_status: str,
    event_semantic_class: str,
) -> str:
    if EVENT_ACQUISITION_PRESENT is not False:
        raise EquityAffectingEventTaxonomyContractError("EVENT_TAXONOMY_IS_NOT_ACQUISITION")
    if classification_status not in CLASSIFICATION_STATUSES:
        raise EquityAffectingEventTaxonomyContractError(
            f"EVENT_CLASSIFICATION_STATUS_UNKNOWN_TOKEN:{classification_status}"
        )
    if classification_status in RECONSTRUCTION_INVALID_STATUSES:
        return "INVALID_FAIL_CLOSED"
    if classification_status == CLASSIFICATION_STATUS_CLASSIFIED:
        if event_semantic_class not in RATIFIED_CLASSIFIED_KIND_SET:
            raise EquityAffectingEventTaxonomyContractError("CLASSIFIED_KIND_NOT_RATIFIED")
    return "INVALID_FAIL_CLOSED"


def build_equity_affecting_event_taxonomy_record_v1(
    *,
    event_record_id: str,
    classification_status: str,
    event_semantic_class: str,
    ordering_key: str,
    event_digest: str,
    mapped_numeric_effect: str,
    bound_account_identity_ref: str,
    bound_account_identity_digest: str,
) -> EquityAffectingEventTaxonomyRecordV1:
    identity_ref, identity_digest = require_bound_account_identity_ref_v1(
        bound_account_identity_ref=bound_account_identity_ref,
        bound_account_identity_digest=bound_account_identity_digest,
    )
    payload = {
        "event_record_id": _require_non_empty_str(field="event_record_id", raw=event_record_id),
        "classification_status": _require_non_empty_str(
            field="classification_status", raw=classification_status
        ),
        "event_semantic_class": _require_non_empty_str(
            field="event_semantic_class", raw=event_semantic_class
        ),
        "target_dimension_id": DIMENSION_EQUITY_STOCK,
        "ordering_key": _require_non_empty_str(field="ordering_key", raw=ordering_key),
        "event_digest": _require_non_empty_str(field="event_digest", raw=event_digest),
        "mapped_numeric_effect": _require_non_empty_str(
            field="mapped_numeric_effect", raw=mapped_numeric_effect
        ),
        "bound_account_identity_ref": identity_ref,
        "bound_account_identity_digest": identity_digest,
    }
    if payload["classification_status"] not in CLASSIFICATION_STATUSES:
        raise EquityAffectingEventTaxonomyContractError(
            f"EVENT_CLASSIFICATION_STATUS_UNKNOWN_TOKEN:{payload['classification_status']}"
        )
    if payload["classification_status"] == CLASSIFICATION_STATUS_UNKNOWN:
        if payload["event_semantic_class"] != CLASSIFICATION_STATUS_UNKNOWN:
            raise EquityAffectingEventTaxonomyContractError("UNKNOWN_STATUS_CLASS_MISMATCH")
    if payload["classification_status"] == CLASSIFICATION_STATUS_UNCLASSIFIED:
        if payload["event_semantic_class"] != CLASSIFICATION_STATUS_UNCLASSIFIED:
            raise EquityAffectingEventTaxonomyContractError("UNCLASSIFIED_STATUS_CLASS_MISMATCH")
    if payload["classification_status"] == CLASSIFICATION_STATUS_CLASSIFIED:
        raise EquityAffectingEventTaxonomyContractError("CLASSIFIED_KIND_NOT_RATIFIED")
    if not _SHA256_HEX.match(payload["event_digest"]):
        raise EquityAffectingEventTaxonomyContractError("EVENT_DIGEST_NOT_SHA256")
    assert_unclassified_event_fail_closed_v1(
        classification_status=payload["classification_status"],
        mapped_numeric_effect=payload["mapped_numeric_effect"],
    )
    eligibility = evaluate_event_reconstruction_eligibility_v1(
        classification_status=payload["classification_status"],
        event_semantic_class=payload["event_semantic_class"],
    )
    payload["reconstruction_eligibility"] = eligibility
    payload["execution_eligibility"] = "INVALID_FAIL_CLOSED"
    digest_payload = dict(payload)
    digest_payload["authority_effect"] = AUTHORITY_EFFECT
    digest = compute_event_taxonomy_digest_v1(digest_payload)
    return EquityAffectingEventTaxonomyRecordV1(
        **payload,
        authority_effect=AUTHORITY_EFFECT,
        provenance_digest=digest,
    )
