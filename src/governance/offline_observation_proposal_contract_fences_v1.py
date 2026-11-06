"""Offline observation / comparison / proposal / eligibility contract fences v1.

Reconciles existing Surface O, Surface M, learning_loop, legacy promotion
engine, and DDO authority markers into one fail-closed taxonomy. This module
does not grant learning, promotion, trading, selection, risk, runtime,
execution, canary, or live authority.
"""

from __future__ import annotations

import ast
import inspect
import tempfile
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final, Mapping

from src.backtest.economic_validity_policy_v1 import canonical_economic_validity_policy_v1
from src.governance.promotion_loop.engine import apply_proposals_to_live_overrides
from src.governance.promotion_loop.models import (
    DecisionStatus,
    PromotionCandidate,
    PromotionDecision,
    PromotionProposal,
)
from src.governance.promotion_loop.policy import AutoApplyPolicy
from src.governance.promotion_loop.promotion_economic_gate_v1 import (
    AUTHORITY_EFFECT_NONE,
    ACTIVATION_EFFECT_NONE,
    DEPLOYMENT_EFFECT_NONE,
    PASS_STATUS,
    PROMOTION_CANDIDATE_ELIGIBILITY_DOES_NOT_IMPLY_ACTIVATION,
    PROMOTION_CANDIDATE_ELIGIBILITY_DOES_NOT_IMPLY_DEPLOYMENT,
    PROMOTION_CANDIDATE_ELIGIBILITY_DOES_NOT_IMPLY_EXECUTION,
    PROMOTION_CANDIDATE_ELIGIBILITY_DOES_NOT_IMPLY_RUNTIME,
    PROMOTION_ECONOMIC_GATE_POLICY_OWNER,
    PromotionEconomicGateInputV1,
    RUNTIME_EFFECT_NONE,
    canonical_promotion_economic_gate_policy_v1,
    evaluate_current_repo_promotion_gate_v1,
    evaluate_promotion_economic_gate_v1,
)
from src.learning.deterministic_decision_outcome_v0.authority_v0 import (
    AUTHORITY_OWNER as DDO_AUTHORITY_OWNER,
    CAPTURE_ADAPTER_PRESENT,
    CAPTURE_RUNTIME_EFFECT,
    LEARNING_PRODUCTIVE_AUTHORITY,
    PROMOTION_AUTHORITY_ACTIVATION,
    PROMOTION_AUTHORITY_EFFECT,
    PROMOTION_CONTROLLER_CODE_PRESENT,
    PROMOTION_ELIGIBILITY_COMPUTATION_ALLOWED,
    RUNTIME_EFFECT as DDO_RUNTIME_EFFECT,
    SECOND_PROMOTION_AUTHORITY_CREATED,
)
from src.learning.deterministic_decision_outcome_v0.capture_v0 import (
    CAPTURE_FAILURE_CHANGES_DECISION,
    IMPLEMENTED_CAPTURE_SEAMS_V0,
)
from src.learning.deterministic_decision_outcome_v0.common_v0 import SCHEMA_NAME_LEDGER_ENVELOPE
from src.learning.deterministic_decision_outcome_v0.enums_v0 import (
    UNKNOWN,
    VALIDATION_GATE_IDS_V0,
)
from src.learning.deterministic_decision_outcome_v0.learning_records_v0 import (
    build_candidate_artifact_v0,
    build_learning_hypothesis_v0,
    build_validation_evidence_pack_v0,
)
from src.learning.deterministic_decision_outcome_v0.promotion_controller_v0 import (
    PROMOTION_ELIGIBLE_EQUALS_DEPLOYMENT_AUTHORIZED,
    evaluate_promotion_eligibility_v0,
)
from src.learning.deterministic_decision_outcome_v0.promotion_records_v0 import (
    build_promotion_policy_v0,
)
from src.meta.learning_loop import authority_lease_and_revocation_v1 as _authority_lease
from src.meta.learning_loop.comparison_common_durable_evidence_binding_v1 import (
    COMPARISON_AUTHORITY_INVARIANTS,
)
from src.meta.learning_loop.comparison_promotion_policy_decision_v1 import (
    AUTHORITY_LEVEL as COMPARISON_PROMOTION_DECISION_AUTHORITY_LEVEL,
    PROMOTION_POLICY_DECISION_AUTHORITY_INVARIANTS,
)
from src.meta.learning_loop.deploy_inactive_v1 import DEPLOYMENT_CANDIDATE_CONTRACT_NAME
from src.meta.learning_loop.models import ConfigPatch, PatchStatus
from src.meta.learning_loop.runtime_observation_feedback_v1 import OBSERVATION_CONTRACT_NAME
from src.trading.master_v2.feedback_learning_boundary_offline_replay_binding_adapter_v0 import (
    FEEDBACK_LEARNING_BOUNDARY_EFFECT_NONE,
    FEEDBACK_LEARNING_CANONICAL_OWNER,
    FEEDBACK_LEARNING_MODE_OBSERVE_ONLY_NO_MUTATION,
    evaluate_offline_feedback_learning_boundary_v0,
)
from src.trading.master_v2.promotion_gate_boundary_offline_replay_binding_adapter_v0 import (
    PROMOTION_GATE_CANONICAL_OWNER,
    RUNTIME_AUTHORITY_EFFECT_NONE as SURFACE_M_RUNTIME_AUTHORITY_EFFECT_NONE,
)

