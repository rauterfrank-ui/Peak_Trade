"""Scoped F1/M9 optimization productive join max-build tests."""

from __future__ import annotations

import json
from pathlib import Path

from src.experiments.canonical_f2_research_backtest_cost_grid_optimizable_surface_v1 import (
    SURFACE_ID as F2_SURFACE_ID,
)
from src.experiments.canonical_f5_fresh_futures_input_freshness_optimizable_surface_v1 import (
    SURFACE_ID as F5_FRESH_SURFACE_ID,
)
from src.governance.m9_volatility_numeric_max_age_numeric_productive_target_v1 import (
    OPTIMIZATION_SURFACE_ID,
    PRODUCTIVE_TARGET_ID,
)
from src.governance.v32_d28_d29_scoped_optimization_productive_join_f1_m9_closure_v1 import (
    BLOCKER_EDGE,
    MINIMAL_NEXT_OWNER_POLICY_QUESTION,
    NEXT_TRUE_BLOCKER,
    prove_v32_d28_d29_scoped_optimization_productive_join_f1_m9_max_build_v1,
)
from src.governance.v32_d28_d29_scoped_optimization_productive_join_policy_v1 import (
    DECISION_CONFIG,
    REGISTRY_CONFIG,
    ScopedJoinResolutionStatusV1,
    ScopedOptimizationProductiveJoinScopeKeyV1,
    WORKPACKAGE_ID,
    adjudicate_global_optimization_universe_join_boolean_v1,
    build_canonical_f1_m9_scope_key_v1,
    compute_scoped_join_registry_digest_v1,
    load_scoped_join_registry_v1,
    prove_scoped_join_policy_invariants_v1,
    resolve_scoped_optimization_productive_join_v1,
)
from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.constants_v1 import (
    PRODUCTIVE_NUMERIC_VALUES_SET,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_max_build_proof_and_decision() -> None:
    assert prove_v32_d28_d29_scoped_optimization_productive_join_f1_m9_max_build_v1(
        repo_root=REPO_ROOT
    )
    decision = json.loads((REPO_ROOT / DECISION_CONFIG).read_text(encoding="utf-8"))
    assert decision["workpackage_id"] == WORKPACKAGE_ID
    assert decision["scoped_join_policy_status"] == "PROVEN_CURRENT"
    assert decision["global_join_boolean_status"] == "LEGACY_COMPATIBILITY_ONLY_UNCHANGED"
    assert decision["optimization_universe_join_authorized_changed"] is False
    assert decision["d28_d29_closure_proven"] is True
    assert decision["next_true_blocker"] == NEXT_TRUE_BLOCKER
    assert decision["blocker_edge"] == BLOCKER_EDGE
    assert decision["minimal_next_owner_policy_question"] == MINIMAL_NEXT_OWNER_POLICY_QUESTION
    assert decision["productive_numeric_values_set_current"] == 0
    assert decision["promotion_authorized"] is False
    assert decision["productive_apply_authorized"] is False
    assert decision["global_optimization_join_authorized"] is False
    assert decision["trading_decision_authority_changed"] is False
    assert decision["external_effect_authorized"] is False


def test_f1_m9_pair_authorized_with_registry_digest() -> None:
    registry = load_scoped_join_registry_v1(repo_root=REPO_ROOT)
    digest = registry["registry_digest"]
    key = build_canonical_f1_m9_scope_key_v1()
    assert key.surface_id == OPTIMIZATION_SURFACE_ID
    assert key.productive_target_id == PRODUCTIVE_TARGET_ID
    result = resolve_scoped_optimization_productive_join_v1(
        key,
        registry=registry,
        expected_registry_digest=str(digest),
    )
    assert result.status == ScopedJoinResolutionStatusV1.SCOPED_JOIN_AUTHORIZED
    assert result.scope_pair_id == "F1-M9-VOLATILITY-MAX-AGE-SECONDS"
    assert result.lineage_refs is not None
    assert "productive_consumer" in result.lineage_refs


def test_registry_digest_stable() -> None:
    raw = json.loads((REPO_ROOT / REGISTRY_CONFIG).read_text(encoding="utf-8"))
    digest = compute_scoped_join_registry_digest_v1(raw)
    loaded = load_scoped_join_registry_v1(repo_root=REPO_ROOT)
    assert loaded["registry_digest"] == digest


def test_negative_isolation_f2_f5_and_unknown() -> None:
    registry = load_scoped_join_registry_v1(repo_root=REPO_ROOT)
    for surface in (F2_SURFACE_ID, F5_FRESH_SURFACE_ID):
        denied = resolve_scoped_optimization_productive_join_v1(
            ScopedOptimizationProductiveJoinScopeKeyV1(
                surface_id=surface,
                productive_target_id=PRODUCTIVE_TARGET_ID,
            ),
            registry=registry,
        )
        assert denied.status == ScopedJoinResolutionStatusV1.SCOPED_JOIN_DENIED_FAIL_CLOSED
    unknown = resolve_scoped_optimization_productive_join_v1(
        ScopedOptimizationProductiveJoinScopeKeyV1(
            surface_id="UNKNOWN_SURFACE_V1",
            productive_target_id=PRODUCTIVE_TARGET_ID,
        ),
        registry=registry,
    )
    assert unknown.status == ScopedJoinResolutionStatusV1.SCOPED_JOIN_UNKNOWN_FAIL_CLOSED
    wrong_target = resolve_scoped_optimization_productive_join_v1(
        ScopedOptimizationProductiveJoinScopeKeyV1(
            surface_id=OPTIMIZATION_SURFACE_ID,
            productive_target_id="peak_trade.governance.productive_target.unknown/v1",
        ),
        registry=registry,
    )
    assert wrong_target.status == ScopedJoinResolutionStatusV1.SCOPED_JOIN_DENIED_FAIL_CLOSED


def test_global_boolean_does_not_authorize_scoped_join() -> None:
    learning = json.loads(
        (
            REPO_ROOT
            / "config/governance/learning_outcome_evidence_ingest_and_state_decision_v1.json"
        ).read_text(encoding="utf-8")
    )
    assert learning["optimization_universe_join_authorized"] is False
    adj = adjudicate_global_optimization_universe_join_boolean_v1(
        learning_decision_value=learning["optimization_universe_join_authorized"]
    )
    assert adj["may_derive_scoped_productive_join_authority"] is False
    assert adj["scoped_registry_is_pair_authority_ssot"] is True
    assert prove_scoped_join_policy_invariants_v1(repo_root=REPO_ROOT)
    assert PRODUCTIVE_NUMERIC_VALUES_SET == 0
