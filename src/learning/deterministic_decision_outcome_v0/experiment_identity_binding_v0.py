"""Canonical Experiment Identity reference adapter v0.

DDO consumes already-serialized Canonical Experiment Identity v1 records.
This module does not import ``src.experiments``, does not mint identity, and
does not become a second experiment-identity owner.

EXISTING AUTHORITATIVE PRODUCER
    -> immutable/versioned identity record
    -> DDO reference adapter
    -> learning/evaluation

Unbound ``candidate.experiment_ref`` values remain explicit non-equivalence.
"""

from __future__ import annotations

import re
from types import MappingProxyType
from typing import Any, Final, Mapping

from src.learning.deterministic_decision_outcome_v0.common_v0 import (
    SCHEMA_NAME_CANONICAL_EXPERIMENT_IDENTITY_REF,
    SCHEMA_VERSION_CANONICAL_EXPERIMENT_IDENTITY_REF_V0,
    SHARED_IDENTITY_FIELD_SPECS_V0,
    FieldSpecV0,
    finalize_record_v0,
    optional_record_id,
    optional_ref,
    parse_shared_envelope_v0,
    reject_unknown_fields,
    require_enum,
    require_mapping,
    require_non_empty_string_or_unknown,
    require_sha256_or_unknown,
)
from src.learning.deterministic_decision_outcome_v0.enums_v0 import (
    EXPERIMENT_IDENTITY_BINDING_STATUS_V0,
    UNKNOWN,
)
from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoValidationError

CANONICAL_EXPERIMENT_IDENTITY_SCHEMA_VERSION: Final[str] = "canonical_experiment_identity_v1"
CANONICAL_EXPERIMENT_IDENTITY_DOMAIN: Final[str] = "peak_trade.canonical_experiment_identity.v1"
CANONICAL_EXPERIMENT_IDENTITY_OWNER_PATH: Final[str] = (
    "src/experiments/canonical_experiment_identity_v1.py"
)
PACKAGE_N_INCOMPLETE_PROJECTION_SCHEMA: Final[str] = "experiment_identity_manifest_v1"
DDO_EXPERIMENT_IDENTITY_OWNER: Final[str] = "EXISTING_CANONICAL_EXPERIMENT_IDENTITY_V1"
SECOND_EXPERIMENT_IDENTITY_OWNER_CREATED: Final[bool] = False
DDO_MINTS_EXPERIMENT_IDENTITY: Final[bool] = False
ADAPTER_ID: Final[str] = "peak_trade.learning.ddo.canonical_experiment_identity_ref_v0"
ADAPTER_VERSION: Final[str] = "canonical_experiment_identity_ref_v0"

_GIT_SHA1_RE: Final[re.Pattern[str]] = re.compile(r"^[0-9a-f]{40}$")

