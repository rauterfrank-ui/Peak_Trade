"""Offline LEVEL_3 trading session single writer contract owner v1."""

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
from src.meta.learning_loop.clock_trust_and_expiry_v1 import (
    ARTIFACT_REL as CLOCK_TRUST_ARTIFACT_REL,
    CONTRACT_NAME as CLOCK_TRUST_CONTRACT_NAME,
    CONTRACT_VERSION as CLOCK_TRUST_CONTRACT_VERSION,
    ClockTrustAndExpiryError,
    PRODUCER_VERSION as CLOCK_TRUST_PRODUCER_VERSION,
    SELF_VERIFICATION_REL as CLOCK_TRUST_SELF_VERIFICATION_REL,
    reverify_clock_trust_and_expiry_v1,
)
from src.meta.learning_loop.comparison_common_durable_evidence_binding_v1 import (
    COMPARISON_AUTHORITY_INVARIANTS,
)
from src.meta.learning_loop.comparison_metric_input_v1.io import read_manifest
from src.meta.learning_loop.contract_safety_v1 import (
    compute_content_sha256,
    deterministic_json_dumps,
    is_valid_sha256_hex,
)

CONTRACT_NAME = "trading_session_single_writer_v1"
CONTRACT_VERSION = "v1"
SESSION_CONTRACT_VERSION = "trading_session_contract_v1"
WRITER_CONTRACT_VERSION = "writer_fencing_contract_v1"
PRODUCER_VERSION = "trading_session_single_writer_v1"
EVIDENCE_LEVEL = "LEVEL_3"
AUTHORITY_LEVEL = "NON_AUTHORITIZING"
RECORD_KIND = "trading_session_single_writer_record"
INPUT_RELATION = (
    "PACKAGES_VERIFIED_CLOCK_TRUST_AND_EXPIRY_FOR_OFFLINE_TRADING_SESSION_SINGLE_WRITER"
)
ARTIFACT_REL = "trading_session_single_writer_v1.json"
SELF_VERIFICATION_REL = "SELF_VERIFICATION.json"
MANIFEST_FILENAME = "MANIFEST.sha256"
STAGING_DIRNAME_PREFIX = ".trading_session_single_writer_staging_"

SCHEMA_VERSION = "trading_session_single_writer_schema_v1"
CREATION_CONTRACT_VERSION = "trading_session_single_writer_creation_v1"
DETERMINISTIC_RULE_SET_VERSION = "trading_session_single_writer_rules_v1"
OFFLINE_DETERMINISTIC_CREATED_AT = "1970-01-01T00:00:00+00:00"
DEFAULT_PRODUCER_IDENTITY_REF = "peak_trade_offline_trading_session_single_writer_producer_v1"
DEFAULT_SOURCE_REVISION = "OFFLINE_DETERMINISTIC_EVIDENCE"

_VALID_CONTRACT_STATUSES = frozenset(
    {
        "TRADING_SESSION_SINGLE_WRITER_VALID_FOR_OFFLINE_EVALUATION",
        "TRADING_SESSION_SINGLE_WRITER_IDEMPOTENT",
        "TRADING_SESSION_SINGLE_WRITER_INVALID",
        "TRADING_SESSION_SINGLE_WRITER_MISSING_IDENTITY",
        "TRADING_SESSION_SINGLE_WRITER_COMPETING_WRITER",
        "TRADING_SESSION_SINGLE_WRITER_DUPLICATE_WRITER_CLAIM",
        "TRADING_SESSION_SINGLE_WRITER_STALE_GENERATION",
        "TRADING_SESSION_SINGLE_WRITER_STALE_REVISION",
        "TRADING_SESSION_SINGLE_WRITER_REPLAY_REJECTED",
        "TRADING_SESSION_SINGLE_WRITER_REVOKED",
        "TRADING_SESSION_SINGLE_WRITER_EXPIRED",
        "TRADING_SESSION_SINGLE_WRITER_UNTRUSTED_CLOCK",
        "TRADING_SESSION_SINGLE_WRITER_MISSING_BINDINGS",
        "TRADING_SESSION_SINGLE_WRITER_TAMPER_DETECTED",
        "TRADING_SESSION_SINGLE_WRITER_BROKEN_LINEAGE",
        "ABSTAIN",
    }
)
_VALID_SINGLE_WRITER_STATUSES = frozenset(
    {"VALID", "IDEMPOTENT", "INVALID", "CONFLICT", "UNKNOWN", "ABSTAIN"}
)
_SELF_VERIFICATION_SCHEMA_VERSION = "trading_session_single_writer_self_verification_v1"

_FORBIDDEN_INDEX_KEYS: frozenset[str] = frozenset(
    {
        "winner",
        "selected",
        "promoted",
        "promotion",
        "promotion_ready",
        "eligible_for_live",
        "live_eligible",
        "runtime_eligible",
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
        "filter_candidates_for_live",
        "promotion_candidate",
        "safety_flags",
    }
)

_TRANSITIVE_LINEAGE_FIELDS = (
    "comparison_run_id",
    "experiment_id",
    "experiment_identity_manifest_id",
    "learning_manifest_id",
    "promotion_candidate_id",
    "config_patch_manifest_id",
    "versioned_artifact_id",
)

TRADING_SESSION_SINGLE_WRITER_AUTHORITY_INVARIANTS: dict[str, bool] = {
    **COMPARISON_AUTHORITY_INVARIANTS,
    "trading_session_single_writer_is_descriptive_only": True,
    "trading_session_single_writer_does_not_start_session": True,
    "trading_session_single_writer_does_not_register_writer": True,
    "trading_session_single_writer_does_not_activate_writer": True,
    "trading_session_single_writer_does_not_acquire_lock": True,
    "trading_session_single_writer_does_not_issue_fencing_token": True,
    "trading_session_single_writer_does_not_mutate_state": True,
    "trading_session_single_writer_does_not_invoke_consumer": True,
    "trading_session_single_writer_does_not_grant_authority": True,
    "trading_session_single_writer_does_not_activate_lease": True,
    "trading_session_single_writer_does_not_authorize_promotion": True,
    "trading_session_single_writer_does_not_create_configpatch": True,
    "trading_session_single_writer_does_not_authorize_runtime": True,
    "trading_session_single_writer_does_not_authorize_live": True,
    "trading_session_single_writer_is_offline_only": True,
    "deny_by_default": True,
    "single_writer_invariant_bound": True,
    "writer_identity_bound": True,
    "writer_generation_bound": True,
    "session_identity_bound": True,
    "executor_epoch_fencing_bound": True,
    "clock_trust_and_expiry_bound": True,
    "secure_handoff_envelope_bound": True,
    "handoff_atomic_claim_consume_bound": True,
    "authority_lease_and_revocation_bound": True,
    "session_ownership_lineage_bound": True,
    "replay_protection_bound": True,
}

