"""Offline LEVEL_3 promotion input binding from completion+validity binding v1."""

from __future__ import annotations

import hashlib
import shutil
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from scripts.ops.primary_evidence_retention_v0 import (
    is_under_tmp,
    verify_manifest_sha256,
    write_manifest_sha256,
)
from src.meta.learning_loop.comparison_common_durable_evidence_binding_v1 import (
    COMPARISON_AUTHORITY_INVARIANTS,
)
from src.meta.learning_loop.comparison_completion_research_validity_binding_v1 import (
    ARTIFACT_REL as UPSTREAM_ARTIFACT_REL,
    CONTRACT_NAME as UPSTREAM_CONTRACT_NAME,
    CONTRACT_VERSION as UPSTREAM_CONTRACT_VERSION,
    PRODUCER_VERSION as UPSTREAM_PRODUCER_VERSION,
    SELF_VERIFICATION_REL as UPSTREAM_SELF_VERIFICATION_REL,
    ComparisonCompletionResearchValidityBindingError,
    reverify_comparison_completion_research_validity_binding_v1,
)
from src.meta.learning_loop.comparison_ssot_v1.io import read_manifest
from src.meta.learning_loop.contract_safety_v1 import (
    compute_content_sha256,
    deterministic_json_dumps,
    is_valid_sha256_hex,
)

CONTRACT_NAME = "comparison_completion_promotion_input_binding_v1"
CONTRACT_VERSION = "v1"
PRODUCER_VERSION = "comparison_completion_promotion_input_binding_v1"
EVIDENCE_LEVEL = "LEVEL_3"
AUTHORITY_LEVEL = "NON_AUTHORITIZING_EVIDENCE_ONLY"
RECORD_KIND = "comparison_completion_promotion_input_binding_record"
INPUT_RELATION = "BINDS_VERIFIED_COMPLETION_VALIDITY_BINDING_V1"
ARTIFACT_REL = "comparison_completion_promotion_input_binding_v1.json"
SELF_VERIFICATION_REL = "SELF_VERIFICATION.json"
MANIFEST_FILENAME = "MANIFEST.sha256"
STAGING_DIRNAME_PREFIX = ".comparison_completion_promotion_input_binding_staging_"

OFFLINE_DETERMINISTIC_CREATED_AT = "1970-01-01T00:00:00+00:00"

_VALID_BINDING_STATUS = frozenset({"PASS", "FAIL", "INCOMPLETE", "NOT_EVALUABLE"})
_CANDIDATE_IDENTITY_NOT_BOUND = "NOT_BOUND"
_WINNER_SELECTION_NOT_SELECTED = "NOT_SELECTED"

PROMOTION_INPUT_AUTHORITY_INVARIANTS: dict[str, bool] = {
    **COMPARISON_AUTHORITY_INVARIANTS,
    "promotion_input_is_descriptive_only": True,
    "promotion_input_does_not_select": True,
    "promotion_input_does_not_accept": True,
    "promotion_input_does_not_choose_winner": True,
    "promotion_input_does_not_authorize_promotion": True,
    "promotion_input_does_not_execute_eligibility": True,
    "promotion_input_does_not_execute_policy": True,
    "promotion_input_does_not_create_configpatch": True,
    "promotion_input_does_not_modify_config": True,
    "promotion_input_does_not_deploy": True,
    "promotion_input_does_not_activate": True,
    "promotion_input_does_not_create_order_intent": True,
    "promotion_input_does_not_modify_trading_logic": True,
    "promotion_input_does_not_authorize_runtime": True,
    "evidence_does_not_authorize_promotion": True,
}

_REQUIRED_NON_AUTHORIZING_FLAGS: dict[str, bool] = {
    "is_comparison_completion_promotion_input_binding": True,
    "evidence_does_not_authorize_promotion": True,
    "evidence_does_not_authorize_runtime": True,
    "promotion_input_does_not_select": True,
    "promotion_input_does_not_accept": True,
    "promotion_input_does_not_choose_winner": True,
    "promotion_input_does_not_authorize_promotion": True,
    "promotion_input_does_not_execute_eligibility": True,
    "promotion_input_does_not_execute_policy": True,
    "promotion_input_does_not_create_configpatch": True,
    "promotion_input_does_not_modify_config": True,
    "promotion_input_does_not_deploy": True,
    "promotion_input_does_not_activate": True,
    "promotion_input_does_not_create_order_intent": True,
    "promotion_input_does_not_modify_trading_logic": True,
    "promotion_input_does_not_authorize_runtime": True,
}

_FORBIDDEN_CAPABILITIES: frozenset[str] = frozenset(
    {
        "CAN_PROMOTE_ARTIFACT",
        "CAN_DEPLOY_INACTIVE",
        "CAN_COMPUTE_SIGNALS",
        "CAN_CREATE_ORDER_INTENTS",
        "CAN_SUBMIT_TESTNET_ORDERS",
        "CAN_SUBMIT_LIVE_ORDERS",
        "CAN_INCREASE_CAPITAL",
        "CAN_CHANGE_RISK_POLICY",
    }
)