_IDENTITY_EXTRA: Final[tuple[FieldSpecV0, ...]] = (
    FieldSpecV0(
        "source_schema_version",
        "REQUIRED",
        "string",
        True,
        "Producer schema. Must be canonical_experiment_identity_v1 when BOUND.",
    ),
    FieldSpecV0(
        "source_identity_domain",
        "REQUIRED",
        "string",
        True,
        "Producer identity domain. Must match the existing canonical owner when BOUND.",
    ),
    FieldSpecV0(
        "source_owner_path",
        "REQUIRED",
        "string",
        True,
        "Existing owner path. Reference only; DDO does not import this module.",
    ),
    FieldSpecV0(
        "identity_digest",
        "REQUIRED",
        "sha256|UNKNOWN",
        True,
        "Producer identity_digest. DDO does not recompute or mint this digest.",
    ),
    FieldSpecV0(
        "git_sha",
        "REQUIRED",
        "string",
        True,
        "Producer git_sha when present. UNKNOWN if the producer omitted it.",
    ),
    FieldSpecV0(
        "completeness",
        "REQUIRED",
        "string",
        True,
        "Producer completeness token. COMPLETE required for BOUND.",
    ),
    FieldSpecV0(
        "claimed_experiment_ref",
        "OPTIONAL",
        "ref|null",
        True,
        "Candidate.experiment_ref being proven. Null/UNKNOWN means unbound.",
    ),
    FieldSpecV0(
        "claimed_candidate_ref",
        "OPTIONAL",
        "record_id|null",
        True,
        "Optional candidate artifact record_id. Not an identity mint.",
    ),
    FieldSpecV0(
        "binding_status",
        "REQUIRED",
        "enum:EXPERIMENT_IDENTITY_BINDING_STATUS_V0",
        True,
        "BOUND only when producer identity is canonical COMPLETE and equivalent.",
    ),
    FieldSpecV0(
        "equivalence_proven",
        "REQUIRED",
        "bool",
        True,
        "True only for BOUND. Unbound refs stay explicit non-equivalence.",
    ),
    FieldSpecV0(
        "ddo_mints_identity",
        "REQUIRED",
        "bool",
        True,
        "Must be false. DDO is not an experiment identity authority.",
    ),
    FieldSpecV0(
        "second_experiment_identity_owner_created",
        "REQUIRED",
        "bool",
        True,
        "Must be false.",
    ),
)

CANONICAL_EXPERIMENT_IDENTITY_REF_FIELD_SPECS_V0: Final[tuple[FieldSpecV0, ...]] = (
    SHARED_IDENTITY_FIELD_SPECS_V0[:-1] + _IDENTITY_EXTRA + SHARED_IDENTITY_FIELD_SPECS_V0[-1:]
)
CANONICAL_EXPERIMENT_IDENTITY_REF_ALLOWED_FIELDS: Final[frozenset[str]] = frozenset(
    spec.name for spec in CANONICAL_EXPERIMENT_IDENTITY_REF_FIELD_SPECS_V0
)


def _require_bool(value: Any, field: str) -> bool:
    if not isinstance(value, bool):
        raise DdoValidationError(f"{field}_MUST_BE_BOOL")
    return value


def _git_sha_or_unknown(value: Any) -> str:
    if value is None:
        return UNKNOWN
    if not isinstance(value, str) or not value:
        raise DdoValidationError("INVALID_GIT_SHA")
    if value == UNKNOWN:
        return UNKNOWN
    if not _GIT_SHA1_RE.fullmatch(value):
        raise DdoValidationError("NONCANONICAL_GIT_SHA")
    return value