CONTRACT_ID: Final[str] = "offline_observation_proposal_contract_fences_v1"
CONTRACT_VERSION: Final[str] = "v1"
OWNER_GO: Final[str] = (
    "PEAK_TRADE_OWNER_GO_WP_02_OFFLINE_OBSERVATION_PROPOSAL_CONTRACT_FENCES_MAX_SAFE_LEVERAGE_V1"
)
AUTHORITY_EFFECT: Final[str] = "NONE"
CAN_GRANT_AUTHORITY: Final[bool] = False
PRODUCTIVE_LEARNING_AUTHORITY: Final[str] = "NONE"
PRODUCTIVE_PROMOTION_AUTHORITY: Final[str] = "NONE"
LIVE_AUTHORIZED: Final[bool] = False
CANARY_AUTHORIZED: Final[bool] = False
TESTNET_AUTHORIZED: Final[bool] = False
ORDERS_ALLOWED: Final[bool] = False

CONTRACT_LAYERS: Final[tuple[str, ...]] = (
    "OBSERVATION",
    "COMPARISON",
    "PROPOSAL",
    "PROMOTION_ELIGIBILITY",
    "PRODUCTIVE_MUTATION",
    "PRODUCTIVE_PROMOTION",
)

LEARNING_LOOP_ALLOWED_ROLE: Final[str] = "OFFLINE_OBSERVATION_COMPARISON_PROPOSAL_CONTRACTS_ONLY"
SURFACE_O_ROLE: Final[str] = "OBSERVATION_ONLY"
SURFACE_M_ROLE: Final[str] = "PROMOTION_GATE_EVALUATE_ONLY"
LEGACY_PROMOTION_ENGINE_ROLE: Final[str] = "PROPOSAL_MANUAL_ONLY_DEFAULT_OFF_UNGRANTED"
DDO_ROLE: Final[str] = "OFFLINE_OBSERVATION_ONLY"
DDO_DOES_NOT_REPLACE_LEARNING_LOOP: Final[bool] = True
HOOK_PRESENCE_IS_NOT_AUTHORITY_GRANT: Final[bool] = True
LEGACY_PROMOTION_ENGINE_AUTO_APPLY_AS_AUTHORITY: Final[str] = "DO_NOT_RESTORE"

