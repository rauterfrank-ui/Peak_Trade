"""WP_DDO_REAL_OUTCOME_HORIZON_TO_NEXT_HARD_BLOCKER_V1 learning stretch tests."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

import pytest

from src.learning.deterministic_decision_outcome_v0.capture_v0 import BLOCKED_CAPTURE_SEAMS_V0
from src.learning.deterministic_decision_outcome_v0.decision_event_v0 import (
    build_decision_event_v0,
)
from src.learning.deterministic_decision_outcome_v0.enums_v0 import UNKNOWN
from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoValidationError
from src.learning.deterministic_decision_outcome_v0.evaluation_engine_v0 import (
    evaluate_offline_bundle_v0,
)
from src.learning.deterministic_decision_outcome_v0.evaluation_observation_v0 import (
    validate_evaluation_observation_v0,
)
from src.learning.deterministic_decision_outcome_v0.real_outcome_horizon_contracts_v1 import (
    REAL_OUTCOME_HORIZON_ENGINE_WIRED,
    SUPPLIER_COMPUTES_ECONOMIC_SCORE,
    SUPPLIER_MINTS_ACTUAL_OUTCOME_REF,
    validate_bar_close_chain_v1,
)
from src.learning.deterministic_decision_outcome_v0.real_outcome_horizon_engine_v1 import (
    REAL_OUTCOME_HORIZON_ENGINE_ID,
    supply_n_bars_evaluation_observation_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_DIR = REPO_ROOT / "src" / "learning" / "deterministic_decision_outcome_v0"


def _decision(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_name": "decision_event",
        "schema_version": "decision_event_v0",
        "record_id": "dec-roh-0001",
        "event_id": "evt-roh-0001",
        "correlation_id": "cor-roh-0001",
        "cycle_id": None,
        "event_time_utc": "2026-09-01T12:00:00Z",
        "decision_type": "NO_ENTRY",
        "decision_result": "NO_ACTION",
        "reason_codes": [],
        "hard_block_reasons": [],
        "decision_time_information_set_ref": "info-set-roh-1",
        "market_snapshot_ref": None,
        "feature_snapshot_ref": None,
        "data_quality_ref": None,
        "risk_snapshot_ref": None,
        "position_snapshot_ref": None,
        "selected_instrument_ref": None,
        "code_sha": UNKNOWN,
        "config_hash": UNKNOWN,
        "authority_owner": UNKNOWN,
        "producer_id": "offline-test-producer",
        "evidence_hash": UNKNOWN,
        "causal_parent_ids": [],
        "evidence_source_refs": ["src-evidence-roh-1"],
    }
    payload.update(overrides)
    return payload


def _identity(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "outcome_record_id": "out-roh-0001",
        "attribution_record_id": "attr-roh-0001",
        "counterfactual_record_id": "cf-roh-0001",
        "correlation_id": "cor-roh-0001",
        "event_time_utc": "2026-09-01T13:00:00Z",
        "code_sha": UNKNOWN,
        "config_hash": UNKNOWN,
    }
    payload.update(overrides)
    return payload


def _valid_n_bars_supplier(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "horizon_start_time_utc": "2026-09-01T12:00:00Z",
        "instrument_ref": "inst:btc-usdt",
        "bar_spec_ref": "bar:1h",
        "n_bars": 2,
        "horizon_observation_status": "OK",
        "outcome_scalar_kind": "LOG_RETURN",
        "bar_close_times_utc": ["2026-09-01T13:00:00Z", "2026-09-01T14:00:00Z"],
        "bar_identity_refs": ["bar-close-1", "bar-close-2"],
        "evaluation_time_information_set_ref": "eval-info-set-roh-1",
        "actual_outcome_ref": "evidence/outcome-measurement-1",
        "economic_score": "LABEL_OPAQUE_1",
    }
    payload.update(overrides)
    return payload


def test_authority_markers_remain_non_authorizing() -> None:
    assert SUPPLIER_MINTS_ACTUAL_OUTCOME_REF is False
    assert SUPPLIER_COMPUTES_ECONOMIC_SCORE is False
    assert REAL_OUTCOME_HORIZON_ENGINE_WIRED is False
    assert "real_outcome_horizon_engine" in BLOCKED_CAPTURE_SEAMS_V0


def test_valid_n_bars_real_claim_end_to_end() -> None:
    decision = build_decision_event_v0(_decision())
    obs = supply_n_bars_evaluation_observation_v1(decision, _valid_n_bars_supplier())
    bundle = evaluate_offline_bundle_v0(decision, obs, identity=_identity())
    assert bundle["outcome_record"]["evaluation_horizon"] == "N_BARS"
    assert bundle["outcome_record"]["actual_outcome_ref"] == "evidence/outcome-measurement-1"
    assert bundle["outcome_record"]["economic_score"] == "LABEL_OPAQUE_1"
    assert bundle["hindsight_leakage"] is False


def test_n_bars_zero_rejected() -> None:
    decision = build_decision_event_v0(_decision())
    with pytest.raises(DdoValidationError, match="N_BARS_MUST_BE_POSITIVE"):
        supply_n_bars_evaluation_observation_v1(
            decision,
            _valid_n_bars_supplier(n_bars=0, bar_close_times_utc=[]),
        )


def test_missing_refs_rejected_for_ok_status() -> None:
    decision = build_decision_event_v0(_decision())
    with pytest.raises(DdoValidationError, match="INVALID_REF:instrument_ref"):
        supply_n_bars_evaluation_observation_v1(
            decision,
            _valid_n_bars_supplier(instrument_ref=UNKNOWN),
        )


def test_horizon_start_before_decision_rejected() -> None:
    decision = build_decision_event_v0(_decision())
    with pytest.raises(DdoValidationError, match="HORIZON_START_BEFORE_DECISION_EVENT"):
        supply_n_bars_evaluation_observation_v1(
            decision,
            _valid_n_bars_supplier(horizon_start_time_utc="2026-09-01T11:00:00Z"),
        )


def test_gap_continuity_violation_rejected() -> None:
    with pytest.raises(DdoValidationError, match="BAR_CLOSE_COUNT_MISMATCH"):
        validate_bar_close_chain_v1(
            horizon_start_time_utc="2026-09-01T12:00:00Z",
            n_bars=2,
            bar_close_times_utc=["2026-09-01T13:00:00Z"],
        )


def test_non_monotonic_bar_closes_rejected() -> None:
    with pytest.raises(DdoValidationError, match="BAR_CLOSE_CHAIN_NOT_STRICTLY_INCREASING"):
        validate_bar_close_chain_v1(
            horizon_start_time_utc="2026-09-01T12:00:00Z",
            n_bars=2,
            bar_close_times_utc=["2026-09-01T14:00:00Z", "2026-09-01T13:00:00Z"],
        )


@pytest.mark.parametrize("status", ["MISSING", "STALE", "GAP", "PARTIAL"])
def test_defective_status_forces_unknown_actual_outcome(status: str) -> None:
    decision = build_decision_event_v0(_decision())
    obs = supply_n_bars_evaluation_observation_v1(
        decision,
        _valid_n_bars_supplier(
            horizon_observation_status=status,
            horizon_observation_reason=f"reason-{status}",
            actual_outcome_ref="evidence/outcome-measurement-1",
        ),
    )
    bundle = evaluate_offline_bundle_v0(decision, obs, identity=_identity())
    assert bundle["outcome_record"]["actual_outcome_ref"] == UNKNOWN


def test_missing_evaluation_time_information_set_ref_for_ok_rejected() -> None:
    decision = build_decision_event_v0(_decision())
    with pytest.raises(DdoValidationError, match="evaluation_time_information_set_ref"):
        supply_n_bars_evaluation_observation_v1(
            decision,
            _valid_n_bars_supplier(evaluation_time_information_set_ref=None),
        )


def test_deferred_horizon_rejects_real_outcome_ref() -> None:
    with pytest.raises(DdoValidationError, match="DEFERRED_HORIZON_REAL_OUTCOME_REF_REJECTED"):
        validate_evaluation_observation_v0(
            {
                "decision_event_ref": "dec-roh-0001",
                "evaluation_horizon": "IMMEDIATE_POST_EVENT",
                "evaluation_time_utc": "2026-09-01T12:05:00Z",
                "actual_outcome_ref": "evidence/forbidden",
            }
        )


def test_n_bars_fields_rejected_on_decision_time_horizon() -> None:
    with pytest.raises(DdoValidationError, match="N_BARS_FIELDS_NOT_ALLOWED_FOR_HORIZON"):
        validate_evaluation_observation_v0(
            {
                "decision_event_ref": "dec-roh-0001",
                "evaluation_horizon": "DECISION_TIME",
                "evaluation_time_utc": "2026-09-01T12:00:00Z",
                "n_bars": 1,
            }
        )


def test_deterministic_supplier_replay() -> None:
    decision = build_decision_event_v0(_decision())
    first = supply_n_bars_evaluation_observation_v1(decision, _valid_n_bars_supplier())
    second = supply_n_bars_evaluation_observation_v1(decision, _valid_n_bars_supplier())
    assert first == second


def test_supplier_does_not_mint_actual_outcome_ref() -> None:
    decision = build_decision_event_v0(_decision())
    supplier = _valid_n_bars_supplier()
    obs = supply_n_bars_evaluation_observation_v1(decision, supplier)
    assert obs["actual_outcome_ref"] == supplier["actual_outcome_ref"]


def test_decision_time_regression_unchanged() -> None:
    decision = build_decision_event_v0(_decision(decision_type="KILL_SWITCH"))
    bundle = evaluate_offline_bundle_v0(
        decision,
        {
            "decision_event_ref": "dec-roh-0001",
            "evaluation_horizon": "DECISION_TIME",
            "evaluation_time_utc": "2026-09-01T12:00:00Z",
            "protected_condition": "PRESENT",
        },
        identity=_identity(),
    )
    assert bundle["outcome_record"]["actual_outcome_ref"] == UNKNOWN
    assert bundle["outcome_record"]["economic_score"] == UNKNOWN
    assert bundle["attribution_record"]["kill_switch_correctness"] == "TRUE_POSITIVE"


def test_hindsight_guard_still_blocks_safety_relabel() -> None:
    decision = build_decision_event_v0(_decision(decision_type="KILL_SWITCH"))
    obs = supply_n_bars_evaluation_observation_v1(decision, _valid_n_bars_supplier())
    obs["later_economic_path"] = {"kill_switch_correctness": "FALSE_POSITIVE"}
    with pytest.raises(DdoValidationError, match="HINDSIGHT_CANNOT_RELABEL"):
        evaluate_offline_bundle_v0(decision, obs, identity=_identity())


def test_supplier_has_no_trading_execution_runtime_imports() -> None:
    forbidden = (
        "src.trading",
        "src.execution",
        "src.live",
        "src.risk",
        "src.risk_layer",
        "src.ops",
    )
    path = PACKAGE_DIR / "real_outcome_horizon_engine_v1.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    hits: list[str] = []
    for node in ast.walk(tree):
        names: list[str] = []
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.append(node.module)
        for name in names:
            if any(name == prefix or name.startswith(prefix + ".") for prefix in forbidden):
                hits.append(f"{path.name}:{name}")
    assert hits == []


def test_engine_id_constant() -> None:
    assert REAL_OUTCOME_HORIZON_ENGINE_ID.endswith("real_outcome_horizon_engine_v1")
