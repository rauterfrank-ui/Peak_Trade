"""Canonical identity binding verifier for integrated offline economic evidence v1.1 (B1)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from src.ops.integrated_offline_economic_evidence_v1.constants_v1 import (
    CANONICAL_IDENTITY_VERIFIER_ID,
    CRS_BINDING_PRODUCTIVE_BOUNDARY,
    CRS_BINDING_RESEARCH_FIXTURE,
    DECISION_EQUIVALENCE_CLASS_FIXTURE,
    DECISION_EQUIVALENCE_CLASS_PRODUCTIVE,
    DOUBLE_PLAY_STRATEGY_INTENT_OWNER,
    EVIDENCE_SCOPE_PRODUCTIVE_CURRENT,
    EXECUTION_MODEL_ANALYTICAL_OBSERVATION_ONLY,
    EXECUTION_MODEL_MV2_BACKTEST_ENGINE,
    EXECUTION_MODEL_SIMULATED_ECONOMICS_BRIDGE,
    FORBIDDEN_STEP29M_STRATEGY_ONLY_MARKERS,
    FORBIDDEN_SUBSTITUTION_RELPATH_MARKERS,
    INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_LAYER_VERSION,
    INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_OWNER,
    MD_BRIDGE_CONTRACT_ID,
    PRODUCTIVE_MASTER_V2_RUNTIME_CYCLE_CAPABILITY_ID,
    RESIDENCY_APPLICABILITY_NOT_ENABLED,
    SIMULATED_ECONOMICS_BRIDGE_OWNER,
)
from src.ops.integrated_offline_economic_evidence_v1.current_offline_decision_equivalence_v1 import (
    DecisionEquivalenceVerificationContextV1,
    verify_current_offline_decision_equivalence_v1,
)
from src.ops.integrated_offline_economic_evidence_v1.current_offline_md_bridge_v1 import (
    verify_current_offline_md_bridge_v1,
)
from src.ops.integrated_offline_economic_evidence_v1.domain_contracts_v1 import (
    safe_resolve_under_repo,
    sha256_file,
)
from src.ops.single_selected_future_policy_v1.constants_v1 import (
    CAP23_RESIDENCY_ELIGIBILITY_GATE_ENABLED,
)

_SHA40 = re.compile(r"^[0-9a-fA-F]{40}$")
_SHA64 = re.compile(r"^[0-9a-fA-F]{64}$")


@dataclass
class CanonicalIdentityVerificationResultV1:
    verified: bool
    productive_identity_verified: bool
    md_bridge_content_verified: bool = False
    decision_equivalence_content_verified: bool = False
    blockers: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "verified": self.verified,
            "productive_identity_verified": self.productive_identity_verified,
            "md_bridge_content_verified": self.md_bridge_content_verified,
            "decision_equivalence_content_verified": self.decision_equivalence_content_verified,
            "blockers": list(self.blockers),
            "notes": list(self.notes),
            "verifier_id": CANONICAL_IDENTITY_VERIFIER_ID,
        }


def _require_non_empty(mapping: Mapping[str, Any], key: str, prefix: str) -> list[str]:
    if not str(mapping.get(key) or "").strip():
        return [f"{prefix}{key.upper()}_MISSING"]
    return []


def _require_sha64(value: str, label: str) -> list[str]:
    if not _SHA64.match(str(value or "")):
        return [f"{label}_INVALID"]
    return []


def _require_sha40(value: str, label: str) -> list[str]:
    if not _SHA40.match(str(value or "")):
        return [f"{label}_INVALID"]
    return []


def resolve_cap23_residency_gate_enabled_for_identity_v1(
    *,
    cap23_residency_gate_enabled: bool | None = None,
) -> bool:
    if cap23_residency_gate_enabled is not None:
        return bool(cap23_residency_gate_enabled)
    return bool(CAP23_RESIDENCY_ELIGIBILITY_GATE_ENABLED)


def _verify_referenced_artifact_digest(
    *,
    repo_root: Path,
    ref: Mapping[str, Any],
    prefix: str,
) -> tuple[str | None, list[str]]:
    relpath = str(ref.get("artifact_relpath") or "")
    expected_digest = str(ref.get("artifact_digest_sha256") or "")
    blockers: list[str] = []
    if not relpath:
        return None, [f"{prefix}:ARTIFACT_RELPATH_MISSING"]
    target = safe_resolve_under_repo(repo_root=repo_root, relpath=relpath)
    if target is None:
        return None, [f"{prefix}:ARTIFACT_RELPATH_FORBIDDEN"]
    if not target.is_file():
        return None, [f"{prefix}:ARTIFACT_MISSING"]
    actual = sha256_file(target)
    if not _SHA64.match(expected_digest):
        blockers.append(f"{prefix}:ARTIFACT_DIGEST_INVALID")
    elif actual.lower() != expected_digest.lower():
        blockers.append(f"{prefix}:ARTIFACT_DIGEST_MISMATCH")
    return relpath, blockers


def verify_canonical_identity_binding_v1(
    *,
    index_document: Mapping[str, Any],
    repo_root: Path | None = None,
    expected_proven_source_sha: str | None = None,
    expected_canonical_decision_config_digest_sha256: str | None = None,
    expected_component_versions_digest_sha256: str | None = None,
    expected_policy_versions_digest_sha256: str | None = None,
    expected_trading_logic_implementation_binding_digest_sha256: str | None = None,
    expected_suitability_registry_snapshot_digest_sha256: str | None = None,
    cap23_residency_gate_enabled: bool | None = None,
) -> CanonicalIdentityVerificationResultV1:
    """Fail-closed verification of canonical_identity_binding_v1 for PRODUCTIVE_CURRENT."""
    blockers: list[str] = []
    notes = ["B1_CANONICAL_IDENTITY_VERIFIER", f"VERIFIER_ID={CANONICAL_IDENTITY_VERIFIER_ID}"]

    scope = str(index_document.get("evidence_scope_class") or "")
    if scope != EVIDENCE_SCOPE_PRODUCTIVE_CURRENT:
        return CanonicalIdentityVerificationResultV1(
            verified=True,
            productive_identity_verified=False,
            notes=[*notes, "SCOPE_NOT_PRODUCTIVE_CURRENT_SKIPPED"],
        )

    binding = index_document.get("canonical_identity_binding_v1")
    if not isinstance(binding, dict):
        return CanonicalIdentityVerificationResultV1(
            verified=False,
            productive_identity_verified=False,
            blockers=["CANONICAL_IDENTITY_BINDING_V1_MISSING"],
            notes=notes,
        )

    proven = str(index_document.get("proven_source_sha") or binding.get("proven_source_sha") or "")
    blockers.extend(_require_sha40(proven, "PROVEN_SOURCE_SHA"))
    if expected_proven_source_sha:
        if proven.lower() != str(expected_proven_source_sha).lower():
            blockers.append("PROVEN_SOURCE_SHA_MISMATCH")
    else:
        blockers.append("EXPECTED_PROVEN_SOURCE_SHA_MISSING")

    if index_document.get("offline_economic_evidence_complete") is True:
        blockers.append("FORBIDDEN_MANUAL_OFFLINE_COMPLETE_BOOLEAN")
    if index_document.get("economic_validity_pass") is True:
        blockers.append("FORBIDDEN_ECONOMIC_VALIDITY_PASS_BOOLEAN")
    if index_document.get("promotion_pass") is True:
        blockers.append("FORBIDDEN_PROMOTION_PASS_BOOLEAN")

    trading = binding.get("trading_logic_identity_v1")
    if not isinstance(trading, dict):
        blockers.append("TRADING_LOGIC_IDENTITY_V1_MISSING")
        trading = {}
    if trading.get("replay_owner") != INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_OWNER:
        blockers.append("TRADING_LOGIC_REPLAY_OWNER_MISMATCH")
    if trading.get("replay_layer_version") != INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_LAYER_VERSION:
        blockers.append("TRADING_LOGIC_REPLAY_LAYER_VERSION_MISMATCH")
    if (
        trading.get("productive_cycle_capability_id")
        != PRODUCTIVE_MASTER_V2_RUNTIME_CYCLE_CAPABILITY_ID
    ):
        blockers.append("PRODUCTIVE_CYCLE_CAPABILITY_MISMATCH")
    for key in (
        "canonical_decision_config_digest_sha256",
        "component_versions_digest_sha256",
        "policy_versions_digest_sha256",
        "trading_logic_implementation_binding_digest_sha256",
    ):
        blockers.extend(_require_non_empty(trading, key, "TRADING_LOGIC:"))
        digest = str(trading.get(key) or "")
        blockers.extend(_require_sha64(digest, f"TRADING_LOGIC:{key.upper()}"))
    if expected_canonical_decision_config_digest_sha256:
        if (
            trading.get("canonical_decision_config_digest_sha256")
            != expected_canonical_decision_config_digest_sha256
        ):
            blockers.append("TRADING_LOGIC:CANONICAL_DECISION_CONFIG_DIGEST_MISMATCH")
    if expected_component_versions_digest_sha256:
        if (
            trading.get("component_versions_digest_sha256")
            != expected_component_versions_digest_sha256
        ):
            blockers.append("TRADING_LOGIC:COMPONENT_VERSIONS_DIGEST_MISMATCH")
    if expected_policy_versions_digest_sha256:
        if trading.get("policy_versions_digest_sha256") != expected_policy_versions_digest_sha256:
            blockers.append("TRADING_LOGIC:POLICY_VERSIONS_DIGEST_MISMATCH")
    if expected_trading_logic_implementation_binding_digest_sha256:
        if (
            trading.get("trading_logic_implementation_binding_digest_sha256")
            != expected_trading_logic_implementation_binding_digest_sha256
        ):
            blockers.append("TRADING_LOGIC:IMPLEMENTATION_BINDING_DIGEST_MISMATCH")

    strategy = binding.get("strategy_selection_identity_v1")
    if not isinstance(strategy, dict):
        blockers.append("STRATEGY_SELECTION_IDENTITY_V1_MISSING")
        strategy = {}
    if strategy.get("strategy_intent_owner") != DOUBLE_PLAY_STRATEGY_INTENT_OWNER:
        blockers.append("STRATEGY_INTENT_OWNER_MISMATCH")
    blockers.extend(
        _require_non_empty(strategy, "suitability_registry_snapshot_digest_sha256", "STRATEGY:")
    )
    blockers.extend(
        _require_sha64(
            str(strategy.get("suitability_registry_snapshot_digest_sha256") or ""),
            "STRATEGY:SUITABILITY_REGISTRY_SNAPSHOT_DIGEST_SHA256",
        )
    )
    if expected_suitability_registry_snapshot_digest_sha256:
        if (
            strategy.get("suitability_registry_snapshot_digest_sha256")
            != expected_suitability_registry_snapshot_digest_sha256
        ):
            blockers.append("STRATEGY:SUITABILITY_REGISTRY_DIGEST_MISMATCH")
    static_strategy_id = str(strategy.get("strategy_id") or "")
    if static_strategy_id and not str(
        strategy.get("suitability_registry_snapshot_digest_sha256") or ""
    ):
        blockers.append("FORBIDDEN_STATIC_STRATEGY_ID_WITHOUT_REGISTRY")
    for marker in FORBIDDEN_STEP29M_STRATEGY_ONLY_MARKERS:
        if marker in static_strategy_id.lower() or marker in str(
            strategy.get("strategy_provenance") or ""
        ):
            blockers.append(f"FORBIDDEN_STEP29M_STRATEGY_SUBSTITUTION:{marker}")
    if strategy.get("step29m_strategy_id_only") is True:
        blockers.append("FORBIDDEN_STEP29M_STRATEGY_ID_ONLY")

    instrument = binding.get("instrument_identity_v1")
    if not isinstance(instrument, dict):
        blockers.append("INSTRUMENT_IDENTITY_V1_MISSING")
        instrument = {}
    for key in (
        "canonical_instrument_id",
        "venue",
        "venue_native_id",
        "market_type",
        "contract_type",
        "instrument_mapping_digest_sha256",
    ):
        blockers.extend(_require_non_empty(instrument, key, "INSTRUMENT:"))
    blockers.extend(
        _require_sha64(
            str(instrument.get("instrument_mapping_digest_sha256") or ""),
            "INSTRUMENT:INSTRUMENT_MAPPING_DIGEST_SHA256",
        )
    )
    display_symbol = str(instrument.get("display_symbol") or "")
    canonical_id = str(instrument.get("canonical_instrument_id") or "")
    if display_symbol and display_symbol == canonical_id and not instrument.get("venue_native_id"):
        blockers.append("INSTRUMENT:DISPLAY_SYMBOL_ONLY_BINDING_REJECTED")

    universe = binding.get("universe_identity_v1")
    if not isinstance(universe, dict):
        blockers.append("UNIVERSE_IDENTITY_V1_MISSING")
        universe = {}
    for key in ("universe_snapshot_id", "ranking_snapshot_id", "selection_integrity_digest_sha256"):
        blockers.extend(_require_non_empty(universe, key, "UNIVERSE:"))
    blockers.extend(
        _require_sha64(
            str(universe.get("selection_integrity_digest_sha256") or ""),
            "UNIVERSE:SELECTION_INTEGRITY_DIGEST_SHA256",
        )
    )
    fleet_marker = str(universe.get("universe_scope_class") or "")
    if fleet_marker in {"RESEARCH_FLEET", "STEP29M_FLEET", "VERSIONED_FINAL_FLEET"}:
        blockers.append("FORBIDDEN_STEP29M_RESEARCH_FLEET_UNIVERSE")
    if "research_fleet" in fleet_marker.lower() or "step29m" in fleet_marker.lower():
        blockers.append("FORBIDDEN_RESEARCH_FLEET_SUBSTITUTION")

    cap23_enabled = resolve_cap23_residency_gate_enabled_for_identity_v1(
        cap23_residency_gate_enabled=cap23_residency_gate_enabled
    )
    residency_applicability = str(universe.get("residency_applicability") or "")
    residency_epoch_id = str(universe.get("residency_epoch_id") or "")
    residency_witness_digest = str(universe.get("residency_witness_digest_sha256") or "")
    if cap23_enabled:
        if residency_applicability == RESIDENCY_APPLICABILITY_NOT_ENABLED:
            blockers.append("RESIDENCY_APPLICABILITY_CONTRADICTS_ENABLED_GATE")
        if not residency_epoch_id:
            blockers.append("UNIVERSE:RESIDENCY_EPOCH_ID_MISSING")
        if not _SHA64.match(residency_witness_digest):
            blockers.append("UNIVERSE:RESIDENCY_WITNESS_DIGEST_SHA256_INVALID")
    else:
        if residency_applicability != RESIDENCY_APPLICABILITY_NOT_ENABLED:
            blockers.append("UNIVERSE:RESIDENCY_APPLICABILITY_NOT_DECLARED")
        if residency_epoch_id and not residency_witness_digest:
            blockers.append("UNIVERSE:RESIDENCY_WITNESS_REQUIRED_WHEN_EPOCH_PRESENT")

    md = binding.get("market_data_lineage_v1")
    if not isinstance(md, dict):
        blockers.append("MARKET_DATA_LINEAGE_V1_MISSING")
        md = {}
    blockers.extend(_require_non_empty(md, "md_lineage_class", "MD:"))
    blockers.extend(_require_non_empty(md, "dataset_content_digest_sha256", "MD:"))
    blockers.extend(
        _require_sha64(str(md.get("dataset_content_digest_sha256") or ""), "MD:DATASET_DIGEST")
    )
    if md.get("bridge_contract_id") != MD_BRIDGE_CONTRACT_ID:
        blockers.append("MD:BRIDGE_CONTRACT_ID_MISMATCH")
    blockers.extend(_require_non_empty(md, "equivalence_attestation_ref", "MD:"))
    attestation = md.get("equivalence_attestation_ref")
    if not isinstance(attestation, dict):
        blockers.append("MD:EQUIVALENCE_ATTESTATION_REF_MALFORMED")
    else:
        blockers.extend(_require_non_empty(attestation, "artifact_relpath", "MD:ATTESTATION:"))
        blockers.extend(
            _require_non_empty(attestation, "artifact_digest_sha256", "MD:ATTESTATION:")
        )
    if md.get("raw_bar_loop_without_productive_gates") is True:
        blockers.append("FORBIDDEN_RAW_BAR_LOOP_WITHOUT_PRODUCTIVE_GATES")

    gates = binding.get("productive_gate_binding_v1")
    if not isinstance(gates, dict):
        blockers.append("PRODUCTIVE_GATE_BINDING_V1_MISSING")
        gates = {}
    for gate_key in (
        "g17_typed_volatility_binding_mode",
        "cap61_observation_acceptance_binding_mode",
        "confirmation_progression_binding_mode",
    ):
        blockers.extend(_require_non_empty(gates, gate_key, "GATE:"))
        mode = str(gates.get(gate_key) or "")
        if mode not in {"MUST_REPLAY", "MUST_RECONSTRUCT", "PROVEN_REFERENCE"}:
            blockers.append(f"GATE:{gate_key.upper()}_INVALID")

    de_ref = binding.get("decision_equivalence_ref")
    if not isinstance(de_ref, dict):
        blockers.append("DECISION_EQUIVALENCE_REF_MISSING")
        de_ref = {}
    for key in ("artifact_relpath", "artifact_digest_sha256", "equivalence_class"):
        blockers.extend(_require_non_empty(de_ref, key, "DECISION_EQUIVALENCE:"))
    eq_class = str(de_ref.get("equivalence_class") or "")
    if eq_class != DECISION_EQUIVALENCE_CLASS_PRODUCTIVE:
        blockers.append("DECISION_EQUIVALENCE_CLASS_NOT_PRODUCTIVE")
    if eq_class == DECISION_EQUIVALENCE_CLASS_FIXTURE:
        blockers.append("FORBIDDEN_FIXTURE_PARITY_AS_PRODUCTIVE_DECISION_EQUIVALENCE")
    if de_ref.get("head_bound_fixture_only") is True:
        blockers.append("FORBIDDEN_HEAD_BOUND_FIXTURE_ONLY_DECISION_EQUIVALENCE")
    if not str(strategy.get("per_decision_selected_strategy_binding_ref") or ""):
        blockers.append("STRATEGY:PER_DECISION_SELECTED_STRATEGY_BINDING_REF_MISSING")

    execution = binding.get("economic_execution_model_identity_v1")
    if not isinstance(execution, dict):
        blockers.append("EXECUTION_MODEL_IDENTITY_V1_MISSING")
        execution = {}
    model_class = str(execution.get("execution_model_class") or "")
    if model_class != EXECUTION_MODEL_SIMULATED_ECONOMICS_BRIDGE:
        blockers.append("EXECUTION_MODEL_CLASS_NOT_SIMULATED_ECONOMICS_BRIDGE")
    if model_class == EXECUTION_MODEL_MV2_BACKTEST_ENGINE:
        blockers.append("FORBIDDEN_MV2_BACKTEST_ENGINE_AS_CURRENT_EXECUTION_AUTHORITY")
    if model_class == EXECUTION_MODEL_ANALYTICAL_OBSERVATION_ONLY:
        blockers.append("FORBIDDEN_ANALYTICAL_OBSERVATION_EXECUTION_AUTHORITY")
    if execution.get("owner") != SIMULATED_ECONOMICS_BRIDGE_OWNER:
        blockers.append("EXECUTION_MODEL_OWNER_MISMATCH")
    for marker in FORBIDDEN_SUBSTITUTION_RELPATH_MARKERS:
        if marker in str(execution.get("lineage_relpath") or ""):
            blockers.append(f"FORBIDDEN_EXECUTION_LINEAGE:{marker}")

    risk = binding.get("risk_sizing_identity_v1")
    if not isinstance(risk, dict):
        blockers.append("RISK_SIZING_IDENTITY_V1_MISSING")
        risk = {}
    crs_mode = str(risk.get("crs_binding_mode") or "")
    if crs_mode != CRS_BINDING_PRODUCTIVE_BOUNDARY:
        blockers.append("CRS_BINDING_MODE_NOT_PRODUCTIVE_BOUNDARY")
    if crs_mode == CRS_BINDING_RESEARCH_FIXTURE:
        blockers.append("FORBIDDEN_RESEARCH_FIXTURE_CRS_BINDING")
    blockers.extend(_require_non_empty(risk, "capital_context_digest_sha256", "RISK:"))
    blockers.extend(
        _require_sha64(
            str(risk.get("capital_context_digest_sha256") or ""), "RISK:CAPITAL_CONTEXT_DIGEST"
        )
    )

    policy = binding.get("economic_policy_reference_v1")
    if not isinstance(policy, dict):
        blockers.append("ECONOMIC_POLICY_REFERENCE_V1_MISSING")
        policy = {}
    for key in ("policy_id", "policy_version", "policy_digest_sha256"):
        blockers.extend(_require_non_empty(policy, key, "POLICY:"))
    for forbidden_threshold in (
        "minimum_net_expectancy",
        "minimum_profit_factor",
        "maximum_max_drawdown",
    ):
        if policy.get(forbidden_threshold) is not None:
            blockers.append(f"FORBIDDEN_POLICY_THRESHOLD_EMBEDDED:{forbidden_threshold}")

    md_bridge_content_verified = False
    decision_equivalence_content_verified = False
    structural_blockers = sorted(set(blockers))

    if (
        repo_root is not None
        and scope == EVIDENCE_SCOPE_PRODUCTIVE_CURRENT
        and not structural_blockers
    ):
        root = repo_root.resolve()
        md_relpath, md_ref_blockers = _verify_referenced_artifact_digest(
            repo_root=root,
            ref=md.get("equivalence_attestation_ref")
            if isinstance(md.get("equivalence_attestation_ref"), Mapping)
            else {},
            prefix="MD:ATTESTATION",
        )
        blockers.extend(md_ref_blockers)
        md_result = verify_current_offline_md_bridge_v1(
            repo_root=root,
            artifact_relpath=md_relpath,
            expected_dataset_content_digest_sha256=str(
                md.get("dataset_content_digest_sha256") or ""
            ),
            expected_instrument_mapping_digest_sha256=str(
                instrument.get("instrument_mapping_digest_sha256") or ""
            ),
        )
        md_bridge_content_verified = md_result.bridge_verified
        if not md_result.bridge_verified:
            blockers.extend(f"MD_BRIDGE:{b}" for b in md_result.blockers)

        de_relpath, de_ref_blockers = _verify_referenced_artifact_digest(
            repo_root=root,
            ref=de_ref,
            prefix="DECISION_EQUIVALENCE",
        )
        blockers.extend(de_ref_blockers)
        de_context = DecisionEquivalenceVerificationContextV1(
            identity_binding_verified=True,
            md_bridge_verified=md_bridge_content_verified,
            declared_equivalence_class=eq_class,
        )
        de_result = verify_current_offline_decision_equivalence_v1(
            repo_root=root,
            artifact_relpath=de_relpath,
            context=de_context,
        )
        decision_equivalence_content_verified = de_result.equivalence_verified
        if not de_result.equivalence_verified:
            blockers.extend(f"DECISION_EQUIVALENCE:{b}" for b in de_result.blockers)
    elif repo_root is not None and scope == EVIDENCE_SCOPE_PRODUCTIVE_CURRENT:
        notes.append("B2_CONTENT_VERIFICATION_SKIPPED_DUE_TO_STRUCTURAL_BLOCKERS")

    unique = sorted(set(blockers))
    verified = not unique
    return CanonicalIdentityVerificationResultV1(
        verified=verified,
        productive_identity_verified=verified,
        md_bridge_content_verified=md_bridge_content_verified,
        decision_equivalence_content_verified=decision_equivalence_content_verified,
        blockers=unique,
        notes=notes,
    )
