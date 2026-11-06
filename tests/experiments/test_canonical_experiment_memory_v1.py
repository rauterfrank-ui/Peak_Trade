"""Phase 2 Immutable Experiment Memory v1 contract tests."""

from __future__ import annotations

import ast
import hashlib
import inspect
import os
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

import pytest

from src.experiments.canonical_experiment_identity_v1 import (
    CanonicalExperimentIdentityRequestV1,
    WORKING_TREE_CLEAN,
    build_canonical_experiment_identity_v1,
)
from src.experiments.canonical_experiment_memory_store_v1 import (
    RECORD_FILENAME,
    CanonicalExperimentMemoryStoreV1,
)
from src.experiments.canonical_experiment_memory_v1 import (
    EXPERIMENT_MEMORY_CAN_MUTATE_LIVE_CONFIG,
    EXPERIMENT_MEMORY_CAN_PROMOTE,
    EXPERIMENT_MEMORY_HAS_RUNTIME_AUTHORITY,
    CanonicalExperimentMemoryRecordRequestV1,
    ExperimentMemoryValidationError,
    ExperimentRecordConflictError,
    build_canonical_experiment_memory_record_v1,
    canonical_record_payload,
    derive_experiment_id_v1,
    validate_canonical_experiment_memory_record_v1,
)
from src.meta.learning_loop.contract_safety_v1 import deterministic_json_dumps

REPO_ROOT = Path(__file__).resolve().parents[2]
MEMORY_MODULE_PATH = REPO_ROOT / "src" / "experiments" / "canonical_experiment_memory_v1.py"
STORE_MODULE_PATH = REPO_ROOT / "src" / "experiments" / "canonical_experiment_memory_store_v1.py"
_GIT_SHA = "ecbe5b7b4f8a71d3a81443a65949fcce6a5de350"
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


def _bound_ref(digest: str) -> dict[str, str]:
    return {"digest": digest, "kind": "IDENTITY_DIGEST_BOUND"}


def _request(
    identity: Mapping[str, Any] | None = None, **overrides: Any
) -> CanonicalExperimentMemoryRecordRequestV1:
    identity = identity or _identity()
    payload: dict[str, Any] = {
        "experiment_identity": identity,
        "hypothesis_id": "hyp.ma-crossover.v1",
        "hypothesis_fingerprint": _digest("hypothesis"),
        "parent_experiment": None,
        "strategy_family": "ma_crossover",
        "candidate_role": "RESEARCH",
        "dataset_ref": _bound_ref(str(identity["dataset_digest"])),
        "cost_model_ref": _bound_ref(str(identity["cost_model_digest"])),
        "risk_policy_ref": _bound_ref(str(identity["risk_policy_digest"])),
        "portfolio_ref": _bound_ref(str(identity["portfolio_digest"])),
        "metrics": {"sharpe": 1.25, "max_drawdown": -0.12},
        "robustness_results": {"walk_forward": {"passed": True, "folds": 4}},
        "regime_results": {"high_vol": {"sharpe": 0.4}},
        "comparison_status": "NOT_COMPARED",
        "disposition": "RESEARCH_ONLY",
        "rejection_reason": None,
        "created_at": "2026-08-17T17:00:00Z",
        "artifacts": [
            {
                "kind": "REPO_RELATIVE",
                "ref": "docs/ops/specs/CANONICAL_EXPERIMENT_IDENTITY_V1.md",
                "digest": _digest("artifact"),
                "media_type": "text/markdown",
            }
        ],
        "experiment_id": None,
        "lineage_ancestors": None,
        "supersedes_experiment_id": None,
    }
    payload.update(overrides)
    return CanonicalExperimentMemoryRecordRequestV1(**payload)


def test_valid_record_accepted_and_identity_round_trips() -> None:
    identity = _identity()
    record = build_canonical_experiment_memory_record_v1(_request(identity))
    assert record["completeness"] == "COMPLETE"
    assert record["experiment_id"] == derive_experiment_id_v1(str(identity["identity_digest"]))
    assert canonical_record_payload(record["experiment_identity"]) == canonical_record_payload(
        identity
    )
    for field_name in _CORE_DIGEST_FIELDS:
        assert record["experiment_identity"][field_name] == identity[field_name]
        assert isinstance(record["experiment_identity"][field_name], str)
        assert len(record["experiment_identity"][field_name]) == 64
    assert record["canonical_trading_decision_core_bound"] is True
    assert record["experiment_memory_has_runtime_authority"] is False
    validate_canonical_experiment_memory_record_v1(record)


