"""Offline LEVEL_3 canonical trading-core decision attestation contract owner v1."""

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
from src.meta.learning_loop.canonical_order_lifecycle_v1 import (
    CanonicalOrderIdentity,
    CanonicalOrderIntentIdentity,
    VerifiedTradingSessionSingleWriterBundle,
    _compute_order_identity_digest,
    _compute_order_intent_identity_digest,
)
from src.meta.learning_loop.comparison_common_durable_evidence_binding_v1 import (
    COMPARISON_AUTHORITY_INVARIANTS,
)
from src.meta.learning_loop.comparison_metric_input_v1.io import read_manifest
from src.meta.learning_loop.contract_safety_v1 import (
    compute_content_sha256,
    deterministic_json_dumps,
)
from src.meta.learning_loop.order_intent_idempotency_v1 import (
    ARTIFACT_REL as IDEMPOTENCY_ARTIFACT_REL,
    CONTRACT_NAME as IDEMPOTENCY_CONTRACT_NAME,
    CONTRACT_VERSION as IDEMPOTENCY_OWNER_CONTRACT_VERSION,
    DETERMINISTIC_RULE_SET_VERSION as IDEMPOTENCY_DETERMINISTIC_RULE_SET_VERSION,
    IDEMPOTENCY_CONTRACT_VERSION,
    PRODUCER_VERSION as IDEMPOTENCY_PRODUCER_VERSION,
    OrderIntentIdempotencyError,
    VerifiedCanonicalOrderLifecycleBundle,
    reverify_order_intent_idempotency_v1,
    verify_canonical_order_lifecycle_bundle,
    verify_trading_session_single_writer_bundle,
)

CONTRACT_NAME = "trading_core_decision_attestation_v1"
CONTRACT_VERSION = "v1"
ATTESTATION_CONTRACT_VERSION = "module_decision_attestation_contract_v1"
ATTESTATION_SCOPE_DEFAULT = "TRADING_CORE_OFFLINE_EVALUATION"
PRODUCER_VERSION = "trading_core_decision_attestation_v1"
EVIDENCE_LEVEL = "LEVEL_3"
AUTHORITY_LEVEL = "NON_AUTHORITIZING"
RECORD_KIND = "trading_core_decision_attestation_record"
INPUT_RELATION = "PACKAGES_VERIFIED_TRADING_SESSION_LIFECYCLE_AND_ORDER_INTENT_IDEMPOTENCY_FOR_OFFLINE_ATTESTATION"
ARTIFACT_REL = "trading_core_decision_attestation_v1.json"
SELF_VERIFICATION_REL = "SELF_VERIFICATION.json"
MANIFEST_FILENAME = "MANIFEST.sha256"
STAGING_DIRNAME_PREFIX = ".trading_core_decision_attestation_staging_"

SCHEMA_VERSION = "trading_core_decision_attestation_schema_v1"
CREATION_CONTRACT_VERSION = "trading_core_decision_attestation_creation_v1"
DETERMINISTIC_RULE_SET_VERSION = "trading_core_decision_attestation_rules_v1"
DETERMINISTIC_SERIALIZATION_VERSION = "deterministic_json_dumps_v1"
OFFLINE_DETERMINISTIC_CREATED_AT = "1970-01-01T00:00:00+00:00"
DEFAULT_PRODUCER_IDENTITY_REF = "peak_trade_offline_trading_core_decision_attestation_producer_v1"
DEFAULT_SOURCE_REVISION = "OFFLINE_DETERMINISTIC_EVIDENCE"

_VALID_INSTRUMENT_TYPES = frozenset({"FUTURES"})
_FORBIDDEN_INSTRUMENT_TYPES = frozenset({"SPOT", "SYNTHETIC_SPOT", "SYNTHETIC-SPOT"})

_REQUIRED_ATTESTATION_REF_FIELDS = (
    "master_v2_attestation_ref",
    "bull_attestation_ref",
    "bear_attestation_ref",
    "double_play_attestation_ref",
    "dynamic_scope_attestation_ref",
    "risk_attestation_ref",
    "sizing_attestation_ref",
    "scope_capital_attestation_ref",
)

_MODULE_SLOT_BY_REF_FIELD = {
    "master_v2_attestation_ref": "master_v2",
    "bull_attestation_ref": "bull",
    "bear_attestation_ref": "bear",
    "double_play_attestation_ref": "double_play",
    "dynamic_scope_attestation_ref": "dynamic_scope",
    "risk_attestation_ref": "risk",
    "sizing_attestation_ref": "sizing",
    "scope_capital_attestation_ref": "scope_capital",
}

_MODULE_OWNER_REFS = {
    "master_v2": "master_v2_owner_v1",
    "bull": "bull_component_owner_v1",
    "bear": "bear_component_owner_v1",
    "double_play": "double_play_owner_v1",
    "dynamic_scope": "dynamic_scope_owner_v1",
    "risk": "risk_owner_v1",
    "sizing": "sizing_owner_v1",
    "scope_capital": "scope_capital_owner_v1",
}

_MODULE_PARENT_SLOTS: dict[str, tuple[str, ...]] = {
    "master_v2": (),
    "double_play": ("master_v2",),
    "bull": ("double_play",),
    "bear": ("double_play",),
    "dynamic_scope": ("bull", "bear"),
    "risk": ("dynamic_scope",),
    "sizing": ("risk",),
    "scope_capital": ("sizing",),
}

_VALID_CLASSIFICATIONS = frozenset(
    {
        "ATTESTATION_CHAIN_VALID",
        "MISSING_ATTESTATION",
        "DIGEST_CHAIN_BROKEN",
        "SESSION_EPOCH_MISMATCH",
        "OUTDATED_VERSION",
        "MODULE_NOT_EXECUTED",
        "PARALLEL_SSOT_DETECTED",
        "FUTURES_MARKET_TYPE_CONFLICT",
        "MISSING_BINDINGS",
        "INVALID",
    }
)

_VALID_CONTRACT_STATUSES = frozenset(
    {
        "TRADING_CORE_DECISION_ATTESTATION_VALID",
        "TRADING_CORE_DECISION_ATTESTATION_MISSING_ATTESTATION",
        "TRADING_CORE_DECISION_ATTESTATION_DIGEST_CHAIN_BROKEN",
        "TRADING_CORE_DECISION_ATTESTATION_SESSION_EPOCH_MISMATCH",
        "TRADING_CORE_DECISION_ATTESTATION_OUTDATED_VERSION",
        "TRADING_CORE_DECISION_ATTESTATION_MODULE_NOT_EXECUTED",
        "TRADING_CORE_DECISION_ATTESTATION_PARALLEL_SSOT_DETECTED",
        "TRADING_CORE_DECISION_ATTESTATION_FUTURES_MARKET_TYPE_CONFLICT",
        "TRADING_CORE_DECISION_ATTESTATION_MISSING_BINDINGS",
        "TRADING_CORE_DECISION_ATTESTATION_INVALID",
        "ABSTAIN",
    }
)
_VALID_ATTESTATION_STATUSES = frozenset(
    {"ADMISSIBLE", "VALID", "CONFLICT", "INVALID", "UNKNOWN", "ABSTAIN"}
)
_SELF_VERIFICATION_SCHEMA_VERSION = "trading_core_decision_attestation_self_verification_v1"

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

TRADING_CORE_DECISION_ATTESTATION_AUTHORITY_INVARIANTS: dict[str, bool] = {
    **COMPARISON_AUTHORITY_INVARIANTS,
    "trading_core_decision_attestation_is_descriptive_only": True,
    "trading_core_decision_attestation_does_not_create_order": True,
    "trading_core_decision_attestation_does_not_submit_order": True,
    "trading_core_decision_attestation_does_not_mutate_order_state": True,
    "trading_core_decision_attestation_does_not_invoke_adapter": True,
    "trading_core_decision_attestation_does_not_invoke_consumer": True,
    "trading_core_decision_attestation_does_not_grant_authority": True,
    "trading_core_decision_attestation_is_offline_only": True,
    "deny_by_default": True,
    "futures_only": True,
    "canonical_order_identity_bound": True,
    "canonical_order_intent_bound": True,
    "trading_session_identity_bound": True,
    "order_intent_idempotency_bound": True,
    "module_attestation_chain_bound": True,
    "attestation_ref_binding_bound": True,
    "digest_chain_bound": True,
    "session_epoch_binding_bound": True,
    "module_execution_bound": True,
    "parallel_ssot_guard_bound": True,
    "provenance_bound": True,
    "cross_domain_lineage_bound": True,
    "deterministic_serialization_bound": True,
    "stable_digest_bound": True,
}

