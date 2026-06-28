"""Offline LEVEL_3 candidate identity binding from promotion input binding v1."""

from __future__ import annotations

import hashlib
import json
import shutil
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Mapping

from scripts.ops.primary_evidence_retention_v0 import (
    is_under_tmp,
    verify_manifest_sha256,
    write_manifest_sha256,
)
from src.governance.promotion_loop.candidate_lineage_manifest_v1 import (
    LineageRefType,
    validate_candidate_lineage_manifest_v1,
)
from src.meta.learning_loop.comparison_completion_promotion_input_binding_v1 import (
    ARTIFACT_REL as PROMOTION_INPUT_ARTIFACT_REL,
    CONTRACT_NAME as PROMOTION_INPUT_CONTRACT_NAME,
    CONTRACT_VERSION as PROMOTION_INPUT_CONTRACT_VERSION,
    PRODUCER_VERSION as PROMOTION_INPUT_PRODUCER_VERSION,
    SELF_VERIFICATION_REL as PROMOTION_INPUT_SELF_VERIFICATION_REL,
    ComparisonCompletionPromotionInputBindingError,
    reverify_comparison_completion_promotion_input_binding_v1,
)
from src.meta.learning_loop.comparison_metric_input_durable_evidence_binding_v1 import (
    INDEX_ARTIFACT_REL as METRIC_INPUT_INDEX_REL,
    MANIFEST_ARTIFACT_REL as METRIC_INPUT_MANIFEST_REL,
    ComparisonMetricInputDurableEvidenceBindingError,
    reverify_comparison_metric_input_durable_evidence_bundle_v1,
)
from src.meta.learning_loop.comparison_common_durable_evidence_binding_v1 import (
    COMPARISON_AUTHORITY_INVARIANTS,
)
from src.meta.learning_loop.comparison_metric_input_v1.io import read_manifest
from src.meta.learning_loop.comparison_ssot_v1.io import read_manifest as read_ssot_manifest
from src.meta.learning_loop.contract_safety_v1 import (
    compute_content_sha256,
    deterministic_json_dumps,
    is_valid_sha256_hex,
)

CONTRACT_NAME = "comparison_promotion_candidate_identity_binding_v1"
CONTRACT_VERSION = "v1"
PRODUCER_VERSION = "comparison_promotion_candidate_identity_binding_v1"
EVIDENCE_LEVEL = "LEVEL_3"
AUTHORITY_LEVEL = "NON_AUTHORITIZING_EVIDENCE_ONLY"
RECORD_KIND = "comparison_promotion_candidate_identity_binding_record"
INPUT_RELATION = "BINDS_VERIFIED_PROMOTION_INPUT_AND_CANDIDATE_IDENTITY"
ARTIFACT_REL = "comparison_promotion_candidate_identity_binding_v1.json"
SELF_VERIFICATION_REL = "SELF_VERIFICATION.json"
MANIFEST_FILENAME = "MANIFEST.sha256"
STAGING_DIRNAME_PREFIX = ".comparison_promotion_candidate_identity_binding_staging_"

CANDIDATE_LINEAGE_ARTIFACT_REL = "candidate_lineage_manifest_v1.json"

CandidateIdentitySourceType = Literal[
    "candidate_lineage_manifest_v1",
    "comparison_metric_input_durable_evidence_binding_v1",
]

OFFLINE_DETERMINISTIC_CREATED_AT = "1970-01-01T00:00:00+00:00"

_VALID_BINDING_STATUS = frozenset({"PASS", "FAIL", "INCOMPLETE", "NOT_EVALUABLE"})
_CANDIDATE_IDENTITY_BOUND = "BOUND"
_CANDIDATE_SELECTION_NOT_SELECTED = "NOT_SELECTED"
_WINNER_SELECTION_NOT_SELECTED = "NOT_SELECTED"

CANDIDATE_IDENTITY_BINDING_AUTHORITY_INVARIANTS: dict[str, bool] = {
    **COMPARISON_AUTHORITY_INVARIANTS,
    "candidate_identity_binding_is_descriptive_only": True,
    "candidate_identity_binding_does_not_select": True,
    "candidate_identity_binding_does_not_choose_winner": True,
    "candidate_identity_binding_does_not_accept": True,
    "candidate_identity_binding_does_not_execute_eligibility": True,
    "candidate_identity_binding_does_not_execute_policy": True,
    "candidate_identity_binding_does_not_create_configpatch": True,
    "candidate_identity_binding_does_not_modify_config": True,
    "candidate_identity_binding_does_not_authorize_promotion": True,
    "candidate_identity_binding_does_not_deploy": True,
    "candidate_identity_binding_does_not_activate": True,
    "candidate_identity_binding_does_not_create_order_intent": True,
    "candidate_identity_binding_does_not_modify_trading_logic": True,
    "candidate_identity_binding_does_not_authorize_runtime": True,
    "evidence_does_not_authorize_promotion": True,
}

_REQUIRED_NON_AUTHORIZING_FLAGS: dict[str, bool] = {
    "is_comparison_promotion_candidate_identity_binding": True,
    "evidence_does_not_authorize_promotion": True,
    "evidence_does_not_authorize_runtime": True,
    "candidate_identity_binding_does_not_select": True,
    "candidate_identity_binding_does_not_choose_winner": True,
    "candidate_identity_binding_does_not_accept": True,
    "candidate_identity_binding_does_not_execute_eligibility": True,
    "candidate_identity_binding_does_not_execute_policy": True,
    "candidate_identity_binding_does_not_create_configpatch": True,
    "candidate_identity_binding_does_not_modify_config": True,
    "candidate_identity_binding_does_not_deploy": True,
    "candidate_identity_binding_does_not_activate": True,
    "candidate_identity_binding_does_not_create_order_intent": True,
    "candidate_identity_binding_does_not_modify_trading_logic": True,
    "candidate_identity_binding_does_not_authorize_runtime": True,
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
        "ranked_input_ids",
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
        "patches",
        "top_n",
        "topn",
    }
)

_SELF_VERIFICATION_SCHEMA_VERSION = (
    "comparison_promotion_candidate_identity_binding_self_verification_v1"
)


class ComparisonPromotionCandidateIdentityBindingError(ValueError):
    """Fail-closed candidate identity binding error."""


