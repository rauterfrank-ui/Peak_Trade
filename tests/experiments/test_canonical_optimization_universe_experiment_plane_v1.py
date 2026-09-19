"""Contract tests for optimization universe M4 experiment plane."""

from __future__ import annotations

import ast
import hashlib
from pathlib import Path
from typing import Any, Mapping

import pytest

from src.experiments.canonical_advanced_search_v1 import SearchAxisV1, SearchSpaceV1
from src.experiments.canonical_comparison_ssot_v1 import ComparisonCandidateV1
from src.experiments.canonical_experiment_identity_v1 import (
    CanonicalExperimentIdentityRequestV1,
    WORKING_TREE_CLEAN,
    build_canonical_experiment_identity_v1,
)
from src.experiments.canonical_experiment_memory_v1 import derive_experiment_id_v1
from src.experiments.canonical_optimization_universe_experiment_plane_v1 import (
    AUTHORIZED_PRODUCTIVE_SURFACES,
    CANDIDATE_DISPOSITION,
    PLANE_STATUS_COMPLETE,
    PLANE_STATUS_REJECTED_INPUT,
    PLANE_STATUS_REJECTED_STALE_INPUT,
    PROPOSAL_DISPOSITION,
    ZERO_AUTHORIZED_PRODUCTIVE_TARGETS,
    OptimizationUniverseExperimentPlaneRequestV1,
    run_optimization_universe_experiment_plane_v1,
)
from src.experiments.canonical_optimization_universe_learning_input_v1 import (
    SCHEMA_VERSION as LEARNING_INPUT_SCHEMA_VERSION,
)
from src.experiments.canonical_robustness_suite_v1 import METRIC_DEFINITION_VERSION
from src.learning.deterministic_decision_outcome_v0.learning_evidence_export_v1 import (
    export_learning_evidence_from_state_v1,
)
from tests.learning.test_learning_evidence_export_v1 import _learning_state

REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = (
    REPO_ROOT / "src" / "experiments" / "canonical_optimization_universe_experiment_plane_v1.py"
)
_GIT_SHA = "c889577bef56300f74039d921472f0638cbb8810"[:40]
_CREATED_AT = "2026-09-19T12:00:00Z"
_TIME_HORIZON = {"start": "2020-01-01T00:00:00Z", "end": "2024-12-31T00:00:00Z"}


def _digest(label: str) -> str:
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


def _identity_request(**overrides: Any) -> CanonicalExperimentIdentityRequestV1:
    payload: dict[str, Any] = {
        "git_sha": _GIT_SHA,
        "working_tree_status": WORKING_TREE_CLEAN,
        "strategy_identity": "offline_plane.synthetic.v1",
        "strategy_params": {"fast": 10, "slow": 50},
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
        "seed": 19,
        "environment": {
            "python_version": "3.11.15",
            "python_implementation": "CPython",
        },
        "parent_lineage_ref": None,
        "dirty_paths_digest": None,
    }
    payload.update(overrides)
    return CanonicalExperimentIdentityRequestV1(**payload)


def _champion(**overrides: Any) -> ComparisonCandidateV1:
    identity = build_canonical_experiment_identity_v1(_identity_request())
    experiment_id = derive_experiment_id_v1(str(identity["identity_digest"]))
    payload: dict[str, Any] = {
        "experiment_identity": identity,
        "robustness_suite_version": "canonical_robustness_suite_v1",
        "metric_definitions": METRIC_DEFINITION_VERSION,
        "time_horizon": dict(_TIME_HORIZON),
        "market_universe": ["SYNTHETIC-OFFLINE-RESEARCH-ONLY"],
        "experiment_id": experiment_id,
        "evidence_refs": (),
    }
    payload.update(overrides)
    return ComparisonCandidateV1(**payload)


def _plane_request(
    evidence: Mapping[str, Any], **overrides: Any
) -> OptimizationUniverseExperimentPlaneRequestV1:
    payload: dict[str, Any] = {
        "learning_evidence": evidence,
        "identity_template": _identity_request(),
        "search_space": SearchSpaceV1(
            search_space_id="search.offline_plane.v1",
            axes=(SearchAxisV1(name="fast", values=(10, 15)),),
        ),
        "champion": _champion(),
        "champion_score": 1.0,
        "challenger_score": 1.05,
        "created_at": _CREATED_AT,
        "search_seed": 19,
        "search_budget": 1,
    }
    payload.update(overrides)
    return OptimizationUniverseExperimentPlaneRequestV1(**payload)


def test_offline_plane_chain_complete(tmp_path: Path) -> None:
    state = _learning_state(tmp_path)
    evidence = export_learning_evidence_from_state_v1(state)
    first = run_optimization_universe_experiment_plane_v1(_plane_request(evidence))
    second = run_optimization_universe_experiment_plane_v1(_plane_request(evidence))
    assert first["status"] == PLANE_STATUS_COMPLETE
    assert first["plane_identity"] == second["plane_identity"]
    assert first["authorized_productive_surfaces"] == 0
    assert ZERO_AUTHORIZED_PRODUCTIVE_TARGETS is True
    chain = first["chain"]
    assert chain is not None
    assert chain["offline_research_context"]["envelope_not_productive_authorization"] is True
    assert chain["selected_candidate"]["disposition"] == CANDIDATE_DISPOSITION
    assert chain["proposal"]["disposition"] == PROPOSAL_DISPOSITION
    assert chain["proposal"]["promotion_authority"] == "NONE"
    assert chain["robustness_evidence_digest"] is not None


def test_rejects_stale_learning_input_schema(tmp_path: Path) -> None:
    state = _learning_state(tmp_path)
    evidence = export_learning_evidence_from_state_v1(state)
    result = run_optimization_universe_experiment_plane_v1(
        _plane_request(
            evidence,
            learning_input_schema_version="canonical_optimization_universe_learning_input_v0",
        )
    )
    assert result["status"] == PLANE_STATUS_REJECTED_STALE_INPUT


def test_rejects_invalid_learning_evidence() -> None:
    result = run_optimization_universe_experiment_plane_v1(
        _plane_request({"schema_version": "invalid"})
    )
    assert result["status"] == PLANE_STATUS_REJECTED_INPUT


def test_learning_input_schema_default_matches_contract(tmp_path: Path) -> None:
    state = _learning_state(tmp_path)
    evidence = export_learning_evidence_from_state_v1(state)
    request = _plane_request(evidence)
    assert request.learning_input_schema_version == LEARNING_INPUT_SCHEMA_VERSION


def test_no_promotion_trading_or_execution_imports() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
    forbidden_imports = {
        "src.core.peak_config",
        "src.governance.promotion_loop",
        "src.governance.promotion_loop.engine",
        "src.execution",
        "src.live",
        "src.trading",
        "src.trading.master_v2",
        "src.experiments.canonical_automated_offline_research_loop_v1",
        "src.experiments.canonical_portfolio_learning_v1",
        "src.experiments.canonical_regime_aware_evaluation_v1",
        "src.meta.learning_loop.bridge",
    }
    assert forbidden_imports.isdisjoint(imported)
    assert AUTHORIZED_PRODUCTIVE_SURFACES == 0
    for token in ("submit_order(", "promote_to_live(", "LIVE_AUTHORIZED"):
        assert token not in source
