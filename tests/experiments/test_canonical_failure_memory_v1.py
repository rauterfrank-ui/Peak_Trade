"""Phase 3 Canonical Failure Memory v1 contract tests."""

from __future__ import annotations

import ast
import hashlib
import inspect
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

import pytest

from src.experiments.canonical_experiment_identity_v1 import (
    CanonicalExperimentIdentityRequestV1,
    WORKING_TREE_CLEAN,
    build_canonical_experiment_identity_v1,
)
from src.experiments.canonical_experiment_memory_v1 import derive_experiment_id_v1
from src.experiments.canonical_failure_memory_store_v1 import (
    RECORD_FILENAME,
    CanonicalFailureMemoryStoreV1,
)
from src.experiments.canonical_failure_memory_v1 import (
    DUPLICATE_DETECTED_IS_NOT_AUTOMATIC_RESEARCH_BAN,
    FAILURE_MEMORY_AUTOMATIC_RESEARCH_BAN,
    FAILURE_MEMORY_CAN_MUTATE_LIVE_CONFIG,
    FAILURE_MEMORY_CAN_PROMOTE,
    FAILURE_MEMORY_HAS_RUNTIME_AUTHORITY,
    CanonicalFailureMemoryRecordRequestV1,
    FailureMemoryValidationError,
    assess_duplicate_hypothesis_v1,
    build_canonical_failure_memory_record_v1,
    canonical_record_payload,
    derive_hypothesis_fingerprint_v1,
    validate_canonical_failure_memory_record_v1,
)
from src.meta.learning_loop.contract_safety_v1 import deterministic_json_dumps

REPO_ROOT = Path(__file__).resolve().parents[2]
MEMORY_MODULE_PATH = REPO_ROOT / "src" / "experiments" / "canonical_failure_memory_v1.py"
STORE_MODULE_PATH = REPO_ROOT / "src" / "experiments" / "canonical_failure_memory_store_v1.py"
_GIT_SHA = "e10f32f56fad0576cd250958401d13f044c5920d"
_CORE_DIGEST_FIELDS = (
    "trading_decision_core_digest",
    "market_context_contract_digest",
    "bull_bear_logic_digest",
    "state_switch_logic_digest",
    "survival_logic_digest",
    "suitability_logic_digest",
    "double_play_logic_digest",
    "entry_position_exit_logic_digest",
)


def _digest(label: str) -> str:
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


