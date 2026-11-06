"""Phase 7 Canonical Reality Gap Store v1 contract tests."""

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
from src.experiments.canonical_reality_gap_store_persist_v1 import (
    RECORD_FILENAME,
    CanonicalRealityGapStoreV1,
)
from src.experiments.canonical_reality_gap_store_v1 import (
    DISPOSITION_REJECTED_REALITY_GAP,
    DISPOSITION_WITHIN_THRESHOLD,
    FAILED_GATE_NOT_TRIGGERED,
    FAILED_GATE_REALITY_GAP,
    OBSERVED_SURFACE_IS_NOT_AUTHORIZATION,
    OBSERVED_SURFACE_LIVE,
    OBSERVED_SURFACE_SHADOW,
    PROMOTION_AUTHORITY,
    REALITY_GAP_CAN_MUTATE_LIVE_CONFIG,
    REALITY_GAP_CAN_PROMOTE,
    REALITY_GAP_STORE_HAS_RUNTIME_AUTHORITY,
    REALITY_GAP_STORE_PRESENT,
    CanonicalRealityGapRecordRequestV1,
    RealityGapDimensionV1,
    RealityGapValidationError,
    build_canonical_reality_gap_record_v1,
    canonical_record_payload,
    validate_canonical_reality_gap_record_v1,
)
from src.meta.learning_loop.contract_safety_v1 import deterministic_json_dumps

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_MODULE_PATH = REPO_ROOT / "src" / "experiments" / "canonical_reality_gap_store_v1.py"
STORE_MODULE_PATH = REPO_ROOT / "src" / "experiments" / "canonical_reality_gap_store_persist_v1.py"
_GIT_SHA = "bc97d43f715305c8b70eb84ddd12fd718f8460a6"
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
_CREATED_AT = "2026-08-17T22:00:00Z"


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


def _dimension(
    name: str = "fee",
    *,
    expected: float = 0.001,
    observed: float = 0.0012,
    threshold: float = 0.001,
    unit: str = "ratio",
) -> RealityGapDimensionV1:
    return RealityGapDimensionV1(
        name=name,
        expected=expected,
        observed=observed,
        threshold=threshold,
        unit=unit,
    )


def _request(
    identity: Mapping[str, Any] | None = None, **overrides: Any
) -> CanonicalRealityGapRecordRequestV1:
    identity = identity or _identity()
    experiment_id = derive_experiment_id_v1(str(identity["identity_digest"]))
    payload: dict[str, Any] = {
        "experiment_identity": identity,
        "observed_surface": OBSERVED_SURFACE_SHADOW,
        "metric_definitions": "canonical_robustness_metrics_v1",
        "threshold_policy_digest": _digest("threshold-policy"),
        "gap_dimensions": (_dimension(),),
        "evidence_refs": [
            {
                "kind": "EXPERIMENT_RECORD",
                "ref": experiment_id,
                "digest": _digest("experiment-record"),
            }
        ],
        "created_at": _CREATED_AT,
        "expected_surface": "RESEARCH",
        "experiment_id": None,
    }
    payload.update(overrides)
    return CanonicalRealityGapRecordRequestV1(**payload)


def test_valid_record_round_trip_preserves_identity_and_core_digests() -> None:
    identity = _identity()
    record = build_canonical_reality_gap_record_v1(_request(identity))
    assert record["completeness"] == "COMPLETE"
    assert record["experiment_id"] == derive_experiment_id_v1(str(identity["identity_digest"]))
    assert canonical_record_payload(record["experiment_identity"]) == canonical_record_payload(
        identity
    )
    for field_name in _CORE_DIGEST_FIELDS:
        assert record["experiment_identity"][field_name] == identity[field_name]
    assert record["canonical_trading_decision_core_bound"] is True
    assert record["reality_gap_store_has_runtime_authority"] is False
    assert record["observed_surface_is_not_authorization"] is True
    assert record["dimension_results"][0]["identity_digest"] == identity["fee_model_digest"]
    validate_canonical_reality_gap_record_v1(record)


def test_identical_inputs_are_deterministic() -> None:
    first = canonical_record_payload(build_canonical_reality_gap_record_v1(_request()))
    second = canonical_record_payload(build_canonical_reality_gap_record_v1(_request()))
    assert deterministic_json_dumps(first) == deterministic_json_dumps(second)
    assert first["reality_gap_record_id"] == second["reality_gap_record_id"]


def test_within_threshold_does_not_reject() -> None:
    record = build_canonical_reality_gap_record_v1(_request())
    assert record["overall_disposition"] == DISPOSITION_WITHIN_THRESHOLD
    assert record["failed_gate"] == FAILED_GATE_NOT_TRIGGERED
    assert record["dimension_results"][0]["status"] == "WITHIN_THRESHOLD"


def test_exceeding_threshold_reuses_rejected_reality_gap() -> None:
    record = build_canonical_reality_gap_record_v1(
        _request(gap_dimensions=(_dimension(observed=0.01, threshold=0.001),))
    )
    assert record["overall_disposition"] == DISPOSITION_REJECTED_REALITY_GAP
    assert record["failed_gate"] == FAILED_GATE_REALITY_GAP
    assert record["dimension_results"][0]["status"] == "EXCEEDS_THRESHOLD"