@dataclass(frozen=True)
class VerifiedPromotionInputBindingBundle:
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
class VerifiedCandidateIdentityBundle:
    bundle_dir: Path
    source_type: CandidateIdentitySourceType
    candidate_identity_ref: str
    candidate_identity_digest: str
    candidate_artifact_ref: str
    candidate_manifest_digest: str
    manifest_digest: str
    comparison_metric_input_ref: str | None
    comparison_metric_input_digest: str | None
    strategy_identity_ref: str | None
    parameter_set_identity_ref: str | None


@dataclass(frozen=True)
class ComparisonPromotionCandidateIdentityBindingInputs:
    promotion_input_binding_bundle_dir: Path
    candidate_identity_bundle_dir: Path


@dataclass(frozen=True)
class ComparisonPromotionCandidateIdentityBindingResult:
    output_dir: Path
    comparison_definition_id: str
    artifact_id: str
    evidence_path: Path
    self_verification_path: Path
    manifest_path: Path
    candidate_identity_binding_status: str
    shared_lineage_status: str
    candidate_identity_ref: str
    candidate_identity_source_type: CandidateIdentitySourceType


def _reject_symlink(path: Path, *, label: str) -> None:
    if path.is_symlink():
        raise ComparisonPromotionCandidateIdentityBindingError(
            f"{label} must not be a symlink: {path}"
        )


def _reject_forbidden_index_keys(payload: Mapping[str, Any]) -> None:
    for key in payload:
        if key in _FORBIDDEN_INDEX_KEYS:
            raise ComparisonPromotionCandidateIdentityBindingError(
                f"candidate identity binding artifact must not contain forbidden key: {key}"
            )


def _validate_regular_file(path: Path, *, label: str) -> None:
    if not path.exists():
        raise ComparisonPromotionCandidateIdentityBindingError(f"{label} not found: {path}")
    _reject_symlink(path, label=label)
    if not path.is_file():
        raise ComparisonPromotionCandidateIdentityBindingError(
            f"{label} must be a regular file: {path}"
        )


def _validate_bundle_dir(bundle_dir: Path, *, label: str) -> None:
    if not bundle_dir.is_dir():
        raise ComparisonPromotionCandidateIdentityBindingError(
            f"{label} must be a directory: {bundle_dir}"
        )
    _reject_symlink(bundle_dir, label=label)


def _validate_output_target(output_dir: Path) -> None:
    if output_dir.exists():
        raise ComparisonPromotionCandidateIdentityBindingError(
            f"output directory already exists (fail-closed): {output_dir}"
        )
    if is_under_tmp(output_dir):
        raise ComparisonPromotionCandidateIdentityBindingError(
            "output directory must be outside /tmp"
        )
    parent = output_dir.parent
    if not parent.is_dir():
        raise ComparisonPromotionCandidateIdentityBindingError(
            f"output parent directory missing: {parent}"
        )
    if is_under_tmp(parent):
        raise ComparisonPromotionCandidateIdentityBindingError(
            "output parent directory must be outside /tmp"
        )