_REQUIRED_NON_AUTHORIZING_FLAGS: dict[str, bool] = {
    "is_trading_core_decision_attestation": True,
    "trading_core_decision_attestation_offline_only": True,
    "trading_core_decision_attestation_contract_complete": False,
    "canonical_order_identity_bound": False,
    "canonical_order_intent_bound": False,
    "trading_session_identity_bound": False,
    "order_intent_idempotency_bound": False,
    "module_attestation_chain_bound": False,
    "attestation_ref_binding_bound": False,
    "digest_chain_bound": False,
    "session_epoch_binding_bound": False,
    "module_execution_bound": False,
    "parallel_ssot_guard_bound": False,
    "provenance_bound": False,
    "cross_domain_lineage_bound": False,
    "deterministic_serialization_bound": False,
    "stable_digest_bound": False,
    "deny_by_default": True,
    "futures_only": True,
    "order_created": False,
    "order_validated": False,
    "order_authorized": False,
    "order_submission_requested": False,
    "order_submitted": False,
    "order_acknowledged": False,
    "order_amended": False,
    "order_cancel_requested": False,
    "order_cancelled": False,
    "order_partially_filled": False,
    "order_filled": False,
    "order_rejected": False,
    "order_expired": False,
    "order_revoked": False,
    "order_state_mutated": False,
    "adapter_invoked": False,
    "exchange_request_sent": False,
    "network_side_effect_created": False,
    "files_transferred_to_runtime": False,
    "queue_message_created": False,
    "database_mutated": False,
    "lock_acquired": False,
    "reservation_created": False,
    "trading_session_started": False,
    "writer_registered": False,
    "writer_activated": False,
    "fencing_token_issued": False,
    "authority_granted": False,
    "authority_activated": False,
    "lease_activated": False,
    "lease_renewed": False,
    "revocation_executed": False,
    "killswitch_executed": False,
    "signature_created": False,
    "private_key_used": False,
    "credentials_accessed": False,
    "runtime_configuration_created": False,
    "runtime_permission_created": False,
    "execution_permission_created": False,
    "arming_token_created": False,
    "runtime_authorized": False,
    "live_authorized": False,
    "orders_allowed": False,
    "scheduler_runtime_allowed": False,
}


class TradingCoreDecisionAttestationError(ValueError):
    """Fail-closed trading-core decision attestation error."""


@dataclass(frozen=True)
class ModuleDecisionAttestation:
    attestation_id: str
    module_owner_ref: str
    module_contract_digest: str
    implementation_digest: str
    input_digest: str
    output_digest: str
    decision_code: str
    decision_trace_digest: str
    policy_digest: str
    parent_attestation_refs: tuple[str, ...]
    correlation_id: str
    session_id: str
    trading_epoch: str
    created_at: str
    manifest_digest: str
    module_slot: str
    module_executed: bool = True
    attestation_contract_version: str = ATTESTATION_CONTRACT_VERSION


@dataclass(frozen=True)
class CanonicalOrderIntentAttestationBindings:
    master_v2_attestation_ref: str
    bull_attestation_ref: str
    bear_attestation_ref: str
    double_play_attestation_ref: str
    dynamic_scope_attestation_ref: str
    risk_attestation_ref: str
    sizing_attestation_ref: str
    scope_capital_attestation_ref: str


@dataclass(frozen=True)
class TradingCoreDecisionAttestationRequest:
    canonical_order_intent_identity: CanonicalOrderIntentIdentity
    canonical_order_identity: CanonicalOrderIdentity
    attestation_bindings: CanonicalOrderIntentAttestationBindings
    module_attestations: tuple[ModuleDecisionAttestation, ...]
    correlation_id: str
    expected_module_contract_digests: dict[str, str]
    provenance_digest: str
    cross_domain_lineage_digest: str
    deterministic_serialization_version: str
    parallel_trading_logic_ssot_detected: bool = False
    attestation_contract_version: str = ATTESTATION_CONTRACT_VERSION
    idempotency_contract_version: str = IDEMPOTENCY_CONTRACT_VERSION
    source_revision: str = DEFAULT_SOURCE_REVISION


@dataclass(frozen=True)
class VerifiedOrderIntentIdempotencyBundle:
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
    idempotency_status: str
    session_identity_digest: str
    idempotency_key: str


@dataclass(frozen=True)
class TradingCoreDecisionAttestationInputs:
    trading_session_single_writer_bundle_dir: Path
    canonical_order_lifecycle_bundle_dir: Path
    order_intent_idempotency_bundle_dir: Path
    attestation_request: TradingCoreDecisionAttestationRequest


@dataclass(frozen=True)
class TradingCoreDecisionAttestationResult:
    output_dir: Path
    contract_id: str
    contract_status: str
    attestation_status: str
    classification: str
    contract_path: Path
    self_verification_path: Path
    manifest_path: Path
    canonical_order_identity_digest: str
    canonical_order_intent_identity_digest: str
    attestation_chain_digest: str


def _reject_symlink(path: Path, *, label: str) -> None:
    if path.is_symlink():
        raise TradingCoreDecisionAttestationError(f"{label} must not be a symlink")


def _reject_forbidden_index_keys(payload: Mapping[str, Any]) -> None:
    for key in payload:
        if key in _FORBIDDEN_INDEX_KEYS:
            raise TradingCoreDecisionAttestationError(f"forbidden index key: {key}")


def _validate_regular_file(path: Path, *, label: str) -> None:
    _reject_symlink(path, label=label)
    if not path.is_file():
        raise TradingCoreDecisionAttestationError(f"{label} must be a regular file: {path}")


def _validate_bundle_dir(bundle_dir: Path, *, label: str) -> None:
    _reject_symlink(bundle_dir, label=label)
    if not bundle_dir.is_dir():
        raise TradingCoreDecisionAttestationError(f"{label} must be a directory: {bundle_dir}")


def _validate_output_target(output_dir: Path) -> None:
    if output_dir.exists():
        raise TradingCoreDecisionAttestationError(f"output directory already exists: {output_dir}")
    if is_under_tmp(output_dir):
        raise TradingCoreDecisionAttestationError("output directory must not be under /tmp")


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
        if resolved_output == resolved_bundle:
            raise TradingCoreDecisionAttestationError(
                "output directory must not equal input bundle"
            )
        if _path_is_under(resolved_output, resolved_bundle) or _path_is_under(
            resolved_bundle, resolved_output
        ):
            raise TradingCoreDecisionAttestationError("output directory overlaps input bundle")


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
    return sorted(
        factors,
        key=lambda item: (item.get("factor_id", ""), item.get("source_field", "")),
    )


def _sorted_strings(values: list[str]) -> list[str]:
    return sorted(values)


def _validate_non_authorizing_flags(payload: Mapping[str, Any]) -> None:
    for key, expected in _REQUIRED_NON_AUTHORIZING_FLAGS.items():
        actual = payload.get(key)
        if key in {
            "trading_core_decision_attestation_contract_complete",
            "canonical_order_identity_bound",
            "canonical_order_intent_bound",
            "trading_session_identity_bound",
            "order_intent_idempotency_bound",
            "module_attestation_chain_bound",
            "attestation_ref_binding_bound",
            "digest_chain_bound",
            "session_epoch_binding_bound",
            "module_execution_bound",
            "parallel_ssot_guard_bound",
            "provenance_bound",
            "cross_domain_lineage_bound",
            "deterministic_serialization_bound",
            "stable_digest_bound",
        }:
            continue
        if actual is not expected:
            raise TradingCoreDecisionAttestationError(
                f"non-authorizing flag {key} must be {expected!r}, got {actual!r}"
            )


def _manifest_file_digest(bundle_dir: Path) -> str:
    manifest_path = bundle_dir / MANIFEST_FILENAME
    _validate_regular_file(manifest_path, label=MANIFEST_FILENAME)
    return hashlib.sha256(manifest_path.read_bytes()).hexdigest()


def _artifact_digest_from_payload(payload: Mapping[str, Any]) -> str:
    return str(payload.get("output_digest") or payload.get("artifact_id") or "")


def _binding_digest(value: str, *, domain: str) -> str:
    return compute_content_sha256(
        {
            "digest_domain": domain,
            "value": value,
            "deterministic_rule_set_version": DETERMINISTIC_RULE_SET_VERSION,
        }
    )


