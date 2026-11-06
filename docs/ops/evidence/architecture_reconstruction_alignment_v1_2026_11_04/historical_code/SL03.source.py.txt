"""Phase 3 Canonical Failure Memory v1 (research evidence only).

Append-only historical memory of rejected research hypotheses. This layer
reuses Phase 1 Canonical Experiment Identity and Phase 2 rejection
dispositions. It has no runtime, order, live, funding, canary, promotion,
or config-write authority.

Duplicate detection is fingerprint-based, not free text. A duplicate is a
warning / annotation / deprioritization signal. It is never an automatic
research ban.
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
from src.experiments.canonical_experiment_memory_v1 import (
    ARTIFACT_KIND_REPO_RELATIVE,
    ARTIFACT_KIND_STORE_RELATIVE,
    CANONICAL_DISPOSITIONS,
    derive_experiment_id_v1,
)
from src.meta.learning_loop.contract_safety_v1 import (
    compute_content_sha256,
    is_valid_sha256_hex,
)

SCHEMA_VERSION: Final[str] = "canonical_failure_memory_v1"
FAILURE_DOMAIN: Final[str] = "peak_trade.canonical_failure_memory.v1"
DIGEST_ALGORITHM: Final[str] = "sha256"
RECORD_COMPLETENESS_COMPLETE: Final[str] = "COMPLETE"
EVIDENCE_KIND_EXPERIMENT_RECORD: Final[str] = "EXPERIMENT_RECORD"
ARTIFACT_KIND_REPO_RELATIVE_REF: Final[str] = ARTIFACT_KIND_REPO_RELATIVE
ARTIFACT_KIND_STORE_RELATIVE_REF: Final[str] = ARTIFACT_KIND_STORE_RELATIVE

FAILURE_MEMORY_HAS_RUNTIME_AUTHORITY: Final[bool] = False
FAILURE_MEMORY_CAN_MUTATE_LIVE_CONFIG: Final[bool] = False
FAILURE_MEMORY_CAN_PROMOTE: Final[bool] = False
FAILURE_MEMORY_AUTOMATIC_RESEARCH_BAN: Final[bool] = False
DUPLICATE_DETECTED_IS_NOT_AUTOMATIC_RESEARCH_BAN: Final[bool] = True
RUNTIME_AUTHORITY_IMPACT: Final[str] = "NONE"

CANONICAL_FAILURE_CLASSES: Final[tuple[str, ...]] = tuple(
    disposition for disposition in CANONICAL_DISPOSITIONS if disposition.startswith("REJECTED_")
)
CANONICAL_REJECTION_REASONS: Final[tuple[str, ...]] = CANONICAL_FAILURE_CLASSES
FAILURE_CLASS_TO_FAILED_GATE: Final[Mapping[str, str]] = MappingProxyType(
    {
        "REJECTED_DATA_QUALITY": "DATA_QUALITY_GATE",
        "REJECTED_REPRODUCIBILITY": "REPRODUCIBILITY_GATE",
        "REJECTED_OVERFIT": "OVERFIT_GATE",
        "REJECTED_COST_SENSITIVITY": "COST_SENSITIVITY_GATE",
        "REJECTED_TAIL_RISK": "TAIL_RISK_GATE",
        "REJECTED_REGIME_CONCENTRATION": "REGIME_CONCENTRATION_GATE",
        "REJECTED_COMPARABILITY": "COMPARABILITY_GATE",
        "REJECTED_REALITY_GAP": "REALITY_GAP_GATE",
        "REJECTED_POLICY": "POLICY_GATE",
    }
)
CANONICAL_FAILED_GATES: Final[tuple[str, ...]] = tuple(FAILURE_CLASS_TO_FAILED_GATE.values())
DUPLICATE_ACTIONS: Final[tuple[str, ...]] = (
    "NONE",
    "WARN",
    "ANNOTATE",
    "PRIORITIZE",
    "DEPRIORITIZE",
    "REQUIRE_EXPLICIT_RETEST_REASON",
)

_CREATED_AT_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,9})?Z$")
_HYPOTHESIS_ID_RE = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
_REGIME_RE = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
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
_EVIDENCE_KINDS: Final[tuple[str, ...]] = (
    EVIDENCE_KIND_EXPERIMENT_RECORD,
    ARTIFACT_KIND_REPO_RELATIVE_REF,
    ARTIFACT_KIND_STORE_RELATIVE_REF,
)

_LOGGER = logging.getLogger(__name__)


class FailureMemoryValidationError(ValueError):
    """Fail-closed Canonical Failure Memory v1 validation error."""


class FailureRecordConflictError(FailureMemoryValidationError):
    """Same failure_record_id with divergent canonical historical content."""


@dataclass(frozen=True)
class CanonicalFailureMemoryRecordRequestV1:
    experiment_identity: Mapping[str, Any]
    hypothesis_id: str
    failure_class: str
    failed_gate: str
    rejection_reason: str
    regime: str
    parameter_region: Mapping[str, Any]
    cost_sensitivity: Mapping[str, Any]
    instability_indicators: Mapping[str, Any]
    evidence_refs: Sequence[Mapping[str, Any]]
    created_at: str
    robustness_policy_digest: str
    hypothesis_fingerprint: str | None = None
    experiment_id: str | None = None
    retest_reason: str | None = None


def derive_hypothesis_fingerprint_v1(
    *,
    identity_digest: str,
    hypothesis_id: str,
    parameter_region: Mapping[str, Any],
    regime: str,
    robustness_policy_digest: str,
    parent_lineage_ref: str | None,
) -> str:
    identity = _require_sha256("identity_digest", identity_digest)
    robustness = _require_sha256("robustness_policy_digest", robustness_policy_digest)
    envelope = {
        "digest_algorithm": DIGEST_ALGORITHM,
        "digest_domain": f"{FAILURE_DOMAIN}.hypothesis_fingerprint",
        "payload": {
            "hypothesis_id": _require_token("hypothesis_id", hypothesis_id, _HYPOTHESIS_ID_RE),
            "identity_digest": identity,
            "parameter_region": _canonicalize_numeric_tree("parameter_region", parameter_region),
            "parent_lineage_ref": parent_lineage_ref,
            "regime": _require_token("regime", regime, _REGIME_RE),
            "robustness_policy_digest": robustness,
        },
        "schema_version": SCHEMA_VERSION,
    }
    return compute_content_sha256(envelope)


def derive_failure_record_id_v1(record_without_ids: Mapping[str, Any]) -> str:
    envelope = {
        "digest_algorithm": DIGEST_ALGORITHM,
        "digest_domain": f"{FAILURE_DOMAIN}.failure_record_id",
        "payload": _plain_mapping(record_without_ids),
        "schema_version": SCHEMA_VERSION,
    }
    return compute_content_sha256(envelope)


def build_canonical_failure_memory_record_v1(
    request: CanonicalFailureMemoryRecordRequestV1,
) -> Mapping[str, Any]:
    identity = _require_identity(request.experiment_identity)
    experiment_id = derive_experiment_id_v1(str(identity["identity_digest"]))
    if request.experiment_id is not None:
        provided = _require_sha256("experiment_id", request.experiment_id)
        if provided != experiment_id:
            raise FailureMemoryValidationError(
                "experiment_id is not bound to the Canonical Experiment Identity digest"
            )
    parent_lineage_ref = None
    parent_lineage = identity.get("parent_lineage")
    if isinstance(parent_lineage, Mapping):
        parent_lineage_ref = parent_lineage.get("parent_lineage_ref")
    fingerprint = derive_hypothesis_fingerprint_v1(
        identity_digest=str(identity["identity_digest"]),
        hypothesis_id=request.hypothesis_id,
        parameter_region=request.parameter_region,
        regime=request.regime,
        robustness_policy_digest=request.robustness_policy_digest,
        parent_lineage_ref=parent_lineage_ref if isinstance(parent_lineage_ref, str) else None,
    )
    if request.hypothesis_fingerprint is not None:
        provided_fp = _require_sha256("hypothesis_fingerprint", request.hypothesis_fingerprint)
        if provided_fp != fingerprint:
            raise FailureMemoryValidationError(
                "hypothesis_fingerprint does not match the canonical derived fingerprint"
            )
    failure_class = _require_failure_class(request.failure_class)
    rejection_reason = _require_rejection_reason(request.rejection_reason, failure_class)
    failed_gate = _require_failed_gate(request.failed_gate, failure_class)
    created_at = _require_created_at(request.created_at)
    dataset_digest = _require_sha256("dataset_digest", identity.get("dataset_digest"))
    evidence_refs = _canonicalize_evidence_refs(request.evidence_refs, experiment_id)
    parameter_region = _canonicalize_numeric_tree("parameter_region", request.parameter_region)
    body = {
        "canonical_trading_decision_core_bound": True,
        "completeness": RECORD_COMPLETENESS_COMPLETE,
        "cost_sensitivity": _canonicalize_numeric_tree(
            "cost_sensitivity", request.cost_sensitivity
        ),
        "created_at": created_at,
        "dataset_digest": dataset_digest,
        "digest_algorithm": DIGEST_ALGORITHM,
        "duplicate_detected_is_not_automatic_research_ban": (
            DUPLICATE_DETECTED_IS_NOT_AUTOMATIC_RESEARCH_BAN
        ),
        "evidence_refs": evidence_refs,
        "experiment_id": experiment_id,
        "experiment_identity": identity,
        "failed_gate": failed_gate,
        "failure_class": failure_class,
        "failure_domain": FAILURE_DOMAIN,
        "failure_memory_automatic_research_ban": FAILURE_MEMORY_AUTOMATIC_RESEARCH_BAN,
        "failure_memory_can_mutate_live_config": FAILURE_MEMORY_CAN_MUTATE_LIVE_CONFIG,
        "failure_memory_can_promote": FAILURE_MEMORY_CAN_PROMOTE,
        "failure_memory_has_runtime_authority": FAILURE_MEMORY_HAS_RUNTIME_AUTHORITY,
        "hypothesis_fingerprint": fingerprint,
        "hypothesis_id": _require_token("hypothesis_id", request.hypothesis_id, _HYPOTHESIS_ID_RE),
        "instability_indicators": _canonicalize_numeric_tree(
            "instability_indicators", request.instability_indicators
        ),
        "parameter_region": parameter_region,
        "record_schema_version": SCHEMA_VERSION,
        "regime": _require_token("regime", request.regime, _REGIME_RE),
        "rejection_reason": rejection_reason,
        "retest_reason": _optional_retest_reason(request.retest_reason),
        "robustness_policy_digest": _require_sha256(
            "robustness_policy_digest", request.robustness_policy_digest
        ),
        "runtime_authority_impact": RUNTIME_AUTHORITY_IMPACT,
    }
    failure_record_id = derive_failure_record_id_v1(body)
    record = dict(body)
    record["failure_record_id"] = failure_record_id
    record["integrity"] = {
        "content_sha256": compute_content_sha256(
            {key: value for key, value in record.items() if key != "integrity"}
        )
    }
    validate_canonical_failure_memory_record_v1(record)
    frozen = _freeze(record)
    _LOGGER.info(
        "canonical_failure_memory_v1 built failure_record_id=%s fingerprint=%s "
        "failure_class=%s runtime_authority=%s automatic_ban=%s",
        record["failure_record_id"],
        record["hypothesis_fingerprint"],
        record["failure_class"],
        record["failure_memory_has_runtime_authority"],
        record["failure_memory_automatic_research_ban"],
    )
    return frozen


def validate_canonical_failure_memory_record_v1(record: Mapping[str, Any]) -> None:
    if not isinstance(record, Mapping):
        raise FailureMemoryValidationError("failure record must be a mapping")
    record = _plain_mapping(record)
    if record.get("record_schema_version") != SCHEMA_VERSION:
        raise FailureMemoryValidationError("record_schema_version mismatch")
    if record.get("failure_domain") != FAILURE_DOMAIN:
        raise FailureMemoryValidationError("failure_domain mismatch")
    if record.get("completeness") != RECORD_COMPLETENESS_COMPLETE:
        raise FailureMemoryValidationError("non-COMPLETE failure records are forbidden")
    if record.get("digest_algorithm") != DIGEST_ALGORITHM:
        raise FailureMemoryValidationError("digest_algorithm mismatch")
    if record.get("failure_memory_has_runtime_authority") is not False:
        raise FailureMemoryValidationError("failure_memory_has_runtime_authority must be false")
    if record.get("failure_memory_can_mutate_live_config") is not False:
        raise FailureMemoryValidationError("failure_memory_can_mutate_live_config must be false")
    if record.get("failure_memory_can_promote") is not False:
        raise FailureMemoryValidationError("failure_memory_can_promote must be false")
    if record.get("failure_memory_automatic_research_ban") is not False:
        raise FailureMemoryValidationError("failure_memory_automatic_research_ban must be false")
    if record.get("duplicate_detected_is_not_automatic_research_ban") is not True:
        raise FailureMemoryValidationError(
            "duplicate_detected_is_not_automatic_research_ban must be true"
        )
    if record.get("runtime_authority_impact") != RUNTIME_AUTHORITY_IMPACT:
        raise FailureMemoryValidationError("runtime_authority_impact must be NONE")
    if record.get("canonical_trading_decision_core_bound") is not True:
        raise FailureMemoryValidationError("canonical_trading_decision_core_bound must be true")

    identity = _require_identity(record.get("experiment_identity"))
    experiment_id = _require_sha256("experiment_id", record.get("experiment_id"))
    expected_id = derive_experiment_id_v1(str(identity["identity_digest"]))
    if experiment_id != expected_id:
        raise FailureMemoryValidationError(
            "experiment_id is not bound to the Canonical Experiment Identity digest"
        )
    dataset_digest = _require_sha256("dataset_digest", record.get("dataset_digest"))
    if dataset_digest != identity.get("dataset_digest"):
        raise FailureMemoryValidationError(
            "dataset_digest must match experiment_identity.dataset_digest"
        )
    failure_class = _require_failure_class(record.get("failure_class"))
    _require_rejection_reason(record.get("rejection_reason"), failure_class)
    _require_failed_gate(record.get("failed_gate"), failure_class)
    _require_created_at(record.get("created_at"))
    _require_token("hypothesis_id", record.get("hypothesis_id"), _HYPOTHESIS_ID_RE)
    _require_token("regime", record.get("regime"), _REGIME_RE)
    _require_sha256("robustness_policy_digest", record.get("robustness_policy_digest"))
    _optional_retest_reason(record.get("retest_reason"))
    _canonicalize_numeric_tree("parameter_region", record.get("parameter_region"))
    _canonicalize_numeric_tree("cost_sensitivity", record.get("cost_sensitivity"))
    _canonicalize_numeric_tree("instability_indicators", record.get("instability_indicators"))
    _canonicalize_evidence_refs(record.get("evidence_refs"), experiment_id)
    for field_name in _CORE_LOGIC_DIGEST_FIELDS:
        _require_sha256(field_name, identity.get(field_name))

    parent_lineage_ref = None
    parent_lineage = identity.get("parent_lineage")
    if isinstance(parent_lineage, Mapping):
        parent_lineage_ref = parent_lineage.get("parent_lineage_ref")
    expected_fp = derive_hypothesis_fingerprint_v1(
        identity_digest=str(identity["identity_digest"]),
        hypothesis_id=str(record.get("hypothesis_id")),
        parameter_region=record.get("parameter_region") or {},
        regime=str(record.get("regime")),
        robustness_policy_digest=str(record.get("robustness_policy_digest")),
        parent_lineage_ref=parent_lineage_ref if isinstance(parent_lineage_ref, str) else None,
    )
    if record.get("hypothesis_fingerprint") != expected_fp:
        raise FailureMemoryValidationError("hypothesis_fingerprint is not canonically derived")

    body = {
        key: value for key, value in record.items() if key not in {"failure_record_id", "integrity"}
    }
    expected_record_id = derive_failure_record_id_v1(body)
    if record.get("failure_record_id") != expected_record_id:
        raise FailureMemoryValidationError("failure_record_id is not bound to canonical content")
    expected_integrity = compute_content_sha256(
        {key: value for key, value in record.items() if key != "integrity"}
    )
    integrity = record.get("integrity")
    if not isinstance(integrity, Mapping) or integrity.get("content_sha256") != expected_integrity:
        raise FailureMemoryValidationError("integrity.content_sha256 mismatch")


def assess_duplicate_hypothesis_v1(
    existing_records: Sequence[Mapping[str, Any]],
    *,
    hypothesis_fingerprint: str,
    failure_class: str | None = None,
    parameter_region: Mapping[str, Any] | None = None,
) -> Mapping[str, Any]:
    fingerprint = _require_sha256("hypothesis_fingerprint", hypothesis_fingerprint)
    matches: list[dict[str, Any]] = []
    for item in existing_records:
        validate_canonical_failure_memory_record_v1(item)
        payload = _plain_mapping(item)
        if payload.get("hypothesis_fingerprint") != fingerprint:
            continue
        matches.append(payload)
    previously_rejected = bool(matches)
    same_failure_mode = False
    if failure_class is not None:
        canonical_class = _require_failure_class(failure_class)
        same_failure_mode = any(item.get("failure_class") == canonical_class for item in matches)
    same_parameter_region = False
    if parameter_region is not None:
        canonical_region = _canonicalize_numeric_tree("parameter_region", parameter_region)
        same_parameter_region = (
            sum(1 for item in matches if item.get("parameter_region") == canonical_region) >= 1
        )
    repeatedly_unstable = False
    if parameter_region is not None:
        canonical_region = _canonicalize_numeric_tree("parameter_region", parameter_region)
        region_hits = [
            item
            for item in matches
            if item.get("parameter_region") == canonical_region
            and _has_instability(item.get("instability_indicators"))
        ]
        repeatedly_unstable = len(region_hits) >= 2
    actions: list[str] = []
    if previously_rejected:
        actions.extend(("WARN", "ANNOTATE", "REQUIRE_EXPLICIT_RETEST_REASON"))
    if same_failure_mode:
        actions.append("ANNOTATE")
    if repeatedly_unstable:
        actions.append("DEPRIORITIZE")
    ordered_actions = tuple(action for action in DUPLICATE_ACTIONS if action in set(actions))
    detected = bool(matches)
    assessment = {
        "actions": list(ordered_actions) if detected else ["NONE"],
        "automatic_research_ban": False,
        "detected": detected,
        "duplicate_detected_is_not_automatic_research_ban": True,
        "failure_memory_has_runtime_authority": False,
        "hypothesis_fingerprint": fingerprint,
        "matching_failure_record_ids": [item["failure_record_id"] for item in matches],
        "matching_record_count": len(matches),
        "previously_rejected": previously_rejected,
        "same_failure_mode_known": same_failure_mode,
        "same_parameter_region_repeatedly_unstable": repeatedly_unstable,
        "same_parameter_region_seen": same_parameter_region,
    }
    return _freeze(assessment)


def canonical_record_payload(record: Mapping[str, Any]) -> dict[str, Any]:
    return _plain_mapping(record)


def freeze_canonical_failure_memory_record_v1(record: Mapping[str, Any]) -> Mapping[str, Any]:
    validate_canonical_failure_memory_record_v1(record)
    return _freeze(canonical_record_payload(record))


def _require_identity(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise FailureMemoryValidationError("experiment_identity present and valid is required")
    identity = _plain_mapping(value)
    try:
        validate_canonical_experiment_identity_v1(identity)
    except CanonicalExperimentIdentityError as exc:
        raise FailureMemoryValidationError(
            f"experiment_identity is not a valid Phase 1 Canonical Experiment Identity: {exc}"
        ) from exc
    return identity


def _require_sha256(field_name: str, value: Any) -> str:
    if not isinstance(value, str) or not is_valid_sha256_hex(value):
        raise FailureMemoryValidationError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


def _require_created_at(value: Any) -> str:
    if not isinstance(value, str) or not _CREATED_AT_RE.fullmatch(value):
        raise FailureMemoryValidationError(
            "created_at must be an explicit UTC timestamp ending with Z"
        )
    return value


def _require_token(field_name: str, value: Any, pattern: re.Pattern[str]) -> str:
    if not isinstance(value, str) or not pattern.fullmatch(value):
        raise FailureMemoryValidationError(f"{field_name} is missing or malformed")
    if value.strip().lower() in _UNAVAILABLE_TOKENS:
        raise FailureMemoryValidationError(f"{field_name} cannot use implicit unavailable tokens")
    return value


def _require_failure_class(value: Any) -> str:
    if not isinstance(value, str) or value not in CANONICAL_FAILURE_CLASSES:
        raise FailureMemoryValidationError("failure_class is unknown or unsupported")
    return value


def _require_rejection_reason(value: Any, failure_class: str) -> str:
    if not isinstance(value, str) or value not in CANONICAL_REJECTION_REASONS:
        raise FailureMemoryValidationError("rejection_reason is not a canonical rejection token")
    if value != failure_class:
        raise FailureMemoryValidationError(
            "rejection_reason must equal failure_class for Canonical Failure Memory v1"
        )
    return value


def _require_failed_gate(value: Any, failure_class: str) -> str:
    expected = FAILURE_CLASS_TO_FAILED_GATE[failure_class]
    if not isinstance(value, str) or value not in CANONICAL_FAILED_GATES:
        raise FailureMemoryValidationError("failed_gate is unknown or unsupported")
    if value != expected:
        raise FailureMemoryValidationError(
            f"failed_gate {value} is inconsistent with failure_class {failure_class}"
        )
    return value


def _optional_retest_reason(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise FailureMemoryValidationError("retest_reason must be a non-empty string or null")
    if value.strip().lower() in _UNAVAILABLE_TOKENS:
        raise FailureMemoryValidationError("retest_reason cannot use implicit unavailable tokens")
    return value.strip()


def _canonicalize_numeric_tree(field_name: str, value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise FailureMemoryValidationError(f"{field_name} must be a mapping")
    try:
        return canonicalize_mapping(value, path=f"$.{field_name}")
    except CanonicalExperimentIdentityError as exc:
        message = str(exc)
        if "non-finite float" in message:
            raise FailureMemoryValidationError(
                f"non-finite numeric values are forbidden in {field_name}"
            ) from exc
        raise FailureMemoryValidationError(
            f"{field_name} is not canonically serializable: {exc}"
        ) from exc


def _canonicalize_evidence_refs(value: Any, experiment_id: str) -> list[dict[str, Any]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise FailureMemoryValidationError("evidence_refs must be a sequence")
    refs: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    experiment_bound = False
    for index, item in enumerate(value):
        if not isinstance(item, Mapping):
            raise FailureMemoryValidationError(f"evidence_refs[{index}] must be a mapping")
        kind = item.get("kind")
        if kind not in _EVIDENCE_KINDS:
            raise FailureMemoryValidationError(f"evidence_refs[{index}].kind is unsupported")
        digest = _require_sha256(f"evidence_refs[{index}].digest", item.get("digest"))
        if kind == EVIDENCE_KIND_EXPERIMENT_RECORD:
            ref = _require_sha256(f"evidence_refs[{index}].ref", item.get("ref"))
            if ref == experiment_id:
                experiment_bound = True
        else:
            ref = _require_relative_artifact_ref(f"evidence_refs[{index}].ref", item.get("ref"))
        extra_keys = set(str(key) for key in item.keys()) - {"kind", "ref", "digest"}
        if extra_keys:
            raise FailureMemoryValidationError(
                f"evidence_refs[{index}] has unsupported keys: {sorted(extra_keys)}"
            )
        key = (str(kind), ref)
        if key in seen:
            raise FailureMemoryValidationError("duplicate evidence_refs are forbidden")
        seen.add(key)
        refs.append({"digest": digest, "kind": kind, "ref": ref})
    if not experiment_bound:
        raise FailureMemoryValidationError(
            "evidence_refs must include the bound EXPERIMENT_RECORD experiment_id"
        )
    return refs


def _require_relative_artifact_ref(field_name: str, value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise FailureMemoryValidationError(f"{field_name} must be a non-empty relative ref")
    ref = value.strip()
    if ref.strip().lower() in _UNAVAILABLE_TOKENS:
        raise FailureMemoryValidationError(f"{field_name} cannot use implicit unavailable tokens")
    if "\x00" in ref:
        raise FailureMemoryValidationError(f"{field_name} contains a NUL byte")
    if ref.startswith("/") or ref.startswith("\\") or ref.startswith("~"):
        raise FailureMemoryValidationError(f"{field_name} absolute or home paths are forbidden")
    if ":" in ref.split("/", 1)[0] and len(ref.split("/", 1)[0]) <= 2:
        raise FailureMemoryValidationError(f"{field_name} drive-qualified paths are forbidden")
    parts = ref.replace("\\", "/").split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise FailureMemoryValidationError(
            f"{field_name} path traversal or empty segments are forbidden"
        )
    if "\\" in ref:
        raise FailureMemoryValidationError(
            f"{field_name} must use store-/repo-relative POSIX paths"
        )
    return ref


def _has_instability(value: Any) -> bool:
    if not isinstance(value, Mapping):
        return False
    payload = _plain_mapping(value)
    if payload.get("unstable") is True:
        return True
    repeated = payload.get("repeated_instability")
    return repeated is True or repeated == 1


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
    "CANONICAL_FAILED_GATES",
    "CANONICAL_FAILURE_CLASSES",
    "CANONICAL_REJECTION_REASONS",
    "CanonicalFailureMemoryRecordRequestV1",
    "DIGEST_ALGORITHM",
    "DUPLICATE_ACTIONS",
    "DUPLICATE_DETECTED_IS_NOT_AUTOMATIC_RESEARCH_BAN",
    "EVIDENCE_KIND_EXPERIMENT_RECORD",
    "FAILURE_CLASS_TO_FAILED_GATE",
    "FAILURE_DOMAIN",
    "FAILURE_MEMORY_AUTOMATIC_RESEARCH_BAN",
    "FAILURE_MEMORY_CAN_MUTATE_LIVE_CONFIG",
    "FAILURE_MEMORY_CAN_PROMOTE",
    "FAILURE_MEMORY_HAS_RUNTIME_AUTHORITY",
    "FailureMemoryValidationError",
    "FailureRecordConflictError",
    "RECORD_COMPLETENESS_COMPLETE",
    "RUNTIME_AUTHORITY_IMPACT",
    "SCHEMA_VERSION",
    "assess_duplicate_hypothesis_v1",
    "build_canonical_failure_memory_record_v1",
    "canonical_record_payload",
    "derive_failure_record_id_v1",
    "derive_hypothesis_fingerprint_v1",
    "freeze_canonical_failure_memory_record_v1",
    "validate_canonical_failure_memory_record_v1",
]