def test_required_field_missing_rejected() -> None:
    identity = _identity()
    with pytest.raises(ExperimentMemoryValidationError):
        build_canonical_experiment_memory_record_v1(_request(identity, created_at=None))
    with pytest.raises(ExperimentMemoryValidationError):
        build_canonical_experiment_memory_record_v1(_request(identity, hypothesis_id=""))
    with pytest.raises(ExperimentMemoryValidationError):
        build_canonical_experiment_memory_record_v1(
            _request(
                identity, dataset_ref={"kind": "IDENTITY_DIGEST_BOUND", "digest": _digest("other")}
            )
        )


def test_phase_1_identity_and_core_digests_survive_persistence(tmp_path: Path) -> None:
    identity = _identity()
    record = build_canonical_experiment_memory_record_v1(_request(identity))
    store = CanonicalExperimentMemoryStoreV1(tmp_path / "memory")
    stored = store.append(record)
    loaded = store.get(str(record["experiment_id"]))
    assert canonical_record_payload(loaded["experiment_identity"]) == canonical_record_payload(
        identity
    )
    for field_name in _CORE_DIGEST_FIELDS:
        assert loaded["experiment_identity"][field_name] == identity[field_name]
    assert canonical_record_payload(stored) == canonical_record_payload(record)


def test_first_append_success_identical_replay_idempotent(tmp_path: Path) -> None:
    record = build_canonical_experiment_memory_record_v1(_request())
    store = CanonicalExperimentMemoryStoreV1(tmp_path / "memory")
    first = store.append(record)
    dest = tmp_path / "memory" / str(record["experiment_id"]) / RECORD_FILENAME
    original = dest.read_bytes()
    second = store.append(record)
    assert dest.read_bytes() == original
    assert canonical_record_payload(first) == canonical_record_payload(second)
    assert store.exists(str(record["experiment_id"])) is True


def test_same_id_changed_metrics_disposition_lineage_rejected(tmp_path: Path) -> None:
    identity = _identity()
    record = build_canonical_experiment_memory_record_v1(_request(identity))
    store = CanonicalExperimentMemoryStoreV1(tmp_path / "memory")
    store.append(record)

    metrics_changed = build_canonical_experiment_memory_record_v1(
        _request(identity, metrics={"sharpe": 9.99})
    )
    with pytest.raises(ExperimentRecordConflictError, match="divergent"):
        store.append(metrics_changed)

    disposition_changed = build_canonical_experiment_memory_record_v1(
        _request(
            identity,
            disposition="REJECTED_OVERFIT",
            rejection_reason="holdout collapse",
        )
    )
    with pytest.raises(ExperimentRecordConflictError, match="divergent"):
        store.append(disposition_changed)

    parent_identity = _identity(strategy_identity="parent.v1")
    parent_record = build_canonical_experiment_memory_record_v1(
        _request(parent_identity, hypothesis_id="hyp.parent")
    )
    lineage_changed = build_canonical_experiment_memory_record_v1(
        _request(identity, parent_experiment=str(parent_record["experiment_id"]))
    )
    with pytest.raises(ExperimentRecordConflictError, match="divergent"):
        store.append(lineage_changed)