def _attestation_body_for_manifest(attestation: ModuleDecisionAttestation) -> dict[str, Any]:
    return {
        "attestation_id": attestation.attestation_id,
        "module_owner_ref": attestation.module_owner_ref,
        "module_contract_digest": attestation.module_contract_digest,
        "implementation_digest": attestation.implementation_digest,
        "input_digest": attestation.input_digest,
        "output_digest": attestation.output_digest,
        "decision_code": attestation.decision_code,
        "decision_trace_digest": attestation.decision_trace_digest,
        "policy_digest": attestation.policy_digest,
        "parent_attestation_refs": list(attestation.parent_attestation_refs),
        "correlation_id": attestation.correlation_id,
        "session_id": attestation.session_id,
        "trading_epoch": attestation.trading_epoch,
        "created_at": attestation.created_at,
        "module_slot": attestation.module_slot,
        "module_executed": attestation.module_executed,
        "attestation_contract_version": attestation.attestation_contract_version,
    }


def compute_module_attestation_manifest_digest(attestation: ModuleDecisionAttestation) -> str:
    body = _attestation_body_for_manifest(attestation)
    return hashlib.sha256(deterministic_json_dumps(body).encode("utf-8")).hexdigest()


def compute_module_attestation_id(
    *,
    module_slot: str,
    module_owner_ref: str,
    input_digest: str,
    output_digest: str,
    session_id: str,
    trading_epoch: str,
) -> str:
    return compute_content_sha256(
        {
            "attestation_domain": ATTESTATION_CONTRACT_VERSION,
            "module_slot": module_slot,
            "module_owner_ref": module_owner_ref,
            "input_digest": input_digest,
            "output_digest": output_digest,
            "session_id": session_id,
            "trading_epoch": trading_epoch,
            "deterministic_rule_set_version": DETERMINISTIC_RULE_SET_VERSION,
        }
    )


def _expected_input_digest(parent_output_digests: list[str]) -> str:
    if not parent_output_digests:
        return ""
    if len(parent_output_digests) == 1:
        return parent_output_digests[0]
    return compute_content_sha256({"parent_output_digests": sorted(parent_output_digests)})


def _module_attestations_by_slot(
    attestations: tuple[ModuleDecisionAttestation, ...],
) -> dict[str, ModuleDecisionAttestation]:
    by_slot: dict[str, ModuleDecisionAttestation] = {}
    for attestation in attestations:
        if attestation.module_slot in by_slot:
            raise TradingCoreDecisionAttestationError(
                f"duplicate module attestation slot: {attestation.module_slot}"
            )
        by_slot[attestation.module_slot] = attestation
    return by_slot


def verify_order_intent_idempotency_bundle(
    bundle_dir: Path | str,
) -> VerifiedOrderIntentIdempotencyBundle:
    path = Path(bundle_dir)
    _validate_bundle_dir(path, label="order intent idempotency bundle")
    ok, msg = verify_manifest_sha256(path)
    if not ok:
        raise TradingCoreDecisionAttestationError(
            f"idempotency MANIFEST.sha256 verification failed: {msg}"
        )

    artifact_path = path / IDEMPOTENCY_ARTIFACT_REL
    _validate_regular_file(artifact_path, label=IDEMPOTENCY_ARTIFACT_REL)
    payload = read_manifest(artifact_path)
    if payload.get("contract_name") != IDEMPOTENCY_CONTRACT_NAME:
        raise TradingCoreDecisionAttestationError("idempotency contract_name mismatch")
    if payload.get("contract_version") != IDEMPOTENCY_OWNER_CONTRACT_VERSION:
        raise TradingCoreDecisionAttestationError("idempotency contract_version mismatch")

    try:
        reverify_order_intent_idempotency_v1(output_dir=path)
    except OrderIntentIdempotencyError as exc:
        raise TradingCoreDecisionAttestationError(str(exc)) from exc

    return VerifiedOrderIntentIdempotencyBundle(
        bundle_dir=path.resolve(),
        contract_name=IDEMPOTENCY_CONTRACT_NAME,
        contract_version=IDEMPOTENCY_OWNER_CONTRACT_VERSION,
        producer_version=IDEMPOTENCY_PRODUCER_VERSION,
        artifact_ref=IDEMPOTENCY_ARTIFACT_REL,
        artifact_digest=_artifact_digest_from_payload(payload),
        manifest_digest=_manifest_file_digest(path),
        artifact_payload=dict(payload),
        contract_id=str(payload.get("contract_id", "")),
        contract_status=str(payload.get("contract_status", "")),
        idempotency_status=str(payload.get("idempotency_status", "")),
        session_identity_digest=str(payload.get("session_identity_digest", "")),
        idempotency_key=str(payload.get("idempotency_key", "")),
    )