def test_mixed_dimensions_reject_when_any_exceeds() -> None:
    record = build_canonical_reality_gap_record_v1(
        _request(
            gap_dimensions=(
                _dimension("fee", expected=0.001, observed=0.001, threshold=0.001),
                _dimension("slippage", expected=0.002, observed=0.02, threshold=0.001),
            )
        )
    )
    statuses = {item["name"]: item["status"] for item in record["dimension_results"]}
    assert statuses["fee"] == "WITHIN_THRESHOLD"
    assert statuses["slippage"] == "EXCEEDS_THRESHOLD"
    assert record["overall_disposition"] == DISPOSITION_REJECTED_REALITY_GAP
    assert record["dimension_results"][1]["identity_digest_field"] == "slippage_model_digest"


def test_missing_or_defaulted_gap_values_fail_closed() -> None:
    with pytest.raises(RealityGapValidationError, match="at least one gap dimension"):
        build_canonical_reality_gap_record_v1(_request(gap_dimensions=()))
    with pytest.raises(RealityGapValidationError, match="unknown or unsupported"):
        build_canonical_reality_gap_record_v1(_request(gap_dimensions=(_dimension(name="impact"),)))
    with pytest.raises(RealityGapValidationError, match="implicit unavailable"):
        build_canonical_reality_gap_record_v1(
            _request(gap_dimensions=(_dimension(unit="default"),))
        )
    with pytest.raises(RealityGapValidationError, match="non-finite"):
        build_canonical_reality_gap_record_v1(
            _request(gap_dimensions=(_dimension(expected=float("nan")),))
        )
    with pytest.raises(RealityGapValidationError, match="non-finite"):
        build_canonical_reality_gap_record_v1(
            _request(gap_dimensions=(_dimension(observed=float("inf")),))
        )
    with pytest.raises(RealityGapValidationError, match="threshold must be >= 0"):
        build_canonical_reality_gap_record_v1(
            _request(gap_dimensions=(_dimension(threshold=-0.001),))
        )


def test_unknown_observed_surface_and_wrong_expected_surface_fail_closed() -> None:
    with pytest.raises(RealityGapValidationError, match="expected_surface must be RESEARCH"):
        build_canonical_reality_gap_record_v1(_request(expected_surface="LIVE"))
    with pytest.raises(RealityGapValidationError, match="observed_surface is unknown"):
        build_canonical_reality_gap_record_v1(_request(observed_surface="PRODUCTION"))
    live_observation = build_canonical_reality_gap_record_v1(
        _request(observed_surface=OBSERVED_SURFACE_LIVE)
    )
    assert live_observation["observed_surface"] == OBSERVED_SURFACE_LIVE
    assert live_observation["observed_surface_is_not_authorization"] is True
    assert live_observation["reality_gap_can_submit_order"] is False
    assert live_observation["reality_gap_can_promote_to_live"] is False


def test_append_only_identical_replay_and_divergent_conflict(tmp_path: Path) -> None:
    store = CanonicalRealityGapStoreV1(tmp_path / "reality-gap")
    record = build_canonical_reality_gap_record_v1(_request())
    first = store.append(record)
    second = store.append(record)
    assert canonical_record_payload(first) == canonical_record_payload(second)
    dest = tmp_path / "reality-gap" / str(record["reality_gap_record_id"]) / RECORD_FILENAME
    original = dest.read_text(encoding="utf-8")
    later = build_canonical_reality_gap_record_v1(_request(created_at="2026-08-17T23:00:00Z"))
    stored_later = store.append(later)
    assert stored_later["reality_gap_record_id"] != record["reality_gap_record_id"]
    assert dest.read_text(encoding="utf-8") == original
    assert store.exists(str(record["reality_gap_record_id"])) is True
    listed = store.list_by_experiment_id(str(record["experiment_id"]))
    assert {item["reality_gap_record_id"] for item in listed} == {
        record["reality_gap_record_id"],
        stored_later["reality_gap_record_id"],
    }


def test_historical_record_not_overwritten_on_conflict(tmp_path: Path) -> None:
    store = CanonicalRealityGapStoreV1(tmp_path / "reality-gap")
    record = build_canonical_reality_gap_record_v1(_request())
    store.append(record)
    dest = tmp_path / "reality-gap" / str(record["reality_gap_record_id"]) / RECORD_FILENAME
    original = dest.read_text(encoding="utf-8")
    mutated = canonical_record_payload(record)
    mutated["observed_surface"] = OBSERVED_SURFACE_LIVE
    dest.write_text(deterministic_json_dumps(mutated) + "\n", encoding="utf-8")
    with pytest.raises(RealityGapValidationError):
        store.get(str(record["reality_gap_record_id"]))
    dest.write_text(original, encoding="utf-8")
    loaded = store.get(str(record["reality_gap_record_id"]))
    assert canonical_record_payload(loaded) == canonical_record_payload(record)
    assert dest.read_text(encoding="utf-8") == original