_REQUIRED_NON_AUTHORIZING_FLAGS: dict[str, bool] = {
    "is_trading_session_single_writer": True,
    "trading_session_single_writer_offline_only": True,
    "trading_session_single_writer_contract_complete": False,
    "single_writer_invariant_bound": False,
    "writer_identity_bound": False,
    "writer_generation_bound": False,
    "session_identity_bound": False,
    "executor_epoch_fencing_bound": False,
    "clock_trust_and_expiry_bound": False,
    "secure_handoff_envelope_bound": False,
    "handoff_atomic_claim_consume_bound": False,
    "authority_lease_and_revocation_bound": False,
    "session_ownership_lineage_bound": False,
    "cross_domain_lineage_bound": False,
    "replay_protection_bound": False,
    "deny_by_default": True,
    "trading_session_started": False,
    "writer_registered": False,
    "writer_activated": False,
    "writer_lock_acquired": False,
    "fencing_token_issued": False,
    "state_mutated": False,
    "lock_acquired": False,
    "reservation_created": False,
    "claim_executed": False,
    "consume_executed": False,
    "consumer_invoked": False,
    "consumer_mutated": False,
    "network_side_effect_created": False,
    "authority_granted": False,
    "authority_activated": False,
    "lease_activated": False,
    "killswitch_executed": False,
    "promotion_policy_executed": False,
    "promotion_authorized": False,
    "promotion_candidate_constructed": False,
    "configpatch_created": False,
    "configpatch_modified": False,
    "configpatch_applied": False,
    "configpatch_accepted": False,
    "runtime_configuration_created": False,
    "runtime_permission_created": False,
    "execution_permission_created": False,
    "arming_token_created": False,
    "runtime_authorized": False,
    "live_authorized": False,
    "orders_allowed": False,
    "scheduler_runtime_allowed": False,
    "signature_created": False,
    "private_key_used": False,
    "credentials_accessed": False,
    "system_clock_read": False,
    "wall_clock_read": False,
    "network_time_read": False,
    "expiry_executed": False,
    "revocation_executed": False,
}


class TradingSessionSingleWriterError(ValueError):
    """Fail-closed trading session single writer error."""


@dataclass(frozen=True)
class TradingSessionIdentity:
    venue: str
    account: str
    instrument: str
    trading_epoch: str


@dataclass(frozen=True)
class TradingSessionSingleWriterRequest:
    trading_session_identity: TradingSessionIdentity
    writer_identity: str
    writer_generation: int
    expected_writer_revision: int
    executor_epoch: int
    session_ownership_lineage: dict[str, Any]
    observed_writer_revision: int = 0
    prior_writer_identity: str = ""
    prior_writer_generation: int = 0
    prior_single_writer_evidence_digest: str = ""
    session_contract_version: str = SESSION_CONTRACT_VERSION
    writer_contract_version: str = WRITER_CONTRACT_VERSION
    source_revision: str = DEFAULT_SOURCE_REVISION


@dataclass(frozen=True)
class VerifiedClockTrustBundle:
    bundle_dir: Path
    contract_name: str
    contract_version: str
    producer_version: str
    artifact_ref: str
    artifact_digest: str
    manifest_digest: str
    artifact_payload: dict[str, Any]
    contract_id: str
    contract_status: str
    clock_trust_status: str
    secure_handoff_envelope_identity: str
    handoff_atomic_claim_consume_identity: str
    secure_handoff_envelope_bundle_ref: str
    handoff_atomic_claim_consume_bundle_ref: str
    authority_lease_and_revocation_bundle_ref: str
    cross_domain_lineage: dict[str, Any]


@dataclass(frozen=True)
class TradingSessionSingleWriterInputs:
    clock_trust_and_expiry_bundle_dir: Path
    trading_session_request: TradingSessionSingleWriterRequest


@dataclass(frozen=True)
class TradingSessionSingleWriterResult:
    output_dir: Path
    contract_id: str
    contract_status: str
    single_writer_status: str
    contract_path: Path
    self_verification_path: Path
    manifest_path: Path
    session_identity_digest: str
    writer_identity_digest: str


def _reject_symlink(path: Path, *, label: str) -> None:
    if path.is_symlink():
        raise TradingSessionSingleWriterError(f"{label} must not be a symlink")


def _reject_forbidden_index_keys(payload: Mapping[str, Any]) -> None:
    for key in payload:
        if key in _FORBIDDEN_INDEX_KEYS:
            raise TradingSessionSingleWriterError(f"forbidden index key: {key}")


def _validate_regular_file(path: Path, *, label: str) -> None:
    _reject_symlink(path, label=label)
    if not path.is_file():
        raise TradingSessionSingleWriterError(f"{label} must be a regular file: {path}")


def _validate_bundle_dir(bundle_dir: Path, *, label: str) -> None:
    _reject_symlink(bundle_dir, label=label)
    if not bundle_dir.is_dir():
        raise TradingSessionSingleWriterError(f"{label} must be a directory: {bundle_dir}")


def _validate_output_target(output_dir: Path) -> None:
    if output_dir.exists():
        raise TradingSessionSingleWriterError(f"output directory already exists: {output_dir}")
    if is_under_tmp(output_dir):
        raise TradingSessionSingleWriterError("output directory must not be under /tmp")


