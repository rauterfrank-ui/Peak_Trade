"""Identity-bound offline observation binding contract tests."""

from __future__ import annotations

import ast
import hashlib
from pathlib import Path
from types import MappingProxyType
from typing import Any

import pytest

from src.experiments.canonical_automated_offline_research_loop_v1 import (
    OfflineExperimentObservationsV1,
    RESEARCH_LOOP_HAS_RUNTIME_AUTHORITY,
)
from src.experiments.canonical_experiment_identity_to_package_n_i16_promotion_admission_v1 import (
    STATUS_ADMITTED,
    CanonicalIdentityToPackageNI16AdmissionRequestV1,
    evaluate_canonical_experiment_identity_to_package_n_i16_promotion_admission_v1,
)
from src.experiments.canonical_experiment_identity_v1 import (
    WORKING_TREE_CLEAN,
    CanonicalExperimentIdentityRequestV1,
    build_canonical_experiment_identity_v1,
    validate_canonical_experiment_identity_v1,
)
from src.experiments.canonical_experiment_memory_store_v1 import CanonicalExperimentMemoryStoreV1
from src.experiments.canonical_experiment_memory_v1 import (
    EXPERIMENT_MEMORY_HAS_RUNTIME_AUTHORITY,
    derive_experiment_id_v1,
    validate_canonical_experiment_memory_record_v1,
)
from src.experiments.canonical_identity_bound_offline_observation_binding_v1 import (
    BOUNDED_AUTO_ALLOWED,
    CanonicalIdentityBoundOfflineObservationBindingError,
    CanonicalIdentityBoundOfflineObservationBindingRequestV1,
    NEW_RUNNER_ARCHITECTURE,
    OBSERVATION_OWNER_OFFLINE_EXPERIMENT_OBSERVATIONS_V1,
    PROMOTION_APPLY_ALLOWED,
    PROMOTION_AUTHORITY,
    STATUS_BOUND,
    STATUS_REJECTED_AUTHORITY_BOUNDARY,
    STATUS_REJECTED_DIVERGENT_DUPLICATE,
    STATUS_REJECTED_EXPERIMENT_ID_MISMATCH,
    STATUS_REJECTED_HASH_REINTERPRETATION_REQUIRED,
    STATUS_REJECTED_IDENTITY_MISMATCH,
    STATUS_REJECTED_INCOMPLETE_IDENTITY,
    STATUS_REJECTED_LINEAGE_DIGEST_MISMATCH,
    STATUS_REJECTED_MISSING_DIMENSION,
    STATUS_REJECTED_UNSUPPORTED_PROJECTION,
    STATUS_REJECTED_WRONG_OBSERVATION_OWNER,
    bind_canonical_identity_bound_offline_observation_v1,
)
from src.experiments.base import ExperimentConfig, ParamSweep
from src.experiments.experiment_identity_manifest_v1 import build_manifest
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
    REPO_ROOT / "src" / "experiments" / "canonical_identity_bound_offline_observation_binding_v1.py"
)
_GIT_SHA = "57c8c7d83aff0892ffedea54257321e841389c2a"
_STRATEGY = "ma_crossover.v1"
_CREATED_AT = "2026-08-18T17:00:00Z"


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


def _observations(**overrides: Any) -> OfflineExperimentObservationsV1:
    payload: dict[str, Any] = {
        "metrics": {"sharpe": 1.25, "max_drawdown": -0.12},
        "robustness_results": {"walk_forward": {"passed": True, "folds": 4}},
        "regime_results": {"high_vol": {"sharpe": 0.4}},
        "artifacts": [
            {
                "kind": "REPO_RELATIVE",
                "ref": "docs/ops/specs/CANONICAL_EXPERIMENT_IDENTITY_V1.md",
                "digest": _digest("artifact"),
                "media_type": "text/markdown",
            }
        ],
        "robustness_observations": {"sample_size": 32},
    }
    payload.update(overrides)
    return OfflineExperimentObservationsV1(**payload)


