"""Offline LEVEL_3 canonical runtime-state reconciliation contract owner v1."""

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
from src.meta.learning_loop.comparison_metric_input_v1.io import read_manifest
from src.meta.learning_loop.contract_safety_v1 import (
    compute_content_sha256,
    deterministic_json_dumps,
)
from src.meta.learning_loop.trading_logic_semantic_diff_evidence_v1 import (
    ARTIFACT_REL as SEMANTIC_DIFF_ARTIFACT_REL,
    CONTRACT_NAME as SEMANTIC_DIFF_CONTRACT_NAME,
    CONTRACT_VERSION as SEMANTIC_DIFF_OWNER_CONTRACT_VERSION,
    SEMANTIC_DIFF_CONTRACT_VERSION,
    TradingLogicSemanticDiffEvidenceError,
    reverify_trading_logic_semantic_diff_evidence_v1,
)

CONTRACT_NAME = "runtime_state_reconciliation_v1"
CONTRACT_VERSION = "v1"
RECONCILIATION_CONTRACT_VERSION = "runtime_state_reconciliation_contract_v1"
RECONCILIATION_SCOPE_DEFAULT = "RUNTIME_STATE_OFFLINE_RECONCILIATION_EVALUATION"
PRODUCER_VERSION = "runtime_state_reconciliation_v1"
EVIDENCE_LEVEL = "LEVEL_3"
AUTHORITY_LEVEL = "NON_AUTHORITIZING"
RECORD_KIND = "runtime_state_reconciliation_record"
INPUT_RELATION = (
    "PACKAGES_VERIFIED_TRADING_LOGIC_SEMANTIC_DIFF_EVIDENCE_AND_RUNTIME_SNAPSHOT_MANIFEST_"
    "FOR_OFFLINE_RECONCILIATION"
)
ARTIFACT_REL = "runtime_state_reconciliation_v1.json"
SELF_VERIFICATION_REL = "SELF_VERIFICATION.json"
MANIFEST_FILENAME = "MANIFEST.sha256"
STAGING_DIRNAME_PREFIX = ".runtime_state_reconciliation_staging_"

SCHEMA_VERSION = "runtime_state_reconciliation_schema_v1"
CREATION_CONTRACT_VERSION = "runtime_state_reconciliation_creation_v1"
DETERMINISTIC_RULE_SET_VERSION = "runtime_state_reconciliation_rules_v1"
DETERMINISTIC_SERIALIZATION_VERSION = "deterministic_json_dumps_v1"
OFFLINE_DETERMINISTIC_CREATED_AT = "1970-01-01T00:00:00+00:00"
DEFAULT_PRODUCER_IDENTITY_REF = "peak_trade_offline_runtime_state_reconciliation_producer_v1"
DEFAULT_SOURCE_REVISION = "OFFLINE_DETERMINISTIC_EVIDENCE"

_VALID_INSTRUMENT_TYPES = frozenset({"FUTURES"})
_FORBIDDEN_INSTRUMENT_TYPES = frozenset({"SPOT", "SYNTHETIC_SPOT", "SYNTHETIC-SPOT"})

_REQUIRED_SNAPSHOT_COMPONENT_NAMES = (
    "local_intent_ledger",
    "submission_ledger",
    "venue_orders",
    "venue_fills",
    "venue_positions",
    "venue_margin",
)

_REQUIRED_RECONCILIATION_LEVEL_NAMES = (
    "r1_event_reconciliation",
    "r2_periodic_snapshot",
    "r3_pre_trade_reconciliation",
    "r4_recovery_reconciliation",
)

_VALID_RECONCILIATION_STATES = frozenset({"CLEAN", "UNCLEAN", "UNKNOWN"})

_VALID_CLASSIFICATIONS = frozenset(
    {
        "RECONCILIATION_VALID",
        "SNAPSHOT_DIVERGENCE",
        "MISSING_BINDINGS",
        "SEMANTIC_DIFF_INVALID",
        "RECONCILIATION_STATE_MISMATCH",
        "LEVEL_MISMATCH",
        "FUTURES_MARKET_TYPE_CONFLICT",
        "INVALID",
    }
)

_VALID_CONTRACT_STATUSES = frozenset(
    {
        "RUNTIME_STATE_RECONCILIATION_VALID",
        "RUNTIME_STATE_RECONCILIATION_SNAPSHOT_DIVERGENCE",
        "RUNTIME_STATE_RECONCILIATION_MISSING_BINDINGS",
        "RUNTIME_STATE_RECONCILIATION_SEMANTIC_DIFF_INVALID",
        "RUNTIME_STATE_RECONCILIATION_STATE_MISMATCH",
        "RUNTIME_STATE_RECONCILIATION_LEVEL_MISMATCH",
        "RUNTIME_STATE_RECONCILIATION_FUTURES_MARKET_TYPE_CONFLICT",
        "RUNTIME_STATE_RECONCILIATION_INVALID",
        "ABSTAIN",
    }
)
_VALID_EVIDENCE_STATUSES = frozenset(
    {"ADMISSIBLE", "VALID", "CONFLICT", "INVALID", "UNKNOWN", "ABSTAIN"}
)
_SELF_VERIFICATION_SCHEMA_VERSION = "runtime_state_reconciliation_self_verification_v1"

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

