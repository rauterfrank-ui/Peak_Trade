"""Canonical Experiment Identity to Package-N I16 promotion admission tests."""

from __future__ import annotations

import ast
import copy
import hashlib
from pathlib import Path
from types import MappingProxyType
from typing import Any

import pytest

from src.experiments.canonical_experiment_identity_to_package_n_i16_promotion_admission_v1 import (
    ADMISSION_AUTHORITY,
    BOUNDED_AUTO_ALLOWED,
    CanonicalIdentityToPackageNI16AdmissionError,
    CanonicalIdentityToPackageNI16AdmissionRequestV1,
    PROMOTION_APPLY_ALLOWED,
    PROMOTION_AUTHORITY,
    REQUIRED_PROMOTION_MODE,
    STATUS_ADMITTED,
    STATUS_REJECTED_AMBIGUOUS_IDENTITY,
    STATUS_REJECTED_AUTHORITY_BOUNDARY,
    STATUS_REJECTED_HASH_REINTERPRETATION_REQUIRED,
    STATUS_REJECTED_INCOMPATIBLE_DIMENSION,
    STATUS_REJECTED_INCOMPLETE_IDENTITY,
    STATUS_REJECTED_INVALID_PACKAGE_N,
    STATUS_REJECTED_UNSUPPORTED_PROJECTION,
    evaluate_canonical_experiment_identity_to_package_n_i16_promotion_admission_v1,
)
from src.experiments.canonical_experiment_identity_v1 import (
    WORKING_TREE_CLEAN,
    CanonicalExperimentIdentityRequestV1,
    build_canonical_experiment_identity_v1,
)
from src.experiments.base import ExperimentConfig, ParamSweep
from src.experiments.experiment_identity_manifest_v1 import (
    PACKAGE_N_IDENTITY_COMPLETENESS,
    build_manifest,
)
from src.governance.promotion_loop.engine import apply_proposals_to_live_overrides
from src.governance.promotion_loop.models import (
    DecisionStatus,
    PromotionCandidate,
    PromotionDecision,
    PromotionProposal,
)
from src.governance.promotion_loop.policy import AutoApplyBounds, AutoApplyPolicy
from src.meta.learning_loop.models import ConfigPatch, PatchStatus

REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "experiments"
    / "canonical_experiment_identity_to_package_n_i16_promotion_admission_v1.py"
)
_GIT_SHA = "b506929832db11bf7cd5e8aa1c08156b72d82df1"
_STRATEGY = "ma_crossover"


def _digest(label: str) -> str:
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


def _phase1(**overrides: Any) -> MappingProxyType:
    payload: dict[str, Any] = {
        "git_sha": _GIT_SHA,
        "working_tree_status": WORKING_TREE_CLEAN,
        "strategy_identity": _STRATEGY,
        "strategy_params": {"slow": 50, "fast": 10},
        "dataset_digest": _digest("dataset"),
        "feature_pipeline_digest": _digest("features"),
        "fee_model_digest": _digest("fee"),
        "slippage_model_digest": _digest("slippage"),
        "funding_model_digest": _digest("funding"),
        "risk_policy_digest": _digest("risk"),
        "portfolio_digest": _digest("portfolio"),
        "split_policy_digest": _digest("split"),
        "market_context_contract_digest": _digest("market-context"),
        "bull_bear_logic_digest": _digest("bull-bear"),
        "state_switch_logic_digest": _digest("state-switch"),
        "survival_logic_digest": _digest("survival"),
        "suitability_logic_digest": _digest("suitability"),
        "double_play_logic_digest": _digest("double-play"),
        "entry_position_exit_logic_digest": _digest("entry-position-exit"),
        "seed": 7,
        "environment": {
            "python_version": "3.11.15",
            "python_implementation": "CPython",
        },
        "parent_lineage_ref": None,
        "dirty_paths_digest": None,
    }
    payload.update(overrides)
    return build_canonical_experiment_identity_v1(CanonicalExperimentIdentityRequestV1(**payload))


def _package_n(*, strategy_name: str = _STRATEGY) -> dict[str, Any]:
    return build_manifest(
        ExperimentConfig(
            name="MA Optimization",
            strategy_name=strategy_name,
            param_sweeps=[ParamSweep("fast", [5, 10])],
            symbols=["BTC/EUR"],
            timeframe="1h",
        )
    )