def _request(**overrides: Any) -> CanonicalIdentityBoundOfflineObservationBindingRequestV1:
    identity = overrides.pop("phase1_identity", _phase1())
    experiment_id = (
        derive_experiment_id_v1(str(identity["identity_digest"]))
        if isinstance(identity, dict) or hasattr(identity, "__getitem__")
        else None
    )
    payload: dict[str, Any] = {
        "phase1_identity": identity,
        "observation_owner": OBSERVATION_OWNER_OFFLINE_EXPERIMENT_OBSERVATIONS_V1,
        "observations": _observations(),
        "claimed_identity_digest": (None if identity is None else str(identity["identity_digest"])),
        "claimed_experiment_id": experiment_id,
        "claimed_parent_lineage_ref": (
            None
            if identity is None
            else identity.get("parent_lineage", {}).get("parent_lineage_ref")
        ),
        "hypothesis_id": "hyp.ma-crossover.v1",
        "hypothesis_fingerprint": _digest("hypothesis"),
        "strategy_family": "ma_crossover",
        "created_at": _CREATED_AT,
    }
    payload.update(overrides)
    return CanonicalIdentityBoundOfflineObservationBindingRequestV1(**payload)


def test_happy_path_binds_complete_identity_to_phase2_memory() -> None:
    identity = _phase1()
    result = bind_canonical_identity_bound_offline_observation_v1(
        _request(phase1_identity=identity)
    )
    assert result["status"] == STATUS_BOUND
    assert result["bound"] is True
    assert result["rejection_reason"] is None
    assert result["observation_owner"] == OBSERVATION_OWNER_OFFLINE_EXPERIMENT_OBSERVATIONS_V1
    assert result["identity_digest"] == identity["identity_digest"]
    assert result["experiment_id"] == derive_experiment_id_v1(str(identity["identity_digest"]))
    observation = result["identity_bound_observation"]
    assert observation is not None
    assert observation["identity_digest"] == identity["identity_digest"]
    assert observation["experiment_id"] == result["experiment_id"]
    record = result["experiment_record"]
    assert record is not None
    validate_canonical_experiment_memory_record_v1(record)
    assert record["experiment_identity"]["identity_digest"] == identity["identity_digest"]
    assert result["authority_invariants"]["promotion_apply_allowed"] is False
    assert result["authority_invariants"]["bounded_auto_allowed"] is False
    assert result["authority_invariants"]["runtime_authority_effect"] is False
    assert result["phase10_runtime_authority"] is False
    assert NEW_RUNNER_ARCHITECTURE is False
    assert PROMOTION_APPLY_ALLOWED is False
    assert BOUNDED_AUTO_ALLOWED is False
    assert PROMOTION_AUTHORITY == "NONE"


def test_incomplete_identity_rejected() -> None:
    phase1 = dict(_phase1())
    phase1["completeness"] = "INCOMPLETE"
    result = bind_canonical_identity_bound_offline_observation_v1(_request(phase1_identity=phase1))
    assert result["status"] == STATUS_REJECTED_INCOMPLETE_IDENTITY
    assert result["bound"] is False
    assert result["experiment_record"] is None


def test_missing_identity_rejected() -> None:
    result = bind_canonical_identity_bound_offline_observation_v1(
        _request(
            phase1_identity=None,
            claimed_identity_digest=_digest("missing"),
            claimed_experiment_id=_digest("missing-id"),
        )
    )
    assert result["status"] == STATUS_REJECTED_MISSING_DIMENSION
    assert result["bound"] is False


def test_identity_mismatch_rejected() -> None:
    result = bind_canonical_identity_bound_offline_observation_v1(
        _request(claimed_identity_digest=_digest("other-identity"))
    )
    assert result["status"] == STATUS_REJECTED_IDENTITY_MISMATCH
    assert result["bound"] is False