_FORBIDDEN_INDEX_KEYS: frozenset[str] = frozenset(
    {
        "winner",
        "selected",
        "promoted",
        "promotion",
        "promotion_ready",
        "promotion_authorized",
        "promotion_decision",
        "eligible_for_live",
        "runtime_authorized",
        "live_authorized",
        "orders_allowed",
        "ranking",
        "pareto",
        "accepted",
        "acceptance",
        "armed",
        "enabled",
        "returns",
        "positions",
        "orders",
        "credentials",
        "strategy_params_mutated",
        "config_patch",
        "configpatch",
        "config_patch_manifest",
        "candidate_lineage_manifest",
        "patches",
    }
)

_SELF_VERIFICATION_SCHEMA_VERSION = (
    "comparison_completion_promotion_input_binding_self_verification_v1"
)


class ComparisonCompletionPromotionInputBindingError(ValueError):
    """Fail-closed promotion input binding error."""


@dataclass(frozen=True)
class VerifiedUpstreamBindingBundle:
    bundle_dir: Path
    contract_name: str
    contract_version: str
    producer_version: str
    artifact_ref: str
    artifact_digest: str
    manifest_digest: str
    evidence_level: str
    parent_artifact_refs: tuple[dict[str, Any], ...]
    evidence_payload: dict[str, Any]


@dataclass(frozen=True)
class ComparisonCompletionPromotionInputBindingInputs:
    completion_validity_binding_bundle_dir: Path


@dataclass(frozen=True)
class ComparisonCompletionPromotionInputBindingResult:
    output_dir: Path
    comparison_definition_id: str
    artifact_id: str
    evidence_path: Path
    self_verification_path: Path
    manifest_path: Path
    promotion_input_binding_status: str
    shared_lineage_status: str


def _reject_symlink(path: Path, *, label: str) -> None:
    if path.is_symlink():
        raise ComparisonCompletionPromotionInputBindingError(
            f"{label} must not be a symlink: {path}"
        )


def _reject_forbidden_index_keys(payload: Mapping[str, Any]) -> None:
    for key in payload:
        if key in _FORBIDDEN_INDEX_KEYS:
            raise ComparisonCompletionPromotionInputBindingError(
                f"promotion input binding artifact must not contain forbidden key: {key}"
            )


def _validate_regular_file(path: Path, *, label: str) -> None:
    if not path.exists():
        raise ComparisonCompletionPromotionInputBindingError(f"{label} not found: {path}")
    _reject_symlink(path, label=label)
    if not path.is_file():
        raise ComparisonCompletionPromotionInputBindingError(
            f"{label} must be a regular file: {path}"
        )


def _validate_bundle_dir(bundle_dir: Path, *, label: str) -> None:
    if not bundle_dir.is_dir():
        raise ComparisonCompletionPromotionInputBindingError(
            f"{label} must be a directory: {bundle_dir}"
        )
    _reject_symlink(bundle_dir, label=label)


def _validate_output_target(output_dir: Path) -> None:
    if output_dir.exists():
        raise ComparisonCompletionPromotionInputBindingError(
            f"output directory already exists (fail-closed): {output_dir}"
        )
    if is_under_tmp(output_dir):
        raise ComparisonCompletionPromotionInputBindingError(
            "output directory must be outside /tmp"
        )
    parent = output_dir.parent
    if not parent.is_dir():
        raise ComparisonCompletionPromotionInputBindingError(
            f"output parent directory missing: {parent}"
        )
    if is_under_tmp(parent):
        raise ComparisonCompletionPromotionInputBindingError(
            "output parent directory must be outside /tmp"
        )