LEDGER_FAMILIES: Final[Mapping[str, str]] = MappingProxyType(
    {
        "ddo_ledger": SCHEMA_NAME_LEDGER_ENVELOPE,
        "execution_accounting_ledger": "execution_accounting_ledger",
        "aiops_trend_ledger": "aiops_trend_ledger",
        "atlas_historical_child_ledger": "atlas_historical_child_ledger",
        "research_trade_ledger": "research_trade_ledger",
    }
)

SURFACE_M_CONSUMERS: Final[tuple[str, ...]] = (
    "src/research/cross_sectional_lead_lag_v0_promotion_economic_gate_precheck_v0.py",
    "src/research/linear_evidence/offline_productive_linear_diagnostics_promotion_economic_gate_consumer_binding_v0.py",
    "src/trading/master_v2/promotion_gate_boundary_offline_replay_binding_adapter_v0.py",
    "src/trading/master_v2/promotion_gate_boundary_backtest_state_file_binding_adapter_v0.py",
)

WP02_ORDER_SCAN_PATHS: Final[tuple[str, ...]] = (
    "src/governance/offline_observation_proposal_contract_fences_v1.py",
    "src/learning/deterministic_decision_outcome_v0/authority_v0.py",
    "src/learning/deterministic_decision_outcome_v0/capture_v0.py",
    "src/learning/deterministic_decision_outcome_v0/promotion_controller_v0.py",
    "src/meta/learning_loop/comparison_promotion_policy_decision_v1.py",
    "src/meta/learning_loop/runtime_observation_feedback_v1.py",
    "src/trading/master_v2/feedback_learning_boundary_offline_replay_binding_adapter_v0.py",
    "src/trading/master_v2/promotion_gate_boundary_offline_replay_binding_adapter_v0.py",
    "src/governance/promotion_loop/engine.py",
)

_ORDER_SUBMIT_NAMES: Final[frozenset[str]] = frozenset(
    {
        "submit_order",
        "submit_orders",
        "place_order",
        "add_order",
        "create_exchange_order",
    }
)
_REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[2]


class OfflineObservationProposalContractFenceError(ValueError):
    """Fail-closed WP-02 offline observation / proposal fence error."""


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise OfflineObservationProposalContractFenceError(code)


def _ddo_envelope(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "record_id": "rec-wp02-01",
        "event_time_utc": "2026-09-02T00:00:00Z",
        "correlation_id": "cor-wp02-01",
        "cycle_id": None,
        "causal_parent_ids": [],
        "producer_id": "wp02-offline-fence",
        "authority_owner": UNKNOWN,
        "code_sha": UNKNOWN,
        "config_hash": UNKNOWN,
        "evidence_hash": UNKNOWN,
        "evidence_source_refs": ["wp02-fence-evidence"],
    }
    payload.update(overrides)
    return payload


def _call_names(tree: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Name):
            names.add(func.id)
        elif isinstance(func, ast.Attribute):
            names.add(func.attr)
    return names


def _scan_order_submit_reachability() -> tuple[bool, tuple[str, ...]]:
    hits: list[str] = []
    for relative in WP02_ORDER_SCAN_PATHS:
        path = _REPO_ROOT / relative
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=relative)
        called = _call_names(tree) & _ORDER_SUBMIT_NAMES
        if called:
            hits.append(f"{relative}:{','.join(sorted(called))}")
    return (not hits, tuple(hits))


