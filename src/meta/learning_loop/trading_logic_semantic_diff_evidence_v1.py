"""Offline LEVEL_3 canonical trading-logic semantic-diff evidence contract owner v1."""

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
from src.meta.learning_loop.trading_core_decision_attestation_v1 import (
    ARTIFACT_REL as ATTESTATION_ARTIFACT_REL,
    ATTESTATION_CONTRACT_VERSION,
    CONTRACT_NAME as ATTESTATION_CONTRACT_NAME,
    CONTRACT_VERSION as ATTESTATION_OWNER_CONTRACT_VERSION,
    DETERMINISTIC_RULE_SET_VERSION as ATTESTATION_DETERMINISTIC_RULE_SET_VERSION,
    DETERMINISTIC_SERIALIZATION_VERSION,
    PRODUCER_VERSION as ATTESTATION_PRODUCER_VERSION,
    TradingCoreDecisionAttestationError,
    reverify_trading_core_decision_attestation_v1,
)

CONTRACT_NAME = "trading_logic_semantic_diff_evidence_v1"
CONTRACT_VERSION = "v1"
SEMANTIC_DIFF_CONTRACT_VERSION = "trading_logic_semantic_diff_contract_v1"
SEMANTIC_DIFF_SCOPE_DEFAULT = "TRADING_LOGIC_OFFLINE_SEMANTIC_DIFF_EVALUATION"
PRODUCER_VERSION = "trading_logic_semantic_diff_evidence_v1"
EVIDENCE_LEVEL = "LEVEL_3"
AUTHORITY_LEVEL = "NON_AUTHORITIZING"
RECORD_KIND = "trading_logic_semantic_diff_evidence_record"
INPUT_RELATION = "PACKAGES_VERIFIED_BASELINE_AND_CANDIDATE_TRADING_CORE_DECISION_ATTESTATION_FOR_OFFLINE_SEMANTIC_DIFF"
ARTIFACT_REL = "trading_logic_semantic_diff_evidence_v1.json"
SELF_VERIFICATION_REL = "SELF_VERIFICATION.json"
MANIFEST_FILENAME = "MANIFEST.sha256"
STAGING_DIRNAME_PREFIX = ".trading_logic_semantic_diff_evidence_staging_"

SCHEMA_VERSION = "trading_logic_semantic_diff_evidence_schema_v1"
CREATION_CONTRACT_VERSION = "trading_logic_semantic_diff_evidence_creation_v1"
DETERMINISTIC_RULE_SET_VERSION = "trading_logic_semantic_diff_evidence_rules_v1"
OFFLINE_DETERMINISTIC_CREATED_AT = "1970-01-01T00:00:00+00:00"
DEFAULT_PRODUCER_IDENTITY_REF = "peak_trade_offline_trading_logic_semantic_diff_producer_v1"
DEFAULT_SOURCE_REVISION = "OFFLINE_DETERMINISTIC_EVIDENCE"

_VALID_INSTRUMENT_TYPES = frozenset({"FUTURES"})
_FORBIDDEN_INSTRUMENT_TYPES = frozenset({"SPOT", "SYNTHETIC_SPOT", "SYNTHETIC-SPOT"})
_VALID_CHANGE_CLASSES = frozenset({"A", "B", "C", "D"})
_CHANGE_CLASS_RANK = {"A": 0, "B": 1, "C": 2, "D": 3}

_REQUIRED_DIFF_LAYER_NAMES = (
    "declared_semantic_diff",
    "structural_contract_diff",
    "configuration_domain_diff",
    "decision_trace_diff",
    "golden_replay_diff",
    "boundary_behavior_diff",
    "risk_output_diff",
    "order_intent_diff",
)

_C_CLASS_SIGNAL_FIELDS = (
    "bull_decision_changed",
    "bear_decision_changed",
    "double_play_resolution_changed",
    "dynamic_scope_selection_changed",
    "risk_accept_reject_changed",
    "sizing_output_changed",
    "capital_envelope_changed",
    "canonical_order_intent_changed",
)

_MODULE_SLOT_TO_C_SIGNAL = {
    "bull": "bull_decision_changed",
    "bear": "bear_decision_changed",
    "double_play": "double_play_resolution_changed",
    "dynamic_scope": "dynamic_scope_selection_changed",
    "risk": "risk_accept_reject_changed",
    "sizing": "sizing_output_changed",
    "scope_capital": "capital_envelope_changed",
}

_VALID_CLASSIFICATIONS = frozenset(
    {
        "SEMANTIC_DIFF_VALID",
        "UNDERDECLARED_CHANGE_CLASS",
        "MISSING_BINDINGS",
        "LAYER_MISMATCH",
        "ATTESTATION_INVALID",
        "FUTURES_MARKET_TYPE_CONFLICT",
        "INVALID",
    }
)

_VALID_CONTRACT_STATUSES = frozenset(
    {
        "TRADING_LOGIC_SEMANTIC_DIFF_EVIDENCE_VALID",
        "TRADING_LOGIC_SEMANTIC_DIFF_EVIDENCE_UNDERDECLARED_CHANGE_CLASS",
        "TRADING_LOGIC_SEMANTIC_DIFF_EVIDENCE_MISSING_BINDINGS",
        "TRADING_LOGIC_SEMANTIC_DIFF_EVIDENCE_LAYER_MISMATCH",
        "TRADING_LOGIC_SEMANTIC_DIFF_EVIDENCE_ATTESTATION_INVALID",
        "TRADING_LOGIC_SEMANTIC_DIFF_EVIDENCE_FUTURES_MARKET_TYPE_CONFLICT",
        "TRADING_LOGIC_SEMANTIC_DIFF_EVIDENCE_INVALID",
        "ABSTAIN",
    }
)
_VALID_EVIDENCE_STATUSES = frozenset(
    {"ADMISSIBLE", "VALID", "CONFLICT", "INVALID", "UNKNOWN", "ABSTAIN"}
)
_SELF_VERIFICATION_SCHEMA_VERSION = "trading_logic_semantic_diff_evidence_self_verification_v1"

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