def _path_is_under(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def _reject_unsafe_overlap(*, upstream_bundle_dir: Path, output_dir: Path) -> None:
    output_res = output_dir.resolve()
    upstream_res = upstream_bundle_dir.resolve()
    if output_res == upstream_res:
        raise ComparisonCompletionPromotionInputBindingError(
            "output directory must not equal upstream binding bundle path (fail-closed)"
        )
    if _path_is_under(upstream_res, output_res):
        raise ComparisonCompletionPromotionInputBindingError(
            "upstream binding bundle must not be inside output directory (fail-closed)"
        )
    if _path_is_under(output_res, upstream_res):
        raise ComparisonCompletionPromotionInputBindingError(
            "output directory must not be inside upstream binding bundle path (fail-closed)"
        )


def _manifest_file_digest(bundle_dir: Path) -> str:
    manifest_path = bundle_dir / MANIFEST_FILENAME
    _validate_regular_file(manifest_path, label=MANIFEST_FILENAME)
    return hashlib.sha256(manifest_path.read_bytes()).hexdigest()


def _artifact_digest_from_evidence(evidence: Mapping[str, Any]) -> str:
    stored = evidence.get("output_digest")
    if isinstance(stored, str) and is_valid_sha256_hex(stored):
        return stored
    integrity = evidence.get("integrity")
    if isinstance(integrity, Mapping):
        digest = integrity.get("content_sha256")
        if isinstance(digest, str) and is_valid_sha256_hex(digest):
            return digest
    raise ComparisonCompletionPromotionInputBindingError("evidence digest missing or invalid")


def _validate_capabilities(capabilities: Any) -> list[str]:
    if not isinstance(capabilities, list):
        raise ComparisonCompletionPromotionInputBindingError("capabilities must be a list")
    normalized: list[str] = []
    for idx, item in enumerate(capabilities):
        if not isinstance(item, str) or not item.strip():
            raise ComparisonCompletionPromotionInputBindingError(
                f"capabilities[{idx}] must be a non-empty string"
            )
        if item in _FORBIDDEN_CAPABILITIES:
            raise ComparisonCompletionPromotionInputBindingError(
                f"forbidden capability present: {item}"
            )
        normalized.append(item)
    return normalized


def _validate_non_authorizing_flags(payload: Mapping[str, Any]) -> None:
    for key, expected in _REQUIRED_NON_AUTHORIZING_FLAGS.items():
        if payload.get(key) is not expected:
            raise ComparisonCompletionPromotionInputBindingError(
                f"{key} must be {expected!r} (fail-closed)"
            )
    if payload.get("evidence_level") != EVIDENCE_LEVEL:
        raise ComparisonCompletionPromotionInputBindingError(
            f"evidence_level must be {EVIDENCE_LEVEL!r} (fail-closed)"
        )


def _normalize_parent_refs(value: Any, *, label: str) -> tuple[dict[str, Any], ...]:
    if not isinstance(value, list):
        raise ComparisonCompletionPromotionInputBindingError(
            f"{label} parent_artifact_refs must be a list"
        )
    refs: list[dict[str, Any]] = []
    for idx, item in enumerate(value):
        if not isinstance(item, Mapping):
            raise ComparisonCompletionPromotionInputBindingError(
                f"{label} parent_artifact_refs[{idx}] must be an object"
            )
        refs.append(dict(item))
    return tuple(refs)


def _load_self_verification(bundle_dir: Path, *, rel: str, label: str) -> dict[str, Any]:
    path = bundle_dir / rel
    _validate_regular_file(path, label=label)
    payload = read_manifest(path)
    if payload.get("overall_status") != "PASS":
        raise ComparisonCompletionPromotionInputBindingError(f"{label} overall_status must be PASS")
    return payload


def _validate_upstream_binding_payload(payload: Mapping[str, Any]) -> None:
    if payload.get("contract_name") != UPSTREAM_CONTRACT_NAME:
        raise ComparisonCompletionPromotionInputBindingError("upstream contract_name mismatch")
    if payload.get("contract_version") != UPSTREAM_CONTRACT_VERSION:
        raise ComparisonCompletionPromotionInputBindingError(
            "upstream contract_version not supported"
        )
    if payload.get("producer_version") != UPSTREAM_PRODUCER_VERSION:
        raise ComparisonCompletionPromotionInputBindingError("upstream producer_version mismatch")
    if payload.get("evidence_level") != EVIDENCE_LEVEL:
        raise ComparisonCompletionPromotionInputBindingError(
            "upstream evidence_level must be LEVEL_3"
        )
    if payload.get("is_completion_research_validity_binding") is not True:
        raise ComparisonCompletionPromotionInputBindingError(
            "is_completion_research_validity_binding must be true"
        )
    for flag in (
        "evidence_does_not_authorize_promotion",
        "evidence_does_not_authorize_runtime",
        "binding_does_not_select",
        "binding_does_not_accept",
        "binding_does_not_promote",
        "binding_does_not_deploy",
        "binding_does_not_activate",
        "binding_does_not_create_order_intent",
        "binding_does_not_modify_trading_logic",
        "binding_does_not_authorize_runtime",
    ):
        if payload.get(flag) is not True:
            raise ComparisonCompletionPromotionInputBindingError(f"upstream {flag} must be true")
    _validate_capabilities(payload.get("capabilities"))

    binding_status = payload.get("binding_status")
    if binding_status not in _VALID_BINDING_STATUS:
        raise ComparisonCompletionPromotionInputBindingError(
            "upstream binding_status missing or invalid"
        )

    required_lineage = (
        "completion_evidence_digest",
        "research_validity_digest",
        "comparison_checkpoint_ref",
        "comparison_checkpoint_digest",
        "experiment_identity_ref",
        "experiment_identity_digest",
        "dataset_identity_ref",
        "dataset_identity_digest",
        "comparison_definition_id",
    )
    for field in required_lineage:
        value = payload.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ComparisonCompletionPromotionInputBindingError(
                f"upstream {field} missing or invalid"
            )
    if not is_valid_sha256_hex(str(payload["experiment_identity_digest"])):
        raise ComparisonCompletionPromotionInputBindingError(
            "upstream experiment_identity_digest invalid"
        )
    if not is_valid_sha256_hex(str(payload["dataset_identity_digest"])):
        raise ComparisonCompletionPromotionInputBindingError(
            "upstream dataset_identity_digest invalid"
        )


def verify_upstream_binding_bundle(bundle_dir: Path | str) -> VerifiedUpstreamBindingBundle:
    """Fail-closed verification of exactly one completion+validity binding bundle."""
    path = Path(bundle_dir)
    _validate_bundle_dir(path, label="completion validity binding bundle")
    try:
        reverify_comparison_completion_research_validity_binding_v1(output_dir=path)
    except ComparisonCompletionResearchValidityBindingError as exc:
        raise ComparisonCompletionPromotionInputBindingError(str(exc)) from exc

    evidence_path = path / UPSTREAM_ARTIFACT_REL
    if not evidence_path.is_file():
        raise ComparisonCompletionPromotionInputBindingError(
            f"upstream artifact not found: {UPSTREAM_ARTIFACT_REL}"
        )
    evidence = read_manifest(evidence_path)
    _validate_upstream_binding_payload(evidence)
    _load_self_verification(
        path, rel=UPSTREAM_SELF_VERIFICATION_REL, label="upstream SELF_VERIFICATION"
    )
    manifest_digest = _manifest_file_digest(path)
    return VerifiedUpstreamBindingBundle(
        bundle_dir=path.resolve(),
        contract_name=str(evidence["contract_name"]),
        contract_version=str(evidence["contract_version"]),
        producer_version=str(evidence["producer_version"]),
        artifact_ref=UPSTREAM_ARTIFACT_REL,
        artifact_digest=_artifact_digest_from_evidence(evidence),
        manifest_digest=manifest_digest,
        evidence_level=str(evidence["evidence_level"]),
        parent_artifact_refs=_normalize_parent_refs(
            evidence.get("parent_artifact_refs"), label="upstream"
        ),
        evidence_payload=dict(evidence),
    )


def _derive_promotion_input_binding_status(
    *,
    upstream_binding_status: str,
    shared_lineage_status: str,
) -> tuple[str, list[str]]:
    reason_codes: list[str] = []
    if shared_lineage_status != "PASS":
        return "FAIL", ["SHARED_LINEAGE_FAIL"]
    if upstream_binding_status not in _VALID_BINDING_STATUS:
        return "FAIL", ["UPSTREAM_BINDING_STATUS_UNKNOWN"]
    if upstream_binding_status == "FAIL":
        reason_codes.append("UPSTREAM_BINDING_FAIL")
        return "FAIL", reason_codes
    if upstream_binding_status == "INCOMPLETE":
        reason_codes.append("UPSTREAM_BINDING_INCOMPLETE")
        return "INCOMPLETE", reason_codes
    if upstream_binding_status == "NOT_EVALUABLE":
        reason_codes.append("UPSTREAM_BINDING_NOT_EVALUABLE")
        return "NOT_EVALUABLE", reason_codes
    reason_codes.extend(["UPSTREAM_BINDING_PASS", "TRANSITIVE_LINEAGE_BOUND"])
    return "PASS", reason_codes


def _input_artifact_ref_mapping(bundle: VerifiedUpstreamBindingBundle) -> dict[str, Any]:
    return {
        "artifact_type": bundle.contract_name,
        "contract_name": bundle.contract_name,
        "contract_version": bundle.contract_version,
        "artifact_ref": bundle.artifact_ref,
        "artifact_digest": bundle.artifact_digest,
        "manifest_digest": bundle.manifest_digest,
        "producer_version": bundle.producer_version,
        "bundle_path": bundle.bundle_dir.as_posix(),
    }


def _compute_output_digest(body: Mapping[str, Any]) -> str:
    excluded = frozenset(
        {"output_digest", "manifest_digest", "integrity", "created_at", "artifact_id"}
    )
    digest_body = {key: body[key] for key in sorted(body) if key not in excluded}
    return compute_content_sha256(digest_body)


def _integrity_body(body: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: value for key, value in body.items() if key not in {"integrity", "manifest_digest"}
    }


def _optional_ref(payload: Mapping[str, Any], key: str) -> str | None:
    value = payload.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        return None
    return value


def build_comparison_completion_promotion_input_binding_v1(
    *,
    upstream: VerifiedUpstreamBindingBundle,
) -> dict[str, Any]:
    upstream_payload = upstream.evidence_payload

    upstream_binding_status = str(upstream_payload.get("binding_status", ""))
    shared_lineage_status = str(upstream_payload.get("shared_lineage_status", ""))
    promotion_input_binding_status, promotion_input_binding_reason_codes = (
        _derive_promotion_input_binding_status(
            upstream_binding_status=upstream_binding_status,
            shared_lineage_status=shared_lineage_status,
        )
    )

    input_refs = [_input_artifact_ref_mapping(upstream)]
    parent_artifact_refs = list(upstream.parent_artifact_refs)
    parent_artifact_refs.sort(
        key=lambda item: (str(item.get("ref_type", "")), str(item.get("digest", "")))
    )

    payload: dict[str, Any] = {
        "contract_name": CONTRACT_NAME,
        "contract_version": CONTRACT_VERSION,
        "artifact_id": "",
        "created_at": OFFLINE_DETERMINISTIC_CREATED_AT,
        "producer_version": PRODUCER_VERSION,
        "record_kind": RECORD_KIND,
        "input_relation": INPUT_RELATION,
        "evidence_level": EVIDENCE_LEVEL,
        "authority_level": AUTHORITY_LEVEL,
        "capabilities": [],
        "is_comparison_completion_promotion_input_binding": True,
        "evidence_does_not_authorize_promotion": True,
        "evidence_does_not_authorize_runtime": True,
        "promotion_input_does_not_select": True,
        "promotion_input_does_not_accept": True,
        "promotion_input_does_not_choose_winner": True,
        "promotion_input_does_not_authorize_promotion": True,
        "promotion_input_does_not_execute_eligibility": True,
        "promotion_input_does_not_execute_policy": True,
        "promotion_input_does_not_create_configpatch": True,
        "promotion_input_does_not_modify_config": True,
        "promotion_input_does_not_deploy": True,
        "promotion_input_does_not_activate": True,
        "promotion_input_does_not_create_order_intent": True,
        "promotion_input_does_not_modify_trading_logic": True,
        "promotion_input_does_not_authorize_runtime": True,
        "promotion_input_authority_invariants": dict(PROMOTION_INPUT_AUTHORITY_INVARIANTS),
        "completion_validity_binding_bundle_ref": upstream.bundle_dir.as_posix(),
        "completion_validity_binding_artifact_ref": upstream.artifact_ref,
        "completion_validity_binding_digest": upstream.artifact_digest,
        "completion_validity_binding_manifest_digest": upstream.manifest_digest,
        "comparison_completion_ref": str(upstream_payload["completion_evidence_bundle_ref"]),
        "comparison_completion_digest": str(upstream_payload["completion_evidence_digest"]),
        "comparison_completion_manifest_digest": str(
            upstream_payload["completion_manifest_digest"]
        ),
        "research_validity_ref": str(upstream_payload["research_validity_bundle_ref"]),
        "research_validity_digest": str(upstream_payload["research_validity_digest"]),
        "research_validity_manifest_digest": str(
            upstream_payload["research_validity_manifest_digest"]
        ),
        "comparison_checkpoint_ref": str(upstream_payload["comparison_checkpoint_ref"]),
        "comparison_checkpoint_digest": str(upstream_payload["comparison_checkpoint_digest"]),
        "experiment_identity_ref": str(upstream_payload["experiment_identity_ref"]),
        "experiment_identity_digest": str(upstream_payload["experiment_identity_digest"]),
        "dataset_identity_ref": str(upstream_payload["dataset_identity_ref"]),
        "dataset_identity_digest": str(upstream_payload["dataset_identity_digest"]),
        "comparison_definition_ref": str(upstream_payload["comparison_definition_id"]),
        "comparison_definition_id": str(upstream_payload["comparison_definition_id"]),
        "candidate_identity_status": _CANDIDATE_IDENTITY_NOT_BOUND,
        "winner_selection_status": _WINNER_SELECTION_NOT_SELECTED,
        "shared_lineage_status": shared_lineage_status,
        "shared_lineage_reason_codes": list(
            upstream_payload.get("shared_lineage_reason_codes", [])
        ),
        "upstream_binding_status": upstream_binding_status,
        "upstream_binding_reason_codes": list(upstream_payload.get("binding_reason_codes", [])),
        "promotion_input_binding_status": promotion_input_binding_status,
        "promotion_input_binding_reason_codes": promotion_input_binding_reason_codes,
        "completion_status": str(upstream_payload.get("completion_status", "")),
        "research_validity_status": str(upstream_payload.get("research_validity_status", "")),
        "upstream_contract_name": upstream.contract_name,
        "upstream_contract_version": upstream.contract_version,
        "upstream_producer_version": upstream.producer_version,
        "input_artifact_refs": input_refs,
        "parent_artifact_refs": parent_artifact_refs,
        "input_digest": "",
        "output_digest": "",
        "manifest_digest": "",
    }

    metric_ref = _optional_ref(upstream_payload, "comparison_metric_input_ref")
    if metric_ref is not None:
        payload["comparison_metric_input_ref"] = metric_ref
        metric_digest = _optional_ref(upstream_payload, "comparison_metric_input_digest")
        if metric_digest is not None:
            payload["comparison_metric_input_digest"] = metric_digest

    selection_ref = _optional_ref(upstream_payload, "selection_procedure_ref")
    if selection_ref is not None:
        payload["selection_procedure_ref"] = selection_ref

    _reject_forbidden_index_keys(payload)
    _validate_non_authorizing_flags(payload)
    _validate_capabilities(payload["capabilities"])

    payload["input_digest"] = compute_content_sha256({"input_artifact_refs": input_refs})
    output_digest = _compute_output_digest(payload)
    payload["output_digest"] = output_digest
    payload["artifact_id"] = output_digest
    return payload


def serialize_comparison_completion_promotion_input_binding_v1(
    evidence: Mapping[str, Any],
) -> str:
    _reject_forbidden_index_keys(evidence)
    _validate_non_authorizing_flags(evidence)
    _validate_capabilities(evidence.get("capabilities"))
    binding_status = evidence.get("promotion_input_binding_status")
    if binding_status not in _VALID_BINDING_STATUS:
        raise ComparisonCompletionPromotionInputBindingError(
            f"promotion_input_binding_status must be one of {sorted(_VALID_BINDING_STATUS)}"
        )
    return deterministic_json_dumps(dict(evidence))


def _evidence_bytes_for_manifest_digest(evidence: Mapping[str, Any]) -> bytes:
    canonical = {
        key: value for key, value in evidence.items() if key not in {"integrity", "manifest_digest"}
    }
    return serialize_comparison_completion_promotion_input_binding_v1(canonical).encode("utf-8")


def _compute_output_manifest_digest(evidence: Mapping[str, Any]) -> str:
    return hashlib.sha256(_evidence_bytes_for_manifest_digest(evidence)).hexdigest()


def _validate_evidence_integrity(evidence: Mapping[str, Any]) -> None:
    if evidence.get("contract_name") != CONTRACT_NAME:
        raise ComparisonCompletionPromotionInputBindingError("contract_name mismatch")
    if evidence.get("contract_version") != CONTRACT_VERSION:
        raise ComparisonCompletionPromotionInputBindingError("contract_version mismatch")
    if evidence.get("producer_version") != PRODUCER_VERSION:
        raise ComparisonCompletionPromotionInputBindingError("producer_version mismatch")
    _validate_non_authorizing_flags(evidence)
    _validate_capabilities(evidence.get("capabilities"))
    invariants = evidence.get("promotion_input_authority_invariants")
    if invariants != PROMOTION_INPUT_AUTHORITY_INVARIANTS:
        raise ComparisonCompletionPromotionInputBindingError(
            "promotion_input_authority_invariants mismatch"
        )
    if evidence.get("candidate_identity_status") != _CANDIDATE_IDENTITY_NOT_BOUND:
        raise ComparisonCompletionPromotionInputBindingError(
            "candidate_identity_status must be NOT_BOUND"
        )
    if evidence.get("winner_selection_status") != _WINNER_SELECTION_NOT_SELECTED:
        raise ComparisonCompletionPromotionInputBindingError(
            "winner_selection_status must be NOT_SELECTED"
        )

    stored = evidence.get("integrity")
    if not isinstance(stored, Mapping):
        raise ComparisonCompletionPromotionInputBindingError("integrity must be an object")
    expected = compute_content_sha256(_integrity_body(evidence))
    actual = stored.get("content_sha256")
    if actual != expected:
        raise ComparisonCompletionPromotionInputBindingError(
            "promotion input binding evidence integrity mismatch"
        )

    output_digest = evidence.get("output_digest")
    if output_digest != _compute_output_digest(evidence):
        raise ComparisonCompletionPromotionInputBindingError("output_digest mismatch")
    if evidence.get("artifact_id") != output_digest:
        raise ComparisonCompletionPromotionInputBindingError("artifact_id must equal output_digest")


def build_self_verification_v1(
    *,
    evidence: Mapping[str, Any],
    upstream: VerifiedUpstreamBindingBundle,
    manifest_digest: str,
) -> dict[str, Any]:
    checks: list[dict[str, str]] = [
        {"check_id": "contract_name", "status": "PASS"},
        {"check_id": "contract_version", "status": "PASS"},
        {"check_id": "evidence_level_level_3", "status": "PASS"},
        {"check_id": "exactly_one_direct_input", "status": "PASS"},
        {"check_id": "upstream_contract_and_version", "status": "PASS"},
        {"check_id": "input_manifest_verified", "status": "PASS"},
        {"check_id": "input_self_verification_pass", "status": "PASS"},
        {"check_id": "upstream_binding_status", "status": "PASS"},
        {"check_id": "completion_lineage", "status": "PASS"},
        {"check_id": "research_validity_lineage", "status": "PASS"},
        {"check_id": "checkpoint_lineage", "status": "PASS"},
        {"check_id": "experiment_dataset_identity", "status": "PASS"},
        {"check_id": "candidate_identity_not_invented", "status": "PASS"},
        {"check_id": "winner_selection_not_claimed", "status": "PASS"},
        {"check_id": "required_fields", "status": "PASS"},
        {"check_id": "promotion_input_binding_status_present", "status": "PASS"},
        {"check_id": "non_authorizing_semantics", "status": "PASS"},
        {"check_id": "forbidden_capabilities_absent", "status": "PASS"},
        {"check_id": "no_configpatch_semantics", "status": "PASS"},
        {"check_id": "canonical_serialization", "status": "PASS"},
        {"check_id": "output_digest", "status": "PASS"},
        {"check_id": "manifest_verification", "status": "PASS"},
        {"check_id": "deterministic_reverification", "status": "PASS"},
    ]

    input_refs = evidence.get("input_artifact_refs")
    if not isinstance(input_refs, list) or len(input_refs) != 1:
        checks = [
            {**c, "status": "FAIL"} if c["check_id"] == "exactly_one_direct_input" else c
            for c in checks
        ]

    if evidence.get("manifest_digest") != manifest_digest:
        checks = [
            {**c, "status": "FAIL"} if c["check_id"] == "manifest_verification" else c
            for c in checks
        ]

    if evidence.get("completion_validity_binding_bundle_ref") != upstream.bundle_dir.as_posix():
        checks = [
            {**c, "status": "FAIL"} if c["check_id"] == "input_manifest_verified" else c
            for c in checks
        ]

    if any(check["status"] != "PASS" for check in checks):
        raise ComparisonCompletionPromotionInputBindingError("self-verification checks failed")

    payload: dict[str, Any] = {
        "self_verification_schema_version": _SELF_VERIFICATION_SCHEMA_VERSION,
        "contract_name": CONTRACT_NAME,
        "contract_version": CONTRACT_VERSION,
        "overall_status": "PASS",
        "checks": checks,
        "verified_artifact_rel": ARTIFACT_REL,
        "verified_output_digest": evidence.get("output_digest"),
        "verified_manifest_digest": manifest_digest,
    }
    digest = compute_content_sha256(payload)
    payload["integrity"] = {"content_sha256": digest}
    return payload


def _finalize_evidence_with_manifest_digest(
    evidence: Mapping[str, Any], *, manifest_digest: str
) -> dict[str, Any]:
    body = dict(evidence)
    body["manifest_digest"] = manifest_digest
    body["output_digest"] = _compute_output_digest(body)
    body["artifact_id"] = body["output_digest"]
    body["integrity"] = {"content_sha256": compute_content_sha256(_integrity_body(body))}
    return body


def _staging_dir_for(output_dir: Path) -> Path:
    return output_dir.parent / f"{STAGING_DIRNAME_PREFIX}{uuid.uuid4().hex}"


def _cleanup_staging(staging: Path) -> None:
    if staging.exists():
        shutil.rmtree(staging)


def verify_binding_inputs(
    inputs: ComparisonCompletionPromotionInputBindingInputs,
) -> VerifiedUpstreamBindingBundle:
    """Verify exactly one completion+validity binding bundle."""
    return verify_upstream_binding_bundle(inputs.completion_validity_binding_bundle_dir)


def reverify_comparison_completion_promotion_input_binding_v1(
    *,
    output_dir: Path | str,
) -> None:
    """Replay promotion input binding bundle without producer or upstream mutation."""
    bundle_dir = Path(output_dir)
    if not bundle_dir.is_dir():
        raise ComparisonCompletionPromotionInputBindingError(
            f"promotion input binding directory not found: {bundle_dir}"
        )
    ok, msg = verify_manifest_sha256(bundle_dir)
    if not ok:
        raise ComparisonCompletionPromotionInputBindingError(
            f"MANIFEST.sha256 verification failed: {msg}"
        )

    evidence_path = bundle_dir / ARTIFACT_REL
    _validate_regular_file(evidence_path, label=ARTIFACT_REL)
    evidence = read_manifest(evidence_path)
    _validate_evidence_integrity(evidence)

    self_path = bundle_dir / SELF_VERIFICATION_REL
    _validate_regular_file(self_path, label=SELF_VERIFICATION_REL)
    self_payload = read_manifest(self_path)
    if self_payload.get("overall_status") != "PASS":
        raise ComparisonCompletionPromotionInputBindingError(
            "SELF_VERIFICATION overall_status must be PASS"
        )

    manifest_digest = _compute_output_manifest_digest(evidence)
    if evidence.get("manifest_digest") != manifest_digest:
        raise ComparisonCompletionPromotionInputBindingError("manifest_digest mismatch on replay")

    upstream_dir = Path(str(evidence["completion_validity_binding_bundle_ref"]))
    upstream = verify_upstream_binding_bundle(upstream_dir)

    if evidence.get("completion_validity_binding_digest") != upstream.artifact_digest:
        raise ComparisonCompletionPromotionInputBindingError(
            "completion_validity_binding_digest mismatch on replay"
        )
    if evidence.get("upstream_binding_status") != upstream.evidence_payload.get("binding_status"):
        raise ComparisonCompletionPromotionInputBindingError(
            "upstream_binding_status mismatch on replay"
        )


def produce_comparison_completion_promotion_input_binding_v1(
    *,
    inputs: ComparisonCompletionPromotionInputBindingInputs,
    output_dir: Path | str,
) -> ComparisonCompletionPromotionInputBindingResult:
    """Bind exactly one verified completion+validity binding bundle to promotion input evidence."""
    final_dir = Path(output_dir)
    _validate_output_target(final_dir)
    _reject_unsafe_overlap(
        upstream_bundle_dir=inputs.completion_validity_binding_bundle_dir,
        output_dir=final_dir,
    )

    upstream = verify_binding_inputs(inputs)
    evidence_body = build_comparison_completion_promotion_input_binding_v1(upstream=upstream)

    staging = _staging_dir_for(final_dir)
    if staging.exists():
        raise ComparisonCompletionPromotionInputBindingError(
            f"staging directory collision: {staging}"
        )

    try:
        staging.mkdir(parents=True, exist_ok=False)
        evidence_path = staging / ARTIFACT_REL
        self_path = staging / SELF_VERIFICATION_REL

        manifest_digest = _compute_output_manifest_digest(evidence_body)
        finalized = _finalize_evidence_with_manifest_digest(
            evidence_body, manifest_digest=manifest_digest
        )
        evidence_path.write_text(
            serialize_comparison_completion_promotion_input_binding_v1(finalized),
            encoding="utf-8",
        )
        self_payload = build_self_verification_v1(
            evidence=finalized,
            upstream=upstream,
            manifest_digest=manifest_digest,
        )
        self_path.write_text(deterministic_json_dumps(self_payload), encoding="utf-8")
        write_manifest_sha256(staging)

        ok, msg = verify_manifest_sha256(staging)
        if not ok:
            raise ComparisonCompletionPromotionInputBindingError(
                f"MANIFEST.sha256 verification failed before publish: {msg}"
            )

        reverify_comparison_completion_promotion_input_binding_v1(output_dir=staging)
        staging.replace(final_dir)

        ok, msg = verify_manifest_sha256(final_dir)
        if not ok:
            raise ComparisonCompletionPromotionInputBindingError(
                f"MANIFEST.sha256 verification failed after publish: {msg}"
            )
    except Exception:
        _cleanup_staging(staging)
        if final_dir.exists():
            shutil.rmtree(final_dir)
        raise

    artifact_id = str(finalized["artifact_id"])
    return ComparisonCompletionPromotionInputBindingResult(
        output_dir=final_dir,
        comparison_definition_id=str(finalized["comparison_definition_id"]),
        artifact_id=artifact_id,
        evidence_path=final_dir / ARTIFACT_REL,
        self_verification_path=final_dir / SELF_VERIFICATION_REL,
        manifest_path=final_dir / MANIFEST_FILENAME,
        promotion_input_binding_status=str(finalized["promotion_input_binding_status"]),
        shared_lineage_status=str(finalized["shared_lineage_status"]),
    )


__all__ = [
    "ARTIFACT_REL",
    "AUTHORITY_LEVEL",
    "CONTRACT_NAME",
    "CONTRACT_VERSION",
    "EVIDENCE_LEVEL",
    "MANIFEST_FILENAME",
    "PRODUCER_VERSION",
    "PROMOTION_INPUT_AUTHORITY_INVARIANTS",
    "SELF_VERIFICATION_REL",
    "ComparisonCompletionPromotionInputBindingError",
    "ComparisonCompletionPromotionInputBindingInputs",
    "ComparisonCompletionPromotionInputBindingResult",
    "VerifiedUpstreamBindingBundle",
    "build_comparison_completion_promotion_input_binding_v1",
    "build_self_verification_v1",
    "produce_comparison_completion_promotion_input_binding_v1",
    "reverify_comparison_completion_promotion_input_binding_v1",
    "serialize_comparison_completion_promotion_input_binding_v1",
    "verify_binding_inputs",
    "verify_upstream_binding_bundle",
]