def _identity(**overrides: Any) -> Mapping[str, Any]:
    payload: dict[str, Any] = {
        "git_sha": _GIT_SHA,
        "working_tree_status": WORKING_TREE_CLEAN,
        "strategy_identity": "ma_crossover.v1",
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


def _request(
    identity: Mapping[str, Any] | None = None, **overrides: Any
) -> CanonicalFailureMemoryRecordRequestV1:
    identity = identity or _identity()
    experiment_id = derive_experiment_id_v1(str(identity["identity_digest"]))
    payload: dict[str, Any] = {
        "experiment_identity": identity,
        "hypothesis_id": "hyp.ma-crossover.v1",
        "failure_class": "REJECTED_OVERFIT",
        "failed_gate": "OVERFIT_GATE",
        "rejection_reason": "REJECTED_OVERFIT",
        "regime": "high_vol",
        "parameter_region": {"fast": 10, "slow": 50},
        "cost_sensitivity": {"fee_stress": 0.25},
        "instability_indicators": {"unstable": True, "fold_sign_flips": 3},
        "evidence_refs": [
            {
                "kind": "EXPERIMENT_RECORD",
                "ref": experiment_id,
                "digest": _digest("experiment-record"),
            }
        ],
        "created_at": "2026-08-17T18:00:00Z",
        "robustness_policy_digest": _digest("robustness-policy"),
        "hypothesis_fingerprint": None,
        "experiment_id": None,
        "retest_reason": None,
    }
    payload.update(overrides)
    return CanonicalFailureMemoryRecordRequestV1(**payload)


def test_valid_record_round_trip_preserves_identity_and_core_digests() -> None:
    identity = _identity()
    record = build_canonical_failure_memory_record_v1(_request(identity))
    assert record["completeness"] == "COMPLETE"
    assert record["experiment_id"] == derive_experiment_id_v1(str(identity["identity_digest"]))
    assert record["dataset_digest"] == identity["dataset_digest"]
    assert canonical_record_payload(record["experiment_identity"]) == canonical_record_payload(
        identity
    )
    for field_name in _CORE_DIGEST_FIELDS:
        assert record["experiment_identity"][field_name] == identity[field_name]
    assert record["canonical_trading_decision_core_bound"] is True
    assert record["failure_memory_has_runtime_authority"] is False
    assert record["failure_memory_automatic_research_ban"] is False
    validate_canonical_failure_memory_record_v1(record)


def test_deterministic_serialization_and_fingerprint() -> None:
    first = canonical_record_payload(build_canonical_failure_memory_record_v1(_request()))
    second = canonical_record_payload(build_canonical_failure_memory_record_v1(_request()))
    assert deterministic_json_dumps(first) == deterministic_json_dumps(second)
    identity = _identity()
    parent_ref = identity["parent_lineage"]["parent_lineage_ref"]
    expected = derive_hypothesis_fingerprint_v1(
        identity_digest=str(identity["identity_digest"]),
        hypothesis_id="hyp.ma-crossover.v1",
        parameter_region={"fast": 10, "slow": 50},
        regime="high_vol",
        robustness_policy_digest=_digest("robustness-policy"),
        parent_lineage_ref=parent_ref,
    )
    assert first["hypothesis_fingerprint"] == expected
    assert first["failure_record_id"] == second["failure_record_id"]


def test_exact_same_hypothesis_is_detected(tmp_path: Path) -> None:
    store = CanonicalFailureMemoryStoreV1(tmp_path / "failure-memory")
    record = build_canonical_failure_memory_record_v1(_request())
    store.append(record)
    assessment = store.assess_duplicate(
        hypothesis_fingerprint=str(record["hypothesis_fingerprint"]),
        failure_class="REJECTED_OVERFIT",
        parameter_region={"fast": 10, "slow": 50},
    )
    assert assessment["detected"] is True
    assert assessment["previously_rejected"] is True
    assert assessment["same_failure_mode_known"] is True
    assert assessment["automatic_research_ban"] is False
    assert "WARN" in assessment["actions"]
    assert "REQUIRE_EXPLICIT_RETEST_REASON" in assessment["actions"]
    assert "AUTOMATIC_RESEARCH_BAN" not in assessment["actions"]


def test_identity_relevant_change_is_not_a_false_duplicate() -> None:
    baseline = build_canonical_failure_memory_record_v1(_request())
    changed_dataset = build_canonical_failure_memory_record_v1(
        _request(_identity(dataset_digest=_digest("dataset-v2")))
    )
    changed_cost = build_canonical_failure_memory_record_v1(
        _request(_identity(fee_model_digest=_digest("fee-v2")))
    )
    changed_core = build_canonical_failure_memory_record_v1(
        _request(_identity(bull_bear_logic_digest=_digest("bull-bear-v2")))
    )
    changed_region = build_canonical_failure_memory_record_v1(
        _request(parameter_region={"fast": 12, "slow": 50})
    )
    changed_regime = build_canonical_failure_memory_record_v1(_request(regime="low_vol"))
    changed_robustness = build_canonical_failure_memory_record_v1(
        _request(robustness_policy_digest=_digest("robustness-v2"))
    )
    fingerprints = {
        baseline["hypothesis_fingerprint"],
        changed_dataset["hypothesis_fingerprint"],
        changed_cost["hypothesis_fingerprint"],
        changed_core["hypothesis_fingerprint"],
        changed_region["hypothesis_fingerprint"],
        changed_regime["hypothesis_fingerprint"],
        changed_robustness["hypothesis_fingerprint"],
    }
    assert len(fingerprints) == 7
    assessment = assess_duplicate_hypothesis_v1(
        [baseline],
        hypothesis_fingerprint=str(changed_dataset["hypothesis_fingerprint"]),
    )
    assert assessment["detected"] is False
    assert assessment["actions"] == ["NONE"]


def test_canonical_rejection_reason_and_unknown_class_fail_closed() -> None:
    with pytest.raises(FailureMemoryValidationError, match="canonical rejection"):
        build_canonical_failure_memory_record_v1(
            _request(rejection_reason="looks overfit in the notebook")
        )
    with pytest.raises(FailureMemoryValidationError, match="unknown or unsupported"):
        build_canonical_failure_memory_record_v1(_request(failure_class="REJECTED_VIBES"))
    with pytest.raises(FailureMemoryValidationError, match="inconsistent"):
        build_canonical_failure_memory_record_v1(
            _request(failure_class="REJECTED_OVERFIT", failed_gate="TAIL_RISK_GATE")
        )
    record = build_canonical_failure_memory_record_v1(
        _request(
            failure_class="REJECTED_TAIL_RISK",
            failed_gate="TAIL_RISK_GATE",
            rejection_reason="REJECTED_TAIL_RISK",
        )
    )
    assert record["rejection_reason"] == "REJECTED_TAIL_RISK"
    assert record["failed_gate"] == "TAIL_RISK_GATE"


def test_append_only_identical_replay_and_divergent_conflict(tmp_path: Path) -> None:
    store = CanonicalFailureMemoryStoreV1(tmp_path / "failure-memory")
    record = build_canonical_failure_memory_record_v1(_request())
    first = store.append(record)
    second = store.append(record)
    assert canonical_record_payload(first) == canonical_record_payload(second)
    dest = tmp_path / "failure-memory" / str(record["failure_record_id"]) / RECORD_FILENAME
    original = dest.read_text(encoding="utf-8")
    mutated = canonical_record_payload(record)
    mutated["cost_sensitivity"] = {"fee_stress": 0.99}
    dest.write_text(deterministic_json_dumps(mutated) + "\n", encoding="utf-8")
    with pytest.raises(FailureMemoryValidationError):
        store.get(str(record["failure_record_id"]))
    dest.write_text(original, encoding="utf-8")
    later = build_canonical_failure_memory_record_v1(_request(created_at="2026-08-17T19:00:00Z"))
    stored_later = store.append(later)
    assert stored_later["failure_record_id"] != record["failure_record_id"]
    assert stored_later["hypothesis_fingerprint"] == record["hypothesis_fingerprint"]
    assert len(store.list_by_hypothesis_fingerprint(str(record["hypothesis_fingerprint"]))) == 2


def test_historical_record_not_overwritten_on_conflict(tmp_path: Path) -> None:
    store = CanonicalFailureMemoryStoreV1(tmp_path / "failure-memory")
    record = build_canonical_failure_memory_record_v1(_request())
    store.append(record)
    dest = tmp_path / "failure-memory" / str(record["failure_record_id"]) / RECORD_FILENAME
    original = dest.read_text(encoding="utf-8")
    store.append(record)
    assert dest.read_text(encoding="utf-8") == original
    later = store.append(
        build_canonical_failure_memory_record_v1(_request(created_at="2026-08-17T21:00:00Z"))
    )
    assert later["failure_record_id"] != record["failure_record_id"]
    assert dest.read_text(encoding="utf-8") == original
    loaded = store.get(str(record["failure_record_id"]))
    assert canonical_record_payload(loaded) == canonical_record_payload(record)


def test_evidence_and_experiment_refs_remain_complete(tmp_path: Path) -> None:
    identity = _identity()
    record = build_canonical_failure_memory_record_v1(_request(identity))
    store = CanonicalFailureMemoryStoreV1(tmp_path / "failure-memory")
    loaded = store.append(record)
    assert loaded["evidence_refs"][0]["kind"] == "EXPERIMENT_RECORD"
    assert loaded["evidence_refs"][0]["ref"] == loaded["experiment_id"]
    assert loaded["experiment_id"] == derive_experiment_id_v1(str(identity["identity_digest"]))
    with pytest.raises(FailureMemoryValidationError, match="EXPERIMENT_RECORD"):
        build_canonical_failure_memory_record_v1(
            _request(
                identity,
                evidence_refs=[
                    {
                        "kind": "REPO_RELATIVE",
                        "ref": "docs/ops/specs/CANONICAL_FAILURE_MEMORY_V1.md",
                        "digest": _digest("doc"),
                    }
                ],
            )
        )


def test_path_traversal_and_non_finite_values_fail_closed() -> None:
    identity = _identity()
    experiment_id = derive_experiment_id_v1(str(identity["identity_digest"]))
    with pytest.raises(FailureMemoryValidationError, match="path traversal"):
        build_canonical_failure_memory_record_v1(
            _request(
                identity,
                evidence_refs=[
                    {
                        "kind": "EXPERIMENT_RECORD",
                        "ref": experiment_id,
                        "digest": _digest("experiment-record"),
                    },
                    {
                        "kind": "REPO_RELATIVE",
                        "ref": "../secrets.env",
                        "digest": _digest("escape"),
                    },
                ],
            )
        )
    with pytest.raises(FailureMemoryValidationError, match="non-finite"):
        build_canonical_failure_memory_record_v1(
            _request(cost_sensitivity={"fee_stress": float("nan")})
        )
    with pytest.raises(FailureMemoryValidationError, match="not bound"):
        build_canonical_failure_memory_record_v1(_request(experiment_id=_digest("unrelated")))
    with pytest.raises(FailureMemoryValidationError, match="does not match"):
        build_canonical_failure_memory_record_v1(
            _request(hypothesis_fingerprint=_digest("wrong-fingerprint"))
        )


def test_authority_boundary_no_runtime_or_promotion_paths() -> None:
    for module_path in (MEMORY_MODULE_PATH, STORE_MODULE_PATH):
        source = module_path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
        forbidden_imports = {
            "src.core.peak_config",
            "src.governance.promotion_loop.engine",
            "src.execution",
            "scripts.run_learning_apply_cycle",
            "src.live",
            "src.trading",
            "src.trading.master_v2",
            "src.risk",
        }
        assert forbidden_imports.isdisjoint(imported)
        for token in (
            "config/live_overrides",
            "load_config_with_live_overrides",
            "submit_order",
            "confirm_token",
            "LIVE_AUTHORIZED",
            "TESTNET_AUTHORIZED",
            "apply_proposals_to_live_overrides",
            "write_live_config",
            "armed",
            "FUNDING_AUTHORIZED",
        ):
            assert token not in source
    assert FAILURE_MEMORY_HAS_RUNTIME_AUTHORITY is False
    assert FAILURE_MEMORY_CAN_MUTATE_LIVE_CONFIG is False
    assert FAILURE_MEMORY_CAN_PROMOTE is False
    assert FAILURE_MEMORY_AUTOMATIC_RESEARCH_BAN is False
    assert DUPLICATE_DETECTED_IS_NOT_AUTOMATIC_RESEARCH_BAN is True
    record = build_canonical_failure_memory_record_v1(_request())
    assert record["failure_memory_has_runtime_authority"] is False
    assert record["failure_memory_can_mutate_live_config"] is False
    assert record["failure_memory_can_promote"] is False
    assert record["failure_memory_automatic_research_ban"] is False
    assert "write_live_config" not in inspect.getsource(build_canonical_failure_memory_record_v1)
    assert "apply_proposals_to_live_overrides" not in inspect.getsource(
        CanonicalFailureMemoryStoreV1.append
    )


def test_frozen_record_is_immutable() -> None:
    record = build_canonical_failure_memory_record_v1(_request())
    assert isinstance(record, MappingProxyType)
    with pytest.raises(TypeError):
        record["failure_class"] = "REJECTED_POLICY"  # type: ignore[index]


def test_repeated_parameter_region_instability_deprioritizes_without_ban(tmp_path: Path) -> None:
    store = CanonicalFailureMemoryStoreV1(tmp_path / "failure-memory")
    first = store.append(build_canonical_failure_memory_record_v1(_request()))
    second = store.append(
        build_canonical_failure_memory_record_v1(_request(created_at="2026-08-17T20:00:00Z"))
    )
    assessment = store.assess_duplicate(
        hypothesis_fingerprint=str(first["hypothesis_fingerprint"]),
        failure_class="REJECTED_OVERFIT",
        parameter_region={"slow": 50, "fast": 10},
    )
    assert assessment["same_parameter_region_repeatedly_unstable"] is True
    assert "DEPRIORITIZE" in assessment["actions"]
    assert assessment["automatic_research_ban"] is False
    assert second["failure_record_id"] != first["failure_record_id"]