def _ddo_does_not_import_learning_loop() -> bool:
    package = _REPO_ROOT / "src" / "learning" / "deterministic_decision_outcome_v0"
    for path in sorted(package.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith("src.meta.learning_loop"):
                        return False
            elif isinstance(node, ast.ImportFrom) and node.module:
                if node.module.startswith("src.meta.learning_loop"):
                    return False
    return True


def _surface_m_pass_input() -> PromotionEconomicGateInputV1:
    return PromotionEconomicGateInputV1(
        strategy_id="mv2_offline_research",
        strategy_version="v1",
        candidate_id="wp02-fence-pass-candidate",
        economic_viability_evidence_ref="evidence://admissible/futures/v1/wp02-fence",
        economic_validity_status=PASS_STATUS,
        economic_validity_proven=True,
        profitability_claim_allowed=True,
        robustness_status=PASS_STATUS,
        data_admissibility_status=PASS_STATUS,
        evidence_admissibility_status=PASS_STATUS,
        policy_threshold_status=PASS_STATUS,
        walk_forward_status=PASS_STATUS,
        out_of_sample_status=PASS_STATUS,
        monte_carlo_status=PASS_STATUS,
        stress_status=PASS_STATUS,
        parameter_sensitivity_status=PASS_STATUS,
        reproducibility_status=PASS_STATUS,
        digest_binding_status=PASS_STATUS,
        manifest_binding_status=PASS_STATUS,
        safety_policy_status=PASS_STATUS,
        futures_only=True,
        bitcoin_direction_allowed=False,
        config_digest="a" * 64,
        implementation_digest="b" * 64,
        policy_digest=canonical_economic_validity_policy_v1().policy_digest(),
        evidence_manifest_digest="c" * 64,
        dataset_digest="d" * 64,
        robustness_result_digests=("wf:" + "e" * 61,),
        safety_policy_digest="f" * 64,
        evidence_admissible=True,
    )


def _prove_surface_m_pass_is_not_grant() -> Mapping[str, Any]:
    policy = canonical_promotion_economic_gate_policy_v1()
    passing = evaluate_promotion_economic_gate_v1(
        policy=policy,
        input_data=_surface_m_pass_input(),
        evaluation_timestamp="2026-09-02T00:00:00Z",
    )
    current = evaluate_current_repo_promotion_gate_v1()
    _require(passing.authority_effect == AUTHORITY_EFFECT_NONE, "SURFACE_M_PASS_AUTHORITY_NOT_NONE")
    _require(passing.runtime_effect == RUNTIME_EFFECT_NONE, "SURFACE_M_PASS_RUNTIME_NOT_NONE")
    _require(
        passing.deployment_effect == DEPLOYMENT_EFFECT_NONE,
        "SURFACE_M_PASS_DEPLOYMENT_NOT_NONE",
    )
    _require(
        passing.activation_effect == ACTIVATION_EFFECT_NONE,
        "SURFACE_M_PASS_ACTIVATION_NOT_NONE",
    )
    _require(passing.deployment_eligible is False, "SURFACE_M_PASS_DEPLOYMENT_ELIGIBLE")
    _require(passing.runtime_eligible is False, "SURFACE_M_PASS_RUNTIME_ELIGIBLE")
    _require(passing.activation_allowed is False, "SURFACE_M_PASS_ACTIVATION_ALLOWED")
    _require(passing.execution_allowed is False, "SURFACE_M_PASS_EXECUTION_ALLOWED")
    _require(
        PROMOTION_CANDIDATE_ELIGIBILITY_DOES_NOT_IMPLY_DEPLOYMENT is True,
        "SURFACE_M_ELIGIBILITY_IMPLIES_DEPLOYMENT",
    )
    _require(
        PROMOTION_CANDIDATE_ELIGIBILITY_DOES_NOT_IMPLY_RUNTIME is True,
        "SURFACE_M_ELIGIBILITY_IMPLIES_RUNTIME",
    )
    _require(
        PROMOTION_CANDIDATE_ELIGIBILITY_DOES_NOT_IMPLY_ACTIVATION is True,
        "SURFACE_M_ELIGIBILITY_IMPLIES_ACTIVATION",
    )
    _require(
        PROMOTION_CANDIDATE_ELIGIBILITY_DOES_NOT_IMPLY_EXECUTION is True,
        "SURFACE_M_ELIGIBILITY_IMPLIES_EXECUTION",
    )
    _require(current.eligible_for_promotion_candidate is False, "CURRENT_REPO_GATE_NOT_FAIL_CLOSED")
    _require(current.authority_effect == AUTHORITY_EFFECT_NONE, "CURRENT_REPO_GATE_AUTHORITY")
    return {
        "pass_eligible_for_promotion_candidate": passing.eligible_for_promotion_candidate,
        "pass_authority_effect": passing.authority_effect,
        "pass_deployment_eligible": passing.deployment_eligible,
        "pass_execution_allowed": passing.execution_allowed,
        "current_repo_eligible": current.eligible_for_promotion_candidate,
        "canonical_owner": PROMOTION_ECONOMIC_GATE_POLICY_OWNER,
        "surface_m_adapter_owner": PROMOTION_GATE_CANONICAL_OWNER,
        "surface_m_runtime_authority_effect": SURFACE_M_RUNTIME_AUTHORITY_EFFECT_NONE,
    }


def _prove_ddo_eligibility_is_not_grant() -> Mapping[str, Any]:
    hypothesis = build_learning_hypothesis_v0(
        _ddo_envelope(
            schema_name="learning_hypothesis",
            schema_version="learning_hypothesis_v0",
            record_id="hyp-wp02-01",
            proposal="wp02-fence-hypothesis",
            productive_authority="NONE",
        )
    )
    candidate = build_candidate_artifact_v0(
        _ddo_envelope(
            schema_name="candidate_artifact",
            schema_version="candidate_artifact_v0",
            record_id="cand-wp02-01",
            hypothesis_ref="hyp-wp02-01",
            intended_scope="P0-evidence-only",
            promotion_class="P0",
            artifact_hash=UNKNOWN,
            rejected=False,
            causal_parent_ids=["hyp-wp02-01"],
        )
    )
    policy = build_promotion_policy_v0(
        _ddo_envelope(
            schema_name="promotion_policy",
            schema_version="promotion_policy_v0",
            record_id="pol-wp02-01",
            policy_version="promotion_policy_v0_wp02_fence",
            allowed_promotion_classes=["P0", "P1"],
            autonomous_promotion_classes=[],
            promotion_authority_activation=False,
        )
    )
    pack = build_validation_evidence_pack_v0(
        _ddo_envelope(
            schema_name="validation_evidence_pack",
            schema_version="validation_evidence_pack_v0",
            record_id="pack-wp02-01",
            candidate_artifact_ref="cand-wp02-01",
            incumbent_artifact_ref=None,
            gates={gate: "PASS" for gate in VALIDATION_GATE_IDS_V0},
            causal_parent_ids=["cand-wp02-01"],
        )
    )
    eligibility = evaluate_promotion_eligibility_v0(
        policy=policy,
        candidate=candidate,
        evidence_pack=pack,
        eligibility_record_id="elig-wp02-01",
        event_time_utc="2026-09-02T00:00:00Z",
        correlation_id="cor-wp02-01",
        producer_id="wp02-offline-fence",
    )
    _require(eligibility["eligible"] is True, "DDO_ELIGIBILITY_PROOF_NOT_ELIGIBLE")
    _require(eligibility["deployment_authorized"] is False, "DDO_ELIGIBILITY_DEPLOYMENT_GRANTED")
    _require(eligibility["execution_authorized"] is False, "DDO_ELIGIBILITY_EXECUTION_GRANTED")
    _require(
        PROMOTION_ELIGIBLE_EQUALS_DEPLOYMENT_AUTHORIZED is False,
        "DDO_ELIGIBLE_EQUALS_DEPLOYMENT",
    )
    _require(hypothesis["productive_authority"] == "NONE", "DDO_HYPOTHESIS_PRODUCTIVE_AUTHORITY")
    return {
        "eligible": eligibility["eligible"],
        "deployment_authorized": eligibility["deployment_authorized"],
        "execution_authorized": eligibility["execution_authorized"],
        "authority_owner": DDO_AUTHORITY_OWNER,
        "promotion_authority_effect": PROMOTION_AUTHORITY_EFFECT,
        "promotion_authority_activation": PROMOTION_AUTHORITY_ACTIVATION,
    }


def _prove_legacy_engine_ungranted() -> Mapping[str, Any]:
    policy = AutoApplyPolicy()
    _require(policy.mode == "manual_only", "LEGACY_ENGINE_DEFAULT_NOT_MANUAL_ONLY")
    _require(policy.is_bounded_auto() is False, "LEGACY_ENGINE_DEFAULT_BOUNDED_AUTO")
    source = inspect.getsource(apply_proposals_to_live_overrides)
    _require("return None" in source, "LEGACY_LIVE_OVERRIDE_WRITER_NOT_FAIL_CLOSED")
    _require("write_text" not in source, "LEGACY_LIVE_OVERRIDE_WRITER_HAS_WRITE_TEXT")
    _require("open(" not in source, "LEGACY_LIVE_OVERRIDE_WRITER_HAS_OPEN")
    patch = ConfigPatch(
        id="wp02-fence-patch-1",
        target="portfolio.leverage",
        old_value=1.0,
        new_value=1.75,
        status=PatchStatus.APPLIED_OFFLINE,
    )
    proposal = PromotionProposal(
        proposal_id="wp02_fence_live_override_001",
        title="wp02 fence live-override deny",
        description="proposal-only proof that auto-apply remains ungranted",
        decisions=[
            PromotionDecision(
                candidate=PromotionCandidate(
                    patch=patch,
                    eligible_for_live=True,
                    tags=["leverage"],
                ),
                status=DecisionStatus.ACCEPTED_FOR_PROPOSAL,
                reasons=["wp02 fence accepted proposal"],
            )
        ],
        meta={},
    )
    with tempfile.TemporaryDirectory() as tmp:
        live_path = Path(tmp) / "config" / "live_overrides" / "auto.toml"
        written = apply_proposals_to_live_overrides(
            [proposal],
            policy=AutoApplyPolicy(mode="bounded_auto"),
            live_override_path=live_path,
        )
        _require(written is None, "LEGACY_LIVE_OVERRIDE_WRITE_RETURNED_PATH")
        _require(not live_path.exists(), "LEGACY_LIVE_OVERRIDE_FILE_CREATED")
    return {
        "default_mode": policy.mode,
        "auto_apply_as_authority": LEGACY_PROMOTION_ENGINE_AUTO_APPLY_AS_AUTHORITY,
        "live_override_write": False,
    }


def _prove_surface_o_observation_only() -> Mapping[str, Any]:
    boundary = evaluate_offline_feedback_learning_boundary_v0()
    _require(boundary.observe_only_no_mutation is True, "SURFACE_O_NOT_OBSERVE_ONLY")
    _require(boundary.no_promotion_mutation is True, "SURFACE_O_PROMOTION_MUTATION")
    _require(
        boundary.no_runtime_eligibility_mutation is True,
        "SURFACE_O_RUNTIME_ELIGIBILITY_MUTATION",
    )
    _require(
        boundary.feedback_learning_mode == FEEDBACK_LEARNING_MODE_OBSERVE_ONLY_NO_MUTATION,
        "SURFACE_O_MODE_NOT_OBSERVE_ONLY",
    )
    _require(
        boundary.feedback_observation_contract_ref == OBSERVATION_CONTRACT_NAME,
        "SURFACE_O_OBSERVATION_CONTRACT_DRIFT",
    )
    _require(
        boundary.learning_deploy_inactive_contract_ref == DEPLOYMENT_CANDIDATE_CONTRACT_NAME,
        "SURFACE_O_DEPLOY_INACTIVE_CONTRACT_DRIFT",
    )
    _require(
        boundary.runtime_authority_effect == "NONE",
        "SURFACE_O_RUNTIME_AUTHORITY_NOT_NONE",
    )
    return {
        "role": SURFACE_O_ROLE,
        "canonical_owner": FEEDBACK_LEARNING_CANONICAL_OWNER,
        "observation_contract": OBSERVATION_CONTRACT_NAME,
        "boundary_effect_none_token": FEEDBACK_LEARNING_BOUNDARY_EFFECT_NONE,
        "observe_only_no_mutation": boundary.observe_only_no_mutation,
    }


def evaluate_offline_observation_proposal_contract_fences_v1() -> MappingProxyType[str, Any]:
    """Evaluate the existing offline observation/proposal fences fail-closed."""
    _require(CAN_GRANT_AUTHORITY is False, "FENCE_CAN_GRANT_AUTHORITY")
    _require(PRODUCTIVE_LEARNING_AUTHORITY == "NONE", "FENCE_PRODUCTIVE_LEARNING_AUTHORITY")
    _require(PRODUCTIVE_PROMOTION_AUTHORITY == "NONE", "FENCE_PRODUCTIVE_PROMOTION_AUTHORITY")
    _require(LEARNING_PRODUCTIVE_AUTHORITY == "NONE", "DDO_PRODUCTIVE_LEARNING_AUTHORITY")
    _require(DDO_AUTHORITY_OWNER == "NONE", "DDO_AUTHORITY_OWNER_NOT_NONE")
    _require(PROMOTION_AUTHORITY_EFFECT == "NONE", "DDO_PROMOTION_AUTHORITY_EFFECT")
    _require(PROMOTION_AUTHORITY_ACTIVATION is False, "DDO_PROMOTION_AUTHORITY_ACTIVATION")
    _require(DDO_RUNTIME_EFFECT == "NONE", "DDO_RUNTIME_EFFECT")
    _require(SECOND_PROMOTION_AUTHORITY_CREATED is False, "DDO_SECOND_PROMOTION_AUTHORITY")
    _require(CAPTURE_RUNTIME_EFFECT == "OBSERVATION_ONLY", "DDO_CAPTURE_NOT_OBSERVATION_ONLY")
    _require(CAPTURE_FAILURE_CHANGES_DECISION is False, "DDO_CAPTURE_CHANGES_DECISION")
    _require(HOOK_PRESENCE_IS_NOT_AUTHORITY_GRANT is True, "HOOK_PRESENCE_TREATED_AS_GRANT")
    _require(CAPTURE_ADAPTER_PRESENT is True, "DDO_CAPTURE_ADAPTER_MISSING")
    _require(bool(IMPLEMENTED_CAPTURE_SEAMS_V0), "DDO_CAPTURE_SEAMS_MISSING")
    _require(PROMOTION_CONTROLLER_CODE_PRESENT is True, "DDO_PROMOTION_CONTROLLER_MISSING")
    _require(
        PROMOTION_ELIGIBILITY_COMPUTATION_ALLOWED is True,
        "DDO_ELIGIBILITY_COMPUTATION_MISSING",
    )
    _require(_ddo_does_not_import_learning_loop(), "DDO_IMPORTS_LEARNING_LOOP")
    _require(DDO_DOES_NOT_REPLACE_LEARNING_LOOP is True, "DDO_REPLACES_LEARNING_LOOP")
    _require(
        all(COMPARISON_AUTHORITY_INVARIANTS.values()),
        "COMPARISON_AUTHORITY_INVARIANTS_DRIFT",
    )
    _require(
        COMPARISON_AUTHORITY_INVARIANTS["comparison_does_not_promote"] is True,
        "COMPARISON_PROMOTES",
    )
    _require(
        PROMOTION_POLICY_DECISION_AUTHORITY_INVARIANTS["promotion_decision_is_descriptive_only"]
        is True,
        "COMPARISON_PROMOTION_DECISION_NOT_DESCRIPTIVE",
    )
    _require(
        COMPARISON_PROMOTION_DECISION_AUTHORITY_LEVEL == "NON_AUTHORITIZING_EVIDENCE_ONLY",
        "COMPARISON_PROMOTION_DECISION_AUTHORITY_LEVEL",
    )
    _require(
        "CAN_GRANT_AUTHORITY" in inspect.getsource(_authority_lease),
        "LEARNING_LOOP_CAN_GRANT_NOT_FORBIDDEN",
    )
    ledger_values = tuple(LEDGER_FAMILIES.values())
    _require(len(set(ledger_values)) == len(ledger_values), "LEDGER_FAMILIES_NOT_DISTINCT")
    _require(
        LEDGER_FAMILIES["ddo_ledger"] == SCHEMA_NAME_LEDGER_ENVELOPE,
        "DDO_LEDGER_FAMILY_DRIFT",
    )
    for consumer in SURFACE_M_CONSUMERS:
        _require((_REPO_ROOT / consumer).is_file(), f"SURFACE_M_CONSUMER_MISSING:{consumer}")
    order_clear, order_hits = _scan_order_submit_reachability()
    _require(order_clear, f"ORDER_SUBMIT_REACHABLE:{';'.join(order_hits)}")
    _require(LIVE_AUTHORIZED is False, "LIVE_AUTHORIZED")
    _require(CANARY_AUTHORIZED is False, "CANARY_AUTHORIZED")
    _require(TESTNET_AUTHORIZED is False, "TESTNET_AUTHORIZED")
    _require(ORDERS_ALLOWED is False, "ORDERS_ALLOWED")

    surface_o = _prove_surface_o_observation_only()
    surface_m = _prove_surface_m_pass_is_not_grant()
    ddo_eligibility = _prove_ddo_eligibility_is_not_grant()
    legacy = _prove_legacy_engine_ungranted()

    report = {
        "contract_id": CONTRACT_ID,
        "contract_version": CONTRACT_VERSION,
        "owner_go": OWNER_GO,
        "authority_effect": AUTHORITY_EFFECT,
        "can_grant_authority": CAN_GRANT_AUTHORITY,
        "contract_layers": CONTRACT_LAYERS,
        "learning_loop_role": LEARNING_LOOP_ALLOWED_ROLE,
        "surface_o_role": SURFACE_O_ROLE,
        "surface_m_role": SURFACE_M_ROLE,
        "legacy_promotion_engine_role": LEGACY_PROMOTION_ENGINE_ROLE,
        "ddo_role": DDO_ROLE,
        "productive_learning_authority": PRODUCTIVE_LEARNING_AUTHORITY,
        "productive_promotion_authority": PRODUCTIVE_PROMOTION_AUTHORITY,
        "second_promotion_authority_created": SECOND_PROMOTION_AUTHORITY_CREATED,
        "second_learning_authority_created": False,
        "ddo_does_not_replace_learning_loop": DDO_DOES_NOT_REPLACE_LEARNING_LOOP,
        "hook_presence_is_not_authority_grant": HOOK_PRESENCE_IS_NOT_AUTHORITY_GRANT,
        "ledger_families": dict(LEDGER_FAMILIES),
        "surface_o": dict(surface_o),
        "surface_m": dict(surface_m),
        "ddo_eligibility": dict(ddo_eligibility),
        "legacy_promotion_engine": dict(legacy),
        "live_authorized": LIVE_AUTHORIZED,
        "canary_authorized": CANARY_AUTHORIZED,
        "testnet_authorized": TESTNET_AUTHORIZED,
        "orders_allowed": ORDERS_ALLOWED,
        "order_submit_reachable_from_wp02": False,
        "status": "PASS",
    }
    return MappingProxyType(report)


__all__ = [
    "AUTHORITY_EFFECT",
    "CAN_GRANT_AUTHORITY",
    "CONTRACT_ID",
    "CONTRACT_LAYERS",
    "CONTRACT_VERSION",
    "DDO_ROLE",
    "LEARNING_LOOP_ALLOWED_ROLE",
    "LEGACY_PROMOTION_ENGINE_ROLE",
    "OfflineObservationProposalContractFenceError",
    "OWNER_GO",
    "PRODUCTIVE_LEARNING_AUTHORITY",
    "PRODUCTIVE_PROMOTION_AUTHORITY",
    "SURFACE_M_ROLE",
    "SURFACE_O_ROLE",
    "evaluate_offline_observation_proposal_contract_fences_v1",
]