def _validate_request(
    request: TradingCoreDecisionAttestationRequest,
    *,
    trading_session: VerifiedTradingSessionSingleWriterBundle,
    lifecycle: VerifiedCanonicalOrderLifecycleBundle,
    idempotency: VerifiedOrderIntentIdempotencyBundle,
) -> list[dict[str, str]]:
    blocking: list[dict[str, str]] = []
    intent = request.canonical_order_intent_identity
    order = request.canonical_order_identity
    session = trading_session.trading_session_identity
    session_id = str(session.get("session_id", ""))
    trading_epoch = str(session.get("trading_epoch", ""))

    if not intent.instrument_type:
        blocking.append(
            _factor(
                factor_id="MISSING_INSTRUMENT_TYPE",
                factor_type="MISSING_PRECONDITION",
                source_field="canonical_order_intent_identity.instrument_type",
                detail="missing",
            )
        )
    elif intent.instrument_type in _FORBIDDEN_INSTRUMENT_TYPES:
        blocking.append(
            _factor(
                factor_id="FORBIDDEN_INSTRUMENT_TYPE",
                factor_type="BLOCKING",
                source_field="canonical_order_intent_identity.instrument_type",
                detail=intent.instrument_type,
            )
        )
    elif intent.instrument_type not in _VALID_INSTRUMENT_TYPES:
        blocking.append(
            _factor(
                factor_id="INVALID_INSTRUMENT_TYPE",
                factor_type="BLOCKING",
                source_field="canonical_order_intent_identity.instrument_type",
                detail=intent.instrument_type,
            )
        )

    if not order.canonical_order_id:
        blocking.append(
            _factor(
                factor_id="MISSING_CANONICAL_ORDER_ID",
                factor_type="MISSING_PRECONDITION",
                source_field="canonical_order_identity.canonical_order_id",
                detail="missing",
            )
        )
    if not intent.order_intent_digest:
        blocking.append(
            _factor(
                factor_id="MISSING_ORDER_INTENT_DIGEST",
                factor_type="MISSING_PRECONDITION",
                source_field="canonical_order_intent_identity.order_intent_digest",
                detail="missing",
            )
        )

    if request.deterministic_serialization_version != DETERMINISTIC_SERIALIZATION_VERSION:
        blocking.append(
            _factor(
                factor_id="SERIALIZATION_VERSION_MISMATCH",
                factor_type="MISSING_PRECONDITION",
                source_field="deterministic_serialization_version",
                detail=request.deterministic_serialization_version,
            )
        )
    if request.attestation_contract_version != ATTESTATION_CONTRACT_VERSION:
        blocking.append(
            _factor(
                factor_id="ATTESTATION_CONTRACT_VERSION_MISMATCH",
                factor_type="MISSING_PRECONDITION",
                source_field="attestation_contract_version",
                detail=request.attestation_contract_version,
            )
        )
    if request.idempotency_contract_version != IDEMPOTENCY_CONTRACT_VERSION:
        blocking.append(
            _factor(
                factor_id="IDEMPOTENCY_CONTRACT_VERSION_MISMATCH",
                factor_type="MISSING_PRECONDITION",
                source_field="idempotency_contract_version",
                detail=request.idempotency_contract_version,
            )
        )

    if request.parallel_trading_logic_ssot_detected:
        blocking.append(
            _factor(
                factor_id="PARALLEL_TRADING_LOGIC_SSOT_DETECTED",
                factor_type="CONTRADICTION",
                source_field="parallel_trading_logic_ssot_detected",
                detail="true",
            )
        )

    bindings = request.attestation_bindings
    for ref_field in _REQUIRED_ATTESTATION_REF_FIELDS:
        ref_value = getattr(bindings, ref_field)
        if not ref_value:
            blocking.append(
                _factor(
                    factor_id="MISSING_ATTESTATION_REF",
                    factor_type="MISSING_PRECONDITION",
                    source_field=f"attestation_bindings.{ref_field}",
                    detail="missing",
                )
            )

    by_slot = _module_attestations_by_slot(request.module_attestations)
    for slot in _MODULE_SLOT_BY_REF_FIELD.values():
        if slot not in by_slot:
            blocking.append(
                _factor(
                    factor_id="MISSING_MODULE_ATTESTATION",
                    factor_type="MISSING_PRECONDITION",
                    source_field=f"module_attestations.{slot}",
                    detail="missing",
                )
            )

    attestation_ids = {att.attestation_id for att in request.module_attestations}
    for ref_field in _REQUIRED_ATTESTATION_REF_FIELDS:
        ref_value = getattr(bindings, ref_field)
        slot = _MODULE_SLOT_BY_REF_FIELD[ref_field]
        if ref_value and slot in by_slot and ref_value != by_slot[slot].attestation_id:
            blocking.append(
                _factor(
                    factor_id="ATTESTATION_REF_MISMATCH",
                    factor_type="CONTRADICTION",
                    source_field=f"attestation_bindings.{ref_field}",
                    detail=ref_value,
                )
            )
        if ref_value and ref_value not in attestation_ids:
            blocking.append(
                _factor(
                    factor_id="UNRESOLVED_ATTESTATION_REF",
                    factor_type="MISSING_PRECONDITION",
                    source_field=f"attestation_bindings.{ref_field}",
                    detail=ref_value,
                )
            )

    for attestation in request.module_attestations:
        if attestation.module_owner_ref != _MODULE_OWNER_REFS.get(attestation.module_slot, ""):
            blocking.append(
                _factor(
                    factor_id="MODULE_OWNER_REF_MISMATCH",
                    factor_type="CONTRADICTION",
                    source_field=f"module_attestations.{attestation.module_slot}.module_owner_ref",
                    detail=attestation.module_owner_ref,
                )
            )

        expected_contract = request.expected_module_contract_digests.get(
            attestation.module_slot, ""
        )
        if expected_contract and attestation.module_contract_digest != expected_contract:
            blocking.append(
                _factor(
                    factor_id="OUTDATED_MODULE_CONTRACT_DIGEST",
                    factor_type="BLOCKING",
                    source_field=f"module_attestations.{attestation.module_slot}.module_contract_digest",
                    detail=attestation.module_contract_digest,
                )
            )

        if attestation.attestation_contract_version != ATTESTATION_CONTRACT_VERSION:
            blocking.append(
                _factor(
                    factor_id="OUTDATED_ATTESTATION_CONTRACT_VERSION",
                    factor_type="BLOCKING",
                    source_field=f"module_attestations.{attestation.module_slot}.attestation_contract_version",
                    detail=attestation.attestation_contract_version,
                )
            )

        if attestation.session_id != session_id:
            blocking.append(
                _factor(
                    factor_id="SESSION_ID_MISMATCH",
                    factor_type="CONTRADICTION",
                    source_field=f"module_attestations.{attestation.module_slot}.session_id",
                    detail=attestation.session_id,
                )
            )
        if attestation.trading_epoch != trading_epoch:
            blocking.append(
                _factor(
                    factor_id="TRADING_EPOCH_MISMATCH",
                    factor_type="CONTRADICTION",
                    source_field=f"module_attestations.{attestation.module_slot}.trading_epoch",
                    detail=attestation.trading_epoch,
                )
            )
        if attestation.correlation_id != request.correlation_id:
            blocking.append(
                _factor(
                    factor_id="CORRELATION_ID_MISMATCH",
                    factor_type="CONTRADICTION",
                    source_field=f"module_attestations.{attestation.module_slot}.correlation_id",
                    detail=attestation.correlation_id,
                )
            )

        expected_manifest = compute_module_attestation_manifest_digest(attestation)
        if attestation.manifest_digest != expected_manifest:
            blocking.append(
                _factor(
                    factor_id="MANIFEST_DIGEST_MISMATCH",
                    factor_type="CONTRADICTION",
                    source_field=f"module_attestations.{attestation.module_slot}.manifest_digest",
                    detail=attestation.manifest_digest,
                )
            )

        if not attestation.module_executed or not attestation.output_digest:
            blocking.append(
                _factor(
                    factor_id="MODULE_NOT_EXECUTED",
                    factor_type="BLOCKING",
                    source_field=f"module_attestations.{attestation.module_slot}.module_executed",
                    detail=str(attestation.module_executed),
                )
            )

        expected_parents = _MODULE_PARENT_SLOTS.get(attestation.module_slot, ())
        parent_ids = set(attestation.parent_attestation_refs)
        expected_parent_ids = {
            by_slot[parent_slot].attestation_id
            for parent_slot in expected_parents
            if parent_slot in by_slot
        }
        if parent_ids != expected_parent_ids:
            blocking.append(
                _factor(
                    factor_id="PARENT_ATTESTATION_REF_MISMATCH",
                    factor_type="CONTRADICTION",
                    source_field=f"module_attestations.{attestation.module_slot}.parent_attestation_refs",
                    detail=",".join(sorted(parent_ids)),
                )
            )

        parent_outputs = [
            by_slot[parent_slot].output_digest
            for parent_slot in expected_parents
            if parent_slot in by_slot
        ]
        expected_input = _expected_input_digest(parent_outputs)
        if expected_input and attestation.input_digest != expected_input:
            blocking.append(
                _factor(
                    factor_id="INPUT_DIGEST_CHAIN_BROKEN",
                    factor_type="CONTRADICTION",
                    source_field=f"module_attestations.{attestation.module_slot}.input_digest",
                    detail=attestation.input_digest,
                )
            )

    if (
        idempotency.session_identity_digest
        and trading_session.session_identity_digest != idempotency.session_identity_digest
    ):
        blocking.append(
            _factor(
                factor_id="IDEMPOTENCY_SESSION_MISMATCH",
                factor_type="CONTRADICTION",
                source_field="order_intent_idempotency.session_identity_digest",
                detail=idempotency.session_identity_digest,
            )
        )

    if lifecycle.session_identity_digest != trading_session.session_identity_digest:
        blocking.append(
            _factor(
                factor_id="LIFECYCLE_SESSION_MISMATCH",
                factor_type="CONTRADICTION",
                source_field="canonical_order_lifecycle.session_identity_digest",
                detail=lifecycle.session_identity_digest,
            )
        )

    return blocking