def test_experiment_id_mismatch_rejected() -> None:
    result = bind_canonical_identity_bound_offline_observation_v1(
        _request(claimed_experiment_id=_digest("unrelated-experiment"))
    )
    assert result["status"] == STATUS_REJECTED_EXPERIMENT_ID_MISMATCH
    assert result["bound"] is False


def test_lineage_mismatch_rejected() -> None:
    result = bind_canonical_identity_bound_offline_observation_v1(
        _request(claimed_parent_lineage_ref="parent.other")
    )
    assert result["status"] == STATUS_REJECTED_LINEAGE_DIGEST_MISMATCH
    assert result["bound"] is False


def test_digest_mismatch_rejected() -> None:
    result = bind_canonical_identity_bound_offline_observation_v1(
        _request(claimed_dataset_digest=_digest("other-dataset"))
    )
    assert result["status"] == STATUS_REJECTED_LINEAGE_DIGEST_MISMATCH
    assert result["bound"] is False


def test_observation_bound_to_wrong_owner_rejected() -> None:
    for owner in (
        "RUN_SUMMARY",
        "PACKAGE_N_EXPERIMENT_IDENTITY_MANIFEST",
        "LIVE_SESSION_REGISTRY",
        "ECONOMIC_VIABILITY_EVIDENCE_V1",
    ):
        result = bind_canonical_identity_bound_offline_observation_v1(
            _request(observation_owner=owner)
        )
        assert result["status"] == STATUS_REJECTED_WRONG_OBSERVATION_OWNER
        assert result["bound"] is False
        assert result["experiment_record"] is None


def test_divergent_duplicate_remains_fail_closed(tmp_path: Path) -> None:
    store = CanonicalExperimentMemoryStoreV1(tmp_path / "memory")
    identity = _phase1()
    first = bind_canonical_identity_bound_offline_observation_v1(
        _request(phase1_identity=identity, experiment_memory_store=store)
    )
    assert first["status"] == STATUS_BOUND
    identical = bind_canonical_identity_bound_offline_observation_v1(
        _request(phase1_identity=identity, experiment_memory_store=store)
    )
    assert identical["status"] == STATUS_BOUND
    assert identical["persist"]["experiment_record_id"] == first["experiment_id"]
    divergent = bind_canonical_identity_bound_offline_observation_v1(
        _request(
            phase1_identity=identity,
            observations=_observations(metrics={"sharpe": 0.1, "max_drawdown": -0.5}),
            experiment_memory_store=store,
        )
    )
    assert divergent["status"] == STATUS_REJECTED_DIVERGENT_DUPLICATE
    assert divergent["bound"] is False
    stored = store.get(str(first["experiment_id"]))
    assert stored["metrics"]["sharpe"] == 1.25


def test_determinism_same_inputs_same_binding() -> None:
    first = dict(bind_canonical_identity_bound_offline_observation_v1(_request()))
    second = dict(bind_canonical_identity_bound_offline_observation_v1(_request()))
    assert first == second
    assert first["integrity"]["content_sha256"] == second["integrity"]["content_sha256"]


def test_no_apply_or_bounded_auto_capability() -> None:
    apply_result = bind_canonical_identity_bound_offline_observation_v1(
        _request(requested_apply=True)
    )
    assert apply_result["status"] == STATUS_REJECTED_AUTHORITY_BOUNDARY
    auto_result = bind_canonical_identity_bound_offline_observation_v1(
        _request(requested_bounded_auto=True)
    )
    assert auto_result["status"] == STATUS_REJECTED_AUTHORITY_BOUNDARY
    assert PROMOTION_APPLY_ALLOWED is False
    assert BOUNDED_AUTO_ALLOWED is False


