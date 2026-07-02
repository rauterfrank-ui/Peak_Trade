"""Contract tests for versioned cross-sectional ranking semantics binding materialization v0."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from src.research.cross_sectional_ranking_semantics_binding_v0 import (
    ATTESTED_OPERATOR_DECISION_DIGEST,
    ENVELOPE_DIGEST_STATUS_REQUIRED_UNBOUND,
    EXTERNAL_BINDING_KEYS,
    DIGEST_BINDING_KEYS,
    RATIFIED_OPERATOR_BINDING_VALUES,
    RATIFIED_OPERATOR_RATIONALES,
    THRESHOLD_POLICY,
    VERSIONED_BINDING_CONFIG_REL_PATH,
    build_operator_decision_digest_input_v0,
    compute_minimum_history_bars_v0,
    compute_operator_decision_digest_v0,
    materialize_versioned_cross_sectional_ranking_semantics_binding_v0,
    serialize_versioned_binding_artifact_json_v0,
)
from src.research.cross_sectional_ranking_semantics_binding_validator_v0 import (
    REASON_INCOMPLETE_BINDING_MARKED_COMPLETE,
    REASON_NUMERIC_STRENGTH_THRESHOLD_ENABLED,
    ValidationVerdict,
    validate_cross_sectional_ranking_semantics_binding_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_ARTIFACT_PATH = REPO_ROOT / VERSIONED_BINDING_CONFIG_REL_PATH


@pytest.fixture
def versioned_envelope() -> dict:
    return materialize_versioned_cross_sectional_ranking_semantics_binding_v0()


def test_operator_decision_digest_matches_attestation() -> None:
    computed = compute_operator_decision_digest_v0()
    assert computed == ATTESTED_OPERATOR_DECISION_DIGEST


def test_operator_decision_digest_changes_when_value_changes() -> None:
    base = compute_operator_decision_digest_v0()
    mutated_values = dict(RATIFIED_OPERATOR_BINDING_VALUES)
    mutated_values["lookback_N"] = 21
    mutated = compute_operator_decision_digest_v0(operator_values=mutated_values)
    assert mutated != base


def test_operator_decision_digest_changes_when_rationale_changes() -> None:
    base = compute_operator_decision_digest_v0()
    mutated_rationales = dict(RATIFIED_OPERATOR_RATIONALES)
    mutated_rationales["lookback_N"] = mutated_rationales["lookback_N"] + " x"
    mutated = compute_operator_decision_digest_v0(operator_rationales=mutated_rationales)
    assert mutated != base


def test_ratified_values_materialized_with_exact_types(versioned_envelope: dict) -> None:
    numeric = versioned_envelope["binding"]["numeric_bindings"]
    assert numeric["lookback_N"] == {"status": "BOUND", "value": 20}
    assert numeric["vol_window_V"] == {"status": "BOUND", "value": 20}
    assert numeric["rebalance_interval_bars"] == {"status": "BOUND", "value": 1}
    assert numeric["signal_lag_bars"] == {"status": "BOUND", "value": 1}
    assert numeric["min_eligible_members_for_rank"] == {"status": "BOUND", "value": 5}
    assert numeric["switch_entry_delay_epochs"] == {"status": "BOUND", "value": 1}
    assert numeric["max_bar_staleness_bars"] == {"status": "BOUND", "value": 1}
    assert numeric["vol_return_method"] == {"status": "BOUND", "value": "log_return"}
    assert isinstance(numeric["lookback_N"]["value"], int)
    assert isinstance(numeric["vol_window_V"]["value"], int)
    assert isinstance(numeric["vol_epsilon"]["value"], float)
    assert numeric["vol_epsilon"]["value"] == 1e-8


def test_min_abs_score_strength_remains_not_applicable(versioned_envelope: dict) -> None:
    field = versioned_envelope["binding"]["numeric_bindings"]["min_abs_score_strength"]
    assert field == {"status": "NOT_APPLICABLE"}
    assert "value" not in field
    assert versioned_envelope["binding"]["threshold_semantics"]["threshold_policy"] == (
        THRESHOLD_POLICY
    )


def test_minimum_history_bars_derived_as_21(versioned_envelope: dict) -> None:
    assert versioned_envelope["derived_fields"]["minimum_history_bars"] == 21
    assert compute_minimum_history_bars_v0(20, 20, 1) == 21


def test_external_bindings_remain_required_unbound(versioned_envelope: dict) -> None:
    external = versioned_envelope["binding"]["external_bindings"]
    for key in EXTERNAL_BINDING_KEYS:
        assert external[key]["status"] == "REQUIRED_UNBOUND"


def test_schema_digest_bindings_remain_required_unbound(versioned_envelope: dict) -> None:
    digest = versioned_envelope["binding"]["digest_bindings"]
    for key in DIGEST_BINDING_KEYS:
        assert digest[key]["status"] == "REQUIRED_UNBOUND"


def test_envelope_digests_bound_and_unbound(versioned_envelope: dict) -> None:
    envelope_digests = versioned_envelope["envelope_digests"]
    assert envelope_digests["operator_decision_digest"] == {
        "status": "BOUND",
        "value": ATTESTED_OPERATOR_DECISION_DIGEST,
    }
    for key in ("semantic_digest", "config_digest", "manifest_digest"):
        assert envelope_digests[key]["status"] == ENVELOPE_DIGEST_STATUS_REQUIRED_UNBOUND


def test_validator_accepts_incomplete(versioned_envelope: dict) -> None:
    result = validate_cross_sectional_ranking_semantics_binding_v0(versioned_envelope["binding"])
    assert result.valid is True
    assert result.verdict == ValidationVerdict.ACCEPTED_INCOMPLETE
    assert result.fail_reasons == ()


def test_complete_rejected_when_externals_unbound(versioned_envelope: dict) -> None:
    binding = deepcopy(versioned_envelope["binding"])
    binding["binding_status"]["overall_binding_status"] = "COMPLETE"
    result = validate_cross_sectional_ranking_semantics_binding_v0(binding)
    assert result.valid is False
    assert REASON_INCOMPLETE_BINDING_MARKED_COMPLETE in result.fail_reasons


def test_missing_rationale_rejected_by_digest_helper() -> None:
    rationales = dict(RATIFIED_OPERATOR_RATIONALES)
    rationales.pop("lookback_N")
    with pytest.raises(ValueError, match="missing operator rationales"):
        build_operator_decision_digest_input_v0(operator_rationales=rationales)


def test_wrong_operator_value_rejected_by_digest_mismatch() -> None:
    mutated_values = dict(RATIFIED_OPERATOR_BINDING_VALUES)
    mutated_values["lookback_N"] = 21
    digest = compute_operator_decision_digest_v0(operator_values=mutated_values)
    assert digest != ATTESTED_OPERATOR_DECISION_DIGEST


def test_min_abs_score_strength_bound_rejected(versioned_envelope: dict) -> None:
    binding = deepcopy(versioned_envelope["binding"])
    binding["numeric_bindings"]["min_abs_score_strength"] = {
        "status": "BOUND",
        "value": 0.1,
    }
    result = validate_cross_sectional_ranking_semantics_binding_v0(binding)
    assert result.valid is False
    assert REASON_NUMERIC_STRENGTH_THRESHOLD_ENABLED in result.fail_reasons


def test_futures_only_and_bitcoin_prohibition(versioned_envelope: dict) -> None:
    constraints = versioned_envelope["binding"]["system_constraints"]
    assert constraints == {
        "futures_only": True,
        "bitcoin_direction_allowed": False,
        "spot_allowed": False,
        "synthetic_spot_allowed": False,
    }


def test_no_fleet_candidate_dataset_or_economic_bindings(versioned_envelope: dict) -> None:
    scope = versioned_envelope["scope_classification"]
    assert scope["candidate_binding_effect"] == "NONE"
    assert scope["fleet_binding_effect"] == "NONE"
    assert scope["economic_policy_effect"] == "NONE"
    assert scope["runtime_effect"] == "NONE"
    binding = versioned_envelope["binding"]
    assert "strategy_id" not in binding
    assert "fleet_rank" not in binding


def test_deterministic_serialization(versioned_envelope: dict) -> None:
    first = serialize_versioned_binding_artifact_json_v0(versioned_envelope)
    second = serialize_versioned_binding_artifact_json_v0(
        materialize_versioned_cross_sectional_ranking_semantics_binding_v0()
    )
    assert first == second


def test_config_artifact_matches_materializer(versioned_envelope: dict) -> None:
    assert CONFIG_ARTIFACT_PATH.is_file()
    on_disk = json.loads(CONFIG_ARTIFACT_PATH.read_text(encoding="utf-8"))
    assert on_disk == versioned_envelope


def test_digest_input_sorted_keys() -> None:
    payload = build_operator_decision_digest_input_v0()
    assert list(payload.keys()) == sorted(RATIFIED_OPERATOR_BINDING_VALUES.keys())