def build_canonical_experiment_identity_ref_v0(
    payload: Mapping[str, Any],
) -> MappingProxyType[str, Any]:
    raw = require_mapping(payload, "canonical_experiment_identity_ref")
    reject_unknown_fields(raw, CANONICAL_EXPERIMENT_IDENTITY_REF_ALLOWED_FIELDS)
    envelope = parse_shared_envelope_v0(
        raw,
        schema_name=SCHEMA_NAME_CANONICAL_EXPERIMENT_IDENTITY_REF,
        schema_version=SCHEMA_VERSION_CANONICAL_EXPERIMENT_IDENTITY_REF_V0,
    )
    ddo_mints = _require_bool(raw.get("ddo_mints_identity"), "ddo_mints_identity")
    second_owner = _require_bool(
        raw.get("second_experiment_identity_owner_created"),
        "second_experiment_identity_owner_created",
    )
    if ddo_mints is not False:
        raise DdoValidationError("DDO_MUST_NOT_MINT_EXPERIMENT_IDENTITY")
    if second_owner is not False:
        raise DdoValidationError("SECOND_EXPERIMENT_IDENTITY_OWNER_FORBIDDEN")
    binding_status = require_enum(
        raw.get("binding_status"), "binding_status", EXPERIMENT_IDENTITY_BINDING_STATUS_V0
    )
    equivalence = _require_bool(raw.get("equivalence_proven"), "equivalence_proven")
    if binding_status == "BOUND" and equivalence is not True:
        raise DdoValidationError("BOUND_REQUIRES_EQUIVALENCE_PROVEN")
    if binding_status != "BOUND" and equivalence is True:
        raise DdoValidationError("EQUIVALENCE_PROVEN_REQUIRES_BOUND")
    source_schema = require_non_empty_string_or_unknown(
        raw.get("source_schema_version"), "source_schema_version"
    )
    source_domain = require_non_empty_string_or_unknown(
        raw.get("source_identity_domain"), "source_identity_domain"
    )
    if binding_status == "BOUND":
        if source_schema != CANONICAL_EXPERIMENT_IDENTITY_SCHEMA_VERSION:
            raise DdoValidationError("BOUND_REQUIRES_CANONICAL_EXPERIMENT_IDENTITY_SCHEMA")
        if source_domain != CANONICAL_EXPERIMENT_IDENTITY_DOMAIN:
            raise DdoValidationError("BOUND_REQUIRES_CANONICAL_EXPERIMENT_IDENTITY_DOMAIN")
        completeness = require_non_empty_string_or_unknown(raw.get("completeness"), "completeness")
        if completeness != "COMPLETE":
            raise DdoValidationError("BOUND_REQUIRES_COMPLETE_IDENTITY")
        identity_digest = require_sha256_or_unknown(raw.get("identity_digest"), "identity_digest")
        if identity_digest == UNKNOWN:
            raise DdoValidationError("BOUND_REQUIRES_IDENTITY_DIGEST")
        git_sha = _git_sha_or_unknown(raw.get("git_sha"))
        if git_sha == UNKNOWN:
            raise DdoValidationError("BOUND_REQUIRES_GIT_SHA")
    else:
        completeness = require_non_empty_string_or_unknown(raw.get("completeness"), "completeness")
        identity_digest = require_sha256_or_unknown(raw.get("identity_digest"), "identity_digest")
        git_sha = raw.get("git_sha")
        git_sha = UNKNOWN if git_sha is None else _git_sha_or_unknown(git_sha)
    canonical = {
        **envelope,
        "source_schema_version": source_schema,
        "source_identity_domain": source_domain,
        "source_owner_path": require_non_empty_string_or_unknown(
            raw.get("source_owner_path"), "source_owner_path"
        ),
        "identity_digest": identity_digest,
        "git_sha": git_sha,
        "completeness": completeness,
        "claimed_experiment_ref": optional_ref(
            raw.get("claimed_experiment_ref"), "claimed_experiment_ref"
        ),
        "claimed_candidate_ref": optional_record_id(
            raw.get("claimed_candidate_ref"), "claimed_candidate_ref"
        ),
        "binding_status": binding_status,
        "equivalence_proven": equivalence,
        "ddo_mints_identity": False,
        "second_experiment_identity_owner_created": False,
    }
    return finalize_record_v0(canonical, raw)


def validate_canonical_experiment_identity_ref_v0(
    payload: Mapping[str, Any],
) -> MappingProxyType[str, Any]:
    return build_canonical_experiment_identity_ref_v0(payload)


def _identity_mapping(identity_payload: Any) -> Mapping[str, Any]:
    raw = require_mapping(identity_payload, "canonical_experiment_identity")
    if raw.get("schema_version") == PACKAGE_N_INCOMPLETE_PROJECTION_SCHEMA:
        raise DdoValidationError("NONCANONICAL_EXPERIMENT_IDENTITY_PACKAGE_N_PROJECTION")
    if raw.get("schema_version") != CANONICAL_EXPERIMENT_IDENTITY_SCHEMA_VERSION:
        raise DdoValidationError(
            f"NONCANONICAL_EXPERIMENT_IDENTITY_SCHEMA:{raw.get('schema_version')!r}"
        )
    if raw.get("identity_domain") != CANONICAL_EXPERIMENT_IDENTITY_DOMAIN:
        raise DdoValidationError("NONCANONICAL_EXPERIMENT_IDENTITY_DOMAIN")
    if raw.get("completeness") != "COMPLETE":
        raise DdoValidationError("INCOMPLETE_EXPERIMENT_IDENTITY")
    digest = raw.get("identity_digest")
    if not isinstance(digest, str) or digest == UNKNOWN:
        raise DdoValidationError("IDENTITY_DIGEST_MISSING")
    require_sha256_or_unknown(digest, "identity_digest")
    return raw


