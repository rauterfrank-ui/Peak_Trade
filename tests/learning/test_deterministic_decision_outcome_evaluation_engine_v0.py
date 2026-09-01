"""WP-FA-05 offline replay / outcome / attribution / counterfactual engine tests."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from src.learning.deterministic_decision_outcome_v0.authority_v0 import (
    ATTRIBUTION_ENGINE_PRESENT,
    COUNTERFACTUAL_ENGINE_PRESENT,
    EVALUATION_RUNTIME_WIRING,
    LEARNING_PRODUCTIVE_AUTHORITY,
    OUTCOME_ENGINE_PRESENT,
    PROMOTION_AUTHORITY_ACTIVATION,
    REPLAY_ENGINE_PRESENT,
    RUNTIME_EFFECT,
    WORKPACKAGE_ID,
)
from src.learning.deterministic_decision_outcome_v0.decision_event_v0 import (
    build_decision_event_v0,
)
from src.learning.deterministic_decision_outcome_v0.enums_v0 import UNKNOWN
from src.learning.deterministic_decision_outcome_v0.errors_v0 import (
    DdoLineageError,
    DdoValidationError,
)
from src.learning.deterministic_decision_outcome_v0.evaluation_engine_v0 import (
    EVALUATION_ENGINE_ID,
    evaluate_offline_bundle_v0,
)
from src.learning.deterministic_decision_outcome_v0.incident_record_v0 import (
    build_incident_record_v0,
)
from src.learning.deterministic_decision_outcome_v0.ledger_v0 import AppendOnlyDdoLedgerV0
from src.learning.deterministic_decision_outcome_v0.reason_codes_v0 import (
    BLUEPRINT_REASON_TAXONOMY_ID,
)
from src.learning.deterministic_decision_outcome_v0.replay_evaluator_v0 import (
    replay_ledger_record_v0,
    replay_same_incident_inputs_same_classification_v0,
    replay_same_inputs_same_classification_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_DIR = REPO_ROOT / "src" / "learning" / "deterministic_decision_outcome_v0"


def _reason(code: str) -> dict[str, str | None]:
    return {
        "taxonomy_id": BLUEPRINT_REASON_TAXONOMY_ID,
        "code": code,
        "source_taxonomy_ref": None,
    }


def _decision(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_name": "decision_event",
        "schema_version": "decision_event_v0",
        "record_id": "dec-eval-0001",
        "event_id": "evt-eval-0001",
        "correlation_id": "cor-eval-0001",
        "cycle_id": None,
        "event_time_utc": "2026-09-01T12:00:00Z",
        "decision_type": "NO_ENTRY",
        "decision_result": "NO_ACTION",
        "reason_codes": [_reason("NO_ENTRY")],
        "hard_block_reasons": [],
        "decision_time_information_set_ref": "info-set-eval-1",
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
        "evidence_source_refs": ["src-evidence-eval-1"],
    }
    payload.update(overrides)
    return payload


def _incident(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_name": "incident_record",
        "schema_version": "incident_record_v0",
        "record_id": "inc-eval-0001",
        "incident_id": "incid-eval-0001",
        "correlation_id": "cor-eval-0001",
        "cycle_id": None,
        "event_time_utc": "2026-09-01T12:00:00Z",
        "incident_class": "KILL_SWITCH",
        "reason_codes": [_reason("KILL_SWITCH")],
        "hard_block_reasons": [],
        "kill_switch_correctness": None,
        "kill_switch_timing_label": None,
        "stale_root_cause": None,
        "decision_event_ref": "dec-eval-0001",
        "decision_time_information_set_ref": "info-set-eval-1",
        "market_snapshot_ref": None,
        "data_quality_ref": None,
        "risk_snapshot_ref": None,
        "position_snapshot_ref": None,
        "code_sha": UNKNOWN,
        "config_hash": UNKNOWN,
        "authority_owner": UNKNOWN,
        "producer_id": "offline-test-producer",
        "evidence_hash": UNKNOWN,
        "causal_parent_ids": ["dec-eval-0001"],
        "evidence_source_refs": ["src-evidence-eval-1"],
    }
    payload.update(overrides)
    return payload


def _observation(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_name": "evaluation_observation",
        "schema_version": "evaluation_observation_v0",
        "decision_event_ref": "dec-eval-0001",
        "evaluation_horizon": "IMMEDIATE_POST_EVENT",
        "evaluation_time_utc": "2026-09-01T12:05:00Z",
        "evaluation_time_information_set_ref": "eval-set-1",
    }
    payload.update(overrides)
    return payload


def _identity(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "outcome_record_id": "out-eval-0001",
        "attribution_record_id": "attr-eval-0001",
        "counterfactual_record_id": "cf-eval-0001",
        "correlation_id": "cor-eval-0001",
        "event_time_utc": "2026-09-01T12:05:00Z",
        "code_sha": UNKNOWN,
        "config_hash": UNKNOWN,
    }
    payload.update(overrides)
    return payload


def test_wp_fa_05_authority_markers_remain_non_authorizing() -> None:
    assert WORKPACKAGE_ID == (
        "WP_FA_05_OFFLINE_REPLAY_OUTCOME_ATTRIBUTION_COUNTERFACTUAL_ENGINE_V1"
    )
    assert OUTCOME_ENGINE_PRESENT is True
    assert ATTRIBUTION_ENGINE_PRESENT is True
    assert COUNTERFACTUAL_ENGINE_PRESENT is True
    assert REPLAY_ENGINE_PRESENT is True
    assert EVALUATION_RUNTIME_WIRING is False
    assert RUNTIME_EFFECT == "NONE"
    assert LEARNING_PRODUCTIVE_AUTHORITY == "NONE"
    assert PROMOTION_AUTHORITY_ACTIVATION is False


def test_kill_switch_true_positive_ignores_later_favorable_move() -> None:
    decision = build_decision_event_v0(_decision(decision_type="KILL_SWITCH"))
    incident = build_incident_record_v0(_incident())
    bundle = evaluate_offline_bundle_v0(
        decision,
        _observation(
            incident_record_ref="inc-eval-0001",
            protected_condition="PRESENT",
            kill_switch_timing_label="ACCEPTABLE",
            later_favorable_price_move=True,
            later_economic_path={"net_pnl_token": "POSITIVE"},
            actual_outcome_ref="econ-obs-1",
            economic_score="POSITIVE",
        ),
        incident_record=incident,
        identity=_identity(),
    )
    assert bundle["evaluator_id"] == EVALUATION_ENGINE_ID
    assert bundle["hindsight_leakage"] is False
    assert bundle["attribution_record"]["kill_switch_correctness"] == "TRUE_POSITIVE"
    assert bundle["outcome_record"]["safety_score"] == "SAFETY_CONTRACT_SATISFIED"
    assert bundle["outcome_record"]["economic_score"] == "POSITIVE"
    assert bundle["trading_core_reachable"] is False


def test_hindsight_cannot_relabel_kill_switch_via_later_economic_path() -> None:
    decision = build_decision_event_v0(_decision(decision_type="KILL_SWITCH"))
    with pytest.raises(DdoValidationError, match="HINDSIGHT_CANNOT_RELABEL"):
        evaluate_offline_bundle_v0(
            decision,
            _observation(
                protected_condition="PRESENT",
                later_economic_path={"kill_switch_correctness": "FALSE_POSITIVE"},
            ),
            identity=_identity(),
        )


def test_false_negative_and_stale_unknown_are_preserved() -> None:
    decision = build_decision_event_v0(_decision(decision_type="NO_ENTRY"))
    incident = build_incident_record_v0(
        _incident(incident_class="STALE", reason_codes=[_reason("STALE_BLOCK")])
    )
    bundle = evaluate_offline_bundle_v0(
        decision,
        _observation(
            incident_record_ref="inc-eval-0001",
            protected_condition="PRESENT",
            evaluation_horizon=UNKNOWN,
        ),
        incident_record=incident,
        identity=_identity(),
    )
    assert bundle["attribution_record"]["kill_switch_correctness"] == "FALSE_NEGATIVE"
    assert bundle["attribution_record"]["stale_root_cause"] == UNKNOWN
    assert bundle["outcome_record"]["actual_outcome_ref"] == UNKNOWN
    assert bundle["outcome_record"]["economic_score"] == UNKNOWN
    assert bundle["counterfactual_record"]["counterfactual_admissibility"] == "UNAVAILABLE"
    assert bundle["unknown_collapsed"] is False


def test_unavailable_counterfactual_has_null_alternative() -> None:
    decision = build_decision_event_v0(_decision())
    bundle = evaluate_offline_bundle_v0(decision, _observation(), identity=_identity())
    assert bundle["counterfactual_record"]["counterfactual_admissibility"] == "UNAVAILABLE"
    assert bundle["counterfactual_record"]["alternative_result_ref"] is None


def test_modelled_counterfactual_requires_assumptions() -> None:
    decision = build_decision_event_v0(_decision())
    with pytest.raises(DdoValidationError, match="COUNTERFACTUAL_CLAIM_CONTRADICTS"):
        evaluate_offline_bundle_v0(
            decision,
            _observation(counterfactual_admissibility_claim="MODELLED"),
            identity=_identity(),
        )
    bundle = evaluate_offline_bundle_v0(
        decision,
        _observation(
            counterfactual_assumptions="hold-last-admissible-state",
            counterfactual_admissibility_claim="MODELLED",
        ),
        identity=_identity(),
    )
    assert bundle["counterfactual_record"]["counterfactual_admissibility"] == "MODELLED"
    assert bundle["counterfactual_record"]["assumptions"] == "hold-last-admissible-state"


def test_replayable_counterfactual_requires_same_decision_time_set() -> None:
    decision = build_decision_event_v0(_decision())
    alternative = build_decision_event_v0(
        _decision(
            record_id="dec-eval-alt-1",
            event_id="evt-eval-alt-1",
            decision_type="NO_EXIT",
            reason_codes=[_reason("NO_EXIT")],
        )
    )
    bundle = evaluate_offline_bundle_v0(
        decision,
        _observation(alternative_decision_event=dict(alternative)),
        identity=_identity(),
    )
    assert bundle["counterfactual_record"]["counterfactual_admissibility"] == "REPLAYABLE"
    mismatched = build_decision_event_v0(
        _decision(
            record_id="dec-eval-alt-2",
            event_id="evt-eval-alt-2",
            decision_time_information_set_ref="other-info-set",
        )
    )
    with pytest.raises(DdoValidationError, match="COUNTERFACTUAL_DECISION_TIME_SET_MISMATCH"):
        evaluate_offline_bundle_v0(
            decision,
            _observation(alternative_decision_event=dict(mismatched)),
            identity=_identity(),
        )


def test_horizon_unknown_does_not_consume_later_economics() -> None:
    decision = build_decision_event_v0(_decision())
    bundle = evaluate_offline_bundle_v0(
        decision,
        _observation(
            evaluation_horizon=UNKNOWN,
            actual_outcome_ref="econ-obs-ignored",
            economic_score="POSITIVE",
        ),
        identity=_identity(),
    )
    assert bundle["outcome_record"]["evaluation_horizon"] == UNKNOWN
    assert bundle["outcome_record"]["economic_score"] == UNKNOWN
    assert bundle["outcome_record"]["actual_outcome_ref"] == UNKNOWN


def test_replay_and_ledger_idempotency(tmp_path: Path) -> None:
    decision = build_decision_event_v0(_decision())
    incident = build_incident_record_v0(_incident())
    replay_same_inputs_same_classification_v0(decision, decision)
    replay_same_incident_inputs_same_classification_v0(incident, incident)
    ledger = AppendOnlyDdoLedgerV0(tmp_path / "ddo_eval.jsonl")
    ledger.append(decision)
    ledger.append(incident)
    first = evaluate_offline_bundle_v0(
        decision,
        _observation(incident_record_ref="inc-eval-0001", protected_condition="PRESENT"),
        incident_record=incident,
        identity=_identity(),
        ledger=ledger,
    )
    second = evaluate_offline_bundle_v0(
        decision,
        _observation(incident_record_ref="inc-eval-0001", protected_condition="PRESENT"),
        incident_record=incident,
        identity=_identity(),
        ledger=ledger,
    )
    assert first["outcome_record"]["content_hash"] == second["outcome_record"]["content_hash"]
    assert second["persist"]["outcome"]["status"] == "IDEMPOTENT_REPLAY"
    classified = replay_ledger_record_v0(ledger, decision["record_id"])
    assert classified["decision_type"] == "NO_ENTRY"


def test_persist_requires_existing_decision_lineage(tmp_path: Path) -> None:
    decision = build_decision_event_v0(_decision())
    ledger = AppendOnlyDdoLedgerV0(tmp_path / "ddo_eval.jsonl")
    with pytest.raises(DdoLineageError, match="CAUSAL_PARENT_MISSING"):
        evaluate_offline_bundle_v0(decision, _observation(), identity=_identity(), ledger=ledger)


def test_unknown_observation_fields_are_rejected() -> None:
    decision = build_decision_event_v0(_decision())
    with pytest.raises(DdoValidationError, match="UNEXPECTED_FIELD"):
        evaluate_offline_bundle_v0(
            decision,
            _observation(invented_hazard="yes"),
            identity=_identity(),
        )


def test_safety_not_applicable_for_non_safety_decision_without_condition() -> None:
    decision = build_decision_event_v0(_decision())
    bundle = evaluate_offline_bundle_v0(decision, _observation(), identity=_identity())
    assert bundle["outcome_record"]["safety_score"] == "SAFETY_NOT_APPLICABLE"
    assert bundle["attribution_record"]["kill_switch_correctness"] == UNKNOWN


def test_false_positive_is_independent_of_profitability() -> None:
    decision = build_decision_event_v0(_decision(decision_type="KILL_SWITCH"))
    bundle = evaluate_offline_bundle_v0(
        decision,
        _observation(
            protected_condition="ABSENT",
            later_favorable_price_move=True,
            economic_score="POSITIVE",
        ),
        identity=_identity(),
    )
    assert bundle["attribution_record"]["kill_switch_correctness"] == "FALSE_POSITIVE"
    assert bundle["outcome_record"]["safety_score"] == "SAFETY_CONTRACT_NOT_SATISFIED"
    assert bundle["outcome_record"]["economic_score"] == "POSITIVE"


def test_engine_package_has_no_forbidden_imports() -> None:
    import ast

    forbidden = (
        "src.trading",
        "src.execution",
        "src.live",
        "src.risk",
        "src.risk_layer",
        "src.ops",
        "urllib",
        "requests",
        "httpx",
        "aiohttp",
        "socket",
        "http.client",
    )
    hits: list[str] = []
    for path in (
        PACKAGE_DIR / "evaluation_engine_v0.py",
        PACKAGE_DIR / "evaluation_observation_v0.py",
        PACKAGE_DIR / "hindsight_guard_v0.py",
        PACKAGE_DIR / "replay_evaluator_v0.py",
    ):
        tree = ast.parse(path.read_text(encoding="utf-8"))
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
