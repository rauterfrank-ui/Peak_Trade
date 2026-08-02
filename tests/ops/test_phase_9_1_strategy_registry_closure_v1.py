"""Owner tests for PHASE_9_1_STRATEGY_REGISTRY_CLOSURE_V1."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ops.phase_9_1_strategy_registry_closure_v1.config_v1 import (
    Phase91ConfigError,
    load_phase91_config_v1,
)
from src.ops.phase_9_1_strategy_registry_closure_v1.constants_v1 import (
    BOUND_REGISTRY_SCHEMA_VERSION,
    CALL_GRAPH_V1,
    CAPABILITY_ID,
    CONFIG_SCHEMA_VERSION,
    CORE_LOGIC_CHANGE,
    HOST_COMPOSITION_STUB_ID,
)
from src.ops.phase_9_1_strategy_registry_closure_v1.evidence_v1 import (
    build_capability_evidence_v1,
)
from src.ops.phase_9_1_strategy_registry_closure_v1.gates_v1 import (
    Phase91GateError,
    assert_composition_input_allowed,
    assert_enabled_for_runtime_authority,
    assert_known_strategy_id,
    reject_direct_fill,
    reject_direct_intent,
    reject_direct_order,
    reject_double_play_bypass,
    reject_master_v2_bypass,
    reject_risk_bypass,
    reject_safety_bypass,
    reject_silent_authority_promotion,
)
from src.ops.phase_9_1_strategy_registry_closure_v1.inventory_v1 import (
    build_strategy_registry_matrix_v1,
    classification_counts_v1,
)
from src.ops.phase_9_1_strategy_registry_closure_v1.models_v1 import StrategyAuthorityClassV1
from src.ops.phase_9_1_strategy_registry_closure_v1.parity_v1 import prove_phase91_parity_v1
from src.ops.phase_9_1_strategy_registry_closure_v1.restart_v1 import (
    prove_restart_deterministic_v1,
)
from src.strategies.registry import build_registry_snapshot

REPO_ROOT = Path(__file__).resolve().parents[2]


def _cfg_digest() -> str:
    return load_phase91_config_v1(repo_root=REPO_ROOT).config_digest


def test_schema_and_classification_complete() -> None:
    cfg = load_phase91_config_v1(repo_root=REPO_ROOT)
    assert cfg.schema_version == CONFIG_SCHEMA_VERSION
    assert cfg.registry_schema_version == BOUND_REGISTRY_SCHEMA_VERSION
    rows = build_strategy_registry_matrix_v1(config_digest=cfg.config_digest)
    snap = build_registry_snapshot()
    registry_ids = set(snap.strategy_ids_sorted)
    matrix_registry_ids = {r.STRATEGY_ID for r in rows if r.STRATEGY_ID in registry_ids}
    assert matrix_registry_ids == registry_ids
    for row in rows:
        assert row.TARGET_CLASSIFICATION in {c.value for c in StrategyAuthorityClassV1}
    # Named runbook models present when repository-proven
    ids = {r.STRATEGY_ID for r in rows}
    for required in (
        "armstrong_cycle",
        "el_karoui_vol_model",
        "ehlers_cycle_filter",
        "bouchaud_microstructure",
        "meta_labeling",
        "vol_regime_overlay",
        "bollinger_bands",
        "ecm_cycle",
        "momentum_1h",
        "mean_reversion",
        "trend_following",
        "master_v2",
        "double_play",
        HOST_COMPOSITION_STUB_ID,
    ):
        assert required in ids


def test_unknown_strategy_id_fail_closed() -> None:
    with pytest.raises(Phase91GateError, match="unknown_strategy_id"):
        assert_known_strategy_id("definitely_not_a_strategy_xyz")


def test_disabled_legacy_strategy_fail_closed() -> None:
    with pytest.raises(Phase91GateError):
        assert_enabled_for_runtime_authority("my_strategy")


def test_legacy_deauthorized_fail_closed() -> None:
    with pytest.raises(Phase91GateError, match="legacy_deauthorized"):
        assert_composition_input_allowed("ecm_cycle")


def test_wrong_config_version_rejected() -> None:
    with pytest.raises(Phase91ConfigError, match="config_version_mismatch"):
        load_phase91_config_v1(
            repo_root=REPO_ROOT,
            expected_schema_version="phase_9_1_strategy_registry_closure_config.v0",
        )


def test_wrong_config_digest_rejected() -> None:
    with pytest.raises(Phase91ConfigError, match="config_digest_mismatch"):
        load_phase91_config_v1(repo_root=REPO_ROOT, expected_digest="0" * 64)


def test_missing_config_rejected(tmp_path: Path) -> None:
    with pytest.raises(Phase91ConfigError, match="missing_registry_closure_config"):
        load_phase91_config_v1(repo_root=tmp_path)


def test_direct_intent_fill_order_forbidden() -> None:
    with pytest.raises(Phase91GateError, match="direct_intent_forbidden"):
        reject_direct_intent("momentum_1h")
    with pytest.raises(Phase91GateError, match="direct_fill_forbidden"):
        reject_direct_fill("momentum_1h")
    with pytest.raises(Phase91GateError, match="direct_order_forbidden"):
        reject_direct_order("momentum_1h")


def test_master_v2_double_play_bypass_forbidden() -> None:
    with pytest.raises(Phase91GateError, match="master_v2_bypass_forbidden"):
        reject_master_v2_bypass("armstrong_cycle")
    with pytest.raises(Phase91GateError, match="double_play_bypass_forbidden"):
        reject_double_play_bypass("armstrong_cycle")


def test_risk_safety_bypass_forbidden() -> None:
    with pytest.raises(Phase91GateError, match="risk_bypass_forbidden"):
        reject_risk_bypass("bollinger_bands")
    with pytest.raises(Phase91GateError, match="safety_bypass_forbidden"):
        reject_safety_bypass("bollinger_bands")


def test_silent_authority_promotion_forbidden() -> None:
    with pytest.raises(Phase91GateError, match="silent_authority_promotion_forbidden"):
        reject_silent_authority_promotion(
            entry_id="armstrong_cycle",
            from_class=StrategyAuthorityClassV1.RESEARCH_INFORMATION,
            to_class=StrategyAuthorityClassV1.CANONICAL_AUTHORITY,
        )


def test_restart_deterministic_reconstruction() -> None:
    proof = prove_restart_deterministic_v1(config_digest=_cfg_digest())
    assert proof["RESTART_DETERMINISTIC"] is True
    assert proof["ok"] is True


def test_parity_and_core_logic_unchanged() -> None:
    parity = prove_phase91_parity_v1()
    assert CORE_LOGIC_CHANGE is False
    assert parity["GOLDEN_VECTOR_PARITY_PASS"] is True
    assert parity["CALL_ORDER_PARITY_PROVEN"] is True
    assert parity["INPUT_OUTPUT_PARITY_PROVEN"] is True
    assert parity["STATE_TRANSITION_PARITY_PROVEN"] is True
    assert parity["DECISION_REASON_PARITY_PROVEN"] is True
    assert parity["RISK_PARITY_PROVEN"] is True
    assert parity["SAFETY_PARITY_PROVEN"] is True
    assert parity["EXIT_PRECEDENCE_PARITY_PROVEN"] is True


def test_composition_input_only_host_stub() -> None:
    assert_composition_input_allowed(HOST_COMPOSITION_STUB_ID)
    with pytest.raises(Phase91GateError):
        assert_composition_input_allowed("momentum_1h")
    with pytest.raises(Phase91GateError):
        assert_enabled_for_runtime_authority(HOST_COMPOSITION_STUB_ID)


def test_productive_call_graph_integration(tmp_path: Path) -> None:
    assert "composition_eligibility_gate" in CALL_GRAPH_V1
    assert "bypass_negative_proof" in CALL_GRAPH_V1
    evidence = build_capability_evidence_v1(
        repository_sha="testsha",
        repo_root=REPO_ROOT,
        evidence_root=tmp_path / "capability_phase_9_1_strategy_registry_closure_v1",
    )
    assert evidence.ok is True
    assert evidence.claims.STRATEGY_REGISTRY_CLOSED is True
    assert evidence.claims.PRODUCTIVE_CALLERS_ENUMERATED is True
    assert evidence.call_graph == CALL_GRAPH_V1
    counts = classification_counts_v1(
        build_strategy_registry_matrix_v1(config_digest=evidence.config_digest)
    )
    assert counts["CANONICAL_AUTHORITY"] == 2
    assert counts["AUTHORIZED_COMPOSITION_INPUT"] == 1
    assert counts["RESEARCH_INFORMATION"] >= 6
    assert counts["LEGACY_DEAUTHORIZED"] >= 6
    summary = json.loads(
        (tmp_path / "capability_phase_9_1_strategy_registry_closure_v1" / "SUMMARY.json").read_text(
            encoding="utf-8"
        )
    )
    assert summary["capability_id"] == CAPABILITY_ID
    assert summary["ok"] is True
    assert summary["repository_sha"] == "testsha"
