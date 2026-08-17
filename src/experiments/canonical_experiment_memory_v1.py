"""Phase 2 Immutable Experiment Memory v1 (research evidence only).

Append-only historical research truth for COMPLETE Canonical Experiment
Identity v1 records. This layer has no runtime, order, live, funding,
canary, promotion, or config-write authority.

Existing tracking surfaces (``tracking/run_summary.py``,
``live_session_registry.py``, Package N identity) remain incomplete
historical projections and are not reinterpreted as COMPLETE memory.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Final, Mapping, Sequence

from src.experiments.canonical_experiment_identity_v1 import (
    CanonicalExperimentIdentityError,
    canonicalize_mapping,
    validate_canonical_experiment_identity_v1,
)
from src.meta.learning_loop.contract_safety_v1 import (
    compute_content_sha256,
    is_valid_sha256_hex,
)

SCHEMA_VERSION: Final[str] = "canonical_experiment_memory_v1"
MEMORY_DOMAIN: Final[str] = "peak_trade.canonical_experiment_memory.v1"
DIGEST_ALGORITHM: Final[str] = "sha256"
RECORD_COMPLETENESS_COMPLETE: Final[str] = "COMPLETE"
LINEAGE_KIND_ROOT: Final[str] = "ROOT"
LINEAGE_KIND_PARENT_BOUND: Final[str] = "PARENT_BOUND"
ARTIFACT_KIND_REPO_RELATIVE: Final[str] = "REPO_RELATIVE"
ARTIFACT_KIND_STORE_RELATIVE: Final[str] = "STORE_RELATIVE"
REF_KIND_IDENTITY_DIGEST_BOUND: Final[str] = "IDENTITY_DIGEST_BOUND"

EXPERIMENT_MEMORY_HAS_RUNTIME_AUTHORITY: Final[bool] = False
EXPERIMENT_MEMORY_CAN_MUTATE_LIVE_CONFIG: Final[bool] = False
EXPERIMENT_MEMORY_CAN_PROMOTE: Final[bool] = False
RUNTIME_AUTHORITY_IMPACT: Final[str] = "NONE"

CANONICAL_DISPOSITIONS: Final[tuple[str, ...]] = (
    "REJECTED_DATA_QUALITY",
    "REJECTED_REPRODUCIBILITY",
    "REJECTED_OVERFIT",
    "REJECTED_COST_SENSITIVITY",
    "REJECTED_TAIL_RISK",
    "REJECTED_REGIME_CONCENTRATION",
    "REJECTED_COMPARABILITY",
    "REJECTED_REALITY_GAP",
    "REJECTED_POLICY",
    "RETEST_WITH_NEW_COST_MODEL",
    "RESEARCH_ONLY",
    "CHALLENGER_ELIGIBLE",
    "SHADOW_ELIGIBLE",
    "TESTNET_ELIGIBLE",
    "PROMOTION_EVIDENCE_READY",
)
_REJECTION_DISPOSITIONS: Final[frozenset[str]] = frozenset(
    disposition for disposition in CANONICAL_DISPOSITIONS if disposition.startswith("REJECTED_")
)
_REJECTION_DISPOSITIONS_REQUIRING_REASON: Final[frozenset[str]] = (
    _REJECTION_DISPOSITIONS | frozenset({"RETEST_WITH_NEW_COST_MODEL"})
)

CANDIDATE_ROLES: Final[tuple[str, ...]] = (
    "UNSCOPED",
    "RESEARCH",
    "CHALLENGER",
    "SHADOW",
    "TESTNET",
)
COMPARISON_STATUSES: Final[tuple[str, ...]] = (
    "NOT_COMPARED",
    "INCOMPARABLE",
    "DEFERRED",
)
ARTIFACT_KINDS: Final[tuple[str, ...]] = (
    ARTIFACT_KIND_REPO_RELATIVE,
    ARTIFACT_KIND_STORE_RELATIVE,
)

_CREATED_AT_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,9})?Z$")
_HYPOTHESIS_ID_RE = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
_STRATEGY_FAMILY_RE = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
_UNAVAILABLE_TOKENS = frozenset(
    {
        "",
        "unknown",
        "unavailable",
        "n/a",
        "na",
        "none",
        "null",
        "implicit",
        "default",
    }
)
_CORE_LOGIC_DIGEST_FIELDS: Final[tuple[str, ...]] = (
    "trading_decision_core_digest",
    "market_context_contract_digest",
    "bull_bear_logic_digest",
    "state_switch_logic_digest",
    "survival_logic_digest",
    "suitability_logic_digest",
    "double_play_logic_digest",
    "entry_position_exit_logic_digest",
)
_IDENTITY_REF_BINDINGS: Final[tuple[tuple[str, str], ...]] = (
    ("dataset_ref", "dataset_digest"),
    ("cost_model_ref", "cost_model_digest"),
    ("risk_policy_ref", "risk_policy_digest"),
    ("portfolio_ref", "portfolio_digest"),
)

_LOGGER = logging.getLogger(__name__)


class ExperimentMemoryValidationError(ValueError):
    """Fail-closed Canonical Experiment Memory v1 validation error."""


class ExperimentRecordConflictError(ExperimentMemoryValidationError):
    """Same experiment_id with divergent canonical historical content."""


@dataclass(frozen=True)
class ArtifactReferenceV1:
    kind: str
    ref: str
    digest: str
    media_type: str | None = None


@dataclass(frozen=True)
class LineageReferenceV1:
    kind: str
    parent_experiment: str | None
    ancestors: tuple[str, ...] = ()


@dataclass(frozen=True)
class CanonicalExperimentMemoryRecordRequestV1:
    experiment_identity: Mapping[str, Any]
    hypothesis_id: str
    hypothesis_fingerprint: str
    parent_experiment: str | None
    strategy_family: str
    candidate_role: str
    dataset_ref: Mapping[str, Any]
    cost_model_ref: Mapping[str, Any]
    risk_policy_ref: Mapping[str, Any]
    portfolio_ref: Mapping[str, Any]
    metrics: Mapping[str, Any]
    robustness_results: Mapping[str, Any]
    regime_results: Mapping[str, Any]
    comparison_status: str
    disposition: str
    rejection_reason: str | None
    created_at: str
    artifacts: Sequence[Mapping[str, Any]]
    experiment_id: str | None = None
    lineage_ancestors: Sequence[str] | tuple[str, ...] | None = None
    supersedes_experiment_id: str | None = None


def derive_experiment_id_v1(identity_digest: str) -> str:
    digest = _require_sha256("identity_digest", identity_digest)
    envelope = {
        "digest_algorithm": DIGEST_ALGORITHM,
        "digest_domain": f"{MEMORY_DOMAIN}.experiment_id",
        "payload": {"identity_digest": digest},
        "schema_version": SCHEMA_VERSION,
    }
    return compute_content_sha256(envelope)


def build_canonical_experiment_memory_record_v1(
    request: CanonicalExperimentMemoryRecordRequestV1,
) -> Mapping[str, Any]:
    identity = _require_identity(request.experiment_identity)
    experiment_id = derive_experiment_id_v1(str(identity["identity_digest"]))
    if request.experiment_id is not None:
        provided = _require_sha256("experiment_id", request.experiment_id)
        if provided != experiment_id:
            raise ExperimentMemoryValidationError(
                "experiment_id is not bound to the Canonical Experiment Identity digest"
            )
    created_at = _require_created_at(request.created_at)
    lineage = _lineage_block(
        experiment_id=experiment_id,
        parent_experiment=request.parent_experiment,
        ancestors=request.lineage_ancestors,
    )
    artifacts = _canonicalize_artifacts(request.artifacts)
    record = {
        "artifacts": artifacts,
        "candidate_role": _require_enum("candidate_role", request.candidate_role, CANDIDATE_ROLES),
        "canonical_trading_decision_core_bound": True,
        "comparison_status": _require_enum(
            "comparison_status", request.comparison_status, COMPARISON_STATUSES
        ),
        "completeness": RECORD_COMPLETENESS_COMPLETE,
        "cost_model_ref": _bound_ref("cost_model_ref", request.cost_model_ref, identity),
        "created_at": created_at,
        "dataset_ref": _bound_ref("dataset_ref", request.dataset_ref, identity),
        "digest_algorithm": DIGEST_ALGORITHM,
        "disposition": _require_disposition(request.disposition),
        "experiment_id": experiment_id,
        "experiment_identity": identity,
        "experiment_memory_can_mutate_live_config": EXPERIMENT_MEMORY_CAN_MUTATE_LIVE_CONFIG,
        "experiment_memory_can_promote": EXPERIMENT_MEMORY_CAN_PROMOTE,
        "experiment_memory_has_runtime_authority": EXPERIMENT_MEMORY_HAS_RUNTIME_AUTHORITY,
        "hypothesis_fingerprint": _require_sha256(
            "hypothesis_fingerprint", request.hypothesis_fingerprint
        ),
        "hypothesis_id": _require_token("hypothesis_id", request.hypothesis_id, _HYPOTHESIS_ID_RE),
        "lineage": lineage,
        "memory_domain": MEMORY_DOMAIN,
        "metrics": _canonicalize_numeric_tree("metrics", request.metrics),
        "parent_experiment": lineage["parent_experiment"],
        "portfolio_ref": _bound_ref("portfolio_ref", request.portfolio_ref, identity),
        "record_schema_version": SCHEMA_VERSION,
        "regime_results": _canonicalize_numeric_tree("regime_results", request.regime_results),
        "rejection_reason": _require_rejection_reason(
            request.disposition, request.rejection_reason
        ),
        "risk_policy_ref": _bound_ref("risk_policy_ref", request.risk_policy_ref, identity),
        "robustness_results": _canonicalize_numeric_tree(
            "robustness_results", request.robustness_results
        ),
        "runtime_authority_impact": RUNTIME_AUTHORITY_IMPACT,
        "strategy_family": _require_token(
            "strategy_family", request.strategy_family, _STRATEGY_FAMILY_RE
        ),
        "supersedes_experiment_id": _optional_experiment_id(
            "supersedes_experiment_id",
            request.supersedes_experiment_id,
            experiment_id,
        ),
    }
    record["integrity"] = {
        "content_sha256": compute_content_sha256(
            {key: value for key, value in record.items() if key != "integrity"}
        )
    }
    validate_canonical_experiment_memory_record_v1(record)
    frozen = _freeze(record)
    _LOGGER.info(
        "canonical_experiment_memory_v1 built experiment_id=%s identity_digest=%s disposition=%s runtime_authority=%s",
        record["experiment_id"],
        identity["identity_digest"],
        record["disposition"],
        record["experiment_memory_has_runtime_authority"],
    )
    return frozen


def validate_canonical_experiment_memory_record_v1(record: Mapping[str, Any]) -> None:
    if not isinstance(record, Mapping):
        raise ExperimentMemoryValidationError("memory record must be a mapping")
    record = _plain_mapping(record)
    if record.get("record_schema_version") != SCHEMA_VERSION:
        raise ExperimentMemoryValidationError("record_schema_version mismatch")
    if record.get("memory_domain") != MEMORY_DOMAIN:
        raise ExperimentMemoryValidationError("memory_domain mismatch")
    if record.get("completeness") != RECORD_COMPLETENESS_COMPLETE:
        raise ExperimentMemoryValidationError("non-COMPLETE memory records are forbidden")
    if record.get("digest_algorithm") != DIGEST_ALGORITHM:
        raise ExperimentMemoryValidationError("digest_algorithm mismatch")
    if record.get("experiment_memory_has_runtime_authority") is not False:
        raise ExperimentMemoryValidationError(
            "experiment_memory_has_runtime_authority must be false"
        )
    if record.get("experiment_memory_can_mutate_live_config") is not False:
        raise ExperimentMemoryValidationError(
            "experiment_memory_can_mutate_live_config must be false"
        )
    if record.get("experiment_memory_can_promote") is not False:
        raise ExperimentMemoryValidationError("experiment_memory_can_promote must be false")
    if record.get("runtime_authority_impact") != RUNTIME_AUTHORITY_IMPACT:
        raise ExperimentMemoryValidationError("runtime_authority_impact must be NONE")
    if record.get("canonical_trading_decision_core_bound") is not True:
        raise ExperimentMemoryValidationError("canonical_trading_decision_core_bound must be true")

    identity = _require_identity(record.get("experiment_identity"))
    experiment_id = _require_sha256("experiment_id", record.get("experiment_id"))
    expected_id = derive_experiment_id_v1(str(identity["identity_digest"]))
    if experiment_id != expected_id:
        raise ExperimentMemoryValidationError(
            "experiment_id is not bound to the Canonical Experiment Identity digest"
        )
    _require_created_at(record.get("created_at"))
    _require_enum("candidate_role", record.get("candidate_role"), CANDIDATE_ROLES)
    _require_enum("comparison_status", record.get("comparison_status"), COMPARISON_STATUSES)
    disposition = _require_disposition(record.get("disposition"))
    _require_rejection_reason(disposition, record.get("rejection_reason"))
    _require_token("hypothesis_id", record.get("hypothesis_id"), _HYPOTHESIS_ID_RE)
    _require_sha256("hypothesis_fingerprint", record.get("hypothesis_fingerprint"))
    _require_token("strategy_family", record.get("strategy_family"), _STRATEGY_FAMILY_RE)
    _optional_experiment_id(
        "supersedes_experiment_id",
        record.get("supersedes_experiment_id"),
        experiment_id,
    )

    lineage = record.get("lineage")
    if not isinstance(lineage, Mapping):
        raise ExperimentMemoryValidationError("lineage must be a mapping")
    expected_lineage = _lineage_block(
        experiment_id=experiment_id,
        parent_experiment=lineage.get("parent_experiment"),
        ancestors=lineage.get("ancestors"),
    )
    if _plain_mapping(lineage) != expected_lineage:
        raise ExperimentMemoryValidationError("lineage is inconsistent")
    if record.get("parent_experiment") != expected_lineage["parent_experiment"]:
        raise ExperimentMemoryValidationError("parent_experiment does not match lineage")

    for ref_field, digest_field in _IDENTITY_REF_BINDINGS:
        expected_ref = _bound_ref(ref_field, record.get(ref_field), identity)
        if _plain_mapping(record.get(ref_field)) != expected_ref:
            raise ExperimentMemoryValidationError(f"{ref_field} is not identity-digest-bound")

    _canonicalize_numeric_tree("metrics", record.get("metrics"))
    _canonicalize_numeric_tree("robustness_results", record.get("robustness_results"))
    _canonicalize_numeric_tree("regime_results", record.get("regime_results"))
    _canonicalize_artifacts(record.get("artifacts"))

    for field_name in _CORE_LOGIC_DIGEST_FIELDS:
        _require_sha256(field_name, identity.get(field_name))

    expected_integrity = compute_content_sha256(
        {key: value for key, value in record.items() if key != "integrity"}
    )
    integrity = record.get("integrity")
    if not isinstance(integrity, Mapping) or integrity.get("content_sha256") != expected_integrity:
        raise ExperimentMemoryValidationError("integrity.content_sha256 mismatch")


def canonical_record_payload(record: Mapping[str, Any]) -> dict[str, Any]:
    return _plain_mapping(record)


def freeze_canonical_experiment_memory_record_v1(record: Mapping[str, Any]) -> Mapping[str, Any]:
    validate_canonical_experiment_memory_record_v1(record)
    return _freeze(canonical_record_payload(record))


def _require_identity(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ExperimentMemoryValidationError("experiment_identity present and valid is required")
    identity = _plain_mapping(value)
    try:
        validate_canonical_experiment_identity_v1(identity)
    except CanonicalExperimentIdentityError as exc:
        raise ExperimentMemoryValidationError(
            f"experiment_identity is not a valid Phase 1 Canonical Experiment Identity: {exc}"
        ) from exc
    return identity


def _require_sha256(field_name: str, value: Any) -> str:
    if not isinstance(value, str) or not is_valid_sha256_hex(value):
        raise ExperimentMemoryValidationError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


def _require_created_at(value: Any) -> str:
    if not isinstance(value, str) or not _CREATED_AT_RE.fullmatch(value):
        raise ExperimentMemoryValidationError(
            "created_at must be an explicit UTC timestamp ending with Z"
        )
    return value


def _require_enum(field_name: str, value: Any, allowed: Sequence[str]) -> str:
    if not isinstance(value, str) or value not in allowed:
        raise ExperimentMemoryValidationError(f"{field_name} is not a canonical value")
    return value


def _require_disposition(value: Any) -> str:
    disposition = _require_enum("disposition", value, CANONICAL_DISPOSITIONS)
    lowered = disposition.lower()
    if "live" in lowered or "authoriz" in lowered:
        raise ExperimentMemoryValidationError("disposition cannot authorize live")
    return disposition


def _require_token(field_name: str, value: Any, pattern: re.Pattern[str]) -> str:
    if not isinstance(value, str) or not pattern.fullmatch(value):
        raise ExperimentMemoryValidationError(f"{field_name} is missing or malformed")
    if value.strip().lower() in _UNAVAILABLE_TOKENS:
        raise ExperimentMemoryValidationError(
            f"{field_name} cannot use implicit unavailable tokens"
        )
    return value


def _require_rejection_reason(disposition: Any, reason: Any) -> str | None:
    disposition_text = str(disposition or "")
    if disposition_text in _REJECTION_DISPOSITIONS_REQUIRING_REASON:
        if not isinstance(reason, str) or not reason.strip():
            raise ExperimentMemoryValidationError(
                "rejection_reason is required for rejected or retest dispositions"
            )
        if reason.strip().lower() in _UNAVAILABLE_TOKENS:
            raise ExperimentMemoryValidationError(
                "rejection_reason cannot use implicit unavailable tokens"
            )
        return reason.strip()
    if reason is None:
        return None
    if not isinstance(reason, str) or not reason.strip():
        raise ExperimentMemoryValidationError("rejection_reason must be a non-empty string or null")
    return reason.strip()


def _optional_experiment_id(field_name: str, value: Any, experiment_id: str) -> str | None:
    if value is None:
        return None
    digest = _require_sha256(field_name, value)
    if digest == experiment_id:
        raise ExperimentMemoryValidationError(f"{field_name} cannot equal experiment_id")
    return digest


def _lineage_block(
    *,
    experiment_id: str,
    parent_experiment: Any,
    ancestors: Any,
) -> dict[str, Any]:
    if parent_experiment is None:
        if ancestors not in (None, (), []):
            raise ExperimentMemoryValidationError("ROOT lineage cannot declare ancestors")
        return {
            "ancestors": [],
            "kind": LINEAGE_KIND_ROOT,
            "parent_experiment": None,
        }
    parent_id = _require_sha256("parent_experiment", parent_experiment)
    if parent_id == experiment_id:
        raise ExperimentMemoryValidationError("self-parent lineage is forbidden")
    ancestor_ids: list[str]
    if ancestors is None:
        ancestor_ids = [parent_id]
    else:
        if not isinstance(ancestors, Sequence) or isinstance(ancestors, (str, bytes)):
            raise ExperimentMemoryValidationError("lineage.ancestors must be a sequence")
        ancestor_ids = [_require_sha256("lineage.ancestors[]", item) for item in ancestors]
        if not ancestor_ids or ancestor_ids[0] != parent_id:
            raise ExperimentMemoryValidationError(
                "lineage.ancestors must start with parent_experiment"
            )
    if experiment_id in ancestor_ids:
        raise ExperimentMemoryValidationError("direct cyclic lineage is forbidden")
    if len(set(ancestor_ids)) != len(ancestor_ids):
        raise ExperimentMemoryValidationError("lineage.ancestors must be unique")
    return {
        "ancestors": ancestor_ids,
        "kind": LINEAGE_KIND_PARENT_BOUND,
        "parent_experiment": parent_id,
    }


def _bound_ref(field_name: str, value: Any, identity: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ExperimentMemoryValidationError(f"{field_name} must be a mapping")
    kind = value.get("kind")
    if kind != REF_KIND_IDENTITY_DIGEST_BOUND:
        raise ExperimentMemoryValidationError(f"{field_name}.kind must be IDENTITY_DIGEST_BOUND")
    digest_field = dict(_IDENTITY_REF_BINDINGS)[field_name]
    expected_digest = _require_sha256(digest_field, identity.get(digest_field))
    provided = _require_sha256(f"{field_name}.digest", value.get("digest"))
    if provided != expected_digest:
        raise ExperimentMemoryValidationError(
            f"{field_name}.digest must match experiment_identity.{digest_field}"
        )
    extra_keys = set(str(key) for key in value.keys()) - {"kind", "digest"}
    if extra_keys:
        raise ExperimentMemoryValidationError(
            f"{field_name} has unsupported keys: {sorted(extra_keys)}"
        )
    return {"digest": expected_digest, "kind": REF_KIND_IDENTITY_DIGEST_BOUND}


def _canonicalize_numeric_tree(field_name: str, value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ExperimentMemoryValidationError(f"{field_name} must be a mapping")
    try:
        return canonicalize_mapping(value, path=f"$.{field_name}")
    except CanonicalExperimentIdentityError as exc:
        message = str(exc)
        if "non-finite float" in message:
            raise ExperimentMemoryValidationError(
                f"non-finite numeric values are forbidden in {field_name}"
            ) from exc
        raise ExperimentMemoryValidationError(
            f"{field_name} is not canonically serializable: {exc}"
        ) from exc


def _canonicalize_artifacts(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ExperimentMemoryValidationError("artifacts must be a sequence")
    artifacts: list[dict[str, Any]] = []
    seen_refs: set[tuple[str, str]] = set()
    for index, item in enumerate(value):
        if not isinstance(item, Mapping):
            raise ExperimentMemoryValidationError(f"artifacts[{index}] must be a mapping")
        kind = _require_enum(f"artifacts[{index}].kind", item.get("kind"), ARTIFACT_KINDS)
        ref = _require_relative_artifact_ref(f"artifacts[{index}].ref", item.get("ref"))
        digest = _require_sha256(f"artifacts[{index}].digest", item.get("digest"))
        media_type = item.get("media_type")
        if media_type is not None:
            if not isinstance(media_type, str) or not media_type.strip() or "/" not in media_type:
                raise ExperimentMemoryValidationError(
                    f"artifacts[{index}].media_type must be a MIME type or null"
                )
            media_type = media_type.strip()
        extra_keys = set(str(key) for key in item.keys()) - {"kind", "ref", "digest", "media_type"}
        if extra_keys:
            raise ExperimentMemoryValidationError(
                f"artifacts[{index}] has unsupported keys: {sorted(extra_keys)}"
            )
        key = (kind, ref)
        if key in seen_refs:
            raise ExperimentMemoryValidationError("duplicate artifact refs are forbidden")
        seen_refs.add(key)
        artifact = {"digest": digest, "kind": kind, "ref": ref}
        if media_type is not None:
            artifact["media_type"] = media_type
        artifacts.append(artifact)
    return artifacts


def _require_relative_artifact_ref(field_name: str, value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ExperimentMemoryValidationError(f"{field_name} must be a non-empty relative ref")
    ref = value.strip()
    if ref.strip().lower() in _UNAVAILABLE_TOKENS:
        raise ExperimentMemoryValidationError(
            f"{field_name} cannot use implicit unavailable tokens"
        )
    if "\x00" in ref:
        raise ExperimentMemoryValidationError(f"{field_name} contains a NUL byte")
    if ref.startswith("/") or ref.startswith("\\") or ref.startswith("~"):
        raise ExperimentMemoryValidationError(f"{field_name} absolute or home paths are forbidden")
    if ":" in ref.split("/", 1)[0] and len(ref.split("/", 1)[0]) <= 2:
        raise ExperimentMemoryValidationError(f"{field_name} drive-qualified paths are forbidden")
    parts = ref.replace("\\", "/").split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise ExperimentMemoryValidationError(
            f"{field_name} path traversal or empty segments are forbidden"
        )
    if "\\" in ref:
        raise ExperimentMemoryValidationError(
            f"{field_name} must use store-/repo-relative POSIX paths"
        )
    return ref


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({str(key): _freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return [_freeze(item) for item in value]
    return value


def _plain_mapping(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _plain_mapping(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_plain_mapping(item) for item in value]
    return value


__all__ = [
    "ARTIFACT_KIND_REPO_RELATIVE",
    "ARTIFACT_KIND_STORE_RELATIVE",
    "ArtifactReferenceV1",
    "CANONICAL_DISPOSITIONS",
    "CANDIDATE_ROLES",
    "COMPARISON_STATUSES",
    "CanonicalExperimentMemoryRecordRequestV1",
    "DIGEST_ALGORITHM",
    "EXPERIMENT_MEMORY_CAN_MUTATE_LIVE_CONFIG",
    "EXPERIMENT_MEMORY_CAN_PROMOTE",
    "EXPERIMENT_MEMORY_HAS_RUNTIME_AUTHORITY",
    "ExperimentMemoryValidationError",
    "ExperimentRecordConflictError",
    "LINEAGE_KIND_PARENT_BOUND",
    "LINEAGE_KIND_ROOT",
    "LineageReferenceV1",
    "MEMORY_DOMAIN",
    "RECORD_COMPLETENESS_COMPLETE",
    "REF_KIND_IDENTITY_DIGEST_BOUND",
    "RUNTIME_AUTHORITY_IMPACT",
    "SCHEMA_VERSION",
    "build_canonical_experiment_memory_record_v1",
    "canonical_record_payload",
    "derive_experiment_id_v1",
    "freeze_canonical_experiment_memory_record_v1",
    "validate_canonical_experiment_memory_record_v1",
]