def _request(**overrides: Any) -> CanonicalIdentityToPackageNI16AdmissionRequestV1:
    payload: dict[str, Any] = {
        "phase1_identity": _phase1(),
        "package_n_manifest": _package_n(),
    }
    payload.update(overrides)
    return CanonicalIdentityToPackageNI16AdmissionRequestV1(**payload)


def test_admitted_keeps_package_n_id_and_attaches_research_parent() -> None:
    package_n = _package_n()
    phase1 = _phase1()
    original_id = package_n["experiment_identity_id"]
    result = evaluate_canonical_experiment_identity_to_package_n_i16_promotion_admission_v1(
        _request(phase1_identity=phase1, package_n_manifest=package_n)
    )
    assert result["status"] == STATUS_ADMITTED
    assert result["rejection_reason"] is None
    assert result["package_n_experiment_identity_id"] == original_id
    assert result["package_n_experiment_identity_id_mutated"] is False
    assert result["hash_reinterpreted"] is False
    assert result["research_evidence_parent_identity_digest"] == phase1["identity_digest"]
    assert (
        result["research_evidence_parent_integrity_sha256"] == phase1["integrity"]["content_sha256"]
    )
    assert result["i16_assessment_consumable"] is True
    assert result["package_n_identity_completeness"] == PACKAGE_N_IDENTITY_COMPLETENESS
    join = result["i16_join"]
    assert join is not None
    assert join["experiment_identity_id"] == original_id
    assert join["evidence_ref"] == phase1["integrity"]["content_sha256"]
    assert result["authority_invariants"]["promotion_apply_allowed"] is False
    assert result["authority_invariants"]["promotion_authority"] == PROMOTION_AUTHORITY
    assert PROMOTION_APPLY_ALLOWED is False
    assert BOUNDED_AUTO_ALLOWED is False
    assert ADMISSION_AUTHORITY == "RESEARCH_EVIDENCE_PARENT_ONLY"


def test_determinism_same_inputs_same_admission() -> None:
    first = dict(
        evaluate_canonical_experiment_identity_to_package_n_i16_promotion_admission_v1(_request())
    )
    second = dict(
        evaluate_canonical_experiment_identity_to_package_n_i16_promotion_admission_v1(_request())
    )
    assert first == second
    assert first["integrity"]["content_sha256"] == second["integrity"]["content_sha256"]


def test_package_n_hash_not_mutated_when_inputs_copied() -> None:
    package_n = _package_n()
    original = copy.deepcopy(package_n)
    evaluate_canonical_experiment_identity_to_package_n_i16_promotion_admission_v1(
        _request(package_n_manifest=package_n)
    )
    assert package_n == original
    assert package_n["experiment_identity_id"] == original["experiment_identity_id"]


def test_strategy_mismatch_rejected() -> None:
    result = evaluate_canonical_experiment_identity_to_package_n_i16_promotion_admission_v1(
        _request(package_n_manifest=_package_n(strategy_name="macd"))
    )
    assert result["status"] == STATUS_REJECTED_INCOMPATIBLE_DIMENSION
    assert result["i16_assessment_consumable"] is False
    assert result["i16_join"] is None


def test_claimed_complete_projection_rejected() -> None:
    result = evaluate_canonical_experiment_identity_to_package_n_i16_promotion_admission_v1(
        _request(claimed_package_n_is_phase1_complete=True)
    )
    assert result["status"] == STATUS_REJECTED_UNSUPPORTED_PROJECTION
    assert result["i16_assessment_consumable"] is False


def test_recomputed_package_n_id_rejected_even_if_equal() -> None:
    package_n = _package_n()
    result = evaluate_canonical_experiment_identity_to_package_n_i16_promotion_admission_v1(
        _request(
            package_n_manifest=package_n,
            claimed_recomputed_package_n_id=package_n["experiment_identity_id"],
        )
    )
    assert result["status"] == STATUS_REJECTED_HASH_REINTERPRETATION_REQUIRED
    assert result["i16_assessment_consumable"] is False


def test_requested_apply_rejected() -> None:
    result = evaluate_canonical_experiment_identity_to_package_n_i16_promotion_admission_v1(
        _request(requested_apply=True)
    )
    assert result["status"] == STATUS_REJECTED_AUTHORITY_BOUNDARY
    assert result["i16_assessment_consumable"] is False