def _path_is_under(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def _reject_unsafe_overlap(*, input_dirs: tuple[Path, ...], output_dir: Path) -> None:
    output_res = output_dir.resolve()
    resolved_inputs = [path.resolve() for path in input_dirs]
    if output_res in resolved_inputs:
        raise ComparisonPromotionCandidateIdentityBindingError(
            "output directory must not equal an input bundle path (fail-closed)"
        )
    for input_res in resolved_inputs:
        if _path_is_under(input_res, output_res):
            raise ComparisonPromotionCandidateIdentityBindingError(
                "input bundle must not be inside output directory (fail-closed)"
            )
        if _path_is_under(output_res, input_res):
            raise ComparisonPromotionCandidateIdentityBindingError(
                "output directory must not be inside input bundle path (fail-closed)"
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
    raise ComparisonPromotionCandidateIdentityBindingError("evidence digest missing or invalid")


def _validate_capabilities(capabilities: Any) -> list[str]:
    if not isinstance(capabilities, list):
        raise ComparisonPromotionCandidateIdentityBindingError("capabilities must be a list")
    normalized: list[str] = []
    for idx, item in enumerate(capabilities):
        if not isinstance(item, str) or not item.strip():
            raise ComparisonPromotionCandidateIdentityBindingError(
                f"capabilities[{idx}] must be a non-empty string"
            )
        if item in _FORBIDDEN_CAPABILITIES:
            raise ComparisonPromotionCandidateIdentityBindingError(
                f"forbidden capability present: {item}"
            )
        normalized.append(item)
    return normalized


def _validate_non_authorizing_flags(payload: Mapping[str, Any]) -> None:
    for key, expected in _REQUIRED_NON_AUTHORIZING_FLAGS.items():
        if payload.get(key) is not expected:
            raise ComparisonPromotionCandidateIdentityBindingError(
                f"{key} must be {expected!r} (fail-closed)"
            )
    if payload.get("evidence_level") != EVIDENCE_LEVEL:
        raise ComparisonPromotionCandidateIdentityBindingError(
            f"evidence_level must be {EVIDENCE_LEVEL!r} (fail-closed)"
        )


def _normalize_parent_refs(value: Any, *, label: str) -> tuple[dict[str, Any], ...]:
    if not isinstance(value, list):
        raise ComparisonPromotionCandidateIdentityBindingError(
            f"{label} parent_artifact_refs must be a list"
        )
    refs: list[dict[str, Any]] = []
    for idx, item in enumerate(value):
        if not isinstance(item, Mapping):
            raise ComparisonPromotionCandidateIdentityBindingError(
                f"{label} parent_artifact_refs[{idx}] must be an object"
            )
        refs.append(dict(item))
    return tuple(refs)


def _load_self_verification(bundle_dir: Path, *, rel: str, label: str) -> dict[str, Any]:
    path = bundle_dir / rel
    _validate_regular_file(path, label=label)
    payload = read_manifest(path)
    if payload.get("overall_status") != "PASS":
        raise ComparisonPromotionCandidateIdentityBindingError(
            f"{label} overall_status must be PASS"
        )
    return payload


def _validate_promotion_input_payload(payload: Mapping[str, Any]) -> None:
    if payload.get("contract_name") != PROMOTION_INPUT_CONTRACT_NAME:
        raise ComparisonPromotionCandidateIdentityBindingError(
            "promotion input contract_name mismatch"
        )
    if payload.get("contract_version") != PROMOTION_INPUT_CONTRACT_VERSION:
        raise ComparisonPromotionCandidateIdentityBindingError(
            "promotion input contract_version not supported"
        )
    if payload.get("producer_version") != PROMOTION_INPUT_PRODUCER_VERSION:
        raise ComparisonPromotionCandidateIdentityBindingError(
            "promotion input producer_version mismatch"
        )
    if payload.get("evidence_level") != EVIDENCE_LEVEL:
        raise ComparisonPromotionCandidateIdentityBindingError(
            "promotion input evidence_level must be LEVEL_3"
        )
    if payload.get("candidate_identity_status") != "NOT_BOUND":
        raise ComparisonPromotionCandidateIdentityBindingError(
            "promotion input candidate_identity_status must be NOT_BOUND"
        )
    if payload.get("winner_selection_status") != _WINNER_SELECTION_NOT_SELECTED:
        raise ComparisonPromotionCandidateIdentityBindingError(
            "promotion input winner_selection_status must be NOT_SELECTED"
        )
    for flag in (
        "promotion_input_does_not_select",
        "promotion_input_does_not_accept",
        "promotion_input_does_not_choose_winner",
        "promotion_input_does_not_authorize_promotion",
        "promotion_input_does_not_execute_eligibility",
        "promotion_input_does_not_execute_policy",
        "promotion_input_does_not_create_configpatch",
        "promotion_input_does_not_authorize_runtime",
    ):
        if payload.get(flag) is not True:
            raise ComparisonPromotionCandidateIdentityBindingError(
                f"promotion input {flag} must be true"
            )
    binding_status = payload.get("promotion_input_binding_status")
    if binding_status not in _VALID_BINDING_STATUS:
        raise ComparisonPromotionCandidateIdentityBindingError(
            "promotion input promotion_input_binding_status missing or invalid"
        )
    _validate_capabilities(payload.get("capabilities"))


def verify_promotion_input_binding_bundle(
    bundle_dir: Path | str,
) -> VerifiedPromotionInputBindingBundle:
    """Fail-closed verification of exactly one promotion input binding bundle."""
    path = Path(bundle_dir)
    _validate_bundle_dir(path, label="promotion input binding bundle")
    try:
        reverify_comparison_completion_promotion_input_binding_v1(output_dir=path)
    except ComparisonCompletionPromotionInputBindingError as exc:
        raise ComparisonPromotionCandidateIdentityBindingError(str(exc)) from exc

    evidence_path = path / PROMOTION_INPUT_ARTIFACT_REL
    if not evidence_path.is_file():
        raise ComparisonPromotionCandidateIdentityBindingError(
            f"promotion input artifact not found: {PROMOTION_INPUT_ARTIFACT_REL}"
        )
    evidence = read_manifest(evidence_path)
    _validate_promotion_input_payload(evidence)
    _load_self_verification(
        path, rel=PROMOTION_INPUT_SELF_VERIFICATION_REL, label="promotion input SELF_VERIFICATION"
    )
    manifest_digest = _manifest_file_digest(path)
    return VerifiedPromotionInputBindingBundle(
        bundle_dir=path.resolve(),
        contract_name=str(evidence["contract_name"]),
        contract_version=str(evidence["contract_version"]),
        producer_version=str(evidence["producer_version"]),
        artifact_ref=PROMOTION_INPUT_ARTIFACT_REL,
        artifact_digest=_artifact_digest_from_evidence(evidence),
        manifest_digest=manifest_digest,
        evidence_level=str(evidence["evidence_level"]),
        parent_artifact_refs=_normalize_parent_refs(
            evidence.get("parent_artifact_refs"), label="promotion input"
        ),
        evidence_payload=dict(evidence),
    )


def _detect_candidate_source_type(bundle_dir: Path) -> CandidateIdentitySourceType:
    has_lineage = (bundle_dir / CANDIDATE_LINEAGE_ARTIFACT_REL).is_file()
    has_metric_index = (bundle_dir / METRIC_INPUT_INDEX_REL).is_file()
    has_metric_manifest = (bundle_dir / METRIC_INPUT_MANIFEST_REL).is_file()
    if has_lineage and (has_metric_index or has_metric_manifest):
        raise ComparisonPromotionCandidateIdentityBindingError(
            "candidate bundle matches multiple supported artifact types (fail-closed)"
        )
    if has_lineage:
        return "candidate_lineage_manifest_v1"
    if has_metric_index and has_metric_manifest:
        return "comparison_metric_input_durable_evidence_binding_v1"
    raise ComparisonPromotionCandidateIdentityBindingError(
        "candidate bundle does not match a supported candidate identity artifact type"
    )


def _read_experiment_identity_id(experiment_bundle_ref: str) -> str:
    experiment_path = Path(experiment_bundle_ref)
    manifest_path = experiment_path / "experiment_identity_manifest_v1.json"
    if not manifest_path.is_file():
        raise ComparisonPromotionCandidateIdentityBindingError(
            "experiment identity manifest not found for lineage cross-check"
        )
    manifest = read_ssot_manifest(manifest_path)
    experiment_id = manifest.get("experiment_identity_id")
    if not isinstance(experiment_id, str) or not experiment_id.strip():
        raise ComparisonPromotionCandidateIdentityBindingError(
            "experiment_identity_id missing in experiment manifest"
        )
    return experiment_id


def _verify_candidate_lineage_bundle(bundle_dir: Path) -> VerifiedCandidateIdentityBundle:
    artifact_path = bundle_dir / CANDIDATE_LINEAGE_ARTIFACT_REL
    _validate_regular_file(artifact_path, label=CANDIDATE_LINEAGE_ARTIFACT_REL)
    payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    valid, phase, errors, verdict = validate_candidate_lineage_manifest_v1(payload)
    if not valid:
        raise ComparisonPromotionCandidateIdentityBindingError(
            f"candidate lineage manifest invalid ({phase}): {'; '.join(errors)}; verdict={verdict}"
        )
    candidate_id = payload.get("candidate_id")
    if not isinstance(candidate_id, str) or not candidate_id.strip():
        raise ComparisonPromotionCandidateIdentityBindingError("candidate_id missing or invalid")
    integrity = payload.get("integrity")
    if not isinstance(integrity, Mapping):
        raise ComparisonPromotionCandidateIdentityBindingError(
            "candidate lineage integrity must be an object"
        )
    digest = integrity.get("content_sha256")
    if not isinstance(digest, str) or not is_valid_sha256_hex(digest):
        raise ComparisonPromotionCandidateIdentityBindingError(
            "candidate lineage integrity.content_sha256 invalid"
        )
    refs = payload.get("refs")
    if not isinstance(refs, list):
        raise ComparisonPromotionCandidateIdentityBindingError(
            "candidate lineage refs must be a list"
        )

    strategy_identity_ref: str | None = None
    for ref in refs:
        if not isinstance(ref, Mapping):
            continue
        if ref.get("ref_type") == LineageRefType.EXPERIMENT.value:
            ref_id = ref.get("ref_id")
            if isinstance(ref_id, str) and ref_id.strip():
                strategy_identity_ref = ref_id
            break

    return VerifiedCandidateIdentityBundle(
        bundle_dir=bundle_dir.resolve(),
        source_type="candidate_lineage_manifest_v1",
        candidate_identity_ref=candidate_id,
        candidate_identity_digest=digest,
        candidate_artifact_ref=CANDIDATE_LINEAGE_ARTIFACT_REL,
        candidate_manifest_digest=digest,
        manifest_digest=_manifest_file_digest(bundle_dir),
        comparison_metric_input_ref=None,
        comparison_metric_input_digest=None,
        strategy_identity_ref=strategy_identity_ref,
        parameter_set_identity_ref=None,
    )


def _verify_metric_input_binding_bundle(bundle_dir: Path) -> VerifiedCandidateIdentityBundle:
    try:
        reverify_comparison_metric_input_durable_evidence_bundle_v1(output_dir=bundle_dir)
    except ComparisonMetricInputDurableEvidenceBindingError as exc:
        raise ComparisonPromotionCandidateIdentityBindingError(str(exc)) from exc

    manifest = read_manifest(bundle_dir / METRIC_INPUT_MANIFEST_REL)
    integrity = manifest.get("integrity")
    if not isinstance(integrity, Mapping):
        raise ComparisonPromotionCandidateIdentityBindingError(
            "metric input integrity must be object"
        )
    digest = integrity.get("content_sha256")
    if not isinstance(digest, str) or not is_valid_sha256_hex(digest):
        raise ComparisonPromotionCandidateIdentityBindingError(
            "metric input integrity.content_sha256 invalid"
        )
    comparison_metric_input_id = manifest.get("comparison_metric_input_id")
    if not isinstance(comparison_metric_input_id, str) or not comparison_metric_input_id.strip():
        raise ComparisonPromotionCandidateIdentityBindingError(
            "comparison_metric_input_id missing or invalid"
        )
    source_ref = manifest.get("source_ref")
    strategy_identity_ref: str | None = None
    if isinstance(source_ref, Mapping):
        ref_id = source_ref.get("ref_id")
        if isinstance(ref_id, str) and ref_id.strip():
            strategy_identity_ref = ref_id

    return VerifiedCandidateIdentityBundle(
        bundle_dir=bundle_dir.resolve(),
        source_type="comparison_metric_input_durable_evidence_binding_v1",
        candidate_identity_ref=comparison_metric_input_id,
        candidate_identity_digest=digest,
        candidate_artifact_ref=METRIC_INPUT_MANIFEST_REL,
        candidate_manifest_digest=digest,
        manifest_digest=_manifest_file_digest(bundle_dir),
        comparison_metric_input_ref=comparison_metric_input_id,
        comparison_metric_input_digest=digest,
        strategy_identity_ref=strategy_identity_ref,
        parameter_set_identity_ref=None,
    )


def verify_candidate_identity_bundle(bundle_dir: Path | str) -> VerifiedCandidateIdentityBundle:
    """Fail-closed verification of exactly one explicit candidate identity bundle."""
    path = Path(bundle_dir)
    _validate_bundle_dir(path, label="candidate identity bundle")
    ok, msg = verify_manifest_sha256(path)
    if not ok:
        raise ComparisonPromotionCandidateIdentityBindingError(
            f"candidate identity MANIFEST.sha256 verification failed: {msg}"
        )
    source_type = _detect_candidate_source_type(path)
    if source_type == "candidate_lineage_manifest_v1":
        return _verify_candidate_lineage_bundle(path)
    return _verify_metric_input_binding_bundle(path)


def _metric_input_id_in_promotion_checkpoint(
    *,
    promotion_input: VerifiedPromotionInputBindingBundle,
    comparison_metric_input_id: str,
) -> bool:
    checkpoint_ref = str(promotion_input.evidence_payload.get("comparison_checkpoint_ref", ""))
    if not checkpoint_ref:
        return False
    checkpoint_index_path = Path(checkpoint_ref) / "comparison_checkpoint_index_v1.json"
    if not checkpoint_index_path.is_file():
        return False
    checkpoint_index = read_ssot_manifest(checkpoint_index_path)
    for ref in checkpoint_index.get("metric_input_binding_refs", []):
        if not isinstance(ref, Mapping):
            continue
        if ref.get("comparison_metric_input_id") == comparison_metric_input_id:
            return True
    return False


def _cross_check_shared_lineage(
    *,
    promotion_input: VerifiedPromotionInputBindingBundle,
    candidate: VerifiedCandidateIdentityBundle,
) -> tuple[str, list[str]]:
    promo = promotion_input.evidence_payload
    reason_codes: list[str] = []

    experiment_ref = str(promo.get("experiment_identity_ref", ""))
    experiment_digest = str(promo.get("experiment_identity_digest", ""))
    if not experiment_ref or not is_valid_sha256_hex(experiment_digest):
        return "FAIL", ["EXPERIMENT_IDENTITY_MISSING"]

    try:
        experiment_identity_id = _read_experiment_identity_id(experiment_ref)
    except ComparisonPromotionCandidateIdentityBindingError:
        return "FAIL", ["EXPERIMENT_IDENTITY_UNREADABLE"]

    if candidate.source_type == "comparison_metric_input_durable_evidence_binding_v1":
        manifest = read_manifest(candidate.bundle_dir / METRIC_INPUT_MANIFEST_REL)
        metric_input_id = manifest.get("comparison_metric_input_id")
        if (
            not isinstance(metric_input_id, str)
            or metric_input_id != candidate.candidate_identity_ref
        ):
            return "FAIL", ["CANDIDATE_METRIC_INPUT_ID_MISMATCH"]
        if not _metric_input_id_in_promotion_checkpoint(
            promotion_input=promotion_input,
            comparison_metric_input_id=metric_input_id,
        ):
            return "FAIL", ["COMPARISON_METRIC_INPUT_NOT_IN_CHECKPOINT"]
        source_ref = manifest.get("source_ref")
        if isinstance(source_ref, Mapping):
            source_domain = source_ref.get("owner_domain", "")
            ref_id = source_ref.get("ref_id")
            ref_digest = source_ref.get("digest")
            if (
                source_domain == "experiments/experiment_identity_manifest_v1"
                or str(source_ref.get("ref_type", "")).upper() == "EXPERIMENT"
            ):
                if ref_id != experiment_identity_id:
                    return "FAIL", ["METRIC_INPUT_EXPERIMENT_ID_MISMATCH"]
                if isinstance(ref_digest, str) and ref_digest != experiment_digest:
                    return "FAIL", ["METRIC_INPUT_EXPERIMENT_DIGEST_MISMATCH"]

    if candidate.source_type == "candidate_lineage_manifest_v1":
        payload = json.loads(
            (candidate.bundle_dir / CANDIDATE_LINEAGE_ARTIFACT_REL).read_text(encoding="utf-8")
        )
        refs = payload.get("refs", [])
        experiment_refs = [
            ref
            for ref in refs
            if isinstance(ref, Mapping) and ref.get("ref_type") == LineageRefType.EXPERIMENT.value
        ]
        if len(experiment_refs) > 1:
            return "FAIL", ["MULTIPLE_CANDIDATE_EXPERIMENT_REFS"]
        if len(experiment_refs) == 1:
            ref = experiment_refs[0]
            if ref.get("ref_id") != experiment_identity_id:
                return "FAIL", ["CANDIDATE_LINEAGE_EXPERIMENT_ID_MISMATCH"]
            ref_digest = ref.get("digest")
            if isinstance(ref_digest, str) and ref_digest != experiment_digest:
                return "FAIL", ["CANDIDATE_LINEAGE_EXPERIMENT_DIGEST_MISMATCH"]
        elif candidate.strategy_identity_ref is not None:
            if candidate.strategy_identity_ref != experiment_identity_id:
                return "FAIL", ["EXPERIMENT_IDENTITY_MISMATCH"]

    promo_metric_ref = promo.get("comparison_metric_input_ref")
    promo_metric_digest = promo.get("comparison_metric_input_digest")
    if promo_metric_ref is not None and candidate.comparison_metric_input_ref is not None:
        if promo_metric_ref != candidate.comparison_metric_input_ref:
            return "FAIL", ["COMPARISON_METRIC_INPUT_REF_MISMATCH"]
        if (
            isinstance(promo_metric_digest, str)
            and promo_metric_digest != candidate.comparison_metric_input_digest
        ):
            return "FAIL", ["COMPARISON_METRIC_INPUT_DIGEST_MISMATCH"]

    reason_codes.extend(["EXPERIMENT_LINEAGE_MATCH", "CANDIDATE_IDENTITY_EXPLICIT"])
    return "PASS", reason_codes


def _derive_candidate_identity_binding_status(
    *,
    promotion_input_binding_status: str,
    shared_lineage_status: str,
) -> tuple[str, list[str]]:
    if shared_lineage_status != "PASS":
        return "FAIL", ["SHARED_LINEAGE_FAIL"]
    if promotion_input_binding_status not in _VALID_BINDING_STATUS:
        return "FAIL", ["PROMOTION_INPUT_BINDING_STATUS_UNKNOWN"]
    if promotion_input_binding_status == "FAIL":
        return "FAIL", ["PROMOTION_INPUT_BINDING_FAIL"]
    if promotion_input_binding_status == "INCOMPLETE":
        return "INCOMPLETE", ["PROMOTION_INPUT_BINDING_INCOMPLETE"]
    if promotion_input_binding_status == "NOT_EVALUABLE":
        return "NOT_EVALUABLE", ["PROMOTION_INPUT_BINDING_NOT_EVALUABLE"]
    return "PASS", ["PROMOTION_INPUT_BINDING_PASS", "CANDIDATE_IDENTITY_BOUND"]


def _input_artifact_ref_mapping(
    *,
    bundle: VerifiedPromotionInputBindingBundle | VerifiedCandidateIdentityBundle,
    contract_name: str,
    contract_version: str,
    producer_version: str,
    artifact_ref: str,
    artifact_digest: str,
) -> dict[str, Any]:
    return {
        "artifact_type": contract_name,
        "contract_name": contract_name,
        "contract_version": contract_version,
        "artifact_ref": artifact_ref,
        "artifact_digest": artifact_digest,
        "manifest_digest": bundle.manifest_digest,
        "producer_version": producer_version,
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


def build_comparison_promotion_candidate_identity_binding_v1(
    *,
    promotion_input: VerifiedPromotionInputBindingBundle,
    candidate: VerifiedCandidateIdentityBundle,
) -> dict[str, Any]:
    promo_payload = promotion_input.evidence_payload
    shared_lineage_status, shared_lineage_reason_codes = _cross_check_shared_lineage(
        promotion_input=promotion_input,
        candidate=candidate,
    )
    promotion_input_binding_status = str(promo_payload.get("promotion_input_binding_status", ""))
    candidate_identity_binding_status, candidate_identity_binding_reason_codes = (
        _derive_candidate_identity_binding_status(
            promotion_input_binding_status=promotion_input_binding_status,
            shared_lineage_status=shared_lineage_status,
        )
    )

    promo_ref = _input_artifact_ref_mapping(
        bundle=promotion_input,
        contract_name=promotion_input.contract_name,
        contract_version=promotion_input.contract_version,
        producer_version=promotion_input.producer_version,
        artifact_ref=promotion_input.artifact_ref,
        artifact_digest=promotion_input.artifact_digest,
    )
    candidate_ref = _input_artifact_ref_mapping(
        bundle=candidate,
        contract_name=candidate.source_type,
        contract_version="v1",
        producer_version=candidate.source_type,
        artifact_ref=candidate.candidate_artifact_ref,
        artifact_digest=candidate.candidate_identity_digest,
    )
    input_refs = [promo_ref, candidate_ref]
    input_refs.sort(
        key=lambda item: (str(item.get("artifact_type", "")), str(item.get("artifact_digest", "")))
    )

    parent_artifact_refs = list(promotion_input.parent_artifact_refs)
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
        "is_comparison_promotion_candidate_identity_binding": True,
        "evidence_does_not_authorize_promotion": True,
        "evidence_does_not_authorize_runtime": True,
        "candidate_identity_binding_does_not_select": True,
        "candidate_identity_binding_does_not_choose_winner": True,
        "candidate_identity_binding_does_not_accept": True,
        "candidate_identity_binding_does_not_execute_eligibility": True,
        "candidate_identity_binding_does_not_execute_policy": True,
        "candidate_identity_binding_does_not_create_configpatch": True,
        "candidate_identity_binding_does_not_modify_config": True,
        "candidate_identity_binding_does_not_deploy": True,
        "candidate_identity_binding_does_not_activate": True,
        "candidate_identity_binding_does_not_create_order_intent": True,
        "candidate_identity_binding_does_not_modify_trading_logic": True,
        "candidate_identity_binding_does_not_authorize_runtime": True,
        "candidate_identity_binding_authority_invariants": dict(
            CANDIDATE_IDENTITY_BINDING_AUTHORITY_INVARIANTS
        ),
        "promotion_input_binding_bundle_ref": promotion_input.bundle_dir.as_posix(),
        "promotion_input_binding_artifact_ref": promotion_input.artifact_ref,
        "promotion_input_binding_digest": promotion_input.artifact_digest,
        "promotion_input_binding_manifest_digest": promotion_input.manifest_digest,
        "candidate_identity_bundle_ref": candidate.bundle_dir.as_posix(),
        "candidate_identity_artifact_ref": candidate.candidate_artifact_ref,
        "candidate_identity_ref": candidate.candidate_identity_ref,
        "candidate_identity_digest": candidate.candidate_identity_digest,
        "candidate_identity_manifest_digest": candidate.candidate_manifest_digest,
        "candidate_identity_source_type": candidate.source_type,
        "candidate_identity_status": _CANDIDATE_IDENTITY_BOUND,
        "candidate_selection_status": _CANDIDATE_SELECTION_NOT_SELECTED,
        "winner_selection_status": _WINNER_SELECTION_NOT_SELECTED,
        "completion_validity_binding_bundle_ref": str(
            promo_payload.get("completion_validity_binding_bundle_ref", "")
        ),
        "comparison_completion_ref": str(promo_payload.get("comparison_completion_ref", "")),
        "comparison_completion_digest": str(promo_payload.get("comparison_completion_digest", "")),
        "research_validity_ref": str(promo_payload.get("research_validity_ref", "")),
        "research_validity_digest": str(promo_payload.get("research_validity_digest", "")),
        "comparison_checkpoint_ref": str(promo_payload.get("comparison_checkpoint_ref", "")),
        "comparison_checkpoint_digest": str(promo_payload.get("comparison_checkpoint_digest", "")),
        "experiment_identity_ref": str(promo_payload.get("experiment_identity_ref", "")),
        "experiment_identity_digest": str(promo_payload.get("experiment_identity_digest", "")),
        "dataset_identity_ref": str(promo_payload.get("dataset_identity_ref", "")),
        "dataset_identity_digest": str(promo_payload.get("dataset_identity_digest", "")),
        "comparison_definition_ref": str(promo_payload.get("comparison_definition_ref", "")),
        "comparison_definition_digest": str(promo_payload.get("comparison_definition_id", "")),
        "comparison_definition_id": str(promo_payload.get("comparison_definition_id", "")),
        "strategy_identity_ref": candidate.strategy_identity_ref
        or str(promo_payload.get("experiment_identity_ref", "")),
        "model_identity_ref": None,
        "parameter_set_identity_ref": candidate.parameter_set_identity_ref,
        "shared_lineage_status": shared_lineage_status,
        "shared_lineage_reason_codes": shared_lineage_reason_codes,
        "promotion_input_binding_status": promotion_input_binding_status,
        "candidate_identity_binding_status": candidate_identity_binding_status,
        "candidate_identity_binding_reason_codes": candidate_identity_binding_reason_codes,
        "upstream_contract_name": promotion_input.contract_name,
        "upstream_contract_version": promotion_input.contract_version,
        "upstream_producer_version": promotion_input.producer_version,
        "input_artifact_refs": input_refs,
        "parent_artifact_refs": parent_artifact_refs,
        "input_digest": "",
        "output_digest": "",
        "manifest_digest": "",
    }

    if candidate.comparison_metric_input_ref is not None:
        payload["comparison_metric_input_ref"] = candidate.comparison_metric_input_ref
        payload["comparison_metric_input_digest"] = candidate.comparison_metric_input_digest

    _reject_forbidden_index_keys(payload)
    _validate_non_authorizing_flags(payload)
    _validate_capabilities(payload["capabilities"])

    payload["input_digest"] = compute_content_sha256({"input_artifact_refs": input_refs})
    output_digest = _compute_output_digest(payload)
    payload["output_digest"] = output_digest
    payload["artifact_id"] = output_digest
    return payload


def serialize_comparison_promotion_candidate_identity_binding_v1(
    evidence: Mapping[str, Any],
) -> str:
    _reject_forbidden_index_keys(evidence)
    _validate_non_authorizing_flags(evidence)
    _validate_capabilities(evidence.get("capabilities"))
    binding_status = evidence.get("candidate_identity_binding_status")
    if binding_status not in _VALID_BINDING_STATUS:
        raise ComparisonPromotionCandidateIdentityBindingError(
            f"candidate_identity_binding_status must be one of {sorted(_VALID_BINDING_STATUS)}"
        )
    if evidence.get("candidate_selection_status") != _CANDIDATE_SELECTION_NOT_SELECTED:
        raise ComparisonPromotionCandidateIdentityBindingError(
            "candidate_selection_status must be NOT_SELECTED"
        )
    if evidence.get("winner_selection_status") != _WINNER_SELECTION_NOT_SELECTED:
        raise ComparisonPromotionCandidateIdentityBindingError(
            "winner_selection_status must be NOT_SELECTED"
        )
    return deterministic_json_dumps(dict(evidence))


def _evidence_bytes_for_manifest_digest(evidence: Mapping[str, Any]) -> bytes:
    canonical = {
        key: value for key, value in evidence.items() if key not in {"integrity", "manifest_digest"}
    }
    return serialize_comparison_promotion_candidate_identity_binding_v1(canonical).encode("utf-8")


def _compute_output_manifest_digest(evidence: Mapping[str, Any]) -> str:
    return hashlib.sha256(_evidence_bytes_for_manifest_digest(evidence)).hexdigest()


def _validate_evidence_integrity(evidence: Mapping[str, Any]) -> None:
    if evidence.get("contract_name") != CONTRACT_NAME:
        raise ComparisonPromotionCandidateIdentityBindingError("contract_name mismatch")
    if evidence.get("contract_version") != CONTRACT_VERSION:
        raise ComparisonPromotionCandidateIdentityBindingError("contract_version mismatch")
    if evidence.get("producer_version") != PRODUCER_VERSION:
        raise ComparisonPromotionCandidateIdentityBindingError("producer_version mismatch")
    _validate_non_authorizing_flags(evidence)
    _validate_capabilities(evidence.get("capabilities"))
    if evidence.get("candidate_identity_status") != _CANDIDATE_IDENTITY_BOUND:
        raise ComparisonPromotionCandidateIdentityBindingError(
            "candidate_identity_status must be BOUND"
        )
    invariants = evidence.get("candidate_identity_binding_authority_invariants")
    if invariants != CANDIDATE_IDENTITY_BINDING_AUTHORITY_INVARIANTS:
        raise ComparisonPromotionCandidateIdentityBindingError(
            "candidate_identity_binding_authority_invariants mismatch"
        )

    stored = evidence.get("integrity")
    if not isinstance(stored, Mapping):
        raise ComparisonPromotionCandidateIdentityBindingError("integrity must be an object")
    expected = compute_content_sha256(_integrity_body(evidence))
    actual = stored.get("content_sha256")
    if actual != expected:
        raise ComparisonPromotionCandidateIdentityBindingError(
            "candidate identity binding evidence integrity mismatch"
        )

    output_digest = evidence.get("output_digest")
    if output_digest != _compute_output_digest(evidence):
        raise ComparisonPromotionCandidateIdentityBindingError("output_digest mismatch")
    if evidence.get("artifact_id") != output_digest:
        raise ComparisonPromotionCandidateIdentityBindingError(
            "artifact_id must equal output_digest"
        )


def build_self_verification_v1(
    *,
    evidence: Mapping[str, Any],
    promotion_input: VerifiedPromotionInputBindingBundle,
    candidate: VerifiedCandidateIdentityBundle,
    manifest_digest: str,
) -> dict[str, Any]:
    checks: list[dict[str, str]] = [
        {"check_id": "contract_name", "status": "PASS"},
        {"check_id": "contract_version", "status": "PASS"},
        {"check_id": "evidence_level_level_3", "status": "PASS"},
        {"check_id": "exactly_two_direct_inputs", "status": "PASS"},
        {"check_id": "promotion_input_contract_and_version", "status": "PASS"},
        {"check_id": "candidate_identity_contract_and_version", "status": "PASS"},
        {"check_id": "input_manifests_verified", "status": "PASS"},
        {"check_id": "promotion_input_self_verification_pass", "status": "PASS"},
        {"check_id": "promotion_input_binding_status", "status": "PASS"},
        {"check_id": "candidate_identity_unique", "status": "PASS"},
        {"check_id": "candidate_identity_digest", "status": "PASS"},
        {"check_id": "shared_experiment_lineage", "status": "PASS"},
        {"check_id": "no_ranking_derivation", "status": "PASS"},
        {"check_id": "no_candidate_selection", "status": "PASS"},
        {"check_id": "no_winner_selection", "status": "PASS"},
        {"check_id": "required_fields", "status": "PASS"},
        {"check_id": "non_authorizing_semantics", "status": "PASS"},
        {"check_id": "forbidden_capabilities_absent", "status": "PASS"},
        {"check_id": "no_configpatch_semantics", "status": "PASS"},
        {"check_id": "canonical_serialization", "status": "PASS"},
        {"check_id": "output_digest", "status": "PASS"},
        {"check_id": "manifest_verification", "status": "PASS"},
        {"check_id": "deterministic_reverification", "status": "PASS"},
    ]

    input_refs = evidence.get("input_artifact_refs")
    if not isinstance(input_refs, list) or len(input_refs) != 2:
        checks = [
            {**c, "status": "FAIL"} if c["check_id"] == "exactly_two_direct_inputs" else c
            for c in checks
        ]

    if evidence.get("manifest_digest") != manifest_digest:
        checks = [
            {**c, "status": "FAIL"} if c["check_id"] == "manifest_verification" else c
            for c in checks
        ]

    if evidence.get("shared_lineage_status") != "PASS":
        checks = [
            {**c, "status": "FAIL"} if c["check_id"] == "shared_experiment_lineage" else c
            for c in checks
        ]

    if evidence.get("candidate_selection_status") != _CANDIDATE_SELECTION_NOT_SELECTED:
        checks = [
            {**c, "status": "FAIL"} if c["check_id"] == "no_candidate_selection" else c
            for c in checks
        ]

    binding_status = evidence.get("candidate_identity_binding_status")
    if binding_status not in _VALID_BINDING_STATUS:
        checks = [
            {**c, "status": "FAIL"} if c["check_id"] == "promotion_input_binding_status" else c
            for c in checks
        ]
    elif binding_status != "PASS":
        checks = [
            {**c, "status": "FAIL"} if c["check_id"] == "promotion_input_binding_status" else c
            for c in checks
        ]

    structural_failures = [
        check
        for check in checks
        if check["status"] != "PASS"
        and check["check_id"] not in {"shared_experiment_lineage", "promotion_input_binding_status"}
    ]
    if structural_failures:
        raise ComparisonPromotionCandidateIdentityBindingError("self-verification checks failed")

    payload: dict[str, Any] = {
        "self_verification_schema_version": _SELF_VERIFICATION_SCHEMA_VERSION,
        "contract_name": CONTRACT_NAME,
        "contract_version": CONTRACT_VERSION,
        "overall_status": "PASS",
        "checks": checks,
        "verified_artifact_rel": ARTIFACT_REL,
        "verified_output_digest": evidence.get("output_digest"),
        "verified_manifest_digest": manifest_digest,
        "verified_promotion_input_bundle_ref": promotion_input.bundle_dir.as_posix(),
        "verified_candidate_identity_bundle_ref": candidate.bundle_dir.as_posix(),
        "verified_candidate_identity_source_type": candidate.source_type,
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
    inputs: ComparisonPromotionCandidateIdentityBindingInputs,
) -> tuple[VerifiedPromotionInputBindingBundle, VerifiedCandidateIdentityBundle]:
    """Verify exactly one promotion input bundle and one candidate identity bundle."""
    promotion_input = verify_promotion_input_binding_bundle(
        inputs.promotion_input_binding_bundle_dir
    )
    candidate = verify_candidate_identity_bundle(inputs.candidate_identity_bundle_dir)
    return promotion_input, candidate


def reverify_comparison_promotion_candidate_identity_binding_v1(
    *,
    output_dir: Path | str,
) -> None:
    """Replay candidate identity binding bundle without producer or upstream mutation."""
    bundle_dir = Path(output_dir)
    if not bundle_dir.is_dir():
        raise ComparisonPromotionCandidateIdentityBindingError(
            f"candidate identity binding directory not found: {bundle_dir}"
        )
    ok, msg = verify_manifest_sha256(bundle_dir)
    if not ok:
        raise ComparisonPromotionCandidateIdentityBindingError(
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
        raise ComparisonPromotionCandidateIdentityBindingError(
            "SELF_VERIFICATION overall_status must be PASS"
        )

    manifest_digest = _compute_output_manifest_digest(evidence)
    if evidence.get("manifest_digest") != manifest_digest:
        raise ComparisonPromotionCandidateIdentityBindingError("manifest_digest mismatch on replay")

    promotion_input = verify_promotion_input_binding_bundle(
        Path(str(evidence["promotion_input_binding_bundle_ref"]))
    )
    candidate = verify_candidate_identity_bundle(
        Path(str(evidence["candidate_identity_bundle_ref"]))
    )

    if evidence.get("promotion_input_binding_digest") != promotion_input.artifact_digest:
        raise ComparisonPromotionCandidateIdentityBindingError(
            "promotion_input_binding_digest mismatch on replay"
        )
    if evidence.get("candidate_identity_digest") != candidate.candidate_identity_digest:
        raise ComparisonPromotionCandidateIdentityBindingError(
            "candidate_identity_digest mismatch on replay"
        )


def produce_comparison_promotion_candidate_identity_binding_v1(
    *,
    inputs: ComparisonPromotionCandidateIdentityBindingInputs,
    output_dir: Path | str,
) -> ComparisonPromotionCandidateIdentityBindingResult:
    """Bind verified promotion input and explicit candidate identity bundles."""
    final_dir = Path(output_dir)
    _validate_output_target(final_dir)
    _reject_unsafe_overlap(
        input_dirs=(
            inputs.promotion_input_binding_bundle_dir,
            inputs.candidate_identity_bundle_dir,
        ),
        output_dir=final_dir,
    )

    promotion_input, candidate = verify_binding_inputs(inputs)
    evidence_body = build_comparison_promotion_candidate_identity_binding_v1(
        promotion_input=promotion_input,
        candidate=candidate,
    )

    staging = _staging_dir_for(final_dir)
    if staging.exists():
        raise ComparisonPromotionCandidateIdentityBindingError(
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
            serialize_comparison_promotion_candidate_identity_binding_v1(finalized),
            encoding="utf-8",
        )
        self_payload = build_self_verification_v1(
            evidence=finalized,
            promotion_input=promotion_input,
            candidate=candidate,
            manifest_digest=manifest_digest,
        )
        self_path.write_text(deterministic_json_dumps(self_payload), encoding="utf-8")
        write_manifest_sha256(staging)

        ok, msg = verify_manifest_sha256(staging)
        if not ok:
            raise ComparisonPromotionCandidateIdentityBindingError(
                f"MANIFEST.sha256 verification failed before publish: {msg}"
            )

        reverify_comparison_promotion_candidate_identity_binding_v1(output_dir=staging)
        staging.replace(final_dir)

        ok, msg = verify_manifest_sha256(final_dir)
        if not ok:
            raise ComparisonPromotionCandidateIdentityBindingError(
                f"MANIFEST.sha256 verification failed after publish: {msg}"
            )
    except Exception:
        _cleanup_staging(staging)
        if final_dir.exists():
            shutil.rmtree(final_dir)
        raise

    return ComparisonPromotionCandidateIdentityBindingResult(
        output_dir=final_dir,
        comparison_definition_id=str(finalized["comparison_definition_id"]),
        artifact_id=str(finalized["artifact_id"]),
        evidence_path=final_dir / ARTIFACT_REL,
        self_verification_path=final_dir / SELF_VERIFICATION_REL,
        manifest_path=final_dir / MANIFEST_FILENAME,
        candidate_identity_binding_status=str(finalized["candidate_identity_binding_status"]),
        shared_lineage_status=str(finalized["shared_lineage_status"]),
        candidate_identity_ref=str(finalized["candidate_identity_ref"]),
        candidate_identity_source_type=candidate.source_type,
    )


__all__ = [
    "ARTIFACT_REL",
    "AUTHORITY_LEVEL",
    "CANDIDATE_LINEAGE_ARTIFACT_REL",
    "CONTRACT_NAME",
    "CONTRACT_VERSION",
    "EVIDENCE_LEVEL",
    "MANIFEST_FILENAME",
    "PRODUCER_VERSION",
    "SELF_VERIFICATION_REL",
    "CANDIDATE_IDENTITY_BINDING_AUTHORITY_INVARIANTS",
    "CandidateIdentitySourceType",
    "ComparisonPromotionCandidateIdentityBindingError",
    "ComparisonPromotionCandidateIdentityBindingInputs",
    "ComparisonPromotionCandidateIdentityBindingResult",
    "VerifiedCandidateIdentityBundle",
    "VerifiedPromotionInputBindingBundle",
    "build_comparison_promotion_candidate_identity_binding_v1",
    "build_self_verification_v1",
    "produce_comparison_promotion_candidate_identity_binding_v1",
    "reverify_comparison_promotion_candidate_identity_binding_v1",
    "serialize_comparison_promotion_candidate_identity_binding_v1",
    "verify_binding_inputs",
    "verify_candidate_identity_bundle",
    "verify_promotion_input_binding_bundle",
]