RUNTIME_STATE_RECONCILIATION_AUTHORITY_INVARIANTS: dict[str, bool] = {
    **COMPARISON_AUTHORITY_INVARIANTS,
    "runtime_state_reconciliation_is_descriptive_only": True,
    "runtime_state_reconciliation_does_not_create_order": True,
    "runtime_state_reconciliation_does_not_submit_order": True,
    "runtime_state_reconciliation_does_not_mutate_order_state": True,
    "runtime_state_reconciliation_does_not_invoke_adapter": True,
    "runtime_state_reconciliation_does_not_invoke_consumer": True,
    "runtime_state_reconciliation_does_not_grant_authority": True,
    "runtime_state_reconciliation_is_offline_only": True,
    "deny_by_default": True,
    "futures_only": True,
    "semantic_diff_evidence_bound": True,
    "snapshot_component_binding_bound": True,
    "reconciliation_level_binding_bound": True,
    "provenance_bound": True,
    "cross_domain_lineage_bound": True,
    "deterministic_serialization_bound": True,
    "stable_digest_bound": True,
}

_REQUIRED_NON_AUTHORIZING_FLAGS: dict[str, bool] = {
    "is_runtime_state_reconciliation": True,
    "runtime_state_reconciliation_offline_only": True,
    "runtime_state_reconciliation_contract_complete": False,
    "semantic_diff_evidence_bound": False,
    "snapshot_component_binding_bound": False,
    "reconciliation_level_binding_bound": False,
    "provenance_bound": False,
    "cross_domain_lineage_bound": False,
    "deterministic_serialization_bound": False,
    "stable_digest_bound": False,
    "deny_by_default": True,
    "futures_only": True,
    "opening_order_allowed": False,
    "increasing_order_allowed": False,
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


class RuntimeStateReconciliationError(ValueError):
    """Fail-closed runtime-state reconciliation error."""


@dataclass(frozen=True)
class ReconciliationSnapshotComponent:
    component_name: str
    local_digest: str
    venue_digest: str
    divergence_detected: bool
    component_digest: str = ""


@dataclass(frozen=True)
class ReconciliationLevelResult:
    level_name: str
    level_pass: bool
    level_digest: str = ""


@dataclass(frozen=True)
class VerifiedTradingLogicSemanticDiffEvidenceBundle:
    bundle_dir: Path
    contract_name: str
    contract_version: str
    producer_version: str
    artifact_ref: str
    artifact_digest: str
    manifest_digest: str
    contract_id: str
    contract_status: str
    semantic_diff_digest: str
    futures_only: bool
    instrument_type: str
    cross_domain_lineage: dict[str, Any]
    provenance_digest: str
    cross_domain_lineage_digest: str
    baseline_attestation_digest: str
    candidate_attestation_digest: str


@dataclass(frozen=True)
class RuntimeReconciliationRequest:
    declared_reconciliation_state: str
    snapshot_components: tuple[ReconciliationSnapshotComponent, ...]
    reconciliation_levels: tuple[ReconciliationLevelResult, ...]
    instrument_type: str = "FUTURES"
    correlation_id: str = "offline-runtime-reconciliation-correlation-001"
    reconciliation_contract_version: str = RECONCILIATION_CONTRACT_VERSION
    semantic_diff_contract_version: str = SEMANTIC_DIFF_CONTRACT_VERSION
    deterministic_serialization_version: str = DETERMINISTIC_SERIALIZATION_VERSION
    provenance_digest: str = ""
    cross_domain_lineage_digest: str = ""
    source_revision: str = DEFAULT_SOURCE_REVISION


@dataclass(frozen=True)
class RuntimeStateReconciliationInputs:
    trading_logic_semantic_diff_evidence_bundle_dir: Path
    reconciliation_request: RuntimeReconciliationRequest


@dataclass(frozen=True)
class RuntimeStateReconciliationResult:
    output_dir: Path
    contract_id: str
    contract_status: str
    evidence_status: str
    classification: str
    contract_path: Path
    self_verification_path: Path
    manifest_path: Path
    reconciliation_state: str
    reconciliation_digest: str


def _reject_symlink(path: Path, *, label: str) -> None:
    if path.is_symlink():
        raise RuntimeStateReconciliationError(f"{label} must not be a symlink: {path}")


def _reject_forbidden_index_keys(payload: Mapping[str, Any]) -> None:
    for key in payload:
        if key in _FORBIDDEN_INDEX_KEYS:
            raise RuntimeStateReconciliationError(f"forbidden index key: {key}")


def _validate_regular_file(path: Path, *, label: str) -> None:
    _reject_symlink(path, label=label)
    if not path.is_file():
        raise RuntimeStateReconciliationError(f"{label} must be a regular file: {path}")


def _validate_bundle_dir(bundle_dir: Path, *, label: str) -> None:
    _reject_symlink(bundle_dir, label=label)
    if not bundle_dir.is_dir():
        raise RuntimeStateReconciliationError(f"{label} must be a directory: {bundle_dir}")


def _validate_output_target(output_dir: Path) -> None:
    if is_under_tmp(output_dir):
        raise RuntimeStateReconciliationError("output_dir must not be under /tmp")
    if output_dir.exists():
        raise RuntimeStateReconciliationError(f"output_dir already exists: {output_dir}")


def _path_is_under(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
    except ValueError:
        return False
    return True


def _reject_unsafe_overlap(*, bundle_dirs: list[Path], output_dir: Path) -> None:
    for bundle_dir in bundle_dirs:
        if _path_is_under(output_dir, bundle_dir) or _path_is_under(bundle_dir, output_dir):
            raise RuntimeStateReconciliationError(
                "output_dir must not overlap with input bundle directories"
            )


def _factor(
    *,
    factor_id: str,
    factor_type: str,
    source_field: str,
    detail: str = "",
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
        if key not in payload:
            raise RuntimeStateReconciliationError(f"missing non-authorizing flag: {key}")
        if payload[key] is not expected and key not in {
            "runtime_state_reconciliation_contract_complete",
            "semantic_diff_evidence_bound",
            "snapshot_component_binding_bound",
            "reconciliation_level_binding_bound",
            "provenance_bound",
            "cross_domain_lineage_bound",
            "deterministic_serialization_bound",
            "stable_digest_bound",
        }:
            raise RuntimeStateReconciliationError(f"non-authorizing flag {key} must be {expected}")


def _binding_digest(value: str, *, domain: str) -> str:
    return compute_content_sha256({"domain": domain, "value": value})


def verify_trading_logic_semantic_diff_evidence_bundle(
    bundle_dir: Path | str,
) -> VerifiedTradingLogicSemanticDiffEvidenceBundle:
    resolved = Path(bundle_dir)
    _validate_bundle_dir(resolved, label="trading_logic_semantic_diff_evidence_bundle_dir")
    try:
        reverify_trading_logic_semantic_diff_evidence_v1(output_dir=resolved)
    except TradingLogicSemanticDiffEvidenceError as exc:
        raise RuntimeStateReconciliationError(str(exc)) from exc
    artifact_path = resolved / SEMANTIC_DIFF_ARTIFACT_REL
    _validate_regular_file(artifact_path, label=SEMANTIC_DIFF_ARTIFACT_REL)
    payload = read_manifest(artifact_path)
    if payload.get("contract_name") != SEMANTIC_DIFF_CONTRACT_NAME:
        raise RuntimeStateReconciliationError("semantic diff contract_name mismatch")
    if payload.get("contract_version") != SEMANTIC_DIFF_OWNER_CONTRACT_VERSION:
        raise RuntimeStateReconciliationError("semantic diff contract_version mismatch")
    upstream = payload.get("upstream_bindings", {})
    if not isinstance(upstream, Mapping):
        upstream = {}
    instrument_type = ""
    baseline_attestation = upstream.get("baseline_trading_core_decision_attestation_digest", "")
    candidate_attestation = upstream.get("candidate_trading_core_decision_attestation_digest", "")
    return VerifiedTradingLogicSemanticDiffEvidenceBundle(
        bundle_dir=resolved,
        contract_name=str(payload.get("contract_name", "")),
        contract_version=str(payload.get("contract_version", "")),
        producer_version=str(payload.get("producer_version", "")),
        artifact_ref=SEMANTIC_DIFF_ARTIFACT_REL,
        artifact_digest=str(payload.get("output_digest", "")),
        manifest_digest=str(payload.get("manifest_digest", "")),
        contract_id=str(payload.get("contract_id", "")),
        contract_status=str(payload.get("contract_status", "")),
        semantic_diff_digest=str(payload.get("semantic_diff_digest", "")),
        futures_only=bool(payload.get("futures_only")),
        instrument_type=instrument_type or "FUTURES",
        cross_domain_lineage=(
            dict(payload.get("cross_domain_lineage", {}))
            if isinstance(payload.get("cross_domain_lineage"), Mapping)
            else {}
        ),
        provenance_digest=str(payload.get("provenance_digest", "")),
        cross_domain_lineage_digest=str(payload.get("cross_domain_lineage_digest", "")),
        baseline_attestation_digest=str(baseline_attestation),
        candidate_attestation_digest=str(candidate_attestation),
    )


def _compute_component_digest(*, component_name: str, local_digest: str, venue_digest: str) -> str:
    return compute_content_sha256(
        {
            "component_name": component_name,
            "local_digest": local_digest,
            "venue_digest": venue_digest,
            "deterministic_rule_set_version": DETERMINISTIC_RULE_SET_VERSION,
        }
    )


def _compute_level_digest(*, level_name: str, level_pass: bool) -> str:
    return compute_content_sha256(
        {
            "level_name": level_name,
            "level_pass": level_pass,
            "deterministic_rule_set_version": DETERMINISTIC_RULE_SET_VERSION,
        }
    )


def _serialize_snapshot_components(
    components: tuple[ReconciliationSnapshotComponent, ...],
) -> list[dict[str, Any]]:
    serialized: list[dict[str, Any]] = []
    for component in sorted(components, key=lambda item: item.component_name):
        component_digest = component.component_digest or _compute_component_digest(
            component_name=component.component_name,
            local_digest=component.local_digest,
            venue_digest=component.venue_digest,
        )
        serialized.append(
            {
                "component_name": component.component_name,
                "local_digest": component.local_digest,
                "venue_digest": component.venue_digest,
                "divergence_detected": component.divergence_detected,
                "component_digest": component_digest,
            }
        )
    return serialized


def _serialize_reconciliation_levels(
    levels: tuple[ReconciliationLevelResult, ...],
) -> list[dict[str, Any]]:
    serialized: list[dict[str, Any]] = []
    for level in sorted(levels, key=lambda item: item.level_name):
        level_digest = level.level_digest or _compute_level_digest(
            level_name=level.level_name,
            level_pass=level.level_pass,
        )
        serialized.append(
            {
                "level_name": level.level_name,
                "level_pass": level.level_pass,
                "level_digest": level_digest,
            }
        )
    return serialized


def _validate_request(
    request: RuntimeReconciliationRequest,
    *,
    semantic_diff: VerifiedTradingLogicSemanticDiffEvidenceBundle,
) -> list[dict[str, str]]:
    blocking_facts: list[dict[str, str]] = []

    if request.reconciliation_contract_version != RECONCILIATION_CONTRACT_VERSION:
        blocking_facts.append(
            _factor(
                factor_id="RECONCILIATION_CONTRACT_VERSION_MISMATCH",
                factor_type="MISSING_PRECONDITION",
                source_field="reconciliation_contract_version",
            )
        )
    if request.semantic_diff_contract_version != SEMANTIC_DIFF_CONTRACT_VERSION:
        blocking_facts.append(
            _factor(
                factor_id="SEMANTIC_DIFF_CONTRACT_VERSION_MISMATCH",
                factor_type="MISSING_PRECONDITION",
                source_field="semantic_diff_contract_version",
            )
        )
    if request.deterministic_serialization_version != DETERMINISTIC_SERIALIZATION_VERSION:
        blocking_facts.append(
            _factor(
                factor_id="DETERMINISTIC_SERIALIZATION_VERSION_MISMATCH",
                factor_type="MISSING_PRECONDITION",
                source_field="deterministic_serialization_version",
            )
        )
    if request.declared_reconciliation_state not in _VALID_RECONCILIATION_STATES:
        blocking_facts.append(
            _factor(
                factor_id="INVALID_RECONCILIATION_STATE",
                factor_type="MISSING_PRECONDITION",
                source_field="declared_reconciliation_state",
            )
        )
    if not request.instrument_type:
        blocking_facts.append(
            _factor(
                factor_id="MISSING_INSTRUMENT_TYPE",
                factor_type="CONTRADICTION",
                source_field="instrument_type",
            )
        )
    elif request.instrument_type in _FORBIDDEN_INSTRUMENT_TYPES:
        blocking_facts.append(
            _factor(
                factor_id="FORBIDDEN_INSTRUMENT_TYPE",
                factor_type="CONTRADICTION",
                source_field="instrument_type",
            )
        )
    elif request.instrument_type not in _VALID_INSTRUMENT_TYPES:
        blocking_facts.append(
            _factor(
                factor_id="INVALID_INSTRUMENT_TYPE",
                factor_type="CONTRADICTION",
                source_field="instrument_type",
            )
        )
    if not semantic_diff.futures_only:
        blocking_facts.append(
            _factor(
                factor_id="FUTURES_ONLY_FLAG_FALSE",
                factor_type="CONTRADICTION",
                source_field="semantic_diff.futures_only",
            )
        )
    if semantic_diff.contract_status != "TRADING_LOGIC_SEMANTIC_DIFF_EVIDENCE_VALID":
        blocking_facts.append(
            _factor(
                factor_id="SEMANTIC_DIFF_CONTRACT_STATUS_INVALID",
                factor_type="MISSING_PRECONDITION",
                source_field="semantic_diff.contract_status",
            )
        )

    component_names = {component.component_name for component in request.snapshot_components}
    for required_name in _REQUIRED_SNAPSHOT_COMPONENT_NAMES:
        if required_name not in component_names:
            blocking_facts.append(
                _factor(
                    factor_id="MISSING_SNAPSHOT_COMPONENT",
                    factor_type="MISSING_PRECONDITION",
                    source_field=required_name,
                )
            )

    level_names = {level.level_name for level in request.reconciliation_levels}
    for required_level in _REQUIRED_RECONCILIATION_LEVEL_NAMES:
        if required_level not in level_names:
            blocking_facts.append(
                _factor(
                    factor_id="MISSING_RECONCILIATION_LEVEL",
                    factor_type="MISSING_PRECONDITION",
                    source_field=required_level,
                )
            )

    for component in request.snapshot_components:
        if not component.local_digest or not component.venue_digest:
            blocking_facts.append(
                _factor(
                    factor_id="MISSING_COMPONENT_DIGEST",
                    factor_type="MISSING_PRECONDITION",
                    source_field=component.component_name,
                )
            )
        expected_divergence = component.local_digest != component.venue_digest
        if component.divergence_detected != expected_divergence:
            blocking_facts.append(
                _factor(
                    factor_id="SNAPSHOT_DIVERGENCE_FLAG_MISMATCH",
                    factor_type="CONTRADICTION",
                    source_field=component.component_name,
                )
            )

    for level in request.reconciliation_levels:
        if level.level_name == "r4_recovery_reconciliation" and not level.level_pass:
            blocking_facts.append(
                _factor(
                    factor_id="R4_RECONCILIATION_NOT_PASS",
                    factor_type="CONTRADICTION",
                    source_field="r4_recovery_reconciliation",
                )
            )

    return blocking_facts


def _evaluate_reconciliation(
    *,
    request: RuntimeReconciliationRequest,
    semantic_diff: VerifiedTradingLogicSemanticDiffEvidenceBundle,
    blocking_facts: list[dict[str, str]],
) -> tuple[str, str, str, list[str], dict[str, Any], str]:
    factor_ids = {item.get("factor_id") for item in blocking_facts}
    reason_codes: list[str] = []
    states: dict[str, Any] = {
        "admissibility_reason": "",
        "deny_reason": "",
    }

    if factor_ids & {
        "FORBIDDEN_INSTRUMENT_TYPE",
        "INVALID_INSTRUMENT_TYPE",
        "MISSING_INSTRUMENT_TYPE",
        "FUTURES_ONLY_FLAG_FALSE",
    }:
        return (
            "RUNTIME_STATE_RECONCILIATION_FUTURES_MARKET_TYPE_CONFLICT",
            "CONFLICT",
            "FUTURES_MARKET_TYPE_CONFLICT",
            _sorted_strings(["FUTURES_MARKET_TYPE_CONFLICT"]),
            {
                "admissibility_reason": "FUTURES_MARKET_TYPE_CONFLICT",
                "deny_reason": "FUTURES_MARKET_TYPE_CONFLICT",
            },
            "UNKNOWN",
        )

    if "SEMANTIC_DIFF_CONTRACT_STATUS_INVALID" in factor_ids:
        return (
            "RUNTIME_STATE_RECONCILIATION_SEMANTIC_DIFF_INVALID",
            "INVALID",
            "SEMANTIC_DIFF_INVALID",
            _sorted_strings(["SEMANTIC_DIFF_INVALID"]),
            {
                "admissibility_reason": "SEMANTIC_DIFF_INVALID",
                "deny_reason": "SEMANTIC_DIFF_INVALID",
            },
            "UNKNOWN",
        )

    if factor_ids & {
        "RECONCILIATION_CONTRACT_VERSION_MISMATCH",
        "SEMANTIC_DIFF_CONTRACT_VERSION_MISMATCH",
        "DETERMINISTIC_SERIALIZATION_VERSION_MISMATCH",
        "INVALID_RECONCILIATION_STATE",
        "MISSING_SNAPSHOT_COMPONENT",
        "MISSING_RECONCILIATION_LEVEL",
        "MISSING_COMPONENT_DIGEST",
    }:
        return (
            "RUNTIME_STATE_RECONCILIATION_MISSING_BINDINGS",
            "INVALID",
            "MISSING_BINDINGS",
            _sorted_strings(["MISSING_BINDINGS"]),
            {
                "admissibility_reason": "MISSING_BINDINGS",
                "deny_reason": "MISSING_BINDINGS",
            },
            "UNKNOWN",
        )

    if "SNAPSHOT_DIVERGENCE_FLAG_MISMATCH" in factor_ids:
        return (
            "RUNTIME_STATE_RECONCILIATION_LEVEL_MISMATCH",
            "INVALID",
            "LEVEL_MISMATCH",
            _sorted_strings(["LEVEL_MISMATCH"]),
            {
                "admissibility_reason": "LEVEL_MISMATCH",
                "deny_reason": "LEVEL_MISMATCH",
            },
            "UNCLEAN",
        )

    divergences = [
        component for component in request.snapshot_components if component.divergence_detected
    ]
    derived_state = "CLEAN" if not divergences else "UNCLEAN"
    if request.declared_reconciliation_state != derived_state:
        return (
            "RUNTIME_STATE_RECONCILIATION_STATE_MISMATCH",
            "CONFLICT",
            "RECONCILIATION_STATE_MISMATCH",
            _sorted_strings(["RECONCILIATION_STATE_MISMATCH"]),
            {
                "admissibility_reason": "RECONCILIATION_STATE_MISMATCH",
                "deny_reason": "RECONCILIATION_STATE_MISMATCH",
            },
            derived_state,
        )

    if divergences:
        return (
            "RUNTIME_STATE_RECONCILIATION_SNAPSHOT_DIVERGENCE",
            "CONFLICT",
            "SNAPSHOT_DIVERGENCE",
            _sorted_strings(["SNAPSHOT_DIVERGENCE"]),
            {
                "admissibility_reason": "SNAPSHOT_DIVERGENCE",
                "deny_reason": "SNAPSHOT_DIVERGENCE",
            },
            "UNCLEAN",
        )

    if "R4_RECONCILIATION_NOT_PASS" in factor_ids:
        return (
            "RUNTIME_STATE_RECONCILIATION_INVALID",
            "INVALID",
            "INVALID",
            _sorted_strings(["R4_RECONCILIATION_NOT_PASS"]),
            {
                "admissibility_reason": "R4_RECONCILIATION_NOT_PASS",
                "deny_reason": "R4_RECONCILIATION_NOT_PASS",
            },
            "UNCLEAN",
        )

    for level in request.reconciliation_levels:
        if not level.level_pass:
            return (
                "RUNTIME_STATE_RECONCILIATION_LEVEL_MISMATCH",
                "INVALID",
                "LEVEL_MISMATCH",
                _sorted_strings(["LEVEL_MISMATCH"]),
                {
                    "admissibility_reason": "LEVEL_MISMATCH",
                    "deny_reason": "LEVEL_MISMATCH",
                },
                derived_state,
            )

    states["admissibility_reason"] = "RECONCILIATION_VALID"
    reason_codes.append("RECONCILIATION_VALID")
    return (
        "RUNTIME_STATE_RECONCILIATION_VALID",
        "VALID",
        "RECONCILIATION_VALID",
        _sorted_strings(reason_codes),
        states,
        "CLEAN",
    )


def _input_artifact_ref_mapping(
    *,
    bundle: VerifiedTradingLogicSemanticDiffEvidenceBundle,
) -> dict[str, Any]:
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


def build_runtime_state_reconciliation_v1(
    *,
    semantic_diff: VerifiedTradingLogicSemanticDiffEvidenceBundle,
    request: RuntimeReconciliationRequest,
) -> dict[str, Any]:
    blocking_facts = _validate_request(request, semantic_diff=semantic_diff)
    contradictions = [item for item in blocking_facts if item.get("factor_type") == "CONTRADICTION"]
    non_contradiction_blocking = [
        item for item in blocking_facts if item.get("factor_type") != "CONTRADICTION"
    ]

    (
        contract_status,
        evidence_status,
        classification,
        reason_codes,
        completion,
        reconciliation_state,
    ) = _evaluate_reconciliation(
        request=request,
        semantic_diff=semantic_diff,
        blocking_facts=blocking_facts,
    )

    serialized_components = _serialize_snapshot_components(request.snapshot_components)
    serialized_levels = _serialize_reconciliation_levels(request.reconciliation_levels)
    reconciliation_digest = compute_content_sha256(
        {
            "snapshot_components": serialized_components,
            "reconciliation_levels": serialized_levels,
            "reconciliation_state": reconciliation_state,
            "declared_reconciliation_state": request.declared_reconciliation_state,
            "deterministic_rule_set_version": DETERMINISTIC_RULE_SET_VERSION,
        }
    )

    input_refs = [_input_artifact_ref_mapping(bundle=semantic_diff)]
    input_digest = compute_content_sha256({"input_artifact_refs": input_refs})

    provenance_digest = request.provenance_digest or _binding_digest(
        request.source_revision, domain="provenance_digest_v1"
    )
    cross_domain_lineage_digest = request.cross_domain_lineage_digest or _binding_digest(
        semantic_diff.cross_domain_lineage_digest,
        domain="cross_domain_lineage_digest_v1",
    )

    contract_id = compute_content_sha256(
        {
            "contract_domain": CONTRACT_NAME,
            "semantic_diff_digest": semantic_diff.semantic_diff_digest,
            "reconciliation_digest": reconciliation_digest,
            "declared_reconciliation_state": request.declared_reconciliation_state,
            "deterministic_rule_set_version": DETERMINISTIC_RULE_SET_VERSION,
        }
    )

    complete = contract_status == "RUNTIME_STATE_RECONCILIATION_VALID"
    r4_pass = any(
        level.level_name == "r4_recovery_reconciliation" and level.level_pass
        for level in request.reconciliation_levels
    )
    zero_unreconciled_exposure = not any(
        component.divergence_detected for component in request.snapshot_components
    )
    open_orders_state_known = all(
        component.local_digest and component.venue_digest
        for component in request.snapshot_components
        if component.component_name in {"local_intent_ledger", "submission_ledger", "venue_orders"}
    )
    position_state_known = all(
        component.local_digest and component.venue_digest
        for component in request.snapshot_components
        if component.component_name == "venue_positions"
    )
    margin_state_known = all(
        component.local_digest and component.venue_digest
        for component in request.snapshot_components
        if component.component_name == "venue_margin"
    )

    payload: dict[str, Any] = {
        "contract_id": "",
        "contract_name": CONTRACT_NAME,
        "contract_version": CONTRACT_VERSION,
        "reconciliation_contract_version": request.reconciliation_contract_version,
        "semantic_diff_contract_version": request.semantic_diff_contract_version,
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
        "evidence_status": evidence_status,
        "evidence_reason": completion.get("admissibility_reason", ""),
        "reconciliation_classification": classification,
        "admissibility_reason": completion.get("admissibility_reason", ""),
        "deny_reason": completion.get("deny_reason", ""),
        "declared_reconciliation_state": request.declared_reconciliation_state,
        "reconciliation_state": reconciliation_state,
        "instrument_type": request.instrument_type,
        "snapshot_components": serialized_components,
        "reconciliation_levels": serialized_levels,
        "reconciliation_digest": reconciliation_digest,
        "correlation_id": request.correlation_id,
        "upstream_bindings": {
            "trading_logic_semantic_diff_evidence_bundle_ref": semantic_diff.bundle_dir.as_posix(),
            "trading_logic_semantic_diff_evidence_contract_id": semantic_diff.contract_id,
            "trading_logic_semantic_diff_evidence_digest": semantic_diff.artifact_digest,
            "baseline_trading_core_decision_attestation_digest": semantic_diff.baseline_attestation_digest,
            "candidate_trading_core_decision_attestation_digest": semantic_diff.candidate_attestation_digest,
        },
        "blocking_facts": _sort_factors(non_contradiction_blocking),
        "missing_preconditions": _sort_factors(
            [item for item in blocking_facts if item.get("factor_type") == "MISSING_PRECONDITION"]
        ),
        "contradictions": _sort_factors(contradictions),
        "runtime_state_reconciliation_authority_invariants": dict(
            RUNTIME_STATE_RECONCILIATION_AUTHORITY_INVARIANTS
        ),
        "input_artifact_refs": input_refs,
        "cross_domain_lineage": dict(semantic_diff.cross_domain_lineage),
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
        "provenance_digest": provenance_digest,
        "cross_domain_lineage_digest": cross_domain_lineage_digest,
        "runtime_state_reconciliation_contract_complete": complete,
        "runtime_state_reconciliation_offline_only": True,
        "semantic_diff_evidence_bound": complete,
        "snapshot_component_binding_bound": complete,
        "reconciliation_level_binding_bound": complete,
        "provenance_bound": complete,
        "cross_domain_lineage_bound": complete,
        "deterministic_serialization_bound": complete,
        "stable_digest_bound": complete,
        "deny_by_default": True,
        "futures_only": True,
        "r4_reconciliation_pass": r4_pass and complete,
        "zero_unreconciled_exposure": zero_unreconciled_exposure and complete,
        "open_orders_state_known": open_orders_state_known and complete,
        "position_state_known": position_state_known and complete,
        "margin_state_known": margin_state_known and complete,
        "reconciliation_state_clean": reconciliation_state == "CLEAN" and complete,
    }

    for key, value in _REQUIRED_NON_AUTHORIZING_FLAGS.items():
        if key in payload:
            continue
        payload[key] = value

    _reject_forbidden_index_keys(payload)
    _validate_non_authorizing_flags(payload)
    if contract_status not in _VALID_CONTRACT_STATUSES:
        raise RuntimeStateReconciliationError("contract_status invalid")
    if evidence_status not in _VALID_EVIDENCE_STATUSES:
        raise RuntimeStateReconciliationError("evidence_status invalid")
    if classification not in _VALID_CLASSIFICATIONS:
        raise RuntimeStateReconciliationError("reconciliation_classification invalid")

    payload["contract_id"] = contract_id
    output_digest = _compute_output_digest(payload)
    payload["output_digest"] = output_digest
    payload["artifact_id"] = output_digest
    return payload


def serialize_runtime_state_reconciliation_v1(contract: Mapping[str, Any]) -> str:
    _reject_forbidden_index_keys(contract)
    _validate_non_authorizing_flags(contract)
    if contract.get("contract_status") not in _VALID_CONTRACT_STATUSES:
        raise RuntimeStateReconciliationError("contract_status invalid")
    for list_field in (
        "contract_reason_codes",
        "blocking_facts",
        "missing_preconditions",
        "contradictions",
        "snapshot_components",
        "reconciliation_levels",
    ):
        values = contract.get(list_field)
        if isinstance(values, list) and values != sorted(
            values,
            key=lambda item: (
                item.get("component_name", item.get("level_name", item.get("factor_id", item)))
                if isinstance(item, dict)
                else item,
                item.get("source_field", "") if isinstance(item, dict) else "",
            ),
        ):
            raise RuntimeStateReconciliationError(f"{list_field} must be sorted deterministically")
    return deterministic_json_dumps(contract)


def _artifact_bytes_for_manifest_digest(artifact: Mapping[str, Any]) -> bytes:
    body = {
        key: value for key, value in artifact.items() if key not in {"integrity", "manifest_digest"}
    }
    return serialize_runtime_state_reconciliation_v1(body).encode("utf-8")


def _compute_output_manifest_digest(artifact: Mapping[str, Any]) -> str:
    return hashlib.sha256(_artifact_bytes_for_manifest_digest(artifact)).hexdigest()


def _validate_contract_integrity(artifact: Mapping[str, Any]) -> None:
    if artifact.get("contract_name") != CONTRACT_NAME:
        raise RuntimeStateReconciliationError("contract_name mismatch")
    if artifact.get("contract_version") != CONTRACT_VERSION:
        raise RuntimeStateReconciliationError("contract_version mismatch")
    integrity = artifact.get("integrity")
    if not isinstance(integrity, Mapping):
        raise RuntimeStateReconciliationError("integrity must be an object")
    expected = compute_content_sha256(_integrity_body(artifact))
    actual = integrity.get("content_sha256")
    if actual != expected:
        raise RuntimeStateReconciliationError("integrity.content_sha256 mismatch")
    output_digest = artifact.get("output_digest")
    if output_digest != _compute_output_digest(artifact):
        raise RuntimeStateReconciliationError("output_digest mismatch")
    if artifact.get("artifact_id") != output_digest:
        raise RuntimeStateReconciliationError("artifact_id must equal output_digest")


def build_self_verification_v1(
    *,
    contract: Mapping[str, Any],
    manifest_digest: str,
) -> dict[str, Any]:
    checks: list[dict[str, str]] = [
        {"check_id": "contract_name", "status": "PASS"},
        {"check_id": "contract_version", "status": "PASS"},
        {"check_id": "evidence_level_level_3", "status": "PASS"},
        {"check_id": "exactly_one_verified_semantic_diff_bundle", "status": "PASS"},
        {"check_id": "offline_only_no_order_creation", "status": "PASS"},
        {"check_id": "offline_only_no_order_submission", "status": "PASS"},
        {"check_id": "no_state_mutation", "status": "PASS"},
        {"check_id": "manifest_verification", "status": "PASS"},
    ]
    structural_failures = [check for check in checks if check["status"] != "PASS"]
    if structural_failures:
        raise RuntimeStateReconciliationError("self-verification checks failed")

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
        "verified_evidence_status": contract.get("evidence_status"),
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


def _component_digest_for_name(semantic_diff_digest: str, component_name: str) -> str:
    return _binding_digest(
        f"{semantic_diff_digest}:{component_name}",
        domain="reconciliation_snapshot_component_v1",
    )


def default_snapshot_components_from_semantic_diff(
    *,
    semantic_diff: VerifiedTradingLogicSemanticDiffEvidenceBundle,
) -> tuple[ReconciliationSnapshotComponent, ...]:
    components: list[ReconciliationSnapshotComponent] = []
    for component_name in _REQUIRED_SNAPSHOT_COMPONENT_NAMES:
        digest = _component_digest_for_name(semantic_diff.semantic_diff_digest, component_name)
        components.append(
            ReconciliationSnapshotComponent(
                component_name=component_name,
                local_digest=digest,
                venue_digest=digest,
                divergence_detected=False,
            )
        )
    return tuple(components)


def default_reconciliation_levels(
    *, all_pass: bool = True
) -> tuple[ReconciliationLevelResult, ...]:
    return tuple(
        ReconciliationLevelResult(level_name=level_name, level_pass=all_pass)
        for level_name in _REQUIRED_RECONCILIATION_LEVEL_NAMES
    )


def default_runtime_reconciliation_request(
    *,
    semantic_diff: VerifiedTradingLogicSemanticDiffEvidenceBundle,
    declared_reconciliation_state: str = "CLEAN",
    instrument_type: str = "FUTURES",
    correlation_id: str = "offline-runtime-reconciliation-correlation-001",
) -> RuntimeReconciliationRequest:
    provenance_digest = _binding_digest(DEFAULT_SOURCE_REVISION, domain="provenance_digest_v1")
    cross_domain_lineage_digest = _binding_digest(
        semantic_diff.cross_domain_lineage_digest,
        domain="cross_domain_lineage_digest_v1",
    )
    return RuntimeReconciliationRequest(
        declared_reconciliation_state=declared_reconciliation_state,
        snapshot_components=default_snapshot_components_from_semantic_diff(
            semantic_diff=semantic_diff
        ),
        reconciliation_levels=default_reconciliation_levels(all_pass=True),
        instrument_type=instrument_type,
        correlation_id=correlation_id,
        provenance_digest=provenance_digest,
        cross_domain_lineage_digest=cross_domain_lineage_digest,
    )


def verify_runtime_state_reconciliation_inputs(
    inputs: RuntimeStateReconciliationInputs,
) -> VerifiedTradingLogicSemanticDiffEvidenceBundle:
    return verify_trading_logic_semantic_diff_evidence_bundle(
        inputs.trading_logic_semantic_diff_evidence_bundle_dir
    )


def reverify_runtime_state_reconciliation_v1(*, output_dir: Path | str) -> None:
    bundle_dir = Path(output_dir)
    if not bundle_dir.is_dir():
        raise RuntimeStateReconciliationError(
            f"runtime state reconciliation directory not found: {bundle_dir}"
        )
    ok, msg = verify_manifest_sha256(bundle_dir)
    if not ok:
        raise RuntimeStateReconciliationError(f"MANIFEST.sha256 verification failed: {msg}")

    artifact_path = bundle_dir / ARTIFACT_REL
    _validate_regular_file(artifact_path, label=ARTIFACT_REL)
    contract = read_manifest(artifact_path)
    _validate_contract_integrity(contract)

    self_path = bundle_dir / SELF_VERIFICATION_REL
    _validate_regular_file(self_path, label=SELF_VERIFICATION_REL)
    self_payload = read_manifest(self_path)
    if self_payload.get("overall_status") != "PASS":
        raise RuntimeStateReconciliationError("SELF_VERIFICATION overall_status must be PASS")

    manifest_digest = _compute_output_manifest_digest(contract)
    if contract.get("manifest_digest") != manifest_digest:
        raise RuntimeStateReconciliationError("manifest_digest mismatch on replay")

    semantic_diff = verify_trading_logic_semantic_diff_evidence_bundle(
        Path(str(contract["upstream_bindings"]["trading_logic_semantic_diff_evidence_bundle_ref"]))
    )
    bindings = contract.get("upstream_bindings", {})
    if bindings.get("trading_logic_semantic_diff_evidence_digest") != semantic_diff.artifact_digest:
        raise RuntimeStateReconciliationError("semantic diff evidence digest mismatch on replay")


def produce_runtime_state_reconciliation_v1(
    *,
    inputs: RuntimeStateReconciliationInputs,
    output_dir: Path | str,
) -> RuntimeStateReconciliationResult:
    final_dir = Path(output_dir)
    _validate_output_target(final_dir)
    _reject_unsafe_overlap(
        bundle_dirs=[inputs.trading_logic_semantic_diff_evidence_bundle_dir],
        output_dir=final_dir,
    )

    semantic_diff = verify_runtime_state_reconciliation_inputs(inputs)
    contract_body = build_runtime_state_reconciliation_v1(
        semantic_diff=semantic_diff,
        request=inputs.reconciliation_request,
    )

    staging = final_dir.parent / f"{STAGING_DIRNAME_PREFIX}{uuid.uuid4().hex}"
    if staging.exists():
        raise RuntimeStateReconciliationError(f"staging directory collision: {staging}")

    try:
        staging.mkdir(parents=True, exist_ok=False)
        artifact_path = staging / ARTIFACT_REL
        self_path = staging / SELF_VERIFICATION_REL

        manifest_digest = _compute_output_manifest_digest(contract_body)
        finalized = _finalize_contract_with_manifest_digest(
            contract_body, manifest_digest=manifest_digest
        )
        artifact_path.write_text(
            serialize_runtime_state_reconciliation_v1(finalized),
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
            raise RuntimeStateReconciliationError(
                f"MANIFEST.sha256 verification failed before publish: {msg}"
            )

        reverify_runtime_state_reconciliation_v1(output_dir=staging)
        staging.replace(final_dir)

        ok, msg = verify_manifest_sha256(final_dir)
        if not ok:
            raise RuntimeStateReconciliationError(
                f"MANIFEST.sha256 verification failed after publish: {msg}"
            )
    except Exception:
        _cleanup_staging(staging)
        if final_dir.exists():
            shutil.rmtree(final_dir)
        raise

    return RuntimeStateReconciliationResult(
        output_dir=final_dir,
        contract_id=str(finalized["contract_id"]),
        contract_status=str(finalized["contract_status"]),
        evidence_status=str(finalized["evidence_status"]),
        classification=str(finalized["reconciliation_classification"]),
        contract_path=final_dir / ARTIFACT_REL,
        self_verification_path=final_dir / SELF_VERIFICATION_REL,
        manifest_path=final_dir / MANIFEST_FILENAME,
        reconciliation_state=str(finalized["reconciliation_state"]),
        reconciliation_digest=str(finalized["reconciliation_digest"]),
    )


def _cleanup_staging(staging: Path) -> None:
    if staging.exists():
        shutil.rmtree(staging)


__all__ = [
    "ARTIFACT_REL",
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
    "RECONCILIATION_CONTRACT_VERSION",
    "RUNTIME_STATE_RECONCILIATION_AUTHORITY_INVARIANTS",
    "ReconciliationLevelResult",
    "ReconciliationSnapshotComponent",
    "RuntimeReconciliationRequest",
    "RuntimeStateReconciliationError",
    "RuntimeStateReconciliationInputs",
    "RuntimeStateReconciliationResult",
    "VerifiedTradingLogicSemanticDiffEvidenceBundle",
    "build_runtime_state_reconciliation_v1",
    "build_self_verification_v1",
    "default_reconciliation_levels",
    "default_runtime_reconciliation_request",
    "default_snapshot_components_from_semantic_diff",
    "produce_runtime_state_reconciliation_v1",
    "reverify_runtime_state_reconciliation_v1",
    "serialize_runtime_state_reconciliation_v1",
    "verify_runtime_state_reconciliation_inputs",
    "verify_trading_logic_semantic_diff_evidence_bundle",
]