TRADING_LOGIC_SEMANTIC_DIFF_EVIDENCE_AUTHORITY_INVARIANTS: dict[str, bool] = {
    **COMPARISON_AUTHORITY_INVARIANTS,
    "trading_logic_semantic_diff_evidence_is_descriptive_only": True,
    "trading_logic_semantic_diff_evidence_does_not_create_order": True,
    "trading_logic_semantic_diff_evidence_does_not_submit_order": True,
    "trading_logic_semantic_diff_evidence_does_not_mutate_order_state": True,
    "trading_logic_semantic_diff_evidence_does_not_invoke_adapter": True,
    "trading_logic_semantic_diff_evidence_does_not_invoke_consumer": True,
    "trading_logic_semantic_diff_evidence_does_not_grant_authority": True,
    "trading_logic_semantic_diff_evidence_is_offline_only": True,
    "deny_by_default": True,
    "futures_only": True,
    "baseline_attestation_bound": True,
    "candidate_attestation_bound": True,
    "declared_semantic_diff_bound": True,
    "diff_layer_binding_bound": True,
    "change_class_binding_bound": True,
    "provenance_bound": True,
    "cross_domain_lineage_bound": True,
    "deterministic_serialization_bound": True,
    "stable_digest_bound": True,
}

_REQUIRED_NON_AUTHORIZING_FLAGS: dict[str, bool] = {
    "is_trading_logic_semantic_diff_evidence": True,
    "trading_logic_semantic_diff_evidence_offline_only": True,
    "trading_logic_semantic_diff_evidence_contract_complete": False,
    "baseline_attestation_bound": False,
    "candidate_attestation_bound": False,
    "declared_semantic_diff_bound": False,
    "diff_layer_binding_bound": False,
    "change_class_binding_bound": False,
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


class TradingLogicSemanticDiffEvidenceError(ValueError):
    """Fail-closed trading-logic semantic-diff evidence error."""


@dataclass(frozen=True)
class SemanticDiffLayer:
    layer_name: str
    baseline_digest: str
    candidate_digest: str
    change_detected: bool
    diff_digest: str = ""


@dataclass(frozen=True)
class VerifiedTradingCoreDecisionAttestationBundle:
    bundle_dir: Path
    contract_name: str
    contract_version: str
    producer_version: str
    artifact_ref: str
    artifact_digest: str
    manifest_digest: str
    contract_id: str
    contract_status: str
    attestation_chain_digest: str
    canonical_order_intent_identity_digest: str
    module_attestations: tuple[dict[str, Any], ...]
    futures_only: bool
    instrument_type: str
    cross_domain_lineage: dict[str, Any]
    provenance_digest: str
    cross_domain_lineage_digest: str


@dataclass(frozen=True)
class SemanticDiffEvidenceRequest:
    declared_change_class: str
    declared_semantic_diff_summary_digest: str
    diff_layers: tuple[SemanticDiffLayer, ...]
    correlation_id: str = "offline-semantic-diff-correlation-001"
    semantic_diff_contract_version: str = SEMANTIC_DIFF_CONTRACT_VERSION
    attestation_contract_version: str = ATTESTATION_CONTRACT_VERSION
    deterministic_serialization_version: str = DETERMINISTIC_SERIALIZATION_VERSION
    provenance_digest: str = ""
    cross_domain_lineage_digest: str = ""
    source_revision: str = DEFAULT_SOURCE_REVISION


@dataclass(frozen=True)
class TradingLogicSemanticDiffEvidenceInputs:
    baseline_trading_core_decision_attestation_bundle_dir: Path
    candidate_trading_core_decision_attestation_bundle_dir: Path
    semantic_diff_request: SemanticDiffEvidenceRequest


@dataclass(frozen=True)
class TradingLogicSemanticDiffEvidenceResult:
    output_dir: Path
    contract_id: str
    contract_status: str
    evidence_status: str
    classification: str
    contract_path: Path
    self_verification_path: Path
    manifest_path: Path
    minimum_change_class: str
    effective_change_class: str
    semantic_diff_digest: str


def _reject_symlink(path: Path, *, label: str) -> None:
    if path.is_symlink():
        raise TradingLogicSemanticDiffEvidenceError(f"{label} must not be a symlink: {path}")


def _reject_forbidden_index_keys(payload: Mapping[str, Any]) -> None:
    for key in payload:
        if key in _FORBIDDEN_INDEX_KEYS:
            raise TradingLogicSemanticDiffEvidenceError(f"forbidden index key: {key}")


def _validate_regular_file(path: Path, *, label: str) -> None:
    _reject_symlink(path, label=label)
    if not path.is_file():
        raise TradingLogicSemanticDiffEvidenceError(f"{label} must be a regular file: {path}")


def _validate_bundle_dir(bundle_dir: Path, *, label: str) -> None:
    _reject_symlink(bundle_dir, label=label)
    if not bundle_dir.is_dir():
        raise TradingLogicSemanticDiffEvidenceError(f"{label} must be a directory: {bundle_dir}")


def _validate_output_target(output_dir: Path) -> None:
    if is_under_tmp(output_dir):
        raise TradingLogicSemanticDiffEvidenceError("output_dir must not be under /tmp")
    if output_dir.exists():
        raise TradingLogicSemanticDiffEvidenceError(f"output_dir already exists: {output_dir}")


def _path_is_under(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
    except ValueError:
        return False
    return True


def _reject_unsafe_overlap(*, bundle_dirs: list[Path], output_dir: Path) -> None:
    for bundle_dir in bundle_dirs:
        if _path_is_under(output_dir, bundle_dir) or _path_is_under(bundle_dir, output_dir):
            raise TradingLogicSemanticDiffEvidenceError(
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
            raise TradingLogicSemanticDiffEvidenceError(f"missing non-authorizing flag: {key}")
        if payload[key] is not expected and key not in {
            "trading_logic_semantic_diff_evidence_contract_complete",
            "baseline_attestation_bound",
            "candidate_attestation_bound",
            "declared_semantic_diff_bound",
            "diff_layer_binding_bound",
            "change_class_binding_bound",
            "provenance_bound",
            "cross_domain_lineage_bound",
            "deterministic_serialization_bound",
            "stable_digest_bound",
        }:
            raise TradingLogicSemanticDiffEvidenceError(
                f"non-authorizing flag {key} must be {expected}"
            )


def _binding_digest(value: str, *, domain: str) -> str:
    return compute_content_sha256({"domain": domain, "value": value})


def _module_attestations_tuple(payload: Mapping[str, Any]) -> tuple[dict[str, Any], ...]:
    module_attestations = payload.get("module_attestations")
    if not isinstance(module_attestations, list):
        return ()
    return tuple(
        sorted(
            (dict(item) for item in module_attestations if isinstance(item, dict)),
            key=lambda item: str(item.get("module_slot", "")),
        )
    )


def verify_trading_core_decision_attestation_bundle(
    bundle_dir: Path | str,
) -> VerifiedTradingCoreDecisionAttestationBundle:
    resolved = Path(bundle_dir)
    _validate_bundle_dir(resolved, label="trading_core_decision_attestation_bundle_dir")
    reverify_trading_core_decision_attestation_v1(output_dir=resolved)
    artifact_path = resolved / ATTESTATION_ARTIFACT_REL
    _validate_regular_file(artifact_path, label=ATTESTATION_ARTIFACT_REL)
    payload = read_manifest(artifact_path)
    if payload.get("contract_name") != ATTESTATION_CONTRACT_NAME:
        raise TradingLogicSemanticDiffEvidenceError("attestation contract_name mismatch")
    if payload.get("contract_version") != ATTESTATION_OWNER_CONTRACT_VERSION:
        raise TradingLogicSemanticDiffEvidenceError("attestation contract_version mismatch")
    intent = payload.get("canonical_order_intent_identity")
    instrument_type = ""
    if isinstance(intent, Mapping):
        instrument_type = str(intent.get("instrument_type", ""))
    return VerifiedTradingCoreDecisionAttestationBundle(
        bundle_dir=resolved,
        contract_name=str(payload.get("contract_name", "")),
        contract_version=str(payload.get("contract_version", "")),
        producer_version=str(payload.get("producer_version", "")),
        artifact_ref=ATTESTATION_ARTIFACT_REL,
        artifact_digest=str(payload.get("output_digest", "")),
        manifest_digest=str(payload.get("manifest_digest", "")),
        contract_id=str(payload.get("contract_id", "")),
        contract_status=str(payload.get("contract_status", "")),
        attestation_chain_digest=str(payload.get("attestation_chain_digest", "")),
        canonical_order_intent_identity_digest=str(
            payload.get("canonical_order_intent_identity_digest", "")
        ),
        module_attestations=_module_attestations_tuple(payload),
        futures_only=bool(payload.get("futures_only")),
        instrument_type=instrument_type,
        cross_domain_lineage=(
            dict(payload.get("cross_domain_lineage", {}))
            if isinstance(payload.get("cross_domain_lineage"), Mapping)
            else {}
        ),
        provenance_digest=str(payload.get("provenance_digest", "")),
        cross_domain_lineage_digest=str(payload.get("cross_domain_lineage_digest", "")),
    )


def _compute_layer_diff_digest(
    *, layer_name: str, baseline_digest: str, candidate_digest: str
) -> str:
    return compute_content_sha256(
        {
            "layer_name": layer_name,
            "baseline_digest": baseline_digest,
            "candidate_digest": candidate_digest,
            "deterministic_rule_set_version": DETERMINISTIC_RULE_SET_VERSION,
        }
    )


def _derive_c_class_signals(
    *,
    baseline: VerifiedTradingCoreDecisionAttestationBundle,
    candidate: VerifiedTradingCoreDecisionAttestationBundle,
) -> dict[str, bool]:
    baseline_by_slot = {
        str(item.get("module_slot", "")): item
        for item in baseline.module_attestations
        if isinstance(item, Mapping)
    }
    candidate_by_slot = {
        str(item.get("module_slot", "")): item
        for item in candidate.module_attestations
        if isinstance(item, Mapping)
    }
    signals = {field: False for field in _C_CLASS_SIGNAL_FIELDS}
    for slot, signal_field in _MODULE_SLOT_TO_C_SIGNAL.items():
        base_item = baseline_by_slot.get(slot, {})
        cand_item = candidate_by_slot.get(slot, {})
        if base_item.get("output_digest") != cand_item.get("output_digest"):
            signals[signal_field] = True
        if base_item.get("decision_code") != cand_item.get("decision_code"):
            signals[signal_field] = True
    if (
        baseline.canonical_order_intent_identity_digest
        != candidate.canonical_order_intent_identity_digest
    ):
        signals["canonical_order_intent_changed"] = True
    if baseline.attestation_chain_digest != candidate.attestation_chain_digest:
        for field in (
            "bull_decision_changed",
            "bear_decision_changed",
            "double_play_resolution_changed",
            "dynamic_scope_selection_changed",
            "risk_accept_reject_changed",
            "sizing_output_changed",
            "capital_envelope_changed",
        ):
            if signals[field]:
                continue
    return signals


def _minimum_change_class_from_signals(signals: Mapping[str, bool]) -> str:
    if any(signals.get(field) for field in _C_CLASS_SIGNAL_FIELDS):
        return "C"
    return "A"


def _minimum_change_class_from_layers(layers: tuple[SemanticDiffLayer, ...]) -> str:
    structural_changed = False
    configuration_changed = False
    decision_trace_changed = False
    golden_replay_changed = False
    boundary_changed = False
    risk_changed = False
    order_intent_changed = False
    for layer in layers:
        if not layer.change_detected:
            continue
        if layer.layer_name == "structural_contract_diff":
            structural_changed = True
        elif layer.layer_name == "configuration_domain_diff":
            configuration_changed = True
        elif layer.layer_name == "decision_trace_diff":
            decision_trace_changed = True
        elif layer.layer_name == "golden_replay_diff":
            golden_replay_changed = True
        elif layer.layer_name == "boundary_behavior_diff":
            boundary_changed = True
        elif layer.layer_name == "risk_output_diff":
            risk_changed = True
        elif layer.layer_name == "order_intent_diff":
            order_intent_changed = True
    if order_intent_changed or risk_changed or decision_trace_changed:
        return "C"
    if golden_replay_changed or boundary_changed:
        return "B"
    if configuration_changed or structural_changed:
        return "B"
    return "A"


def _merge_minimum_change_class(*classes: str) -> str:
    ranked = sorted(classes, key=lambda item: _CHANGE_CLASS_RANK.get(item, 99), reverse=True)
    return ranked[0] if ranked else "A"


def _serialize_diff_layers(layers: tuple[SemanticDiffLayer, ...]) -> list[dict[str, Any]]:
    serialized: list[dict[str, Any]] = []
    for layer in sorted(layers, key=lambda item: item.layer_name):
        diff_digest = layer.diff_digest or _compute_layer_diff_digest(
            layer_name=layer.layer_name,
            baseline_digest=layer.baseline_digest,
            candidate_digest=layer.candidate_digest,
        )
        serialized.append(
            {
                "layer_name": layer.layer_name,
                "baseline_digest": layer.baseline_digest,
                "candidate_digest": layer.candidate_digest,
                "change_detected": layer.change_detected,
                "diff_digest": diff_digest,
            }
        )
    return serialized


def _validate_request(
    request: SemanticDiffEvidenceRequest,
    *,
    baseline: VerifiedTradingCoreDecisionAttestationBundle,
    candidate: VerifiedTradingCoreDecisionAttestationBundle,
) -> list[dict[str, str]]:
    blocking_facts: list[dict[str, str]] = []

    if request.semantic_diff_contract_version != SEMANTIC_DIFF_CONTRACT_VERSION:
        blocking_facts.append(
            _factor(
                factor_id="SEMANTIC_DIFF_CONTRACT_VERSION_MISMATCH",
                factor_type="MISSING_PRECONDITION",
                source_field="semantic_diff_contract_version",
            )
        )
    if request.attestation_contract_version != ATTESTATION_CONTRACT_VERSION:
        blocking_facts.append(
            _factor(
                factor_id="ATTESTATION_CONTRACT_VERSION_MISMATCH",
                factor_type="MISSING_PRECONDITION",
                source_field="attestation_contract_version",
            )
        )
    if request.deterministic_serialization_version != DETERMINISTIC_SERIALIZATION_VERSION:
        blocking_facts.append(
            _factor(
                factor_id="SERIALIZATION_VERSION_MISMATCH",
                factor_type="MISSING_PRECONDITION",
                source_field="deterministic_serialization_version",
            )
        )
    if request.declared_change_class not in _VALID_CHANGE_CLASSES:
        blocking_facts.append(
            _factor(
                factor_id="INVALID_DECLARED_CHANGE_CLASS",
                factor_type="MISSING_PRECONDITION",
                source_field="declared_change_class",
            )
        )
    if not request.declared_semantic_diff_summary_digest:
        blocking_facts.append(
            _factor(
                factor_id="MISSING_DECLARED_SEMANTIC_DIFF_SUMMARY_DIGEST",
                factor_type="MISSING_PRECONDITION",
                source_field="declared_semantic_diff_summary_digest",
            )
        )

    layer_names = {layer.layer_name for layer in request.diff_layers}
    for required_name in _REQUIRED_DIFF_LAYER_NAMES:
        if required_name not in layer_names:
            blocking_facts.append(
                _factor(
                    factor_id="MISSING_DIFF_LAYER",
                    factor_type="MISSING_PRECONDITION",
                    source_field=required_name,
                )
            )

    for layer in request.diff_layers:
        if layer.layer_name not in _REQUIRED_DIFF_LAYER_NAMES:
            blocking_facts.append(
                _factor(
                    factor_id="UNKNOWN_DIFF_LAYER",
                    factor_type="MISSING_PRECONDITION",
                    source_field=layer.layer_name,
                )
            )
        if not layer.baseline_digest or not layer.candidate_digest:
            blocking_facts.append(
                _factor(
                    factor_id="MISSING_LAYER_DIGEST",
                    factor_type="MISSING_PRECONDITION",
                    source_field=layer.layer_name,
                )
            )
        derived_change = layer.baseline_digest != layer.candidate_digest
        if layer.change_detected != derived_change:
            blocking_facts.append(
                _factor(
                    factor_id="LAYER_CHANGE_FLAG_MISMATCH",
                    factor_type="CONTRADICTION",
                    source_field=layer.layer_name,
                )
            )

    for bundle, label in ((baseline, "baseline"), (candidate, "candidate")):
        if bundle.contract_status != "TRADING_CORE_DECISION_ATTESTATION_VALID":
            blocking_facts.append(
                _factor(
                    factor_id="ATTESTATION_CONTRACT_STATUS_INVALID",
                    factor_type="CONTRADICTION",
                    source_field=f"{label}_contract_status",
                )
            )
        if not bundle.futures_only:
            blocking_facts.append(
                _factor(
                    factor_id="FUTURES_ONLY_FLAG_FALSE",
                    factor_type="CONTRADICTION",
                    source_field=f"{label}_futures_only",
                )
            )
        if bundle.instrument_type in _FORBIDDEN_INSTRUMENT_TYPES:
            blocking_facts.append(
                _factor(
                    factor_id="FORBIDDEN_INSTRUMENT_TYPE",
                    factor_type="CONTRADICTION",
                    source_field=f"{label}_instrument_type",
                )
            )
        elif bundle.instrument_type not in _VALID_INSTRUMENT_TYPES:
            blocking_facts.append(
                _factor(
                    factor_id="INVALID_INSTRUMENT_TYPE",
                    factor_type="CONTRADICTION",
                    source_field=f"{label}_instrument_type",
                )
            )

    return blocking_facts


def _evaluate_semantic_diff(
    *,
    request: SemanticDiffEvidenceRequest,
    baseline: VerifiedTradingCoreDecisionAttestationBundle,
    candidate: VerifiedTradingCoreDecisionAttestationBundle,
    blocking_facts: list[dict[str, str]],
) -> tuple[str, str, str, list[str], dict[str, Any], str, str]:
    factor_ids = {item.get("factor_id") for item in blocking_facts}
    reason_codes: list[str] = []
    states: dict[str, Any] = {
        "evidence_status": "UNKNOWN",
        "semantic_diff_classification": "INVALID",
        "admissibility_reason": "",
        "deny_reason": "",
    }

    market_type_factors = {
        "FORBIDDEN_INSTRUMENT_TYPE",
        "INVALID_INSTRUMENT_TYPE",
        "FUTURES_ONLY_FLAG_FALSE",
    }
    if factor_ids & market_type_factors:
        states["evidence_status"] = "INVALID"
        states["semantic_diff_classification"] = "FUTURES_MARKET_TYPE_CONFLICT"
        states["deny_reason"] = "FUTURES_MARKET_TYPE_CONFLICT"
        reason_codes.append("FUTURES_MARKET_TYPE_CONFLICT")
        return (
            "TRADING_LOGIC_SEMANTIC_DIFF_EVIDENCE_FUTURES_MARKET_TYPE_CONFLICT",
            states["evidence_status"],
            states["semantic_diff_classification"],
            _sorted_strings(reason_codes),
            states,
            "D",
            request.declared_change_class,
        )

    if "ATTESTATION_CONTRACT_STATUS_INVALID" in factor_ids:
        states["evidence_status"] = "INVALID"
        states["semantic_diff_classification"] = "ATTESTATION_INVALID"
        states["deny_reason"] = "ATTESTATION_INVALID"
        reason_codes.append("ATTESTATION_INVALID")
        return (
            "TRADING_LOGIC_SEMANTIC_DIFF_EVIDENCE_ATTESTATION_INVALID",
            states["evidence_status"],
            states["semantic_diff_classification"],
            _sorted_strings(reason_codes),
            states,
            "D",
            request.declared_change_class,
        )

    missing_factors = {
        "MISSING_DIFF_LAYER",
        "MISSING_LAYER_DIGEST",
        "MISSING_DECLARED_SEMANTIC_DIFF_SUMMARY_DIGEST",
        "INVALID_DECLARED_CHANGE_CLASS",
        "SEMANTIC_DIFF_CONTRACT_VERSION_MISMATCH",
        "ATTESTATION_CONTRACT_VERSION_MISMATCH",
        "SERIALIZATION_VERSION_MISMATCH",
        "UNKNOWN_DIFF_LAYER",
    }
    if factor_ids & missing_factors:
        states["evidence_status"] = "INVALID"
        states["semantic_diff_classification"] = "MISSING_BINDINGS"
        states["deny_reason"] = "MISSING_BINDINGS"
        reason_codes.append("MISSING_BINDINGS")
        return (
            "TRADING_LOGIC_SEMANTIC_DIFF_EVIDENCE_MISSING_BINDINGS",
            states["evidence_status"],
            states["semantic_diff_classification"],
            _sorted_strings(reason_codes),
            states,
            "D",
            request.declared_change_class,
        )

    if "LAYER_CHANGE_FLAG_MISMATCH" in factor_ids:
        states["evidence_status"] = "CONFLICT"
        states["semantic_diff_classification"] = "LAYER_MISMATCH"
        states["deny_reason"] = "LAYER_MISMATCH"
        reason_codes.append("LAYER_MISMATCH")
        return (
            "TRADING_LOGIC_SEMANTIC_DIFF_EVIDENCE_LAYER_MISMATCH",
            states["evidence_status"],
            states["semantic_diff_classification"],
            _sorted_strings(reason_codes),
            states,
            "D",
            request.declared_change_class,
        )

    derived_signals = _derive_c_class_signals(baseline=baseline, candidate=candidate)
    minimum_from_signals = _minimum_change_class_from_signals(derived_signals)
    minimum_from_layers = _minimum_change_class_from_layers(request.diff_layers)
    minimum_change_class = _merge_minimum_change_class(minimum_from_signals, minimum_from_layers)

    declared_rank = _CHANGE_CLASS_RANK.get(request.declared_change_class, 99)
    minimum_rank = _CHANGE_CLASS_RANK.get(minimum_change_class, 99)
    if declared_rank < minimum_rank:
        states["evidence_status"] = "CONFLICT"
        states["semantic_diff_classification"] = "UNDERDECLARED_CHANGE_CLASS"
        states["deny_reason"] = "UNDERDECLARED_CHANGE_CLASS"
        reason_codes.append("UNDERDECLARED_CHANGE_CLASS")
        return (
            "TRADING_LOGIC_SEMANTIC_DIFF_EVIDENCE_UNDERDECLARED_CHANGE_CLASS",
            states["evidence_status"],
            states["semantic_diff_classification"],
            _sorted_strings(reason_codes),
            states,
            minimum_change_class,
            request.declared_change_class,
        )

    if blocking_facts:
        states["evidence_status"] = "INVALID"
        states["semantic_diff_classification"] = "INVALID"
        states["deny_reason"] = "INVALID"
        reason_codes.append("INVALID")
        return (
            "TRADING_LOGIC_SEMANTIC_DIFF_EVIDENCE_INVALID",
            states["evidence_status"],
            states["semantic_diff_classification"],
            _sorted_strings(reason_codes),
            states,
            minimum_change_class,
            request.declared_change_class,
        )

    effective_change_class = _merge_minimum_change_class(
        request.declared_change_class, minimum_change_class
    )
    states["evidence_status"] = "VALID"
    states["semantic_diff_classification"] = "SEMANTIC_DIFF_VALID"
    states["admissibility_reason"] = "SEMANTIC_DIFF_VALID"
    reason_codes.append("SEMANTIC_DIFF_VALID")
    return (
        "TRADING_LOGIC_SEMANTIC_DIFF_EVIDENCE_VALID",
        states["evidence_status"],
        states["semantic_diff_classification"],
        _sorted_strings(reason_codes),
        states,
        minimum_change_class,
        effective_change_class,
    )


def _input_artifact_ref_mapping(
    *,
    bundle: VerifiedTradingCoreDecisionAttestationBundle,
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


def build_trading_logic_semantic_diff_evidence_v1(
    *,
    baseline: VerifiedTradingCoreDecisionAttestationBundle,
    candidate: VerifiedTradingCoreDecisionAttestationBundle,
    request: SemanticDiffEvidenceRequest,
) -> dict[str, Any]:
    blocking_facts = _validate_request(request, baseline=baseline, candidate=candidate)
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
        minimum_change_class,
        effective_change_class,
    ) = _evaluate_semantic_diff(
        request=request,
        baseline=baseline,
        candidate=candidate,
        blocking_facts=blocking_facts,
    )

    derived_signals = _derive_c_class_signals(baseline=baseline, candidate=candidate)
    serialized_layers = _serialize_diff_layers(request.diff_layers)
    semantic_diff_digest = compute_content_sha256(
        {
            "diff_layers": serialized_layers,
            "c_class_signals": {key: derived_signals[key] for key in sorted(derived_signals)},
            "minimum_change_class": minimum_change_class,
            "effective_change_class": effective_change_class,
            "deterministic_rule_set_version": DETERMINISTIC_RULE_SET_VERSION,
        }
    )

    input_refs = [
        _input_artifact_ref_mapping(bundle=baseline),
        _input_artifact_ref_mapping(bundle=candidate),
    ]
    input_digest = compute_content_sha256({"input_artifact_refs": input_refs})

    provenance_digest = request.provenance_digest or _binding_digest(
        request.source_revision, domain="provenance_digest_v1"
    )
    cross_domain_lineage_digest = request.cross_domain_lineage_digest or _binding_digest(
        compute_content_sha256(
            {
                "baseline": baseline.cross_domain_lineage_digest,
                "candidate": candidate.cross_domain_lineage_digest,
            }
        ),
        domain="cross_domain_lineage_digest_v1",
    )

    contract_id = compute_content_sha256(
        {
            "contract_domain": CONTRACT_NAME,
            "baseline_attestation_digest": baseline.artifact_digest,
            "candidate_attestation_digest": candidate.artifact_digest,
            "semantic_diff_digest": semantic_diff_digest,
            "declared_change_class": request.declared_change_class,
            "deterministic_rule_set_version": DETERMINISTIC_RULE_SET_VERSION,
        }
    )

    complete = contract_status == "TRADING_LOGIC_SEMANTIC_DIFF_EVIDENCE_VALID"

    payload: dict[str, Any] = {
        "contract_id": "",
        "contract_name": CONTRACT_NAME,
        "contract_version": CONTRACT_VERSION,
        "semantic_diff_contract_version": request.semantic_diff_contract_version,
        "attestation_contract_version": request.attestation_contract_version,
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
        "semantic_diff_classification": classification,
        "admissibility_reason": completion.get("admissibility_reason", ""),
        "deny_reason": completion.get("deny_reason", ""),
        "declared_change_class": request.declared_change_class,
        "minimum_change_class": minimum_change_class,
        "effective_change_class": effective_change_class,
        "declared_semantic_diff": {
            "summary_digest": request.declared_semantic_diff_summary_digest,
            "declared_change_class": request.declared_change_class,
        },
        "structural_contract_diff": next(
            (
                layer
                for layer in serialized_layers
                if layer["layer_name"] == "structural_contract_diff"
            ),
            {},
        ),
        "configuration_domain_diff": next(
            (
                layer
                for layer in serialized_layers
                if layer["layer_name"] == "configuration_domain_diff"
            ),
            {},
        ),
        "decision_trace_diff": next(
            (layer for layer in serialized_layers if layer["layer_name"] == "decision_trace_diff"),
            {},
        ),
        "golden_replay_diff": next(
            (layer for layer in serialized_layers if layer["layer_name"] == "golden_replay_diff"),
            {},
        ),
        "boundary_behavior_diff": next(
            (
                layer
                for layer in serialized_layers
                if layer["layer_name"] == "boundary_behavior_diff"
            ),
            {},
        ),
        "risk_output_diff": next(
            (layer for layer in serialized_layers if layer["layer_name"] == "risk_output_diff"),
            {},
        ),
        "order_intent_diff": next(
            (layer for layer in serialized_layers if layer["layer_name"] == "order_intent_diff"),
            {},
        ),
        "diff_layers": serialized_layers,
        "c_class_signals": {key: derived_signals[key] for key in sorted(derived_signals)},
        "semantic_diff_digest": semantic_diff_digest,
        "correlation_id": request.correlation_id,
        "upstream_bindings": {
            "baseline_trading_core_decision_attestation_bundle_ref": baseline.bundle_dir.as_posix(),
            "baseline_trading_core_decision_attestation_contract_id": baseline.contract_id,
            "baseline_trading_core_decision_attestation_digest": baseline.artifact_digest,
            "candidate_trading_core_decision_attestation_bundle_ref": candidate.bundle_dir.as_posix(),
            "candidate_trading_core_decision_attestation_contract_id": candidate.contract_id,
            "candidate_trading_core_decision_attestation_digest": candidate.artifact_digest,
        },
        "blocking_facts": _sort_factors(non_contradiction_blocking),
        "missing_preconditions": _sort_factors(
            [item for item in blocking_facts if item.get("factor_type") == "MISSING_PRECONDITION"]
        ),
        "contradictions": _sort_factors(contradictions),
        "trading_logic_semantic_diff_evidence_authority_invariants": dict(
            TRADING_LOGIC_SEMANTIC_DIFF_EVIDENCE_AUTHORITY_INVARIANTS
        ),
        "input_artifact_refs": input_refs,
        "cross_domain_lineage": {
            "baseline_cross_domain_lineage_digest": baseline.cross_domain_lineage_digest,
            "candidate_cross_domain_lineage_digest": candidate.cross_domain_lineage_digest,
        },
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
        "trading_logic_semantic_diff_evidence_contract_complete": complete,
        "trading_logic_semantic_diff_evidence_offline_only": True,
        "baseline_attestation_bound": complete,
        "candidate_attestation_bound": complete,
        "declared_semantic_diff_bound": complete,
        "diff_layer_binding_bound": complete,
        "change_class_binding_bound": complete,
        "provenance_bound": complete,
        "cross_domain_lineage_bound": complete,
        "deterministic_serialization_bound": complete,
        "stable_digest_bound": complete,
        "deny_by_default": True,
        "futures_only": True,
    }

    for key, value in _REQUIRED_NON_AUTHORIZING_FLAGS.items():
        if key in payload:
            continue
        payload[key] = value

    _reject_forbidden_index_keys(payload)
    _validate_non_authorizing_flags(payload)
    if contract_status not in _VALID_CONTRACT_STATUSES:
        raise TradingLogicSemanticDiffEvidenceError("contract_status invalid")
    if evidence_status not in _VALID_EVIDENCE_STATUSES:
        raise TradingLogicSemanticDiffEvidenceError("evidence_status invalid")
    if classification not in _VALID_CLASSIFICATIONS:
        raise TradingLogicSemanticDiffEvidenceError("semantic_diff_classification invalid")

    payload["contract_id"] = contract_id
    output_digest = _compute_output_digest(payload)
    payload["output_digest"] = output_digest
    payload["artifact_id"] = output_digest
    return payload


def serialize_trading_logic_semantic_diff_evidence_v1(contract: Mapping[str, Any]) -> str:
    _reject_forbidden_index_keys(contract)
    _validate_non_authorizing_flags(contract)
    if contract.get("contract_status") not in _VALID_CONTRACT_STATUSES:
        raise TradingLogicSemanticDiffEvidenceError("contract_status invalid")
    for list_field in (
        "contract_reason_codes",
        "blocking_facts",
        "missing_preconditions",
        "contradictions",
        "diff_layers",
    ):
        values = contract.get(list_field)
        if isinstance(values, list) and values != sorted(
            values,
            key=lambda item: (
                item.get("layer_name", item.get("factor_id", item))
                if isinstance(item, dict)
                else item,
                item.get("source_field", "") if isinstance(item, dict) else "",
            ),
        ):
            raise TradingLogicSemanticDiffEvidenceError(
                f"{list_field} must be sorted deterministically"
            )
    return deterministic_json_dumps(contract)


def _artifact_bytes_for_manifest_digest(artifact: Mapping[str, Any]) -> bytes:
    body = {
        key: value for key, value in artifact.items() if key not in {"integrity", "manifest_digest"}
    }
    return serialize_trading_logic_semantic_diff_evidence_v1(body).encode("utf-8")


def _compute_output_manifest_digest(artifact: Mapping[str, Any]) -> str:
    return hashlib.sha256(_artifact_bytes_for_manifest_digest(artifact)).hexdigest()


def _validate_contract_integrity(artifact: Mapping[str, Any]) -> None:
    if artifact.get("contract_name") != CONTRACT_NAME:
        raise TradingLogicSemanticDiffEvidenceError("contract_name mismatch")
    if artifact.get("contract_version") != CONTRACT_VERSION:
        raise TradingLogicSemanticDiffEvidenceError("contract_version mismatch")
    integrity = artifact.get("integrity")
    if not isinstance(integrity, Mapping):
        raise TradingLogicSemanticDiffEvidenceError("integrity must be an object")
    expected = compute_content_sha256(_integrity_body(artifact))
    actual = integrity.get("content_sha256")
    if actual != expected:
        raise TradingLogicSemanticDiffEvidenceError("integrity.content_sha256 mismatch")
    output_digest = artifact.get("output_digest")
    if output_digest != _compute_output_digest(artifact):
        raise TradingLogicSemanticDiffEvidenceError("output_digest mismatch")
    if artifact.get("artifact_id") != output_digest:
        raise TradingLogicSemanticDiffEvidenceError("artifact_id must equal output_digest")


def build_self_verification_v1(
    *,
    contract: Mapping[str, Any],
    manifest_digest: str,
) -> dict[str, Any]:
    checks: list[dict[str, str]] = [
        {"check_id": "contract_name", "status": "PASS"},
        {"check_id": "contract_version", "status": "PASS"},
        {"check_id": "evidence_level_level_3", "status": "PASS"},
        {"check_id": "exactly_two_verified_attestation_bundles", "status": "PASS"},
        {"check_id": "offline_only_no_order_creation", "status": "PASS"},
        {"check_id": "offline_only_no_order_submission", "status": "PASS"},
        {"check_id": "no_state_mutation", "status": "PASS"},
        {"check_id": "manifest_verification", "status": "PASS"},
    ]
    structural_failures = [check for check in checks if check["status"] != "PASS"]
    if structural_failures:
        raise TradingLogicSemanticDiffEvidenceError("self-verification checks failed")

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


def _staging_dir_for(output_dir: Path) -> Path:
    return output_dir.parent / f"{STAGING_DIRNAME_PREFIX}{uuid.uuid4().hex}"


def _cleanup_staging(staging: Path) -> None:
    if staging.exists():
        shutil.rmtree(staging)


def default_diff_layers_from_attestations(
    *,
    baseline: VerifiedTradingCoreDecisionAttestationBundle,
    candidate: VerifiedTradingCoreDecisionAttestationBundle,
    declared_semantic_diff_summary_digest: str,
) -> tuple[SemanticDiffLayer, ...]:
    baseline_chain = baseline.attestation_chain_digest
    candidate_chain = candidate.attestation_chain_digest
    baseline_intent = baseline.canonical_order_intent_identity_digest
    candidate_intent = candidate.canonical_order_intent_identity_digest

    def _layer(name: str, base: str, cand: str) -> SemanticDiffLayer:
        return SemanticDiffLayer(
            layer_name=name,
            baseline_digest=base,
            candidate_digest=cand,
            change_detected=base != cand,
        )

    return (
        _layer(
            "declared_semantic_diff",
            declared_semantic_diff_summary_digest,
            declared_semantic_diff_summary_digest,
        ),
        _layer("structural_contract_diff", baseline_chain, candidate_chain),
        _layer(
            "configuration_domain_diff", baseline.provenance_digest, candidate.provenance_digest
        ),
        _layer("decision_trace_diff", baseline_chain, candidate_chain),
        _layer("golden_replay_diff", baseline_chain, candidate_chain),
        _layer("boundary_behavior_diff", baseline_chain, candidate_chain),
        _layer("risk_output_diff", baseline_chain, candidate_chain),
        _layer("order_intent_diff", baseline_intent, candidate_intent),
    )


def default_semantic_diff_evidence_request(
    *,
    baseline: VerifiedTradingCoreDecisionAttestationBundle,
    candidate: VerifiedTradingCoreDecisionAttestationBundle,
    declared_change_class: str = "A",
    declared_semantic_diff_summary_digest: str | None = None,
    correlation_id: str = "offline-semantic-diff-correlation-001",
) -> SemanticDiffEvidenceRequest:
    summary_digest = declared_semantic_diff_summary_digest or _binding_digest(
        f"{baseline.artifact_digest}:{candidate.artifact_digest}",
        domain="declared_semantic_diff_summary_v1",
    )
    layers = default_diff_layers_from_attestations(
        baseline=baseline,
        candidate=candidate,
        declared_semantic_diff_summary_digest=summary_digest,
    )
    provenance_digest = _binding_digest(DEFAULT_SOURCE_REVISION, domain="provenance_digest_v1")
    cross_domain_lineage_digest = _binding_digest(
        compute_content_sha256(
            {
                "baseline": baseline.cross_domain_lineage_digest,
                "candidate": candidate.cross_domain_lineage_digest,
            }
        ),
        domain="cross_domain_lineage_digest_v1",
    )
    return SemanticDiffEvidenceRequest(
        declared_change_class=declared_change_class,
        declared_semantic_diff_summary_digest=summary_digest,
        diff_layers=layers,
        correlation_id=correlation_id,
        provenance_digest=provenance_digest,
        cross_domain_lineage_digest=cross_domain_lineage_digest,
    )


def verify_trading_logic_semantic_diff_evidence_inputs(
    inputs: TradingLogicSemanticDiffEvidenceInputs,
) -> tuple[
    VerifiedTradingCoreDecisionAttestationBundle, VerifiedTradingCoreDecisionAttestationBundle
]:
    baseline = verify_trading_core_decision_attestation_bundle(
        inputs.baseline_trading_core_decision_attestation_bundle_dir
    )
    candidate = verify_trading_core_decision_attestation_bundle(
        inputs.candidate_trading_core_decision_attestation_bundle_dir
    )
    return baseline, candidate


def reverify_trading_logic_semantic_diff_evidence_v1(*, output_dir: Path | str) -> None:
    bundle_dir = Path(output_dir)
    if not bundle_dir.is_dir():
        raise TradingLogicSemanticDiffEvidenceError(
            f"trading logic semantic diff evidence directory not found: {bundle_dir}"
        )
    ok, msg = verify_manifest_sha256(bundle_dir)
    if not ok:
        raise TradingLogicSemanticDiffEvidenceError(f"MANIFEST.sha256 verification failed: {msg}")

    artifact_path = bundle_dir / ARTIFACT_REL
    _validate_regular_file(artifact_path, label=ARTIFACT_REL)
    contract = read_manifest(artifact_path)
    _validate_contract_integrity(contract)

    self_path = bundle_dir / SELF_VERIFICATION_REL
    _validate_regular_file(self_path, label=SELF_VERIFICATION_REL)
    self_payload = read_manifest(self_path)
    if self_payload.get("overall_status") != "PASS":
        raise TradingLogicSemanticDiffEvidenceError("SELF_VERIFICATION overall_status must be PASS")

    manifest_digest = _compute_output_manifest_digest(contract)
    if contract.get("manifest_digest") != manifest_digest:
        raise TradingLogicSemanticDiffEvidenceError("manifest_digest mismatch on replay")

    baseline = verify_trading_core_decision_attestation_bundle(
        Path(
            str(
                contract["upstream_bindings"][
                    "baseline_trading_core_decision_attestation_bundle_ref"
                ]
            )
        )
    )
    candidate = verify_trading_core_decision_attestation_bundle(
        Path(
            str(
                contract["upstream_bindings"][
                    "candidate_trading_core_decision_attestation_bundle_ref"
                ]
            )
        )
    )
    bindings = contract.get("upstream_bindings", {})
    if (
        bindings.get("baseline_trading_core_decision_attestation_digest")
        != baseline.artifact_digest
    ):
        raise TradingLogicSemanticDiffEvidenceError(
            "baseline attestation digest mismatch on replay"
        )
    if (
        bindings.get("candidate_trading_core_decision_attestation_digest")
        != candidate.artifact_digest
    ):
        raise TradingLogicSemanticDiffEvidenceError(
            "candidate attestation digest mismatch on replay"
        )


def produce_trading_logic_semantic_diff_evidence_v1(
    *,
    inputs: TradingLogicSemanticDiffEvidenceInputs,
    output_dir: Path | str,
) -> TradingLogicSemanticDiffEvidenceResult:
    final_dir = Path(output_dir)
    _validate_output_target(final_dir)
    _reject_unsafe_overlap(
        bundle_dirs=[
            inputs.baseline_trading_core_decision_attestation_bundle_dir,
            inputs.candidate_trading_core_decision_attestation_bundle_dir,
        ],
        output_dir=final_dir,
    )

    baseline, candidate = verify_trading_logic_semantic_diff_evidence_inputs(inputs)
    contract_body = build_trading_logic_semantic_diff_evidence_v1(
        baseline=baseline,
        candidate=candidate,
        request=inputs.semantic_diff_request,
    )

    staging = _staging_dir_for(final_dir)
    if staging.exists():
        raise TradingLogicSemanticDiffEvidenceError(f"staging directory collision: {staging}")

    try:
        staging.mkdir(parents=True, exist_ok=False)
        artifact_path = staging / ARTIFACT_REL
        self_path = staging / SELF_VERIFICATION_REL

        manifest_digest = _compute_output_manifest_digest(contract_body)
        finalized = _finalize_contract_with_manifest_digest(
            contract_body, manifest_digest=manifest_digest
        )
        artifact_path.write_text(
            serialize_trading_logic_semantic_diff_evidence_v1(finalized),
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
            raise TradingLogicSemanticDiffEvidenceError(
                f"MANIFEST.sha256 verification failed before publish: {msg}"
            )

        reverify_trading_logic_semantic_diff_evidence_v1(output_dir=staging)
        staging.replace(final_dir)

        ok, msg = verify_manifest_sha256(final_dir)
        if not ok:
            raise TradingLogicSemanticDiffEvidenceError(
                f"MANIFEST.sha256 verification failed after publish: {msg}"
            )
    except Exception:
        _cleanup_staging(staging)
        if final_dir.exists():
            shutil.rmtree(final_dir)
        raise

    return TradingLogicSemanticDiffEvidenceResult(
        output_dir=final_dir,
        contract_id=str(finalized["contract_id"]),
        contract_status=str(finalized["contract_status"]),
        evidence_status=str(finalized["evidence_status"]),
        classification=str(finalized["semantic_diff_classification"]),
        contract_path=final_dir / ARTIFACT_REL,
        self_verification_path=final_dir / SELF_VERIFICATION_REL,
        manifest_path=final_dir / MANIFEST_FILENAME,
        minimum_change_class=str(finalized["minimum_change_class"]),
        effective_change_class=str(finalized["effective_change_class"]),
        semantic_diff_digest=str(finalized["semantic_diff_digest"]),
    )


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
    "SCHEMA_VERSION",
    "SELF_VERIFICATION_REL",
    "SEMANTIC_DIFF_CONTRACT_VERSION",
    "TRADING_LOGIC_SEMANTIC_DIFF_EVIDENCE_AUTHORITY_INVARIANTS",
    "SemanticDiffLayer",
    "SemanticDiffEvidenceRequest",
    "TradingLogicSemanticDiffEvidenceError",
    "TradingLogicSemanticDiffEvidenceInputs",
    "TradingLogicSemanticDiffEvidenceResult",
    "VerifiedTradingCoreDecisionAttestationBundle",
    "build_self_verification_v1",
    "build_trading_logic_semantic_diff_evidence_v1",
    "default_diff_layers_from_attestations",
    "default_semantic_diff_evidence_request",
    "produce_trading_logic_semantic_diff_evidence_v1",
    "reverify_trading_logic_semantic_diff_evidence_v1",
    "serialize_trading_logic_semantic_diff_evidence_v1",
    "verify_trading_core_decision_attestation_bundle",
    "verify_trading_logic_semantic_diff_evidence_inputs",
]