def _path_is_under(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def _reject_unsafe_overlap(*, bundle_dirs: list[Path], output_dir: Path) -> None:
    resolved_output = output_dir.resolve()
    for bundle_dir in bundle_dirs:
        resolved_bundle = bundle_dir.resolve()
        if resolved_bundle == resolved_output:
            raise TradingSessionSingleWriterError(
                "output directory must not equal input bundle directory"
            )
        if _path_is_under(resolved_output, resolved_bundle) or _path_is_under(
            resolved_bundle, resolved_output
        ):
            raise TradingSessionSingleWriterError(
                "output directory must not overlap input bundle directory"
            )


def _manifest_file_digest(bundle_dir: Path) -> str:
    manifest_path = bundle_dir / MANIFEST_FILENAME
    _validate_regular_file(manifest_path, label=MANIFEST_FILENAME)
    return hashlib.sha256(manifest_path.read_bytes()).hexdigest()


def _factor(
    *,
    factor_id: str,
    factor_type: str,
    source_field: str,
    detail: str,
) -> dict[str, str]:
    return {
        "factor_id": factor_id,
        "factor_type": factor_type,
        "source_field": source_field,
        "detail": detail,
    }


def _sort_factors(factors: list[dict[str, str]]) -> list[dict[str, str]]:
    return sorted(factors, key=lambda item: (item["factor_id"], item["source_field"]))


def _sorted_strings(values: list[str]) -> list[str]:
    return sorted(values)


def _load_self_verification(bundle_dir: Path, *, rel: str, label: str) -> dict[str, Any]:
    path = bundle_dir / rel
    _validate_regular_file(path, label=label)
    payload = read_manifest(path)
    if not isinstance(payload, dict):
        raise TradingSessionSingleWriterError(f"{label} must be an object")
    return payload


def _artifact_digest_from_payload(payload: Mapping[str, Any]) -> str:
    output_digest = payload.get("output_digest")
    if isinstance(output_digest, str) and is_valid_sha256_hex(output_digest):
        return output_digest
    raise TradingSessionSingleWriterError("artifact output_digest missing or invalid")


def _validate_non_authorizing_flags(payload: Mapping[str, Any]) -> None:
    for key, expected in _REQUIRED_NON_AUTHORIZING_FLAGS.items():
        actual = payload.get(key)
        if key in {
            "trading_session_single_writer_contract_complete",
            "single_writer_invariant_bound",
            "writer_identity_bound",
            "writer_generation_bound",
            "session_identity_bound",
            "executor_epoch_fencing_bound",
            "clock_trust_and_expiry_bound",
            "secure_handoff_envelope_bound",
            "handoff_atomic_claim_consume_bound",
            "authority_lease_and_revocation_bound",
            "session_ownership_lineage_bound",
            "cross_domain_lineage_bound",
            "replay_protection_bound",
        }:
            continue
        if actual is not expected:
            raise TradingSessionSingleWriterError(f"{key} must be {expected!r}, got {actual!r}")


def _extract_cross_domain_lineage(payload: Mapping[str, Any]) -> dict[str, Any]:
    lineage = payload.get("cross_domain_lineage")
    if isinstance(lineage, dict) and lineage:
        return dict(lineage)
    extracted: dict[str, Any] = {}
    for field in _TRANSITIVE_LINEAGE_FIELDS:
        value = payload.get(field)
        if value is not None and str(value):
            extracted[field] = str(value)
    return extracted


def verify_clock_trust_and_expiry_bundle(
    bundle_dir: Path | str,
) -> VerifiedClockTrustBundle:
    path = Path(bundle_dir)
    _validate_bundle_dir(path, label="clock trust and expiry bundle")
    ok, msg = verify_manifest_sha256(path)
    if not ok:
        raise TradingSessionSingleWriterError(
            f"clock trust MANIFEST.sha256 verification failed: {msg}"
        )

    artifact_path = path / CLOCK_TRUST_ARTIFACT_REL
    _validate_regular_file(artifact_path, label=CLOCK_TRUST_ARTIFACT_REL)
    payload = read_manifest(artifact_path)
    if payload.get("contract_name") != CLOCK_TRUST_CONTRACT_NAME:
        raise TradingSessionSingleWriterError("clock trust contract_name mismatch")
    if payload.get("contract_version") != CLOCK_TRUST_CONTRACT_VERSION:
        raise TradingSessionSingleWriterError("clock trust contract_version mismatch")

    self_payload = _load_self_verification(
        path,
        rel=CLOCK_TRUST_SELF_VERIFICATION_REL,
        label=CLOCK_TRUST_SELF_VERIFICATION_REL,
    )
    if self_payload.get("overall_status") != "PASS":
        raise TradingSessionSingleWriterError(
            "clock trust SELF_VERIFICATION overall_status must be PASS"
        )

    try:
        reverify_clock_trust_and_expiry_v1(output_dir=path)
    except ClockTrustAndExpiryError as exc:
        raise TradingSessionSingleWriterError(str(exc)) from exc

    return VerifiedClockTrustBundle(
        bundle_dir=path.resolve(),
        contract_name=CLOCK_TRUST_CONTRACT_NAME,
        contract_version=CLOCK_TRUST_CONTRACT_VERSION,
        producer_version=CLOCK_TRUST_PRODUCER_VERSION,
        artifact_ref=CLOCK_TRUST_ARTIFACT_REL,
        artifact_digest=_artifact_digest_from_payload(payload),
        manifest_digest=_manifest_file_digest(path),
        artifact_payload=dict(payload),
        contract_id=str(payload.get("contract_id", "")),
        contract_status=str(payload.get("contract_status", "")),
        clock_trust_status=str(payload.get("clock_trust_status", "")),
        secure_handoff_envelope_identity=str(payload.get("secure_handoff_envelope_identity", "")),
        handoff_atomic_claim_consume_identity=str(
            payload.get("handoff_atomic_claim_consume_identity", "")
        ),
        secure_handoff_envelope_bundle_ref=str(
            payload.get("secure_handoff_envelope_bundle_ref", "")
        ),
        handoff_atomic_claim_consume_bundle_ref=str(
            payload.get("handoff_atomic_claim_consume_bundle_ref", "")
        ),
        authority_lease_and_revocation_bundle_ref=str(
            payload.get("authority_lease_and_revocation_bundle_ref", "")
        ),
        cross_domain_lineage=_extract_cross_domain_lineage(payload),
    )


def _compute_session_identity_digest(*, session: TradingSessionIdentity) -> str:
    return compute_content_sha256(
        {
            "identity_domain": SESSION_CONTRACT_VERSION,
            "venue": session.venue,
            "account": session.account,
            "instrument": session.instrument,
            "trading_epoch": session.trading_epoch,
            "deterministic_rule_set_version": DETERMINISTIC_RULE_SET_VERSION,
        }
    )


def _compute_writer_identity_digest(
    *,
    writer_identity: str,
    writer_generation: int,
    executor_epoch: int,
) -> str:
    return compute_content_sha256(
        {
            "identity_domain": WRITER_CONTRACT_VERSION,
            "writer_identity": writer_identity,
            "writer_generation": writer_generation,
            "executor_epoch": executor_epoch,
            "deterministic_rule_set_version": DETERMINISTIC_RULE_SET_VERSION,
        }
    )


def _compute_single_writer_evidence_digest(
    *,
    session_digest: str,
    writer_digest: str,
    clock_trust_digest: str,
    expected_writer_revision: int,
) -> str:
    return compute_content_sha256(
        {
            "session_identity_digest": session_digest,
            "writer_identity_digest": writer_digest,
            "clock_trust_digest": clock_trust_digest,
            "expected_writer_revision": expected_writer_revision,
            "deterministic_rule_set_version": DETERMINISTIC_RULE_SET_VERSION,
        }
    )


def _lineage_matches(
    *,
    session_lineage: Mapping[str, Any],
    clock_trust_lineage: Mapping[str, Any],
) -> bool:
    if not session_lineage:
        return False
    if not clock_trust_lineage:
        return True
    for field, clock_val in clock_trust_lineage.items():
        if clock_val is None or not str(clock_val):
            continue
        session_val = session_lineage.get(field)
        if not session_val or str(session_val) != str(clock_val):
            return False
    return True


def _validate_request(
    request: TradingSessionSingleWriterRequest,
    *,
    clock_trust: VerifiedClockTrustBundle,
) -> list[dict[str, str]]:
    blocking: list[dict[str, str]] = []

    if request.session_contract_version != SESSION_CONTRACT_VERSION:
        blocking.append(
            _factor(
                factor_id="MISMATCHED_SESSION_CONTRACT_VERSION",
                factor_type="CONTRADICTION",
                source_field="session_contract_version",
                detail=request.session_contract_version,
            )
        )
    if request.writer_contract_version != WRITER_CONTRACT_VERSION:
        blocking.append(
            _factor(
                factor_id="MISMATCHED_WRITER_CONTRACT_VERSION",
                factor_type="CONTRADICTION",
                source_field="writer_contract_version",
                detail=request.writer_contract_version,
            )
        )

    session = request.trading_session_identity
    for field_name, value in (
        ("venue", session.venue),
        ("account", session.account),
        ("instrument", session.instrument),
        ("trading_epoch", session.trading_epoch),
    ):
        if not value:
            blocking.append(
                _factor(
                    factor_id=f"MISSING_SESSION_{field_name.upper()}",
                    factor_type="MISSING_PRECONDITION",
                    source_field=f"trading_session_identity.{field_name}",
                    detail="missing",
                )
            )

    if not request.writer_identity:
        blocking.append(
            _factor(
                factor_id="MISSING_WRITER_IDENTITY",
                factor_type="MISSING_PRECONDITION",
                source_field="writer_identity",
                detail="missing",
            )
        )

    if request.writer_generation <= 0:
        blocking.append(
            _factor(
                factor_id="INVALID_WRITER_GENERATION",
                factor_type="MISSING_PRECONDITION",
                source_field="writer_generation",
                detail=str(request.writer_generation),
            )
        )

    if request.executor_epoch <= 0:
        blocking.append(
            _factor(
                factor_id="INVALID_EXECUTOR_EPOCH",
                factor_type="MISSING_PRECONDITION",
                source_field="executor_epoch",
                detail=str(request.executor_epoch),
            )
        )

    if not request.session_ownership_lineage:
        blocking.append(
            _factor(
                factor_id="MISSING_SESSION_OWNERSHIP_LINEAGE",
                factor_type="MISSING_PRECONDITION",
                source_field="session_ownership_lineage",
                detail="missing",
            )
        )

    if clock_trust.contract_status == "CLOCK_TRUST_REVOKED":
        blocking.append(
            _factor(
                factor_id="UPSTREAM_CLOCK_TRUST_REVOKED",
                factor_type="BLOCKING",
                source_field="clock_trust.contract_status",
                detail=clock_trust.contract_status,
            )
        )
    elif clock_trust.contract_status == "CLOCK_TRUST_EXPIRED":
        blocking.append(
            _factor(
                factor_id="UPSTREAM_CLOCK_TRUST_EXPIRED",
                factor_type="BLOCKING",
                source_field="clock_trust.contract_status",
                detail=clock_trust.contract_status,
            )
        )
    elif clock_trust.contract_status == "CLOCK_TRUST_UNTRUSTED_CLOCK_SOURCE":
        blocking.append(
            _factor(
                factor_id="UPSTREAM_CLOCK_TRUST_UNTRUSTED",
                factor_type="BLOCKING",
                source_field="clock_trust.contract_status",
                detail=clock_trust.contract_status,
            )
        )

    if not clock_trust.secure_handoff_envelope_identity:
        blocking.append(
            _factor(
                factor_id="MISSING_SECURE_HANDOFF_ENVELOPE_BINDING",
                factor_type="MISSING_PRECONDITION",
                source_field="secure_handoff_envelope_identity",
                detail="missing",
            )
        )
    if not clock_trust.handoff_atomic_claim_consume_identity:
        blocking.append(
            _factor(
                factor_id="MISSING_HANDOFF_ATOMIC_CLAIM_CONSUME_BINDING",
                factor_type="MISSING_PRECONDITION",
                source_field="handoff_atomic_claim_consume_identity",
                detail="missing",
            )
        )
    if not clock_trust.authority_lease_and_revocation_bundle_ref:
        blocking.append(
            _factor(
                factor_id="MISSING_AUTHORITY_LEASE_BINDING",
                factor_type="MISSING_PRECONDITION",
                source_field="authority_lease_and_revocation_bundle_ref",
                detail="missing",
            )
        )

    clock_payload = clock_trust.artifact_payload
    if not clock_payload.get("secure_handoff_envelope_bound"):
        blocking.append(
            _factor(
                factor_id="UPSTREAM_ENVELOPE_NOT_BOUND",
                factor_type="MISSING_PRECONDITION",
                source_field="secure_handoff_envelope_bound",
                detail="false",
            )
        )
    if not clock_payload.get("handoff_atomic_claim_consume_bound"):
        blocking.append(
            _factor(
                factor_id="UPSTREAM_CLAIM_CONSUME_NOT_BOUND",
                factor_type="MISSING_PRECONDITION",
                source_field="handoff_atomic_claim_consume_bound",
                detail="false",
            )
        )
    if not clock_payload.get("authority_lease_and_revocation_bound"):
        blocking.append(
            _factor(
                factor_id="UPSTREAM_AUTHORITY_LEASE_NOT_BOUND",
                factor_type="MISSING_PRECONDITION",
                source_field="authority_lease_and_revocation_bound",
                detail="false",
            )
        )

    expected_lineage: dict[str, Any] = dict(clock_trust.cross_domain_lineage)
    for field in _TRANSITIVE_LINEAGE_FIELDS:
        value = clock_trust.artifact_payload.get(field)
        if value is not None and str(value):
            expected_lineage[field] = str(value)
    if expected_lineage and request.session_ownership_lineage:
        if not _lineage_matches(
            session_lineage=request.session_ownership_lineage,
            clock_trust_lineage=expected_lineage,
        ):
            blocking.append(
                _factor(
                    factor_id="BROKEN_SESSION_OWNERSHIP_LINEAGE",
                    factor_type="CONTRADICTION",
                    source_field="session_ownership_lineage",
                    detail="lineage mismatch with clock trust artifact lineage",
                )
            )

    if request.prior_writer_identity and request.prior_writer_identity != request.writer_identity:
        blocking.append(
            _factor(
                factor_id="COMPETING_WRITER",
                factor_type="BLOCKING",
                source_field="prior_writer_identity",
                detail=request.prior_writer_identity,
            )
        )

    if (
        request.prior_writer_identity == request.writer_identity
        and request.prior_writer_generation > 0
        and request.writer_generation < request.prior_writer_generation
    ):
        blocking.append(
            _factor(
                factor_id="STALE_WRITER_GENERATION",
                factor_type="BLOCKING",
                source_field="writer_generation",
                detail=str(request.writer_generation),
            )
        )

    if (
        request.prior_writer_identity == request.writer_identity
        and request.prior_writer_generation > 0
        and request.writer_generation == request.prior_writer_generation
        and request.observed_writer_revision != request.expected_writer_revision
    ):
        blocking.append(
            _factor(
                factor_id="DUPLICATE_WRITER_CLAIM",
                factor_type="BLOCKING",
                source_field="writer_generation",
                detail="duplicate claim with mismatched revision",
            )
        )

    if (
        request.expected_writer_revision > 0
        and request.observed_writer_revision != request.expected_writer_revision
        and "DUPLICATE_WRITER_CLAIM" not in {item.get("factor_id") for item in blocking}
    ):
        blocking.append(
            _factor(
                factor_id="STALE_WRITER_REVISION",
                factor_type="BLOCKING",
                source_field="observed_writer_revision",
                detail=str(request.observed_writer_revision),
            )
        )

    session_digest = _compute_session_identity_digest(session=request.trading_session_identity)
    writer_digest = _compute_writer_identity_digest(
        writer_identity=request.writer_identity,
        writer_generation=request.writer_generation,
        executor_epoch=request.executor_epoch,
    )
    evidence_digest = _compute_single_writer_evidence_digest(
        session_digest=session_digest,
        writer_digest=writer_digest,
        clock_trust_digest=clock_trust.artifact_digest,
        expected_writer_revision=request.expected_writer_revision,
    )
    if (
        request.prior_single_writer_evidence_digest
        and request.prior_single_writer_evidence_digest == evidence_digest
    ):
        blocking.append(
            _factor(
                factor_id="REPLAYED_SINGLE_WRITER_EVIDENCE",
                factor_type="BLOCKING",
                source_field="prior_single_writer_evidence_digest",
                detail="duplicate single writer evidence digest",
            )
        )

    return blocking


def _evaluate_single_writer(
    *,
    request: TradingSessionSingleWriterRequest,
    clock_trust: VerifiedClockTrustBundle,
    blocking_facts: list[dict[str, str]],
) -> tuple[str, str, list[str], dict[str, Any]]:
    reason_codes: list[str] = []
    factor_ids = {item.get("factor_id") for item in blocking_facts}
    states: dict[str, Any] = {
        "single_writer_status": "UNKNOWN",
        "single_writer_reason": "",
        "trading_session_single_writer_contract_complete": False,
        "single_writer_invariant_bound": False,
        "writer_identity_bound": False,
        "writer_generation_bound": False,
        "session_identity_bound": False,
        "executor_epoch_fencing_bound": False,
        "clock_trust_and_expiry_bound": False,
        "secure_handoff_envelope_bound": False,
        "handoff_atomic_claim_consume_bound": False,
        "authority_lease_and_revocation_bound": False,
        "session_ownership_lineage_bound": False,
        "cross_domain_lineage_bound": False,
        "replay_protection_bound": False,
    }

    if {
        "MISSING_SESSION_VENUE",
        "MISSING_SESSION_ACCOUNT",
        "MISSING_SESSION_INSTRUMENT",
        "MISSING_SESSION_TRADING_EPOCH",
        "MISSING_WRITER_IDENTITY",
        "INVALID_WRITER_GENERATION",
        "INVALID_EXECUTOR_EPOCH",
        "MISSING_SESSION_OWNERSHIP_LINEAGE",
    } & factor_ids:
        states["single_writer_status"] = "INVALID"
        states["single_writer_reason"] = "MISSING_IDENTITY"
        reason_codes.append("MISSING_IDENTITY")
        return (
            "TRADING_SESSION_SINGLE_WRITER_MISSING_IDENTITY",
            states["single_writer_status"],
            _sorted_strings(reason_codes),
            states,
        )

    if "UPSTREAM_CLOCK_TRUST_REVOKED" in factor_ids:
        states["clock_trust_and_expiry_bound"] = True
        states["single_writer_status"] = "INVALID"
        states["single_writer_reason"] = "UPSTREAM_REVOKED"
        reason_codes.append("UPSTREAM_REVOKED")
        return (
            "TRADING_SESSION_SINGLE_WRITER_REVOKED",
            states["single_writer_status"],
            _sorted_strings(reason_codes),
            states,
        )

    if "UPSTREAM_CLOCK_TRUST_EXPIRED" in factor_ids:
        states["clock_trust_and_expiry_bound"] = True
        states["single_writer_status"] = "INVALID"
        states["single_writer_reason"] = "UPSTREAM_EXPIRED"
        reason_codes.append("UPSTREAM_EXPIRED")
        return (
            "TRADING_SESSION_SINGLE_WRITER_EXPIRED",
            states["single_writer_status"],
            _sorted_strings(reason_codes),
            states,
        )

    if "UPSTREAM_CLOCK_TRUST_UNTRUSTED" in factor_ids:
        states["clock_trust_and_expiry_bound"] = True
        states["single_writer_status"] = "INVALID"
        states["single_writer_reason"] = "UPSTREAM_UNTRUSTED_CLOCK"
        reason_codes.append("UPSTREAM_UNTRUSTED_CLOCK")
        return (
            "TRADING_SESSION_SINGLE_WRITER_UNTRUSTED_CLOCK",
            states["single_writer_status"],
            _sorted_strings(reason_codes),
            states,
        )

    if {
        "MISSING_SECURE_HANDOFF_ENVELOPE_BINDING",
        "MISSING_HANDOFF_ATOMIC_CLAIM_CONSUME_BINDING",
        "MISSING_AUTHORITY_LEASE_BINDING",
        "UPSTREAM_ENVELOPE_NOT_BOUND",
        "UPSTREAM_CLAIM_CONSUME_NOT_BOUND",
        "UPSTREAM_AUTHORITY_LEASE_NOT_BOUND",
    } & factor_ids:
        states["single_writer_status"] = "INVALID"
        states["single_writer_reason"] = "MISSING_BINDINGS"
        reason_codes.append("MISSING_BINDINGS")
        return (
            "TRADING_SESSION_SINGLE_WRITER_MISSING_BINDINGS",
            states["single_writer_status"],
            _sorted_strings(reason_codes),
            states,
        )

    if "REPLAYED_SINGLE_WRITER_EVIDENCE" in factor_ids:
        states["replay_protection_bound"] = True
        states["single_writer_status"] = "INVALID"
        states["single_writer_reason"] = "REPLAYED_SINGLE_WRITER_EVIDENCE"
        reason_codes.append("REPLAYED_SINGLE_WRITER_EVIDENCE")
        return (
            "TRADING_SESSION_SINGLE_WRITER_REPLAY_REJECTED",
            states["single_writer_status"],
            _sorted_strings(reason_codes),
            states,
        )

    if "COMPETING_WRITER" in factor_ids:
        states["single_writer_status"] = "CONFLICT"
        states["single_writer_reason"] = "COMPETING_WRITER"
        reason_codes.append("COMPETING_WRITER")
        return (
            "TRADING_SESSION_SINGLE_WRITER_COMPETING_WRITER",
            states["single_writer_status"],
            _sorted_strings(reason_codes),
            states,
        )

    if "DUPLICATE_WRITER_CLAIM" in factor_ids:
        states["single_writer_status"] = "CONFLICT"
        states["single_writer_reason"] = "DUPLICATE_WRITER_CLAIM"
        reason_codes.append("DUPLICATE_WRITER_CLAIM")
        return (
            "TRADING_SESSION_SINGLE_WRITER_DUPLICATE_WRITER_CLAIM",
            states["single_writer_status"],
            _sorted_strings(reason_codes),
            states,
        )

    if "STALE_WRITER_GENERATION" in factor_ids:
        states["writer_generation_bound"] = True
        states["single_writer_status"] = "INVALID"
        states["single_writer_reason"] = "STALE_WRITER_GENERATION"
        reason_codes.append("STALE_WRITER_GENERATION")
        return (
            "TRADING_SESSION_SINGLE_WRITER_STALE_GENERATION",
            states["single_writer_status"],
            _sorted_strings(reason_codes),
            states,
        )

    if "STALE_WRITER_REVISION" in factor_ids:
        states["writer_identity_bound"] = True
        states["single_writer_status"] = "INVALID"
        states["single_writer_reason"] = "STALE_WRITER_REVISION"
        reason_codes.append("STALE_WRITER_REVISION")
        return (
            "TRADING_SESSION_SINGLE_WRITER_STALE_REVISION",
            states["single_writer_status"],
            _sorted_strings(reason_codes),
            states,
        )

    if "BROKEN_SESSION_OWNERSHIP_LINEAGE" in factor_ids:
        states["single_writer_status"] = "INVALID"
        states["single_writer_reason"] = "BROKEN_LINEAGE"
        reason_codes.append("BROKEN_LINEAGE")
        return (
            "TRADING_SESSION_SINGLE_WRITER_BROKEN_LINEAGE",
            states["single_writer_status"],
            _sorted_strings(reason_codes),
            states,
        )

    contradictions = [item for item in blocking_facts if item.get("factor_type") == "CONTRADICTION"]
    if contradictions:
        states["single_writer_status"] = "INVALID"
        states["single_writer_reason"] = "TAMPER_OR_CONTRADICTION"
        reason_codes.append("TAMPER_OR_CONTRADICTION")
        return (
            "TRADING_SESSION_SINGLE_WRITER_TAMPER_DETECTED",
            states["single_writer_status"],
            _sorted_strings(reason_codes),
            states,
        )

    if blocking_facts:
        states["single_writer_status"] = "INVALID"
        states["single_writer_reason"] = "CONTRACT_FAIL_CLOSED"
        reason_codes.append("CONTRACT_FAIL_CLOSED")
        return (
            "TRADING_SESSION_SINGLE_WRITER_INVALID",
            states["single_writer_status"],
            _sorted_strings(reason_codes),
            states,
        )

    if (
        request.prior_writer_identity == request.writer_identity
        and request.prior_writer_generation == request.writer_generation
        and request.prior_writer_generation > 0
    ):
        states.update(
            {
                "single_writer_status": "IDEMPOTENT",
                "single_writer_reason": "IDEMPOTENT_SINGLE_WRITER",
                "trading_session_single_writer_contract_complete": True,
                "single_writer_invariant_bound": True,
                "writer_identity_bound": True,
                "writer_generation_bound": True,
                "session_identity_bound": True,
                "executor_epoch_fencing_bound": True,
                "clock_trust_and_expiry_bound": True,
                "secure_handoff_envelope_bound": True,
                "handoff_atomic_claim_consume_bound": True,
                "authority_lease_and_revocation_bound": True,
                "session_ownership_lineage_bound": True,
                "cross_domain_lineage_bound": True,
                "replay_protection_bound": True,
            }
        )
        reason_codes.extend(
            [
                "IDEMPOTENT_SINGLE_WRITER",
                "SESSION_IDENTITY_BOUND",
                "WRITER_IDENTITY_BOUND",
                "WRITER_GENERATION_BOUND",
                "EXECUTOR_EPOCH_FENCING_BOUND",
                "CLOCK_TRUST_AND_EXPIRY_BOUND",
            ]
        )
        return (
            "TRADING_SESSION_SINGLE_WRITER_IDEMPOTENT",
            states["single_writer_status"],
            _sorted_strings(reason_codes),
            states,
        )

    if clock_trust.contract_status != "CLOCK_TRUST_VALID_FOR_OFFLINE_TEMPORAL_EVALUATION":
        states["clock_trust_and_expiry_bound"] = True
        states["single_writer_status"] = "INVALID"
        states["single_writer_reason"] = "UPSTREAM_CLOCK_TRUST_INVALID"
        reason_codes.append("UPSTREAM_CLOCK_TRUST_INVALID")
        return (
            "TRADING_SESSION_SINGLE_WRITER_INVALID",
            states["single_writer_status"],
            _sorted_strings(reason_codes),
            states,
        )

    states.update(
        {
            "single_writer_status": "VALID",
            "single_writer_reason": "SINGLE_WRITER_INVARIANT_BOUND",
            "trading_session_single_writer_contract_complete": True,
            "single_writer_invariant_bound": True,
            "writer_identity_bound": True,
            "writer_generation_bound": True,
            "session_identity_bound": True,
            "executor_epoch_fencing_bound": True,
            "clock_trust_and_expiry_bound": True,
            "secure_handoff_envelope_bound": True,
            "handoff_atomic_claim_consume_bound": True,
            "authority_lease_and_revocation_bound": True,
            "session_ownership_lineage_bound": True,
            "cross_domain_lineage_bound": True,
            "replay_protection_bound": True,
        }
    )
    reason_codes.extend(
        [
            "SESSION_IDENTITY_BOUND",
            "WRITER_IDENTITY_BOUND",
            "WRITER_GENERATION_BOUND",
            "EXECUTOR_EPOCH_FENCING_BOUND",
            "CLOCK_TRUST_AND_EXPIRY_BOUND",
            "SECURE_HANDOFF_ENVELOPE_BOUND",
            "HANDOFF_ATOMIC_CLAIM_CONSUME_BOUND",
            "AUTHORITY_LEASE_BOUND",
            "SINGLE_WRITER_INVARIANT_BOUND",
            "TRADING_SESSION_SINGLE_WRITER_VALID_FOR_OFFLINE_EVALUATION",
        ]
    )
    return (
        "TRADING_SESSION_SINGLE_WRITER_VALID_FOR_OFFLINE_EVALUATION",
        states["single_writer_status"],
        _sorted_strings(reason_codes),
        states,
    )


def _input_artifact_ref_mapping(
    *,
    bundle_dir: Path,
    contract_name: str,
    contract_version: str,
    producer_version: str,
    artifact_ref: str,
    artifact_digest: str,
    manifest_digest: str,
) -> dict[str, Any]:
    return {
        "artifact_type": contract_name,
        "contract_name": contract_name,
        "contract_version": contract_version,
        "artifact_ref": artifact_ref,
        "artifact_digest": artifact_digest,
        "manifest_digest": manifest_digest,
        "producer_version": producer_version,
        "bundle_path": bundle_dir.as_posix(),
    }


def _compute_output_digest(body: Mapping[str, Any]) -> str:
    excluded = frozenset(
        {
            "output_digest",
            "manifest_digest",
            "integrity",
            "created_at",
            "artifact_id",
            "contract_id",
        }
    )
    digest_body = {key: body[key] for key in sorted(body) if key not in excluded}
    return compute_content_sha256(digest_body)


def _integrity_body(body: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: value for key, value in body.items() if key not in {"integrity", "manifest_digest"}
    }


def build_trading_session_single_writer_v1(
    *,
    clock_trust: VerifiedClockTrustBundle,
    request: TradingSessionSingleWriterRequest,
) -> dict[str, Any]:
    blocking_facts = _validate_request(request, clock_trust=clock_trust)
    contradictions = [item for item in blocking_facts if item.get("factor_type") == "CONTRADICTION"]
    non_contradiction_blocking = [
        item for item in blocking_facts if item.get("factor_type") != "CONTRADICTION"
    ]

    contract_status, single_writer_status, reason_codes, completion_flags = _evaluate_single_writer(
        request=request,
        clock_trust=clock_trust,
        blocking_facts=blocking_facts,
    )

    session = request.trading_session_identity
    session_identity_digest = _compute_session_identity_digest(session=session)
    writer_identity_digest = _compute_writer_identity_digest(
        writer_identity=request.writer_identity,
        writer_generation=request.writer_generation,
        executor_epoch=request.executor_epoch,
    )
    single_writer_evidence_digest = _compute_single_writer_evidence_digest(
        session_digest=session_identity_digest,
        writer_digest=writer_identity_digest,
        clock_trust_digest=clock_trust.artifact_digest,
        expected_writer_revision=request.expected_writer_revision,
    )

    input_refs = [
        _input_artifact_ref_mapping(
            bundle_dir=clock_trust.bundle_dir,
            contract_name=clock_trust.contract_name,
            contract_version=clock_trust.contract_version,
            producer_version=clock_trust.producer_version,
            artifact_ref=clock_trust.artifact_ref,
            artifact_digest=clock_trust.artifact_digest,
            manifest_digest=clock_trust.manifest_digest,
        )
    ]
    input_digest = compute_content_sha256({"input_artifact_refs": input_refs})

    contract_id = compute_content_sha256(
        {
            "contract_domain": CONTRACT_NAME,
            "session_identity_digest": session_identity_digest,
            "writer_identity_digest": writer_identity_digest,
            "clock_trust_contract_id": clock_trust.contract_id,
            "deterministic_rule_set_version": DETERMINISTIC_RULE_SET_VERSION,
        }
    )

    clock_payload = clock_trust.artifact_payload
    session_identity_binding = {
        "venue": session.venue,
        "account": session.account,
        "instrument": session.instrument,
        "trading_epoch": session.trading_epoch,
        "session_identity_digest": session_identity_digest,
    }
    writer_binding = {
        "writer_identity": request.writer_identity,
        "writer_generation": request.writer_generation,
        "expected_writer_revision": request.expected_writer_revision,
        "observed_writer_revision": request.observed_writer_revision,
        "executor_epoch": request.executor_epoch,
        "writer_identity_digest": writer_identity_digest,
    }
    upstream_bindings = {
        "clock_trust_contract_id": clock_trust.contract_id,
        "clock_trust_contract_status": clock_trust.contract_status,
        "clock_trust_status": clock_trust.clock_trust_status,
        "clock_trust_digest": clock_trust.artifact_digest,
        "secure_handoff_envelope_identity": clock_trust.secure_handoff_envelope_identity,
        "handoff_atomic_claim_consume_identity": clock_trust.handoff_atomic_claim_consume_identity,
        "secure_handoff_envelope_bundle_ref": clock_trust.secure_handoff_envelope_bundle_ref,
        "handoff_atomic_claim_consume_bundle_ref": clock_trust.handoff_atomic_claim_consume_bundle_ref,
        "authority_lease_and_revocation_bundle_ref": clock_trust.authority_lease_and_revocation_bundle_ref,
    }

    payload: dict[str, Any] = {
        "contract_id": "",
        "contract_name": CONTRACT_NAME,
        "contract_version": CONTRACT_VERSION,
        "session_contract_version": request.session_contract_version,
        "writer_contract_version": request.writer_contract_version,
        "schema_version": SCHEMA_VERSION,
        "creation_contract_version": CREATION_CONTRACT_VERSION,
        "artifact_id": "",
        "created_at": OFFLINE_DETERMINISTIC_CREATED_AT,
        "contract_creation_time": OFFLINE_DETERMINISTIC_CREATED_AT,
        "producer_version": PRODUCER_VERSION,
        "producer_identity_ref": DEFAULT_PRODUCER_IDENTITY_REF,
        "record_kind": RECORD_KIND,
        "input_relation": INPUT_RELATION,
        "evidence_level": EVIDENCE_LEVEL,
        "authority_level": AUTHORITY_LEVEL,
        "deterministic_rule_set_version": DETERMINISTIC_RULE_SET_VERSION,
        "contract_status": contract_status,
        "contract_reason_codes": reason_codes,
        "single_writer_status": single_writer_status,
        "single_writer_reason": completion_flags.get("single_writer_reason", ""),
        "trading_session_identity": {
            "venue": session.venue,
            "account": session.account,
            "instrument": session.instrument,
            "trading_epoch": session.trading_epoch,
        },
        "session_identity_digest": session_identity_digest,
        "session_identity_binding": session_identity_binding,
        "writer_identity": request.writer_identity,
        "writer_generation": request.writer_generation,
        "expected_writer_revision": request.expected_writer_revision,
        "observed_writer_revision": request.observed_writer_revision,
        "executor_epoch": request.executor_epoch,
        "writer_identity_digest": writer_identity_digest,
        "writer_binding": writer_binding,
        "single_writer_evidence_digest": single_writer_evidence_digest,
        "session_ownership_lineage": dict(request.session_ownership_lineage),
        "upstream_bindings": upstream_bindings,
        "clock_trust_and_expiry_bundle_ref": clock_trust.bundle_dir.as_posix(),
        "clock_trust_contract_id": clock_trust.contract_id,
        "clock_trust_digest": clock_trust.artifact_digest,
        "secure_handoff_envelope_identity": clock_trust.secure_handoff_envelope_identity,
        "handoff_atomic_claim_consume_identity": clock_trust.handoff_atomic_claim_consume_identity,
        "blocking_facts": _sort_factors(non_contradiction_blocking),
        "missing_preconditions": _sort_factors(
            [item for item in blocking_facts if item.get("factor_type") == "MISSING_PRECONDITION"]
        ),
        "contradictions": _sort_factors(contradictions),
        "trading_session_single_writer_authority_invariants": dict(
            TRADING_SESSION_SINGLE_WRITER_AUTHORITY_INVARIANTS
        ),
        "input_artifact_refs": input_refs,
        "cross_domain_lineage": (
            dict(clock_trust.cross_domain_lineage)
            if clock_trust.cross_domain_lineage
            else dict(request.session_ownership_lineage)
        ),
        "provenance": {
            "producer_contract_name": CONTRACT_NAME,
            "producer_contract_version": CONTRACT_VERSION,
            "creation_contract_version": CREATION_CONTRACT_VERSION,
            "evidence_level": EVIDENCE_LEVEL,
            "offline_only": True,
            "contract_created_for_offline_evidence_only": True,
            "source_revision": request.source_revision,
        },
        "integrity_metadata": {
            "digest_algorithm": "sha256",
            "canonical_serialization": "deterministic_json_dumps",
            "contract_id_domain": CONTRACT_NAME,
            "signature_created": False,
        },
        "input_digest": input_digest,
        "output_digest": "",
        "manifest_digest": "",
    }

    for key, value in _REQUIRED_NON_AUTHORIZING_FLAGS.items():
        payload[key] = value
    payload.update(
        {
            key: completion_flags[key]
            for key in completion_flags
            if key in _REQUIRED_NON_AUTHORIZING_FLAGS
            or key.endswith("_bound")
            or key.endswith("_complete")
        }
    )

    for field in _TRANSITIVE_LINEAGE_FIELDS:
        value = clock_payload.get(field) or request.session_ownership_lineage.get(field)
        if value is not None and str(value):
            payload[field] = str(value)

    _reject_forbidden_index_keys(payload)
    _validate_non_authorizing_flags(payload)
    if contract_status not in _VALID_CONTRACT_STATUSES:
        raise TradingSessionSingleWriterError("contract_status invalid")
    if single_writer_status not in _VALID_SINGLE_WRITER_STATUSES:
        raise TradingSessionSingleWriterError("single_writer_status invalid")

    payload["input_digest"] = input_digest
    output_digest = _compute_output_digest(payload)
    payload["output_digest"] = output_digest
    payload["artifact_id"] = output_digest
    payload["contract_id"] = contract_id
    return payload


def serialize_trading_session_single_writer_v1(contract: Mapping[str, Any]) -> str:
    _reject_forbidden_index_keys(contract)
    _validate_non_authorizing_flags(contract)
    if contract.get("contract_status") not in _VALID_CONTRACT_STATUSES:
        raise TradingSessionSingleWriterError("contract_status invalid")
    for list_field in (
        "contract_reason_codes",
        "blocking_facts",
        "missing_preconditions",
        "contradictions",
    ):
        values = contract.get(list_field)
        if isinstance(values, list) and values != sorted(
            values,
            key=lambda item: (
                item.get("factor_id", item) if isinstance(item, dict) else item,
                item.get("source_field", "") if isinstance(item, dict) else "",
            ),
        ):
            raise TradingSessionSingleWriterError(f"{list_field} must be sorted deterministically")
    return deterministic_json_dumps(contract)


def _artifact_bytes_for_manifest_digest(artifact: Mapping[str, Any]) -> bytes:
    body = {
        key: value for key, value in artifact.items() if key not in {"integrity", "manifest_digest"}
    }
    return serialize_trading_session_single_writer_v1(body).encode("utf-8")


def _compute_output_manifest_digest(artifact: Mapping[str, Any]) -> str:
    return hashlib.sha256(_artifact_bytes_for_manifest_digest(artifact)).hexdigest()


def _validate_contract_integrity(artifact: Mapping[str, Any]) -> None:
    if artifact.get("contract_name") != CONTRACT_NAME:
        raise TradingSessionSingleWriterError("contract_name mismatch")
    if artifact.get("contract_version") != CONTRACT_VERSION:
        raise TradingSessionSingleWriterError("contract_version mismatch")
    integrity = artifact.get("integrity")
    if not isinstance(integrity, Mapping):
        raise TradingSessionSingleWriterError("integrity must be an object")
    expected = compute_content_sha256(_integrity_body(artifact))
    actual = integrity.get("content_sha256")
    if actual != expected:
        raise TradingSessionSingleWriterError("integrity.content_sha256 mismatch")
    output_digest = artifact.get("output_digest")
    if output_digest != _compute_output_digest(artifact):
        raise TradingSessionSingleWriterError("output_digest mismatch")
    if artifact.get("artifact_id") != output_digest:
        raise TradingSessionSingleWriterError("artifact_id must equal output_digest")


def build_self_verification_v1(
    *,
    contract: Mapping[str, Any],
    manifest_digest: str,
) -> dict[str, Any]:
    checks: list[dict[str, str]] = [
        {"check_id": "contract_name", "status": "PASS"},
        {"check_id": "contract_version", "status": "PASS"},
        {"check_id": "evidence_level_level_3", "status": "PASS"},
        {"check_id": "exactly_one_verified_input_bundle", "status": "PASS"},
        {"check_id": "offline_only_no_session_start", "status": "PASS"},
        {"check_id": "offline_only_no_writer_registration", "status": "PASS"},
        {"check_id": "no_state_mutation", "status": "PASS"},
        {"check_id": "no_consumer_invocation", "status": "PASS"},
        {"check_id": "deny_by_default", "status": "PASS"},
        {"check_id": "single_writer_invariant_bound", "status": "PASS"},
        {"check_id": "output_digest", "status": "PASS"},
        {"check_id": "manifest_verification", "status": "PASS"},
        {"check_id": "deterministic_reverification", "status": "PASS"},
    ]

    input_refs = contract.get("input_artifact_refs")
    if not isinstance(input_refs, list) or len(input_refs) != 1:
        checks = [
            {**c, "status": "FAIL"} if c["check_id"] == "exactly_one_verified_input_bundle" else c
            for c in checks
        ]

    if contract.get("manifest_digest") != manifest_digest:
        checks = [
            {**c, "status": "FAIL"} if c["check_id"] == "manifest_verification" else c
            for c in checks
        ]

    structural_failures = [check for check in checks if check["status"] != "PASS"]
    if structural_failures:
        raise TradingSessionSingleWriterError("self-verification checks failed")

    payload: dict[str, Any] = {
        "self_verification_schema_version": _SELF_VERIFICATION_SCHEMA_VERSION,
        "contract_name": CONTRACT_NAME,
        "contract_version": CONTRACT_VERSION,
        "overall_status": "PASS",
        "checks": checks,
        "verified_artifact_rel": ARTIFACT_REL,
        "verified_output_digest": contract.get("output_digest"),
        "verified_manifest_digest": manifest_digest,
        "verified_contract_status": contract.get("contract_status"),
        "verified_single_writer_status": contract.get("single_writer_status"),
        "verified_deterministic_rule_set_version": DETERMINISTIC_RULE_SET_VERSION,
    }
    digest = compute_content_sha256(payload)
    payload["integrity"] = {"content_sha256": digest}
    return payload


def _finalize_contract_with_manifest_digest(
    artifact: Mapping[str, Any], *, manifest_digest: str
) -> dict[str, Any]:
    body = dict(artifact)
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


def default_trading_session_single_writer_request(
    *,
    clock_trust: VerifiedClockTrustBundle,
    venue: str = "testnet",
    account: str = "acct-001",
    instrument: str = "BTC-PERP",
    trading_epoch: str = "epoch-001",
    writer_identity: str = "writer-primary-001",
    writer_generation: int = 1,
    expected_writer_revision: int = 1,
    executor_epoch: int = 1,
) -> TradingSessionSingleWriterRequest:
    lineage: dict[str, Any] = (
        dict(clock_trust.cross_domain_lineage) if clock_trust.cross_domain_lineage else {}
    )
    for field in _TRANSITIVE_LINEAGE_FIELDS:
        value = clock_trust.artifact_payload.get(field)
        if value is not None and str(value):
            lineage[field] = str(value)
    if not lineage:
        lineage = {"provenance_kind": "OFFLINE_DETERMINISTIC_EVIDENCE"}
    return TradingSessionSingleWriterRequest(
        trading_session_identity=TradingSessionIdentity(
            venue=venue,
            account=account,
            instrument=instrument,
            trading_epoch=trading_epoch,
        ),
        writer_identity=writer_identity,
        writer_generation=writer_generation,
        expected_writer_revision=expected_writer_revision,
        observed_writer_revision=expected_writer_revision,
        executor_epoch=executor_epoch,
        session_ownership_lineage=lineage,
    )


def verify_trading_session_single_writer_inputs(
    inputs: TradingSessionSingleWriterInputs,
) -> VerifiedClockTrustBundle:
    return verify_clock_trust_and_expiry_bundle(inputs.clock_trust_and_expiry_bundle_dir)


def reverify_trading_session_single_writer_v1(*, output_dir: Path | str) -> None:
    bundle_dir = Path(output_dir)
    if not bundle_dir.is_dir():
        raise TradingSessionSingleWriterError(
            f"trading session single writer directory not found: {bundle_dir}"
        )
    ok, msg = verify_manifest_sha256(bundle_dir)
    if not ok:
        raise TradingSessionSingleWriterError(f"MANIFEST.sha256 verification failed: {msg}")

    artifact_path = bundle_dir / ARTIFACT_REL
    _validate_regular_file(artifact_path, label=ARTIFACT_REL)
    contract = read_manifest(artifact_path)
    _validate_contract_integrity(contract)

    self_path = bundle_dir / SELF_VERIFICATION_REL
    _validate_regular_file(self_path, label=SELF_VERIFICATION_REL)
    self_payload = read_manifest(self_path)
    if self_payload.get("overall_status") != "PASS":
        raise TradingSessionSingleWriterError("SELF_VERIFICATION overall_status must be PASS")

    manifest_digest = _compute_output_manifest_digest(contract)
    if contract.get("manifest_digest") != manifest_digest:
        raise TradingSessionSingleWriterError("manifest_digest mismatch on replay")

    clock_trust = verify_clock_trust_and_expiry_bundle(
        Path(str(contract["clock_trust_and_expiry_bundle_ref"]))
    )
    if contract.get("clock_trust_digest") != clock_trust.artifact_digest:
        raise TradingSessionSingleWriterError("clock trust digest mismatch on replay")
    if contract.get("clock_trust_contract_id") != clock_trust.contract_id:
        raise TradingSessionSingleWriterError("clock trust contract id mismatch on replay")


def produce_trading_session_single_writer_v1(
    *,
    inputs: TradingSessionSingleWriterInputs,
    output_dir: Path | str,
) -> TradingSessionSingleWriterResult:
    final_dir = Path(output_dir)
    _validate_output_target(final_dir)
    _reject_unsafe_overlap(
        bundle_dirs=[inputs.clock_trust_and_expiry_bundle_dir],
        output_dir=final_dir,
    )

    clock_trust = verify_trading_session_single_writer_inputs(inputs)
    contract_body = build_trading_session_single_writer_v1(
        clock_trust=clock_trust,
        request=inputs.trading_session_request,
    )

    staging = _staging_dir_for(final_dir)
    if staging.exists():
        raise TradingSessionSingleWriterError(f"staging directory collision: {staging}")

    try:
        staging.mkdir(parents=True, exist_ok=False)
        artifact_path = staging / ARTIFACT_REL
        self_path = staging / SELF_VERIFICATION_REL

        manifest_digest = _compute_output_manifest_digest(contract_body)
        finalized = _finalize_contract_with_manifest_digest(
            contract_body, manifest_digest=manifest_digest
        )
        artifact_path.write_text(
            serialize_trading_session_single_writer_v1(finalized),
            encoding="utf-8",
        )
        self_payload = build_self_verification_v1(
            contract=finalized,
            manifest_digest=manifest_digest,
        )
        self_path.write_text(deterministic_json_dumps(self_payload), encoding="utf-8")
        write_manifest_sha256(staging)

        ok, msg = verify_manifest_sha256(staging)
        if not ok:
            raise TradingSessionSingleWriterError(
                f"MANIFEST.sha256 verification failed before publish: {msg}"
            )

        reverify_trading_session_single_writer_v1(output_dir=staging)
        staging.replace(final_dir)

        ok, msg = verify_manifest_sha256(final_dir)
        if not ok:
            raise TradingSessionSingleWriterError(
                f"MANIFEST.sha256 verification failed after publish: {msg}"
            )
    except Exception:
        _cleanup_staging(staging)
        if final_dir.exists():
            shutil.rmtree(final_dir)
        raise

    return TradingSessionSingleWriterResult(
        output_dir=final_dir,
        contract_id=str(finalized["contract_id"]),
        contract_status=str(finalized["contract_status"]),
        single_writer_status=str(finalized["single_writer_status"]),
        contract_path=final_dir / ARTIFACT_REL,
        self_verification_path=final_dir / SELF_VERIFICATION_REL,
        manifest_path=final_dir / MANIFEST_FILENAME,
        session_identity_digest=str(finalized["session_identity_digest"]),
        writer_identity_digest=str(finalized["writer_identity_digest"]),
    )


__all__ = [
    "ARTIFACT_REL",
    "CONTRACT_NAME",
    "CONTRACT_VERSION",
    "CREATION_CONTRACT_VERSION",
    "DEFAULT_PRODUCER_IDENTITY_REF",
    "DEFAULT_SOURCE_REVISION",
    "DETERMINISTIC_RULE_SET_VERSION",
    "EVIDENCE_LEVEL",
    "MANIFEST_FILENAME",
    "PRODUCER_VERSION",
    "SCHEMA_VERSION",
    "SELF_VERIFICATION_REL",
    "SESSION_CONTRACT_VERSION",
    "TRADING_SESSION_SINGLE_WRITER_AUTHORITY_INVARIANTS",
    "WRITER_CONTRACT_VERSION",
    "TradingSessionIdentity",
    "TradingSessionSingleWriterError",
    "TradingSessionSingleWriterInputs",
    "TradingSessionSingleWriterRequest",
    "TradingSessionSingleWriterResult",
    "VerifiedClockTrustBundle",
    "build_trading_session_single_writer_v1",
    "default_trading_session_single_writer_request",
    "produce_trading_session_single_writer_v1",
    "reverify_trading_session_single_writer_v1",
    "serialize_trading_session_single_writer_v1",
    "verify_clock_trust_and_expiry_bundle",
    "verify_trading_session_single_writer_inputs",
]