def test_parent_lineage_round_trip_and_self_parent_rejected(tmp_path: Path) -> None:
    parent_identity = _identity(strategy_identity="parent.v1")
    parent = build_canonical_experiment_memory_record_v1(
        _request(parent_identity, hypothesis_id="hyp.parent")
    )
    child_identity = _identity(
        strategy_identity="child.v1", parent_lineage_ref=str(parent["experiment_id"])
    )
    child = build_canonical_experiment_memory_record_v1(
        _request(
            child_identity,
            hypothesis_id="hyp.child",
            parent_experiment=str(parent["experiment_id"]),
        )
    )
    assert child["parent_experiment"] == parent["experiment_id"]
    assert child["lineage"]["kind"] == "PARENT_BOUND"
    assert child["lineage"]["ancestors"] == [parent["experiment_id"]]

    store = CanonicalExperimentMemoryStoreV1(tmp_path / "memory")
    store.append(parent)
    stored_child = store.append(child)
    loaded = store.get(str(child["experiment_id"]))
    assert loaded["parent_experiment"] == parent["experiment_id"]
    assert loaded["lineage"] == stored_child["lineage"]

    with pytest.raises(ExperimentMemoryValidationError, match="self-parent"):
        build_canonical_experiment_memory_record_v1(
            _request(
                child_identity,
                experiment_id=str(child["experiment_id"]),
                parent_experiment=str(child["experiment_id"]),
            )
        )


def test_deterministic_serialization_and_artifact_refs(tmp_path: Path) -> None:
    record = build_canonical_experiment_memory_record_v1(_request())
    first = deterministic_json_dumps(canonical_record_payload(record))
    second = deterministic_json_dumps(
        canonical_record_payload(build_canonical_experiment_memory_record_v1(_request()))
    )
    assert first == second
    store = CanonicalExperimentMemoryStoreV1(tmp_path / "memory")
    store.append(record)
    loaded = store.get(str(record["experiment_id"]))
    assert loaded["artifacts"][0]["ref"] == "docs/ops/specs/CANONICAL_EXPERIMENT_IDENTITY_V1.md"
    assert loaded["artifacts"][0]["kind"] == "REPO_RELATIVE"
    assert "media_type" in loaded["artifacts"][0]


def test_atomic_write_failure_leaves_no_partial_record(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    record = build_canonical_experiment_memory_record_v1(_request())
    store = CanonicalExperimentMemoryStoreV1(tmp_path / "memory")

    def _boom(src: str, dst: str) -> None:
        raise OSError("simulated link failure")

    monkeypatch.setattr(os, "link", _boom)
    with pytest.raises(OSError, match="simulated link failure"):
        store.append(record)
    dest_dir = tmp_path / "memory" / str(record["experiment_id"])
    leftover_records = list(dest_dir.glob(RECORD_FILENAME)) if dest_dir.exists() else []
    assert leftover_records == []
    assert store.exists(str(record["experiment_id"])) is False


def test_corrupt_record_fails_closed(tmp_path: Path) -> None:
    record = build_canonical_experiment_memory_record_v1(_request())
    store = CanonicalExperimentMemoryStoreV1(tmp_path / "memory")
    store.append(record)
    dest = tmp_path / "memory" / str(record["experiment_id"]) / RECORD_FILENAME
    dest.write_text("{not-json", encoding="utf-8")
    with pytest.raises(ExperimentMemoryValidationError, match="corrupt"):
        store.get(str(record["experiment_id"]))
    with pytest.raises(ExperimentMemoryValidationError, match="corrupt"):
        store.exists(str(record["experiment_id"]))


@pytest.mark.parametrize("bad_value", [float("nan"), float("inf"), float("-inf")])
def test_non_finite_metrics_rejected(bad_value: float) -> None:
    with pytest.raises(ExperimentMemoryValidationError, match="non-finite"):
        build_canonical_experiment_memory_record_v1(_request(metrics={"sharpe": bad_value}))
    with pytest.raises(ExperimentMemoryValidationError, match="non-finite"):
        build_canonical_experiment_memory_record_v1(
            _request(robustness_results={"score": bad_value})
        )


def test_filesystem_traversal_and_malformed_ids_rejected(tmp_path: Path) -> None:
    store = CanonicalExperimentMemoryStoreV1(tmp_path / "memory")
    for bad_id in ("../etc/passwd", "/tmp/abs", "abcd", ".." * 32, r"..\\secret"):
        with pytest.raises(ExperimentMemoryValidationError):
            store.get(bad_id)
        with pytest.raises(ExperimentMemoryValidationError):
            store.exists(bad_id)
    with pytest.raises(ExperimentMemoryValidationError, match="path traversal|relative ref"):
        build_canonical_experiment_memory_record_v1(
            _request(
                artifacts=[
                    {
                        "kind": "REPO_RELATIVE",
                        "ref": "../secrets/id_rsa",
                        "digest": _digest("oops"),
                    }
                ]
            )
        )
    with pytest.raises(ExperimentMemoryValidationError, match="absolute"):
        build_canonical_experiment_memory_record_v1(
            _request(
                artifacts=[
                    {
                        "kind": "STORE_RELATIVE",
                        "ref": "/etc/passwd",
                        "digest": _digest("oops"),
                    }
                ]
            )
        )


def test_list_metadata_is_unsorted_ranking_free(tmp_path: Path) -> None:
    store = CanonicalExperimentMemoryStoreV1(tmp_path / "memory")
    first = build_canonical_experiment_memory_record_v1(
        _request(_identity(seed=1), hypothesis_id="hyp.a")
    )
    second = build_canonical_experiment_memory_record_v1(
        _request(_identity(seed=2), hypothesis_id="hyp.b")
    )
    store.append(second)
    store.append(first)
    rows = store.list_metadata()
    assert [row["experiment_id"] for row in rows] == sorted(row["experiment_id"] for row in rows)
    assert {row["hypothesis_id"] for row in rows} == {"hyp.a", "hyp.b"}
    assert "sharpe" not in rows[0]
    assert "rank" not in rows[0]


def test_frozen_record_is_immutable() -> None:
    record = build_canonical_experiment_memory_record_v1(_request())
    assert isinstance(record, MappingProxyType)
    with pytest.raises(TypeError):
        record["disposition"] = "REJECTED_OVERFIT"  # type: ignore[index]


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
        ):
            assert token not in source
    assert EXPERIMENT_MEMORY_HAS_RUNTIME_AUTHORITY is False
    assert EXPERIMENT_MEMORY_CAN_MUTATE_LIVE_CONFIG is False
    assert EXPERIMENT_MEMORY_CAN_PROMOTE is False
    record = build_canonical_experiment_memory_record_v1(_request())
    assert record["experiment_memory_has_runtime_authority"] is False
    assert record["experiment_memory_can_mutate_live_config"] is False
    assert record["experiment_memory_can_promote"] is False
    assert "write_live_config" not in inspect.getsource(build_canonical_experiment_memory_record_v1)
    assert "apply_proposals_to_live_overrides" not in inspect.getsource(
        CanonicalExperimentMemoryStoreV1.append
    )


