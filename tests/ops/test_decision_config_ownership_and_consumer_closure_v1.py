"""Capability 6.3 — Decision config ownership and consumer closure tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.decision_config_ownership_and_consumer_closure_v1.authority_matrix_v1 import (
    build_config_authority_matrix_v1,
    inventory_decision_config_authority_surfaces_v1,
)
from src.ops.decision_config_ownership_and_consumer_closure_v1.canonical_values_v1 import (
    CANONICAL_ADVERSE_EXIT_DISTANCE,
    CANONICAL_CONFIRMATION_EPOCHS,
    CANONICAL_DECISION_CONFIG_DIGEST,
    CANONICAL_REVERSAL_DISTANCE,
    CANONICAL_UP_DISTANCE,
    clear_canonical_decision_runtime_config_cache_v1,
)
from src.ops.decision_config_ownership_and_consumer_closure_v1.config_loader_v1 import (
    DecisionConfigError,
    load_canonical_decision_runtime_config_v1,
    reject_legacy_bridge_fallback_v1,
    reject_parallel_owner_conflict_v1,
)
from src.ops.decision_config_ownership_and_consumer_closure_v1.constants_v1 import (
    CALL_GRAPH_AFTER,
    CALL_GRAPH_BEFORE,
    CALL_GRAPH_CONFIG_BIND_STEP,
    CAPABILITY_ID,
    CORE_LOGIC_CHANGE,
    EXPECTED_ADVERSE_EXIT_DISTANCE,
    EXPECTED_CONFIRMATION_EPOCHS,
    EXPECTED_REVERSAL_DISTANCE,
    EXPECTED_UP_DISTANCE,
    PACKAGE_MARKER,
)
from src.ops.decision_config_ownership_and_consumer_closure_v1.cycle_harness_v1 import (
    build_capability_evidence_v1,
    prove_deterministic_replay_v1,
    prove_restart_config_digest_stable_v1,
    run_failure_injections_v1,
    run_productive_host_config_cycles_v1,
)
from src.ops.decision_config_ownership_and_consumer_closure_v1.host_binding_v1 import (
    HostDecisionConfigBindingV1,
    ensure_host_decision_config_binding_v1,
    require_bound_decision_config_v1,
)
from src.ops.decision_config_ownership_and_consumer_closure_v1.parity_v1 import (
    prove_trading_logic_parity_v1,
)
from src.ops.decision_config_ownership_and_consumer_closure_v1.reason_codes_v1 import (
    DecisionConfigFailureCodeV1,
)
from src.ops.dynamic_scope_persistence_binding_v1.constants_v1 import (
    FROZEN_ADVERSE_EXIT_DISTANCE,
    FROZEN_REVERSAL_DISTANCE,
    FROZEN_UP_DISTANCE,
)
from src.ops.dynamic_scope_persistence_binding_v1.host_binding_v1 import (
    dynamic_scope_config_digest_v1,
)
from src.ops.stateful_confirmation_and_c1_productive_binding_v1.host_binding_v1 import (
    confirmation_config_digest_v1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.decision_economics_cycle_bridge_v1 import (
    CALL_GRAPH_V1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.full_economic_reconstruction_verifier_v1 import (
    REQUIRED_CALL_GRAPH,
)

REPO_SHA = "0003c493a66f27a619638e88e3b58b05b64ce02e"
CAP61_DIGEST = "06ca8fabf72c34c4cff86dccdf1c2fc2a99a21f764dbf5f27ed93b7bc5f31791"
CAP62_DIGEST = "808a1c920f895f81c3ddc7431349c3272f77d2e5da66825c9d92919ed6ddce3e"


def test_constants_and_call_graph_bound() -> None:
    assert CAPABILITY_ID.endswith("DECISION_CONFIG_OWNERSHIP_AND_CONSUMER_CLOSURE_V1")
    assert PACKAGE_MARKER.endswith("=true")
    assert CORE_LOGIC_CHANGE is False
    assert CALL_GRAPH_CONFIG_BIND_STEP in CALL_GRAPH_AFTER
    assert CALL_GRAPH_CONFIG_BIND_STEP not in CALL_GRAPH_BEFORE
    assert CALL_GRAPH_V1 == REQUIRED_CALL_GRAPH
    assert CALL_GRAPH_CONFIG_BIND_STEP in CALL_GRAPH_V1
    assert CANONICAL_CONFIRMATION_EPOCHS == EXPECTED_CONFIRMATION_EPOCHS == 2
    assert CANONICAL_UP_DISTANCE == EXPECTED_UP_DISTANCE == 200.0
    assert CANONICAL_ADVERSE_EXIT_DISTANCE == EXPECTED_ADVERSE_EXIT_DISTANCE == 80.0
    assert CANONICAL_REVERSAL_DISTANCE == EXPECTED_REVERSAL_DISTANCE == 120.0
    assert FROZEN_UP_DISTANCE == CANONICAL_UP_DISTANCE
    assert FROZEN_ADVERSE_EXIT_DISTANCE == CANONICAL_ADVERSE_EXIT_DISTANCE
    assert FROZEN_REVERSAL_DISTANCE == CANONICAL_REVERSAL_DISTANCE


def test_typed_config_model_and_digest() -> None:
    cfg = load_canonical_decision_runtime_config_v1()
    assert cfg.config_version == "v1"
    assert cfg.confirmation_epochs == 2
    assert cfg.up_distance == 200.0
    assert cfg.adverse_exit_distance == 80.0
    assert cfg.reversal_distance == 120.0
    assert len(cfg.config_digest()) == 64
    assert cfg.config_digest() == CANONICAL_DECISION_CONFIG_DIGEST


def test_authority_matrix_classification() -> None:
    matrix = build_config_authority_matrix_v1()
    by_key = {r["CONFIG_KEY"]: r for r in matrix}
    for key in (
        "confirmation_epochs",
        "up_distance",
        "adverse_exit_distance",
        "reversal_distance",
    ):
        assert by_key[key]["MIGRATION_REQUIRED"] is True
        assert by_key[key]["VALUE_CLASSIFICATION"] == "CANONICAL_RUNTIME_CONFIG"
        assert by_key[key]["CORE_LOGIC_EFFECT"] == "NONE"
    assert by_key["PRICE_PATH_MAX_LEN"]["MIGRATION_REQUIRED"] is False
    assert by_key["PRICE_PATH_MAX_LEN"]["VALUE_CLASSIFICATION"] == "IMMUTABLE_DOMAIN_CONSTANT"
    assert by_key["fee_rate_bps"]["MIGRATION_REQUIRED"] is False
    assert by_key["fee_rate_bps"]["VALUE_CLASSIFICATION"] == "EXECUTION_MODEL_CONFIG"
    assert by_key["slippage_bps"]["MIGRATION_REQUIRED"] is False
    assert by_key["slippage_bps"]["VALUE_CLASSIFICATION"] == "EXECUTION_MODEL_CONFIG"
    inv = inventory_decision_config_authority_surfaces_v1()
    assert inv["parallel_config_authority_created"] is False
    assert inv["core_logic_changed"] is False


def test_parity_contract() -> None:
    parity = prove_trading_logic_parity_v1()
    assert parity["GOLDEN_VECTOR_PARITY_PASS"] is True
    assert parity["CALL_ORDER_PARITY_PROVEN"] is True
    assert parity["INPUT_OUTPUT_PARITY_PROVEN"] is True
    assert parity["STATE_TRANSITION_PARITY_PROVEN"] is True
    assert parity["DECISION_REASON_PARITY_PROVEN"] is True
    assert parity["MASTER_V2_PARITY_PROVEN"] is True
    assert parity["DOUBLE_PLAY_PARITY_PROVEN"] is True
    assert parity["BULL_BEAR_PARITY_PROVEN"] is True
    assert parity["CONFIRMATION_PARITY_PROVEN"] is True
    assert parity["DYNAMIC_SCOPE_PARITY_PROVEN"] is True
    assert parity["RISK_PARITY_PROVEN"] is True
    assert parity["SAFETY_PARITY_PROVEN"] is True
    assert parity["EXIT_PRECEDENCE_PARITY_PROVEN"] is True
    assert parity["EFFECTIVE_NUMERIC_VALUES_UNCHANGED"] is True
    assert parity["frozen_thresholds"]["confirmation_epochs"] == 2
    assert parity["frozen_thresholds"]["up_distance"] == 200.0


def test_predecessor_digests_stable() -> None:
    assert confirmation_config_digest_v1() == CAP61_DIGEST
    assert dynamic_scope_config_digest_v1() == CAP62_DIGEST


def test_missing_key_fail_closed(tmp_path: Path) -> None:
    path = tmp_path / "missing.toml"
    path.write_text(
        "[canonical_decision_runtime_config_v1]\n"
        'config_version = "v1"\n'
        'schema_version = "canonical_decision_runtime_config.v1"\n'
        "up_distance = 200.0\n"
        "adverse_exit_distance = 80.0\n"
        "reversal_distance = 120.0\n",
        encoding="utf-8",
    )
    clear_canonical_decision_runtime_config_cache_v1()
    with pytest.raises(DecisionConfigError) as exc:
        load_canonical_decision_runtime_config_v1(path, enforce_frozen_effective_values=False)
    assert exc.value.code is DecisionConfigFailureCodeV1.CONFIG_KEY_MISSING


def test_invalid_type_fail_closed(tmp_path: Path) -> None:
    path = tmp_path / "bad_type.toml"
    path.write_text(
        "[canonical_decision_runtime_config_v1]\n"
        'config_version = "v1"\n'
        'schema_version = "canonical_decision_runtime_config.v1"\n'
        'confirmation_epochs = "two"\n'
        "up_distance = 200.0\n"
        "adverse_exit_distance = 80.0\n"
        "reversal_distance = 120.0\n",
        encoding="utf-8",
    )
    with pytest.raises(DecisionConfigError) as exc:
        load_canonical_decision_runtime_config_v1(path, enforce_frozen_effective_values=False)
    assert exc.value.code is DecisionConfigFailureCodeV1.CONFIG_TYPE_INVALID


def test_legacy_fallback_and_parallel_owner_negatives() -> None:
    with pytest.raises(DecisionConfigError) as exc:
        reject_legacy_bridge_fallback_v1(attempted=True)
    assert exc.value.code is DecisionConfigFailureCodeV1.LEGACY_BRIDGE_FALLBACK_ATTEMPT
    with pytest.raises(DecisionConfigError) as exc2:
        reject_parallel_owner_conflict_v1(
            owner_a_value=200.0, owner_b_value=199.0, key="up_distance"
        )
    assert exc2.value.code is DecisionConfigFailureCodeV1.PARALLEL_CONFIG_OWNER_CONFLICT


def test_host_binding_and_consumer_require(tmp_path: Path) -> None:
    binding = HostDecisionConfigBindingV1()
    ensure_host_decision_config_binding_v1(
        binding,
        repository_sha=REPO_SHA,
        state_root=tmp_path,
        persist=True,
    )
    cfg = require_bound_decision_config_v1(binding)
    assert cfg.confirmation_epochs == 2
    assert binding.config_digest == CANONICAL_DECISION_CONFIG_DIGEST
    unbound = HostDecisionConfigBindingV1()
    with pytest.raises(DecisionConfigError) as exc:
        require_bound_decision_config_v1(unbound)
    assert exc.value.code is DecisionConfigFailureCodeV1.PRODUCTIVE_CONSUMER_UNBOUND


def test_productive_host_path_integration(tmp_path: Path) -> None:
    result = run_productive_host_config_cycles_v1(
        repository_sha=REPO_SHA,
        work_root=tmp_path / "host",
    )
    assert result["ok"] is True
    assert result["final_config_digest"] == CANONICAL_DECISION_CONFIG_DIGEST
    assert result["effective_values"]["confirmation_epochs"] == 2
    assert result["effective_values"]["up_distance"] == 200.0


def test_restart_and_replay(tmp_path: Path) -> None:
    restart = prove_restart_config_digest_stable_v1(
        repository_sha=REPO_SHA,
        work_root=tmp_path / "restart",
    )
    assert restart["ok"] is True
    assert restart["confirmation_compatible"] is True
    assert restart["dynamic_scope_compatible"] is True
    replay = prove_deterministic_replay_v1(
        repository_sha=REPO_SHA,
        work_root=tmp_path / "replay",
    )
    assert replay["ok"] is True


def test_failure_injections(tmp_path: Path) -> None:
    results = run_failure_injections_v1(work_root=tmp_path, repository_sha=REPO_SHA)
    assert results["ok"] is True
    assert results["missing_key"]["ok"] is True
    assert results["invalid_type"]["ok"] is True
    assert results["digest_mismatch"]["ok"] is True
    assert results["legacy_fallback"]["ok"] is True
    assert results["parallel_owner"]["ok"] is True
    assert results["incompatible_version"]["ok"] is True
    assert results["restart_mismatch"]["ok"] is True
    assert results["consumer_unbound"]["ok"] is True


def test_full_capability_evidence(tmp_path: Path) -> None:
    evidence = build_capability_evidence_v1(
        repository_sha=REPO_SHA,
        work_root=tmp_path / "evidence",
    )
    payload = evidence.to_dict()
    assert evidence.ok is True
    assert payload["claims"]["EFFECTIVE_NUMERIC_VALUES_UNCHANGED"] is True
    assert payload["claims"]["PREDECESSOR_DIGEST_BOUND"] is True
    assert payload["claims"]["CONFIG_DIGEST_MISMATCH_FAIL_CLOSED"] is True
    assert payload["claims"]["NO_LIVE_ORDER_PATH"] is True
    assert payload["effective_values_before"] == payload["effective_values_after"]