def test_evidence_and_experiment_refs_remain_complete() -> None:
    identity = _identity()
    record = build_canonical_reality_gap_record_v1(_request(identity))
    assert record["evidence_refs"][0]["kind"] == "EXPERIMENT_RECORD"
    assert record["evidence_refs"][0]["ref"] == record["experiment_id"]
    with pytest.raises(RealityGapValidationError, match="EXPERIMENT_RECORD"):
        build_canonical_reality_gap_record_v1(
            _request(
                identity,
                evidence_refs=[
                    {
                        "kind": "REPO_RELATIVE",
                        "ref": "docs/ops/specs/CANONICAL_REALITY_GAP_STORE_V1.md",
                        "digest": _digest("doc"),
                    }
                ],
            )
        )
    with pytest.raises(RealityGapValidationError, match="path traversal"):
        build_canonical_reality_gap_record_v1(
            _request(
                identity,
                evidence_refs=[
                    {
                        "kind": "EXPERIMENT_RECORD",
                        "ref": derive_experiment_id_v1(str(identity["identity_digest"])),
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
    with pytest.raises(RealityGapValidationError, match="not bound"):
        build_canonical_reality_gap_record_v1(_request(experiment_id=_digest("unrelated")))


def test_store_does_not_write_failure_memory(tmp_path: Path) -> None:
    store = CanonicalRealityGapStoreV1(tmp_path / "reality-gap")
    record = build_canonical_reality_gap_record_v1(
        _request(gap_dimensions=(_dimension(observed=0.05, threshold=0.001),))
    )
    stored = store.append(record)
    assert stored["overall_disposition"] == DISPOSITION_REJECTED_REALITY_GAP
    leftover = [
        path for path in tmp_path.rglob("*") if path.is_file() and "failure_memory" in path.name
    ]
    assert leftover == []
    schema_source = SCHEMA_MODULE_PATH.read_text(encoding="utf-8")
    persist_source = STORE_MODULE_PATH.read_text(encoding="utf-8")
    assert "canonical_failure_memory_store_v1" not in schema_source
    assert "canonical_failure_memory_store_v1" not in persist_source


def test_no_runtime_live_config_promotion_or_authority_paths() -> None:
    for module_path in (SCHEMA_MODULE_PATH, STORE_MODULE_PATH):
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
            "src.governance.promotion_loop",
            "src.governance.promotion_loop.engine",
            "src.execution",
            "scripts.run_learning_apply_cycle",
            "src.live",
            "src.trading",
            "src.trading.master_v2",
            "src.risk",
            "src.experiments.canonical_comparison_ssot_v1",
            "src.experiments.canonical_champion_challenger_v1",
            "src.meta.learning_loop.comparison_ssot_v1",
            "src.meta.learning_loop.runtime_observation_feedback_v1",
            "src.meta.learning_loop.canary_micro_live_readiness_v1",
            "src.experiments.live_session_registry",
        }
        assert forbidden_imports.isdisjoint(imported)
        for token in (
            "config/live_overrides",
            "config/auto/",
            "load_config_with_live_overrides",
            "submit_order(",
            "apply_proposals_to_live_overrides",
            "write_live_config(",
            "LIVE_AUTHORIZED",
            "TESTNET_AUTHORIZED",
            "FUNDING_AUTHORIZED",
            "promote_to_live(",
            "create_confirm_token(",
            "use_confirm_token(",
        ):
            assert token not in source
        assert "Phase 8" not in source
        assert "regime-aware" not in source.lower()
    record = build_canonical_reality_gap_record_v1(_request())
    assert isinstance(record, MappingProxyType)
    with pytest.raises(TypeError):
        record["overall_disposition"] = DISPOSITION_REJECTED_REALITY_GAP  # type: ignore[index]
    assert REALITY_GAP_STORE_PRESENT is True
    assert REALITY_GAP_STORE_HAS_RUNTIME_AUTHORITY is False
    assert REALITY_GAP_CAN_MUTATE_LIVE_CONFIG is False
    assert REALITY_GAP_CAN_PROMOTE is False
    assert PROMOTION_AUTHORITY == "NONE"
    assert OBSERVED_SURFACE_IS_NOT_AUTHORIZATION is True
    assert record["reality_gap_can_mutate_live_config"] is False
    assert record["reality_gap_can_submit_order"] is False
    assert record["reality_gap_can_fund"] is False
    assert record["reality_gap_can_increase_risk"] is False
    assert record["reality_gap_can_increase_leverage"] is False
    assert record["reality_gap_can_authorize_canary"] is False
    assert record["reality_gap_can_promote_to_live"] is False
    assert "apply_proposals_to_live_overrides" not in inspect.getsource(
        build_canonical_reality_gap_record_v1
    )
    assert "apply_proposals_to_live_overrides" not in inspect.getsource(
        CanonicalRealityGapStoreV1.append
    )
