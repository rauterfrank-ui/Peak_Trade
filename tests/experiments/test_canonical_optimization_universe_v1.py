"""Contract tests for optimization universe v1 foundation."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from src.experiments.canonical_optimization_universe_learning_input_v1 import (
    SCHEMA_VERSION as LEARNING_INPUT_SCHEMA_VERSION,
    STATUS_ACCEPTED_OFFLINE_RESEARCH_INPUT,
)
from src.experiments.canonical_optimization_universe_v1 import (
    OPTIMIZATION_CAN_DEFINE_OPTIMIZABLE_ENVELOPE,
    OPTIMIZATION_PRODUCTIVE_AUTHORITY,
    SCHEMA_VERSION,
    STATUS_ACCEPTED_REGISTERED_RESEARCH_CAPABILITY,
    STATUS_FOUNDATION_OK,
    STATUS_REJECTED_STALE_INPUT_CONTRACT,
    STATUS_REJECTED_UNREGISTERED_CAPABILITY,
    ZERO_AUTHORIZED_PRODUCTIVE_TARGETS,
    CanonicalOptimizationUniverseError,
    CanonicalOptimizationUniverseRequestV1,
    build_optimization_universe_capability_registry_v1,
    derive_optimization_universe_identity_v1,
    validate_canonical_optimization_universe_v1,
    validate_registered_optimization_capability_v1,
)
from src.learning.deterministic_decision_outcome_v0.learning_evidence_export_v1 import (
    export_learning_evidence_from_state_v1,
)
from tests.learning.test_learning_evidence_export_v1 import _learning_state

REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO_ROOT / "src" / "experiments" / "canonical_optimization_universe_v1.py"


def test_universe_identity_is_deterministic() -> None:
    first = derive_optimization_universe_identity_v1()
    second = derive_optimization_universe_identity_v1()
    assert first == second
    assert len(first) == 64


def test_registry_digest_is_deterministic() -> None:
    a = build_optimization_universe_capability_registry_v1()
    b = build_optimization_universe_capability_registry_v1()
    assert a["registry_digest"] == b["registry_digest"]
    assert a["registered_capability_count"] == 8
    assert a["zero_authorized_productive_targets"] is False
    assert len(a["authorized_productive_targets"]) == 1


def test_m9_productive_target_registered_in_foundation() -> None:
    result = validate_canonical_optimization_universe_v1()
    assert ZERO_AUTHORIZED_PRODUCTIVE_TARGETS is False
    assert result["zero_authorized_productive_targets"] is False
    assert len(result["authorized_productive_targets"]) == 1
    assert result["optimizable_envelope_defined"] is False
    assert result["optimizable_envelope_ref"] == "peak_trade.canonical_optimizable_envelope.v1"


def test_accepts_registered_research_capability() -> None:
    result = validate_canonical_optimization_universe_v1(
        CanonicalOptimizationUniverseRequestV1(
            capability_id="peak_trade.canonical_meta_learning.v1"
        )
    )
    assert result["capability_validation_status"] == STATUS_ACCEPTED_REGISTERED_RESEARCH_CAPABILITY
    assert result["validated_capability_id"] == "peak_trade.canonical_meta_learning.v1"
    entry = validate_registered_optimization_capability_v1("peak_trade.canonical_meta_learning.v1")
    assert entry["productive_authority"] == "NONE"


def test_rejects_unknown_capability() -> None:
    result = validate_canonical_optimization_universe_v1(
        CanonicalOptimizationUniverseRequestV1(
            capability_id="peak_trade.canonical_champion_challenger.v1"
        )
    )
    assert result["status"] == STATUS_REJECTED_UNREGISTERED_CAPABILITY
    with pytest.raises(CanonicalOptimizationUniverseError):
        validate_registered_optimization_capability_v1(
            "peak_trade.canonical_champion_challenger.v1"
        )


def test_accepts_m1_learning_input_via_foundation(tmp_path: Path) -> None:
    state = _learning_state(tmp_path)
    evidence = export_learning_evidence_from_state_v1(state)
    result = validate_canonical_optimization_universe_v1(
        CanonicalOptimizationUniverseRequestV1(learning_evidence=evidence)
    )
    assert result["learning_input_validation"] is not None
    assert result["learning_input_validation"]["status"] == STATUS_ACCEPTED_OFFLINE_RESEARCH_INPUT
    assert result["status"] == STATUS_ACCEPTED_OFFLINE_RESEARCH_INPUT


def test_rejects_stale_learning_input_schema_version(tmp_path: Path) -> None:
    state = _learning_state(tmp_path)
    evidence = export_learning_evidence_from_state_v1(state)
    result = validate_canonical_optimization_universe_v1(
        CanonicalOptimizationUniverseRequestV1(
            learning_evidence=evidence,
            learning_input_schema_version="canonical_optimization_universe_learning_input_v0",
        )
    )
    assert result["status"] == STATUS_REJECTED_STALE_INPUT_CONTRACT


def test_rejects_invalid_learning_evidence() -> None:
    result = validate_canonical_optimization_universe_v1(
        CanonicalOptimizationUniverseRequestV1(learning_evidence={"schema_version": "bogus"})
    )
    assert result["learning_input_validation"] is not None
    assert result["learning_input_validation"]["status"] != STATUS_ACCEPTED_OFFLINE_RESEARCH_INPUT


def test_forbidden_productive_target_request() -> None:
    with pytest.raises(CanonicalOptimizationUniverseError):
        validate_canonical_optimization_universe_v1(
            CanonicalOptimizationUniverseRequestV1(requested_productive_target="any_parameter")
        )


def test_authority_constants_fail_closed() -> None:
    assert OPTIMIZATION_PRODUCTIVE_AUTHORITY == "NONE"
    assert OPTIMIZATION_CAN_DEFINE_OPTIMIZABLE_ENVELOPE is False
    foundation = validate_canonical_optimization_universe_v1()
    assert foundation["status"] == STATUS_FOUNDATION_OK
    assert foundation["learning_input_boundary_schema_version"] == LEARNING_INPUT_SCHEMA_VERSION
    assert foundation["schema_version"] == SCHEMA_VERSION


def test_no_runtime_promotion_execution_or_forbidden_join_paths() -> None:
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
        "src.live.live_gates",
        "src.risk",
        "src.trading",
        "src.trading.master_v2",
        "src.experiments.canonical_champion_challenger_v1",
        "src.experiments.canonical_portfolio_learning_v1",
        "src.experiments.canonical_regime_aware_evaluation_v1",
        "src.experiments.canonical_automated_offline_research_loop_v1",
        "src.experiments.canonical_advanced_search_v1",
        "src.meta.learning_loop.comparison_ssot_v1",
        "src.meta.learning_loop.bridge",
        "src.meta.learning_loop.emitter",
    }
    assert forbidden_imports.isdisjoint(imported)
    for token in (
        "config/live_overrides",
        "submit_order(",
        "promote_to_live(",
        "LIVE_AUTHORIZED=true",
        "TESTNET_AUTHORIZED=true",
    ):
        assert token not in source