def test_rejected_disposition_requires_reason_and_does_not_authorize_live() -> None:
    with pytest.raises(ExperimentMemoryValidationError, match="rejection_reason"):
        build_canonical_experiment_memory_record_v1(
            _request(disposition="REJECTED_TAIL_RISK", rejection_reason=None)
        )
    record = build_canonical_experiment_memory_record_v1(
        _request(disposition="PROMOTION_EVIDENCE_READY", rejection_reason=None)
    )
    assert record["disposition"] == "PROMOTION_EVIDENCE_READY"
    assert record["experiment_memory_has_runtime_authority"] is False
    with pytest.raises(ExperimentMemoryValidationError):
        build_canonical_experiment_memory_record_v1(_request(disposition="LIVE_AUTHORIZED"))


def test_new_experiment_id_appends(tmp_path: Path) -> None:
    store = CanonicalExperimentMemoryStoreV1(tmp_path / "memory")
    first = store.append(build_canonical_experiment_memory_record_v1(_request(_identity(seed=1))))
    second = store.append(build_canonical_experiment_memory_record_v1(_request(_identity(seed=2))))
    assert first["experiment_id"] != second["experiment_id"]
    assert len(store.list_metadata()) == 2


def test_provided_experiment_id_must_match_identity_binding() -> None:
    identity = _identity()
    with pytest.raises(ExperimentMemoryValidationError, match="not bound"):
        build_canonical_experiment_memory_record_v1(
            _request(identity, experiment_id=_digest("unrelated"))
        )


def test_no_silent_cost_or_risk_defaults() -> None:
    identity = dict(_identity())
    identity["fee_model_digest"] = "0"
    with pytest.raises(ExperimentMemoryValidationError, match="Canonical Experiment Identity"):
        build_canonical_experiment_memory_record_v1(_request(identity))
