"""Bounded Futures Testnet preflight operator-review proof package (v0, PE-20).

Deterministic, offline durable packaging and persistence for explicit PE-19
operator-review approve proofs bound to PE-13 through PE-18 evidence chain.
Reuses PE-19 review semantics and PE-16 archive/manifest primitives without
implicit authority, credentials, network, or exchange access.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from scripts.ops.primary_evidence_retention_v0 import (
    MANIFEST_FILENAME,
    is_under_tmp,
    require_durable_archive_root,
    verify_manifest_sha256,
    write_manifest_sha256,
)
from src.ops.bounded_futures_testnet_preflight_operator_review_reproducibility_contract_v0 import (
    CONTRACT_VERSION as PE19_CONTRACT_VERSION,
    DECISION_APPROVE_FOR_SEPARATE_NEXT_PHASE_REVIEW,
    DECISION_REJECT,
    DECISION_REQUEST_CHANGES,
    EXPECTED_OPERATOR_NAME,
    OperatorDecisionRecord,
    PreflightOperatorReviewInput,
    compute_decision_record_digest,
    compute_review_input_digest,
    evaluate_operator_review,
    serialize_decision_record_canonical,
    serialize_review_input_canonical,
    validate_decision_record,
    validate_review_input,
)
from src.ops.bounded_futures_testnet_preflight_packet_archive_contract_v0 import (
    ARCHIVE_CONTRACT_VERSION,
)
from src.ops.bounded_futures_testnet_preflight_packet_builder_contract_v0 import (
    BUILDER_VERSION,
)
from src.ops.bounded_futures_testnet_preflight_packet_completeness_truth_contract_v0 import (
    COMPLETENESS_CONTRACT_VERSION,
)
from src.ops.bounded_futures_testnet_preflight_packet_contract_v0 import (
    CONTRACT_VERSION as PE13_CONTRACT_VERSION,
    ENVIRONMENT_TESTNET,
    FOLLOWUP_RUN_GATE,
    PE12_CONTRACT_VERSION,
)
from src.ops.bounded_futures_testnet_preflight_packet_replay_contract_v0 import (
    HASH_ALGORITHM,
    REPLAY_CONTRACT_VERSION,
)
from src.ops.bounded_futures_testnet_preflight_source_state_capture_contract_v0 import (
    CONTRACT_VERSION as PE18_CONTRACT_VERSION,
)

PACKAGE_MARKER = "BOUNDED_FUTURES_TESTNET_PREFLIGHT_OPERATOR_REVIEW_PROOF_PACKAGE_CONTRACT_V0=true"
CONTRACT_VERSION = "bounded_futures_testnet_preflight_operator_review_proof_package.v0"
PACKAGE_SCHEMA_VERSION = (
    "bounded_futures_testnet_preflight_operator_review_proof_package.serialization.v0"
)
PACKAGE_RELATIVE_PREFIX = "bounded_futures_testnet_preflight_operator_review_proof_package"

PACKAGE_STATUS_PERSISTED_VERIFIED = "persisted_verified"
PACKAGE_STATUS_REJECTED = "rejected"

ARTIFACT_OPERATOR_REVIEW_INPUT = "OPERATOR_REVIEW_INPUT.json"
ARTIFACT_OPERATOR_DECISION_RECORD = "OPERATOR_DECISION_RECORD.json"
ARTIFACT_OPERATOR_REVIEW_PROOF = "OPERATOR_REVIEW_PROOF.json"
ARTIFACT_SOURCE_STATE_BINDING = "SOURCE_STATE_BINDING.json"
ARTIFACT_EVIDENCE_CHAIN_BINDING = "EVIDENCE_CHAIN_BINDING.json"
ARTIFACT_SAFETY_SNAPSHOT = "SAFETY_SNAPSHOT.json"
ARTIFACT_PACKAGE_METADATA = "PACKAGE_METADATA.json"
ARTIFACT_PACKAGE_SUMMARY = "PACKAGE_SUMMARY.md"

REQUIRED_ARTIFACT_FILENAMES: tuple[str, ...] = (
    ARTIFACT_OPERATOR_REVIEW_INPUT,
    ARTIFACT_OPERATOR_DECISION_RECORD,
    ARTIFACT_OPERATOR_REVIEW_PROOF,
    ARTIFACT_SOURCE_STATE_BINDING,
    ARTIFACT_EVIDENCE_CHAIN_BINDING,
    ARTIFACT_SAFETY_SNAPSHOT,
    ARTIFACT_PACKAGE_METADATA,
    ARTIFACT_PACKAGE_SUMMARY,
    MANIFEST_FILENAME,
)

_EXPECTED_CONTRACT_VERSIONS: dict[str, str] = {
    "pe12_lifecycle": PE12_CONTRACT_VERSION,
    "pe13_packet": PE13_CONTRACT_VERSION,
    "pe14_builder": BUILDER_VERSION,
    "pe15_replay": REPLAY_CONTRACT_VERSION,
    "pe16_archive": ARCHIVE_CONTRACT_VERSION,
    "pe17_completeness_truth": COMPLETENESS_CONTRACT_VERSION,
    "pe18_source_state_capture": PE18_CONTRACT_VERSION,
    "pe19_operator_review": PE19_CONTRACT_VERSION,
    "pe20_operator_review_proof_package": CONTRACT_VERSION,
}

_PACKAGE_INPUT_KEYS = frozenset(
    {
        "archive_root",
        "review_input",
        "decision_record",
        "source_state_digest",
        "package_summary_md",
        "package_contract_version",
        "package_schema_version",
        "hash_algorithm",
        "futures_only",
        "environment",
    }
)


@dataclass(frozen=True)
class OperatorReviewProofPackageInput:
    archive_root: Path
    review_input: PreflightOperatorReviewInput
    decision_record: OperatorDecisionRecord
    source_state_digest: str
    package_summary_md: str
    package_contract_version: str = CONTRACT_VERSION
    package_schema_version: str = PACKAGE_SCHEMA_VERSION
    hash_algorithm: str = HASH_ALGORITHM
    futures_only: bool = True
    environment: str = ENVIRONMENT_TESTNET


def _sorted_unique(items: list[str]) -> list[str]:
    return sorted(dict.fromkeys(items))


def _reject_unknown_keys(data: dict[str, Any], allowed: frozenset[str], prefix: str) -> list[str]:
    unknown = sorted(set(data) - allowed)
    if unknown:
        return [f"{prefix}: unknown field(s) {unknown!r}"]
    return []


def _atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_path = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".tmp_{path.name}_",
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
    except Exception:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        raise


def _resolve_under_root(root: Path, relative_path: str) -> tuple[Path | None, list[str]]:
    errors: list[str] = []
    if not relative_path:
        errors.append("package_relative_path required")
        return None, errors
    if relative_path.startswith("/"):
        errors.append("package_relative_path must be relative")
        return None, errors
    if ".." in Path(relative_path).parts:
        errors.append("package_relative_path must not contain '..'")
        return None, errors
    try:
        root_resolved = root.resolve()
        candidate = (root / relative_path).resolve()
        if candidate != root_resolved and root_resolved not in candidate.parents:
            errors.append("package destination escapes archive_root")
            return None, errors
        return candidate, errors
    except OSError as exc:
        errors.append(f"package path resolution failed: {exc}")
        return None, errors


def validate_archive_destination(archive_root: Path) -> list[str]:
    """Fail closed when archive root is missing or under /tmp."""
    errors: list[str] = []
    if is_under_tmp(archive_root):
        errors.append("archive_root must be outside /tmp")
    ok, msg = require_durable_archive_root(archive_root)
    if not ok:
        errors.append(msg)
    return errors


def _source_state_binding_dict(
    review_input: PreflightOperatorReviewInput,
    *,
    source_state_digest: str,
) -> dict[str, Any]:
    return {
        "package_contract_version": CONTRACT_VERSION,
        "source_revision": review_input.source_revision,
        "repository_identity": review_input.repository_identity,
        "source_state_digest": source_state_digest,
        "pe18_source_state_capture_contract_version": PE18_CONTRACT_VERSION,
    }


def _evidence_chain_binding_dict(review_input: PreflightOperatorReviewInput) -> dict[str, Any]:
    chain = asdict(review_input.evidence_chain)
    return {
        "package_contract_version": CONTRACT_VERSION,
        "source_revision": review_input.source_revision,
        "contract_versions": asdict(review_input.contract_versions),
        "evidence_chain": chain,
        "manifest_verify_rc": chain["manifest_verify_rc"],
    }


def _safety_snapshot_dict(review_input: PreflightOperatorReviewInput) -> dict[str, Any]:
    policy = asdict(review_input.safety_snapshot)
    return {
        "package_contract_version": CONTRACT_VERSION,
        "futures_only": review_input.futures_only,
        "environment": review_input.environment,
        "non_authorizing": review_input.non_authorizing,
        "preflight_remains_blocked": policy["preflight_remains_blocked"],
        "ready_for_operator_arming": policy["ready_for_operator_arming"],
        "execution_authorized": policy["execution_authorized"],
        "live_authorized": policy["live_authorized"],
        "zero_order_authorized": False,
        "network_allowed": policy["network_allowed"],
        "credentials_allowed": policy["credentials_allowed"],
        "orders_allowed": policy["orders_allowed"],
        "scheduler_runtime_allowed": policy["scheduler_runtime_allowed"],
        "operator_go_present": policy["operator_go_present"],
        "followup_run_gate": policy["followup_run_gate"],
    }


def _package_metadata_dict(
    *,
    review_input: PreflightOperatorReviewInput,
    decision_record: OperatorDecisionRecord,
    review_proof: dict[str, Any],
    source_state_digest: str,
    package_id: str,
    package_digest: str,
    review_input_digest: str,
    decision_record_digest: str,
    review_proof_digest: str,
) -> dict[str, Any]:
    return {
        "package_contract_version": CONTRACT_VERSION,
        "package_schema_version": PACKAGE_SCHEMA_VERSION,
        "hash_algorithm": HASH_ALGORITHM,
        "package_id": package_id,
        "package_digest": package_digest,
        "source_revision": review_input.source_revision,
        "repository_identity": review_input.repository_identity,
        "operator_review_input_digest": review_input_digest,
        "operator_decision_record_digest": decision_record_digest,
        "operator_review_proof_digest": review_proof_digest,
        "source_state_digest": source_state_digest,
        "contract_versions": {
            **_EXPECTED_CONTRACT_VERSIONS,
            "pe20_operator_review_proof_package": CONTRACT_VERSION,
        },
        "futures_only": review_input.futures_only,
        "environment": review_input.environment,
        "non_authorizing": True,
        "decision": decision_record.decision if review_proof.get("decision_record_valid") else None,
        "operator_name": (
            decision_record.operator_name if review_proof.get("decision_record_valid") else None
        ),
    }


def _package_identity_payload(
    *,
    review_input: PreflightOperatorReviewInput,
    review_input_digest: str,
    decision_record_digest: str,
    review_proof_digest: str,
    source_state_digest: str,
    package_contract_version: str = CONTRACT_VERSION,
    package_schema_version: str = PACKAGE_SCHEMA_VERSION,
) -> dict[str, Any]:
    return {
        "package_contract_version": package_contract_version,
        "package_schema_version": package_schema_version,
        "hash_algorithm": HASH_ALGORITHM,
        "source_revision": review_input.source_revision,
        "repository_identity": review_input.repository_identity,
        "operator_review_input_digest": review_input_digest,
        "operator_decision_record_digest": decision_record_digest,
        "operator_review_proof_digest": review_proof_digest,
        "source_state_digest": source_state_digest,
        "packet_digest": review_input.evidence_chain.packet_digest,
        "input_capture_digest": review_input.evidence_chain.input_capture_digest,
        "replay_manifest_digest": review_input.evidence_chain.replay_manifest_digest,
        "archive_identity": review_input.evidence_chain.archive_identity,
        "archive_manifest_digest": review_input.evidence_chain.archive_manifest_digest,
        "completeness_truth_identity": review_input.evidence_chain.completeness_truth_identity,
        "futures_only": review_input.futures_only,
        "environment": review_input.environment,
    }


def compute_package_id(
    *,
    review_input: PreflightOperatorReviewInput,
    review_input_digest: str,
    decision_record_digest: str,
    review_proof_digest: str,
    source_state_digest: str,
) -> str:
    """Deterministic package identity from stable non-secret bindings."""
    payload = _package_identity_payload(
        review_input=review_input,
        review_input_digest=review_input_digest,
        decision_record_digest=decision_record_digest,
        review_proof_digest=review_proof_digest,
        source_state_digest=source_state_digest,
    )
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def compute_package_digest(
    *,
    review_input: PreflightOperatorReviewInput,
    decision_record: OperatorDecisionRecord,
    review_proof: dict[str, Any],
    source_state_digest: str,
    package_summary_md: str,
) -> str:
    """Deterministic digest over canonical package artifact bindings."""
    review_input_digest = compute_review_input_digest(review_input)
    decision_record_digest = compute_decision_record_digest(decision_record)
    review_proof_canonical = json.dumps(review_proof, sort_keys=True, separators=(",", ":"))
    review_proof_digest = hashlib.sha256(review_proof_canonical.encode("utf-8")).hexdigest()
    payload = {
        "package_contract_version": CONTRACT_VERSION,
        "package_schema_version": PACKAGE_SCHEMA_VERSION,
        "hash_algorithm": HASH_ALGORITHM,
        "operator_review_input": json.loads(serialize_review_input_canonical(review_input)),
        "operator_decision_record": json.loads(
            serialize_decision_record_canonical(decision_record)
        ),
        "operator_review_proof": review_proof,
        "source_state_binding": _source_state_binding_dict(
            review_input,
            source_state_digest=source_state_digest,
        ),
        "evidence_chain_binding": _evidence_chain_binding_dict(review_input),
        "safety_snapshot": _safety_snapshot_dict(review_input),
        "package_summary_md": package_summary_md.rstrip() + "\n",
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def compute_package_relative_path(package_id: str) -> str:
    """Deterministic relative package path under the injected archive root."""
    return f"{PACKAGE_RELATIVE_PREFIX}/{package_id}"


def validate_manifest_entries(entries: tuple[str, ...]) -> list[str]:
    """Reject duplicate, absolute, or traversal manifest artifact paths."""
    errors: list[str] = []
    if len(entries) != len(set(entries)):
        errors.append("duplicate artifact filenames in manifest plan")
    for entry in entries:
        if entry.startswith("/"):
            errors.append(f"absolute manifest path rejected: {entry!r}")
        if ".." in Path(entry).parts:
            errors.append(f"path traversal rejected in manifest entry: {entry!r}")
    missing = sorted(set(REQUIRED_ARTIFACT_FILENAMES) - {MANIFEST_FILENAME} - set(entries))
    if missing:
        errors.append(f"missing required artifacts in manifest plan: {missing}")
    return errors


def _evaluate_review_proof_binding(
    package_input: OperatorReviewProofPackageInput,
) -> tuple[dict[str, Any], list[str]]:
    review_input = package_input.review_input
    decision_record = package_input.decision_record
    errors: list[str] = []
    errors.extend(validate_archive_destination(package_input.archive_root))

    if package_input.package_contract_version != CONTRACT_VERSION:
        errors.append(f"package_contract_version must be {CONTRACT_VERSION!r}")
    if package_input.package_schema_version != PACKAGE_SCHEMA_VERSION:
        errors.append(f"package_schema_version must be {PACKAGE_SCHEMA_VERSION!r}")
    if package_input.hash_algorithm != HASH_ALGORITHM:
        errors.append(f"hash_algorithm must be {HASH_ALGORITHM!r}")
    if package_input.futures_only is not True:
        errors.append("futures_only must be true")
    if package_input.environment != ENVIRONMENT_TESTNET:
        errors.append(f"environment must be {ENVIRONMENT_TESTNET!r}")
    if not package_input.package_summary_md.strip():
        errors.append("package_summary_md required")

    input_errors = validate_review_input(review_input)
    errors.extend(input_errors)
    input_valid = not input_errors
    review_input_digest = compute_review_input_digest(review_input) if input_valid else None

    decision_errors = validate_decision_record(
        decision_record,
        review_input=review_input if input_valid else None,
        expected_review_input_digest=review_input_digest,
    )
    errors.extend(decision_errors)
    decision_valid = not decision_errors
    decision_record_digest = (
        compute_decision_record_digest(decision_record) if decision_valid else None
    )

    review_proof = evaluate_operator_review(
        review_input,
        decision_record,
        review_input_digest=review_input_digest,
        decision_record_digest=decision_record_digest,
    )
    if not review_proof.get("review_valid"):
        errors.append("review proof invalid")

    if decision_record.decision != DECISION_APPROVE_FOR_SEPARATE_NEXT_PHASE_REVIEW:
        errors.append("decision must be approve_for_separate_next_phase_review for proof package")
    if decision_record.operator_name != EXPECTED_OPERATOR_NAME:
        errors.append(f"operator_name must be {EXPECTED_OPERATOR_NAME!r}")
    if decision_record.decision in (DECISION_REJECT, DECISION_REQUEST_CHANGES):
        errors.append(f"decision {decision_record.decision!r} cannot produce approve package")

    if not package_input.source_state_digest:
        errors.append("source_state_digest required")
    elif len(package_input.source_state_digest) != 64:
        errors.append("source_state_digest must be 64-char lowercase sha256 hex")
    elif (
        input_valid
        and package_input.source_state_digest != review_input.evidence_chain.source_state_digest
    ):
        errors.append("source_state_digest mismatch with review input evidence chain")

    for field_name, expected in _EXPECTED_CONTRACT_VERSIONS.items():
        if field_name == "pe20_operator_review_proof_package":
            continue
        actual = getattr(review_input.contract_versions, field_name)
        if actual != expected:
            errors.append(f"contract_versions: {field_name} must be {expected!r}, got {actual!r}")

    return review_proof, _sorted_unique(errors)


def build_proof_package_plan(
    package_input: OperatorReviewProofPackageInput,
) -> dict[str, Any]:
    """Build deterministic proof-package plan without filesystem mutation."""
    review_proof, validation_errors = _evaluate_review_proof_binding(package_input)
    review_input = package_input.review_input
    decision_record = package_input.decision_record

    input_errors = validate_review_input(review_input)
    input_valid = not input_errors
    review_input_digest = compute_review_input_digest(review_input) if input_valid else ""

    decision_errors = validate_decision_record(
        decision_record,
        review_input=review_input if input_valid else None,
        expected_review_input_digest=review_input_digest or None,
    )
    decision_valid = not decision_errors
    decision_record_digest = (
        compute_decision_record_digest(decision_record) if decision_valid else ""
    )

    review_proof_canonical = json.dumps(review_proof, sort_keys=True, separators=(",", ":"))
    review_proof_digest = hashlib.sha256(review_proof_canonical.encode("utf-8")).hexdigest()

    package_id = ""
    package_digest = ""
    if not validation_errors and review_input_digest and decision_record_digest:
        package_id = compute_package_id(
            review_input=review_input,
            review_input_digest=review_input_digest,
            decision_record_digest=decision_record_digest,
            review_proof_digest=review_proof_digest,
            source_state_digest=package_input.source_state_digest,
        )
        package_digest = compute_package_digest(
            review_input=review_input,
            decision_record=decision_record,
            review_proof=review_proof,
            source_state_digest=package_input.source_state_digest,
            package_summary_md=package_input.package_summary_md,
        )

    package_relative_path = compute_package_relative_path(package_id) if package_id else ""
    manifest_entries = tuple(sorted(set(REQUIRED_ARTIFACT_FILENAMES) - {MANIFEST_FILENAME}))
    validation_errors.extend(validate_manifest_entries(manifest_entries))

    destination, path_errors = (
        _resolve_under_root(package_input.archive_root, package_relative_path)
        if package_relative_path
        else (None, [])
    )
    validation_errors.extend(path_errors)

    artifact_contents: dict[str, str] = {}
    if not validation_errors and package_id:
        artifact_contents = {
            ARTIFACT_OPERATOR_REVIEW_INPUT: serialize_review_input_canonical(review_input),
            ARTIFACT_OPERATOR_DECISION_RECORD: serialize_decision_record_canonical(decision_record),
            ARTIFACT_OPERATOR_REVIEW_PROOF: review_proof_canonical,
            ARTIFACT_SOURCE_STATE_BINDING: json.dumps(
                _source_state_binding_dict(
                    review_input,
                    source_state_digest=package_input.source_state_digest,
                ),
                sort_keys=True,
                separators=(",", ":"),
            ),
            ARTIFACT_EVIDENCE_CHAIN_BINDING: json.dumps(
                _evidence_chain_binding_dict(review_input),
                sort_keys=True,
                separators=(",", ":"),
            ),
            ARTIFACT_SAFETY_SNAPSHOT: json.dumps(
                _safety_snapshot_dict(review_input),
                sort_keys=True,
                separators=(",", ":"),
            ),
            ARTIFACT_PACKAGE_METADATA: json.dumps(
                _package_metadata_dict(
                    review_input=review_input,
                    decision_record=decision_record,
                    review_proof=review_proof,
                    source_state_digest=package_input.source_state_digest,
                    package_id=package_id,
                    package_digest=package_digest,
                    review_input_digest=review_input_digest,
                    decision_record_digest=decision_record_digest,
                    review_proof_digest=review_proof_digest,
                ),
                sort_keys=True,
                separators=(",", ":"),
            ),
            ARTIFACT_PACKAGE_SUMMARY: package_input.package_summary_md.rstrip() + "\n",
        }

    return {
        "package_status": PACKAGE_STATUS_REJECTED if validation_errors else "planned",
        "package_id": package_id,
        "package_digest": package_digest,
        "package_relative_path": package_relative_path,
        "package_destination": str(destination) if destination is not None else "",
        "required_artifacts": list(REQUIRED_ARTIFACT_FILENAMES),
        "manifest_entries": list(manifest_entries),
        "artifact_contents": artifact_contents,
        "review_proof": review_proof,
        "review_input_digest": review_input_digest or None,
        "decision_record_digest": decision_record_digest or None,
        "review_proof_digest": review_proof_digest if review_proof_digest else None,
        "validation_errors": validation_errors,
        "durable_destination_valid": not validation_errors and destination is not None,
        "non_authorizing": True,
        "execution_authorized": False,
        "live_authorized": False,
        "followup_run_gate": FOLLOWUP_RUN_GATE,
    }


def _directory_contents_match(root: Path, artifact_contents: dict[str, str]) -> bool:
    if not root.is_dir():
        return False
    for name, expected in artifact_contents.items():
        if name == MANIFEST_FILENAME:
            continue
        path = root / name
        if not path.is_file():
            return False
        if path.read_text(encoding="utf-8") != expected:
            return False
    return True


def _cleanup_directory(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)


def persist_operator_review_proof_package(
    package_input: OperatorReviewProofPackageInput,
) -> dict[str, Any]:
    """Persist verified operator-review proof package under injected archive root."""
    plan = build_proof_package_plan(package_input)
    validation_errors = list(plan["validation_errors"])
    archive_root = package_input.archive_root
    package_id = plan["package_id"]
    package_relative_path = plan["package_relative_path"]
    artifact_contents: dict[str, str] = plan["artifact_contents"]

    destination, path_errors = (
        _resolve_under_root(archive_root, package_relative_path)
        if package_relative_path
        else (None, ["package_relative_path required"])
    )
    validation_errors.extend(path_errors)

    if validation_errors or destination is None or not artifact_contents:
        return _package_result(
            package_status=PACKAGE_STATUS_REJECTED,
            package_id=package_id,
            package_digest=plan["package_digest"],
            source_revision=package_input.review_input.source_revision,
            review_proof=plan["review_proof"],
            validation_errors=validation_errors,
            durable_destination_valid=False,
        )

    collision_detected = False
    if destination.exists():
        if _directory_contents_match(destination, artifact_contents):
            verify_ok, _ = verify_manifest_sha256(destination)
            manifest_verify_rc = 0 if verify_ok else 1
            if manifest_verify_rc != 0:
                validation_errors.append("existing package manifest verification failed")
                return _package_result(
                    package_status=PACKAGE_STATUS_REJECTED,
                    package_id=package_id,
                    package_digest=plan["package_digest"],
                    source_revision=package_input.review_input.source_revision,
                    review_proof=plan["review_proof"],
                    validation_errors=validation_errors,
                    collision_detected=True,
                    durable_destination_valid=False,
                )
            return _package_result(
                package_status=PACKAGE_STATUS_PERSISTED_VERIFIED,
                package_id=package_id,
                package_digest=plan["package_digest"],
                source_revision=package_input.review_input.source_revision,
                review_proof=plan["review_proof"],
                validation_errors=[],
                required_artifacts_present=True,
                manifest_written=True,
                manifest_verify_rc=0,
                durable_destination_valid=True,
                collision_detected=False,
                collision_free=True,
            )
        collision_detected = True
        validation_errors.append("package identity collision with differing content")
        return _package_result(
            package_status=PACKAGE_STATUS_REJECTED,
            package_id=package_id,
            package_digest=plan["package_digest"],
            source_revision=package_input.review_input.source_revision,
            review_proof=plan["review_proof"],
            validation_errors=validation_errors,
            collision_detected=collision_detected,
            durable_destination_valid=False,
        )

    staging = destination.parent / f".staging_{package_id}"
    if staging.exists():
        _cleanup_directory(staging)
    staging.mkdir(parents=True, exist_ok=True)

    try:
        for name, content in artifact_contents.items():
            if name == MANIFEST_FILENAME:
                continue
            _atomic_write_text(staging / name, content)
        write_manifest_sha256(staging)
        verify_ok, verify_msg = verify_manifest_sha256(staging)
        manifest_verify_rc = 0 if verify_ok else 1
        if manifest_verify_rc != 0:
            validation_errors.append(f"manifest verification failed: {verify_msg}")
            _cleanup_directory(staging)
            return _package_result(
                package_status=PACKAGE_STATUS_REJECTED,
                package_id=package_id,
                package_digest=plan["package_digest"],
                source_revision=package_input.review_input.source_revision,
                review_proof=plan["review_proof"],
                validation_errors=validation_errors,
                manifest_written=True,
                manifest_verify_rc=manifest_verify_rc,
                durable_destination_valid=False,
            )
        destination.parent.mkdir(parents=True, exist_ok=True)
        staging.rename(destination)
    except OSError as exc:
        _cleanup_directory(staging)
        validation_errors.append(f"persist failed: {exc}")
        return _package_result(
            package_status=PACKAGE_STATUS_REJECTED,
            package_id=package_id,
            package_digest=plan["package_digest"],
            source_revision=package_input.review_input.source_revision,
            review_proof=plan["review_proof"],
            validation_errors=validation_errors,
            durable_destination_valid=False,
        )

    final_verify_ok, final_verify_msg = verify_manifest_sha256(destination)
    manifest_verify_rc = 0 if final_verify_ok else 1
    if manifest_verify_rc != 0:
        validation_errors.append(f"post-write manifest verification failed: {final_verify_msg}")
        return _package_result(
            package_status=PACKAGE_STATUS_REJECTED,
            package_id=package_id,
            package_digest=plan["package_digest"],
            source_revision=package_input.review_input.source_revision,
            review_proof=plan["review_proof"],
            validation_errors=validation_errors,
            manifest_written=True,
            manifest_verify_rc=manifest_verify_rc,
            durable_destination_valid=False,
        )

    return _package_result(
        package_status=PACKAGE_STATUS_PERSISTED_VERIFIED,
        package_id=package_id,
        package_digest=plan["package_digest"],
        source_revision=package_input.review_input.source_revision,
        review_proof=plan["review_proof"],
        validation_errors=[],
        required_artifacts_present=True,
        manifest_written=True,
        manifest_verify_rc=0,
        durable_destination_valid=True,
        collision_detected=False,
        collision_free=True,
    )


def evaluate_proof_package_result(
    package_result: dict[str, Any],
) -> dict[str, Any]:
    """Evaluate persisted or planned package result; never grants authority."""
    review_proof = package_result.get("review_proof") or {}
    validation_errors = list(package_result.get("validation_errors") or [])

    review_input_valid = review_proof.get("review_input_valid") is True
    decision_record_valid = review_proof.get("decision_record_valid") is True
    review_proof_valid = review_proof.get("review_valid") is True
    approve_decision_confirmed = (
        review_proof_valid
        and review_proof.get("decision") == DECISION_APPROVE_FOR_SEPARATE_NEXT_PHASE_REVIEW
    )
    source_state_binding_valid = (
        review_input_valid
        and review_proof.get("evidence_manifest_verified") is True
        and not any("source_state_digest" in err for err in validation_errors)
    )
    evidence_chain_binding_valid = (
        review_input_valid
        and review_proof.get("contract_versions_match") is True
        and review_proof.get("evidence_manifest_verified") is True
    )
    safety_snapshot_valid = review_input_valid and not any(
        "safety_snapshot" in err for err in validation_errors
    )

    package_status = package_result.get("package_status")
    persisted_verified = package_status == PACKAGE_STATUS_PERSISTED_VERIFIED
    required_artifacts_present = package_result.get("required_artifacts_present") is True
    manifest_written = package_result.get("manifest_written") is True
    manifest_verify_rc = package_result.get("manifest_verify_rc")
    durable_destination_valid = package_result.get("durable_destination_valid") is True
    collision_free = package_result.get("collision_free") is True

    static_glb016 = (
        persisted_verified
        and review_input_valid
        and decision_record_valid
        and review_proof_valid
        and approve_decision_confirmed
        and source_state_binding_valid
        and evidence_chain_binding_valid
        and safety_snapshot_valid
        and required_artifacts_present
        and manifest_written
        and manifest_verify_rc == 0
        and durable_destination_valid
        and collision_free
        and not validation_errors
    )

    return {
        "package_contract_version": CONTRACT_VERSION,
        "package_status": package_status,
        "package_id": package_result.get("package_id"),
        "package_digest": package_result.get("package_digest"),
        "source_revision": package_result.get("source_revision"),
        "review_input_valid": review_input_valid,
        "decision_record_valid": decision_record_valid,
        "review_proof_valid": review_proof_valid,
        "approve_decision_confirmed": approve_decision_confirmed,
        "source_state_binding_valid": source_state_binding_valid,
        "evidence_chain_binding_valid": evidence_chain_binding_valid,
        "safety_snapshot_valid": safety_snapshot_valid,
        "required_artifacts_present": required_artifacts_present,
        "manifest_written": manifest_written,
        "manifest_verify_rc": manifest_verify_rc,
        "durable_destination_valid": durable_destination_valid,
        "collision_free": collision_free,
        "static_glb016_reproducibility_satisfied": static_glb016,
        "validation_errors": validation_errors,
        "non_authorizing": True,
        "preflight_remains_blocked": True,
        "ready_for_operator_arming": False,
        "execution_authorized": False,
        "live_authorized": False,
        "zero_order_authorized": False,
        "followup_run_gate": FOLLOWUP_RUN_GATE,
    }


def explicit_contract_proof_kwargs(package_evaluation: dict[str, Any]) -> dict[str, Any]:
    """Build kwargs for PE-17 ExplicitContractProof from a PE-20 package evaluation."""
    valid = package_evaluation.get("static_glb016_reproducibility_satisfied") is True
    return {
        "contract_version": CONTRACT_VERSION,
        "validation_pass": valid,
        "contract_marker": PACKAGE_MARKER if valid else None,
    }


def validate_package_input_mapping(data: dict[str, Any]) -> list[str]:
    """Validate explicit mapping input for unknown top-level keys."""
    return _reject_unknown_keys(data, _PACKAGE_INPUT_KEYS, "package_input")


def _package_result(
    *,
    package_status: str,
    package_id: str,
    package_digest: str,
    source_revision: str,
    review_proof: dict[str, Any],
    validation_errors: list[str],
    required_artifacts_present: bool = False,
    manifest_written: bool = False,
    manifest_verify_rc: int | None = None,
    durable_destination_valid: bool = False,
    collision_detected: bool = False,
    collision_free: bool = False,
) -> dict[str, Any]:
    base = {
        "package_status": package_status,
        "package_id": package_id,
        "package_digest": package_digest,
        "package_relative_path": (compute_package_relative_path(package_id) if package_id else ""),
        "source_revision": source_revision,
        "review_proof": review_proof,
        "required_artifacts_present": required_artifacts_present,
        "manifest_written": manifest_written,
        "manifest_verify_rc": manifest_verify_rc,
        "durable_destination_valid": durable_destination_valid,
        "collision_detected": collision_detected,
        "collision_free": collision_free,
        "validation_errors": validation_errors,
        "non_authorizing": True,
        "execution_authorized": False,
        "live_authorized": False,
        "followup_run_gate": FOLLOWUP_RUN_GATE,
    }
    return {**base, **evaluate_proof_package_result(base)}