def bind_canonical_experiment_identity_ref_v0(
    *,
    identity_payload: Mapping[str, Any],
    envelope: Mapping[str, Any],
    claimed_experiment_ref: str | None = None,
    claimed_candidate_ref: str | None = None,
) -> MappingProxyType[str, Any]:
    """Bind a producer identity record. Does not recompute identity_digest."""
    identity = _identity_mapping(identity_payload)
    digest = str(identity["identity_digest"])
    if (
        claimed_experiment_ref is not None
        and claimed_experiment_ref != UNKNOWN
        and claimed_experiment_ref != digest
    ):
        raise DdoValidationError("EXPERIMENT_REF_NOT_EQUIVALENT_TO_CANONICAL_IDENTITY_DIGEST")
    payload = {
        **dict(envelope),
        "schema_name": SCHEMA_NAME_CANONICAL_EXPERIMENT_IDENTITY_REF,
        "schema_version": SCHEMA_VERSION_CANONICAL_EXPERIMENT_IDENTITY_REF_V0,
        "source_schema_version": CANONICAL_EXPERIMENT_IDENTITY_SCHEMA_VERSION,
        "source_identity_domain": CANONICAL_EXPERIMENT_IDENTITY_DOMAIN,
        "source_owner_path": CANONICAL_EXPERIMENT_IDENTITY_OWNER_PATH,
        "identity_digest": digest,
        "git_sha": identity.get("git_sha"),
        "completeness": "COMPLETE",
        "claimed_experiment_ref": claimed_experiment_ref,
        "claimed_candidate_ref": claimed_candidate_ref,
        "binding_status": "BOUND",
        "equivalence_proven": True,
        "ddo_mints_identity": False,
        "second_experiment_identity_owner_created": False,
        "producer_id": envelope.get("producer_id", ADAPTER_ID),
        "producer_version": envelope.get("producer_version", ADAPTER_VERSION),
    }
    return build_canonical_experiment_identity_ref_v0(payload)


def observe_unbound_experiment_ref_v0(
    *,
    envelope: Mapping[str, Any],
    claimed_experiment_ref: str | None = None,
    claimed_candidate_ref: str | None = None,
) -> MappingProxyType[str, Any]:
    """Preserve opaque experiment_ref as explicit non-equivalence. Does not mint identity."""
    payload = {
        **dict(envelope),
        "schema_name": SCHEMA_NAME_CANONICAL_EXPERIMENT_IDENTITY_REF,
        "schema_version": SCHEMA_VERSION_CANONICAL_EXPERIMENT_IDENTITY_REF_V0,
        "source_schema_version": UNKNOWN,
        "source_identity_domain": UNKNOWN,
        "source_owner_path": CANONICAL_EXPERIMENT_IDENTITY_OWNER_PATH,
        "identity_digest": UNKNOWN,
        "git_sha": UNKNOWN,
        "completeness": UNKNOWN,
        "claimed_experiment_ref": claimed_experiment_ref,
        "claimed_candidate_ref": claimed_candidate_ref,
        "binding_status": UNKNOWN,
        "equivalence_proven": False,
        "ddo_mints_identity": False,
        "second_experiment_identity_owner_created": False,
        "producer_id": envelope.get("producer_id", ADAPTER_ID),
        "producer_version": envelope.get("producer_version", ADAPTER_VERSION),
    }
    return build_canonical_experiment_identity_ref_v0(payload)