def test_bounded_auto_mode_rejected() -> None:
    result = evaluate_canonical_experiment_identity_to_package_n_i16_promotion_admission_v1(
        _request(requested_promotion_mode="bounded_auto")
    )
    assert result["status"] == STATUS_REJECTED_AUTHORITY_BOUNDARY
    assert result["requested_promotion_mode"] == "bounded_auto"
    assert result["required_promotion_mode"] == REQUIRED_PROMOTION_MODE


def test_incomplete_phase1_rejected() -> None:
    phase1 = dict(_phase1())
    phase1["completeness"] = "INCOMPLETE"
    result = evaluate_canonical_experiment_identity_to_package_n_i16_promotion_admission_v1(
        _request(phase1_identity=phase1)
    )
    assert result["status"] == STATUS_REJECTED_INCOMPLETE_IDENTITY
    assert result["i16_assessment_consumable"] is False


def test_invalid_package_n_rejected() -> None:
    result = evaluate_canonical_experiment_identity_to_package_n_i16_promotion_admission_v1(
        _request(package_n_manifest={"experiment_identity_id": "not-a-hash"})
    )
    assert result["status"] == STATUS_REJECTED_INVALID_PACKAGE_N
    assert result["i16_assessment_consumable"] is False


def test_malformed_request_raises() -> None:
    with pytest.raises(CanonicalIdentityToPackageNI16AdmissionError, match="mapping"):
        evaluate_canonical_experiment_identity_to_package_n_i16_promotion_admission_v1(
            CanonicalIdentityToPackageNI16AdmissionRequestV1(
                phase1_identity="not-a-mapping",  # type: ignore[arg-type]
                package_n_manifest=_package_n(),
            )
        )


def test_identity_planes_remain_distinct_on_admit() -> None:
    phase1 = _phase1()
    package_n = _package_n()
    result = evaluate_canonical_experiment_identity_to_package_n_i16_promotion_admission_v1(
        _request(phase1_identity=phase1, package_n_manifest=package_n)
    )
    assert result["status"] == STATUS_ADMITTED
    assert phase1["identity_digest"] != package_n["experiment_identity_id"]
    assert phase1["schema_version"] != package_n["schema_version"]
    assert phase1["identity_domain"] != package_n["identity_domain"]


def test_frozen_result_is_immutable() -> None:
    result = evaluate_canonical_experiment_identity_to_package_n_i16_promotion_admission_v1(
        _request()
    )
    assert isinstance(result, MappingProxyType)
    with pytest.raises(TypeError):
        result["status"] = "PROMOTED"  # type: ignore[index]


def test_module_does_not_import_apply_or_live_paths() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
    forbidden = {
        "src.core.peak_config",
        "src.governance.promotion_loop.engine",
        "src.execution",
        "scripts.run_learning_apply_cycle",
        "src.live",
        "src.trading",
    }
    assert imported.isdisjoint(forbidden)
    assert "apply_proposals_to_live_overrides" not in source
    assert "bounded_auto" in source
    assert BOUNDED_AUTO_ALLOWED is False


def test_phase0b_apply_firewall_still_fail_closed(tmp_path: Path) -> None:
    patch = ConfigPatch(
        id="patch-leverage-admission-regression",
        target="portfolio.leverage",
        old_value=1.0,
        new_value=1.75,
        status=PatchStatus.APPLIED_OFFLINE,
    )
    candidate = PromotionCandidate(
        patch=patch,
        eligible_for_live=True,
        tags=["leverage"],
    )
    decision = PromotionDecision(
        candidate=candidate,
        status=DecisionStatus.ACCEPTED_FOR_PROPOSAL,
        reasons=["admission contract must not reopen apply"],
    )
    proposal = PromotionProposal(
        proposal_id="admission_apply_regression",
        title="fail-closed apply regression",
        description="bounded_auto must still not write",
        decisions=[decision],
        meta={},
    )
    live_path = tmp_path / "auto.toml"
    policy = AutoApplyPolicy(
        mode="bounded_auto",
        leverage_bounds=AutoApplyBounds(min_value=1.0, max_value=2.0, max_step=1.0),
    )
    written = apply_proposals_to_live_overrides(
        [proposal],
        policy=policy,
        live_override_path=live_path,
    )
    assert written is None
    assert not live_path.exists()