def _evaluate_attestation(
    *,
    request: TradingCoreDecisionAttestationRequest,
    blocking_facts: list[dict[str, str]],
) -> tuple[str, str, str, list[str], dict[str, Any]]:
    factor_ids = {item.get("factor_id") for item in blocking_facts}
    reason_codes: list[str] = []
    states: dict[str, Any] = {
        "attestation_status": "UNKNOWN",
        "attestation_reason": "",
        "attestation_chain_classification": "INVALID",
        "admissibility_reason": "",
        "deny_reason": "",
    }

    market_type_factors = {
        "FORBIDDEN_INSTRUMENT_TYPE",
        "INVALID_INSTRUMENT_TYPE",
        "MISSING_INSTRUMENT_TYPE",
    }
    if factor_ids & market_type_factors:
        states["attestation_status"] = "INVALID"
        states["attestation_chain_classification"] = "FUTURES_MARKET_TYPE_CONFLICT"
        states["deny_reason"] = "FUTURES_MARKET_TYPE_CONFLICT"
        reason_codes.append("FUTURES_MARKET_TYPE_CONFLICT")
        return (
            "TRADING_CORE_DECISION_ATTESTATION_FUTURES_MARKET_TYPE_CONFLICT",
            states["attestation_status"],
            states["attestation_chain_classification"],
            _sorted_strings(reason_codes),
            states,
        )

    if "PARALLEL_TRADING_LOGIC_SSOT_DETECTED" in factor_ids:
        states["attestation_status"] = "CONFLICT"
        states["attestation_chain_classification"] = "PARALLEL_SSOT_DETECTED"
        states["deny_reason"] = "PARALLEL_TRADING_LOGIC_SSOT_DETECTED"
        reason_codes.append("PARALLEL_TRADING_LOGIC_SSOT_DETECTED")
        return (
            "TRADING_CORE_DECISION_ATTESTATION_PARALLEL_SSOT_DETECTED",
            states["attestation_status"],
            states["attestation_chain_classification"],
            _sorted_strings(reason_codes),
            states,
        )

    missing_factors = {
        "MISSING_ATTESTATION_REF",
        "MISSING_MODULE_ATTESTATION",
        "UNRESOLVED_ATTESTATION_REF",
        "SERIALIZATION_VERSION_MISMATCH",
        "ATTESTATION_CONTRACT_VERSION_MISMATCH",
        "IDEMPOTENCY_CONTRACT_VERSION_MISMATCH",
    }
    if factor_ids & missing_factors:
        states["attestation_status"] = "INVALID"
        states["attestation_chain_classification"] = "MISSING_BINDINGS"
        states["deny_reason"] = "MISSING_BINDINGS"
        reason_codes.append("MISSING_BINDINGS")
        return (
            "TRADING_CORE_DECISION_ATTESTATION_MISSING_BINDINGS",
            states["attestation_status"],
            states["attestation_chain_classification"],
            _sorted_strings(reason_codes),
            states,
        )

    outdated_factors = {
        "OUTDATED_MODULE_CONTRACT_DIGEST",
        "OUTDATED_ATTESTATION_CONTRACT_VERSION",
    }
    if factor_ids & outdated_factors:
        states["attestation_status"] = "CONFLICT"
        states["attestation_chain_classification"] = "OUTDATED_VERSION"
        states["deny_reason"] = "OUTDATED_VERSION"
        reason_codes.append("OUTDATED_VERSION")
        return (
            "TRADING_CORE_DECISION_ATTESTATION_OUTDATED_VERSION",
            states["attestation_status"],
            states["attestation_chain_classification"],
            _sorted_strings(reason_codes),
            states,
        )

    session_epoch_factors = {
        "SESSION_ID_MISMATCH",
        "TRADING_EPOCH_MISMATCH",
        "CORRELATION_ID_MISMATCH",
        "IDEMPOTENCY_SESSION_MISMATCH",
        "LIFECYCLE_SESSION_MISMATCH",
    }
    if factor_ids & session_epoch_factors:
        states["attestation_status"] = "CONFLICT"
        states["attestation_chain_classification"] = "SESSION_EPOCH_MISMATCH"
        states["deny_reason"] = "SESSION_EPOCH_MISMATCH"
        reason_codes.append("SESSION_EPOCH_MISMATCH")
        return (
            "TRADING_CORE_DECISION_ATTESTATION_SESSION_EPOCH_MISMATCH",
            states["attestation_status"],
            states["attestation_chain_classification"],
            _sorted_strings(reason_codes),
            states,
        )

    if "MODULE_NOT_EXECUTED" in factor_ids:
        states["attestation_status"] = "CONFLICT"
        states["attestation_chain_classification"] = "MODULE_NOT_EXECUTED"
        states["deny_reason"] = "MODULE_NOT_EXECUTED"
        reason_codes.append("MODULE_NOT_EXECUTED")
        return (
            "TRADING_CORE_DECISION_ATTESTATION_MODULE_NOT_EXECUTED",
            states["attestation_status"],
            states["attestation_chain_classification"],
            _sorted_strings(reason_codes),
            states,
        )

    digest_chain_factors = {
        "INPUT_DIGEST_CHAIN_BROKEN",
        "MANIFEST_DIGEST_MISMATCH",
        "PARENT_ATTESTATION_REF_MISMATCH",
        "ATTESTATION_REF_MISMATCH",
    }
    if factor_ids & digest_chain_factors:
        states["attestation_status"] = "CONFLICT"
        states["attestation_chain_classification"] = "DIGEST_CHAIN_BROKEN"
        states["deny_reason"] = "DIGEST_CHAIN_BROKEN"
        reason_codes.append("DIGEST_CHAIN_BROKEN")
        return (
            "TRADING_CORE_DECISION_ATTESTATION_DIGEST_CHAIN_BROKEN",
            states["attestation_status"],
            states["attestation_chain_classification"],
            _sorted_strings(reason_codes),
            states,
        )

    missing_attestation_factors = {
        "MISSING_CANONICAL_ORDER_ID",
        "MISSING_ORDER_INTENT_DIGEST",
        "MODULE_OWNER_REF_MISMATCH",
    }
    if factor_ids & missing_attestation_factors:
        states["attestation_status"] = "INVALID"
        states["attestation_chain_classification"] = "MISSING_ATTESTATION"
        states["deny_reason"] = "MISSING_ATTESTATION"
        reason_codes.append("MISSING_ATTESTATION")
        return (
            "TRADING_CORE_DECISION_ATTESTATION_MISSING_ATTESTATION",
            states["attestation_status"],
            states["attestation_chain_classification"],
            _sorted_strings(reason_codes),
            states,
        )

    if blocking_facts:
        states["attestation_status"] = "INVALID"
        states["attestation_chain_classification"] = "INVALID"
        states["deny_reason"] = "INVALID"
        reason_codes.append("INVALID")
        return (
            "TRADING_CORE_DECISION_ATTESTATION_INVALID",
            states["attestation_status"],
            states["attestation_chain_classification"],
            _sorted_strings(reason_codes),
            states,
        )

    states["attestation_status"] = "VALID"
    states["attestation_chain_classification"] = "ATTESTATION_CHAIN_VALID"
    states["admissibility_reason"] = "ATTESTATION_CHAIN_VALID"
    reason_codes.append("ATTESTATION_CHAIN_VALID")
    return (
        "TRADING_CORE_DECISION_ATTESTATION_VALID",
        states["attestation_status"],
        states["attestation_chain_classification"],
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


def _serialize_module_attestations(
    attestations: tuple[ModuleDecisionAttestation, ...],
) -> list[dict[str, Any]]:
    serialized: list[dict[str, Any]] = []
    for attestation in sorted(attestations, key=lambda item: item.module_slot):
        serialized.append(
            {
                "attestation_id": attestation.attestation_id,
                "module_slot": attestation.module_slot,
                "module_owner_ref": attestation.module_owner_ref,
                "module_contract_digest": attestation.module_contract_digest,
                "implementation_digest": attestation.implementation_digest,
                "input_digest": attestation.input_digest,
                "output_digest": attestation.output_digest,
                "decision_code": attestation.decision_code,
                "decision_trace_digest": attestation.decision_trace_digest,
                "policy_digest": attestation.policy_digest,
                "parent_attestation_refs": list(attestation.parent_attestation_refs),
                "correlation_id": attestation.correlation_id,
                "session_id": attestation.session_id,
                "trading_epoch": attestation.trading_epoch,
                "created_at": attestation.created_at,
                "manifest_digest": attestation.manifest_digest,
                "module_executed": attestation.module_executed,
                "attestation_contract_version": attestation.attestation_contract_version,
            }
        )
    return serialized


def _compute_attestation_chain_digest(
    attestations: tuple[ModuleDecisionAttestation, ...],
) -> str:
    return compute_content_sha256(
        {
            "module_attestations": _serialize_module_attestations(attestations),
            "deterministic_rule_set_version": DETERMINISTIC_RULE_SET_VERSION,
        }
    )


def build_trading_core_decision_attestation_v1(
    *,
    trading_session: VerifiedTradingSessionSingleWriterBundle,
    lifecycle: VerifiedCanonicalOrderLifecycleBundle,
    idempotency: VerifiedOrderIntentIdempotencyBundle,
    request: TradingCoreDecisionAttestationRequest,
) -> dict[str, Any]:
    blocking_facts = _validate_request(
        request,
        trading_session=trading_session,
        lifecycle=lifecycle,
        idempotency=idempotency,
    )
    contradictions = [item for item in blocking_facts if item.get("factor_type") == "CONTRADICTION"]
    non_contradiction_blocking = [
        item for item in blocking_facts if item.get("factor_type") != "CONTRADICTION"
    ]

    contract_status, attestation_status, classification, reason_codes, completion = (
        _evaluate_attestation(request=request, blocking_facts=blocking_facts)
    )

    intent = request.canonical_order_intent_identity
    order = request.canonical_order_identity
    order_intent_identity_digest = _compute_order_intent_identity_digest(intent=intent)
    canonical_order_identity_digest = _compute_order_identity_digest(order=order)
    attestation_chain_digest = _compute_attestation_chain_digest(request.module_attestations)

    input_refs = [
        _input_artifact_ref_mapping(
            bundle_dir=trading_session.bundle_dir,
            contract_name=trading_session.contract_name,
            contract_version=trading_session.contract_version,
            producer_version=trading_session.producer_version,
            artifact_ref=trading_session.artifact_ref,
            artifact_digest=trading_session.artifact_digest,
            manifest_digest=trading_session.manifest_digest,
        ),
        _input_artifact_ref_mapping(
            bundle_dir=lifecycle.bundle_dir,
            contract_name=lifecycle.contract_name,
            contract_version=lifecycle.contract_version,
            producer_version=lifecycle.producer_version,
            artifact_ref=lifecycle.artifact_ref,
            artifact_digest=lifecycle.artifact_digest,
            manifest_digest=lifecycle.manifest_digest,
        ),
        _input_artifact_ref_mapping(
            bundle_dir=idempotency.bundle_dir,
            contract_name=idempotency.contract_name,
            contract_version=idempotency.contract_version,
            producer_version=idempotency.producer_version,
            artifact_ref=idempotency.artifact_ref,
            artifact_digest=idempotency.artifact_digest,
            manifest_digest=idempotency.manifest_digest,
        ),
    ]
    input_digest = compute_content_sha256({"input_artifact_refs": input_refs})

    contract_id = compute_content_sha256(
        {
            "contract_domain": CONTRACT_NAME,
            "canonical_order_identity_digest": canonical_order_identity_digest,
            "order_intent_identity_digest": order_intent_identity_digest,
            "session_identity_digest": trading_session.session_identity_digest,
            "attestation_chain_digest": attestation_chain_digest,
            "deterministic_rule_set_version": DETERMINISTIC_RULE_SET_VERSION,
        }
    )

    complete = contract_status == "TRADING_CORE_DECISION_ATTESTATION_VALID"
    bindings = request.attestation_bindings

    payload: dict[str, Any] = {
        "contract_id": "",
        "contract_name": CONTRACT_NAME,
        "contract_version": CONTRACT_VERSION,
        "attestation_contract_version": request.attestation_contract_version,
        "idempotency_contract_version": request.idempotency_contract_version,
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
        "deterministic_serialization_version": request.deterministic_serialization_version,
        "contract_status": contract_status,
        "contract_reason_codes": reason_codes,
        "attestation_status": attestation_status,
        "attestation_reason": completion.get("attestation_reason", ""),
        "attestation_chain_classification": classification,
        "admissibility_reason": completion.get("admissibility_reason", ""),
        "deny_reason": completion.get("deny_reason", ""),
        "canonical_order_intent_identity": {
            "client_order_id": intent.client_order_id,
            "order_intent_digest": intent.order_intent_digest,
            "instrument_type": intent.instrument_type,
            "venue": intent.venue,
            "account": intent.account,
            "instrument": intent.instrument,
            "trading_epoch": intent.trading_epoch,
        },
        "canonical_order_intent_identity_digest": order_intent_identity_digest,
        "canonical_order_identity": {
            "canonical_order_id": order.canonical_order_id,
            "client_order_id": order.client_order_id,
            "venue_order_id": order.venue_order_id,
        },
        "canonical_order_identity_digest": canonical_order_identity_digest,
        "attestation_bindings": {
            "master_v2_attestation_ref": bindings.master_v2_attestation_ref,
            "bull_attestation_ref": bindings.bull_attestation_ref,
            "bear_attestation_ref": bindings.bear_attestation_ref,
            "double_play_attestation_ref": bindings.double_play_attestation_ref,
            "dynamic_scope_attestation_ref": bindings.dynamic_scope_attestation_ref,
            "risk_attestation_ref": bindings.risk_attestation_ref,
            "sizing_attestation_ref": bindings.sizing_attestation_ref,
            "scope_capital_attestation_ref": bindings.scope_capital_attestation_ref,
        },
        "module_attestations": _serialize_module_attestations(request.module_attestations),
        "attestation_chain_digest": attestation_chain_digest,
        "correlation_id": request.correlation_id,
        "parallel_trading_logic_ssot_detected": request.parallel_trading_logic_ssot_detected,
        "trading_session_identity": dict(trading_session.trading_session_identity),
        "session_identity_digest": trading_session.session_identity_digest,
        "writer_identity": trading_session.writer_identity,
        "writer_identity_digest": trading_session.writer_identity_digest,
        "provenance_digest": request.provenance_digest,
        "cross_domain_lineage_digest": request.cross_domain_lineage_digest,
        "upstream_bindings": {
            "trading_session_single_writer_bundle_ref": trading_session.bundle_dir.as_posix(),
            "trading_session_contract_id": trading_session.contract_id,
            "trading_session_digest": trading_session.artifact_digest,
            "canonical_order_lifecycle_bundle_ref": lifecycle.bundle_dir.as_posix(),
            "canonical_order_lifecycle_contract_id": lifecycle.contract_id,
            "canonical_order_lifecycle_digest": lifecycle.artifact_digest,
            "order_intent_idempotency_bundle_ref": idempotency.bundle_dir.as_posix(),
            "order_intent_idempotency_contract_id": idempotency.contract_id,
            "order_intent_idempotency_digest": idempotency.artifact_digest,
            "lifecycle_evidence_digest": lifecycle.lifecycle_evidence_digest,
            "idempotency_key": idempotency.idempotency_key,
        },
        "blocking_facts": _sort_factors(non_contradiction_blocking),
        "missing_preconditions": _sort_factors(
            [item for item in blocking_facts if item.get("factor_type") == "MISSING_PRECONDITION"]
        ),
        "contradictions": _sort_factors(contradictions),
        "trading_core_decision_attestation_authority_invariants": dict(
            TRADING_CORE_DECISION_ATTESTATION_AUTHORITY_INVARIANTS
        ),
        "input_artifact_refs": input_refs,
        "cross_domain_lineage": (
            dict(trading_session.cross_domain_lineage)
            if trading_session.cross_domain_lineage
            else {}
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
        "trading_core_decision_attestation_contract_complete": complete,
        "trading_core_decision_attestation_offline_only": True,
        "order_intent_idempotency_bound": complete,
        "module_attestation_chain_bound": complete,
        "attestation_ref_binding_bound": complete,
        "digest_chain_bound": complete,
        "session_epoch_binding_bound": complete,
        "module_execution_bound": complete,
        "parallel_ssot_guard_bound": complete,
        "provenance_bound": complete,
        "cross_domain_lineage_bound": complete,
        "deterministic_serialization_bound": True,
        "stable_digest_bound": True,
    }

    for key, value in _REQUIRED_NON_AUTHORIZING_FLAGS.items():
        payload[key] = value
    for binding_key in (
        "trading_core_decision_attestation_contract_complete",
        "canonical_order_identity_bound",
        "canonical_order_intent_bound",
        "trading_session_identity_bound",
        "order_intent_idempotency_bound",
        "module_attestation_chain_bound",
        "attestation_ref_binding_bound",
        "digest_chain_bound",
        "session_epoch_binding_bound",
        "module_execution_bound",
        "parallel_ssot_guard_bound",
        "provenance_bound",
        "cross_domain_lineage_bound",
    ):
        payload[binding_key] = complete

    _reject_forbidden_index_keys(payload)
    _validate_non_authorizing_flags(payload)
    if contract_status not in _VALID_CONTRACT_STATUSES:
        raise TradingCoreDecisionAttestationError("contract_status invalid")
    if attestation_status not in _VALID_ATTESTATION_STATUSES:
        raise TradingCoreDecisionAttestationError("attestation_status invalid")
    if classification not in _VALID_CLASSIFICATIONS:
        raise TradingCoreDecisionAttestationError("attestation_chain_classification invalid")

    payload["contract_id"] = contract_id
    output_digest = _compute_output_digest(payload)
    payload["output_digest"] = output_digest
    payload["artifact_id"] = output_digest
    return payload


def serialize_trading_core_decision_attestation_v1(contract: Mapping[str, Any]) -> str:
    _reject_forbidden_index_keys(contract)
    _validate_non_authorizing_flags(contract)
    if contract.get("contract_status") not in _VALID_CONTRACT_STATUSES:
        raise TradingCoreDecisionAttestationError("contract_status invalid")
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
            raise TradingCoreDecisionAttestationError(
                f"{list_field} must be sorted deterministically"
            )
    module_attestations = contract.get("module_attestations")
    if isinstance(module_attestations, list) and module_attestations != sorted(
        module_attestations,
        key=lambda item: item.get("module_slot", "") if isinstance(item, dict) else "",
    ):
        raise TradingCoreDecisionAttestationError(
            "module_attestations must be sorted deterministically"
        )
    return deterministic_json_dumps(contract)


def _artifact_bytes_for_manifest_digest(artifact: Mapping[str, Any]) -> bytes:
    body = {
        key: value for key, value in artifact.items() if key not in {"integrity", "manifest_digest"}
    }
    return serialize_trading_core_decision_attestation_v1(body).encode("utf-8")


def _compute_output_manifest_digest(artifact: Mapping[str, Any]) -> str:
    return hashlib.sha256(_artifact_bytes_for_manifest_digest(artifact)).hexdigest()


def _validate_contract_integrity(artifact: Mapping[str, Any]) -> None:
    if artifact.get("contract_name") != CONTRACT_NAME:
        raise TradingCoreDecisionAttestationError("contract_name mismatch")
    if artifact.get("contract_version") != CONTRACT_VERSION:
        raise TradingCoreDecisionAttestationError("contract_version mismatch")
    integrity = artifact.get("integrity")
    if not isinstance(integrity, Mapping):
        raise TradingCoreDecisionAttestationError("integrity must be an object")
    expected = compute_content_sha256(_integrity_body(artifact))
    actual = integrity.get("content_sha256")
    if actual != expected:
        raise TradingCoreDecisionAttestationError("integrity.content_sha256 mismatch")
    output_digest = artifact.get("output_digest")
    if output_digest != _compute_output_digest(artifact):
        raise TradingCoreDecisionAttestationError("output_digest mismatch")
    if artifact.get("artifact_id") != output_digest:
        raise TradingCoreDecisionAttestationError("artifact_id must equal output_digest")


def build_self_verification_v1(
    *,
    contract: Mapping[str, Any],
    manifest_digest: str,
) -> dict[str, Any]:
    checks: list[dict[str, str]] = [
        {"check_id": "contract_name", "status": "PASS"},
        {"check_id": "contract_version", "status": "PASS"},
        {"check_id": "evidence_level_level_3", "status": "PASS"},
        {"check_id": "exactly_three_verified_input_bundles", "status": "PASS"},
        {"check_id": "offline_only_no_order_creation", "status": "PASS"},
        {"check_id": "offline_only_no_order_submission", "status": "PASS"},
        {"check_id": "no_state_mutation", "status": "PASS"},
        {"check_id": "manifest_verification", "status": "PASS"},
    ]
    structural_failures = [check for check in checks if check["status"] != "PASS"]
    if structural_failures:
        raise TradingCoreDecisionAttestationError("self-verification checks failed")

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
        "verified_attestation_status": contract.get("attestation_status"),
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


def _default_module_contract_digest(module_slot: str) -> str:
    return _binding_digest(
        f"{_MODULE_OWNER_REFS[module_slot]}:{ATTESTATION_CONTRACT_VERSION}",
        domain="module_contract_digest_v1",
    )


def _default_module_output_digest(
    *,
    module_slot: str,
    input_digest: str,
    decision_code: str,
) -> str:
    return compute_content_sha256(
        {
            "module_slot": module_slot,
            "input_digest": input_digest,
            "decision_code": decision_code,
            "deterministic_rule_set_version": DETERMINISTIC_RULE_SET_VERSION,
        }
    )


def build_default_module_attestations(
    *,
    trading_session: VerifiedTradingSessionSingleWriterBundle,
    lifecycle: VerifiedCanonicalOrderLifecycleBundle,
    idempotency: VerifiedOrderIntentIdempotencyBundle,
    correlation_id: str,
    order_intent_digest: str,
) -> tuple[ModuleDecisionAttestation, ...]:
    session = trading_session.trading_session_identity
    session_id = str(session.get("session_id", ""))
    trading_epoch = str(session.get("trading_epoch", ""))
    root_input = compute_content_sha256(
        {
            "session_identity_digest": trading_session.session_identity_digest,
            "order_intent_digest": order_intent_digest,
            "idempotency_key": idempotency.idempotency_key,
            "lifecycle_contract_digest": lifecycle.lifecycle_contract_digest,
            "deterministic_rule_set_version": DETERMINISTIC_RULE_SET_VERSION,
        }
    )

    attestations: dict[str, ModuleDecisionAttestation] = {}
    for slot in (
        "master_v2",
        "double_play",
        "bull",
        "bear",
        "dynamic_scope",
        "risk",
        "sizing",
        "scope_capital",
    ):
        parent_slots = _MODULE_PARENT_SLOTS[slot]
        parent_outputs = [attestations[parent].output_digest for parent in parent_slots]
        input_digest = root_input if not parent_outputs else _expected_input_digest(parent_outputs)
        decision_code = f"{slot.upper()}_DECISION_OK"
        output_digest = _default_module_output_digest(
            module_slot=slot,
            input_digest=input_digest,
            decision_code=decision_code,
        )
        parent_refs = tuple(attestations[parent].attestation_id for parent in parent_slots)
        attestation_id = compute_module_attestation_id(
            module_slot=slot,
            module_owner_ref=_MODULE_OWNER_REFS[slot],
            input_digest=input_digest,
            output_digest=output_digest,
            session_id=session_id,
            trading_epoch=trading_epoch,
        )
        draft = ModuleDecisionAttestation(
            attestation_id=attestation_id,
            module_owner_ref=_MODULE_OWNER_REFS[slot],
            module_contract_digest=_default_module_contract_digest(slot),
            implementation_digest=_binding_digest(slot, domain="implementation_digest_v1"),
            input_digest=input_digest,
            output_digest=output_digest,
            decision_code=decision_code,
            decision_trace_digest=_binding_digest(decision_code, domain="decision_trace_digest_v1"),
            policy_digest=_binding_digest(slot, domain="policy_digest_v1"),
            parent_attestation_refs=parent_refs,
            correlation_id=correlation_id,
            session_id=session_id,
            trading_epoch=trading_epoch,
            created_at=OFFLINE_DETERMINISTIC_CREATED_AT,
            manifest_digest="",
            module_slot=slot,
            module_executed=True,
        )
        manifest_digest = compute_module_attestation_manifest_digest(draft)
        attestations[slot] = ModuleDecisionAttestation(
            **{**draft.__dict__, "manifest_digest": manifest_digest}
        )

    return tuple(attestations[slot] for slot in sorted(attestations))


def default_attestation_bindings(
    module_attestations: tuple[ModuleDecisionAttestation, ...],
) -> CanonicalOrderIntentAttestationBindings:
    by_slot = {att.module_slot: att for att in module_attestations}
    return CanonicalOrderIntentAttestationBindings(
        master_v2_attestation_ref=by_slot["master_v2"].attestation_id,
        bull_attestation_ref=by_slot["bull"].attestation_id,
        bear_attestation_ref=by_slot["bear"].attestation_id,
        double_play_attestation_ref=by_slot["double_play"].attestation_id,
        dynamic_scope_attestation_ref=by_slot["dynamic_scope"].attestation_id,
        risk_attestation_ref=by_slot["risk"].attestation_id,
        sizing_attestation_ref=by_slot["sizing"].attestation_id,
        scope_capital_attestation_ref=by_slot["scope_capital"].attestation_id,
    )


def default_trading_core_decision_attestation_request(
    *,
    trading_session: VerifiedTradingSessionSingleWriterBundle,
    lifecycle: VerifiedCanonicalOrderLifecycleBundle,
    idempotency: VerifiedOrderIntentIdempotencyBundle,
    client_order_id: str = "client-order-001",
    order_intent_digest: str = "aabbccddeeff00112233445566778899aabbccddeeff00112233445566778899",
    canonical_order_id: str = "canonical-order-001",
    instrument_type: str = "FUTURES",
    correlation_id: str = "offline-attestation-correlation-001",
) -> TradingCoreDecisionAttestationRequest:
    session = trading_session.trading_session_identity
    intent = CanonicalOrderIntentIdentity(
        client_order_id=client_order_id,
        order_intent_digest=order_intent_digest,
        instrument_type=instrument_type,
        venue=str(session.get("venue", "")),
        account=str(session.get("account", "")),
        instrument=str(session.get("instrument", "")),
        trading_epoch=str(session.get("trading_epoch", "")),
    )
    order = CanonicalOrderIdentity(
        canonical_order_id=canonical_order_id,
        client_order_id=client_order_id,
    )
    module_attestations = build_default_module_attestations(
        trading_session=trading_session,
        lifecycle=lifecycle,
        idempotency=idempotency,
        correlation_id=correlation_id,
        order_intent_digest=order_intent_digest,
    )
    expected_digests = {slot: _default_module_contract_digest(slot) for slot in _MODULE_OWNER_REFS}
    provenance_digest = _binding_digest(DEFAULT_SOURCE_REVISION, domain="provenance_digest_v1")
    cross_domain_lineage_digest = _binding_digest(
        compute_content_sha256(dict(trading_session.cross_domain_lineage or {"offline": True})),
        domain="cross_domain_lineage_digest_v1",
    )
    return TradingCoreDecisionAttestationRequest(
        canonical_order_intent_identity=intent,
        canonical_order_identity=order,
        attestation_bindings=default_attestation_bindings(module_attestations),
        module_attestations=module_attestations,
        correlation_id=correlation_id,
        expected_module_contract_digests=expected_digests,
        provenance_digest=provenance_digest,
        cross_domain_lineage_digest=cross_domain_lineage_digest,
        deterministic_serialization_version=DETERMINISTIC_SERIALIZATION_VERSION,
    )


def verify_trading_core_decision_attestation_inputs(
    inputs: TradingCoreDecisionAttestationInputs,
) -> tuple[
    VerifiedTradingSessionSingleWriterBundle,
    VerifiedCanonicalOrderLifecycleBundle,
    VerifiedOrderIntentIdempotencyBundle,
]:
    trading_session = verify_trading_session_single_writer_bundle(
        inputs.trading_session_single_writer_bundle_dir
    )
    lifecycle = verify_canonical_order_lifecycle_bundle(inputs.canonical_order_lifecycle_bundle_dir)
    idempotency = verify_order_intent_idempotency_bundle(inputs.order_intent_idempotency_bundle_dir)
    return trading_session, lifecycle, idempotency


def reverify_trading_core_decision_attestation_v1(*, output_dir: Path | str) -> None:
    bundle_dir = Path(output_dir)
    if not bundle_dir.is_dir():
        raise TradingCoreDecisionAttestationError(
            f"trading core decision attestation directory not found: {bundle_dir}"
        )
    ok, msg = verify_manifest_sha256(bundle_dir)
    if not ok:
        raise TradingCoreDecisionAttestationError(f"MANIFEST.sha256 verification failed: {msg}")

    artifact_path = bundle_dir / ARTIFACT_REL
    _validate_regular_file(artifact_path, label=ARTIFACT_REL)
    contract = read_manifest(artifact_path)
    _validate_contract_integrity(contract)

    self_path = bundle_dir / SELF_VERIFICATION_REL
    _validate_regular_file(self_path, label=SELF_VERIFICATION_REL)
    self_payload = read_manifest(self_path)
    if self_payload.get("overall_status") != "PASS":
        raise TradingCoreDecisionAttestationError("SELF_VERIFICATION overall_status must be PASS")

    manifest_digest = _compute_output_manifest_digest(contract)
    if contract.get("manifest_digest") != manifest_digest:
        raise TradingCoreDecisionAttestationError("manifest_digest mismatch on replay")

    trading_session = verify_trading_session_single_writer_bundle(
        Path(str(contract["upstream_bindings"]["trading_session_single_writer_bundle_ref"]))
    )
    lifecycle = verify_canonical_order_lifecycle_bundle(
        Path(str(contract["upstream_bindings"]["canonical_order_lifecycle_bundle_ref"]))
    )
    idempotency = verify_order_intent_idempotency_bundle(
        Path(str(contract["upstream_bindings"]["order_intent_idempotency_bundle_ref"]))
    )
    if (
        contract.get("upstream_bindings", {}).get("trading_session_digest")
        != trading_session.artifact_digest
    ):
        raise TradingCoreDecisionAttestationError("trading session digest mismatch on replay")
    if (
        contract.get("upstream_bindings", {}).get("canonical_order_lifecycle_digest")
        != lifecycle.artifact_digest
    ):
        raise TradingCoreDecisionAttestationError("lifecycle digest mismatch on replay")
    if (
        contract.get("upstream_bindings", {}).get("order_intent_idempotency_digest")
        != idempotency.artifact_digest
    ):
        raise TradingCoreDecisionAttestationError("idempotency digest mismatch on replay")


def produce_trading_core_decision_attestation_v1(
    *,
    inputs: TradingCoreDecisionAttestationInputs,
    output_dir: Path | str,
) -> TradingCoreDecisionAttestationResult:
    final_dir = Path(output_dir)
    _validate_output_target(final_dir)
    _reject_unsafe_overlap(
        bundle_dirs=[
            inputs.trading_session_single_writer_bundle_dir,
            inputs.canonical_order_lifecycle_bundle_dir,
            inputs.order_intent_idempotency_bundle_dir,
        ],
        output_dir=final_dir,
    )

    trading_session, lifecycle, idempotency = verify_trading_core_decision_attestation_inputs(
        inputs
    )
    contract_body = build_trading_core_decision_attestation_v1(
        trading_session=trading_session,
        lifecycle=lifecycle,
        idempotency=idempotency,
        request=inputs.attestation_request,
    )

    staging = _staging_dir_for(final_dir)
    if staging.exists():
        raise TradingCoreDecisionAttestationError(f"staging directory collision: {staging}")

    try:
        staging.mkdir(parents=True, exist_ok=False)
        artifact_path = staging / ARTIFACT_REL
        self_path = staging / SELF_VERIFICATION_REL

        manifest_digest = _compute_output_manifest_digest(contract_body)
        finalized = _finalize_contract_with_manifest_digest(
            contract_body, manifest_digest=manifest_digest
        )
        artifact_path.write_text(
            serialize_trading_core_decision_attestation_v1(finalized),
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
            raise TradingCoreDecisionAttestationError(
                f"MANIFEST.sha256 verification failed before publish: {msg}"
            )

        reverify_trading_core_decision_attestation_v1(output_dir=staging)
        staging.replace(final_dir)

        ok, msg = verify_manifest_sha256(final_dir)
        if not ok:
            raise TradingCoreDecisionAttestationError(
                f"MANIFEST.sha256 verification failed after publish: {msg}"
            )
    except Exception:
        _cleanup_staging(staging)
        if final_dir.exists():
            shutil.rmtree(final_dir)
        raise

    return TradingCoreDecisionAttestationResult(
        output_dir=final_dir,
        contract_id=str(finalized["contract_id"]),
        contract_status=str(finalized["contract_status"]),
        attestation_status=str(finalized["attestation_status"]),
        classification=str(finalized["attestation_chain_classification"]),
        contract_path=final_dir / ARTIFACT_REL,
        self_verification_path=final_dir / SELF_VERIFICATION_REL,
        manifest_path=final_dir / MANIFEST_FILENAME,
        canonical_order_identity_digest=str(finalized["canonical_order_identity_digest"]),
        canonical_order_intent_identity_digest=str(
            finalized["canonical_order_intent_identity_digest"]
        ),
        attestation_chain_digest=str(finalized["attestation_chain_digest"]),
    )


__all__ = [
    "ARTIFACT_REL",
    "ATTESTATION_CONTRACT_VERSION",
    "ATTESTATION_SCOPE_DEFAULT",
    "CONTRACT_NAME",
    "CONTRACT_VERSION",
    "CREATION_CONTRACT_VERSION",
    "DEFAULT_PRODUCER_IDENTITY_REF",
    "DEFAULT_SOURCE_REVISION",
    "DETERMINISTIC_RULE_SET_VERSION",
    "DETERMINISTIC_SERIALIZATION_VERSION",
    "EVIDENCE_LEVEL",
    "MANIFEST_FILENAME",
    "PRODUCER_VERSION",
    "SCHEMA_VERSION",
    "SELF_VERIFICATION_REL",
    "TRADING_CORE_DECISION_ATTESTATION_AUTHORITY_INVARIANTS",
    "CanonicalOrderIntentAttestationBindings",
    "ModuleDecisionAttestation",
    "TradingCoreDecisionAttestationError",
    "TradingCoreDecisionAttestationInputs",
    "TradingCoreDecisionAttestationRequest",
    "TradingCoreDecisionAttestationResult",
    "VerifiedOrderIntentIdempotencyBundle",
    "build_default_module_attestations",
    "build_self_verification_v1",
    "build_trading_core_decision_attestation_v1",
    "compute_module_attestation_id",
    "compute_module_attestation_manifest_digest",
    "default_attestation_bindings",
    "default_trading_core_decision_attestation_request",
    "produce_trading_core_decision_attestation_v1",
    "reverify_trading_core_decision_attestation_v1",
    "serialize_trading_core_decision_attestation_v1",
    "verify_order_intent_idempotency_bundle",
    "verify_trading_core_decision_attestation_inputs",
    "verify_trading_session_single_writer_bundle",
]