def test_legacy_complete_claim_and_hash_reinterpretation_rejected() -> None:
    legacy = bind_canonical_identity_bound_offline_observation_v1(
        _request(claimed_legacy_is_phase1_complete=True)
    )
    assert legacy["status"] == STATUS_REJECTED_UNSUPPORTED_PROJECTION
    identity = _phase1()
    reinterpreted = bind_canonical_identity_bound_offline_observation_v1(
        _request(
            phase1_identity=identity,
            claimed_recomputed_identity_digest=str(identity["identity_digest"]),
        )
    )
    assert reinterpreted["status"] == STATUS_REJECTED_HASH_REINTERPRETATION_REQUIRED
    experiment_id = derive_experiment_id_v1(str(identity["identity_digest"]))
    recomputed_id = bind_canonical_identity_bound_offline_observation_v1(
        _request(
            phase1_identity=identity,
            claimed_recomputed_experiment_id=experiment_id,
        )
    )
    assert recomputed_id["status"] == STATUS_REJECTED_HASH_REINTERPRETATION_REQUIRED


def test_identity_not_mutated_when_inputs_copied() -> None:
    identity = _phase1()
    digest = identity["identity_digest"]
    integrity = identity["integrity"]["content_sha256"]
    bind_canonical_identity_bound_offline_observation_v1(_request(phase1_identity=identity))
    assert identity["identity_digest"] == digest
    assert identity["integrity"]["content_sha256"] == integrity


def test_malformed_observations_raise() -> None:
    with pytest.raises(CanonicalIdentityBoundOfflineObservationBindingError, match="observations"):
        bind_canonical_identity_bound_offline_observation_v1(
            _request(observations="not-observations")
        )


def test_frozen_result_is_immutable() -> None:
    result = bind_canonical_identity_bound_offline_observation_v1(_request())
    assert isinstance(result, MappingProxyType)
    with pytest.raises(TypeError):
        result["status"] = "PROMOTED"  # type: ignore[index]


def test_no_runtime_authority_and_existing_contracts_remain_compatible() -> None:
    identity = _phase1()
    validate_canonical_experiment_identity_v1(identity)
    result = bind_canonical_identity_bound_offline_observation_v1(
        _request(phase1_identity=identity)
    )
    assert result["status"] == STATUS_BOUND
    validate_canonical_experiment_memory_record_v1(result["experiment_record"])
    assert RESEARCH_LOOP_HAS_RUNTIME_AUTHORITY is False
    assert EXPERIMENT_MEMORY_HAS_RUNTIME_AUTHORITY is False
    package_n = build_manifest(
        ExperimentConfig(
            name="MA Optimization",
            strategy_name="ma_crossover.v1",
            param_sweeps=[ParamSweep("fast", [5, 10])],
            symbols=["BTC/EUR"],
            timeframe="1h",
        )
    )
    admission = evaluate_canonical_experiment_identity_to_package_n_i16_promotion_admission_v1(
        CanonicalIdentityToPackageNI16AdmissionRequestV1(
            phase1_identity=identity,
            package_n_manifest=package_n,
        )
    )
    assert admission["status"] == STATUS_ADMITTED
    assert admission["package_n_experiment_identity_id"] == package_n["experiment_identity_id"]
    assert result["experiment_id"] != package_n["experiment_identity_id"]
    assert result["identity_reinterpreted"] is False
    assert result["package_n_experiment_identity_id_mutated"] is False


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
        "src.experiments.canonical_automated_offline_research_loop_v1",
        "src.experiments.experiment_identity_manifest_v1",
        "src.experiments.canonical_experiment_identity_to_package_n_i16_promotion_admission_v1",
    }
    assert imported.isdisjoint(forbidden)
    assert "apply_proposals_to_live_overrides" not in source
    assert "run_canonical_automated_offline_research_loop_v1" not in source
    assert BOUNDED_AUTO_ALLOWED is False
    assert NEW_RUNNER_ARCHITECTURE is False


def test_phase0b_apply_firewall_still_fail_closed(tmp_path: Path) -> None:
    patch = ConfigPatch(
        id="patch-leverage-observation-binding-regression",
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
        reasons=["observation binding must not reopen apply"],
    )
    proposal = PromotionProposal(
        proposal_id="observation_binding_apply_regression",
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
